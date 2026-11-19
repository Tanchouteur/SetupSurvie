# Documentation SetupSurvie

- [Mesurer le classement des espaces](essais/mesurer-classement-documentaire.md) — protocole avant/après, résultats Bazzite et recette à étendre chez Marc.

- [Guide de design Veillée](architecture/guide-design.md) — navigation, lecture, vidéo et recette visuelle.
- [File d’attente](utilisation/file-attente.md) — voir, réordonner, mettre en pause et reprendre les travaux du portail. [Décision et suivi](decisions/file-attente-travaux.md).

- [Premier transfert réel entre SSD sur Bazzite](essais/2026-11-18-transfert-ssd-bazzite.md) — mise à jour, interruption et reprise sur deux SSD physiques.
- [Refonte du design « Veillée » — 0.44.0](essais/2026-11-18-refonte-design-veillee.md) — nouvelle identité du portail, accès rapide, vérifications et limites
- [Téléchargement YouTube réel — 0.43.4](essais/2026-11-18-youtube-reel-bazzite-windows.md) — trois vidéos sur Bazzite, contrôle Windows sans YouTube.
- [Demandes de vidéos avec de vrais modèles — 0.43.4](essais/2026-11-18-demandes-videos-modele-reel.md) — essai R7, liens et sous-titres, vidéos fictives.

- [Bouton de liste YouTube — 0.43.0](essais/2026-11-18-bouton-liste-youtube.md) — dépôt depuis le site, suivi, pause, reprise ; contrôleur simulé.

