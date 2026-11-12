# Inventaire des données locales

> Guide de référence du pilote — documentation réorganisée le 11 novembre 2026. Les essais Windows chez Marc et sur téléphone restent à réaliser lorsqu’ils sont indiqués comme non validés.

La page **Données locales**, accessible depuis la navigation et `http://localhost:8080/#data`, recense les archives encyclopédiques, les guides et les modèles présents sur le volume dédié.

Pour chaque collection : nom compréhensible, langue, mois de l’édition, taille et disponibilité. Un bouton ouvre la collection dans Kiwix. Les guides s’ouvrent dans le lecteur de la bibliothèque. Les modèles sont indiqués séparément : leur présence sur disque ne signifie pas qu’ils occupent la VRAM.

L’API publique locale `GET /api/inventory` ne télécharge rien et n’interroge pas Ollama. Les répertoires des archives et modèles sont montés en lecture seule dans le service `pilot`. Une archive n’est annoncée disponible que si son fichier complet est présent et qu’elle apparaît au catalogue Kiwix. Les fichiers `.zim.part` sont signalés incomplets. Pour les modèles, les références du manifeste et la taille des fichiers associés sont contrôlées ; aucun recalcul intégral des sommes de contrôle n’est effectué à chaque visite. Les tailles des modèles peuvent inclure des fichiers partagés, ce ne sont donc pas des mesures d’occupation physique cumulables.

Vérification le 11 novembre 2026 sur ce PC :

- Wikipédia français : édition 2026-05, 55,4 Go ; Wikipédia anglais : édition 2026-08, 127,4 Go.
- Wikilivres français et anglais : éditions 2026-10, respectivement 1,2 et 4,7 Go.
- Trois petits guides de démonstration et sept modèles présents.
- Trois tests automatisés d’inventaire réussis : archive absente du catalogue ou partielle, fichiers de modèle absents/incomplets/corrompus, guide disparu et liens symboliques exclus.
- Vérification Firefox : quatre cartes de collections et sept cartes de modèles, liens vers Kiwix et affichage bureau. Contenu contraint à 390 px sans débordement ; ce contrôle ne remplace pas un essai sur téléphone réel.

La suite complète a aussi été tentée dans l’image WebUI : les trois variantes d’un test de configuration Compose échouent car l’exécutable Docker n’est pas installé dans cette image. La validation Docker/Windows reste à effectuer séparément. Cette page ne constitue pas une validation de l’ensemble du pilote pour installation chez Marc.
