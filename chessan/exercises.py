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
from .dashboard import TC_LABELS, ignored, save_json, standalone

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


def _evaluate(cfg, con, fens, enough=None):
    """enough : s'arrêter dès que ce nombre de positions de `fens` est évalué (première publication :
    une position très longue à calculer ne retarde pas tout le monde, elle sera faite au passage complet)."""
    depth = cfg["exercises"]["depth"]
    con.executescript(SCHEMA)
    done = {r[0]: json.loads(r[1]) for r in con.execute(
        "SELECT fen, moves FROM exercise_evals WHERE depth = ?", (depth,))}
    todo = [f for f in dict.fromkeys(fens) if f not in done]
    if todo:
        procs = cfg["engine"]["processes"]
        print(f"Exercices : {len(todo)} position(s) à évaluer (tous les coups, profondeur {depth}) avec {procs} process")
        # Jauge d'attente : objectif = positions encore nécessaires (enough), pas toutes celles lancées.
        goal = len(todo) if not enough else max(1, min(len(todo), enough - (len(set(fens)) - len(todo))))
        if cfg.get("on_ex_progress"):
            cfg["on_ex_progress"](0, goal)
        start = time.time()
        pool = mp.Pool(procs, initializer=analyze._init_worker, initargs=(cfg["engine"],))
        try:
            for i, (fen, d, moves) in enumerate(pool.imap_unordered(_eval_all, [(f, depth) for f in todo]), 1):
                con.execute("INSERT OR REPLACE INTO exercise_evals VALUES (?, ?, ?)", (fen, d, json.dumps(moves)))
                con.commit()
                done[fen] = moves
                if cfg.get("on_ex_progress"):
                    cfg["on_ex_progress"](min(i, goal), goal)
                if i % 20 == 0 or i == len(todo):
                    el = time.time() - start
                    print(f"  {i}/{len(todo)} — {el / 60:.1f} min, ~{el / i * (len(todo) - i) / 60:.0f} min restantes", flush=True)
                if enough and sum(f in done for f in set(fens)) >= enough:
                    print(f"  {enough} positions prêtes en {(time.time() - start) / 60:.1f} min : on publie, le reste suit", flush=True)
                    break
        finally:
            pool.terminate()
            pool.join()
    return done


def _mate_budget(moves):
    """Mat : on accepte un mat aussi rapide que le meilleur (un coup de plus à partir du mat en 3)."""
    best = moves[0][5]
    return best + (1 if best >= 3 else 0)


def _mate_lines(cfg, con, items, max_nodes=30):
    """Prolonge les exercices de mat jusqu'au mat : après chaque bon coup, l'adversaire joue
    sa meilleure défense et le joueur continue. Arbre construit niveau par niveau ;
    item["nx"][uci] = {r, rs, chk, b, mv, nx} pour chaque coup accepté (mat pas encore donné).
    Au-delà de max_nodes positions par exercice, la ligne s'arrête (le coup est alors validé)."""
    cfg = {**cfg, "on_ex_progress": None}   # courts calculs : la jauge d'attente ne repart pas à zéro
    level = []                          # (exercice, nœud parent, fen du nœud parent)
    for it in items:
        if it["th"] == "mate":
            it["b"] = _mate_budget(it["mv"])
            it["_n"] = 0
            level.append((it, it, it["fen"]))
    while level:
        expand = []                     # (exercice, parent, uci, fen du nœud enfant)
        for it, node, fen in level:
            node["nx"] = {}
            for m in node["mv"]:
                if not (0 < m[5] <= node["b"]) or m[5] == 1 or not m[3] or it["_n"] >= max_nodes:
                    continue
                board = chess.Board(fen)
                board.push_uci(m[0])
                board.push_uci(m[3])
                it["_n"] += 1
                expand.append((it, node, m, board.fen()))
        evals = _evaluate(cfg, con, [f for *_, f in expand]) if expand else {}
        level = []
        for it, node, m, fen in expand:
            moves = evals.get(fen)
            if not moves or moves[0][5] <= 0:
                continue                # plus de mat vu à cette profondeur : la ligne s'arrête là
            child = {"r": m[3], "rs": m[4], "chk": chess.Board(fen).is_check(),
                     "b": max(m[5] - 1, moves[0][5]), "mv": moves}
            node["nx"][m[0]] = child
            level.append((it, child, fen))
    for it in items:
        it.pop("_n", None)


def _theme(moves, tol):
    if moves[0][5] > 0:
        return "mate"
    best = moves[0][2]
    good = sum(1 for m in moves if m[2] >= best - tol)
    return "tactic" if good <= 2 else "safe"


def build_data(cfg, con, first=None):
    """first : n'évaluer que les `first` erreurs les plus coûteuses (première publication rapide)."""
    ex = cfg["exercises"]
    # Première publication : on lance un peu plus de positions que nécessaire et on garde les `first`
    # premières prêtes (les plus graves d'abord).
    cands = _candidates(cfg, con)[:first + first // 2 if first else None]
    evals = _evaluate(cfg, con, [r["fen_before"] for r in cands], enough=first)
    if first:
        cands = [r for r in cands if r["fen_before"] in evals][:first]
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
            "chk": chess.Board(r["fen_before"]).is_check(),
            "mv": moves,
        })
    # Répartition équilibrée entre thèmes, à tour de rôle, dans l'ordre de gravité.
    items, i = [], 0
    while len(items) < ex["max"] and any(i < len(v) for v in by_theme.values()):
        for v in by_theme.values():
            if i < len(v) and len(items) < ex["max"]:
                items.append(v[i])
        i += 1
    _mate_lines(cfg, con, items)
    return {
        "player": cfg["username"].capitalize(),
        "themes": THEMES,
        "tcLabels": {tc: TC_LABELS.get(tc, tc.capitalize()) for tc in cfg["time_classes"]},
        "tolerance": ex["tolerance"],
        "depth": ex["depth"],
        "since": cfg["since"].isoformat(),
        "generated": dt.datetime.now().strftime("%Y-%m-%d %H:%M"),
        "items": items,
        "more": first is not None,           # première publication : d'autres exercices suivent
    }


def build(cfg, con, first=None):
    template = (cfg["root"] / "templates" / "exercises.html").read_text()
    data = build_data(cfg, con, first)
    payload = json.dumps(data, ensure_ascii=False, separators=(",", ":")).replace("<", "\\u003c")
    fragment = template.replace("__TITLE__", f"Exercices {data['player']}").replace("__DATA__", payload)
    out = cfg["out_dir"]
    (out / "fragments").mkdir(parents=True, exist_ok=True)
    (out / "exercises.html").write_text(standalone(fragment))
    (out / "fragments" / "exercises.html").write_text(fragment)
    save_json(out, "exercises", data)
    counts = {t: sum(1 for x in data["items"] if x["th"] == t) for t in THEMES}
    print(f"Exercices : {len(data['items'])} ({', '.join(f'{THEMES[t]} {n}' for t, n in counts.items())})"
          f" → {out / 'exercises.html'}")
