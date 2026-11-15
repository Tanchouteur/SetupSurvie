# Rapport réel 0.15.0, demandes de synthèse et changement de modèle

**Bilan daté — 15 novembre 2026 ; correction 0.15.1.** Les pièces transmises par
Louis comprennent un R2 sans IA et deux captures de conversations. Les fichiers
bruts restent privés ; aucun accès au PC de Marc ni modèle réel n’est lancé ici.

## Rapport reçu

Le JSON de 971 938 octets est créé le 15 novembre à **11:15:41 UTC**, en version
0.15.0. SHA-256 : `4e11c51017f7c597a50277f79e0a5baf60f934dd9455a180dbe3b9c058e0db0c`.

Les **32 recherches sont complètes**, avec zéro archive en échec, zéro archive
laissée sans tentative et aucune reformulation omise. Première réponse médiane
**268 ms** sur les 31 cas avec document, fin médiane **2 112,5 ms**. La durée
maximale est 45 655 ms. Le cas négatif garde zéro résultat. Feu, générateur et
vélo retrouvent des titres directement liés au besoin ; solaire remonte désormais
« DIY Solar Panel Install ».

Le cache est déjà chaud : **1 099 des 1 155 traces** réutilisent une réponse.
La comparaison des médianes 36,24 s en 0.14.0 et 2,11 s ici ne doit donc pas être
attribuée entièrement au code. Le cas « faire du feux », entièrement en cache
dans les deux rapports, passe de 19 621 à 1 930 ms ; cela reste un constat sur
ces deux campagnes, pas une garantie pour tous les besoins. Aucun avis humain
n’est encore enregistré ; les 32 résultats ne sont pas déclarés pédagogiquement
validés ou lus.

## Échec de liaison avec l’assistant

Les captures montrent une demande de synthèse sur le feu, successivement avec
GPT-OSS 20B et Gemma4 E4B. Les modèles parlent d’absence de documents ou proposent
encore de chercher ; le suivi indépendant indique une recherche limitée et
aucune source consultée. Cette contradiction ne prouve pas que la bibliothèque
manque de documents. Les captures ne suffisent pas à expliquer les réponses qui
n’aboutissent pas « une fois sur deux » : les mesures de ces demandes sont absentes.

Le code 0.15.0 reproduit un défaut précis : « synthese » et « info » dans la phrase
de Marc deviennent des groupes obligatoires en plus du feu. La commande de résumé
réduit donc le rappel avant même la lecture des sources. La relance pratique sur
le frottement conserve aussi le mot « comme », manque le lien FR/EN avec friction
et n’est pas automatiquement préparée comme lecture.

## Correction et portée

La 0.15.1 sépare une instruction explicite de résumé de son sujet, pour la
recherche commune comme pour celle préparée dans l’assistant. Elle garde les
emplois techniques de « synthèse », les prépositions utiles du sujet et le périmètre
de collection. La demande originale reste dans la conversation et dans le plan,
afin que le modèle reçoive toujours le format demandé.

« Comme » ne devient plus un mot documentaire obligatoire. Frottement/friction
partagent un concept bilingue, sans assimiler toute recherche de frottement au
feu. Une demande pratique portant une action connue prépare la recherche et la
lecture avant le premier appel au modèle, après les exclusions géographiques
et calculatoires existantes.

Le niveau **z** est retenu : correction compatible d’une préparation déjà promise,
sans nouveau parcours de synthèse multi-document. Budget documentaire, nombre de
documents prélus, profils/modèles et schéma privé 1 restent inchangés. Le
[programme de synthèse et illustrations](../decisions/assistant-recherche-et-synthese.md)
trace la suite demandée et la boucle d’outils contrôlée ; elle n’est pas annoncée
livrée par ce seul correctif.

## Changement de modèle signalé pendant la correction

