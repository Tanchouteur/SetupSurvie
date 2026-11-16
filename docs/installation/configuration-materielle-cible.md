# Configuration matérielle cible de SetupSurvie

**Référence évolutive — choix provisoires exprimés par Louis le 16 novembre
2026.** Cette fiche rassemble la configuration envisagée et les observations
qui permettent de l’affiner. Elle ne constitue pas encore une configuration
idéale validée, un minimum logiciel obligatoire ni une liste d’achats arrêtée.
Aucun essai matériel supplémentaire n’a été exécuté pour sa rédaction.

## Base retenue pour la cible

| Composant | Orientation de Louis | État de la décision |
| --- | --- | --- |
| Carte graphique | **NVIDIA avec 16 Go de mémoire vidéo (VRAM)**, probablement une **GeForce RTX 5060 Ti 16 Go** | Capacité cible retenue ; référence probable, à confirmer selon les essais et le coût |
| Mémoire du PC (RAM) | **Au moins 32 Go au départ**, puis **64 Go si les prix baissent suffisamment** | DDR4 ou DDR5 acceptées dans la réflexion ; plateforme et kit non choisis |
| Stockage principal | **SSD NVMe d’au moins 2 To, PCIe 4.0 au minimum** | Base souhaitée ; modèle et capacité finale à préciser selon le fonds réel |
| Processeur | **À déterminer après mesures** | Aucun modèle, nombre de cœurs ou budget arrêté ; priorité actuelle au stockage |

