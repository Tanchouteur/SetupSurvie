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
