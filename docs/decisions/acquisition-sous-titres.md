# Récupérer les sous-titres déjà proposés par la source

**Choix actuel — 0.31.0, 16 novembre 2026.** Complément de L6 : récupération
explicite depuis le site, puis conservation locale, index et traduction française
optionnelle. Le [guide vidéo](../utilisation/videos-locales.md) décrit le parcours ;
le [bilan daté](../essais/2026-11-16-acquisition-sous-titres.md) sépare les preuves
réelles, simulées et les validations restantes. Les vidéos des ZIM demandent un
chantier distinct ; aucune couverture du fonds de Marc n’est certifiée.

## Source et dépendance retenues

L’image Open WebUI épinglée inclut déjà `youtube-transcript-api==1.2.4` dans son
[manifeste amont](https://github.com/open-webui/open-webui/blob/v0.12.5/backend/requirements.txt).
La [référence versionnée](https://github.com/jdepoix/youtube-transcript-api/tree/v1.2.4)
permet de lister les pistes, distinguer celles déclarées fournies/automatiques et
récupérer texte et temps sans télécharger le média. Le manifeste ne constitue pas
un nouvel essai de l’image sous Windows ; une dépendance absente produit une erreur
locale expliquée. Aucune image tierce n’est changée par cette livraison.

`yt-dlp` a été envisagé comme solution plus générale. Il n’est pas ajouté pour
ce seul besoin. Aucune traduction en ligne, authentification YouTube, reprise de
cookies ou proxy d’environnement, ni contournement d’un blocage fournisseur n’est
prévu. Hors ligne, piste absente ou fournisseur bloqué : le parcours de
reconnaissance audio locale 0.26.0 reste disponible après sa préparation.

## Choix et contrôles

La référence provient des métadonnées YouTube associées ou d’une adresse exacte
saisie volontairement. Elle n’est jamais devinée par titre. L’utilisateur reste
responsable de choisir le média correspondant ; le logiciel ne compare pas toutes
ses images ou son audio avec la source distante.

Choix automatique : français, puis langue parlée déclarée, puis anglais ; piste
fournie avant automatique dans la même langue. Un choix de langue explicite
accepte sa variante régionale. La langue et l’origine déclarées ne prouvent ni
fidélité humaine ni droit de redistribution.

Les lignes partageant un début sont jointes sans retirer leurs mots ; les autres
chevauchements raccourcissent seulement la durée d’affichage. Le rapport privé
conserve temps bruts et ajustements. Temps, ordre ou volumes invalides ne deviennent
pas une piste vide « réussie ». Le lecteur demande de vérifier l’alignement local.

Un enfant réseau borné produit une piste complète ; pause et arrêt du service
le rejoignent. La publication recontrôle la révision du média. Les originaux
restent intacts. La piste complète rejoint l’index ; sa traduction française
utilise ensuite la file locale si demandée. Un arrêt IA conserve la piste source.
Les états SQLite et les pistes suivent les sauvegardes et le transfert de disque.

## Étapes historiques et essai réel

Le premier essai R7, avant raccordement au portail, a récupéré en **813 ms** la
piste `fr-FR` déclarée automatique de la [présentation rapide de Kiwix](https://www.youtube.com/watch?v=4p2HsIAqitg) :
185 segments, 182 ajustements de durée, sans média téléchargé ni modèle chargé.
Son rapport reste privé dans `audio-transcription/report-provider-first.json` du
laboratoire R7. Les neuf tests de sélection et cinq tests de file initiaux
utilisaient des fournisseurs/modèles simulés ; ils ne validaient alors pas le site.

Le rejeu 0.31.0 avec le choix explicite « français » accepte cette piste `fr-FR`
en **1 386 ms**. Les mêmes 185 segments et 182 ajustements sont conservés, sans
traduction distante demandée. Rapport privé `report-provider-031.json`. Cette
observation datée n’atteste ni disponibilité future du fournisseur, ni alignement
avec un MP4 de Marc, ni fidélité ou droits de redistribution.

## Prochaine étape : les médias dans les ZIM

Une exploration locale du 16 novembre 2026 avec libzim **3.13.1** génère une ZIM
de **36 622 octets**, sans corpus téléchargé. Son article HTML référence un WebM
local de **1 135 octets**, une piste VTT anglaise de **57 octets** et une vidéo
distante fictive. L’énumération `_get_entry_by_id` retrouve les trois types MIME,
et `get_entry_by_path` restitue exactement les octets du média et de la piste.
Aucun accès réseau ni modèle. Recette et rapport privés temporaires :
`/tmp/ss031-zim-probe/`. Cela prouve la lecture de ces ressources synthétiques,
pas l’inventaire produit ni l’examen du fonds de Marc.

L’inventaire devra donc distinguer média interne présent et lien distant, joindre
les `<track>` à la bonne vidéo, conserver les archives non examinées et vérifier
l’édition. L’index documentaire actuel saute les archives ayant déjà un index natif
et ne conserve que les articles textuels : il ne suffit pas pour certifier cette
couverture vidéo. Prévoir une préparation reprenable qui examine aussi ces
archives, puis servir les médias/pistes via les lecteurs existants, avec limites
explicites. Cette étape reste prévue ; la 0.31.0 concerne `library/video/`.
