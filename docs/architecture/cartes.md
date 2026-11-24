# Architecture — cartes et itinéraires

**Référence d’architecture par domaine — découpée du README le 20 novembre 2026 (0.67.0).** Chaque section décrit un mécanisme au moment de sa livraison et reste valable sauf note de remplacement. Pour les fichiers, voir la [carte du code](carte-du-code.md) ; pour la vue d’ensemble, l’[architecture](README.md).

## Cartes et accès aux itinéraires — 0.11.0

La route protégée `/api/geography/shade/{z}/{x}/{y}.png` sert un
ombrage RGBA prêt à superposer (et non des hauteurs Terrarium). L’ancien endpoint
`/api/geography/terrain/` conserve son format DEM pour les lecteurs déjà ouverts.
Les mesures et profils d’altitude gardent les HGT originaux. Le cache mémoire est limité à 128
tuiles compressées, avec déduplication des générations identiques, concurrence
limitée à deux et invalidation par manifestes/fichiers. Le cache HTTP reste privé,
revalidé par ETag, après vérification du profil ; les autres API restent no-store.

`POST /api/admin/map-notebook/accesses` propose jusqu’à trois accès OSRM du profil
choisi dans les 1 000 m ; `near: [latitude, longitude]` restreint la recherche aux
100 m autour d’un clic manuel. Le calcul accepte un `access_token` facultatif par
étape. Les jetons signés sont liés au point, mode, évitements, graphe et délai de
quinze minutes ; ils deviennent invalides après redémarrage. Les erreurs de routage
conservent `detail` textuel et ajoutent un champ `code` stable ; le portail lit
aussi les réponses structurées `detail.code` / `detail.message` des essais. Les limites restent 12 calculs et 30 recherches d’accès par
minute et par profil.

Les instantanés JSON des nouveaux trajets ajoutent `connectors` et
`access_selected` ; aucune table n’est migrée. Les jetons et hints OSRM ne sont pas
conservés dans les trajets. Les versions anciennes restent lisibles. L’export GPX
n’ajoute pas les raccordements non vérifiés dans la trace routée.
