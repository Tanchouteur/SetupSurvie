"""The storage guard must fail before a container can write to the system disk."""
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import linux_lab as lab
from delivery_paths import locked


class StorageGuardTests(unittest.TestCase):
    def test_game_mode_blocks_llm_start_before_process_execution(self):
        with tempfile.TemporaryDirectory() as root:
            mount = Path(root)
            (mount / 'private').mkdir()
            (mount / 'private/inference-paused.json').write_text('{}')
            with patch.object(lab, 'MOUNT', mount), patch.object(lab, 'checked_mount'), patch.object(lab, 'command') as run:
                with self.assertRaisesRegex(RuntimeError, 'mode jeu'):
                    lab.podman('start', lab.PREFIX + 'ollama')
                with self.assertRaisesRegex(RuntimeError, 'mode jeu'):
                    lab.podman('run', lab.reference('ollama'))
                run.assert_not_called()

    def test_game_mode_keeps_document_services_manageable(self):
        with tempfile.TemporaryDirectory() as root:
            mount = Path(root)
            (mount / 'private').mkdir()
            (mount / 'private/inference-paused.json').write_text('{}')
            with patch.object(lab, 'MOUNT', mount), patch.object(lab, 'checked_mount'), patch.object(lab, 'command') as run, patch.object(lab.os,'getuid',return_value=1000,create=True):
                lab.podman('restart', lab.PREFIX + 'portal')
                run.assert_called_once()

    def test_missing_image_prevents_podman(self):
        with tempfile.TemporaryDirectory() as root:
            with patch.object(lab, 'IMAGE', Path(root) / 'absent.img'), patch.object(lab, 'command') as run:
                with self.assertRaises(RuntimeError):
                    lab.podman('pull', 'example.invalid/image')
                run.assert_not_called()

    def test_image_larger_than_ssd_prevents_podman(self):
        with tempfile.TemporaryDirectory() as root:
            image = Path(root) / 'wrong.img'
            image.write_bytes(b'too small')
            with patch.object(lab, 'SSD', image.parent), patch.object(lab, 'disk_capacity', return_value=1), \
                    patch.object(lab, 'IMAGE', image), patch.object(lab, 'command') as run:
                with self.assertRaises(RuntimeError):
                    lab.podman('pull', 'example.invalid/image')
                run.assert_not_called()

    @unittest.skipUnless(sys.platform == 'linux', 'Agrandissement du laboratoire sur Linux.')
    def test_growth_waits_for_the_transfer_and_preserves_existing_data(self):
        with tempfile.TemporaryDirectory() as folder:
            mount = Path(folder)
            catalog = mount / 'data/catalog'
            catalog.mkdir(parents=True)
            image = mount / 'storage.img'
            image.write_bytes(b'setupsurvie')
            with patch.object(lab, 'IMAGE', image), \
                    patch.object(lab, 'checked_mount', return_value='/dev/loop-test'), \
                    patch.object(lab, 'disk_capacity', return_value=4096), \
                    patch.object(lab.os, 'geteuid', return_value=0), \
                    patch.object(lab.os, 'fchown'), \
                    patch.object(lab.shutil, 'disk_usage', return_value=lab.shutil._ntuple_diskusage(
                        30_000_000_000, 0, 30_000_000_000)), \
                    patch.object(lab, 'command') as run:
                with locked(catalog / 'publication.lock'):
                    with self.assertRaisesRegex(RuntimeError, 'publication documentaire'):
                        lab.grow(mount)
                self.assertEqual(image.read_bytes(), b'setupsurvie')
                run.assert_not_called()
                lab.grow(mount)
                self.assertEqual(image.stat().st_size, 4096)
                self.assertTrue(image.read_bytes().startswith(b'setupsurvie'))
                self.assertEqual([call.args[0] for call in run.call_args_list], [
                    ['losetup', '--set-capacity', '/dev/loop-test'], ['resize2fs', '/dev/loop-test'],
                ])

    def test_unmounted_volume_prevents_podman(self):
        with tempfile.TemporaryDirectory() as root:
            image = Path(root) / 'sparse.img'
            with image.open('wb') as stream:
                stream.truncate(1024)
            with patch.object(lab, 'SSD', image.parent), patch.object(lab, 'disk_capacity', return_value=4096), \
                    patch.object(lab, 'IMAGE', image), patch.object(lab, 'loop_device', return_value=None), \
                    patch.object(lab, 'command') as run:
                run.return_value.returncode = 1
                with self.assertRaises(RuntimeError):
                    lab.podman('pull', 'example.invalid/image')
                self.assertEqual(run.call_count, 1)
                self.assertEqual(run.call_args.args[0][0], 'findmnt')


if __name__ == '__main__':
    unittest.main()
