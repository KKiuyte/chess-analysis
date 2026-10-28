"""Agrégation des données et génération d'un dashboard HTML autonome par cadence."""
import datetime as dt
import json

from . import insights

PHASES = ["opening", "middlegame", "endgame"]
RESULT = {"win": "W", "draw": "D", "loss": "L"}
TC_LABELS = {"bullet": "Bullet", "blitz": "Blitz", "rapid": "Rapide", "daily": "Daily"}


def classify(loss, cls):
    if loss >= cls["blunder"]:
        return 3
    if loss >= cls["mistake"]:
        return 2
    if loss >= cls["inaccuracy"]:
        return 1
    return 0


def ignored(win_before, win_after, cls):
    """Position déjà jouée : perdue, ou gagnée et qui le reste."""
    return win_before < cls["lost_below"] or (
        win_before > cls["won_above"] and win_after > cls["still_won_above"])


def build_data(cfg, con, tc):
    cls = cfg["classification"]
    tc_cfg = cfg["time_classes"][tc]
    games, index = [], {}
    rows = con.execute(
        """SELECT g.*, a.limit_key FROM games g LEFT JOIN analyzed_games a ON a.game_id = g.id
           WHERE g.time_class = ? ORDER BY g.end_time""", (tc,)).fetchall()
    for r in rows:
        index[r["id"]] = len(games)
        games.append({
            "u": r["url"], "d": r["date"], "m": r["month"], "c": r["color"], "o": r["opponent"],
            "me": r["my_elo"], "oe": r["opp_elo"], "r": RESULT[r["result"]],
            "f": r["opening_family"], "v": r["opening_variant"], "eco": r["eco"],
            "a": int(r["limit_key"] is not None),
            # par phase : [coups comptés, imprécisions, erreurs, gaffes]
            "s": [[0, 0, 0, 0] for _ in PHASES],
        })

    for r in con.execute(
            """SELECT m.* FROM moves m JOIN games g ON g.id = m.game_id
               WHERE g.time_class = ? AND m.is_mine = 1 AND m.win_before IS NOT NULL""", (tc,)):
        g = games[index[r["game_id"]]]
        wb, wa = r["win_before"], r["win_after"]
        if ignored(wb, wa, cls):
            continue
        loss = max(0.0, wb - wa)
        stats = g["s"][PHASES.index(r["phase"])]
        stats[0] += 1
        k = classify(loss, cls)
        if k:
            stats[k] += 1

    return {
        "player": cfg["username"].capitalize(),
        "tc": tc,
        "tcLabel": TC_LABELS.get(tc, tc.capitalize()),
        "since": cfg["since"].isoformat(),
        "generated": dt.datetime.now().strftime("%Y-%m-%d %H:%M"),
        "engine": tc_cfg,
        "thresholds": {k: cls[k] for k in ("inaccuracy", "mistake", "blunder")},
        "openings": {"minGames": tc_cfg.get("min_games", cfg["openings"]["min_games"]),
                     "lowScore": cfg["openings"]["low_score"]},
        "diag": insights.compute(cfg, con, tc, rows),
        "games": games,
    }


def page_html(template, data):
    payload = json.dumps(data, ensure_ascii=False, separators=(",", ":")).replace("<", "\\u003c")
    title = f"Échecs {data['player'].capitalize()} {data['tcLabel']}"
    return template.replace("__TITLE__", title).replace("__DATA__", payload)


def standalone(fragment):
    """Le template est un fragment ; le fichier local reçoit son squelette complet."""
    return ('<!doctype html>\n<html lang="fr">\n<head>\n<meta charset="utf-8">\n'
            '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n'
            '<style>[hidden]{display:none!important}</style>\n'
            f'</head>\n<body>\n{fragment}\n</body>\n</html>\n')


def build(cfg, con):
    template = (cfg["root"] / "templates" / "dashboard.html").read_text()
    out = cfg["out_dir"]
    (out / "fragments").mkdir(parents=True, exist_ok=True)
    for tc in cfg["time_classes"]:
        data = build_data(cfg, con, tc)
        fragment = page_html(template, data)
        (out / f"dashboard-{tc}.html").write_text(standalone(fragment))
        (out / "fragments" / f"dashboard-{tc}.html").write_text(fragment)
        analyzed = sum(g["a"] for g in data["games"])
        print(f"Dashboard {tc} : {len(data['games'])} parties ({analyzed} analysées) → {out / f'dashboard-{tc}.html'}")
