# Installation Linux neuve sur Bazzite

**Bilan de recette du 17 novembre 2026 — finition en cours, candidat 0.40.2.**
Cette installation utilise le parcours Docker Linux et un démon rootless dédié,
pas le laboratoire Podman. Le pilote NVIDIA, Python 3.15.2 et Docker étaient
présents : ce n’est pas une installation de l’OS sur un PC vierge.

## Installation et données

Installation sur le SSD système dans `/home/louis/SetupSurvie-essai`, avec
code installé dans `application`, données dans `donnees`, réglages dans `prive`
et rapports privés dans `rapports`. Le clone `depot` est conservé séparément.
Aucune modification du laboratoire ni des applications personnelles de Louis.
Le plafond de l’essai reste **300 milliards d’octets tout compris**.

Louis confirme le 17 novembre de terminer avec le fonds déjà présent plutôt
que de compléter le plan thématique de 180 Go. Les **110 ressources du catalogue
hors Wikipédia anglais** sont présentes et leurs tailles et SHA-256 ont été
recalculés : 110 conformes. Les compléments déjà téléchargés et les fichiers
partiels sont conservés ; ils ne sont pas tous déclarés acquis. Le fonds de Marc
reste distinct et sans ce plafond documentaire.

Avant la bascule du clone vers l’application installée : sauvegarde arrêtée de
148 fichiers, puis vérification de chaque taille/empreinte. La mise à jour
logicielle **0.40.0 → 0.40.1** a ensuite utilisé `pilot_update.py apply`, avec
son propre instantané et journal terminé. Comptes, conversations et réglages
sont conservés. Il ne s’agit pas d’une restauration autonome du disque de secours.

## Incidents rencontrés et corrections

| Incident | Correction et preuve |
| --- | --- |
| libzim 3.13.1 indisponible sous Python 3.15 | Version 4.1.0 vérifiée dans l’environnement isolé de ce Python ; 3.13.1 conservée jusqu’à Python 3.14. API d’énumération compatible. |
| Contrôleur inaccessible depuis les conteneurs rootless | Passerelle `10.0.2.2` et accès à la boucle locale du démon dédié ; contrôleur limité à `127.0.0.1`. Le portail le joint. |
| Binaire PMTiles Linux refusé car supérieur à 50 Mo | Archive toujours vérifiée ; limite du binaire décompressé portée à 150 Mo. Fonds Sud et Solliès vérifiés. |
| Processus hôtes perdus après la session SSH | Service utilisateur systemd, linger et reprise sur échec ; service actif indépendamment de SSH. Les chemins avec espaces sont échappés. |
| Exceptions d’auxiliaires sous forme de traceback | Module `setup` partagé avec les auxiliaires pour garder un message d’erreur compréhensible. |
| Index annoncé dégradé alors que 101 guides étaient indexés | La préparation continue après le délai du démarrage ; l’état dégradé disparaît quand elle réussit. Reproduit sur le fonds réel et couvert par trois tests. |
| Identité d’écriture du routage incompatible avec Docker rootless | L’essai de montage refuse l’UID conteneur 1000 et accepte l’UID 0 du démon rootless, qui correspond à louis sur l’hôte. Détection explicite du mode Docker ; vérification réelle du graphe encore en cours. |

Le démarrage automatique a été réellement activé et les services relancés ;
le redémarrage complet du PC n’est pas encore validé par ce bilan.

## Résultats et limites documentaires

- Le navigateur rejoint le portail par l’IP LAN. La recherche « loi d’Ohm »
  retrouve des pages PDF ; le lecteur affiche le document Victron et ses pages.
- Fonds de carte Sud/Solliès, relief, adresses et points d’intérêt : vérifiés
  dans leurs manifestes, carte affichée dans le navigateur. Le routage est
  une préparation séparée ; les premières demandes à 25 km ont échoué.
- Gemma4 E4B et GPT-OSS 20B présents. Gemma4 produit une réponse sur la loi
  d’Ohm mais le contrôle de références la marque **incomplète** : ce cas ne
  valide pas la fidélité documentaire. Le calcul réel `12 × 7` aboutit à `84`.
- L’extraction de `OFF-shelter-kit-2010.en.pdf` contient du texte décalé et des
  caractères de contrôle malgré une empreinte conforme. L’essai de traduction
  échoue et ne publie pas de traduction. Le document doit être examiné pour
  extraction adaptée/OCR ; l’intégrité ne garantit pas un texte exploitable.
- Une traduction courte depuis un autre PDF lisible reste en cours de recette.
- Les essais réels iPhone/Android, la confiance HTTPS sur ces appareils,
  `survie.local` depuis ces clients, la campagne des 89 questions et le
  transfert/restauration entre SSD restent séparés.

## Vérifications de développement

Suite locale finale du candidat 0.40.2 : **1 026 tests, 6 ignorés**, sans échec.
Huit tests ciblés couvrent le carnet/cartes et la préparation du routage.
Les contrôles systemd, réseau isolé, routage réel et CI seront consignés dans
le reçu final. Aucun modèle, corpus ou carte lourde téléchargé dans le runner.

0.40.0 porte l’ajout fonctionnel du démarrage Linux ; 0.40.1 et 0.40.2 sont les
corrections compatibles constatées pendant la recette. Aucun changement de
schéma personnel ni des images tierces.
