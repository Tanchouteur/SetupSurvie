# Intégration du transfert SSD Windows — 0.42.0

**Bilan daté du 17 novembre 2026.** Louis demande la fusion de la branche
`codex/transfert-ssd-windows`, reprise après épuisement du crédit de son agent.

La livraison conserve les correctifs de copie/reprise Windows, la protection
contre les lanceurs de maintenance pendant le transfert, la reprise des mises
à jour interrompues et le suivi dans **Mon appareil → Stockage**. Le navigateur
du PC serveur peut piloter l’assistant local et suivre la copie quand le portail
est arrêté. Le [guide actuel](../exploitation/transfert-installation.md) décrit
les étapes et les observations de transfert déjà rapportées par la branche.

Le niveau mineur **0.42.0** est retenu : aux corrections compatibles s’ajoute
le pilotage du transfert dans le navigateur. La version API et le manifeste
restent cohérents. Les références des composants tiers ne changent pas.

Deux défauts de tests observés dans la CI de la branche ont été corrigés :
la simulation Windows du protocole reste limitée au module testé, sans modifier
le système de chemins de Python ; les tests de flux documentaires ne lancent
plus un inventaire vidéo indépendant qui pouvait encore écrire pendant la
suppression de leur dossier temporaire sous Windows.

## Vérifications d’intégration

- Fusion avec `main` sans conflit ; les changements Linux et PDF récents sont conservés.
- Tests ciblés du lanceur Windows : 6 réussis ; flux/cache de recherche : 14 réussis.
- Suivi HTTP local sur données fictives sous Chromium et WebKit, en 390 et
  1 280 pixels : progression à 50 %, sept commandes visibles avec autorisation,
  fragment d’autorisation effacé, lecture seule sans autorisation, aucun
  débordement horizontal ni erreur JavaScript.
- Suite complète locale après correction : **1 060 tests, 6 ignorés**, en
  215,176 s. Suite Linux CI du même code : **1 060 tests, 6 ignorés**, en 83,181 s.
- Transfert : 32 tests, dont 2 réservés à Windows et ignorés localement ;
  mise à jour : 21 tests réussis.
- Paquet logiciel : 1 008 fichiers comparés au dépôt et aux empreintes du
  manifeste ; SHA-256 `ec122fc0adb324bc78ef0a9602820bf703964b0827c2ececfa67cded549697f0`.
  Ce paquet correspond au code `fa67f5b` ; les compléments de bilan suivants
  ne modifient que la documentation.
- `git diff --check` et renvois locaux du bilan réussis.

Les huit jobs de la [CI finale](https://github.com/Tanchouteur/SetupSurvie/actions/runs/44168736221)
réussissent sur `fa67f5b1d05be670351ae86788c7f9f3cbf20bee` : Linux, Windows,
lecteurs isolés Python 3.11/3.13/3.14, Kiwix, routage hors ligne et navigateurs.
Les changements postérieurs à ce code sont documentaires.

## Limites

Aucune copie physique, activation, mise à jour ou inférence sur les PC de Louis
ou de Marc n’a été exécutée pour cette fusion. Les observations physiques déjà
rapportées dans le guide restent distinctes de ces tests d’intégration.
Windows vierge, restauration autonome, redémarrage physique et Safari sur iPhone
restent à qualifier. La copie en deux temps avec bascule courte demeure une
proposition explicitement **non implémentée**.
