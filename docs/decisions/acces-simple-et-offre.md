# Connexion simple et direction du produit

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

## Hypothèses commerciales à tester

- Présenter d’abord les usages concrets : comprendre une réparation, consulter un manuel, apprendre, préparer une réserve et vérifier un calcul. La préparation aux coupures constitue un bénéfice supplémentaire mesurable.
- Montrer ce qui est livré : collections exactes et datées, langues, modèle utilisé, temps d’attente, capacité de fonctionnement hors ligne et procédure de récupération.
- Soigner les premières minutes : QR code visible, peu de choix, aide courte, source ouvrable et état explicite lorsque l’IA est arrêtée. Les noms techniques restent à côté des choix pour permettre les essais.
- Vendre éventuellement la préparation, l’installation, le matériel et les mises à jour documentaires ; préserver l’usage du contenu déjà livré sans abonnement obligatoire. Ce sont des hypothèses d’offre, aucun tarif ni niveau de demande n’est encore validé.
- Prévoir des mises à jour par support local et une sauvegarde récupérable. Documenter les licences de chaque contenu avant une distribution commerciale.

Recette avec Marc et quelques personnes novices : noter le temps pour connecter un téléphone, trouver une information, comprendre une réponse et rouvrir sa source. Observer où ils hésitent avant de demander leur avis. Leur faire comparer quelques modèles sur leurs propres questions, sans leur annoncer lequel serait « le meilleur ».
