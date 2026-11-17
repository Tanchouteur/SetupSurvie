# Formules, réduction du contexte et suite de lecture

**Bilan ciblé — 17 novembre 2026, candidat 0.38.3.** Complète la
[préservation des formules 0.37.3](2026-11-17-formules-documentaires.md), dans
le même objectif de fidélité des sources reçues par l’assistant.

## Deux chemins encore exposés

La recherche par passages et les nouvelles traductions gardaient les blocs
mathématiques, mais `fit_context` réduisait les textes reçus par coupes brutes
à 700/300 caractères. L’outil `read_source` coupait aussi chaque suite à 3 500
caractères sans regarder les équations. Ces deux chemins pouvaient transmettre
une demi-fraction à l’IA. La relecture de code et les tests le reproduisent,
sans déduire un incident réel non observé chez Marc.

La réduction conserve maintenant un préfixe arrêté avant une formule traversant
sa limite, pour les lectures simples et par lots. La lecture explicite conserve
une tranche contiguë et ses vrais offsets ; elle peut s’arrêter avant un bloc,
reprendre à son début, ou revenir au début d’une petite formule quand la position
était à l’intérieur. Un bloc plus long que la fenêtre est omis et signalé par
`formula_omitted`, avec lecture partielle. Si rien de lisible ne reste, la lecture
échoue sans nouvelle source déclarée consultée. Le contexte, les limites de texte
et la réserve de sortie ne sont pas augmentés.

Les originaux, historiques, références enregistrées et formules elles-mêmes
ne sont pas réécrits. Cette protection de structure ne prouve pas la validité
d’un calcul ou le sens d’une réponse. La formule omise reste à lire dans l’original.
Correction compatible, niveau patch ; schéma personnel et composants tiers inchangés.

## Vérifications

Avant correction, **61 tests d’orchestration, 2 échecs** en 16,174 s : coupe de
contexte et lecture explicite de la suite. Après correction : **61 tests réussis
en 14,857 s**. Les tests traversent le moteur et le protocole HTTP simulé ; les
tranches sont comparées au texte source et la suite reçoit une formule entière.
**19 tests d’extraction/formules réussis en 0,401 s** couvrent aussi position au
milieu du bloc, bloc trop grand, préfixe incomplet et conservation des bornes.
Les fixtures sont minuscules et fictives, sans modèle ni corpus téléchargé dans
le runner. Aucun nouvel essai de génération réelle n’est revendiqué pour ce lot.

Suite complète locale : **1 013 tests en 202,916 s, 6 ignorés**, aucun échec.
La CI reste en cours avant livraison.


Paquet candidat source `338dae2a7aa26a3c5bd78fc3f51286eb77bf4785` : **978 fichiers**, **17 278 278 octets**
décompressés, ZIP **7 726 665 octets**, SHA-256
`158c1844d9245c8798df447c0310b40f864748d48d714396c5ca1faeb315fe49`.
Chaque fichier est comparé à Git avec ses filtres et aux tailles/empreintes du
manifeste ; 1 282 liens locaux et ancres sont contrôlés sans cible manquante.
Ce reçu est ajouté après le paquet, donc non prétendu inclus dans celui-ci.
Aucun déploiement sur les PC clients n’est effectué pour ces contrôles.
