#!/usr/bin/env python3
"""Prepare a pinned French/English corpus, preserving existing Kiwix archives."""
import fcntl
import hashlib
import json
import shutil
import time
import urllib.request
import xml.etree.ElementTree as ET

import linux_lab as lab
from lab_library_ranges import download

ARCHIVES = (
    ('wikibooks', 'wikibooks_fr_all_maxi_2026-10.zim', 'fra', 'Wikilivres français'),
    ('wikibooks', 'wikibooks_en_all_maxi_2026-10.zim', 'eng', 'Wikibooks anglais'),
    ('wikipedia', 'wikipedia_en_all_maxi_2026-08.zim', 'eng', 'Wikipédia anglais illustré'),
)
NS = {'m': 'urn:ietf:params:xml:ns:metalink'}


def main():
    lab.checked_mount()
    with (lab.MOUNT / 'private/corpus.lock').open('w') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        path = lab.MOUNT / 'results/corpus-manifest.json'
        manifest = json.loads(path.read_text()) if path.exists() else {'archives': []}
        for directory, name, language, title in ARCHIVES:
            destination = lab.MOUNT / 'data/library/zim' / name
            if destination.exists() and any(x['name'] == name and x.get('verified') for x in manifest['archives']):
                print('Déjà vérifié :', name, flush=True)
                continue
            url = f'https://download.kiwix.org/zim/{directory}/{name}'
            with urllib.request.urlopen(url + '.meta4', timeout=60) as response:
                meta = ET.fromstring(response.read())
            record = meta.find('m:file', NS)
            size = int(record.findtext('m:size', namespaces=NS))
            expected = next(e.text.strip() for e in record.findall('m:hash', NS) if e.get('type') == 'sha-256')
            mirrors = [e.text.strip().rsplit('/', 1)[0] + '/' for e in record.findall('m:url', NS)
                       if e.text.startswith('https://') and any(host in e.text for host in ('ftp.fau.de/', 'mirrors.dotsrc.org/', 'ftp.nluug.nl/'))]
            if not mirrors:
                mirrors = [f'https://download.kiwix.org/zim/{directory}/']
            partial = destination.with_suffix('.zim.part')
            # Conservative: reserve enough for a full outstanding archive, even on resume.
            if not destination.exists():
                if shutil.disk_usage(lab.MOUNT).free < size + 5_000_000_000:
                    raise RuntimeError('Marge insuffisante dans le volume plafonné pour ' + name)
                print(f'Téléchargement : {name}, {size / 1e9:.2f} Go', flush=True)
                download(partial, name, size, mirrors=mirrors,
                         status_path=lab.MOUNT / 'results/corpus-progress.json')
            candidate = destination if destination.exists() else partial
            digest = hashlib.sha256()
            with candidate.open('rb') as stream:
                for block in iter(lambda: stream.read(8 * 1024 * 1024), b''):
                    digest.update(block)
            if candidate.stat().st_size != size or digest.hexdigest() != expected:
                raise RuntimeError('Archive non publiée : taille ou empreinte incorrecte pour ' + name)
            candidate.chmod(0o644)  # Kiwix reads public archives as a different container user.
            if candidate == partial:
                partial.rename(destination)
            entry = {'name': name, 'language': language, 'title': title, 'url': url, 'bytes': size,
                     'sha256': expected, 'verified': True, 'verified_at': time.strftime('%Y-%m-%dT%H:%M:%S%z')}
            manifest['archives'] = [x for x in manifest['archives'] if x['name'] != name] + [entry]
            lab.setup.write_json(path, manifest)
            lab.podman('restart', lab.PREFIX + 'kiwix', capture=True)
            print('ARCHIVE_READY', name, flush=True)


if __name__ == '__main__':
    main()
