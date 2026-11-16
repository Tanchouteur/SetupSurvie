# Boîte à idées

**Registre actuel — ouvert le 14 novembre 2026.** Les idées conservées ici ne sont
pas des fonctionnalités livrées ni un engagement de calendrier.

| ID | Idée | Origine | Statut et périmètre |
| --- | --- | --- | --- |
| IDEE-001 | Espace « Maison de Solliès-Ville » | Louis, retour de l’appel avec Marc, 14 novembre 2026 | **Plus tard** : regrouper les équipements réellement possédés, leurs notices, entretien et consommables ; envisager stocks et suivi. Structure par maison à étudier. Ne pas créer d’inventaire fictif, de stock supposé ni d’onglet vide. Distinguer documents partagés et données familiales ; les profils actuels ne protègent pas les informations entre lecteurs du réseau. |
| IDEE-002 | Deux espaces autonomie/résilience et savoir/culture | Marc, idée rapportée par Louis le 14 novembre 2026 | **Retenue** dans un seul logiciel ; première sélection documentaire 0.3.0, qualification du fonds à poursuivre. Voir le [plan](plan-ameliorations-marc.md). |
| IDEE-003 | Contexte IA adapté au matériel et CPU mieux utilisés | Louis, 14 novembre 2026 | **Partiellement livré** : 16k et réglage par modèle, indexation multiprocessus et requêtes parallèles ; calibration matérielle réelle à faire. Saturation systématique de RAM écartée. |
| IDEE-004 | Indexation automatique après installation et nouveaux téléchargements | Louis, 14 novembre 2026 | **Implémentée en 0.4.0, recette réelle attendue (L1)** : après vérification du lot, file persistante, seulement les archives nouvelles/modifiées, pause et plage nocturne. Lancement manuel conservé ; première préparation du fonds existant explicite. |
| IDEE-005 | Comprendre les liens dans les archives | Marc, usage 0.3.0 rapporté par Louis le 14 novembre 2026, photo de sommaire Wikilivres | **Plus tard** : distinguer texte simple, lien, lien visité et disponibilité hors ligne ; ne pas faire dépendre la compréhension de la couleur seule. Les couleurs de la source ne prouvent pas un droit d’accès ni la présence d’un article. Examiner un exemple adressable avant d’affirmer qu’un élément noir est un lien désactivé. La lecture qui échoue après une recherche est suivie séparément comme défaut prioritaire du moteur. |
| IDEE-006 | Réorganiser et simplifier les réglages et leurs écrans | Louis, 14 novembre 2026 : « c’est le fouillis » | **Implémenté en 0.12.0 après intégration recherche 0.11.1** : [guide et inventaire](../utilisation/parametres-et-appareil.md), [captures et validations](../essais/2026-11-14-parametres-ux.md). Relecture par Marc et Safari physique restent distincts. Le [prompt historique](prompt-refonte-parametres.md) conserve le périmètre ; les moteurs ne sont pas modifiés par ce chantier. |

| IDEE-007 | Lecture pendant la traduction IA | Louis, 16 novembre 2026 | **Lecture livrée en 0.28.0** : pages/passages, lecteur dédié, position retrouvée ; [guide](../utilisation/documents-et-traduction.md#lire-pendant-que-le-document-se-traduit--0280). Commandes pause/arrêt/reprise/suppression privée en validation 0.29.0. La publication partagée reste réservée au document terminé et contrôlé. |
| IDEE-008 | Refaire la présentation des conversations | Louis, 16 novembre 2026 : interface jugée peu pratique | **Direction validée le 16 novembre 2026** : [trois zones](conversations-trois-zones.md), conversations à gauche, discussion centrale de largeur limitée, documents à droite ; trois vues sur téléphone et raccourcis de tâche. Dossiers, profondeur et parcours restent à préciser avec Louis avant le développement global. |

| IDEE-009 | Choisir les modèles à télécharger pour le stock hors ligne | Louis, 16 novembre 2026 | **Demandé pour la suite** : [périmètre](conversations-trois-zones.md#modèles-à-stocker-hors-ligne--demande-complémentaire). Stock disque distinct du modèle chargé et des trois modes conseillés ; catalogue, volume, reprise et choix à vérifier. |

Les problèmes prioritaires de recherche, classement des collections, contenus
pratiques, langues et délai de l’assistant sont suivis dans le
[retour d’expérience de Marc](../essais/2026-11-14-retour-experience-marc.md).
