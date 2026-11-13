#!/usr/bin/env python3
"""Keep the functional next portal's full control markup aligned with classic.

Shared JS implements existing actions; isolated layout/navigation adds the new UX.
Run after changing the classic control markup. Do not edit generated HTML. No data, assets or credentials are copied.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def build():
    source = (ROOT / 'portal/classique/index.html').read_text()
    for name in ('app.js','style.css','documents.js','settings.js'):
        source=source.replace('/classique/'+name,'/'+name)
    source=source.replace('<script defer src="/classique/context.js?v=0.1.32"></script>','')
    source = source.replace('SetupSurvie — Des connaissances à portée de main', 'SetupSurvie — Nouvelle interface')
    source = source.replace('<script defer src="/app.js', '<script defer src="/nouveau/layout.js?v=0.1.32"></script><script defer src="/app.js', 1)
    source = source.replace('</head>', '<link rel="stylesheet" href="/nouveau/style.css?v=0.1.32"><script defer src="/nouveau/navigation.js?v=0.1.32"></script></head>', 1)
    source = source.replace('<body>', '<body class="next-interface">', 1)
    return source


if __name__ == '__main__':
    html=build()
    (ROOT / 'portal/nouveau/index.html').write_text(html)
    (ROOT / 'portal/index.html').write_text(html)
