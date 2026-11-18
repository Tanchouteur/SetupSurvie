# Première vague de fiabilité documentaire sur le R7

Bilan du 18 novembre 2026. Essai demandé par Louis pour distinguer une source
absente d’un défaut de recherche ou d’usage des sources par l’assistant.

## Dispositif

SetupSurvie 0.43.4, commit `30055f5`, R7 (RTX 4080), Ollama 0.40.14 et
Gemma 4 E4B (empreinte commençant par `dc35e8d9c606`). Mode « Réponse
moyenne », réflexion activée, contexte demandé de 16 384 jetons et sortie
plafonnée à 2 048 jetons par appel pour cet essai.

Huit questions de la [banque de Claude](../../tests/evaluation/banque-questions-effondrement.json)
sont posées mot pour mot en conversation neuve. Le fonds d’essai contient cinq
guides voisins. On compare ce fonds à une variante qui ajoute huit fiches
fictives avec des réponses vérifiables. Deux questions de contrôle, sur les
fractions et la météo, sont posées avec les fiches présentes. Sur certains
cas, un troisième passage associe directement la fiche à la conversation.
La recherche seule examine les cinq premiers résultats avec la question
complète, puis avec des mots-clés courts. Les traces distinguent les requêtes
internes de l’assistant des passages effectivement lus.

Les routes `/api/search`, `/api/questions` et `/api/jobs/{id}` appellent le
vrai pilote en mémoire. Chaque variante a son propre index SQLite et son
propre état temporaire. Ollama tourne sur le R7. Le catalogue Kiwix est vide
pour cet essai. Les rapports JSON avec réponses intégrales restent privés.

## Résultats avec les fiches présentes

| Question | Recherche seule, question complète | L’assistant a lu la fiche | Observation |
| --- | --- | --- | --- |
| EDU-01 · Apprentissage culturel | Aucun résultat | Oui | Sa recherche interne a retiré la fin de la question. Il cite le planning fictif et demande les âges. |
| EDU-03 · École à la maison | Fiche au premier rang | Non | Aucun appel de recherche. Il demande le matériel disponible et propose tout de même une semaine d’activités générales. |
| AGR-03 · Compost | Fiche au premier rang | Oui | Utilise et cite la fiche. |
| AGR-05 · Arrosage | Fiche au premier rang | Oui | Utilise et cite la fiche. |
| AGR-06 · Rotation des cultures | Fiche au premier rang | Oui | Cite l’ordre précis des cultures du document. |
| REP-01 · Crevaison | Fiche au premier rang | Oui | Utilise et cite la fiche. |
| ORG-02 · Tâches dans un hameau | Aucun résultat | Non | Sa recherche revient vide. Il donne une réponse générale mais affirme à tort qu’il n’y a pas de document précis. |
| CUL-02 · Les Misérables | Aucun résultat | Non | Aucun appel de recherche. Il répond correctement de mémoire. |

Les huit fiches sont lisibles directement et remontent au premier rang avec les
mots-clés courts. Pour ORG-02, « hameau tâches » retrouve la fiche. Pour
CUL-02, « les misérables victor hugo » la retrouve. Les deux contrôles
donnent une leçon de fractions et une limite explicite sur la météo en temps réel.

Sur la question de Marc (EDU-01), retirer la fiche laisse une recherche vide
et l’assistant propose quand même une organisation générale adaptable, sans
citation inventée. C’est un résultat sur Gemma 4, avec une version et un fonds
d’essai différents de ceux de la capture de Marc sous GPT-OSS.

## Vérification avec la fiche jointe ou absente

- **Fiche jointe.** Quatre réponses sur quatre lisent et citent la fiche
  sélectionnée. La semaine d’école à la maison s’appuie alors sur le planning
  fourni. La réponse sur le hameau reprend la rotation et les suppléants.
- **Fiche absente.** Huit réponses sur huit proposent une aide générale sans
  citation. La recherche autonome de la bibliothèque n’a renvoyé aucune fiche
  sur ces huit formulations. La mention explicite de l’origine générale des
  conseils varie selon les réponses.
- **Synthèse.** Sur huit fiches présentes, cinq ressortent dans la recherche
  seule avec la question complète et cinq sont lues automatiquement par
  l’assistant. Les deux groupes diffèrent sur EDU-01 et EDU-03. La recherche
  par mots-clés retrouve les huit. On dispose de 22 combinaisons terminées
  sur dix questions distinctes, plus une répétition d’EDU-01 sans fiche.

## Reproduire

Depuis un checkout de SetupSurvie sur un hôte de test dédié avec Gemma 4 E4B
déjà installé, les dépendances Python de test et Ollama local :

```bash
python3 tests/real_document_coverage_check.py \
  --commit "$(git rev-parse --short HEAD)" \
  --report /chemin/prive/rapport-neuf.json \
  --pause-marker /chemin/prive/inference-paused.json \
  --attach EDU-01 EDU-03 ORG-02 AGR-05
```

Indiquer le marqueur de pause de l’installation d’essai. Une indisponibilité
GPU a interrompu le premier passage après onze réponses. La recette vérifie
la marge VRAM et accepte une attente bornée avec `--gpu-wait-seconds` sans
arrêter les autres tâches. La reprise peut sélectionner des variantes avec
`--conditions` et doit écrire dans un nouveau rapport. Une première reprise
a échoué à cause d’une signature incompatible du garde de test. Les essais
concernés ont été écartés du décompte et rejoués avec le garde corrigé.

Ce petit essai permet d’attribuer des défauts précis de recherche et de
consultation des sources. La campagne des 89 questions sur le fonds réel de
Marc, les archives Kiwix, les questions critiques, les autres modèles et le
seuil V1 restent à mesurer.
