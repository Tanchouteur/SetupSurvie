"""YouTube list button: site API, host job and cooperative pause. No network."""
import asyncio
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from unittest.mock import AsyncMock,MagicMock,patch

from fastapi import HTTPException
from fastapi.testclient import TestClient

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import library_tasks as jobs  # noqa: E402
import setup  # noqa: E402
import test_library_tasks as fixtures  # noqa: E402
import test_youtube_videos as downloads  # noqa: E402
import youtube_videos as tool  # noqa: E402
from pilot import app as gateway,store,youtube_pipeline,youtube_downloads as site  # noqa: E402

A,B='aaaaaaaaaaa','bbbbbbbbbbb'
LIST='[Eau]\nhttps://youtu.be/'+A+'\nhttps://www.youtube.com/playlist?list=PL1\nhttps://youtu.be/'+B+'\n'


class SiteTests(unittest.TestCase):
    def setUp(self):
        temporary=tempfile.TemporaryDirectory();self.addCleanup(temporary.cleanup)
        p=patch.object(store,'ROOT',Path(temporary.name));p.start();self.addCleanup(p.stop);store.init()
        self.command=AsyncMock(return_value={'accepted':True})
        p=patch.object(site.operations,'library_command',self.command);p.start();self.addCleanup(p.stop)

    def test_first_online_installation_queues_its_list_once(self):
        deploy = store.ROOT / 'deploy'
        deploy.mkdir()
        (deploy / youtube_pipeline.INSTALLATION_LIST).write_text(LIST, encoding='utf-8-sig')
        data = store.ROOT / 'data'
        state = data / 'state/pilot'
        state.mkdir(parents=True)
        installation = MagicMock(work=store.ROOT / 'private')
        with patch.object(setup, 'ROOT', store.ROOT), patch.object(store, 'ROOT', state):
            store.init()
            self.assertFalse(youtube_pipeline.enqueue_installation_list())
            setup.schedule_initial_videos(installation, {'data_dir': data}, offline=True)
            self.assertFalse(youtube_pipeline.enqueue_installation_list())
            setup.schedule_initial_videos(installation, {'data_dir': data}, offline=False)
            self.assertTrue(youtube_pipeline.enqueue_installation_list())
            job, = youtube_pipeline.pending()
            identifier = job['id']
            row = youtube_pipeline.read(identifier)
            self.assertEqual((row['height'], row['total']), (480, 2))
            self.assertEqual((site.folder() / (identifier + '.txt')).read_text(encoding='utf-8'), LIST)
            youtube_pipeline.update(identifier, status='paused')
            youtube_pipeline.initialize()
            self.assertTrue(youtube_pipeline.enqueue_installation_list())
            self.assertEqual(youtube_pipeline.pending(), [])
            self.assertEqual(youtube_pipeline.read(identifier)['status'], 'paused')

    def test_check_explains_refused_lines_without_network(self):
        value=site.check(LIST)
        self.assertEqual([item['id'] for item in value['videos']],[A,B]);self.assertEqual(value['videos'][0]['theme'],'Eau')
        self.assertEqual(value['refused'][0]['reason'],'playlist_refused');self.assertIn('liste de lecture',value['refused'][0]['message'])

    def test_start_saves_the_list_for_the_host_and_sends_only_its_identifier(self):
        value=asyncio.run(site.start(LIST,480))
        self.assertTrue(value['accepted']);action,body=self.command.await_args.args
        self.assertEqual(action,'youtube-download');self.assertEqual(set(body),{'list','max_height'});self.assertEqual(body['max_height'],480)
        self.assertLess(len(json.dumps(body)),1024)
        saved=store.ROOT/'youtube-lists'/(body['list']+'.txt');self.assertEqual(saved.read_text(),LIST)
        if os.name!='nt':self.assertEqual(saved.stat().st_mode&0o777,0o644)
        for text,height,code in [('bonjour',480,400),(LIST,1080,400),('x'*300_001,480,413)]:
            with self.assertRaises(HTTPException) as caught:asyncio.run(site.start(text,height))
            self.assertEqual(caught.exception.status_code,code)
        for _ in range(25):asyncio.run(site.start(LIST,360))
        self.assertEqual(len(list((store.ROOT/'youtube-lists').glob('*.txt'))),site.KEEP_LISTS)

    def test_status_and_pause_only_concern_youtube_downloads(self):
        self.command.return_value={'phase':'downloading','action':'index'}
        self.assertEqual(asyncio.run(site.status())['phase'],'busy')
        with self.assertRaises(HTTPException) as caught:asyncio.run(site.pause())
        self.assertEqual(caught.exception.status_code,409)
        self.command.return_value={'phase':'downloading','action':'youtube-download','message':'Téléchargement…','options':{'max_height':480,'videos':2},
                                   'youtube':{'videos':2,'done':1,'current':{'index':2},'counts':{'downloaded':1},'items':[{'line':2,'status':'downloaded'}],'secret':'x'}}
        value=asyncio.run(site.status())
        self.assertEqual(value['progress']['current'],{'index':2});self.assertNotIn('secret',value['progress']);self.assertFalse(value['resumable'])
        asyncio.run(site.pause());self.assertEqual(self.command.await_args.args[0],'youtube-download-pause')
        self.command.side_effect=HTTPException(503,'Le service de téléchargement ne répond pas.')
        self.assertEqual(asyncio.run(site.status())['available'],False)

    def test_finished_job_refreshes_the_video_inventory_once(self):
        from pilot import videos
        self.command.return_value={'id':'j'*32,'phase':'completed','action':'youtube-download','options':{},'youtube':{}}
        with patch.object(site,'REFRESHED',None),patch.object(videos,'ensure_fresh',AsyncMock(return_value='refreshing')) as refresh:
            asyncio.run(site.status());asyncio.run(site.status())
        refresh.assert_awaited_once_with(force=True)

    def test_http_endpoints_are_reserved_to_the_family_profile(self):
        client=TestClient(gateway.app)
        self.addCleanup(gateway.app.dependency_overrides.clear)
        gateway.app.dependency_overrides[gateway.user]=lambda:{'id':'enfant','role':'user'}
        self.assertEqual(client.post('/api/admin/youtube-downloads/check',json={'text':LIST}).status_code,403)
        self.assertEqual(client.get('/api/admin/youtube-downloads').status_code,403)
        gateway.app.dependency_overrides[gateway.user]=lambda:{'id':'famille','role':'admin'}
        self.assertEqual(len(client.post('/api/admin/youtube-downloads/check',json={'text':LIST}).json()['videos']),2)
        with patch.object(youtube_pipeline,'launch') as launch:
            response=client.post('/api/admin/youtube-downloads',json={'text':LIST,'max_height':720})
        self.assertEqual(response.status_code,202)
        queued=youtube_pipeline.read(response.json()['job'])
        self.assertEqual((queued['height'],queued['status']), (720,'queued'))
        launch.assert_called_once()
        self.assertEqual(client.post('/api/admin/youtube-downloads/resume').status_code,202)
        self.assertEqual(self.command.await_args.args,('youtube-download',{'resume':True}))


