# Clôture de la première version fiable : preuves en 0.15.0

**Audit historique du 15 novembre 2026.** Le [suivi actuel de l’objectif](../decisions/fiabilisation-recherche-et-contenus.md#état-actuel-pour-la-fin-de-lobjectif--16-novembre-2026-0320) remplace cet état pour les validations restantes. Les conclusions ci-dessous conservent leurs preuves et leur contexte ; l’avancée minimale vidéo décrite à cette date ne constitue pas une clôture du besoin actuel.

**Complément reçu après cet audit :** le [R2 réel 0.15.0](2026-11-15-rapport-0150-et-requetes-synthese.md)
est maintenant disponible : 32 recherches complètes, fin médiane 2,11 s avec cache
largement réutilisé, sans avis humain. Il lève l’attente décrite ci-dessous ; les
captures révèlent toutefois un échec de l’assistant, étudié et corrigé en partie
en 0.15.1. Le [programme de synthèse](../decisions/assistant-recherche-et-synthese.md)
devient le chantier actif ; cet audit conserve ses preuves à sa date initiale.

**Audit daté — 15 novembre 2026, version publiée 0.15.0, `f89bc42`.** Cet audit
remplace comme état courant l’[audit initial 0.14.0](2026-11-15-audit-fin-recherche.md),
dont les mesures historiques restent conservées. Il ne déclare pas l’objectif
terminé et ne présente pas le plan entier L1–L9 comme livré.

L’objectif de Louis est de fiabiliser le moteur de recherche, puis d’avancer ou
au minimum d’étudier et documenter acquisition/traduction des sous-titres. Les
critères ci-dessous proviennent du [plan retenu](../decisions/plan-ameliorations-marc.md),
des retours de Marc et des [recettes R1–R7](recettes-progressives-marc.md).

## État des critères de recherche

| Exigence | Preuve examinée | Ce qu’elle établit et ce qui manque |
| --- | --- | --- |
| Recherche sans IA dans les vrais contenus préparés | R1 réel 0.12.0 et diagnostic du R2 0.14.0 : 135 archives, 120 index natifs, 15 compléments locaux et 3 238 articles | Préparation et utilisation observées pour cet état du fonds. Ajout/changement d’édition et pause/reprise restent à valider sur le PC cible. |
| Indexation reprenable après contenu vérifié, sans doublonner les index natifs | `tests/test_archive_index.py` et `tests/test_search_index_queue.py` : libzim réel sur petites archives, file durable, curseur, ancien index conservé, édition remplacée et pause | Contrats et petit scénario réels testés. La totalité de la bibliothèque n’est pas réextraite dans le runner. |
| Demandes naturelles, FR/EN, filtres et recherche générale préservée | `tests/test_search_reference.py`, liste versionnée de 32 cas et sources fictives attendues ; contrôles de domaines, collections et types | Référence automatisée sans régression dans la suite 0.15.0. Les 32 titres du R2 réel ne valident pas leur contenu. Les exemples déjà utilisés pour corriger le tri ne sont plus une évaluation aveugle. |
| Titres, plein texte, compléments et lecture réunis | 63 contrôles natifs rejoués sur le code 0.15.0, cinq archives de 290 378 octets : chemins échappés, alias, extraits et lecture ; 36 contrôles sur 135 archives de 8 280 525 octets | Mécanismes réellement éprouvés avec le Kiwix épinglé. Ces petits fonds n’établissent ni débit HDD ni pertinence des 755 Go. Aucun changement de ce moteur entre 0.14.3 et 0.15.0. |
| Couverture, pannes et absences correctement distinguées | R2 0.14.0 : toutes les archives sélectionnées tentées dans 32 cas ; 31 sans archive en échec ; neuf recherches complètes et 23 partielles. Tests de catalogues périmés, réponses invalides et erreurs bornées | Progrès réel observé ; 150 reformulations non exécutées et des expirations persistent dans ce rapport antérieur aux corrections. Le nouveau plafond 0.14.2 ne masque pas les échéances. Nouveau R2 requis. |
| Premiers résultats utiles pendant l’attente, lecture et arrêt | R2 réel : médiane 311 ms pour les premiers documents dans 31 cas ; arrivée avant une seconde dans 27 cas. Tests SSE, lecture, annulation et réponse tardive | Réception réelle rapide. La médiane de fin reste 36,24 s en 0.14.0 ; l’effet du traitement 0.14.1 et des variantes supplémentaires 0.14.2 n’est pas encore mesuré chez Marc. |
| Cache actuel, quotas et annulation sans fichiers laissés ouverts | `test_search_progress.py`, `test_search_processing.py`, `test_search_refinement_budget.py` et recette native : cache mémoire/disque, génération changée, réserves, fin des threads et répétition | Contrats et réemploi natif testés. Le gain synthétique du traitement ne prédit pas Windows ; aucune saturation CPU/HDD n’est établie par le dernier R2. |
| Assistant : recherche commune, lecture réelle, citation et limite indépendante du texte | 27 tests d’orchestration et onze tests de suivi en 0.15.0 : erreurs, extraction vide, réponse fictive fausse, annulation, accès par profil et persistance | Le logiciel observe et conserve les opérations ; il ne garantit pas que le modèle utilise correctement les passages. R4 réel volontaire requis, sans levée implicite du mode jeu. |
| Confort et navigation conservés | 130 assertions ciblées par navigateur en 0.15.0 : suivi 25, recherche 50, flux 18, chat 37 ; Chromium et WebKit avec API de fixtures | Parcours ciblés réussis à 1366/390/320 pixels notamment. Ni toute la campagne Web, ni Safari sur iPhone physique ne sont certifiés par ces quatre recettes. |
| Données conservées et livraison vérifiée | 593 tests Python, trois ignorés ; schéma 1, table de suivi optionnelle ; paquet de 753 fichiers déballé et comparé au code `496083b` | Preuve de développement Linux et de paquet. La CI `43705794886` ne démarre aucun job à cause de la restriction GitHub ; aucune nouvelle validation CI Windows n’en découle. Mise à jour et usage hors ligne réels restent à vérifier. |
| Traçabilité depuis 0.2.0 | [Journal](journal-recherche-depuis-020.md), bilans 0.14.1, 0.14.2, 0.14.3 et 0.15.0, guides courants | Livré/testé/prévu restent distincts. Le résumé final ne doit pas transformer développement ou index prêt en validation humaine du fonds. |

Pour vérifier l’état exact audité, les recettes Kiwix de 63 puis 36 contrôles ont
été rejouées successivement sur ce code 0.15.0 : **99 contrôles réussis**, les
huit recherches de la recette à 135 archives avec couverture complète. Les
services et fichiers temporaires de ces recettes sont supprimés à leur fin.
Ces essais n’ajoutent aucun corpus téléchargé et ne changent pas le logiciel.

## Partie sous-titres : périmètre minimal atteint

L’[étude technique](../decisions/videos-locales-et-recherche.md) examine acquisition
des pistes existantes, transcription en langue source, traduction française,
segments horodatés, reprise et lecture sans IA. Elle cite les références officielles
consultées et distingue la traduction d’une page de celle d’une piste vidéo.
Le [protocole par vidéo](protocole-sous-titres-videos.md) sépare contrôles techniques,
langue, synchronisation et portée de relecture. L’inventaire local en lecture seule
est livré en 0.14.0, avec vingt tests repris dans la suite courante.

Cette étude et cet outil satisfont l’avancée minimale demandée pour cette partie
de l’objectif. Ils ne terminent pas L6 : recherche dans les titres/paroles,
acquisition réelle, transcription, traduction et lecteur synchronisé restent à
développer. Le dossier `library/video/` est rapporté par Louis ; son contenu réel
n’a pas été examiné par l’agent. Aucun sous-titre français n’est déclaré validé.

## Ce qui bloque maintenant la conclusion

Le dernier R2 reçu reste la **0.14.0**, créé le 15 novembre à 07:49:29 UTC,
avec **zéro avis humain sur 32 recherches**. Le rapport confirme des progrès,
mais précède les correctifs 0.14.1–0.14.3 et le suivi 0.15.0. Aucun rapport plus
récent n’est présent dans les fichiers transmis à la session lors de cet audit.

La [recette ciblée](recettes-progressives-marc.md#prochaine-validation-ciblée--0150)
demande d’abord R2 et l’ouverture de quelques documents prioritaires ; R4 et R7
se font séparément. Il n’est pas demandé de refaire l’extraction intégrale ni
de lancer toutes les préparations pendant cette recette.

L’agent n’a pas d’accès de développement vérifié au PC de Marc ; TeamViewer
détenu par Louis ne constitue pas un tel accès. Le dernier passage GitHub refusé
pour facturation reste distinct et ne peut être remplacé par un test Linux affirmé
« Windows ». Aucun processus de contrôle distant n’est annoncé en attente.

Sans nouvelle mesure et lecture réelle, on peut confirmer les mécanismes testés,
mais pas clore la fiabilité de cette version sur ce fonds. La décision CPU/SSD,
le réglage mémoire automatique et l’activation de l’aide IA restent sans preuve
nouvelle. Aucun budget ou score n’est modifié à nouveau pour masquer cette attente.

Les gros chantiers encore ouverts du plan — L5 livres longs, suite L6 vidéo,
qualification éditoriale, installation vierge et secours complet — gardent leur
propre état. Ils ne sont ni déclarés finis, ni utilisés comme substitut à la
validation du moteur demandée par Louis.
