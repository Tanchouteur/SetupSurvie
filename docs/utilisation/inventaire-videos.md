# Inventorier les vidéos locales

**Guide actuel — outil autonome préparé le 15 novembre 2026.** Testé sur de petits
fichiers fictifs dans le runner Linux ; recette Windows et fonds de Marc à faire.
Il prépare l'inventaire prévu dans les [décisions vidéo](../decisions/videos-locales-et-recherche.md)
et le [protocole par vidéo](../essais/protocole-sous-titres-videos.md).
Le [bilan de développement](../essais/2026-11-15-inventaire-videos.md) précise les essais.

Cet outil lit `library/video/` et ses sous-dossiers, sans changer ni recopier les
originaux. Il ne télécharge rien, ne lance aucun modèle, ne démarre aucun service
et ne met à jour aucun index de recherche. Python 3.11 ou plus récent suffit,
sans paquet supplémentaire, Docker, FFmpeg ni yt-dlp.

## Lancer sous Windows

Utiliser la copie du script de cette branche, depuis le dossier qui contient
`scripts/`. Il n'est pas nécessaire de mettre à jour ou d'arrêter l'application
en service. Adapter le chemin des vidéos à leur emplacement réel. Exemple
PowerShell, si les vidéos sont dans `D:\SetupSurvie\donnees\library\video` :

```powershell
py -3 scripts\library_videos.py --video-dir "D:\SetupSurvie\donnees\library\video" --output-dir "$env:USERPROFILE\Documents\inventaire-videos-$(Get-Date -Format yyyyMMdd-HHmmss)"
```

Le rapport doit aller dans un **nouveau dossier**, hors du dossier vidéo. Un ancien
rapport n'est jamais remplacé. Le dossier Documents de l'utilisateur sert ici de
sortie privée ; les rapports contiennent titres, descriptions et chemins locaux.
Si `py` est absent mais Python est déjà installé, utiliser son exécutable `python`.
L'outil n'installe pas Python.

Sous Linux, depuis le même dossier de code, en adaptant les chemins :

```bash
python3 scripts/library_videos.py --video-dir "/chemin/library/video" --output-dir "$HOME/inventaire-videos-$(date +%Y%m%d-%H%M%S)"
```

Attendre de préférence la fin des téléchargements. Sont exclus les noms marqués
`.part`, `.ytdl`, `.tmp`, `.temp`, `.download`, `.crdownload` ainsi que les fragments
vidéo `.f137.mp4` et équivalents. Un média au nom final est aussi exclu si un
marqueur du même préfixe subsiste, y compris pour une piste associée. Ce choix
prudent peut exclure un média déjà terminé : examiner les fichiers signalés,
sans les supprimer automatiquement. Les répertoires marqués incomplets et les
liens symboliques ou points de réanalyse Windows détectés ne sont pas parcourus.

**« Terminé » reste présumé par le nom et l'absence de marqueurs.** La taille et
la date de modification sont comparées avant et après examen ; une modification
observée produit une erreur. Aucun décodage ne prouve la fin, l'intégrité du
conteneur ou la présence d'audio. Une écriture active sans marqueur, invisible
pendant ce bref examen, peut échapper à cette détection.

## Lire les rapports

Le dossier de sortie contient `inventory.json`, puis un fichier JSON par vidéo,
nommé par son `inventory_id`. Le récapitulatif donne les chemins des rapports,
les exclusions, erreurs et fichiers non examinés, dont les annexes orphelines.
Une vidéo vide ou inaccessible apparaît dans les erreurs du récapitulatif.

| `subtitle_status` | Signification et prochaine étape |
| --- | --- |
| `french_available` | Piste locale déclarée française par son nom, contrôles structurels réussis. Vérifier langue réelle, sens et synchronisation dans le lecteur. |
| `source_only` | Pas de piste française exploitable ; une piste locale correspond exactement à la langue source déclarée dans les métadonnées. Examiner les possibilités françaises avant de traduire. |
| `missing` | Aucune piste locale associée. Examiner les pistes récupérables, sinon envisager une transcription. |
| `invalid` | Des pistes sont présentes, aucune ne passe les contrôles. Lire leurs erreurs avant de préparer une autre piste. |
| `unknown` | Une piste est exploitable, mais sa langue ou son rapport à la langue source reste inconnu. Identifier les langues avant traitement. |

Toutes les pistes et leurs erreurs restent dans le rapport, même si une autre
piste française est exploitable. `next_action` indique la prochaine action
**conseillée**, jamais une opération déjà exécutée. `unknowns` liste les
informations manquantes. Les validations de traduction et de synchronisation
restent toujours `not_verified` ; la relecture humaine reste `not_performed`.
Les parties de parole manquantes restent inconnues.

