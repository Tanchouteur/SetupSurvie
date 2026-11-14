# Rapports 0.12.0 et suite du moteur de recherche

**Bilan de développement 0.13.0 — 14 novembre 2026, CI à confirmer.** Les deux exports transmis par Louis
à 21:42/21:43 UTC restent dans les pièces jointes privées. Aucun corpus volumineux
n’est copié dans le runner ; ses environ 8,7 Go libres demandent des fixtures
minuscules. Cette contrainte de test n’est pas une limitation du produit cible.

## Faits des rapports

L’examen des 135 archives termine sans erreur : 120 index natifs compatibles,
15 compléments locaux et 3 238 articles extraits. Les 14 archives multilingues
dont la recherche native était refusée disposent de leurs compléments, dont
Low-tech Magazine. Les 15 SQLite sont interrogées sans erreur ni péremption.
Des guides pratiques de générateur et de solaire apparaissent effectivement
dans les résultats. Les anciens 120 articles ne décrivaient donc pas tout le fonds.

Les 32 recherches restent partielles, médiane 12 586 ms, maximum 13 114 ms ;
31 atteignent l’échéance globale. Le cas Wikipédia termine plus tôt mais avec
un appel natif et une suggestion expirés. Les traces n’ont plus de HTTP 400 :
le traitement multilingue a bien changé le résultat réel. Elles contiennent
91 appels plein texte et dix suggestions expirés, plus une reformulation expirée.
Les résultats utiles et la vitesse ne sont donc pas déclarés validés.

## Décisions supplémentaires de Louis

- Continuer pendant la nuit sans attendre d’essai utilisateur ; créer un
  environnement de test borné à de petits documents et archives, sans modèle réel.
- Un délai supérieur est acceptable si nécessaire ; afficher les documents
  trouvés progressivement pour permettre la lecture pendant que la recherche
  continue. Garder arrêt, état courant et limites honnêtes.
- Un cache utile peut être volumineux. **2 Go est un exemple, pas un plafond** ;
  sa taille doit pouvoir évoluer. Il doit suivre les modifications du fonds et
  des index, éviter les calculs répétés et ne pas mémoriser une panne comme absence.
- Ne pas brider l’objectif fonctionnel pour le matériel actuel. Mesurer les
  blocages ; un achat de matériel supérieur est envisageable si le besoin est
  établi. Cette intention n’est pas un achat ni un nouveau matériel déjà disponible.
- Les six dossiers pratiques ne constituent pas la structure principale ni la
  preuve de couverture : recherche générale, connaissances et guides sur tous
  les sujets disponibles restent le cœur demandé.
- Après fiabilisation de la recherche, avancer ou au moins étudier/documenter
  traduction et sous-titres. Les vidéos 480p ajoutées dans `library/video/` doivent
  rejoindre la recherche documentaire commune ; voir le
  [besoin des vidéos locales](../decisions/videos-locales-et-recherche.md).

## Pistes à éprouver

Les lots natifs longs, les expirations répétées et la réutilisation des moteurs
de recherche Kiwix doivent être reproduits. La source officielle de libkiwix
dimensionne ses caches d’archives et de moteurs selon le catalogue ; les options
exactes de l’image épinglée et leur effet doivent être vérifiés avant changement.
Une mesure sur petits fichiers n’est pas extrapolée aux 755 Go de Marc.

## Correction réalisée

La version passe à **0.13.0** : diffusion progressive et cache disque constituent
une évolution fonctionnelle compatible, d’où le changement du niveau mineur.
Le schéma privé reste 1 et les images tierces restent épinglées sans modification.
Le JSON des anciens clients et des outils garde son fonctionnement et son budget.

