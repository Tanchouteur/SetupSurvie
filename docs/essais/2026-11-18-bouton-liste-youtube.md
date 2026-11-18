# Bouton de liste YouTube dans le site — 0.43.0

**Bilan daté du 18 novembre 2026.** Essais dans le runner de développement, sans
modèle, sans YouTube et avec un contrôleur d’hôte simulé pour le navigateur.
Aucune vidéo réelle n’a été téléchargée, et aucun essai n’a eu lieu sur le PC de
Marc ou sur Windows.

## Livré

**Famille → Bibliothèque → Collections → Vidéos de la bibliothèque → Ajouter des
vidéos depuis YouTube** : liste collée ou fichier texte, vérification, qualité,
lancement, suivi, pause et reprise. Le site enregistre la liste dans
`state/pilot/youtube-lists/` et transmet seulement son identifiant au contrôleur,
limité à 1 Ko par commande. Le contrôleur lance `scripts/youtube_videos.py` dans
un travail détaché, qui continue si la page est fermée.

## Vérifications exécutées

| Vérification | Résultat |
| --- | --- |
| `tests/test_youtube_downloads.py` : API du site, travail hôte, progression, pause réelle d’un faux yt-dlp | réussis |
| `tests/browser_youtube_downloads.py` dans Chromium, ordinateur et téléphone émulé, contrôleur simulé : 22 contrôles | réussis |
| Profil non administrateur | zone masquée, API refusée (403) |

Le navigateur a révélé deux défauts corrigés : le message de vérification effacé
par le rafraîchissement, et des totaux affichés deux fois à la fin. La relecture a
révélé deux autres défauts, que les tests simulés ne montraient pas : une liste
écrite en `0600` par le conteneur `root` aurait été illisible par l’hôte Linux, et
le contrôle limité à une fois par minute pouvait retarder l’apparition des vidéos.

## Limites

- Le trajet complet site → contrôleur réel → YouTube reste à essayer sur un PC cible.
- Windows, WebKit et un vrai iPhone ne sont pas testés pour ce parcours.
- Une seule opération de bibliothèque à la fois : le bouton attend la fin d’une
  autre préparation.
