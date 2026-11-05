"""Publication dans Firestore pour l'appli web (projet Firebase « analyse-echecs »).

Lit les JSON écrits par les étapes dashboard et exercises (output/<pseudo>/data/) et les
range ainsi :

    players/{pseudo}              { pseudo, pages: [{id, label}], since, updated }
    players/{pseudo}/pages/{id}   { json: "<données de la page>", updated }

Les données restent une chaîne JSON : Firestore refuse les tableaux de tableaux (les coups
des exercices) et l'appli les réinjecte telles quelles dans les templates.
Écriture avec le SDK Admin et la clé du compte de service indiquée par
[firebase].credentials (fichier non versionné).
"""
import json
import os
from pathlib import Path

ORDER = ["bullet", "blitz", "rapid", "daily"]
_db = None


def client(cfg):
    """Client Firestore : clé du compte de service sur la VM, identité du job sur Cloud Run."""
    global _db
    if _db is None:
        import firebase_admin
        from firebase_admin import credentials, firestore
        key = Path(cfg["firebase"]["credentials"]).expanduser()
        if not key.is_absolute():
            key = cfg["root"] / key
        if key.exists():
            app = firebase_admin.initialize_app(credentials.Certificate(str(key)))
        elif os.environ.get("CLOUD_RUN_JOB"):
            app = firebase_admin.initialize_app(options={"projectId": "analyse-echecs"})
        else:
            print(f"Publication ignorée : clé du compte de service introuvable ({key})")
            return None
        _db = firestore.client(app)
    return _db


def _pages(cfg):
    """(id, libellé, fichier JSON) des pages disponibles pour ce joueur, dans l'ordre d'affichage."""
    src = cfg["out_dir"] / "data"
    out = []
    dashboards = sorted(src.glob("dashboard-*.json"),
                        key=lambda p: ORDER.index(p.stem[10:]) if p.stem[10:] in ORDER else 99)
    for f in dashboards:
        tc = f.stem[len("dashboard-"):]
        if tc in cfg["time_classes"]:
            out.append((f.stem, json.loads(f.read_text())["tcLabel"], f))
    ex = src / "exercises.json"
    if ex.exists() and cfg["username"] in cfg["exercises"]["players"]:
        out.append(("exercises", "Exercices", ex))
    return out


def publish(cfg):
    from firebase_admin import firestore
    db = client(cfg)
    if db is None:
        return
    user = cfg["username"]
    pages = _pages(cfg)
    if not pages:
        print(f"Publication : rien à publier pour {user} (lancer d'abord dashboard / exercises)")
        return
    ref = db.collection("players").document(user)
    batch = db.batch()
    for pid, _, f in pages:
        batch.set(ref.collection("pages").document(pid), {"json": f.read_text(), "updated": firestore.SERVER_TIMESTAMP})
    # Le document joueur en dernier : l'appli l'écoute et charge les pages quand il change.
    batch.set(ref, {"pseudo": user, "since": cfg["since"].isoformat(),
                    "pages": [{"id": pid, "label": label} for pid, label, _ in pages],
                    "updated": firestore.SERVER_TIMESTAMP})
    batch.commit()
    size = sum(f.stat().st_size for _, _, f in pages) // 1024
    print(f"Publication : {len(pages)} page(s), {size} Ko → Firestore players/{user}")
