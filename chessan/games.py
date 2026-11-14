"""Parties à rejouer dans l'appli : une liste (page « games ») et une fiche par partie.

Liste (output/<pseudo>/data/games.json), une entrée par partie des cadences gardées :
    {id, t, d, tc, c, o, oe, me, r, rd, f, v, u, n, a, q: [imprécisions, erreurs, gaffes], ex}
Fiche (publish : players/{pseudo}/games/{id}), un élément par demi-coup :
    [san, uci, pendule]                                  coup de l'adversaire (ou non analysé)
    [san, uci, pendule, gain avant, gain après, classe, meilleur san, meilleur uci, type de gaffe]
gain = % de gain du joueur ; classe 0-3 (rien, imprécision, erreur, gaffe) ; type : insights.BLUNDER_KINDS.
"""
import json

from . import dashboard, insights

RESULT = {"win": "W", "draw": "D", "loss": "L"}


def _exercise_games(cfg):
    """Nombre d'exercices tirés de chaque partie (identifiant d'exercice = <partie>-<demi-coup>)."""
    f = cfg["out_dir"] / "data" / "exercises.json"
    out = {}
    if f.exists():
        for x in json.loads(f.read_text())["items"]:
            gid = x["id"].rsplit("-", 1)[0]
            out[gid] = out.get(gid, 0) + 1
    return out


def _games(cfg, con):
    tcs = list(cfg["time_classes"])
    return con.execute(
        f"""SELECT g.*, a.limit_key FROM games g LEFT JOIN analyzed_games a ON a.game_id = g.id
            WHERE g.date >= ? AND g.time_class IN ({",".join("?" * len(tcs))})
            ORDER BY g.end_time DESC""", (cfg["since"].isoformat(), *tcs)).fetchall()


def details(cfg, con, game_ids=None):
    """{id: fiche} des parties demandées (toutes par défaut)."""
    cls = cfg["classification"]
    ids = game_ids if game_ids is not None else [g["id"] for g in _games(cfg, con)]
    out = {}
    for gid in ids:
        plies = []
        for m in con.execute("SELECT * FROM moves WHERE game_id = ? ORDER BY ply", (gid,)):
            clock = None if m["clock"] is None else round(m["clock"])
            e = [m["san"], m["uci"], clock]
            if m["is_mine"] and m["win_before"] is not None:
                wb, wa = m["win_before"], m["win_after"]
                k = 0 if dashboard.ignored(wb, wa, cls) else dashboard.classify(max(0.0, wb - wa), cls)
                kind = ""
                if k >= 2 and m["best_uci"] and m["best_uci"] != m["uci"]:
                    kind = insights.blunder_kind(m["fen_before"], m["uci"], m["best_uci"], m["cp_before"], m["cp_after"])
                e += [round(wb, 1), round(wa, 1), k, m["best_san"] or "", m["best_uci"] or "", kind]
            plies.append(e)
        out[gid] = {"id": gid, "m": plies}
    return out


def build_data(cfg, con, fiches=None):
    """fiches : résultat de details() pour compter les fautes ; recalculé sinon."""
    games = _games(cfg, con)
    fiches = fiches or details(cfg, con, [g["id"] for g in games])
    exs = _exercise_games(cfg)
    items = []
    for g in games:
        q = [0, 0, 0]
        for e in fiches.get(g["id"], {}).get("m", []):
            if len(e) > 5 and e[5]:
                q[e[5] - 1] += 1
        items.append({
            "id": g["id"], "t": g["end_time"], "d": g["date"], "tc": g["time_class"], "c": g["color"],
            "o": g["opponent"], "oe": g["opp_elo"], "me": g["my_elo"], "r": RESULT[g["result"]],
            "rd": g["result_detail"], "f": g["opening_family"], "v": g["opening_variant"], "u": g["url"],
            "n": g["n_plies"], "a": int(g["limit_key"] is not None), "q": q, "ex": exs.get(g["id"], 0),
        })
    return {
        "player": cfg["username"].capitalize(),
        "tcLabels": {tc: dashboard.TC_LABELS.get(tc, tc.capitalize()) for tc in cfg["time_classes"]},
        "kinds": insights.BLUNDER_KINDS,
        "since": cfg["since"].isoformat(),
        "items": items,
    }


def build(cfg, con):
    """Écrit la liste (data/games.json) et renvoie les fiches, publiées à part (une par document)."""
    fiches = details(cfg, con)
    data = build_data(cfg, con, fiches)
    dashboard.save_json(cfg["out_dir"], "games", data)
    print(f"Parties : {len(data['items'])} à rejouer")
    return fiches
