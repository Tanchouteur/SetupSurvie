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
    source = source.replace('<script defer src="/app.js', '<script defer src="/nouveau/layout.js?v=0.34.0"></script><script defer src="/app.js', 1)
    source=source.replace('</head>','<script defer src="/source-figures.js?v=0.28.0"></script></head>')
    source=source.replace('</head>','<script defer src="/long-summaries.js?v=0.34.0"></script></head>')
    source=source.replace('</head>','<link rel="stylesheet" href="/bilingual-reader.css?v=0.23.0"><script defer src="/bilingual-reader.js?v=0.28.0"></script></head>')
    source=source.replace('</head>', '<script defer src="/nouveau/videos.js?v=0.33.0"></script><script defer src="/nouveau/captions.js?v=0.33.0"></script><script defer src="/nouveau/transcriptions.js?v=0.33.0"></script><script defer src="/nouveau/acquisitions.js?v=0.31.0"></script><script defer src="/nouveau/archive-videos.js?v=0.33.0"></script></head>')
    source=source.replace('</head>', '<script defer src="/nouveau/performance.js?v=0.26.1"></script><script defer src="/nouveau/translation-benchmark.js?v=0.26.1"></script></head>')
    source = source.replace('</head>', '<link rel="stylesheet" href="/nouveau/style.css?v=0.31.0"><script defer src="/nouveau/collections.js?v=0.11.1"></script><script defer src="/nouveau/catalogue.js?v=0.34.0"></script><script defer src="/nouveau/search-check.js?v=0.26.1"></script><script defer src="/nouveau/search-experiment.js?v=0.26.1"></script><script defer src="/nouveau/search-tools.js?v=0.26.1"></script><script defer src="/nouveau/assistant-diagnostics.js?v=0.30.0"></script><script defer src="/nouveau/practical.js?v=0.34.0"></script><script defer src="/nouveau/usage-recipe.js?v=0.26.1"></script><link rel="stylesheet" href="/nouveau/settings.css?v=0.25.0"><script defer src="/nouveau/settings-layout.js?v=0.34.0"></script><script defer src="/nouveau/navigation.js?v=0.34.0"></script></head>', 1)
    source=source.replace('<script defer src="/nouveau/navigation.js', '<link rel="stylesheet" href="/nouveau/ux-system.css?v=0.34.0"><script defer src="/nouveau/ux-system.js?v=0.34.0"></script><script defer src="/nouveau/navigation.js')
    source=source.replace('<script defer src="/nouveau/navigation.js', '<link rel="stylesheet" href="/nouveau/assistant-workspace.css?v=0.34.0"><script defer src="/nouveau/assistant-workspace.js?v=0.34.0"></script><script defer src="/nouveau/navigation.js')
    source=source.replace('<script defer src="/nouveau/navigation.js', '<link rel="stylesheet" href="/nouveau/reader-work.css?v=0.34.0"><script defer src="/nouveau/reader-work.js?v=0.34.0"></script><script defer src="/nouveau/navigation.js')
    source = source.replace('<body>', '<body class="next-interface">', 1)
    source=source.replace('/app.js?v=map-redesign-0.1.12','/app.js?v=0.34.0')
    source=source.replace('/documents.js?v=0.1.25','/documents.js?v=0.29.0')
    source=source.replace('/style.css?v=map-redesign-0.1.12','/style.css?v=0.28.0')
    return source


if __name__ == '__main__':
    (ROOT / 'portal/nouveau/search-reference.json').write_bytes((ROOT / 'pilot/search-reference.json').read_bytes())
    html=build()
    (ROOT / 'portal/nouveau/index.html').write_text(html)
    (ROOT / 'portal/index.html').write_text(html)
