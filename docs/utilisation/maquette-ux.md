# Essayer la nouvelle organisation du portail

**Depuis 0.1.32**, la [nouvelle interface fonctionnelle](nouvelle-interface.md)
est l’entrée principale ; la classique reste sous `/classique/`. La maquette
ci-dessous est conservée comme démonstration fictive de la phase 0.1.31.

**Guide actuel de la maquette 0.1.31 — 13 novembre 2026.**
La refonte complète reste un [plan](../decisions/plan-refonte-ux.md).

## Ouvrir et revenir au portail habituel

Sur une installation mise à jour en 0.1.31, cliquer sur **Essayer la nouvelle
organisation** dans le menu du portail, ou ouvrir `/maquette/` sur le même serveur.
L’adresse habituelle reste celle de l’interface actuelle. Le lien **Revenir à
l’interface actuelle** reste visible dans la maquette, y compris sur téléphone.

La maquette possède ses propres pages, styles et scripts dans `portal/maquette/`.
Elle ne remplace pas le portail. La référence Git `interface-classique-0.1.30`
conserve le code d’avant cette livraison ; aucun retour de version n’est nécessaire
pour retrouver l’interface habituelle. La route séparée `/classique/` du plan
n’est pas encore nécessaire ni créée : l’interface classique reste à la racine.
Sa compatibilité et sa conservation autonome devront être traitées avant tout
remplacement de cette racine par la refonte complète.

## Ce que l’on peut essayer

- Accueil : recherche et accès aux collections, à l’assistant et aux cartes.
- Bibliothèque : ouvrir une collection directement, lire ses exemples, rechercher,
  suivre un parcours, ajouter un favori et retrouver la place des traductions.
- Assistant : écrire un brouillon et changer de page sans le perdre. L’envoi est
  une simulation annoncée ; aucune réponse IA n’est produite.
- Cartes : illustration sans données géographiques et navigation entre carte,
  repères et itinéraires. Les vraies cartes restent accessibles par un lien.
- Mon appareil : vue d’ensemble, activité, téléchargements, stockage et réglages.
  Un sélecteur permet d’essayer transfert, vérification, mode jeu et suivi indisponible.

**Toutes les collections, les mesures et les activités affichées dans la maquette
sont fictives.** Elle n’appelle aucune API du serveur et ne lit pas l’état réel
du PC de Marc. Les liens vers le portail actuel permettent de retrouver les vraies
fonctions ; leur ouverture seule ne lance aucune opération.
La pause documentaire proposée sur ordinateur change uniquement l’exemple affiché.

Les deux profils de démonstration Famille et Visiteur ne sont pas les profils
réels. Ils permettent d’essayer la séparation des brouillons et favoris locaux.
Les profils réels restent dans le portail habituel.

## Navigation et mémoire

Les flèches Précédent/Suivant du navigateur suivent les changements de page.
Les liens peuvent être copiés et ouverts dans un nouvel onglet. Revenir à une
liste conserve la recherche et la position de défilement. Un rechargement conserve
la page et la position de cette entrée d’historique.

La maquette mémorise les sous-rubriques visitées, les volets ouverts, le mode de
réponse, les brouillons et les favoris fictifs, par profil de démonstration dans
ce navigateur. Une ouverture sans lien précis reprend le dernier écran connu ;
un lien explicite reste prioritaire. Les enregistrements expirent à leur prochaine
lecture après sept jours sans mise à jour. Ce n’est ni une sauvegarde ni une
synchronisation entre appareils. Si le stockage navigateur est refusé, les fonctions
de navigation restent utilisables ; la mémoire peut être limitée à la page ouverte.

La commande **Mon appareil → Réglages → Effacer la mémoire de cette maquette**
efface uniquement ses données de démonstration pour ce navigateur. Elle n’efface
aucun profil, favori ou historique réel. La pause de démonstration n’est pas
restaurée après rechargement ; aucune action réelle n’est relancée.

Sur téléphone, les cinq rubriques restent accessibles dans la barre du bas.
Les cartes et les suivis se consultent ; les commandes complexes de préparation
et la simulation pause/reprise sont retirées de cette présentation. Les réglages
réels sont encore ceux du portail actuel, pas une refonte mobile déjà raccordée.

## État de la réalisation

Cette livraison fournit une maquette navigable et un lien de découverte dans le
portail. Elle ne réalise pas encore le suivi commun Windows/web, le raccordement
des collections réelles dans la nouvelle bibliothèque ni le déplacement des
commandes de production. Les fonctions actuelles, données et processus restent
dans le portail existant. Aucun déploiement sur le PC de Marc n’est réalisé par
la création de ces fichiers.

La recette reproductible est `tests/browser_ux_preview.js`, ajoutée au lanceur
navigateur de la CI : Chromium et WebKit y sont prévus. Les résultats réellement
obtenus et limites figurent dans le [bilan de la maquette](../essais/2026-11-13-maquette-ux.md).
