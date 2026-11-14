# Outils spécialisés tiers d'analyse et de progression aux échecs (état 2025-2026)

Recherche du 14/11/2026. Environ 20 appels d'outils. Plusieurs pages officielles étaient bloquées ou vides (aimchess.com/pricing n'a renvoyé que le titre ; chessmonitor.com sans tarifs ; billet Lichess de ChessMonitor en 403). Une bonne partie des données de prix vient donc des fiches App Store, plus fiables que les annuaires « IA » générés automatiquement (stork.ai, marlvel.ai, creati.ai), que j'ai écartés ou signalés comme tels.

## Q1. Fonctions de base de chaque outil (import auto chess.com/Lichess, puzzles tirés de ses propres erreurs, explications en langage naturel, répertoire construit sur ses parties)

### À retenir
Aimchess (analytique par phase + entraînement « Retry Mistakes ») et Chessbook (répertoire + contrôle des parties en ligne contre ce répertoire) sont les deux concurrents qui recouvrent le plus l'appli. DecodeChess fournit des explications en langage naturel, mais partie par partie et sans synchronisation de compte. ChessBase 26 et Fritz 20 ajoutent un assistant IA jugé faible. Une vague de petits outils web (Chessiro, Chessigma, Chessie, ChessMonitor, Chesscope, NextMove) couvre chacun une partie de la chaîne. Je n'en ai trouvé aucun qui fasse tout à la fois : analyse en lot chaque nuit + tableaux de bord par cadence + rapport de coach LLM + exercices tirés de ses erreurs (mats, tactiques, coups sûrs, ouvertures) + répertoire avec « fuites ».

### Constats sourcés

