# Sous-titres français : validation de chaque vidéo

**Protocole cible retenu — 14 novembre 2026, outillage non livré.** Louis demande
explicitement que la récupération ou la création de sous-titres français soit
validée pour chaque vidéo. Ce document complète le
[lot L6](../decisions/plan-ameliorations-marc.md#l6--vidéos-et-sous-titres-français-hors-ligne)
et le rapport R6 ; ce n’est pas le bilan d’un inventaire ou d’un essai réel.

## Périmètre et inventaire attendu

Recenser les vidéos réellement présentes dans la bibliothèque locale, y compris
leurs pistes déjà associées. Garder un identifiant stable lié à la source et à
son édition ; dédupliquer sans perdre les liens des collections. Un titre ou un
lien vers une vidéo absente n’est pas une preuve que son média est disponible.
Les archives non examinées, entrées illisibles et médias inaccessibles doivent
rester dans le bilan : un inventaire partiel ne peut pas être annoncé exhaustif.

Chaque vidéo doit avoir une ligne exportable avec :

- collection, titre, identifiant de source et révision du média ;
- présence du média et de l’audio, durée/langue si établies, sinon inconnues ;
- pistes trouvées, langues et formats, provenance et origine humaine/automatique ;
- action choisie : récupérer une piste française, traduire une piste existante,
  transcrire puis traduire, ou expliquer pourquoi aucun traitement n’a abouti ;
- progression, parties manquantes et erreurs, résultat des contrôles techniques,
  portée/date de la relecture humaine et prochaine action.

Privilégier une piste française existante exploitable ; si elle manque, examiner
une piste source puis la transcription locale. Une piste distante encore non
récupérée ne devient pas disponible hors ligne. Conserver provenance et conditions
d’usage des pistes récupérées. Pour une vidéo sans parole, enregistrer explicitement
ce constat et la façon dont il a été vérifié, plutôt qu’un faux sous-titre vide validé.

## Contrôles pour chaque piste préparée

Vérifier le fichier lisible, les segments ordonnés, les temps cohérents avec la
durée du média, les segments non vides et les parties non traitées. Une langue
déclarée ou détectée ne garantit pas que toute la piste est française. Signaler
les anomalies de chiffres, unités, négations et vocabulaire technique ; aucun
de ces contrôles ne certifie à lui seul le sens de la traduction.

Lire la piste française dans le lecteur local, sans Internet et sans moteur IA,
avec sélection de langue, désactivation et retour à l’original. Vérifier la
synchronisation à plusieurs positions et après déplacement dans la vidéo.
Conserver séparément les contrôles automatiques et l’essai de lecture réalisé.
La lecture sans IA utilise les fichiers préparés ; elle ne relance pas la création.

Prévoir une relecture humaine du début, du milieu, de la fin et d’un passage
technique utile. Enregistrer ce qui a réellement été relu et les erreurs trouvées.
Cette vérification par extraits ne doit pas être nommée validation intégrale de
chaque phrase. Une relecture complète, si faite, reçoit son propre périmètre.

## Reprise et critères de fin

La préparation doit pouvoir être mise en pause et reprise explicitement, par
segments, sans modifier le média original ni perdre une ancienne piste saine.
Respecter le mode jeu et les réserves matérielles. Mesurer temps et espace sur
le PC cible ; les fixtures du runner ne prédisent pas la durée du fonds réel.
Une édition modifiée invalide la correspondance silencieuse avec les anciens
horodatages et demande un nouveau contrôle.

Le rapport doit distinguer au minimum **à préparer**, **en cours**, **piste
disponible, contrôles à faire**, **contrôles techniques réussis**, **relecture
humaine à faire/effectuée avec portée**, et **échec ou média indisponible**.
Ne pas fusionner tous ces états sous « traduit » ou « validé ».

La fin du lot sur la bibliothèque de Marc exige un bilan de chaque vidéo
inventoriée et des sources restant non examinées, puis la résolution ou une
décision explicite pour les exceptions. Une erreur récurrente, un média non traité
ou une partie manquante ne peut pas disparaître dans un taux de réussite global.
Le développement doit aussi couvrir piste existante, absence de piste, mauvaise
langue, piste mal formée/décalée, interruption/reprise et lecture hors ligne sur
de petits médias synthétiques. Ces essais ne remplacent pas le relevé vidéo par
vidéo du fonds réel.