Chaque rapport conserve notamment :

- collection relative, chemin du média, titre et origine du titre, description ;
- identifiant et extracteur source, chaîne, URL et date de publication déclarée ;
- format, taille, date de modification, hauteur, durée et langue déclarées ;
- état du `.info.json`, pistes locales SRT/WebVTT, langues déclarées, origine
  documentée ou inconnue, contrôles et prochaine action ;
- date d'inventaire, limites, révision du média et chemins de même source.

Le titre vient du `.info.json` associé, sinon du nom du fichier. La hauteur 480p,
la durée et la langue ne sont pas mesurées : une valeur absente reste `null`.
L'audio reste inconnu. Seuls les champs utiles des métadonnées sont exportés,
sans recopier les listes de formats et leurs URL de téléchargement.

L'identifiant local est le SHA-256 du chemin relatif : stable à chaque passage
sur ce chemin, indépendant du disque racine, mais modifié par un renommage. La
clé source `extracteur:id`, si disponible, rassemble les copies dans
`same_source_paths`, sans affirmer qu'elles ont la même édition ni les supprimer.
La révision courante est taille/date, ce qui **n'est pas une empreinte du contenu**.
L'option `--hash-media` calcule en plus un SHA-256 intégral, en lecture séquentielle ;
elle peut durer longtemps sur une grande bibliothèque. Deux empreintes égales
permettent de comparer les octets, sans valider le contenu pédagogique.

## Association et contrôles des pistes

Pour `Cours.mp4`, l'outil cherche `Cours.info.json`, `Cours.fr.srt`,
`Cours.fr-CA.vtt`, `Cours.en.vtt` ou `Cours.srt` dans le même dossier. Une piste
sans suffixe de langue reste de langue inconnue. Le préfixe vidéo le plus long
est prioritaire : si `Cours.en.mp4` existe, `Cours.en.srt` lui est associé.
Deux conteneurs de même base partagent les annexes ; leur correspondance réelle
reste à examiner. Les autres conventions de nommage ne sont pas devinées.

Les formats vidéo reconnus sont MP4, MKV, WebM, MOV, AVI, M4V, OGV, MPEG et MPG.
L'outil n'extrait pas les sous-titres intégrés au conteneur et n'examine pas les
ZIM. Il n'ouvre aucun lien distant. Les langues dans `subtitles` et
`automatic_captions` du `.info.json` restent **seulement annoncées à distance**.
L'origine d'une piste locale n'est attribuée que lorsqu'une entrée
`requested_subtitles` correspond à la langue et à une URL présente dans l'une
de ces deux listes, avec un chemin compatible s'il est renseigné. `provided`
signifie « fournie », sans certifier une rédaction humaine ; `automatic` ne
précise pas si une traduction automatique a eu lieu. Sans preuve, l'origine
reste `unknown`. Les métadonnées peuvent être anciennes ou incorrectes.

Les contrôles limités portent sur UTF-8 (BOM accepté), entête WebVTT, numéros SRT,
intervalles lisibles, temps croissants et non nuls, ordre, chevauchements,
segments non vides et dépassement de la durée **déclarée**, si connue. Un
chevauchement est signalé comme erreur par prudence, même s'il est intentionnel.
Les trous temporels sont dénombrés et un échantillon est conservé : un silence
n'est pas une parole manquante prouvée. Les annexes de plus de 8 Mio sont refusées.
Les autres encodages, notamment UTF-16, demandent un examen séparé sans modifier
l'original. `technical_status: passed` désigne uniquement ces contrôles, sans
certifier une conformité exhaustive SRT/WebVTT ni le rendu des styles.

Une piste nommée `.fr.srt` peut contenir de l'anglais ou être décalée ; l'outil
ne le détecte pas. La lecture locale hors ligne, la synchronisation après
recherche/déplacement et la relecture du début, milieu, fin et passage technique
restent à réaliser vidéo par vidéo selon le protocole.

Codes de sortie : **0** rapport produit, **1** rapport produit avec erreurs de
parcours/médias, **2** lancement ou export impossible. Des sous-titres invalides,
des métadonnées invalides ou des exclusions restent consultables même avec 0.
`exhaustive` reste faux, car les conteneurs, ZIM et fichiers exclus ne sont pas
qualifiés. En cas d'interruption d'export, un dossier partiel peut subsister :
ne pas le considérer comme une livraison complète ; relancer vers un nouveau
dossier et vérifier le récapitulatif ainsi que chacun des rapports référencés.
