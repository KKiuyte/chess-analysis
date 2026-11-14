# Coachs IA d'échecs (2024-2026) et marché francophone

Recherche faite le 2026-11-14. Beaucoup de sources sont des annuaires d'outils IA ou des comparatifs écrits par des concurrents (Chessiro, Chessiverse, Take Take Take). Les prix et les fonctions changent vite. Les données anciennes sont signalées.

## 1. Les coachs IA existants : ce qu'ils font, la qualité des explications, les prix, la traction

### Takeaway
En 2026, le marché est saturé de « coachs IA » : quelques acteurs financés (Take Take Take de Carlsen, Chessigma, Chessiro, Chessiverse, ChessMood) et une longue traîne d'apps solo et de projets GitHub. Les plus sérieux utilisent tous la même architecture : Stockfish/Maia calcule, puis le LLM ne fait que mettre en mots. Les LLM laissés seuls hallucinent beaucoup (environ 22 % de sous-affirmations fausses pour GPT-5.4 sans outils), et la méfiance des joueurs envers les explications IA est réelle.

### Cited Findings
**Panorama et prix (comparatif d'octobre 2026)** — [aitoolsbakery](https://aitoolsbakery.com/blog/best-ai-chess-coach-apps/)
- **Chess.com Coach** : Game Review par moteur, avec un commentaire de « coach ». Chess.com ne le présente pas comme un LLM et il n'y a pas de conversation libre. Les explications à chaque coup sont réservées au niveau Diamond, qui inclut aussi les Insights dans le temps. Le compte gratuit a droit à 1 revue complète par jour. Gold coûte de 4,99 à 6,99 $ et Diamond de 99,99 à 119,99 $, le rythme de facturation n'étant pas précisé.
- **Dr. Wolf** (Chess.com) : coach vocal pour débutants, 5,99 $/mois ou 39,99 $/an, noté 4,8 sur iPhone (27 003 avis). L'app a rejoint Chess.com vers 2020 (donnée ancienne) — [Chess.com news](https://www.chess.com/news/view/dr-wolf-joins-chess-com).
- **Take Take Take** (Carlsen) : revue de partie en langage naturel avec Gemini 3 Flash. Stockfish, des détecteurs de motifs et Maia tournent d'abord, et le modèle ne fait que traduire ces résultats ; l'équipe qualifie son rôle de « volontairement étroit ». L'app est gratuite, sans achat intégré listé. Elle compte plus de 10 000 installations Android et a 125 avis iPhone (4,4) — [aitoolsbakery](https://aitoolsbakery.com/blog/best-ai-chess-coach-apps/). Le coach IA récupère automatiquement les parties Lichess. La société avait levé 90 M NOK en février 2026 (plafond de valorisation de 300 M NOK) — [ai.engineer](https://ai.engineer/orgs/take-take-take). Le lancement initial date d'octobre 2024 — [Euronews](https://www.euronews.com/2024/10/28/chess-grandmaster-magnus-carlsen-on-how-ai-and-tech-are-changing-the-game). La fiche App Store de la nouvelle version date de janvier 2026 et le partenariat Lichess d'avril 2026 — [taketaketake blog](https://taketaketake.com/blog/lichess-partnership). Le modèle économique annoncé est la gratuité, avec publicité ou fonctions premium possibles plus tard.
- **Noctie** : bots « humains » sur 25 niveaux, notes de coups, import Chess.com/Lichess, puzzles tirés des erreurs avec répétition espacée. Pas de LLM ni d'explications rédigées. 13,90 $/mois ou 99,99 $/an, essai de 7 jours — [aitoolsbakery](https://aitoolsbakery.com/blog/best-ai-chess-coach-apps/). D'autres annuaires donnent 15 à 16 $/mois, les sources divergent — [AlternativeTo](https://alternativeto.net/software/noctie-ai/about).
- **ChessMind AI** : revue, plan d'étude et fonction « ChessGPT ». Le modèle utilisé n'est pas indiqué. 9,99 $/mois, 69,99 $/an ou 229,99 $ à vie.
- **Chessiverse** : plus de 1 000 bots. Ses « Coach Insights » lisent toutes les parties revues ensemble : c'est un diagnostic multi-parties. 12,99 $/mois, 89,99 $/an ou 299 $ à vie, avec un niveau gratuit.
- **ChessMood** : scan IA gratuit et plan d'étude, adossés à des cours. 99 à 129 $/mois.
- **Chess Coach: AI Chess Tutor** (développeur solo) : Stockfish 18, au choix Gemini, GPT, Claude, DeepSeek ou Qwen, ou votre propre clé. 5 analyses gratuites, puis des packs de crédits de 2,19 à 3,69 $. Plus de 10 000 installations Android.
- **Chessigma** (fondateurs Mehdi et Eliot ; prix en euros, app App Store en français) : revue de parties, puzzles et parties importées gratuits et illimités. Le coach IA « Froggy » a un quota mensuel (200 ou 400 messages selon le plan ; le tableau est ambigu). Le « Chess DNA report », le plan quotidien personnalisé, Blunder Shield et Blunder Fix sont payants. 12 €/mois, 83 €/an (soit 6,92 €/mois) ou 429 € à vie — [Chessigma pricing](https://www.chessigma.com/pricing). Selon l'App Store, les réponses du coach sont écrites par un modèle d'IA via un service tiers — [App Store](https://apps.apple.com/us/app/chessigma-apprenez-les-%C3%A9checs/id6791621546?l=fr-FR).
- **Chessiro** : analyse Stockfish 19 gratuite et illimitée. Le compte gratuit a 2 explications de coups, 1 question au coach et 1 explication de puzzle par mois. Plus donne 50 crédits par mois et Pro 250. Le coach « apprend votre jeu au fil du temps » et repère les erreurs récurrentes. Il fonctionne en 24 langues, avec la voix. Chessiro reconnaît lui-même que son coach peut « simplifier à l'excès » dans les positions stratégiques complexes, les finales et la théorie — [Chessiro](https://chessiro.com/blog/best-ai-chess-coach).
- **Chessvision.ai** : outil de reconnaissance de diagrammes et de lecture d'e-books. Aucune source ne parle de coach IA — [neura.market](https://www.neura.market/ai-tools-directory/games/chessvision-ai).
- **Autres** : Rookion vend une offre à vie sans limite de parties sur StackSocial ; Chess Journal coûte 5 $ une fois, « sans abonnement » — [Product Hunt](https://www.producthunt.com/products/chess-journal). Il existe aussi ChessNextMove à 9,99 $/mois et ChessGPT à 4,99 $/mois — [dataconomy](https://dataconomy.com/tools/chessgpt-ai-chess-coach/). Sur GitHub, de nombreux clones open source font « Stockfish + LLM sur les parties Chess.com » — [alishaifthikhar/chess-coach](https://github.com/alishaifthikhar/chess-coach), [akmenon1996/LLM-ChessCoach](https://github.com/akmenon1996/LLM-ChessCoach) ; on en parle aussi sur HN — [HN](https://news.ycombinator.com/item?id=43378562).

**Exactitude et hallucinations**
- L'article arXiv 2608.04240 (Hebbar, Sheng, Oh, Viswanath ; août 2026), avec son benchmark ACT-Eval de 325 paires position-coup : GPT-5.4 sans outils produit 22,0 % de sous-affirmations fausses, et les petits modèles open-weight dépassent 40 %. Les outils (moteur, vérification de légalité) améliorent nettement les faits, mais la couverture des idées stratégiques et tactiques d'expert reste limitée pour tous les modèles — [arXiv](https://arxiv.org/abs/2608.04240).
- Le README d'un projet open source avertit que les LLM inventent des coups et des cases s'ils jugent seuls une position. Le projet fonde donc les explications sur des faits vérifiés par le moteur, avec une vérification automatique — [GitHub](https://github.com/alishaifthikhar/chess-coach).
- Sur Reddit (avril 2025), des utilisateurs racontent que ChatGPT perd la position vers le coup 10 et s'effondre vers le coup 20. Renvoyer la position à chaque tour améliore nettement les choses — [r/compsci](https://reddit.birdcat.cafe/r/compsci/comments/1k64ucu/hallucinations_while_playing_chess_with_chatgpt).
- Plaintes d'utilisateurs : un fil du forum Chess.com dit « il y en a une douzaine en ligne, aucun ne me semble utile » — [Chess.com forum](https://www.chess.com/forum/view/general/a-personalized-chess-coach-powered-by-ai). Un billet Lichess s'intitule « AI slop is invading the chess world » (« les LLM sont notoires pour leur confusion et leur fausse assurance ») ; la page a renvoyé une erreur 403 et je n'ai lu que l'extrait — [Lichess](https://lichess.org/@/RuyLopez1000/blog/ai-slop-is-invading-the-chess-world/wakxj7bo). Un test sur Substack conclut que l'outil « n'est pas vraiment fiable » après une fausse affirmation sur une partie de l'auteur — [Substack](https://nickvasquezmd.substack.com/p/the-peril-and-promise).

### Inferences
- Une explication par LLM est devenue banale, et le gratuit est la norme (Take Take Take, revue gratuite chez Chessigma et Chessiro). Elle ne suffit pas à différencier un produit.
- Bien fonder les explications sur le moteur est une condition d'entrée, pas un avantage. La crédibilité se gagne en ne laissant jamais le LLM affirmer une évaluation ou un coup que Stockfish n'a pas fourni.

### Gaps
- Je n'ai trouvé aucune donnée récente sur Play Magnus/Magnus Trainer (absorbé par Chess.com en 2022, hors période) ni sur des fonctions IA de ChessKid.
- Je n'ai pas trouvé d'annonce officielle de Chess.com sur des explications par LLM entre 2025 et 2026.
- Les entreprises ne publient pas de chiffres d'utilisateurs ou d'abonnés pour Take Take Take, Chessigma ou Chessiro.

## 2. Un outil analyse-t-il automatiquement toutes les parties pour en tirer un diagnostic et un plan d'entraînement ?

### Takeaway
Oui, en partie, et c'est une tendance de 2026 : Chessiverse (Coach Insights sur toutes les parties revues), Chessigma (« Chess DNA report » et plan quotidien personnalisé, payants), Chessiro (erreurs récurrentes, sessions selon un profil), ChessMood (scan et plan d'étude) et Rochess. Aucun ne combine clairement toutes ces briques : analyse nocturne automatique de tout l'historique, rapport rédigé façon coach, exercices tirés des erreurs, et répertoire d'ouvertures avec ses « fuites ».

### Cited Findings
- Chessiverse : « Coach Insights reads all reviewed games together » (il lit ensemble toutes les parties revues) — [aitoolsbakery](https://aitoolsbakery.com/blog/best-ai-chess-coach-apps/)
- Chessigma : Chess DNA report, Blunder Shield et plan quotidien « Personalized » réservés aux payants. L'Opening Trainer est limité à 5 lignes en gratuit — [Chessigma](https://www.chessigma.com/pricing)
- Chessiro : « learns how you play over time », repère les erreurs récurrentes, propose Replay Mistakes (puzzles tirés de vos gaffes) et Smart Shuffle (sessions selon votre profil). L'article ne décrit pas de plan formel sur plusieurs mois — [Chessiro](https://chessiro.com/blog/best-ai-chess-coach)
- Take Take Take récupère automatiquement les parties Lichess. Rien n'indique une analyse de chaque partie ni un diagnostic multi-parties — [ai.engineer](https://ai.engineer/orgs/take-take-take)
- Noctie : import des parties et puzzles d'erreurs en répétition espacée. Le diagnostic multi-parties n'est pas mentionné — [aitoolsbakery](https://aitoolsbakery.com/blog/best-ai-chess-coach-apps/)
- Rochess (FR) : « Analyse tes parties. Corrige ce qui revient. » ; il montre ce qui vous coûte le plus de points et propose un plan d'entraînement gratuit. Le Premium ajoute les questions au coach et des puzzles tirés de vos erreurs — [rochess.fr](https://www.rochess.fr/)

### Inferences
- L'idée d'un diagnostic multi-parties est déjà occupée, notamment par Chessigma, qui est francophone et bon marché. La différenciation restante tient à l'exécution : le côté automatique et nocturne, sans clic ; la profondeur d'analyse (pas de baisse de profondeur, contrairement aux analyses navigateur rapides) ; la qualité éditoriale du rapport en français ; et le répertoire d'ouvertures « fuites », moins couvert. Il faut vérifier ce dernier point face à Chessigma et à Aimchess, ce dernier étant traité ailleurs.

### Gaps
- Je n'ai pas testé ces produits en main propre, donc je ne peux pas juger la qualité réelle de leurs rapports multi-parties.
- Je ne sais pas si l'analyse de Chessigma ou Chessiro tourne automatiquement sur toutes les parties, ou seulement à la demande.

## 3. L'offre en français et le marché francophone

### Takeaway
La France est un marché d'échecs en forte croissance : environ 50 000 licenciés FFE en 2019, 81 781 en 2024-2025, plus de 92 000 en 2025-2026 (record), et un objectif de 100 000 en 2026-2027. Plus de 60 % ont moins de 20 ans. Les outils en français existent (Chessigma, Rochess, apps traduites, Chessiro en 24 langues), mais peu sont nés en France ; Chessigma semble l'être, ce qui en fait le concurrent direct.

### Cited Findings
- FFE : 81 781 licenciés en 2024-2025 (+7,40 % sur un an) selon les comptes annuels, et 81 742 au 31 août 2025 dans 964 clubs — [annexe des comptes 2025 FFE](http://www.echecs.asso.fr/(etnsnqjsribe5dzd3uzdszbp)/Actus/15919/AGFFE-2026-Annexe_des_comptes_2025.pdf), [Wikipédia FFE](https://fr.wikipedia.org/wiki/F%C3%A9d%C3%A9ration_fran%C3%A7aise_des_%C3%A9checs)
- Saison 2025-2026 : « plus de 92 000 licenciés », environ un millier de clubs, plus de 60 % de moins de 20 ans, objectif de 100 000 en 2026-2027 (communiqué FFE du 15 septembre 2026) — [Sport Business Club](https://www.sportbusiness.club/echecs-record-de-licencies-a-la-ffe/). Wikipédia donne 92 634 licenciés et 1 009 clubs — [Wikipédia](https://fr.wikipedia.org/wiki/F%C3%A9d%C3%A9ration_fran%C3%A7aise_des_%C3%A9checs).
- 86 049 licences A et B au 10 avril 2026, dont 39 881 primo-licenciés et 58 321 moins de 20 ans — [statistiques.com](https://www.statistiques.com/jeux/echecs). C'est un comptage en cours de saison, d'où l'écart avec le chiffre final.
- Class'Échecs a touché plus de 140 000 élèves en 2024-2025 — [Breizh-info](https://www.breizh-info.com/2025/04/14/245770/championnat-de-france-jeunes-dechecs-a-vichy-1-700-talents-reunis-les-echecs-en-pleine-ascension/)
- Championnat de France 2025 à Vichy : record de participation avec 1 145 joueurs — [FFE Vichy 2025](https://vichy2025.ffechecs.org/record-de-participation-battu-pour-le-championnat-de-france-dechecs-2025-a-vichy/)
- Les moteurs de l'engouement : *Le Jeu de la Dame*, les plateformes en ligne, les lives d'Inoxtag (« des dizaines de milliers de spectateurs »), le Hoop Gambit de Wembanyama — [Sport Business Club](https://www.sportbusiness.club/echecs-record-de-licencies-a-la-ffe/)
- France : environ 23 400 joueurs classés FIDE (mai 2025), l'une des cinq plus grandes populations — [ChessBase](https://en.chessbase.com/post/chess-statistics-today). Lichess compte 111 392 joueurs sur sa page fédération France, une mesure différente — [Lichess](https://lichess.org/fide/federation/France).
- Chess.com revendique plus de 225 M de membres dans le monde en septembre 2025 et ne donne pas de chiffre par pays — [Chess.com stats](https://www.chess.com/terms/chess-stats).
- Streamers : Kevin « Blitzstream » Bordi est le streamer d'échecs français le plus populaire et directeur du contenu français de Chess.com — [Chess.com](https://www.chess.com/article/view/streamer-of-the-month-blitzstream). Il a environ 238 000 abonnés Twitch, environ 777 spectateurs en moyenne sur 30 jours et un pic de 20 122 en janvier 2021 (instantané non daté) — [Streams Charts](https://streamscharts.com/channels/blitzstream).
- Outils en français : Chessigma (app en français, prix en euros) — [App Store](https://apps.apple.com/us/app/chessigma-apprenez-les-%C3%A9checs/id6791621546?l=fr-FR) ; Rochess.fr (analyse dans le navigateur, plan gratuit, Premium dont le prix n'est pas affiché) — [rochess.fr](https://www.rochess.fr/) ; « Analyse Échecs: Chess AI », éditeur basé en Nouvelle-Écosse — [App Store FR](https://apps.apple.com/fr/app/analyse-%C3%A9checs-chess-ai/id6742461009) ; projet open source français « Analyse tes parties… Stockfish + explications IA », avec clé Gemini ou Anthropic — [GitHub](https://github.com/Juleslassoeur/chess-coach) ; Chessiro en 24 langues — [Chessiro](https://chessiro.com/blog/best-ai-chess-coach).
- Cours particuliers en France : 20 à 80 €/h en général — [Groupe Réussite](https://groupe-reussite.fr/ressources/cp-sport-tarifs-cours-echecs/). Moyenne Superprof de 20 €/h à Chevreuse et 33 €/h à Nantes — [Superprof Nantes](https://www.superprof.fr/cours/echecs/nantes/). Un GMI à 2600 Elo demande 100 €/h — [Superprof](https://www.superprof.fr/grand-maitre-international-2600-elo-multiple-champion-france-numero-francais-membre-equipe-france-places.html). D'autres profils vont de 19 €/h à 85 €/h en webcam.

### Inferences
- Les 92 000 licenciés ne sont qu'un plancher : la grande majorité des joueurs en ligne français ne sont pas licenciés. Les jeunes (60 %) ont un faible pouvoir d'achat, mais leurs parents sont des acheteurs potentiels. Les adultes licenciés et les joueurs en ligne de 1000 à 1800 Elo sont le cœur de cible.
- Prix d'ancrage : une heure de cours humain coûte 20 à 80 €. Un abonnement de 5 à 10 €/mois vaut donc moins d'un quart d'heure de cours, ce qui donne un argument de valeur clair.
- Chessigma (français, 6,92 à 12 €/mois, revue gratuite, rapport « DNA ») est le concurrent le plus direct à étudier en détail.

### Gaps
- Je n'ai trouvé aucune donnée publique sur le nombre d'utilisateurs français de Chess.com ou de Lichess.
- Je n'ai pas trouvé de chiffres récents et datés d'audience pour les streamers (Blitzstream, Inoxtag, autres coachs YouTube).
- Je n'ai pas trouvé de services français identifiés d'« analyse de vos parties » vendus par des coachs YouTube ou Twitch, ni leurs tarifs.
- Je n'ai pas vérifié la nationalité exacte de Chessigma ; elle se déduit des prénoms, de l'interface française et des prix en euros.

## 4. Disposition à payer et taux de conversion freemium

### Takeaway
Les joueurs amateurs veulent une meilleure revue de leurs parties mais rechignent à payer un abonnement « pour qu'un ordinateur me dise que j'ai lâché mon fou ». Le marché répond par le gratuit, l'achat unique ou le « lifetime ». Les prix acceptés se situent autour de 5 à 15 $/mois ou 40 à 100 $/an. En freemium, la conversion médiane tourne autour de 2 %.

### Cited Findings
- Forum Chess.com : « you shouldn't have to pay a monthly subscription just to let a computer tell you that you hung your bishop on move 12 » (on ne devrait pas payer un abonnement pour qu'un ordinateur vous dise que vous avez lâché votre fou au 12e coup) — [Chess.com forum](https://www.chess.com/forum/view/general/a-personalized-chess-coach-powered-by-ai). Un blog Chess.com de 2026 s'intitule « Stop Paying for Chess Analysis: The 4 Best Free Tools » — [Chess.com blog](https://www.chess.com/blog/Alexander-PC/stop-paying-for-chess-analysis-the-4-best-free-tools-in-2026).
- Fourchettes de prix observées : Dr. Wolf à 39,99 $/an ; Noctie à 99,99 $/an ; Chessiverse à 89,99 $/an ; ChessMind à 69,99 $/an ; Chessigma à 83 €/an ; offres à vie entre 229 et 429 € ; achat unique de 5 $ pour Chess Journal — [aitoolsbakery](https://aitoolsbakery.com/blog/best-ai-chess-coach-apps/), [Chessigma](https://www.chessigma.com/pricing), [Product Hunt](https://www.producthunt.com/products/chess-journal)
- RevenueCat 2026, sur des données 2025 : conversion médiane de l'essai au payant à 35 jours de 10,7 % avec un paywall strict, contre 2,1 % en freemium. Le chiffre freemium est stable depuis 2025 — [RevenueCat](https://revenuecat.com/blog/growth/subscription-app-trends-benchmarks-2026). La rétention à 1 an est proche dans les deux modèles (27 % et 28 %), selon un résumé secondaire non vérifié à la source. Selon RevenueCat, les apps IA gagnent 41 % de plus par utilisateur mais perdent leurs abonnés 30 % plus vite — [PPC Land](https://ppc.land/ai-apps-earn-41-more-per-user-but-churn-30-faster-revenuecat-finds/).
- Adapty : environ 2,6 % du freemium vers le payant ; une fourchette « bonne » de 3 à 5 % est citée sans source — [Adapty](https://adapty.io/blog/freemium-app-monetization-strategies/).

### Inferences
- Pour une petite app web française, un scénario prudent table sur environ 2 % de payants parmi les actifs. Avec 1 000 utilisateurs actifs, cela fait 20 abonnés, soit environ 100 à 200 €/mois. La rentabilité suppose une audience de quelques milliers d'utilisateurs, ou un partenariat avec un club, un streamer ou la FFE.
- Pistes de modèle compatibles avec la réticence à l'abonnement : un essai gratuit du rapport complet (premier rapport offert), puis un abonnement annuel bon marché (40 à 60 €/an) ; une offre « club » B2B2C pour les clubs FFE ; éventuellement un achat unique d'un rapport approfondi.

### Gaps
- Je n'ai trouvé aucun sondage spécifique aux échecs sur la disposition à payer, ni de taux de conversion publiés par un acteur des échecs.
- La recherche Reddit est limitée : je n'ai pas trouvé de vrai fil r/chess avec sondage.

## 5. Coût des LLM et façon dont les concurrents limitent l'IA

### Takeaway
Les concurrents mettent l'analyse moteur gratuitement à disposition et rationnent la partie LLM par crédits ou quotas mensuels, ou la réservent aux payants : Chessiro donne 2 explications par mois en gratuit, puis 50 ou 250 crédits ; Chessigma a un quota de messages au coach ; Chess Coach AI vend des packs de crédits. Take Take Take, financé, rend l'IA gratuite avec un modèle bon marché (Gemini 3 Flash).

### Cited Findings
- Chessiro : analyse moteur illimitée gratuite. Le gratuit donne 2 explications de coups, 1 question au coach et 1 explication de puzzle par mois ; Plus offre 50 crédits par mois et Pro 250 — [Chessiro](https://chessiro.com/blog/best-ai-chess-coach)
- Chessigma : revue gratuite illimitée, quota mensuel de messages au coach « Froggy », rapport et plan personnalisé payants — [Chessigma](https://www.chessigma.com/pricing)
- Chess Coach: AI Chess Tutor : 5 analyses gratuites, packs de crédits de 2,19 à 3,69 $, ou votre propre clé API — [aitoolsbakery](https://aitoolsbakery.com/blog/best-ai-chess-coach-apps/)
- Chess.com : 1 revue par jour en gratuit, explications à chaque coup réservées à Diamond — [aitoolsbakery](https://aitoolsbakery.com/blog/best-ai-chess-coach-apps/)
- Take Take Take : Gemini 3 Flash, un modèle léger, utilisé de façon étroite (traduction des résultats moteur) — [aitoolsbakery](https://aitoolsbakery.com/blog/best-ai-chess-coach-apps/)

### Inferences
- Un rapport de synthèse hebdomadaire ou nocturne par utilisateur, nourri des faits moteur, ne coûte probablement que quelques centimes par rapport. C'est une estimation non sourcée ici, à vérifier avec la grille tarifaire Claude et un comptage réel de tokens. Le coût dominant sera plutôt le calcul Stockfish profond sur tout l'historique, si on ne baisse pas la profondeur.
- Le modèle de limitation qui s'impose : moteur et revue gratuits, LLM rationné. Une app qui offre le rapport rédigé comme pièce maîtresse devrait plutôt rationner le nombre de parties analysées en profondeur ou la fréquence des rapports.

### Gaps
- Aucun concurrent ne publie son coût réel par rapport ou par explication.
