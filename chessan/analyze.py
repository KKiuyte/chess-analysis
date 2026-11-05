"""Analyse Stockfish de mes coups, multi-process, persistée partie par partie (reprise possible)."""
import datetime as dt
import math
import multiprocessing as mp
import os
import time

import chess
import chess.engine

from .config import engine_limit

MATE_CP = 10000
_engine = None


def win_pct(cp):
    """Centipawns (point de vue du joueur) → % de gain."""
    return 50 + 50 * (2 / (1 + math.exp(-0.00368208 * cp)) - 1)


def _init_worker(engine_cfg):
    global _engine
    os.nice(engine_cfg.get("nice", 0))
    _engine = chess.engine.SimpleEngine.popen_uci(engine_cfg["path"])
    _engine.configure({"Threads": engine_cfg["threads"], "Hash": engine_cfg["hash_mb"]})


def _evaluate(board, limit, game_id):
    """(score centipawns côté blancs, meilleur coup) pour une position."""
    if board.is_checkmate():
        return (-MATE_CP if board.turn == chess.WHITE else MATE_CP), None
    if board.is_game_over():
        return 0, None
    info = _engine.analyse(board, limit, game=game_id)
    pv = info.get("pv") or [None]
    return info["score"].white().score(mate_score=MATE_CP), pv[0]


def _positions(moves):
    """Positions à évaluer pour une partie : avant et après chacun de mes coups (sans doublon)."""
    fens = {}
    for ply, fen_before, uci, is_mine in moves:
        if is_mine:
            board = chess.Board(fen_before)
            board.push_uci(uci)
            fens[fen_before] = None
            fens[board.fen()] = None
    return list(fens)


def _eval_position(task):
    """Une position, évaluée par le Stockfish du process (la répartition se fait par position :
    tous les process restent occupés jusqu'au bout, même avec peu de parties).
    Mémoire de Stockfish vidée à chaque position (game unique) : le résultat ne dépend pas de
    l'ordre de répartition entre process, donc l'analyse est reproductible."""
    fen, limit_kwargs, game_id = task
    cp, best = _evaluate(chess.Board(fen), chess.engine.Limit(**limit_kwargs), (game_id, fen))
    return game_id, fen, cp, best.uci() if best else None


def _game_results(game_id, my_color, moves, evals):
    """Lignes à écrire dans moves, à partir des évaluations {fen: (cp côté blancs, meilleur coup uci)}."""
    sign = 1 if my_color == "w" else -1
    results = []
    for ply, fen_before, uci, is_mine in moves:
        if not is_mine:
            continue
        board = chess.Board(fen_before)
        cp_before, best = evals[fen_before]
        board.push_uci(uci)
        cp_after, _ = evals[board.fen()]
        cp_before, cp_after = sign * cp_before, sign * cp_after
        best_move = chess.Move.from_uci(best) if best else None
        best_san = chess.Board(fen_before).san(best_move) if best_move else None
        results.append((cp_before, cp_after, win_pct(cp_before), win_pct(cp_after),
                        best, best_san, game_id, ply))
    return results


def tc_limit(cfg, con, tc):
    """Limite moteur d'une cadence pour ce joueur. [app].elo_depth = [[Elo minimum, écart], ...] ajuste
    la profondeur selon son dernier classement dans la cadence : erreurs grossières sous 1000,
    plus fines chez les joueurs forts."""
    tc_cfg = cfg["time_classes"][tc]
    steps = cfg.get("app", {}).get("elo_depth") if "depth" in tc_cfg else None
    if steps:
        r = con.execute("""SELECT my_elo FROM games WHERE time_class = ? AND my_elo IS NOT NULL
                           ORDER BY end_time DESC LIMIT 1""", (tc,)).fetchone()
        if r:
            delta = max((s for s in steps if r[0] >= s[0]), key=lambda s: s[0], default=(0, 0))[1]
            tc_cfg = {**tc_cfg, "depth": tc_cfg["depth"] + delta}
    return engine_limit(tc_cfg)


def _up_to_date(old, key):
    """Partie déjà analysée avec cette limite, ou à une profondeur au moins égale : on la garde."""
    if old is None:
        return False
    if old == key:
        return True
    return old[0] == key[0] == "d" and int(old[1:]) >= int(key[1:])