class HostJobTests(unittest.TestCase):
    setUp=fixtures.LibraryJobTests.setUp
    seed=fixtures.LibraryJobTests.seed

    def saved_list(self,text=LIST):
        folder=Path(self.config['data_dir'])/'state/pilot/youtube-lists';folder.mkdir(parents=True,exist_ok=True)
        identifier='c'*32;(folder/(identifier+'.txt')).write_text(text);return identifier

    def test_start_copies_the_list_and_spawns_the_supervisor(self):
        identifier=self.saved_list()
        with patch.object(jobs.subprocess,'Popen',return_value=MagicMock(pid=os.getpid())) as process:
            self.manager.start('youtube-download',{'list':identifier,'max_height':480})
        state=self.manager.read();folder=self.manager.paths(state['id'])
        self.assertEqual(state['action'],'youtube-download');self.assertEqual(state['options'],{'max_height':480,'videos':2})
        self.assertEqual((folder/'liste.txt').read_text(),LIST);self.assertIn('library_tasks.py',process.call_args.args[0][1])
        for body in ({'list':'../x','max_height':480},{'list':'d'*32,'max_height':480},{'list':identifier,'max_height':1080}):
            state['phase']='completed';self.manager.write(state)
            with patch.object(jobs.subprocess,'Popen') as process,self.assertRaises(setup.SetupError):self.manager.start('youtube-download',body)
            process.assert_not_called()
        self.saved_list('rien\n');state['phase']='completed';self.manager.write(state)
        with self.assertRaisesRegex(setup.SetupError,'aucune adresse'):self.manager.start('youtube-download',{'list':'c'*32})

    def run_job(self,progress,code=0,cancel=False):
        state,folder=self.seed(action='youtube-download',phase='starting');state['options']={'max_height':480,'videos':2};self.manager.write(state)
        (folder/'liste.txt').write_text(LIST)
        if cancel:(folder/'cancel').touch()
        def spawn(command,**options):
            setup.write_json(folder/'progress.json',progress);return MagicMock(pid=os.getpid(),wait=lambda:code)
        with patch.object(jobs.subprocess,'Popen',side_effect=spawn) as process:self.manager.run(state['id'])
        return state,folder,process

    def test_run_uses_the_fixed_tool_command_and_reports_counts(self):
        state,folder,process=self.run_job({'phase':'completed','counts':{'downloaded':1,'skipped':0,'error':1,'refused':1}},code=2)
        command=process.call_args.args[0]
        self.assertEqual(command[0],sys.executable);self.assertTrue(command[3].endswith('youtube_videos.py'));self.assertEqual(command[4],'download')
        for flag in ('--data-dir','--progress','--cancel'):self.assertIn(flag,command)
        self.assertEqual(command[command.index('--max-height')+1],'480')
        state=self.manager.read();self.assertEqual(state['phase'],'completed');self.assertIn('1 vidéo(s) ajoutée(s)',state['message']);self.assertIn('2 non téléchargée(s)',state['message'])
        self.assertEqual(self.manager.status()['youtube']['counts']['downloaded'],1)

    def test_paused_or_failed_tool_and_resume(self):
        self.run_job({'phase':'paused','counts':{}},code=3)
        state=self.manager.read();self.assertEqual(state['phase'],'paused');self.assertIn('Reprendre',state['message'])
        with patch.object(jobs.subprocess,'Popen',return_value=MagicMock(pid=os.getpid())):self.manager.start('youtube-download',{'resume':True})
        resumed=self.manager.read();self.assertNotEqual(resumed['id'],state['id'])
        self.assertEqual((self.manager.paths(resumed['id'])/'liste.txt').read_text(),LIST)
        resumed['phase']='completed';self.manager.write(resumed)
        with self.assertRaisesRegex(setup.SetupError,'reprendre'):self.manager.start('youtube-download',{'resume':True})
        import shutil;shutil.rmtree(self.manager.paths('a'*32))
        self.run_job({'phase':'running'},code=1)
        self.assertEqual(self.manager.read()['phase'],'error')


