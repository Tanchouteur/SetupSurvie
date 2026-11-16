# Essai de traduction de 40 pages et sous-menu des tests

**Bilan candidat 0.25.0 — 16 novembre 2026.** Nouvelle fonction compatible et
organisation des vérifications, donc version mineure. Guides actuels :
[test de traduction](../exploitation/test-traduction-40-pages.md) et
[paramètres](../utilisation/parametres-et-appareil.md).

## Mesure réelle du parcours de traduction

Le serveur génère un PDF de 40 pages/9 600 mots, l’extrait avec la même fonction
que les PDF de la bibliothèque, conserve un instantané et traduit les passages
avec le moteur ordinaire et ses contrôles. Le récit est fictif, récurrent dans
sa structure et dépourvu de schémas : son nombre de pages n’en fait pas un manuel
technique représentatif. Le PDF d’essai mesure 79 531 octets, 60 467 caractères
extraits et 40 passages ; le rapport conserve ces volumes et empreintes.

Une file distincte conserve chaque passage terminé, les tentatives, les contrôles
refusés et les sessions de pause/reprise. Elle partage le verrou de l’assistant,
cède à son usage ordinaire, respecte le mode jeu et ne reprend pas seule après
redémarrage. Une interruption rejoint l’extraction avant de quitter. Chaque
session peut durer huit heures, avec reprise explicite pour la suite. L’essai ne
crée aucune conversation ou traduction publiée dans la bibliothèque.

Les ressources sont relevées toutes les cinq secondes, avec contexte demandé,
transmis et observé, tokens, chargement, premier texte et génération. Le rapport
numérique exclut les textes. Le temps actif inclut les sessions de travail, le
temps écoulé inclut aussi les pauses. Les comptes par page cumulent les tentatives.
Le PDF, les traductions et les propositions refusées restent dans l’état privé.
Le moteur documentaire de traduction a aussi reçu les phases de mesure et la
lecture du contexte après génération qui manquaient à son observation précédente.

## Tests simulés et navigateur

Les tests Python utilisent le vrai PDF de 40 pages, l’extraction et la reprise,
avec modèle et compteurs simulés : volume, confidentialité, aucune publication,
40 pages terminées, pause/reprise sans retraduire les passages acquis, contrôle
de qualité bloquant, redémarrage, PDF modifié, mode jeu pendant génération et API
réservée à Famille. Les anciennes recettes de traduction et PDF restent exécutées.

Dix-neuf contrôles navigateur vérifient le menu, les cinq rubriques, les liens
directs, aucune inférence à l’ouverture, lancement unique, pause/reprise avec
rechargement, fin des 40 pages, export numérique, contexte, retour navigateur
et largeurs 1366/390/320. Le vrai moteur est testé séparément sur le R7. Les
anciennes recettes sont adaptées au déplacement de leurs commandes, en conservant
leurs assertions fonctionnelles. Les panneaux et identifiants existants sont
déplacés, pas clonés ; les brouillons et l’historique restent ceux du routeur.

## Essai R7 complet

Le R7 avait environ 9 492 Mio de VRAM libres ; une autre tâche occupait le reste
et n’a pas été arrêtée. Gemma `gemma4:e4b`, Ollama natif 0.40.14, contexte 16k,
24 couches GPU, six threads, sortie 4 096 tokens, réserve 1 536 Mio et maintien
quinze secondes. Aucun poids téléchargé ni service modifié. Les ressources natives
sont appelées directement ; le pont HTTP est vérifié séparément.

Le premier essai `report-gemma4-40-pages.json` s’arrête avant la première page :
la garde de la recette réservait à nouveau toute l’allocation prévue pendant
le chargement déjà commencé. Ce refus ne prouve pas un manque de VRAM. L’estimation
complète est maintenant contrôlée au lancement ; la marge réellement libre et
les modèles tiers restent vérifiés pendant l’essai. Une exception inattendue
conserve aussi désormais le statut échoué de la tentative, au lieu de « en cours ».

Rejeu `report-gemma4-40-pages-v2.json` :

| Observation | Valeur |
| --- | ---: |
| Pages / passages terminés | 40 / 40 |
| Temps actif total | 514 224 ms, soit 8 min 34 s |
| Mots source traduits par minute active | 1 120 |
| Durée médiane par page | 12 636,5 ms |
| Durée maximale par page | 18 541 ms |
| Appels au modèle | 40 |
| Tokens d’entrée / sortie annoncés | 19 542 / 14 960 |
| Chargement / génération cumulés annoncés | 5 440 / 478 377 ms |
| Échantillons matériels | 103 |
| RAM disponible minimale observée | environ 20,5 Gio |
| CPU total médian observé | environ 45,5 % |
| VRAM totale maximale observée, autres tâches incluses | environ 10,1 Gio |

Les quarante contrôles techniques passent sans avertissement. Relecture ciblée
des pages 1, 20 et 40 : récit, couleurs, personnages et références chiffrées
conservés ; la tournure française relative à l’urgence est moins précise que
l’original, et « page marker » devient « marque-page ». Ce contrôle limité n’est
donc pas une validation intégrale de fidélité ni d’un vocabulaire technique.
Les sorties fictives restent dans un fichier privé distinct pour relecture.

Empreinte Python du rejeu :
`bed8bdf1e2eab3e93559c2a30400b513917f95f65f5e1535709a3dbdc7d994f4`.
Ces performances ne sont pas celles de GPT‑OSS ou du PC Windows de Marc. La
structure récurrente du récit, le cache et l’autre activité GPU font partie des
conditions de mesure, pas d’un benchmark matériel contrôlé.

## Complément après le rapport Windows 0.24.0

Le [rapport de Marc](2026-11-16-rapport-performances-marc-0240.md) montre des
recherches partielles sans échec d'archive. Le diagnostic exporte désormais les
états et compteurs autorisés des vidéos, du catalogue, des classements et de
l'index local. Les champs absents ne deviennent pas des zéros ; chemins, titres
et erreurs libres de ces composants restent exclus. La fin du diagnostic signale
aussi une couverture limitée si une recherche classique est partielle.
Quatorze tests ciblés passent, dont les nouveaux cas de couverture et de confidentialité.

## Recherche vide pendant l'attente

Louis demande de ne pas confondre absence provisoire et résultat final. Le message
commence désormais par « Recherche en cours — aucun résultat pour le moment ».
La fin complète, partielle, l'arrêt et l'erreur retirent tous l'attente, dans le
statut et dans la liste vide. Les résultats reçus, passages ouverts et navigation
au clavier restent conservés. Trente-huit contrôles par Chromium et WebKit passent
contre le petit flux HTTP de test, dont les quatre fins sans résultat. Aucun délai
ou résultat du fonds réel n'est déduit de cette fixture.

Le contrôle WebKit CI a aussi révélé que le texte interne des options natives
débordait de leurs listes à 320 pixels, alors que leurs rectangles visibles
tenaient dans la page. Le correctif borne ce contenu dans les seuls libellés
des tests et conserve un indicateur de focus à l'intérieur des listes. Le
débordement global de la page n'est pas masqué ; le contrôle complet reste requis.

## Suite

La demande vidéo est précisée : les nouveaux médias de Marc seront des MP4
YouTube seuls. La traduction de pistes présentes 0.24.0 est intermédiaire ;
transcription des MP4, récupération de pistes, vidéos/pistes des ZIM et relecture
du fonds restent ouvertes. Le test de 40 pages ne clôt pas ces besoins ni le
glossaire et la fidélité d’un vrai livre long. CI et reçu de paquet suivent.
