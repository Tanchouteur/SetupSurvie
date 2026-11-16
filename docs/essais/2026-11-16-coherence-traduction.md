# Vocabulaire et cohérence des traductions longues

**Bilan daté — candidat 0.32.0, 16 novembre 2026.** Nouvelle fonction compatible,
incrément mineur après 0.31.0. Les modèles, images et empreintes des dépendances
restent inchangés. Guide actuel : [documents et traduction](../utilisation/documents-et-traduction.md#garder-les-mêmes-mots-dans-un-document--0320).

## Changements et limites

Une liste facultative de mots original/français appartient à chaque profil.
Chaque traduction en prend une copie immuable au lancement. Une reprise ne
change donc pas le vocabulaire à cause d’un réglage modifié plus tard. Les anciennes
traductions restent sur leur fonctionnement, sans emprunter de nouveaux mots.
Le panneau distingue les mots du travail et ceux des prochains travaux ; une
saisie non enregistrée doit être enregistrée avant de lancer une traduction.

Le modèle reçoit seulement les termes présents dans le passage et, pour les
nouveaux travaux, la fin du passage précédent effectivement terminé (600 caractères
source/français chacun au plus). Ce repère est distinct du texte à traduire,
présenté comme donnée non vérifiée et retiré s’il ne tient pas dans le budget.
Aucun mot n’est remplacé automatiquement après génération. Une préférence non
retrouvée produit un avertissement, y compris si une flexion correcte peut
l’expliquer. Les contrôles de nombres/unités restent bloquants. Le modèle peut
mal interpréter des données malgré les consignes ; les contrôles ne prouvent
pas le sens, et aucune relecture humaine générale n’est revendiquée.

La base ajoute `translation_guidance` sans supprimer d’états. Les copies suivent
le travail et sa suppression ; la liste du profil reste réutilisable. Les sorties
refusées ne comptent pas comme traduites. Les avertissements suivent export et
publication ; la liste complète reste dans le travail privé et son export.

## Essais automatisés et navigateur

- Tests sans modèle : préférences par profil, validation/limites, copie au départ,
  pause/reprise après réinitialisation, repère du seul précédent terminé, ancienne
  traduction, absence de terme, refus des nombres ajoutés, propagation des
  avertissements, suppression et conservation des données publiées.
- Test transport : séparation JSON du passage, du vocabulaire et du repère,
  absence de substitution et retrait du repère si le budget est trop petit.
- Test API : lecture/écriture limitée au profil, paramètres validés et aucun
  lancement de travail à l’enregistrement.
- Parcours Playwright MCP : 15 contrôles, véritable portail/API/SQLite et modèle
  simulé ; vocabulaire enregistré, saisie non enregistrée explicite, copie figée,
  reprise, rechargement, liste vide et largeur 1366/390/320 pixels.
- Chromium et WebKit : vocabulaire 15 + commandes 16 + lecture progressive 26,
  soit **57 contrôles par navigateur**, avec modèle simulé. WebKit ne remplace
  pas Safari sur le téléphone réel de Marc.

## Notice réelle sur R7

La notice de gamme UV-5R/GT-3 préexistante est utilisée sans téléchargement :
17 968 170 octets, 60 pages, SHA-256
`bd43cd9b58c311fcf0e0f02eeb4a1e9bbd0fdd1a6deea4150ba9df9c5932e485`.
Plage d’essai : pages PDF **4 à 8** (chaque page PDF rassemble deux pages imprimées),
**9 passages**, vrai Gemma4 E4B, contexte 16k, 24 couches GPU, six threads,
réflexion désactivée. Les réserves sont contrôlées, aucun autre modèle n’est
évincé ni profil GPU changé ; pas de déploiement chez Marc. Le vocabulaire d’essai
comprend battery/batterie, charger/chargeur, channel/canal. Le contrôle sert à
évaluer une traduction, pas à certifier les consignes du fabricant.

Premier résultat : **3/9** conservés, arrêt au quatrième après **61,700 s**.
La proposition rétablissait l’espace de `Chapter4` en `Chapitre 4` ; le contrôle
ignorait le chiffre attaché au libellé source et signalait à tort un ajout.
La version **3** reconnaît ce chiffre des deux côtés. Les tests gardent le refus
de `Chapter4` vers `Chapitre 5` ou `X7` vers `X8` ; les seuils ne sont pas abaissés.
Rapport négatif privé conservé : `report-translation-0320.json`.

Rejeu après cette correction : **9/9**, **128 686 ms** (2 min 09 s), pause après
trois passages, réinitialisation et reprise explicite. Les passages terminés
restent identiques et les neuf parties correspondent au lecteur publié.
**5 passages sans anomalie détectée, 4 avertissements de trous d’extraction**
(touches dessinées manquantes dans le texte). Les douze applications de termes
ont retrouvé leur forme demandée ; les huit passages suivants ont utilisé le
repère précédent. Ces compteurs ne prouvent pas une fidélité générale.
Rapport privé : `report-translation-0320-v2.json`.

La relecture ciblée des passages 4 et 9 conserve leur ordre, la distinction
confirmation/annulation et les valeurs. Elle repère aussi une limite utile : le
nom de touche CALL était rendu par APPEL dans le quatrième passage. La consigne
est renforcée pour conserver les inscriptions exactes. Un détecteur limité de
noms devant/après « key/button » ajoute un avertissement si l’inscription n’est
plus repérée ; il ne connaît pas toutes les interfaces et ne valide pas une
procédure. Les touches absentes du texte ne sont toujours pas inventées.
Le rejeu du dernier code est conservé séparément ci-dessous.

Les rapports source/traduction complets restent privés sur le R7. Aucun texte de
la notice n’est ajouté à Git par ces essais. Ce chapitre ne certifie pas un livre
réel de 500 pages, sa cohérence complète ni les performances Windows de Marc.

## Validation locale du candidat

La suite locale passe **903 tests en 183,578 s**, avec **16 ignorés** (dépendances
libzim optionnelles et procédures Windows absentes du runner). Après les dernières
consignes et alertes de touches, **6 tests de vocabulaire/budget** et **13 de
contrôles de traduction** passent. Les tests simulés ne prouvent pas le sens du
modèle réel ; les recettes R7 ci-dessus restent la preuve distincte.
Les liens locaux des documents modifiés et `git diff --check` sont vérifiés ;
aucun rapport utilisateur, modèle ou corpus volumineux n’est ajouté à Git.

### Rejeu du dernier comportement

Avec la consigne sur les inscriptions, les mêmes cinq pages terminent encore :
**9/9 en 129 602 ms** (2 min 10 s), cinq contrôles sans anomalie repérée et
quatre avertissements de trous de touches, aucun passage bloqué. Les passages
conservés lors de la pause restent identiques après reprise ; les neuf parties
correspondent au lecteur. Le quatrième passage garde désormais **CALL** dans la
traduction. Rapport privé `report-translation-0320-v3.json` et empreintes du code
et de la recette incluses. Cette vérification ciblée ne certifie pas toute la
notice ou les autres ouvrages.

Les six vérifications de qualité navigateur passent également dans Chromium et
WebKit : nombres ajoutés refusés, proposition rejetée visible, comparaison source,
avertissement conservé dans l’export et la publication, saisie accessible sur
mobile et touches manquantes signalées avec le contrôle version 3. Elles utilisent
un modèle simulé ; la génération réelle est celle des rapports R7 séparés.

## Contrôle connexe du changement de modèle et des sources

Sur le même code candidat, la recette `real_assistant_check.py` précharge le
Llama 3.1 8B déjà installé, puis pose une seule demande naturelle à Gemma4 E4B
avec cinq PDF fictifs explicitement sélectionnés. Les faits utiles sont en page
6, pas dans les introductions. Le traitement lit les cinq sources sans omission,
retrouve les cinq valeurs attendues (17, 23, 31, 43, 59) et les référence. La
réponse précise que les données fictives ne suffisent pas à établir les principes
techniques des capteurs ; elle n’invente pas ce contenu absent.

La première demande termine en **14 461 ms**, première sortie à **5 723 ms**,
préparation du modèle cible **4 105 ms**, un appel de rédaction et aucune reprise
du modèle. Contexte demandé/observé 16k, 24 couches GPU et six threads dans la
recette. Rapport privé `report-assistant-0320-switch.json`. Les deux modèles
coexistent encore dans l’observation finale : ce résultat prouve une demande
après changement de cible dans ces conditions, pas l’éviction sous saturation
ni la disparition de tous les refus sur le Windows de Marc. Aucun autre modèle
n’est déchargé pour l’essai ; expiration naturelle après quinze secondes.
