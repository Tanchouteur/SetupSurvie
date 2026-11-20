# Utiliser le serveur familial

**Index des guides d’utilisation — revu le 20 novembre 2026 pour la 0.66.0.**
Chaque guide indique en tête la version qu’il décrit. Les usages réels chez Marc
et sur Safari iPhone restent à vérifier sur place.

## Premiers pas

1. Relier l’appareil au même réseau que le serveur, puis ouvrir l’adresse ou le
   QR code affichés dans **Mon appareil → Paramètres → Profils et connexion**
   (raccourci **Autre appareil**). Un Wi-Fi invité peut empêcher la connexion.
2. Ouvrir la **Bibliothèque** pour chercher et consulter guides et archives.
   Elle reste disponible lorsque le moteur IA est arrêté.
3. Ouvrir l’**Assistant**, choisir son profil (sans mot de passe), puis un mode :
   réponse rapide, moyenne ou approfondie. Les autres modèles restent
   disponibles pour les comparaisons.
4. Vérifier les sources de la réponse en ouvrant les documents consultés. Une
   réponse sans source consultée ne doit pas être présentée comme issue de la
   bibliothèque.

L’assistant peut rechercher et lire les documents locaux, calculer et convertir
des unités. Il n’a ni Internet, ni accès aux fichiers du PC. Il ne certifie ni
une conduite médicale, ni la potabilité, ni la sécurité d’un ouvrage.

Le lien **Open WebUI** donne accès aux dossiers et conversations avancées avec
le même profil ; les historiques restent distincts et la bibliothèque du portail
n’est pas importée automatiquement dans ses collections. Le lien **Documents de
secours** (`/secours.html`) permet de lire les fichiers sans l’API ni l’IA.

## Guides par sujet

### Se repérer et régler

| Guide | Contenu | Version décrite |
| --- | --- | --- |
| [Portail sur ordinateur et téléphone](portail.md) | Rubriques, navigation, conversation, modèles, anciennes adresses | 0.63.4 |
| [Paramètres et Mon appareil](parametres-et-appareil.md) | Cinq rubriques de paramètres, où trouver chaque commande | 0.36.0 |
| [Profils locaux sans mot de passe](profils-locaux.md) | Choisir ou créer un profil, Famille, Open WebUI | 0.1.29 |
| [File d’attente](file-attente.md) | Voir, réordonner, mettre en pause et reprendre les travaux | 0.67.3 |
| [Préparations de la bibliothèque](preparations-bibliotheque.md) | Étapes de préparation, dépendances, cartes de la file | 0.67.0 |
| [Inventaire des données locales](inventaire-local.md) | Ce qui est présent sur le disque | 0.67.0 |

### Chercher, lire et vérifier

| Guide | Contenu | Version décrite |
| --- | --- | --- |
| [Recherche documentaire](recherche-documentaire.md) | Résultats, filtres, espaces, contrôle de la recherche depuis le site | 0.36.1 |
| [Rendre les archives recherchables](indexation-archives.md) | Indexation complémentaire automatique et pause | 0.37.3 |
| [Classer les documents et nommer les collections](classement-et-collections.md) | Fonds principal, Autre, suppression, corrections et export | 0.67.0 |
| [Sources, dates et fiabilité](sources-et-fiabilite.md) | Sources réellement lues, dates, relances, limites | 0.38.3 |
| [Documents, favoris et traductions](documents-et-traduction.md) | Lecteur PDF, favoris, documents d’une conversation, traduction et contrôles | 0.60.2 |
| [Synthèse documentaire](synthese-documentaire.md) | Plusieurs documents, lecture d’un livre entier par étapes | 0.19.0 |
| [Illustrations et références](illustrations-et-references.md) | Images d’origine et pages PDF | 0.19.0 |
| [Dossiers pratiques](dossiers-pratiques.md) | Six dossiers de repères facultatifs | 0.9.0 |

### Vidéos

| Guide | Contenu | Version décrite |
| --- | --- | --- |
| [Vidéos locales et sous-titres](videos-locales.md) | Lecteur, recherche des passages, pistes françaises | 0.63.3 |
| [Télécharger une liste YouTube](telecharger-videos-youtube.md) | Bouton du site ou ligne de commande, avec Internet | 0.51.0 |
| [Inventaire des vidéos et sous-titres](inventaire-videos.md) | Outil en lecture seule, rapports privés | 0.23.0 |

### Cartes

| Guide | Contenu | Version décrite |
| --- | --- | --- |
| [Lieux de référence et cartes hors ligne](parametres-et-cartes.md) | Lieux de référence, adresses, relief, zone téléchargée sur téléphone | 0.67.0 |
| [Points et itinéraires](points-et-itineraires.md) | Listes de points, itinéraires locaux, choix d’accès | 0.50.0 |

### Mesurer et tester (facultatif)

| Guide | Contenu | Version décrite |
| --- | --- | --- |
| [Vérifier l’usage hors ligne](verifier-usage-hors-ligne.md) | Contrôle sans IA et étapes humaines | 0.10.0 |
| [Mesurer les délais et la mémoire de l’assistant](mesurer-assistant-et-memoire.md) | Rapports de délais, essai mémoire volontaire | 0.43.2 |
| [Comparer une aide IA à la recherche](comparer-recherche-ia.md) | Essai volontaire et avis humains | 0.9.1 |

Les diagnostics de performances et de Kiwix sont dans
l’[exploitation](../exploitation/README.md).

### Archive

- [Maquette UX](maquette-ux.md) — prototype fictif 0.1.31, retiré en 0.59.0.

## Raccourcis Windows

Depuis l’installation 0.1.13, le Bureau propose **Ouvrir SetupSurvie** et
**Arrêter SetupSurvie**, et le serveur démarre à l’ouverture de session Windows.
Arrêter conserve comptes, conversations et contenus, mais coupe l’accès depuis
les autres appareils. Fermer seulement le navigateur laisse le serveur disponible.
Voir le [parcours Windows](../installation/deux-etapes-windows.md).

## Ajouter des collections

Avec le profil **Famille** : **Mon appareil → Paramètres → Bibliothèque et
préparations → Télécharger des collections et préparer les cartes → Enrichir la
bibliothèque**. Choisir thèmes, langues et plafond, puis **Chercher les
contenus**. Le téléchargement continue sur le serveur si la page est fermée et
se suit dans la [file d’attente](file-attente.md). Voir la
[sélection Kiwix par thème](../bibliotheque/selection-kiwix-par-theme.md) et les
[parcours de savoir-faire](../bibliotheque/savoirs-durables.md)
(**Bibliothèque → Explorer les savoir-faire**).

Après une mise à jour, recharger la page : la version affichée vient du serveur.
