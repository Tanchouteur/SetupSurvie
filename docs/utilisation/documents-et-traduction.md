# Documents, favoris et traductions

**Guide de référence — pilote 0.41.0, 17 novembre 2026.** Fonction du portail ; les conversations Open WebUI restent distinctes.

## Lire et retrouver un document

Les résultats PDF proposent **Lire le PDF** dans une page dédiée : pagination,
zoom, recherche dans le texte et illustrations d’origine. Le lecteur PDF.js est
fourni localement, sans service Internet ni IA. **Texte et assistant** conserve
l’aperçu textuel pour poser des questions. Le bouton d’ouverture directe et le
téléchargement restent disponibles si le lecteur rencontre un problème.

Depuis 0.41.0, les grandes images sont redimensionnées pour l’affichage avec
un budget de canvas explicite. Le PDF source, ses pages et ses illustrations
restent intacts ; l’ouverture directe et le téléchargement donnent toujours
l’original. Cela ne borne pas toute la mémoire nécessaire au décodage et ne
garantit pas la lecture de tout PDF sur un téléphone.

Avec le profil choisi, **Ajouter aux favoris** marque un document ou un article
Kiwix. Les favoris sont propres au profil, enregistrés côté serveur et conservés entre
appareils. Dans la Bibliothèque, **Mes favoris** affiche la liste ; saisir une
recherche la limite au contenu de ces documents, y compris les pages tardives des
PDF. L’assistant peut aussi chercher dans vos favoris lorsqu’on le lui demande.
La limite actuelle est de 1 000 favoris par compte. Pour les articles Kiwix, la
recherche dans les favoris utilise le texte consulté au moment de l’ajout ; elle
ne garantit pas sa fraîcheur après remplacement d’une archive.

Le filtre **Traductions IA partagées** liste les traductions récentes ; une
recherche retrouve aussi les autres traductions indexées. Les filtres de langue
s’appliquent aux trois vues. Un document supprimé du disque peut rester dans les
favoris ; cela ne le rend pas disponible. Son étoile peut être retirée.

Depuis 0.1.29, les [profils locaux](profils-locaux.md) remplacent les mots de passe.
Les données dites privées ci-dessous restent hors du fonds public, mais toute
personne du réseau peut choisir leur profil pour les consulter.

## Choisir les documents d’une conversation — 0.17.0

Dans les résultats de la **Bibliothèque**, utiliser **Choisir pour l’assistant**
pour les documents à comparer. Le même bouton existe dans le lecteur textuel.
Le premier choix crée une conversation enregistrée, sans démarrer l’IA ; les
suivants s’y ajoutent. Le bandeau indique le nombre choisi et **Poser une question**
ouvre l’assistant. La sélection accepte douze références au maximum ; une page
précise de PDF peut être choisie séparément. Cette limite de dossier n’est pas une
limite de taille de la bibliothèque.

Dans l’assistant, la liste des documents reste repliée pour laisser la réponse
lisible. La déplier pour ouvrir ou retirer un document. La sélection est conservée
côté serveur après rechargement et à la réouverture de la conversation sur un autre
appareil avec le même profil. Retirer une référence ne supprime ni le fichier,
ni les messages, ni les traductions déjà faites. Créer une **Nouvelle conversation**
commence sans reprendre les documents de la précédente.

**Poser une question sur ce document** conserve son rôle : ouvrir une nouvelle
conversation autour de cette seule source. Un document ainsi choisi reste un
brouillon jusqu’à la première question ou traduction. Pour composer une sélection
persistante avant la question, préférer **Choisir pour l’assistant**.

Le dossier choisi est lu par passages adaptés à la question. Pour un PDF entier,
le moteur peut retrouver une page tardive déjà indexée dans ce fichier ; une page
explicitement choisie reste cette page. Sans correspondance indexée, le début
limité reste disponible et signalé. Le modèle ne lit pas automatiquement tous
les livres. Le suivi distingue les sources choisies, préparées et réellement
consultées ; un document illisible ne valide aucune citation et ne bloque pas
les autres. Voir le [guide de synthèse](synthese-documentaire.md).

Pendant une réponse, attendre sa fin ou l’annuler pour modifier la sélection.
Le serveur refuse aussi un deuxième envoi concurrent dans la même conversation.
Une référence déjà choisie mais devenue indisponible reste retirable. Une nouvelle
référence qui ne s’ouvre pas n’écrase pas la sélection précédente.

