# Fiabiliser la recherche et l’utilité de la bibliothèque

**Chantier actuel — 14 novembre 2026.** Louis demande de travailler tous les
points du retour de Marc et de fiabiliser en priorité le cœur de recherche.
Le [plan retenu et son suivi](plan-ameliorations-marc.md) porte désormais le programme L1–L9, décisions, critères de fin et pistes écartées. Les [recettes progressives](../essais/recettes-progressives-marc.md) précisent les rapports à demander et les blocages à annoncer. Le [compte rendu](../essais/2026-11-14-retour-experience-marc.md) conserve les
observations ; ce suivi distingue réalisation et validations manquantes.

## État actuel pour la fin de l’objectif — 16 novembre 2026, 0.33.1

L’objectif actif reste l’utilité réelle de l’assistant et une première version
fiable de recherche, puis les traductions et sous-titres. Une fonction codée ou
un CI vert ne suffit pas à qualifier tout le fonds réel. Le tableau historique
plus bas conserve le point de départ du 14 novembre ; le [plan L1–L9](plan-ameliorations-marc.md)
et les bilans liés sont les références de réalisation.

| Partie | Preuve actuelle | Ce qui reste concret |
| --- | --- | --- |
| Recherche classique et index | R2 Marc 0.25.0 : 32 demandes, 31 avec résultats ; 120 index natifs compatibles et 15 compléments pour 135 archives. [Rapport et limites](../essais/2026-11-16-rapports-marc-0250.md) | Avis humains manquants, couverture encore partielle dans ce rapport, ouverture de résultats prioritaires et mesure après SSD à faire sur Marc |
| Assistant documentaire | [Essai R7 0.32.0](../essais/2026-11-16-coherence-traduction.md#contrôle-connexe-du-changement-de-modèle-et-des-sources) : première demande après changement de cible, cinq PDF effectivement lus en page 6, cinq valeurs référencées, 14,461 s | Le changement avec coexistence de modèles ne prouve pas l’éviction sous saturation ni les refus de démarrage Windows ; exporter les traces d’un cas réel si nécessaire |
| Traductions longues | 40 pages fictives terminées sur Marc ; vocabulaire personnel figé et repère borné 0.32.0 ; chapitre réel de notice, 9 passages et reprise/lecture testés sur R7 | Cohérence complète d’un livre réel de 500 pages et sémantique de chaque passage non certifiées ; poursuivre la relecture progressive, sans transformer les contrôles numériques en certificat |
| Vidéos locales et collections | Index/lecteur, traduction et transcription audio hors ligne ; [récupération YouTube 0.31.0](../essais/2026-11-16-acquisition-sous-titres.md) réelle sur R7 puis pistes conservées ; [examen ZIM 0.33.0](../essais/2026-11-16-videos-collections.md), pistes internes dans la recherche/lecteur et préparation française | Audio des vidéos internes à raccorder ; contenu réel de Marc, codecs, mots et alignement de chaque vidéo encore à vérifier |
| Mesures et conservation | Exports lisibles avec version/heure, ressources/contextes, [diagnostic de refus](../essais/2026-11-16-diagnostic-refus-demarrage.md), arrêt/reprise/suppression des traductions et paquet comparé à Git | Les observations après erreur restent distinctes de l’instant exact de la panne ; aucun test humain non exécuté n’est compté comme réussi |

Le [correctif 0.33.1](../essais/2026-11-16-intention-pratique-et-prix.md) complète
la recherche pratique : aperçu de prix séparé d’un titre d’instructions, demandes
courtes reconnues sans « comment ». Le retour de Marc sur le prix de réparation
du vélo est reproduit sur petits textes ; l’article exact et sa pertinence réelle
restent à vérifier. Ce correctif ne clôt pas la validation du fonds complet.

Le [protocole ciblé courant](../essais/recettes-progressives-marc.md#prochaine-validation-ciblée--0330)
évite de refaire toutes les préparations. Les essais chez Marc sont progressifs ;
un accès TeamViewer détenu par Louis ne devient pas un accès autonome de l’agent.
Tant qu’un développement ou une vérification autonome utile reste possible, ces
validations externes ne bloquent pas la poursuite du travail. La conclusion sur
sa machine exige toutefois ses observations effectives.

Les [prochains objectifs UX et campagne de fiabilité globale](choix-actuels.md#deux-prochains-objectifs--décision-de-louis-du-16-novembre-2026),
notamment restauration sur deux supports physiques, restent distincts et ne sont
pas lancés par ce suivi. Aucune étude ou étape minimale n’est utilisée pour
annoncer l’objectif actif achevé.

## Point de départ historique — 14 novembre 2026

| Point | État | Preuve ou prochaine vérification |
| --- | --- | --- |
| Recherche commune, classement pratique, titres et requêtes FR/EN | Implémenté en 0.1.36, testé sur petites fixtures | Recette du fonds réel depuis le site de Marc ; repérer les sources manquées avant de compléter le fonds |
| Assistant : recherche préalable, reprise de sujet, contexte et appels répétés | Implémenté sur demandes reconnues ; orchestration simulée | Comparer rapide et relance Wikipédia avec modèles réels, relever les phases et délais |
| Collections de même source | Regroupement et variantes implémentés | Vérifier les libellés issus des archives de Marc ; enrichir les noms insuffisamment explicites sans fusionner les fichiers |
| Compréhension de Parcours | Libellé et explication clarifiés : Apprendre par thème | Recueillir l’usage ; un thème n’est pas une procédure ni un cours complet validé |
| Profondeur et guides réellement opératoires | **À qualifier dans le fonds réel** | Ouvrir les documents sur feu et générateur à pédales ; distinguer histoire, principe et fabrication. Noter pièces, schémas, étapes et lacunes confirmées |
| Vidéos anglaises | **À développer et qualifier** | Inventorier les pistes réellement présentes dans les ZIM, puis lecture locale, transcription si nécessaire, traduction et conservation des sous-titres. Aucun téléchargement lourd ni sous-titre fabriqué implicitement |
| Traduction en haut du lecteur | Accès à la traduction dédiée ajouté pour les sources anglaises du portail | Ne remplace pas une traduction instantanée de page dans tous les lecteurs Kiwix/PDF |
| Traduction de page hors ligne | **Intégration à étudier** ; possibilité Firefox documentée | Préinstaller les langues sur le client et tester Internet coupé ; vérifier aussi les autres navigateurs et préserver l’original |
| Traduction de gros livres | Fonction existante par passages ; limites documentées | Un PDF de 500 pages peut être admis, mais durée, fidélité et cohérence d’un livre réel restent à mesurer |
| Complément IA à la recherche | **Évaluation ultérieure sur base mesurée** | Comparer reformulation/reclassement puis index multilingue éventuel ; mesurer qualité, indexation, espace, RAM/VRAM, reprise et délai. Garder le socle sans IA |
| Maison de Solliès-Ville | **Plus tard**, demande explicite de Louis | [Boîte à idées](boite-a-idees.md), pas d’inventaire fictif ni d’onglet vide |

La [référence d’utilisation](../utilisation/recherche-documentaire.md) donne les
commandes visibles et la recette Windows. Le [bilan 0.1.36](../essais/2026-11-14-moteur-recherche-utile.md)
précise les essais de développement. Une validation sur les fichiers générés ne
ferme pas les lignes nécessitant le contenu ou le matériel réels.

Louis peut tester depuis le site sur le Windows de Marc ; son accès TeamViewer
personnel est déclaré. Aucun accès distant autonome de l’agent n’est établi.

## Suite 0.3.0

Le [rapport réel reçu et le bilan 0.3.0](../essais/2026-11-14-recherche-index-et-espaces.md) motivent la réservation des titres, le parallélisme CPU, le classement par action, les deux périmètres et le contexte réglable. L’[indexation complémentaire](../utilisation/indexation-archives.md) est implémentée ; les index du fonds de Marc ne sont pas créés par le développement dans le runner. Le tableau initial ci-dessus conserve son état 0.1.36 ; le plan lié distingue les suites livrées et non validées.
