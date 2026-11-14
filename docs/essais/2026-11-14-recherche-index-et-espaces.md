# Rapport de Marc et première mise en œuvre du plan

**Bilan de développement — 14 novembre 2026, 0.3.0.** Pas de déploiement autonome
sur le Windows de Marc, pas d’inférence réelle ni de corpus téléchargé dans le
runner. Le fichier joint utilisateur a été lu ; il reste hors de Git.

## Rapport reçu

Rapport créé le 14 novembre à 11:49:09 UTC, version **0.2.0**, huit recherches,
135 collections sélectionnées globalement dont 64 n’annoncent pas d’index texte.

- « Faire du feu » : **9,192 s**, retrouve Production de feu (Wikipédia FR),
  Fire Making et Guide de survie/Faire du feu (Wikilivres). Ces pages sont donc
  présentes et trouvables ; leur contenu n’a pas été relu dans ce rapport.
- « Allumer un feu » : **10,184 s**, Wikilivres en tête, mais la recherche par
  titre n’a pas commencé et 58 collections ne sont pas interrogées.
- Recherche limitée à Wikipédia : **1,626 s**, trois collections interrogées,
  avec des catégories et un titre potentiellement ambigu parmi les résultats.
- Six recherches atteignent environ dix secondes ; les titres sont souvent
  annulés avant d’avoir un créneau. Les résultats globaux restent partiels.
- Générateur : variantes `/hr`, `/uk`, `/he` présentées comme anglaises ; eau :
  directive et références générales trop haut ; vélo : guide de générateur
  devant la réparation ; graines : conservation de fruits encore présente.

## Changement livré

- Titres sur une file séparée ; collections techniques courantes prioritaires.
  Entre trois et douze requêtes texte simultanées selon les CPU, deux recherches
  par titre séparées ; budget global Kiwix six secondes, appel texte trois
  secondes, titre deux secondes. Les comptes de couverture restent explicites.
- Intention réparation, conservation, purification ou construction conservée
  pour classer les candidats. Pénalisation des pages de navigation ; langue des
  variantes Appropedia distinguée et regroupement des variantes d’un article.
- Index texte SQLite des ZIM sans index Kiwix réel, lecteur libzim 3.13.1 dans
  un environnement optionnel séparé ; requêtes SQLite sans dépendance libzim
  dans le pilote. Extraction multiprocessus, reprise, publication par archive,
  marge disque, commandes depuis le site. Les index locaux sont interrogés en
  parallèle de Kiwix ; leurs recherches disposent d’un budget de trois secondes.
- Deux périmètres documentaires et recherche globale, aussi pour l’assistant.
  Classement automatique simple au niveau des résultats, non qualification
  éditoriale de tous les articles. Les collections restent ouvrables directement.
- Contexte conversationnel par défaut **16 384 tokens**, réglage par modèle
  8k/16k/32k/64k dans Famille, budgets internes d’historique et d’extraits adaptés.
  Aucune calibration automatique de la RAM/VRAM ni performance LLM revendiquée.

**Version 0.3.0** : incrément mineur pour l’indexation optionnelle et les nouveaux
périmètres, fonctions compatibles. Schéma existant 1 conservé, index séparés
reconstruisibles et réglages dans la table existante. Images tierces inchangées.

## Vérifications et limites

Petites archives générées : découverte d’un mot seulement dans le corps, reprise
au curseur 64, ancien index accessible pendant une interruption, filtrage de
collection et fusion même si Kiwix est arrêté. Régressions du rapport sur données
fictives : réparation de vélo, graines, potabilisation, catégories et titres non
bloqués par les requêtes lentes. Tests API des droits et des réglages de contexte.
Kiwix 3.8.1 réel vérifié sur cinq archives générées, environ 280 Ko, sans corpus.

Le volume de l’index, la durée, la consommation mémoire et les nouveaux délais
chez Marc restent à relever. Refaire **Vérifier la recherche** avant/après la
création des index. La procédure réelle Windows d’installation de l’outil et
l’intégralité du fonds ne sont pas validées par les fixtures ou la CI.

Les sous-titres, la traduction de lecture intégrée, le livre réel de 500 pages,
la qualification des tutoriels, les variantes encore mal nommées et la calibration
matérielle restent suivis dans le [plan actuel](../decisions/plan-ameliorations-marc.md).
