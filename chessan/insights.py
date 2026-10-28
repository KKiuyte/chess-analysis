"""Diagnostic et conseils d'amélioration, calculés sur toute la période d'une cadence."""
import statistics as st
from collections import Counter, defaultdict

import chess

PIECE_VALUE = {chess.PAWN: 1, chess.KNIGHT: 3, chess.BISHOP: 3, chess.ROOK: 5, chess.QUEEN: 9, chess.KING: 100}
SCORE = {"win": 1, "draw": 0.5, "loss": 0}
MATE = 9000  # au-delà, l'évaluation est un mat (mate_score = 10 000)

BLUNDER_KINDS = {
    "hanging": "Matériel laissé en prise",
    "missed_capture": "Capture gagnante ratée",
    "mate_allowed": "Mat concédé",
    "mate_missed": "Mat raté",
    "other": "Autre tactique ou plan",
}
PUZZLES = {
    "hanging": ("Exercices « pièce en prise » sur Lichess", "https://lichess.org/training/hangingPiece"),
    "missed_capture": ("Exercices « pièce en prise » sur Lichess", "https://lichess.org/training/hangingPiece"),
    "mate_allowed": ("Exercices « mat en 2 » sur Lichess", "https://lichess.org/training/mateIn2"),
    "mate_missed": ("Exercices « mat en 1 » sur Lichess", "https://lichess.org/training/mateIn1"),
    "other": ("Exercices « fourchette » sur Lichess", "https://lichess.org/training/fork"),
}


def _material_hung(board_after, me):
    """Plus gros gain matériel immédiat offert à l'adversaire (échange simple), en points."""
    best = 0
    for mv in board_after.legal_moves:
        if not board_after.is_capture(mv) or board_after.is_en_passant(mv):
            continue
        victim = PIECE_VALUE[board_after.piece_type_at(mv.to_square)]
        attacker = PIECE_VALUE[board_after.piece_type_at(mv.from_square)]
        b = board_after.copy(stack=False)
        b.push(mv)
        gain = victim - attacker if b.is_attacked_by(me, mv.to_square) else victim
        best = max(best, gain)
    return best


def blunder_kind(fen_before, uci, best_uci, cp_before, cp_after):
    """Type de gaffe, par heuristique sur la position (pas de moteur)."""
    if cp_after <= -MATE:
        return "mate_allowed"
    if cp_before >= MATE:
        return "mate_missed"
    board = chess.Board(fen_before)
    me = board.turn
    played = chess.Move.from_uci(uci)
    best = chess.Move.from_uci(best_uci) if best_uci else None
    after = board.copy(stack=False)
    after.push(played)
    if _material_hung(after, me) >= 2:
        return "hanging"
    if best and board.is_capture(best) and not board.is_capture(played):
        return "missed_capture"
    return "other"


def _pl(n, word, plural=None):
    return f"{n} {word if n < 2 else (plural or word + 's')}"


def _pct(x):
    return f"{x * 100:.0f} %"


def _n(x):
    return f"{x:.1f}".replace(".", ",")


def _parse_tc(tc):
    if not tc or "/" in tc:
        return None, 0
    base, _, inc = tc.partition("+")
    return int(base), int(inc or 0)