Les anciennes conversations à un document sont reprises. La compatibilité avec
l’ancien champ d’API `source` est conservée ; la liste s’appelle `selected_sources`.
Les conversations plus anciennes sans association ne sont pas reconstituées à
partir de leurs citations. Depuis une conversation ouverte, revenir à la
Bibliothèque puis choisir les documents voulus.

## Lire une version française déjà terminée — 0.21.0

Dans un document du portail, **Lire en français** apparaît lorsqu’une traduction
terminée a déjà été ajoutée aux documents partagés. Le bouton lit ce texte
localement, sans chercher sur Internet ni charger un modèle. **Voir l’original**
revient au texte source. Les articles Kiwix sont concernés lorsqu’ils sont ouverts
par le lecteur du portail ; l’interface Kiwix ouverte directement n’est pas modifiée.

Le lecteur PDF propose aussi **Lire en français**, puis **Voir le PDF original**.
Le texte français reste lié aux numéros de pages du fichier original. Les flèches
parcourent les pages traduites ; une page absente de la plage reste annoncée comme
non traduite. Revenir au PDF conserve la page et ses illustrations originales.
Le texte français ne reproduit pas la mise en page et ne traduit pas les dessins.
Le choix français peut être retrouvé au rechargement dans le même navigateur.

Si plusieurs versions partagées existent, un sélecteur affiche leur date et
l’édition originale connue. Une différence de taille/date du fichier original
signale **original modifié**. Une ancienne traduction dont la correspondance n’a
pas été enregistrée reste **à comparer**. Dans ces deux cas, l’ouverture de la
version française demande un choix explicite dans le lecteur ; elle n’est pas
associée automatiquement à la nouvelle édition. Ce contrôle utilise un repère
local de taille/date, pas une empreinte complète du PDF ou du ZIM : il ne certifie
pas que deux contenus identiques en taille/date soient identiques en sens.

Les avertissements suivent le texte français, y compris ceux sur les touches
manquantes. Les documents partagés restent lisibles après suppression de la
conversation. Les brouillons et anciennes traductions restées privées ne sont
pas exposés par ce lecteur. Ouvrir **Lire en français** ne relance aucune traduction ;
pour préparer une nouvelle version, utiliser le panneau de traduction ci-dessous.

Si la version française ne s’ouvre pas, revenir à l’original ou réessayer. Une
panne de cette option ne bloque ni l’original, ni les PDF, ni la recherche. Les
fichiers partagés restent également ouvrables depuis la Bibliothèque. Le modèle
peut être arrêté pendant cette lecture.

## Lire confortablement une traduction en cours — 0.39.0

Depuis la Bibliothèque, le panneau conserve ses commandes et les passages déjà
lus pendant les actualisations. L’état donne les passages et pages terminés,
ainsi que la page en cours ; **Lire les derniers passages traduits** permet de
rejoindre volontairement le dernier groupe prêt, sans déplacement automatique.
Une actualisation ne remet pas le texte au début et ne referme pas les comparaisons.
Dans l’assistant, **Lire le texte français** ouvre une fenêtre large sur ordinateur.

Les titres, listes, tableaux et formules présents dans le texte sont rendus dans
une présentation de lecture ; les simples retours de ligne de la prose peuvent
se réunir. Ce rendu ne reconstitue pas la composition exacte d’un PDF, ses colonnes
ou ses illustrations. Les pages originales et les comparaisons restent accessibles.
Le rendu ne change ni le texte enregistré, ni les contrôles, ni les exports.

## Traduire en français

Depuis **0.34.0**, les commandes restent dans le lecteur du portail. Dans le
lecteur PDF dédié, **Traduire ce PDF** les ouvre sans quitter le fichier. Ouvrir
ces commandes ne démarre aucun calcul. Ce n’est pas une traduction instantanée
de chaque page Kiwix ni une traduction de vidéo.

