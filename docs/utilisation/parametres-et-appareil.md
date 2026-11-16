# Paramètres et Mon appareil

**Guide actuel — 0.34.0, 16 novembre 2026.** Les profils sont toujours sans mot
de passe. Choisir **Famille** pour modifier les réglages partagés ; ce profil est
librement accessible et ne protège pas la confidentialité entre personnes du réseau.

## Trouver la bonne rubrique

Dans **Mon appareil**, trois entrées restent visibles sur ordinateur et téléphone :

- **Vue d’ensemble** : état de l’assistant, disponibilité des fonctions et progression.
  Les mesures détaillées du PC et du modèle sont dans **Détails techniques**.
- **Travaux en cours** : progression, fichiers, dernière observation et accès aux
  téléchargements. Un transfert Windows indépendant reste suivi en lecture seule.
  **Vos traductions et synthèses** retrouve les travaux récents du profil ;
  l’actualisation ne les reprend pas et ne les montre pas dans le suivi global.
- **Paramètres** : choisir l’une des cinq rubriques ci-dessous. Ouvrir une page,
  déplier une option ou recharger ne lance aucun travail.

| Rubrique | Pour quoi faire ? |
| --- | --- |
| Profils et connexion | Créer/gérer les profils, afficher le QR code, copier l’adresse du site ou imprimer la fiche pour un autre appareil |
| Bibliothèque et préparations | Ajouter un guide, télécharger des collections, préparer les cartes et la recherche, consulter le stockage, changer les lieux de référence |
| Assistant | Démarrer/arrêter le moteur ; ouvrir le réglage manuel du contexte et les instructions |
| Tests et diagnostics | Mesurer les lenteurs, vérifier la recherche, comparer une aide IA, tester la mémoire et une traduction de 40 pages, vérifier l’usage hors ligne |
| Entretien et données | Exporter les classements/dossiers, gérer les repères du navigateur et consulter les anciens retours |

Les tests sont rangés en cinq rubriques dépliables : lenteurs, recherche (avec son comparatif IA), mémoire, traduction longue et usage hors ligne. Le [guide du test de 40 pages](../exploitation/test-traduction-40-pages.md) explique la durée, le rapport et la reprise. Le lien depuis Assistant mène à l’essai mémoire ; le réglage du contexte reste dans Assistant.

Les options techniques se déplient. Leur état ouvert/fermé est mémorisé par
profil dans ce navigateur. Les liens **Tous les paramètres** et de retour à la
rubrique parente complètent les flèches du navigateur. Les anciennes adresses
restent utilisables ; les nouvelles sous-rubriques ont aussi des liens directs.
Le dernier onglet de Mon appareil est conservé. Les brouillons de conversation,
les filtres et les observations hors ligne gardent leur fonctionnement habituel.
Un formulaire déplacé n’est pas reconstruit à chaque navigation : la saisie reste
en place pendant la visite. Les fichiers à joindre ne sont pas sauvegardés par
un rechargement du navigateur.

## Sur un téléphone

Le suivi, les profils, le QR code, les diagnostics et leurs rapports restent
accessibles. **Assistant** permet aussi l’arrêt et la reprise explicite du moteur.
Une reprise en mode jeu garde l’avertissement et la commande explicite existants.
Les commandes de pause d’un téléchargement ou d’une zone gérés par le portail
restent accessibles en dépliant leur préparation ; le transfert Windows indépendant
conserve sa procédure de pause sur le PC.

Pour ajouter un fichier, choisir de nouveaux téléchargements, préparer les index
ou modifier les coordonnées, utiliser un ordinateur. La page l’explique ; elle ne
lance pas ces opérations en changeant de rubrique. Les cartes, documents et anciens
index continuent à fonctionner pendant les pauses selon leur disponibilité réelle.

