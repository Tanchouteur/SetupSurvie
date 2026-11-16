# Audio des vidéos incluses : source, français et recherche

**Bilan de livraison 0.35.0 — 16 novembre 2026.** Nouvelle capacité compatible,
sans migration destructive ni changement d’image ou de modèle épinglé. Le niveau
mineur correspond au parcours audio désormais utilisable sur les médias ZIM.
Les corrections moteur 0.33.1 restent conservées. Aucun déploiement client réalisé.

La refonte UX est livrée d’abord en 0.34.0 sur `main` (`2782165`, PR nº 13).
Le candidat audio initial portait aussi 0.34.0 ; il devient 0.35.0 après reprise
normale de cette refonte. Les rapports privés R7 ci-dessous gardent leur version
d’exécution initiale ; ils ne sont pas renumérotés rétroactivement. La CI de
l’état réuni est relancée après cette réconciliation et passe les huit jobs.

## Ce qui change

La commande audio existante accepte les vidéos effectivement incluses dans une
collection. Le backend construit la référence depuis l’inventaire et le Kiwix
configuré ; la page d’origine ne peut pas choisir un hôte de transcription. Le
worker vérifie l’identité/édition servie puis lit le média par portions de 256 Kio,
sans extraire une copie complète. Les redirections, lectures secondaires, listes
distantes et tailles incohérentes sont refusées.

Le parcours garde unités terminées, pause/reprise explicite, contrôle de la source
avant/après lecture et avant publication. Une piste source complète rejoint le
lecteur et l’index ; sa préparation française utilise la file et les contrôles
existants. Les mêmes routes, identifiants et écrans sont conservés. Le champ de
capacité `audio_transcription_supported` permet au contrôle déjà présent d’être
proposé aussi sur une vidéo d’archive sans piste exploitable.

Le déplacement utilise le flux audio, ce qui évite de revenir à la première
image-clé de la vidéo pour chaque unité. Les temps natifs sont conservés, et les
segments situés après la fin de l’audio décodé ne sont pas publiés. Les rapports
ajoutent requêtes/octets et temps HTTP aux étapes décodage/chargement/reconnaissance.
Ce sont des octets transférés, éventuellement relus, pas des compteurs du disque.

## Preuves exécutées

- **954 tests locaux en 250,080 s, 6 ignorés**, dont sept cas de lecture par
  portions, cinq parcours sur vraies petites archives avec ASR/français simulés,
  échec audio, source remplacée, reprise, protocoles et bornes de fin de média.
- **Après reprise de l’UX : 962 tests en 200,704 s, 6 ignorés**, aucun échec.
  Les modules du parcours audio restent identiques à ceux de l’essai R7 v4 ;
  les ajouts UX et la version API sont testés ensemble dans ce second passage.
- **Chromium et WebKit : 67 contrôles par navigateur**, sur quatre recettes
  ciblées : archive avec piste 17, archive audio 16, audio local 15, traduction
  de piste 19. Les codecs sont réellement décodés sur un petit WebM vert ; voix,
  modèles et contrôleur hôte y sont simulés. Les formats de Marc et Safari réel
  ne sont pas qualifiés par ces essais.
  Les mêmes 67 contrôles par navigateur sont rejoués après la fusion UX. Une
  capture Chromium 1366 × 900, `ss035-audio-video-ux-pc.png` dans les artefacts
  privés du runner, est aussi examinée : commandes audio repliées dans la carte
  du média, préparation française et avertissement de durée visibles à l’ouverture,
  aucun débordement horizontal. Aucun modèle n’est démarré pour cette capture.
- **Kiwix réel épinglé 3.8.1 : dix contrôles**, archive générée de 36 675 octets,
  média de 1 135 octets. Le lecteur produit relit l’identité et des plages avec
  ETag via les vrais octets HTTP du service. `nc` sert seulement de transport vers
  ce conteneur ; aucune réponse simulée. La fixture a un nom de fichier différent
  de son nom embarqué. La taille de bloc est réduite à 32 octets dans ce petit
  test pour provoquer deux demandes ; la production garde 256 Kio.
- **R7, PyAV 14.0.1 réel :** fenêtre 58–62 secondes décodée en **64 000 échantillons**,
  exactement identiques par fichier local et par portions, **120 trames audio**.
  Sur le MP4 synthétique complété d’un bloc `free` de 8 Mio, **786 432 octets**
  média sont transférés pour 8 656 422 octets de conteneur. Ce remplissage n’est
  pas une vidéo dense à haut débit. La liste HLS forcée est refusée avant toute
  ouverture secondaire. Pas de modèle dans ce contrôle.
