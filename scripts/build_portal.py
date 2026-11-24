#!/usr/bin/env python3
"""Build the single portal page from its control markup and ordered assets.

`portal/interface/modele.html` holds the controls and their IDs; shared JS implements
the actions and the interface modules add navigation and layout. Run after changing
the template or any local CSS/JS file: every `?v=` of the portal pages is replaced by
a short SHA-256 of the file it loads, so browsers never keep a stale copy and nobody
has to bump version numbers by hand. Do not edit `portal/index.html` by hand.
No data, assets or credentials are copied.
"""
import hashlib
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / 'portal/interface/modele.html'
PORTAL = ROOT / 'portal'
# Standalone pages whose local assets are stamped in place by the same rule.
PAGES = ('cartes.html', 'pdf.html', 'secours.html', 'suivi-copie.html', 'maintenance.html')
ASSET = re.compile(r'((?:href|src)=")(/[^"?#]+\.(?:css|js))\?v=[^"]*(")')


def stamp(html):
    """Replace each local `?v=` by the content hash of the referenced file."""
    def replace(match):
        path = PORTAL / match.group(2).lstrip('/')
        if not path.is_file():
            raise FileNotFoundError(f'Missing portal asset: {match.group(2)}')
        digest = hashlib.sha256(path.read_bytes()).hexdigest()[:10]
        return f'{match.group(1)}{match.group(2)}?v={digest}{match.group(3)}'
    return ASSET.sub(replace, html)


def build():
    source = TEMPLATE.read_text()
    source = source.replace('<script defer src="/app.js', '<script defer src="/interface/layout.js?v="></script><script defer src="/app.js', 1)
    source = source.replace('<script defer src="/app.js', '<link rel="stylesheet" href="/translation-text.css?v="><script defer src="/translation-text.js?v="></script><script defer src="/app.js', 1)
    # One ordered asset list: shared primitives, feature modules, then navigation.
    assets = [
        ('css', '/interface/style.css'),
        ('css', '/interface/ux-system.css'),
        ('css', '/interface/settings.css'),
        ('css', '/interface/assistant-workspace.css'),
        ('css', '/interface/reader-work.css'),
        ('js', '/source-figures.js'),
        ('js', '/long-summaries.js'),
        ('css', '/bilingual-reader.css'),
        ('js', '/bilingual-reader.js'),
        ('js', '/interface/videos.js'),
        ('js', '/interface/captions.js'),
        ('js', '/interface/transcriptions.js'),
        ('js', '/interface/acquisitions.js'),
        ('js', '/interface/archive-videos.js'),
        ('js', '/interface/youtube-downloads.js'),
        ('css', '/interface/work-queue.css'),
        ('js', '/work-queue-preview.js'),
        ('js', '/interface/work-queue.js'),
        ('js', '/interface/performance.js'),
        ('js', '/interface/translation-benchmark.js'),
        ('js', '/interface/collections.js'),
        ('js', '/interface/collection-sort.js'),
        ('css', '/interface/collection-sort.css'),
        ('js', '/interface/catalogue.js'),
        ('js', '/interface/search-check.js'),
        ('js', '/interface/search-experiment.js'),
        ('js', '/interface/search-tools.js'),
        ('js', '/interface/search-start.js'),
        ('js', '/interface/assistant-diagnostics.js'),
        ('js', '/interface/practical.js'),
        ('js', '/interface/usage-recipe.js'),
        ('js', '/interface/settings-layout.js'),
        ('js', '/interface/ux-system.js'),
        ('js', '/interface/assistant-workspace.js'),
        ('js', '/interface/assistant-status.js'),
        ('js', '/interface/reader-work.js'),
        ('css', '/interface/motion.css'),
        ('js', '/interface/motion.js'),
        ('css', '/resource-status.css'),
        ('js', '/resource-status.js'),
        ('css', '/design/system.css'),
        ('css', '/interface/library-video.css'),
        ('js', '/design/experience.js'),
        ('css', '/maintenance-view.css'),
        ('js', '/maintenance-view.js'),
        ('css', '/interface/maintenance.css'),
        ('js', '/interface/maintenance.js'),
        ('js', '/interface/device-summary.js'),
        ('js', '/interface/home.js'),
        ('css', '/core/core.css'),
        ('js', '/core/feedback.js'),
        ('js', '/interface/navigation.js'),
    ]
    tags = []
    for kind, path in assets:
        tags.append(f'<link rel="stylesheet" href="{path}?v=">' if kind == 'css'
                    else f'<script defer src="{path}?v="></script>')
    source = source.replace('</head>', ''.join(tags) + '</head>', 1)
    source = source.replace('<script defer src="/interface/layout.js',
                            '<script defer src="/interface/ui.js?v="></script><script defer src="/interface/layout.js', 1)
    preload = ''.join(f'<link rel="preload" href="/design/fonts/{name}.woff2" as="font" type="font/woff2" crossorigin>'
                      for name in ('atkinson-next-latin-wght', 'fraunces-latin-wght'))
    # Tokens first: every later sheet reads its colours, radii and durations.
    source = source.replace('<link rel="stylesheet"', preload + '<link rel="stylesheet" href="/design/tokens.css?v="><link rel="stylesheet"', 1)
    # The shared network layer runs before every other deferred script.
    source = source.replace('<script defer src=', '<script defer src="/core/net.js?v="></script><script defer src=', 1)
    source = source.replace('<body>', '<body class="next-interface">', 1)
    return stamp(source)


def stamped_pages():
    """Return the standalone pages with their asset hashes refreshed."""
    return {name: stamp((PORTAL / name).read_text()) for name in PAGES}


if __name__ == '__main__':
    (ROOT / 'portal/interface/search-reference.json').write_bytes((ROOT / 'pilot/search-reference.json').read_bytes())
    (ROOT / 'portal/index.html').write_text(build())
    for name, text in stamped_pages().items():
        if (PORTAL / name).read_text() != text:
            (PORTAL / name).write_text(text)
