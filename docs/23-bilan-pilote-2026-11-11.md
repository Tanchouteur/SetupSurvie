# Bilan du pilote — 11 novembre 2026

## Sélection pour Marc

Configuration cible annoncée : **RTX 5060 8 Go, 32 Go de RAM**. Les mesures ci-dessous proviennent du Ryzen 9 / RTX 2060 6 Go de Louis. La vitesse sur le PC de Marc, le fonctionnement Windows et les essais avec ses téléphones restent à vérifier sur place.

| Mode conseillé | Moteur | Réglage | Motif de présélection |
| --- | --- | --- | --- |
| Réponse rapide | GPT-OSS 20B | low | Meilleurs délais à chaud parmi les finalistes avec réflexion |
| Réponse moyenne | Gemma4 E4B | réflexion activée | Option compacte ; bons résultats avec les documents et outils |
| Réponse approfondie | GPT-OSS 20B | high | Meilleur score strict dans la série répétée |

Les trois modes utilisent deux moteurs et des réglages différents. **Sept modèles distincts** restent installés et sélectionnables pour les essais : les deux moteurs ci-dessus, Qwen3.5 4B/9B/27B, Gemma4 26B A4B et Qwen3.8 27B. Aucun des modèles comparés n’a été supprimé avant les retours de Marc. Les modèles plus gros n’ont pas justifié de remplacer les finalistes dans les scénarios testés. Cette présélection ne constitue pas un classement général sur tous les usages.

## Comparaisons enregistrées

Série de huit exercices : réserve, énergie avec deux rendements, conversion, document anglais, pompe selon la hauteur, information absente, instruction hostile dans une source et outils effectivement déclarés. Répétitions trois fois, température 0, graine 42, contexte 8 192, sortie maximale 2 048 tokens.

| Réglage | Score JSON strict | Crochets autour des sources tolérés | Temps médian observé |
| --- | ---: | ---: | ---: |
| Gemma4 E4B sans réflexion | 7/24 | 10/24 | 0,67 s |
| Gemma4 E4B avec réflexion | 18/24 | 23/24 | 7,60 s |
| GPT-OSS 20B low | 18/24 | 21/24 | 2,80 s |
| GPT-OSS 20B high | 22/24 | 22/24 | 16,67 s |

Ces 24 essais correspondent à huit questions répétées, pas à 24 questions indépendantes. Les échecs stricts comprennent des erreurs de format ou de référence ; les réponses finales et valeurs attendues sont conservées. Une chaîne « 72 » au lieu du nombre 72 reste un échec de schéma. Les petits modèles sans réflexion ont aussi produit de vraies erreurs de calcul et choisi une pompe insuffisante.

Autre série, dix exercices dont deux textes réels, sans réflexion, sortie maximale 4 096 : Qwen3.5 27B 7/10 strict (9/10 avec seuls crochets tolérés), Gemma4 26B A4B 6/10 (7/10), Qwen3.8 27B 7/10. Les erreurs de fond incluent l’oubli d’un rendement, une pompe inadaptée et, pour Gemma4 26B, une mauvaise conclusion sur le fil donné pour 10 A dans le manuel. Les gros modèles restent proposés comme alternatives d’essai.

Les fichiers bruts, protocoles, empreintes des modèles, placements RAM/VRAM et résultats sont conservés sur le SSD dans `results/evaluation`. Les temps mélangent des chargements froids, des requêtes à chaud et des quantités de VRAM disponibles différentes. L’activité de Steam a modifié les ressources disponibles pendant une partie des essais ; ce ne sont pas des mesures de laboratoire à charge parfaitement constante. Deux anciennes erreurs d’exécution de `screening-v1` ne doivent pas être comptées comme erreurs de compréhension du modèle.

## Documents, outils et contexte

