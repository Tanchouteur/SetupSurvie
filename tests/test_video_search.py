"""Videos-only search, automatic inventory and assistant links on tiny fixtures.

No download, decoder, model or real inference: the engine talks to a mocked
HTTP model and the video folder holds a few bytes.
"""
import asyncio
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import AsyncMock,patch

from fastapi.testclient import TestClient
from pilot import app as gateway,collection_sort,engine,library,network,store,video_requests,videos
import test_engine_evidence as harness


def add_video(root,name,title,description='',subtitle=None):
    (root/(name+'.mp4')).write_bytes(b'0123456789abcdef')
    (root/(name+'.info.json')).write_text(json.dumps({'title':title,'language':'fr','duration':30,'channel':'Chaîne fictive','id':name,'extractor':'Youtube','description':description}))
    if subtitle:(root/(name+'.fr.srt')).write_text('1\n00:00:02,000 --> 00:00:05,000\n'+subtitle+'\n')


class VideoSearchTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        temporary=tempfile.TemporaryDirectory();self.addCleanup(temporary.cleanup);self.root=Path(temporary.name)
        for module,key,value in [(store,'ROOT',self.root/'state'),(videos,'ROOT',self.root/'video'),(videos,'ACTIVE',None),(videos,'CHECKED',0.0),(library,'GUIDES',self.root/'guides')]:
            p=patch.object(module,key,value);p.start();self.addCleanup(p.stop)
        videos.ROOT.mkdir();library.GUIDES.mkdir();store.init();videos.STOP.clear()
        add_video(videos.ROOT,'feu','Allumer un feu sans allumettes','Méthode fictive de démonstration.','Frotter le bâton fictif contre la planche.')
        add_video(videos.ROOT,'eau','Bouillir de l’eau','Vidéo fictive.')
        (library.GUIDES/'feu.fr.txt').write_text('Allumer un feu : guide fictif avec du petit bois.')
        library.index_guides()

    def plan(self,text):return library.retrieval.plan(text,library.search_terms(text),library.SYNONYMS)

    async def search(self,query,**options):
        with patch.object(library,'books',AsyncMock(return_value=[])):return await library.search(query,**options)

    async def wait_inventory(self):
        if videos.ACTIVE is not None:await videos.ACTIVE

    async def test_never_indexed_folder_is_inventoried_automatically_then_listed_without_query(self):
        self.assertTrue(videos.stale())
        found=await self.search('',kind='videos')
        self.assertEqual(list(found),[]);self.assertEqual(found.coverage['videos']['status'],'not_indexed')
        self.assertIn('automatiquement',found.coverage['warning'])
        await self.wait_inventory();self.assertFalse(videos.stale())
        videos.CHECKED=0.0
        found=await self.search('',kind='videos',domain='culture')
        self.assertEqual([item['title'] for item in found],['Allumer un feu sans allumettes','Bouillir de l’eau'])
        self.assertTrue(all(item['kind']=='video' for item in found));self.assertEqual(found.coverage['domain'],'culture')

    async def test_video_group_reclassification_applies_to_title_and_subtitle_partitions(self):
        sidecar=videos.ROOT/'eau.info.json'
        sidecar.write_text(json.dumps({**json.loads(sidecar.read_text()),'channel':'Autre chaîne'}))
        videos.scan()
        key=collection_sort.video({'source':{'channel':'Chaîne fictive'}})
        with patch.object(network,'CATALOG',self.root/'catalog'):
            collection_sort.save(network.CATALOG,collection_sort.Sort(frozenset({key})))
            self.assertFalse(await self.search('allumettes',kind='videos',domain='resilience'))
            result=await self.search('planche',kind='videos',domain='other')
            self.assertEqual(result[0]['match'],'subtitle')
            self.assertEqual(result.coverage['videos']['indexes_queried'],1)
            self.assertTrue(await self.search('allumettes',kind='videos',domain='all'))
            collection_sort.save(network.CATALOG,collection_sort.Sort())
            self.assertTrue(await self.search('allumettes',kind='videos',domain='resilience'))

    async def test_long_video_question_keeps_partial_matches(self):
        videos.scan()
        found=await self.search('longueur inconnue du bâton fictif pour le feu demandé ici',kind='videos')
        self.assertEqual(found[0]['title'],'Allumer un feu sans allumettes');self.assertEqual(found[0]['kind'],'video')
        self.assertFalse([key for key in found[0] if key.startswith('_')])

    async def test_collection_group_counts_include_all_pages_and_can_be_filtered(self):
        for name, title, channel in [('feu','Première vidéo','Série de tests'),('eau','Deuxième vidéo','Série de tests'),
                                     ('extra','Vidéo isolée','')]:
            add_video(videos.ROOT,name,title)
            sidecar=videos.ROOT/(name+'.info.json')
            sidecar.write_text(json.dumps({**json.loads(sidecar.read_text()),'channel':channel}))
        videos.scan()
        listing=videos.listing(limit=1,grouped=True)
        self.assertEqual((listing['total'],listing['group_total']),(3,2))
        group=listing['groups'][0]
        self.assertEqual((group['name'],group['count']),('Série de tests',2))
        self.assertEqual(videos.listing(offset=1,limit=1,grouped=True)['groups'][0]['video']['title'],'Vidéo isolée')
        self.assertEqual(videos.listing(query='serie',grouped=True)['groups'][0]['count'],2)
        first=videos.listing(limit=1,group=group['id'])
        second=videos.listing(offset=1,limit=1,group=group['id'])
        self.assertEqual(first['total'],2)
        self.assertEqual([item['title'] for item in first['videos']+second['videos']],['Deuxième vidéo','Première vidéo'])
        self.assertEqual(videos.listing(query='premiere',grouped=True)['groups'][0]['video']['title'],'Première vidéo')

    async def test_kind_separates_videos_and_documents(self):
        videos.scan()
        only=await self.search('allumer feu',kind='videos',domain='all')
        self.assertTrue(only);self.assertEqual({item['kind'] for item in only},{'video'})
        documents=await self.search('allumer feu',kind='documents',domain='all')
        self.assertTrue(documents);self.assertNotIn('video',{item['kind'] for item in documents})
        mixed=await self.search('allumer feu',domain='all')
        self.assertEqual({item['kind'] for item in mixed},{'video','guide'})
        with self.assertRaises(ValueError):await self.search('feu',kind='images')

    async def test_new_file_triggers_refresh_but_partial_download_and_user_stop_do_not(self):
        videos.scan();self.assertFalse(videos.stale())
        (videos.ROOT/'nouvelle.mp4.part').write_bytes(b'1234')
        self.assertFalse(videos.stale())
        add_video(videos.ROOT,'abri','Monter un abri','Vidéo fictive.')
        self.assertTrue(videos.stale())
        self.assertEqual(await videos.ensure_fresh(),'refreshing');await self.wait_inventory()
        self.assertEqual(await videos.ensure_fresh(),'checked')
        self.assertEqual(await videos.ensure_fresh(force=True),'fresh')
        self.assertIn('Monter un abri',[item['title'] for item in videos.listing()['videos']])
        report=videos.status();report.update(phase='paused',stopped_by='user')
        (store.ROOT/'videos-report.json').write_text(json.dumps(report))
        self.assertFalse(videos.stale())
        report.update(stopped_by='service_restarted');(store.ROOT/'videos-report.json').write_text(json.dumps(report))
        self.assertTrue(videos.stale())

    async def test_previous_index_stays_searchable_during_refresh(self):
        videos.scan()
        report=videos.status();report['phase']='running';(store.ROOT/'videos-report.json').write_text(json.dumps(report))
        with patch.object(videos,'ACTIVE',asyncio.get_running_loop().create_future()):
            found,coverage=videos.search(self.plan('bouillir'))
        self.assertEqual(coverage['status'],'refreshing');self.assertEqual(len(found),1)
        self.assertEqual(coverage['indexed_videos'],2)

    async def test_shutdown_ignores_inventory_of_another_or_cancelled_loop(self):
        other=asyncio.new_event_loop();foreign=other.create_future()
        try:
            with patch.object(videos,'ACTIVE',foreign):
                await videos.stop(reason='service_restarted')
                videos.STOP.clear()
                self.assertEqual(await videos.ensure_fresh(force=True),'refreshing');started=videos.ACTIVE
            await started
        finally:other.close()
        cancelled=asyncio.get_running_loop().create_task(asyncio.sleep(10))
        with patch.object(videos,'ACTIVE',cancelled):
            cancelled.cancel();await asyncio.sleep(0)
            await videos.stop(reason='service_restarted')
        videos.STOP.clear()

    def test_http_search_accepts_empty_query_only_for_videos(self):
        videos.scan()
        with patch.object(videos,'ensure_fresh',AsyncMock(return_value='fresh')),patch.object(library,'books',AsyncMock(return_value=[])):
            client=TestClient(gateway.app)
            data=client.get('/api/search',params={'q':'','kind':'videos'}).json()
            self.assertEqual(len(data['results']),2);self.assertEqual(data['coverage']['kind'],'videos')
            self.assertEqual(client.get('/api/search',params={'q':''}).json()['results'],[])
            self.assertEqual(client.get('/api/search',params={'q':'x','kind':'images'}).status_code,422)


