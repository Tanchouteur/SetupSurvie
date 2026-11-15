# Antennes radio : fréquence, longueur et type d’antenne

Fiche de référence SetupSurvie, rédigée le 15 novembre 2026. Calculs théoriques et
ordres de grandeur ; ce document n’est pas une notice de réglage du Baofeng UV-5R.
Il ne donne pas une longueur universelle pour toutes les antennes.

## Ce qu’il faut connaître avant de choisir

Demander la fréquence en MHz, l’usage réception seule ou émission, et le type
d’antenne : brin vertical quart d’onde avec contrepoids/plan de masse, dipôle à
deux bras, ou antenne commerciale pour portatif. Vérifier les bandes prévues par
le fabricant, l’impédance de l’ensemble, le connecteur exact et la puissance admise.
La seule mention « 8 W » ne détermine ni la longueur ni le type de connecteur.
Le modèle exact du poste compte : la notice commune distingue plusieurs variantes.

## Longueurs électriques théoriques en espace libre

La vitesse de la lumière dans le vide est exactement 299 792 458 m/s.
Pour une fréquence f exprimée en MHz :

- Longueur d’onde entière lambda, en mètres : 299,792458 / f.
- Quart d’onde théorique, en mètres : 74,9481145 / f.
- Demi-onde théorique, en mètres : 149,896229 / f.

Un monopôle quart d’onde demande aussi un retour de courant, par exemple un
contrepoids ou un plan de masse. Un dipôle demi-onde comporte deux bras : la
longueur totale vaut une demi-onde, chaque bras environ un quart d’onde.
Ne pas confondre longueur totale et longueur d’un seul bras.

Exemples théoriques, arrondis après calcul :

| Fréquence | Quart d’onde | Demi-onde totale | Chaque bras du dipôle théorique |
| --- | --- | --- | --- |
| 145 MHz | 51,69 cm | 103,38 cm | 51,69 cm |
| 433 MHz | 17,31 cm | 34,62 cm | 17,31 cm |

Les valeurs sont des exemples de calcul, pas une autorisation d’émettre sur ces
fréquences. La notice du poste et les règles locales déterminent son utilisation.

## Longueur physique réelle et réglage

La longueur physique dépend du diamètre, des isolants, du support et de ce qui
entoure l’antenne. Pour un dipôle filaire simple, l’ARRL propose comme point de
départ pratique une longueur totale en pieds de 468 / f en MHz, soit environ
142,65 / f mètres ; chaque bras fait la moitié. C’est une estimation à ajuster
par mesure, pas la demi-onde géométrique exacte.

Une antenne de portatif raccourcie ou à bobine peut être beaucoup plus courte
qu’un quart d’onde ; un modèle double bande n’est pas un simple brin calculé pour
une seule fréquence. Ne pas couper une antenne commerciale d’après ce tableau.
Choisir d’abord une antenne spécifiée pour les bandes et le poste concernés.

Avant une utilisation en émission, contrôler l’accord et l’adaptation avec un
analyseur ou un appareil de mesure du ROS/SWR adapté aux fréquences. La notice
constructeur UV-5R indique de ne pas émettre sans antenne et demande une adaptation
correcte d’une antenne externe. La longueur seule ne garantit ni bon accord, ni
portée, ni absence de dommage au poste.

## Sources et limites

- [BIPM — Brochure sur le SI, définition du mètre et valeur de c](https://www.bipm.org/en/publications/si-brochure).
- [ARRL — Single Band Dipoles](https://www.arrl.org/single-band-dipoles) : géométrie
  d’un dipôle, point de départ pratique et ajustement par mesure. Le tutoriel vise
  les dipôles filaires HF : ne pas transposer ses détails de construction sans
  examen à un portatif VHF/UHF.
- [Baofeng — téléchargement des notices UV-5R et UV-5RTP](https://www.baofengradio.com/pages/download) :
  commandes et précautions de l’appareil, distinctes des calculs généraux ci-dessus.

Les calculs ci-dessus sont reproductibles avec un calculateur ; les dimensions
ne constituent pas la validation d’une antenne fabriquée. Pour une demande sans
fréquence ou sans type d’antenne, demander ces précisions avant de proposer une taille.