1. Dans une source anglaise, cliquer sur **Traduire en français**, ou **Traduction : ouvrir ou reprendre** si un travail existe. Choisir un travail à retrouver ou une nouvelle traduction. Les travaux sont ceux du profil courant, pour cet original ; une traduction limitée à des pages reste identifiée comme telle.
2. Choisir le temps de réponse. Pour un nouveau travail PDF, conserver la première page à 1 et la dernière vide pour tout le document, ou indiquer une plage. Les numéros désignent les pages du fichier, pas forcément la pagination imprimée. Les options permettent aussi de modifier les termes anglais/français avant le départ ; enregistrer les changements.
3. Cliquer sur **Démarrer la traduction**. Une conversation associée conserve le travail, sans remplacer la discussion en cours. Un lien permet de l’ouvrir. Les conversations existantes gardent également leurs commandes de traduction : une demande comme « traduit moi ce guide en français » peut déclencher la traduction dédiée. Avec plusieurs documents choisis, ce traitement porte sur le seul document indiqué.
4. Lire les passages terminés par groupes de dix, avec page/section, modèle utilisé, contrôle enregistré et **Comparer avec l’original**. La progression ne ferme pas les comparaisons ouvertes. Les propositions refusées restent signalées et séparées du texte traduit.
5. **Mettre en pause** conserve les passages terminés. Choisir au besoin un autre mode puis reprendre explicitement le reste. **Arrêter** conserve les passages terminés. **Supprimer ce travail** demande confirmation ; supprimer le travail privé n’efface ni l’original ni une version déjà publiée.
6. Une nouvelle traduction terminée est ajoutée automatiquement aux **documents locaux, visibles par tous**. Le panneau donne accès au document partagé et permet de retenter un ajout échoué. Les anciennes traductions privées restent privées jusqu’à publication explicite.
7. Télécharger le texte français permet aussi de conserver une traduction partielle ; les passages manquants y sont indiqués. Retrouver les travaux récents dans **Mon appareil → Travaux en cours → Mes traductions et synthèses**, ou depuis leur original.

Depuis **0.49.1**, le modèle reçoit un format de réponse centré sur le texte
traduit. GPT-OSS pouvait choisir le statut de refus proposé par l’ancien format
pour un passage ordinaire. Une réponse vide, interrompue ou signalée comme un
refus reste à reprendre. Les contrôles de traduction sont appliqués avant de
compter un passage terminé. Pour une traduction interrompue, utilisez
**Reprendre avec le modèle choisi** dans le travail existant.

Depuis **0.50.2**, si la réponse est vide, tronquée ou mal formée, ou si
le contrôle rejette le texte proposé, SetupSurvie retente le passage avec le
même modèle. Il le découpe en deux si une fin de phrase ou de ligne adaptée
est disponible. Chaque morceau est vérifié, puis le passage complet est vérifié
avant son enregistrement. Le nouvel essai écarte l’extrait du passage précédent
et conserve les termes préférés. Les passages terminés et leur numérotation
sont conservés, y compris quand on reprend un travail créé avant la mise à jour.
Un refus explicite ou un échec persistant laisse le passage en attente de reprise.

Le contrôle distingue aussi le verbe « a » et les mots élidés comme « s’il »
d’une unité de mesure, ainsi qu’un article « A » après un numéro de page isolé.
Une modification de la valeur ou d’une unité explicite
comme « A » (ampères) continue de bloquer la publication. Un ordinal anglais
comme « 1st » peut être rendu par « 1re » ou « première ». Une mesure
manquante reste bloquante même si le même chiffre figure dans un ordinal.

Le traitement continue quand le navigateur est fermé, tant que le serveur et le moteur fonctionnent. Après un arrêt du serveur, la traduction est mise en pause et attend une reprise explicite. Une pause du moteur, notamment le mode jeu, empêche un nouveau départ ou une reprise ; elle est aussi vérifiée entre les passages. Aucun démarrage forcé n’est effectué.

Depuis 0.1.18, le panneau de traduction peut se réduire et défiler sur les écrans
courts pour garder le champ de question et son bouton d’envoi accessibles.

Une traduction utilise la même file d’inférence que les questions du portail. Elle libère cette file entre les passages. Une seule traduction active par compte et quatre en attente ou en cours sur le serveur sont autorisées. Alterner les modèles entre questions et traduction peut provoquer des rechargements par Ollama et augmenter les délais.