**Open WebUI** et **Documents de secours** restent accessibles en bas de page sur
le téléphone et dans le menu sur ordinateur. Les conversations Open WebUI sont
distinctes de celles du portail. Aucun lien vers l’interface classique ni bouton
« Faire un retour » n’est ajouté.

## Correspondance complète des commandes

Inventaire réalisé sur le DOM fonctionnel 0.11.0, puis vérifié après déplacement.
Les commandes des moteurs et leurs API sont conservées. Les champs et boutons des
dialogues restent dans leur dialogue ; seule leur entrée change de place.

Dans le tableau, les destinations abrégées sont sous **Mon appareil → Paramètres**.

| Ancien emplacement et commandes | Destination actuelle et niveau |
| --- | --- |
| Réglages : raccourcis profils, connexion, téléchargements, état ; doublon « Gérer les profils » | Cinq entrées du hub ; profils/connexion dans **Profils et connexion**, téléchargements dans **Bibliothèque et préparations**, état dans **Vue d’ensemble** ; raccourcis redondants retirés |
| Profils : nom, créer, liste des profils et actions proposées par le serveur ; changement via le nom dans le menu | **Profils et connexion → Gérer les profils** ; choix du profil toujours dans le menu/en haut du téléphone |
| Connexion : QR code, imprimer, adresse directe, copier, adresse sécurisée | **Profils et connexion → Ouvrir sur un téléphone** |
| Lieux : domicile/départ, adresse, recherche locale ou IGN, rechercher, résultats, confirmer, vérifier sur carte | **Bibliothèque et préparations → Changer le domicile ou le point de départ** ; modification sur ordinateur |
| Lieux : choisir sur carte, nom/latitude/longitude, enregistrer un point, revenir au domicile | Même page ; saisie manuelle dépliable, action de retour au domicile conservée |
| Moteur : démarrer/forcer explicitement la reprise, arrêter et libérer la mémoire, état/avertissement | **Assistant → Démarrer ou arrêter l’assistant**, ouvert par défaut ; accessible sur téléphone |
| Ajout de guide : titre, fichier PDF/TXT/MD/EPUB, langue, provenance, date, édition, licence, ajouter | **Bibliothèque et préparations → Ajouter un guide**, dépliable sur ordinateur |
| Index : préparer/vérifier/réparer l’outil, créer/reprendre, mettre en pause, exporter le rapport | **Bibliothèque et préparations → Préparer la recherche dans les archives**, dépliable ; suivi/pause/rapport sur téléphone |
| Index automatique : activer, heure début/fin, processus parallèles, enregistrer | Sous la même préparation, **Préparation automatique après téléchargement**, sur ordinateur |
| Contexte : modèle, 8k/16k/32k/64k, enregistrer | **Assistant → Options avancées : mémoire et essai du modèle** |
| Essai mémoire : mode, plafond, lancer, arrêter, appliquer, revenir au réglage précédent, exporter | **Tests et diagnostics → Mesurer un contexte adapté à ce PC** ; essai volontaire, aucune IA à l’ouverture |
| Instructions exactes et contexte produit affiché | **Assistant → Instructions transmises aux modèles**, dépliable ; lecture seule |
| Contrôle recherche : court/complet, ouvrir, résultats et liens, avis humains, arrêt/export/fermeture du dialogue | **Tests et diagnostics → Recherche** ; dialogue inchangé |
| Comparatif IA : modèle, demandes, budget, lancer, arrêter, exporter, cas et avis humains | Sous **Vérifier la recherche → Comparer une aide IA à la recherche**, dépliable ; toujours facultatif |
| Usage hors ligne : ouvrir, conditions réseau/appareil, lancer, arrêter, exporter, nouvel essai, fermer ; étapes humaines, observation | **Tests et diagnostics → Usage hors ligne**, panneau distinct ; dialogue conservé |
| Classements et noms : exporter les métadonnées | **Entretien et données → Conserver les classements et les dossiers pratiques** |
| Dossiers pratiques : exporter les dossiers | Même rubrique dépliable ; édition des références toujours dans la bibliothèque |
| Mémoire de navigation : effacer onglets/filtres/brouillons locaux | **Entretien et données → Effacer les repères de ce navigateur** ; confirmation avant effacement, données serveur conservées |
| Retours déjà enregistrés : actualiser/lire | **Entretien et données → Consulter les retours déjà enregistrés**, secondaire ; aucune création de retour réintroduite |
| Téléchargements : thèmes, langues, maximum à ajouter, suppléments culturels, chercher les contenus | **Bibliothèque et préparations → Télécharger des collections et préparer les cartes → Enrichir la bibliothèque**, ordinateur |
| Sélection : collections proposées, besoins à vérifier, télécharger, pause, actualiser, progression | Même page de téléchargements ; suivi/pause du portail disponibles sur téléphone |
| Géographie : zones préparées, ouvrir la carte, actualiser, arrêter | Même page → **Préparer des cartes, adresses et itinéraires**, dépliable ; suivi/pause sur téléphone |
| Géographie : point enregistré, latitude/longitude, rayon, relief, télécharger, préparer itinéraires | Même préparation, formulaires sur ordinateur ; aucune modification des cartes ou téléchargements |
| Stockage : résumé disque, modèles enregistrés, préparation/inventaire | **Bibliothèque et préparations → Voir les fichiers et l’espace disque** ; lecture seule |
| Vue d’ensemble : état, fonctions disponibles, suivi des travaux | **Mon appareil → Vue d’ensemble** ; bouton **Gérer l’assistant** vers la bonne rubrique |
| Mesures : GPU/VRAM, RAM, espace libre, questions, modèle chargé, date de mesure | Vue d’ensemble → **Détails techniques : mémoire et modèle chargé**, dépliable |
| Activité : volumes, fichiers actifs, date, messages | **Mon appareil → Travaux en cours** ; suivi conservé indépendamment de l’assistant |
| Open WebUI, documents de secours | Menu ordinateur et bas de page mobile, conservés |

