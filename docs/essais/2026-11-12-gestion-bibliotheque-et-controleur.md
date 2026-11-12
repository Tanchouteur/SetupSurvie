# Gestion de bibliothèque et récupération du contrôleur — 12 novembre 2026

**Statut : bilan daté**, pilote 0.1.9, sur le Linux de Louis.
La procédure actuelle est le [guide de sélection Kiwix](../bibliotheque/selection-kiwix-par-theme.md).

## Diagnostic de l’affichage et du moteur

Le portail répondait en version API 0.1.8, alors que son étiquette HTML indiquait
encore 0.1.7. Cette étiquette était écrite en dur. Elle vient désormais de la
réponse `/api/status` ; les URL des ressources du portail ont été renouvelées.

Le service hôte de commande n’écoutait plus sur 11436. Son fichier de suivi
désignait un processus qui n’existait plus. Ollama était arrêté et aucun marqueur
de pause n’était présent. Les quatre services Web fonctionnaient. Le journal
du contrôleur ne fournissait pas de trace permettant d’attribuer cet arrêt à
un agent particulier. Un redémarrage partiel des services peut laisser le
contrôleur arrêté : la seule disponibilité du portail ne prouve pas sa présence.

Le contrôleur et Ollama ont été remis en route sans démarrage forcé ni question
à un modèle. Le portail retrouve `online: true`, `control_available: true` et
« Assistant prêt », sans modèle chargé. La récupération du laboratoire restaure
maintenant le contrôleur sans démarrer Ollama. Un contrôleur d’une ancienne
version est remplacé lors de l’actualisation, sans toucher au moteur.

## Parcours ajouté

**Données locales → Enrichir la bibliothèque**, avec un compte administrateur.
Le bloc est replié par défaut et ne crée aucune nouvelle entrée de menu.
Thèmes, langues, plafond, aperçu, transfert et pause/reprise restent au même endroit.
Les lecteurs conservent l’inventaire et la consultation habituels.

Les tâches documentaires sont des processus hôtes distincts, avec état et plan
privés persistants. Fermer le navigateur ou relancer le contrôleur ne les efface
pas. Le contrôleur propose des actions et paramètres bornés ; aucune commande,
URL ou destination libre n’est exposée par ces routes. Les contrôles de montage,
budget, marge, verrou et SHA-256 du téléchargeur restent appliqués.

## Vérifications exécutées

- **106 tests automatisés réussis**, dans un conteneur sans réseau, données
  privées ou GPU. Ils couvrent notamment les droits administrateur, la reprise,
  la pause avant publication, la disparition d’un processus, les actions bornées
  et le remplacement d’un ancien contrôleur. Compose analyse les configurations
  Windows, Linux CPU et Linux GPU sans les démarrer.
- **Chromium et WebKit**, largeurs 1366, 768, 390 et 320 pixels : bloc replié,
  thèmes, aperçu, modification des choix, lancement, rechargement de page,
  pause/reprise, fin de tâche, absence de débordement et absence du bloc chez un
  lecteur. Les jobs sont simulés et toutes les requêtes externes sont bloquées.
- Régression WebKit sur le site local réel : conversation longue, tableau,
  navigation et hauteur réduite simulant le clavier, aux cinq largeurs existantes.
- **18 recherches documentaires réelles réussies**, avec lecture des sources et
  ouverture des originaux ; 107 guides inspectés, aucune archive signalée
  indisponible. Ce contrôle ne génère aucune réponse IA.
- `PRAGMA quick_check` renvoie **ok** pour les bases du portail et d’Open WebUI.
  Aucun compte ni contenu de conversation n’a été affiché ou modifié par ce contrôle.
- Préparation réelle, via le contrôleur authentifié, des thèmes autonomie,
  survie, agriculture et énergie : **10 ajouts proposés, 9,92 Go**, sans télécharger
  ces archives. Le même plan reste disponible après redémarrage du contrôleur.
- Actualisation des services locaux : API **0.1.9**, routes documentaires réservées
  à l’administrateur (401 sans connexion), moteur et contrôleur disponibles,
  marqueur de pause inchangé. Une copie du code précédent a été conservée sur le SSD.
- `git diff --check` et cibles/ancres des liens documentaires vérifiés.

Les rapports et captures sont dans `results/library-web/` sur le SSD, hors Git.
Ces vérifications n’établissent pas l’absence de toute anomalie possible. Elles
n’ont pas montré de corruption dans les bases, documents et parcours contrôlés.

Windows de Marc, iPhone réel, nouveau téléchargement Kiwix complet depuis le
bouton et nouvelle génération IA n’ont pas été testés dans cette tâche. Les
transferts du nouveau parcours sont vérifiés avec des fichiers simulés et leurs
empreintes ; le préparateur réutilise le téléchargeur existant. Les contrôles
Linux ne sont pas présentés comme une recette Windows ou une validation iPhone.
