# Architecture — assistant, lecture et synthèse

**Référence d’architecture par domaine — découpée du README le 20 novembre 2026 (0.67.0).** Chaque section décrit un mécanisme au moment de sa livraison et reste valable sauf note de remplacement. Pour les fichiers, voir la [carte du code](carte-du-code.md) ; pour la vue d’ensemble, l’[architecture](README.md).

## Dossiers de lecture pratique (0.9.0)

`pilot/practical.py` lit les six objectifs et points dans `deploy/kiwix-themes.json`.
Les API publiques `/api/library/dossiers` et `/{id}` sont indépendantes de l’IA ;
`/{id}/search` déclenche seulement les recherches documentaires explicites.
Famille modifie les références via `/api/admin/library/dossiers/{id}/references`,
avec révision du dossier et du fichier source. `settings`, préfixe `dossier:v1:`,
conserve les notes communes sans migration. Export via `/api/admin/library/dossiers-export`.
Une erreur du module optionnel laisse les autres chemins accessibles. Le
[guide](../utilisation/dossiers-pratiques.md) décrit la reprise et les limites.

## Suivi documentaire de l’assistant — 0.15.0

`pilot/documentary.py` observe les sorties de recherche et de lecture, sans analyser
la prose du modèle. Les appels réutilisés partagent leur clé, les résultats et
sources sont comptés par identifiant. Le résumé versionné borne états et compteurs ;
les liens consultés sont filtrés séparément et restent privés à la conversation.
`engine.DOCUMENTARY` sert les observations vivantes sur l’API de demande.

La table optionnelle `documentary_evidence` conserve résumé et liens avec index de
conversation, référence de message et suppression en cascade. Le message et son
suivi final partagent la transaction ; la table ne dépend pas d’une clé étrangère
vers les demandes nettoyables. Les colonnes existantes et le schéma global 1 sont
conservés. Une table absente n’empêche ni réponse ni lecture d’ancien historique.
`assistant_metrics` garde seulement les nombres filtrés, utilisables en repli sur
la demande. L’annulation persiste les observations sans créer de faux message.

