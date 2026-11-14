# Comparer une aide IA à la recherche

**Guide actuel — 0.8.0, 14 novembre 2026.** Essai facultatif pour décider si le
modèle local apporte un gain sur les documents de ce PC. La recherche habituelle
ne change pas et reste utilisable sans IA. Aucun nouveau modèle n’est téléchargé.

## Lancer puis relire

1. Choisir **Famille → Mon appareil → Réglages → Vérifier la recherche → Comparer
   une aide IA à la recherche**. Ouvrir ce panneau ne lance aucune inférence.
2. Réserver une période disponible, sans usage simultané d’Open WebUI. Le moteur
   doit être démarré volontairement, le modèle déjà présent et les mesures mémoire
   disponibles. Le mode jeu est respecté ; aucune autre application n’est arrêtée.
   Garder le fonds documentaire et les corrections de classement inchangés pendant
   la comparaison ; noter tout changement avant de comparer deux rapports.
3. Choisir le mode, huit demandes de vérification ou les 32 demandes complètes,
   puis le délai souhaité par recherche : 5, 15, 30 ou 60 secondes. Ce délai sert à
   évaluer l’intérêt de l’option ; les appels peuvent dépasser ce budget avant
   leur arrêt technique. Un appel IA est borné entre 30 et 90 secondes selon ce choix,
   une recherche à 30 secondes, le comparatif complet à une heure.
4. **Lancer le comparatif avec l’IA locale** compare trois méthodes sur les mêmes
   demandes. Une question ou une traduction du portail prend la priorité ; une
   pause moteur ou une mémoire insuffisante interrompt les requêtes de l’essai.
   **Arrêter le comparatif** conserve les résultats déjà enregistrés.
5. Après la fin, ouvrir chaque demande, lire les documents liés et choisir
   **Utile pour cette demande**, **Ne répond pas à cette demande**, ou laisser
   **À vérifier**. Une mention, un bon titre ou un extrait prometteur ne prouvent
   pas que le document contient un guide exploitable. Un document inaccessible
   reste à vérifier ; le signaler avec l’adresse exacte.
6. **Télécharger le comparatif** exporte les mesures et avis conservés. Les avis
   restent disponibles après rechargement. Le dernier essai est affiché ; exporter
   avant d’en lancer un autre permet de comparer plusieurs exécutions.

L’essai continue lorsque le panneau est fermé. Après un redémarrage du service,
il est signalé interrompu et n’est jamais repris automatiquement. Le modèle testé
est déchargé si cela peut être confirmé sans gêner une nouvelle demande ni lever
une pause. Les réserves sont celles des essais mémoire : 4 Gio de RAM et 512 Mio
de mémoire vidéo. Ce sont des observations ponctuelles, pas une garantie de pire cas.

## Ce qui est comparé

- **Actuelle** : le moteur documentaire commun, sans appel au modèle.
- **Reformulée** : l’IA propose une expression française et une anglaise, puis le
  même moteur cherche chacune dans le domaine et la collection d’origine. Les
  résultats sont fusionnés par rang réciproque, avec une constante de 60.
- **Reclassée** : le modèle classe au plus douze candidats à partir de leurs
  titres et courts extraits. Il doit restituer uniquement leurs indices : un
  identifiant inventé ou un format invalide est refusé. Cela ne constitue pas une
  lecture complète et ne crée pas de nouvelles sources ou citations.

Les cinq candidats actuels restent dans le lot de relecture. Le modèle voit les
candidats ordonnés par identifiant, sans l’étiquette de la méthode. Les résultats
habituels restent conservés en cas d’échec. Aucun appel de ce module n’est ajouté
à la recherche ordinaire et aucun index sémantique n’est créé.

La référence versionnée est dans `pilot/search-reference.json`, embarquée avec le
service ; `scripts/build_next_portal.py` produit aussi sa copie statique destinée
au contrôle sans IA. Les huit cas `verify-*` restent séparés des 24 cas de réglage.
Les documents fictifs des tests ne sont jamais des attentes imposées au fonds réel.

## Lire la conclusion

Le rapport sépare les deux groupes et mesure les besoins ayant un résultat utile
parmi les cinq premiers, les résultats jugés hors sujet, les cas sans candidat
utile dans le lot examiné, les erreurs, la médiane et le cas lent à 95 %. Un avis
manquant reste inconnu et n’est pas compté hors sujet. Les avis de tous les candidats
d’une demande sont nécessaires pour la comparaison complète de cette demande.
Les proportions ne mesurent pas le rappel de toute la bibliothèque.

Une méthode devient seulement **candidate à confirmer** si elle améliore les huit
cas de vérification, sans perdre de cas réussi parmi les demandes examinées, sans
augmenter la proportion hors sujet ni ajouter de résultats sur un cas jugé sans
candidat utile. Les méthodes doivent être terminées et relues, leur couverture
complète et leur temps total par demande inférieur au budget choisi. Une recherche
partielle peut rester utile, mais ne valide pas cette option. Sans preuve suffisante,
aucun gain n’est déclaré ; cela ne démontre pas que l’IA serait toujours inutile.

Le temps « Reformulée » inclut le moteur actuel, la génération et les nouvelles
recherches ; « Reclassée » ajoute le dernier appel IA. La préparation initiale du
modèle est distincte de ces demandes. Les durées de chargement retournées par le
moteur sont conservées par appel. Les caches restent en place et la méthode actuelle
passe en premier : le protocole ne certifie aucune comparaison à froid. Refaire
l’essai et examiner les variations avant une décision. Il ne valide ni la qualité
d’une procédure ni un autre modèle ou un autre PC.
Les temps comprennent aussi le suivi des ressources et les écritures de l’essai ;
ils ne mesurent pas exactement le délai d’affichage dans le navigateur.

## Données et suite de la décision

Les rapports privés sont dans `state/pilot/search-experiments/`, couverts par la
sauvegarde habituelle. Ils contiennent les demandes fixes de test, reformulations,
titres et courts extraits, identifiants, avis, couverture, modèle/digest, contexte,
matériel et mémoire libre minimale observée, durées et compteurs techniques.
Ils ne contiennent pas de conversations, de raisonnement privé ni de texte complet.
L’accès au panneau suit le [profil Famille](profils-locaux.md).

L’aide reste **désactivée par défaut**, même après un résultat favorable. Le rapport
R2/R4 réel doit permettre de retenir ou écarter son intégration. Un index sémantique
multilingue est reporté jusqu’à ce comparatif, avec ses coûts de stockage et de
préparation à mesurer séparément. Aucun gain réel n’a été mesuré dans le runner CPU.

Les sorties structurées suivent les [schémas JSON d’Ollama](https://docs.ollama.com/capabilities/structured-outputs)
et les [champs de durée de l’API locale](https://docs.ollama.com/api/chat) ; le service
valide aussi les valeurs reçues au lieu de se fier au seul format demandé.
