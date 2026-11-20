#!/usr/bin/env python3
"""Build the single portal page from its control markup and ordered assets.

`portal/interface/modele.html` holds the controls and their IDs; shared JS implements
the actions and the interface modules add navigation and layout. Run after changing
the template or an asset version. Do not edit `portal/index.html` by hand.
No data, assets or credentials are copied.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / 'portal/interface/modele.html'


def build():
    source = TEMPLATE.read_text()
    source = source.replace('<script defer src="/app.js', '<script defer src="/interface/layout.js?v=0.67.0"></script><script defer src="/app.js', 1)
    source = source.replace('<script defer src="/app.js', '<link rel="stylesheet" href="/translation-text.css?v=0.39.0"><script defer src="/translation-text.js?v=0.39.0"></script><script defer src="/app.js', 1)
    # One ordered asset list: shared primitives, feature modules, then navigation.
    assets = [
        ('css', '/interface/style.css', '0.63.4'),
        ('css', '/interface/ux-system.css', '0.56.0'),
        ('css', '/interface/settings.css', '0.39.0'),
        ('css', '/interface/assistant-workspace.css', '0.62.0'),
        ('css', '/interface/reader-work.css', '0.39.0'),
        ('js', '/source-figures.js', '0.28.0'),
        ('js', '/long-summaries.js', '0.52.1'),
        ('css', '/bilingual-reader.css', '0.23.0'),
        ('js', '/bilingual-reader.js', '0.60.0'),
        ('js', '/interface/videos.js', '0.65.0'),
        ('js', '/interface/captions.js', '0.54.0'),
        ('js', '/interface/transcriptions.js', '0.54.0'),
        ('js', '/interface/acquisitions.js', '0.54.0'),
        ('js', '/interface/archive-videos.js', '0.64.2'),
        ('js', '/interface/youtube-downloads.js', '0.69.6'),
        ('css', '/interface/work-queue.css', '0.63.1'),
        ('js', '/work-queue-preview.js', '0.64.2'),
        ('js', '/interface/work-queue.js', '0.67.2'),
        ('js', '/interface/performance.js', '0.26.1'),
        ('js', '/interface/translation-benchmark.js', '0.26.1'),
        ('js', '/interface/collections.js', '0.54.0'),
        ('js', '/interface/collection-sort.js', '0.67.4'),
        ('css', '/interface/collection-sort.css', '0.65.2'),
        ('js', '/interface/catalogue.js', '0.67.0'),
        ('js', '/interface/search-check.js', '0.63.0'),
        ('js', '/interface/search-experiment.js', '0.26.1'),
        ('js', '/interface/search-tools.js', '0.67.0'),
        ('js', '/interface/assistant-diagnostics.js', '0.30.0'),
        ('js', '/interface/practical.js', '0.34.0'),
        ('js', '/interface/usage-recipe.js', '0.26.1'),
        ('js', '/interface/settings-layout.js', '0.65.0'),
        ('js', '/interface/ux-system.js', '0.56.0'),
        ('js', '/interface/assistant-workspace.js', '0.58.0'),
        ('js', '/interface/reader-work.js', '0.63.0'),
        ('css', '/interface/motion.css', '0.37.0'),
        ('js', '/interface/motion.js', '0.55.2'),
        ('css', '/resource-status.css', '0.49.0'),
        ('js', '/resource-status.js', '0.63.0'),
        ('css', '/design/tokens.css', '0.44.0'),
        ('css', '/design/system.css', '0.63.4'),
        ('css', '/interface/library-video.css', '0.54.0'),
        ('js', '/design/experience.js', '0.63.0'),
        ('css', '/maintenance-view.css', '0.69.0'),
        ('js', '/maintenance-view.js', '0.69.3'),
        ('css', '/interface/maintenance.css', '0.69.1'),
        ('js', '/interface/maintenance.js', '0.69.2'),
        ('js', '/interface/navigation.js', '0.68.1'),
    ]
    tags = []
    for kind, path, version in assets:
        tags.append(f'<link rel="stylesheet" href="{path}?v={version}">' if kind == 'css'
                    else f'<script defer src="{path}?v={version}"></script>')
    source = source.replace('</head>', ''.join(tags) + '</head>', 1)
    source = source.replace('<script defer src="/interface/layout.js',
                            '<script defer src="/interface/ui.js?v=0.36.0"></script><script defer src="/interface/layout.js', 1)
    preload = ''.join(f'<link rel="preload" href="/design/fonts/{name}.woff2" as="font" type="font/woff2" crossorigin>'
                      for name in ('atkinson-next-latin-wght', 'fraunces-latin-wght'))
    source = source.replace('<link rel="stylesheet"', preload + '<link rel="stylesheet"', 1)
    source = source.replace('<body>', '<body class="next-interface">', 1)
    return source


if __name__ == '__main__':
    (ROOT / 'portal/interface/search-reference.json').write_bytes((ROOT / 'pilot/search-reference.json').read_bytes())
    (ROOT / 'portal/index.html').write_text(build())
