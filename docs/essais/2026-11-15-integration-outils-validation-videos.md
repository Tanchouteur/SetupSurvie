# Intégration des outils de diagnostic et d’inventaire vidéo

**Bilan de livraison — 0.14.0, 15 novembre 2026.** Les deux agents lancés par
Louis ont terminé leurs fichiers réservés. Leurs commits sont fusionnés sans
réécriture dans une branche d’intégration issue de main **0.13.1** (`b0567db`).

- Diagnostic Kiwix : `233ecdb`, huit tests initiaux ;
  [bilan de préparation](2026-11-15-diagnostic-performances-kiwix.md).
- Inventaire vidéo : `cbec193`, vingt tests initiaux ;
  [bilan de préparation](2026-11-15-inventaire-videos.md).

## Comportement livré

`scripts/diagnose_kiwix.py` mesure explicitement une archive précise, l’accès Kiwix,
sa recherche native, le flux du portail et la répétition, en série, sans IA.
Le rapport sépare réception des premiers documents, fin, couverture, erreurs et
réutilisation. Les ressources internes Kiwix inconnues le restent ; aucune cause
matérielle n’est déduite de la seule latence. Le script n’efface pas les caches
pour prétendre repartir à froid. Le [guide actuel](../exploitation/diagnostic-performances-kiwix.md)
donne les commandes et les budgets, l’arrêt et les codes de sortie.

`scripts/library_videos.py` examine les vidéos locales présumées terminées,
métadonnées `.info.json` et pistes associées SRT/WebVTT. Les originaux restent
intacts et les rapports vont dans un nouveau dossier extérieur. Une piste
française déclarée n’est pas une traduction ou une synchronisation validée.
Les fichiers incomplets, anomalies et parties non examinées restent visibles.
Le [guide actuel](../utilisation/inventaire-videos.md) précise les chemins à adapter
sur Windows/Linux et la portée limitée aux fichiers et annexes locales.

L’inventaire ne prépare pas encore un index vidéo, ne récupère pas de piste
distante, ne transcrit pas l’audio et ne traduit pas. Les vidéos des ZIM et pistes
intégrées aux conteneurs restent à examiner séparément. Cette première étape
alimente la [suite vidéo](../decisions/videos-locales-et-recherche.md) sans la
déclarer terminée. Aucun bouton ou réglage supplémentaire n’est ajouté au portail.

## Ajustements d’intégration

La version **0.14.0** correspond à l’ajout de deux outils compatibles utilisables,
d’où le niveau mineur. Les branches des agents avaient conservé la version sur
instruction de coordination ; la livraison commune met API et manifeste à jour.
Le moteur 0.13.1 est conservé : seule sa constante de version change. Les images,
schéma privé 1, réglages, index et fichiers Web restent inchangés.

Le diagnostic exporte désormais une liste explicite de champs utiles, plutôt
que l’intégralité des objets JSON fournis par le serveur. Les manifestes et
informations du lecteur, champs inconnus et corps bruts ne sont pas copiés.
Les traces, formulations, délais, compteurs de titres/reformulations et erreurs
catégorielles restent disponibles, avec limites. Un test injecte des champs
sentinelles inconnus, y compris dans le manifeste et les traces, et vérifie
qu’ils sont absents de l’export sans perdre les mesures documentées.

Les guides courants, index documentaires, décisions et journal sont actualisés.
Les bilans initiaux des agents restent historiques, avec un renvoi vers cette
intégration ; leurs validations ne sont pas réécrites comme des essais Windows.
Les deux tests d’outils sont ajoutés à la recette Windows de CI pour les prochains
passages possibles ; leur ajout ne signifie pas qu’ils ont déjà tourné sur Windows.

## Vérifications

Dans l’environnement isolé du runner Linux, **561 tests Python réussis, trois
ignorés**, comprenant les vingt tests vidéo et neuf tests de diagnostic après
filtrage. Les tests initiaux des branches ont aussi été relus et rejoués avant
fusion. Les commandes d’aide, compilation Python et `git diff --check` passent.
Les tests du nouveau filtrage sont rejoués après ajout des compteurs conservés.

Un essai HTTP avec l’API 0.14.0 et deux services de fixtures vérifie ensuite le
script de diagnostic contre le vrai contrat du portail : deux flux SSE, premiers
documents avant fin, sept étapes terminées et absence de texte documentaire dans
l’export. Les réponses natives de cet essai sont simulées ; aucun fonds de Marc
ni modèle réel n’est utilisé. Les tests Kiwix réels de la correction du moteur
restent ceux de la [0.13.1](2026-11-15-classement-titres-et-intention.md).

CI complète et Python Windows réel des deux outils non exécutés : GitHub a refusé
la dernière relance de la livraison précédente avant exécution, pour restriction
du compte. La [validation 0.13.1](2026-11-15-classement-titres-et-intention.md#validation-finale-et-limites-de-ci)
distingue aussi ses campagnes navigateur. Aucun nouveau résultat Windows, Safari
ou vidéo réelle n’est revendiqué par cette intégration sans modification Web.

Le code d’intégration **`ba33e8a`** est poussé. Le nouveau
[passage CI](https://github.com/Tanchouteur/SetupSurvie/actions/runs/43689514723)
termine sans lancer aucun job : les huit jobs n’ont aucune étape exécutée et
l’annotation GitHub confirme la restriction du compte. Il ne s’agit pas de huit
tests exécutés en échec et aucun résultat de cette campagne n’est revendiqué.

Le paquet local est construit puis déballé avec le lecteur de mise à jour :
**741 fichiers acceptés**, version **0.14.0**, schéma **1**,
**6 632 726 octets** compressés. Chaque fichier est comparé au commit `ba33e8a`.
Les deux scripts et leurs guides sont présents ; leurs commandes `--help` passent
également depuis la copie déballée. Aucun modèle, ZIM, média ou cache SQLite.
Empreinte du paquet audité :
`a95f2cb46091f9153ac09e9e1701a879078d5fa3b49fafa6a4af3bd5366f1e01`.
Le complément de bilan final est documentaire seulement ; le code reste identique.
Aucun déploiement sur les PC de Louis ou Marc n’est effectué.

## Prochaine validation chez Marc

Mettre à jour normalement, vérifier la version, puis refaire le contrôle de
recherche sans IA et ouvrir les résultats utiles. Une reconstruction complète
des index n’est pas requise pour ces seules corrections et outils. Le diagnostic
supplémentaire sert à cibler une archive si les délais restent problématiques.
L’inventaire vidéo doit ensuite être exécuté sur le vrai `library/video/` ; ses
rapports permettent de choisir acquisition, transcription ou traduction pour
chaque média. La qualité réelle et les avis humains restent indispensables.
