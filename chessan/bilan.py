"""Bilan du joueur rédigé par Claude, à partir d'un dossier de faits établis par Stockfish.

Le dossier (build_dossier) rassemble, pour chaque cadence publiée : volume, classement,
résultats, fins de défaites, taux d'erreurs par phase, constats des dashboards, ouvertures,
et quelques parties représentatives (gaffes les plus coûteuses, victoires laissées filer).
Claude ne « calcule » aucune position : il relie et hiérarchise ces faits.
"""
import datetime as dt
import json
from collections import Counter

from .dashboard import TC_LABELS, classify, ignored
from .insights import BLUNDER_KINDS, blunder_kind

PHASES = {"opening": "ouverture", "middlegame": "milieu", "endgame": "finale"}
RESULT_DETAIL = {"timeout": "au temps", "checkmated": "par mat", "resigned": "par abandon",
                 "abandoned": "par abandon de partie", "timevsinsufficient": "nulle au temps",
                 "repetition": "par répétition", "stalemate": "par pat", "agreed": "d'un commun accord",
                 "insufficient": "matériel insuffisant", "50move": "règle des 50 coups"}


def _pct(a, b):
    return round(100 * a / b) if b else None


def _score(rows):
    pts = sum({"win": 1, "draw": 0.5}.get(r["result"], 0) for r in rows)
    return _pct(pts, len(rows))


def _cadence(cfg, con, tc, diag):
    cls = cfg["classification"]
    # Mêmes parties que les dashboards (toute la base de la cadence), pour que les chiffres concordent.
    games = con.execute("SELECT * FROM games WHERE time_class = ? ORDER BY end_time", (tc,)).fetchall()
    if not games:
        return None
    by_id = {g["id"]: g for g in games}
    res = Counter(g["result"] for g in games)
    losses = Counter(RESULT_DETAIL.get(g["result_detail"], g["result_detail"]) for g in games if g["result"] == "loss")

    # Classement : début, fin, extrêmes et fin de chaque mois.
    elos = [(g["date"], g["my_elo"]) for g in games if g["my_elo"]]
    months = {}
    for d, e in elos:
        months[d[:7]] = e

    # Erreurs par phase, sur les coups analysés (positions déjà décidées ignorées, comme les dashboards).
    per_phase = {p: [0, 0, 0, 0] for p in PHASES}
    moves = con.execute(
        """SELECT m.*, g.id AS gid FROM moves m JOIN games g ON g.id = m.game_id
           WHERE g.time_class = ? AND m.is_mine = 1 AND m.win_before IS NOT NULL""", (tc,)).fetchall()
    for m in moves:
        if ignored(m["win_before"], m["win_after"], cls):
            continue
        st = per_phase[m["phase"]]
        st[0] += 1
        k = classify(max(0.0, m["win_before"] - m["win_after"]), cls)
        if k:
            st[k] += 1
    errors = {PHASES[p]: {"coups": n, "imprecisions_100": round(100 * i / n, 1), "erreurs_100": round(100 * e / n, 1),
                          "gaffes_100": round(100 * b / n, 1)}
              for p, (n, i, e, b) in per_phase.items() if n}

    # Ouvertures les plus jouées, par couleur.
    openings = {}
    for color, label in (("w", "blancs"), ("b", "noirs")):
        fam = Counter(g["opening_family"] for g in games if g["color"] == color and g["opening_family"])
        openings[label] = [{"ouverture": f, "parties": n,
                            "score_pct": _score([g for g in games if g["color"] == color and g["opening_family"] == f])}
                           for f, n in fam.most_common(5)]

    # Exemples : les gaffes les plus coûteuses (une par partie), les victoires laissées filer.
    worst, seen = [], set()
    for m in sorted(moves, key=lambda m: m["win_after"] - m["win_before"]):
        if m["gid"] in seen or ignored(m["win_before"], m["win_after"], cls):
            continue
        seen.add(m["gid"])
        g = by_id[m["gid"]]
        kind = blunder_kind(m["fen_before"], m["uci"], m["best_uci"], m["cp_before"], m["cp_after"])
        worst.append({"partie": g["url"], "date": g["date"], "couleur": "blancs" if g["color"] == "w" else "noirs",
                      "adversaire_elo": g["opp_elo"], "coup": m["move_no"], "phase": PHASES[m["phase"]],
                      "joue": m["san"], "meilleur": m["best_san"],
                      "gain_avant_pct": round(m["win_before"]), "gain_apres_pct": round(m["win_after"]),
                      "type": BLUNDER_KINDS.get(kind, kind),
                      "pendule_s": round(m["clock"]) if m["clock"] is not None else None,
                      "resultat": {"win": "gagnée", "draw": "nulle", "loss": "perdue"}[g["result"]]})
        if len(worst) == 6:
            break
    best_by_game = {}
    for m in moves:
        best_by_game[m["gid"]] = max(best_by_game.get(m["gid"], 0), m["win_before"])
    blown = [{"partie": by_id[gid]["url"], "date": by_id[gid]["date"], "meilleur_gain_pct": round(w),
              "fin": "nulle" if by_id[gid]["result"] == "draw"
              else "perdue " + RESULT_DETAIL.get(by_id[gid]["result_detail"], by_id[gid]["result_detail"])}
             for gid, w in sorted(best_by_game.items(), key=lambda x: -x[1])
             if w >= 90 and by_id[gid]["result"] != "win"][:4]

    analysed = len({m["gid"] for m in moves})
    return {
        "cadence": TC_LABELS.get(tc, tc),
        "parties": len(games), "parties_analysees": analysed, "premiere_partie": games[0]["date"],
        "classement": {"debut": elos[0][1] if elos else None, "fin": elos[-1][1] if elos else None,
                       "min": min(e for _, e in elos) if elos else None, "max": max(e for _, e in elos) if elos else None,
                       "fin_de_mois": months},
        "resultats": {"victoires": res["win"], "nulles": res["draw"], "defaites": res["loss"],
                      "score_pct": _score(games),
                      "score_blancs_pct": _score([g for g in games if g["color"] == "w"]),
                      "score_noirs_pct": _score([g for g in games if g["color"] == "b"])},
        "defaites_par_type": dict(losses.most_common()),
        "erreurs_par_phase": errors,
        "constats_des_dashboards": [{"titre": c["title"], "niveau": c["level"],
                                     "chiffre_cle": f"{c['metric']['value']} {c['metric']['label']}",
                                     "faits": c["facts"]} for c in diag],
        "ouvertures": openings,
        "gaffes_les_plus_couteuses": worst,
        "victoires_laissees_filer": blown,
    }


