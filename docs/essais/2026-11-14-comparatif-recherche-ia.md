# Comparatif facultatif de recherche avec le modèle local

**Bilan daté — 0.8.0, 14 novembre 2026.** Lot L8 du
[plan des améliorations de Marc](../decisions/plan-ameliorations-marc.md).

L’outil prépare un comparatif reproductible chez Marc, sans modifier le chemin
de recherche habituel. Trois méthodes : actuelle, reformulations bilingues avec
fusion par rang, puis reclassement de douze candidats au maximum. Les huit cas
réservés et les 24 cas de réglage sont séparés dans le rapport. La référence est
embarquée dans le service pour fonctionner aussi dans le conteneur Windows/Linux.

Les avis humains sont conservés et exportés. Un avis inconnu ne devient pas un
échec documentaire. Le bilan propose seulement une piste à confirmer si le gain,
l’absence de régression, les faux positifs, la couverture et le budget de délai
le permettent. L’aide reste désactivée dans le produit, sans changement de réglage
ni ajout de modèle. La recherche sémantique reste reportée : aucun gain matériel
n’est établi qui justifierait sa préparation ou sa place disque.

Les tests utilisent exclusivement des résultats et une inférence simulés :
reformulation, permutation invalide, identifiant inventé, erreur, pause, priorité
d’une conversation, annulation, redémarrage, exclusion mutuelle avec la calibration,
persistance des avis et absence de modification de la recherche habituelle.
Un inventaire simulé de 400 archives vérifie que le rapport reste borné et ne
recopie ni les chemins ni les détails de chaque archive. Un usage vidéo sans
mesures vidéo interrompt le bilan matériel au lieu de le considérer complet.
Le [guide actuel](../utilisation/comparer-recherche-ia.md) précise la recette,
les biais des caches, les données exportées et les critères de décision.

La version mineure 0.8.0 ajoute une expérimentation compatible et des rapports ;
le schéma existant et les images tierces restent inchangés. La
[CI du code 5450f17](https://github.com/Tanchouteur/SetupSurvie/actions/runs/43614574719)
est réussie : **447 tests Python, dont trois ignorés**, contrôles Windows,
Kiwix sur petites archives et routage synthétique. Chromium et WebKit passent
chacun les **15 nouveaux contrôles** : départ explicite, arrêt, relecture,
conservation, export et disposition de 320 à 1 366 pixels. La qualité, le temps et le
coût mémoire réels chez Marc ne sont pas validés ; le rapport R2/R4 reste attendu.
