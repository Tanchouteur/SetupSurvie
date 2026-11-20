# Audit du portail : maintenabilité, design et expérience — 20 novembre 2026

**Bilan daté et propositions de l’agent — référence `origin/main` à `0f68236`
(0.69.4).** Demande de Louis : juger si le code est maintenable, si sa structure
doit changer, et auditer le design et l’expérience pour qu’une personne qui ne
comprend pas tout s’en serve sans effort, sans jamais rester sans information,
avec une interface soignée et animée. Ce document ne contient aucune décision :
les lots proposés attendent l’accord de Louis.

Méthode : lecture du code de `portal/` et `pilot/`, mesures par script, puis
navigation dans Chromium (Playwright, conteneur sans accès externe) sur le
serveur de démonstration `tests/browser_translation_server.py` (données
fictives, aucun modèle IA). Captures en 1440 × 900 et 390 × 844, puis
coupure simulée des API. Aucun essai sur iPhone réel, sur Bazzite ou avec un
vrai fonds : les noms de collections visibles (`craft`, `quality-bad`…)
viennent des fixtures.

## 1. Verdict

| Partie | État | Faut-il changer la structure ? |
| --- | --- | --- |
| Serveur Python (`pilot/`, `scripts/`) | Sain : 79 modules par domaine, routes minces, messages en français, 1 219 tests unitaires. | Non. Seulement découper `pilot/app.py` (182 routes dans un fichier) en routeurs FastAPI par domaine, quand l’occasion se présente. |
| Portail (`portal/`) | Fonctionne et bien testé (≈ 75 recettes navigateur), mais **c’est là qu’est la dette**. | **Oui, progressivement.** Pas de réécriture ni de framework : une refondation par lots, écran par écran, protégée par les tests existants. |
| Design | Identité « Veillée » réussie (accueil, typographies, couleurs chaudes). | Le système existe (`design/tokens.css`) mais n’est pas appliqué partout. |
| Expérience | Messages honnêtes, mais encore des trous : erreurs brutes, état de connexion absent, vocabulaire technique visible de tous. | Corrections ciblées prioritaires, avant toute refonte visuelle. |

## 2. Maintenabilité du portail

### Ce qui pose problème

1. **Le balisage ne montre pas l’écran réel.** `interface/modele.html`
   (57 lignes, jusqu’à 3 900 caractères par ligne) contient encore la mise en
   page d’origine (barre latérale, bouton « ☰ Menu », barre d’état). Puis
   `layout.js`, `settings-layout.js`, `assistant-workspace.js` et
   `design/experience.js` **déplacent les éléments au chargement**. Exemple :
   `experience.js` déplace la version et l’état du service dans le pied de page.
   Pour savoir où s’affiche un élément, il faut lire quatre fichiers, et l’ordre
   des scripts dans `scripts/build_portal.py` devient une dépendance cachée.
   14 `MutationObserver` réagissent à ces déplacements.
2. **CSS en couches successives.** Il y a 25 feuilles et 5 700 lignes. `design/system.css`,
   chargée presque en dernier, redéfinit les anciennes : on y compte 1 046 préfixes
   `.next-interface` pour gagner en priorité. On relève aussi **311 couleurs hexadécimales
   distinctes**, **102 tailles de police**, 57 arrondis, 37 points de rupture
   et 28 valeurs de `z-index`, alors que les jetons de design existent.
3. **Pas de socle JavaScript commun.** Une cinquantaine de fichiers partagent
   des globales (`S`, `$`) selon l’ordre de chargement. Quatre fonctions
   `api()`/`request()` différentes, 17 fichiers appellent `fetch` directement.
   On trouve **112 endroits qui affichent `error.message` tel quel**. Un seul
   module, `collection-sort.js`, traduit les erreurs réseau. Il y a aussi
   17 `setInterval` indépendants.
4. **Code très compact.** `app.js` fait 97 Ko en 888 lignes (jusqu’à 783
   caractères par ligne), avec 240 lignes de plus de 300 caractères. Les
   relectures et les diffs en deviennent difficiles, pour un humain comme
   pour un agent.
5. **Versions de cache manuelles.** Le paramètre `?v=` est à incrémenter à la main
   pour chaque fichier listé. Un oubli sert une ancienne version.

### Ce qui est solide et à garder

Le portail fonctionne sans ressource externe ni chaîne de compilation. Les
boutons ont un nom accessible : aucun élément sans nom détecté sur
les quatre écrans principaux. `prefers-reduced-motion` est respecté, les
tests navigateurs sont nombreux et le guide de design est tenu à jour.

### Structure proposée (sans framework)

Un framework (React, Vue…) imposerait une chaîne de compilation et une
réécriture risquée pour un gain faible ici. Proposition :

