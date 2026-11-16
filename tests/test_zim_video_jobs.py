"""Host job integration, no actual detached process, archive, network or model."""
import os
from pathlib import Path
import unittest
from unittest.mock import patch,MagicMock
import test_library_tasks as fixtures
import library_tasks as jobs
import setup


class ArchiveVideoJobTests(unittest.TestCase):
    setUp=fixtures.LibraryJobTests.setUp
    seed=fixtures.LibraryJobTests.seed

    def test_prepared_reader_and_non_gaming_state_are_required_before_spawning(self):
        with patch.object(jobs.subprocess,'Popen') as process:
            with self.assertRaises(setup.SetupError):self.manager.start('video-inventory',{})
            process.assert_not_called()
        with patch.object(self.manager,'index_ready',return_value=True),patch.object(jobs.index_queue,'gaming',return_value=True),patch.object(jobs.subprocess,'Popen') as process:
            with self.assertRaisesRegex(setup.SetupError,'mode jeu'):self.manager.start('video-inventory',{})
            process.assert_not_called()

    def test_fixed_reader_command_and_completed_report_never_restart_services(self):
        state,folder=self.seed(action='video-inventory',phase='starting');state['options']={};self.manager.write(state)
        report=Path(self.config['data_dir'])/'state/pilot/zim-videos/progress.json';setup.write_json(report,{'job_id':state['id'],'phase':'completed'})
        with patch.object(jobs.subprocess,'Popen',return_value=MagicMock(pid=os.getpid(),wait=lambda:0)) as process,patch.object(self.app,'compose') as compose:
            self.manager.run(state['id'])
        command=process.call_args.args[0];self.assertEqual(command[0],str(self.manager.index_python()));self.assertIn('inventory_zim_videos.py',command[3])
        self.assertIn('--cancel',command);self.assertIn('--job-id',command);self.assertNotIn('pip',command);compose.assert_not_called()
        self.assertEqual(self.manager.read()['phase'],'completed')

    def test_cancelled_inventory_keeps_pause_and_gaming_requests_a_cooperative_pause(self):
        state,folder=self.seed(action='video-inventory',phase='downloading');(folder/'cancel').touch()
        with patch.object(jobs.subprocess,'Popen') as process:self.manager.run(state['id'])
        process.assert_not_called();self.assertEqual(self.manager.read()['phase'],'paused')
        state['phase']='downloading';self.manager.write(state);(folder/'cancel').unlink()
        with patch.object(jobs.index_queue,'gaming',return_value=True),patch.object(self.manager,'pause') as pause:self.manager.auto_index()
        pause.assert_called_once_with(automatic=True)

    def test_dead_supervisor_recovers_only_the_matching_terminal_report(self):
        state,folder=self.seed(action='video-inventory',phase='downloading');report=Path(self.config['data_dir'])/'state/pilot/zim-videos/progress.json'
        setup.write_json(report,{'job_id':state['id'],'phase':'partial'})
        with patch.object(jobs.discovery,'identity',return_value=None):self.assertEqual(self.manager.current()['phase'],'error')
        state['phase']='downloading';self.manager.write(state);setup.write_json(report,{'job_id':'different','phase':'completed'})
        with patch.object(jobs.discovery,'identity',return_value=None):self.assertEqual(self.manager.current()['phase'],'interrupted')
