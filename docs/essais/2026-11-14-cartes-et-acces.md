# Cartes et choix d’accès — 14 novembre 2026

**Bilan de développement 0.11.0, branche `codex/cartes`.** La recette sur les PC
Linux de Louis et Windows de Marc reste distincte des essais décrits ici.
Références : [itinéraires](../utilisation/points-et-itineraires.md),
[relief](../utilisation/parametres-et-cartes.md).

## Défauts et changements

Louis signale des lenteurs et de grands carrés flous sur les deux PC, ainsi qu’un
échec de trajet Maison → La Fuan d’avou. La capture du trajet présente une erreur
générique 503 ; elle ne prouve pas qu’une voie manque. Le problème réel du moteur
sur chaque installation reste à diagnostiquer après mise à jour.

Le [décodeur raster-dem de MapLibre 5.10](https://github.com/maplibre/maplibre-gl-js/blob/v5.10.0/src/data/dem_data.ts) ignore l’alpha dans sa lecture des hauteurs.
Les anciennes tuiles mélangeaient hauteurs valides et altitude zéro transparente.
L’ombrage est désormais produit côté serveur en RGBA, avec transparence des zones
absentes et des surfaces plates, ombrage borné et échantillonnage des voisins.
Cela supprime ce mécanisme de fausses pentes et de masque opaque, sans prétendre
avoir reproduit la capture sur les machines physiques.

Le cache mémoire passe de 32 à 128 tuiles ; les générations identiques sont
regroupées. L’ETag tient compte du remplacement des HGT et des manifestes, et
l’authentification reste vérifiée avant chaque revalidation privée. Le middleware
ne remplace plus ces en-têtes par no-store ; les autres API restent inchangées.
La boucle d’interpolation évite les conversions répétées des outils publics.

Les changements de relief et le retour au départ conservent le style courant.
Les redimensionnements sont regroupés et le double cadrage des trajets supprimé.
La capture d’impression se fait sur une image du rendu synchrone, sans demander un
buffer préservé en permanence. L’ancien réglage était d’ailleurs une option de
premier niveau obsolète dans MapLibre 5 ; aucun gain GPU de sa suppression seule
n’est revendiqué.

Les propositions reposent sur le service local [nearest d’OSRM](https://project-osrm.org/docs/v5.24.0/api/#nearest-service), avec le profil et les exclusions du trajet.
Les accès proches demandés par Louis sont confirmés explicitement dans le panneau
existant. Ils restent distincts des points enregistrés et des liaisons non
vérifiées. Les erreurs locales sont catégorisées ; une panne moteur ne produit pas
de propositions artificielles. Les anciens trajets et les profils sans mot de
passe restent compatibles.

## Vérifications de développement

La suite locale termine **503 tests sans échec, dont 12 ignorés dans le runner**.
Les six recettes d’interface passent sur **Chromium et WebKit** dans le conteneur
TEST Playwright 1.58.2, limité à 1 CPU / 2 Go, sans secrets ni données réelles.
Le paquet de mise à jour 0.11.0 est construit et son manifeste contrôlé ; les
résultats de CI sont vérifiés séparément.

- Tests ciblés d’altitude/cache, validation des accès signés, erreurs de moteur,
  autorisations, snapshots et GPX sur petites données synthétiques.
- Playwright MCP / Chromium : choix au clavier et manuel, annulation, états
  d’erreur, réponse périmée, six formats de consultation et trois formats de rendu.
- Une archive PMTiles **fictive de 585 octets**, générée localement, vérifie de
  vraies lectures HTTP Range, routes vectorielles et polices locales. La couche
  raster et la conservation des trajets sont vérifiées avec le vrai MapLibre.
- Sur cinq générations à froid d’une dalle HGT synthétique plate dans le runner
  CPU, médiane avant/après **198,36 / 135,68 ms** ; cache chaud **0,38 / 0,42 ms**.
  Ce microtest ne mesure ni la fluidité GPU ni les performances des PC réels.
- Tests OSRM réels étendus dans la CI existante, avec l’image épinglée et le petit
  réseau OSM synthétique. Résultats distants à compléter après publication.

Les fixtures sont distinctes de vrais contenus : `display-small.pmtiles` est
reproductible par `tests/make_map_display_fixture.py` avec pmtiles 3.7.0 dans un
environnement jetable. Cette dépendance n’est pas ajoutée au produit. Le PNG RGBA
de test contient volontairement une zone transparente et ne représente pas un
terrain réel. Aucun modèle ni corpus réel téléchargé dans le runner.

## Recette réelle restante

1. Sur chaque PC, relever version, navigateur, données géographiques et état des
   trois services OSRM sans lancer l’IA ni interrompre les préparations actives.
2. Rejouer les deux captures : même zone et zoom, relief présent/absent, zooms et
   déplacements répétés. Comparer les délais et vérifier routes et noms lisibles.
3. Calculer Maison → La Fuan d’avou ; distinguer moteur, version du graphe,
   couverture et raccordement avant de conclure à l’absence de chemin.
4. Si nécessaire, choisir un accès, contrôler les distances séparées et enregistrer.
   Recharger le trajet moteur arrêté, puis vérifier impression et GPX.
5. Essayer un autre accès, une zone sans altitude, les modes piéton/moto/voiture,
   deux onglets et un changement de profil. Aucun raccordement n’est certifié
   praticable par ces essais logiciels.

Pas de déploiement sur les PC dans cette livraison de branche. Safari iPhone
physique et fonctionnement hors Internet restent à contrôler. Le test automatisé
WebKit ne remplace pas ces validations.

## Coordination et version

La branche a repris `main` 0.10.0 après le lot de recette de recherche/lecture,
sans modifier la navigation ni Compose. Les changements communs concernent les
routes cartographiques du pilote, la version et quelques renvois documentaires.
L’intégration sur main se fera séparément du chantier recherche, après contrôle.

**0.11.0** est une évolution fonctionnelle compatible : sélection d’accès et
nouveaux états d’itinéraire. Le schéma de données et les versions des composants
tiers restent inchangés. Le nouvel endpoint d’ombrage est séparé de l’ancien endpoint DEM, conservé
pour les lecteurs déjà ouverts. Recharger l’onglet permet de bénéficier des
corrections du nouveau lecteur.