Les favoris, conversations, traductions, classement des sources, dossiers pratiques,
cartes et itinéraires restent dans leurs parcours d’usage ; la refonte ne modifie
pas leurs moteurs ni leurs données.

## Liens directs conservés et nouveaux

Toutes les adresses sont relatives à l’adresse locale de votre installation.

| Adresse | Page |
| --- | --- |
| `/#/appareil/ensemble` | Vue d’ensemble |
| `/#/appareil/activite` | Travaux en cours (ancien onglet Activité) |
| `/#/appareil/reglages` | Accueil Paramètres (ancien écran Réglages) |
| `/#/appareil/profils`, `/#/appareil/connexion` | Anciennes pages profils/connexion conservées |
| `/#/appareil/telechargements`, `/#/appareil/stockage` | Anciennes pages téléchargements/stockage conservées |
| `/#/appareil/acces` | Profils et connexion |
| `/#/appareil/bibliotheque` | Bibliothèque et préparations |
| `/#/appareil/assistant` | Commandes et options de l’assistant |
| `/#/appareil/entretien` | Entretien et données, lien vers les tests |
| `/#/appareil/tests` | Tests et diagnostics, cinq rubriques dépliables |
| `/#/appareil/tests?test=translation` | Test de traduction sur 40 pages |
| `/#/appareil/tests?test=memory` | Essai mémoire, réglage manuel conservé dans Assistant |
| `/#/appareil/lieux` | Lieux de référence |

Les anciens fragments `#settings`, `#users`, `#connect`, `#data`, `#monitor` restent
pris en charge. Le retour de choix d’un lieu depuis la carte conserve les champs
et ouvre la page des lieux. Aucun changement de schéma ni migration n’est nécessaire.

Les [preuves et captures](../essais/2026-11-14-parametres-ux.md) précisent les
navigateurs testés. WebKit émulé ne remplace pas Safari sur iPhone physique.