**Aimchess** (Chess.com, LLC)
- Se connecte à Chess.com, Lichess ou Chess24 pour analyser les parties. Il décompose le jeu en Ouvertures, Tactique, Finales, Exploitation de l'avantage, Ressources défensives et Gestion du temps, avec comparaison aux joueurs de même niveau — [App Store](https://apps.apple.com/app/id1524941307)
- Exercices : Adaptive Tactics, Blindfold Tactics, Blunder Preventer, 360 Trainer, Checkmate Flash Cards. La « Training Room » comprend Opening Improver, Advantage Capitalization Trainer, Endgames, Intuition Trainer, **Retry Mistakes**, Defender, Time Trainer et des plans d'entraînement personnalisés — [App Store](https://apps.apple.com/app/id1524941307)
- Pas d'explications en langage naturel : un avis demande des explications sur le pourquoi d'un coup, car « la flèche seule » ne suffit pas aux débutants — [App Store](https://apps.apple.com/app/id1524941307)
- Racheté par Play Magnus Group en 2021 — [Play Magnus Group](https://playmagnusgroup.com/chess-training-and-analytics-startup-aimchess-joins-play-magnus-group). Il est donc passé sous Chess.com avec le rachat de PMG (voir Q3).
- **Signes de délaissement (à signaler)** : dernière mise à jour iOS en version 1.3.1 du 28/06/2024 — [App Store](https://apps.apple.com/app/id1524941307). Des fils du forum chess.com font état d'une panne de plusieurs jours « sans la moindre annonce », d'un lien Aimchess sur Chess.com menant à une 404, puis d'un retour — [forum chess.com](https://www.chess.com/forum/view/help-support/aimchess-com-down) ; [fil « What happened to Aimchess »](https://www.chess.com/clubs/forum/view/what-happened-to-aim-chess). Je n'ai trouvé aucune annonce officielle de fermeture.

**Chessable** (Chess.com)
- Cours d'ouvertures et de technique en répétition espacée (« MoveTrainer »). Depuis 2025, Chessable PRO comprend 20 % de remise sur les cours, 300 cours réservés PRO, un mode hors ligne et un **entraînement par puzzles personnalisés tirés de vos propres parties** — [Chess.com State of Chess 2025](https://www.chess.com/news/view/2025-state-of-chess)
- « Train away the mistakes in your very own online games with Puzzle Connect » (Puzzle Connect sert à corriger les erreurs de vos propres parties en ligne) — [blog Chessable, changements au 02/01/2025](https://chess.com/blog/Chessable/new-year-big-changes-to-chessable-pro). Chessable 3.0 annonce aussi des puzzles personnalisés et un entraînement d'ouvertures simplifié — [Chess.com](https://www.chess.com/news/view/announcing-chessable-3)
- L'intégration à Chess.com progresse : les « Courses » de Chess.com, qui donnent accès à la bibliothèque Chessable, étaient en bêta en mars 2025, avec un lancement prévu en avril ou mai — [State of Chess 2025](https://www.chess.com/news/view/2025-state-of-chess)
- Pas de répertoire généré à partir de vos parties : le répertoire vient des cours achetés (inféré de toutes les sources ci-dessus ; non confirmé explicitement).

**DecodeChess**
- Explications « en langage intuitif », produites par des algorithmes d'IA maison et calculées sur leurs serveurs — [FAQ DecodeChess](https://decodechess.com/?p=3409)
- « Decode Game » explique les coups recommandés par Stockfish sur toute une partie (15 à 60 s). « Decode Deep » analyse une position : menaces, plans, concepts, meilleurs coups. S'y ajoutent l'explication de vos erreurs, une courbe de partie qui suggère les positions à décoder et un adversaire « humain » — [tarifs DecodeChess](https://decodechess.com/pricing/)
- Import en **PGN/FEN** des parties jouées ailleurs. La page ne mentionne aucune synchronisation automatique de compte — [tarifs DecodeChess](https://decodechess.com/pricing/)
- Pas d'exercices tirés de vos erreurs, pas de répertoire, pas de statistiques agrégées sur l'ensemble des parties (absents de la page de tarifs).
- Partenariat avec Chessify (analyse cloud) — [Chessify](https://chessify.me/news/chessify-partnership-with-decodechess)
- Peu adapté au mobile : le site recommande tablette ou ordinateur — [tarifs DecodeChess](https://decodechess.com/pricing/)

**ChessBase 26 / Fritz 20-21** (ChessBase GmbH, logiciel de bureau)
- ChessBase 26 est sorti le 11/11/2025 — [ChessBase](https://en.chessbase.com/post/chessbase-26-expand-your-chess-horizon). Fritz 20 est sorti en mai 2025 avec une fonction « AI Chat » qui commente la partie à la demande — [ChessBase](https://en.chessbase.com/post/brand-new-release-fritz-20). Fritz 21 suit en 2026 — [revue Fritz 21](https://en.chessbase.com/post/review-fritz-21)
- L'assistant IA de CB26 commente le placement des pièces et la stratégie, signale les plans typiques et met en garde contre les mauvaises décisions. Le rapport d'ouverture donne taux de réussite, tendances, déviations typiques et préférences selon le niveau — [revue ChessBase 26, 14/02/2026](https://en.chessbase.com/post/review-chessbase-26-the-beginning-of-a-new-era)
- La revue (publiée sur le site de l'éditeur) ne mentionne **aucun import automatique** des parties chess.com/Lichess — [revue CB26](https://en.chessbase.com/post/review-chessbase-26-the-beginning-of-a-new-era)

**Chessbook** (répertoire)
- Construction d'un répertoire en répétition espacée, détection automatique des trous de couverture, choix des coups selon les statistiques des maîtres, le moteur et les résultats à votre niveau, gestion des transpositions — [App Store](https://apps.apple.com/us/app/chessbook/id6466343415)
- **Contrôle de vos parties Lichess/Chess.com pour repérer les erreurs d'ouverture et mesurer à quel point vous avez suivi votre répertoire.** C'est la fonction la plus proche des « fuites » de l'appli — [App Store](https://apps.apple.com/us/app/chessbook/id6466343415)
- Peut générer un répertoire à partir des parties Lichess ; import PGN — [64squares](https://64squares.substack.com/p/chessbook-review) ; [revue Lichess](https://en.lichess.org/ublog/B3xp08nE/redirect)
- Plans de milieu de jeu issus des parties de joueurs forts — [App Store](https://apps.apple.com/us/app/chessbook/id6466343415)

**Noctie**
- IA de jeu « humaine », du débutant au GM, qui imite les ouvertures humaines. Elle **génère aussi des puzzles à partir de vos erreurs** (sur les parties jouées contre elle) — [App Store](https://apps.apple.com/us/app/noctie-chess/id6444289077)

**Petits outils web (2025-2026)**
- **Chessiro** : import Chess.com/Lichess + PGN, revue coup par coup gratuite et illimitée, « Smart Shuffle » (puzzles tirés de vos erreurs), coach IA en anglais simple, détection de l'ouverture partie par partie mais sans explorateur — [blog Chessiro, mis à jour le 19/07/2026, rédigé par l'éditeur](https://chessiro.com/blog/best-chess-analysis-tools)
- **Chessigma** : analyse gratuite avec Stockfish 17, ouvertures identifiées (où l'on sort de la théorie). Offres payantes avec le coach IA « Froggy », un plan quotidien et un rapport « Chess DNA » — [Chessigma](https://chessigma.com/) ; [Chessiro](https://chessiro.com/blog/best-chess-analysis-tools)
- **ChessMonitor** : fusionne les parties Chess.com et Lichess, filtres souples, tendances long terme, statistiques personnalisées (fonctions de base gratuites). La version « Studio » (offres Plus/Pro) ajoute une base Ultra, la recherche de joueurs Chess.com/Lichess, des fichiers de répertoire et Stockfish 19 — [chessmonitor.com](https://www.chessmonitor.com/) ; [résultat de recherche sur le billet Lichess](https://lichess.org/@/ChessMonitor_Stats/blog/introducing-chessmonitor/FWt5cR1E). Le projet est né sur Reddit.
- **Chesscope** : un seul arbre de répertoire construit à partir des parties Lichess/Chess.com ou d'un PGN, avec Stockfish et les statistiques du livre Lichess. Gratuit, sans compte — [AlternativeTo](https://alternativeto.net/software/chesscope/about/)
- **Chessie** : analyse les parties Chess.com importées et transforme gaffes, erreurs et tactiques manquées en puzzles — [Product Hunt](https://www.producthunt.com/p/chessie/chessie-2). **Learn From Your Blunders** fait de même à partir d'un identifiant — [Product Hunt](https://www.producthunt.com/products/learn-from-your-blunders)
- **NextMove Chess** : parties Chess.com et Lichess, motifs récurrents, plan d'étude personnel — [Product Hunt](https://www.producthunt.com/p/nextmove-2/nextmove-chess)
- **Chess Atlas** : outil gratuit d'analyse des faiblesses du répertoire d'ouverture — [blog Lichess](https://lichess.org/@/ChessAtlasApp/blog/i-built-a-free-tool-to-analyze-your-chess-openings-repertoire-weaknesses/UoOVBu2X). **HollowLeaf Repertoire Builder** (versions de janvier 2026) et préparation contre un adversaire — [blog Lichess](https://lichess.org/@/HollowLeaf/blog/repertoire-builder-14-jan-2026-release/QUMETcfi)
- Des développeurs postent régulièrement sur le forum chess.com des outils d'analyse en lot (« fatigué de revoir une partie à la fois ») — [forum chess.com](https://www.chess.com/forum/view/game-analysis/i-got-tired-of-reviewing-one-game-at-a-time-so-i-built-something-different) ; [entraîneur quotidien tiré de vos parties](https://www.chess.com/forum/view/general/i-built-a-daily-chess-trainer-that-works-from-your-own-games-looking-for-testers?lc=1)

### Inférences
- « Puzzles tirés de vos erreurs » est devenu une fonction banale (Chessable PRO, Aimchess, Noctie, Chessiro, Chessie, Learn From Your Blunders). Ce n'est plus un différenciant en soi. Ce qui reste rare : la typologie de l'appli (mats jusqu'au bout, « coups sûrs », exercices d'ouverture tirés des fuites du répertoire).
- Les « fuites » de répertoire déduites de vos propres parties n'existent vraiment que chez Chessbook (contrôle des parties contre le répertoire), Chesscope et Chess Atlas (arbre et faiblesses). Aucun ne les relie à un rapport de coach LLM.
- Les explications en langage naturel sont soit à la position (DecodeChess, assistant ChessBase), soit à la partie (Chessiro, Chessigma). Je n'ai trouvé aucun « rapport de coach » qui synthétise des centaines de parties par cadence, à part peut-être le « Chess DNA » de Chessigma (contenu non vérifié).

### Lacunes
- Je n'ai rien trouvé de fiable sur **chessinsights.xyz**, **ChessTempo** (analyse de parties), **Listudy** ni **ChessPal** : ils ne sont pas sortis dans les recherches. À vérifier directement.
- Le contenu exact du rapport « Chess DNA » de Chessigma n'est pas vérifié.
- Je n'ai pas vérifié si Aimchess analyse encore automatiquement les nouvelles parties en 2026.

## Q2. Tarifs et modèle économique (date de consultation : 14/11/2026 sauf mention)

### À retenir
Le marché se situe entre 6 et 15 $/mois. Les outils de niche à forte valeur perçue sont à 8 $/mois environ (DecodeChess, Chessbook). ChessBase reste en licence logicielle (environ 70 € par produit, bundles à plus de 200 €). Les nouveaux outils web sont presque tous en freemium avec un coach IA payant.

### Constats sourcés
- **Aimchess** : Premium à 9,99 $/mois ou 71,99 $/an (l'équivalent de 5,99 $/mois). Le gratuit donne 15 leçons par jour et des rapports ou statistiques limités — [App Store](https://apps.apple.com/app/id1524941307). Un concurrent cite 15,99 $/mois, chiffre que je n'ai pas pu confirmer — [Chessigma](https://chessigma.com/supercoach).
- **DecodeChess** : gratuit avec 1 Decode Game par jour. Illimité à 8,25 $/mois ou 84 $/an (7 jours remboursables). Packs de crédits à 15 $ (60 crédits) ou 25 $ (120 crédits), valables 12 mois — [tarifs DecodeChess](https://decodechess.com/pricing/)
- **Chessable PRO** : je n'ai trouvé aucun prix officiel. Promotions de type « jusqu'à 6 mois offerts pour un abonnement d'un an ». Abonnement mensuel ou annuel dans l'appli — [App Store](https://apps.apple.com/be/app/chessable/id1523279049). Le modèle est hybride : vente de cours à l'unité plus un abonnement PRO (20 % de remise cumulable avec les soldes, jusqu'à −60 %) — [blog Chessable](https://chess.com/blog/Chessable/new-year-big-changes-to-chessable-pro)
- **Chessbook** : gratuit jusqu'à 400 coups de répertoire. Pro à 7,99 $/mois ou 79,99 $/an. La plateforme web gratuite est décrite comme généreuse — [App Store](https://apps.apple.com/us/app/chessbook/id6466343415). Un écosystème tiers vend des cours au format Chessbook (jusqu'à 100 $ par cours) — [Gumroad](https://pebble85.gumroad.com/l/zdolp)
- **Noctie** : gratuit avec achats intégrés, « Club Noctie » à 14,99 $ — [App Store](https://apps.apple.com/us/app/noctie-chess/id6444289077). Un concurrent cite environ 15 $/mois — [Chessiverse](https://chessiverse.com/compare/chessiverse-vs-noctie)
- **ChessBase / Fritz** : Fritz 20 à 69,90 € (mai 2025), 54,99 $ sur Steam — [ChessBase](https://en.chessbase.com/post/brand-new-release-fritz-20) ; [DekuDeals](https://www.dekudeals.com/items/fritz-chess-20-steam-edition). Bundle CB26 + Fritz 20 à 229,90 € au lieu de 268,80 € (Noël 2025) — [ChessBase](https://en.chessbase.com/post/christmas-offer-chessbase-26-plus-fritz20-the-winning-bundle). Fritz 21 à 69,90 € ; ChessBase pour Mac à 9,95 €/mois ou 99,95 €/an — [page de revue CB26](https://en.chessbase.com/post/review-chessbase-26-the-beginning-of-a-new-era)
- **Chessiro** : revue gratuite et illimitée, quota IA mensuel gratuit, offres payantes avec crédits de coach. **Chessigma** : analyse gratuite, coach IA payant. **ChessMonitor** : profils gratuits, Studio en Plus/Pro (prix non visibles) — [Chessiro](https://chessiro.com/blog/best-chess-analysis-tools) ; [ChessMonitor](https://www.chessmonitor.com/)

### Inférences
- Un prix de 5 à 8 €/mois (ou environ 60 €/an) placerait l'appli dans la fourchette de Chessbook et DecodeChess, sous Noctie et sous l'Aimchess mensuel.
- Le schéma dominant chez les nouveaux venus, « gratuit pour l'analyse moteur, payant pour l'IA », colle à la structure de coûts de l'appli : Stockfish calculé de nuit, coût marginal LLM.

### Lacunes
- Prix officiel de Chessable PRO en 2025-2026 et prix des offres ChessMonitor Plus/Pro.
- Prix exact de ChessBase 26 seul (69,90 € apparaît dans un extrait ambigu, non retenu).

## Q3. Audience et traction

### À retenir
Les acteurs historiques (Aimchess, Chessable) sont adossés à Chess.com, qui revendique plus de 200 millions de membres, mais Aimchess semble délaissé. Chessbook montre une forte satisfaction sur un petit volume. Pour la plupart des nouveaux outils web, je n'ai trouvé aucun chiffre d'usage public.

### Constats sourcés
- Chess.com a racheté Play Magnus Group (Chessable, Aimchess et d'autres) pour environ 82,9 M$ ; finalisation début 2023 selon les sources — [Front Office Sports](https://frontofficesports.com/top-chess-player-platform-join-forces-in-82-9m-deal) ; [Dot Esports](https://vip-develop.dotesports.com/?p=666001)
- Chess.com revendique « plus de 200 millions de membres » (mars 2025) — [State of Chess 2025](https://www.chess.com/news/view/2025-state-of-chess)
- Chess.com a licencié environ 40 personnes en 2024 pour recentrer ses priorités. Le fil Reddit associé évoque le sort des marques PMG — [r/chess via miroir](https://lr.us.psf.lt/r/chess/comments/1dp766a/chesscom_fires_around_40_staff_as_it_prioritizes/laewghe)
- Aimchess sur iOS : 3,9/5 sur 197 notes, sans mise à jour depuis juin 2024 — [App Store](https://apps.apple.com/app/id1524941307)
- Chessbook sur iOS : 4,9/5 sur 2 200 notes — [App Store](https://apps.apple.com/us/app/chessbook/id6466343415). Fondateur Marcus Buffett — [entretien](https://saychess.substack.com/p/an-interview-with-marcus-buffett)
- Aimchess figure sur CB Insights (fiche entreprise) — [CB Insights](https://www.cbinsights.com/company/aimchess). Détail du financement non consulté.

### Inférences
- Le délaissement d'Aimchess (aucune mise à jour depuis plus de 2 ans, pannes non annoncées) laisse vacante la niche « analytique par phase sur toutes vos parties + entraînement ciblé ».
- Chessbook montre que les adultes qui veulent progresser paient pour un outil de répertoire bien conçu.

### Lacunes
- Nombre d'utilisateurs de Chessable, Aimchess, DecodeChess, Chessbook et Noctie ; levées de fonds de DecodeChess, Noctie et Chessbook. Aucune source fiable trouvée.

## Q4. Prise en charge du français

### À retenir
Aucun des outils dont j'ai vu une fiche de langues ne propose le français : Aimchess et Chessbook sont en anglais seulement. Je n'ai pas trouvé de concurrent francophone spécialisé.

### Constats sourcés
- Aimchess sur iOS : anglais uniquement — [App Store](https://apps.apple.com/app/id1524941307)
- Chessbook sur iOS : anglais uniquement — [App Store](https://apps.apple.com/us/app/chessbook/id6466343415)
- ChessBase est un éditeur allemand qui vend historiquement en plusieurs langues, mais la revue de CB26 ne liste pas les langues de l'interface (captures en anglais) — [revue CB26](https://en.chessbase.com/post/review-chessbase-26-the-beginning-of-a-new-era)

### Inférences
- Le français (interface, rapport de coach LLM, explications) est probablement un vrai différenciant. Un LLM permet de produire nativement en français ce que DecodeChess et Chessiro produisent en anglais.

### Lacunes
- Langues de DecodeChess, Chessable (cours en partie traduits ?), Noctie, ChessMonitor et Chessiro : non vérifiées.

## Q5. Avis des utilisateurs : ce qu'ils aiment, ce qu'ils jugent inutile, raisons d'abandon

### À retenir
Plaintes récurrentes : manque de guidage (« une bibliothèque, pas une salle de classe »), absence d'explication du pourquoi, analyses non automatiques des nouvelles parties, bugs et produit délaissé (Aimchess), explications IA génériques ou fausses (ChessBase, Chessbook). Points appréciés : répétition espacée, statistiques à votre niveau, gratuit généreux.

### Constats sourcés
- Aimchess : « home screen lists content without order of difficulty, priority, or duration » (contenu présenté sans ordre de difficulté, de priorité ni de durée), comparé à une bibliothèque plutôt qu'à une salle de classe. On demande aussi des explications sur la valeur d'un coup, **l'analyse automatique des parties nouvellement synchronisées**, des filtres par ouverture, de pouvoir revenir d'un coup en arrière dans l'entraîneur d'ouvertures et d'afficher les coups alternatifs — [App Store](https://apps.apple.com/app/id1524941307)
- Aimchess : prix jugé élevé vu les bugs et la lenteur (agrégateur peu fiable, à prendre avec prudence) — [stork.ai](https://www.stork.ai/en/aimchess). Panne non annoncée et lien 404 depuis Chess.com — [forum chess.com](https://www.chess.com/forum/view/help-support/aimchess-com-down)
- Aimchess et Chessable sont jugés « priced pretty fair » (à un prix plutôt juste) et sont recommandés plutôt que Chess.com Premium pour progresser — [blog chess.com](https://www.chess.com/blog/Pipercody/the-new-prices-and-memberships) ; [Blind](https://www.teamblind.com/post/is-chesscom-premium-worth-it-aczrcgrq)
- Chessable : fil Reddit de janvier 2025, « Chessable responds to critical feedback », réaction aux passages en PRO-only (Short & Sweet, leçons d'essai) — [r/chess via miroir](https://pol1.lr.ggtyler.dev/r/chess/comments/1hxl45y/chessable_responds_to_critical_feedback/m6drgh0/?context=3) ; [blog Chessable](https://chess.com/blog/Chessable/new-year-big-changes-to-chessable-pro)
- Chessbook : forte progression Elo rapportée, éloges pour les statistiques de maîtres et le gratuit, alternative raisonnable à la mémorisation de tableaux si/alors. Critiques : onboarding peu clair, descriptions de coups maigres et parfois fausses, déconseillé aux débutants — [App Store](https://apps.apple.com/us/app/chessbook/id6466343415)
- ChessBase 26 : l'assistant IA contredit parfois Stockfish (léger avantage annoncé contre +2 pour Stockfish), propos génériques, « l'une des options les plus faibles actuellement ». Le filtre par cadence est peu fiable (des parties de blitz apparaissent malgré le filtre) — [revue CB26](https://en.chessbase.com/post/review-chessbase-26-the-beginning-of-a-new-era)
- DecodeChess : pas de dialogue (contrairement aux coachs IA conversationnels) — [stork.ai, peu fiable](https://www.stork.ai/en/decodechess)
- Noctie : « feels like you are playing a human » (on a l'impression de jouer contre un humain) — [App Store](https://apps.apple.com/us/app/noctie-chess/id6444289077). La plupart des « avis » trouvés sont des fiches d'annuaires générées.

### Inférences
- Les points faibles cités sont précisément ce que l'appli fait ou peut faire : analyse nocturne automatique de toutes les nouvelles parties, rapport de coach qui hiérarchise les priorités, filtres fiables par cadence (les données chess.com sont nettes), explications. Le risque est celui de ChessBase : un LLM qui contredit le moteur. Il faut ancrer chaque affirmation du LLM sur les évaluations Stockfish.

### Lacunes
- Je n'ai pas pu collecter directement de fils Reddit r/chess ou r/chessbeginners ni d'avis Trustpilot (recherches non concluantes). Les sentiments rapportés viennent surtout des App Stores et des forums chess.com.

## Q6. Recouvrements avec l'appli et lacunes restantes

### À retenir
Recouvrement le plus fort : **Aimchess** (stats par phase + entraînement sur vos erreurs, mais produit délaissé et sans LLM), **Chessbook** (répertoire + contrôle des parties contre le répertoire, ce qui correspond aux « fuites ») et **Chessiro/Chessigma** (import + revue + puzzles personnels + coach IA par partie). Lacunes encore ouvertes : synthèse LLM sur l'ensemble des parties et par cadence, en français, reliée à des exercices typés et au répertoire déduit.

### Constats sourcés (récapitulatif, voir sources plus haut)
| Fonction de l'appli | Concurrents qui la couvrent |
|---|---|
| Import chess.com par pseudo, analyse auto | Aimchess (Chess.com/Lichess/Chess24), Chessiro, ChessMonitor, Chessie, NextMove, Chessbook (contrôle) |
| Tableaux de bord par cadence / par phase | Aimchess (phases), ChessMonitor (filtres, tendances) ; filtre par cadence de ChessBase jugé peu fiable |
| Rapport de coach LLM | Chessigma (Froggy, « Chess DNA »), Chessiro (par partie), assistant CB26 / AI Chat Fritz 20 (par position) |
| Exercices tirés de vos erreurs | Chessable PRO (Puzzle Connect), Aimchess (Retry Mistakes, Blunder Preventer), Noctie, Chessiro, Chessie, Learn From Your Blunders |
| Rejouer une partie avec courbe d'éval | DecodeChess (graphe), ChessBase, Chessigma/Chessiro |
| Répertoire personnel + fuites | Chessbook, Chesscope, Chess Atlas, HollowLeaf |
| Explications en langage naturel | DecodeChess (le plus abouti, partie par partie), Chessiro, CB26 |
| Français | aucun vérifié |

### Inférences
- Lacunes que l'appli peut occuper : (1) un **rapport global** en français qui hiérarchise les priorités sur toutes les parties et par cadence (la plainte « bibliothèque, pas salle de classe ») ; (2) des exercices de **mat jusqu'au bout** et de **coups sûrs**, typologie absente ailleurs (les autres font des « puzzles de vos erreurs » génériques) ; (3) le lien répertoire → fuites → exercices d'ouverture → rapport, dans une seule boucle ; (4) une analyse profonde de nuit plutôt qu'une revue instantanée peu profonde, cohérente avec le principe « qualité d'analyse d'abord ».
- Menaces : Chess.com peut intégrer nativement Puzzle Connect / Insights (hors périmètre ici) ; Chessbook peut ajouter un LLM ; la multiplication de clones gratuits sur Product Hunt rend la fonction « puzzles de vos erreurs » banale.

### Lacunes
- Je n'ai pas fait de comparaison mains sur clavier : la profondeur réelle d'analyse des concurrents (profondeur Stockfish, temps par coup) n'est pas documentée publiquement.
