# Comprendre les essais refusés avant lancement

**Bilan du candidat 0.30.0 — 16 novembre 2026.** Suite aux refus intermittents
signalés oralement par Louis pendant les essais Windows 0.25.0. Les cinq rapports
ne permettent pas de reconstruire toutes les tentatives antérieures ; cette
livraison fournit les observations qui manquaient, sans annoncer leur cause.

Les contrôles mémoire, comparatif IA, performances et traduction de 40 pages
conservent désormais leurs refus HTTP 409/429/503 sur un mode connu, même quand
aucun travail n’a pu être créé. Leurs erreurs d’origine et leur code HTTP restent
identiques. Le diagnostic facultatif ne doit pas remplacer un refus s’il échoue.
L’enregistrement est borné aux vingt derniers refus dans un fichier privé.

Chaque observation distingue : modèle/mode/contexte choisis, type d’essai et
heure/version ; état du contrôleur, commande start/stop en cours et marge RAM/VRAM
observée ; réponses indépendantes des API locales version, modèles chargés et
modèles installés. Un contrôleur qui annonce hors ligne peut ainsi être comparé
à l’API moteur qui répond. Aucun appel de chargement, téléchargement, arrêt ou
inférence n’est envoyé par le diagnostic. Les mesures mémoire portent sur le PC
entier et sont prises après le refus, pas exactement à l’instant de sa décision.

Le contrôleur hôte conserve aussi un résumé borné de sa dernière commande :
action, cible Windows/Linux, début/fin, durée, étape et catégorie d’échec. Les
étapes sont garde de transfert, commande au service, attente API et terminé.
Aucun message d’exception libre, chemin, environnement, jeton ou log brut n’est
conservé dans cet export. Les anciens contrôleurs peuvent omettre ce champ,
explicitement non mesuré jusqu’à leur mise à jour.

Depuis **Paramètres → Tests et diagnostics → Mémoire et contexte**, utiliser
**Télécharger le diagnostic de démarrage** si un lancement d’essai refuse le
moteur. Le fichier associe les refus enregistrés à une nouvelle observation
actuelle, sans les confondre. Son nom contient type, version, date et heure.
Ouvrir le sous-menu ne lance pas ce contrôle ni une inférence.

## Vérifications

**47 tests ciblés** réussissent sur le runner CPU : appels GET strictement bornés,
champs autorisés, absence de textes privés, rétention de vingt refus, erreur
facultative qui ne masque pas la réponse, accès Famille et état hôte de commande
réussie/échouée. Aucun modèle ou corpus n’est téléchargé. Les essais navigateur,
la suite et la CI finale suivent. Aucun nouveau diagnostic physique de Marc
n’est présenté comme exécuté.

Version **y**, fonctionnalité de diagnostic compatible et données séparées ;
aucune migration, modification des modèles ou changement de marge de mémoire.
Les réglages et le mode jeu restent respectés. Référence actuelle :
[mesures et mémoire](../utilisation/mesurer-assistant-et-memoire.md).

Les recettes ciblées passent sur **Chromium et WebKit** : neuf contrôles du
nouvel export et vingt-huit des mesures/calibration existantes par navigateur.
Le refus et l’état actuel sont bien deux objets distincts dans le fichier ;
aucun POST n’est envoyé par le nouveau bouton. Le nom de rapport contient
version/date/heure et l’interface reste contenue à 320, 390 et 1366 px.

Le refus garde aussi une catégorie lorsqu’il correspond exactement à un message
connu (pause, pression RAM/VRAM, activité concurrente, matériel ou moteur
indisponible). Un message inconnu reste non catégorisé ; son texte libre n’est
pas copié. Le test vérifie que ces catégories restent distinctes des états
observés ensuite. Aucune interprétation d’un log n’est utilisée pour les deviner.

Le premier CI Windows révèle une hypothèse POSIX dans le nouveau test : comparer
`stat().st_mode` à 0600 ne mesure pas les ACL de Windows. Le test vérifie désormais
sur tous les systèmes l’écriture privée dans le dossier d’état, puis les bits
0600 sur POSIX uniquement. Le contrôle d’accès Famille et le filtrage des champs
restent vérifiés sous Windows aussi. Aucune validation d’ACL Windows n’est
revendiquée, ni modification globale des permissions de l’installation.
