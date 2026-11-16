# Récupérer les sous-titres déjà proposés par la source

**Chantier en cours — 16 novembre 2026.** Complément de L6, non livré et non
accessible depuis le site. Le candidat de transcription 0.26.0 reste un chantier
distinct ; le numéro de cette prochaine fonction sera fixé après synchronisation
avec main et coordination du transfert de disque.

## Choix de réalisation

L'image Open WebUI épinglée inclut déjà `youtube-transcript-api==1.2.4` selon son
[manifeste amont](https://github.com/open-webui/open-webui/blob/v0.12.5/backend/requirements.txt).
Cette bibliothèque permet de lister les pistes YouTube, distinguer celles déclarées
fournies et automatiques, puis récupérer texte et temps sans télécharger le média.
Voir sa [référence versionnée](https://github.com/jdepoix/youtube-transcript-api/tree/v1.2.4).
La présence d'une langue ou d'une origine déclarée ne prouve ni fidélité ni droits
de redistribution. Le manifeste n'est pas un nouvel essai du conteneur Windows.

La piste retenue évite pour l'instant un outil de téléchargement supplémentaire.
`yt-dlp` a été examiné comme solution plus large ; il ne devient pas une dépendance
pour récupérer seulement les paroles. Le besoin reste une action explicite avec
Internet, puis un usage local sans Internet. Hors ligne, absence de piste ou refus
du fournisseur, la transcription audio locale reste l'autre parcours ; aucun
blocage distant ne doit être présenté comme une absence de parole dans le média.

## Première partie codée, hors parcours utilisateur

`pilot/provider_subtitles.py` valide les références YouTube et les métadonnées
source ; une URL arbitraire n'est jamais passée à un téléchargeur. La fonction
réseau n'est appelée ni à l'import ni à l'ouverture de Collections. Une session
ne reprend pas les identifiants/proxies d'environnement ; domaines, délais et
volume de réponse sont bornés. Les erreurs libres, URLs et cookies du fournisseur
ne deviennent pas des messages publics. Aucun proxy ou contournement de blocage
n'est prévu.

Une piste française disponible est prioritaire, puis la langue parlée déclarée,
puis l'anglais. Dans une même langue, la piste déclarée fournie passe avant celle
déclarée automatique. Aucune traduction en ligne n'est demandée implicitement.
Les autres langues pourront passer dans la file de traduction locale.

Les lignes et temps bruts seront conservés dans le rapport privé. Les lignes au
même début sont jointes sans retirer leurs mots ; les autres chevauchements
raccourcissent uniquement le temps d'affichage jusqu'au début suivant. Chaque
ajustement reste enregistré. Des valeurs invalides ou un texte trop grand sont
refusés au lieu de devenir une piste vide « réussie ». Ce choix doit être montré
dans le futur lecteur et vérifié sur les pistes effectivement récupérées.

Neuf tests sans réseau passent : références, priorité de langue/origine,
chevauchement, conservation des mots, refus des temps invalides, volume et fermeture
de réponse, session explicite et refus d'un autre domaine avant transport.
Cela ne valide pas la compatibilité réelle avec YouTube.

## Suite nécessaire

- Ajouter la file durable, l'arrêt et la reprise, la publication conditionnelle et
  la conservation des originaux. Vérifier source locale inchangée et identité de la
  vidéo distante ; ne pas deviner un identifiant depuis un titre quelconque.
- Intégrer récupération et choix de langue dans les commandes vidéo existantes,
  avec résultat compréhensible et export privé ; ne pas ajouter un écran technique.
- Joindre la piste complète à l'index et au lecteur, puis sa traduction française
  locale lorsqu'elle est nécessaire. Tester suppression/changement de source,
  interruption, réponse tardive et panne réseau.
- Exécuter une recette réelle de récupération et de lecture ; les refus et limites
  du fournisseur sont aussi des résultats. Aucun contenu de Marc n'est disponible
  dans le runner pour cette validation.
- Inventorier et traiter les vidéos/pistes contenues dans les ZIM séparément. Le
  blocage anti-robot de la page de spécification consultée ne permet pas de déduire
  l'absence de pistes dans ces archives ; utiliser la bibliothèque libzim épinglée
  et de petites archives générées pour développer le parcours.