Depuis 0.20.1, chaque passage reprend le **contexte configuré pour son modèle**,
limité par la capacité annoncée par le moteur local. Il ne revient plus toujours
à 8k. La sortie et une marge de format restent réservées ; un passage dépassant
ce budget est refusé sans être coupé silencieusement. Le changement de modèle ou
de contexte est préparé avant l’envoi du texte, avec une reprise bornée en cas
d’accusé de chargement vide. Cela préserve le passage à traduire, sans modifier
le modèle choisi ni lever une pause. Ce mécanisme ne garantit pas le fonctionnement
de tous les modèles ni le respect du sens ; les contrôles de traduction restent
nécessaires. Les réglages de contexte se trouvent dans
[Paramètres → Assistant](mesurer-assistant-et-memoire.md).

## Taille des documents et livres longs

**Limites relues dans le code 0.1.35 le 14 novembre 2026.** Un PDF de 500 pages
peut être accepté : la traduction ne charge pas tout le livre dans un seul
contexte. Le texte est extrait page par page, puis découpé en passages d’environ
2 200 caractères. Chaque passage terminé est enregistré ; pause et reprise
explicite conservent ce qui est déjà traduit. Un essai de 500 pages fictives vérifie désormais les instantanés, l’interruption,
la reprise et la dernière page publiée, avec traduction simulée. Il ne prouve
aucun délai garanti ni fidélité d’un vrai livre de 500 pages.

Pour les PDF locaux, les limites sont : fichier de **300 millions d’octets au
maximum (300 Mo décimaux)**, document de **1 200 pages au maximum**, **100 000
caractères par page** et **5 millions de caractères sur la plage demandée**.
Un fichier dépassant 1 200 pages est refusé même si la plage choisie est courte ;
il faut une copie découpée. Une plage peut réduire la quantité totale de texte,
mais ne contourne pas les autres limites. Un PDF chiffré est refusé. Les pages
sans texte extractible sont signalées et ne deviennent pas traduites par OCR.

Pour un guide textuel, l’aperçu doit être complet et faire moins de 500 000
caractères ; pour un article d’archive, moins de 100 000. La traduction intégrale
d’un aperçu déclaré incomplet est refusée. La mise en page, les images et la
cohérence d’un terme entre tous les passages d’un livre ne sont pas garanties.
Cette fonction ne produit pas de sous-titres vidéo.

## Ce qui est traduit et ce qui reste à vérifier

Les PDF sont lus dans le fichier original, page par page : la traduction n’est pas limitée aux quatre premières pages de l’aperçu. Les pages demandées sont découpées en passages courts. Le texte source de ces passages est conservé dans l’état privé : une reprise ne mélange pas un nouvel original avec le début d’une ancienne traduction.

Une page sans texte extractible est signalée comme telle. Elle peut être illustrée, blanche, numérisée ou demander une reconnaissance de caractères (OCR). Elle n’est pas comptée comme traduite. Le compteur « traitement terminé » n’affirme donc pas que toutes les pages illustrées ont été traduites.

**La traduction est du texte, sans conservation de la mise en page du PDF et sans traduction des images.** L’extraction peut désordonner un tableau ou perdre des caractères : contrôler l’original, surtout les mesures, doses, unités, avertissements et consignes. Le contrôle du format d’une réponse ne certifie ni sa fidélité ni sa sécurité.

Un refus explicite, une réponse vide, un format inexploitable ou une réponse interrompue n’est pas publié comme traduction réussie. Le panneau explique le blocage et permet de reprendre avec un autre modèle. Ce parcours ne garantit pas l’absence de refus de tous les modèles ; leur fidélité réelle reste à évaluer sur les documents de Marc.

Limites actuelles : PDF accessible de 300 Mo maximum, 1 200 pages maximum, 100 000 caractères par page et cinq millions de caractères pour la plage choisie. Un PDF protégé est refusé explicitement. Pour les autres guides et articles, le texte intégral disponible dans l’index ou le lecteur est utilisé ; un aperçu atteignant sa limite de taille est refusé plutôt que présenté comme un document entièrement traduit. Les plages de pages sont réservées aux PDF. Aucun OCR automatique ni traduction d’un ZIM entier n’est ajouté.

## Garder les mêmes mots dans un document — 0.32.0

Dans le panneau de traduction, ouvrir **Mots à traduire de la même façon
(facultatif)**. **Ajouter un mot**, indiquer le terme original et sa forme
française, puis **Enregistrer ces mots** avant de lancer la traduction. La liste
peut rester vide ; il n’est pas nécessaire de la remplir pour traduire.
Un exemple de mécanique est `bearing` → `roulement` ; un même mot peut avoir
un autre sens selon le document. Ces choix ne sont pas une validation technique.

