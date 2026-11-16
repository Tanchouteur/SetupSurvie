# Campagne Windows chez Marc du 16 novembre 2026

**Bilan daté.** Les essais ont utilisé le PC Windows de Marc. Les écritures et
arrêts de services ont porté sur des répertoires, profils et conteneurs dédiés
avec des données fictives. Les archives et services actifs ont été consultés
en lecture. La campagne n’a déployé aucun correctif sur le serveur actif.

## Versions et moyens

- Installation observée en **0.30.0**, confirmée par `/api/health`. Les
  892 fichiers inscrits au manifeste du paquet local correspondent aux octets
  installés. SHA-256 du paquet local
  `f2931d498f8b503dc9648f3a79ca24585b0c0482107e3812b9b535d648c4bab7`.
  La copie Git de maintenance locale était à `003d8a6`. Comparés à ce commit,
  deux guides d’essais et deux scripts PowerShell diffèrent encore après
  normalisation des fins de ligne. Le paquet local sert de référence aux
  observations du serveur actif.
- Dépôt historique `moteur` à `ed7ea4f` avec deux fichiers modifiés et trois
  sauvegardes non suivies, tous conservés. Développement et essais sur clone
  indépendant, depuis `f4738abe6a5fb68fc7b0ebdff3da73176288bdce` (`0.31.0`).
- Windows 11 Famille build 26300, Intel Core Ultra 5 225F (10 cœurs /
  10 threads), 32 Gio de RAM installés, RTX 5060 Ti (8151 Mio utilisables,
  pilote 621.01). Docker Desktop, moteur Linux 29.9.3, Python 3.12 et Edge avec
  Playwright dans un environnement Python isolé. Git HTTPS opérationnel.
- Disques physiques NTFS distincts. `C:` NVMe de 1 To, 331 Go libres.
  `D:` HDD de 4 To, environ 2,56 To libres et stockage de la bibliothèque.
  `E:` USB d’environ 67 Go, seul disque externe détecté. Les 135 archives
  ZIM occupent à elles seules **752 555 744 374 octets**.
- Portail Caddy, pilote, Open WebUI et Kiwix actifs. Les trois services OSRM
  redémarraient en boucle, code 139. Le marqueur de pause IA était absent et
  le contrôleur indiquait Ollama en ligne. `/api/ps` indiquait zéro modèle
  chargé au départ et à la fin. Au repos, environ 15 Gio de RAM libres et
  2 Gio de VRAM utilisés. Aucun modèle chargé pour cette campagne.
  Un ancien refus de reprise de bibliothèque signalait une mise à jour en
  cours. Le journal de la mise à jour indiquait ensuite `complete`.

## Matrice et résultats

