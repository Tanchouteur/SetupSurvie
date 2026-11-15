# Audit de fin de la première version du moteur

**État vérifié le 15 novembre 2026, logiciel 0.14.0.** Base publiée : `a390b9c`.
**Complément après réception du R2 0.14.0 :** ce rapport est désormais analysé
dans le [bilan et correctif 0.14.1](2026-11-15-rapport-0140-et-traitement-progressif.md).
Il lève l’attente de mesure 0.13/0.14 décrite dans l’audit initial ci-dessous :
premiers documents à 311 ms de médiane, fin à 36,24 s, 31 recherches couvrant
toutes leurs archives sans échec, aucun avis humain. La fiabilité finale n’est
toujours pas déclarée acquise ; correction du traitement et mesures suivantes
restent distinctes de cette réception. Le tableau conserve la preuve initiale.
Le [complément 0.14.2](2026-11-15-budget-reformulations.md) corrige ensuite le
plafond de variantes du flux long ; le prochain R2 porte sur cette version,
avec les optimisations 0.14.1 incluses.
Cet audit ne déclare pas l’objectif terminé. Il confronte les critères de recherche
du [plan](../decisions/plan-ameliorations-marc.md) aux preuves disponibles, après
intégration des outils des deux agents. Aucun nouveau modèle ni corpus n’est lancé.

## Preuves et critères encore ouverts

| Critère | Preuve disponible | Conclusion actuelle |
| --- | --- | --- |
| Archives réellement préparées | R1 de Marc 0.12.0 : 135 examinées sans erreur, 120 index natifs compatibles, 15 compléments et 3 238 articles locaux | Préparation confirmée pour cet état du fonds ; un nouvel ajout, une pause/reprise et une édition changée restent à vérifier sur le PC cible |
| Demandes naturelles, variantes et filtres | Référence de 32 cas, dont huit de vérification séparés ; `test_search_reference.py` vérifie source attendue et filtre adapté sur documents fictifs | Contrat testé, sans preuve du classement de tout le fonds de Marc |
| Recherche et lecture Kiwix | 54 contrôles natifs sur cinq petites archives : mots surlignés conservés, titres et plein texte réunis, caractères spéciaux, alias et ouverture des sources ; 28 contrôles sur 135 minuscules archives | Mécanismes corrigés et éprouvés ; leur taille ne représente pas 755 Go |
| Délais et couverture sur le fonds réel | Dernier R2 transmis : 0.12.0, 32 recherches partielles, 31 échéances atteintes, aucun avis humain enregistré | Le gain des corrections 0.13/0.14 n’est pas encore mesuré sur ce fonds ; nouveau R2 requis |
| Résultats progressifs, arrêt et navigation | Chromium local : 452 assertions ciblées ; quatre recettes WebKit isolées : 275, dont recherche 50 et flux 18 | Scénarios ciblés réussis ; la campagne WebKit enchaînée et Safari iPhone réel ne sont pas déclarés validés |
| Réutilisation sans figer les pannes | Cache de réponses valides, état des ZIM/index dans les clés, quota ajustable ; tests de remplacement, panne, annulation, SQLite Windows et réutilisation native disque | Contrats testés ; effet à chaud et pression CPU/disque/RAM du PC réel encore à mesurer |
| Assistant et sources | Moteur documentaire commun, relecture de sources et mesures par phase ; outils et orchestration testés sans LLM réel | Nouveau R4 volontaire nécessaire pour la rapidité et les citations d’un modèle réel ; aucun démarrage en mode jeu n’est imposé |
| Compatibilité et conservation | Schéma 1, images inchangées, code moteur 0.13.1 conservé ; 561 tests locaux, trois ignorés ; paquets 0.13.1 et 0.14.0 déballés et comparés | Preuves de développement et de paquet ; Windows réel des deux nouveaux outils, mise à jour et usage hors ligne chez Marc restent distincts |
| Étude de traduction et acquisition de sous-titres | [Étude technique](../decisions/videos-locales-et-recherche.md), sources officielles, ordre de préparation et [protocole par vidéo](protocole-sous-titres-videos.md) ; inventaire local livré | Étude minimale demandée réalisée ; acquisition, transcription, traduction et validation de chaque vraie vidéo restent à exécuter |
| Traçabilité depuis 0.2.0 | [Journal](journal-recherche-depuis-020.md), guides courants et bilans datés | Le résumé final peut distinguer livré, testé et encore attendu ; il ne doit pas transformer les fixtures en essais réels |

Les preuves détaillées et les limites sont conservées dans les bilans
[0.13.0](2026-11-14-recherche-0120-et-travail-nocturne.md),
[0.13.1](2026-11-15-classement-titres-et-intention.md) et
[0.14.0](2026-11-15-integration-outils-validation-videos.md).
Le dernier passage GitHub de l’intégration n’a exécuté aucun job à cause d’une
restriction du compte ; il ne vaut ni réussite ni test de code exécuté en échec.

## Validation demandée par l’audit initial

Le nouveau R2 ci-dessus répond à la demande de mesure 0.14.0. Pour le prochain
passage, appliquer **0.14.2** et conserver les avis humains ; les étapes suivantes
décrivent la demande initiale, pas un rapport encore manquant en 0.14.0.

1. Appliquer la mise à jour habituelle et vérifier **0.14.0** dans le portail.
2. Avec Famille : **Mon appareil → Paramètres → Entretien et diagnostics →
   Vérifier la recherche → Contrôle complet · 32 recherches**, sans IA.
   Les 135 archives déjà examinées n’ont pas à être réextraites pour cette seule
   mise à jour. La préparation d’index est une autre commande, située dans
   **Bibliothèque et préparations**, à utiliser si les contenus ont changé.
3. Ouvrir au minimum les résultats feu, eau, générateur et vélo ; ajouter solaire
   et semences si possible. Choisir le résultat utile, aucun ou à vérifier selon
   ce qui a effectivement été lu. Un titre pertinent ne suffit pas.
4. Télécharger le rapport avant fermeture. Il doit conserver première réception,
   fin, couverture, erreurs et avis humains. Si une source échoue à l’ouverture,
   conserver son titre et l’adresse complète du portail après le clic.
5. Répéter les demandes problématiques pour observer le réemploi des réponses.
   Si nécessaire, utiliser ensuite le [diagnostic d’une archive](../exploitation/diagnostic-performances-kiwix.md),
   sans supprimer les caches ni annoncer un départ froid non établi.

Les [recettes progressives](recettes-progressives-marc.md) gardent aussi R4 et R7
pour les réponses IA et l’usage réellement hors ligne. L’agent ne dispose pas
d’un accès validé au PC de Marc ; TeamViewer détenu par Louis ne constitue pas
un accès de développement. Une fois les mesures reçues, comparer aux rapports
précédents et corriger les anomalies reproduites avant de clore l’objectif.

La prochaine modification de classement, de budget ou de matériel doit répondre
à une anomalie reproduite ou à ces mesures. En attendant, aucun nouveau résultat
réel ni fin de l’objectif ne sont revendiqués par cet audit.
