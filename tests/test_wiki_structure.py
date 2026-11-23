import asyncio
from unittest import IsolatedAsyncioTestCase, TestCase
from unittest.mock import AsyncMock, patch

from fastapi import HTTPException

from pilot import library, retrieval, wiki_structure


class ArticleStructureTests(TestCase):
    def test_categories_and_sections_are_subject_evidence(self):
        raw = b'''
            <link rel="mw:PageProp/Category" href="./Category:Seed_saving#sort">
            <a href="Category:Water_treatment">Link only</a>
            <div id="mw-normal-catlinks"><ul><li><a href="/wiki/Category:Botany">Botany</a></li></ul></div>
            <nav><h2>Water treatment</h2></nav>
            <h2><span></span>History</h2><h3>Origins</h3>
            <h2>See also</h2><h2>Water treatment</h2>
        '''
        structure = wiki_structure.extract(raw)
        self.assertEqual(structure, {'categories': ['Seed saving', 'Botany'], 'sections': ['History'], 'subsections': ['Origins']})
        item = {'id': 'zim:wikipedia_en_test/Seed_library', 'title': 'Seed library', '_wiki_structure': structure}
        self.assertEqual(retrieval.domains(item), ['resilience', 'culture'])

    def test_incidental_excerpt_uses_fallback_only_without_structure(self):
        item = {'id': 'zim:wikipedia_fr_test/Eau', 'title': 'Eau', 'excerpt': 'Fabrication et réparation des batteries'}
        self.assertIn('resilience', retrieval.domains(item))
        item['_wiki_structure'] = wiki_structure.extract(b'<h2>General properties</h2><h3>Water treatment</h3>')
        self.assertEqual(retrieval.domains(item), ['culture'])
        self.assertIn('resilience', retrieval.domains(dict(item, id='video:fixture')))


class SearchStructureTests(IsolatedAsyncioTestCase):
    async def test_only_local_articles_are_read_and_failed_read_keeps_fallback(self):
        a = {'id': 'zim:wikipedia_fr_test/Radio', 'title': 'Radio'}
        b = {'id': 'zim:wikipedia_fr_test/Radio_B', 'title': 'Radio B'}
        unrelated = {'id': 'zim:wikibooks_fr_test/Radio', 'title': 'Radio'}
        plan = retrieval.plan('radio', ['radio'], {})
        self.assertEqual(retrieval.domains(a), ['resilience'])
        reader = AsyncMock(side_effect=[(b'<h2>Homophonies</h2>', 'text/html'), HTTPException(404)])
        with patch.object(library, 'get', reader):
            report = await library.enrich_wikipedia([a, b, unrelated], plan, 'gen1', retrieval.NormalCache())
            self.assertEqual((report['selected'], report['read']), (2, 1))
            self.assertEqual(retrieval.domains(a), ['culture'])
            self.assertEqual(retrieval.domains(b), ['resilience'])
            self.assertEqual(retrieval.domains(unrelated), ['resilience'])
            await library.enrich_wikipedia([a], plan, 'gen1', retrieval.NormalCache())
            self.assertEqual(reader.await_count, 2)
            reader.side_effect = None
            reader.return_value = (b'<h2>Homophones</h2>', 'text/html')
            await library.enrich_wikipedia([a], plan, 'gen2', retrieval.NormalCache())
            self.assertEqual(reader.await_count, 3)

    async def test_concurrency_is_bounded_across_searches(self):
        plan = retrieval.plan('radio', ['radio'], {})
        running = peak = 0

        async def read(_path, _max_bytes):
            nonlocal running, peak
            running += 1
            peak = max(peak, running)
            await asyncio.sleep(0.005)
            running -= 1
            return b'<h2>History</h2>', 'text/html'

        items = [{'id': f'zim:wikipedia_fr_test/Radio_{i}', 'title': 'Radio'} for i in range(22)]
        with patch.object(library, 'get', read):
            first, second = await asyncio.gather(
                library.enrich_wikipedia(items, plan, 'shared', retrieval.NormalCache()),
                library.enrich_wikipedia(items[:4], plan, 'shared', retrieval.NormalCache()),
            )
        self.assertEqual((first['selected'], first['read'], second['read'], peak), (12, 12, 4, 2))

    async def test_redirect_alias_uses_one_result_slot_without_merging_other_editions(self):
        canonical = 'zim:wikipedia_fr_test/Photosynthèse'
        alias = 'zim:wikipedia_fr_test/Photosynthese'
        other = 'zim:wikipedia_en_test/Photosynthesis'
        items = [
            {'id': canonical, 'title': 'Photosynthèse'},
            {'id': alias, 'title': 'Photosynthese'},
            {'id': other, 'title': 'Photosynthesis', 'excerpt': 'Photosynthèse'},
        ]
        plan = retrieval.plan('photosynthèse', ['photosynthese'], {})
        redirected = '/content/wikipedia_fr_test/Photosynth%C3%A8se'

        async def read(path, _maximum):
            return library.Fetched(b'<h2>History</h2>', 'text/html', path if 'wikipedia_en' in path else redirected)

        with patch.object(library, 'get', side_effect=read) as reader:
            for _ in range(2):
                await library.enrich_wikipedia(items, plan, 'redirects', retrieval.NormalCache())
                ranked = retrieval.ordered(items, plan, 5)
                self.assertEqual(len(ranked), 2)
                self.assertIn(ranked[0]['id'], {alias, canonical})
                self.assertEqual(ranked[1]['id'], other)
                self.assertNotIn('_resolved_zim_id', ranked[0])
            self.assertEqual(reader.await_count, 3)
