# Rapports réels reçus en 0.9.3

**Bilan de réception — 14 novembre 2026.** Louis transmet les exports d’indexation,
de contrôle complet sans IA et de comparatif IA. Les fichiers bruts restent dans
les pièces jointes privées ; ce document ne recopie ni leurs gros manifestes ni
les textes documentaires. Suite du [rapport 0.8.0](2026-11-14-rapports-recherche-080.md).

## Indexation réellement terminée

Le rapport créé à 18:25:22 UTC indique **135/135 archives examinées, aucune erreur** :
134 statuts `kiwix_index`, un statut `ready` pour `phet_fr_all_2026-08.zim`, avec
120 articles extraits et 756 entrées non textuelles ignorées. Neuf processus ont
été choisis ; file vide, aucune suspension. Le contrôle du lecteur réussit sous
Python 3.12.10 64 bits, SQLite 3.49.1 et libzim 3.13.1 avec FTS5.

Les 120 articles ne représentent pas tout le fonds : les 134 autres archives
réutilisent leur propre index natif. Aucun réindexage complet de Wikipédia ni
téléchargement supplémentaire n’est nécessaire pour expliquer ce compteur.
Ce résultat valide cette exécution, pas la cause exacte de l’ancien échec.

## Recherche sans IA

Le contrôle créé à 18:25:40 UTC termine ses 32 demandes. Kiwix répond en 9 ms,
le catalogue de 135 collections est obtenu en direct en 126 ms ; 102 guides
sont prêts. Les index locaux interrogés ne sont signalés ni illisibles ni périmés.

- **31 recherches partielles, une complète** : la recherche ciblée Wikipédia
  termine en 2 950 ms. Toutes les recherches partielles atteignent le délai global.
- Médiane **6 368,5 ms**, maximum **10 266 ms**. Des appels plein texte expirent
  vers trois secondes ; certains appels de titres vers deux secondes.
- Six demandes n’achèvent aucune interrogation plein texte : bâche/toit, radio,
  couture, panneau solaire, conserves et « réparation vélo ». Des résultats de
  guides restent affichés ; leur présence ne prouve pas une recherche globale.
- Les demandes feu et générateur retrouvent plusieurs sources attendues, mais
  certains résultats sont insuffisamment liés au besoin. « Réparation vélo »
  remonte notamment un modèle d’inventaire familial et des exercices de prix de vélo.
  Le cas négatif de propulsion remonte aussi des correspondances partielles.
- Aucun des 32 cas n’a encore d’avis humain enregistré. Le rang utile et la
  qualité d’une procédure ne sont pas certifiés par les titres exportés.

Le code 0.9.3 interroge de petits lots, avec un budget global de six secondes,
deux appels plein texte et deux appels de titres en parallèle. Les raffinements
attendent la fin de tous les lots et ne sont jamais tentés dans ce rapport.
Les erreurs concernent aussi des lots mêlant collections prioritaires et générales.
Cela oriente les reproductions vers l’ordonnancement, les délais et la validation
des correspondances ; le rapport seul ne mesure pas CPU, disque ou cache natif.

## Comparatif avec IA

Huit cas de vérification sont prévus, budget de quinze secondes pour toute une
demande, mode rapide GPT-OSS 20B, contexte 8 192. Deux cas démarrent et leurs
reformulations expirent à **15 001 ms** ; l’arrêt après deux échecs fonctionne.
La recherche de référence consomme déjà environ 6,5 s, puis l’appel modèle dure
environ 8,3–8,4 s sans premier fragment, texte ou réflexion reçu.

Ce rapport n’établit ni débit de génération, ni panne mémoire, ni gain de
pertinence. Aucun reclassement n’aboutit et aucun avis humain n’est donné.
L’aide IA reste désactivée dans la recherche ordinaire ; la priorité est le
moteur documentaire commun. Le matériel déclaré est une RTX 5060 Ti de 8 Go
avec environ 32 Go de RAM ; les performances de ce poste ne sont pas déduites
des tests CPU du runner.

## Suite à vérifier

Reproduire les pertes d’intention et le rejet insuffisant des résultats natifs
partiels. Vérifier le regroupement, les tâches conservées après annulation,
la priorité des collections et le budget avant d’en changer les valeurs.
Consigner chaque correction dans le [journal depuis 0.2.0](journal-recherche-depuis-020.md).
La recette R7 en préparation reste non livrée tant que ces corrections prioritaires
ne sont pas traitées ; les tests de corpus et de modèle restent sur le PC cible.

**Suite :** les [corrections 0.9.4](2026-11-14-corrections-rapports-093.md)
reproduisent ces défauts sur petites données et passent la CI ; un nouveau
contrôle sans IA chez Marc doit encore établir leur effet sur le fonds complet.
