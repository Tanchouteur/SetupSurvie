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

    def test_global_pause_requests_a_category_checkpoint_and_holds_host_preparations(self):
        state, folder = self.seed(action='category-index', phase='downloading')
        marker = self.root / 'data/state/pilot/work-queue.pause'
        marker.touch()
        self.manager.auto_index()
        self.assertTrue((folder / 'cancel').is_file())
        self.assertFalse((folder / 'auto-pause').exists())
        self.manager.write({**state, 'phase': 'paused'})
        with self.assertRaisesRegex(setup.SetupError, 'Reprenez la file'):
            self.manager.start('category-index', {})
        with patch.object(self.manager, 'index_ready') as readiness:
            self.manager.auto_index()
        readiness.assert_not_called()
        marker.unlink()
        self.assertFalse(self.manager.queue_paused())

    def test_reference_download_pins_only_the_requested_edition_and_keeps_previous_plan(self):
        import library_reference

        item = {**self.item, 'classification': 'main'}
        archive = Path(item['path']).name
        worker = MagicMock(pid=os.getpid())
        with patch.object(library_reference, 'load', return_value={'items': [item]}), \
             patch.object(jobs.subprocess, 'Popen', return_value=worker) as launch:
            with self.assertRaisesRegex(setup.SetupError, 'ne figure pas'):
                self.manager.start('download', {'reference_archive': 'old.zim'})
            launch.assert_not_called()
            job = self.manager.start('download', {'reference_archive': archive})
            self.assertEqual(content.catalog(self.manager.paths(job)/'plan.json'), [item])
            self.assertEqual(self.manager.status()['plan']['count'], 1)
            self.assertEqual(self.manager.status()['action'], 'download')

            self.manager.write({**self.manager.read(), 'phase': 'paused', 'options': {}})
            with self.assertRaisesRegex(setup.SetupError, 'téléchargement précédent'):
                self.manager.start('download', {'reference_archive': archive})
            launch.assert_called_once()

    def test_reference_restoration_verifies_before_replacing_or_removing_exact_files(self):
        import library_reference
        from pilot import collection_sort

        root = self.root/'data'
        item = {**self.item, 'classification': 'other'}
        target = root/item['path']
        previous = target.with_name('garden_en_all_2025-12.zim')
        extra = target.with_name('notes_fr_all_2026-01.zim')
        target.write_bytes(b'wrong size')
        previous.write_bytes(b'older edition')
        extra.write_bytes(b'extra archive')
        catalog = {'items': [item]}
        preview = library_reference.restoration_plan(root, catalog, collection_sort.Sort())
        with patch.object(library_reference, 'load', return_value=catalog), \
             patch.object(jobs.subprocess, 'Popen', return_value=MagicMock(pid=os.getpid())):
            with self.assertRaisesRegex(setup.SetupError, 'a changé'):
                self.manager.start('download', {'reference_confirmation': '1'*64})
            job = self.manager.start('download', {'reference_confirmation': preview['confirmation_token']})

        class Response(io.BytesIO):
            status = 200
            headers = {}

            def geturl(self):
                return item['url']

        with patch('content_mirrors.opener_for', return_value=None), \
             patch('content_mirrors.network_open', return_value=Response(b'x'*len(self.raw))), \
             patch.object(self.app, 'compose') as compose:
            self.manager.run(job)
            compose.assert_not_called()
        self.assertEqual(self.manager.read()['phase'], 'error')
        self.assertEqual(target.read_bytes(), b'wrong size')
        self.assertTrue(previous.is_file())
        self.assertTrue(extra.is_file())

        target.with_name(target.name+'.part').write_bytes(self.raw)
        with patch.object(self.app, 'catalog'), patch.object(self.app, 'compose') as compose:
            self.manager.run(job)
        self.assertEqual(self.manager.read()['phase'], 'completed')
        self.assertEqual(target.read_bytes(), self.raw)
        self.assertFalse(previous.exists())
        self.assertFalse(extra.exists())
        self.assertEqual(collection_sort.load(root/'catalog').state(collection_sort.archive(target.name)), 'other')
        self.assertEqual([call.args[1:] for call in compose.call_args_list], [('stop', 'kiwix'), ('start', 'kiwix')])

    def test_reference_selection_applies_ranking_at_once_and_keeps_a_paused_download(self):
        import library_reference
        from pilot import collection_sort

        root = self.root/'data'
        state, folder = self.seed(phase='paused')
        partial = root/(self.item['path']+'.part')
        partial.write_bytes(b'xx')
        present = {**self.item, 'id': 'present', 'path': 'library/zim/notes_fr_all_2026-01.zim',
                   'title': 'Notes', 'bytes': 5, 'classification': 'other'}
        (root/present['path']).write_bytes(b'notes')
        missing = {**self.item, 'id': 'missing', 'path': 'library/zim/wikipedia_en_all_maxi_2026-08.zim',
                   'title': 'Wikipédia EN', 'classification': 'main'}
        catalog = {'items': [present, missing]}
        plan = library_reference.restoration_plan(root, catalog, collection_sort.Sort())
        key = collection_sort.archive('notes_fr_all_2026-01.zim')
        self.assertEqual([row['key'] for row in plan['moves']], [key])
        with patch.object(library_reference, 'load', return_value=catalog), \
             patch.object(jobs.subprocess, 'Popen') as launch:
            with self.assertRaisesRegex(setup.SetupError, 'Cochez'):
                self.manager.start('download', {'reference_confirmation': plan['confirmation_token'],
                                                'selection': {'downloads': [], 'removals': [], 'moves': []}})
            with self.assertRaisesRegex(setup.SetupError, 'a changé'):
                self.manager.start('download', {'reference_confirmation': plan['confirmation_token'],
                                                'selection': {'moves': ['zim:inconnue']}})
            result = self.manager.start('download', {'reference_confirmation': plan['confirmation_token'],
                                                     'selection': {'moves': [key]}})
            launch.assert_not_called()
            self.assertIsNone(result)
            # A download still needs the paused one to be cancelled or resumed first.
            plan = library_reference.restoration_plan(root, catalog, collection_sort.load(root/'catalog'))
            with self.assertRaisesRegex(setup.SetupError, 'Annulez ou reprenez'):
                self.manager.start('download', {'reference_confirmation': plan['confirmation_token'],
                                                'selection': {'downloads': ['wikipedia_en_all_maxi_2026-08.zim']}})
        self.assertEqual(collection_sort.load(root/'catalog').state(key), 'other')
        self.assertEqual(self.manager.read()['phase'], 'paused')
        self.assertTrue(partial.is_file())

    def test_reference_selection_downloads_only_the_ticked_edition(self):
        import library_reference
        from pilot import collection_sort

        root = self.root/'data'
        wanted = {**self.item, 'classification': 'main'}
        unwanted = {**self.item, 'id': 'en', 'path': 'library/zim/wikipedia_en_all_maxi_2026-08.zim',
                    'title': 'Wikipédia EN', 'bytes': 10**12, 'classification': 'main'}
        extra = root/'library/zim/notes_fr_all_2026-01.zim'
        extra.write_bytes(b'extra archive')
        catalog = {'items': [wanted, unwanted]}
        plan = library_reference.restoration_plan(root, catalog, collection_sort.Sort())
        self.assertFalse(plan['space_sufficient'])
        with patch.object(library_reference, 'load', return_value=catalog), \
             patch.object(jobs.subprocess, 'Popen', return_value=MagicMock(pid=os.getpid())):
            job = self.manager.start('download', {'reference_confirmation': plan['confirmation_token'],
                                                  'selection': {'downloads': [Path(wanted['path']).name]}})
        self.assertEqual([item['id'] for item in content.catalog(self.manager.paths(job)/'plan.json')], ['book'])
        (root/(wanted['path']+'.part')).write_bytes(self.raw)
        with patch.object(self.app, 'catalog'), patch.object(self.app, 'compose'):
            self.manager.run(job)
        self.assertEqual(self.manager.read()['phase'], 'completed')
        self.assertEqual((root/wanted['path']).read_bytes(), self.raw)
        self.assertFalse((root/unwanted['path']).exists())
        self.assertTrue(extra.is_file())

    def test_cancel_deletes_started_files_and_disarms_recovery(self):
        root = self.root/'data'
        state, folder = self.seed(phase='paused')
        partial = root/(self.item['path']+'.part')
        partial.write_bytes(b'abc')
        finished = root/'library/zim/kept_fr_all_2026-01.zim'
        finished.write_bytes(b'done')
        setup.write_json(self.app.work/'content-resume.json', {'schema': 1, 'enabled': True, 'selection': str(folder/'plan.json')})
        with self.assertRaisesRegex(setup.SetupError, 'plus dans la file'):
            self.manager.cancel('b'*32)
        self.assertEqual(self.manager.cancel(state['id']), 'cancelled')
        self.assertFalse(partial.exists())
        self.assertTrue(finished.is_file())
        current = self.manager.read()
        self.assertEqual(current['phase'], 'cancelled')
        self.assertIn('1 fichier(s) commencé(s) supprimé(s)', current['message'])
        self.assertFalse(json.loads((self.app.work/'content-resume.json').read_text())['enabled'])
        self.assertNotIn('plan', self.manager.status())
        with self.assertRaisesRegex(setup.SetupError, 'déjà terminé ou annulé'):
            self.manager.cancel(state['id'])

    def test_cancel_of_a_running_download_cleans_up_at_the_next_checkpoint(self):
        root = self.root/'data'
        state, folder = self.seed(phase='downloading')
        self.assertEqual(self.manager.cancel(state['id']), 'requested')
        self.assertTrue((folder/'cancel').is_file() and (folder/'discard').is_file())
        self.assertIn('Annulation demandée', self.manager.status()['message'])
        partial = root/(self.item['path']+'.part')
        partial.write_bytes(b'abc')
        self.manager.write({**self.manager.read(), 'action': 'download'})
        self.manager.run(state['id'])
        self.assertEqual(self.manager.read()['phase'], 'cancelled')
        self.assertFalse(partial.exists())

    def test_index_requires_finished_reader_preparation_and_reports_progress(self):
        with self.assertRaises(setup.SetupError):self.manager.start('index',{})
        binary=self.manager.index_python();binary.parent.mkdir(parents=True);binary.touch()
        self.assertFalse(self.manager.status()['index_reader_ready'])
        setup.write_json(self.app.work/'search-tools/reader-ready.json',{'libzim':'3.13.1'})
        self.assertTrue(self.manager.status()['index_reader_ready'])
        progress=Path(self.config['data_dir'])/'state/pilot/archive-index/progress.json'
        setup.write_json(progress,{'phase':'paused','archives':2,'articles':100})
        self.assertEqual(self.manager.status()['search_index']['articles'],100)

    def test_failed_reader_preflight_is_visible_and_invalidates_old_ready_marker(self):
        state,folder=self.seed(action='index',phase='starting');state['options']={};self.manager.write(state)
        marker=self.app.work/'search-tools/reader-ready.json';setup.write_json(marker,{'libzim':'3.13.1'})
        report={'job_id':state['id'],'phase':'partial','archives':135,'completed':0,'articles':0,'results':[],
                'reader_probe':{'schema':1,'ok':False,'error':'reader_import'},'error_summary':{'reader_import':1}}
        setup.write_json(self.root/'data/state/pilot/archive-index/progress.json',report)
        with patch.object(self.manager,'check_storage',return_value=(self.root/'data',None)),patch.object(jobs.subprocess,'Popen',return_value=MagicMock(pid=os.getpid(),wait=lambda:1)):
            self.manager.run(state['id'])
        value=self.manager.status();self.assertEqual(value['phase'],'error');self.assertIn('ne parvient pas à se charger',value['message'])
        self.assertEqual(value['reader_probe']['error'],'reader_import');self.assertFalse(marker.exists())

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
