# Rendre les archives recherchables

**Guide actuel — 0.3.0, 14 novembre 2026.** L’index complémentaire extrait le texte
des archives ZIM qui n’ont pas de véritable index de recherche Kiwix. Il ne
modifie pas les archives et ne lance aucun modèle IA.

## Depuis le site Windows ou Linux

Dans **Famille → Mon appareil → Réglages → Rendre les archives recherchables** :

1. Choisir **Préparer l’outil · Internet requis** une première fois. Le PC serveur
   crée un environnement Python séparé et récupère `libzim==3.13.1`, sans modèle
   ni corpus. Les roues téléchargées sont conservées pour une réinstallation
   locale sur la même plateforme. Aucune installation Python globale.
2. Une fois l’outil prêt, choisir **Créer ou reprendre les index**. Cette étape
   fonctionne sans Internet. Plusieurs processus utilisent les cœurs disponibles,
   jusqu’à huit par défaut, en conservant un cœur lorsque c’est possible.
3. Laisser le PC travailler ; fermer le navigateur n’arrête pas l’opération.
   Le suivi compte les archives examinées et les articles des archives terminées.
4. **Mettre en pause** conserve les index publiés et la progression validée.
   Après un redémarrage ou une interruption, la reprise est explicite avec le
   même bouton ; aucune indexation lourde ne démarre automatiquement.

Les index sont disponibles dans la recherche dès la fin de chaque archive,
sans redémarrer l’assistant. Les archives déjà indexées par Kiwix sont examinées
puis ignorées. Les comptes et conversations restent dans leurs bases habituelles.

## Données et limites

Les fichiers SQLite sont dans `data/state/pilot/archive-index`, à côté de l’état
du pilote. Ils sont reconstruisibles ; les nouveaux fichiers temporaires ne
remplacent l’ancien index qu’après une extraction terminée et synchronisée.
Le curseur est validé tous les 64 éléments ; une interruption peut faire relire
le dernier lot. L’identité, la taille et la modification du ZIM invalident une
ancienne préparation. Le verrou `.lease` ne doit jamais être supprimé pour forcer
un second travail. L’état indique les archives en erreur ; les autres continuent.

L’outil lit le HTML, XHTML et texte brut, par passages d’environ 2 400 caractères.
Il ignore redirections et contenus non textuels, limite un article à 2 Mo à lire
et 500 000 caractères à indexer. Il ne transcrit pas l’audio, ne fait pas d’OCR,
ne traduit pas les vidéos et ne garantit pas la qualité d’une procédure.
Une marge libre de 15 Go est contrôlée pendant l’écriture depuis le site ; le contrôle du
stockage du laboratoire reste appliqué avant le lancement. L’espace final
nécessaire et la durée sur le fonds réel de Marc ne sont pas encore mesurés.

La préparation utilise Python et pip du PC serveur ; elle demande leur
fonctionnement et une roue compatible avec le système et l’architecture.
[Le paquet libzim officiel](https://pypi.org/project/libzim/3.13.1/) fournit les
roues utilisées ; Windows x64 et Linux sont couverts par la recette CI.
Les index ne sont pas inclus dans un petit paquet logiciel. Les sauvegardes de
l’état peuvent devenir plus grandes : prévoir la capacité du disque de secours.

## Commande de maintenance

Après préparation de l’environnement, l’opération équivalente est :

```text
<python de prive/search-tools> scripts/index_archives.py --zim-dir <data/library/zim> --state-dir <data/state/pilot>
```

`--workers 1` à `--workers 16` permet un réglage explicite en maintenance ;
`--include-indexed` reconstruit aussi les archives déjà indexées par Kiwix et
n’est pas le fonctionnement normal du site. Les deux systèmes utilisent la même
base SQLite ; seuls les chemins des environnements Python diffèrent.

La commande de maintenance permet `--reserve-bytes` pour une réserve explicite ; ne jamais descendre sous 15 Go dans le laboratoire. Le test CLI sur de minuscules archives temporaires choisit 1 Go pour ne pas dépendre de la capacité de la VM de CI.
