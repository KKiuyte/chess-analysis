"""Exercices personnalisés : mes erreurs et gaffes, rejouées sur un échiquier.

Chaque position est réévaluée en multipv sur tous les coups légaux : la page sait
noter n'importe quel coup et montrer la réfutation d'un mauvais coup.
"""
import datetime as dt
import json
import multiprocessing as mp
import time

import chess
import chess.engine

from . import analyze
from .dashboard import TC_LABELS, ignored, standalone

THEMES = {
    "mate": "Trouve le mat",
    "tactic": "Trouve le coup gagnant",
    "safe": "Joue un coup sûr",
}
SCHEMA = """
CREATE TABLE IF NOT EXISTS exercise_evals (
    fen TEXT,
    depth INTEGER,
    moves TEXT,              -- JSON : [[uci, san, win%, réponse uci, réponse san, mat en N (négatif : mat subi, 0 : pas de mat)], ...] trié du meilleur au pire
    PRIMARY KEY (fen, depth)
);
"""


def _eval_all(task):
    """Tous les coups légaux d'une position, du point de vue du joueur au trait."""
    fen, depth = task
    board = chess.Board(fen)
    infos = analyze._engine.analyse(board, chess.engine.Limit(depth=depth),
                                    multipv=board.legal_moves.count(), game=fen)
    out = []
    for info in infos:
        pv = info.get("pv")
        if not pv:
            continue
        score = info["score"].pov(board.turn)
        cp = score.score(mate_score=analyze.MATE_CP)
        after = board.copy(stack=False)
        san = after.san(pv[0])
        after.push(pv[0])
        reply = pv[1] if len(pv) > 1 else None
        mate = score.mate() or 0
        out.append([pv[0].uci(), san, round(analyze.win_pct(cp), 1),
                    reply.uci() if reply else None, after.san(reply) if reply else None, mate])
    out.sort(key=lambda m: -m[2])
    return fen, depth, out


def _candidates(cfg, con):
    """Mes erreurs et gaffes dans des positions encore jouables, une par position."""
    cls, ex = cfg["classification"], cfg["exercises"]
    rows = con.execute(
        """SELECT m.*, g.url, g.date, g.time_class, g.opponent, g.opp_elo, g.color AS my_color
           FROM moves m JOIN games g ON g.id = m.game_id
           WHERE m.is_mine = 1 AND m.win_before IS NOT NULL AND m.win_before - m.win_after >= ?
             AND m.win_before >= ?
           ORDER BY g.end_time DESC""", (cls["mistake"], ex["min_win_before"])).fetchall()
    seen, out = set(), []
    for r in rows:
        key = " ".join(r["fen_before"].split()[:4])
        if key in seen or ignored(r["win_before"], r["win_after"], cls) or r["time_class"] not in cfg["time_classes"]:
            continue
        seen.add(key)
        out.append(r)
    # Les plus coûteuses d'abord, puis on garde de la marge pour le tri par thème après évaluation.
    out.sort(key=lambda r: -(r["win_before"] - r["win_after"]))
    return out[:ex["max"] * 2]


def _evaluate(cfg, con, fens):
    depth = cfg["exercises"]["depth"]
    con.executescript(SCHEMA)
    done = {r[0]: json.loads(r[1]) for r in con.execute(
        "SELECT fen, moves FROM exercise_evals WHERE depth = ?", (depth,))}
    todo = [f for f in dict.fromkeys(fens) if f not in done]
    if todo:
        procs = cfg["engine"]["processes"]
        print(f"Exercices : {len(todo)} position(s) à évaluer (tous les coups, profondeur {depth}) avec {procs} process")
        start = time.time()
        pool = mp.Pool(procs, initializer=analyze._init_worker, initargs=(cfg["engine"],))
        try:
            for i, (fen, d, moves) in enumerate(pool.imap_unordered(_eval_all, [(f, depth) for f in todo]), 1):
                con.execute("INSERT OR REPLACE INTO exercise_evals VALUES (?, ?, ?)", (fen, d, json.dumps(moves)))
                con.commit()
                done[fen] = moves
                if i % 20 == 0 or i == len(todo):
                    el = time.time() - start
                    print(f"  {i}/{len(todo)} — {el / 60:.1f} min, ~{el / i * (len(todo) - i) / 60:.0f} min restantes", flush=True)
        finally:
            pool.terminate()
            pool.join()
    return done


def _theme(moves, tol):
    if moves[0][5] > 0:
        return "mate"
    best = moves[0][2]
    good = sum(1 for m in moves if m[2] >= best - tol)
    return "tactic" if good <= 2 else "safe"


def build_data(cfg, con):
    ex = cfg["exercises"]
    cands = _candidates(cfg, con)
    evals = _evaluate(cfg, con, [r["fen_before"] for r in cands])
    by_theme = {t: [] for t in THEMES}
    for r in cands:
        moves = evals.get(r["fen_before"])
        if not moves:
            continue
        played = next((m for m in moves if m[0] == r["uci"]), None)
        # La réévaluation doit confirmer que le coup de la partie était une vraie erreur.
        if not played or moves[0][2] - played[2] < cfg["classification"]["mistake"]:
            continue
        th = _theme(moves, ex["tolerance"])
        by_theme[th].append({
            "id": f"{r['game_id']}-{r['ply']}", "fen": r["fen_before"], "th": th,
            "tc": r["time_class"], "u": r["url"], "d": r["date"], "o": r["opponent"], "oe": r["opp_elo"],
            "n": r["move_no"], "c": r["my_color"], "pu": r["uci"], "ps": r["san"],
            "wb": round(r["win_before"], 1),
            "mv": moves,
        })
    # Répartition équilibrée entre thèmes, à tour de rôle, dans l'ordre de gravité.
    items, i = [], 0
    while len(items) < ex["max"] and any(i < len(v) for v in by_theme.values()):
        for v in by_theme.values():
            if i < len(v) and len(items) < ex["max"]:
                items.append(v[i])
        i += 1
    return {
        "player": cfg["username"].capitalize(),
        "themes": THEMES,
        "tcLabels": {tc: TC_LABELS.get(tc, tc.capitalize()) for tc in cfg["time_classes"]},
        "tolerance": ex["tolerance"],
        "depth": ex["depth"],
        "since": cfg["since"].isoformat(),
        "generated": dt.datetime.now().strftime("%Y-%m-%d %H:%M"),
        "items": items,
    }


def build(cfg, con):
    template = (cfg["root"] / "templates" / "exercises.html").read_text()
    data = build_data(cfg, con)
    payload = json.dumps(data, ensure_ascii=False, separators=(",", ":")).replace("<", "\\u003c")
    fragment = template.replace("__TITLE__", f"Exercices {data['player']}").replace("__DATA__", payload)
    out = cfg["out_dir"]
    (out / "fragments").mkdir(parents=True, exist_ok=True)
    (out / "exercises.html").write_text(standalone(fragment))
    (out / "fragments" / "exercises.html").write_text(fragment)
    counts = {t: sum(1 for x in data["items"] if x["th"] == t) for t in THEMES}
    print(f"Exercices : {len(data['items'])} ({', '.join(f'{THEMES[t]} {n}' for t, n in counts.items())})"
          f" → {out / 'exercises.html'}")
