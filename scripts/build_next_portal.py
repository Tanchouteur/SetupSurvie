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
    source = source.replace('<script defer src="/app.js', '<script defer src="/nouveau/layout.js?v=0.48.1"></script><script defer src="/app.js', 1)
    source = source.replace('<script defer src="/app.js', '<link rel="stylesheet" href="/translation-text.css?v=0.39.0"><script defer src="/translation-text.js?v=0.39.0"></script><script defer src="/app.js', 1)
    # One ordered asset list: shared primitives, feature modules, then navigation.
    assets = [
        ('css', '/nouveau/style.css', '0.48.0'),
        ('css', '/nouveau/ux-system.css', '0.43.2'),
        ('css', '/nouveau/settings.css', '0.39.0'),
        ('css', '/nouveau/assistant-workspace.css', '0.38.0'),
        ('css', '/nouveau/reader-work.css', '0.39.0'),
        ('js', '/source-figures.js', '0.28.0'),
        ('js', '/long-summaries.js', '0.34.0'),
        ('css', '/bilingual-reader.css', '0.23.0'),
        ('js', '/bilingual-reader.js', '0.28.0'),
        ('js', '/nouveau/videos.js', '0.48.0'),
        ('js', '/nouveau/captions.js', '0.48.0'),
        ('js', '/nouveau/transcriptions.js', '0.48.0'),
        ('js', '/nouveau/acquisitions.js', '0.48.0'),
        ('js', '/nouveau/archive-videos.js', '0.48.0'),
        ('js', '/nouveau/youtube-downloads.js', '0.43.6'),
        ('js', '/nouveau/performance.js', '0.26.1'),
        ('js', '/nouveau/translation-benchmark.js', '0.26.1'),
        ('js', '/nouveau/collections.js', '0.48.0'),
        ('js', '/nouveau/catalogue.js', '0.48.0'),
        ('js', '/nouveau/search-check.js', '0.26.1'),
        ('js', '/nouveau/search-experiment.js', '0.26.1'),
        ('js', '/nouveau/search-tools.js', '0.26.1'),
        ('js', '/nouveau/assistant-diagnostics.js', '0.30.0'),
        ('js', '/nouveau/practical.js', '0.34.0'),
        ('js', '/nouveau/usage-recipe.js', '0.26.1'),
        ('js', '/nouveau/settings-layout.js', '0.43.6'),
        ('js', '/nouveau/ux-system.js', '0.36.0'),
        ('js', '/nouveau/assistant-workspace.js', '0.38.0'),
        ('js', '/nouveau/reader-work.js', '0.39.0'),
        ('css', '/nouveau/motion.css', '0.37.0'),
        ('js', '/nouveau/motion.js', '0.37.2'),
        ('css', '/resource-status.css', '0.43.2'),
        ('js', '/resource-status.js', '0.43.2'),
        ('css', '/design/tokens.css', '0.44.0'),
        ('css', '/design/system.css', '0.48.1'),
        ('css', '/nouveau/library-video.css', '0.48.0'),
        ('js', '/design/experience.js', '0.44.0'),
        ('js', '/nouveau/navigation.js', '0.47.1'),
    ]
    tags = []
    for kind, path, version in assets:
        tags.append(f'<link rel="stylesheet" href="{path}?v={version}">' if kind == 'css'
                    else f'<script defer src="{path}?v={version}"></script>')
    source = source.replace('</head>', ''.join(tags) + '</head>', 1)
    source = source.replace('<script defer src="/nouveau/layout.js',
                            '<script defer src="/nouveau/ui.js?v=0.36.0"></script><script defer src="/nouveau/layout.js', 1)
    preload = ''.join(f'<link rel="preload" href="/design/fonts/{name}.woff2" as="font" type="font/woff2" crossorigin>'
                      for name in ('atkinson-next-latin-wght', 'fraunces-latin-wght'))
    source = source.replace('<link rel="stylesheet"', preload + '<link rel="stylesheet"', 1)
    source = source.replace('<body>', '<body class="next-interface">', 1)
    source=source.replace('/app.js?v=map-redesign-0.1.12','/app.js?v=0.48.1')
    source=source.replace('/documents.js?v=0.1.25','/documents.js?v=0.43.3')
    source=source.replace('/style.css?v=map-redesign-0.1.12','/style.css?v=0.39.0')
    return source


if __name__ == '__main__':
    (ROOT / 'portal/nouveau/search-reference.json').write_bytes((ROOT / 'pilot/search-reference.json').read_bytes())
    html=build()
    (ROOT / 'portal/nouveau/index.html').write_text(html)
    (ROOT / 'portal/index.html').write_text(html)
