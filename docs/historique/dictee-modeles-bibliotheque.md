# Dictée, trois modèles et bibliothèque — 11 novembre 2026

> Archive — document conservé pour retracer les propositions et le prototype initial. Les constats et commandes décrivent cette étape ; pour installer le pilote actuel, suivre le [guide Marc](../installation/pilote-marc.md).

## Choix confirmés

Le périmètre documentaire était déjà convenu dans les documents 03 et 11 :
Wikipédia français **avec illustrations**, bibliothèque française et anglaise,
accès direct sans IA, notamment sur téléphone. Kiwix était déjà retenu et installé.
Le problème constaté était un catalogue vide, pas un choix de bibliothèque à refaire.

Louis demande aussi au moins trois tailles de modèles, avec des noms simples dans
le sélecteur. Le plafond de stockage actuel est **600 Go**, appliqué par le volume
de 590 Go décrit dans le document 17. Tous les nouveaux téléchargements restent
dans ce volume sur le SSD Crucial de 4 To.

## Dictée hors ligne

L'erreur de transcription provenait du modèle Whisper absent : Open WebUI était
correctement en mode hors ligne, mais la préparation initiale n'avait téléchargé
que le modèle de dialogue et les embeddings. Le mode hors ligne est conservé.

`Systran/faster-whisper-small`, révision
`536b0662742c02347bc0e980a01041f333bce120`, est désormais préparé dans
`data/state/openwebui/cache/whisper/faster-whisper-small`. Son chemin absolu dans
le conteneur est configuré comme modèle de dictée. Il travaille sur CPU en int8,
sans prendre de VRAM à l'assistant. La révision est fixée dans `deploy/versions.json`.

Commande de préparation explicite :

```bash
./scripts/lab.sh prepare-speech
```

Après changement de configuration, recréer le conteneur Open WebUI en conservant
son dossier de données ; un simple `start` ne remplace pas l'environnement d'un
conteneur déjà créé. L'intervention du 11 novembre l'a effectué.

Essais : fichier WAV français produit avec eSpeak, transcription par le véritable
point d'accès `/api/v1/audio/transcriptions`, puis chargement et transcription dans
un conteneur `--network=none`, cache monté en lecture seule. Les deux fonctionnent
sans l'erreur de snapshot manquant. La phrase de synthèse est partiellement
reconnue, avec des erreurs : ce test valide le câblage et la disponibilité locale,
pas la précision sur une voix humaine. Essai micro réel encore nécessaire.
Résultats dans `results/dictee-api-test.json` et `results/dictee-offline-test.json`.

## Les trois choix dans l'assistant

| Nom affiché | Modèle local | Raisonnement par défaut |
| --- | --- | --- |
| Réponse rapide · Qwen3.5 4B | `qwen3.5:4b-q4_K_M` | Désactivé |
| Réponse moyenne · Qwen3.5 9B | `qwen3.5:9b-q4_K_M` | Activé |
| Réponse approfondie · Qwen3.5 27B | `qwen3.5:27b-q4_K_M` | Activé |

Les trois modèles ont été téléchargés. Le nom lisible est enregistré dans les
métadonnées Open WebUI en conservant l'identifiant natif : aucun poids dupliqué,
aucun alias ambigu dans les relevés. `python3 scripts/lab_models.py` réapplique
ces noms sans effacer les conversations. Contexte de départ : 4 096 tokens ; un
seul modèle chargé à la fois. La limite de RAM du conteneur Ollama passe de 12 à
22 Gio, avec un plafond mémoire + swap de 24 Gio, pour permettre le 27B hybride.
Cela ne réserve pas cette mémoire en permanence.

### Première comparaison

Trois cas, trois répétitions par modèle, même prompt, Q4_K_M, contexte 4 096,
sortie plafonnée à 256 tokens, température 0, seed 42, raisonnement désactivé.
Les téléchargements et l'activité du PC continuent : les chiffres décrivent cet
environnement, pas un classement matériel en conditions contrôlées.

| Taille | Médiane de génération à chaud | Calcul de réserve : résultat observé |
| --- | --- | --- |
| 4B | 40,06 tokens/s | Faux : 32 jours et 4 litres, sur les trois répétitions |
| 9B | 13,68 tokens/s | Faux : 32 jours et 48 litres, sur les trois répétitions |
| 27B | 3,65 tokens/s | Commence faux puis se corrige à 33 jours et 6 litres ; réponse contradictoire |

Addition et restitution du document anglais ALPHA réussissent dans cette série.
Le 4B avait donné la bonne réponse au calcul lors de la première session du
document 17 : conserver les deux séries, sans présenter le premier succès comme
une preuve de fiabilité. Le placement GPU automatique a varié ; les valeurs
`size` et `size_vram`, compteurs, réponses et relevés RAM/swap sont enregistrés.
La première session avait atteint environ 79 tokens/s sur le 4B entièrement
chargé sur GPU ; elle n'est pas directement comparable à cette nouvelle série.

Résultats : `results/comparison-4b.json`, `comparison-9b.json`, `comparison-27b.json`.
Le script accepte maintenant `--model`, `--repetitions` et `--output`.

