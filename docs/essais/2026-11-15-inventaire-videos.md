# Inventaire des vidéos — 15 novembre 2026

**Suite :** intégration au paquet 0.14.0 décrite dans le
[bilan commun](2026-11-15-integration-outils-validation-videos.md). Les constats
ci-dessous restent ceux de la préparation initiale sur la branche dédiée.

**Bilan de développement sur fixtures minuscules, runner Linux CPU.**
Branche `codex/videos-inventaire`, créée dans un worktree séparé depuis
`origin/main` au commit `d57017c`, après `git status` propre et
`git pull --ff-only` réussi sur SetupSurvie. Aucune fusion dans `main`.

## Livrable

L'outil autonome `scripts/library_videos.py` parcourt récursivement un dossier
vidéo et exporte un JSON par média présumé terminé, plus `inventory.json`.
Le [guide d'utilisation](../utilisation/inventaire-videos.md) décrit les commandes
Windows/Linux, le contrat des rapports et les exclusions. Le périmètre suit les
[décisions vidéo](../decisions/videos-locales-et-recherche.md) et le
[protocole de validation par vidéo](protocole-sous-titres-videos.md).

Les rapports séparent français déclaré disponible, piste source seule, piste
manquante, pistes invalides et langue inconnue. Ils conservent les métadonnées
utiles, les pistes associées, les anomalies, les informations inconnues et la
prochaine action. Une piste distante annoncée ne devient pas une piste locale.
Les états de traduction, synchronisation et relecture humaine restent non vérifiés.

Les groupes de même source préservent tous les chemins ; ils ne certifient pas
une même édition. La taille/date constitue une révision indicative. Le SHA-256
intégral du média est facultatif, afin de ne pas lire automatiquement tout le
fonds. L'identifiant d'inventaire est stable pour un même chemin relatif et change
avec un renommage. L'empreinte `text_utf8_sha256` d'une piste porte sur le texte
UTF-8 décodé sans BOM, avant normalisation des fins de ligne ; elle ne doit pas
être comparée à une empreinte des octets originaux avec BOM.

Seuls les quatre fichiers réservés sont ajoutés : outil, tests, guide et ce
bilan. Conformément à la demande, aucune modification du moteur, du portail,
de Compose, des dépendances, des versions ni des index documentaires partagés.
La version du produit reste inchangée sur instruction explicite ; cet outil
reste autonome sur sa branche, sans intégration dans le produit livré.

## Vérifications effectuées

```bash
python3 -m unittest discover -s tests -p test_library_videos.py -v
python3 scripts/library_videos.py --help
git diff --check
```

**20 tests réussis**, avec médias contenant seulement quelques octets fictifs,
SRT/WebVTT et métadonnées créés en répertoires temporaires puis nettoyés.
Aucune vidéo réellement décodable n'est utilisée ni présentée comme validée.

Les tests couvrent :

- export par vidéo et récapitulatif par un vrai appel CLI ; conservation exacte
  des octets et dates de modification des sources ; refus d'écrasement et de
  sortie dans la bibliothèque ; codes d'erreur et média vide ;
- français déclaré, variantes régionales, piste source, langue inconnue ou autre,
  métadonnées absentes/corrompues, champs de mauvais type, entier très grand,
  Unicode invalide et pistes uniquement distantes ;
- provenance automatique étayée par les métadonnées, sans certifier le contenu ;
- UTF-8/BOM/CRLF, entête VTT et notes, numéros SRT, segments vides, temps inversés,
  désordonnés ou hors durée déclarée, chevauchements, fichiers mal formés ou
  illisibles, contrôle de taille avec limite abaissée en test ;
- trous temporels conservés sans les qualifier de paroles manquantes ;
- téléchargements partiels, fragments et marqueurs associés à un nom final,
  répertoire incomplet, annexes orphelines, appariement par préfixe le plus long
  et séparation entre sous-dossiers ;
- stabilité des identifiants, changement de révision et empreinte sur contenu
  modifié, regroupement de copies sans suppression, liens symboliques exclus,
  modification pendant examen et erreur de parcours simulée.

Les tests vérifient que disponibilité déclarée et contrôles structurels ne
modifient jamais les états de validation linguistique, humaine ou de synchronisation.
La suite générale du produit n'a pas été exécutée : le script n'importe que la
bibliothèque standard et ne modifie aucun composant de l'application.

## Limites et recette restante

Aucun téléchargement, modèle IA, corpus lourd, changement de service ou accès
au disque de Marc. Aucun test réel Windows, lecteur, navigateur, audio ou codec.
La compatibilité Windows repose ici sur Python standard et une commande documentée ;
les jonctions Windows ne sont pas éprouvées sur un système Windows réel.

La fin d'un téléchargement est présumée, sans décodage. Un fichier actif sans
marqueur peut ne pas être détecté s'il reste inchangé pendant l'examen. Les
marqueurs et noms intermédiaires sont ignorés prudemment ; une exclusion n'est
pas une recommandation de supprimer le fichier.

La langue provient du nom des pistes et du `.info.json`, sans détection des
paroles. Les noms non reconnus, pistes internes aux conteneurs, annexes d'autres
formats, fichiers exclus et vidéos ZIM restent hors analyse. Les styles WebVTT,
leur rendu et la conformité exhaustive des formats ne sont pas certifiés.
Un contrôle structurel réussi ne prouve ni synchronisation ni fidélité de la
traduction. Aucun sous-titre n'est créé, traduit ou publié.

Sur le PC cible, exécuter d'abord l'inventaire après la fin des téléchargements,
examiner chaque erreur/exclusion et confirmer l'appariement des fichiers. Puis
suivre le protocole par vidéo : langue réelle, lecture hors ligne, audio,
synchronisation au début/milieu/fin et après déplacement, relecture du sens et
conditions d'usage. Les acquisitions, transcriptions, traductions et l'intégration
des titres à la recherche restent des travaux ultérieurs.
