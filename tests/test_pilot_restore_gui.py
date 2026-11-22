from importlib import util
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'scripts'))


class RestoreWindowTests(unittest.TestCase):
    def test_chooses_backup_and_new_destination_then_opens_site(self):
        self.exercise_restore(resume=False)

    def test_offers_to_resume_the_same_destination(self):
        self.exercise_restore(resume=True)

    def test_opens_restored_installation_without_a_kit_picker(self):
        gui = self.load_gui()
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp).resolve()
            with patch.object(sys, 'argv', ['restaurer', '--open', str(base)]), \
                 patch.object(gui.tk, 'Tk'), patch.object(gui.filedialog, 'askdirectory') as picker, \
                 patch.object(gui, 'start_restored') as start, patch.object(gui, 'show_operation') as show:
                gui.main()
                action = show.call_args.args[3]
                action(None)
                picker.assert_not_called()
                start.assert_called_once_with(base, progress=None)

    def load_gui(self):
        path = Path(__file__).resolve().parents[1]/'scripts/pilot_restore_gui.py'
        spec = util.spec_from_file_location('restore_window_test', path)
        gui = util.module_from_spec(spec)
        tk = MagicMock()
        with patch.dict(sys.modules, {'tkinter': tk}):
            spec.loader.exec_module(gui)
        return gui

    def exercise_restore(self, *, resume):
        gui = self.load_gui()
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp).resolve()
            kit, snapshot, disk = (root/name for name in ('kit', 'sauvegarde', 'autre disque'))
            for folder in (kit, snapshot, disk):
                folder.mkdir()
            (kit/'manifest.json').write_text('{}')
            (snapshot/'backup.json').write_text('{}')
            (disk/'SetupSurvie').mkdir()
            previous = disk/'SetupSurvie-Restaure-previous'
            if resume:
                previous.mkdir()
                gui.setup.write_json(previous/gui.RESTORE_JOURNAL, {
                    'schema': 1, 'phase': 'copying', 'project': 'survie-restored-test',
                    'inputs': gui.restore_inputs(snapshot, kit, 'windows'),
                })
            with patch.object(sys, 'argv', ['restore', str(kit)]), \
                 patch.object(gui, 'host_target', return_value='windows'), \
                 patch.object(gui.tk, 'Tk') as tk, patch.object(gui, 'ttk'), \
                 patch.object(gui.filedialog, 'askdirectory', side_effect=[str(snapshot), str(disk)]), \
                 patch.object(gui.messagebox, 'askokcancel', return_value=True) as create, \
                 patch.object(gui.messagebox, 'askyesnocancel', return_value=True) as resume_prompt, \
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
            self.assertEqual(restore.call_args.kwargs['resume'], resume)
            if resume:
                resume_prompt.assert_called_once()
                create.assert_not_called()
                self.assertEqual(work.parent, previous)
            else:
                resume_prompt.assert_not_called()
                create.assert_called_once()
                self.assertFalse(work.parent.exists())
            self.assertEqual(restore.call_args.kwargs['target'], 'windows')
            open_site.assert_called_once_with('http://127.0.0.1:8080')
