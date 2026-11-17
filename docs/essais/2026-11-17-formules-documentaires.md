# Formules conservées dans les sources et traductions

**Bilan daté — 17 novembre 2026. Livraison visée 0.37.3, correction compatible.**
Suite ciblée de la [recette Bazzite précédente](2026-11-17-assistant-bibliotheque-bazzite.md).
L’objectif reste recherche/assistant, puis traduction et sous-titres. Aucun nouvel
essai d’installation ou de transfert n’est entrepris.

## Défaut et correction

Le lecteur ignorait les balises MathML sans alternative texte. La recette de
préparation de sources reproduisait ce défaut ; l’index complémentaire, lui,
aplatissait les fractions. L’IA pouvait ainsi lire un texte sans ses équations.
Le contrôle des nombres ne détectait pas une inversion de fraction conservant
les mêmes valeurs.

Un lecteur commun conserve l’alternative de l’auteur ou un sous-ensemble borné
de MathML de présentation : fractions, groupes, indices, puissances, racines,
scripts et matrices simples. Les formes inconnues deviennent un message explicite,
sans calcul, OCR, requête externe ou équation inventée. Le comportement est fondé
sur la [structure MathML de présentation du W3C](https://www.w3.org/TR/MathML3/chapter3.html),
sans revendiquer la prise en charge intégrale de cette norme.

Les blocs restent entiers dans les instantanés longs. Les extraits de recherche
réduisent leur fenêtre si une formule serait coupée, en gardant leurs budgets
et offsets exacts. Pour traduire, le logiciel remplace temporairement les blocs
par des repères puis réinsère les originaux uniquement si la suite de repères
revient intacte. La version 4 du contrôle compare aussi les blocs finaux ; les
échecs restent privés, visibles et non publiés. Les contrôles numériques restent
actifs. Le sens des phrases autour des formules n’est pas certifié.

Les compléments d’index passent au format de construction 2 lors d’une reprise
explicite ; leurs anciennes publications restent lisibles jusque-là et pendant
la construction. Les index natifs Kiwix ne sont pas reconstruits. Aucun ancien
instantané, texte utilisateur ou document publié n’est réécrit. Pour retrouver
une équation déjà perdue, repartir de l’article original.

## Essais réels Bazzite

RTX 2060 6 Go, 32 Go RAM ; services existants et modèle Gemma4 E4B, contexte
16 384. API et données d’essai isolées sur le SSD du laboratoire. Le candidat
portait 0.37.2 avant l’arrivée sur main du correctif d’interface portant déjà ce
numéro ; l’intégration finale prend 0.37.3 et préserve les deux travaux.

Article réellement présent dans `wikibooks_en_all_maxi_2026-10` :
`Amateur_Radio_Manual/Ohm%27s_Law_and_Resistors`. HTML original de **34 752 octets**,
SHA-256 `8f145eb6691bee7e944f566bcc38983e869a8f5db61a388161d3519c367095b1`.
Le nouveau lecteur extrait **8 698 caractères, 23 formules et zéro formule
signalée illisible**. Les fichiers documentaires existants restent inchangés.

Premier essai : demander au modèle de recopier lui-même les formules termine
3 passages sur 5 puis bloque, car `×` devient `\times`. La proposition rejetée
reste conservée. Le contrôle n’est pas assoupli : les formules sont ensuite
protégées par le logiciel. Nouveau travail complet : **5/5 passages terminés en
106 412 ms**, cinq rapports version 4 sans anomalie détectée. Les **23 blocs sont
identiques octet pour octet** après traduction et présents dans le document
français publié. L’original est inchangé. Il s’agit d’un chapitre, pas d’un livre
complet ou d’une validation humaine de toute la terminologie.

Deux demandes rejouées après la dernière correction des extraits :

- Moteur de 1 Ω sous 12 V, fil prévu pour 10 A : **19 467 ms**, une source lue
  et citée. La trace confirme l’outil `calculate`, expression `12 / 1`, résultat
  exact 12. La réponse conclut 12 A et explique que le fil de l’exemple ne convient
  pas. Cela ne dimensionne pas une installation réelle.
- Résistances en série : **17 095 ms**, une source lue et citée, courants égaux
  et tensions additionnées. La formule est effectivement reçue. « Head to tail »
  reste rendu par « tête-bêche », expression ambiguë pour un montage : ce point
  de vocabulaire technique reste ouvert. L’extrait anglais ajouté par la revue
  des procédures conserve les notations, mais n’équivaut pas à une explication
  entièrement française ni à une validation du câblage.

## Tests automatisés et traçabilité

Première suite : **996 tests, 6 ignorés, 202,869 s**. Après protection des blocs :
**1 000 tests, 6 ignorés, 204,740 s**, avant le dernier scénario de fenêtre de
recherche. Derniers contrôles ciblés : **16 tests d’extraction/formules en 0,502 s**,
**22 tests de lecture/recherche en 0,252 s**, **61 tests de traduction en 29,426 s**.
Les fixtures sont synthétiques et minuscules ; aucun corpus ou modèle téléchargé
dans le runner. La première CI du code réuni `f7ca588` passe sept jobs, dont Windows et
**1 001 tests Linux (6 ignorés, 74,301 s)**, puis échoue dans l’audit clavier
WebKit : l’aide reçoit le focus avant le rappel `requestAnimationFrame` du
routeur après Suivant. La recette attend désormais ce travail de restauration
avant d’envoyer Entrée, sans délai fixe, retrait d’assertion ou changement du
produit. Le rejeu ciblé Chromium/WebKit passe ses 16 contrôles par moteur ; la
[CI du code `3413f3d`](https://github.com/Tanchouteur/SetupSurvie/actions/runs/44052550891)
réussit ses huit jobs, y compris Windows et les parcours Chromium/WebKit/Firefox.
Linux : **1 001 tests, 6 ignorés, 80,739 s**. La vérification MCP Chromium confirme
également ouverture par Entrée puis fermeture par Échap avec focus conservé.
L’essai Firefox local via l’adresse inter-conteneurs n’atteint pas le profil de
fixture ; il n’est pas présenté comme réussi. Son contrôle CI reste distinct.
La relecture ajoute ensuite une garde au seuil d’aperçu de 100 000 caractères :
une formule traversant ce seuil est omise, et la lecture reste partielle. Une
ancienne copie tronquée avec bloc non fermé n’alimente plus un extrait de calcul.
Les tests ciblés couvrent l’API de lecture et les fenêtres : **18 contrôles de
formules en 0,416 s**, **22 de recherche en 0,266 s**. La suite CI finale est
relancée sur ce code : **1 003 tests Linux, 6 ignorés, 80,102 s**, aucun échec.
Windows termine sans échec. Le job navigateur passe Chromium, WebKit et l’audit
clavier Firefox, puis dépasse son délai au lancement d’une traduction dans le
lecteur Firefox. Le rapport initial ne conserve pas le message du panneau : la
cause exacte de ce passage CI ne peut pas être certifiée rétroactivement.

Le diagnostic local rejoue les six recettes Firefox précédentes et le lecteur :
15 contrôles du lecteur passent. Une collision est ensuite provoquée volontairement
avec une traduction déjà active sur le même profil : l’API la refuse correctement,
le panneau dit « Une traduction est déjà en cours pour votre compte », et l’ancienne
recette attend à tort un nouveau travail pendant 30 s. La recette crée désormais
son propre profil et garde un diagnostic borné du panneau en cas d’échec, sans
retirer la protection du produit ni arrêter un travail hérité. **16 contrôles
Firefox passent**, y compris avec une traduction préalable dans un autre profil ;
le travail initial reste conservé et est mis en pause seulement pour nettoyer
la fixture. Ces comptes et documents sont entièrement fictifs.

La CI finale de `ef3ad47` est relancée. Son résultat et le reçu du paquet restent
à vérifier avant intégration.

Les rapports complets, échecs initiaux, traces d’outils et recettes restent privés,
hors Git. Archive locale `setupsurvie-formules-0372-preuves-privees.tgz`, **39 136
octets**, SHA-256 `ddf4f1d46577a74a3ca3800024de8c8b21a109670c1bbadd2af5da427bd99e72`.
Les empreintes des six modules identifient le candidat effectivement observé.
La garde ajoutée ensuite aux limites d’aperçu est contrôlée par les nouveaux tests
synthétiques et la CI ; aucune nouvelle inférence Bazzite n’est revendiquée pour
ce dernier ajout.
Le chapitre réel n’est pas copié dans les fixtures ou le paquet logiciel.

## Nettoyage et limites

Conteneur d’API et dossier d’essai supprimés, huit conteneurs historiques arrêtés,
Docker utilisateur toujours inactif, laboratoire démonté et boucle détachée.
L’image de 590 milliards d’octets est conservée, le runtime historique reste
0.1.34 et le clone de Louis reste propre. Aucune application utilisateur fermée,
installation active remplacée, pause d’inférence levée ou donnée personnelle copiée.

Ces essais Linux ne prouvent pas les refus de premier appel sous Windows, le
fonds entier de Marc, tous les schémas, la cohérence d’un livre réel de 500 pages
ou les sous-titres de chaque vidéo réelle. Les validations vidéo déjà acquises
restent celles des bilans précédents ; aucune nouvelle campagne vidéo n’est
revendiquée ici. L’objectif global reste ouvert sur ces vérifications ciblées.
