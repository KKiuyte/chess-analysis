#!/usr/bin/env python3
"""Commande unique : collecte → analyse moteur → dashboards.

    .venv/bin/python run.py              # tout
    .venv/bin/python run.py collect      # une seule étape (collect | analyze | dashboard | exercises | site)
    .venv/bin/python run.py --user yoy008  # un seul joueur
"""
import argparse

from chessan import analyze, collect, config, dashboard, db, exercises, site


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("steps", nargs="*", choices=["collect", "analyze", "dashboard", "exercises", "site"],
                   help="étapes à lancer (défaut : toutes)")
    p.add_argument("--config", help="chemin vers config.toml")
    p.add_argument("--user", help="un seul joueur (défaut : tous ceux de la config)")
    args = p.parse_args()
    steps = args.steps or ["collect", "analyze", "dashboard", "exercises", "site"]

    for user in [args.user] if args.user else config.players(args.config):
        cfg = config.load(args.config, user)
        con = db.connect(cfg["db_path"])
        print(f"\n=== {cfg['username']} : parties depuis le {cfg['since']}, cadences : {', '.join(cfg['time_classes'])}")
        if "collect" in steps:
            raw_files = collect.collect(cfg, con)
            collect.ingest(cfg, con, raw_files)
        if "analyze" in steps:
            analyze.analyze(cfg, con)
        if "dashboard" in steps:
            dashboard.build(cfg, con)
        if "exercises" in steps and user in cfg["exercises"]["players"]:
            exercises.build(cfg, con)
        con.close()

    if "site" in steps:
        # docs/ (GitHub Pages) regroupe tous les joueurs, même si un seul a été recalculé.
        site.build(config.ROOT, config.players(args.config), config.load(args.config)["period"].get("months", 6))


if __name__ == "__main__":
    main()
