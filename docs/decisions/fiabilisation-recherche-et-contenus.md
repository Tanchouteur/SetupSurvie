# Fiabiliser la recherche et l’utilité de la bibliothèque

**Chantier actuel — 14 novembre 2026.** Louis demande de travailler tous les
points du retour de Marc et de fiabiliser en priorité le cœur de recherche.
Le [plan retenu et son suivi](plan-ameliorations-marc.md) porte désormais les lots, décisions et pistes écartées. Le [compte rendu](../essais/2026-11-14-retour-experience-marc.md) conserve les
observations ; ce suivi distingue réalisation et validations manquantes.

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