def pending_tasks(cfg, con):
    tasks = []
    for tc in cfg["time_classes"]:
        limit_kwargs, key = tc_limit(cfg, con, tc)
        rows = [r for r in con.execute(
            """SELECT g.id, g.color, a.limit_key FROM games g
               LEFT JOIN analyzed_games a ON a.game_id = g.id
               WHERE g.time_class = ?
                 AND g.id IN (SELECT id FROM games WHERE time_class = ? ORDER BY end_time DESC LIMIT ?)
               ORDER BY g.end_time DESC""", (tc, tc, cfg.get("max_games") or -1)).fetchall()
                if not _up_to_date(r["limit_key"], key)]
        for r in rows:
            moves = [tuple(m) for m in con.execute(
                "SELECT ply, fen_before, uci, is_mine FROM moves WHERE game_id = ? ORDER BY ply", (r["id"],))]
            tasks.append(((r["id"], r["color"], moves, limit_kwargs), key))
    return tasks


def cost(task):
    """Coût estimé d'une partie : positions à évaluer, pondérées par la profondeur (≈ ×2 tous les 2 niveaux)."""
    (_, _, moves, limit_kwargs), _ = task
    depth = limit_kwargs.get("depth", 14)
    return len(_positions(moves)) * 2 ** ((depth - 12) / 2)


def evaluate(tasks, engine_cfg, procs, on_game):
    """Analyse des parties `tasks` (cf. pending_tasks) avec `procs` Stockfish, répartis position par
    position. on_game(game_id, clé, lignes pour moves) est appelé dès qu'une partie est complète."""
    games = {t[0][0]: t for t in tasks}
    need = {gid: _positions(t[0][2]) for gid, t in games.items()}
    evals = {gid: {} for gid in games}

    def finish(gid):
        (game_id, color, moves, _), key = games[gid]
        on_game(game_id, key, _game_results(game_id, color, moves, evals.pop(gid)))

    for gid in [g for g in games if not need[g]]:   # partie sans coup à moi à évaluer
        finish(gid)
    jobs = [(fen, games[gid][0][3], gid) for gid in games for fen in need[gid]]
    if not jobs:
        return
    pool = mp.Pool(procs, initializer=_init_worker, initargs=(engine_cfg,))
    try:
        for gid, fen, cp, best in pool.imap_unordered(_eval_position, jobs, chunksize=2):
            evals[gid][fen] = (cp, best)
            if len(evals[gid]) == len(need[gid]):
                finish(gid)
    except KeyboardInterrupt:
        print("\nInterrompu : les parties déjà analysées sont enregistrées, relancer pour reprendre.")
        raise
    finally:
        # Tous les résultats sont reçus : on arrête les workers sans attendre leurs moteurs
        # (le thread de SimpleEngine empêche sinon les workers de se terminer). Stockfish
        # s'arrête de lui-même quand son entrée standard se ferme.
        pool.terminate()
        pool.join()


def save_game(con, game_id, key, results):
    con.executemany(
        """UPDATE moves SET cp_before=?, cp_after=?, win_before=?, win_after=?, best_uci=?, best_san=?
           WHERE game_id=? AND ply=?""", [tuple(r) for r in results])
    con.execute("INSERT OR REPLACE INTO analyzed_games VALUES (?, ?, ?)",
                (game_id, key, dt.datetime.now(dt.timezone.utc).isoformat()))
    con.commit()


def analyze(cfg, con, tasks=None):
    """Analyse locale des parties en attente (ou de `tasks`), enregistrées au fil de l'eau."""
    tasks = pending_tasks(cfg, con) if tasks is None else tasks
    if not tasks:
        print("Analyse moteur : rien de nouveau")
        return
    n, procs = len(tasks), cfg["engine"]["processes"]
    print(f"Analyse moteur : {n} partie(s), {sum(len(_positions(t[0][2])) for t in tasks)} positions "
          f"à analyser avec {procs} process")
    start, done = time.time(), 0

    def on_game(game_id, key, results):
        nonlocal done
        save_game(con, game_id, key, results)
        done += 1
        if cfg.get("on_game"):
            cfg["on_game"]()
        if done % 10 == 0 or done == n:
            elapsed = time.time() - start
            print(f"  {done}/{n} parties — {elapsed / 60:.1f} min écoulées, ~{elapsed / done * (n - done) / 60:.0f} min restantes",
                  flush=True)

    evaluate(tasks, cfg["engine"], procs, on_game)
