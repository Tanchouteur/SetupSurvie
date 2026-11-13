# Profils locaux, sans mot de passe

**Guide actuel — 0.1.29, 13 novembre 2026.** Décision de Louis : l’accès sur le
réseau familial ne doit pas dépendre d’un mot de passe ou d’un code oublié.

## Utiliser et changer de profil

À l’ouverture, le profil **Famille** fonctionne immédiatement. Toucher le nom
affiché dans le menu ou en haut du téléphone pour choisir son profil, ou créer
un profil avec un prénom ou un nom. Les cartes proposent le même choix sans
quitter leur page. Aucun identifiant, mot de passe ou code de secours à saisir.

Le profil choisi est conservé dans ce navigateur. Après effacement des cookies,
changement d’appareil ou longue absence, le choisir à nouveau dans la liste :
les conversations et favoris sont conservés sur le serveur. Les onglets du
portail et des cartes se mettent à jour lors du changement ; une requête d’un
ancien onglet est refusée si elle viserait le nouveau profil. Les traitements
déjà lancés restent associés au profil qui les a demandés.

Les profils servent à **ranger les conversations, traductions et favoris**.
Toute personne pouvant accéder à l’appareil sur le réseau peut choisir un autre
profil et en consulter les données. Ils ne protègent pas la confidentialité entre
les utilisateurs du réseau. Le profil **Famille**, ainsi que les anciens profils
administrateurs, donne accès aux réglages ; chacun peut le choisir librement.
L’application ne prouve pas à elle seule qu’une adresse n’est accessible que sur
le LAN : conserver l’installation et ses accès réseau dans le périmètre familial.

Les anciens comptes deviennent des profils avec leur identifiant interne, pour
retrouver leurs échanges et favoris. Aucun compte, historique ou mot de passe
existant n’est effacé. Si Open WebUI n’a pas encore démarré, les profils déjà
connus restent utilisables ; une ancienne identité retrouvée dans les échanges
peut temporairement s’afficher « Profil conservé… ». Actualiser la liste après
redémarrage des services, sans supprimer les bases.

## Les deux liens du menu

- **Lire les documents si le portail ne répond plus** : page simple de fichiers
  et d’accès à l’encyclopédie, indépendante de l’API et de l’IA.
- **Assistant avancé · Open WebUI** : autre interface pour les dossiers et les
  conversations avancées. Elle reprend automatiquement le profil choisi, sans
  mot de passe ; ses conversations restent distinctes de celles du portail.

Les deux liens sont séparés et décrits. Sur un écran court, le menu défile pour
les atteindre. Si l’assistant avancé était ouvert avant un changement de profil,
le recharger ou rouvrir le lien pour actualiser son espace. Son service reste
nécessaire pour ses fonctions natives et la dictée ; le portail, la lecture et
la recherche ne dépendent pas de sa connexion pour identifier le profil.

## Mettre à jour une installation

Utiliser la [mise à jour habituelle](../exploitation/mises-a-jour-et-bibliotheque-pilote.md),
qui sauvegarde les états et recrée les services Web. Recharger les pages ensuite.
Le port HTTP `3000` est désormais servi par Caddy, qui transmet le profil à
Open WebUI ; HTTPS reste sur `8444`. Ne pas exposer directement le port interne
Open WebUI : il attend les en-têtes fournis par le proxy. Les anciennes clés
internes sont conservées ; elles ne sont pas demandées aux utilisateurs.

Pour le laboratoire Bazzite uniquement, après conservation du travail local et
synchronisation du dépôt, actualiser d’abord le portail et le pilote, puis leurs
accès :

```bash
python3 scripts/lab_refresh_library.py
python3 scripts/linux_lab.py refresh-access
```

La seconde commande vérifie le montage et recrée seulement **Open WebUI et Caddy**,
sans supprimer leurs données ni démarrer l’IA. Elle coupe momentanément l’interface
avancée : terminer une réponse en cours avant cette maintenance. La pause IA
reste conservée. Une simple relance d’anciens conteneurs ne modifie pas leurs
ports ou leur configuration.

## Vérifications et limites

Les tests utilisent des états minuscules : import en lecture seule, conservation
des identifiants et historiques, favoris par profil, reprise après redémarrage,
absence d’Open WebUI, changement d’onglet et refus d’une action périmée. Les
recettes navigateur contrôlent choix/création de profil, conversations, favoris,
cartes et absence de chevauchement du menu entre 320 et 1 440 pixels.

Le vrai Caddy épinglé est testé avec des services simulés pour vérifier que les
en-têtes d’identité entrants sont retirés puis remplacés par ceux du profil.
Le fonctionnement natif utilise le mode d’en-têtes de confiance d’Open WebUI
[v0.12.5, connexion](https://github.com/open-webui/open-webui/blob/v0.12.5/backend/open_webui/routers/auths.py)
et son [écran de connexion automatique](https://github.com/open-webui/open-webui/blob/v0.12.5/src/routes/auth/+page.svelte).
Ce contrôle et les simulations ne remplacent pas un essai complet sur
l’installation cible, avec son image native et Safari sur iPhone.

Validation locale du 13 novembre 2026 : **300 tests, dont 3 COM Windows ignorés
sous Linux, sans échec** ; parcours du portail exécutés avec Chromium via
Playwright MCP, sans modèle réel. Les résultats Windows et Chromium/WebKit de
la CI sont à vérifier sur le commit de livraison.