- `portal/core/` : **un seul** client API. Il traduit les erreurs en français
  simple, suit l’état de connexion et relance avec un délai. On y ajoute un petit
  magasin d’état avec événements et des composants d’interface communs : bandeau,
  toast, états vide, chargement et erreur, bouton occupé.
- **Un gabarit HTML par écran** qui décrit l’écran réel, puis suppression des
  déplacements au chargement. On avance écran par écran, en gardant les
  recettes navigateur vertes.
- CSS : `tokens.css` chargé en premier comme seule source des valeurs et
  `@layer tokens, base, composants, pages`. On garde un fichier par composant,
  on retire les préfixes `.next-interface` et un contrôle CI refuse toute couleur
  brute hors jetons. Échelle cible : 7 tailles de texte, 4 arrondis, 6 niveaux
  de `z-index` nommés.
- `build_portal.py` calcule une empreinte du contenu à la place des `?v=`
  manuels. Le JavaScript est reformaté dans un commit dédié, sans aucun
  changement de comportement.

## 3. Audit de l’expérience

### P0 — Ne jamais laisser sans information

1. **Erreur brute en anglais.** Si le serveur ne répond plus, la recherche
   affiche « Failed to fetch »
   ([capture](captures/audit-ux-2026-11-20/recherche-serveur-injoignable.png)).
   Le même risque existe aux 112 endroits cités plus haut.
2. **Aucun état de connexion global.** Le pied de page garde « ● Bibliothèque
   locale » en vert alors que toutes les API échouent : `#service-status`
   n’est mis à jour qu’au chargement (`app.js`, fonction `status`). Il faut un
   bandeau persistant, par exemple : « L’appareil SetupSurvie ne répond pas.
   Vérifiez qu’il est allumé et que vous êtes sur le même Wi-Fi. Nouvel essai
   dans 5 s… ». Il disparaît seul au retour de la connexion.
3. **Le message d’erreur cache le bouton Envoyer.** Dans l’assistant, le toast
   s’affiche en bas à droite, par-dessus « Envoyer »
   ([capture](captures/audit-ux-2026-11-20/assistant-envoi-impossible.png)).
   Le texte conservé est une bonne chose, mais le message ne dit pas quoi faire.
4. **Signaux contradictoires sur l’assistant.** L’en-tête affiche « Modèle
   chargé : Indisponible » pendant que l’assistant répond. La notion de modèle
   en mémoire est technique et sera lue comme « assistant en panne ». Sur
   téléphone, cette pastille est masquée : aucune information n’est donnée. Il faut un
   seul état, en mots simples, près du champ de saisie : « Prêt », « Démarre (environ
   1 min), votre question partira ensuite » ou « Arrêté : la bibliothèque reste
   disponible ». À vérifier sur une installation réelle.
5. **Recherche sans résultat.** Depuis l’accueil, la recherche cherche dans
   l’espace « Autonomie et résilience » sans le dire. Le message obtenu
   (« partie interrogée », « catalogue interrogé », « doit être actualisée »)
   est long et technique. Proposition : « Aucun résultat pour « eau potable »
   dans Autonomie et résilience. » avec le bouton **Chercher dans toute la
   bibliothèque**, des orthographes ou thèmes proches, et le détail technique replié.

### P1 — Comprendre sans connaître l’informatique

6. **Vocabulaire technique visible de tous** : RAM, VRAM, GPT-OSS 20B, Open
   WebUI, « Préparation à vérifier », « Voir les durées », numéro de version
   dans l’en-tête. Proposition : par défaut, des mots d’usage. Les détails
   techniques passent dans **Mon appareil → Détails techniques** (profil
   Famille) et dans des sections « Détails » repliées.
7. **Mon appareil s’ouvre sur des mesures mémoire.** Il devrait commencer par
   une réponse : « Tout fonctionne » ou « 2 choses à regarder ». Chaque point
   donne une explication et un bouton d’action. Les mesures viennent ensuite.
8. **Trop de recherches différentes.** On compte la loupe de l’en-tête, l’accueil,
   Bibliothèque → Rechercher (espace et trois filtres), Filtrer les collections
   et la recherche des conversations. Proposition : un seul champ, avec les filtres
   regroupés sous « Affiner ».
9. **L’icône de la file (« ☷ 0 ») est obscure** et passe à « ? » en cas de
   souci. Proposition : un libellé « Tâches » avec son état (« 2 en cours »,
   « 1 problème »).
