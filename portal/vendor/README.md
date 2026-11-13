# Bibliothèques de rendu hors ligne

- Marked 18.2.0 : paquet npm officiel, intégrité SHA-512 du tarball vérifiée contre les métadonnées du registre ; licence MIT incluse.
- DOMPurify 3.4.17 : distribution officielle du tag GitHub cure53/DOMPurify ; licence incluse.

Aucune ressource distante n’est chargée par le navigateur. Le rendu applique une liste fermée de balises et attributs, puis rétablit les citations locales hors des blocs de code.

Empreintes SHA-256 des fichiers distribués :

- `DOMPurify-LICENSE` : `cfc7749b96f63bd31c3c42b5c471bf756814053e847c10f3eb003417bc523d30`
- `marked-LICENSE` : `8e3a3f82f59a60958f56ca08f445647c32a4733dc7ca6c2c46f6eb898471ab9c`
- `marked.js` : `392f4df89533b50f1dadff3f6dc0952350bd39c9f17def50a0374ef47d6147ef`
- `purify.min.js` : `cd37898f9782adf54820c413191b5691803f0f137c799d6edcfd38523b4c2c31`

## PDF.js 6.5.438 — lecteur dédié

Distribution officielle [pdfjs-dist](https://www.npmjs.com/package/pdfjs-dist),
variante legacy, fournie dans `pdfjs/` avec worker, CSS, images, CMaps, polices et
WASM. Les fichiers et leurs licences proviennent du tarball officiel vérifié ;
les empreintes SHA-256 et tailles sont dans `pdfjs/manifest.json`.
Les attributs Git préservent leurs octets et espaces amont, y compris sous Windows. Aucun npm ni
CDN n’est nécessaire à l’exécution. Source :
`https://registry.npmjs.org/pdfjs-dist/-/pdfjs-dist-6.5.438.tgz`.

Intégrité SHA-512 vérifiée contre les métadonnées npm :
`sha512-vg8Pw1x+AFKy4AMDvhuWl5cOYV8d698UoEANoFFhc79hqXDnZQqnOXoxw3HG907WHOg1JYOvLhP756boddFxpA==`.
Licence Apache-2.0, avec licences des polices et composants incluses. Le lot
embarqué pèse environ 7,6 Mo, sans source maps. Son intégrité est testée par
`tests/test_pdf_assets.py`. Pour le modèle worker/rendu, voir la
[documentation officielle](https://mozilla.github.io/pdf.js/getting_started/).
Le lecteur désactive l’évaluation dynamique et les formulaires XFA ; il n’ajoute
pas de gestionnaire de scripts PDF. La fidélité d’une extraction textuelle n’est
pas celle du rendu original, et ce lecteur n’ajoute pas d’OCR.
