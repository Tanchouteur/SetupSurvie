"""The storage guard must fail before a container can write to the system disk."""
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import linux_lab as lab


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

    def test_wrong_capacity_prevents_podman(self):
        with tempfile.TemporaryDirectory() as root:
            image = Path(root) / 'wrong.img'
            image.write_bytes(b'too small')
            with patch.object(lab, 'IMAGE', image), patch.object(lab, 'command') as run:
                with self.assertRaises(RuntimeError):
                    lab.podman('pull', 'example.invalid/image')
                run.assert_not_called()

    def test_unmounted_volume_prevents_podman(self):
        with tempfile.TemporaryDirectory() as root:
            image = Path(root) / 'sparse.img'
            with image.open('wb') as stream:
                stream.truncate(1024)
            with patch.object(lab, 'CAPACITY',1024),patch.object(lab, 'IMAGE', image), patch.object(lab, 'loop_device', return_value=None), \
                    patch.object(lab, 'command') as run:
                run.return_value.returncode = 1
                with self.assertRaises(RuntimeError):
                    lab.podman('pull', 'example.invalid/image')
                self.assertEqual(run.call_count, 1)
                self.assertEqual(run.call_args.args[0][0], 'findmnt')


if __name__ == '__main__':
    unittest.main()
