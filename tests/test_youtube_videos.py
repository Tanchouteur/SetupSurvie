"""YouTube list downloads with a simulated yt-dlp: no network, no real media."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import youtube_videos as tool  # noqa: E402
from pilot import store,videos  # noqa: E402

FAKE=ROOT/'tests/fixtures/fake_yt_dlp.py'
A,B,C,D='aaaaaaaaaaa','bbbbbbbbbbb','ccccccccccc','ddddddddddd'


class ListTests(unittest.TestCase):
    def test_themes_comments_duplicates_and_refused_lines(self):
        entries,errors=tool.parse_list('﻿# Ma liste\n\n[Eau potable]\nhttps://www.youtube.com/watch?v='+A+'&t=30s  commentaire\nhttps://youtu.be/'+B+'\n'
                                       '[]\nhttps://www.youtube.com/shorts/'+C+'\nhttps://www.youtube.com/watch?v='+A+'\n'
                                       'https://www.youtube.com/playlist?list=PL123\nhttps://www.youtube.com/@chaine\nhttp://www.youtube.com/watch?v='+D+'\nbonjour\n'
                                       '[CON]\nhttps://m.youtube.com/watch?v='+D+'\n[  a/b:c?  ]\nhttps://www.youtube.com/live/'+'e'*11+'\n')
        self.assertEqual([(e['line'],e['id'],e['theme']) for e in entries],[(4,A,'Eau potable'),(5,B,'Eau potable'),(7,C,''),(14,D,'_CON'),(16,'e'*11,'a b c')])
        self.assertEqual(entries[0]['url'],'https://www.youtube.com/watch?v='+A)
        self.assertEqual([(e['line'],e['reason']) for e in errors],[(8,'duplicate_in_list'),(9,'playlist_refused'),(10,'playlist_refused'),(11,'invalid_url'),(12,'invalid_url')])
        self.assertEqual(errors[0]['first_line'],4)

    def test_folder_names_are_valid_everywhere(self):
        self.assertEqual(tool.folder_name('  Feu : allumage / sans "allumettes"?. '),'Feu allumage sans allumettes')
        self.assertEqual(tool.folder_name('nul'),'_nul');self.assertEqual(tool.folder_name('',"Sans chaîne"),'Sans chaîne')
        self.assertLessEqual(len(tool.folder_name('x'*300)),80)

    def test_error_messages_are_classified_without_guessing(self):
        cases={'ERROR: Private video':'private','ERROR: Sign in to confirm your age':'age_restricted','ERROR: Sign in to confirm you’re not a bot':'bot_check',
               'ERROR: The uploader has not made this video available in your country':'region_blocked','ERROR: HTTP Error 429: Too Many Requests':'rate_limited',
               'ERROR: Video unavailable':'unavailable','ERROR: Requested format is not available':'no_format','ERROR: [Errno 28] No space left on device':'disk_space',
               'ERROR: Unable to download webpage: timed out':'network','ERROR: something new':'tool_failed'}
        for text,reason in cases.items():self.assertEqual(tool.classify(text,1),reason,text)
        self.assertEqual(tool.classify('',0),'output_missing')

    def test_command_uses_no_account_cookie_or_playlist_and_adapts_to_ffmpeg(self):
        entry={'url':'https://www.youtube.com/watch?v='+A}
        plain=tool.command(['yt-dlp'],entry,Path('/tmp/x'),max_height=480,max_bytes=10,ffmpeg=None)
        for flag in ('--ignore-config','--no-playlist','--write-info-json','--write-subs','--write-auto-subs','--continue','--windows-filenames'):self.assertIn(flag,plain)
        self.assertFalse([value for value in plain if 'cookie' in value or 'proxy' in value or 'username' in value])
        self.assertEqual(plain[plain.index('-f')+1],'b[height<=480][ext=mp4]/b[height<=480]');self.assertNotIn('--merge-output-format',plain)
        self.assertEqual(plain[-2:],['--',entry['url']])
        merged=tool.command(['yt-dlp'],entry,Path('/tmp/x'),max_height=720,max_bytes=10,ffmpeg=Path('/opt/ffmpeg'))
        self.assertIn('bv*[height<=720]',merged[merged.index('-f')+1]);self.assertEqual(merged[merged.index('--ffmpeg-location')+1],'/opt/ffmpeg')
        self.assertNotIn('--js-runtimes',merged)
        node=tool.command(['yt-dlp'],entry,Path('/tmp/x'),max_height=480,max_bytes=10,ffmpeg=None,js_runtime='node')
        self.assertEqual(node[node.index('--js-runtimes')+1],'node')


class DownloadTests(unittest.TestCase):
    def setUp(self):
        temporary=tempfile.TemporaryDirectory();self.addCleanup(temporary.cleanup);self.root=Path(temporary.name)
        self.data=self.root/'data';self.library=self.data/'library'/'video';self.library.mkdir(parents=True)
        self.plan=self.root/'plan.json';self.calls=self.root/'calls.jsonl';self.plan.write_text('{}')
        self.fake=FAKE
        env=patch.dict(os.environ,{'FAKE_YTDLP':str(self.plan),'FAKE_YTDLP_CALLS':str(self.calls)});env.start();self.addCleanup(env.stop)
        self.output=[]

    def scenario(self,**values):self.plan.write_text(json.dumps(values))

    def calls_made(self):return [json.loads(line) for line in self.calls.read_text().splitlines()] if self.calls.exists() else []

    def run_list(self,text,*extra):
        listing=self.root/'liste.txt';listing.write_text(text,encoding='utf-8')
        args=tool.argparse.Namespace(action='download',list=str(listing),work_dir=None,data_dir=str(self.data),lab=False,max_height=480,
                                     max_size_gb=0.001,reserve_gb=0,ffmpeg=None,yt_dlp=str(self.fake))
        for key,value in extra:setattr(args,key,value)
        code=tool.run_list(args,log=self.output.append)
        report=json.loads(sorted((self.data/'state/video-downloads/rapports').glob('*.json'))[-1].read_text())
        return code,report

    def test_list_is_downloaded_renamed_sorted_and_found_by_the_pilot(self):
        self.scenario(**{A:{'kind':'ok','title':'Allumer un feu','channel':'Chaîne: Survie'},B:{'kind':'nosubs','title':'Filtrer l’eau'},C:{'kind':'private'}})
        code,report=self.run_list('[Feu]\nhttps://youtu.be/'+A+'\n[]\nhttps://youtu.be/'+B+'\nhttps://youtu.be/'+C+'\nhttps://www.youtube.com/playlist?list=PL1\n')
        self.assertEqual(code,2);self.assertEqual(report['counts'],{'downloaded':2,'skipped':0,'refused':1,'error':1})
        self.assertEqual(report['yt_dlp'],'2099.01.01-fake');self.assertFalse(report['ffmpeg'])
        feu=self.library/'youtube'/'Feu'
        self.assertEqual(sorted(p.name for p in feu.iterdir()),['Allumer un feu ['+A+'].en.vtt','Allumer un feu ['+A+'].fr.vtt','Allumer un feu ['+A+'].info.json','Allumer un feu ['+A+'].mp4'])
        self.assertTrue((self.library/'youtube'/'Chaîne fictive'/('Filtrer l’eau ['+B+'].mp4')).is_file())
        first=next(item for item in report['items'] if item['id']==A)
        self.assertEqual(first['subtitles'],['Allumer un feu ['+A+'].en.vtt','Allumer un feu ['+A+'].fr.vtt']);self.assertEqual(first['path'],'youtube/Feu/Allumer un feu ['+A+'].mp4')
        self.assertEqual(next(item for item in report['items'] if item['id']==C)['reason'],'private')
        self.assertFalse((self.data/'state/video-downloads/en-cours'/A).exists())
        self.assertTrue(any('vidéo privée' in line for line in self.output))
        # The pilot finds the new videos with their title and French track.
        temporary=tempfile.TemporaryDirectory();self.addCleanup(temporary.cleanup)
        with patch.object(store,'ROOT',Path(temporary.name)),patch.object(videos,'ROOT',self.library),patch.object(videos,'ACTIVE',None):
            store.init();videos.STOP.clear();videos.scan();listed=videos.listing()['videos']
        found=next(item for item in listed if item['title']=='Allumer un feu')
        self.assertEqual(found['collection'],'Chaîne: Survie')
        self.assertIn('fr',[track['language'] for track in found['tracks'] if track['status']=='passed'])

    def test_rerun_resumes_partial_download_and_skips_present_videos(self):
        self.scenario(**{A:{'kind':'partial'}})
        (self.library/'Marc').mkdir();(self.library/'Marc'/('Ancienne vidéo ['+B+'].webm')).write_bytes(b'x')
        code,report=self.run_list('https://youtu.be/'+A+'\nhttps://youtu.be/'+B+'\n')
        self.assertEqual(code,2);self.assertEqual(report['items'][0]['reason'],'network')
        self.assertEqual(report['items'][1],{'line':2,'id':B,'url':'https://www.youtube.com/watch?v='+B,'theme':'','status':'skipped','reason':'already_present','path':'Marc/Ancienne vidéo ['+B+'].webm'})
        self.assertTrue(list((self.data/'state/video-downloads/en-cours'/A).glob('*.part')))
        self.assertFalse(list(self.library.rglob('*.part')))
        code,report=self.run_list('https://youtu.be/'+A+'\nhttps://youtu.be/'+B+'\n')
        self.assertEqual(code,0);self.assertEqual(report['counts']['downloaded'],1)
        calls=len(self.calls_made())
        code,report=self.run_list('https://youtu.be/'+A+'\n')
        self.assertEqual(report['items'][0]['reason'],'already_present');self.assertEqual(len(self.calls_made()),calls)

    def test_name_collision_keeps_both_files_and_matching_sidecars(self):
        self.scenario(**{A:{'kind':'ok','title':'Même titre','channel':'C'}})
        folder=self.library/'youtube'/'C';folder.mkdir(parents=True)
        (folder/('Même titre ['+A+'].fr.vtt')).write_text('ancienne piste orpheline')
        code,report=self.run_list('https://youtu.be/'+A+'\n')
        self.assertEqual(code,0)
        self.assertEqual((folder/('Même titre ['+A+'].fr.vtt')).read_text(),'ancienne piste orpheline')
        self.assertEqual(sorted(p.name for p in folder.glob('*(2)*')),['Même titre ['+A+'] (2).en.vtt','Même titre ['+A+'] (2).fr.vtt','Même titre ['+A+'] (2).info.json','Même titre ['+A+'] (2).mp4'])

    def test_missing_output_and_low_disk_are_errors_without_partial_publication(self):
        self.scenario(**{A:{'kind':'empty'}})
        code,report=self.run_list('https://youtu.be/'+A+'\nhttps://youtu.be/'+B+'\n')
        self.assertEqual(report['items'][0]['reason'],'output_missing');self.assertEqual(report['counts']['downloaded'],1)
        with patch.object(tool,'free_bytes',return_value=0):
            code,report=self.run_list('https://youtu.be/'+C+'\nhttps://youtu.be/'+D+'\n')
        self.assertEqual([item.get('reason') for item in report['items']],['disk_space']);self.assertTrue(any('espace disque' in line for line in self.output))
        self.assertFalse(any(C in line for line in map(json.dumps,self.calls_made())))

    def test_installation_is_found_like_the_windows_update_launcher(self):
        application=self.root/'SetupSurvie';application.mkdir()
        with self.assertRaises(tool.setup.SetupError):tool.find_work_dir(application)
        (self.root/'prive').mkdir();(self.root/'prive'/'settings.json').write_text('{}')
        self.assertEqual(tool.find_work_dir(application),self.root/'prive')
        (application/'.local').mkdir();(application/'.local'/'settings.json').write_text('{}')
        with self.assertRaises(tool.setup.SetupError):tool.find_work_dir(application)

    def test_check_reads_the_list_without_network_or_data(self):
        listing=self.root/'liste.txt';listing.write_text('[Eau]\nhttps://youtu.be/'+A+'\nnope\n')
        code=tool.run_list(tool.argparse.Namespace(action='check',list=str(listing)),log=self.output.append)
        self.assertEqual(code,2);self.assertIn('ligne 2 : '+A+' → [Eau]',self.output);self.assertFalse(self.calls.exists())

    def test_download_prepares_the_tools_by_itself_or_explains_why_not(self):
        with patch.object(tool.youtube_tools,'ensure',return_value=True) as ensure,patch.object(tool.youtube_tools,'installed_version',return_value='2026.10.26'):
            command=tool.downloader(self.data,log=self.output.append)
        ensure.assert_called_once();self.assertEqual(command[1:],['-m','yt_dlp'])
        self.assertEqual(command[0],str(tool.youtube_tools.python(self.data)))
        with patch.object(tool.youtube_tools,'ensure',return_value=False),patch.object(tool.youtube_tools,'installed_version',return_value=None):
            with self.assertRaises(tool.setup.SetupError) as caught:tool.downloader(self.data)
        self.assertIn('Internet',str(caught.exception))
        ffmpeg=self.data/'tools'/'ffmpeg'/tool.youtube_tools.manifest()['ffmpeg']['version']/('ffmpeg.exe' if os.name=='nt' else 'ffmpeg')
        ffmpeg.parent.mkdir(parents=True);ffmpeg.write_text('')
        self.assertEqual(tool.find_ffmpeg(None,self.data),ffmpeg)
        deno=tool.youtube_tools.paths(self.data)['venv']/('Scripts/deno.exe' if os.name=='nt' else 'bin/deno');deno.parent.mkdir(parents=True);deno.write_text('')
        self.assertEqual(tool.find_js_runtime(self.data),'deno')

if __name__=='__main__':unittest.main()
