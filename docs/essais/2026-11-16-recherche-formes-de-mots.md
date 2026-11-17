# Recherche : retrouver les formes courantes des mots

**Bilan de livraison 0.35.1 — 17 novembre 2026, premiers essais le 16.** Correctif compatible de la recherche,
sans nouvel écran, modèle ou format de base. Le niveau correctif corrige des
documents déjà indexés qui pouvaient être écartés à cause du nombre du mot.
La refonte UX 0.34.0 et l’audio des collections 0.35.0 sont conservés.

## Défaut reproduit et changement

La demande « affûter un couteau » pouvait manquer un titre « Affûtage des
couteaux ». Le même défaut existe pour tuyau/tuyaux, ruche/ruches, compteur/
compteurs et plusieurs autres noms. Les variantes ne concernaient auparavant
que le petit vocabulaire technique explicite. Les groupes obligatoires et le
filtrage final pouvaient donc retirer un document pertinent, même renvoyé par Kiwix.

Le plan ajoute des variantes bornées sur les mots entiers inconnus de ce
vocabulaire : pluriels courants et quelques irréguliers. Les alias explicites
restent prioritaires. Le mot initial est conservé et la correspondance exacte
garde son avantage de classement. Les groupes d’autres sujets ne sont pas
supprimés ; les références alphanumériques et des formes ambiguës/invariables
restent intactes. Les variantes ne sont pas déclarées traductions anglaises.

Les index FTS existants utilisent les nouveaux groupes, sans réindexation.
Le même plan sert aux guides, aux compléments ZIM, aux paroles vidéo et au
choix de passages documentaires pour l’assistant. Les caches HTTP conservent
les octets d’origine ; les nouveaux paramètres disposent de leurs propres clés.

Le vrai Kiwix révèle ensuite un second cas : dans une archive sans index de
texte, « tuyaux cuivre » manque le titre singulier. La recherche par titres
essaie d’abord la formulation initiale, puis au plus quatre reformulations,
uniquement si aucun titre reçu ne couvre le sujet. Le nombre de collections
ciblées, le parallélisme et le budget global restent les mêmes. Les traces et
`title_requests`/`title_refinement_requests` rendent ces tentatives observables.
Ces compteurs sont logiques, cache compris ; ils ne mesurent pas les lectures disque.
Les chemins locaux, titres et autres mots de la demande sont contrôlés comme
auparavant ; un résultat par titre ne fait pas disparaître l’absence d’index.

## Vérifications enregistrées

- Avant correction, le petit index réel de guides échoue notamment sur les
  deux directions couteau/couteaux et tuyau/tuyaux. Les journaux privés restent
  dans `/tmp/ss0351-before.log` ; aucun corpus client n’est utilisé.
- **Dix tests ciblés en 3,123 s** : treize couples sur le vrai index SQLite,
  priorité exacte, cuivre/plastique, invariants, références UV5R/145MHz, ambiguïtés
  étal/étaux et email/émaux, passage documentaire tardif, repli de titres et
  absence de requête supplémentaire si la première suffit.
- **79 contrôles sur Kiwix 3.8.1 réel épinglé**, cinq archives générées totalisant
  moins de 1 Mo : nouveaux cas dans le texte et les titres seuls, ouverture des
  sources, contraintes et limites de couverture conservées. Le premier essai de
  titres échoue sur « tuyaux cuivre » ; il reste dans le journal privé
  `/tmp/ss0351-kiwix-titles.log`. Le rejeu corrigé passe et écrit
  `/tmp/ss0351-kiwix-final.json`.
- Une première suite recherche de 107 tests passe avant le complément de titres.
  La suite complète atteint ensuite **972 tests en 212,645 s, 6 ignorés**, sans
  échec. Le diagnostic de performances conserve aussi les deux nouveaux compteurs
  de tentatives par titre ; son contrôle ciblé est rejoué après cet ajout.
  Les quatorze tests du diagnostic passent en **5,277 s** après l’ajout des compteurs.
- Contrôle des liens des **185 fichiers Markdown suivis** : aucun fichier cible
  manquant ; un ancien renvoi d’audit utilisait l’ancre datée 0.32.0 du suivi.
  Il pointe désormais vers une ancre stable, sans modifier les résultats historiques.
  Après reprise des nouvelles décisions du projet, les **186 fichiers Markdown**
  sont vérifiés sans cible ni ancre locale manquante détectée.

## Fermeture et restauration de la page

