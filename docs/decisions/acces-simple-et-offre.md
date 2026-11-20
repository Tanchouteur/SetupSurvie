# Connexion simple et direction du produit

## Offre de PC préinstallé — précision de Louis du 16 novembre 2026

**Direction commerciale confirmée, offre encore à qualifier.** Le code propre de
SetupSurvie n'est pas publié en open source. Les clients visés achètent un **PC
avec SetupSurvie déjà installé**. Le produit à éprouver est donc la machine
préparée et son usage familial ; son utilisateur n'a pas à installer et assembler
les services. Les composants et contenus tiers conservent leurs propres licences.
Cette précision ne vaut ni lancement commercial vérifié, ni prix, ni engagement
de garantie, d'abonnement ou d'assistance défini.

Deux parcours guident les choix :

- **Avant livraison :** préparer une configuration connue, acquérir les contenus
  et modèles choisis, vérifier leurs éditions et états, tester la machine et
  conserver une référence de ce qui a réellement été livré. Les outils de
  téléchargement et de préparation servent d'abord à ce travail ; leur présence
  ne doit pas en faire une étape obligatoire chez le client.
- **Chez le client :** brancher, accéder depuis un appareil du réseau et utiliser
  les fonctions préparées, avec des explications simples sur ce qui reste à
  configurer. Réseau, certificats, reprise après coupure, mises à jour, sauvegarde
  et restauration doivent être qualifiés sur la configuration vendue. Ne pas
  annoncer un démarrage sans aucune configuration avant recette réelle.

La priorité recommandée est la cohérence de la machine livrée, sa simplicité,
la fiabilité et le secours. Dans l'[étude NOMAD](apports-nomad.md), la préparation
guidée et le contrôle des liens relèvent surtout de l'atelier et de l'entretien ;
Kolibri pourrait enrichir l'usage familial. Ce classement ne lance aucun lot et
ne remplace pas les deux objectifs actuels de simplification et de fiabilité.
Les modalités de suivi et d'assistance restent à définir avec Louis et Marc.

**Actualisation 0.1.29, 13 novembre 2026 :** Louis retient les profils locaux sans
mot de passe ni code de secours. Le [guide actuel](../utilisation/profils-locaux.md)
prévaut sur les propositions ou descriptions de connexion conservées ci-dessous.

> Guide de référence du pilote — documentation réorganisée le 11 novembre 2026. Les essais Windows chez Marc et sur téléphone restent à réaliser lorsqu’ils sont indiqués comme non validés.

## Parcours visé

La promesse à éprouver avec Marc : **brancher, scanner, trouver une information et ouvrir sa source, même sans Internet**. L’IA devient une aide pour comprendre les documents. La bibliothèque reste une fonction utile lorsque le moteur est arrêté ou occupé.

Pour le pilote, la page **Autre appareil** fournit un QR code direct, une adresse facile à retenir, une adresse HTTPS et une fiche imprimable. Le nom est annoncé depuis le vrai PC hôte, car le multicast d’un conteneur Docker ne suffit pas pour découvrir le serveur sur le Wi-Fi domestique.

Exemple de préparation Windows, avec adresse IPv4 réservée dans le routeur :

```powershell
.\scripts\survie.ps1 --work-dir D:\SetupSurvie\prive configure --lan --lan-host 192.168.1.50 --name survie
.\scripts\survie.ps1 --work-dir D:\SetupSurvie\prive up
```

Nom demandé : `http://survie.local:8080`. Les clients peuvent le garder en favori ou en raccourci sur l’écran d’accueil. Le QR code pointe directement vers l’adresse du PC : aucun besoin de retenir les nombres et aucune dépendance au fonctionnement du nom local. La fiche publique ne contient aucun mot de passe.

La découverte utilise mDNS et le domaine spécial `.local`. Elle dépend du client et du réseau : le Wi-Fi invité, le filtrage du multicast ou certains environnements de navigateur peuvent empêcher la résolution. Les accès directs restent nécessaires. L’annonce se réessaie après une coupure et suit l’adresse de l’interface active ; réserver l’IP évite aussi de rendre une fiche papier obsolète. [Norme mDNS](https://www.rfc-editor.org/info/rfc6762/).

La lecture publique par HTTP est immédiatement accessible. Pour la dictée et les connexions protégées, l’opérateur prépare une fois la confiance du certificat local sur les appareils concernés ; voir le [guide Marc](../installation/pilote-marc.md). Il ne faut pas promettre un HTTPS local sans configuration sur tous les téléphones.

## Piste pour une offre plus prévisible

Une boîte accompagnée d’un petit routeur ou point d’accès permettrait de maîtriser le Wi-Fi, les adresses et le DNS local. Le client scannerait une fiche Wi-Fi puis ouvrirait une adresse courte servie par le routeur, par exemple `survie.home.arpa`. `home.arpa` est réservé aux réseaux domestiques ; le routeur doit réellement fournir les enregistrements DNS correspondants. Cela éviterait de dépendre du support mDNS de chaque client. [Domaine domestique normalisé](https://www.rfc-editor.org/info/rfc8375/).

Cette architecture reste une piste à prototyper, avec son coût, sa consommation et sa maintenance. Elle ne résout pas à elle seule la confiance HTTPS. Un portail d’accueil Wi-Fi pourrait guider la connexion, tout en permettant d’ouvrir ensuite le navigateur normal pour les fonctions qui l’exigent.

## Périmètre V1 décidé par Louis le 20 novembre 2026

Pour cette V1, les amis de Louis achèteront leur matériel et recevront
SetupSurvie gratuitement. La machine de référence fonctionne sous Linux.
La préparation prévoit un bureau léger et Firefox avec son traducteur et
les langues choisies déjà téléchargées. Le bureau et les langues restent
à choisir. Ce périmètre remplace l’hypothèse de vente du PC préinstallé
pour la V1. Les conditions propres aux composants et contenus tiers
restent applicables à leur partage.

## Hypothèses commerciales à tester

- Présenter d’abord les usages concrets : comprendre une réparation, consulter un manuel, apprendre, préparer une réserve et vérifier un calcul. La préparation aux coupures constitue un bénéfice supplémentaire mesurable.
- Montrer ce qui est livré : collections exactes et datées, langues, modèle utilisé, temps d’attente, capacité de fonctionnement hors ligne et procédure de récupération.
- Soigner les premières minutes : QR code visible, peu de choix, aide courte, source ouvrable et état explicite lorsque l’IA est arrêtée. Les noms techniques restent à côté des choix pour permettre les essais.
- Le modèle de vente du PC préinstallé est confirmé par Louis le 16 novembre 2026. Les prix, les prestations complémentaires et leur financement restent à définir et à tester ; le souhait historique de préserver l'usage du contenu livré sans abonnement obligatoire reste une hypothèse d'offre, sans formule commerciale validée.
- Prévoir des mises à jour par support local et une sauvegarde récupérable. Documenter les licences de chaque contenu avant une distribution commerciale.

Recette avec Marc et quelques personnes novices : noter le temps pour connecter un téléphone, trouver une information, comprendre une réponse et rouvrir sa source. Observer où ils hésitent avant de demander leur avis. Leur faire comparer quelques modèles sur leurs propres questions, sans leur annoncer lequel serait « le meilleur ».
