# Truc a faire trouver par Louis et Marc
> a maintenir a jour par l'ia quand elle avance dessus

- Chercher d'autre c'est pas sorcier a mettre dans la librairie
  - **Fait le 21/11 (0.85.0)** : les 19 thèmes C'est pas sorcier (édition 2026-11) sont dans le fonds de référence, plus Mondial Tissus et Maître Lucas. Marc fait aussi télécharger par son Claude des vidéos sur des sujets précis : à fusionner dans la référence (noter source, chaîne et sujet de chaque vidéo).
- faire le gros du trie de ce qu'on veux pas, récupéré ça et mettre a jour l'installeur par rapport a ça. (d'ailleur peut etre viré le syteme ou on choisis ce qu'on télécharge comme ça c'est l'installeur qui le fait pour matcher avec le dataset qu'on a choisi)
  - **En cours** : fonds de référence figé `deploy/library-reference.json` (0.85.0), tri par défaut revu, relevé de Marc du 21/11 conservé et commande `library_reference.py diff` pour reporter son tri. Attente : le tri de Marc (inventaire `/api/inventory` + export du classement).
- Faire tester le logiciel a d'autre gens
- est ce qu'il y a vidal ? c'est un truc qui te donne la pesologie etc sur les medocs etc qui peut etre tres utiles genre notice du medicament. y compris pour savoir aussi a quoi sert quel medocs etc les truc incompatible (a voir aussi si il existe plus efficace ou plus récent mais un truc de ce type la)
  - Piste à vérifier : le Vidal est payant et non redistribuable. La Base de données publique des médicaments (ANSM, données ouvertes : notices, RCP, compositions) et le Thésaurus des interactions médicamenteuses de l'ANSM (PDF) couvriraient notices, posologies officielles et incompatibilités, en français. Droits, format hors ligne et date de mise à jour à examiner.
- faire un systeme ou on peut faire sous titré toute la biblioteque en francais etc
- Page « Organiser les collections » rapprochée du fonds de référence (demande de Louis du 21/11) :
  - afficher aussi les collections du manifeste absentes de l'installation, grisées, avec un bouton **Télécharger** par collection ;
  - montrer l'écart avec le manifeste : manquante, autre édition, hors référence, taille ou empreinte différente (même logique que `library_reference.py verify`) ;
  - bouton en haut **Revenir à l'état du manifeste**, avec confirmation détaillée (ce qui sera téléchargé, retiré ou reclassé, place nécessaire) : téléchargements suivis dans la File d'attente, aucune suppression sans confirmation ;
  - à développer puis à tester sur le labo Bazzite (ordinateur et téléphone), en plus de la campagne de tests de la bibliothèque complète ;
  - réutiliser la vérification rapide et la File d’attente pour les plans figés. Indiquer quand seule la taille a été contrôlée. Pour remplacer une édition, cibler le fichier exact confirmé et conserver l’ancienne édition jusqu’à vérification de la nouvelle. La suppression actuelle agit sur toute la famille de la collection.
  - **Décision de Louis du 21/11** : cette page **remplace « Enrichir la bibliothèque »** dans le portail. Raisons : Enrichir prend les dernières éditions (dérive par rapport à la référence), choisit par mots-clés hors référence, crée des doublons d'édition, et remplace le plan suivi par la reprise automatique (un seul plan à la fois). La découverte par thème (`kiwix_select.py`) reste un outil en ligne de commande pour proposer des ajouts à la référence. D'ici là, ne pas utiliser Enrichir chez Marc.
- Campagne de tests sur le labo Bazzite (fonds de référence complet) :
  - **21/11, labo 0.86.2** : estimation et téléchargement suivis dans la File d’attente port 18080. La reprise documentaire est armée au démarrage, et le minuteur `setupsurvie-lab-recette-fonds.timer` surveille aussi le transfert et la préparation finale. Le premier redémarrage réel reste à vérifier. Le labo utilise 6 Gio pour Kiwix avec relance en cas d’échec.
  - **Préparation des archives déjà présentes** : le lecteur isolé libzim 4.1.0 a validé la passe des 115 premières archives (114 avec index natif utilisable, un index local). L’inventaire vidéo a repris après correction du lecteur des titres YouTube archivés. Les pistes existantes sont recensées au fil du traitement.
  - **Comparaison partielle** : quatre réglages comparés sur sept requêtes et les mêmes 89 archives Kiwix. Le filtre PDF retire deux résultats hors sujet sur les moisissures. Le repli trouve des repères sur les ruches et les orages. L’OMS et les guides vélo gardent leurs places. Le tannage reste à examiner, ainsi que les homonymes. Les résultats et le suivi sont sous `/run/media/louis/SetupSurvie/results/comparaison-recherche/`.
  - relevé des 136 requêtes des 68 thèmes de Marc, puis comparaison des réglages de recherche (rôles, langue, traduction des requêtes, priorité aux guides, tri) ;
  - liste des manques par thème et recherche de guides français (NRBC, gaz, armes et réglementation, tannage, vannerie, météo, chasse sous-marine, vie à bord…) ;
  - essais de l'assistant (documents ouverts et cités) quand Louis lève la pause IA ;
  - vérifier la reprise automatique après un vrai redémarrage (labo, puis installation Linux du produit) ; manques Windows restants : première installation avec lots non armée, tâche `register-windows-resume.ps1` jamais enregistrée.

- Faire en sorte de crée les sous titre francais, meme si la vidéo est francais, comme ça on peux aussi indexé les sous titre des vidéo francaise
  - Lien constaté le 21/11 sur le labo : 51 collections (surtout vidéo : C'est pas sorcier, Maître Lucas…) n'ont pas d'index plein texte et ne sont trouvées que par leur titre. Des sous-titres français indexés rendraient leur contenu cherchable. Voir `docs/essais/protocole-sous-titres-videos.md` et les sous-titres existants avant de développer.
