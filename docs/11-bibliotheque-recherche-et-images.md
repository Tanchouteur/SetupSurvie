# Bibliothèque, recherche IA et images

Étude au 30 octobre 2026. Louis précise vouloir Wikipédia français avec illustrations et la possibilité pour l’assistant de retrouver des images documentaires avec les informations textuelles associées. Les champignons restent un exemple parmi d’autres. Aucun connecteur ni import n’est encore réalisé.

## Accès direct sur le LAN : besoin confirmé

Louis confirme que toute la bibliothèque doit aussi être accessible sans interroger l’IA, avec une utilisation pratique sur téléphone. La lecture et la recherche documentaire doivent donc rester possibles indépendamment de la disponibilité du modèle. Ne pas réduire cet accès à un répertoire de fichiers brut.

Proposition d’expérience : un point d’entrée commun sur le LAN avec deux accès, Bibliothèque et Assistant. Pour la bibliothèque, prévoir navigation par thèmes, recherche sans génération IA, filtres langue/type et ouverture des documents illustrés. Sur téléphone, privilégier des pages lisibles, de grands boutons et un retour simple aux résultats. L’organisation exacte et les favoris éventuels restent des propositions à valider.

Kiwix assure la consultation des ZIM ; les PDF et guides nécessitent un lecteur navigateur adapté. Un catalogue commun pourrait orienter vers ces lecteurs. Son moteur de recherche transversal doit être étudié : ne pas promettre qu’une recherche Kiwix interroge aussi les PDF. Même sans recherche transversale initiale, chaque collection doit être clairement accessible et ses limites visibles.

Vérifications proposées : accéder à chaque type de ressource sur téléphone et ordinateur, lire sans IA, chercher quand le modèle est déchargé ou occupé par une tâche longue, puis recommencer sans Internet. Prévoir la gestion des pages volumineuses et PDF peu lisibles sur petit écran, avec conservation de l’original.

## Répartition des rôles proposée

| Élément | Rôle |
| --- | --- |
| Ollama | Charge les modèles locaux et exécute les demandes reçues par API. Ne gère pas seul la bibliothèque ni ses droits et mises à jour. |
| Open WebUI | Interface navigateur, conversations, sélection des modèles et connexion aux connaissances/outils configurés. Inclut des fonctions documentaires, pas seulement une interface graphique. |
| Stockage documentaire | Conserve les originaux : archives ZIM, PDF, guides, images et métadonnées. |
| Kiwix Serve | Rend les archives ZIM consultables depuis le navigateur sur le LAN et fournit une recherche dans les archives compatibles. |
| Préparation documentaire | Extrait texte, tableaux, pages et associations avec les illustrations selon les formats ; OCR au besoin. |
| Recherche documentaire | Retrouve les passages utiles ; recherche native Kiwix et/ou index spécialisés selon le corpus. |
| Connecteur d’outils | Permet à l’assistant de rechercher, lire les sources et demander leurs images ; à développer/configurer et tester. |

Le dialogue passe par Open WebUI, qui appelle Ollama. En cas de question documentaire, une étape retrouve d’abord des sources ou l’assistant appelle des outils de recherche ; les passages sélectionnés reviennent au modèle pour rédiger la réponse. Le modèle ne relit pas toute la bibliothèque à chaque question et n’apprend pas définitivement les fichiers par leur simple ajout.

