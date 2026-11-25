# Inventaire des données locales

**Guide de référence — revu le 25 novembre 2026 pour la 0.117.0.** Les essais
Windows chez Marc et sur téléphone réel restent à réaliser.

## Où voir ce qui est sur l’appareil

- **Bibliothèque → Collections** : encyclopédies et guides présents, avec un
  lien pour ouvrir chaque collection dans Kiwix.
- **Mon appareil → Paramètres → Bibliothèque et préparations** : pages
  **Stockage** (fichiers et espace disque) et **Téléchargements** (ajouts de
  collections). Chacune propose un retour **← Paramètres · Bibliothèque**.
- Le classement des collections (Fonds principal, Autre, suppression) est décrit
  dans le [guide des collections](classement-et-collections.md).

Pour chaque collection : nom compréhensible, langue, mois de l’édition, taille et
disponibilité. Les guides s’ouvrent dans le lecteur de la bibliothèque. Les
modèles sont indiqués séparément : leur présence sur disque ne signifie pas
qu’ils occupent la VRAM.

## Espace disque et analyse du stockage (depuis 0.117.0)

**Mon appareil → Vue d’ensemble** montre une carte **Espace disque**, pleine
largeur, sous « Mémoire et modèle chargé » : une phrase d’état (espace libre,
place prise par SetupSurvie et par ses copies de sécurité) puis une barre par
disque concerné. Couleurs : braise pour SetupSurvie, flamme pour les copies de
sécurité, gris pour les autres fichiers du PC, papier pour l’espace libre. Un
disque qui ne porte qu’un point de restauration ou d’autres copies a sa propre
ligne. Sous 10 % d’espace libre, le résumé de l’appareil ajoute un point
« Disque presque plein ».

Toute la carte ouvre **Stockage** (`#/appareil/stockage`), dont la section
**Analyse de l’espace** détaille :

- les catégories (Bibliothèque, Index et caches de recherche, Assistant IA,
  Logiciels et outils, Profils et réglages, Copies de sécurité, Fichiers
  temporaires, Autres), triées par taille ;
- pour chacune, ses éléments (par exemple Wikipédia et archives, Cartes,
  Vidéos, Modèles d’IA, Index des catégories, Disque Docker, Sauvegardes des
  mises à jour, Point de restauration), avec la mention **reconstructible**
  pour ce qui peut être recalculé ;
- pour chaque élément, ses dix plus gros fichiers ou dossiers.

L’analyse est faite par le contrôleur du PC serveur (`scripts/storage_report.py`)
en lecture seule, en arrière-plan : au premier affichage, puis quand la dernière
a plus de 24 heures, ou à la demande avec **Analyser à nouveau** (profil
Famille, `POST /api/admin/storage/scan`). Le résultat est gardé dans
`private/storage-report.json`. `GET /api/storage` renvoie seulement des tailles
et des noms relatifs, jamais de chemin complet. L’espace libre est relu à
chaque affichage. Les tailles sont en base 1024, comme l’Explorateur Windows.

Elle couvre le dossier d’installation entier lorsqu’il est dédié (logiciel,
données, réglages privés, `updates/`, `maintenance*/`, `images.tar`, anciennes
versions), le disque de Docker Desktop indiqué par ses réglages Windows, le
cache des installateurs et, sous Linux, le dossier `.<installation>-secours`
(point de restauration et anciennes installations). Le point de restauration
est réservé à root : s’il est illisible, sa taille vient de son
`transfer.json` (« taille déclarée »), sinon la ligne indique un accès partiel.
L’analyse est refusée pendant un transfert.

Mesure du 25 novembre 2026 sur le SSD Windows de Marc (lecture seule, hors
portail) : 0,4 à 2,2 s pour environ 250 000 fichiers ; 828 Gio pour SetupSurvie
(dont 699 Gio d’archives ZIM, 72 Gio d’index des catégories, 15 Gio de disque
Docker) et 29 Gio de sauvegardes de mises à jour. L’affichage dans le portail
réel, sur téléphone et sous Linux avec un point de restauration n’a pas encore
été essayé.

## Fonctionnement

L’API locale `GET /api/inventory` ne télécharge rien et n’interroge pas Ollama.
Les répertoires des archives et des modèles sont montés en lecture seule dans le
service `pilot`. Une archive n’est annoncée disponible que si son fichier complet
est présent et qu’elle apparaît au catalogue Kiwix ; les fichiers `.zim.part`
sont signalés incomplets. Pour les modèles, les références du manifeste et la
taille des fichiers associés sont contrôlées, sans recalcul intégral des sommes
de contrôle à chaque visite. Les tailles des modèles peuvent inclure des
fichiers partagés : ce ne sont pas des mesures d’occupation physique cumulables.

## Historique — vérification du 11 novembre 2026

Sur le PC Linux de Louis : Wikipédia français (édition 2026-05, 55,4 Go) et
anglais (2026-08, 127,4 Go), Wikilivres français et anglais (2026-10, 1,2 et
4,7 Go), trois guides de démonstration et sept modèles. Trois tests automatisés
d’inventaire (archive absente ou partielle, modèle absent/incomplet/corrompu,
guide disparu et liens symboliques exclus) et une vérification Firefox à 390 px
sans débordement ont réussi ; ce contrôle ne remplaçait pas un essai sur téléphone
réel ni une validation Docker/Windows. La page s’appelait alors **Données locales**
(`#data`).
