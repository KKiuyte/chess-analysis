# Analyse de mes parties chess.com

Récupère les parties chess.com d'un ou plusieurs joueurs via l'API publique, les stocke en SQLite, analyse leurs
coups avec Stockfish et génère un dashboard HTML autonome par joueur et par cadence, plus une page d'exercices tirés de
leurs erreurs.

Pages publiées : https://kkiuyte.github.io/chess-analysis/

Projet personnel, non affilié à chess.com.

## Lancer

```bash
cd ~/chess-analysis
.venv/bin/python run.py                  # collecte → analyse moteur → dashboards → exercices → site
.venv/bin/python run.py collect          # une étape seulement (collect | analyze | dashboard | exercises | site)
.venv/bin/python run.py --user yoy008    # un seul joueur
```

Sans `--user`, la commande traite le joueur principal (`username`) puis chaque joueur de `[players]`.

Résultat : `output/<pseudo>/dashboard-<cadence>.html`, des fichiers autonomes à ouvrir dans
un navigateur (Chart.js et les polices sont chargés depuis un CDN). Les mêmes pages
sans squelette HTML (`output/<pseudo>/fragments/`), pour la publication en page claude.ai.
L'étape `site` copie les pages de tous les joueurs dans `docs/` avec un index : c'est ce que sert GitHub Pages
(branche `main`, dossier `/docs`). Pour mettre le site à jour : `run.py`, puis commit et push de `docs/`.

Tout est incrémental, on peut relancer sans risque :
- **collecte** : seuls le mois en cours et les mois pas encore complets en cache sont re-téléchargés ;
- **analyse** : seules les parties pas encore analysées (ou analysées avec une autre limite moteur) passent dans
  Stockfish. Chaque partie est enregistrée dès qu'elle est finie : un Ctrl-C ne perd que les parties en cours.

## Installation (déjà faite sur la VM)

```bash
python3 -m venv .venv && .venv/bin/pip install chess
# Stockfish officiel (binaire générique x86-64) dans bin/stockfish :
curl -LO https://github.com/official-stockfish/Stockfish/releases/download/sf_19/stockfish-linux-x86-64-universal.tar.gz
tar xzf stockfish-linux-x86-64-universal.tar.gz && cp stockfish/stockfish-linux-x86-64-universal bin/stockfish
# Email de contact envoyé à chess.com dans le User-Agent (fichier non versionné) :
echo 'contact = "moi@example.com"' > config.local.toml    # ou : export CHESS_CONTACT=moi@example.com
```

`config.local.toml` (non versionné) complète et remplace `config.toml` : c'est là que va l'email de contact.

## Paramètres (`config.toml`)

| Clé | Rôle |
|---|---|
| `username` | joueur principal |
| `contact` | email mis dans le User-Agent des requêtes : dans `config.local.toml` ou `CHESS_CONTACT`, pas dans `config.toml` |
| `players.<pseudo>` | autres joueurs ; leurs clés (ex. `time_classes`) remplacent celles de premier niveau |
| `period.months` / `period.since` | 6 derniers mois calendaires, ou une date de début explicite |
| `filters` | parties classées seulement, échecs standard seulement |
| `time_classes.<cadence>` | une cadence = un dashboard ; `depth = N` ou `time = s` ; `min_games` optionnel |
| `engine` | chemin du binaire, nombre de process, threads, hash, priorité `nice` |
| `classification` | seuils imprécision / erreur / gaffe, positions déjà décidées ignorées |
| `phases` | 12 coups d'ouverture, finale à ≤ 13 points de pièces pour un camp |
| `openings` | « fréquente à faible score » : au moins N parties et score < X % |
| `exercises` | joueurs qui ont une page d'exercices, profondeur, nombre d'exercices, tolérance d'un coup accepté |

Changer la limite moteur d'une cadence relance l'analyse de ses parties au prochain `run.py`. Les seuils de
classification et d'ouvertures s'appliquent à la génération du dashboard, sans relancer le moteur. Les phases sont
calculées à l'ingestion : après avoir modifié `[phases]`, supprimer `data/<pseudo>/chess.db` et relancer.

## Méthode

- **Ouvertures** : nom tiré du header `ECOUrl` (ex. `Sicilian-Defense-Najdorf-Variation-6.Bg5` → famille
  *Sicilian Defense*, variante *Najdorf Variation*), code `ECO` en secours. Score = (V + ½ N) / parties.
- **Moteur** : chaque position est évaluée une fois à la limite configurée ; pour chacun de mes coups on compare
  l'évaluation avant (avec le meilleur coup) et après. Les mats valent ±10 000 cp.
- **% de gain** : `50 + 50 × (2 / (1 + exp(−0,00368208 × cp)) − 1)`, du point de vue du joueur.
- **Classement** par % de gain perdu : imprécision ≥ 10, erreur ≥ 20, gaffe ≥ 30. Les coups joués dans une position
  déjà perdue (< 5 %) ou déjà gagnée qui le reste (> 95 % avant, > 90 % après) ne sont pas comptés.
- **Phases** : ouverture = coups 1 à 12 ; finale = un des deux camps a ≤ 13 points hors pions et rois
  (C/F = 3, T = 5, D = 9) ; sinon milieu de partie.

## Diagnostic et conseils

`chessan/insights.py` calcule, sur toute la période d'une cadence, des cartes classées par priorité :
pendule (pertes au temps, retard sur l'adversaire, gaffes selon le temps restant), types de gaffes (matériel laissé en
prise, capture gagnante ratée, mat concédé ou raté : heuristique sur la position, sans moteur), phase la plus fragile,
positions gagnantes non converties, ouvertures (% de gain à la sortie de l'ouverture comparé au score final), tilt
et fatigue (score après une défaite, au fil d'une session). Les conseils sont générés par des règles à partir de ces
chiffres et changent quand les données changent.

## Exercices

`chessan/exercises.py` reprend les erreurs et gaffes (≥ 20 points de % de gain perdus) faites dans des positions encore
jouables (≥ 30 % avant le coup), une par position, les plus coûteuses d'abord. Chaque position est réévaluée en
multipv sur **tous** les coups légaux (profondeur 12, en cache dans la table `exercise_evals`) : la page note
n'importe quel coup et montre la réponse de l'adversaire à un mauvais coup. Trois thèmes, répartis à parts égales :
*Trouve le mat* (le meilleur coup mate), *Trouve le coup gagnant* (un ou deux coups seulement conviennent),
*Joue un coup sûr* (plusieurs coups conviennent, il fallait éviter la gaffe). Un coup est accepté s'il perd moins de
8 points par rapport au meilleur ; pour un mat, il faut un mat aussi rapide.

Sur claude.ai, la progression est synchronisée par compte (capability `db`) ; sur GitHub Pages, elle reste dans le
navigateur.

## Fichiers

```
config.toml          paramètres
run.py               commande unique
chessan/collect.py   API chess.com (retry/backoff sur 429) → cache data/<pseudo>/raw/AAAA-MM.json → SQLite
chessan/openings.py  famille / variante depuis ECOUrl
chessan/phases.py    ouverture / milieu / finale
chessan/analyze.py   Stockfish multi-process, persistance partie par partie
chessan/insights.py  diagnostic et conseils
chessan/dashboard.py agrégats → JSON embarqué dans templates/dashboard.html
chessan/exercises.py positions d'exercices → templates/exercises.html
chessan/site.py      docs/ pour GitHub Pages
data/<pseudo>/chess.db tables games, moves (avec pendule) + analyzed_games, archives
```
