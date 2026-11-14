# Vérifier l’usage sans Internet et sans IA

**Guide actuel — 0.10.0, 14 novembre 2026.** Ce contrôle R7 complète les
[32 recherches documentaires](recherche-documentaire.md#vérification-sur-le-windows-de-marc-depuis-le-site).
Il mesure quelques accès et recueille vos observations ; il ne valide pas
automatiquement les documents, les sauvegardes ou toute l’installation.

## Préparer et lancer l’essai

1. Depuis le profil **Famille**, ouvrir **Mon appareil → Paramètres → Entretien et diagnostics → Vérifier l’usage
   hors ligne → Tester l’usage hors ligne**.
2. Pour un essai sans Internet, couper l’accès à Internet du serveur et de
   l’appareil de consultation, tout en conservant leur réseau local. Ne pas
   désactiver le Wi-Fi ou l’Ethernet qui les relie. Sur téléphone, vérifier aussi
   les données mobiles. Le portail ne coupe rien et ne peut pas certifier cette
   condition ; la personne qui teste la déclare dans le formulaire.
3. Pour vérifier aussi l’usage sans IA, arrêter le moteur depuis **Mon appareil**
   lorsqu’aucune réponse ou préparation IA n’est en cours. Respecter une pause
   déjà demandée ou le mode jeu ; ce contrôle ne démarre ni ne reprend le moteur.
4. Choisir la connexion et le type d’appareil utilisés pour cet essai, puis
   **Lancer les contrôles**. Ils durent au maximum 90 secondes, avec une limite
   de quinze secondes pour chaque lecture. **Arrêter** conserve les mesures reçues.
5. Lire les résultats. Ouvrir **Étapes vérifiées par vous**, effectuer les essais
   utiles et indiquer pour chacun **Essai réussi**, **Problème rencontré**,
   **Ne s’applique pas à cet essai** ou **Non effectué**. Garder ce dernier choix
   si l’étape n’a pas été faite. Les étapes de maintenance sont dans un volet séparé.
6. Ajouter une observation courte si nécessaire, puis **Télécharger le rapport
   d’usage**. Retourner ce fichier avec le contrôle documentaire R2 si demandé.

Les vérifications humaines n’ont pas la limite de 90 secondes. Elles peuvent être
effectuées progressivement. Une restauration ou une panne forcée s’essaie sur une
copie jetable distincte ; cet outil ne provoque pas ces opérations. Le protocole
de [sauvegarde et restauration](../exploitation/disque-de-secours-hors-ligne.md)
reste un chantier distinct avec sa propre recette.

## Ce qui est mesuré

Le portail lit son état et sa version, l’état du contrôleur IA, l’accès Kiwix,
le catalogue et les compteurs d’index. Il effectue deux recherches « faire du
feu », dans Toute la bibliothèque puis Autonomie et résilience. Il lit au maximum
deux aperçus distincts, vérifie à nouveau l’état du moteur, la réponse de la page
statique de secours et la version du serveur.

Ces appels sont des lectures locales. Ils ne lancent ni modèle, traduction,
téléchargement, création d’index, sauvegarde ou mise à jour. Une recherche peut
alimenter le cache documentaire habituel. Les mesures sont faites au fil de
l’essai et ne constituent pas un instantané atomique de tous les services.

Un contrôleur inaccessible ne prouve pas que le moteur est arrêté. Les états
avant et après restent distincts ; une coupure Internet déclarée ne devient pas
une mesure réseau. Une couverture complète annoncée par le moteur ne signifie
pas que la source répond au besoin. La présence de texte dans un aperçu ne
prouve pas l’ouverture de l’original illustré.

Une erreur de lecture conserve les autres résultats. Un changement de version
détecté avant ou après le contrôle interdit de le considérer comme un essai de
la même version et demande de recharger le site. Les contrôles non réalisés
restent absents des mesures ; ils ne sont jamais comptés comme réussis.

## Retrouver ses étapes et exporter

Fermer puis rouvrir le dialogue conserve les mesures tant que la page reste
chargée. Recharger le site retrouve seulement les observations et leurs conditions,
par profil et version, dans ce navigateur ; il faut relancer les mesures. Rien ne
reprend automatiquement. Les conditions deviennent fixes après une observation
ou une mesure ; **Nouvel essai** efface ce brouillon local et repart de zéro.
Télécharger d’abord l’ancien rapport pour le conserver.

Un changement de profil arrête le contrôle en cours et ferme le dialogue.
Les réponses tardives ne remplissent pas l’essai du profil suivant. Les profils
ne sont pas une protection de confidentialité entre les personnes du réseau.
Si la mémoire du navigateur est indisponible, un message invite à exporter ;
le rapport de la page reste téléchargeable. Les brouillons ne sont pas des
sauvegardes sur le serveur et ne suivent pas automatiquement un autre navigateur.

Le fichier JSON contient version, référence des étapes, dates, connexion déclarée,
type d’appareil choisi, délais, états, titres et identifiants des sources trouvées,
choix humains et observation libre de 600 caractères au maximum. Il n’exporte
ni conversation, ni texte des documents, ni manifeste détaillé des archives,
ni identifiant du profil. Ne pas mettre de secret dans l’observation libre.
Les étapes non applicables sont comptées séparément des essais effectués.

Les tests automatisés utilisent de petits documents et des états simulés :
[bilan de livraison](../essais/2026-11-14-recette-usage-hors-ligne.md).
La coupure réelle d’Internet, Windows chez Marc et Safari sur un iPhone physique
restent des essais utilisateur, pas des résultats déduits de l’émulation.
