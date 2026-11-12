# Revue de fiabilité — 12 novembre 2026

**Bilan daté, pilote 0.1.21, à partir de la 0.1.20 (`f7f8282`).** Analyse du code,
des guides et tests dans le runner Linux CPU. Aucun accès au PC de Marc pendant
cette revue, aucun téléchargement documentaire lourd et aucune inférence réelle.

## Conclusion et corrections

Le projet correspond aux besoins de Louis et Marc : bibliothèque indépendante du
moteur IA, sources consultables, apprentissage et réparation, données séparées du
logiciel. Il reste un pilote accompagné. Une CI verte ne certifie ni la vérité des
documents ni une réinstallation complète sur le matériel cible.

La 0.1.21 corrige quatre problèmes confirmés :

- La sauvegarde omettait la pause du moteur et le registre des téléchargements.
  Ils sont maintenant copiés et restaurés, sans remplacement du registre privé
  par celui d’un kit plus ancien. Les contenus volumineux restent à conserver
  séparément ; leur registre ne prouve pas leur présence sur le disque restauré.
- Une préparation documentaire pouvait modifier les guides ou relancer le pilote
  pendant la sauvegarde. Les tâches actives sont refusées ; le démarrage des tâches
  et les transferts utilisent des verrous partagés avec la sauvegarde.
  Après un échec partiel de l’arrêt des services, leur redémarrage est tenté.
- Les destinations de restauration pouvaient se chevaucher. Elles sont contrôlées
  avant copie. Les fichiers du manifeste sont vérifiés, sans doublon de casse ni
  chemin réservé Windows ; les réglages doivent appartenir au manifeste vérifié.
  La lecture UTF-8 explicite conserve aussi les accents sous Windows ; ce cas est
  testé en simulant un encodage système Windows différent.
- Le diagnostic exigeait Ollama même en pause. Il contrôle maintenant la partie
  documentaire et indique les vérifications différées. Une inférence demandée
  explicitement reste refusée tant que le marqueur de pause existe.

La compatibilité des anciennes sauvegardes est conservée ; elles ne peuvent
restituer les fichiers absents à l’époque. Le retour arrière des mises à jour
accepte les nouveaux instantanés sans annuler une pause ou un téléchargement récent.
Les procédures actuelles sont dans le [guide Marc](../installation/pilote-marc.md#sauvegarder-et-restaurer)
et le [guide des mises à jour](../exploitation/mises-a-jour-et-bibliotheque-pilote.md).

## Vérifications et limites

Suite locale : **214 tests, dont 2 ignorés**, sans échec ; services et contenus
réels remplacés par des fixtures. Les contrôles portent notamment sur restauration
de la pause et du registre, échec d’arrêt, concurrence, chemins et diagnostic en pause.
La configuration Compose et le retour arrière simulé font partie de la suite.
Les liens Markdown vers les fichiers locaux ont été vérifiés. Une analyse Semgrep
de 58 fichiers Python avec trois règles ciblées (exécution dynamique, shell et TLS)
n’a rien signalé ; sa portée est limitée à ces règles.
Les tests de livraison et de diagnostic sont aussi ajoutés au job Windows de la CI.
Le bilan Windows 0.1.20 reste la [référence des essais chez Marc](2026-11-12-installateur-windows-simple.md).

Cette revue n’est pas un audit complet de sécurité, de dépendances ou de licences.
Les modèles, le corpus réel, la restauration des conteneurs et le téléphone ne sont
pas validés par ces tests. L’interface n’est pas modifiée par cette livraison.

## Prochaines étapes proposées, dans l’ordre

| Priorité | Travail | Critère de réussite |
| --- | --- | --- |
| 1 | Recette Windows complète sur un PC ou une VM distincte | Installation depuis zéro, redémarrages et reprise après interruption ; aucune action sur l’instance de Marc en service |
| 2 | Restauration réelle depuis une sauvegarde et le kit | Comptes, conversations, documents privés et pause retrouvés ; fichiers volumineux et empreintes contrôlés ; copie sur un deuxième support indépendant |
| 3 | Fonctionnement sans Internet après redémarrage | Portail, Kiwix, recherche, cartes et assistant disponibles sur le LAN ; limites et besoins de cache notés, accès IP vérifié |
| 4 | Examen des 753 Go préparés chez Marc | Auditer le plan JSON exact, doublons, langues, éditions, illustrations, licences et manuels pratiques ; examiner les quatre niveaux par sujet, pas seulement le volume |
| 5 | Évaluation des modèles sur le matériel cible | Exécuter le [protocole de fiabilité](protocole-fiabilite-ia.md), vérifier citations, dates, contradictions, abstention et temps de réponse ; pause levée explicitement pour ces essais |
| 6 | Recette avec des utilisateurs novices et un vrai iPhone | Trouver puis ouvrir une source, comprendre une erreur, annuler une réponse ; vérifier Safari, HTTPS, dictée et accès par IP/QR code |
| 7 | Préparer une diffusion plus large | Examiner dépendances, mises à jour, droits de redistribution, gestion des identifiants et support ; extraire progressivement les responsabilités des gros fichiers avec tests de régression |

Le kit système hors ligne, avec pilotes, installateurs et notices propres aux
équipements, reste à construire et à essayer. Les cours, plans et alternatives
sans consommables industriels exigent une sélection éditoriale ; cocher un thème
ne garantit pas cette couverture. La [référence des savoirs durables](../bibliotheque/savoirs-durables.md)
reste le point unique pour ces besoins.
