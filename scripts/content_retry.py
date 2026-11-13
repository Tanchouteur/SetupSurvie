"""Supervise a pinned selection: keep verified files and continue past network errors."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import time

import content
import setup


def remaining(root, items):
    receipt = root/'catalog/downloaded-content.json'
    recorded = {i['path']: i for i in content.catalog(receipt)} if receipt.exists() else {}
    pending = []
    for item in items:
        saved = recorded.get(item['path'], {})
        target = content.destination(root, item['path'])
        if (all(saved.get(key) == item.get(key) for key in ('id', 'path', 'bytes', 'sha256'))
                and target.is_file() and target.stat().st_size == item['bytes']):
            continue
        pending.append(item)
    return pending


def refresh_windows_trust(url):
    """Schannel may retrieve missing Windows issuers; HTTPS verification stays enabled."""
    if os.name != 'nt':
        return False
    curl = Path(os.environ.get('SystemRoot', 'C:/Windows'))/'System32/curl.exe'
    if not curl.is_file():
        return False
    result = subprocess.run([str(curl), '--noproxy', '*', '--head', '--location', '--fail',
        '--silent', '--show-error', '--proto', '=https', '--proto-redir', '=https',
        '--connect-timeout', '20', '--max-time', '60', '--user-agent',
        'SetupSurvie-offline-library/0.1', url], capture_output=True, timeout=65,
        creationflags=subprocess.CREATE_NO_WINDOW)
    return result.returncode == 0


def supervise(root, items, *, max_rounds=96, retry_delay=60, cancelled=None,
              download=None, trust_refresh=None, wait=None):
    download = download or content.download
    trust_refresh = trust_refresh or refresh_windows_trust
    wait = wait or time.sleep
    status_path = root/'catalog/content-retry.json'
    failed = {}
    pending = remaining(root, items)
    missing = sum(max(0, i['bytes']-(content.destination(root, i['path']+'.part').stat().st_size
                  if content.destination(root, i['path']+'.part').is_file() else 0))
                  for i in pending if not content.destination(root, i['path']).exists())
    content.check_capacity(root, missing)
    print(f'{len(items)-len(pending)} éléments déjà vérifiés conservés ; {len(pending)} à préparer.', flush=True)
    for attempt in range(1, max_rounds+1):
        for item in pending:
            if cancelled and cancelled():
                raise content.DownloadPaused()
            try:
                try:
                    download(root, [item], cancelled=cancelled)
                except Exception as exc:
                    if 'CERTIFICATE_VERIFY_FAILED' not in str(exc):
                        raise
                    print('Vérification HTTPS avec les autorités Windows ; validation des certificats conservée.', flush=True)
                    try:
                        trust_refresh(item['url'])
                    except (OSError, subprocess.SubprocessError):
                        pass
                    download(root, [item], cancelled=cancelled)
                failed.pop(item['id'], None)
            except content.DownloadPaused:
                raise
            except Exception as exc:
                failed[item['id']] = {'title': item['title'], 'error': str(exc), 'attempt': attempt}
                print(f"En attente : {item['id']} — {exc}. Les autres contenus continuent.", file=sys.stderr, flush=True)
            setup.write_json(status_path, {'status': 'running', 'pid': os.getpid(),
                             'attempt': attempt, 'failed': failed})
        pending = remaining(root, items)
        if not pending:
            content.install_templates(root)
            setup.write_json(status_path, {'status': 'done', 'pid': os.getpid(), 'failed': {}})
            setup.write_json(root/'catalog/content-progress.json', {'status': 'done'})
            print('Sélection complète vérifiée. Actualisation des services à effectuer séparément.', flush=True)
            return True
        if attempt == max_rounds:
            setup.write_json(status_path, {'status': 'incomplete', 'pid': os.getpid(),
                             'pending': [i['id'] for i in pending], 'failed': failed})
            setup.write_json(root/'catalog/content-progress.json', {'status': 'interrupted',
                             'id': pending[0]['id'], 'message': 'Tentatives épuisées ; relancer pour reprendre les contenus restants.'})
            break
        delay = min(retry_delay*2**min(attempt-1, 5), 900)
        setup.write_json(status_path, {'status': 'waiting_retry', 'pid': os.getpid(),
                         'attempt': attempt, 'pending': [i['id'] for i in pending], 'failed': failed,
                         'next_retry_at': time.time()+delay})
        setup.write_json(root/'catalog/content-progress.json', {'status': 'waiting_retry',
                         'id': pending[0]['id'], 'message': f'{len(pending)} contenus en attente ; nouvelle tentative automatique.'})
        if attempt < max_rounds:
            for _ in range(delay):
                if cancelled and cancelled():
                    raise content.DownloadPaused()
                wait(1)
    print('Certains contenus restent en attente ; fichiers vérifiés et partiels conservés.', file=sys.stderr, flush=True)
    return False


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--work-dir', required=True)
    parser.add_argument('--selection', type=Path, required=True)
    parser.add_argument('--max-rounds', type=int, default=96)
    parser.add_argument('--retry-delay', type=int, default=60)
    args = parser.parse_args()
    if args.max_rounds < 1 or args.retry_delay < 0:
        parser.error('Nombre de tentatives positif et délai non négatif requis.')
    app = setup.Installation(args.work_dir)
    root = setup.safe_path(app.load()['data_dir'])
    plan = json.loads(args.selection.read_text(encoding='utf-8'))
    if plan.get('schema') != 1 or plan.get('kind') != 'SetupSurvie Kiwix thematic selection':
        raise setup.SetupError('Plan de sélection non reconnu.')
    # One supervisor per data directory; per-file downloads keep their own lock.
    from delivery_paths import locked
    with locked(root/'catalog/content-supervisor.lock'):
        return 0 if supervise(root, content.catalog(args.selection),
                              max_rounds=args.max_rounds, retry_delay=args.retry_delay,
                              cancelled=lambda: (root/'catalog/content-supervisor.pause').exists()) else 1


if __name__ == '__main__':
    try:
        sys.exit(main())
    except content.DownloadPaused:
        print('Téléchargement mis en pause ; fichiers conservés.', flush=True)
    except (setup.SetupError, OSError, ValueError) as exc:
        print('ERREUR :', exc, file=sys.stderr, flush=True)
        sys.exit(1)
