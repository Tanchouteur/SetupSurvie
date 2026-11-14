from collections import namedtuple
import shutil
import hashlib
import io
import json
import os
from pathlib import Path
import sys
import tempfile
import time
import unittest
from unittest.mock import patch, MagicMock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import content
import discovery
import library_tasks as jobs
import setup


class LibraryJobTests(unittest.TestCase):
    def setUp(self):
        # Tiny fixtures must not depend on the CI host having the production
        # 15 GB reserve. Capacity failure cases override this fixture explicitly.
        usage=namedtuple('Usage','total used free')(200_000_000_000,100_000_000_000,100_000_000_000)
        disk=patch.object(shutil,'disk_usage',return_value=usage);disk.start();self.addCleanup(disk.stop)
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.app = setup.Installation(self.root / 'private')
        self.config = self.app.init('linux', self.root / 'data', cpu=True)
        self.manager = jobs.Manager(self.app, self.config, 'compose')
        self.raw = b'archive test with checksum'
        self.item = {'id':'book', 'title':'Jardin', 'pack':'kiwix-themes',
                     'path':'library/zim/garden_en_all_2026-01.zim',
                     'url':'https://download.kiwix.org/zim/other/garden_en_all_2026-01.zim',
                     'bytes':len(self.raw), 'sha256':hashlib.sha256(self.raw).hexdigest()}

    def seed(self, action='download', phase='planned'):
        job = 'a' * 32; folder = self.manager.paths(job); folder.mkdir(parents=True)
        state = {'id':job, 'phase':phase, 'action':action, 'pid':os.getpid(),
                 'identity':discovery.identity(os.getpid()), 'options':{'themes':['agriculture'], 'languages':['fr','en'], 'max_add_gb':10}}
        self.manager.write(state); (folder / 'ready').touch()
        plan = {'schema':1, 'items':[self.item], 'candidates':[], 'remaining_download_bytes':len(self.raw),
                'missing_themes':[], 'library_bytes':0}
        setup.write_json(folder / 'plan.json', plan)
        return state, folder

    def test_index_requires_finished_reader_preparation_and_reports_progress(self):
        with self.assertRaises(setup.SetupError):self.manager.start('index',{})
        binary=self.manager.index_python();binary.parent.mkdir(parents=True);binary.touch()
        self.assertFalse(self.manager.status()['index_reader_ready'])
        setup.write_json(self.app.work/'search-tools/reader-ready.json',{'libzim':'3.13.1'})
        self.assertTrue(self.manager.status()['index_reader_ready'])
        progress=Path(self.config['data_dir'])/'state/pilot/archive-index/progress.json'
        setup.write_json(progress,{'phase':'paused','archives':2,'articles':100})
        self.assertEqual(self.manager.status()['search_index']['articles'],100)

    def test_backup_operation_lock_refuses_new_job_before_spawning(self):
        lock=self.app.work/'library-web/operation.lock';lock.mkdir(parents=True)
        with patch.object(jobs.subprocess,'Popen') as launch:
            with self.assertRaisesRegex(setup.SetupError,'opération'):
                self.manager.start('plan',{'themes':['agriculture'],'max_add_gb':0})
            launch.assert_not_called()
        self.assertEqual(self.manager.read()['phase'],'idle')

    def test_geography_uses_bounded_detached_worker_without_model_or_restart(self):
        state,folder=self.seed(action='geography')
        state['options']={'lat':43.1,'lon':6.1,'radius_km':5,'terrain':True};self.manager.write(state)
        with patch.object(self.manager,'check_storage',return_value=(self.root/'data',None)), patch.object(jobs.geography_data,'prepare') as prepare, patch.object(self.app,'compose') as compose:
            self.manager.run(state['id'])
        self.assertEqual(self.manager.read()['phase'],'completed')
        self.assertEqual(prepare.call_args.args[1],state['options']);compose.assert_not_called()
        with patch.object(self.manager,'check_storage'),patch.object(jobs.subprocess,'Popen') as launch:
            with self.assertRaises(setup.SetupError):self.manager.start('geography',{'lat':43,'lon':6,'radius_km':26})
            launch.assert_not_called()

    def test_all_themes_and_unlimited_transfer_are_accepted(self):
        with patch.object(jobs.subprocess,'Popen',return_value=MagicMock(pid=os.getpid())):
            self.manager.start('plan',{'themes':list(jobs.kiwix_select.themes()),'max_add_gb':0})
        self.assertEqual(set(self.manager.read()['options']['themes']),set(jobs.kiwix_select.themes()))
        self.assertEqual(self.manager.read()['options']['max_add_gb'],0)

    def test_learning_review_is_reported_and_old_plans_remain_readable(self):
        state,folder=self.seed()
        plan={'items':[],'candidates':[],'remaining_download_bytes':0,'missing_themes':[],'library_bytes':0}
        setup.write_json(folder/'plan.json',plan)
        self.assertEqual(self.manager.status()['plan']['learning_coverage'],[])
        self.assertTrue(self.manager.status()['plan']['legacy_selection'])
        plan['learning_coverage']=[{'id':'sciences','status':'references_to_review','references':1,'local_references':0,'skills_to_review':['Algèbre']}]
        setup.write_json(folder/'plan.json',plan)
        self.assertEqual(self.manager.status()['plan']['learning_coverage'],plan['learning_coverage'])

    def test_pdf_plan_updates_source_receipt_and_restarts_search_without_ollama(self):
        state,folder=self.seed()
        plan=json.loads((folder/'plan.json').read_text())
        pdf={**self.item,'path':'library/guides/test.pdf','language':'fr','publisher':'Test',
             'edition':'2026','licence':'Test fixture'}
        plan['items']=[pdf];setup.write_json(folder/'plan.json',plan)
        class Response(io.BytesIO):
            status=200;headers={}
            def geturl(inner):return pdf['url']
        opener=MagicMock();opener.open.return_value=Response(self.raw)
        with patch.object(content.urllib.request,'build_opener',return_value=opener), \
             patch.object(self.app,'catalog'),patch.object(self.app,'compose') as compose:
            self.manager.run(state['id'])
        self.assertEqual(self.manager.read()['phase'],'completed')
        receipt=content.catalog(Path(self.config['data_dir'])/'catalog/downloaded-content.json')
        self.assertEqual(receipt,[pdf])
        compose.assert_called_once_with(self.config,'restart','kiwix','pilot')

    def test_selection_is_validated_before_spawning_any_command(self):
        for body in [{'themes':['unknown']}, {'themes':['agriculture'],'max_add_gb':True},
                     {'themes':['agriculture'],'max_add_gb':-1}, {'themes':['agriculture'],'languages':['other']}]:
            with self.subTest(body=body), patch.object(jobs.subprocess, 'Popen') as launch:
                with self.assertRaises(setup.SetupError):self.manager.start('plan', body)
                launch.assert_not_called()

    def test_fixed_detached_worker_and_duplicate_operation_rejected(self):
        fake = MagicMock(pid=os.getpid())
        with patch.object(jobs.subprocess, 'Popen', return_value=fake) as launch:
            self.manager.start('plan', {'themes':['agriculture'], 'command':'rm anything', 'path':'/outside'})
        command = launch.call_args.args[0]
        self.assertEqual(Path(command[1]).name, 'library_tasks.py')
        self.assertNotIn('/outside', command)
        with patch.object(jobs.subprocess, 'Popen') as launch:
            with self.assertRaises(setup.SetupError):self.manager.start('plan', {'themes':['agriculture']})
            launch.assert_not_called()

    def test_status_survives_new_controller_and_never_exposes_process_or_paths(self):
        state, folder = self.seed(phase='downloading')
        fresh = jobs.Manager(self.app, self.config, 'compose')
        value = fresh.status()
        self.assertEqual(value['phase'], 'downloading')
        for key in ('pid','identity','directory','secret'):self.assertNotIn(key, value)
        self.assertEqual(value['plan']['count'], 1)

    def test_dead_worker_is_reported_interrupted(self):
        self.seed(phase='planning')
        with patch.object(discovery, 'identity', return_value=None):
            self.assertEqual(self.manager.status()['phase'], 'interrupted')

    def test_old_download_id_and_unknown_action_cannot_execute(self):
        self.seed()
        for action, body in [('download',{'id':'b'*32}), ('run',{}), ('download',{'id':'../outside'})]:
            with patch.object(jobs.subprocess, 'Popen') as launch:
                with self.assertRaises(setup.SetupError):self.manager.start(action, body)
                launch.assert_not_called()

    def test_pause_preserves_partial_and_mode_game(self):
        state, folder = self.seed(phase='downloading')
        paused = self.app.work / 'inference-paused.json'; paused.write_text('{"reason":"gaming"}')
        partial = Path(self.config['data_dir']) / (self.item['path'] + '.part')
        partial.parent.mkdir(parents=True, exist_ok=True); partial.write_bytes(self.raw[:3])
        self.manager.pause()
        with patch.object(self.app, 'compose') as compose:
            self.manager.run(state['id']); compose.assert_not_called()
        self.assertEqual(self.manager.read()['phase'], 'paused')
        self.assertEqual(partial.read_bytes(), self.raw[:3])
        self.assertTrue(paused.exists())

    def test_user_shutdown_pauses_detached_job_before_services_can_stop(self):
        import control
        state,folder=self.seed(phase='downloading')
        def stop(app):self.manager.run(state['id'])
        with patch.object(control,'stop',side_effect=stop) as stopped:
            jobs.shutdown(self.app,self.config)
        stopped.assert_called_once_with(self.app)
        self.assertTrue((folder/'cancel').exists())
        self.assertEqual(self.manager.current()['phase'],'paused')

    def test_download_verifies_and_refreshes_only_kiwix(self):
        state, _ = self.seed()
        paused = self.app.work / 'inference-paused.json'; paused.write_text('{"reason":"gaming"}')
        class Response(io.BytesIO):
            status = 200; headers = {}
            def geturl(self):return self.item_url
        response = Response(self.raw); response.item_url = self.item['url']
        opener = MagicMock(); opener.open.return_value = response
        with patch('content_mirrors.opener_for',return_value=None), patch.object(content.urllib.request, 'build_opener', return_value=opener), \
             patch.object(self.app, 'catalog') as catalog, patch.object(self.app, 'compose') as compose:
            self.manager.run(state['id'])
        self.assertEqual(self.manager.read()['phase'], 'completed')
        self.assertEqual((Path(self.config['data_dir']) / self.item['path']).read_bytes(), self.raw)
        catalog.assert_called_once_with(self.config)
        compose.assert_called_once_with(self.config, 'restart', 'kiwix')
        self.assertTrue(paused.exists())

    def test_bad_hash_never_published_and_never_refreshes(self):
        state, _ = self.seed()
        def fail(*a, **k):raise setup.SetupError('bad checksum')
        with patch.object(content, 'download', side_effect=fail), patch.object(self.app, 'compose') as compose:
            self.manager.run(state['id']); compose.assert_not_called()
        self.assertEqual(self.manager.read()['phase'], 'error')
        self.assertFalse((Path(self.config['data_dir']) / self.item['path']).exists())

    def test_missing_lab_mount_blocks_before_spawn(self):
        import linux_lab as lab
        self.manager.backend = 'lab'
        with patch.object(lab, 'checked_mount', side_effect=RuntimeError('volume absent')), patch.object(jobs.subprocess, 'Popen') as launch:
            with self.assertRaises(RuntimeError):self.manager.start('plan', {'themes':['agriculture']})
            launch.assert_not_called()

    def test_library_recovery_restores_controller_without_starting_ollama(self):
        import control
        import lab_refresh_library
        import linux_lab as lab
        result=MagicMock(returncode=0)
        with patch.object(lab,'checked_mount'),patch.object(lab,'MOUNT',self.root), \
             patch.object(setup.Installation,'load',return_value={**self.config,'bind':'127.0.0.1'}), \
             patch.object(setup.Installation,'catalog'),patch.object(lab_refresh_library.shutil,'copytree'), \
             patch.object(lab,'podman',return_value=result) as podman,patch.object(control,'start') as start:
            lab_refresh_library.refresh()
        self.assertEqual((self.root/'runtime/deploy/assistant-system.fr.txt').read_text(),(setup.ROOT/'deploy/assistant-system.fr.txt').read_text())
        self.assertEqual(start.call_args.args[2],'lab')
        self.assertTrue(any('pilot.configure' in str(call) for call in podman.call_args_list))
        self.assertFalse(any('ollama' in str(call) for call in podman.call_args_list))


if __name__ == '__main__':unittest.main()
