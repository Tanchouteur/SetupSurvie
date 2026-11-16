# Vidéo synthétique de recette

`solid-green.webm` est un aplat vert de 96 × 64 pixels, douze secondes, deux images
par seconde, VP8, sans audio ni contenu documentaire. Créé pour ce dépôt le
16 novembre 2026, 1 135 octets. Aucun média tiers ou téléchargement.

Recette : capture JPEG d’un rectangle HTML `rgb(40,90,67)` avec Chromium
Playwright 1.58.2 ; concaténer 24 fois les octets JPEG, puis avec le FFmpeg fourni
dans l’image Playwright déjà épinglée :

```sh
ffmpeg-linux -f image2pipe -c:v mjpeg -framerate 2 -i frames.bin -c:v libvpx -b:v 20k -an solid-green.webm
```

Cette fixture vérifie décodage, seek et pistes WebVTT dans le navigateur. Elle
ne valide ni parole, langue, reconnaissance vocale, traduction ni vidéo de Marc.
