# Consoles spontanées Windows — 14 novembre 2026

**Correctif candidat 0.1.36 — branche locale, non publié sur main à la demande de Louis.**

Le PC conserve son interface 0.1.34 ; seuls les scripts hôte nécessaires ont été
actualisés. Le paquet complet candidat n’est pas déployé. Le correctif reste à
intégrer à la refonte en cours avant une future mise à jour générale. Le parent des outils GPU et les processus de
console ont été relevés par l’API Windows de liste des processus, sans arrêter
Ollama, Docker ou le réseau. Une première tentative d’abonnement WMI a été
annulée par Windows ; la capture retenue est la capture native suivante.

Avant : trois lancements de nvidia-smi et de leur conhost en 45 secondes.
Après suppression du sous-processus au profit de NVML : zéro en 135 secondes,
mesures conservées. Ce constat est borné à la fenêtre d’observation, pas une
garantie portant sur toutes les applications du PC.

La livraison comprend aussi le lanceur pythonw des tâches automatiques, la
migration des helpers stables lors des mises à jour, et la conservation des
préférences/tâches désactivées. Les tests contrôlent : mémoire/température NVML,
libération du pilote, pilote absent, absence de sous-processus GPU sous Windows,
arguments sans shell, code d’échec PowerShell, propriété du lanceur, préférences
conservées et absence d’activation implicite d’un démarrage non configuré.

L’IA native déjà lancée reste intacte. Aucun essai d’inférence ni redémarrage du
PC n’est nécessaire pour appliquer la correction du contrôleur. Le nouveau
lanceur est testé séparément et les scripts hôte corrigés sont appliqués avec la
bibliothèque et les cartes conservées. Les incidents et limites sont consignés
dans le [journal Windows](../exploitation/journal-incidents-windows.md#win-018--consoles-répétées-malgré-le-masquage-des-mesures-gpu).


Retour utilisateur : les fenêtres ont cessé après le correctif local. Les tâches
de démarrage et les deux tâches de reprise retournent 0 après migration et
réarmement du plan confirmé. Le sondage réseau local et les mesures NVML restent
séparés d’un essai d’inférence, qui n’a pas été lancé pour cette correction.
La suite étendue a nécessité de remplacer une ancienne fixture Linux de 590 Go
par 1 Ko simulé ; son temporaire a été retiré après arrêt du seul processus de test.


Validation finale locale : **350 tests exécutés, 339 réussites et 11 ignorés**
sur Windows (cas Linux/COM/liens non disponibles selon le test). L’ancien cas
`pwrite` du laboratoire est correctement réservé aux plateformes le proposant.
Le kit miniature inclut le nouveau helper de démarrage. `git diff --check` est
réussi. Les tests et captures ne prétendent pas couvrir les consoles d’autres
logiciels ni constituer un redémarrage à froid du PC.


Trois vérifications réelles du site sain, via le helper installé, sont réussies
avec interdiction simulée de créer un enfant : aucun PowerShell ni autre helper
n’est lancé pour ce contrôle périodique. Le paquet candidat a été rangé parmi les
livraisons locales non publiées, pour ne pas le présenter comme une sortie de main.


## Mise à jour locale demandée ensuite par Louis

Après la validation du correctif hôte, Louis demande aussi d’actualiser le site
encore affiché en 0.1.34. Le candidat local **0.1.36**, construit sur main 0.1.35
avec le correctif des consoles, est alors déployé entièrement. Main n’est ni
modifié ni poussé. Les contrôles HTTP par le nom local annoncent 0.1.36 ; 615
fichiers installés correspondent au paquet. Les 127 fichiers de l’instantané
privé sont vérifiés et les anciens enregistrements, réglages, bibliothèque et
cartes sont conservés. Le serveur Ollama garde son processus initial.

Un défaut distinct de routage, préexistant au déploiement, est relevé : les trois
conteneurs créés à 09 h 52 redémarrent sur un refus de lecture de
`network.osrm.fileIndex`. Ce déploiement ne modifie pas leurs fichiers ni leurs
permissions. L’accès aux fonds de carte reste disponible ; le routage nécessite
un diagnostic séparé. Les détails de déploiement restent dans les diagnostics
locaux, sans publication de données privées.


## Intégration après réparation Docker — pilote 0.2.0

La restriction temporaire de publication est levée par Louis après réparation
Docker ; il autorise fusion, déploiement et push. La refonte moteur de main
0.1.36 est conservée. Le numéro 0.2.0 est choisi pour cette livraison regroupée,
sans migration de schéma. Les anciens paragraphes décrivent la chronologie du
correctif local avant cette nouvelle autorisation.

La suite intégrée avant changement du seul numéro de version exécute 365 tests,
354 réussites et 11 ignorés sur Windows. La recette PowerShell passe aussi, y
compris les nouveaux cas refus du GUI sans enregistrement et limitation des
relances. La réparation Docker et sa sauvegarde froide sont détaillées dans
WIN-019. La cause initiale de perte du registre reste indéterminée.

Le déploiement réel en 0.2.0 est terminé : 626 fichiers logiciels vérifiés,
127 fichiers d’instantané privé contrôlés et anciens enregistrements conservés.
Le plan documentaire ne contient aucun ajout restant (181/181). Les tailles des
modèles, ZIM et cartes, les reçus, réglages et préférences de reprise sont
inchangés. L’API de santé répond en 0.2.0 sans fonction dégradée ; les 102 guides
sont indexés. La lecture réelle d’une page PDF, les deux fonds de carte et les
mesures GPU natives sont vérifiés, sans lancer d’inférence.

Les trois tâches automatiques utilisent `pythonw.exe` et leur dernier résultat
est zéro. La recherche globale retrouve des sources mais annonce une couverture
partielle selon le budget et les index disponibles ; cela ne valide pas toutes
les collections. Le défaut de routage décrit plus haut reste ouvert. Aucun
redémarrage complet du PC ni essai client Wi-Fi supplémentaire n’est effectué.
