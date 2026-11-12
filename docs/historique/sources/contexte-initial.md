Projet : serveur autonome de connaissances avec IA locale

> Archive — document conservé pour retracer les propositions et le prototype initial. Les constats et commandes décrivent cette étape ; pour installer le pilote actuel, suivre le [guide Marc](../../installation/pilote-marc.md).
1. Personnes et origine du projet
Je m’appelle Louis, je suis étudiant en école d’ingénieur informatique en alternance. Je connais surtout Java et le développement web, ainsi qu’un peu Python et C. J’ai déjà un environnement personnel avec Proxmox/NAS et des services Docker.

Je développe ce projet avec mon oncle, Marc Tanchou.

Son idée initiale : disposer d’une énorme réserve de connaissances utilisable en cas de coupure d’Internet, crise prolongée, guerre civile ou situation de survie. Nous avons envisagé un LLM local, puis une bibliothèque documentaire hors ligne pour compléter et fiabiliser ses réponses.

Le projet a évolué : mon oncle pense pouvoir vendre quelques appareils si nous arrivons à concevoir un système propre et pratique. Il proposerait de me reverser une part sur chaque PC vendu. C’est donc potentiellement un petit produit commercial, développé ensemble.
2. Matériel disponible
Le PC de mon oncle possède :
- Une NVIDIA RTX 5060 Ti avec 8 Go de VRAM.
- 32 Go de RAM DDR5.
- Processeur, stockage disponible et système d’exploitation encore inconnus.
Mon propre PC peut également servir au développement, mais sa configuration n’a pas été précisée dans cette conversation.

Le temps d’inférence était initialement secondaire pour mon oncle. Pour un appareil partagé et éventuellement vendu, la réactivité reste à mesurer.
3. Objectif utilisateur
Concevoir un appareil qui :
- Fonctionne sans Internet après sa préparation.
- Héberge une grosse bibliothèque de connaissances.
- Propose un assistant IA exécuté localement.
- Sert de mini serveur pour les téléphones, tablettes et autres PC à proximité.
- S’utilise depuis un navigateur, idéalement sans installer d’application sur les appareils clients.
- Offre une expérience suffisamment simple pour quelqu’un de peu technique.
- Peut être reproduit sur plusieurs PC.
L’autonomie énergétique n’a pas été définie. Le fonctionnement sans Internet est demandé ; batterie, panneaux solaires et durée d’autonomie restent des choix ouverts.

La portée réseau n’est pas définie : un réseau Wi-Fi local est envisagé, pas une couverture automatiquement étendue à tout un quartier.
4. Priorité actuelle : une installation reproductible
Mon dernier besoin explicite :

Nous voulons préparer le système une première fois sur le PC de mon oncle ou sur mon PC, l’améliorer et le tester, puis généraliser l’installation aux autres machines.

Je souhaite utiliser Docker, probablement Docker Compose, pour faciliter cette reproduction.

Architecture de déploiement à étudier :
- Applications et services dans des conteneurs lorsque pertinent.
- Configuration versionnée dans Git.
- Volumes persistants clairement identifiés.
- Procédure d’installation automatisée.
- Versions des composants fixées et testées.
- Sauvegarde et restauration hors ligne.
- Séparation entre configuration commune et paramètres propres à chaque appareil.
Attention : Docker seul ne prépare pas tout le PC. Linux, pilotes GPU, accès au GPU depuis les conteneurs, disques, réseau et démarrage automatique nécessitent aussi une préparation de l’hôte.

Nous n’avons encore rien installé ni développé dans le cadre de cette conversation.
5. Langue et traduction
Mon oncle a confirmé que l’anglais technique lui pose problème.

Il a demandé :
- Si l’IA pouvait traduire l’ensemble de la bibliothèque.
- Quel type d’IA serait intégré.
L’objectif est donc une utilisation en français, même si une partie des sources reste anglaise.

