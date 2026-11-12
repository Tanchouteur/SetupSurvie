# Vérifier les sources et l’incertitude des modèles

**Protocole à exécuter sur les modèles réels — pilote 0.1.18.** Préparé le
12 novembre 2026. Aucun résultat GPT-OSS/Gemma réel n’est annoncé par ce document.

## Ce qui est déjà vérifié

Les tests CPU utilisent des documents minuscules et des réponses HTTP simulées :
préservation des anciennes métadonnées et conversations, dates dans les outils
de recherche/lecture, document associé, conservation des références dans les
réponses et refus des citations non lues. Ils vérifient aussi que la date d’une
archive ne devient pas une date d’article, et qu’une source absente ne crée pas
de référence consultée.

La recette Playwright du portail vérifie les dates dans le lecteur et les
citations, leur conservation après rechargement, l’ajout d’un document sans date,
le refus d’une date impossible et l’affichage des métadonnées comme texte. Les
dispositions de 320 à 1 366 pixels sont contrôlées. La recette de traduction
existante est conservée. Chromium/WebKit en CI ne remplacent pas Safari iPhone.

Ces réponses simulées prouvent le transport des informations et les limites des
outils. Elles ne prouvent pas qu’un modèle produit lui-même une réponse correcte.

## Préparer les petits documents fictifs

Sur une machine de test, depuis le dépôt :

```bash
python scripts/prepare_reliability_cases.py /CHEMIN/NEUF/recette-fiabilite
```

Sous Windows, remplacer le chemin par exemple par `D:\Essais\recette-fiabilite`
et utiliser `py -3` si nécessaire. La destination doit être nouvelle ; aucun
fichier existant n’est remplacé. Le script prépare sept textes fictifs, leurs
métadonnées et une fiche de recette ; il ne télécharge rien et ne contacte aucun
modèle. Les cas sont conservés dans `fixtures/evaluation/reliability.json`.

Utiliser **une installation d’essai dédiée**, avec les modèles déjà préparés sur
le PC cible. Copier le contenu du sous-dossier `guides` dans sa bibliothèque de
test, puis réindexer depuis Paramètres. Garder `RECETTE.md` hors de la bibliothèque :
cette fiche contient les questions et critères de notation, pas des sources.
Ne pas importer ces exemples dans le fonds familial, ni les présenter comme des
notices réelles ou un corpus pratique. Ne pas copier de comptes ou conversations
réels dans l’installation de test.

## Campagne et critères

Ouvrir une nouvelle conversation pour chaque question et chaque mode. Associer
le document indiqué lorsqu’il n’y en a qu’un ; laisser l’assistant rechercher
les deux notices pour la contradiction. Utiliser les questions de `RECETTE.md`
sans lui montrer les critères attendus ni les réponses précédentes.

| Cas | Contrôle humain attendu |
| --- | --- |
| Fait daté | Volume attribué à la notice, titre, date 2010 et édition A |
| Information absente | Charge maximale inconnue ; pas de conversion abusive du volume en charge |
| Contradiction | Deux notices et dates citées, désaccord 10/20 kg, pas d’arbitrage fondé sur la seule nouveauté |
| Source ancienne | Horaires de 2010 distingués d’une ouverture actuelle inconnue |
| Lecture partielle | Page 2 manquante annoncée, charge non inventée |
| Déduction | Quatre bouteilles de deux litres attribuées au document, total de huit litres annoncé comme calcul |
| Date inconnue | Compartiments cités, date du document inconnue sans substitution par la collecte |
| Source absente | Recherche sans notice inventée, limite de la base explicitée |

Comparer les trois modes conseillés, avec deux répétitions par cas si le temps
disponible le permet. Pour chaque réponse, conserver dans un rapport privé :
version, machine, système, mode, modèle exact, question, réponse, sources réellement
ouvertes, délai, réussite/échec de chaque critère et informations encore manquantes.
Une réponse tronquée, une erreur ou une exécution non réalisée reste identifiée
comme telle ; elle n’est pas comptée comme une réussite.

La pause du moteur doit avoir été explicitement levée avant tout essai réel.
Ne pas lancer de modèle ni de benchmark dans le runner CPU et ne pas arrêter les
applications de l’utilisateur pour libérer de la VRAM. Les résultats Linux et
Windows restent séparés ; un résultat ne certifie pas tous les documents ni tous
les usages futurs.
