# Installation Linux neuve sur Bazzite

**Bilan de recette du 17 novembre 2026 — installation fonctionnelle 0.41.0, recette clôturée avec limites.**
Cette installation utilise le parcours Docker Linux et un démon rootless dédié,
pas le laboratoire Podman. Le pilote NVIDIA, Python 3.15.2 et Docker étaient
présents : ce n’est pas une installation de l’OS sur un PC vierge.

## Installation et données

Installation sur le SSD système dans `/home/louis/SetupSurvie-essai`, avec
code installé dans `application`, données dans `donnees`, réglages dans `prive`
et rapports privés dans `rapports`. Le clone `depot` est conservé séparément.
Aucune modification du laboratoire ni des applications personnelles de Louis.
Le plafond de l’essai reste **300 milliards d’octets tout compris**. Le relevé
intermédiaire après les préparations et sauvegardes est de 162 609 971 200 octets
alloués ; le relevé final figure au reçu de clôture.

Louis confirme le 17 novembre de terminer avec le fonds déjà présent plutôt
que de compléter le plan thématique de 180 Go. Les **110 ressources du catalogue
hors Wikipédia anglais** sont présentes et leurs tailles et SHA-256 ont été
recalculés : 110 conformes. Les compléments déjà téléchargés et les fichiers
partiels sont conservés ; ils ne sont pas tous déclarés acquis. Le fonds de Marc
reste distinct et sans ce plafond documentaire. Le fonds finalement conservé
comprend **159 ressources vérifiées** (113 990 805 208 octets) : **58 ZIM**,
57 index natifs reconnus et un index complémentaire prêt. La file est vide.
Ces index ne constituent pas une importation dans les collections Open WebUI.

Avant la bascule du clone vers l’application installée : sauvegarde arrêtée de
148 fichiers, puis vérification de chaque taille/empreinte. La mise à jour
logicielle **0.40.0 → 0.40.1** a ensuite utilisé `pilot_update.py apply`, avec
son propre instantané et journal terminé. Les mises à jour 0.40.1 → 0.40.2
puis 0.40.2 → 0.41.0 sont également terminées avec leurs instantanés.
Comptes, conversations et réglages
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
| Identité d’écriture du routage incompatible avec Docker rootless | L’essai de montage refuse l’UID conteneur 1000 et accepte l’UID 0 du démon rootless, qui correspond à louis sur l’hôte. Détection explicite du mode Docker ; graphe réel préparé et trois calculs HTTP réussis. |

La couverture du PDF Victron (image RVB et masque de 4 832 × 7 528 pixels)
a fait planter le lecteur navigateur. Des budgets explicites de 16 Mio pour
le redimensionnement et 4 194 304 pixels par canvas évitent les sondes de
capacité excessive de PDF.js. La même source s’affiche ensuite page 6 puis
couverture sur la 0.41.0 réellement installée, sans interception réseau et
sans modifier le fichier original. Une fixture compressée de moins
de 200 Ko contient une vraie image de 5 000 × 7 200 pixels ; Chromium vérifie
son pixel bleu et un canvas de 1 326 × 1 909 pixels. L’environnement local a aussi arrêté WebKit par manque de mémoire pendant
la recette synthétique ; un essai de page lourd après la carte a encore fait
planter l’onglet Chromium MCP. Le budget des canvases ne borne donc pas toute
la mémoire du navigateur ou du décodage. L’ouverture isolée et les essais
physiques sur téléphone restent distincts. Le fichier local de glyphes 8192–8447 manquant sur la carte est
ajouté avec provenance et SHA-256.

Le démarrage automatique a été réellement activé et les services relancés ;
le redémarrage complet du PC n’est pas encore validé par ce bilan.

## Résultats et limites documentaires

- Le navigateur rejoint le portail par l’IP LAN. La recherche « loi d’Ohm »
  retrouve des pages PDF ; le lecteur affiche le document Victron et ses pages.
- Fonds de carte Sud/Solliès, relief, adresses et points d’intérêt : vérifiés
  dans leurs manifestes, carte affichée dans le navigateur. Le routage est
  une préparation séparée ; les premières demandes à 25 km ont échoué.
  Le réseau local retenu couvre un rayon de **10 km** autour de Solliès,
  bbox `[5.904491,43.080452,6.175509,43.279548]`, source Overpass conservée
  avec son SHA-256. Trois calculs réels : 2 287,1 m à pied, 5 020,1 m à moto
  et en voiture. Ce n’est pas une couverture routière de tout le Sud.
- Gemma4 E4B et GPT-OSS 20B présents. Gemma4 produit une réponse sur la loi
  d’Ohm mais le contrôle de références la marque **incomplète** : ce cas ne
  valide pas la fidélité documentaire. Le calcul réel `12 × 7` aboutit à `84`.
