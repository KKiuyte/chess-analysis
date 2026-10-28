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


def _analyze_game(task):
    game_id, my_color, moves, limit_kwargs = task
    limit = chess.engine.Limit(**limit_kwargs)
    sign = 1 if my_color == "w" else -1
    cache = {}

    def ev(fen):
        if fen not in cache:
            cache[fen] = _evaluate(chess.Board(fen), limit, game_id)
        return cache[fen]

    results = []
    for ply, fen_before, uci, is_mine in moves:
        if not is_mine:
            continue
        board = chess.Board(fen_before)
        cp_before, best = ev(fen_before)
        board.push_uci(uci)
        cp_after, _ = ev(board.fen())
        cp_before, cp_after = sign * cp_before, sign * cp_after
        best_san = chess.Board(fen_before).san(best) if best else None
        results.append((cp_before, cp_after, win_pct(cp_before), win_pct(cp_after),
                        best.uci() if best else None, best_san, game_id, ply))
    return game_id, results


def pending_tasks(cfg, con):
    tasks = []
    for tc, tc_cfg in cfg["time_classes"].items():
        limit_kwargs, key = engine_limit(tc_cfg)
        rows = con.execute(
            """SELECT g.id, g.color FROM games g
               LEFT JOIN analyzed_games a ON a.game_id = g.id
               WHERE g.time_class = ? AND (a.limit_key IS NULL OR a.limit_key != ?)
               ORDER BY g.end_time DESC""", (tc, key)).fetchall()
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
    keys = {t[0][0]: t[1] for t in tasks}
    n = len(tasks)
    procs = cfg["engine"]["processes"]
    print(f"Analyse moteur : {n} partie(s) à analyser avec {procs} process")
    start = time.time()
    pool = mp.Pool(procs, initializer=_init_worker, initargs=(cfg["engine"],))
    try:
        for i, (game_id, results) in enumerate(pool.imap_unordered(_analyze_game, [t[0] for t in tasks]), 1):
            con.executemany(
                """UPDATE moves SET cp_before=?, cp_after=?, win_before=?, win_after=?, best_uci=?, best_san=?
                   WHERE game_id=? AND ply=?""", results)
            con.execute("INSERT OR REPLACE INTO analyzed_games VALUES (?, ?, ?)",
                        (game_id, keys[game_id], dt.datetime.now(dt.timezone.utc).isoformat()))
            con.commit()
            if i % 10 == 0 or i == n:
                elapsed = time.time() - start
                eta = elapsed / i * (n - i)
                print(f"  {i}/{n} parties — {elapsed / 60:.1f} min écoulées, ~{eta / 60:.0f} min restantes",
                      flush=True)
    except KeyboardInterrupt:
        print("\nInterrompu : les parties déjà analysées sont enregistrées, relancer pour reprendre.")
        raise
    finally:
        # Tous les résultats sont reçus : on arrête les workers sans attendre leurs moteurs
        # (le thread de SimpleEngine empêche sinon les workers de se terminer). Stockfish
        # s'arrête de lui-même quand son entrée standard se ferme.
        pool.terminate()
        pool.join()