| Périmètre | Version et environnement | Résultat |
| --- | --- | --- |
| Accès réel | 0.30.0 actif, Edge Windows et HTTP local | Accueil, secours, cartes, inventaire vidéo et catalogue Kiwix répondent. `survie.local` répond depuis le serveur. Un PDF absent renvoie 404. Les clients LAN et Safari iPhone restent à essayer. |
| Recherche et originaux | 0.30.0 actif, trois recherches simultanées rejouées | Trois couvertures partielles en 12,6 à 12,8 s. Les premiers aperçus et les originaux Kiwix correspondants répondent sur leurs ports respectifs. L’ordre des résultats peut varier. Pour « réparer un vélo », le premier résultat concernait le prix d’une réparation et répondait mal au besoin pratique. Évaluer la pertinence sur une série plus large. |
| Navigation et profils | 0.31.0 isolé, Edge, profils fictifs | Changement et synchronisation des profils entre onglets, rejet d’une écriture issue d’un profil obsolète, historique, favoris, rechargement, retour/suivant et vues étroites vérifiés. Les brouillons et dossiers n’ont pas fait l’objet d’une recette dédiée. |
| Documents et bibliothèque | 0.31.0 isolé, Edge, PDF et média synthétiques | PDF rendu, accès statique à l’original en cas de panne du pilote, ouverture de la page citée, figures originales, recherche par collection et recherche progressive vérifiées. Décodage vidéo et sélection des pistes anglaise et française testés. |
| Assistant et travaux longs | 0.31.0 isolé, Edge et réponses simulées | Sélection persistante de plusieurs documents, annulation de requête, preuves de lecture, pause et reprise, perte d’une lecture finale, rechargement et export vérifiés. Le PDF de synthèse est lu jusqu’à sa dernière page. |
| Traduction et sous-titres | 0.31.0 isolé, Edge et calcul simulé | Progression, pause, reprise explicite, arrêt, résultats partiels et exports vérifiés. Cas de proposition rejetée et brouillon de sous-titres non publié vérifiés. Fidélité, reconnaissance et acquisition auprès du fournisseur non évaluées avec leurs moteurs réels. |
| Charge | 0.30.0 actif, lecture documentaire | Délais mesurés sur deux séries de trois recherches. La qualité, la charge RAM/VRAM et les délais sous inférence concurrente restent à mesurer. |
| Hors ligne et panne réelle | 0.31.0, Caddy, pilote et Kiwix dans un projet Docker jetable | Réseau Docker interne vérifié et requête extérieure en échec. Accueil, page de secours, original texte, aperçu et catalogue répondent. Arrêt du pilote seul, lecture statique encore disponible, redémarrage du pilote et contrôle SQLite réussis. |
| Transfert et reprise | 0.31.0, données synthétiques de `D:` vers un dossier jetable sur `E:` | Copie vérifiée, adaptation des chemins et contrôle des relations SQLite. Reprise après arrêt du processus, rejet d’une copie altérée et simulation de manque de place réussis. Les services et images Docker n’ont pas été transférés dans cet essai de petite taille. |
| Sauvegarde privée | 0.31.0, état fictif créé par le schéma du pilote | Après renommage de la source, restauration des fichiers et vérification du profil, de la conversation, du message, de la sélection documentaire, du favori et du passage traduit. Intégrité SQLite, clés étrangères, pause et nouveaux chemins vérifiés. Import des images et démarrage standard simulés. |
| Secours intégral | Protocole de restauration hors ligne | Bloqué par la capacité du seul support externe. Reste à vérifier avec un disque dimensionné pour l’ensemble inventorié avec sa marge, une cible sans accès à la source et aux caches, puis un redémarrage et une lecture après retrait du support. |

## Anomalies reproduites et corrigées

### Itinéraires indisponibles après mise à jour Windows

**Gravité élevée pour le routage.** Les trois conteneurs de l’installation en
0.30.0 avaient été créés avant l’ajout de la surcharge Compose Windows. Un
`docker inspect` montrait l’utilisateur par défaut. Le journal affichait
`network.osrm.fileIndex` et `Permission denied`. Le portail répondait quand
même et indiquait qu’un graphe était préparé.

Sur le clone 0.31.0, construire un petit graphe et créer les trois routeurs
sans la surcharge. Lancer ensuite la phase de remise en service du code de
mise à jour. Attendu, les routeurs utilisent la configuration courante et
répondent. Avant correction, les conteneurs conservent leur configuration et
les trois demandes échouent. La cause est l’absence des routeurs dans la
remise en service après mise à jour.

Le commit `eba62b7` demande une remise en conformité Compose des seuls
routeurs Windows lorsque le graphe existe. Le graphe et l’image locale sont
réutilisés. Le test de régression vérifie le chemin sans graphe et la
tolérance à un échec de Compose sur ce service optionnel. En Docker Desktop
avec le correctif, les trois demandes renvoient `Ok` sur le graphe fictif
(325,8 m à pied, 394,1 m à moto, 769,9 m en voiture). La demande voiture passe
encore après redémarrage du conteneur de test. Les services Web étaient
simulés dans cet essai ciblé de la remise en service.

Pour la première mise à jour conduite par un ancien script, l’agent qui
intègre la correction doit prévoir une recréation explicite des trois
routeurs et vérifier un trajet réel pour chaque mode.

