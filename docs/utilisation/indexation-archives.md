# Rendre les archives recherchables

**Guide actuel — 0.11.1, 14 novembre 2026.** L’index complémentaire extrait le texte
des archives ZIM sans index natif utilisable par Kiwix. Il ne modifie pas les originaux,
ne charge aucun modèle IA et ne transcrit pas les vidéos.

## Après une installation ou un téléchargement

Une archive téléchargée et vérifiée est inscrite dans une file persistante.
L’installation depuis un kit ajoute aussi les archives dont la copie est vérifiée.
Une fois le téléchargement terminé et les verrous de publication libérés, le
contrôleur démarre la préparation si l’outil est prêt et le créneau autorisé.
Les archives inchangées déjà traitées sont ignorées. Un téléchargement partiel
n’est jamais indexé comme document complet.

L’outil est préparé pendant une nouvelle installation en ligne. Une installation
existante peut encore demander **Préparer l’outil · Internet requis** une première
fois, dans **Famille → Mon appareil → Paramètres → Bibliothèque et préparations → Préparer la recherche dans les archives**.
La simple mise à jour du logiciel ne lance pas rétroactivement une extraction
de tout le fonds. **Créer ou reprendre les index** permet cet examen initial.
Une fois préparé, le traitement est entièrement local et fonctionne sans Internet.

Depuis 0.11.1, l’examen distingue **index natif présent** et **langues compatibles
avec Kiwix**. Plusieurs langues dans une même archive peuvent faire refuser sa
recherche native, même seule. Un index local complémentaire est alors préparé.
Le seul mot `mul` dans un nom ne suffit pas : une métadonnée contenant uniquement
ce code reste compatible avec cette règle.

Sur une installation déjà examinée, appliquer la mise à jour puis relancer
**Créer ou reprendre les index**, même si l’ancien rapport disait 135/135.
Les archives natives compatibles restent réutilisées et les compléments inchangés
ne sont pas reconstruits. Les archives nouvellement reconnues incompatibles
reçoivent leur complément ; la durée dépend du texte présent. Il n’est pas
nécessaire de réparer l’outil s’il était déjà prêt. Télécharger ensuite le rapport
d’indexation, puis le nouveau contrôle complet de recherche.

Une préparation longue peut tourner la nuit. Dans **Préparation automatique après
téléchargement**, activer/désactiver la fonction, choisir les heures du PC serveur
et la puissance de calcul. Deux heures identiques autorisent toute la journée ;
22 h à 6 h couvre la nuit. Fermer le navigateur n’arrête pas le travail.

## Après la correction des formules — 0.37.3

Les nouveaux compléments de texte conservent les formules HTML prises en charge.
Pour actualiser les anciens compléments, lancer **Créer ou reprendre les index** :
le format de construction 2 remplace le format 1 après reconstruction réussie.
Les anciens index publiés restent recherchables pendant ce travail ; une pause
ou un échec ne les supprime pas. Cette reprise peut durer : elle concerne les
compléments, pas une reconstruction des index natifs déjà compatibles de Kiwix.

La lecture directe d’un article profite du nouveau lecteur sans attendre cette
reconstruction. Un ancien fichier texte ou une traduction ayant déjà perdu les
équations ne se répare pas automatiquement ; repartir de l’article original.

## Pause, reprise et ressources

**Mettre en pause** conserve la progression et bloque une reprise automatique
non souhaitée. Après une coupure ou la perte du processus, la reprise est également
explicite : **Créer ou reprendre les index**. Le contrôleur reconnaît un processus
d’indexation enfant encore vivant et ne lance pas de doublon. Un résultat terminé
et identifié peut être récupéré même si son superviseur s’est arrêté.

Une préparation automatique s’arrête au prochain point de contrôle si son créneau
se termine, si elle est désactivée ou si le mode jeu est activé. Elle peut reprendre
au prochain créneau autorisé, contrairement à une pause volontaire. L’IA simplement
arrêtée n’empêche pas l’indexation CPU. Une sélection de téléchargement en attente
n’est jamais remplacée par un lancement automatique.