La liste (40 entrées au maximum) appartient au profil choisi et se réutilise dans
ses prochaines traductions. Chaque travail prend une copie des choix à son
lancement. Modifier ensuite la liste ne change ni les passages déjà traduits ni
ceux encore à faire dans ce travail. Le panneau distingue les mots du travail
et les préférences pour la suite. Les mots non enregistrés demandent de les
sauvegarder avant de lancer la traduction. Retirer toutes les entrées et
enregistrer rétablit une traduction sans vocabulaire imposé pour les travaux futurs.

Seuls les mots ou expressions repérés dans le passage courant sont proposés au
modèle ; aucun remplacement automatique n’est fait dans le texte. Si la forme
française demandée n’est pas retrouvée, un avertissement invite à relire le
passage. Il peut aussi s’agir d’une flexion grammaticale correcte ; cet avertissement
ne bloque donc pas à lui seul. Il suit le texte exporté et les versions partagées.
La liste complète reste dans le travail privé et son export, sans être publiée
comme un glossaire familial indépendant.

Pour les nouvelles traductions, le modèle reçoit aussi la fin du passage traduit
juste avant (600 caractères source et français au maximum chacun). Ce repère
reste séparé du texte à traduire et n’est pas une source supplémentaire. Il est
retiré si le contexte disponible est trop petit ; les contrôles du passage courant
continuent à refuser les nombres ajoutés, même s’ils figuraient dans le repère.
Une page sans texte extractible interrompt ce lien avec le passage précédent.
Le modèle peut néanmoins se tromper : la cohérence du vocabulaire et du sens
reste à relire, notamment sur un livre long.

La liste et la progression restent sur le serveur lors d’une pause ou d’un
redémarrage ; aucune inférence ne reprend automatiquement. Les anciennes
traductions gardent leur fonctionnement, sans emprunter les mots enregistrés plus
tard. Supprimer un travail enlève sa copie de vocabulaire, tout en gardant la
liste réutilisable du profil, l’original et toute version déjà partagée.

## Contrôles de traduction — depuis 0.1.28

Chaque **nouveau passage** passe des contrôles locaux avant d’être enregistré
comme traduit. Ils ne demandent ni Internet ni seconde inférence.

| Résultat | Comportement et action |
| --- | --- |
| Nombres ajoutés, perdus ou modifiés ; association nombre/unité reconnue différente ; long texte identique à la source | Passage refusé, traitement interrompu. La proposition reste visible comme **refusée, ne pas utiliser** ; elle ne compte pas comme traduite et n’est pas publiée. Choisir un autre mode puis **Reprendre**. Les passages terminés restent conservés |
| Réponse beaucoup plus courte ou longue ; négation anglaise sans équivalent français repéré ; blancs ou caractères manquants dans une commande extraite | Passage conservé avec **À relire**. L’avertissement apparaît dans la conversation, l’export et le document local partagé. Comparer à la source |
| Aucune anomalie repérée | Passage conservé avec la mention **Contrôles limités**. Cela ne valide pas son sens ni sa fidélité |
| Ancien passage déjà traduit | **Pas de contrôle enregistré**. Il n’est pas présenté comme validé rétroactivement ; les anciennes publications restent inchangées |

Dans chaque passage, **Comparer avec le texte original** affiche l’instantané
source conservé pour le travail, sous la traduction. Les formules protégées sont
transmises au modèle sous forme de repères, puis réinsérées à l’identique par
le logiciel ; leur contenu n’a pas besoin d’être retapé par le modèle. Le bouton **Consulter l’original**
ouvre le document pour contrôler aussi la mise en page et les tableaux. Le texte
source et une proposition refusée restent privés ; le partage n’ajoute que les
avertissements aux traductions acceptées. Les avertissements ne sont pas un
certificat de relecture humaine.

Le modèle reçoit la consigne de garder les chiffres, signes, occurrences et
unités, sans conversion. Les contrôles tolèrent notamment `1.5` / `1,5`, `1 000` /
`1000`, et les noms d’unités courants traduits. Ils sont conservateurs : un nombre
écrit en lettres, une conversion correcte ou un format de milliers ambigu peut
bloquer le passage. Il n’existe pas de bouton pour accepter silencieusement une
proposition refusée. Si un autre mode reste bloqué, conserver l’original et
l’export des passages terminés ; une traduction manuelle reste nécessaire.

