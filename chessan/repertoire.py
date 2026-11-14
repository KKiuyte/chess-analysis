"""Répertoire d'ouvertures personnel : les positions d'ouverture rencontrées plusieurs fois, ce que le
joueur y joue, ce que Stockfish préfère, et où il quitte la théorie.

Théorie = positions des lignes nommées de la base d'ouvertures Lichess (chessan/data/lichess_openings.tsv,
domaine public CC0, https://github.com/lichess-org/chess-openings).

Page « repertoire » (output/<pseudo>/data/repertoire.json) :
    pos   : [{k, c, ply, path, name, fen, n, th, mv: [{s, u, n, sc, l, th}], b: [san, uci], out}]
    leaks : [{k, s, u, n, l, b: [san, uci], path, name, fen, c}]   les 5 « fuites » par couleur
"""
import functools
from collections import Counter, defaultdict

import chess

from . import dashboard

SCORE = {"win": 1, "draw": 0.5, "loss": 0}
DATA = __import__("pathlib").Path(__file__).parent / "data" / "lichess_openings.tsv"


def _epd(board_or_fen):
    b = board_or_fen if isinstance(board_or_fen, chess.Board) else chess.Board(board_or_fen)
    return b.epd()


@functools.lru_cache(maxsize=1)
def theory():
    """{epd: nom} de toutes les positions des lignes de la base Lichess (nom de la ligne la plus courte
    qui y aboutit exactement, sinon de la première qui y passe)."""
    exact, passing = {}, {}
    for line in DATA.read_text().splitlines()[1:]:
        eco, name, pgn = line.split("\t")
        b = chess.Board()
        sans = [t for t in pgn.split() if not t[0].isdigit()]
        for k, san in enumerate(sans):
            b.push_san(san)
            e = b.epd()
            if k == len(sans) - 1:
                if e not in exact or len(sans) < exact[e][0]:
                    exact[e] = (len(sans), name)
            else:
                passing.setdefault(e, name)
    out = dict(passing)
    out.update({e: n for e, (_, n) in exact.items()})
    out[chess.Board().epd()] = "Position de départ"
    return out


def _path(sans, start_ply=0):
    out = []
    for i, s in enumerate(sans):
        p = start_ply + i
        out.append(f"{p // 2 + 1}.{s}" if p % 2 == 0 else (s if i else f"{p // 2 + 1}…{s}"))
    return " ".join(out)


def build_data(cfg, con):
    rep = cfg.get("repertoire", {})
    min_seen, max_ply = rep.get("min_seen", 3), rep.get("max_ply", 2 * cfg["phases"]["opening_moves"])
    tol = cfg["exercises"]["tolerance"]
    th = theory()
    tcs = list(cfg["time_classes"])
    games = con.execute(
        f"""SELECT id, color, result, end_time FROM games
            WHERE date >= ? AND time_class IN ({",".join("?" * len(tcs))}) ORDER BY end_time DESC""",
        (cfg["since"].isoformat(), *tcs)).fetchall()

    pos = {}
    for g in games:
        sans = []
        for m in con.execute("SELECT * FROM moves WHERE game_id = ? AND ply < ? ORDER BY ply", (g["id"], max_ply)):
            if m["is_mine"]:
                board = chess.Board(m["fen_before"])
                e = board.epd()
                p = pos.get(e)
                if p is None:
                    p = pos[e] = {"c": g["color"], "ply": m["ply"], "fen": m["fen_before"], "n": 0, "paths": Counter(),
                                  "mv": {}, "best": Counter()}
                p["n"] += 1
                p["paths"][tuple(sans)] += 1
                mv = p["mv"].get(m["san"])
                if mv is None:
                    after = board.copy(stack=False)
                    after.push_uci(m["uci"])
                    mv = p["mv"][m["san"]] = {"u": m["uci"], "n": 0, "sc": 0.0, "l": 0.0, "ln": 0, "th": after.epd() in th,
                                               "last": (g["id"], m["ply"])}   # partie la plus récente où il a été joué
                mv["n"] += 1
                mv["sc"] += SCORE[g["result"]]
                if m["win_before"] is not None:
                    mv["l"] += max(0.0, m["win_before"] - m["win_after"])
                    mv["ln"] += 1
                    if m["best_san"]:
                        p["best"][(m["best_san"], m["best_uci"])] += 1
            sans.append(m["san"])

    out, leaks = [], []
    for e, p in pos.items():
        if p["n"] < min_seen:
            continue
        path = list(p["paths"].most_common(1)[0][0])
        # Nom : la dernière position nommée du chemin (la ligne la plus précise atteinte).
        b, name = chess.Board(), None
        for s in path:
            b.push_san(s)
            name = th.get(b.epd(), name)
        moves = sorted(({"s": s, "u": v["u"], "n": v["n"], "sc": round(100 * v["sc"] / v["n"]),
                         "l": round(v["l"] / v["ln"], 1) if v["ln"] else None, "th": v["th"]}
                        for s, v in p["mv"].items()), key=lambda v: -v["n"])
        best = list(p["best"].most_common(1)[0][0]) if p["best"] else None
        in_th = e in th
        k = f"p{len(out)}"
        item = {"k": k, "c": p["c"], "ply": p["ply"], "path": _path(path), "name": name, "fen": p["fen"],
                "n": p["n"], "th": in_th, "mv": moves, "b": best,
                # Sortie de théorie : position connue, mais le coup le plus joué n'y est plus.
                "out": in_th and not moves[0]["th"]}
        out.append(item)
        for mv in moves:
            if mv["n"] >= min_seen and mv["l"] is not None and mv["l"] >= tol and best and best[0] != mv["s"]:
                leaks.append({"k": k, "s": mv["s"], "u": mv["u"], "n": mv["n"], "l": mv["l"], "b": best,
                              "path": item["path"], "name": name, "fen": p["fen"], "c": p["c"], "ply": p["ply"],
                              "w": mv["n"] * mv["l"], "last": p["mv"][mv["s"]]["last"]})
    out.sort(key=lambda x: (x["ply"], -x["n"]))
    top = []
    for c in ("w", "b"):
        top += sorted((x for x in leaks if x["c"] == c), key=lambda x: -x["w"])[:5]
    return {
        "player": cfg["username"].capitalize(),
        "since": cfg["since"].isoformat(),
        "minSeen": min_seen,
        "maxMoves": max_ply // 2,
        "tolerance": tol,
        "games": {c: sum(1 for g in games if g["color"] == c) for c in ("w", "b")},
        "pos": out,
        "leaks": [{k: v for k, v in x.items() if k not in ("w", "last")} for x in top],
    }, top


def leaks(cfg, con):
    """Fuites, avec la partie la plus récente où le coup fautif a été joué (« last » : (game_id, ply)), pour les exercices."""
    return build_data(cfg, con)[1]


def build(cfg, con):
    data, _ = build_data(cfg, con)
    dashboard.save_json(cfg["out_dir"], "repertoire", data)
    print(f"Répertoire : {len(data['pos'])} positions vues au moins {data['minSeen']} fois, {len(data['leaks'])} fuites")
