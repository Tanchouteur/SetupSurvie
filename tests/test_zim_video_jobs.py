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

    def test_offline_installation_queues_archive_inventory_until_host_is_available(self):
        data = Path(self.config['data_dir'])
        (data / 'library/zim/encyclopedie.zim').write_bytes(b'zim fixture')
        setup.schedule_initial_videos(self.app, self.config, offline=True)
        pending = self.app.work / setup.INITIAL_ZIM_VIDEO_REQUEST
        self.assertTrue(pending.exists())
        with patch.object(self.manager, 'index_ready', return_value=False), patch.object(jobs.subprocess, 'Popen') as process:
            self.manager.auto_index()
            process.assert_not_called()
            self.assertTrue(self.manager.status()['initial_video_inventory_pending'])
        with patch.object(self.manager, 'index_ready', return_value=True), patch.object(jobs.index_queue, 'gaming', return_value=True), patch.object(jobs.subprocess, 'Popen') as process:
            self.manager.auto_index()
            process.assert_not_called()
            self.assertTrue(pending.exists())
        with patch.object(self.manager, 'index_ready', return_value=True), patch.object(jobs.subprocess, 'Popen', return_value=MagicMock(pid=os.getpid())) as process:
            self.manager.auto_index()
            self.manager.auto_index()
            process.assert_called_once()
        state = self.manager.read()
        self.assertEqual(state['action'], 'video-inventory')
        self.assertTrue(state['options']['automatic'])
        self.assertFalse(pending.exists())
        self.assertFalse(self.manager.status()['initial_video_inventory_pending'])

    def test_partial_initial_video_inventory_does_not_block_text_indexing(self):
        data = Path(self.config['data_dir'])
        (data / 'library/zim/encyclopedie.zim').write_bytes(b'zim fixture')
        jobs.index_queue.enqueue(data, {'path': 'library/zim/encyclopedie.zim', 'sha256': 'a' * 64})
        self.manager.write({'phase': 'error', 'action': 'video-inventory', 'options': {'automatic': True}})
        with patch.object(self.manager, 'index_ready', return_value=True), patch.object(self.manager, 'start') as start:
            self.manager.auto_index()
        start.assert_called_once_with('index', {'automatic': True})

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