class VideoRequestTests(unittest.TestCase):
    def test_intent_and_query_follow_the_reported_questions(self):
        self.assertTrue(video_requests.requested('Cherche une vidéo sur comment faire du feux'))
        self.assertTrue(video_requests.requested('ok bah trouve une vidéo de nimporte quoi dans la biblioteque'))
        self.assertFalse(video_requests.requested('Comment faire du feu ?'))
        self.assertEqual(video_requests.query('ok bah trouve une vidéo de n’importe quoi dans la biblioteque'),'')
        self.assertIn('feux',video_requests.query('Cherche une vidéo sur comment faire du feux'))
        self.assertNotIn('video',video_requests.query('Cherche une vidéo sur comment faire du feux'))

    def test_open_url_and_appendix_only_add_missing_links(self):
        url=video_requests.open_url('video:'+'a'*64+'#t=2000&track=1')
        self.assertEqual(url,'/#/bibliotheque/recherche?kind=videos&source=video:'+'a'*64+'%23t%3D2000%26track%3D1')
        row={'id':'video:'+'a'*64,'title':'Feu [test]','open_url':url,'has_subtitles':False,'subtitle_languages':[]}
        answer=video_requests.appendix('Voici une vidéo.',[row])
        self.assertIn('[Feu  test]('+url+')',answer);self.assertIn('sans sous-titres',answer)
        linked='Voir [Feu]('+url+').'
        self.assertEqual(video_requests.appendix(linked,[row]),linked)


    def test_misformatted_player_addresses_become_real_links(self):
        url=video_requests.open_url('video:'+'a'*64+'#t=2000&track=0')
        for text in ('Voir [https:/'+url+'].','Voir ['+url+'].'):
            self.assertIn('[Ouvrir la vidéo]('+url+')',video_requests.repair(text))
        self.assertEqual(video_requests.repair('[Titre](https:/'+url+')'),'[Titre]('+url+')')
        row={'id':'video:'+'a'*64,'title':'Feu','open_url':video_requests.open_url('video:'+'a'*64),'has_subtitles':True,'subtitle_languages':['fr']}
        self.assertNotIn('Vidéos trouvées',video_requests.appendix(video_requests.repair('Voir ['+url+']'),[row]))
        self.assertIn('Vidéos trouvées',video_requests.appendix('Voir https:/'+url,[row]))