Une deuxième condition réactive le raisonnement pour le calcul, avec un plafond
de 1 536 tokens : les modèles 4B et 9B donnent cette fois 33 jours et 6 litres,
en respectivement 12,84 et 45,32 secondes, chargement éventuel compris. Le 27B
répond aussi correctement, en **343,94 secondes** (environ 5 min 44 s).
Les trois réponses complètes sont dans `results/comparison-thinking.json`.
Ces essais motivent le raisonnement
sur les deux choix les plus lents ; ils ne suffisent pas à désigner le meilleur
modèle sur les usages réels. Le calcul déterministe et un corpus plus exigeant
restent nécessaires pour évaluer le rendement qualité/temps.

## Wikipédia et accueil

Archive retenue : `wikipedia_fr_all_maxi_2026-05.zim`, **55 438 794 004 octets**.
Empreinte SHA-256 publiée par Kiwix :
`61401b1b3618afe736450a868c7205f572f590db310e044a9c72b51fbfcfb431`.
Source : [répertoire officiel](https://download.kiwix.org/zim/wikipedia/) et
[Metallink des miroirs et empreintes](https://download.kiwix.org/zim/wikipedia/wikipedia_fr_all_maxi_2026-05.zim.meta4).

`python3 scripts/lab_library.py` télécharge avec reprise dans un fichier `.zim.part`,
à partir des miroirs annoncés par Kiwix. Les plages reçues doivent répondre 206
avec le bon `Content-Range`. Les plages terminées sont enregistrées après
synchronisation disque. L'archive n'est publiée en `.zim` et Kiwix n'est redémarré
qu'après validation de la taille et de l'empreinte complète. Le catalogue de
l'accueil montre la préparation puis la disponibilité ; il ne présente pas un
téléchargement partiel comme une bibliothèque prête.

L'accueil est simplifié pour les personnes sans connaissances informatiques :

- Deux actions : **Chercher une information** et **Poser une question**.
- Une seule recherche pour les articles Wikipédia et les titres des guides.
- Des résultats nommés « Article Wikipédia » et « Guide », des titres lisibles,
  et la copie texte ALPHA masquée lorsqu'un original illustré existe.
- Des messages d'installation, d'absence de langue et d'indisponibilité lisibles,
  sans vocabulaire Kiwix/ZIM/import dans le parcours normal.
- Un relais HTTP local limité aux deux points d'accès nécessaires de Kiwix,
  pour afficher les résultats dans l'accueil sans requêtes entre origines.

La recherche utilise l'[API publique Kiwix](https://kiwix-tools.readthedocs.io/en/latest/kiwix-serve.html),
avec sélection de langue et réponse XML. Elle ne constitue pas encore une
indexation du texte de tous les PDF ni un connecteur entre Wikipédia et l'IA.
Ces étapes restent distinctes de l'accès direct aux articles illustrés.

### Vérifications après installation

L'archive française est téléchargée, son SHA-256 complet correspond, et Kiwix
l'a chargée. L'ancienne URL utilisateur de recherche française répond maintenant
avec des résultats. Dans le navigateur, « électricité » affiche 12 articles sur
l'accueil ; le premier lien ouvre bien l'article local « Électricité de Strasbourg ».
L'article général « Électricité » est aussi accessible directement : son HTML
contient 28 images locales et une illustration WebP a été effectivement servie
en HTTP 200 depuis l'archive. Le classement des résultats natifs reste à améliorer.

Le navigateur a vérifié une seule zone de recherche, un champ suffisamment large
sur ordinateur, et aucun débordement horizontal, y compris avec une largeur de
contenu contrainte à 390 px. Les captures et relevés sont dans
`results/portal-search-ready.png`, `portal-desktop.png`, `portal-mobile.png`,
`portal-search-test.json`, `portal-ui-test.json` et `wikipedia-illustrations-test.json`.
Le téléphone réel reste à tester. Les outils de navigateur temporaires et leurs
caches sont dans le volume dédié ; le navigateur de vérification est arrêté.

18 tests unitaires passent, dont reprise du téléchargement par plages et refus
d'un serveur ignorant les plages. La compilation Python, la configuration Caddy,
les parcours de recherche dans le navigateur et un appel réel du profil rapide
par Open WebUI ont été vérifiés. L'intégration Docker Compose reste non exécutée
sur ce PC sans Docker. L'occupation physique du fichier de stockage est d'environ
**96,4 Go**, sous le plafond de 600 Go.

## Seconde phase : interface

Louis demande explicitement une refonte ultérieure, plus originale et plus claire,
pour des personnes sans connaissance de l'informatique ou de l'IA. L'accueil
actuel constitue une simplification fonctionnelle, pas la refonte finale.
Prévoir un parcours cohérent de recherche, lecture et aide, une présentation des
sources immédiatement compréhensible, une vraie adaptation au téléphone et des
essais avec des personnes découvrant le produit. Les notions de serveur, moteur,
archives, import et indexation appartiennent aux réglages de maintenance.

Les fichiers CSS et JavaScript de l'accueil sont désormais versionnés dans leurs
URL ; le serveur demande leur revalidation. Une capture utilisateur montrait
le nouveau HTML avec l'ancienne feuille de style en cache.