def _summary(c):
    """Résumé d'une autre cadence, pour les comparaisons."""
    by_type = c["defaites_par_type"]
    losses = c["resultats"]["defaites"]
    return {"cadence": c["cadence"], "parties": c["parties"], "score_pct": c["resultats"]["score_pct"],
            "classement_fin": c["classement"]["fin"],
            "defaites_au_temps_pct": _pct(by_type.get("au temps", 0), losses),
            "gaffes_pour_100_coups": {p: v["gaffes_100"] for p, v in c["erreurs_par_phase"].items()}}


def build_dossier(cfg, con, tc, previous=None):
    """Dossier du bilan de la cadence `tc` (dashboards déjà construits), avec un résumé des autres."""
    data_dir = cfg["out_dir"] / "data"
    cads = {}
    for t in cfg["time_classes"]:
        f = data_dir / f"dashboard-{t}.json"
        if f.exists():
            c = _cadence(cfg, con, t, json.loads(f.read_text())["diag"])
            if c:
                cads[t] = c
    return {
        "joueur": cfg["username"],
        "date": dt.date.today().isoformat(),
        "reglages": {"seuils_perte_de_gain_pct": {k: cfg["classification"][k] for k in ("inaccuracy", "mistake", "blunder")},
                     "note": "« gain » = probabilité de gain estimée par Stockfish depuis l'évaluation, du point de vue du joueur."},
        "cadence": cads[tc],
        "autres_cadences": [_summary(c) for t, c in cads.items() if t != tc],
        "bilan_precedent": previous,
    }


# --------------------------------------------------------------------------------------------
# Appel à Claude
# --------------------------------------------------------------------------------------------
MODEL = "claude-opus-5-5"

# Entraînements de l'appli que le bilan peut proposer (filtres de l'onglet Exercices).
TRAININGS = {
    "mate": "Exercices « Trouve le mat » : mats à trouver dans tes propres parties",
    "tactic": "Exercices « Trouve le coup gagnant » : un seul coup gagne (prise, fourchette, échec…)",
    "safe": "Exercices « Joue un coup sûr » : plusieurs coups conviennent, il faut éviter celui qui perd du matériel",
    "all": "Tous les exercices tirés de tes erreurs",
}

