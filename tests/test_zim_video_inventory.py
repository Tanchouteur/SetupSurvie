"""Small generated archives only; no downloaded media or Internet."""
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import json
import subprocess
import sys
from pilot import zim_video_inventory as inventory
try:
    from libzim.writer import Creator,Item,StringProvider,Hint
    HAS_ZIM=True
except ImportError:HAS_ZIM=False


class ReferenceTests(unittest.TestCase):
    def test_display_title_hides_technical_names_and_preserves_question_marks(self):
        payload={'path':'opaque/videoplayback?id=123','title':'videoplayback?id=123',
                 'collection':'Cours','inventory_id':'deadbeef001'}
        self.assertEqual(inventory.display_title(payload,{}),'Cours — Vidéo sans titre (deadbeef)')
        payload.update(title='Comment reconnaître une étoile ?')
        self.assertEqual(inventory.display_title(payload,{}),payload['title'])
        payload.update(title='Carte_du_ciel.mp4',path='media/Carte_du_ciel.mp4')
        self.assertEqual(inventory.display_title(payload,{}),'Carte du ciel')
        self.assertFalse(inventory.standalone_media('some/segment.m4s?part=1','video/mp4'))
        self.assertFalse(inventory.standalone_media('library/index.d.ts','video/mp2t'))
        self.assertTrue(inventory.standalone_media('media/concert.ts','video/mp2t'))

    def test_relative_archive_paths_and_remote_urls_remain_distinct(self):
        self.assertEqual(inventory.resolve('A/course.html','../media/clip%20one.webm#t=2')['path'],'media/clip one.webm')
        self.assertEqual(inventory.resolve('A/course.html','/tracks/en.vtt')['path'],'tracks/en.vtt')
        for url in ('https://example.invalid/v.mp4','//example.invalid/v.mp4'):
            self.assertEqual(inventory.resolve('A/course.html',url)['status'],'remote_reference')
        for url in ('../../outside.webm','javascript:alert(1)','file:///tmp/private','foo\\bar','%00video.mp4'):
            self.assertIn(inventory.resolve('A/course.html',url)['status'],('invalid_reference','unsupported_reference'))
        self.assertEqual(inventory.resolve('A/course.html','v.mp4','https://example.invalid/base/')['status'],'remote_reference')
        self.assertEqual(inventory.resolve('A/course.html','v.mp4','../media/')['path'],'media/v.mp4')

    def test_multiple_videos_lazy_sources_and_their_tracks_do_not_mix(self):
        parser=inventory.Videos();parser.feed('<video title="One" data-src="one.webm"><track src="one.en.vtt" srclang="en"></video><video><source src="two.mp4"><track data-src="two.fr.vtt" srclang="fr"></video><iframe src="https://www.youtube.com/embed/abcDEF_12-3"></iframe>')
        self.assertEqual(len(parser.items),3);self.assertEqual(parser.items[0]['tracks'][0]['src'],'one.en.vtt');self.assertEqual(parser.items[1]['tracks'][0]['language_declared'],'fr');self.assertEqual(parser.items[2]['tracks'],[])

    def test_reference_limit_is_an_explicit_issue_instead_of_complete_coverage(self):
        parser=inventory.Videos();parser.feed('<video src="v.webm"></video>'*(inventory.MAX_VIDEOS_PER_PAGE+1))
        self.assertEqual(len(parser.items),inventory.MAX_VIDEOS_PER_PAGE);self.assertIn('video_reference_limit',parser.errors)


