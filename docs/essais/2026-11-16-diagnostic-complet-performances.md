# Diagnostic commun des lenteurs — 16 novembre 2026

**Bilan de livraison 0.22.0.** Le [guide actuel](../exploitation/diagnostic-complet-performances.md)
décrit son utilisation ; la [demande initiale](../decisions/diagnostic-lenteurs-en-un-clic.md)
reste conservée. Nouvelle fonction compatible : niveau mineur, schéma 1 et
versions des images tierces inchangés. Aucun déploiement sur les PC clients.

## Changement

Un seul lancement dans Entretien enchaîne onze étapes de recherche et IA et
échantillonne les ressources du PC serveur. Le rapport sépare arrivée des premiers
documents, fin, couverture, CPU du pilote, chargement du modèle, traitement de
l’entrée, premier texte, rédaction, lecture et débit de tokens. CPU par cœur,
disque, RAM et GPU viennent du contrôleur natif, pas du navigateur.

La mesure continue sans l’onglet, reste annulable et conserve les résultats
partiels. Un moteur arrêté ou en pause ne démarre pas. Les demandes ordinaires
prennent la priorité sur les essais IA. Contrôleurs anciens, mesures absentes,
étapes non réalisées et volumes non rapprochés restent explicites. Aucun verdict
matériel ou certificat de qualité n’est produit automatiquement.

## Tests de développement

Tests ciblés : deltas CPU/disques, remise à zéro, premier échantillon, compteurs
manquants, PDH anglais, pont authentifié, absence de fuite privée, pause,
annulation immédiate/en cours, redémarrage et nettoyage limité au test.
Une réponse terminée sans lecture effective est signalée séparément.
L’API exige Famille et un GET ne lance aucune inférence. Le contrôle natif Windows
et les onze tests de campagne passent dans le job Windows.

Quinze contrôles passent dans Chromium et WebKit : ouverture sans action,
lancement unique, suivi, navigation, arrêt, export, erreur mémoire visible et
affichage à 1366/390/320 pixels. Les états de ces tests sont simulés ; aucun
modèle ou corpus n’est téléchargé dans le runner CPU.

## Essai réel et défaut découvert

R7, Gemma `gemma4:e4b` déjà installé, Ollama natif 0.40.14, contexte 16k,
32 couches GPU, six threads, réserve vidéo 1536 Mio et maintien quinze secondes.
Les fonctions natives de collecte sont réelles, appelées directement dans la
recette ; le pont HTTP est testé séparément. Trois petits textes sont fictifs :
ces durées ne représentent pas les centaines de Go de Marc. Aucun téléchargement,
arrêt de tâche tierce, changement GPU ou déchargement forcé.

Le premier rapport privé `report-gemma4-performance.json` termine techniquement
en 26 894 ms, mais les réponses documentaires n’ont lu **aucune source**.
« Fais une courte synthèse des documents de la bibliothèque sur… » laissait des
mots de consigne dans le sujet. La correction générale accepte les adjectifs de
longueur et le cadrage documentaire, tout en préservant les usages techniques de
« synthèse ». Le protocole ajoute une lecture avec documents déjà trouvés pour
isoler la recherche naturelle. Une réponse sans lecture porte désormais cette
limite, indépendamment du statut `done`.

Le rejeu privé `report-gemma4-performance-0220.json` termine les onze étapes en
**28 417 ms**, avec dix échantillons natifs. Une source est réellement lue dans
chacune des réponses documentaires et dans celle à document sélectionné.
La première rédaction seule prend 11 007 ms, puis 5 458 ms ; le premier rapport
séparait environ 4,9 s de chargement initial. Cela démontre la séparation des
mesures sur cet essai, pas un diagnostic du HDD ou de la VRAM de Marc.
La couverture des archives reste partielle : elles sont absentes de la fixture.
Empreinte Python du rejeu :
`202931f96049d48d6ff28484324b54bdbbb754bf3a6046f63bc6418ab4c3395c`.
Le nettoyage après crash a ensuite été complété et vérifié par tests simulés.

## Suite de la qualification

Code fonctionnel `1badd20`, [huit jobs CI réussis](https://github.com/Tanchouteur/SetupSurvie/actions/runs/43818175933) :
777 tests Python (quatre réservés à Windows ignorés sous Linux), 15 contrôles de
diagnostic et 28 contrôles de lecture française par navigateur, plus les recettes
complètes existantes. Le contrôle natif Windows est réussi ; ce n’est pas une
mesure sur le PC de Marc. La suite locale avant le dernier ajout de contrôle
comptait 776 tests, puis les seize tests ciblés sont repassés (un Windows ignoré).
Les liens documentaires locaux et `git diff --check` sont vérifiés.

Les premiers candidats 0.21.0 n’ont pas été publiés séparément : une recette
WebKit a révélé un débordement de 15 pixels sans boîte DOM dépassante ; son contenu
est désormais borné horizontalement dans le lecteur français. Une temporisation
seule ne le corrigeait pas. Un autre essai CI a échoué sur la création de profil
de la recette UX ; aucun succès n’en a été déduit. Les huit jobs finaux du code
0.22.0 passent, y compris tous ces parcours, sans suppression d’assertion.

Recevoir ensuite le JSON de Marc : composants limitants encore inconnus. Windows réel de Marc,
iPhone réel, gros corpus, pic matériel continu et fidélité générale des réponses
ne sont pas validés par ces essais. Traduction et sous-titres restent ouverts.