- **R7, modèle et audio réels :** archive native contenant le MP4 synthétique
  déjà présent, 132 secondes avec de longs silences. Whisper small préparé,
  CPU/int8/quatre threads, puis Gemma4 E4B. Le rejeu final `...-v4.json` termine en
  **30 451 ms**, **3 unités**, **7 segments reconnus et 7 traduits**. Pause après
  la première unité, puis unité conservée à l’identique après reprise, français
  effectivement retrouvé dans l’index. Les originaux MP4/ZIM sont inchangés et
  aucun MP4 n’est extrait. Le serveur HTTP de ce dernier essai est simulé sur
  loopback, à partir d’une vraie ZIM ; Kiwix réel est testé séparément ci-dessus.
  Les treize contrôles passent, dont la recherche française. Empreinte des sources
  Python du pilote : `e3f73aa0f3fca77dd6b2e5e7584c6be6bcd790533ce60f0fb18aa260a3cd7880` ;
  recette : `a5062681e191a1a2b6f582718f827b8140a20e3c87eefee10504dc73a872af56`.
  Au contrôle préalable, 10 496 Mio de VRAM étaient libres alors qu’un autre
  traitement utilisait déjà le GPU. Il n’a été ni arrêté ni modifié. Ce passage
  ne constitue donc pas un benchmark de la vitesse maximale du modèle.

Le temps sur ce fichier peu parlé et cette RTX 4080 ne prédit pas celui d’un long
documentaire ou du Windows de Marc. La relecture des sept couples reconnus/français
par l’agent retrouve les valeurs 17 mm et 420 et la négation sur le couvercle ;
elle ne certifie pas tous les mots reconnus ni leur synchronisation avec l’audio.

## Échecs utiles conservés

Le premier script réel utilisait mal le paramètre de rapport détaillé, puis
restaurait ses chemins avant la fin d’un thread d’index. Ce passage n’est pas
compté comme validation. La recette rejoint désormais les tâches avant de quitter
ses remplacements de configuration et conserve un rapport privé même si elle
s’interrompt. Les rejeux réussis v2/v3 (22 816/22 645 ms) et v4 sont distincts de
ce premier échec ; v4 porte sur les sources finales, après le correctif catalogue.

Le contrôle Kiwix réel a aussi détecté que son entrée de catalogue isolée contient
`dc:issued` sans déclaration de namespace. Le lecteur enveloppe maintenant les
namespaces connus, tout en gardant les contrôles stricts d’identité et de nom.
Ce correctif est couvert par le cas réel et un test régressif ; les préfixes inconnus
ou déclarations de type/entité ne sont pas acceptés par ce chemin.

La [note de conception](../decisions/audio-videos-zim.md) conserve le prototype
et les premiers contrôles. Le R7 reçoit seulement libzim 3.13.1 dans son venv de
test (roue 10,7 Mo) ; pas de nouveau modèle ni de corpus. Rapports complets et
paroles restent privés sous `setupsurvie-test/audio-transcription/`.

## Livraison et limites

Les huit [jobs CI du code final](https://github.com/Tanchouteur/SetupSurvie/actions/runs/43950604434)
passent au commit `f8bce46d12fb14adfa87eae1c4cb8b8fff238696`, après la fusion
de l’UX : Linux, Windows, lecteurs isolés Python 3.11/3.13/3.14, vrai Kiwix,
routage hors ligne et navigation complète Chromium/WebKit. La suite Linux CI
compte **962 tests en 97,825 s, 6 ignorés** ; la nouvelle recette audio conserve
ses seize contrôles sur chacun des deux navigateurs. Les ajouts qui suivent
ce commit sont documentaires, dont la reprise du reçu UX `6bfdc0c` et la consigne
durable de design de Louis. Le premier CI audio `43949417262`, sur le candidat
isolé `3387bc2`, est annulé comme remplacé par cet essai complet réconcilié ;
il n’est pas compté comme validation générale.

Le reçu de paquet après comparaison de chaque fichier avec Git accompagne
l’intégration successive sur `main`, sans écraser la livraison UX.
Le [guide](../utilisation/videos-locales.md#créer-les-sous-titres-dune-vidéo-de-collection--0350)
porte les commandes courantes. Aucun média réel de Marc n’est examiné ici : mots,
langue, codecs et alignement de chaque vidéo restent à qualifier. Les lecteurs
uniquement générés par JavaScript et les médias seulement liés à Internet ne sont
pas déclarés inclus. L’objectif global et R6 ne sont pas clos par cette livraison.