@unittest.skipUnless(HAS_ZIM,'Optional libzim reader required')
class ArchiveVideoTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup);self.root=Path(self.temp.name);self.zim=self.root/'fixture.zim';self.state=self.root/'state'
        self.create()

    def create(self,extra=False):
        from zim_video_fixture import create
        create(self.zim,extra=extra)

    def test_youtube_titles_enrich_existing_inventory_without_changing_video_identity(self):
        from zim_video_fixture import create
        create(self.zim,youtube=True)
        with patch.object(inventory,'save_youtube_titles',lambda *args:None):
            original=inventory.build(self.zim,self.state)
        path=self.state/original['file']
        with inventory.connect(path,True) as db:
            old_rows=db.execute('SELECT payload FROM video_items ORDER BY id').fetchall()
        updated=inventory.build(self.zim,self.state)
        self.assertEqual(updated['status'],'reused')
        self.assertEqual(updated['revision'],original['revision'])
        with inventory.connect(path,True) as db:
            rows=db.execute('SELECT payload FROM video_items ORDER BY id').fetchall()
            titles=json.loads(db.execute('SELECT value FROM metadata WHERE key=?',(inventory.YOUTUBE_TITLES,)).fetchone()[0])
        self.assertEqual(rows,old_rows)
        self.assertEqual(titles,{'videos/aaaaaaaaaaa/video.webm':'How do we measure a shadow?',
                                 'videos/bbbbbbbbbbb/video.webm':'A different lesson'})
        self.assertEqual(inventory.build(self.zim,self.state)['status'],'reused')

    def test_native_text_index_does_not_skip_media_and_local_presence_is_not_decoding(self):
        result=inventory.build(self.zim,self.state);self.assertEqual(result['status'],'completed');self.assertEqual(result['video_resources'],2)
        data=inventory.references(self.state/result['file']);first=data['items'][0]
        self.assertEqual(first['title'],'Fictional video course');self.assertEqual(first['sources'][0]['availability'],'present')
        self.assertEqual(first['tracks'][0]['availability'],'present');self.assertEqual(first['tracks'][0]['checks']['technical_status'],'passed');self.assertEqual(first['tracks'][1]['availability'],'missing_or_unsupported')
        self.assertEqual(result['usable_tracks'],1)
        with inventory.connect(self.state/result['file'],True) as db:
            self.assertIn('Fictional 17 mm.',db.execute('SELECT webvtt FROM subtitles WHERE usable=1').fetchone()[0])
            self.assertEqual(db.execute('SELECT start_ms,end_ms,text FROM subtitle_cues').fetchone()[:],(1000,2000,'Fictional 17 mm.'))
        self.assertEqual(data['items'][1]['sources'][0]['resolved']['status'],'remote_reference')
        self.assertEqual(inventory.build(self.zim,self.state)['status'],'reused')
        with self.assertRaises(ValueError):inventory.references(self.state/result['file'],limit=101)

    def test_cancelled_scan_keeps_cursor_and_reuses_it_without_publishing_partial(self):
        calls=0;native=inventory.shutil.disk_usage
        def cancel_after_a_checkpoint(path):
            nonlocal calls
            calls+=1
            if calls==4:raise inventory.Paused()
            return native(path)
        with patch.object(inventory.shutil,'disk_usage',side_effect=cancel_after_a_checkpoint),self.assertRaises(inventory.Paused):inventory.build(self.zim,self.state,checkpoint=1)
        self.assertFalse(list(self.state.glob('*.sqlite')));building=next(self.state.glob('*.building'))
        with inventory.connect(building,True) as db:self.assertEqual(db.execute("SELECT value FROM metadata WHERE key='cursor'").fetchone()[0],'2')
        result=inventory.build(self.zim,self.state,checkpoint=1);self.assertEqual(result['status'],'completed');self.assertFalse(list(self.state.glob('*.building')))

    def test_replaced_archive_keeps_last_completed_inventory_and_rescans_new_edition(self):
        original=inventory.build(self.zim,self.state);before=(self.state/original['file']).read_bytes();self.create(extra=True)
        cancel=self.root/'cancel';cancel.touch()
        with self.assertRaises(inventory.Paused):inventory.build(self.zim,self.state,cancel=cancel)
        self.assertEqual((self.state/original['file']).read_bytes(),before);cancel.unlink()
        changed=inventory.build(self.zim,self.state);self.assertEqual(changed['video_resources'],3);self.assertNotEqual(changed['revision'],original['revision'])

    def test_large_html_stays_in_coverage_issues(self):
        with patch.object(inventory,'MAX_HTML',20):result=inventory.build(self.zim,self.state)
        self.assertEqual(result['status'],'partial');self.assertEqual(result['skipped_html'],1);self.assertEqual(result['video_resources'],2)

    def test_cli_separate_process_scans_then_reuses_without_reading_video_bytes(self):
        before=self.zim.read_bytes();script=Path(__file__).resolve().parents[1]/'scripts/inventory_zim_videos.py'
        command=[sys.executable,str(script),'--zim-dir',str(self.root),'--state-dir',str(self.root/'cli-state'),'--workers','2','--reserve-bytes','1000000']
        for state in ('completed','reused'):
            completed=subprocess.run(command,capture_output=True,text=True,timeout=30);self.assertEqual(completed.returncode,0,completed.stderr)
            report=json.loads(completed.stdout);self.assertEqual(report['phase'],'completed');self.assertEqual(report['results'][0]['status'],state)
            self.assertEqual(report['network_requests'],0);self.assertFalse(report['media_extracted']);self.assertEqual(report['results'][0]['video_resources'],2)
        self.assertEqual(self.zim.read_bytes(),before)

    def test_cli_unexamined_archive_path_keeps_global_coverage_partial(self):
        (self.root/'directory.zim').mkdir();script=Path(__file__).resolve().parents[1]/'scripts/inventory_zim_videos.py'
        result=subprocess.run([sys.executable,str(script),'--zim-dir',str(self.root),'--state-dir',str(self.root/'cli-state'),
            '--workers','1','--reserve-bytes','1000000','--job-id','fixture-job'],capture_output=True,text=True,timeout=30)
        self.assertEqual(result.returncode,0,result.stderr);report=json.loads(result.stdout)
        self.assertEqual(report['job_id'],'fixture-job');self.assertEqual(report['phase'],'partial');self.assertEqual(report['archives'],2)
        self.assertEqual(report['unexamined'],[{'archive':'directory.zim','reason':'link_or_not_file'}])
        self.assertEqual(report['completed'],1);self.assertEqual(report['results'][0]['video_resources'],2)