La RTX 5060 Ti existe en variantes 8 et 16 Go : la candidate ci-dessus est bien
la **16 Go** ([spécifications NVIDIA](https://www.nvidia.com/fr-fr/geforce/graphics-cards/50-series/rtx-5060-family/)).
Cette orientation ne désigne pas le meilleur GPU à prix égal et n’annonce aucun
gain chiffré dans SetupSurvie. Aucune baisse de prix de la RAM n’est acquise.

DDR4 et DDR5 restent deux options de plateforme ; elles ne sont pas
interchangeables dans les mêmes emplacements. Vérifier la compatibilité du
processeur, de la carte mère et du kit, ainsi que la possibilité de passer à
64 Go. Leur effet sur ce projet n’a pas été comparé à configuration égale.

## Matériel observé et cible future

Le laboratoire de Louis utilise un Ryzen 9, une RTX 2060 **6 Go** et **32 Go de
RAM**, sous Bazzite. Les rapports Windows de Marc identifient une RTX 5060 Ti
**8 Go** et environ **32 Go de RAM**. La cible 16 Go ne décrit donc pas un achat
ou un remplacement déjà réalisé. Les résultats du R7 avec une RTX 4080 ne
prédisent pas ceux d’une RTX 5060 Ti ayant la même capacité vidéo.

Louis indique aussi un **HDD** et un processeur de la famille **Core Ultra 5**
pour Marc ; le diagnostic ne les identifie pas lui-même et la référence exacte
du CPU reste à relever.

**Nouveau fait déclaré par Louis le 16 novembre 2026 :** Marc a commandé un
SSD NVMe PCIe 4.0 de **2 To**, à ajouter le lendemain. Le modèle exact, la pose,
le transfert et les performances après changement ne sont pas encore vérifiés.
Le HDD doit rester conservé jusqu’à validation de la copie et du redémarrage.
Un chantier de transfert automatique est confié à un autre agent ; le
[protocole de secours](../exploitation/disque-de-secours-hors-ligne.md) reste
la référence des exigences, sans déclaration de restauration déjà validée.

Les constats et leurs limites sont conservés dans les
[choix actuels](../decisions/choix-actuels.md), le
[bilan Linux du 11 novembre](../essais/bilan-pilote-2026-11-11.md) et les
[rapports Windows 0.22.0](../essais/2026-11-16-rapport-performances-marc-0220.md)
et [0.24.0](../essais/2026-11-16-rapport-performances-marc-0240.md), reçus le
16 novembre.
Les anciennes appellations « RTX 5060 » dans les bilans restent datées ; la
précision « Ti 8 Go » vient des rapports ultérieurs.

## Observations datées chez Marc

### Campagne 0.22.0 : premières recherches et chargement

Le rapport porte sur SetupSurvie **0.22.0**, GPT-OSS 20B, contexte **16 384** et
Ollama **0.40.16**. Il rapproche les données du disque `D:` d’environ **4 To**,
avec environ **2,56 To libres**, mais **n’identifie pas son type HDD ou SSD**.
Le nom du processeur n’est pas fourni ; dix processeurs logiques sont annoncés.

| Phase observée | Mesure du rapport | Interprétation limitée à cet essai |
| --- | --- | --- |
| Trois recherches sans IA, premier passage de la campagne | Fin en **62,3 à 72,4 s** ; premiers résultats en **0,10 à 0,18 s** ; recherches partielles | Distinguer attente du premier document et fin de recherche |
| Mêmes recherches répétées | Fin en **4,2 à 9,3 s**, recherches complètes | Réutilisation accrue des caches ; premier passage non contrôlé « à froid » |
| Premières recherches | Activité disque médiane **76 à 93 %**, lectures médianes **5 à 9 Mo/s** ; CPU total médian **11 à 14 %** | Forte piste de limitation par les accès disque, sans attribution exclusive démontrée |
| Première rédaction seule | **119,2 s**, dont **107,9 s de chargement** annoncées par Ollama | Le chargement domine cette demande ; ce compteur ne mesure pas uniquement le disque |
| Rédaction répétée, modèle chargé | **9,1 s**, environ **27 tokens/s** ; CPU médian proche de **55 %**, certains cœurs vers **92 %** | Le processeur participe aussi ; ce rapport ne compare pas deux CPU |
| Mémoire avec modèle chargé | Environ **5 Gio de RAM disponibles** au minimum et **7,2 Gio de VRAM utilisés sur 7,96 Gio** ; placement partiel du modèle | Aucun échec mémoire observé, mais marge et placement à surveiller |

Les compteurs couvrent tout le PC. Les autres activités, caches et composants
n’ont pas été isolés. Un faible débit en Mo/s peut accompagner beaucoup de
petites lectures dispersées ; il ne suffit pas à identifier le disque ni son
débit maximal. La priorité au SSD est cohérente avec ces observations ; son gain
réel reste à mesurer sur les mêmes recherches.

Deux autres réponses se sont arrêtées **avant l’appel au modèle**, sur un budget
de contexte logiciel dépassé. Ce défaut a été corrigé en 0.23.1 ; il ne prouve
pas un manque de RAM ou de puissance. Conserver cette distinction avant de
comparer les performances de versions différentes.

### Campagne 0.24.0 : coût CPU après réutilisation des caches

Le [bilan plus récent](../essais/2026-11-16-rapport-performances-marc-0240.md)
porte sur le même modèle et la même version Ollama, avec **32 768 tokens de
contexte demandé, transmis et chargé**. Le logiciel et le contexte ont changé
ensemble ; ce n’est pas une comparaison matérielle isolée avec 0.22.0.

| Phase observée | Mesure du rapport | Conséquence pour le dimensionnement |
| --- | --- | --- |
| Recherches avec appels Kiwix déjà en cache, dès le premier passage | Fin en **3,1 à 6,5 s** ; classement : environ **2,3 à 5,8 s de CPU** dans le fil de sélection | Le CPU représente une part importante du coût restant lorsque les accès Kiwix sont cachés |
| Première rédaction seule | **122,0 s**, dont **111,4 s de chargement** ; disque actif à **98 %** en médiane, environ **133 Mo/s** lus | Le stockage reste une piste forte pour le démarrage du modèle |
| Rédaction répétée et synthèses | CPU médian autour de **56 %**, certains cœurs vers **96 à 98 %** ; modèle partiellement en VRAM ; génération généralement **25 à 26 tokens/s** | Examiner CPU et placement après chargement ; le SSD ne promet pas le même gain sur la rédaction |
| Trois synthèses | Minimum de **7,06 à 7,33 Gio de RAM disponibles** ; occupation vidéo totale jusqu’à environ **7,54 Gio** ; aucun échec mémoire | Scénarios terminés en 32k chargé, sans essai remplissant toute cette fenêtre |

Les réponses documentaires naturelles durent **106,6 s puis 55,4 s**, avec
recherche, lecture, préparation, rédaction et parfois un second appel de liaison
des citations. Une partie de l’attente vient donc du parcours logiciel et du
calcul, même après chargement. Les compteurs d’archives n’expliquent pas à eux
seuls la couverture globale restée partielle.

La faible activité disque des recherches de cette campagne (médianes 3 à 7 %)
est observée sur peu d’échantillons. Les caches étaient déjà utilisés : ces
résultats ne démontrent ni un remplacement du disque ni une disparition de son
coût sur des archives non cachées. Les minima mémoire des deux campagnes ne
mesurent pas isolément le coût du passage de 16k à 32k.

## Rôle du processeur dans notre usage

Le processeur fait fonctionner les services qui répondent au portail et les
traitements locaux : recherche dans les index, extraction et préparation des textes,
classement des résultats, indexation et gestion des documents. Leur coût varie
avec les sources et les travaux en cours. Si une phase attend surtout le disque,
un CPU plus puissant peut rester en attente lui aussi.

Pour l’IA, l’importance du CPU dépend du **placement réel du modèle**. Quand le
modèle tient entièrement sur le GPU avec son contexte, le GPU prend en charge
l’essentiel du calcul du modèle ; le CPU reste nécessaire aux autres étapes.
Quand une partie tourne en RAM système, le CPU et les échanges mémoire
participent davantage au coût. Ollama distingue ces placements dans
[`ollama ps`](https://docs.ollama.com/faq#how-can-i-tell-if-my-model-was-loaded-onto-the-gpu).
C’est une explication technique de l’effet possible, pas une mesure de gain
entre les configurations envisagées.

Un CPU total peu occupé n’exclut pas un cœur très sollicité. Inversement, le CPU
actif pendant l’IA ne démontre pas qu’il limite seul le débit. Il faut regarder
la phase, les cœurs, la RAM, la VRAM et le placement ensemble. **Le choix du CPU
reste ouvert** : ces résultats ne justifient pas encore un modèle haut de gamme,
ni un nombre minimal de cœurs pour la cible.

## Dimensionner RAM, VRAM et stockage ensemble

Les **16 Go de VRAM** visent davantage de marge pour le modèle et son contexte.
Ils ne garantissent pas que tous les modèles proposés tiendront entièrement
sur le GPU. Le format des poids, le contexte, les demandes simultanées et les
autres usages vidéo comptent ; l’augmentation de mémoire liée aux requêtes
parallèles est décrite par [Ollama](https://docs.ollama.com/faq#how-does-ollama-handle-concurrent-requests).
Les profils conseillés restent ceux du projet jusqu’à comparaison réelle.

Les **32 Go de RAM** sont la base de départ souhaitée ; les campagnes actuelles
ne valident pas toutes les charges avec cette capacité. Les **64 Go** visent plus de
marge pour les services, le cache des fichiers et les traitements, sans remplacer
la VRAM. Leur effet sur les temps et la stabilité reste à mesurer. La fenêtre
native annoncée d’un modèle ne vaut pas contexte confortable sur la machine.

Les **2 To** sont une base de stockage, pas un plafond documentaire pour Marc ni
la preuve que tout son fonds y tiendra. Additionner système, services et disque
virtuel Docker éventuel, documents, cartes, vidéos, modèles, index, caches et
espace temporaire des mises à jour. Son fonds reste
[sans plafond logiciel](../bibliotheque/bibliotheque-complete-marc.md), dans les
limites physiques du stockage. Les règles du laboratoire (600 Go au total,
500 Go documentaires) restent propres au PC de Louis.

Le SSD doit accueillir les données réellement sollicitées : remplacer seulement
le disque système en laissant les archives, index ou modèles sur un disque lent
peut conserver les attentes correspondantes. Sous Windows, vérifier aussi le
placement du disque virtuel Docker selon le [guide d’installation](pilote-marc.md#avant-de-copier-le-kit).
Le débit séquentiel publicitaire et la mention PCIe 4.0 ne mesurent pas à eux seuls
la recherche dans nos archives. La copie de secours reste à prévoir sur un
[autre disque physique](../exploitation/disque-de-secours-hors-ligne.md).

## SSD commandé par Marc — déclaration du 16 novembre 2026

Marc a commandé un **SSD NVMe PCIe 4.0 de 2 To**, selon Louis dans la demande de transfert. Cela ne prouve pas son installation ni ses performances. Le [parcours de transfert](../exploitation/transfert-installation.md) mesure la capacité réelle, préserve le HDD et distingue le stockage Docker. Les essais Windows et la comparaison avant/après restent à réaliser.

## Affiner la fiche au fil des observations

1. Relever la référence exacte du CPU, les capacités RAM/VRAM, le modèle et le
   type du disque, ainsi que l’emplacement réel des archives, index, modèles et
   données Docker. Conserver version du logiciel, modèle/digest, contexte et
   activités concurrentes avec chaque mesure.
2. Utiliser le [diagnostic complet](../exploitation/diagnostic-complet-performances.md)
   pour séparer recherche sans IA, chargement, traitement de l’entrée et
   génération. Conserver le premier passage et les répétitions, sans appeler le
   premier « à froid » si l’état des caches n’est pas contrôlé.
3. Lors d’un changement matériel, comparer autant que possible à logiciel,
   fonds, modèle et contexte identiques. Vérifier aussi que les recherches
   terminent avec une couverture comparable. Mesurer après le changement de
   stockage avant d’attribuer le coût restant au CPU.
4. Comparer les contextes avec l’[essai mémoire volontaire](../utilisation/mesurer-assistant-et-memoire.md#essai-mémoire-volontaire-sur-le-pc-serveur).
   Consigner chargement, premier texte, débit, RAM/VRAM et placement, sans supposer
   que toute une fenêtre 32k tient confortablement parce qu’un contexte chargé
   de cette taille a déjà été observé avec une entrée plus courte.
5. Ajouter ici un lien vers chaque nouveau bilan daté, puis réviser les décisions
   si les observations le justifient. Conserver les résultats défavorables et
   les anciennes conditions d’essai.

Cette liste décrit les prochains relevés ; ils n’ont pas été exécutés pour cette
fiche. Respecter la pause IA et les usages habituels des PC ; aucune inférence
ou préparation lourde dans le runner CPU. Version logicielle inchangée : cette
livraison porte uniquement sur la documentation.
