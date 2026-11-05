"""Analyse d'un pseudo demandée depuis l'appli, de la collecte à la publication.

Tourne dans le job Cloud Run « analyse » (lancé par la Cloud Function quand
requests/{pseudo} passe à « pending ») ou à la main sur la VM :

    .venv/bin/python -m chessan.worker <pseudo>

L'état est gardé dans Cloud Storage (gs://<bucket>/players/<pseudo>.tar.gz : base SQLite
+ cache chess.com) : chaque mise à jour n'analyse que les nouvelles parties.
L'avancement est écrit dans requests/{pseudo}, que l'appli affiche en direct.

Analyse répartie : si le travail est assez long ([app] cost_per_machine), la machine lancée par
la fonction (« coordinatrice ») découpe les parties en petits paquets (file d'attente dans
gs://<bucket>/runs/<run>/) et lance des machines d'appoint (même job, `--shard <pseudo> <run>`).
Chaque machine, coordinatrice comprise, réserve le paquet suivant (création atomique de
claim-<i>), le traite, recommence : les machines rapides en font plus, celles qui démarrent
tard moins, et tout finit ensemble. Un paquet réservé mais jamais rendu (machine plantée) est
refait par la coordinatrice.
"""
import io
import json
import os
import sys
import tarfile
import threading
import time
import traceback

from . import analyze, bilan, collect, config, dashboard, db, exercises, publish

REGION = "europe-west1"


class Abandon(Exception):
    """Fin normale sans analyse (pas assez de parties…) : message montré tel quel dans l'appli."""


def _bucket(cfg):
    from google.cloud import storage
    return storage.Client(project="analyse-echecs").bucket(cfg["app"]["bucket"])


def _blob(cfg, pseudo):
    return _bucket(cfg).blob(f"players/{pseudo}.tar.gz")


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
    # La base est en WAL : on reporte d'abord dans chess.db tout ce qui est encore dans chess.db-wal,
    # sinon l'archive perdrait les dernières écritures (parties analysées, bilan…).
    import sqlite3
    c = sqlite3.connect(cfg["db_path"], timeout=30)
    c.execute("PRAGMA wal_checkpoint(TRUNCATE)")
    c.close()
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


class Progress:
    """Parties terminées, ajoutées au compteur commun requests/{pseudo}.progressDone (toutes les
    machines y contribuent) au plus toutes les 2 s."""
    def __init__(self, req):
        self.req, self.pending, self.last = req, 0, time.monotonic()

    def add(self):
        self.pending += 1
        if time.monotonic() - self.last >= 2:
            self.flush()

    def flush(self):
        from firebase_admin import firestore
        if self.pending:
            self.req.update({"progressDone": firestore.Increment(self.pending)})
            self.pending = 0
        self.last = time.monotonic()


def _session():
    import google.auth
    from google.auth.transport.requests import AuthorizedSession
    creds, _ = google.auth.default(scopes=["https://www.googleapis.com/auth/cloud-platform"])
    return AuthorizedSession(creds)