def compute(cfg, con, tc, games):
    """`games` : lignes de la table games pour la cadence. Renvoie la liste des cartes du diagnostic."""
    cls = cfg["classification"]
    opening_moves = cfg["phases"]["opening_moves"]
    by_id = {g["id"]: g for g in games}
    if not games:
        return []

    mine, clocks = defaultdict(list), defaultdict(dict)
    for r in con.execute(
            """SELECT m.* FROM moves m JOIN games g ON g.id = m.game_id
               WHERE g.time_class = ? ORDER BY m.game_id, m.ply""", (tc,)):
        clocks[r["game_id"]][r["ply"]] = r["clock"]
        if r["is_mine"] and r["win_before"] is not None:
            mine[r["game_id"]].append(dict(r))

    counted = []
    for gid, ms in mine.items():
        for m in ms:
            wb, wa = m["win_before"], m["win_after"]
            m["loss"] = max(0.0, wb - wa)
            m["ignored"] = wb < cls["lost_below"] or (wb > cls["won_above"] and wa > cls["still_won_above"])
            if not m["ignored"]:
                counted.append(m)
    blunders = [m for m in counted if m["loss"] >= cls["blunder"]]
    for m in blunders:
        m["kind"] = blunder_kind(m["fen_before"], m["uci"], m["best_uci"], m["cp_before"], m["cp_after"])

    cards = []
    n_games = len(games)
    losses = [g for g in games if g["result"] == "loss"]
    blunder_rate = lambda ms: sum(m["loss"] >= cls["blunder"] for m in ms) / len(ms) * 100 if ms else 0

    # --- 1. Pendule ---------------------------------------------------------------------------
    base, inc = _parse_tc(Counter(g["time_control"] for g in games).most_common(1)[0][0])
    has_clock = base and sum(any(v is not None for v in clocks[g["id"]].values()) for g in games) > n_games / 2
    if has_clock and losses:
        timeouts = [g for g in losses if g["result_detail"] == "timeout"]
        last_win = {gid: ms[-1]["win_after"] for gid, ms in mine.items() if ms}
        to_better = [g for g in timeouts if last_win.get(g["id"], 0) > 50]
        to_winning = [g for g in timeouts if last_win.get(g["id"], 0) > 80]
        share = len(timeouts) / len(losses)

        def clock_at(g, move_no):
            mp = 2 * (move_no - 1) + (0 if g["color"] == "w" else 1)
            op = mp + 1 if g["color"] == "w" else mp - 1
            return clocks[g["id"]].get(mp), clocks[g["id"]].get(op)

        gaps = {}
        for k in (10, 20, 30):
            pairs = [clock_at(g, k) for g in games]
            pairs = [(a, b) for a, b in pairs if a is not None and b is not None]
            if len(pairs) >= 20:
                gaps[k] = (st.median(a for a, _ in pairs), st.median(a - b for a, b in pairs))

        spent = defaultdict(list)
        for gid, ms in mine.items():
            for m in ms:
                prev = clocks[gid].get(m["ply"] - 2)
                if prev is not None and m["clock"] is not None:
                    spent[m["phase"]].append(prev - m["clock"] + inc)
        # tranches proportionnelles à la cadence : 3+0 → 30 s / 1 min / 2 min, 1+0 → 10 s / 20 s / 40 s
        cuts = [base / 6, base / 3, base * 2 / 3]
        dur = lambda x: f"{x / 60:g} min" if x >= 60 and x % 60 == 0 else f"{x:.0f} s"
        buckets = [(f"Moins de {dur(cuts[0])}", 0, cuts[0]), (f"{dur(cuts[0])} à {dur(cuts[1])}", cuts[0], cuts[1]),
                   (f"{dur(cuts[1])} à {dur(cuts[2])}", cuts[1], cuts[2]), (f"Plus de {dur(cuts[2])}", cuts[2], 1e9)]
        bars = []
        for label, lo, hi in buckets:
            ms = [m for m in counted if m["clock"] is not None and lo <= m["clock"] < hi]
            if len(ms) >= 50:
                bars.append({"label": label, "value": round(blunder_rate(ms), 1), "text": f"{_n(blunder_rate(ms))} gaffes / 100 coups"})

        facts = [f"{len(timeouts)} de tes {len(losses)} défaites ({_pct(share)}) sont des pertes au temps."]
        if to_better:
            facts.append(f"Dans {len(to_better)} d'entre elles tu étais mieux selon Stockfish, et dans {len(to_winning)} "
                         f"tu étais même nettement gagnant (plus de 80 % de gain).")
        if gaps:
            k0 = min(gaps)
            used = base - gaps[k0][0]
            gap_txt = " ; ".join(f"coup {k} : {abs(d):.0f} s {'de retard' if d < 0 else 'd’avance'}" for k, (_, d) in gaps.items())
            facts.append(f"Au coup {k0}, tu as déjà consommé {used:.0f} s en moyenne. Écart de pendule avec ton adversaire "
                         f"(médiane) : {gap_txt}.")
        if spent:
            facts.append("Temps médian par coup : " + ", ".join(
                f"{lbl} {_n(st.median(spent[p]))} s" for p, lbl in
                (("opening", "ouverture"), ("middlegame", "milieu"), ("endgame", "finale")) if spent[p]) + ".")
        if len(bars) >= 2 and bars[0]["value"] > bars[-1]["value"] * 1.5:
            facts.append(f"Tu gaffes {_n(bars[0]['value'] / bars[-1]['value'])} fois plus souvent avec moins de "
                         f"{dur(cuts[0])} qu'avec plus de {dur(cuts[2])} à la pendule.")

        actions = []
        if gaps:
            target = round(base / 9 / 5) * 5 or 10
            actions.append(f"Joue tes {min(gaps)} premiers coups en {target} s maximum : ce sont des coups que tu connais, "
                           f"ils ne doivent pas te coûter du temps de réflexion.")
        if to_winning:
            actions.append("Quand tu es nettement gagnant, échange les pièces et joue des coups simples et rapides. "
                           "Une position gagnée se perd surtout à la pendule.")
        actions.append(f"Sous {dur(cuts[0])}, joue le premier coup sûr que tu vois (pas de pièce en prise, pas d'échec adverse "
                       "dangereux) au lieu de chercher le meilleur.")
        if inc == 0:
            sugg = 1 if base <= 60 else 2 if base <= 300 else 5
            actions.append(f"Essaie quelques semaines en {base // 60}+{sugg} : l'incrément de {sugg} s par coup supprime "
                           f"une bonne partie des pertes au temps et laisse ton niveau de jeu s'exprimer.")
        level = "priority" if share >= 0.25 else ("info" if share >= 0.1 else "good")
        title = ("La pendule te coûte beaucoup de parties" if level == "priority"
                 else "Tu gères plutôt bien ta pendule" if level == "good" else "La pendule te coûte quelques parties")
        cards.append({"id": "clock", "level": level, "title": title,
                      "metric": {"value": _pct(share), "label": "des défaites au temps"},
                      "facts": facts, "bars": bars, "barsTitle": "Gaffes pour 100 coups selon le temps qu'il te reste",
                      "actions": actions if level != "good" else actions[-1:], "links": [],
                      "weight": len(to_better) * 2 + len(timeouts)})

    # --- 2. Types de gaffes -------------------------------------------------------------------
    if blunders:
        kinds = Counter(m["kind"] for m in blunders)
        top, top_n = kinds.most_common(1)[0]
        per_game = len(blunders) / len(mine)
        bars = [{"label": BLUNDER_KINDS[k], "value": round(v / len(blunders) * 100), "text": f"{v} ({_pct(v / len(blunders))})"}
                for k, v in kinds.most_common()]
        facts = [f"{len(blunders)} gaffes en {len(mine)} parties analysées, soit {_n(per_game)} par partie.",
                 f"Type le plus fréquent : {BLUNDER_KINDS[top].lower()} ({_pct(top_n / len(blunders))} des gaffes)."]
        mates = kinds["mate_allowed"] + kinds["mate_missed"]
        if mates:
            facts.append(f"{_pl(kinds['mate_allowed'], 'mat concédé', 'mats concédés')} et "
                         f"{_pl(kinds['mate_missed'], 'mat raté', 'mats ratés')}.")
        advice = {
            "hanging": "Avant de lâcher ta pièce, fais un contrôle en 2 secondes : la pièce que je bouge est-elle défendue "
                       "sur sa nouvelle case ? Et celle qu'elle protégeait, l'est-elle encore ?",
            "missed_capture": "Après chaque coup adverse, demande-toi d'abord ce qu'il vient de laisser sans défense, "
                              "avant de penser à ton propre plan.",
            "mate_allowed": "Avant chaque coup, regarde tous les échecs que l'adversaire pourra donner ensuite, "
                            "surtout près de ton roi.",
            "mate_missed": "Commence chaque réflexion par les échecs que tu peux donner : un mat se cache souvent derrière.",
            "other": "Cherche dans l'ordre les échecs, les captures puis les menaces (adverses et les tiennes) avant de jouer.",
        }
        actions = [advice[top]]
        second = [k for k, _ in kinds.most_common() if k not in (top, "other")][:1]
        if second:
            actions.append(advice[second[0]])
        actions.append("10 minutes d'exercices tactiques par jour sur le thème ci-dessous, en visant la justesse plutôt "
                       "que la vitesse.")
        label, url = PUZZLES[top]
        cards.append({"id": "blunders", "level": "priority" if per_game >= 1 else "info",
                      "title": {"hanging": "Tu laisses trop souvent du matériel en prise",
                                "missed_capture": "Tu passes à côté de captures gagnantes",
                                "mate_allowed": "Tu concèdes des mats évitables",
                                "mate_missed": "Tu rates des mats",
                                "other": "Tes gaffes viennent surtout de tactiques plus fines"}[top],
                      "metric": {"value": _n(per_game), "label": "gaffes par partie"},
                      "facts": facts, "bars": bars, "barsTitle": "Répartition des gaffes par type",
                      "actions": actions, "links": [{"label": label, "url": url}],
                      "note": "Type détecté automatiquement : « en prise » = après ton coup, l'adversaire peut gagner au "
                              "moins 2 points de matériel par une capture simple.",
                      "weight": len(blunders) / 5})

    # --- 3. Phase la plus fragile -------------------------------------------------------------
    phase_ms = {p: [m for m in counted if m["phase"] == p] for p in ("opening", "middlegame", "endgame")}
    rates = {p: blunder_rate(ms) for p, ms in phase_ms.items() if len(ms) >= 100}
    if len(rates) >= 2:
        worst = max(rates, key=rates.get)
        best = min(rates, key=rates.get)
        ratio = rates[worst] / rates[best] if rates[best] else 0
        lbl = {"opening": "l'ouverture", "middlegame": "le milieu de partie", "endgame": "la finale"}
        actions = {
            "opening": ["Revois les 8 à 10 premiers coups de tes deux ouvertures principales jusqu'à les jouer sans réfléchir.",
                        "Après chaque partie perdue, regarde à quel coup tu es sorti de ta préparation."],
            "middlegame": ["C'est la phase où les pièces se croisent le plus : applique ta routine échecs, captures, menaces "
                           "à chaque coup, même quand la position semble calme.",
                           "Quand tu as un avantage, cherche à échanger des pièces pour arriver vite en finale, "
                           "où tu fais moins d'erreurs."],
            "endgame": ["Travaille les finales de base (roi et pion, tours) dans la section Pratique de Lichess.",
                        "En finale, active ton roi tôt : c'est une pièce forte quand les dames ont disparu."],
        }[worst]
        links = [{"label": "Finales de base sur Lichess", "url": "https://lichess.org/practice"}] if worst == "endgame" else []
        bars = [{"label": {"opening": "Ouverture", "middlegame": "Milieu", "endgame": "Finale"}[p],
                 "value": round(v, 1), "text": f"{_n(v)} gaffes / 100 coups"} for p, v in rates.items()]
        spread = ratio < 1.3
        if spread:
            actions = actions[:1]
        cards.append({"id": "phase", "level": "priority" if ratio >= 1.8 else "good" if spread else "info",
                      "title": "Tes gaffes sont réparties sur toutes les phases" if spread
                               else f"Tu gaffes surtout dans {lbl[worst]}",
                      "metric": {"value": f"×{_n(ratio)}", "label": f"par rapport à {lbl[best]}"},
                      "facts": [f"{_n(rates[worst])} gaffes pour 100 coups dans {lbl[worst]}, contre {_n(rates[best])} dans {lbl[best]}."],
                      "bars": bars, "barsTitle": "Gaffes pour 100 coups par phase",
                      "actions": actions, "links": links, "weight": ratio * 20})

    # --- 4. Transformer l'avantage ------------------------------------------------------------
    had = [gid for gid, ms in mine.items() if max(m["win_before"] for m in ms) >= 85]
    blown = [gid for gid in had if by_id[gid]["result"] != "win"]
    if len(had) >= 10:
        how_txt = {"timeout": "perdues au temps", "checkmated": "perdues par mat", "resigned": "perdues par abandon"}
        how = Counter("nulles" if by_id[gid]["result"] == "draw" else how_txt.get(by_id[gid]["result_detail"], "perdues autrement")
                      for gid in blown)
        parts = [f"{v} {k if v > 1 else k.replace('perdues', 'perdue').replace('nulles', 'nulle')}"
                 for k, v in how.most_common()]
        lost_pos = [gid for gid, ms in mine.items() if min(m["win_before"] for m in ms) <= 15]
        saved = [gid for gid in lost_pos if by_id[gid]["result"] == "win"]
        facts = [f"Tu as eu une position nettement gagnante (85 % ou plus) dans {len(had)} parties, "
                 f"et tu n'en as gagné que {len(had) - len(blown)}.",
                 f"Les {len(blown)} autres se sont terminées ainsi : {', '.join(parts)}."]
        if lost_pos:
            facts.append(f"À l'inverse, tu as gagné {len(saved)} des {len(lost_pos)} parties où tu étais perdu (15 % ou moins) : "
                         f"tes adversaires gaffent aussi, ne lâche jamais trop tôt.")
        share = len(blown) / len(had)
        cards.append({"id": "convert", "level": "priority" if share >= 0.25 else "info",
                      "title": "Tu laisses filer des parties gagnées" if share >= 0.15 else "Tu transformes bien tes avantages",
                      "metric": {"value": _pct(share), "label": "des positions gagnantes non converties"},
                      "facts": facts, "bars": [],
                      "actions": ["Avec une pièce d'avance, échange les autres pièces : moins il en reste, moins l'adversaire "
                                  "a de ressources.",
                                  "Quand tu gagnes, regarde avant chaque coup les échecs et les captures que l'adversaire "
                                  "peut faire : ses seules chances sont tactiques.",
                                  ] + (["Garde de l'avance à la pendule : une position gagnée sans temps reste une "
                                        "partie à risque."] if has_clock else []),
                      "links": [], "weight": len(blown)})

    # --- 5. Ouvertures : sortie d'ouverture vs résultat ---------------------------------------
    out_win = {}
    for gid, ms in mine.items():
        after = [m for m in ms if m["move_no"] > opening_moves]
        if after:
            out_win[gid] = after[0]["win_before"]
    min_games = cfg["time_classes"][tc].get("min_games", cfg["openings"]["min_games"])
    low_score = cfg["openings"]["low_score"]
    if out_win:
        fam = defaultdict(list)
        for gid, w in out_win.items():
            g = by_id[gid]
            fam[(g["color"], g["opening_family"])].append((w, SCORE[g["result"]]))
        stats = [(c, f, len(v), st.mean(a for a, _ in v), st.mean(b for _, b in v) * 100)
                 for (c, f), v in fam.items() if len(v) >= min_games]
        coul = {"w": "blancs", "b": "noirs"}
        bad_open = sorted([s for s in stats if s[3] < 45], key=lambda s: s[3])
        bad_after = sorted([s for s in stats if s[3] >= 55 and s[4] < low_score], key=lambda s: s[4])
        avg = st.mean(out_win.values())
        facts = [f"Après {opening_moves} coups, tu as en moyenne {avg:.0f} % de chances de gain : "
                 + ("tes ouvertures te donnent plutôt de bonnes positions." if avg >= 52 else
                    "tu sors de l'ouverture à peu près à égalité." if avg >= 45 else
                    "tu sors souvent de l'ouverture en position inférieure.")]
        actions = []
        for c, f, n, w, s in bad_open[:3]:
            facts.append(f"Avec les {coul[c]}, en {f} ({n} parties), tu sors de l'ouverture à {w:.0f} % seulement "
                         f"(score final {s:.0f} %).")
        if bad_open:
            c, f, *_ = bad_open[0]
            actions.append(f"Revois tes parties en {f} avec les {coul[c]} : choisis un système simple pour les 6 à 8 "
                           f"premiers coups et tiens-t'y.")
        for c, f, n, w, s in bad_after[:3]:
            facts.append(f"Avec les {coul[c]}, en {f} ({n} parties), tu sors bien de l'ouverture ({w:.0f} %) mais ton score "
                         f"final n'est que de {s:.0f} % : le problème vient de la suite, pas de l'ouverture.")
        if bad_after:
            c, f, *_ = bad_after[0]
            actions.append(f"Rejoue tes défaites en {f} avec les {coul[c]} à partir du coup {opening_moves} : "
                           f"cherche si le même type de position revient (plan, structure de pions).")
        if not actions:
            actions.append("Inutile de changer de répertoire : concentre ton travail sur le milieu de partie.")
        cards.append({"id": "openings", "level": "info" if bad_open else "good",
                      "title": "Certaines ouvertures te mettent en difficulté" if bad_open else "Tes ouvertures tiennent la route",
                      "metric": {"value": f"{avg:.0f} %", "label": f"de gain moyen après {opening_moves} coups"},
                      "facts": facts, "bars": [], "actions": actions, "links": [],
                      "weight": 10 + 5 * len(bad_open)})

    # --- 6. Enchaînement des parties (tilt, fatigue) ------------------------------------------
    seq = sorted(games, key=lambda g: g["end_time"])
    after = defaultdict(list)
    sessions, cur = [], [seq[0]]
    for a, b in zip(seq, seq[1:]):
        if b["end_time"] - a["end_time"] < 1800:
            after[a["result"]].append(SCORE[b["result"]])
            cur.append(b)
        else:
            sessions.append(cur)
            cur = [b]
    sessions.append(cur)
    if len(after["loss"]) >= 30 and len(after["win"]) >= 30:
        s_loss, s_win = st.mean(after["loss"]) * 100, st.mean(after["win"]) * 100
        overall = st.mean(SCORE[g["result"]] for g in games) * 100
        late = [SCORE[g["result"]] for s in sessions for g in s[4:]]
        early = [SCORE[g["result"]] for s in sessions for g in s[:1]]
        s_late = st.mean(late) * 100 if len(late) >= 30 else None
        s_early = st.mean(early) * 100
        tilt = s_loss < overall - 6
        fatigue = s_late is not None and s_late < s_early - 8
        facts = [f"Score juste après une défaite : {s_loss:.0f} % ; juste après une victoire : {s_win:.0f} % "
                 f"(moyenne générale {overall:.0f} %)."]
        if s_late is not None:
            facts.append(f"Score sur la 1re partie d'une session : {s_early:.0f} % ; à partir de la 5e : {s_late:.0f} %.")
        actions = []
        if tilt:
            actions.append("Après deux défaites d'affilée, fais une pause de 15 minutes avant de relancer une partie.")
        if fatigue:
            actions.append("Limite tes sessions à 4 ou 5 parties : ton score baisse nettement au-delà.")
        if not actions:
            actions.append("Pas besoin de changer tes habitudes de jeu : enchaîner les parties ne te fait pas baisser.")
        cards.append({"id": "tilt", "level": "info" if (tilt or fatigue) else "good",
                      "title": ("Les défaites te déstabilisent" if tilt else "Tes longues sessions te fatiguent" if fatigue
                                else "Pas de signe de tilt ni de fatigue"),
                      "metric": {"value": f"{s_loss:.0f} %", "label": "de score après une défaite"},
                      "facts": facts, "bars": [], "actions": actions, "links": [], "weight": 5 if (tilt or fatigue) else 0})

    if n_games < 50:
        for c in cards:
            c["note"] = (c.get("note", "") + f" Seulement {n_games} parties : tendance à confirmer.").strip()
    order = {"priority": 0, "info": 1, "good": 2}
    cards.sort(key=lambda c: (order[c["level"]], -c["weight"]))
    for c in cards:
        del c["weight"]
    return cards
