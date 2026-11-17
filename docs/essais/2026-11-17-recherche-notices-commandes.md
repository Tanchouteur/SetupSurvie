# Recherche préalable des commandes dans les notices

**Bilan ciblé — 17 novembre 2026, candidat 0.38.2.** Suite du
[contre-exemple réel de la 0.38.1](2026-11-17-aide-generale-sans-source.md#contre-épreuve-de-notice-non-annoncée-fictive).

## Défaut et changement

« Selon la notice du contrôleur TQ-917, quelle touche efface sa mémoire ? »
renvoyait `None` dans `document_request`. Le modèle réel demandait alors la
notice sans chercher localement. Ajouter seulement « notice » au routage
laisserait aussi les mots conversationnels devenir des contraintes de recherche.

Le moteur reconnaît maintenant une demande explicite de touche/bouton/commande
ou réglage dans une notice, en français ou anglais. Une unique référence mixte
lettres/chiffres explicitement fournie sert de requête initiale. La demande
complète reste dans la conversation et dans la sélection des passages lus ;
aucune commande n’est codée en dur et aucun résultat n’est une source avant lecture.
Une référence absente ou plusieurs références conservent la demande complète.
Une relance courte conserve la référence/collection de la dernière question
utilisateur seulement, jamais une référence inventée par l’assistant, et ne
remonte pas au-delà d’un nouveau sujet.

Version patch : correction d’un routage compatible. Schéma des données, moteurs
cartographiques et versions tierces inchangés ; aucun composant UX modifié.

## Contrôles exécutés

Avant correction : **12 tests, 4 échecs et 6 erreurs**, dont absence du nouveau
sélecteur ; les quatre formulations retournent à tort aucune préparation.
Après correction : **12 tests de demandes et recherche, 0,996 s**, puis
**59 tests d’orchestration, 14,883 s**, tous réussis. Petites fixtures fictives :
notice TQ-917 trouvée par référence, passage REPERE lu et cité ; question complète
et filtres conservés, question numérique nue sans recherche, plusieurs références
sans réduction, nouveau sujet sans ancien appareil. Aucune commande d’appareil
réel n’est validée par ces fixtures.

La suite complète et la CI restent à terminer. Après relecture des filtres,
le dernier test ajoute priorité à la collection de la relance et conservation
du parcours spécifique aux favoris, sans élargissement implicite.

## Deux essais réels R7

Gemma4 E4B existant, contexte 16 384, huit couches GPU et quatre threads,
maintien 15 s, réserve mémoire contrôlée et aucun autre traitement arrêté.
Le moteur utilise une petite notice fictive locale indexée, pas le fonds de Marc.
La recherche et la lecture traversent le produit ; les générations sont réelles.

- Notice TQ-917 présente : **25 917 ms**, recherche sur la référence, un document
  effectivement lu et cité. La réponse donne REPERE pour afficher l’identifiant
  de recette et rappelle que la notice ne décrit aucun appareil réel.
- Notice ZQ-816 absente : **11 734 ms**, recherche réellement exécutée et paquet
  sans passage ; le modèle demande la notice sans inventer de touche. Il ne faut
  pas transformer ce fonds de test vide sur ce sujet en absence générale sur Marc.

Le rapport conserve réponses, appels et empreintes du moteur observé avant le
dernier ajustement de priorité des filtres. Cet ajustement est testé sur fixtures ;
aucun rejeu réel correspondant n’est revendiqué. Les tests portent sur un appareil
inventé et ne valident pas les commandes d’un vrai poste, toutes les références,
les variantes d’édition ou les relances d’une conversation réelle.
Rapport/recette privés hors Git ; dossier d’essai supprimé après export.


Archive privée locale `setupsurvie-0382-notices-prive.tgz`, **4 797 octets**,
SHA-256 `96f08d098e8730436d08c15a1185922bad2e5dd0a38fb5a3fa5e26b5b60bd217`.
Derniers contrôles de filtres : **12 tests, 0,733 s**, sans échec.


Suite complète locale : **1010 tests en 201.679 s, 6 ignorés**, aucun échec.

Paquet candidat source `3e5543d417f1eaa6d10e20ad39b1590ef399c8d5` : **977 fichiers**, **17 268 205 octets**
décompressés, ZIP **7 722 757 octets**, SHA-256
`49cfd70329ff0244b205992c42f109cd64a4df8ef6bff6799574056ebeb1a3de`.
Chaque fichier est comparé à Git avec ses filtres et aux tailles/empreintes du
manifeste ; 1 277 liens locaux et ancres contrôlés, aucune cible manquante.
Ce reçu est postérieur au paquet et n’est pas prétendu inclus dedans.
La CI complète reste en cours ; aucun déploiement client n’est annoncé.
