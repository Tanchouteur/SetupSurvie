# Documents choisis et pages pertinentes des PDF

**Bilan daté du 15 novembre 2026 — préparation de la livraison 0.17.0.** Le lot
rend explicite la sélection de plusieurs documents pour l’assistant. Il ne clôt
pas la validation du sens de toutes les réponses ni le programme des vidéos.

## Comportement ajouté

Les résultats et le lecteur proposent **Choisir pour l’assistant**. Le premier
choix crée une conversation enregistrée sans lancer le modèle. On peut ajouter,
ouvrir ou retirer des documents, puis poser une question commune. La sélection
est conservée côté serveur ; la liste reste repliée dans l’assistant. Une ancienne
réponse de lecture retardée ne doit pas remplacer une nouvelle conversation.

Douze références au maximum composent cette sélection ; le dossier transmis
reste adapté au contexte réel. Le modèle lit des passages, pas automatiquement
douze livres entiers. Les sources non lisibles ne deviennent pas des citations
et n’empêchent pas les autres lectures. Les textes restent des données d’outils,
sans être placés dans les instructions système. Les mesures séparent documents
choisis, préparés et consultés.

Un PDF entier choisi peut fournir une page tardive déjà indexée correspondant au
sujet. La recherche est restreinte à ce fichier, avec le vocabulaire commun. Une
page choisie explicitement reste cette page ; sans correspondance, le début
limité reste le repli. Le numéro de la page effectivement lue est conservé dans
la référence. Le test de régression atteint notamment une page fictive 48.

La traduction garde un document cible sélectionnable et conserve les autres
références de la conversation. Les messages, traductions et fichiers ne sont
pas supprimés lorsqu’une référence est retirée. Les associations historiques à
un document restent utilisables ; la nouvelle table privée est optionnelle et
le schéma de livraison reste 1. Les modifications et questions concurrentes sont
refusées pendant une réponse. La pause moteur est respectée même si la mesure
de disponibilité annonce encore le moteur en ligne.

L’ajout des références présente d’abord les valeurs et lignes de tableau au
modèle, avec jusqu’à vingt-quatre liens, pour ne pas épuiser la place sur les
seules introductions. Cela ne certifie pas la fidélité de leur sens et ne réécrit
pas le texte. Cette adaptation suit l’essai défavorable consigné ci-dessous.

## Vérifications réalisées

- Runner Linux Python 3.13 : **665 tests réussis, trois ignorés**, sans modèle
  réel. Tests nouveaux d’API, persistance, isolation par profil, traduction,
  sélection illisible, repli sans table optionnelle, pause, doubles envois et
  lecture réelle des passages indexés tardifs.
- Chromium et WebKit : **77 contrôles ciblés par navigateur**, dont sélection
  multiple 17, confort 37 et mesures 23. La traduction existante a également été
  rejouée sur Chromium : association, pause/reprise, export et plage PDF conservés.
  Aucun iPhone physique ni Windows de Marc testé dans le runner.
- JavaScript vérifié, HTML régénéré, versions API/manifeste 0.17.0 cohérentes.
  La CI Windows/Linux et le paquet seront consignés dans le reçu de livraison.

## Essais avec le vrai modèle sur le R7

Gemma4 E4B, digest
`dc35e8d9c6061baa6f0fa870975ab6932e2542b579b13ea0f199fa4bb7300c9c`,
Ollama natif 0.40.14, contexte 16k, réflexion activée, sortie maximale 4 096
tokens, huit couches GPU et six threads. Les autres tâches ne sont pas arrêtées.
Les rapports sont privés ; aucun compte ni vrai document familial n’est copié.

Premier essai de sélection explicite sur cinq notices textuelles fictives :
**89 151 ms**, cinq documents préparés/lus, cinq valeurs et associations correctes.
**Limite observée :** les douze liens admis concernaient surtout des introductions
et avertissements, laissant le tableau sans références par ligne. Les dates
n’étaient pas reprises. Cet essai ne devient pas une validation éditoriale au
motif que la demande a terminé. SHA-256 du rapport privé :
`1eeba2a64f65b6b54df2496cab4c03d44b0b9001a75f3a4875ebadf14e2b89aa` ;
digest du code Python : `1246a310186da51cd8940d5d65f6846556b2e5ea4b37afac63a92ca3b139b69c`.

Après la priorité aux fragments factuels, essai sur **cinq PDF de six pages** :
les valeurs sont uniquement à la page 6, hors de l’aperçu des quatre premières.
**79 124 ms**, cinq pages 6 lues, cinq valeurs correctes et cinq références directes
correctes dans le tableau, dates reprises. Aucune étape de liaison supplémentaire
n’a été nécessaire. Cela confirme la lecture de ces pages, pas une lecture
intégrale des PDF ni la pertinence d’un vrai manuel. SHA-256 du rapport privé :
`d9d30a6e5e6571b16daaa60077b5b1a68f290df5e3d86a927f7c1f5136195732` ;
digest du code Python : `bdae5285a980678dcbe471df74278da78549a3a5b93fe4120d6c86301b15989c`.

La [recette réelle](assistant-modele-reel.md) ajoute `--selected` et `--pdf-fixture`.
Le dernier rejeu sur le code à livrer et le reçu final sont ajoutés après contrôle.
Les mesures R7 ne prédisent pas la cadence du Windows de Marc. Ces cas servent
au développement ; aucune évaluation aveugle ni qualité générale n’est revendiquée.

## Choix et suite

Conserver la sélection explicite, sa reprise et le document de traduction distinct.
Conserver une recherche de page restreinte au PDF choisi ; ne pas remplacer
silencieusement cette sélection par des documents d’un autre fonds. Ne pas
transformer une sélection enregistrée en preuve de lecture ou de contenu fiable.

Les longues synthèses intermédiaires, les illustrations originales et la
qualification sur des sujets variés restent nécessaires. La traduction longue
et l’acquisition/création des sous-titres restent les étapes suivantes du
[plan](../decisions/plan-ameliorations-marc.md). Version mineure 0.17.0 justifiée
par ce nouveau parcours compatible, sans migration destructive ni changement
des modèles conseillés ou des versions tierces. Aucun déploiement chez Marc.