class PauseAndProgressTests(unittest.TestCase):
    setUp=downloads.DownloadTests.setUp
    scenario=downloads.DownloadTests.scenario

    def args(self,listing,**extra):
        values=dict(action='download',list=str(listing),work_dir=None,data_dir=str(self.data),lab=False,max_height=480,max_size_gb=0.001,reserve_gb=0,
                    ffmpeg=None,yt_dlp=str(self.fake),progress=str(self.root/'progress.json'),cancel=str(self.root/'cancel'))
        values.update(extra);return tool.argparse.Namespace(**values)

    def test_progress_file_follows_the_list(self):
        listing=self.root/'liste.txt';listing.write_text(LIST)
        self.assertEqual(tool.run_list(self.args(listing),log=self.output.append),2)
        value=json.loads((self.root/'progress.json').read_text())
        self.assertEqual(value['phase'],'completed');self.assertEqual(value['videos'],2);self.assertEqual(value['counts']['downloaded'],2)
        self.assertEqual(value['counts']['refused'],1);self.assertTrue(any('liste de lecture' in item.get('message','') for item in value['items']))

    def test_pause_stops_the_running_download_and_keeps_partial_files(self):
        self.scenario(**{A:{'kind':'slow'}})
        listing=self.root/'liste.txt';listing.write_text('https://youtu.be/'+A+'\nhttps://youtu.be/'+B+'\n')
        def later():
            for _ in range(100):
                if list((self.data/'state/video-downloads/en-cours'/A).glob('*.part')) if (self.data/'state/video-downloads/en-cours'/A).exists() else False:break
                time.sleep(.1)
            (self.root/'cancel').touch()
        threading.Thread(target=later,daemon=True).start()
        started=time.monotonic()
        self.assertEqual(tool.run_list(self.args(listing),log=self.output.append),3)
        self.assertLess(time.monotonic()-started,25)
        value=json.loads((self.root/'progress.json').read_text())
        self.assertEqual(value['phase'],'paused');self.assertEqual(value['counts']['downloaded'],0)
        self.assertTrue(list((self.data/'state/video-downloads/en-cours'/A).glob('*.part')))
        self.assertFalse(any(B in json.dumps(call) for call in downloads.DownloadTests.calls_made(self)))


if __name__=='__main__':unittest.main()