La documentation [Open WebUI RAG](https://docs.openwebui.com/features/chat-conversations/rag/) décrit récupération de passages et citations ; ses [bases de connaissances](https://docs.openwebui.com/features/workspace/knowledge/) permettent de travailler avec des collections de fichiers. La taille de la bibliothèque et le maintien des images doivent être évalués séparément.

## Gestion des données

Louis et Marc gèrent les ajouts au prototype. Proposition : un catalogue commun décrit chaque ressource, sa langue, provenance, version, licence, empreinte de fichier, emplacement et état de traitement. Séparer original conservé, contenu consultable, extraction réussie et indexation réussie. La base interne d’Open WebUI et un index de recherche ne remplacent pas les originaux.

Conserver séparément les conversations/réglages, le catalogue, les fichiers et les index reconstruisibles. Une mise à jour doit conserver la cohérence entre article, image et version ; changer une archive ZIM peut invalider les chemins enregistrés. Garder une version testée avant de basculer, prévoir la place temporaire et vérifier les liens sur plusieurs appareils.

La gestion peut démarrer avec les collections Open WebUI pour les guides et un catalogue Kiwix pour les ZIM. Un catalogue transversal plus complet reste une proposition, pas un logiciel déjà sélectionné ni une raison de développer immédiatement une interface d’administration propre.

## Wikipédia français avec images

La cible est une archive française `all_maxi` : version complète avec illustrations, par opposition à `nopic` sans images et `mini` abrégée. Il s’agit d’un instantané hors ligne ; ne pas promettre tous les fichiers haute résolution et médias du site vivant. Choisir et inspecter l’archive précise avant de figer sa date, son volume et sa couverture. [FAQ Kiwix](https://get.kiwix.org/en/faq/).

Le répertoire de téléchargement officiel a été consulté, mais la variante française recherchée n’a pas été retrouvée dans la restitution textuelle utilisée ; aucune version ni taille actuelle n’est confirmée par cette note. Le repère de février 2026 conservé dans le contexte initial reste historique. Passer par le catalogue pour sélectionner la ressource et vérifier le fichier avant téléchargement.

Télécharger l’archive et la servir avec Kiwix donne une bibliothèque consultable. Cela ne constitue pas un import de Wikipédia dans Open WebUI ni une indexation vectorielle de toute l’encyclopédie.

## Deux chemins de recherche à comparer

### Wikipédia et autres ZIM : recherche à la demande

Piste initiale : un outil local appelle la recherche Kiwix, lit les articles pertinents, en extrait les passages et les illustrations associées, puis fournit leurs références au modèle. Cela permet de tester l’accès à une encyclopédie entière sans recalculer d’emblée les embeddings de tous ses articles.

La documentation de Kiwix Serve fournit une recherche plein texte publique et un accès brut public aux entrées ZIM. La recherche dépend de la présence d’un index dans l’archive ; les recherches multi-archives d’une même requête ont notamment une contrainte de langue. Le connecteur pourra faire plusieurs requêtes séparées si nécessaire. Son efficacité sémantique et multilingue reste à mesurer. [API Kiwix Serve](https://kiwix-tools.readthedocs.io/en/latest/kiwix-serve.html).

L’indexation vectorielle de tout ou partie des ZIM reste une évolution possible si les essais démontrent un manque ; elle ajoute du traitement, du stockage et une procédure de mise à jour.

### PDF et guides : extraction et index de passages

Préparer les documents, découper le texte en passages, calculer leurs représentations pour la recherche, puis conserver les références aux pages et images. Open WebUI peut assurer une première chaîne ; Docling et Qdrant restent des candidats si les besoins le justifient. Ne pas déployer une deuxième chaîne redondante sans mesurer le bénéfice.

Un PDF scanné peut nécessiter de l’OCR pour son texte et un rendu de page pour conserver les figures. Transformer une image en texte OCR ne préserve pas automatiquement son sens visuel ou son lien avec la bonne légende. [Extraction documentaire Open WebUI](https://docs.openwebui.com/features/chat-conversations/rag/document-extraction/).

## Retrouver des images avec le texte

Premier objectif proposé : retrouver l’article ou la page pertinente, puis afficher ses illustrations documentaires avec légende, source et emplacement. Le service fournit une adresse locale réellement existante ; le modèle ne doit pas inventer de chemin d’image. Préserver auteur et licence lorsqu’ils sont disponibles, et signaler les métadonnées manquantes plutôt que les inventer.

Exemple de demande : « Compare ces deux types de pièces et montre les schémas correspondants. » Le résultat viserait une explication, les figures issues des documents, leurs légendes et les liens vers les pages d’origine. L’association entre image et sujet doit être vérifiée : une image décorative ou une autre espèce figurant sur la page peut être trompeuse.

Pour afficher une image déjà trouvée et correctement légendée, un modèle texte peut suffire. Si le modèle doit analyser les détails visuels d’une figure, il faut lui fournir l’image à un modèle compatible. Chercher dans une collection par ressemblance visuelle constitue encore un autre besoin, demandant un index d’images ou de pages multimodal et des essais spécifiques. Aucun de ces trois niveaux ne découle automatiquement de la présence d’images dans les originaux.

L’affichage dans la conversation est à tester dans Open WebUI avec le format de retour de l’outil retenu, les droits d’accès et les adresses LAN. Un lien utilisable uniquement depuis le serveur (`localhost`) ne suffit pas pour le téléphone d’un utilisateur. Si l’affichage intégré ne convient pas, ouvrir la page source illustrée reste une solution utilisable.

## Première démonstration proposée

Préparer une archive adaptée à un premier essai et quelques guides illustrés ; ne pas commencer par un import massif. Vérifier sur téléphone et ordinateur, sans Internet : recherche d’un article, lecture des sources, affichage des images locales, association correcte aux légendes et absence de lien distant nécessaire.

Comparer ensuite recherche native Kiwix et recherche de passages sur des questions représentatives. Ce test déterminera si le connecteur suffit pour l’encyclopédie et quels contenus méritent une indexation complémentaire. Aucun verdict de fiabilité sur les usages sensibles ne découle de cette démonstration.