SYSTEM = """Tu es entraîneur d'échecs. Tu rédiges le bilan d'un joueur amateur de chess.com pour une cadence (blitz, rapid, daily…), à partir d'un dossier de statistiques établies par le moteur Stockfish sur ses parties.

Le bilan s'affiche en tête du dashboard de cette cadence, dans une appli. Le joueur veut comprendre en un coup d'œil ce qui lui coûte des parties et quoi travailler. Tutoie-le, écris en français simple, et sois bref : chaque champ a une longueur maximale, respecte-la.

Les faits
- Toute affirmation chiffrée vient du dossier. N'invente aucun chiffre, aucune partie, aucune variante. Tu peux faire des calculs simples à partir des chiffres du dossier, en restant exact.
- Tu n'as pas les positions : ne commente un coup qu'avec ce que le dossier en dit.
- Quand un constat repose sur peu de parties (moins d'une vingtaine), dis-le.
- Les liens de parties viennent du dossier, aucun autre lien.

Ce qui fait un bon bilan
- Les priorités sont classées par le nombre de parties ou de points qu'elles coûtent dans cette cadence.
- Relie les constats qui ont une cause commune (par exemple des positions gagnantes perdues au temps relèvent de la gestion de la pendule).
- Le dossier résume aussi les autres cadences du joueur : compare-les quand c'est éclairant, sans t'y étendre.
- Les entraînements se font dans l'appli, sur des exercices tirés des propres erreurs du joueur. Propose uniquement les entraînements de la liste ci-dessous, par leur identifiant. Ce qui ne se travaille pas par des exercices (gestion de la pendule, routine de vérification pendant la partie) se travaille en jouant : donne alors un conseil de jeu précis, sans entraînement.
- Les objectifs sont mesurables avec les indicateurs du dossier, pour que le prochain bilan vérifie les progrès.
- Si le dossier contient un bilan précédent, dis d'abord si ses objectifs ont été tenus, chiffres à l'appui.

Ton : bienveillant et franc, sans flatterie ni dramatisation.

Entraînements de l'appli (identifiant : contenu) :
""" + "\n".join(f"- {k} : {v}" for k, v in TRAININGS.items())

_TRAINING = {"anyOf": [{"type": "string", "enum": list(TRAININGS)}, {"type": "null"}],
             "description": "Identifiant d'un entraînement de l'appli, ou null."}
_SHORT = lambda n, what="": {"type": "string", "description": f"{what} {n} mots au plus.".strip()}

SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": ["portrait", "progres", "points_forts", "priorites", "plan", "objectifs"],
    "properties": {
        "portrait": _SHORT(45, "2 phrases : ce qui coûte le plus de parties dans cette cadence."),
        "progres": {"type": ["string", "null"],
                    "description": "Objectifs du bilan précédent tenus ou non, chiffres à l'appui, 40 mots au plus ; "
                                   "null sans bilan précédent."},
        "points_forts": {"type": "array", "description": "Exactement 2 points forts chiffrés.", "items": {
            "type": "object", "additionalProperties": False, "required": ["titre", "detail"],
            "properties": {"titre": _SHORT(8), "detail": _SHORT(25, "1 phrase chiffrée.")}}},
        "priorites": {"type": "array", "description": "Exactement 3 priorités, de la plus coûteuse à la moins coûteuse.",
                      "items": {
            "type": "object", "additionalProperties": False,
            "required": ["titre", "constat", "action", "entrainement", "exemple"],
            "properties": {
                "titre": _SHORT(8),
                "constat": _SHORT(35, "1 phrase chiffrée : le problème et ce qu'il coûte."),
                "action": _SHORT(30, "1 action concrète à appliquer en partie."),
                "entrainement": _TRAINING,
                "exemple": {"type": ["object", "null"], "additionalProperties": False,
                            "required": ["lien", "explication"],
                            "description": "Une partie du dossier qui illustre le problème, ou null.",
                            "properties": {"lien": {"type": "string"}, "explication": _SHORT(25, "1 phrase.")}}}}},
        "plan": {"type": "array", "description": "Plan sur 2 semaines, 20 à 30 minutes par jour en tout, 3 à 5 lignes.",
                 "items": {
            "type": "object", "additionalProperties": False, "required": ["quand", "activite", "minutes", "entrainement"],
            "properties": {"quand": _SHORT(5, "Ex. « Chaque jour », « Lundi, mercredi, vendredi »."),
                           "activite": _SHORT(15), "minutes": {"type": "integer"}, "entrainement": _TRAINING}}},
        "objectifs": {"type": "array", "description": "2 à 3 objectifs mesurables pour le prochain bilan.", "items": {
            "type": "object", "additionalProperties": False, "required": ["indicateur", "actuel", "cible"],
            "properties": {"indicateur": _SHORT(8), "actuel": _SHORT(6), "cible": _SHORT(6)}}},
    },
}


def user_message(dossier):
    return ("Voici le dossier, au format JSON :\n<dossier>\n"
            + json.dumps(dossier, ensure_ascii=False, indent=1)
            + f"\n</dossier>\n\nRédige le bilan {dossier['cadence']['cadence']} de ce joueur.")


