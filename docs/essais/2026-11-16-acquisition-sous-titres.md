# Acquisition des sous-titres depuis le site

**Bilan daté — candidat 0.31.0, 16 novembre 2026.** Nouvelle fonction compatible :
incrément mineur après 0.30.0, sans modification des images tierces ou suppression
de données. La branche reprend main 0.30.0 par fusion normale ; cartes Windows,
transfert, commandes de traduction et diagnostic de démarrage sont conservés.

## Comportement

Une action « Récupérer sur YouTube » par vidéo locale utilise sa référence associée
ou l’adresse exacte saisie. Aucun réseau à l’ouverture de Collections ou pendant
la lecture. Français prioritaire, choix français/anglais possible, variantes
régionales admises. Récupération seule, sans téléchargement du média ni traduction
distante. Si demandé, la piste source complète rejoint ensuite la traduction locale.

La file privée garde états et pistes complètes, refuse une réponse tardive pour
un média modifié, sérialise pause/reprise et rejoint l’enfant réseau à l’arrêt.
Les refus fournisseur ne deviennent pas des succès vides. Un moteur IA en pause
n’efface pas la piste source. Le suivi ne relit pas les paroles complètes à chaque
actualisation ; SQLite conserve leur résumé. L’export privé dédié contient les
paroles et temps bruts, avec un nom version/date/heure lisible.

Le lecteur et la recherche utilisent les pistes complètes et leurs temps. Les
chevauchements ajustés restent explicites. Les originaux ne sont jamais réécrits ;
la sauvegarde et le transfert emportent rapports, bases et pistes.

## Preuves obtenues

- Dix tests fournisseur sans réseau : références, sélection/langues régionales,
  provenance, conservation des mots, chevauchements, volumes et domaines autorisés.
- Onze tests de file/processus : conservation et index source/français, vidéo
  modifiée, pause/reprise, redémarrage, fournisseur bloqué puis réessai, pause IA,
  enfant réel sans environnement secret, annulation et sortie trop grande rejointes,
  reprise d’une base du premier candidat sans perte des pistes terminées.
- Test API : réservé au profil Famille, validation des paramètres, commandes et
  rapport, indisponibilité optionnelle isolée. Test de transfert étendu aux bases,
  WebVTT et rapports d’acquisition.
- Parcours Playwright MCP : seize vérifications, fournisseur et traduction simulés,
  véritable portail/API/index, affichage à 1366, 390 et 320 pixels. Premier essai
  rejeté correctement : la fixture réécrivait le média avant une reprise et
  changeait sa révision. La fixture de commande a été corrigée pour conserver la
  même source ; le garde-fou produit reste intact.
- R7 réel : youtube-transcript-api 1.2.4, source publique Kiwix `4p2HsIAqitg`,
  choix français, piste `fr-FR` automatique, 185 segments/182 durées ajustées,
  **1 386 ms**, aucune traduction distante ou vidéo téléchargée. Pas de modèle
  chargé. Rapport brut privé `audio-transcription/report-provider-031.json`.

## Limites et suite

Pas de récupération réelle depuis le conteneur Windows de Marc, ni comparaison
avec ses MP4. L’alignement et les traductions doivent encore être relus sur les
médias réellement utilisés. Les droits et la fidélité ne sont pas certifiés par
la présence d’une piste. Les vidéos et pistes contenues dans les ZIM restent à
inventorier séparément. Le fournisseur peut refuser une requête future ; la
reconnaissance audio locale reste un autre parcours.

La suite complète de tests, les deux navigateurs, le CI et le paquet de livraison
sont consignés ci-dessous après leur exécution. Aucun déploiement sur les PC n’est
réalisé par cette recette.

## Navigation ciblée

Les trois recettes récupération/traduction/audio passent sous **Chromium et WebKit** :
16 + 19 + 15 = **50 contrôles par navigateur**, sur le portail et l’API de fixtures.
Une première exécution a révélé un sélecteur de test trop large (`details`) après
ajout de la commande : il cible désormais explicitement la préparation française.
Les assertions de traduction et de lecture restent conservées. WebKit n’est pas
un essai de Safari sur un téléphone réel.

La vérification visuelle mobile a aussi repéré une case trop grande dans les
commandes audio/récupération. Une règle limitée à ces commandes rétablit une
case compacte et un libellé cliquable de hauteur confortable ; le cache des
fichiers concernés est actualisé. Aucun écran général de conversation n’est refait.

Suite locale : **895 tests en 181,639 s, 16 ignorés** (libzim optionnel et
procédures Windows absents du runner). Après la correction de concurrence du
premier schéma, les **11 tests de file/processus passent en 3,385 s**. Le CI
complet du dernier code reste la référence d’intégration ci-dessous.

Le CI Linux de `fc65bde` réussissait mais signalait un transport stdout encore
ouvert après le test de sortie enfant trop grande (Python 3.12). Le correctif
rejoint aussi le drainage du canal sans conserver de texte supplémentaire, et
protège cette fermeture contre une annulation. Les trois tests d’enfant réel
exigent désormais un retour de processus et une fin de flux. Le passage local
en avertissements de ressources stricts est conservé dans `/tmp/ss031-child-drain.log`.
