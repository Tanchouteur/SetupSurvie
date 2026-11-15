# Prompts pour deux agents en parallèle

**Coordination proposée à Louis — 15 novembre 2026.** Le moteur, son classement
et sa livraison restent pris en charge par l’agent principal. Les deux chantiers
ci-dessous ont des fichiers distincts. Copier chaque bloc dans une session séparée.
Les chemins de worktree sont ceux du runner ; ailleurs, créer un équivalent isolé.

## Agent 1 — Inventaire vidéo et sous-titres

```text
Projet SetupSurvie. Prépare l’inventaire des vidéos et de leurs sous-titres, pendant
qu’un autre agent fiabilise le moteur de recherche. Lis les AGENTS.md applicables,
docs/decisions/videos-locales-et-recherche.md et
docs/essais/protocole-sous-titres-videos.md. Commence par status puis pull --ff-only.
Crée la branche codex/videos-inventaire et un worktree séparé sous
/srv/happier/workspaces/tasks/setupsurvie-videos-inventaire, depuis origin/main à jour.

Marc ajoute des vidéos YouTube 480p dans library/video/. Nous voulons ensuite les
chercher avec les documents et disposer de sous-titres français pour chaque vidéo.
Implémente maintenant un outil Windows/Linux en lecture seule, sans IA ni Internet,
qui inventorie les médias terminés, titres, métadonnées associées et pistes locales
SRT/WebVTT. Exploite les .info.json lorsqu’ils existent, sans leur faire confiance.
Signale français disponible, piste source seulement, piste manquante, format invalide,
durée/langue inconnue, fichier incomplet et examen partiel. Ne déclare pas le sens,
la synchronisation ou l’exhaustivité validés sans preuve. Le rapport JSON doit être
exportable et expliquer les limites et la prochaine action pour chaque média.
Préserve les originaux ; ignore les .part et refuse les sorties dans le fonds source,
les liens sortant du dossier et les métadonnées démesurées. Aucune copie des vidéos.

Fichiers réservés : scripts/library_videos.py, tests/test_library_videos.py,
docs/utilisation/inventaire-videos.md et docs/essais/2026-11-15-inventaire-videos.md.
Ne modifie ni moteur, interface, Compose, installation, dépendances, VERSION/release,
ni index documentaires partagés. L’intégration et ces renvois seront faits par l’agent
principal. Utilise seulement des fixtures minuscules ; aucun modèle/corpus téléchargé.
Teste les erreurs, fichiers incomplets, pistes absentes/mal formées et la conservation
des originaux. Committe et pousse ta branche ; ne fusionne pas main toi-même.
Rends branche/commit, commande Windows à copier, exemples du rapport, preuves et limites.
```

## Agent 2 — Diagnostic des délais Kiwix

```text
Projet SetupSurvie. Un autre agent corrige le moteur ; ton périmètre est un outil de
diagnostic en lecture seule, sans modifier son comportement. Lis les AGENTS.md,
docs/essais/2026-11-14-recherche-0120-et-travail-nocturne.md et
docs/exploitation/cache-et-recherche-progressive.md. Commence par status et pull
--ff-only. Crée codex/diagnostic-kiwix dans un worktree séparé sous
/srv/happier/workspaces/tasks/setupsurvie-diagnostic-kiwix, depuis origin/main à jour.

Les 135 archives de Marc sont examinées, 15 compléments locaux prêts. En 0.12.0,
31/32 recherches atteignaient le budget de douze secondes. La 0.13.0 ajoute budget
long, flux progressif et cache. Il manque une mesure distinguant recherche directe
Kiwix, réponse du portail, réutilisation à chaud et pression matérielle réellement
observable. Ne présume pas que le CPU, la RAM ou le disque sont responsables.

Prépare une commande Windows/Linux explicite, annulable et bornée, fournissant un
JSON exploitable sans modèle IA. Réutilise les diagnostics existants. N’exécute les
mesures natives que sur demande, avec quelques requêtes représentatives ; ne lance
pas toutes les collections simultanément et n’efface pas les caches pour simuler
le froid. Distingue observation froide/non établie et répétition chaude. Mesure
premiers résultats, fin, couverture, erreurs, et ressources seulement si accessibles
sans nouveau privilège. Une donnée inaccessible reste inconnue. Aucun chemin privé,
secret, conversation ni journal brut dans le rapport ; argument d’URL et paramètres
strictement bornés. Explique quand l’essai représente une charge sur le PC.

Fichiers réservés : scripts/diagnose_kiwix.py, tests/test_kiwix_diagnostic.py,
docs/exploitation/diagnostic-performances-kiwix.md et
docs/essais/2026-11-15-diagnostic-performances-kiwix.md.
Ne modifie ni pilot/, portail, Compose, caches internes, dépendances, VERSION/release,
ni index documentaires partagés. Pas de modèle ou de corpus lourd téléchargé dans
le runner ; petites fixtures/services simulés pour les tests. Aucun accès supposé
au PC de Marc. Committe et pousse la branche, sans fusionner main. Fournis commande
Windows, exemple JSON, tests, mesures effectivement faites et questions restantes.
```

Chaque agent doit annoncer son périmètre et sa branche avant de commencer. Les
changements sortant de ces fichiers doivent être signalés pour coordination ;
ils ne sont pas à appliquer silencieusement. Louis peut transmettre leurs comptes
rendus à la session principale pour intégration successive et vérification.