- [Qualité visuelle à reprendre](decisions/refonte-ux-evolutive.md#cohérence-et-qualité-visuelle-à-reprendre--demande-de-louis-du-17-novembre-2026) — demande de Louis : navigation des cartes, indicateurs RAM/GPU et cohérence de tout le site ; chantier futur.

- [Intégration du transfert SSD Windows — 0.42.0](essais/2026-11-17-integration-transfert-ssd-windows.md) — reprise de copie, suivi navigateur, tests et limites.

- [Installation Linux neuve sur Bazzite](essais/2026-11-17-installation-neuve-bazzite.md) — recette réelle 0.41.0, fonds réduit vérifié, CI réussie et limites.

- [Trouver les vidéos — 0.40.0](essais/2026-11-17-recherche-videos.md) — filtre Vidéos uniquement, répertoire automatique, liens donnés par l’assistant.
- [Télécharger une liste de vidéos YouTube](utilisation/telecharger-videos-youtube.md) — outils yt-dlp, Deno et FFmpeg inclus dans l’installation, le kit et le transfert ; [décision et questions ouvertes](decisions/telechargement-videos-youtube.md).
- [Mémoire visible et lecture de traduction — 0.39.0](essais/2026-11-17-memoire-et-lecture-traduction.md) — état réel, navigation et actualisation stable.

- [Lecture et recherche avec réseau isolé — 0.38.3](essais/2026-11-17-lecture-reseau-isole.md) — API HTTP réelle, aucun réseau externe, données fictives.

- [Formules, contexte et suite de lecture — 0.38.3](essais/2026-11-17-formules-contexte-et-suite.md) — blocs entiers et positions exactes.

- [Recherche préalable des notices — 0.38.2](essais/2026-11-17-recherche-notices-commandes.md) — référence explicite, lecture et relances.

- [Aide générale sans source précise — 0.38.1](essais/2026-11-17-aide-generale-sans-source.md) — consignes cohérentes, recherche vide et limites documentaires.
- [Projets dépliables et volet redimensionnable — 0.38.0](essais/2026-11-17-projets-assistant.md) — comportement, essais et limites.

- [Formules conservées dans les sources et traductions — 0.37.3](essais/2026-11-17-formules-documentaires.md) — équations extraites, calcul réel et contrôles de fidélité limités.
- [Feuille de route vers la V1](decisions/feuille-de-route-v1.md) — bilan général du 17 novembre 2026 : bloquants, améliorations, gros essais manquants et questions ; proposition à valider.
- [Ingénierie de tests](essais/ingenierie-de-tests.md) — stratégie du 17 novembre 2026 pour pouvoir compter sur SetupSurvie en effondrement total : banque de 89 questions, notation, modes dégradés, scénarios ; non exécutée.
- [Installation neuve et transfert entre SSD sur Bazzite](essais/plan-installation-neuve-et-transfert-bazzite.md) — protocole préparé, non exécuté : installation Linux de zéro ≤ 300 Go, transfert, nettoyage.

- [Volets, transitions et classement — 0.37.0, audit 0.37.2](essais/2026-11-17-volets-transitions-classement.md)

- [Finition et reprise de la base UX](essais/2026-11-16-finitions-interface.md) — défauts des captures, nettoyage CSS/JS et preuves du candidat 0.36.0.

- [Base et composants de l’interface](architecture/composants-interface.md) — organisation CSS/JS, cartes cohérentes et corrections après les captures utilisateur.

- [Offre de PC préinstallé](decisions/acces-simple-et-offre.md) — précision de Louis du 16 novembre 2026 : code propre non publié en open source, préparation avant livraison distincte de l'usage client ; offre encore à qualifier.

- [Apports utiles de NOMAD](decisions/apports-nomad.md) — décision du 16 novembre 2026 : conserver SetupSurvie ; pistes de préparation guidée, contrôle des liens et essai Kolibri, sans nouvelle fonction livrée.

- [Assistant et travaux sur Bazzite 0.37.2](essais/2026-11-17-assistant-bibliotheque-bazzite.md) — demandes naturelles, lectures réelles et sous-titres.
- [Recherche et formes de mots 0.36.1](essais/2026-11-16-recherche-formes-de-mots.md) — singulier/pluriel, repli par titres et limites.

- [Refonte UX 0.34.0](essais/2026-11-16-refonte-ux.md) — assistant en trois zones, traduction dans les lecteurs et vérifications.
- [Inventaire des parcours et composants](decisions/inventaire-parcours-ux.md) — capacités préservées, preuves et règles d’extension.

- [Fondations UX et retour volontaire](essais/2026-11-16-fondations-ux.md) — premier lot candidat, tests et limites.

- [Refonte UX évolutive](decisions/refonte-ux-evolutive.md) — chantier PC/téléphone, traduction dans le lecteur, composants et coordination.
- [Retour à la version précédente](exploitation/retour-version-avant-refonte.md) — procédure conservant les données récentes.

- [Demande pratique et prix](essais/2026-11-16-intention-pratique-et-prix.md) — 0.33.1, classement des actions courtes, tarifs toujours retrouvables et limites.
- [Audio des vidéos ZIM](decisions/audio-videos-zim.md) — 0.35.0, commandes existantes, portions et reprise ; [preuves et limites](essais/2026-11-16-audio-videos-collections.md).

- [Vidéos dans les ZIM](decisions/inventaire-videos-zim.md) — inventaire volontaire, lecteur et pistes dans la recherche ; limites du parcours et essais.
- [Validation des vidéos de collections](essais/2026-11-16-videos-collections.md) — 0.33.0, huit jobs CI et preuves natives/lecteur/navigateurs séparées du fonds réel.
- [Coordination UX et vidéos](decisions/coordination-ux-et-videos.md) — branches séparées, contrats et intégrations successives.
- [Intégration des corrections Windows](essais/2026-11-16-integration-corrections-windows.md) — 0.32.1, contrôleur et routeurs après mise à jour ; bilan réel distinct.

- [Cohérence des traductions](essais/2026-11-16-coherence-traduction.md) — 0.32.0, mots choisis, contexte borné et faux blocage des libellés PDF corrigé.
- [Campagne Windows chez Marc du 16 novembre 2026](essais/2026-11-16-campagne-windows-marc.md) — contrôles du portail actif, essais isolés, défauts reproduits et limites de la restauration.

- [Deux prochains objectifs](decisions/choix-actuels.md#deux-prochains-objectifs--décision-de-louis-du-16-novembre-2026) — simplifier toute l’expérience sans perdre de fonctions, puis mener une campagne autonome de fiabilité réelle incluant copie et restauration complètes hors ligne. Priorités à réaliser.

- [Acquisition des sous-titres](decisions/acquisition-sous-titres.md) — choix de la 0.31.0 ; [essais et limites](essais/2026-11-16-acquisition-sous-titres.md).

- [Diagnostic des essais refusés](essais/2026-11-16-diagnostic-refus-demarrage.md) — 0.30.0, refus conservés et état actuel séparé, sans charger un modèle.

- [Commandes des traductions](essais/2026-11-16-commandes-traduction.md) — 0.29.0, pause/arrêt/reprise et suppression du travail privé.

- [Correctif d’itinéraires Windows](essais/2026-11-16-integration-routage-windows.md) — 0.28.1, intégration de la branche fournie et limites de validation.

- [Prompt de refonte des conversations](decisions/prompt-refonte-conversations.md) — préparation, périmètre validé et fonctions à préserver.
- [Conversations en trois zones et modèles hors ligne](decisions/conversations-trois-zones.md) — direction validée par Louis ; détails à cadrer avant refonte générale.
- [Bilan et recette du transfert](essais/2026-11-16-transfert-fiable.md) — résultats, échecs et validations Windows restantes.
- [Coordination transfert et vidéos](decisions/integration-transfert-et-videos.md) — fichiers partagés et contrat des environnements hors ligne.
- [Transférer une installation vers un SSD](exploitation/transfert-installation.md) — parcours local, reprise, bascule et retour à la source ; recette Windows réelle restante.

- [Lecture progressive des traductions](essais/2026-11-16-lecture-traduction-progressive.md) — 0.28.0, progression par page et lecture conservée pendant le travail.

- [Rapports Windows de Marc en 0.25.0](essais/2026-11-16-rapports-marc-0250.md) — calibration, recherche, comparatif et 40 pages ; corrections 0.26.1 et limites.

- [Des MP4 seuls aux sous-titres](essais/2026-11-16-transcription-audio-videos.md) — 0.26.0, reconnaissance locale, reprise et essai R7.

- [Performances réelles de Marc en 0.24.0](essais/2026-11-16-rapport-performances-marc-0240.md) — 32k chargé, synthèses terminées, coût du chargement et des citations ; cache et couverture à distinguer.

- [Test de traduction sur 40 pages](exploitation/test-traduction-40-pages.md) — 0.25.0, vrai PDF d’essai, reprise et rapport de ressources.
- [Tests et diagnostics](utilisation/parametres-et-appareil.md) — vérifications regroupées, commandes et liens conservés.

- [Préparer les sous-titres français](utilisation/videos-locales.md#préparer-une-piste-française-depuis-le-site--0240) — 0.24.0, traduction synchronisée des pistes présentes et reprise.
- [Essais de traduction des sous-titres](essais/2026-11-16-traduction-sous-titres.md) — modèle réel, contrôles et limites.

- [Rapport de performances de Marc et budget documentaire](essais/2026-11-16-rapport-performances-marc-0220.md) — 0.23.1, défaut de contexte reproduit, mesures RAM/disque/IA et limites.

- [Vidéos locales et sous-titres](utilisation/videos-locales.md) — 0.23.0, recherche des passages et lecteur local ; préparation des pistes manquantes encore distincte.
- [Télécharger une liste de vidéos YouTube](utilisation/telecharger-videos-youtube.md) — 0.43.0, bouton du site ou ligne de commande, avec Internet ; rangement dans library/video/youtube/.

- [Lecture française intégrée](utilisation/documents-et-traduction.md#lire-une-version-française-déjà-terminée--0210) — 0.21.0, version publiée dans les lecteurs portail/PDF.

- [Mesurer les lenteurs en un clic](exploitation/diagnostic-complet-performances.md) — 0.22.0, recherche, IA et ressources du serveur dans un rapport unique.

- [Traduction : contexte, reprise et texte incomplet](essais/2026-11-16-traduction-contexte-et-reprise.md) — 0.20.1, essai réel et contrôle synthétique de 500 pages.

- [Relances et conditions de départ](utilisation/sources-et-fiabilite.md#reprendre-une-discussion-et-vérifier-les-conditions-de-départ--0200) — 0.20.0, sources relues, extraits exacts et limites.
- [Essais des relances et des conditions](essais/2026-11-15-relances-et-conditions.md) — erreurs réelles conservées, corrections et contrôle des outils.

- [Illustrations et références](utilisation/illustrations-et-references.md) — images originales, pages PDF, légendes et limites, 0.19.0.
- [Essais des illustrations originales](essais/2026-11-15-illustrations-originales.md) — comparaison avec 0.18.0, modèle réel et navigateurs.

- [Synthèses longues et reprise](utilisation/synthese-documentaire.md#lire-un-livre-entier-par-étapes--0180) — lecture complète extractible, notes et pause/reprise, 0.18.0.
- [Essais des synthèses longues](essais/2026-11-15-syntheses-longues-et-reprise.md) — preuves, approches corrigées et limites.

- [Choisir plusieurs documents pour l’assistant](utilisation/documents-et-traduction.md#choisir-les-documents-dune-conversation--0170) — sélection persistante, PDF et traduction distincte, 0.17.0.

- [Synthèse de plusieurs documents](utilisation/synthese-documentaire.md) — 0.16.0, passages pertinents, limites de contexte et contrôle des références.
- [Essais de synthèse sur modèles réels](essais/2026-11-15-synthese-multi-sources-et-essais-reels.md) — comparaison R7 avec 0.15.1, progrès et échecs conservés.

- [Assistant : recherche, synthèse et illustrations](decisions/assistant-recherche-et-synthese.md) — besoin retenu, boucle d’outils bornée et fonctions encore à développer.
- [R2 0.15.0 et demandes de synthèse](essais/2026-11-15-rapport-0150-et-requetes-synthese.md) — 32 recherches complètes, contraste avec les captures et correctif 0.15.1.

- [Suivi documentaire de l’assistant](essais/2026-11-15-suivi-documentaire-assistant.md) — 0.15.0, opérations observées et sources consultées conservées indépendamment du texte du modèle.

- [Questions périphériques et titres exacts](essais/2026-11-15-questions-peripheriques-et-titres-exacts.md) — correctif 0.14.3, sources conservées et lecture réelle encore nécessaire.

- [Budget des reformulations](essais/2026-11-15-budget-reformulations.md) — correctif 0.14.2, source manquée reproduite et plafond adapté aux lots du flux long.

- [Rapport réel 0.14.0 et traitement progressif](essais/2026-11-15-rapport-0140-et-traitement-progressif.md) — progrès mesurés, lenteur reproduite et correctif 0.14.1.

- [Audit de clôture du moteur en 0.15.0](essais/2026-11-15-audit-recherche-0150.md) — preuves actuelles, limites et [prochaine recette ciblée](essais/recettes-progressives-marc.md#prochaine-validation-ciblée--0150).

- [Inventaire des vidéos et sous-titres](utilisation/inventaire-videos.md) — outil en lecture seule 0.14.0, état par média et rapports privés.
- [Diagnostic des délais Kiwix](exploitation/diagnostic-performances-kiwix.md) — outil 0.14.0, une archive, réception et répétition sans effacer les caches.
- [Intégration des outils des deux agents](essais/2026-11-15-integration-outils-validation-videos.md) — preuves, compatibilité et limites.

- [Classement, extraits et ouverture des articles](essais/2026-11-15-classement-titres-et-intention.md) — correction 0.13.1, vérifications et limites.
- [Prompts pour deux agents](decisions/prompts-agents-videos-et-performances.md) — périmètres isolés vidéo/sous-titres et diagnostic Kiwix, proposés à Louis.

- [Recherche progressive et cache](exploitation/cache-et-recherche-progressive.md) — guide 0.14.2, premiers documents, arrêt, budgets, mesures et caches distincts.
- [Rapports 0.12.0 et travail nocturne](essais/2026-11-14-recherche-0120-et-travail-nocturne.md) — préparation réelle et délais ; correction et essais distincts.
- [Vidéos locales dans la recherche](decisions/videos-locales-et-recherche.md) — besoin confirmé, `library/video/`, réalisation prévue.

- [Paramètres et Mon appareil](utilisation/parametres-et-appareil.md) — guide actuel 0.12.0, quatre usages et correspondance complète des commandes.

- [Rapport réel 0.10.0](essais/2026-11-14-rapport-recherche-0100.md) — couverture et latence comparées à 0.9.3, refus multilingue reproduit.
- [Index multilingues et diagnostic détaillé](essais/2026-11-14-index-multilingues-et-diagnostic.md) — correction 0.11.1 ; préparation réelle confirmée par les rapports 0.12.0.
- [Prompt de refonte des paramètres](decisions/prompt-refonte-parametres.md) — périmètre et règles pour le chantier parallèle demandé par Louis.
- [Fiabilisation des cartes et choix d’accès](essais/2026-11-14-cartes-et-acces.md) — 0.11.0, intégré sur main ; validations et limites.

- [Sous-titres français pour chaque vidéo](essais/protocole-sous-titres-videos.md) — précision du plan L6, inventaire et contrôles réels à réaliser.
- [Vérifier l’usage hors ligne](utilisation/verifier-usage-hors-ligne.md) — contrôle R7 depuis le site, mesures sans IA et étapes humaines séparées.
- [Contrôle d’usage hors ligne](essais/2026-11-14-recette-usage-hors-ligne.md) — 0.10.0, recette exportable et CI réussie ; usage physique à vérifier.
- [Journal depuis la 0.2.0](essais/journal-recherche-depuis-020.md) — suivi des différences, décisions, preuves et validations restantes pour le résumé final.
- [Rapports réels 0.9.3](essais/2026-11-14-rapports-recherche-093.md) — indexation réussie, recherches encore partielles et comparatif IA interrompu.
- [Corrections après les rapports 0.9.3](essais/2026-11-14-corrections-rapports-093.md) — 0.9.4, ordonnanceur, précision et contexte ; CI réussie, nouveau contrôle réel attendu.

- [Conservation des index pendant la maintenance](essais/2026-11-14-index-sauvegarde-et-retour-arriere.md) — 0.9.3, CI réussie ; exclusions, restauration SQLite et retour arrière testés sur petites données.

- [Contrôle de l’indexation isolée](essais/2026-11-14-indexation-isolee.md) — 0.9.2, lancement Windows corrigé et CI réussie ; terminaison réelle reçue en 0.9.3.

- [Corrections des rapports réels](essais/2026-11-14-corrections-rapports-recherche.md) — 0.9.1, CI réussie ; contrôle du fonds Windows réel encore attendu.

- [Rapports réels de recherche 0.8.0](essais/2026-11-14-rapports-recherche-080.md) — échecs partiels, comparatif IA interrompu et tentative d’indexation à diagnostiquer.
- [Dossiers pratiques](utilisation/dossiers-pratiques.md) — guide 0.9.0, objectifs et références examinées.
- [Six dossiers pratiques](essais/2026-11-14-dossiers-pratiques.md) — bilan 0.9.0, CI réussie ; relecture du fonds réel attendue.

- [Comparer une aide IA à la recherche](utilisation/comparer-recherche-ia.md) — guide 0.8.0, essai volontaire et avis humains.
- [Comparatif de recherche IA](essais/2026-11-14-comparatif-recherche-ia.md) — bilan 0.8.0, CI réussie ; mesure réelle attendue.

- [Plan des améliorations de Marc](decisions/plan-ameliorations-marc.md) — programme complet L1–L9, décisions, critères de fin et validations progressives.
- [Recettes progressives chez Marc](essais/recettes-progressives-marc.md) — rapports manuels actuels/prévus et conditions de blocage.
- [Mesurer les délais et la mémoire de l’assistant](utilisation/mesurer-assistant-et-memoire.md) — guide 0.7.0, rapports et essai mémoire volontaire.
- [Mesures assistant et contexte](essais/2026-11-14-mesures-assistant-et-contexte.md) — bilan 0.7.0, CI réussie ; R4 réel à faire.
- [Classer les documents et nommer les collections](utilisation/classement-et-collections.md) — guide 0.6.0, corrections communes, révisions et export.
- [Classements et collections corrigibles](essais/2026-11-14-classement-et-collections.md) — bilan 0.6.0, CI réussie ; relecture réelle à faire.
- [Référence de pertinence et lecture](essais/2026-11-14-reference-recherche-et-lecture.md) — bilan 0.5.0, 32 demandes, lecture redirigée et CI réussie ; fonds réel à vérifier.
- [Indexation complémentaire des archives](utilisation/indexation-archives.md) — guide 0.4.0, automatisation et pause.
- [Indexation automatique et diagnostic](essais/2026-11-14-indexation-automatique-et-diagnostic.md) — bilan 0.4.0, CI Linux/Windows et navigateurs réussie ; recette du fonds réel à faire.
- [Rapport de Marc et indexation](essais/2026-11-14-recherche-index-et-espaces.md) — bilan 0.3.0 et limites.

Index mis à jour le 16 novembre 2026. Commencer par le parcours correspondant au besoin.

## Guides de référence

| Besoin | Point d’entrée |
| --- | --- |
| Utiliser le serveur en famille | [Utilisation](utilisation/README.md) |
| Installer depuis le kit ou le dépôt | [Installation](installation/README.md) |
| Préparer la configuration matérielle cible | [Choix provisoires et mesures](installation/configuration-materielle-cible.md) |
| Sauvegarder, restaurer et mettre à jour | [Exploitation](exploitation/README.md) |
| Comprendre une panne sans IA | [Manuel de secours](exploitation/manuel-de-secours.md) |
| Préparer un disque de secours complet Windows/Linux | [Protocole cible hors ligne](exploitation/disque-de-secours-hors-ligne.md) |
| Comprendre les composants et les données | [Architecture](architecture/README.md) |
| Trouver les contenus recensés et les lots envisagés | [Bibliothèque](bibliotheque/README.md) |
| Connaître les choix retenus | [Choix actuels](decisions/choix-actuels.md) |

## Lire les statuts

- **Guide de référence** : procédure ou description à entretenir avec le logiciel.
- **Plan ou proposition** : objectif et pistes ; aucune réalisation implicite.
- **Bilan daté** : constat d’une campagne, avec sa version, sa machine et ses limites.
- **Archive** : étape conservée, dont les commandes et affirmations peuvent être dépassées.

Les bilans ne constituent pas une nouvelle validation à chaque mise à jour de cet index. Les constats Linux, Windows, mobiles et hors ligne restent distincts.

## Tous les documents conservés

### Utilisation

- [Recherche documentaire et recette depuis le site](utilisation/recherche-documentaire.md) — guide actuel 0.5.0 : pertinence, lecture, collections et contrôles court/complet sans terminal.

- [Nouvelle interface Windows/Linux](utilisation/nouvelle-interface.md) — guide actuel 0.1.35 : organisation, conversation, suivi réel, navigation et mise à jour normale.

- [Maquette UX historique](utilisation/maquette-ux.md) — prototype fictif 0.1.31, retiré du paquet en 0.59.0.

- [Profils locaux, sans mot de passe](utilisation/profils-locaux.md) — accès familial, anciens comptes et liens du menu, depuis 0.1.29.

- [Sources, dates et fiabilité des réponses](utilisation/sources-et-fiabilite.md) — guide actuel 0.15.0, suivi de recherche et de lecture indépendant du modèle.

- [Documents, favoris et traductions](utilisation/documents-et-traduction.md) — guide actuel 0.1.36, lecture PDF, contrôles de traduction et accès de secours.

- [Paramètres, déplacements et cartes hors ligne](utilisation/parametres-et-cartes.md) — guide du pilote 0.1.10.


- [Inventaire des données locales](utilisation/inventaire-local.md)

### Installation

- [Installation Windows avec un seul lanceur](installation/deux-etapes-windows.md) — démarrage automatique sans IA depuis 0.1.30, reprise et mises à jour Git ; installation complète sur PC vierge encore à valider.

- [Préparer et vérifier le kit hors ligne](installation/preparer-kit-hors-ligne.md)

- [Première version d’essai chez Marc](installation/pilote-marc.md)

### Exploitation

- [Disque de secours complet et restauration sans Internet](exploitation/disque-de-secours-hors-ligne.md) — protocole cible du 13 novembre 2026 ; export autonome et restauration intersystèmes à développer et qualifier.
- [Manuel de secours : comprendre la panne et préserver ses données](exploitation/manuel-de-secours.md) — guide humain actuel de premier diagnostic, avec les limites de la version 0.1.29.

- [Coupures du PC et redémarrage](exploitation/coupures-et-redemarrage.md) — protections de coupure et reprise automatique Windows sans IA depuis 0.1.27.

- [Mettre à jour le pilote et ajouter des contenus](exploitation/mises-a-jour-et-bibliotheque-pilote.md) — miroirs automatiques et transferts simultanés depuis 0.1.26.

### Décisions et besoins

- [Fiabilisation de la recherche et des contenus](decisions/fiabilisation-recherche-et-contenus.md) — chantier demandé par Louis : réalisé, à tester chez Marc et suites à développer.

- [Boîte à idées](decisions/boite-a-idees.md) — évolutions reportées, dont Maison de Solliès-Ville.

- [Plan de refonte UX du portail](decisions/plan-refonte-ux.md) — proposition du 13 novembre 2026 : interface classique conservée, collections directement ouvrables, navigation mémorisée, suivi machine et mobile simplifié ; non implémentée.

- [Questions et décisions](decisions/questions-et-decisions.md)
- [Fonctionnalités et user stories](decisions/fonctionnalites-et-user-stories.md)
- [Connexion simple et direction du produit](decisions/acces-simple-et-offre.md)

### Bibliothèque

- [Savoirs et savoir-faire durables](bibliotheque/savoirs-durables.md) — référence unifiée des nouveaux besoins de Marc, pilote 0.1.19.

- [Bibliothèque complète de Marc et laboratoire réduit](bibliotheque/bibliotheque-complete-marc.md) — guide actuel ; préparation introduite en 0.1.15, sélection affinée en 0.1.19.

- [Where There Is No Doctor : téléchargement et recette](bibliotheque/where-there-is-no-doctor.md)

- [Sélection automatique Kiwix par thème](bibliotheque/selection-kiwix-par-theme.md) — guide de référence du pilote 0.1.9.

- [Bibliothèque hors ligne : quoi télécharger avec une enveloppe de 500 Go](bibliotheque/plan-bibliotheque-hors-ligne-500go.md)
- [Inventaire des ressources téléchargées — 11 novembre 2026](bibliotheque/inventaire-ressources-telechargees.md)

### Essais et résultats

- [Consoles spontanées Windows — 14 novembre 2026](essais/2026-11-14-consoles-windows.md) — capture native, mesures NVML, réparation Docker et intégration 0.2.0.
- [Moteur de recherche utile — 14 novembre 2026](essais/2026-11-14-moteur-recherche-utile.md) — première consolidation 0.1.36, Kiwix réel sur petites archives générées et orchestration simulée.

- [Retour d’expérience de Marc — 14 novembre 2026](essais/2026-11-14-retour-experience-marc.md) — appel rapporté par Louis, cinq captures, recherche prioritaire et propositions non implémentées.

- [Recherche et confort des conversations — 14 novembre 2026](essais/2026-11-14-recherche-et-conversations.md) — correction Kiwix, limites explicites et conversation lisible, 0.1.35.
- [Recherche des ressources et cartes directes — 13 novembre 2026](essais/2026-11-13-recherche-collections-et-cartes.md) — filtre Collections, relief local par défaut et non-régression de l’interface 0.1.34.

- [Audit du fonds réel de Marc — 13 novembre 2026](essais/2026-11-13-audit-fonds-marc.md) — volumes, besoins, accès aux vidéos et défaut de recherche Kiwix ; cartes préparées séparément.
- [Interface fonctionnelle Windows/Linux — 13 novembre 2026](essais/2026-11-13-interface-fonctionnelle.md) — API réelles sur fixtures, classique conservée et validations distinctes.

- [Maquette UX navigable — 13 novembre 2026](essais/2026-11-13-maquette-ux.md) — recette navigateur, limites et suite Python comparée à la référence.

- [Reprise de bibliothèque et consoles Windows — 13 novembre 2026](essais/2026-11-13-reprise-bibliotheque-windows.md) — correction HTTPS, supervision du plan et appels GPU silencieux, pilote 0.1.24.

- [Revue de fiabilité et prochaines étapes — 12 novembre 2026](essais/revue-fiabilite-2026-11-12.md) — corrections 0.1.22 et validations restant à réaliser.
- [Mise à jour Git fournie sur Windows — 12 novembre 2026](essais/2026-11-12-mise-a-jour-git-windows.md) — intégration aux installations et kits, lanceur stable et raccourci, pilote 0.1.21.

- [Installateur Windows simplifié — 12 novembre 2026](essais/2026-11-12-installateur-windows-simple.md) — diagnostic réel, garde des ports, reprise et raccourcis ; limites de recette complète.

- [Vérifier les sources et l’incertitude des modèles](essais/protocole-fiabilite-ia.md) — protocole ; essais sur modèles réels encore à exécuter.

- [Kit Marc et recette hors ligne — 12 novembre 2026](essais/2026-11-12-kit-marc-hors-ligne.md)

- [Démarrage Windows et cartes locales — 12 novembre 2026](essais/2026-11-12-demarrage-windows-et-cartes-locales.md)
- [Refonte de la carte — 12 novembre 2026](essais/2026-11-12-refonte-carte.md)

- [Points et itinéraires — 12 novembre 2026](essais/2026-11-12-points-et-itineraires.md)

- [Paramètres et géographie — 12 novembre 2026](essais/2026-11-12-parametres-et-geographie.md)

- [Gestion de bibliothèque et récupération du contrôleur — 12 novembre 2026](essais/2026-11-12-gestion-bibliotheque-et-controleur.md)
- [Mesurer le gain réel d’un gros modèle](essais/protocole-comparaison-ia.md)
- [Vérifications du paquet de prototype](essais/verification-prototype.md)
- [Essais sur le PC Linux de Louis — 11 novembre 2026](essais/essais-linux-2026-11-11.md)
- [Campagne modèles, contexte, outils et corpus](essais/campagne-modeles-contexte-et-corpus.md)
- [Bilan du pilote — 11 novembre 2026](essais/bilan-pilote-2026-11-11.md)
- [Ressources prioritaires : téléchargements du 11 novembre 2026](essais/telechargements-prioritaires.md)
- [Bibliothèque du Sud, recherche et IA — pilote 0.1.7](essais/bibliotheque-sud-recherche-et-ia.md)

### Historique des études et du prototype

- [Cadrage et besoins](historique/cadrage.md)
- [État des lieux](historique/etat-des-lieux.md)
- [Rôle et limites de l’IA locale](historique/ia-locale.md)
- [Périmètre du prototype](historique/perimetre-prototype.md)
- [Fiabilité et outils spécialisés : étude](historique/fiabilite-et-outils.md)
- [Modes IA, agents et travaux longs : étude](historique/modes-ia-et-travaux-longs.md)
- [Modèles et outils : sélection pour les essais](historique/selection-modeles-et-outils.md)
- [Machines dédiées : enveloppe de 1 000 € et paliers supérieurs](historique/machines-dediees.md)
- [Bibliothèque, recherche IA et images](historique/bibliotheque-recherche-et-images.md)
- [NOMAD ou assemblage : comparaison et recommandation d’essai](historique/comparaison-nomad-assemblage.md)
- [Architecture concrète à essayer et installation reproductible](historique/architecture-et-installation-prototype.md)
- [Installer et tester le prototype](historique/installation.md)
- [Dictée, trois modèles et bibliothèque — 11 novembre 2026](historique/dictee-modeles-bibliotheque.md)
- [Avant la première version installée chez Marc](historique/avant-premiere-installation-marc.md)
- [Projet : serveur autonome de connaissances avec IA locale](historique/sources/contexte-initial.md)

Les [archives et la table des anciens chemins](historique/README.md) permettent de retrouver les références antérieures. Les [consignes de contribution](../AGENTS.md) définissent la maintenance documentaire.

Le pilote 0.1.11 ajoute les [listes de points et itinéraires hors ligne](utilisation/points-et-itineraires.md), avec consultation mobile et préparation sur ordinateur.

[Notice Baofeng et antennes](bibliotheque/baofeng-et-antennes.md) : ajout au catalogue et recette de guidage pratique.