Le CI `43958161595` passe sept jobs puis échoue en navigation WebKit : une
requête `/api/videos` du filtre de collection rencontre un refus « access control »
pendant le cycle de rechargement. Cet échec est conservé, sans filtrage des erreurs
de la recette. Le contrôle de cycle est renforcé : un minuteur tente un nouvel
appel après le départ de la page. Avant correction, cet appel repart réellement,
bien que les anciennes requêtes aient été annulées.

L’API du navigateur marque maintenant la page en fermeture dès `beforeunload` ou
`pagehide`, annule les requêtes actives et refuse localement les appels suivants
avec `AbortError`. `pageshow` réautorise les appels quand la page est restaurée.
Une annulation connue conserve ce type d’erreur, même si WebKit présente une
erreur réseau différente ; les autres erreurs restent propagées. Aucun filtre
global d’erreurs ni changement de présentation. Le générateur renouvelle seulement
le cache d’`app.js` et régénère les deux entrées HTML.

Après correction : **trois passages par navigateur**, Chromium et WebKit, avec
**8 contrôles de cycle + 18 de filtre par passage**, soit **78 par navigateur**.
Annulation en vol, absence de nouvel appel tardif, restauration et filtre via
les flèches/rechargement sont vérifiés. La génération est aussi contrôlée par
deux tests Python. Cela ne constitue pas un essai Safari sur iPhone physique.

Un fichier core privé de WebKit apparaît pendant ces essais locaux ; seules
ses métadonnées ELF sont examinées, sans contenu mémoire. Ce fichier de 6,12 Go
logiques/160,8 Mo alloués est supprimé de notre worktree et n’est pas versionné.
Les dumps sont désactivés seulement dans le conteneur de test de cette tâche,
sans modification de la sécurité globale du runner ni des navigateurs clients.

## Choix conservés et écartés

Ajouter seulement « couteau » et « tuyau » au vocabulaire technique aurait corrigé
ces exemples sans traiter les autres noms. Les formes de nombre sont donc
regroupées par règles communes. La suppression aveugle d’un s/x et les préfixes
arbitraires sont écartés : « Paris » ne devient pas « pari », « cours » ne devient
pas « cour ». Les ambiguïtés dues aux accents restent protégées par les cas ciblés.
Les tentatives de titres restent bornées ; aucun chargement IA ni hausse du budget
global n’est ajouté pour ce problème de mots. Le temps réel sur HDD reste à mesurer.

## Portée et limites

Ces règles ne sont pas une analyse grammaticale complète. Certaines formes
rares ou polysémiques restent volontairement distinctes, notamment après
suppression des accents. Une entrée bien classée ne prouve ni que son texte est
une procédure complète, ni qu’un modèle réel l’expliquera correctement. Les
archives de Marc, les délais sur son disque et la compréhension humaine restent
à qualifier ; aucune nouvelle inférence ni aucun déploiement client n’est effectué.

Les exceptions de nombre sont relues dans les références linguistiques
primaires de l’[Académie française](https://www.academie-francaise.fr/mickael-b-france)
et du [Portail linguistique du Canada](https://nos-langues.canada.ca/fr/cles-de-la-redaction/noms-en-ail-pluriel).
Leur distinction des sens de « travail » ou d’« émail » rappelle les limites d’un
rapprochement automatique ; le moteur ne prétend pas résoudre ces sens.

## Livraison vérifiée

Les huit [jobs CI du code final](https://github.com/Tanchouteur/SetupSurvie/actions/runs/44025349791)
passent au commit `db206a9ff84db830e45e7c746bff38b18aa0bea2` : Linux,
Windows, lecteurs isolés Python 3.11/3.13/3.14, vrai Kiwix, routage hors ligne
et navigation complète Chromium/WebKit. La suite Linux compte **972 tests en
62,484 s, 6 ignorés**. Le contrôle de cycle conserve ses huit assertions sur
chacun des deux navigateurs. Aucun test humain ou Safari physique n’est déduit
de ces résultats.

Le premier CI `43957470597` est annulé comme remplacé lors de l’ajout des compteurs
au diagnostic. Le second, `43958161595`, conserve son échec WebKit décrit plus
haut. Le dernier valide la correction et les nouvelles assertions ; les erreurs
JavaScript ne sont pas filtrées. Les ajouts après le code validé sont uniquement
documentaires, dont la reprise de la consigne de traçabilité de `main` (`1df999b`).
L’UX et les orientations de PC préinstallé/NOMAD restent conservées ; aucun nouveau
module de ces propositions n’est lancé par ce correctif. Le reçu du paquet est
ajouté après sa comparaison à Git, sans annoncer un déploiement client.
