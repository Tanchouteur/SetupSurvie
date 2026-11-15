# Diagnostic des performances Kiwix Windows/Linux

**Suite :** intégration au paquet 0.14.0 décrite dans le
[bilan commun](2026-11-15-integration-outils-validation-videos.md). Les constats
ci-dessous restent ceux de la préparation initiale sur la branche dédiée.

**Bilan daté — 15 novembre 2026.** Script autonome préparé sur la branche
`codex/diagnostic-kiwix`, issue de `origin/main` (`d57017c`), dans un worktree séparé.
Pas de fusion de main, de déploiement ni d’accès supposé au PC de Marc.

Le [bilan 0.13.0](2026-11-14-recherche-0120-et-travail-nocturne.md) établit les
mécanismes sur petits ZIM et laisse les délais réels à mesurer. Le nouvel outil
réutilise le diagnostic GET du portail, son flux SSE, sa couverture et ses traces.
Il ajoute des lectures Kiwix directes, une archive explicitement choisie, deux
passages successifs, un budget total et un export JSON conservant les résultats
partiels en cas d’arrêt. Le [guide actuel](../exploitation/diagnostic-performances-kiwix.md)
fournit commandes Windows/Linux, schéma, interprétation et limites.

Le premier passage ne revendique pas un état froid : aucun cache n’est supprimé.
La répétition peut réutiliser plusieurs couches de cache. Les ressources restent
« inconnu » sauf relevé local expressément demandé ; les ressources internes de
Kiwix ne sont pas accessibles par ces API. Aucun diagnostic matériel n’est déduit
de la latence seule. Les limites d’arrêt du calcul interne Kiwix sont explicites.

## Vérifications exécutées

Dans le runner Linux CPU :

```bash
python3 -m unittest discover -s tests -p test_kiwix_diagnostic.py -v
```

Huit tests réussis sur serveur HTTP local et réponses fictives minuscules :
ordre séquentiel et répétition, paramètres Kiwix `books.name` et filtre portail,
réception progressive avant fin, couverture et traces conservées, échéance avec
résultats partiels, erreurs HTTP/formats/volume, refus des redirections, budget
cumulé, annulation et export partiel sans écrasement, interruption SIGINT réelle d’un
sous-processus de diagnostic sous Linux, ressources inconnues et
rejet des arguments non bornés. Les erreurs réseau ne révèlent pas leur texte brut.

Aucun modèle, corpus, ZIM, index partagé ou service réel n’est utilisé. Tests
stdlib uniquement, sans nouvelle dépendance. `git diff --check` et compilation
Python du script et du test sont les contrôles complémentaires de livraison.
Les temps des fixtures ne sont pas publiés comme une estimation matérielle.

## Limites et périmètre

Windows réel, Python Windows, les postes de Louis/Marc et leurs ressources,
les archives Kiwix réelles et les certificats locaux ne sont pas testés ici.
La suite complète du produit n’est pas relancée : aucun module du service ou de
l’interface n’est changé. Aucun résultat sur le fonds de Marc n’est revendiqué.
La pertinence et la lecture humaine restent à vérifier après les mesures.

Seuls les quatre fichiers réservés sont ajoutés. Les index documentaires partagés
restent inchangés conformément au périmètre ; les deux nouveaux documents se
renvoient au guide et aux références existantes. Ni version produit, ni images,
ni dépendances, ni Compose, ni pilote, ni portail ne changent, conformément à la
demande explicite. Le diagnostic est un outil séparé à essayer volontairement,
pas une nouvelle livraison fonctionnelle des services.
