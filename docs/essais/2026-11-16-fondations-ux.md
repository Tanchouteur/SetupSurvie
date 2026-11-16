# Fondations UX et retour volontaire

**Bilan du candidat 0.33.0 — 16 novembre 2026.** Premier lot du
[chantier UX](../decisions/refonte-ux-evolutive.md), pas la refonte terminée et
pas un déploiement client. Travail isolé sur `codex/refonte-ux`.

## Changements réalisés

- Référence avant refonte : tag poussé `ux-reference-0.32.1` et paquet vérifié de
  7,2 Mio conservé dans l’espace de tâche, hors Git. Le guide de retour en donne
  chemin, empreinte et limites.
- Retour volontaire au paquet antérieur, avec sauvegarde de l’état récent,
  contrôles d’intégrité/compatibilité et rétablissement de la version quittée
  en cas d’échec. Lanceur PowerShell distinct des lanceurs racine.
- Primitives communes d’aide et variables CSS ; aides au survol/clic/clavier,
  fermeture par Échap, texte lisible tant que le pointeur est dessus.
- En-têtes concrets, texte décoratif retiré, collection plus proche du premier
  écran, lecture prioritaire sans imposer de reparcourir la recherche.
- Sur PC : colonnes de collections adaptées à l’espace, largeur de lecture
  bornée, actions et clavier vérifiés à plusieurs tailles.

Le niveau mineur est retenu car le retour volontaire est une nouvelle capacité
et le socle UX prépare une évolution fonctionnelle significative. La version
candidate sera ajustée à l’intégration si le chantier parallèle livre avant elle.
Aucune référence de composant tiers n’a changé.

## Vérifications exécutées

Runner Linux CPU, Python isolé déjà disponible, fixtures minuscules et services
simulés. Aucun modèle ou corpus réel téléchargé, aucune inférence réelle.

| Contrôle | Résultat |
| --- | --- |
| Suite `python -m unittest discover -s tests -v` | 909 tests, aucun échec, 6 ignorés, environ 211 s |
| Mise à jour/retour, après dernière modification | 19 tests réussis, dont retour conservant les données récentes, réactualisation et récupération d’échec |
| Pages générées | 2 tests réussis |
| Compose généré Windows CPU/GPU et routeurs | 2 tests réussis, sans démarrer de service |
| Nouvelle recette navigateur | 41 contrôles Chromium, largeurs 320, 390, 1024, 1366, 1440 et 1920 px |
| Recette portail existante | 29 contrôles Chromium réussis après correction du retour depuis un lecteur |
| Recette paramètres existante | 182 contrôles Chromium réussis, profils, brouillons, commandes et largeurs |
| Aide au survol | Ouverture, déplacement du pointeur sur le texte et fermeture Échap vérifiés |
| JavaScript et diff | Analyse syntaxique Node et `git diff --check` réussis |

Les tests navigateur passent par Playwright MCP, sur un serveur de fixtures de
ce worktree au port 18769. Le port 8769 appartenait au chantier parallèle et n’a
pas été arrêté ; les vérifications ont été rejouées dans le serveur dédié.
Une tentative de lancement navigateur Node local a échoué faute de binaire
Chromium à la version attendue ; aucune réussite locale WebKit n’est revendiquée.
La recette est ajoutée au lanceur CI Chromium/WebKit pour vérification distante.
Un `docker compose config` brut sans les variables générées de l’installation
est insuffisant ; les deux recettes Compose ci-dessus utilisent la configuration
correctement générée et passent.

## Limites et suites

Le retour complet réel sur Windows/Linux reste à qualifier. Les essais de retour
portent sur les échanges fichiers/données avec services simulés, pas sur les
images réelles ni la tenue physique du stockage. Le lanceur PowerShell n’a pas
été exécuté sur Windows dans le runner.

Les dossiers et volets de conversations, documents consultés, traduction dans
le lecteur et le catalogue complet de composants restent à construire. Le PC est
une cible principale, notamment pour l’espace IA à trois zones et la comparaison.
Les tests automatiques ne prouvent pas une amélioration perçue par Marc ni Safari
sur iPhone physique. L’intégration sur main et le déploiement ne sont pas réalisés
par ce premier lot. Le moteur et les vidéos restent le chantier parallèle.

## Suite du chantier

Ce bilan conserve les résultats du premier candidat. La livraison finale est
la **0.34.0**, après intégration vidéo 0.33.0 ; voir le
[bilan final](2026-11-16-refonte-ux.md) pour les volets, lecteurs, recettes et limites actuels.
