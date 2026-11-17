# Lecture et recherche sans réseau externe

**Bilan de développement — 17 novembre 2026, code produit 0.38.3.** Complète la
[recette Bazzite](2026-11-17-assistant-bibliotheque-bazzite.md), qui avait arrêté
les moteurs sans couper le réseau externe. Aucun code produit ni numéro de
version n’est modifié : seule une recette réutilisable est ajoutée.

## Conditions et résultats

Conteneur jetable du Docker TEST, `--network none`, racine en lecture seule,
stockage temporaire limité à 96 Mio, 512 Mio de RAM, un CPU, aucune capacité
Linux ni accès au GPU ou aux données utilisateur. Le dépôt de la recette est
monté en lecture seule. L’image déjà présente fournit Python 3.13.18 et les
dépendances FastAPI/httpx/pypdf/Uvicorn ; aucun téléchargement. Son identifiant
local est `sha256:7e5c855a7f1854e3940ea9e7d4a98c97b04cb146628b870089e4a896a4556e77` ;
ce n’est pas une nouvelle image imposée au produit.

`tests/real_offline_read_check.py --require-isolated` constate **lo uniquement,
zéro route IPv4**, puis lance le véritable service Uvicorn et appelle son API
par HTTP. Aucun outil métier n’est simulé. Kiwix, Ollama, WebUI et le contrôleur
pointent sur un port local fermé ; les profils et bases sont temporaires.

**13 contrôles réussis** : état/version, recherche et lecture d’un guide,
indexation d’une vidéo avec piste française, recherche d’un mot des paroles,
lecture de sa source et du WebVTT, octets MP4 servis, favori enregistré,
conversation créée, puis favori et documents associés conservés après
redémarrage du service, version identique. Les fichiers sont minuscules et
fictifs ; la piste française est fournie, pas générée pendant cet essai.

Contrôle négatif dans le runner connecté : refus avant création des fichiers
ou lancement du service, code de sortie 1 et zéro contrôle exécuté. Les premières
tentatives de conteneur ont échoué pour permissions du montage puis parce que
celui-ci masquait l’environnement Python de l’image ; montage séparé et utilisateur
root **du Docker rootless TEST**, sans capacités, corrigent uniquement le harnais.
Ces tentatives ne sont pas des échecs du service ni des essais réussis.

Le conteneur est supprimé après exécution et son stockage temporaire disparaît.
Aucun service de Marc, Bazzite ou R7 n’est démarré ou arrêté.

## Reproduire et limites

Voir le [guide d’usage hors ligne](../utilisation/verifier-usage-hors-ligne.md#recette-de-développement-avec-réseau-isolé).
Le conteneur doit disposer à l’avance des dépendances Python du pilote. Exemple
à adapter à une image existante, sans masquer son environnement Python :

```sh
docker run --rm --network none --read-only \
  --tmpfs /tmp:rw,nosuid,nodev,size=96m --cap-drop ALL \
  --security-opt no-new-privileges --memory 512m --cpus 1 --pids-limit 64 \
  -e PYTHONDONTWRITEBYTECODE=1 -e PYTHONPATH=/workspace \
  --mount type=bind,src="$PWD",dst=/workspace,readonly --workdir /workspace \
  --entrypoint python IMAGE_PILOTE_EXISTANTE \
  tests/real_offline_read_check.py --require-isolated
```

Les chemins de dépendances et les droits de lecture dépendent de l’image ; ne
pas modifier globalement les permissions du dépôt pour contourner un refus.
Le JSON contient les contrôles et limites, et une erreur renvoie un code non nul.

Cette recette ne décode pas le MP4 fictif, ne génère ni traduction ni transcription,
ne vérifie ni l’interface du navigateur ni le fonds Windows de Marc. Elle ne
remplace pas la coupure physique d’Internet du serveur et des appareils clients,
ni la relecture humaine des mots, chiffres, négations et synchronisation des vidéos.


## Échecs CI et contrôle des attentes

La [première CI de cette recette](https://github.com/Tanchouteur/SetupSurvie/actions/runs/44082621017)
termine avec six jobs réussis et deux échecs, conservés comme tels. Linux :
1 013 tests en 72,281 s, 6 ignorés. Windows dépasse les cinq secondes du helper
de transcription pendant une publication durable ; les logs montrent aussi
une préparation de fixture de 17 secondes. Le navigateur Chromium échoue sur
la présence d’une conversation dans son projet, après visibilité du conteneur.
Aucun changement produit ne distingue ce commit de la 0.38.3 déjà validée.

Les tests sont ajustés sans désactiver d’assertion : le workflow durable attend
au maximum 30 secondes au lieu d’un objectif de performance de cinq secondes ;
le test navigateur attend la conversation exacte, chargée de façon asynchrone,
avant de vérifier son imbrication. Aucun délai du produit n’est augmenté.
Avec une publication volontairement retardée de 5,2 s dans le processus de test,
l’ancien helper échoue (6,553 s), le nouveau réussit (6,745 s). Les 13 tests de
transcription passent en 11,612 s. Les 22 contrôles navigateur passent avec un
retard réseau de 800 ms sur les requêtes de projet. Les tentatives de reproduction
n’ont pas reproduit l’assertion Chromium initiale ; la course est identifiée
par lecture du chargement asynchrone, pas revendiquée comme incident reproduit.
