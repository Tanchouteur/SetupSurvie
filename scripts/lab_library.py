#!/usr/bin/env python3
"""Fetch the agreed French illustrated Wikipedia archive inside the isolated lab."""
import hashlib
import json
import time

import content
import linux_lab as lab
from lab_library_ranges import download

NAME = 'wikipedia_fr_all_maxi_2026-05.zim'
URL = 'https://download.kiwix.org/zim/wikipedia/' + NAME
# Mirror advertised by Kiwix's official Metalink; same size and SHA-256.
DOWNLOAD_URL = 'https://ftp.fau.de/kiwix/zim/wikipedia/' + NAME
SIZE = 55_438_794_004
SHA256 = '61401b1b3618afe736450a868c7205f572f590db310e044a9c72b51fbfcfb431'


def main():
    lab.checked_mount()
    destination = lab.MOUNT / 'data/library/zim' / NAME
    partial = destination.with_suffix('.zim.part')
    status = lab.MOUNT / 'data/catalog/kiwix.json'
    if not destination.exists():
        lab.setup.write_json(status, {'preparing': NAME, 'archives': []})
        remaining = SIZE - (partial.stat().st_size if partial.exists() else 0)
        if remaining < 0 or content.free_space(lab.MOUNT / 'data', lab.MOUNT) < remaining + 2_000_000_000:
            raise RuntimeError('Espace insuffisant ou fichier partiel trop grand.')
        download(partial, NAME, SIZE)
    candidate = destination if destination.exists() else partial
    if candidate.stat().st_size != SIZE:
        raise RuntimeError('Taille inattendue : archive non publiée.')
    digest = hashlib.sha256()
    with candidate.open('rb') as stream:
        for block in iter(lambda: stream.read(8 * 1024 * 1024), b''):
            digest.update(block)
    if digest.hexdigest() != SHA256:
        raise RuntimeError('Empreinte incorrecte : archive non publiée.')
    candidate.chmod(0o644)
    if candidate == partial:
        partial.rename(destination)
    manifest = {'archives': [{'name': NAME, 'language': 'fra', 'title': 'Wikipédia français avec illustrations',
        'url': URL, 'download_url': DOWNLOAD_URL, 'bytes': SIZE, 'sha256': SHA256, 'verified_at': time.strftime('%Y-%m-%dT%H:%M:%S%z')}]}
    lab.setup.write_json(status, manifest)
    lab.setup.write_json(lab.MOUNT / 'results/library-manifest.json', manifest)
    lab.podman('restart', lab.PREFIX + 'kiwix', capture=True)
    print(json.dumps(manifest, ensure_ascii=False, indent=2), flush=True)


if __name__ == '__main__':
    main()
