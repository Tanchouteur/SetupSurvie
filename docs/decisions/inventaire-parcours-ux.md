# Inventaire des parcours et composants UX

**Référence de développement — 0.34.0, 16 novembre 2026.** Cet inventaire relie
les fonctions au parcours et aux recettes. Une recette sur fixtures vérifie les
interactions et les contrats ; elle ne prouve ni couverture du fonds réel,
ni fidélité d’un modèle, ni facilité perçue par un utilisateur novice.

## Capacités conservées et nouvelles entrées

| Besoin | Entrée actuelle | Preuve principale |
| --- | --- | --- |
| Chercher ou reprendre | Accueil : recherche, collections, dernière lecture et discussion mémorisées par profil | `browser_next_portal`, `browser_ux_foundations` ; mémoire locale limitée à sept jours |
| Ouvrir une collection sans IA | Bibliothèque → Collections : filtre des titres/descriptions, variantes, accès Kiwix direct | `browser_collection_filter`, `browser_catalogue`, `browser_next_portal` |
| Chercher dans le contenu | Bibliothèque → Rechercher : espaces, langues, collections, résultats progressifs, arrêt, passages regroupés et avertissement si recherche partielle | `browser_search_core`, `browser_search_progress`, `browser_search_tools` |
| Parcours, favoris et dossiers pratiques | Onglets existants de Bibliothèque ; favoris du profil, fiches pratiques et exports conservés | `browser_practical`, `browser_usage_recipe`, `browser_documents`, `browser_sources` |
| Lire textes, tableaux, illustrations et PDF | Lecteur : Résultats, question, sélection, original, lecteur PDF ; lecture prioritaire sans formulaire au-dessus | `browser_search_core`, `browser_source_figures`, `browser_bilingual_reader` |
| Lire une version française publiée | Lecteurs portail/PDF : version française et original, choix de version, édition et avertissements | `browser_french_lifecycle`, `browser_bilingual_reader` |
| Traduire et reprendre un original | Lecteur portail et PDF dédié : nouveau travail ou existant, plage PDF, termes, mode, progression, comparaison, pause/reprise/arrêt/suppression, export et publication | `browser_reader_work` ; recettes traduction existantes pour contrôles, termes, qualité et publication ; API et tests unitaires |
| Retrouver les travaux personnels | Mon appareil → Travaux en cours : métadonnées des traductions/synthèses du profil, lien vers leur conversation | API `/my-work`, test d’isolement `test_pilot_api` ; états récents observés, aucune reprise automatique |
| Organiser les échanges | Assistant : conversations et dossiers à gauche, recherche titre/messages, renommage et classement, pagination, suppression avec confirmation | `browser_assistant_workspace`, `test_conversation_organization`, `test_pilot_api` |
| Poser une question et apprendre | Assistant : discussion au centre, dictée, mode, exemples de tâches, brouillons, interruption et restauration d’un échange | `browser_chat_comfort`, `browser_learning`, `browser_request_lifecycle`, `browser_model_switch` |
| Choisir les documents et comparer | Assistant → Documents à droite : sélection multiple, document de travail, synthèse longue ; sources consultées séparées des choix | `browser_document_choices`, `browser_long_summaries`, `browser_documentary_evidence` |
| Relire les sources utilisées | Réponse et volet Sources consultées ; ouvertures d’original et pages précises ; absence de suivi expliquée | `browser_sources`, `browser_documentary_evidence`, tests de provenance serveur |
| Vidéos et sous-titres | Bibliothèque/lecteurs et Mon appareil : vidéos locales/ZIM, pistes, transcription, traduction et acquisition volontaires | `browser_local_videos`, `browser_archive_videos`, `browser_caption_preparation`, `browser_audio_transcription`, `browser_caption_acquisition` ; lot vidéo 0.33.0 préservé |
| Cartes et itinéraires | Cartes : page native, recherche, relief, repères, trajets et zones ; restrictions de préparation mobile conservées | recettes cartographiques et job CI `maps-interface` ; aucune carte lourde dans le runner |
| Voir l’état et les transferts | Mon appareil → Vue d’ensemble/Travaux : état, détails techniques, préparations et transferts indépendants ; arrêt volontaire distinct d’une panne | `browser_settings_ux`, tests des superviseurs ; pas de démarrage IA à l’ouverture |
| Régler et diagnostiquer | Mon appareil → Paramètres/Tests : profils, réseau/QR, bibliothèque, assistant, entretien, export, calibration et essais volontaires | `browser_settings_ux`, `browser_assistant_diagnostics`, `browser_startup_diagnostic`, `browser_performance`, `browser_translation_benchmark` |
| Changer de personne | Nom du profil, en haut sur PC et téléphone ; Famille sans mot de passe ; IDs et historiques conservés | `browser_profiles`, tests API profil et onglets périmés |
| Accéder aux fonctions avancées et au secours | Outils sur PC, liens de navigation sur téléphone : Open WebUI et `/secours.html` | `browser_ux_foundations`, `browser_next_portal` ; aucune dépendance à l’IA |
| Mettre à jour et revenir | Mise à jour normale ; retour volontaire au paquet 0.33.1 conservant les données récentes | 19 tests `test_pilot_update`, vérification de compatibilité SQLite ; machines physiques restant à qualifier |

## Ajouter une fonction sans nouvelle refonte

Choisir d’abord sa destination parmi les cinq rubriques, son objet (conversation,
document, travail ou appareil) et son propriétaire. Une nouvelle commande de
lecture s’ajoute au lecteur ; le volet Documents regroupe les travaux de la
discussion. Un diagnostic avancé reste dans Tests ou Entretien. Ne pas ajouter
une destination principale pour chaque outil.

Réutiliser les tokens de `ux-system.css`, les boutons existants, les états
serveur, le composant d’aide `SurvieUI.help` et le contrôleur `reader-work`.
Conserver des noms courts et concrets. Les conséquences, états incomplets et
risques de suppression restent visibles ; l’aide facultative explique un terme
ou un choix, sans cacher une condition essentielle.

Utiliser des identifiants ou `data-*` stables, le générateur HTML et les événements
existants. Conserver un seul jeu de contrôles quand la disposition change.
Préciser les états vide, chargement, indisponible, en cours, pause et terminé ;
l’ouverture ou le retour dans une page ne lance pas une opération. Vérifier le
profil et les réponses tardives avant d’afficher des données personnelles.

Recette minimale : clavier, largeur 320/390 et PC 1024/1440/1920, écran court,
Précédent/Suivant, rechargement, changement de profil et indisponibilité du module.
Les composants optionnels doivent échouer sans bloquer les fonctions de base.

## Comparer l’usage avant et après

Référence technique : version 0.33.1 avec les mêmes contenus, profil et machine.
Faire réaliser sans indiquer le chemin : trouver et lire un document, traduire
une plage puis la retrouver, ranger une discussion, vérifier les documents lus,
ouvrir une vidéo, retrouver un transfert et changer de profil. Relever réussite
sans aide, hésitations, mauvais clics et capacité à expliquer le résultat. Séparer
le temps de navigation du temps d’inférence ou de recherche. Une réduction des
clics ne suffit pas si le choix devient moins compréhensible.

Le seuil technique est l’absence de perte de fonction et de données, de blocage
sur téléphone/PC et de déclenchement implicite. L’amélioration humaine reste à
mesurer avec Marc : toute tâche devenue moins compréhensible doit conduire à
une correction ciblée. Les critères et preuves automatiques figurent au
[bilan de livraison](../essais/2026-11-16-refonte-ux.md).