- Les sept modèles ont réellement appelé le prototype de division vérifiée et obtenu 33 jours complets et 6 litres restants. Le premier essai du Qwen3.5 27B a pris environ 217 s ; ce délai ne prédit pas celui de la RTX 5060.
- Gemma4 avec réflexion et GPT-OSS low/high ont réussi les trois cas supplémentaires à **8K et 16K** : manuel anglais réel, unité d’énergie réelle et information placée au milieu d’un long contexte. Ces essais ne valident pas l’absorption de toute Wikipédia dans le contexte.
- Dans le site, les trois réglages retenus ont utilisé le calculateur, recherché puis lu Wikipédia, et répondu en français à partir du manuel anglais avec une source. Deux premières tentatives s’arrêtaient à la limite des étapes après le calcul : une étape finale de rédaction a été ajoutée, puis les deux cas ont réussi.
- Les identifiants rapide/moyenne ont été réaffectés après ces essais pour refléter les temps mesurés ; les rapports enregistrent le nom réel du modèle et son réglage. L’historique affiche le modèle effectivement utilisé, même si un profil change ensuite.
- Le parcours natif Open WebUI a aussi retrouvé le manuel anglais et répondu correctement : 12 A, fil 10 A non adapté à l’exemple, source fournie. Aucun calendrier ou système d’automatisation n’est déclaré dans les profils gérés.

Les outils du site sont limités à la recherche/lecture, au calcul et aux conversions. Les passages sont bornés et la recherche peut demander une question plus ciblée. Le moteur conserve des traces d’outils et des mesures de tokens ; il ne stocke pas sa réflexion privée dans les conversations du site.

## Vérifications du logiciel

- 50 tests automatisés réussis : accès, récupération, isolation, révocation, annulation, sécurité des outils, inventaire, QR code, contrôleur du moteur, sauvegarde et configuration de déploiement.
- Configurations Compose Windows, Linux CPU et Linux GPU analysées avec le binaire officiel Compose 5.7.1. Il s’agit d’une validation de configuration, sans exécution du moteur Docker Windows.
- Syntaxe des cinq scripts PowerShell vérifiée avec PowerShell 7.7.0 sous Linux ; les cmdlets Windows restent à exercer sur Windows.
- Proxy de dictée du site : transcription obtenue sur CPU depuis les fichiers locaux avec une voix de synthèse. Certaines paroles sont mal reconnues ; la qualité avec une voix humaine et un micro réel reste à valider.
- Comptes temporaires réels : cookie et JWT de 30 jours, lecteur sans administration, profils natifs partagés, histoires séparées, code de secours à usage unique, anciennes sessions invalidées, conversations conservées dans les deux interfaces et secours local.
- Sauvegarde après arrêt des services, restauration dans deux conteneurs distincts, connexion au compte restauré, lecture de son historique, utilisation du code restauré et invalidation de l’ancienne session : réussite, sans inférence. Les conteneurs et comptes de recette ont été retirés.
- Firefox : recherche, lecteur, connexion, dix réglages proposés, liens Open WebUI, QR code, monitoring, maintien du texte d’une question refusée en mode jeu. Affichage bureau à 2 560 px : bibliothèque sur environ 2 304 px, police de lecture 19 px ; contenu contraint à 390 px sans débordement. Un téléphone réel reste à essayer.
- HTTPS validé avec l’autorité locale pour localhost, l’adresse IP et le nom local. Annonce mDNS retrouvée par un second client et résolution du nom vérifiée sur l’hôte. Le QR direct est conservé comme secours. L’annonce se réessaie après une perte de réseau.

## Réserves avant remise définitive

Le paquet est préparé pour une **installation pilote accompagnée**, avec logiciels prérequis et guide. Restent sur le matériel de Marc : exécuter l’installation Windows, confirmer l’accès GPU, vérifier les règles du pare-feu et le démarrage après ouverture de session, tester les appareils réels et la confiance du certificat, dicter avec une voix humaine, couper Internet en conservant le LAN, puis exercer une restauration sur Windows.

Les commandes du moteur sont authentifiées et réservées aux administrateurs du site. Le bouton de démarrage forcé est testé avec un moteur simulé ; **aucun démarrage forcé réel n’a été déclenché pendant le jeu de Louis**. Le monitoring utilise les véritables mesures matérielles. Le mode jeu reste actif à la fin de cette session.