Le nombre de processus s’adapte aux CPU et à la RAM disponibles, avec prise en
compte des limites de conteneur Linux et jusqu’à seize processus automatiques.
Un cœur est conservé lorsque possible ; le calcul réduit le nombre de processus
si la marge mémoire est faible. Un réglage explicite de 1 à 16 est disponible.
Cela ne garantit pas une accélération proportionnelle : le disque peut limiter.
La réserve disque par défaut de 15 Go et les limites du laboratoire restent appliquées.

## Suivi et rapport

Le suivi distingue les archives encore dans la file, l’opération en cours et le
nombre d’articles des archives terminées. **Télécharger le rapport d’indexation**
exporte version, progression, réglages, motifs d’arrêt et erreurs ; il ne contient
pas les conversations ni les secrets du PC. Une erreur conserve les fichiers
vérifiés et les index déjà publiés, puis demande une reprise explicite.
Les résultats indiquent aussi les langues natives, la compatibilité des langues
et la raison du complément (`native_multilingual`, `native_language_missing` ou
`missing_index`). Ce contrôle de métadonnées ne certifie pas tous les usages de
l’API Kiwix. Une langue d’article non déterminée n’est pas déclarée française.

Si un fichier a été remplacé depuis sa vérification, la file est suspendue et
l’indique. Refaire la vérification ou le téléchargement de cette archive avant de
reprendre ; la nouvelle édition ne doit pas être marquée traitée par l’ancien travail.

Les index publiés sont immédiatement disponibles, sans redémarrage de l’assistant.
Le manifeste conserve toutes les archives préparées, même lorsqu’un nouveau lot
n’en contient qu’une. Les index manquants, illisibles ou périmés sont signalés dans
la recherche ; une archive supprimée n’est pas proposée depuis un ancien index.

## Données et limites

Les SQLite, le manifeste et la progression sont dans `data/state/pilot/archive-index`.
La file est dans `data/catalog/search-index-queue.json`. Les index sont reconstruisibles ;
les bases temporaires remplacent l’ancien index seulement après extraction complète
et synchronisation. Le curseur est validé tous les 64 éléments. Ne pas supprimer les
verrous `.lease` pour forcer un second travail.

Le traitement lit HTML, XHTML et texte brut en passages d’environ 2 400 caractères,
ignore les redirections et les formats non textuels, et limite un article à 2 Mo
à lire et 500 000 caractères à indexer. Il ne fait pas d’OCR générique. Une indexation
texte terminée ne signifie pas que le contenu parlé ou les images sont recherchables,
ni qu’une procédure est bonne. Le volume final et la durée sur le fonds réel restent
à mesurer. Les sauvegardes de l’état peuvent grossir ; prévoir leur capacité.

## Kit hors ligne et maintenance

Le lecteur `libzim==3.13.1` est isolé dans `prive/search-tools`. Ses paquets et
empreintes sont conservés dans `data/tools/search-index-wheels`, puis exportés sous
`app/vendor/search-index` lorsqu’ils sont disponibles. Le kit doit contenir une
roue compatible avec **le système, l’architecture et la version Python cibles**.
Le lecteur du PC Linux ne suffit pas à préparer un Windows hors ligne.

Pour ajouter une cible au cache depuis une installation connectée :

```text
python scripts/search_index_tools.py --work-dir <prive> --cache-target win_amd64:3.13
```

La cible `manylinux_2_28_x86_64:3.13` prépare Linux x64 ; Python 3.11 à 3.14 sont
acceptés. Ce téléchargement n’exécute pas le paquet étranger. Les empreintes sont
vérifiées avant installation hors ligne. Un outil absent ou incompatible est
signalé sans basculer silencieusement en ligne ni bloquer la lecture des documents.
Une restauration réelle intersystèmes reste une recette distincte.

Commande manuelle équivalente à la préparation locale :

```text
<python de prive/search-tools> scripts/index_archives.py --zim-dir <data/library/zim> --state-dir <data/state/pilot>
```

