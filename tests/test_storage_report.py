import json
import os
from pathlib import Path
import shutil
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import setup
import storage_report


def write(path, size):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b'x' * size)


class StorageReportTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.base = Path(temp.name) / 'SetupSurvie'
        for name in ('application', 'data', 'private'):
            (self.base / name).mkdir(parents=True)
        self.app = setup.Installation(self.base / 'private')
        self.config = {'data_dir': str(self.base / 'data'), 'app_dir': str(self.base / 'application')}
        data = self.base / 'data'
        write(data / 'library/zim/wikipedia.zim', 40_000)
        write(data / 'library/zim/small.zim', 4_000)
        write(data / 'library/maps/sud.pmtiles', 9_000)
        write(data / 'library/ebooks/livre.pdf', 1_000)
        write(data / 'library/loose.txt', 500)
        write(data / 'models/blobs/sha256-a', 30_000)
        write(data / 'state/pilot/pilot.db', 2_000)
        write(data / 'state/pilot/videos.db', 3_000)
        write(data / 'state/pilot/archive-index/a.sqlite', 7_000)
        write(data / 'state/pilot/zim-videos/v.webm', 6_000)
        write(data / 'state/openwebui/cache/embedding/m.bin', 5_000)
        write(data / 'state/openwebui/webui.db', 1_000)
        write(data / 'tmp/part', 100)
        write(data / 'surprise.bin', 200)
        write(self.base / 'application/pilot/app.py', 800)
        write(self.base / 'private/settings.json', 100)
        write(self.base / 'updates/op/previous/app.py', 2_500)
        write(self.base / 'application.failed-1/app.py', 300)
        write(self.base / 'images.tar', 8_000)
        write(self.base / 'notes.txt', 50)

    def scan(self):
        with patch.object(storage_report, 'docker_disks', return_value=[]):
            return storage_report.scan(self.app, self.config)

    def items(self, report):
        return {item['id']: item for item in report['items']}

    def test_every_file_lands_in_one_item_with_its_largest_entries(self):
        report = self.scan()
        items = self.items(report)
        expected = {'zim': 44_000, 'maps': 9_000, 'ebooks': 1_000, 'library-other': 500, 'models': 30_000,
                    'pilot-state': 2_000, 'video-db': 3_000, 'archive-index': 7_000, 'zim-videos': 6_000,
                    'webui-cache': 5_000, 'webui': 1_000, 'tmp': 100, 'data-other': 200, 'application': 800,
                    'private': 100, 'updates': 2_500, 'old-app': 300, 'images': 8_000, 'base-other': 50}
        if os.name == 'nt':
            self.assertEqual({key: items[key]['bytes'] for key in expected}, expected)
        else:
            # Allocated blocks: at least the logical size, rounded to the filesystem block.
            for key, size in expected.items():
                self.assertGreaterEqual(items[key]['bytes'], size, key)
        self.assertEqual(set(items), set(expected))
        self.assertEqual([entry['name'] for entry in items['zim']['top']], ['wikipedia.zim', 'small.zim'])
        self.assertEqual(items['updates']['top'][0]['name'], 'op/')
        self.assertTrue(items['archive-index']['rebuildable'])
        self.assertFalse(items['pilot-state']['rebuildable'])
        self.assertEqual(report['backups'], items['updates']['bytes'] + items['old-app']['bytes'])
        self.assertEqual(report['total'] + report['backups'], sum(item['bytes'] for item in report['items']))
        self.assertNotIn(str(self.base), json.dumps(report))

    def test_disk_totals_separate_setupsurvie_from_backups(self):
        report = self.scan()
        self.assertEqual(len(report['disks']), 1)
        disk = report['disks'][0]
        self.assertTrue(disk['data'])
        self.assertEqual(disk['setupsurvie'], report['total'])
        self.assertEqual(disk['backups'], report['backups'])
        self.assertEqual([category['id'] for category in report['categories']][:2], ['library', 'models'])

    @unittest.skipIf(os.name == 'nt', 'hard links are deduplicated on Linux only')
    def test_hard_links_count_once(self):
        data = self.base / 'data'
        os.link(data / 'models/blobs/sha256-a', data / 'models/blobs/sha256-b')
        items = self.items(self.scan())
        self.assertLess(items['models']['bytes'], 60_000)
        self.assertEqual(items['models']['files'], 2)

    @unittest.skipIf(os.name == 'nt', 'permissions are checked on Linux')
    def test_unreadable_folders_are_reported(self):
        data = self.base / 'data'
        secret = data / 'state/caddy/locked'
        write(secret / 'key', 100)
        secret.chmod(0)
        self.addCleanup(secret.chmod, 0o700)
        if os.access(secret, os.R_OK):
            self.skipTest('running as root')
        items = self.items(self.scan())
        self.assertEqual(items['caddy']['unreadable'], 1)

    def test_sealed_restore_point_uses_its_declared_size_on_its_own_disk(self):
        recovery = self.base.parent / '.SetupSurvie-secours'
        write(recovery / 'archives/old/app.py', 700)
        (recovery / 'point').mkdir()
        (recovery / 'point/transfer.json').write_text(json.dumps({'bytes': 123_456_789}))
        # Resolved paths: Windows runners hand out short temp names (RUNNER~1) that the scan expands.
        point = (recovery / 'point').resolve()
        other = {str(recovery.resolve()): 'backup-disk'}
        real_device = storage_report.device_of
        with patch.object(storage_report, 'device_of', lambda path: other.get(str(Path(path).resolve()), real_device(path))), \
                patch.object(storage_report.Walker, 'add', wraps_add(storage_report.Walker.add, point)):
            report = self.scan()
        items = self.items(report)
        self.assertEqual(items['restore-point']['bytes'], 123_456_789)
        self.assertTrue(items['restore-point']['estimated'])
        self.assertEqual(items['restore-point']['disks'], {'backup-disk': 123_456_789})
        self.assertIn('old-installs', items)

    def test_docker_disks_follow_the_desktop_settings(self):
        root = self.base.parent / 'DockerData'
        write(root / 'DockerDesktopWSL/disk/docker_data.vhdx', 2_000)
        appdata = self.base.parent / 'AppData'
        (appdata / 'Docker').mkdir(parents=True)
        (appdata / 'Docker/settings-store.json').write_text(json.dumps({'CustomWslDistroDir': str(root), 'dataFolder': ''}))
        with patch.object(storage_report, 'os') as fake_os:
            fake_os.name = 'nt'
            fake_os.environ = {'APPDATA': str(appdata)}
            found = storage_report.docker_disks()
        self.assertEqual(found, [(root / 'DockerDesktopWSL/disk/docker_data.vhdx').resolve()])

    def test_analyzer_runs_in_background_and_keeps_its_report(self):
        analyzer = storage_report.Analyzer(self.app, self.config)
        with patch.object(storage_report, 'docker_disks', return_value=[]):
            first = analyzer.status()
            self.assertIsNone(first['report'])
            self.assertTrue(first['disks'])
            for _ in range(200):
                if not analyzer.running:
                    break
                time.sleep(0.02)
            value = analyzer.status()
        self.assertFalse(value['scanning'])
        self.assertEqual(value['report']['schema'], 1)
        self.assertTrue((self.base / 'private' / storage_report.REPORT).is_file())

    def test_analysis_is_refused_during_a_transfer(self):
        (self.base / 'private/transfer-guard.json').write_text('{}')
        with self.assertRaises(setup.SetupError):
            storage_report.Analyzer(self.app, self.config).start()


def wraps_add(original, point):
    """Make the sealed point unreadable to the walker, as root-only folders are."""
    def add(walker, identifier, device, entry, name, expand=False):
        if Path(entry.path).resolve() == point:
            walker.item(identifier, device)['unreadable'] += 1
            return None
        return original(walker, identifier, device, entry, name, expand)
    return add


if __name__ == '__main__':
    unittest.main()