Pistes envisagées :
- Questions et réponses en français.
- Recherche dans des documents français et anglais.
- Traduction ou explication à la demande.
- Conservation des originaux.
- Traductions enregistrées des principaux guides.
- Ajout direct des ressources déjà disponibles en français.
Pas de décision de traduire toute la bibliothèque à l’avance. Une traduction massive demanderait un traitement spécifique : découpage des documents, tableaux, mise en page, OCR des scans, texte dans les schémas et contrôle des termes techniques.

La recherche multilingue doit être testée : un modèle qui parle français ne garantit pas que le moteur retrouve correctement les documents anglais.
6. Contenus souhaités
Exemples de domaines utiles évoqués ou proposés :
- Encyclopédie générale.
- Eau, hygiène et assainissement.
- Premiers secours et références médicales.
- Jardinage et agriculture.
- Conservation et préparation des aliments.
- Champignons et plantes.
- Réparation, mécanique et électricité.
- Énergie et autonomie.
- Cartes et navigation.
- Sciences et enseignement.
Les photos, schémas et illustrations sont importants. Nous voulons pouvoir consulter de vrais documents illustrés, pas uniquement obtenir du texte généré.

Exemple donné : comparer deux champignons. Cela illustre le besoin de guides spécialisés et de bonnes images ; l’IA ou une comparaison photographique ne doit pas être présentée comme une validation suffisante pour les consommer.
7. Kiwix
Kiwix permet de consulter des archives de sites hors ligne au format .zim.

Pour Wikipédia :
- mini : introductions et fiches synthétiques.
- nopic : articles complets sans images.
- maxi : articles avec illustrations, sans garantir tous les médias originaux.
Une archive Wikipédia français maxi de février 2026 avait été trouvée à environ 50 Gio, soit 54 Go. Ce chiffre dépend de la version.

Point architectural essentiel :

Consulter une archive ZIM dans Kiwix et permettre au LLM d’interroger son contenu sont deux fonctions différentes.

L’ajout de Wikipédia ne signifie pas automatiquement que toute l’encyclopédie est indexée pour l’assistant IA.
8. Solution étudiée : Offline Survival
Projet :

https://github.com/carlospolop/offline-survival

D’après sa documentation, il sert à construire automatiquement une bibliothèque locale :
- Téléchargement de ressources par profils.
- Conservation des fichiers originaux.
- Consultation et recherche hors ligne.
- Import de documents personnels, dont des fichiers ZIM.
- Intégration de Kiwix.
- IA locale facultative via Ollama.
- Export d’une bibliothèque vers un autre ordinateur ou un disque.
- Versions proposées pour Windows, macOS et Linux.
Profils annoncés :
1. Survival Essential.
2. Survival Plus.
3. Civilization Core.
4. Civilization Rebuild.
5. Civilization Max.
Exemples du catalogue consulté : Survival Manual, Simple English Wikipedia, sélection Wikipédia, OMS, WikEM, iFixit, Appropedia, Energypedia, LibreTexts et Project Gutenberg.

Les contenus consultés étaient principalement anglais, avec des sélections espagnoles. Aucune sélection française complète n’avait été confirmée.

Limites :
- Installation et fonctionnement non testés.
- Tout fichier téléchargé n’est pas nécessairement indexé pour l’IA.
- Les documents d’architecture ne constituent pas une preuve des fonctions effectivement opérationnelles.
- Projet à évaluer avant d’en faire une dépendance centrale du produit.
9. Solution étudiée : Project NOMAD
Projet officiel :

https://github.com/Crosstalk-Solutions/project-nomad

Site :

https://www.projectnomad.us/

NOMAD correspond davantage à l’idée d’un serveur accessible par navigateur sur le réseau local.

Il orchestre notamment :
- Kiwix : bibliothèque hors ligne.
- Ollama : exécution des modèles.
- Qdrant : recherche documentaire vectorielle.
- Kolibri : cours et ressources éducatives.
- Cartes hors ligne.
- Notes et autres outils.
Il utilise Docker et cible principalement Linux Debian/Ubuntu. Un chemin Windows via WSL2 était documenté avec support communautaire.

Proposition précédente de l’assistant : utiliser NOMAD comme base du prototype. Ce n’est pas encore une décision validée.

