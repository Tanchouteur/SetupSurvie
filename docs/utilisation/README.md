# Utiliser le serveur familial

Guide du pilote, mis à jour le 12 novembre 2026. Les usages réels chez Marc et sur
Safari iPhone restent à vérifier sur place.

1. Relier l’appareil au même réseau que le serveur, puis ouvrir l’adresse ou le QR code de la page **Autre appareil**. Un Wi-Fi invité peut empêcher la connexion.
2. Ouvrir la **Bibliothèque** pour chercher et consulter les guides et archives. Elle reste disponible lorsque le moteur IA est arrêté.
3. Ouvrir l’assistant, se connecter et choisir un mode : réponse rapide, moyenne ou approfondie. Les autres modèles restent disponibles pour les comparaisons.
4. Vérifier les sources de la réponse en ouvrant les documents cités. Une réponse sans source consultée ne doit pas être présentée comme issue de la bibliothèque.

L’assistant du portail peut rechercher et lire les documents locaux, calculer et
convertir des unités. Il n’a pas implicitement Internet ni accès aux fichiers du
PC. Les documents manquants doivent être signalés. Les réponses sensibles ne
certifient ni une conduite médicale, ni la potabilité, ni la sécurité d’un ouvrage.

Le lien vers **Open WebUI** donne accès aux dossiers et conversations avancées.
Le compte est partagé avec le portail ; les historiques sont distincts. L’index
du portail et les archives Kiwix ne constituent pas un import automatique dans
les collections Open WebUI.

Depuis **Bibliothèque → Cartes hors ligne**, les cartes du Sud et de Solliès-Ville
permettent de se repérer. Elles ne calculent pas d’itinéraire et n’incluent pas
l’état actuel des chemins ni de couche altimétrique.

Pour les mots de passe, le code de secours, la dictée, les certificats et l’état
du moteur, suivre le [guide Marc](../installation/pilote-marc.md). Une pause de
l’IA doit être levée explicitement par l’administrateur ; consulter la bibliothèque
ne nécessite pas de la lever.

Pour les stocks et objets, voir le [guide de l’inventaire local](inventaire-local.md).
Le fonds recensé et ses limites sont dans la [documentation de bibliothèque](../bibliotheque/README.md).

## Ajouter des collections par thème

Avec un compte administrateur : **Données locales → Enrichir la bibliothèque**.
Choisir les thèmes, langues et plafond, puis **Chercher les contenus** pour voir
le volume proposé. **Télécharger la sélection** lance le transfert sur le PC
serveur ; fermer la page ne l’arrête pas. Le même bloc permet de suivre, mettre
en pause et reprendre. La consultation quotidienne garde le même menu.
Voir le [guide de sélection Kiwix](../bibliotheque/selection-kiwix-par-theme.md).

La version affichée dans l’en-tête vient désormais du serveur. Après une mise à
jour, recharger la page pour charger également le nouveau JavaScript.

Les [paramètres et outils cartographiques](parametres-et-cartes.md) permettent de préparer les lieux, adresses et altitudes pour le hors ligne.

Le pilote 0.1.11 ajoute les [listes de points et itinéraires hors ligne](points-et-itineraires.md), avec consultation mobile et préparation sur ordinateur.

## Ouvrir et arrêter depuis le PC Windows

À partir de l’installation 0.1.13, le Bureau propose **Ouvrir SetupSurvie** et
**Arrêter SetupSurvie**. Le serveur démarre aussi à l’ouverture de session
Windows. Ouvrir lance les services et le navigateur ; arrêter conserve les
comptes, conversations et contenus, mais coupe l’accès depuis les autres appareils.
Le PC reste allumé. Fermer uniquement le navigateur laisse le serveur disponible.
Voir le [guide des raccourcis](../installation/pilote-marc.md#installer-à-partir-du-kit)
pour désactiver le démarrage automatique ou équiper une installation existante.

## Documents et traduction

Depuis 0.1.19, **Bibliothèque → Explorer les savoir-faire** permet de choisir un
sujet, chercher ses documents et préparer une question pédagogique à envoyer.
Les [parcours de savoir-faire](../bibliotheque/savoirs-durables.md) regroupent les
besoins de Marc, sans ajout au menu principal.

Le [guide des sources et de la fiabilité](sources-et-fiabilite.md) décrit les dates
affichées, les citations réellement lues, la distinction entre faits et déductions
et les réponses que la base ne permet pas d’établir, à partir de 0.1.18.

Le [guide des documents, favoris et traductions](documents-et-traduction.md)
explique la lecture PDF en pleine page, les favoris personnels et leur recherche,
les associations aux conversations et la traduction progressive. Depuis 0.1.25,
les nouvelles traductions terminées rejoignent les documents locaux partagés ;
les anciennes restent privées jusqu’à publication explicite. **Lecture de secours**
permet de consulter les fichiers sans l’API ni l’IA.
