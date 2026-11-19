> Actualisation du 19 novembre 2026 : la maquette fictive est retirée du paquet en 0.59.0 ; l’interface classique reste liée à la génération et aux tests de l’interface actuelle.

# Feuille de route vers la V1 (1.0.0)

**Statut : bilan et proposition de l’agent du 17 novembre 2026, à la demande de
Louis.** Ce document porte sur le **projet en général**, pas sur une livraison
précise : d’autres agents travaillent en parallèle et les versions évoluent.
Repère de lecture seulement : `main` en 0.37.2 (commit `7f65c2d`) le jour de la
rédaction. Mettre à jour les niveaux de preuve et cocher les points à mesure que
des essais réels sont livrés ; ne pas déduire qu’un point est clos parce qu’une
fonction a été codée. Ce document classe ce qui doit, devrait ou peut être
amélioré avant une V1, et liste les gros essais encore manquants. Il ne modifie
ni le code ni la version.
Les priorités proposées ici restent à confirmer par Louis ; elles ne remplacent
pas les [deux objectifs du 16 novembre](choix-actuels.md#deux-prochains-objectifs--décision-de-louis-du-16-novembre-2026).

> Demande de Louis, 17 novembre 2026 : analyser tout ce qui a été fait, tracer
> dans la documentation ce qui peut et doit être amélioré pour une V1 et les gros
> points restant à tester ; préparer une installation complète de zéro sur le PC
> Bazzite (RTX 2060, deux SSD) avec téléchargement de la bibliothèque et des
> cartes, journal et correction des problèmes, puis un transfert d’un SSD à
> l’autre limité à **300 Go**, puis un nettoyage. **Ne pas toucher au code pour
> l’instant.** Le protocole de cet essai est dans
> [Installation neuve et transfert entre SSD sur Bazzite](../essais/plan-installation-neuve-et-transfert-bazzite.md).

## 1. Ce qui existe (état observé le 17 novembre 2026)

Tableau par capacité ; les numéros de version cités servent seulement à
retrouver les bilans. Légende : **Réel** = essayé sur un PC cible avec de vraies données ;
**Simulé** = tests automatisés, fixtures ou CI ; **Absent** = non réalisé.

| Domaine | Ce qui est livré | Niveau de preuve |
| --- | --- | --- |
| Interface | Portail refondu (0.34–0.37) : assistant en trois zones, volets, dossiers, glisser-déposer, transitions, lecteurs portail/PDF, aides facultatives, composants communs | Simulé (Chromium, Firefox, WebKit émulé) + captures de Louis. **Aucun usage humain mesuré**, aucun iPhone réel |
| Recherche | Recherche commune Kiwix + guides, indexation automatique, cache, résultats progressifs, formes de mots, classement pratique/prix, deux espaces | Réel sur Bazzite (6 recherches, 0.36.1) et rapports Windows de Marc (0.9–0.25) ; **fonds complet de Marc non qualifié** |
| Assistant | Outils recherche/lecture/calcul/conversion, synthèses multi-sources, longues lectures, illustrations, suivi documentaire, relances, trois modes | Réel ponctuel (R7, Bazzite 0.37.1) ; **fidélité non évaluée sur un jeu de vérité** |
| Traduction | Documents par passages, pause/reprise, contrôles numériques, vocabulaire, publication, lecture française | Réel court (4 passages, 40 pages fictives) ; **aucun livre entier**, aucune relecture bilingue humaine |
| Vidéos | Inventaire, vidéos locales et des ZIM, sous-titres YouTube, transcription Whisper CPU, traduction des pistes | Réel sur MP4 synthétique de 132 s ; **vidéos réelles de Marc non qualifiées** |
| Cartes | PMTiles Sud, points, itinéraires OSRM hors ligne | Réel chez Marc (Windows) ; CI sur réseau synthétique |
| Profils | Sans mot de passe, Famille, Open WebUI par en-têtes | Simulé ; pas de recette multi-utilisateurs simultanés |
| Installation Windows | Lanceur unique, reprise, démarrage automatique, raccourcis, mise à jour Git | Diagnostic réel chez Marc ; **jamais d’installation sur Windows vierge** |
| Installation Linux | `install.sh` sur Linux préparé (Docker + NVIDIA Container Toolkit) | Premier parcours réel Bazzite repris et terminé : [bilan](../essais/2026-11-17-installation-neuve-bazzite.md). Docker, Python et le pilote GPU étaient déjà présents ; OS vierge non qualifié. |
| Mises à jour | `pilot_update.py`, sauvegarde, retour arrière | Réel chez Marc à plusieurs reprises (incidents corrigés) |
| Transfert | `transfer.py` et assistant graphique : copie reprenable, préparation, activation, retour | Simulé (fixtures) ; **ni Windows réel, ni Linux réel** |
| Secours | Protocole R01–R18, manuel de secours, `/secours.html` | **Plan** ; aucun scénario R01–R18 exécuté |
| Coupures | Écritures durables, verrous, reprise explicite | Simulé (processus tués) ; aucune coupure électrique réelle |

## 2. Doit être fait avant la V1 (bloquant)

| ID | Point | Pourquoi c’est bloquant | Preuve attendue |
| --- | --- | --- | --- |
| V1-D01 | **Installation de zéro réussie sur chaque système vendu** (Windows vierge, et Linux si proposé) | L’offre est un PC préinstallé : la préparation avant livraison doit être reproductible sans l’agent | Journal complet d’une installation sur disque vide, temps, téléchargements, erreurs corrigées. Premier essai Linux : [protocole Bazzite](../essais/plan-installation-neuve-et-transfert-bazzite.md) |
| V1-D02 | **Transfert et restauration réels** d’un disque à l’autre, puis fonctionnement sans le disque source et sans Internet | Objectif 2 de Louis. [Transfert Bazzite entre SSD validé](../essais/2026-11-18-transfert-ssd-bazzite.md) sur le même PC avec données source indisponibles et sortie Internet isolée. Docker reste sur le disque système | Scénarios R02, R05, R08, R15 au minimum du [protocole de secours](../exploitation/disque-de-secours-hors-ligne.md#10-recette-dacceptation) |
| V1-D03 | **Droits de redistribution commerciale** des contenus | 107 des 111 entrées du catalogue portent `commercial_review: true` ; vendre un PC avec ces fichiers n’est pas autorisé par défaut | Tableau par ressource : licence, preuve, décision (inclure / téléchargement par le client / retirer) |
| V1-D04 | **Licences des modèles et composants tiers** pour un usage commercial | Gemma, GPT-OSS, Qwen, Kiwix, Open WebUI, OSRM, cartes : conditions différentes | Inventaire des licences et mentions obligatoires livrées avec le PC |
| V1-D05 | **Profil matériel de référence** et modes conseillés validés sur ce matériel | Les modes « rapide/moyenne/approfondie » sont mesurés sur RTX 2060 et 5060 Ti 8 Go, pas sur la [cible 16 Go](../installation/configuration-materielle-cible.md) | Mesures de délai, contexte stable et mémoire sur la machine vendue |
| V1-D06 | **Fidélité de l’assistant sur un jeu de vérité** | Les essais réels montrent des ajouts non sourcés (exemples de fabrication, « tête-bêche ») ; aucune mesure de taux d’erreur | 30 à 50 questions à réponse vérifiable, relecture humaine, taux d’erreurs graves, comparaison des modes ([protocole](../essais/protocole-fiabilite-ia.md)) |
| V1-D07 | **Usage réel sur téléphone**, dont Safari iPhone | Public non informaticien ; aucune recette sur iPhone physique | Parcours QR code → recherche → lecture → question, sur iPhone et Android réels |
| V1-D08 | **Premier usage par une personne non accompagnée** | La refonte UX n’a pas encore été jugée par un utilisateur cible | Marc (ou une autre personne) réalise 5 à 8 tâches sans aide ; incompréhensions notées |
| V1-D09 | **Démarrage après coupure et redémarrage** sur la machine vendue | Alimentation solaire de Marc ; seuls des processus tués ont été testés | Coupure physique pendant lecture, téléchargement et traduction ; état après redémarrage |
| V1-D10 | **Mise à jour d’une V1 vers une version suivante** sans perte | Nécessaire pour un produit vendu ; aujourd’hui éprouvée seulement entre versions pilotes | Mise à jour + retour arrière sur une copie de l’installation vendue |
| V1-D11 | **Manuel humain autonome** testé par une personne | Exigence du protocole de secours ; le manuel actuel est un premier guide | Recette humaine R16–R17 |

Complément du 17 novembre 2026 : la stratégie d’évaluation et des modes dégradés
est dans l’[ingénierie de tests](../essais/ingenierie-de-tests.md), avec une
banque de 89 questions. Cas réel ajouté : sur le PC de Marc (fonds de 753 Go),
une question sur l’organisation scolaire des enfants est refusée sans aucune
source consultée. Le **sur-refus** compte comme un défaut au même titre qu’une
erreur (V1-D06).

## 3. Devrait être amélioré pour la V1

### Interface et simplicité

- **Retirer ou isoler les anciennes interfaces** : `portal/classique/` et
  `portal/maquette/` restent livrées à côté de `portal/nouveau/`. Décider de leur
  sort (archive hors paquet ou suppression) pour réduire la maintenance et les
  risques de régression. À arbitrer avec Louis.
- **Mesurer la simplicité au lieu de la supposer** : nombre de clics pour les
  10 tâches principales, temps pour trouver une source, taux d’abandon. Aujourd’hui
  la validation porte sur le bon fonctionnement, pas sur la facilité.
- **Vocabulaire** : relire tous les libellés avec quelqu’un qui ne connaît pas le
  projet (termes comme « contexte », « index », « ZIM », « profil de modèle »).
- **Messages d’erreur** : vérifier qu’une erreur de moteur arrêté, de modèle trop
  gros ou de disque plein propose une action compréhensible.
- **Premier lancement** : écran d’accueil guidé sur un PC neuf (aucune conversation,
  aucun index prêt, moteur en préparation).

### Recherche et assistant

- Ambiguïtés restantes (« couteaux » → lieu homonyme, « antenne radio » → antenne
  automobile) : envisager la désambiguïsation par l’espace pratique.
- Contexte 8 192 refusé : adapter automatiquement la proposition de contexte au
  matériel détecté, avec explication.
- Extraction PDF avec trous d’équations : signaler la page incomplète au lecteur
  et à la traduction plutôt que de la traduire silencieusement.

### Exploitation

- **Installation Linux portable** : jamais exécutée ; Bazzite (système immuable,
  Docker rootless) est un bon premier cas difficile.
- **Profil documentaire pour une installation limitée** (ex. 300 Go) : aujourd’hui
  le catalogue complet fait 200 Go, dont Wikipédia anglais 127 Go ; il manque un
  choix simple « fonds réduit » sans réglage manuel.
- **Stockage Docker** : sous Linux comme sous Windows, l’emplacement des images
  n’est pas déplacé par SetupSurvie. Documenter et contrôler ce point à l’installation.
- **Diagnostic unique d’installation** : un rapport « tout est prêt / ce qui
  manque » après installation (services, modèles, index, cartes, réseau, HTTPS).

### Code et maintenance

- `pilot/app.py` (72 Ko) et `portal/app.js` (90 Ko) concentrent beaucoup de
  responsabilités ; découper progressivement lors des prochaines corrections,
  sans refonte globale avant V1.
- 213 fichiers de tests et 8 jobs CI : conserver, mais ajouter un **test de bout
  en bout d’installation Linux** dans la CI si possible (petites fixtures).

### Documentation

- `docs/decisions/choix-actuels.md` (555 lignes) est devenu un journal des
  livraisons. Proposition : garder en tête un tableau court des choix en vigueur
  et déplacer le détail par version vers `docs/historique/`.
- `docs/README.md` liste les documents par ordre d’ajout : prévoir un index par
  usage (installer, utiliser, réparer) pour Marc et pour l’acheteur.
- Préparer un **guide client** distinct du guide développeur et du guide pilote.

## 4. Peut attendre après la V1

Les idées de la [boîte à idées](boite-a-idees.md) restent hors V1 sauf décision, dont le contexte personnel de chaque foyer (IDEE-011, demandé « dans le futur ») :
Maison de Solliès-Ville (IDEE-001), compréhension des liens (IDEE-005), choix des
modèles à stocker (IDEE-009), apports NOMAD dont Kolibri (IDEE-010). Également :
recherche par image (IMG-04), Wi-Fi dédié (EVO-01), batterie (EVO-02),
installation d’un PC nu entièrement sans Internet (INS-09), restauration
Windows ↔ Linux (R03–R04), démarrage de secours (R18).

## 5. Gros essais encore manquants

Ordre proposé, du plus utile au moins urgent :

| Rang | Essai | Machine | Dépend de |
| --- | --- | --- | --- |
| 1 | Installation Linux de zéro avec bibliothèque, cartes et modèles | Bazzite, SSD système | Décisions du [protocole](../essais/plan-installation-neuve-et-transfert-bazzite.md#3-décisions-à-obtenir-avant-de-commencer) |
| 2 | Transfert SSD → SSD réel, activation, redémarrage, hors ligne | Bazzite, deux SSD | Essai 1 |
| 3 | Restauration sans source (source rendue inaccessible) et sans Internet | Bazzite | Essai 2 |
| 4 | Transfert HDD → SSD 2 To de Marc | Windows de Marc | Pose du SSD par Marc |
| 5 | Jeu de vérité de l’assistant et de la traduction (V1-D06) | Bazzite puis Windows | Questions et réponses vérifiées à préparer |
| 6 | Parcours téléphone réels (iPhone, Android), QR code, HTTPS, `survie.local` | Réseau domestique | Installation en service |
| 7 | Usage non accompagné (V1-D08) | Chez Marc | Version stabilisée |
| 8 | Coupure électrique réelle pendant écriture | PC de test | Accord sur le risque matériel |
| 9 | Installation sur Windows vierge | PC ou VM Windows dédiée | Licence et machine |
| 10 | Mise à jour V1 → V1.0.1 et retour | Copie d’installation | Paquet de test |

Chaque résultat suit les règles habituelles : version, machine, supports,
réseau, preuves, limites ; « préparé », « vérifié » et « réussi » restent distincts.

## 6. Critères proposés pour annoncer 1.0.0

Seuil de l’assistant décidé par Louis le 17 novembre 2026 : au moins **95 %**
des réponses de la banque sans refus injustifié ni erreur grave, car une réponse
peut sauver une vie ; voir l’[ingénierie de tests](../essais/ingenierie-de-tests.md#seuils-pour-la-v1).
Proposition à valider par Louis pour le reste : tous les points V1-D01 à V1-D11 ont une preuve
réelle datée, aucun défaut connu ne fait perdre de données ni ne bloque la
bibliothèque, et une personne non accompagnée réussit les tâches principales.
Tant que ces critères ne sont pas remplis, rester en `0.y.z`.

## 7. Questions pour Louis

1. Quels systèmes seront vendus en V1 : Windows seulement, Linux seulement, ou les deux ?
2. Les anciennes interfaces `classique` et `maquette` peuvent-elles sortir du paquet ?
3. Qui fera la recette humaine (Marc, une autre personne) et quand ?
4. Faut-il un avis juridique pour les droits des contenus et modèles avant la vente ?
5. Les critères de la section 6 conviennent-ils pour la 1.0.0 ?
