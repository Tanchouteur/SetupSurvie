# Trouver les vidéos — 0.40.0

**Bilan daté du 17 novembre 2026.** Essais dans le runner de développement
(CPU, sans modèle ni Internet), sur de petites vidéos fictives. Aucun essai sur
les PC de Marc ou de Louis : le PC Bazzite n’était pas joignable pendant ce
travail.

## Constat de départ

En voulant tester le sous-titrage, Louis ne trouvait pas les vidéos chez Marc
(0.38.3, captures du 17 novembre) :

- la recherche mélangeait vidéos et documents, sans moyen d’afficher seulement
  les vidéos. Elle exigeait aussi un mot-clé, et l’espace « Autonomie et
  résilience » pouvait écarter des vidéos non classées ;
- le répertoire des vidéos ne se créait que par un clic volontaire dans
  Collections. Tant que personne ne l’avait fait, aucune vidéo n’était trouvable ;
- à « Cherche une vidéo sur comment faire du feu » puis « trouve une vidéo de
  n’importe quoi dans la bibliothèque », l’assistant a répondu qu’aucune vidéo
  n’était indexée. Il n’avait aucun outil pour lister les vidéos ni donner leur
  lien, et ne distinguait pas « pas encore répertorié » de « absent ».

Un premier travail d’un autre agent sur l’API (filtre `kind`, liste sans
mot-clé) avait été interrompu sans commit. Il a été repris, corrigé et complété
dans cette livraison.

## Ce qui a changé

- `GET /api/search?kind=all|documents|videos`. En mode `videos`, une requête vide
  liste les vidéos par titre, l’espace documentaire est ignoré, et la couverture
  indique l’état du répertoire : non créé, en cours d’actualisation, dossier
  absent, partiel.
- Le répertoire des vidéos locales se met à jour seul au démarrage, puis au plus
  une fois par minute lors d’une recherche si les fichiers ont changé (noms,
  tailles, dates). Les téléchargements inachevés sont ignorés, et l’ancien
  répertoire reste consultable pendant l’actualisation. Un arrêt volontaire est
  respecté tant que les fichiers ne changent pas ; une interruption par
  redémarrage est reprise.
- Portail : menu **Documents et vidéos / Vidéos uniquement / Documents
  uniquement**, conservé dans l’adresse de la page.
- Assistant : outil `find_videos`. Quand la question parle de vidéo, une
  recherche de vidéos est faite avant le modèle, sans mot-clé si la demande est
  générale. Si rien ne correspond au sujet, l’assistant reçoit quelques autres
  vidéos et leur nombre total. Il reçoit pour chaque vidéo un lien `open_url` qui
  ouvre le lecteur. Les liens réels sont ajoutés à la fin de la réponse si le
  modèle les oublie.

## Vérifications exécutées

| Vérification | Résultat |
| --- | --- |
| `tests/test_video_search.py` : 12 tests (filtre, liste sans mot-clé, actualisation automatique, fichiers `.part`, arrêt volontaire ou par redémarrage, recherche pendant l’actualisation, API HTTP, détection des demandes, liens ajoutés, quatre scénarios d’assistant avec moteur simulé, dont une liste de repli hors sujet qui n’est pas ajoutée comme résultat ; arrêt du service avec un inventaire annulé ou d’une autre boucle) | réussis |
| Suite complète `python -m unittest discover -s tests` (runner, Python 3.13) | 1026 tests réussis, 6 ignorés, après intégration de `main` (0.39.0) |
| `tests/search_processing_smoke.py` | réussi |
| `tests/profile_proxy_smoke.py` | non exécutable dans le runner (Docker Caddy absent, même échec sur `main`) ; laissé à la CI GitHub |
| `tests/browser_video_search.py` : API et portail réels dans Chromium (image Playwright du runner), affichage ordinateur et téléphone (format iPhone 13 émulé) : 17 contrôles | réussis |

Contrôles du navigateur : répertoire créé sans clic au démarrage ; menu visible ;
recherche vide en mode vidéos qui affiche les deux vidéos par titre ; choix
conservé dans l’adresse ; mot-clé limité aux vidéos ; « Documents uniquement »
sans vidéo ; lien de l’assistant qui ouvre le lecteur ; aucune erreur JavaScript.

La première CI GitHub a révélé deux défauts, corrigés : le libellé « document(s) »
attendu par un essai navigateur (désormais « résultat(s) » en mode mixte), et,
sous Windows, un arrêt du service bloqué par l’annulation de l’inventaire
automatique.

Deux tests existants de budget de contexte ont révélé que chaque phrase ajoutée
aux consignes permanentes réduit la place des passages lus. En conséquence, la
consigne vidéo n’est envoyée que lorsque la question parle de vidéo, et
`find_videos` n’est proposé au premier tour des questions documentaires que dans
ce cas.

## Limites et validations restantes

- **Aucun vrai modèle n’a été interrogé.** La présentation des liens par
  GPT-OSS ou les autres profils reste à mesurer sur les PC cibles. L’ajout
  automatique des liens protège seulement contre leur oubli.
- La détection de la demande repose sur les mots « vidéo » et « YouTube ». Une
  demande comme « montre-moi comment faire » sans ce mot reste une recherche
  documentaire ordinaire, qui inclut d’ailleurs les vidéos.
- Non testés : WebKit, un vrai iPhone, Windows chez Marc, un dossier de plusieurs
  milliers de vidéos (durée du contrôle des fichiers).
- Les vidéos incluses dans les ZIM demandent toujours leur examen volontaire.
  Avant cet examen, la couverture reste « partielle ».
- Le dossier lu reste `library/video/`. Louis a parlé de `library/videos/` :
  à confirmer, voir le [plan YouTube](../decisions/telechargement-videos-youtube.md).