10. **Téléphone.** Le titre de page remplace la marque et se coupe (« Votre
    esp… », « Bibliothè… »). Les onglets Mes favoris et Traductions sortent de
    l’écran sans indice de défilement. Dans la Bibliothèque, il faut passer
    titre, texte, onglets, filtres, encadré de filtre et encadré d’organisation
    avant la première collection
    ([capture](captures/audit-ux-2026-11-20/telephone-bibliotheque.png)).
11. **Cartes, une autre application.** L’en-tête diffère : bouton Imprimer, pas
    d’Outils, de loupe ni de version. Trois boutons braise sont visibles en
    même temps, contre la règle « braise = action principale ». Le texte des
    onglets est très petit.
12. **États vides peu utiles.** L’onglet Rechercher vide ne propose ni exemple
    ni recherche récente. La file affiche trois encadrés vides identiques au
    lieu d’un seul « Rien en cours ». Dans l’assistant, les deux colonnes
    latérales restent ouvertes et presque vides sur ordinateur.

### P2 — Finition « site professionnel »

13. **Mouvement.** Il existe 11 animations sobres, avec le mouvement réduit
    respecté. Il manque :
    - des transitions entre écrans (View Transitions, avec repli sans animation) ;
    - des squelettes de chargement pour les listes et les résultats ;
    - des boutons qui montrent leur état (« Envoi… », puis une coche) ;
    - les étapes visibles de l’assistant (« Je lis 3 documents… ») ;
    - des confirmations brèves après une action.

    Durées de 150 à 250 ms, en décélération, sans animation décorative en boucle.
14. **Cohérence visuelle.** Réduire les 102 tailles de police à l’échelle
    cible. Supprimer les textes de 10–11 px dans la jauge et la navigation
    mobile. Une seule action braise par écran.
15. **À conserver.** L’accueil (scène du feu, recherche centrale,
    suggestions), la typographie Fraunces et Atkinson Hyperlegible, la barre de
    navigation basse sur téléphone et la franchise des messages (« cela ne
    prouve pas l’absence d’information »).

## 4. Lots proposés (à valider par Louis)

| Lot | Contenu | Version indicative |
| --- | --- | --- |
| 1. Jamais sans information | Client API commun, traduction des erreurs, bandeau de connexion avec nouvel essai, état unique de l’assistant, toast qui ne masque plus les commandes, messages de recherche réécrits. | `y` |
| 2. Mode simple | Vocabulaire d’usage par défaut, détails techniques regroupés, Mon appareil qui commence par « Tout va bien / quoi faire », en-tête et file lisibles, téléphone allégé. | `y` |
| 3. Refondation structurelle | Gabarits par écran sans déplacement au chargement, CSS en couches sur les jetons, en-tête commun avec Cartes, empreintes automatiques, formatage du code. Écran par écran, recettes navigateur vertes à chaque étape. | `y` par étape, sans changement fonctionnel visible |
| 4. Finition | Transitions, squelettes, boutons d’état, étapes de l’assistant, échelle typographique. Recette Chromium, Firefox et WebKit puis iPhone réel. | `y` ou `z` |

Le lot 1 apporte le plus de valeur pour un risque faible. Le lot 3 est le
plus long ; le faire avant le lot 4 évite d’ajouter des animations sur une
structure qui va changer.

## 5. Performance : réécrire en Rust ?

Proposition de l’agent, sans mesure nouvelle : **non, une réécriture
n’apporterait pas de gain perceptible.** Le temps ressenti vient de composants
déjà écrits en langages compilés :

- l’inférence : Ollama, en C++ et CUDA ;
- les archives : Kiwix et libzim, en C++ ;
- les itinéraires : OSRM, en C++ ;
- les index : SQLite FTS5, en C ;
- le serveur web : Caddy, en Go.

Le Python du pilote assemble ces composants et attend surtout leurs réponses.
Une réécriture coûterait des mois et risquerait de casser 1 219 tests, la
préservation des données et les mises à jour, pour quelques millisecondes.
Démarche utile : mesurer (`pilot/performance.py`, recettes de délais), puis
optimiser seulement une fonction réellement lente : requête SQL, cache,
traitement en arrière-plan. En dernier recours, cette seule fonction pourrait
passer dans un module Rust via PyO3. Côté portail, la lenteur ressentie se
corrige surtout par le retour visuel immédiat (lots 1 et 4).

## 6. Limites

- Serveur de démonstration et données fictives. Délais, fonds réel, démarrage
  du moteur IA et carte avec fond préparé non observés.
- Chromium seulement. La page de maintenance n’a pas pu être capturée sur
  ordinateur dans ce conteneur. Aucun essai WebKit, Firefox ou iPhone réel
  pour cet audit.
- Les nombres sont des comptages par script sur `portal/` (hors `vendor/` et
  `cartes-hors-ligne/`) : ce sont des indicateurs, pas une mesure de qualité.
