# Recherche des ressources et cartes directes — 13 novembre 2026

**Bilan daté — 0.1.34.** Voir le [guide actuel](../utilisation/nouvelle-interface.md).

## Demande et changement

Louis demande un champ dans Collections pour répondre à « est-ce qu’on a cette
ressource ? », en préservant la nouvelle présentation. Il demande aussi que
l’onglet Cartes ouvre directement la carte et que le relief soit visible immédiatement.
Le dépôt est synchronisé jusqu’à `f570c63` avant modification, en préservant les
correctifs et le compte rendu réel des cartes Windows 0.1.33.

Le filtre est un module isolé qui masque seulement les cartes non correspondantes.
Il ne remplace pas leurs boutons, ne supprime pas leurs gestionnaires et ne
modifie pas les collections. Les champs de métadonnées sont ajoutés aux cartes
par le rendu existant, avec des attributs DOM, sans nouveau contrat d’API.
Les titres et noms de fichiers, descriptions et langues sont comparés après
normalisation des accents et majuscules ; tous les mots saisis doivent correspondre.

Un compteur distingue les ressources recensées et disponibles à la lecture.
Un partiel reste marqué à préparer. Un résultat vide explique que les articles
peuvent néanmoins traiter le sujet et propose la recherche dans leur contenu.
Le filtre est mémorisé par profil et repris dans l’URL sans entrée d’historique
à chaque frappe. La recherche se fait sur l’inventaire chargé, sans inférence,
requête de contenu, installation ou téléchargement.

L’entrée Cartes est un lien vers la page native existante ; les anciens liens
`#/cartes` y conduisent aussi. Le retour mène à l’accueil, pour ne pas boucler.
La couche de relief est activée à l’initialisation seulement lorsque le statut
local annonce des altitudes. Le bouton et `aria-pressed` correspondent à cet état.
L’utilisateur peut toujours masquer/réactiver le relief. Son absence ne bloque
pas la carte et ne déclenche pas de préparation en ligne. La présence d’une
zone locale ne garantit pas le relief hors de sa couverture.

## Vérifications

Sur runner CPU, sans corpus, carte lourde ou modèle :

- Suite Python complète : **332 tests, 3 ignorés**, réussie.
- Syntaxe JavaScript et `git diff --check` vérifiés ; génération des deux entrées
  modernes cohérente avec la classique.
- Recette Chromium Collections : **18 contrôles** (accents/casse, mots multiples,
  noms de fichier, compteur, partiels, état vide, recherche de contenu, retour,
  rechargement, effacement, liens conservés et petit écran).
- Recette Chromium Cartes : **12 contrôles**, avec une tuile de relief synthétique
  de 853 octets. Relief activé dès l’ouverture, tuiles locales, bouton réversible,
  retour sans boucle, absence d’altitudes et absence de mutations/requêtes Internet.
- Recette fonctionnelle du portail : **27 contrôles**, incluant l’ouverture native
  directe depuis le menu mobile, les documents, profils, brouillons et PDF.
- Les recettes sont ajoutées aux lanceurs CI Chromium/WebKit ; les modules de
  l’interface classique et les campagnes existantes sont conservés.

Les résultats CI seront consignés avant intégration. Aucun déploiement sur le PC
Windows de Marc ni essai Safari iPhone physique ne sont effectués dans le runner.
Les résultats Windows 0.1.33 du journal d’incidents restent distincts de cette recette.
