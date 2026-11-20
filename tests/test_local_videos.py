"""Local sidecars, FTS and HTTP on tiny fixtures, never inference or downloads."""
import asyncio
import hashlib
import json
from pathlib import Path
import tempfile
import threading
import unittest
from unittest.mock import AsyncMock,patch

import httpx
from fastapi import HTTPException
from pilot import app as gateway,catalogue,document_text,documentary,engine,favorites,library,research,store,videos


class LocalVideoTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        temporary=tempfile.TemporaryDirectory();self.addCleanup(temporary.cleanup);self.root=Path(temporary.name)
        for module,key,value in [(store,'ROOT',self.root/'state'),(videos,'ROOT',self.root/'video'),(videos,'ACTIVE',None),(library,'GUIDES',self.root/'guides')]:
            p=patch.object(module,key,value);p.start();self.addCleanup(p.stop)
        videos.ROOT.mkdir();library.GUIDES.mkdir();store.init();videos.STOP.clear()
        (videos.ROOT/'cours.mp4').write_bytes(b'0123456789abcdef')
        (videos.ROOT/'cours.info.json').write_text(json.dumps({'title':'Guide de fabrication du générateur à pédales','language':'en','duration':20,'channel':'Canadian Prepper','id':'fixture','extractor':'Youtube','description':'Fabrication et assemblage du générateur, cours fictif de test.'}))
        (videos.ROOT/'cours.fr.srt').write_text('1\n00:00:01,000 --> 00:00:04,000\nFabrication du générateur à pédales : fixation du rotor fictif à 17 mm.\n\n2\n00:00:08,000 --> 00:00:10,000\nRaccordement de la dynamo fictive.\n')
        (videos.ROOT/'cours.en.vtt').write_text('WEBVTT\n\n00:01.000 --> 00:04.000\nGenerator building: imaginary pedal axle 31 mm.\n')
        videos.scan();self.id=videos.listing()['videos'][0]['id']

    def plan(self,text):return library.retrieval.plan(text,library.search_terms(text),library.SYNONYMS)

    async def test_title_caption_and_french_english_segment_keep_real_timestamp_and_track(self):
        found,coverage=videos.search(self.plan('rotor'))
        self.assertEqual(coverage['status'],'complete');self.assertEqual(len(found),1)
        self.assertIn('#t=1000&track=',found[0]['id']);self.assertEqual(found[0]['kind'],'video')
        value=await library.source(found[0]['id']);self.assertIn('17 mm',value['text']);self.assertEqual(value['language'],'fr')
        english,_=videos.search(self.plan('axle'),'en');self.assertEqual(len(english),1)
        self.assertIn('31 mm',(await library.source(english[0]['id']))['text'])
        self.assertEqual((await library.source(english[0]['id']))['language'],'en')
        later=videos.source(self.id+'#t=8000');self.assertIn('dynamo',later['text']);self.assertNotIn('rotor',later['text'])
        self.assertEqual(catalogue.canonical(found[0]['id']),self.id)

    async def test_opening_uses_the_selected_track_without_the_text_search_index(self):
        with videos.connect() as db:
            db.execute('DELETE FROM video_text')
        source=await library.source(self.id+'#t=4000')
        self.assertIn('dynamo',source['text'])
        self.assertNotIn('rotor',source['text'])
        self.assertEqual(source['language'],'fr')
        self.assertIn('31 mm',(await library.source(self.id+'#t=1000&track=0'))['text'])

    async def test_common_search_returns_documents_and_caption_then_assistant_reads_only_text(self):
        (library.GUIDES/'guide.fr.txt').write_text('Fabrication du générateur à pédales : construire un support. Texte fictif.')
        library.index_guides()
        with patch.object(library,'books',AsyncMock(return_value=[])):
            found=await library.search('fabriquer un générateur à pédales',domain='all')
        self.assertIn('video',{item['kind'] for item in found});self.assertIn('guide',{item['kind'] for item in found})
        video=next(item for item in found if item['kind']=='video');reference={}
        self.assertTrue(video['other_matches']);self.assertTrue(all(item['kind']=='video' and 'position_ms' in item for item in video['other_matches']))
        packet=await research.read([video['id']],'générateur à pédales',18000,{},lambda item,*args,**kw:engine.reference(reference,item,*args,**kw))
        self.assertEqual(packet['failed'],0);self.assertIn('no_pixels',packet['results'][0]['reading_scope'])
        evidence=documentary.Evidence();evidence.record('read_source',{'id':video['id']},{**await library.source(video['id'])})
        self.assertEqual(evidence.summary()['sources_read'],1);self.assertEqual(len(evidence.consulted),1)

    async def test_changed_or_removed_media_metadata_track_invalidate_index_without_replacing_original(self):
        original=(videos.ROOT/'cours.mp4').read_bytes()
        (videos.ROOT/'cours.fr.srt').write_text('changed')
        with self.assertRaises(HTTPException) as caught:videos.source(self.id)
        self.assertEqual(caught.exception.status_code,409)
        found,coverage=videos.search(self.plan('rotor'));self.assertEqual(found,[]);self.assertGreater(coverage['stale_results'],0)
        videos.scan();self.assertEqual((videos.ROOT/'cours.mp4').read_bytes(),original)
        value=videos.source(self.id);self.assertEqual(value['subtitle_status'],'source_only')
        (videos.ROOT/'cours.mp4').unlink()
        with self.assertRaises(HTTPException):videos.source(self.id)

    async def test_missing_subtitles_remain_title_only_without_fabricated_readable_text(self):
        for p in videos.ROOT.glob('*.srt'):p.unlink()
        for p in videos.ROOT.glob('*.vtt'):p.unlink()
        videos.scan();value=videos.source(self.id)
        self.assertEqual(value['text'],'');self.assertFalse(value['transcription_available'])
        self.assertEqual(value['subtitle_status'],'missing')
        found,_=videos.search(self.plan('générateur'));self.assertEqual(found[0]['transcription_origin'],'metadata_only')
        with self.assertRaises(HTTPException) as caught:await document_text.extract(self.id)
        self.assertIn('horodatages',caught.exception.detail)

    async def test_webvtt_converts_srt_without_executable_markup_and_no_remote_url(self):
        key,_=videos.identity(self.id);vtt=videos.webvtt(key,1)
        self.assertTrue(vtt.startswith('WEBVTT'));self.assertIn('00:00:01.000 --> 00:00:04.000',vtt)
        self.assertIn('17 mm',vtt);self.assertNotIn('http',vtt)
        (videos.ROOT/'cours.fr.srt').write_text('1\n00:00:01,000 --> 00:00:02,000\n&lt;script&gt;test&lt;/script&gt; &amp; 17 mm\n')
        videos.scan();vtt=videos.webvtt(key,1)
        self.assertIn('&lt;script&gt;',vtt);self.assertNotIn('<script>',vtt)

    async def test_partial_downloads_and_links_are_excluded_not_offered_as_ready(self):
        (videos.ROOT/'unfinished.mp4').write_bytes(b'fake');(videos.ROOT/'unfinished.mp4.part').write_bytes(b'fake')
        outside=self.root/'outside.mp4';outside.write_bytes(b'fake')
        try:(videos.ROOT/'linked.mp4').symlink_to(outside)
        except OSError:pass
        report=videos.scan();self.assertEqual(report['videos'],1)
        self.assertTrue(report['skipped']);self.assertEqual(videos.listing()['total'],1)
        with self.assertRaises(HTTPException):videos.safe_file('../outside.mp4')
        with self.assertRaises(HTTPException):videos.identity('video:../../outside')

    async def test_pause_preserves_previous_index_and_resume_is_explicit(self):
        videos.STOP.set();report=videos.scan();self.assertEqual(report['phase'],'paused')
        self.assertEqual(videos.listing()['total'],1)
        videos.STOP.clear();await videos.start();self.assertEqual(videos.status()['phase'],'running');await videos.ACTIVE
        self.assertEqual(videos.status()['phase'],'completed')
        self.assertEqual(videos.listing(query='générateur pédales')['total'],1)
        self.assertEqual(videos.listing(query='absent')['total'],0)

    async def test_previous_index_remains_readable_during_replacement_transaction(self):
        reached=threading.Event();release=threading.Event();original=videos.inventory.inspect_subtitle
        def inspected(*args,**kwargs):
            if kwargs.get('include_cues') and not reached.is_set():
                reached.set()
                if not release.wait(5):raise RuntimeError('Test release not received.')
            return original(*args,**kwargs)
        with patch.object(videos.inventory,'inspect_subtitle',side_effect=inspected):
            await videos.start()
            self.assertTrue(await asyncio.to_thread(reached.wait,3))
            try:
                source=await asyncio.wait_for(asyncio.to_thread(videos.source,self.id),2)
                self.assertIn('17 mm',source['text'])
            finally:
                release.set();await videos.ACTIVE
        self.assertEqual(videos.status()['phase'],'completed')

    async def test_favorites_and_human_classification_keep_the_video_identifier(self):
        await favorites.add('family',self.id)
        self.assertEqual(favorites.listing('family')[0]['kind'],'video')
        current=catalogue.revision(self.id,library.GUIDES,self.root/'zim')
        info=catalogue.save(self.id,{'domains':['resilience'],'document_type':'procedure','status':'reviewed'},current,library.GUIDES,self.root/'zim')
        source=await library.source(self.id)
        self.assertEqual(source['classification']['method'],'human')
        with patch.object(library,'books',AsyncMock(return_value=[])):
            found=await library.search('rotor',favorite_user='family')
        self.assertTrue(found);self.assertEqual(found[0]['kind'],'video')

    async def test_media_ranges_and_subtitles_are_served_without_inference_and_admin_scans_are_guarded(self):
        role={'id':'family','role':'reader'}
        async def user():return role
        gateway.app.dependency_overrides[gateway.user]=user;self.addCleanup(gateway.app.dependency_overrides.clear)
        key,_=videos.identity(self.id)
        with patch.object(engine,'launch',side_effect=AssertionError('No inference')):
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=gateway.app),base_url='http://test') as client:
                self.assertEqual((await client.post('/api/admin/videos/index')).status_code,403)
                listing=await client.get('/api/videos');self.assertEqual(listing.json()['total'],1)
                partial=await client.get('/api/videos/media?id='+key,headers={'Range':'bytes=2-5'})
                self.assertEqual(partial.status_code,206);self.assertEqual(partial.content,b'2345')
                self.assertEqual(partial.headers['content-range'],'bytes 2-5/16')
                track=await client.get('/api/videos/track?id='+key+'&track=1');self.assertEqual(track.status_code,200)
                self.assertIn('17 mm',track.text)
                self.assertEqual((await client.get('/api/videos/media?id=../../outside')).status_code,422)
                role['role']='admin';record=(await client.get('/api/admin/videos/report')).json()['per_video'][0]
                self.assertEqual(record['validation']['human_review'],'not_performed')
                self.assertEqual(record['media']['revision_stat']['size_bytes'],16)
                self.assertEqual(record['source']['extractor'],'Youtube');self.assertEqual(record['path'],'cours.mp4')
