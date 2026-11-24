# Audit de bugs et corrections — 0.113.2

**Bilan daté du 24 novembre 2026.** Recherche systématique de défauts menée à la
demande de Louis : relecture du code par zone, envoi d'entrées invalides aux
188 routes de l'API (client de test FastAPI, services simulés) et reproduction
de chaque piste par un petit script. Exécuté sur le runner CPU, sans modèle IA,
sans corpus et sans Windows réel. La suite complète passait avant l'audit
(1362 tests) : les défauts ci-dessous étaient hors de sa couverture. Chaque
correction a reçu un test de non-régression.

## Défauts corrigés

| Domaine | Défaut constaté | Correction |
| --- | --- | --- |
| Index des guides | Après un échec (dossier non monté au démarrage, fichier illisible), l'actualisation automatique ne reprenait jamais ; `/api/health` gardait `index` dégradé. | Nouvel essai dès que le dossier change ; l'état dégradé s'efface après une indexation réussie. |
| Téléchargement documentaire | `content.py download --lab` sans `--no-refresh` s'arrêtait sur `NameError` après le téléchargement. | Import local corrigé ; test du redémarrage Kiwix/pilote. |
| Contrôles de traduction (version 11) | Unités composées ou absentes acceptées (`mg/h` → `mg/min`, `kcal` → `kJ`, `mV` → `µV`) ; dose échangée avec un numéro de page acceptée ; `10 – 20 mg` bloqué à tort ; « ſ » faisait échouer le contrôle. | Débits comparés avec leurs deux unités, liste d'unités élargie, échange refusé, tiret de plage distingué du signe, recherche d'unité robuste. |
| Inventaire vidéo ZIM | Une balise `<base href>` sans valeur arrêtait l'inventaire de toute l'archive, à chaque relance. | Attributs sans valeur traités comme vides, comme dans les autres analyseurs. |
| Conversations | `folder_id: ""` provoquait une erreur 503 et marquait la fonction dégradée ; la recherche ne trouvait pas « École » avec « école ». | Vide = Sans dossier ; recherche insensible à la casse et aux accents. |
| Assistant | Une question contenant « code » (« code postal ») laissait un appel d'outil JSON brut s'afficher comme réponse ; `1/0` donnait un message générique. | Détection limitée aux questions de programmation ; message « Division par zéro » transmis au modèle. |
| Lecture disque Kiwix | Une erreur du fil de lecture après une annulation remplaçait l'annulation ou le délai dépassé. | L'annulation reste prioritaire, après la fin du fil. |
| Transcription | Des sous-titres reconnus qui se chevauchent étaient refusés par le contrôle d'unité : le même passage échouait à chaque reprise. | Le sous-titre suivant commence à la fin du précédent (ou le rejoint) ; l'anomalie `recognition_overlap` reste enregistrée. |
| Files vidéo | Des tâches restées `running` après un plantage occupaient les places de la file jusqu'à l'ouverture de la liste. | Seules les tâches réellement actives dans le processus comptent. |
| Restauration Windows | Sous Windows PowerShell 5.1, une sortie d'erreur de la préparation pouvait interrompre la restauration et perdre son code (dont 3010). | Même protection que `update-windows.ps1`. **Non testé sous Windows.** |
| Divers | Réindexation sans dossier : 500 brut ; téléversement laissant un fichier orphelin si l'index échoue ; `inference.json`/`network.json` valides mais non objets ; minimum d'espace libre ignorant 0 ; libellés `all_nopic`/`all_maxi` ; sections « Références culturelles » prises pour des annexes ; surveillance d'une phase de routage liée à la phase suivante ; messages techniques bruts dans les cartes et la recherche ; profil non changé si le stockage du navigateur est bloqué. | Messages compréhensibles, nettoyage, valeurs par défaut sûres et liaisons corrigées. |

## Pistes écartées après vérification

- Ollama écoute `0.0.0.0:11435` sous Windows : le pare-feu installé par
  `open-lan-firewall.ps1` bloque déjà 11435 et 11436 sur les interfaces physiques.
- Suppression des archives hors référence par « Revenir à l'état de la
  référence » : comportement documenté et confirmé avant exécution.
- Jeton d'accès d'itinéraire non textuel : refusé en amont par la validation HTTP.
- Banc de traduction contrôlé sans les options de la production : laissé en
  l'état, Louis jugeant les traductions secondaires (24 novembre 2026).

## Limites

- Aucun essai Windows, iPhone, modèle réel ni Whisper réel. Le chevauchement de
  transcription est reproduit avec des horodatages synthétiques.
- Les contrôles de traduction restent conservateurs et ne valident pas le sens :
  un échange entre deux nombres sans unité ni libellé n'est pas détectable.