def machines_for(cfg, tasks):
    """Nombre de machines : une par tranche de travail [app].cost_per_machine, au plus machines_max."""
    if not os.environ.get("CLOUD_RUN_JOB"):
        return 1
    total = sum(analyze.cost(t) for t in tasks)
    return max(1, min(cfg["app"]["machines_max"], int(total // cfg["app"]["cost_per_machine"])))


def chunks_of(tasks, size):
    """Paquets consécutifs de coût ≈ size. Les profondeurs les plus fortes d'abord (daily, rapide) : leurs
    positions sont les plus longues, mieux vaut qu'elles ne restent pas pour la fin quand les machines
    d'appoint s'arrêtent ; à profondeur égale, les parties récentes d'abord (ordre de pending_tasks)."""
    tasks = sorted(tasks, key=lambda t: -t[0][3].get("depth", 0))
    out, cur, load = [], [], 0.0
    for t in tasks:
        cur.append(t)
        load += analyze.cost(t)
        if load >= size:
            out.append(cur)
            cur, load = [], 0.0
    if cur:
        out.append(cur)
    return out


def _claim(bucket, run_id, i):
    """Réserve le paquet i : la création échoue si une autre machine l'a déjà réservé."""
    from google.api_core.exceptions import PreconditionFailed
    try:
        bucket.blob(f"runs/{run_id}/claim-{i}").upload_from_string(b"", if_generation_match=0)
        return True
    except PreconditionFailed:
        return False


def distributed(cfg, con, pseudo, tasks, machines, status):
    bucket = _bucket(cfg)
    run_id = f"{pseudo}-{int(time.time())}"
    chunks = chunks_of(tasks, cfg["app"]["chunk_cost"])
    for i, chunk in enumerate(chunks):
        bucket.blob(f"runs/{run_id}/chunk-{i}.json").upload_from_string(json.dumps(chunk))
    bucket.blob(f"runs/{run_id}/plan.json").upload_from_string(json.dumps({"chunks": len(chunks)}))
    execution = None
    try:
        job = os.environ.get("CLOUD_RUN_JOB", "analyse")
        r = _session().post(f"https://run.googleapis.com/v2/projects/analyse-echecs/locations/{REGION}/jobs/{job}:run",
                            json={"overrides": {"containerOverrides": [{"args": ["--shard", pseudo, run_id]}],
                                                "taskCount": machines - 1}})
        r.raise_for_status()
        execution = r.json()["metadata"]["name"]
        print(f"Analyse répartie : {len(chunks)} paquets, {machines} machines (appoint : {execution.split('/')[-1]})", flush=True)
    except Exception:
        traceback.print_exc()
        print("Machines d'appoint indisponibles : tous les paquets sur cette machine", flush=True)
    status(machines=machines if execution else 1)

    # La coordinatrice dépile la file comme les autres (et tout, si l'appoint n'a pas démarré).
    mine = set()
    for i, chunk in enumerate(chunks):
        if _claim(bucket, run_id, i):
            analyze.analyze(cfg, con, chunk)
            mine.add(i)
    print(f"Coordinatrice : {len(mine)} paquet(s) sur {len(chunks)}", flush=True)

    todo, session = set(range(len(chunks))) - mine, _session()
    while todo:
        for i in sorted(todo):
            blob = bucket.blob(f"runs/{run_id}/result-{i}.json")
            if blob.exists():
                for game_id, key, rows in json.loads(blob.download_as_bytes()):
                    analyze.save_game(con, game_id, key, rows)
                todo.discard(i)
        if not todo:
            break
        ex = session.get(f"https://run.googleapis.com/v2/{execution}").json() if execution else {"completionTime": 1}
        if ex.get("completionTime"):
            time.sleep(3)            # dernier résultat éventuellement en cours d'écriture
            for i in sorted(todo):
                if not bucket.blob(f"runs/{run_id}/result-{i}.json").exists():
                    print(f"Paquet {i} réservé mais jamais rendu : refait ici", flush=True)
                    analyze.analyze(cfg, con, chunks[i])
                    todo.discard(i)
        else:
            time.sleep(2)
    for blob in bucket.list_blobs(prefix=f"runs/{run_id}/"):
        blob.delete()


def run_shard(pseudo, run_id):
    """Machine d'appoint : dépile la file de paquets et dépose le résultat de chacun dans le bucket."""
    pseudo = pseudo.lower()
    cfg = player_config(pseudo)
    bucket = _bucket(cfg)
    n = json.loads(bucket.blob(f"runs/{run_id}/plan.json").download_as_bytes())["chunks"]
    progress = Progress(publish.client(cfg).collection("requests").document(pseudo))
    task = int(os.environ.get("CLOUD_RUN_TASK_INDEX", 0))
    done = 0
    for i in range(n):
        if not _claim(bucket, run_id, i):
            continue
        chunk = json.loads(bucket.blob(f"runs/{run_id}/chunk-{i}.json").download_as_bytes())
        out = []

        def on_game(game_id, key, rows):
            out.append([game_id, key, rows])
            progress.add()

        analyze.evaluate(chunk, cfg["engine"], cfg["engine"]["processes"], on_game)
        progress.flush()
        bucket.blob(f"runs/{run_id}/result-{i}.json").upload_from_string(json.dumps(out))
        done += 1
    print(f"Machine d'appoint {task} : {done} paquet(s) sur {n}", flush=True)


def preview(con):
    """Dernière partie du joueur, rejouée sur l'écran d'attente pendant l'analyse."""
    g = con.execute("SELECT * FROM games ORDER BY end_time DESC LIMIT 1").fetchone()
    if not g:
        return None
    moves = [r[0] for r in con.execute("SELECT uci FROM moves WHERE game_id = ? ORDER BY ply", (g["id"],))]
    return {"adversaire": g["opponent"], "elo": g["opp_elo"], "couleur": g["color"], "resultat": g["result"],
            "date": g["date"], "cadence": g["time_class"], "coups": moves[:300]}


def run(pseudo):
    from firebase_admin import firestore
    pseudo = pseudo.lower()
    cfg = player_config(pseudo)
    req = publish.client(cfg).collection("requests").document(pseudo)

    def status(**kw):
        req.set({**kw, "updatedAt": firestore.SERVER_TIMESTAMP}, merge=True)

    def throttled(field):
        """Avancement « i / n » écrit au plus toutes les 2 s (et toujours au début et à la fin)."""
        last = [0.0]
        def f(i, n):
            now = time.monotonic()
            if i in (0, n) or now - last[0] >= 2:
                last[0] = now
                status(**{field: [i, n]})
        return f

    # Étapes (champ « stage ») : 0 récupération, 1 analyse Stockfish, 2 dashboards et exercices, 3 publication.
    try:
        status(status="running", stage=0, step="Récupération de tes parties sur chess.com", started=firestore.SERVER_TIMESTAMP,
               progress=None, progressDone=0, progressTotal=None, machines=None, exProgress=None,
               found=None, skipped=None, preview=None, error=None)
        restore(cfg, pseudo)
        con = db.connect(cfg["db_path"])
        collect.ingest(cfg, con, collect.collect(cfg, con))

        since = cfg["since"].isoformat()
        counts = dict(con.execute("SELECT time_class, COUNT(*) FROM games WHERE date >= ? GROUP BY time_class",
                                  (since,)).fetchall())
        min_default = cfg["app"]["min_games"]
        found = {tc: counts.get(tc, 0) for tc in cfg["time_classes"] if counts.get(tc, 0)}
        kept, skipped = {}, []
        for tc, v in cfg["time_classes"].items():
            need = v.get("min_games", min_default)
            if counts.get(tc, 0) >= need:
                kept[tc] = v
            elif counts.get(tc, 0):
                skipped.append({"tc": tc, "n": counts[tc], "min": need})
        cfg["skipped"] = skipped
        status(found=found, skipped=skipped, preview=preview(con))
        if not kept:
            raise Abandon(f"Pas assez de parties classées depuis le {cfg['since'].strftime('%d/%m/%Y')} : "
                          f"il en faut au moins {min_default} dans une cadence (3 en daily).")
        cfg["time_classes"] = kept

        tasks = analyze.pending_tasks(cfg, con)
        machines = machines_for(cfg, tasks)
        status(stage=1, step="Analyse de tes parties par Stockfish", progressTotal=len(tasks), machines=1)
        progress = Progress(req)
        cfg["on_game"] = progress.add
        if machines > 1:
            distributed(cfg, con, pseudo, tasks, machines, status)
        else:
            analyze.analyze(cfg, con, tasks)
        progress.flush()

        # Première publication dès que possible : dashboards + quelques exercices (les erreurs les
        # plus coûteuses). Les autres exercices sont faits ensuite, sans le dire, puis republiés :
        # l'appli ne recharge pas la page affichée, la nouvelle version vient au changement d'onglet.
        status(stage=2, step="Préparation des dashboards et des exercices")
        cfg["on_ex_progress"] = throttled("exProgress")
        # Cadences dont le premier bilan IA va être rédigé : annoncé dans le dashboard en attendant.
        if bilan.api_key(cfg):
            cfg["bilan_pending"] = {tc for tc in cfg["time_classes"]
                                    if dashboard.latest_bilan(con, tc) is None and bilan.due(cfg, con, tc)[0]}
        dashboard.build(cfg, con)

        # Bilans IA (Claude) lancés tout de suite, en parallèle des exercices : ils n'ont besoin que
        # des dashboards et passent leur temps à attendre la réponse de l'API (connexion à part).
        bilans = {"done": []}

        def write_bilans():
            c = db.connect(cfg["db_path"])
            try:
                bilans["done"] = bilan.run(cfg, c)
            except Exception:
                traceback.print_exc()
            finally:
                c.close()
        writer = threading.Thread(target=write_bilans)
        if cfg.get("bilan_pending") or bilan.api_key(cfg):
            writer.start()

        exercises.build(cfg, con, first=cfg["app"]["first_exercises"])
        status(stage=3, step="Publication")
        save(cfg, pseudo)
        publish.publish(cfg)
        status(status="done", stage=4, step=None, finished=firestore.SERVER_TIMESTAMP)

        cfg["on_ex_progress"] = None
        try:
            exercises.build(cfg, con)
            save(cfg, pseudo)
            publish.publish(cfg)
        except Exception:
            traceback.print_exc()            # la première publication reste en place
        if writer.is_alive() or writer.ident:
            writer.join()
        done = bilans["done"]
        # Republier si un bilan est arrivé, ou si un bilan annoncé n'a pas pu être rédigé
        # (le dashboard revient alors aux conseils automatiques).
        if done or cfg.get("bilan_pending"):
            cfg["bilan_pending"] = set()
            try:
                dashboard.build(cfg, con)
                save(cfg, pseudo)
                publish.publish(cfg)
            except Exception:
                traceback.print_exc()
        con.close()
    except Abandon as e:
        status(status="error", error=str(e), step=None, finished=firestore.SERVER_TIMESTAMP)
    except Exception:
        traceback.print_exc()
        status(status="error", error="L'analyse a échoué. Réessaie dans quelques minutes.",
               step=None, finished=firestore.SERVER_TIMESTAMP)
        sys.exit(1)


if __name__ == "__main__":
    if len(sys.argv) == 4 and sys.argv[1] == "--shard":
        run_shard(sys.argv[2], sys.argv[3])
    elif len(sys.argv) == 2:
        run(sys.argv[1])
    else:
        sys.exit(__doc__)