`--workers 1` à `--workers 16` impose le parallélisme ; `--include-indexed` force
également les ZIM déjà indexés par Kiwix et n’est pas le fonctionnement normal.
Avec `--cancel <fichier>`, créer ce fichier demande une pause au prochain point
de contrôle ; attendre la fin du processus avant une sauvegarde ou mise à jour.
`--reserve-bytes` règle la réserve en maintenance ; ne pas descendre sous 15 Go
au laboratoire. Les petits tests CLI choisissent explicitement 1 Go pour ne pas
dépendre de la capacité de la VM de CI.

## Comprendre les compteurs depuis 0.9.1

Le suivi distingue les archives examinées, celles qui réutilisent leur index Kiwix
intégré, les index locaux prêts et les archives en erreur. Zéro article ajouté à
l’index local ne signifie donc pas que tous les index intégrés sont absents.
Si le suivi signale un échec, télécharger le rapport d’indexation ; éviter les
relances répétées avant d’en examiner les erreurs. La capture seule ne précise
ni la cause de l’échec ni les sources effectivement indexées.

## Vérification de l’outil depuis 0.9.2

La préparation vérifie désormais, dans son propre Python isolé, que le lecteur
prévu se charge et que SQLite peut créer puis interroger son index de texte.
Cette vérification est aussi exécutée avant chaque nouvelle indexation, y compris
pour un ancien outil déjà marqué prêt. Elle ne parcourt aucun document et ne
démarre ni modèle IA ni connexion réseau. Le délai maximal de la vérification
après installation du lecteur est de trente secondes.

Un échec de ce contrôle arrête le lancement avant les archives : le rapport
indique zéro archive parcourue, le motif et les versions disponibles. Il distingue
lecteur absent, import impossible, version/API incompatible et recherche SQLite
indisponible. Le marqueur prêt est retiré, les anciens index sont conservés.
**Vérifier / réparer l’outil** reste une action explicite ; si SQLite manque,
le rapport doit être examiné avant de modifier l’installation Python. Une
réinstallation de libzim seule ne garantit pas la réparation de ce prérequis.

Le rapport conserve ensuite, pour chaque archive en erreur, une cause limitée :
réserve d’espace insuffisante, disque plein, fichier absent, accès refusé, source
modifiée, index SQLite ou lecture de l’archive. Il ne recopie pas les messages
natifs susceptibles de contenir des chemins privés. Un échec de lecture inconnu
reste un échec à diagnostiquer, sans conclure automatiquement à une archive corrompue.

Les marqueurs préparés avant 0.9.2 restent reconnus ; leur vérification effective
a lieu au prochain lancement. Aucun travail lourd n’est relancé par la mise à jour.
Sous Windows, le lancement des processus conserve aussi le mécanisme Python
adapté à l’environnement isolé : le remplacement par son `pythonw.exe` pouvait
bloquer ce démarrage. La préparation vérifie les prérequis ; elle ne garantit
pas à elle seule que les processus ont ensuite parcouru les archives.
Voir le [bilan des essais isolés](../essais/2026-11-14-indexation-isolee.md).

## Sauvegarde et mise à jour depuis 0.9.3

Mettre les préparations en pause et attendre leur arrêt avant ces opérations.
La sauvegarde privée conserve aussi les index et leur progression. Elle refuse
désormais un écrivain CLI actif avant d’arrêter les services ; la mise à jour et
son retour arrière gardent cette exclusion jusqu’à leur fin. Un processus
d’extraction encore vivant sans son superviseur reste pris en compte.

Le motif `index_busy` indique un processus actif ou un verrou à examiner, et non
un lecteur à réinstaller. Attendre l’arrêt confirmé ; transmettre le rapport si
l’état reste incompréhensible. Ne pas supprimer les `.lease` pour débloquer.
Ces fichiers ne sont pas transportés comme des états à restaurer. Les index
restaurés restent soumis à la vérification de leurs sources : une archive
remplacée ou recopiée avec une autre date peut demander une nouvelle préparation.

Pour la première mise à jour vers 0.9.3, l’ancien programme de maintenance reste
en charge : respecter la pause préalable. Voir le
[bilan des protections](../essais/2026-11-14-index-sauvegarde-et-retour-arriere.md).
