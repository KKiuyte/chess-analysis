"""Analyse d'un pseudo demandée depuis l'appli, de la collecte à la publication.

Tourne dans le job Cloud Run « analyse » (lancé par la Cloud Function quand
requests/{pseudo} passe à « pending ») ou à la main sur la VM :

    .venv/bin/python -m chessan.worker <pseudo>

L'état est gardé dans Cloud Storage (gs://<bucket>/players/<pseudo>.tar.gz : base SQLite
+ cache chess.com) : chaque mise à jour n'analyse que les nouvelles parties.
L'avancement est écrit dans requests/{pseudo}, que l'appli affiche en direct.
"""
import io
import os
import sys
import tarfile
import traceback

from . import analyze, collect, config, dashboard, db, exercises, publish


class Abandon(Exception):
    """Fin normale sans analyse (pas assez de parties…) : message montré tel quel dans l'appli."""


def _blob(cfg, pseudo):
    from google.cloud import storage
    return storage.Client(project="analyse-echecs").bucket(cfg["app"]["bucket"]).blob(f"players/{pseudo}.tar.gz")


def restore(cfg, pseudo):
    blob = _blob(cfg, pseudo)
    if not blob.exists():
        return False
    data_dir = cfg["db_path"].parent
    data_dir.mkdir(parents=True, exist_ok=True)
    with tarfile.open(fileobj=io.BytesIO(blob.download_as_bytes()), mode="r:gz") as tar:
        tar.extractall(data_dir, filter="data")
    return True


def save(cfg, pseudo):
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w:gz") as tar:
        tar.add(cfg["db_path"], arcname="chess.db")
        if cfg["raw_dir"].exists():
            tar.add(cfg["raw_dir"], arcname="raw")
    _blob(cfg, pseudo).upload_from_string(buf.getvalue(), content_type="application/gzip")


def player_config(pseudo):
    cfg = config.load(user=pseudo)
    if pseudo not in config.players():
        # Joueur venu de l'appli : toutes les cadences, gardées ensuite selon le nombre de parties.
        cfg["time_classes"] = {tc: dict(v) for tc, v in cfg["app"]["time_classes"].items()}
        cfg["exercises"]["players"] = [pseudo]
        cfg["max_games"] = cfg["app"]["max_games"]
    # Sur Cloud Run, os.cpu_count() ne reflète pas les cœurs alloués : le job fixe ENGINE_PROCESSES.
    cfg["engine"]["processes"] = int(os.environ.get("ENGINE_PROCESSES") or os.cpu_count() or 1)
    cfg["engine"]["nice"] = 0
    return cfg


def run(pseudo):
    from firebase_admin import firestore
    pseudo = pseudo.lower()
    cfg = player_config(pseudo)
    req = publish.client(cfg).collection("requests").document(pseudo)

    def status(**kw):
        req.set({**kw, "updatedAt": firestore.SERVER_TIMESTAMP}, merge=True)

    try:
        status(status="running", step="Récupération de tes parties sur chess.com", progress=None, error=None)
        restore(cfg, pseudo)
        con = db.connect(cfg["db_path"])
        collect.ingest(cfg, con, collect.collect(cfg, con))

        since = cfg["since"].isoformat()
        counts = dict(con.execute("SELECT time_class, COUNT(*) FROM games WHERE date >= ? GROUP BY time_class",
                                  (since,)).fetchall())
        min_default = cfg["app"]["min_games"]
        kept = {tc: v for tc, v in cfg["time_classes"].items() if counts.get(tc, 0) >= v.get("min_games", min_default)}
        if not kept:
            raise Abandon(f"Pas assez de parties classées depuis le {cfg['since'].strftime('%d/%m/%Y')} "
                          f"(il en faut au moins {min_default} dans une cadence).")
        cfg["time_classes"] = kept

        cfg["on_progress"] = lambda i, n: status(step="Analyse de tes parties par Stockfish", progress=[i, n])
        status(step="Analyse de tes parties par Stockfish", progress=None)
        analyze.analyze(cfg, con)

        status(step="Préparation des dashboards et des exercices", progress=None)
        dashboard.build(cfg, con)
        exercises.build(cfg, con)
        con.close()
        save(cfg, pseudo)
        publish.publish(cfg)
        status(status="done", step=None, progress=None, finished=firestore.SERVER_TIMESTAMP)
    except Abandon as e:
        status(status="error", error=str(e), step=None, progress=None, finished=firestore.SERVER_TIMESTAMP)
    except Exception:
        traceback.print_exc()
        status(status="error", error="L'analyse a échoué. Réessaie dans quelques minutes.",
               step=None, progress=None, finished=firestore.SERVER_TIMESTAMP)
        sys.exit(1)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    run(sys.argv[1])