- L’extraction de `OFF-shelter-kit-2010.en.pdf` contient du texte décalé et des
  caractères de contrôle malgré une empreinte conforme. L’essai de traduction
  échoue et ne publie pas de traduction. Le document doit être examiné pour
  extraction adaptée/OCR ; l’intégrité ne garantit pas un texte exploitable.
- Une page du PDF lisible `OFF-shelter-safety-2009.en.pdf` est traduite avec
  Gemma4 E4B : travail terminé, un passage contrôlé, aucun avertissement ni
  blocage automatique. Cela ne vaut pas relecture bilingue ou qualification
  d’un livre entier.
- Les essais réels iPhone/Android, la confiance HTTPS sur ces appareils,
  `survie.local` depuis ces clients, la campagne des 89 questions et le
  transfert/restauration entre SSD restent séparés.

## Vérifications de développement

Suite locale du candidat 0.40.3 : **1 026 tests en 229,559 s, 6 ignorés**, sans échec.
Après intégration de la vidéo de main, la suite **0.41.0 compte 1 038 tests
en 207,144 s, 6 ignorés**, sans échec. Les huit jobs CI ont réussi (reçu final ci-dessous).
Huit tests ciblés couvrent le carnet/cartes et la préparation du routage.
Une coupure de sortie externe dans les huit espaces réseau des conteneurs
dédiés est vérifiée par un témoin Internet accessible avant et bloqué pendant.
Ollama est arrêté : santé API, recherche, lecture PDF statique, cartes, trois
itinéraires et contrôleur passent tous. Les règles sont retirées et Ollama
rétabli ensuite ; le réseau du PC et les autres applications restent disponibles.
Cette recette ne coupe pas physiquement Internet sur le PC et le téléphone.
Les contrôles CI seront consignés dans le reçu final. Aucun modèle, corpus ou carte lourde téléchargé dans le runner.

Les numéros 0.40.0 à 0.40.3 désignent les candidats internes de la branche Linux
pendant ces essais, distincts de la livraison vidéo 0.40.0 intégrée entre-temps
sur main. La livraison commune devient **0.41.0** : ajout fonctionnel compatible
du démarrage Linux et corrections issues de la recette, avec la vidéo conservée.
Les anciens commits et résultats ne sont pas renumérotés. Aucun changement de
schéma personnel ni des images tierces.

Deux échecs CI antérieurs restent conservés : nettoyage Windows d’un
rapport vidéo encore écrit en arrière-plan et saisie de plage PDF sous WebKit.
Le test Kiwix attend désormais l’écrivain avant de supprimer son répertoire
temporaire ; le test de traduction engage et vérifie les champs avant envoi.
Le produit garde ses délais. Le scénario WebKit ciblé de traduction passe
localement avec les pages 3–5, pause/reprise, export et quatre tailles d’écran.

## Reçu final — 0.41.0

Les huit jobs de la [CI 44162714983](https://github.com/Tanchouteur/SetupSurvie/actions/runs/44162714983)
réussissent sur `958a267f4add2158c9791661fba6303ffadcc5c7` : Linux,
Windows, routage, recherche Kiwix, lecteurs isolés et navigateurs. Linux :
1 038 tests en 63,647 s. Les recettes PDF sous Chromium **et WebKit** vérifient
la grande image bleue et un canvas de 1 326 × 1 909 pixels. Les problèmes
locaux de mémoire restent documentés ; ce succès ne qualifie pas un iPhone.

La 0.41.0 est appliquée sur Bazzite par mise à jour sauvegardée, puis le service
utilisateur a été redémarré. Santé HTTP : `ok=true`, aucune fonction dégradée ;
contrôleur joignable, service actif et activé, linger actif. La vérification de
l’installateur réussit, dont caches embeddings et dictée CPU. La reprise après
redémarrage physique du PC n’a pas été exécutée.

L’essai final 0.41.0 bloque effectivement la sortie externe des huit conteneurs,
arrête Ollama et vérifie recherche, lecture statique du PDF, cartes, trois
itinéraires et contrôleur. Le navigateur ouvre aussi le PDF Victron à la page 6
pendant cette isolation, moteur arrêté. Les règles sont supprimées ensuite et
le moteur rétabli ; rapport `cleaned=true`. Aucun changement durable de pare-feu.

Mesure finale : **163 538 415 616 octets alloués**, soit 163,5 Go, pour tout le
dossier d’essai (application, clone, données, modèles, Docker dédié, sauvegardes,
rapports et fichiers partiels). Plafond de 300 Go respecté. L’installation est
conservée pour la campagne et le transfert futurs ; aucun nettoyage de son fonds.

Paquet réellement appliqué 0.41.0 : SHA-256
`1e1f3358ec862e85cef310ce0c0602af8049bf82715bce4c2fe91188c8065bf2`.
Les ajouts documentaires et corrections de tests postérieurs ne sont pas annoncés
comme inclus dans ce paquet. Les gros contenus et rapports privés restent hors Git.
