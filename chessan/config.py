"""Chargement de config.toml."""
import datetime as dt
import os
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def players(path=None):
    """Joueurs à traiter : `username` puis ceux de la section [players]."""
    cfg = _read(path)
    return [cfg["username"].lower()] + [p.lower() for p in cfg.get("players", {}) if p.lower() != cfg["username"].lower()]


def _read(path):
    """config.toml, complété par config.local.toml (non versionné) s'il existe."""
    path = Path(path or ROOT / "config.toml")
    with open(path, "rb") as f:
        cfg = tomllib.load(f)
    local = path.with_name("config.local.toml")
    if local.exists():
        with open(local, "rb") as f:
            for k, v in tomllib.load(f).items():
                if isinstance(v, dict) and isinstance(cfg.get(k), dict):
                    cfg[k].update(v)
                else:
                    cfg[k] = v
    return cfg


def load(path=None, user=None):
    """Config d'un joueur : les clés de [players.<pseudo>] remplacent celles de premier niveau."""
    cfg = _read(path)
    user = (user or cfg["username"]).lower()
    overrides = {k.lower(): v for k, v in cfg.pop("players", {}).items()}.get(user, {})
    cfg.update(overrides)
    cfg["username"] = user
    cfg["contact"] = os.environ.get("CHESS_CONTACT") or cfg.get("contact")
    cfg["root"] = ROOT
    cfg["db_path"] = ROOT / "data" / user / "chess.db"
    cfg["raw_dir"] = ROOT / "data" / user / "raw"
    cfg["out_dir"] = ROOT / cfg["output"]["dir"] / user
    cfg["engine"]["path"] = str((ROOT / cfg["engine"]["path"]).resolve())
    cfg["since"] = start_date(cfg["period"])
    return cfg


def start_date(period, today=None):
    """Date de début de la période (incluse)."""
    if period.get("since"):
        return dt.date.fromisoformat(period["since"])
    today = today or dt.date.today()
    y, m = today.year, today.month - (period.get("months", 6) - 1)
    while m <= 0:
        y, m = y - 1, m + 12
    return dt.date(y, m, 1)


def engine_limit(tc_cfg):
    """(kwargs pour chess.engine.Limit, clé courte stockée en base)."""
    if "depth" in tc_cfg:
        return {"depth": int(tc_cfg["depth"])}, f"d{int(tc_cfg['depth'])}"
    if "time" in tc_cfg:
        return {"time": float(tc_cfg["time"])}, f"t{float(tc_cfg['time'])}"
    return {"depth": 14}, "d14"