Le portail et le contrôle exportable consomment le même moteur en flux SSE.
Les guides puis les articles peuvent apparaître sans attendre le dernier appel ;
la lecture reste ouverte. Arrêt, déconnexion et nouvelle demande annulent le
travail du client et conservent les résultats déjà reçus. Les mises à jour en
attente sont regroupées, sans accumulation de messages. Le budget natif de ce
parcours passe de 12 à 60 secondes, chaque plein texte de 3 à 10 secondes et
chaque titre de 2 à 5 ; le contrôle autorise 90 secondes par demande.
Il exporte aussi le délai d’arrivée des premiers documents et le nombre de mises
à jour reçues, séparément de la durée finale.
Les limites d’appels et de voies simultanées sont conservées, avec couverture
partielle honnête si nécessaire. Aucun appel IA n’est ajouté.

Le cache mémoire dure cinq minutes ; un cache SQLite reconstructible conserve
les seules réponses valides au plus 24 heures. Une empreinte de l’état des ZIM,
des identifiants et du manifeste rend les anciennes réponses inéligibles après
changement. Le budget disque initial de 2 Go est ajustable et transmis au service
Windows/Linux et au laboratoire ; une valeur de 8 Go est acceptée dans les tests.
La réserve libre reste distincte. Un cache absent, corrompu ou plein ne doit pas
empêcher une recherche. Voir le [guide de référence](../exploitation/cache-et-recherche-progressive.md).

## Vérifications exécutées dans le runner

- **521 tests Python réussis, trois ignorés**, avec FastAPI/httpx et libzim dans
  l’environnement isolé. Treize nouveaux cas vérifient notamment guides reçus avant
  catalogue lent, flux borné, déconnexion, erreurs privées, favoris, requête vide,
  renouvellement du fonds, cache invalide et quota. Une réponse simulée à 3,1 s
  expire avec l’ancien budget mais aboutit avec le nouveau.
- **35 contrôles Kiwix 3.8.1 réels** sur cinq ZIM fictifs générés, 283 Ko :
  langues multilingues, compléments, requêtes et recherche directe conservés.
- **28 contrôles à 135 archives**, 8 280 525 octets générés : huit demandes
  couvrent feu, générateur, eau, vélo, comète, langue, musique et fractions. Toutes
  les collections éligibles sont examinées sans échec, avec résultats progressifs.
  Premiers résultats entre 29 et 57 ms, fin entre 1 267 et 2 416 ms sur ces seuls
  fichiers minuscules lors du second passage. Une répétition à chaud n’ajoute
  aucun appel HTTP natif ; après effacement de la mémoire du processus, le cache
  disque réutilise aussi les réponses natives réelles sans nouvel appel. La réserve
  disque est abaissée uniquement pour ces fichiers temporaires de test.
- **Chromium MCP : 18 contrôles de flux HTTP réel**, backend et documents de test,
  puis **50 contrôles de recherche** réussis dans un contexte neuf.
  Lecture pendant attente, passages dépliés et focus clavier conservés, arrêt, erreur, rechargement
  et largeurs 1 366/390/320 pixels sont couverts. Pas d’erreur JavaScript observée.
- **Caddy épinglé réel** : le premier paquet traverse le proxy avant la fin du
  traitement ; aucune modification de sa configuration n’est nécessaire.
- **19 tests d’installation ciblés réussis** après ajout du budget cache ; Compose
  Windows, Linux CPU et Linux GPU acceptent la valeur de 8 Go. Aucune installation
  système réelle n’est lancée. La CI Windows et navigateur reste à confirmer.

Les médias, corpus et réponses des fixtures sont fictifs. Aucun modèle, ZIM du
fonds ou vidéo YouTube n’est téléchargé ; les environnements natifs temporaires
sont supprimés. Ces temps ne sont pas une mesure des performances de Marc.
WebKit dépend de la CI ; un test réel Safari iPhone n’a pas été exécuté.

## Livraison et limites restantes

