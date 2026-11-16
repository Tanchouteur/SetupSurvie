# Vidéos des collections : inventaire, lecture et recherche

**Bilan du candidat 0.33.0 — 16 novembre 2026.** Le numéro mineur correspond à
un nouveau parcours compatible ; aucune migration destructive ni version de
composant tiers changée. Les corrections Windows 0.32.1 sont conservées.
Ce document décrit le développement et ses preuves, pas une mise à jour du PC de Marc.

## Comportement

L’examen volontaire des ZIM est accessible dans Collections, avec progression
par archive, pause, reprise et rapport. Il utilise le lecteur isolé déjà préparé
sur l’hôte, même pour les archives munies d’un index texte natif. Il respecte le
mode jeu, les baux et la coordination des travaux lourds. L’ouverture d’une page
ne lance pas d’examen, de téléchargement ni de modèle.

Chaque inventaire est reconstruit avec points de reprise et publication atomique.
Le précédent reste disponible pendant le suivant ; un changement d’édition
invalide les anciennes références sans supprimer les originaux. Seuls les petits
textes de pistes sont préparés en cache, jamais l’ensemble d’une vidéo.

Les médias internes rejoignent la liste vidéo existante avec article d’origine.
Kiwix sert la lecture par portions sur le réseau local. Les paroles contrôlées
rejoignent la recherche et la lecture documentaire avec langue/horodatage. La
préparation française réutilise les contrôles et la file existants ; originaux
intacts, temps conservés, statut automatique visible. Les liens distants et
lecteurs JavaScript ne sont pas présentés comme des vidéos incluses.

## Vérifications exécutées

- **Archives natives libzim 3.13.1 :** petites ZIM générées, dont index natif,
  pistes redirigées, vidéo non liée, reprise et changement d’édition. Les premières
  fixtures binaires ne sont pas décodables et ne servent pas de preuve de lecture.
- **API/index :** recherches source/français, vraie piste interne copiée en cache,
  cache manquant réparé par réutilisation de l’inventaire, source remplacée refusée,
  contrôles de rôle, suivi et ancien état non confondu avec le nouveau.
- **Transport HTTP simulé :** demandes complètes/partielles, plages refusées,
  taille/type différents, redirection distante, corps tronqué/trop grand, fermeture
  des connexions et absence du lecteur. Aucun réseau extérieur dans ces tests.
- **Kiwix réel épinglé 3.8.1 :** archive **36 675 octets**, WebM **1 135 octets**,
  sept contrôles : média exact, type, HTTP 206 et plage exacte, taille totale,
  redirection de piste dans l’archive, piste canonique et article d’origine.
  `tests/kiwix_video_smoke.py` reproduit cet essai avec nettoyage de son seul TEST.
- **Chromium MCP :** 17 contrôles du parcours complet avec vraie ZIM/WebM,
  lecteur HTTP et contrôleur hôte simulés, traduction simulée, temps conservés,
  lecture à 1 seconde et largeurs 1 366/390/320. Aucune erreur JavaScript observée.

Les recettes ciblées **Chromium et WebKit** passent ensuite **58 contrôles par
navigateur** : vidéos locales 22, archives 17, préparation française 19.
La suite locale passe **933 tests en 214,886 s, 6 ignorés** avant le dernier
complément du suivi hôte. Après ce complément, les **14 tests ciblés** des
archives/API/transport passent en 2,473 s. La CI du code final et le reçu de
paquet seront consignés après leur fin.

Le premier test HTTP utilisait le `wget` minimal de l’image Kiwix, qui refuse
lui-même un HTTP 206. Le test passe maintenant par une requête HTTP brute avec
`nc`, sans modifier le serveur ni accepter une réponse 200 comme preuve de seek.
Une première recette navigateur attendait une fonction asynchrone avec un outil
qui ne la réévaluait pas correctement ; elle attend désormais le nouveau travail
effectif. Les anciennes pistes terminées ne valident pas une nouvelle traduction.

## Limites conservées

Aucune vidéo ou ZIM réelle de Marc examinée. Les résultats synthétiques ne
valident ni tous les codecs, ni les paroles, ni l’alignement d’un montage différent,
ni la fidélité humaine d’une traduction. WebKit n’est pas Safari iPhone réel.
La reconnaissance audio des vidéos internes reste à raccorder ; le parcours
`library/video/` existant conserve cette fonction pour les MP4 seuls. Les lecteurs
JavaScript et pistes intégrées au conteneur ne sont pas tous interprétés.

La [coordination UX](../decisions/coordination-ux-et-videos.md) conserve les contrats
pour l’agent parallèle. Le [guide](../utilisation/videos-locales.md) porte la
procédure courante ; L6 et l’objectif global restent ouverts.
