# Inventaire des données locales

**Guide de référence — revu le 20 novembre 2026 pour la 0.67.0.** Les essais
Windows chez Marc et sur téléphone réel restent à réaliser.

## Où voir ce qui est sur l’appareil

- **Bibliothèque → Collections** : encyclopédies et guides présents, avec un
  lien pour ouvrir chaque collection dans Kiwix.
- **Mon appareil → Paramètres → Bibliothèque et préparations** : pages
  **Stockage** (fichiers et espace disque) et **Téléchargements** (ajouts de
  collections). Chacune propose un retour **← Paramètres · Bibliothèque**.
- Le classement des collections (Fonds principal, Autre, suppression) est décrit
  dans le [guide des collections](classement-et-collections.md).

Pour chaque collection : nom compréhensible, langue, mois de l’édition, taille et
disponibilité. Les guides s’ouvrent dans le lecteur de la bibliothèque. Les
modèles sont indiqués séparément : leur présence sur disque ne signifie pas
qu’ils occupent la VRAM.

## Fonctionnement

L’API locale `GET /api/inventory` ne télécharge rien et n’interroge pas Ollama.
Les répertoires des archives et des modèles sont montés en lecture seule dans le
service `pilot`. Une archive n’est annoncée disponible que si son fichier complet
est présent et qu’elle apparaît au catalogue Kiwix ; les fichiers `.zim.part`
sont signalés incomplets. Pour les modèles, les références du manifeste et la
taille des fichiers associés sont contrôlées, sans recalcul intégral des sommes
de contrôle à chaque visite. Les tailles des modèles peuvent inclure des
fichiers partagés : ce ne sont pas des mesures d’occupation physique cumulables.

## Historique — vérification du 11 novembre 2026

Sur le PC Linux de Louis : Wikipédia français (édition 2026-05, 55,4 Go) et
anglais (2026-08, 127,4 Go), Wikilivres français et anglais (2026-10, 1,2 et
4,7 Go), trois guides de démonstration et sept modèles. Trois tests automatisés
d’inventaire (archive absente ou partielle, modèle absent/incomplet/corrompu,
guide disparu et liens symboliques exclus) et une vérification Firefox à 390 px
sans débordement ont réussi ; ce contrôle ne remplaçait pas un essai sur téléphone
réel ni une validation Docker/Windows. La page s’appelait alors **Données locales**
(`#data`).