Il faut comparer :
- Adapter NOMAD.
- Assembler directement les composants nécessaires avec notre propre Docker Compose.
- Développer seulement l’interface et les fonctions réellement manquantes.
Éviter de cumuler NOMAD et Offline Survival sans raison claire.
10. Modèles IA évoqués
Le catalogue d’Offline Survival consulté prévoyait :
- Qwen2.5 1.5B.
- Gemma 3 4B.
- Qwen3 8B.
- Llama 3.1 8B.
- Mistral Small 24B.
- BGE-M3 et Nomic Embed Text pour les embeddings.
Ollama est le moteur d’exécution, pas le modèle lui-même.

Qwen3 8B a été proposé comme premier candidat à tester sur le PC de mon oncle. Aucun benchmark ni choix définitif n’a été fait.

Un modèle plus gros peut utiliser la RAM et le processeur en complément du GPU, avec un ralentissement. Les performances réelles et la consommation mémoire restent à mesurer.
11. Architecture fonctionnelle proposée, non encore validée
- Un PC serveur Linux.
- Un routeur/point d’accès Wi-Fi dédié relié en Ethernet.
- Un portail Web accessible depuis les appareils clients.
- Une bibliothèque consultable indépendamment de l’IA.
- Un assistant utilisant des passages retrouvés dans les documents et indiquant ses sources.
- Une partie administration distincte.
- Une restauration possible sans téléchargement sur Internet.
Le routeur dédié est une proposition pour simplifier et fiabiliser le réseau ; il n’a pas encore été choisi.

Pour commencer, une seule génération IA à la fois avec file d’attente a été proposée. La consultation documentaire pourrait fonctionner en parallèle. Capacité à mesurer.
12. Stockage : chiffres et limites
Une addition des tailles estimées déclarées dans le catalogue avait donné :
Ensemble	Estimation
42 ressources associées à Civilization Max	149 Go
Tous les modèles du catalogue	32 Go
Wikipédia français maxi ajouté	54 Go
Total	Environ 235 Go


Ce n’est ni une mesure de l’installation finale, ni un maximum absolu.

Il manque notamment les dépendances, index, fichiers temporaires et éventuelles nouvelles ressources. Le profil Civilization Max annonçait aussi une cible de 1 à 2 To, qui n’a pas été réconciliée avec cette addition.

L’estimation précédente de 350–500 Go installés était une marge proposée, pas une mesure vérifiée. Un SSD de 1 To a ensuite été proposé pour le prototype.
13. Reproduction, maintenance et vente
Prévoir une séparation entre :
1. Système et applications.
2. Bibliothèque commune, modèles et index.
3. Données personnelles : documents ajoutés, notes, conversations et réglages.
Objectifs :
- Préparer les contenus une fois et les réutiliser sur plusieurs appareils.
- Ne pas retélécharger ni recalculer inutilement les mêmes données.
- Générer des identifiants et secrets propres à chaque appareil.
- Mettre à jour sans effacer les données.
- Conserver les composants nécessaires à une restauration hors ligne.
- Vérifier le fonctionnement après redémarrage avec Internet déconnecté.
Pour une vente, vérifier séparément les licences des logiciels, modèles et contenus. NOMAD était sous licence Apache 2.0 lors de la consultation, mais cela ne couvre pas automatiquement les documents tiers. Certains contenus comportent des restrictions commerciales.
14. Décisions restant à prendre
- Base NOMAD ou assemblage propre.
- OS et configuration de la première machine.
- Matériel de série et budget.
- Prix de vente envisagé.
- Nombre d’utilisateurs simultanés.
- Autonomie électrique éventuelle.
- Sélection documentaire initiale et droits de redistribution.
- Modèle IA et embeddings.
- Périmètre exact de l’indexation, notamment des ZIM.
- Interface française et stratégie de traduction.
- Installation, mises à jour et restauration.
Prochaine étape attendue : proposer une architecture technique concrète et reproductible, centrée sur Docker Compose et une préparation automatisée de l’hôte, permettant de construire un prototype sur un PC existant puis de le déployer sur d’autres machines.

Ne pas considérer les fonctions annoncées des projets comme déjà testées. Revalider les versions, licences et comportements avant de figer l’architecture.