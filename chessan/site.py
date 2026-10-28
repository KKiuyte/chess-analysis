"""Site statique pour GitHub Pages : les pages de chaque joueur copiées dans docs/, plus un index."""
import datetime as dt
import html
import shutil

from .dashboard import TC_LABELS

ORDER = ["bullet", "blitz", "rapid", "daily"]

INDEX = """<!doctype html>
<html lang="fr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Analyses d'échecs</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:opsz,wght@12..96,700&family=Atkinson+Hyperlegible:wght@400;700&display=swap">
<style>
:root {{ --bg: #f4f5f1; --surface: #fcfcfa; --fg: #171a17; --muted: #586058; --line: #dde1d9; --accent: #3b6a44; }}
@media (prefers-color-scheme: dark) {{
  :root {{ --bg: #121513; --surface: #1a1d1b; --fg: #edefeb; --muted: #a4aca5; --line: #2b312d; --accent: #86b98e; color-scheme: dark; }}
}}
* {{ box-sizing: border-box; }}
body {{ margin: 0; background: var(--bg); color: var(--fg); font: 15px/1.5 "Atkinson Hyperlegible", system-ui, sans-serif; padding: 32px 16px 48px; }}
.wrap {{ max-width: 860px; margin: 0 auto; display: flex; flex-direction: column; gap: 28px; }}
h1, h2 {{ font-family: "Bricolage Grotesque", system-ui, sans-serif; margin: 0; line-height: 1.15; }}
h1 {{ font-size: clamp(28px, 6vw, 40px); }}
h2 {{ font-size: 20px; }}
p {{ margin: 0; }}
.muted {{ color: var(--muted); }}
.grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(240px, 1fr)); gap: 12px; }}
.card {{ background: var(--surface); border: 1px solid var(--line); border-radius: 10px; padding: 16px; display: flex; flex-direction: column; gap: 10px; }}
.card ul {{ list-style: none; margin: 0; padding: 0; display: flex; flex-direction: column; gap: 6px; }}
a {{ color: var(--accent); font-weight: 700; }}
footer {{ font-size: 13px; color: var(--muted); border-top: 1px solid var(--line); padding-top: 16px; }}
</style>
</head>
<body>
<div class="wrap">
  <header>
    <h1>Analyses d'échecs</h1>
    <p class="muted" style="margin-top:8px">Parties chess.com des {months} derniers mois analysées par Stockfish : résultats par ouverture,
    erreurs par phase de jeu, conseils, et exercices tirés des erreurs de chaque joueur. Mis à jour le {date}.</p>
  </header>
  <div class="grid">
{cards}
  </div>
  <footer>Site personnel, non affilié à chess.com. Données issues de l'API publique de chess.com.
  Sur cette version, la progression des exercices est gardée dans le navigateur.</footer>
</div>
</body>
</html>
"""


def build(root, players, months):
    docs = root / "docs"
    cards = []
    for user in players:
        src = root / "output" / user
        if not src.is_dir():
            continue
        dest = docs / user
        dest.mkdir(parents=True, exist_ok=True)
        links = []
        dashboards = sorted(src.glob("dashboard-*.html"),
                            key=lambda p: ORDER.index(p.stem[10:]) if p.stem[10:] in ORDER else 99)
        for page in dashboards:
            shutil.copy2(page, dest / page.name)
            tc = page.stem[len("dashboard-"):]
            links.append((f"{user}/{page.name}", f"Dashboard {TC_LABELS.get(tc, tc)}"))
        if (src / "exercises.html").exists():
            shutil.copy2(src / "exercises.html", dest / "exercises.html")
            links.append((f"{user}/exercises.html", "Exercices"))
        items = "\n".join(f'      <li><a href="{html.escape(h)}">{html.escape(t)}</a></li>' for h, t in links)
        cards.append(f'    <div class="card"><h2>{html.escape(user.capitalize())}</h2>\n    <ul>\n{items}\n    </ul></div>')
    (docs / ".nojekyll").touch()
    (docs / "index.html").write_text(INDEX.format(cards="\n".join(cards), months=months,
                                                  date=dt.date.today().strftime("%d/%m/%Y")))
    print(f"Site : {len(cards)} joueur(s) → {docs / 'index.html'}")