Depuis la version **2** de ces contrôles (0.20.1), un avertissement signale aussi
certains trous du texte source, comme une touche dessinée dans un PDF devenue
« Press the         key ». Le programme ne reconstitue pas la touche. Comparer
la page originale ; le seul contrôle des nombres ne rend pas cette commande
utilisable. La détection est partielle et peut donner de faux positifs ; elle
ne réalise aucun OCR. Les anciens rapports gardent leur version et leurs résultats.

La version **3** des contrôles (0.32.0) reconnaît aussi les chiffres joints à un
libellé par l’extraction PDF : `Chapter4` et `Chapitre 4` portent le même nombre.
Une modification vers `Chapitre 5` ou de `X7` vers `X8` reste bloquante. Les
seuils de longueur, négations et unités ne changent pas. La consigne préserve
aussi les noms inscrits sur les touches et boutons. Si une inscription reconnue
comme `CALL` est remplacée par `APPEL`, un avertissement demande de comparer
l’original et l’appareil ; toutes les inscriptions et interfaces ne sont pas
reconnues automatiquement.

La version **4** des contrôles (0.37.3) protège aussi les formules extractibles
présentes dans les articles HTML. Le lecteur conserve leurs fractions, indices,
puissances et groupes sous forme de blocs de notation, sans recalculer ni
compléter la source. Une structure non prise en charge affiche **Formule non
extractible : consultez l’original illustré**. Une formule représentée uniquement
par une image sans alternative reste à lire dans l’original ; il n’y a pas d’OCR.

Pendant la traduction, le logiciel conserve les blocs originaux et demande au
modèle de traduire le texte autour de repères. Chaque repère doit revenir une
seule fois, dans le même ordre ; sinon le passage et sa proposition restent
refusés. Après réinsertion, les blocs doivent conserver les mêmes formules.
Les passages ne coupent pas ces blocs en deux ; une formule exceptionnellement
longue peut dépasser le contexte disponible et bloquer proprement la traduction.
Cela ne valide ni le raisonnement autour d’une formule ni sa correspondance
avec une illustration. Les anciens rapports gardent leur version.

Les textes déjà extraits avec des équations manquantes ne sont pas réparés
par la mise à jour. Utiliser l’article original pour un nouveau travail ; une
traduction en reprise conserve son ancien instantané. Les originaux, anciennes
traductions et publications ne sont pas remplacés automatiquement. Voir les
[preuves et limites](../essais/2026-11-17-formules-documentaires.md).

Les unités reconnues forment une liste limitée (masses, volumes, longueurs,
durées, températures, quelques unités électriques et pressions). Les tableaux, le sens des
formules, les unités rares, négations complexes et changements de sens ne sont pas
validés. Une phrase peut conserver les mêmes nombres tout en disant l’inverse.
Les seuils de longueur et la recherche de négations sont des indices, avec des
faux positifs et des erreurs possibles non détectées. Les passages privilégient
les fins de phrase quand leur taille le permet ; cela ne donne pas au modèle le
contexte du manuel entier. Aucun glossaire technique ni moteur spécialisé évalué
n’est encore ajouté. Pour une consigne importante, comparer l’original ou utiliser
une traduction relue par une personne compétente.

## Partage, sauvegarde et suppression

**Depuis 0.1.25, une nouvelle traduction terminée devient un document local
partagé**, consultable sans compte sur le réseau familial. Les brouillons,
instantanés sources, conversations et exports privés restent rattachés au profil, hors du fonds documentaire partagé.
Les anciennes traductions restent privées : leur propriétaire doit choisir
**Ajouter aux documents locaux · visible par tous** pour les publier. Cette mise
à jour ne publie pas rétroactivement des travaux privés.

Le document partagé est un fichier HTML français indépendant, marqué **Traduction
IA non vérifiée**. Il conserve le titre, la date et l’édition connues de l’original,
les pages traitées, les modèles employés et un lien vers l’original. Une traduction
d’une plage de pages l’indique ; des pages sans texte donnent une traduction
signalée partielle. Les nombres, unités et consignes doivent toujours être
comparés à l’original. Une traduction ne constitue pas une seconde source fiable.
Les droits de l’original continuent de s’appliquer ; le partage local n’accorde
aucune autorisation supplémentaire de revente ou redistribution.