class VideoAssistantTests(unittest.TestCase):
    setUp=harness.EvidenceTests.setUp
    run_chat=harness.EvidenceTests.run_chat
    call=staticmethod(harness.EvidenceTests.call)

    def video(self):
        key='b'*64
        return {'id':'video:'+key,'kind':'video','title':'Allumer un feu sans allumettes','collection':'Chaîne fictive','language':'fr',
                'duration_seconds':30,'match':'title','excerpt':'Méthode fictive.','tracks':[{'status':'passed','language':'fr'}]}

    def question(self,text):
        with store.connect() as db:db.execute("UPDATE messages SET content=? WHERE conversation_id='c' AND role='user'",(text,))

    def test_video_request_lists_real_links_even_when_the_model_forgets_them(self):
        self.question('ok bah trouve une vidéo de nimporte quoi dans la biblioteque')
        video=self.video()
        async def search(query,language='',**options):
            if options.get('kind')=='videos':return library.SearchResults([video],{'status':'complete','videos':{'status':'complete','indexed_videos':1}})
            return library.SearchResults([],{'status':'complete'})
        def reply(payload):
            names=[tool['function']['name'] for tool in payload['tools']]
            self.assertIn('find_videos',names)
            packets=[json.loads(m['content']) for m in payload['messages'] if m.get('tool_name')=='find_videos']
            self.assertEqual(packets[0]['results'][0]['open_url'],video_requests.open_url(video['id']))
            self.assertTrue(packets[0]['results'][0]['has_subtitles'])
            self.assertIn('open_url exact',' '.join(m['content'] for m in payload['messages'] if m['role']=='system'))
            return {'content':'Une vidéo est disponible.'}
        _,saved=self.run_chat([reply],search=search)
        self.assertEqual([call.kwargs.get('kind') for call in self.lookup_calls],['videos'])
        self.assertEqual(self.lookup_calls[0].args[0],'')
        self.assertIn('[Allumer un feu sans allumettes]('+video_requests.open_url(video['id'])+')',saved['content'])

    def test_empty_subject_search_shows_other_videos_and_index_state(self):
        self.question('Cherche une vidéo sur la soudure à l’arc')
        video=self.video()
        async def search(query,language='',**options):
            if options.get('kind')=='videos':
                rows=[video] if not query else []
                return library.SearchResults(rows,{'status':'complete','videos':{'status':'complete','indexed_videos':1}})
            return library.SearchResults([],{'status':'complete'})
        def reply(payload):
            packet=next(json.loads(m['content']) for m in payload['messages'] if m.get('tool_name')=='find_videos')
            self.assertEqual(packet['results'],[]);self.assertEqual(packet['coverage']['indexed_videos'],1)
            self.assertEqual(packet['other_videos'][0]['title'],video['title'])
            return {'content':'Aucune vidéo sur la soudure ; une autre vidéo existe : [Allumer un feu sans allumettes]('+video_requests.open_url(video['id'])+').'}
        _,saved=self.run_chat([reply],search=search)
        self.assertEqual(saved['content'].count('/bibliotheque/recherche'),1)

    def test_subject_request_reads_available_subtitles_before_the_model(self):
        self.question('D’après la vidéo sur le feu, quelle longueur d’archet est indiquée ?')
        video=self.video();passage={**self.a,'id':video['id'],'title':video['title'],'text':'Archet fictif de 60 cm.'}
        async def search(query,language='',**options):
            if options.get('kind')=='videos':return library.SearchResults([video],{'status':'complete','videos':{'status':'complete','indexed_videos':1}})
            return library.SearchResults([],{'status':'complete'})
        def reply(payload):
            packets=[json.loads(m['content']) for m in payload['messages'] if m.get('tool_name')=='read_sources']
            self.assertEqual(packets[-1]['results'][0]['id'],video['id'])
            return {'content':'L’archet mesure 60 cm [1]. [Voir la vidéo]('+video_requests.open_url(video['id'])+')'}
        _,saved=self.run_chat([reply],search=search,read=lambda identifier:passage)
        self.assertIn('60 cm',saved['content']);self.assertEqual(saved['sources'][0]['id'],video['id'])

    def test_rejected_citation_keeps_the_real_video_links(self):
        self.question('Trouve une vidéo sans piste sur un archet')
        video={**self.video(),'tracks':[]}
        async def search(query,language='',**options):
            if options.get('kind')=='videos':return library.SearchResults([video],{'status':'complete','videos':{'status':'complete','indexed_videos':1}})
            return library.SearchResults([],{'status':'complete'})
        _,saved=self.run_chat([{'content':'Voici la vidéo [1].'}],search=search,expected_status='incomplete')
        self.assertIn(video_requests.open_url(video['id']),saved['content'])

    def test_off_topic_fallback_is_not_appended_as_found(self):
        self.question('Cherche une vidéo sur la soudure à l’arc')
        video=self.video()
        async def search(query,language='',**options):
            rows=[video] if options.get('kind')=='videos' and not query else []
            return library.SearchResults(rows,{'status':'complete','videos':{'status':'complete','indexed_videos':1}})
        _,saved=self.run_chat([{'content':'Aucune vidéo sur la soudure.'}],search=search)
        self.assertNotIn('Vidéos trouvées',saved['content'])

    def test_model_can_call_find_videos_itself(self):
        self.question('Bonjour, et pour les abris ?')
        video=self.video()
        async def search(query,language='',**options):
            if options.get('kind')=='videos':return library.SearchResults([video],{'status':'complete','videos':{'status':'complete','indexed_videos':1}})
            return library.SearchResults([],{'status':'complete'})
        def first(payload):
            self.assertIn('find_videos',[tool['function']['name'] for tool in payload['tools']])
            return self.call('find_videos',{'query':'abri'})
        _,saved=self.run_chat([first,{'content':'Voici ce que j’ai trouvé.'}],search=search)
        self.assertIn(('abri',),[tuple(call.args[:1]) for call in self.lookup_calls if call.kwargs.get('kind')=='videos'])
        self.assertIn(video_requests.open_url(video['id']),saved['content'])


if __name__=='__main__':unittest.main()
