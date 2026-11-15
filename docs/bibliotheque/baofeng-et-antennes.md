# Notice Baofeng et calculs d’antenne

**Guide actuel — 0.19.1, 15 novembre 2026.** Louis confirme le modèle **UV‑5R**
inscrit sur son poste, présenté dans sa demande comme « 8 W ». Cette déclaration
ne valide pas une puissance mesurée ni une équivalence avec l’UV‑5RTP.
Le [bilan des essais](../essais/2026-11-15-notices-et-guidage-pratique.md) distingue
l’ajout au catalogue, les essais sur le R7 et la préparation chez Marc.

## Contenu proposé

Le catalogue ajoute la notice commune **Baofeng UV‑5R et GT‑3**, édition indiquée
V1.0, PDF multilingue de 60 pages. Partie française : pages **31 à 41 du fichier
PDF** ; la pagination imprimée peut être différente. Le tableau anglais de la
page PDF 22 distingue UV‑5R et UV‑5RTP/GT‑3TP : ne pas attribuer automatiquement
les trois niveaux de puissance de la seconde variante au poste UV‑5R de Louis.
La date de publication n’est pas établie ; les dates internes du fichier ne
suffisent pas à la dater.

[Page de téléchargement Radioddity](https://www.radioddity.com/pages/baofeng-download),
[PDF multilingue vérifié](https://radioddity.s3.amazonaws.com/Baofeng%20UV5R%20%26%20GT-3%20Series%20User%20Manual%20%5BEN%20DE%20IT%20FR%20ES%5D.pdf),
[notices proposées par Baofeng](https://www.baofengradio.com/pages/download).
Le PDF est un contenu séparé du code : 17 968 170 octets, SHA-256
`bd43cd9b58c311fcf0e0f02eeb4a1e9bbd0fdd1a6deea4150ba9df9c5932e485`.
L’exemplaire a été téléchargé et son texte extrait sur le R7 ; cela n’annonce
aucun téléchargement sur le PC de Marc. Les droits de redistribution commerciale
et de traduction restent à vérifier ; le PDF n’est pas ajouté au dépôt public.

La fiche originale SetupSurvie [Antennes radio](../../deploy/library-templates/antennes-radio.fr.md)
complète la notice avec des calculs généraux, les références BIPM/ARRL et leurs
limites. Elle distingue quart d’onde, longueur totale d’un dipôle et longueur de
chaque bras, dimensions théoriques, ajustement réel et antenne commerciale raccourcie.
Elle ne transforme pas une longueur calculée en garantie de bon accord ou de portée.

## Ajouter au poste cible

Après mise à jour normale du logiciel, avec Internet, depuis le dossier application :

```powershell
py -3 scripts\content.py download --work-dir D:\SetupSurvie\prive --id baofeng-uv5r-manual
```

Adapter le dossier privé à l’installation existante ; ne pas créer une seconde
installation. Le téléchargeur vérifie taille/empreinte, conserve les contenus et
installe aussi la fiche française dans `library/guides/REF-antennes-radio.fr.md`
si elle n’existe pas. Les [procédures de téléchargement](../exploitation/mises-a-jour-et-bibliotheque-pilote.md#télécharger-des-lots-sans-réinstaller)
et la préparation des services restent celles de l’installation.

Sur Linux, utiliser `python3 scripts/content.py download --work-dir /chemin/prive
--id baofeng-uv5r-manual` sur une seule ligne, avec le dossier privé existant.
Le laboratoire de Louis garde ses contraintes de montage/capacité ; aucun modèle
ni vraie notice n’est téléchargé dans le petit runner CPU de développement.

Changer le code seul n’ajoute pas le PDF aux anciens plans de téléchargement.
La notice fait aussi partie des nouvelles sélections du lot **communications**.
Le texte doit être indexé par le pilote pour apparaître dans la recherche ; cette
préparation et les index ZIM sont des étapes différentes. Chercher ensuite
« Baofeng UV‑5R » dans la Bibliothèque et ouvrir la notice pour contrôler sa présence.
La notice et la fiche installées restent consultables hors ligne sans IA.

## Essayer l’aide réellement apportée

Demander une opération précise : verrouiller le clavier, mémoriser un canal vide,
ou comparer les deux types d’antenne. Vérifier que l’assistant cite la bonne page
et donne les commandes documentées, sans proposer un effacement des autres canaux.
Pour une dimension, indiquer fréquence et type de montage ; si ces informations
manquent, l’assistant doit les demander avant d’annoncer une taille.
Le tableau de la fiche donne des exemples de calcul, pas des fréquences autorisées.

Ces questions forment un cas de recette parmi d’autres. Elles ne remplacent pas
les essais de procédures, paramètres manquants, contradictions et calculs dans
d’autres domaines. Une source réellement ouverte et un chiffre bien calculé ne
suffisent pas à prouver que l’ensemble d’une réponse est fidèle ou applicable.
