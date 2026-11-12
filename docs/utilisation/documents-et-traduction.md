# Documents associés et traduction progressive

**Guide de référence — pilote 0.1.16, 12 novembre 2026.** Fonction du portail ; les conversations Open WebUI restent distinctes.

## Garder un document dans une conversation

Depuis la Bibliothèque, ouvrir un document puis **Poser une question sur ce document**. Le document est enregistré côté serveur avec la première question, ou au démarrage d’une traduction. Rouvrir la conversation, recharger la page ou changer d’appareil avec le même compte conserve ensuite cette association.

Le bandeau **Document associé** permet d’ouvrir la source ou de la **Retirer**. Le retrait est également conservé. Retirer le document ne supprime pas les passages déjà traduits. Une source absente ne devient pas disponible simplement parce que son titre est enregistré ; retirer ou remplacer une référence indisponible avant de poser une nouvelle question.

Les anciennes conversations n’enregistraient pas ce lien : la mise à jour ne peut pas deviner le document initial à partir de plusieurs citations. Pour réassocier une source à une conversation existante, ouvrir cette conversation, consulter le document dans la Bibliothèque, puis choisir **Associer à la conversation ouverte**.

Un document sélectionné mais n’ayant donné lieu à aucune question ni traduction reste un brouillon dans le navigateur ; son association n’est pas encore enregistrée sur le serveur.

## Traduire en français

1. Associer le document et choisir le modèle dans **Temps à consacrer**.
2. Déplier **Traduire le document en français**. Pour un PDF, conserver la première page à 1 et la dernière vide pour tout le document, ou choisir une plage, par exemple 1 à 10. Les numéros désignent les pages du fichier PDF, pas forcément la pagination imprimée.
3. Cliquer sur **Traduire en français**. Une demande simple dans la conversation, comme « traduit moi ce guide en français » ou « peux-tu me traduire le document entièrement en français », déclenche également la traduction complète dédiée. Les autres formulations gardent le traitement habituel de l’assistant ; pour une plage de pages, utiliser les champs du panneau.
4. Suivre le nombre de passages traduits. Les passages se consultent par groupes de dix, avec leur page/section, le modèle utilisé et un accès à l’original.
5. **Mettre en pause** interrompt le passage en cours. Choisir au besoin un autre modèle, puis **Reprendre avec le modèle choisi** : les passages terminés sont conservés, seul le travail restant est repris.
6. **Télécharger le texte français** enregistre un fichier texte, même si la traduction est partielle. Les passages manquants y sont explicitement indiqués.

Le traitement continue quand le navigateur est fermé, tant que le serveur et le moteur fonctionnent. Après un arrêt du serveur, la traduction est mise en pause et attend une reprise explicite. Une pause du moteur, notamment le mode jeu, empêche un nouveau départ ou une reprise ; elle est aussi vérifiée entre les passages. Aucun démarrage forcé n’est effectué.

Une traduction utilise la même file d’inférence que les questions du portail. Elle libère cette file entre les passages. Une seule traduction active par compte et quatre en attente ou en cours sur le serveur sont autorisées. Alterner les modèles entre questions et traduction peut provoquer des rechargements par Ollama et augmenter les délais.

## Ce qui est traduit et ce qui reste à vérifier

Les PDF sont lus dans le fichier original, page par page : la traduction n’est pas limitée aux quatre premières pages de l’aperçu. Les pages demandées sont découpées en passages courts. Le texte source de ces passages est conservé dans l’état privé : une reprise ne mélange pas un nouvel original avec le début d’une ancienne traduction.

Une page sans texte extractible est signalée comme telle. Elle peut être illustrée, blanche, numérisée ou demander une reconnaissance de caractères (OCR). Elle n’est pas comptée comme traduite. Le compteur « traitement terminé » n’affirme donc pas que toutes les pages illustrées ont été traduites.

**La traduction est du texte, sans conservation de la mise en page du PDF et sans traduction des images.** L’extraction peut désordonner un tableau ou perdre des caractères : contrôler l’original, surtout les mesures, doses, unités, avertissements et consignes. Le contrôle du format d’une réponse ne certifie ni sa fidélité ni sa sécurité.

Un refus explicite, une réponse vide, un format inexploitable ou une réponse interrompue n’est pas publié comme traduction réussie. Le panneau explique le blocage et permet de reprendre avec un autre modèle. Ce parcours ne garantit pas l’absence de refus de tous les modèles ; leur fidélité réelle reste à évaluer sur les documents de Marc.

Limites actuelles : PDF accessible de 300 Mo maximum, 1 200 pages maximum, 100 000 caractères par page et cinq millions de caractères pour la plage choisie. Un PDF protégé est refusé explicitement. Pour les autres guides et articles, le texte intégral disponible dans l’index ou le lecteur est utilisé ; un aperçu atteignant sa limite de taille est refusé plutôt que présenté comme un document entièrement traduit. Les plages de pages sont réservées aux PDF. Aucun OCR automatique ni traduction d’un ZIM entier n’est ajouté.

## Confidentialité, sauvegarde et suppression

Les associations, traductions et instantanés textuels restent dans la base privée du pilote, accessibles uniquement au propriétaire de la conversation, y compris pour l’export. Ils sont conservés avec les sauvegardes privées de l’installation ; ils ne sont pas ajoutés au catalogue public, au kit ou aux collections Open WebUI.

Supprimer une conversation supprime ses associations et traductions. Une traduction active doit d’abord être mise en pause. Les documents originaux ne sont pas modifiés. Ne pas partager un export contenant un document familial privé.

## Vérifications de cette livraison

Tests sur le runner CPU avec petites fixtures et réponses simulées : reprise après interruption, absence de mélange avec une source modifiée, accès entre comptes refusé, pauses, refus et réponses tronquées, conservation de toutes les pages d’un PDF de six pages et choix d’une plage.

Le parcours Playwright utilise une véritable API locale avec identité et inférence simulées : association après rechargement, traduction depuis la conversation, pause/reprise, export et navigation de 320 à 1 366 pixels. La suite locale compte 162 tests (161 réussis, un test COM Windows ignoré sur Linux). Les tests de l’API et de traduction sont aussi ajoutés au job Windows, et la recette Chromium/WebKit à la CI ; les résultats distants sont à consulter dans la CI du commit concerné. Recettes : `tests/browser_translation_server.py` (nécessite les dépendances de tests et uvicorn dans un environnement isolé) et `tests/browser_translation.js` (Playwright MCP, adresse du serveur de fixture à adapter). Le serveur de recette écoute sur 8769 et ne doit servir que dans un environnement de test isolé.

Aucun modèle réel, GPU, corpus ou compte utilisateur n’a été utilisé pour ces contrôles. La traduction réelle par GPT-OSS/Gemma, l’installation Windows et Safari sur iPhone restent à vérifier. L’écran 0.1.14 ne dispose pas de cette fonction : installer la mise à jour 0.1.16 et recharger le navigateur avant l’essai.
