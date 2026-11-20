# Portail toujours informatif, routes par domaine — 0.70.0

**Bilan daté — 20 novembre 2026, runner CPU de développement (Chromium distant,
données fictives, aucun modèle IA).** Suite de l’[audit du portail](2026-11-20-audit-ux-et-maintenabilite-portail.md)
et de la [décision de Louis](../decisions/choix-actuels.md#portail-toujours-informatif-et-socle-commun--décision-de-louis-du-20-novembre-2026).
Règles durables : [guide de design](../architecture/guide-design.md#toujours-informer--0700),
[architecture de l’interface](../architecture/interface.md#socle-commun-et-structure--0700),
[guide du portail](../utilisation/portail.md#être-toujours-informé--0700).

## Niveau de version

Passage de **0.69.4 à 0.70.0** (`y`). Ce sont de nouvelles fonctions compatibles :
bandeau de connexion, résumé de Mon appareil, état et étapes de l’assistant,
écran de départ de la recherche. Les données, URL et API restent inchangées.

## Réalisé

| Point de l’audit | Réalisation |
| --- | --- |
| P0-1 Erreur brute « Failed to fetch » | `core/net.js` traduit toute panne réseau des requêtes `/api/` en français, pour les quatre fonctions `api()`/`request()` et les `fetch` directs ; `toast()` applique la même traduction. |
| P0-2 Aucun état de connexion | Bandeau `#connection-banner` après contrôle de `/api/health`. Il compte les secondes jusqu’au nouvel essai (3, 5, 10 puis 15 s) et propose « Réessayer maintenant » et les documents de secours. Il confirme le retour de la connexion, puis se masque pendant une maintenance. Le pied de page affiche « Appareil connecté » ou « Appareil injoignable ». [Capture](captures/portail-0700/bandeau-connexion.png) |
| P0-3 Message sur le bouton Envoyer | Messages en haut à droite (sous l’en-tête sur téléphone), avec un ton (info, succès, erreur). |
| P0-4 Signaux contradictoires sur l’assistant | « Modèle chargé : Non vérifié » au lieu de « Indisponible ». Une ligne d’état près de la saisie (prêt, démarre, pause, arrêté, injoignable) propose l’action utile. Le bandeau historique de l’assistant est remplacé. Frise d’étapes pendant une réponse. [Capture](captures/portail-0700/assistant-etapes.png) |
| P0-5 Recherche sans résultat | Phrase courte nommant l’espace cherché. « Chercher dans toute la bibliothèque » est proposé en premier. Une recherche incomplète le dit dans la phrase. Les précisions sont repliées dans « Détails de la recherche ». [Capture](captures/portail-0700/recherche-sans-resultat.png) |
| P1-6 Vocabulaire technique | Sur demande de Louis, modèle chargé, RAM et VRAM restent affichés. Les libellés sont clarifiés et les explications données en mots simples. |
| P1-7 Mon appareil | Résumé « Tout fonctionne » ou « N points à regarder », chaque point avec son action. Il reste compact pour garder les mesures en haut (décision du 17 novembre). [Capture](captures/portail-0700/mon-appareil-resume.png) |
| P1-8 Recherches multiples | Écran de départ de Rechercher (idées et dernières recherches par profil). Filtres repliés sous « Filtres » sur téléphone. Les points d’entrée existants sont conservés. |
| P1-9 Icône « ☷ 0 » | Entrée **Tâches** avec icône de liste et état en mots (« 2 en cours », « 1 problème », « En pause »). Pastille numérique sur téléphone. |
| P1-10 Téléphone | En-tête avec logo et commandes, sans titre coupé, avec une pastille compacte modèle/RAM/VRAM. Onglets et types de collections sur une ligne avec fondu. Filtre des collections allégé. [Capture](captures/portail-0700/telephone-bibliotheque.png) |
| P1-11 Cartes | En-tête identique au portail, écrit dans `cartes.html`, et barre de navigation basse sur téléphone. Une seule action braise visible. « Imprimer » devient une commande discrète. Textes d’au moins 12 px. |
| P1-12 États vides | File vide : un seul « Rien en cours ». [Capture](captures/portail-0700/telephone-file-vide.png) Recherche : écran de départ. Le volet Documents choisis de l’assistant est conservé, car il explique où apparaîtront les sources. |
| P2-13 Mouvement | Boutons occupés automatiques (cercle puis halo de fin), silhouettes de chargement des résultats, apparitions courtes. Tout respecte `prefers-reduced-motion`. Les transitions View Transitions ne sont pas utilisées (voir le guide de design). |
| P2-14 Cohérence visuelle | Variables chargées en premier. 61 couleurs quasi identiques (ΔE ≤ 2) pointent vers les variables. Plafonds testés : 239 couleurs brutes, 81 tailles de police. La jauge passe de 10 à 11 px. Correction du double calque de la conversation active. |
| Structure (lot 3) | Navigation principale et pied de page écrits dans `modele.html`. Empreintes `?v=` calculées par `build_portal.py` pour le portail et les pages autonomes, avec un test qui détecte un oubli de régénération. Socle réseau commun. |
| Serveur | 182 routes réparties dans `pilot/routes/` (9 routeurs et `deps.py`). `pilot/app.py` passe de 1 681 à 137 lignes. Les empreintes `source_digest` des recettes réelles incluent ce sous-dossier. |

Non traité à la demande de Louis : le reformatage du code compact.

## Vérifications exécutées

- **Tests unitaires** : `python -m unittest discover -s tests` sur la branche
  finale (résultat dans le message de livraison). Sur la branche des routes
  seule : `OK (skipped=39)`, comme la référence, sans modification de test.
  Mêmes routes avant et après (183 avec `/openapi.json`), et même route
  retenue pour chaque URL concrète.
- **Recettes navigateur, Chromium uniquement**, via un serveur Playwright en
  conteneur (`BROWSER_WS`) : 46 recettes sur 51 réussies. Les 5 autres
  (`browser_documents`, `browser_archive_videos`, `browser_archive_audio`,
  `browser_next_portal`, `browser_work_queue`) échouent à l’identique sur la
  référence `1a281be`, car elles supposent un navigateur local. Les recettes
  modifiées (`browser_search_progress`, `browser_search_core`,
  `browser_search_tools`, `browser_chat_comfort`,
  `browser_memory_translation_comfort`) ont été rejouées après correction.
- **Essais manuels** : captures à 1440 × 900 et 390 × 844, plus une coupure
  simulée des API (bandeau, pied de page, message de recherche).
- **Analyse syntaxique** : `node --check` sur les scripts du portail ;
  `git diff --check`.

## Non réalisé et limites

- WebKit et Firefox ne sont pas joués ici (le conteneur n’a que Chromium). La
  CI GitHub joue les trois moteurs, ainsi que les recettes de cartes
  (`browser_maps_runner.cjs`), qui demandent un rendu WebGL indisponible dans
  ce conteneur.
- Aucun essai sur iPhone ou Android réels, ni sur Bazzite, ni avec le vrai fonds,
  ni avec un vrai moteur IA (démarrage réel, étapes réelles d’une réponse).
- Les autres déplacements de balisage au chargement (environ 150 opérations
  dans `layout.js`, `settings-layout.js` et `assistant-workspace.js`) restent
  à reprendre écran par écran.
- Les plafonds de couleurs et de tailles empêchent seulement d’en ajouter : les
  anciennes valeurs restent à réduire.
