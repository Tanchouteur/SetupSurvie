# Rapport de performances de Marc et budget documentaire

**Suite :** le [rapport réel 0.24.0](2026-11-16-rapport-performances-marc-0240.md)
observe les trois réponses terminées et 32k chargé. Code et réglage ayant changé
ensemble, il ne mesure pas l'effet isolé de chacun. Le bilan ci-dessous conserve
les résultats et limites de la campagne 0.22.0.

**Analyse du rapport reçu le 16 novembre 2026 — correctif 0.23.1.** Rapport
0.22.0, protocole 1, onze étapes, 411 045 ms, 136 échantillons dont 135 avec
ressources du PC. Les données brutes restent privées et hors Git.

## Observations sur le PC Windows de Marc

Le serveur annonce environ 32 Go de RAM, dix processeurs logiques et une RTX
5060 Ti de 8 Go. Les compteurs rapprochent le fonds du disque `0 D:` d’environ
4 To, avec environ 2,56 To libres. Le rapport ne donne pas le type HDD/SSD.

| Recherche sans IA | Premier passage de la campagne | Répétition |
| --- | ---: | ---: |
| Faire du feu | 66,4 s | 4,3 s |
| Panneau solaire / batterie | 62,3 s | 9,3 s |
| Révolution française | 72,4 s | 4,2 s |

Les premiers résultats arrivent en 0,10–0,18 s ; ces durées sont celles de fin.
Les trois premières recherches sont partielles ; les répétitions sont complètes.
Le cache est davantage réutilisé. Sur les premières recherches, l’activité médiane
du disque atteint environ 76–93 %, avec des pointes proches de 100 %, alors que
le CPU total médian reste autour de 11–14 %. Les débits lus médians sont seulement
de 5–9 Mo/s, compatibles avec un travail de nombreuses lectures dispersées.
Le disque constitue donc une piste forte pour ces recherches initiales, sans
preuve que chaque durée lui soit exclusivement imputable. Les compteurs couvrent
tout le PC ; l’état initial des caches et les autres activités ne sont pas contrôlés.

GPT‑OSS 20B, contexte **16 384**, Ollama 0.40.16 :

- Première rédaction seule : **119,2 s**, dont **107,9 s de chargement** annoncées
  par le moteur. Pendant cette étape, le disque lit environ 155 Mo/s en médiane.
- Répétition avec modèle chargé : **9,1 s**, dont environ 8,7 s de génération.
  Les deux rédactions produisent environ **27 tokens/s**. Le CPU médian pendant
  la répétition est autour de 55 %, certains cœurs atteignent environ 92 %.
- Une fois le modèle chargé, il reste environ **5 Gio de RAM disponibles**
  (minimum observé proche de 4,96 Gio), avec environ **7,2 Gio de VRAM utilisés
  sur 7,96 Gio**. Aucun échec mémoire n’est observé. L’allocation du modèle annoncée
  par le moteur dépasse sa seule part en VRAM : le placement est partiel.

Augmenter à **32k mérite un essai**. La capacité native annoncée est 131 072,
mais elle ne mesure pas la mémoire nécessaire ni le débit sur ce PC. Le rapport
ne compare pas 16k et 32k ; l’essai mémoire dédié doit mesurer cette différence.
La RAM disponible avant chargement (environ 13–17 Gio durant les recherches)
ne constitue pas la marge restante après chargement.

## Défaut logiciel identifié

Les deux réponses documentaires naturelles durent **6,5 s et 4,7 s**. Chacune
trouve **24 candidats**, prépare **10 sources**, puis s’arrête sur `context_budget`
**avant tout appel au modèle**. Le budget estime 10 688 tokens d’entrée, plus
4 096 de réponse et 2 048 de réserve : **16 832**, soit **448 au-dessus** des 16 384.
Ces échecs ne prouvent donc ni absence de documents ni insuffisance physique de RAM.

La réponse avec trois documents choisis termine en **45,3 s** : environ 0,1 s de
lecture, 4,7 s de préparation, 28,6 s de rédaction et 10,8 s de liaison des sources.
Elle illustre un autre profil de coût : deux appels au modèle, et non une recherche
restée bloquée pendant toute la réponse.

## Correction générale 0.23.1

Le lecteur calculait la place des extraits avec une réserve forfaitaire, sans
compter tous les identifiants de la demande d’outil, ni le surcoût du JSON d’outil
encodé comme une chaîne dans la conversation. Les archives aux noms longs et
les métadonnées détaillées dépassaient ensuite le budget global.

Le dossier réserve désormais cet encadrement réel et mesure son volume encodé.
Le nombre de passages s’adapte avant admission : les premières sources pertinentes
gardent un passage utile au lieu de céder leur place aux dernières lorsque les
métadonnées sont longues. Les identités, éditions, texte et positions restent
ceux des sources. Seuls les passages effectivement retenus sont déclarés lus.
Les omissions restent explicites ; question, contexte configuré et réserve de
réponse sont conservés. Le JSON est compacté sans changer sa signification.

