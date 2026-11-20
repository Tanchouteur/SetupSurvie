# Reproduire la campagne

1. Préparer des machines ou VM jetables avec un disque de travail distinct
   du support de copie. Relever l'image de distribution, son empreinte, le
   noyau, la mémoire, le stockage, le commit SetupSurvie et les outils déjà
   installés. Masquer le Python du système seulement sur une cible jetable et
   rétablir la commande après le test.
2. Sur une image propre, lancer l'[installation automatique](../../installation/README.md#installation-automatique-linux)
   avec une sélection figée. Relever les outils réellement utilisés et les
   fichiers téléchargés. Couper le seul processus d'installation pendant une
   écriture, conserver le partiel puis relancer la même commande. Vérifier que
   la modification des lots est refusée sans remplacer les données.
3. Vérifier l'apparition des collections et documents dans la recherche. Ouvrir
   un PDF et un article. Si une liste YouTube de recette est prévue, attendre
   la publication des pistes, puis rechercher un passage par son texte.
4. Produire la copie sur le second disque avec le [guide de transfert](../../exploitation/transfert-installation.md).
   Pendant la campagne de panne, interrompre la copie et relever la taille
   d'un fichier partiel. Relancer, puis contrôler le manifeste et les empreintes.
5. Mettre la copie à disposition de la VM cible. Utiliser un disque vierge de
   SetupSurvie. Le chemin de la source doit être absent dans la VM. Établir
   l'absence de sortie Internet par un témoin TCP et vérifier que l'hôte reste
   accessible. Détacher le support avant le lancement.
6. Restaurer avec le [lanceur de la copie](../../exploitation/transfert-installation.md#restaurer-sur-une-autre-machine-linux-hors-ligne).
   Contrôler les binaires employés, la présence des fichiers Docker et
   l'import des images. Après le démarrage, contrôler santé, recherche et
   lecture. Rejouer la même commande, puis redémarrer la VM et recommencer
   les contrôles sans reconnecter le support.
7. Conserver les résultats anonymisés avec le code de retour, la version, la
   date, les empreintes et le statut. Garder les journaux bruts et les données
   privées hors du dépôt.

## Commandes de la campagne Linux 0.72.0

Les VM utilisent un disque virtuel de 100 Gio et systemd. Les installations en
ligne ont disposé de 6 Gio de mémoire et les restaurations de 5 Gio. Les
empreintes des images de départ et du logiciel figurent dans les
[résultats](resultats.md#traçabilité-du-logiciel-et-des-images).

```sh
sha256sum -c SetupSurvie-linux-0.72.0.tar.gz.sha256
tar -xzf SetupSurvie-linux-0.72.0.tar.gz
cd SetupSurvie
sudo ./scripts/install.sh --preparer-systeme /srv/setup-survie \
  --content-pack health --content-pack water --content-pack books-fr
```

Pour tester une restauration, régler le réseau QEMU sur `restrict=on` dès
la création de l'invité et n'ouvrir qu'une redirection SSH locale. Présenter
le support en lecture seule, copier le dossier entier dans
`/srv/recette-transfert` avec root propriétaire, puis démonter le support.
La source `/srv/setup-survie` doit être absente. Exécuter le témoin TCP
depuis l'invité avant la restauration, puis après le redémarrage.

```sh
test ! -e /srv/setup-survie
! mountpoint -q /mnt/support
! timeout 4 bash -c '</dev/tcp/1.1.1.1/443'
sudo /srv/recette-transfert/transferer-setupsurvie.sh --restaurer-hors-ligne
curl -fsS http://127.0.0.1:8080/api/health
curl -fsS http://127.0.0.1:8080/api/inference
curl -fsS http://127.0.0.1:8081/catalog/v2/entries
curl -fsS -H 'Range: bytes=0-4' http://127.0.0.1:8080/guides/PRI-who-wash-13.en.pdf
```

Contrôler dans `transfer.json` la phase `active`, le chemin de destination
et les résultats d'activation. Relever les deux unités systemd et
`/proc/sys/kernel/random/boot_id` avant et après le redémarrage. Pour une
recette automatique, une commande dont le résultat est inattendu doit faire
échouer l'essai.

## Comparer les modèles avant et après restauration en 0.74.0

Préparer une source neuve avec l'archive 0.74.0 vérifiée, une configuration
CPU et au moins 16 Gio de RAM détectés par Linux. Attendre que l'installation
se termine. À ce stade, relever tous les modèles locaux et leurs empreintes
depuis la source. Le relevé doit contenir GPT-OSS 20B et Qwen3 1,7B.

```sh
set -e
set -o pipefail
python=/srv/setup-survie/outils-linux/bin/python3
curl -fsS http://127.0.0.1:11435/api/tags | "$python" -c '
import json, sys
for model in sorted(json.load(sys.stdin)["models"], key=lambda model: model["name"]):
    print(model["name"], model["digest"])
' > modeles-source.txt
```

Créer la copie puis la restaurer sur un disque distinct, dans une nouvelle
VM de 6 Gio sans accès Internet. Après activation et redémarrage, confirmer
que le support est toujours démonté et que le portail est sain. Démarrer le
moteur local via le profil Famille sur cette VM de recette, puis répéter le
relevé avec `/srv/recette-transfert/outils-linux/bin/python3` et
`modeles-cible.txt`. Comparer les deux fichiers avec `diff -u`. Le relevé
après redémarrage doit inclure chaque nom et chaque empreinte de la source.

Dans le portail de la cible, vérifier que le profil rapide indique Qwen3
1,7B et que GPT-OSS 20B reste proposé. Pour l'essai réel de traduction,
partir d'un MP4 accompagné d'une piste anglaise copiée depuis la source.
Demander la traduction avec le profil rapide, puis vérifier que la piste
française est complète, lisible en WebVTT et trouvée par son texte dans la
recherche. Vérifier que la piste anglaise reste utilisable. Consigner les
deux relevés de modèles, les états de traitement, la RAM et les résultats
de lecture. Les tests des téléchargements et de la file automatique
s'effectuent sur la source connectée.