CI, intégration main et audit du paquet : à compléter après exécution.
Le prochain R2 doit mesurer le fonds réel à froid puis à chaud, la couverture et
les appels réutilisés, puis ouvrir feu/eau/générateur/vélo et quelques sujets de
culture. Les avis humains sont nécessaires pour qualifier l’utilité. Le rapport
0.12.0 justifie le changement de budget ; il ne mesure pas son nouveau gain.
Les nouveaux index ne sont pas à reconstruire intégralement pour ce seul essai.

Le cache interne de moteurs Kiwix peut contribuer aux ouvertures répétées ; cette
piste n’est pas mesurée sur le PC cible et aucune nouvelle allocation native n’est
imposée. CPU, disque et RAM devront être distingués avant un changement matériel.
La suite traduction/vidéos est [étudiée et documentée](../decisions/videos-locales-et-recherche.md),
avec sources officielles, ordre de livraison et contrôle par média. L’indexation
des paroles, l’acquisition de pistes et le lecteur synchronisé ne sont pas livrés
par cette correction du moteur.

## Audit du paquet

Le paquet du code `51f9f02` a été construit puis déballé avec le lecteur de mise
à jour : **729 fichiers acceptés**, 6 578 027 octets compressés, version 0.13.0 et
schéma 1. Tous les fichiers déballés sont identiques aux sources de ce commit,
notamment le cache, le flux et la mesure des premières réponses. Aucun ZIM, modèle,
base cache ou média vidéo n’est inclus. Empreinte du paquet audité :
`37049168d0d516c2cd1d04680c50718b834dcaeaaba25899b0175fa89d48e481`.
Le présent complément de bilan modifie seulement la documentation ; il ne change
pas ce code validé. Cet audit ne vaut pas déploiement chez Marc.

## Corrections issues de la CI

Le premier scénario WebKit utilisait une phase intermédiaire de 0,8 seconde,
trop courte pour assurer son observation avant la fin ; le premier scénario de
lecture attend maintenant 1,8 seconde. Le rapport doit accepter des premiers et
derniers paquets reçus ensemble : des durées égales sont légitimes et ne doivent
pas être transformées en avance artificielle. Les assertions gardent valeurs
finies, cohérence chronologique et mises à jour effectivement reçues. Le code
n’invente pas une première réponse avant la réception réelle. Chromium et WebKit
ont ensuite réussi les 18 contrôles de flux, les 50 de recherche et les 175 de
paramètres sur `b4a9637` ; le job Windows de ce même passage a révélé le cas suivant.

Sous Windows, un contrôle d’ordre des reformulations limité à une seconde a
expiré pendant une écriture du nouveau cache. Le thread SQLite pouvait continuer
après l’annulation et empêcher le nettoyage du dossier (`WinError 32`). La
correction sérialise les écritures en arrière-plan, avec file limitée à 8 Mo et
256 réponses. Elles ne retardent plus le résultat HTTP. L’arrêt attend leur fin,
et une lecture annulée attend la fermeture de son accès. Deux tests avec thread
volontairement bloqué vérifient livraison avant écriture, attente à l’arrêt et
fermeture avant terminaison de l’annulation. Le test d’ordonnancement désactive
le cache disque, dont il ne mesure pas la vitesse ; son ordre reste vérifié.
La nouvelle campagne locale termine à 521 tests, trois ignorés, et les 28 contrôles
Kiwix à 135 archives, dont la réutilisation disque après effacement de la mémoire,
réussissent encore. CI finale et nouvel audit du paquet à confirmer.

Un passage Windows suivant a identifié quatre anciennes suites qui supprimaient
leur dossier temporaire avant la fermeture du moteur. Elles enregistrent maintenant
le nettoyage asynchrone du cache avant celui des fichiers, comme le service le fait
à l’arrêt. Les assertions de recherche et leurs données ne changent pas. Ce second
écart concernait le cycle de vie des fixtures ; il reste distingué du premier
thread survivant à l’annulation. La persistance disque est testée séparément sur
les vrais petits ZIM et avec les threads volontairement retenus.