Supprimer une conversation supprime ses associations et ses traductions privées,
**mais conserve les documents déjà publiés** et les favoris. Une traduction active
doit d’abord être mise en pause. Une traduction terminée dont l’ajout automatique
a échoué bloque la suppression pour préserver son résultat : réessayer l’ajout
avant de supprimer la conversation. Les originaux ne sont pas modifiés.

Les fichiers partagés sont dans `library/guides/TRAD-….fr.html` ; les sauvegarder
avec les autres documents locaux. Les sauvegardes privées conservent associations,
progression, favoris et métadonnées, mais ne remplacent pas une copie du fonds.
Après interruption entre l’écriture du fichier et son indexation, le pilote
réessaie l’ajout au démarrage, sans relancer d’IA. Une inférence interrompue reste
en pause. Un fichier publié modifié à la main est conservé, sans écrasement.
La publication est actuellement limitée à 20 millions de caractères traduits.

## Si une fonction ne répond plus

Le lien **Lecture de secours** ouvre `/secours.html`. Il donne un accès aux fichiers
locaux et à Kiwix sans API du pilote ni moteur IA. Sa liste est la dernière liste
statique produite par l’indexation (ou le catalogue d’installation précédent) ; son
filtre porte sur les titres. Si elle manque, le lien Kiwix reste accessible. Le
serveur web et les disques doivent toujours fonctionner. Selon le navigateur, un
PDF ouvert directement peut être téléchargé plutôt qu’affiché : l’ouvrir ensuite
avec le lecteur du téléphone ou du PC.

Les nouveaux modules de favoris, publication et rendu PDF ont des replis séparés.
Un échec d’indexation au démarrage conserve le dernier index validé et cesse de
bloquer le démarrage après 30 secondes ; le travail déjà lancé en thread peut
continuer. Une base SQLite corrompue, un disque plein ou une panne du serveur web
peuvent affecter plusieurs fonctions : suivre le [guide de reprise](../exploitation/coupures-et-redemarrage.md)
et conserver une sauvegarde indépendante.

## Actualiser le laboratoire de Louis

Dans le clone du projet sur le PC Bazzite, vérifier que le travail local est conservé puis récupérer `main` avec `git pull --ff-only`. Depuis ce même dossier :

```bash
python3 scripts/lab_refresh_library.py
```

