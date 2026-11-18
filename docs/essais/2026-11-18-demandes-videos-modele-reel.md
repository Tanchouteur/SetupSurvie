# Demandes de vidéos avec de vrais modèles — 0.43.2

**Bilan daté du 18 novembre 2026.** Essai sur le R7 (RTX 4080, Ollama local), avec
le vrai assistant et trois vidéos fictives. Recette :
`tests/real_video_request_check.py`. Aucun téléchargement, aucune vidéo réelle.
GPT-OSS 20B, le modèle vu dans les captures de Marc, n’est pas installé sur le R7 et
n’a pas été essayé ; le PC de Marc non plus.

## Cas essayés

Sujet dans le titre (« Cherche une vidéo sur comment faire du feux »), demande
générale (« trouve une vidéo de nimporte quoi »), mot présent seulement dans les
sous-titres, sujet absent, et question sur le contenu d’une vidéo avec demande de
lien. La recherche vidéo a été lancée avec l’espace « Autonomie et résilience » de
la conversation.

## Défauts trouvés puis corrigés

| Observation avec le vrai modèle | Correction |
| --- | --- |
| Citation d’une source non lue : réponse rejetée et lien perdu | Sous-titres des vidéos trouvées lus avant la réponse ; liens réels conservés après un rejet |
| Le modèle demandait la permission de lire les sous-titres | Lecture automatique et consigne de répondre directement |
| Question longue : vidéo trouvée puis écartée du classement | La recherche vidéo garde les correspondances partielles |
| Adresse écrite `[https://nouveau/#/…]`, non cliquable | Réparation côté serveur et lien comptabilisé seulement s’il est valide |

## Résultat final

| Modèle | Séries | Cas réussis | Durée par cas |
| --- | --- | --- | --- |
| `gemma4:e4b` | 3 | 15 / 15 | environ 1 à 7 s |
| `llama3.1:8b` | 1 | 5 / 5, dont un lien ajouté par le logiciel | environ 2 à 6 s |

Les contrôles automatiques portent sur l’état de la réponse, la validité des liens,
la vidéo attendue, l’absence de fausse déclaration et la valeur fictive de 60 cm. Les
réponses de la dernière série Gemma et celles de Llama ont été relues ; ce nombre
d’essais ne mesure pas une fiabilité générale.

## Limites

- Fichiers fictifs de quelques secondes, pas le fonds réel ni un grand catalogue.
- Les sous-titres sont du texte : le modèle ne voit ni les images ni les gestes.
- Vidéos des ZIM non couvertes par cette recette.
