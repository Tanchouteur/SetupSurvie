# Reconnaissance audio des vidéos internes

**Référence actuelle 0.35.0 — 16 novembre 2026.** La reconnaissance des médias
inclus est maintenant raccordée à la commande audio existante, avec suivi,
pause/reprise, préparation française optionnelle et index. Le
[guide actuel](../utilisation/videos-locales.md#créer-les-sous-titres-dune-vidéo-de-collection--0350)
décrit les commandes ; le [bilan](../essais/2026-11-16-audio-videos-collections.md)
sépare tests simulés, lecteur réel et modèles du R7. Aucun fonds de Marc ni
ensemble de sous-titres ne devient automatiquement validé par ce raccordement.

Le descripteur privé est construit depuis le service configuré et l’inventaire
local ; l’archive ne choisit pas son hôte réseau. Chaque unité revalide sa source.
Le lecteur vérifie l’édition servie, refuse les redirections/lectures secondaires
et lit par portions bornées. Le worker utilise le flux audio pour se déplacer,
garde les temps natifs et ne publie pas de segment au-delà de l’audio décodé.
Un cache de lecture de 256 Kio n’est pas une limite de taille des vidéos ni du
cache documentaire. Les métriques HTTP ne sont pas des mesures d’octets disque.

Les paragraphes suivants conservent l’étape de conception et ses observations
avant raccordement ; leur futur ne décrit pas l’état livré ci-dessus.

## Historique : prototype isolé

## Lecture choisie

Utiliser un objet lisible avec déplacement pour le décodeur audio, servi par
portions HTTP du Kiwix configuré sur l’appareil. Le descripteur sera construit
par le backend depuis l’inventaire vérifié ; une page HTML ne peut pas désigner
un autre hôte. Le fichier vidéo complet n’a pas à être extrait ni écrit dans un
cache disque avant de commencer. Le cache mémoire de lecture est borné à 256 Kio
par objet ; ce n’est ni une limite de taille des vidéos ni celle du cache de recherche.

Le prototype `pilot/archive_media.py` vérifie l’identifiant de l’édition et le
nom de collection via l’entrée du catalogue Kiwix, puis exige des portions
cohérentes avec la taille du média. Il refuse les redirections, réponses HTML,
portions tronquées, édition changée et lecture complète implicite d’un gros fichier.
Les mesures comptent requêtes, octets transférés, cache mémoire et temps HTTP,
sans enregistrer l’adresse interne dans le rapport. Les octets peuvent être
relus ; il ne s’agit pas d’un total d’octets uniques.

## Preuves présentes

- **Six tests locaux**, service HTTP simulé, en **0,012 s** : déplacements dans
  un fichier de 1,28 Mo, lecture de la fin sans copier le fichier entier, cache,
  entrées invalides, édition/collection, plages, réponses mauvaises et fermeture.
- **Kiwix réel 3.8.1 épinglé**, archive générée de 36 675 octets :
  `/catalog/v2/entry/<uuid>` répond avec l’identité attendue. Un chemin de contenu
  utilisant directement cet UUID répond 404 ; garder le nom de collection pour
  la lecture et vérifier son identité par le catalogue. Aucun corpus téléchargé.

Ces premières preuves portent sur les échanges HTTP ; reconnaissance et français
ne sont pas validés par ces contrôles.
L’interface garde pour l’instant le parcours audio sur les MP4 locaux seulement.

### Complément réel PyAV sur le R7

Le runtime déjà installé **PyAV 14.0.1** lit ensuite le même audio AAC en local
et à travers `RangeReader` : mêmes quatre trames après déplacement près de
58 secondes, première trame à **57,984 s**. Le MP4 synthétique de **267 806 octets**
est complété d’un bloc MP4 `free` de 8 Mio ; taille testée **8 656 422 octets**.
Ce remplissage n’est pas une vraie vidéo à haut débit. **786 432 octets** média
sont transférés en trois portions, plus une requête catalogue ; cache de 256 Kio,
trois réutilisations, **56 ms** de lecture/contrôles sur ce serveur HTTP simulé du
R7, hors préparation et arrêt du simulateur. Ce n’est pas une mesure du disque.
La liste distante forcée HLS est refusée avant toute ouverture secondaire.
Aucun modèle, Internet, reconnaissance ou français n’est utilisé pour cet essai.

Le premier contrôle utilisait un déplacement global du conteneur : sur ce média,
il revenait à la première image-clé et l’audio repartait à zéro. Le second utilise
le flux audio pour le déplacement ; il conserve ses temps natifs. Ce résultat
guide le futur raccordement de `speech_worker.py` ; il n’en annonce pas la correction.
Les rapports privés `report-archive-ranges-0340.json` et `...-v2.json` restent sur
le R7. La recette opt-in `tests/real_archive_media_check.py` permet de reproduire
le contrôle sans modèle, avec un petit MP4 synthétique déjà présent.

## Raccordement restant

1. Construire le descripteur depuis le seul service configuré, vérifier la
   révision de l’archive avant/après chaque unité et lier la source au travail.
2. Brancher cette lecture dans `speech_worker.py`, avec fermeture sur erreur ou
   pause. Le décodeur ne doit ouvrir ni protocole secondaire, ni liste distante.
3. Réutiliser progression, reprise et publication contrôlée de `transcriptions.py`,
   puis la préparation française et la recherche existantes. Ne pas publier de
   piste partielle ni confondre audio absent et absence d’information.
4. Tester un vrai petit média décodable et la reprise ; mesurer les octets lus.
   Une inférence réelle se fait sur le R7 après ses contrôles de ressources/pause,
   jamais en téléchargeant un modèle dans le runner CPU.

Références primaires de conception : [PyAV, ouverture d’un objet fichier](https://pyav.org/docs/6.2.0/api/toplevel.html)
et [FFmpeg, protocoles autorisés](https://ffmpeg.org/ffmpeg-protocols.html#Protocol-Options).
La version installée reste celle épinglée du projet ; ces références ne changent
aucun composant ni ne remplacent les essais du runtime réel.