Louis décrit un premier envoi qui semble seulement décharger le modèle précédent,
puis un second qui fonctionne. Aucun rapport de durée de ce cas n’est fourni :
le déchargement comme cause exacte reste une hypothèse. Le code reproduit en
revanche la fin d’une demande sans reprise quand le premier flux est vide ou
qu’une erreur transitoire survient avant toute sortie.

`pilot/model_session.py` prépare explicitement le modèle choisi si un autre est
chargé ou si un contexte connu change, avec le même contexte et maintien cinq
minutes. L’appel sans messages est un chargement documenté dans le code Ollama
[épinglé 0.40.13](https://github.com/ollama/ollama/blob/v0.40.13/server/routes.go)
et sa [FAQ officielle](https://docs.ollama.com/faq#how-can-i-preload-a-model-into-ollama-to-get-faster-response-times),
consultés le 15 novembre. Le moteur gère l’éviction ; aucun arrêt arbitraire ni
changement automatique de modèle/contexte n’est introduit.

Une seule reprise par demande est partagée entre préparation et appels du modèle :
flux vide, erreur transitoire HTTP 500/502/503/504, transport avant toute sortie
ou mémoire explicitement signalée. Dès qu’un texte, une réflexion, des tokens ou
un appel d’outil existe, le flux n’est pas rejoué. Les limites de sortie et erreurs
permanentes ne sont pas relancées. Pause vérifiée avant préparation/reprise,
annulation propagée, question/lectures conservées, erreur finale compréhensible.
La préparation/cold start admet 300 secondes sans données ; le modèle déjà chargé
reste à 180 secondes, dans le plafond global de quinze minutes.

Le portail affiche chargement/changement/reprise. **Voir les durées** présente
préparation et nombre de reprises ; l’export ajoute les motifs bornés, sans texte
privé ni erreur brute. Caches des deux scripts renouvelés par le générateur ; pas
de changement d’organisation UX. Les traitements de traduction/comparatif ne
passent pas encore par cette session.

## Vérifications

Les nouveaux tests reprennent la phrase exacte de Marc, des variantes FR/EN,
le sujet « synthèse chimique », une demande historique et la conservation de
« corrosion sur acier ». Un test SQLite FTS réel sur minuscules documents vérifie
que demande de synthèse et sujet retrouvent puis ouvrent la même source fictive.
L’orchestration avec HTTP simulé vérifie la lecture avant le premier appel au
modèle pour la synthèse et la relance sur le frottement.

La suite finale exécute **616 tests en 89,054 s**, trois contrôles COM Windows
ignorés dans le runner Linux. Les 13 tests de session et les tests d’orchestration
HTTP couvrent changement prêt, contexte modifié, modèle déjà chargé, récupération
vide/transitoire, limite partagée, erreur permanente, flux partiel, pause et
annulation. Aucun double message enregistré après reprise.

La recette Kiwix native réussit **69 contrôles** sur cinq archives minuscules
créées localement, **290 961 octets**. Un premier essai attendait à tort un article
anglais générique sans passage sur le frottement pour cette demande spécifique ;
la fixture ajoute un vrai passage fictif de friction et vérifie son ouverture.
Le classement n’a pas été assoupli pour forcer cette mauvaise attente.

Les essais navigateur réussissent **78 contrôles par navigateur**, Chromium et
WebKit : états du modèle 20, durées 21, confort 37, avec API fictive et aucun modèle
réel. Les trois recettes ont aussi été exécutées via le MCP Chromium. La seconde
campagne utilise l’image Playwright déjà présente, sans téléchargement lourd.
Les vues sont vérifiées jusqu’à 320 pixels ; cela ne remplace pas un iPhone réel.
Les reçus du paquet et de la CI sont consignés après publication. Aucun gain de fidélité d’un modèle
réel, aucune synthèse de cinq documents et aucune extraction de schéma PDF ne
sont déduits de ces tests. Le changement de modèles réel sur Windows reste à
vérifier avec le [protocole assistant](recettes-progressives-marc.md#prochaine-validation-assistant--0151).