### Refus HTTP du contrôleur interrompu

**Gravité moyenne.** Le test réseau de boucle locale envoie à un contrôleur
jetable des requêtes POST refusées avec un petit corps JSON. Attendu, HTTP
401 ou 404. Sur Windows, deux exécutions initiales ont reproduit
`WinError 10053`. Quand le contrôleur ferme la connexion en laissant des
octets à lire, le client peut perdre le statut de refus.

Le commit `2379b4d` consomme les corps refusés d’au plus 1 Kio avec une limite
totale de 250 ms, puis renvoie le refus. Le test réseau vérifie aussi
l’absence d’exécution de la commande. Les tests ciblés du contrôleur et de
mise à jour passent sur Windows (27 au total).

Un second scénario sur le contrôleur jetable transmet un en-tête
d’autorisation contenant un caractère hors ASCII. Le client recevait
`RemoteDisconnected` car la comparaison de chaînes levait `TypeError`.
Le commit `141d9cb` compare les octets de l’en-tête et renvoie HTTP 401.
Les 11 tests du contrôleur passent avec ce cas supplémentaire.

### Essais Windows de transfert et de reprise

**Gravité basse pour le produit, moyenne pour la recette.** Deux scripts
PowerShell de test sortaient à 1 sur ce PC avec la politique de session.
Le lanceur réel invoque déjà sa sonde avec le paramètre de processus
approprié. Le test de sauvegarde interrompue trouvait encore le verrou
après la fin du processus enfant, reproduit isolément.

Le commit `03afd4a` aligne les deux invocations de test sur le lanceur réel.
Les commits `03afd4a` et `7961d20` laissent à Windows au plus deux secondes
pour libérer les verrous après l’arrêt des processus de test. La contention
pendant la vie du processus et l’absence de manifeste incomplet restent
contrôlées.

Le scénario automatisé de concurrence des recherches Kiwix échouait dans
deux suites complètes mais réussissait isolément. Il utilisait le répertoire
de cache par défaut alors que les requêtes simulées doivent s’exécuter pour
débloquer le scénario. Le commit `4863745` isole l’état et désactive le
cache persistant dans ce test. Le moteur de recherche est identique.

## Intégration et limites

**Complément de l’agent principal :** la branche est reprise sur la 0.32.0 par
fusion normale pour une livraison **0.32.1**, correction compatible. Le vocabulaire,
les contrôles de traduction version 3 et les reçus antérieurs sont conservés.
Le [bilan d’intégration](2026-11-16-integration-corrections-windows.md) distingue
les tests de développement de ce compte rendu réalisé sur Windows.


La branche `codex/campagne-windows-20261116` conserve la version 0.31.0
comme référence d’essai. L’agent principal attribuera la version de
livraison à l’intégration. Examiner les conflits éventuels dans
`scripts/control.py` et `scripts/pilot_update.py` avant intégration.
Rejouer deux mises à jour sur une installation isolée, la première avec
l’ancien mécanisme puis une conduite avec le nouveau. Après mise à jour,
contrôler le portail, les trois trajets, la bibliothèque et la pause IA.

Vingt-quatre recettes Edge ont réussi. Deux avaient d’abord dépassé la
fenêtre de 7,5 s. La recherche progressive et la synthèse ont réussi au
rejeu avec une fenêtre de 22 s. La recette guidée d’usage hors ligne dans
Edge n’a pas été menée à son terme. L’essai Docker sans accès externe
figure dans la matrice.

La suite Windows a compté 897 tests, dont 870 réussis et 27 ignorés, avec
l’état de test dans un répertoire dédié. Ce passage incluait `7961d20`.
Les 11 tests du contrôleur ont ensuite été rejoués avec `141d9cb`.

Les sorties brutes et scripts d’essai sont conservés sur le PC de Marc,
hors Git. Les validations restantes comprennent l’IA sur des réponses à
vérité vérifiable, la charge IA soutenue, les parcours sur téléphone réel
et le [protocole intégral du disque de secours](../exploitation/disque-de-secours-hors-ligne.md).