PRICE = {"input": 4.0, "output": 20.0, "cache_read": 0.20, "cache_write": 5.0}   # $ / million de jetons (Opus 5.5)


def _links(dossier):
    c = dossier["cadence"]
    return {x["partie"] for x in c["gaffes_les_plus_couteuses"] + c["victoires_laissees_filer"]}


def check(dossier, b):
    """Liens de parties hors dossier : la réponse est rejetée."""
    allowed = _links(dossier)
    return [p["exemple"]["lien"] for p in b["priorites"] if p["exemple"] and p["exemple"]["lien"] not in allowed]


def generate(dossier, api_key, effort="high", raw_path=None):
    """Bilan (dict conforme à SCHEMA) et coût en $. Refus et liens inventés lèvent une exception."""
    import anthropic
    client = anthropic.Anthropic(api_key=api_key)
    with client.beta.messages.stream(
        model=MODEL,
        max_tokens=32000,
        betas=["server-side-fallback-2026-07-01"],
        fallbacks="default",
        system=SYSTEM,
        output_config={"effort": effort, "format": {"type": "json_schema", "schema": SCHEMA}},
        messages=[{"role": "user", "content": user_message(dossier)}],
    ) as stream:
        msg = stream.get_final_message()
    if msg.stop_reason == "refusal":
        raise RuntimeError(f"bilan refusé ({msg.stop_details})")
    if msg.stop_reason == "max_tokens":
        raise RuntimeError("bilan tronqué (max_tokens)")
    text = next(b.text for b in msg.content if b.type == "text")
    if raw_path:                       # réponse brute gardée avant tout contrôle
        raw_path.write_text(text)
    b = json.loads(text)
    bad = check(dossier, b)
    if bad:
        raise RuntimeError(f"liens hors dossier : {bad}")
    u = msg.usage
    cost = (u.input_tokens * PRICE["input"] + u.output_tokens * PRICE["output"]
            + (u.cache_read_input_tokens or 0) * PRICE["cache_read"]
            + (u.cache_creation_input_tokens or 0) * PRICE["cache_write"]) / 1e6
    return b, {"model": msg.model, "input_tokens": u.input_tokens, "output_tokens": u.output_tokens,
               "cost_usd": round(cost, 4), "message_id": msg.id}


# --------------------------------------------------------------------------------------------
# Quand générer, et enregistrement
# --------------------------------------------------------------------------------------------
def api_key(cfg):
    """Clé : variable ANTHROPIC_API_KEY (job Cloud Run, via Secret Manager), sinon secrets/anthropic-api-key."""
    import os
    if os.environ.get("ANTHROPIC_API_KEY"):
        return os.environ["ANTHROPIC_API_KEY"].strip()
    f = cfg["root"] / "secrets" / "anthropic-api-key"
    return f.read_text().strip() if f.exists() else None


def due(cfg, con, tc):
    """(faut-il un nouveau bilan, nombre de parties, bilan précédent ou None)."""
    app = cfg["app"]
    n = con.execute("SELECT COUNT(*) FROM games WHERE time_class = ?", (tc,)).fetchone()[0]
    if n < app["bilan_min_games"]:
        return False, n, None
    r = con.execute("SELECT created, games, bilan FROM bilans WHERE tc = ? ORDER BY created DESC LIMIT 1", (tc,)).fetchone()
    if not r:
        return True, n, None
    new = n - r["games"]
    age = (dt.datetime.now(dt.timezone.utc) - dt.datetime.fromisoformat(r["created"])).days
    prev = json.loads(r["bilan"])
    previous = {"date": r["created"][:10], "parties_a_cette_date": r["games"], "objectifs": prev["objectifs"]}
    return new >= app["bilan_new_games"] or (age >= app["bilan_days"] and new > 0), n, previous


def run(cfg, con):
    """Génère les bilans dus pour les cadences publiées. Renvoie les cadences mises à jour."""
    key = api_key(cfg)
    if not key:
        print("Bilan IA : pas de clé API, ignoré")
        return []
    done = []
    for tc in cfg["time_classes"]:
        go, n, previous = due(cfg, con, tc)
        if not go:
            continue
        try:
            b, meta = generate(build_dossier(cfg, con, tc, previous), key)
        except Exception as e:                      # un bilan raté ne bloque pas le reste
            print(f"Bilan IA {tc} : échec ({e})")
            continue
        con.execute("INSERT INTO bilans VALUES (?, ?, ?, ?, ?)",
                    (tc, dt.datetime.now(dt.timezone.utc).isoformat(), n, json.dumps(b, ensure_ascii=False),
                     json.dumps(meta)))
        con.commit()
        print(f"Bilan IA {tc} : {meta['output_tokens']} jetons produits, {meta['cost_usd']} $")
        done.append(tc)
    return done
