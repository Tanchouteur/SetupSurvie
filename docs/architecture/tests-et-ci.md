# Tests automatisés et CI

**Guide actuel — 20 novembre 2026, SetupSurvie 0.69.0.** Le [workflow GitHub
Actions](../../.github/workflows/tests.yml) contrôle les PR et les commits de
`main`. Une nouvelle révision d’une PR annule son ancien run.
Un run de `main` déjà démarré se termine si un autre commit arrive.

## Relancer en local

Dans un environnement Python isolé, à la racine du dépôt :

```sh
python -m pip install -r tests/requirements-kiwix.txt
python -m unittest discover -s tests -v
```

Les tests de configuration utilisent `docker compose config` sur des réglages
temporaires. Les essais Kiwix et OSRM utilisent de petites données synthétiques
et leurs propres services. La [stratégie d’ingénierie de tests](../essais/ingenierie-de-tests.md)
décrit les autres validations, de l’installation physique à l’évaluation des
modèles sur un vrai fonds.

Pour un test du portail, avec Node, les navigateurs Playwright 1.58.2 et
leurs bibliothèques système disponibles :

```sh
npm install --prefix /tmp/setupsurvie-browser playwright@1.58.2
BROWSER_ENGINE=chromium node tests/browser_translations_runner.cjs browser_ux_foundations.js
```

Sans nom de recette, le lanceur joue le lot du moteur choisi. Sans
`BROWSER_ENGINE`, il joue les trois moteurs. Il démarre l’API de test sur le
port 8769 et crée un contexte de navigation par recette. Ajouter les
recettes de ce serveur aux listes du lanceur. `BROWSER_PYTHON` permet de
choisir le Python du serveur, et `BROWSER_ARTIFACTS` le dossier de captures.
Les cartes hors ligne ont leur propre lanceur, `tests/browser_maps_runner.cjs`.

## Lire les résultats GitHub Actions

| Contrôle | Ce qu’il exécute |
| --- | --- |
| Python et paquet logiciel (Linux) | Découverte automatique, Compose et Caddy, recherche et mandataire de profils, construction et relecture du zip avec son SHA-256 |
| Python et lanceurs (Windows) | Découverte automatique, scripts PowerShell d’installation et de mise à jour, démarrage des outils YouTube |
| Lecteur d’index isolé (Windows) | Lecture d’une archive miniature en Python 3.11, 3.13 et 3.14 |
| Kiwix et OSRM | Archives et réseau routier synthétiques sur les moteurs prévus |
| Navigateurs | Portail dans Chromium, WebKit et Firefox, avec cartes hors ligne dans Chromium et WebKit |

Les étapes Windows se poursuivent après un échec de test, et les recettes du
portail affichent le nom et le résultat de chaque scénario. Un échec renvoie
un statut rouge, avec des captures du portail disponibles dans les artefacts
du run lorsque la page a pu être capturée. Le workflow ignore le navigateur
pour les PR dont le diff contient uniquement de la documentation. Sur
`main`, le navigateur est toujours testé.

L’artefact `logiciel-et-empreinte` contient le zip logiciel et l’empreinte
vérifiée après construction. Les résultats CI portent sur des runners
jetables. Les installations de Marc et de Louis, le Safari d’un iPhone,
la restauration depuis un disque physique et les réponses des modèles réels
relèvent de recettes sur le matériel cible.