Le script vérifie le montage SSD, actualise le portail, le pilote et son contexte documentaire puis redémarre uniquement les services documentaires concernés. Il conserve les états et ne démarre pas Ollama. Recharger ensuite le navigateur et vérifier la version **0.1.29** avant le nouvel essai. Cette procédure est propre au laboratoire ; pour une installation portable, utiliser le [paquet logiciel et sa procédure de mise à jour](../exploitation/mises-a-jour-et-bibliotheque-pilote.md#petites-mises-à-jour-du-logiciel).

## Vérifications et limites

Les tests utilisent de petites fixtures et une inférence simulée : isolation des
comptes, publication et reprise après erreur d’écriture/indexation, conservation
après suppression de conversation, recherche dans les favoris et accès PDF par
plages d’octets. Les recettes navigateur testent le rendu PDF réel, le parcours
partage/favoris et les replis avec API, lecteur ou module optionnel indisponibles,
entre 320 et 1 366 pixels. La vérification de la livraison 0.1.25, le 13 novembre, comptait 261 tests,
dont 3 tests COM Windows ignorés sous Linux, sans échec ; le parcours documentaire
avait aussi été exécuté avec Chromium via Playwright MCP. Voir `tests/test_document_library.py`,
`tests/browser_documents.js` et la CI du commit concerné.

Les résultats de la livraison initiale 0.1.16 (162 tests, un test Windows ignoré)
restent historiques. Les tests simulés ne prouvent ni la fidélité d’un modèle réel,
ni la tenue physique du stockage après coupure. Safari sur iPhone, les gros PDF
et les performances avec le fonds complet restent à vérifier sur les clients.
Aucun OCR automatique ni pièce jointe privée multiple n’est ajouté par ce patch.

Pour 0.1.28, `tests/test_translation_quality.py` vérifie les erreurs de nombres,
unités, signes, les formats tolérés, la reprise sans perte et les limites des
heuristiques. `tests/browser_translation_quality.js` injecte une mauvaise dose
fictive puis un résumé trop court et vérifie comparaison, avertissements,
publication et disposition mobile. Ces tests utilisent des réponses simulées ;
aucun résultat de fidélité sur modèle réel n’en est déduit.

Vérification locale 0.1.28 : **290 tests sans échec, dont 3 tests COM Windows
ignorés sous Linux**. Le nouveau parcours de contrôle a aussi été exécuté avec
Chromium via Playwright MCP. La CI du commit de livraison exécute les contrôles
Windows et les parcours Chromium/WebKit ; ces moteurs ne remplacent pas un essai
sur iPhone physique.


Depuis 0.18.0, le [parcours de synthèse longue](synthese-documentaire.md#lire-un-livre-entier-par-étapes--0180)
peut lire les textes choisis par étapes conservées et produire une synthèse
commune. Il crée sa propre conversation ; la traduction reste une action distincte.


Le [guide des illustrations](illustrations-et-references.md) décrit les visuels
originaux proposés dans l’assistant depuis 0.19.0. Leur affichage conserve
les légendes d’origine ; il n’ajoute pas de traduction des libellés ni d’OCR.

## Lire pendant que le document se traduit — 0.28.0

Déplier le panneau de traduction dans la conversation. Dès qu’un passage est
terminé, son texte français apparaît : vous pouvez commencer à lire pendant que
les suivants sont préparés. Le suivi indique les pages/sections entièrement
traduites, les pages commencées et celle en cours, en plus des passages. Une page
illustrée sans texte exploitable reste signalée, sans être comptée comme traduite.

Les actualisations ne referment plus une comparaison avec l’original et ne
remplacent pas un passage déjà prêt. **Passages suivants/précédents** parcourent
le texte par groupes de dix. **Lire les derniers passages traduits** rejoint
volontairement la fin disponible ; **Lire depuis le début** revient au premier
groupe. L’arrivée d’une nouvelle page ne vous déplace pas automatiquement.

**Lire le texte français** ouvre une fenêtre de lecture dédiée, avec le suivi
et le texte ; la saisie de conversation ne réduit plus la place disponible.
**Fermer la lecture**, Échap ou le retour du navigateur la ferment sans arrêter
la traduction. Le navigateur peut retrouver cette fenêtre après rechargement.

Le navigateur retrouve le groupe de passages lu après rechargement ou retour à
la conversation, pour ce profil et cette traduction. Pause et reprise gardent
cette position. Sur un autre appareil, le travail traduit est conservé côté
serveur, mais cette position locale n’est pas transférée automatiquement.
Lire ou recharger ne reprend pas une traduction en pause.

Le brouillon en cours reste dans la conversation. Sa publication dans les
traductions partagées attend la fin du traitement ; les avertissements de
traduction automatique restent visibles dès les premiers passages.

## Gérer une traduction — 0.29.0

Les commandes se trouvent dans le panneau de traduction et dans **Lire le texte
français** pendant la lecture :

- **Mettre en pause** interrompt le passage en cours et conserve les précédents.
- **Arrêter la traduction** conserve aussi le texte, avec l’état **Arrêtée**.
  Elle ne repart pas en rechargeant la page ou en redémarrant le serveur.
- **Reprendre avec le modèle choisi** poursuit seulement les passages restants,
  après pause, arrêt ou erreur, lorsque le moteur est disponible.
- **Supprimer la traduction** retire définitivement ce travail privé et ses
  passages après confirmation. L’original, la conversation et toute traduction
  déjà partagée dans la bibliothèque restent conservés. Le message de
  confirmation rappelle cette différence. On peut ensuite lancer un nouveau
  travail sur le même document.

Arrêter ou supprimer annule et attend le traitement en cours. Aucune de ces
commandes ne décharge un modèle utilisé ailleurs ni ne force le mode jeu. Les
versions partagées sont des documents indépendants : leur retrait de la
bibliothèque ne fait pas partie de la suppression du travail dans la conversation.


## Retour au lecteur PDF — correctif 0.37.2

Revenir sur la fenêtre du PDF pendant son chargement ne doit pas être interprété
comme un changement de profil. La vérification attend la fin de l’initialisation.
Si vous choisissez réellement un autre profil dans un autre onglet, le lecteur
ferme les commandes de traduction et vous demande de le recharger. Le document
original reste accessible ; aucune traduction n’est relancée automatiquement.
