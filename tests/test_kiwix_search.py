"""Kiwix protocol fixtures reproduce multilingual HTTP 400, no corpus/model."""
import asyncio
import json
import tempfile
import unittest
from pathlib import Path
from html import escape
from unittest.mock import AsyncMock,patch
from urllib.parse import urlsplit,parse_qs,quote
from fastapi import HTTPException
import httpx
from pilot import collection_sort,library,network,store,videos


class KiwixSearchTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        patcher=patch.object(store,'ROOT',Path(self.temp.name));patcher.start();self.addCleanup(patcher.stop);store.init()
        self.catalog=[{'book':'wikipedia_fr','language':'fra','fulltext':True,'title':'Wikipédia'},
                      {'book':'manual_en','language':'eng','fulltext':True,'title':'Manual'},
                      {'book':'multi','language':'eng,fra','fulltext':True,'title':'Multilingue'},
                      {'book':'video','language':'fra','fulltext':False,'title':'Vidéos'}]
        self.addAsyncCleanup(library.kiwix_queries.close)
        # A search may start the optional video scan; join its writer before
        # restoring ROOT and deleting this test's directory (notably Windows).
        self.addAsyncCleanup(videos.stop,reason='service_stopped')

    def xml(self,book,title='Feu de camp'):
        return f'<rss><channel><item><title>{title}</title><link>/content/{book}/Feu_de_camp</link><description>Extrait fictif sur le sujet demandé.</description></item></channel></rss>'.encode(), 'application/xml'

    async def test_fire_query_searches_explicit_archives_separates_languages_and_reports_unindexed(self):
        calls=[]
        async def fetch(path,*args):
            if path.startswith('/suggest?'):return b'[]','application/json'
            values=parse_qs(urlsplit(path).query);calls.append(values)
            self.assertNotIn('books.filter.lang',values)
            names=values['books.name']
            if 'multi' in names:self.assertEqual(names,['multi'])
            return self.xml(names[0])
        with patch.object(library,'books',AsyncMock(return_value=self.catalog)),patch.object(library,'get',AsyncMock(side_effect=fetch)):
            found=await library.search('comment faire un feu')
        self.assertEqual(len(found),3)
        self.assertEqual(found.coverage['searched'],3);self.assertEqual(found.coverage['without_fulltext'],1)
        self.assertEqual(found.coverage['native_incompatible'],1)
        english=next(c for c in calls if c['books.name']==['manual_en'])
        self.assertEqual(english['pattern'],['fire'])
        self.assertTrue(all(r['id'].startswith('zim:') for r in found))

    async def test_rejected_batch_retries_individual_archives_without_hiding_success(self):
        catalog=[dict(self.catalog[0],book=name) for name in ['a','broken','b']]
        async def fetch(path,*args):
            if path.startswith('/suggest?'):return b'[]','application/json'
            names=parse_qs(urlsplit(path).query)['books.name']
            if len(names)>1 or names==['broken']:raise HTTPException(400,'Different languages')
            return self.xml(names[0])
        with patch.object(library,'books',AsyncMock(return_value=catalog)),patch.object(library,'get',AsyncMock(side_effect=fetch)):
            found=await library.search('feu')
        self.assertEqual(len(found),2);self.assertEqual(found.coverage['searched'],2)
        self.assertEqual(found.coverage['failed'],1);self.assertEqual(found.coverage['status'],'partial')
        self.assertIn('partielle',found.coverage['warning'])

    async def test_catalogue_outage_is_not_a_valid_empty_search(self):
        with patch.object(library,'books',AsyncMock(return_value=library.Catalog(available=False))):
            found=await library.search('feu')
        self.assertEqual(found,[]);self.assertEqual(found.coverage['status'],'unavailable')
        self.assertIn('ne prouvent pas',found.coverage['warning'])

    async def test_exact_language_filter_includes_multilingual_but_not_unrelated_language(self):
        calls=[]
        async def fetch(path,*args):
            if path.startswith('/suggest?'):return b'[]','application/json'
            values=parse_qs(urlsplit(path).query);calls.extend(values['books.name']);return self.xml(values['books.name'][0])
        with patch.object(library,'books',AsyncMock(return_value=self.catalog)),patch.object(library,'get',AsyncMock(side_effect=fetch)):
            await library.search('feu',language='fr')
        self.assertEqual(set(calls),{'wikipedia_fr','video'})

    async def test_french_search_skips_the_english_ifixit_edition_and_english_pages(self):
        english, french = 'ifixit_en_all_2025-12', 'ifixit_fr_all_2026-03'
        catalog = [dict(self.catalog[0], book=book) for book in (english, french)]
        calls = []
        async def fetch(path, *args):
            names = parse_qs(urlsplit(path).query).get('books.name', [])
            calls.extend(names)
            if path.startswith('/suggest?'):
                return b'[]', 'application/json'
            return (f'<rss><channel><item><title>Water purification system</title>'
                    f'<link>/content/{names[0]}/Device/Water_Purification_System</link>'
                    '<description>This is a system for drinking water with a filter that removes particles from the water.</description>'
                    '</item></channel></rss>').encode(), 'application/xml'

        with patch.object(library, 'books', AsyncMock(return_value=catalog)), \
                patch.object(library, 'get', fetch), patch.object(library.search_cache, 'budget', return_value=0):
            found = await library.search('eau potable', 'fr', kind='documents')
            self.assertEqual(found, [])
            self.assertEqual(set(calls), {french})
            found = await library.search('eau potable', 'en', kind='documents')
            self.assertEqual({(item['book'], item['language']) for item in found}, {(english, 'en')})

    def scoped_catalogue(self):
        dictionary = 'wiktionary_fr_all'
        culture = 'gutenberg_fr_all'
        sorting = collection_sort.Sort(other=frozenset(map(collection_sort.archive, (dictionary, culture))))
        root = Path(self.temp.name)
        collection_sort.save(root, sorting)
        books = [self.catalog[0], *({'book': book, 'language': 'fra', 'fulltext': True, 'title': book}
                                    for book in (dictionary, culture))]
        return root, books

    async def test_portal_only_queries_other_collections_when_explicitly_requested(self):
        from pilot.app import app

        root, books = self.scoped_catalogue()
        names = {book['book'] for book in books}
        calls = set()

        async def fetch(path, *args):
            parameters = parse_qs(urlsplit(path).query)
            calls.update(parameters.get('content', parameters.get('books.name', [])))
            if path.startswith('/suggest?'):
                return b'[]', 'application/json'
            return b'<rss><channel/></rss>', 'application/xml'

        cases = (
            ({}, {'wikipedia_fr'}),
            ({'stream': 'true', 'domain': 'resilience'}, {'wikipedia_fr'}),
            ({'domain': 'other'}, names - {'wikipedia_fr'}),
            ({'domain': 'all'}, names),
        )
        with patch.object(network, 'CATALOG', root), \
                patch.object(library, 'books', AsyncMock(return_value=books)), \
                patch.object(library, 'get', fetch), \
                patch.object(library.search_cache, 'budget', return_value=0):
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url='http://fixture') as client:
                for (params, expected), query in zip(cases, ('compost', 'potager', 'semis', 'jardin')):
                    with self.subTest(params=params):
                        calls.clear()
                        response = await client.get('/api/search', params={'q': query, 'kind': 'documents', **params})
                        self.assertEqual(response.status_code, 200)
                        if params.get('stream'):
                            self.assertIn('"state":"done"', response.text)
                        self.assertEqual(calls, expected)

    async def test_assistant_uses_selected_scope_for_preparation_and_model_tool_calls(self):
        from pilot import engine, operations
        from pilot.app import app
        from pilot.routes import deps

        root, books = self.scoped_catalogue()
        calls = []
        turns = []

        async def fetch(path, *args):
            parameters = parse_qs(urlsplit(path).query)
            names = parameters.get('content', parameters.get('books.name', []))
            calls.append((parameters.get('term', parameters.get('pattern', ['']))[0], names))
            if path.startswith('/suggest?'):
                return b'[]', 'application/json'
            return b'<rss><channel/></rss>', 'application/xml'

        def simulated_model(request):
            if request.url.path == '/api/ps':
                return httpx.Response(200, json={'models': []})
            payload = json.loads(request.content)
            if not payload.get('messages'):
                return httpx.Response(200, json={'done': True})
            tools = [message for message in payload['messages'] if message.get('tool_name') == 'search_library']
            if not tools:
                # The model has no authority to broaden the user's scope.
                message = {'tool_calls': [{'function': {'name': 'search_library',
                            'arguments': {'query': 'batterie', 'domain': 'all'}}}]}
            else:
                message = {'content': 'Aucun passage utile dans le résultat de cet essai fictif.'}
            turns.append(message)
            return httpx.Response(200, content=(json.dumps({'message': message, 'done': True}) + '\n').encode())

        client_class = httpx.AsyncClient
        def model_client(**options):
            return client_class(transport=httpx.MockTransport(simulated_model), **options)

        def current_user():
            return {'id': 'fixture-user', 'role': 'admin', 'name': 'Fixture'}

        policy = Path(__file__).resolve().parents[1] / 'deploy/assistant-system.fr.txt'
        with patch.dict(app.dependency_overrides, {deps.user: current_user}), \
                patch.object(network, 'CATALOG', root), \
                patch.object(library, 'books', AsyncMock(return_value=books)), \
                patch.object(library, 'get', fetch), \
                patch.object(library.search_cache, 'budget', return_value=0), \
                patch.object(engine, 'POLICY', policy), \
                patch.object(engine.model_runtime, 'describe', AsyncMock(return_value={'available': True, 'installed': True, 'native_context': 131072})), \
                patch.object(operations, 'status', AsyncMock(return_value={'online': True, 'message': 'Fixture'})):
            async with client_class(transport=httpx.ASGITransport(app=app), base_url='http://fixture') as client:
                with patch.object(engine.httpx, 'AsyncClient', side_effect=model_client):
                    for options, expected in (
                        ({}, {'wikipedia_fr'}),
                        ({'domain': 'all'}, {book['book'] for book in books}),
                    ):
                        calls.clear()
                        turns.clear()
                        response = await client.post('/api/questions', headers={'Origin': 'http://fixture'},
                                                     json={'message': 'Cherche un document sur le compost', **options})
                        self.assertEqual(response.status_code, 200)
                        job = response.json()['id']
                        if job in engine.ACTIVE:
                            await asyncio.wait_for(engine.ACTIVE[job], 10)
                        with store.connect() as db:
                            self.assertEqual(db.execute('SELECT status FROM jobs WHERE id=?', (job,)).fetchone()[0], 'done')
                        self.assertEqual(len(turns), 2)
                        for topic in ('compost', 'batterie'):
                            self.assertEqual({name for pattern, names in calls if topic in pattern for name in names},
                                             expected, (options, calls))

    async def test_duplicate_hits_are_deduplicated_and_unknown_books_rejected(self):
        async def fetch(path,*args):
            if path.startswith('/suggest?'):return b'[]','application/json'
            return self.xml('not_in_catalogue')
        with patch.object(library,'books',AsyncMock(return_value=self.catalog)),patch.object(library,'get',AsyncMock(side_effect=fetch)):
            found=await library.search('feu')
        self.assertEqual(found,[])

    async def test_catalogue_parses_language_namespaces_uuid_and_fulltext_flags(self):
        xml=b'<feed xmlns="http://www.w3.org/2005/Atom" xmlns:dc="http://purl.org/dc/elements/1.1/"><entry><id>urn:uuid:12345678-1234-1234-1234-123456789012</id><title>Test</title><dc:language>fra</dc:language><tags>_ftindex:yes;_pictures:yes</tags><link type="text/html" href="/content/test/"/></entry></feed>'
        with patch.object(library,'get',AsyncMock(return_value=(xml,'application/xml'))):value=await library.books()
        self.assertEqual(value[0]['book'],'test');self.assertEqual(value[0]['language'],'fra')
        self.assertTrue(value[0]['fulltext']);self.assertTrue(value[0]['search_id'])

    async def test_html_escaped_suggestion_paths_share_the_native_fulltext_identity(self):
        cases=[('Compost_et_l&apos;urbanisme',"Compost_et_l'urbanisme"),('Compost &amp; jardin','Compost & jardin'),
               ('Compost_&#233;t&#233;','Compost_été'),('Compost_%26amp%3B','Compost_&amp;')]
        zims=Path(self.temp.name)/'zim';zims.mkdir()
        for edition,(suggested,expected) in enumerate(cases,1):
            with self.subTest(path=suggested):
                # Each mocked response is a different archive edition. Keep the
                # real disk-cache invalidation instead of reusing an old fixture.
                (zims/'wikipedia_fr.zim').write_bytes(b'x'*edition)
                await library.kiwix_queries.close()
                async def reader(path):
                    if path.startswith('/suggest?'):return json.dumps([{'kind':'path','value':'Compost','path':suggested}]).encode(),'application/json'
                    link='/content/wikipedia_fr/'+quote(expected,safe='/')
                    return ('<rss><channel><item><title>Compost</title><link>'+escape(link)+'</link><description>Compost, extrait fictif.</description></item></channel></rss>').encode(),'application/xml'
                with patch.object(library,'books',AsyncMock(return_value=self.catalog[:1])),patch.object(library,'get',reader),patch.dict('os.environ',{'ZIM_DIR':str(zims)}):
                    found=await library.search('compost')
                self.assertEqual([row['id'] for row in found],['zim:wikipedia_fr/'+expected])

    async def test_title_only_paths_decode_entities_before_rejecting_unsafe_paths(self):
        paths=['&#47;&#47;other.invalid/path','https&#58;//other.invalid/path','&#46;&#46;/private','folder/&#46;&#46;/private','folder&#92;private','%252e%252e/private']
        async def reader(path):
            if path.startswith('/suggest?'):return json.dumps([{'kind':'path','value':'Compost','path':p} for p in paths]).encode(),'application/json'
            return b'<rss><channel/></rss>','application/xml'
        with patch.object(library,'books',AsyncMock(return_value=self.catalog[:1])),patch.object(library,'get',reader):
            found=await library.search('compost')
        self.assertEqual(found,[])

    async def test_fulltext_excerpt_keeps_highlighted_words_and_following_text(self):
        cases=[
            '<description><b>Bicycle</b> <b>puncture repair</b> : fictional excerpt after the matches.</description>',
            '<description>Before <b>bicycle</b> <i>puncture repair</i> and after. <script>PRIVATE SCRIPT</script></description>',
            '<description>&lt;b&gt;Bicycle&lt;/b&gt; puncture repair, escaped HTML excerpt.</description>',
        ]
        for edition,description in enumerate(cases):
            with self.subTest(description=edition):
                async def reader(path):
                    if path.startswith('/suggest?'):return b'[]','application/json'
                    return ('<rss><channel><item><title>Bicycle maintenance</title><link>/content/wikipedia_fr/Repair</link>'+description+'</item></channel></rss>').encode(),'application/xml'
                book=dict(self.catalog[0],book='wikipedia_fr_'+str(edition))
                # Unique collection identity also keeps the real response cache isolated.
                async def scoped(path,*args):
                    if path.startswith('/content/'):raise HTTPException(404)
                    raw,content=await reader(path);return raw.replace(b'wikipedia_fr/',book['book'].encode()+b'/'),content
                with patch.object(library,'books',AsyncMock(return_value=[book])),patch.object(library,'get',scoped):
                    found=await library.search('bicycle puncture repair')
                self.assertEqual(len(found),1)
                self.assertIn('puncture repair',found[0]['excerpt'].lower())
                self.assertNotIn('<b>',found[0]['excerpt']);self.assertNotIn('PRIVATE SCRIPT',found[0]['excerpt'])
                if edition<2:self.assertIn('after',found[0]['excerpt'])

    async def test_request_budget_is_bounded_and_unsearched_books_are_disclosed(self):
        catalog=[dict(self.catalog[0],book='wikipedia_fr_'+str(i)) for i in range(45)]
        async def fetch(path,*args):
            if path.startswith('/suggest?'):return b'[]','application/json'
            if path.startswith('/content/'):raise HTTPException(404)
            return self.xml(parse_qs(urlsplit(path).query)['books.name'][0])
        with patch.object(library,'books',AsyncMock(return_value=catalog)),patch.object(library,'get',AsyncMock(side_effect=fetch)) as get:
            found=await library.search('feu')
        calls = [call.args[0] for call in get.await_args_list]
        self.assertLessEqual(sum(path.startswith(('/search?', '/suggest?')) for path in calls), 36)
        self.assertLessEqual(sum(path.startswith('/content/') for path in calls), 12)
        self.assertGreater(found.coverage['not_searched'], 0)
        self.assertEqual(found.coverage['status'],'partial')