Le portail rend un élément `details` replié, mis à jour sans détruire son ouverture
ou le bouton focalisé. Les sources lues mais non citées restent ouvrables sans
être ajoutées aux références numérotées. Le [guide](../utilisation/sources-et-fiabilite.md#suivi-des-recherches-et-lectures-dans-lassistant)
et le [bilan](../essais/2026-11-15-suivi-documentaire-assistant.md) précisent les
limites : des opérations terminées ne prouvent ni exhaustivité ni bonne réponse.

## Préparation des demandes de synthèse — 0.15.1

`retrieval.search_subject` distingue une commande explicite de résumé de son sujet,
sans bannir « synthèse » des recherches techniques. `library.search_terms` l’utilise
sur le chemin commun ; la demande originale reste dans `Plan.original` et dans
la conversation. Les prépositions internes du sujet et les périmètres sont gardés.
Le concept frottement/friction est bilingue ; le mot de liaison « comme » n’est
plus un groupe obligatoire. `engine.document_request` prépare aussi les demandes
pratiques avec action reconnue, après ses exclusions géographiques/calculatoires.

Budget court de l’assistant, lecture de deux premiers documents et association
unique restent inchangés. Le [programme retenu](../decisions/assistant-recherche-et-synthese.md)
sépare ce correctif du travail multi-source, de la sélection de passages et de
la boucle d’outils contrôlée. Aucun modèle ni schéma de données ne change ici.

La session de modèle (`pilot/model_session.py`) prépare le modèle cible par un
appel local sans messages lorsqu’un autre est chargé ou qu’un contexte connu
change. Le planificateur Ollama garde la responsabilité du déchargement. La
session dispose d’une seule reprise pour préparation/flux vide/erreur transitoire
avant toute sortie, partagée entre tours d’outils ; elle ne rejoue jamais un outil
et vérifie l’état volontaire du moteur avant préparation/reprise. Les sorties
partielles et erreurs restent distinctes d’une absence documentaire. Voir le
[guide des mesures](../utilisation/mesurer-assistant-et-memoire.md).

## Dossiers documentaires — 0.16.0

`pilot/research.py` choisit des passages correspondant aux concepts bilingues de
la question, avec positions dans le texte extrait et budget UTF-8. Il distingue
les documents/pages, élimine les textes identiques et conserve les avertissements
de traduction. `read_sources` est un outil de lecture par lot, limité à douze
candidats et trois lectures simultanées. Le cache de sources est propre à la demande.

La préparation appelle le moteur commun avec le budget documentaire long et
adapte le dossier à la place restante, sans changer modèle ou contexte conseillé.
Le premier tour documentaire spécialise les outils ; les autres outils restent
disponibles aux tours suivants et dès le départ pour une demande géographique.
Une consigne secondaire de réponse reste dans la conversation complète et n’est
pas imposée à la première recherche du sujet principal.

Deux tours sans preuve documentaire nouvelle conduisent à la rédaction. Pour une
synthèse explicite, les références numériques sont contrôlées contre les passages
consultés. `citation_links.py` peut demander une association JSON de fragments
numérotés par le serveur et de sources lues, sans régénération des faits.
Ce contrôle ne vérifie pas le sens. Un échec conserve le texte utile avec avertissement,
ou les extraits si une source inconnue est citée, et l’état incomplet/échoué. Les propositions refusées
restent dans les traces privées, en dehors des mesures numériques.
Les instructions sont regroupées dans le premier message système pour éviter
une fin de conversation système sans marqueur de génération dans certains modèles.
Le lecteur de métadonnées reconnaît aussi les modèles dont le gabarit ne présente
les outils qu’après le dernier message utilisateur ; leurs définitions de confiance
restent alors visibles après les résultats d’outils, sans élever ces résultats au rôle système.

## Sélection documentaire persistante — 0.17.0

`conversation_document_choices` conserve la liste ordonnée privée des références,
avec cascade sur la conversation. La table historique `conversation_sources`
conserve le premier document pour les anciens lecteurs. Aucune conversation ou
traduction existante n’est convertie destructivement ; le schéma de livraison
reste 1. L’absence de la table optionnelle laisse utilisable l’association simple.
Après un retour à un ancien code, une référence principale retirée ou différente
ne ressuscite pas automatiquement la liste multiple précédente.

L’API `POST /api/conversations` crée une conversation avec une sélection sans IA ;
`PUT /api/conversations/{id}/sources` remplace cette liste après contrôle du profil.
Les questions acceptent `source_ids`, et conservent le champ historique `source_id`.
Le serveur refuse les changements et les doubles questions pendant une réponse.
La lecture réelle au moment de la demande reste distincte du titre enregistré.
Les métadonnées et textes documentaires passent par les résultats d’outils, sans
être élevés au rôle système. La traduction choisit son document et conserve les autres.

Pour un PDF entier, `focused_page` interroge uniquement ses passages déjà indexés,
avec le vocabulaire commun, puis conserve l’identité de la page retenue. Le travail
SQLite se fait dans un thread dont l’annulation attend la fermeture. Une page
explicitement associée n’est pas remplacée ; sans résultat, l’aperçu demeure limité.
Cette sélection n’est ni un OCR ni une synthèse exhaustive de toutes les pages.

## Lecture longue et notes reprenables — 0.18.0

`pilot/document_text.py` partage l’extraction complète avec les traductions :
PDF depuis le fichier d’origine, caractères conservés par segments et pages sans
texte explicites. Un changement de fichier détecté pendant la lecture annule son
instantané. Pas d’OCR. Les plafonds sont documentés dans le [guide](../utilisation/synthese-documentaire.md#lire-un-livre-entier-par-étapes--0180).

`pilot/summaries.py` enregistre les tâches, entrées, textes et notes dans quatre
tables optionnelles `summary_*`, sans migration destructive du schéma 1. Le
parcours crée sa propre conversation, contrôle le profil et partage `engine.LOCK`
par étape. Il utilise `model_session` pour charger le modèle choisi et reprendre
un premier échec transitoire ; pas de changement silencieux de modèle/contexte.
L’arrêt du service attend ses tâches avant de fermer le cache documentaire.
Redémarrer marque le travail en pause et ne relance aucune inférence.

Chaque note initiale désigne un passage et un extrait dont le serveur vérifie
la présence exacte, à des différences d’espacement près. Les regroupements
adressent une note précise par `étape:note`, puis transportent seulement ses
sources et pages. Le graphe et les extraits originaux restent exportables ;
aucun raisonnement privé du modèle n’est conservé. Cette vérification de
provenance ne contrôle pas la fidélité sémantique des notes ni de la synthèse.
Le texte final et, au besoin, sa liaison de références utilisent les mêmes
budgets de contexte. Une sortie tronquée, un JSON invalide ou une citation
inventée ne termine pas son étape. Les brouillons sans références restent
incomplets et reprenables.

Les routes `/api/summaries` créent le travail ; `/{id}` consulte son suivi,
`/{id}/pause`, `/{id}/resume` le contrôlent et `/{id}/export` exporte le Markdown.
`GET /api/conversations/{id}` ajoute `summary_jobs`. La création accepte `question`,
`mode`, `conversation_id` et/ou `source_ids` ; les références sont copiées au départ.
Une tâche active par profil et quatre au total sont admises. Les questions,
changements de sélection et suppressions sont refusés dans sa conversation
active ; une reprise attend aussi la fin des autres travaux de cette conversation.
Les calibrations et comparatifs IA cèdent la priorité. Une panne du module
optionnel ne désactive pas la recherche, la lecture ni les autres conversations.

## Illustrations originales et références — 0.19.0

`pilot/illustrations.py` extrait les légendes HTML5 et anciennes vignettes,
conserve les images locales de la même archive et prépare des candidats issus
des seules sources lues. Les PDF proposent les pages retenues, pas un recadrage
de schéma. Le classement des légendes par sujet et la diversité des sources
précèdent le plafond de contexte. Les métadonnées non retenues restent hors des
paquets de lecture et des réponses API ; elles sont gardées dans l’instantané
privé pour une synthèse longue. Plafonds dans le [guide](../utilisation/illustrations-et-references.md).

Une demande visuelle prépare la sélection avant la rédaction via un petit JSON
sans pixels ; `source_illustrations` permet aussi au modèle de la demander après
ses autres lectures. Le serveur valide les identifiants candidats, conserve la
provenance et refuse les identifiants inventés. Le contrôle ne juge pas le sens
d’une légende ni le contenu d’une image. Les échecs restent locaux à la fonction.
Les champs `figures` et `figure_status` sont ajoutés au JSON des sources de
conversation, sans table ni migration destructive ; schéma de livraison 1.

`portal/source-figures.js` affiche les originaux avec légende et liens. Le rendu
PDF utilise PDF.js existant, un worker partagé, une file de rendu et des aperçus
limités à un million de pixels. Les URL temporaires sont libérées au retrait des
messages ; les ressources se chargent près de la zone visible. Aucun OCR ni
modèle vision. Les erreurs de ressource n’interrompent pas le portail.
`GET /api/illustrations/document` vérifie la référence/page et l’empreinte connue
avant/après le rendu. `/api/media` accepte aussi `source_id` et `revision` pour
les images d’article : même archive, type image et contrôle de version avant/après
lecture. Les paramètres historiques sans source restent compatibles.

`research.citation_spans` reconnaît les références simples, groupées et avec page
hors du code. Les mêmes formes deviennent des boutons dans le portail ; seules
les pages effectivement retenues bénéficient d’un lien direct vers cette page.
Une référence inconnue garde le contrôle d’échec. La validité du numéro ne certifie
ni l’affirmation ni l’usage de la pagination imprimée.

## La bibliothèque d’abord — 0.108.0

Depuis la 0.108.0, toute question qui porte un sujet est d’abord cherchée et
lue dans la bibliothèque, avant la rédaction : questions en « quel… », « que
faire… », « pourquoi… », et demandes courtes comme « tanner une peau ? ».
Auparavant, seules les questions en « comment… », de dimensions ou avec un
verbe d’action déclenchaient cette préparation ; pour les autres, un petit
modèle répondait souvent de mémoire. Restent exclus : salutations et
remerciements, calculs (« calcule », « combien », « convertir »), demandes de
position et demandes de vidéos, qui ont leur propre recherche.

Mesure sur le labo Bazzite (gemma4:e4b, 205 archives, une question par thème
de Marc, 68 questions) : réponses citant un document lu, 23 en 0.100.0 et 48
avec ce changement ; réponses marquées « Références à vérifier », 15 puis 5.
Ces essais ne valident pas la justesse des réponses.

## Procédures ordinaires — 0.19.1

Le choix des passages analyse tous les mots utiles de la question bornée, y
compris après les dix premiers termes ; la limite des requêtes globales reste
distincte. Les variantes ordinaires démarrage/poursuite servent à ce classement
de lecture, sans ajouter des exigences aux requêtes réseau.
Les demandes « comment… » et de dimensions préparent aussi le moteur commun,
sans liste de modèles d’appareils. La première question sert de sujet de recherche ;
une seconde question garde sa place dans la demande complète mais ne devient pas
une contrainte lexicale de la première. Décimales/abréviations restent intactes.

Si le modèle demande une recherche, le moteur prépare pour les résultats non lus
un premier paquet de quatre passages candidats au maximum, classés par le moteur
commun, avant sa rédaction. Les appels/résultats restent des paires complètes ;
les lectures explicites suivantes, périmètre et budgets restent disponibles.
Une référence dans une réponse documentaire ordinaire est contrôlée comme dans
une synthèse ; un résultat de recherche ne devient jamais implicitement une lecture.
Pour une lecture préparatoire automatique, les pages d’un même PDF sont comparées
sur le sujet et le début de section, en écartant les mots du titre répétés partout.
La meilleure page de chaque document reçoit la priorité ; les pages explicitement
choisies restent littérales. Les autres passages demeurent accessibles aux outils.
Le lecteur HTML préfère l’article principal ou le conteneur sémantique `main` ;
les pages anciennes sans ces balises conservent leur extraction. Les traductions
générées multi-pages gardent explicitement toutes leurs sections. La sélection
du plus grand article est une heuristique ; elle ne qualifie pas la couverture
d’un site entier. La couverture transmise au modèle garde statut, avertissement,
périmètre et compteurs utiles sans les diagnostics volumineux de chaque appel.
Le contexte produit est condensé pour garder plus de place aux textes utiles,
sans changer modèle ou taille de contexte.
L’allocation répartit les extraits courts entre plusieurs sources selon le budget ;
les omissions et lectures partielles restent explicites.

## Relances, conditions et appels d’outils — 0.20.0

`conversation_context.py` conserve seulement des pointeurs bornés vers les sources
de la dernière réponse : titres, identifiants, ancienne question, sans numéros ni
extraits hérités. Une relance référentielle relit au plus quatre sources ; une
sélection explicite reste prioritaire. Une demande explicite d’une autre collection
prépare sa recherche. Les numéros et observations sont recréés après lecture.
La reconnaissance linguistique des relances reste une heuristique.

`tool_protocol.py` reconnaît certaines propositions JSON textuelles d’outils
connus, sans les exécuter. Une reprise native au plus consomme le budget ordinaire ;
un nouvel échec donne `incomplete` / `tool_protocol`. Les exemples de code demandés
sont préservés. Les arguments natifs non JSON ou non objets reçoivent une erreur
d’outil au lieu de perdre toute la conversation. Ce contrôle ne promet pas la
compatibilité avec tous les formats de tous les modèles.

`procedure_review.py` prépare au plus 48 segments de 30 à 900 caractères, issus
uniquement des lectures de cette demande et contenant des marqueurs de conditions.
Un appel JSON contraint (256 tokens, délai 60 s, budget d’entrée vérifié) choisit
zéro à trois identifiants. Le serveur insère les extraits exacts avant la réponse,
avec source et échappement du balisage documentaire. Aucun fait réécrit ou segment
inventé n’est accepté. Un budget trop court, une sortie invalide ou une erreur
laisse la réponse disponible et enregistre une limite numérique.
La pertinence, les omissions et les paraphrases ne sont pas certifiées ; ce
complément ne remplace pas une vérification humaine ou matérielle.

## Budget des dossiers documentaires — 0.23.1

`engine.read_batch` réserve l’encadrement réel de l’appel `read_sources`, notamment
ses identifiants, avant lecture. `research.read` accepte une mesure de paquet :
le moteur compte le JSON compact puis son encodage comme chaîne du message outil.
Les appels hors conversation conservent la mesure standard. Le nombre de places
tient compte des métadonnées avant de répartir les passages, pour garder les
candidats prioritaires. Références et preuves ne sont enregistrées qu’après
admission ; aucun extrait déjà déclaré lu n’est retiré pour masquer le dépassement.
`reading_packets` exporte des volumes et comptes, sans identifiant ni texte.
Le diagnostic ajoute marge/dépassement estimés et conserve le contexte demandé
quand la limite native réduit le contexte transmis. Réglages et schémas inchangés.

## Extraction mathématique — 0.37.3

`html_text.Text` est partagé par le lecteur, l’index complémentaire d’archives et
la recette d’extraction documentaire du laboratoire. `math_text` est un lecteur
borné de MathML de présentation : alternative auteur, annotation TeX ou notation
structurée d’un sous-ensemble explicite. Fractions, racines, scripts et matrices
simples sont conservés ; structures inconnues et dépassements sont signalés.
Aucune résolution externe, OCR, évaluation mathématique ou nouveau composant.

`document_text.chunks` conserve les blocs de formule entiers. `research.passages`
réduit une fenêtre coupant une formule, sans augmenter son budget ni modifier
les offsets de la source. `translations.translate` masque les blocs par des
repères propres au passage et les réinsère sans retouche si leur suite est exacte.
Un repère modifié, perdu, ajouté ou réordonné bloque la proposition privée.
`translation_quality` version 4 compare ensuite les blocs et garde les contrôles
numériques existants ; aucune validation générale du sens n’est revendiquée.

Depuis 0.38.3, `engine.fit_context` utilise le préfixe protégé pour les résultats
de lecture simples et par lots. Les `next_offset` restent les positions source
exactes, même quand une formule est entièrement retirée de l’extrait compacté.
`math_text.reading_window` borne aussi la lecture explicite `read_source` à
3 500 caractères, revient au début d’une petite formule si nécessaire et omet
un bloc trop long avec `formula_omitted`. Un résultat sans texte n’est pas compté
comme nouvelle lecture. Aucun offset d’un état sauvegardé n’est réécrit.

Le format de construction des compléments SQLite passe de 1 à 2. L’index déjà
publié reste lisible pendant la reconstruction ; une interruption conserve
l’ancienne publication. Le schéma des données personnelles reste à 1. Les index
natifs Kiwix, instantanés de travaux et anciens fichiers texte ne sont pas réécrits.
Voir la [procédure d’indexation](../utilisation/indexation-archives.md) et le
[bilan réel](../essais/2026-11-17-formules-documentaires.md).