Le diagnostic conserve contexte demandé/transmis/chargé, limite native, tokens
réels d’entrée/sortie, marge ou dépassement estimés et volume du dossier. Il
signale la réduction par la limite native aussi pour la rédaction sans documents.
Les nouveaux champs numériques n’ajoutent aucun contenu documentaire à l’export.

Niveau correctif `0.23.1` : réparation compatible du budget et de ses mesures ;
aucune migration de données, modification d’image tierce ou hausse automatique
du contexte sur les PC.

## Vérifications et limites

Le test de régression reproduit douze identifiants longs, titres avec guillemets
et barres obliques inverses, éditions et textes français distincts. Le vrai moteur
d’orchestration, avec HTTP simulé, doit transmettre un dossier qui tient en 16k,
conserver la question et les sources prioritaires, garder les positions exactes,
et terminer avec des citations réellement lues. La confidentialité de l’export,
la marge positive/négative et une limite native plus petite sont aussi vérifiées.

Essais réels R7 : Gemma `gemma4:e4b`, Ollama 0.40.14, 32 couches GPU, six threads,
4 096 tokens de sortie et réserve vidéo 1 536 Mio. Aucun modèle téléchargé ni
processus tiers arrêté. Recherche/textes fictifs injectés, mais orchestration,
budget et inférence réels ; ce test n’exerce pas les archives Kiwix.

Le premier essai atteint bien le modèle et tient en 16k, puis échoue sur les
citations : quatre dernières notices avaient été retenues, avec des numéros que
le modèle ne reliait pas correctement. Ce résultat défavorable est conservé dans
`report-gemma4-context-fit-16k.json`. La répartition a ensuite été corrigée pour
tenir compte des longues métadonnées avant de créer les places, et préserver les
premiers candidats.

| Rejeu final | Sources lues / citées | Entrée réelle du moteur | Contexte chargé annoncé | Durée totale |
| --- | ---: | ---: | ---: | ---: |
| 16k | 3 / 3 | 4 367 tokens | 16 384 | 11 177 ms |
| 32k | 12 / 12 | 12 147 tokens | 32 768 | 21 054 ms |

Les valeurs 17–19 puis 17–28 sont reliées aux bonnes notices. À 16k, le modèle
ouvre par un refus de comparaison technique des données fictives, puis les
résume correctement ; cela ne valide pas la qualité de guidage sur de vrais
documents. À 32k, il produit le tableau des douze valeurs. Les volumes encodés
sont respectivement 4 487 / 4 892 octets et 36 426 / 37 660 octets disponibles.
L’estimation préalable reste prudente : elle n’est pas le compte de tokens réel.

Rapports privés `report-gemma4-context-fit-16k-v2.json` et
`report-gemma4-context-fit-32k.json`, empreinte Python commune :
`084689df8091a52ec5ad26d9c92519c30d50e8d4368bff4d4fbdc2007de7add6`.
Ces essais vérifient l’allocation annoncée et l’adaptation du dossier, pas une
entrée remplissant réellement 32k ni son coût mémoire maximal. Ils n’estiment
pas les performances de GPT‑OSS ou du PC de Marc. L’essai mémoire dédié garde
ce rôle. Aucun contexte client modifié, aucun déploiement client réalisé.

Suite locale finale : **789 tests Python réussis, quatre réservés à Windows
ignorés**, en 136,9 s. Code fonctionnel `7801964`,
[huit jobs CI réussis](https://github.com/Tanchouteur/SetupSurvie/actions/runs/43829077963) :
789 tests Python en 54,8 s sous Linux, contrôles Windows, index isolés, Kiwix natif,
routage synthétique et recettes Chromium/WebKit. Aucun modèle réel ne tourne en CI.
Le paquet est comparé au commit avec les filtres Git de fins de ligne Windows ;
le reçu final ci-dessous identifie sa version documentaire exacte.

Paquet `setupsurvie-0231-validated.zip`, commit documentaire `25aae6c`,
**837 fichiers**, 6 973 142 octets compressés et 15 656 776 octets décompressés ;
tous les octets comparés au commit filtré et au manifeste :
`1a1815a30bbf9536dad4393f500e975d6b3af81173c069361fe4360a15661b8d`.
Le présent reçu est ajouté après construction. Données privées, modèles, corpus
et rapports réels ne sont pas inclus. Aucun déploiement sur les PC clients.
Le rapport de Marc précède ce correctif : il ne le valide pas. La fidélité sur
tout le fonds et le coût de 32k sous Windows restent à mesurer.

Références actuelles : [diagnostic complet](../exploitation/diagnostic-complet-performances.md),
[essai mémoire](../utilisation/mesurer-assistant-et-memoire.md),
[recette de modèle réel](assistant-modele-reel.md).
