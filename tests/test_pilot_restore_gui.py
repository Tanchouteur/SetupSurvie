from importlib import util
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'scripts'))


class RestoreWindowTests(unittest.TestCase):
    def test_chooses_backup_and_new_destination_then_opens_site(self):
        path = Path(__file__).resolve().parents[1]/'scripts/pilot_restore_gui.py'
        spec = util.spec_from_file_location('restore_window_test', path)
        gui = util.module_from_spec(spec)
        tk = MagicMock()
        with patch.dict(sys.modules, {'tkinter': tk}):
            spec.loader.exec_module(gui)

        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp).resolve()
            kit, snapshot, disk = (root/name for name in ('kit', 'sauvegarde', 'autre disque'))
            for folder in (kit, snapshot, disk):
                folder.mkdir()
            (kit/'manifest.json').write_text('{}')
            (snapshot/'backup.json').write_text('{}')
            (disk/'SetupSurvie').mkdir()
            with patch.object(sys, 'argv', ['restore', str(kit)]), \
                 patch.object(gui, 'host_target', return_value='windows'), \
                 patch.object(gui.tk, 'Tk') as tk, patch.object(gui, 'ttk'), \
                 patch.object(gui.filedialog, 'askdirectory', side_effect=[str(snapshot), str(disk)]), \
                 patch.object(gui.messagebox, 'askokcancel', return_value=True), \
                 patch.object(gui.messagebox, 'askyesno', return_value=True), \
                 patch.object(gui, 'restore') as restore, patch.object(gui.webbrowser, 'open') as open_site, \
                 patch.object(gui.threading, 'Thread') as worker:
                worker.side_effect = lambda target, daemon: type('Worker', (), {'start': staticmethod(target)})()
                tk.return_value.after.side_effect = lambda _delay, callback: callback()
                gui.main()
            source, kit_root, work, data = restore.call_args.args
            self.assertEqual((source, kit_root), (snapshot, kit))
            self.assertEqual((work.name, data.name), ('private', 'data'))
            self.assertEqual(work.parent, data.parent)
            self.assertEqual(work.parent.parent, disk)
            self.assertTrue(work.parent.name.startswith('SetupSurvie-Restaure-'))
            self.assertFalse(work.parent.exists())
            self.assertEqual(restore.call_args.kwargs['target'], 'windows')
            open_site.assert_called_once_with('http://127.0.0.1:8080')
