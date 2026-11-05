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


def pending_tasks(cfg, con):
    tasks = []
    for tc, tc_cfg in cfg["time_classes"].items():
        limit_kwargs, key = engine_limit(tc_cfg)
        rows = con.execute(
            """SELECT g.id, g.color FROM games g
               LEFT JOIN analyzed_games a ON a.game_id = g.id
               WHERE g.time_class = ? AND (a.limit_key IS NULL OR a.limit_key != ?)
                 AND g.id IN (SELECT id FROM games WHERE time_class = ? ORDER BY end_time DESC LIMIT ?)
               ORDER BY g.end_time DESC""", (tc, key, tc, cfg.get("max_games") or -1)).fetchall()
        for r in rows:
            moves = [tuple(m) for m in con.execute(
                "SELECT ply, fen_before, uci, is_mine FROM moves WHERE game_id = ? ORDER BY ply", (r["id"],))]
            tasks.append(((r["id"], r["color"], moves, limit_kwargs), key))
    return tasks


def analyze(cfg, con):
    tasks = pending_tasks(cfg, con)
    if not tasks:
        print("Analyse moteur : rien de nouveau")
        return
    games = {t[0][0]: t for t in tasks}            # game_id → ((id, couleur, coups, limite), clé)
    need = {gid: _positions(t[0][2]) for gid, t in games.items()}
    jobs = [(fen, t[0][3], gid) for gid, t in games.items() for fen in need[gid]]
    evals = {gid: {} for gid in games}
    n = len(tasks)
    procs = cfg["engine"]["processes"]
    print(f"Analyse moteur : {n} partie(s), {len(jobs)} positions à analyser avec {procs} process")
    if cfg.get("on_progress"):
        cfg["on_progress"](0, n)
    start = time.time()
    done = 0

    def save(gid):
        nonlocal done
        (game_id, color, moves, _), key = games[gid]
        con.executemany(
            """UPDATE moves SET cp_before=?, cp_after=?, win_before=?, win_after=?, best_uci=?, best_san=?
               WHERE game_id=? AND ply=?""", _game_results(game_id, color, moves, evals.pop(gid)))
        con.execute("INSERT OR REPLACE INTO analyzed_games VALUES (?, ?, ?)",
                    (game_id, key, dt.datetime.now(dt.timezone.utc).isoformat()))
        con.commit()
        done += 1
        if cfg.get("on_progress"):
            cfg["on_progress"](done, n)
        if done % 10 == 0 or done == n:
            elapsed = time.time() - start
            print(f"  {done}/{n} parties — {elapsed / 60:.1f} min écoulées, ~{elapsed / done * (n - done) / 60:.0f} min restantes",
                  flush=True)

    for gid in [g for g in games if not need[g]]:   # partie sans coup à moi à évaluer
        save(gid)
    pool = mp.Pool(procs, initializer=_init_worker, initargs=(cfg["engine"],))
    try:
        for gid, fen, cp, best in pool.imap_unordered(_eval_position, jobs, chunksize=2):
            evals[gid][fen] = (cp, best)
            if len(evals[gid]) == len(need[gid]):
                save(gid)
    except KeyboardInterrupt:
        print("\nInterrompu : les parties déjà analysées sont enregistrées, relancer pour reprendre.")
        raise
    finally:
        # Tous les résultats sont reçus : on arrête les workers sans attendre leurs moteurs
        # (le thread de SimpleEngine empêche sinon les workers de se terminer). Stockfish
        # s'arrête de lui-même quand son entrée standard se ferme.
        pool.terminate()
        pool.join()
