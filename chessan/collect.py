"""Collecte incrémentale des parties via l'API publique chess.com, puis ingestion SQLite."""
import datetime as dt
import io
import json
import time
import urllib.error
import urllib.request

import chess.pgn

from .openings import split_opening
from .phases import phase

API = "https://api.chess.com/pub/player/{user}/games/archives"
DRAW_CODES = {"agreed", "repetition", "stalemate", "insufficient", "50move", "timevsinsufficient"}


def fetch_json(url, user_agent, max_tries=6):
    """GET JSON avec retry/backoff sur 429 et erreurs serveur."""
    delay = 2.0
    for attempt in range(1, max_tries + 1):
        req = urllib.request.Request(url, headers={"User-Agent": user_agent, "Accept": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                return json.load(r)
        except urllib.error.HTTPError as e:
            if e.code != 429 and e.code < 500:
                raise
            wait = float(e.headers.get("Retry-After") or delay)
            print(f"  HTTP {e.code} sur {url}, nouvel essai dans {wait:.0f} s ({attempt}/{max_tries})")
        except (urllib.error.URLError, TimeoutError) as e:
            wait = delay
            print(f"  erreur réseau ({e}), nouvel essai dans {wait:.0f} s ({attempt}/{max_tries})")
        time.sleep(wait)
        delay = min(delay * 2, 120)
    raise RuntimeError(f"échec après {max_tries} essais : {url}")


def month_key(archive_url):
    y, m = archive_url.rstrip("/").split("/")[-2:]
    return f"{y}-{m}"


def needs_fetch(con, month, raw_path):
    """Un mois est re-téléchargé s'il n'est pas en cache ou s'il a été récupéré avant sa fin."""
    if not raw_path.exists():
        return True
    row = con.execute("SELECT fetched_at FROM archives WHERE month = ?", (month,)).fetchone()
    if not row:
        return True
    y, m = map(int, month.split("-"))
    month_end = dt.datetime(y + (m == 12), m % 12 + 1, 1, tzinfo=dt.timezone.utc)
    return dt.datetime.fromisoformat(row["fetched_at"]) < month_end


def collect(cfg, con):
    user = cfg["username"].lower()
    if not cfg.get("contact"):
        raise SystemExit("Contact manquant : définir CHESS_CONTACT ou `contact` dans config.local.toml "
                         "(chess.com demande un moyen de contact dans le User-Agent).")
    ua = f"chess-analysis/1.0 (personal stats for {user}; contact: {cfg['contact']})"
    since_month = cfg["since"].strftime("%Y-%m")
    cfg["raw_dir"].mkdir(parents=True, exist_ok=True)

    archives = fetch_json(API.format(user=user), ua)["archives"]
    archives = [a for a in archives if month_key(a) >= since_month]
    print(f"{len(archives)} archive(s) mensuelle(s) depuis {since_month}")

    for url in archives:
        month = month_key(url)
        raw_path = cfg["raw_dir"] / f"{month}.json"
        if not needs_fetch(con, month, raw_path):
            print(f"  {month} : en cache")
            continue
        data = fetch_json(url, ua)
        raw_path.write_text(json.dumps(data))
        con.execute(
            "INSERT OR REPLACE INTO archives VALUES (?, ?, ?)",
            (month, dt.datetime.now(dt.timezone.utc).isoformat(), len(data.get("games", []))),
        )
        con.commit()
        print(f"  {month} : {len(data.get('games', []))} parties téléchargées")
        time.sleep(1)  # requêtes séquentielles, sans marteler l'API

    return [cfg["raw_dir"] / f"{month_key(a)}.json" for a in archives]


def _result(code):
    if code == "win":
        return "win"
    return "draw" if code in DRAW_CODES else "loss"


def ingest(cfg, con, raw_files):
    """Insère les nouvelles parties et leurs coups ; met à jour ouvertures et phases."""
    user = cfg["username"].lower()
    since_ts = dt.datetime.combine(cfg["since"], dt.time(), dt.timezone.utc).timestamp()
    tcs = set(cfg["time_classes"])
    flt = cfg["filters"]
    ph = cfg["phases"]
    known = {r[0] for r in con.execute("SELECT id FROM games")}
    added = 0

    for path in raw_files:
        for g in json.loads(path.read_text()).get("games", []):
            if g.get("time_class") not in tcs or g.get("end_time", 0) < since_ts:
                continue
            if flt.get("rated_only") and not g.get("rated"):
                continue
            if flt.get("standard_only") and g.get("rules") != "chess":
                continue
            if not g.get("pgn"):
                continue
            color = "w" if g["white"]["username"].lower() == user else "b"
            me, opp = (g["white"], g["black"]) if color == "w" else (g["black"], g["white"])
            pgn = chess.pgn.read_game(io.StringIO(g["pgn"]))
            if pgn is None:
                continue
            eco_url = pgn.headers.get("ECOUrl", "")
            eco = pgn.headers.get("ECO", "")
            family, variant = split_opening(eco_url, eco)
            gid = g.get("uuid") or g["url"]
            end = dt.datetime.fromtimestamp(g["end_time"], dt.timezone.utc)
            mainline = list(pgn.mainline_moves())

            con.execute(
                """INSERT INTO games VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                   ON CONFLICT(id) DO UPDATE SET opening_family = excluded.opening_family,
                                                 opening_variant = excluded.opening_variant""",
                (gid, g["url"], g["end_time"], end.date().isoformat(), end.strftime("%Y-%m"),
                 g["time_class"], g.get("time_control"), int(bool(g.get("rated"))), g.get("rules"),
                 color, opp["username"], me.get("rating"), opp.get("rating"),
                 _result(me["result"]), me["result"], eco, eco_url, family, variant,
                 g["pgn"], len(mainline)),
            )
            if gid in known:
                continue

            board = pgn.board()
            rows = []
            for ply, node in enumerate(pgn.mainline()):
                move = node.move
                mover = "w" if board.turn == chess.WHITE else "b"
                rows.append((gid, ply, board.fullmove_number, mover, int(mover == color),
                             board.san(move), move.uci(), board.fen(),
                             phase(board, board.fullmove_number, ph["opening_moves"], ph["endgame_material"]),
                             node.clock()))
                board.push(move)
            con.executemany(
                "INSERT INTO moves (game_id, ply, move_no, color, is_mine, san, uci, fen_before, phase, clock) "
                "VALUES (?,?,?,?,?,?,?,?,?,?)", rows)
            known.add(gid)
            added += 1
    con.commit()
    backfill_clocks(con)
    total = con.execute("SELECT COUNT(*) FROM games").fetchone()[0]
    print(f"{added} nouvelle(s) partie(s) ingérée(s), {total} en base")


def backfill_clocks(con):
    """Renseigne la pendule des parties ingérées avant l'ajout de la colonne `clock`."""
    ids = [r[0] for r in con.execute(
        "SELECT game_id FROM moves GROUP BY game_id HAVING COUNT(clock) = 0")]
    filled = 0
    for gid in ids:
        pgn = chess.pgn.read_game(io.StringIO(
            con.execute("SELECT pgn FROM games WHERE id = ?", (gid,)).fetchone()[0]))
        clocks = [(node.clock(), gid, ply) for ply, node in enumerate(pgn.mainline())]
        if any(c is not None for c, _, _ in clocks):
            con.executemany("UPDATE moves SET clock = ? WHERE game_id = ? AND ply = ?", clocks)
            filled += 1
    con.commit()
    if filled:
        print(f"Pendule renseignée pour {filled} partie(s) déjà en base")
