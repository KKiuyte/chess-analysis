"""Invitations à l'appli (accès sur invitation, voir firestore.rules).

    .venv/bin/python -m chessan.invite add prenom.nom@gmail.com [note]
    .venv/bin/python -m chessan.invite pseudo yoy008     # invite les comptes déjà inscrits avec ce pseudo
    .venv/bin/python -m chessan.invite list
    .venv/bin/python -m chessan.invite remove prenom.nom@gmail.com
"""
import sys

from firebase_admin import firestore

from . import config, publish


def main(argv):
    db = publish.client(config.load())
    inv = db.collection("invites")
    cmd, *args = argv or ["list"]
    if cmd == "add" and args:
        email = args[0].strip().lower()
        inv.document(email).set({"note": " ".join(args[1:]), "created": firestore.SERVER_TIMESTAMP})
        print(f"Invité : {email}")
    elif cmd == "pseudo" and args:
        uids = [u.id for u in db.collection("users").where("pseudo", "==", args[0].lower()).stream()]
        for uid in uids:
            inv.document(uid).set({"note": f"pseudo {args[0].lower()}", "created": firestore.SERVER_TIMESTAMP})
        print(f"{len(uids)} compte(s) invité(s) pour le pseudo {args[0].lower()}")
    elif cmd == "remove" and args:
        inv.document(args[0].strip().lower()).delete()
        print(f"Invitation retirée : {args[0].strip().lower()}")
    elif cmd == "list":
        for d in inv.stream():
            print(d.id, "·", d.to_dict().get("note", ""))
    else:
        print(__doc__)


if __name__ == "__main__":
    main(sys.argv[1:])
