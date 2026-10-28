"""Schéma SQLite."""
import sqlite3

SCHEMA = """
CREATE TABLE IF NOT EXISTS games (
    id TEXT PRIMARY KEY,
    url TEXT,
    end_time INTEGER,
    date TEXT,
    month TEXT,
    time_class TEXT,
    time_control TEXT,
    rated INTEGER,
    rules TEXT,
    color TEXT,              -- 'w' / 'b'
    opponent TEXT,
    my_elo INTEGER,
    opp_elo INTEGER,
    result TEXT,             -- 'win' / 'draw' / 'loss'
    result_detail TEXT,      -- code chess.com (checkmated, timeout, resigned...)
    eco TEXT,
    eco_url TEXT,
    opening_family TEXT,
    opening_variant TEXT,
    pgn TEXT,
    n_plies INTEGER
);

CREATE TABLE IF NOT EXISTS moves (
    game_id TEXT,
    ply INTEGER,             -- 0 = premier demi-coup de la partie
    move_no INTEGER,         -- numéro de coup complet
    color TEXT,
    is_mine INTEGER,
    san TEXT,
    uci TEXT,
    fen_before TEXT,
    phase TEXT,              -- 'opening' / 'middlegame' / 'endgame'
    -- analyse moteur (mes coups uniquement), point de vue du joueur
    cp_before INTEGER,
    cp_after INTEGER,
    win_before REAL,
    win_after REAL,
    best_uci TEXT,
    best_san TEXT,
    clock REAL,              -- temps restant au joueur après le coup (s), tiré de [%clk]
    PRIMARY KEY (game_id, ply)
);

CREATE TABLE IF NOT EXISTS analyzed_games (
    game_id TEXT PRIMARY KEY,
    limit_key TEXT,
    analyzed_at TEXT
);

CREATE TABLE IF NOT EXISTS archives (
    month TEXT PRIMARY KEY,  -- 'YYYY-MM'
    fetched_at TEXT,
    n_games INTEGER
);
"""


def connect(path):
    path.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(path)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA journal_mode=WAL")
    con.executescript(SCHEMA)
    cols = {r[1] for r in con.execute("PRAGMA table_info(moves)")}
    if "clock" not in cols:  # base créée avant l'ajout de la pendule
        con.execute("ALTER TABLE moves ADD COLUMN clock REAL")
    return con
