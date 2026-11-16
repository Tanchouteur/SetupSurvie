# Coordination du transfert et du chantier vidéo

**Suivi d’intégration — 16 novembre 2026, branche `codex/transfert-fiable`.**
Base initiale : `a7f742b`, logiciel 0.25.0. Louis signale un chantier vidéo avec
une 0.26.0 en préparation ; aucune version finale de transfert n’est réservée
avant synchronisation et intégration. Ce fichier ne déclare pas une coordination
humaine terminée ni une fusion déjà effectuée.

## Périmètre et fichiers partagés

Le transfert ajoute ses propres scripts et tests, réutilise les verrous et
l’arrêt documentaire existants, puis ajoute des garde-fous aux points d’entrée
`setup.py`, `control.py`, `pilot_update.py` et aux lanceurs Windows.
Il ne modifie ni moteurs de recherche/conversation, ni Compose, ni
`scripts/linux_lab.py`, ni le générateur du portail, ni l’API.

La seule modification CI est l’ajout des deux commandes de tests de transfert
au travail Windows existant dans `.github/workflows/tests.yml`. Les scénarios
Linux sont déjà ramassés par la découverte générale.

Les lanceurs et guides sont dans le périmètre transfert. Les ajouts indépendants
aux guides, à la CI et aux scripts partagés doivent être relus au moment de
synchroniser avec `main`, sans remplacement par une ancienne copie.

## Contrat à vérifier avec la 0.26.0 vidéo

- Les vidéos, sous-titres, modèles et caches dans `data` sont inventoriés même
  s’ils ne figurent pas au catalogue. Les travaux et bases sous `private` ou
  `data/state` sont conservés. Les fichiers incomplets gardent leur statut.
- Un nouveau répertoire d’état externe ou un montage hors des trois racines
  déclarées doit rejoindre l’inventaire ou provoquer un refus explicite.
- Les environnements Python ne sont pas portables par simple copie. L’adaptateur
  actuel régénère `private/search-tools` depuis ses roues vérifiées. Tout autre
  `pyvenv.cfg` détecté bloque l’examen avant arrêt. **Si la vidéo ajoute un venv,
  il faut ajouter son adaptateur et le cache hors ligne avant d’annoncer le
  transfert compatible 0.26.0.** Ne pas contourner ce refus par une exclusion.
- Les nouveaux processus détachés qui écrivent doivent participer à l’arrêt
  coopératif/verrou de maintenance ; le transfert ne tue pas de PID inconnu.
- Les nouveaux chemins hôte dans JSON/catalogues et fichiers opérationnels
  doivent être relocalisés. Les textes de conversations et les IDs ne sont
  jamais remplacés globalement.
- La reprise d’inférence reste volontaire, sans démarrage implicite d’une
  transcription, traduction ou génération après la bascule.

## Lecture du chantier vidéo distant

La branche distante `codex/video-audio-transcription`, commit `55d81ab`, a été
lue sans modification. Elle prépare 0.26.0 et ajoute
`state/pilot/video-transcriptions.db`, utilise le cache Whisper déjà sous
`state/openwebui/cache/whisper` et stocke ses publications dans les ressources
existantes. Ces dossiers sont inclus par l’inventaire générique du transfert.
Son arrêt FastAPI appelle `transcriptions.stop_all()` avant fermeture ; le
processus audio enfant appartient au conteneur pilote arrêté par Compose.
Aucun nouveau venv hôte n’a été relevé dans cette lecture. Cela ne remplace pas
une recette de transcription en cours au moment du transfert après intégration.
Ses ajouts Compose (`versions.json`), Linux, API, portail et versions doivent
être conservés. Aucun de ces fichiers n’a été copié depuis cette branche vers
la nôtre ; cette lecture ne vaut pas fusion ni accord de l’autre agent.

## Revue indépendante

Les dix-huit tests initiaux passent dans le runner. La revue reproduit puis
corrige le refus des routeurs OSRM sans HEALTHCHECK et le retour source pendant
maintenance. Un nouveau contrôle conserve ensemble les états vidéo, pistes et
cache Whisper. L'horloge du test de délai Kiwix est rendue déterministe sans
changer le moteur. La [preuve datée](../essais/2026-11-16-transfert-fiable.md)
distingue ces tests de la recette physique non exécutée.

## Intégration à effectuer

1. Vérifier le dépôt et récupérer `origin/main` sans écraser de travail.
2. Relire les modifications vidéo par rapport à la base et appliquer le contrat
   ci-dessus. Résoudre les conflits fichier par fichier.
3. Attribuer une version **mineure** à la livraison intégrée, car le transfert
   est une fonctionnalité significative ; si 0.26.0 est déjà livrée, utiliser
   0.27.0. Si la livraison reste commune, décider ensemble de son numéro final.
   Synchroniser manifeste, API et version affichée par le mécanisme existant.
4. Refaire la suite complète, les contrôles Windows de CI, le paquet compatible
   0.1.16 et les tests de transfert après synchronisation.
5. Fusionner uniquement après contrôles et coordination, puis vérifier le commit
   distant. Préparer le paquet exact pour Marc et consigner sa recette SSD.

Les tests sur fixtures ne valident pas le déplacement physique chez Marc. La
reconstruction complète d’un autre Windows sans prérequis et la conversion
Windows/Linux restent des travaux distincts du protocole de secours.

## Synchronisation effectuée pour la recette 0.27.0

La revue `38374f4` est jointe au main vidéo `9a7e687`, sans rebase ni perte des
ajouts Compose/API/portail/CI. La version candidate devient 0.27.0 : nouvelle
fonction de transfert compatible, donc niveau mineur. API, release et README
sont alignés. Les transcriptions et traductions ne sont pas relancées au transfert.
Le contrôle d’intégration conserve base en pause, IDs, pistes et cache Whisper.
La suite complète et la CI doivent encore valider cet ensemble avant fusion.
