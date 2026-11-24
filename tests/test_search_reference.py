"""Versioned natural requests, tested on fictional documents, never Marc's corpus."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import AsyncMock, patch

from pilot import library, store

BASE = Path(__file__).resolve().parents[1]
REFERENCE = json.loads((BASE/'portal/interface/search-reference.json').read_text(encoding='utf-8'))
FIXTURES = json.loads((BASE/'tests/search_reference_fixtures.json').read_text(encoding='utf-8'))


class SearchReferenceTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        temporary = tempfile.TemporaryDirectory(); self.addCleanup(temporary.cleanup)
        root = Path(temporary.name); guides = root/'guides'; guides.mkdir()
        metadata = []
        for item in FIXTURES['documents']:
            path = item['id']+'.'+item['language']+'.txt'
            (guides/path).write_text(item['text'], encoding='utf-8')
            metadata.append({**item, 'path':path, 'provenance':item.get('provenance','Fixture fictive')})
        (guides/'metadata.json').write_text(json.dumps(metadata), encoding='utf-8')
        for target, name, value in [(store,'ROOT',root/'state'), (library,'GUIDES',guides), (library,'books',AsyncMock(return_value=[]))]:
            patched = patch.object(target,name,value); patched.start(); self.addCleanup(patched.stop)
        store.init(); library.index_guides()
        self.addAsyncCleanup(library.kiwix_queries.close)

    async def verify_cases(self, verification):
        for case in REFERENCE['cases']:
            if case['id'].startswith('verify-') != verification: continue
            with self.subTest(case=case['id'],query=case['query']):
                expected = FIXTURES['expected'][case['id']]
                found = await library.search(case['query'],limit=5,collection=case.get('collection',''))
                if expected is None:
                    self.assertEqual(found,[]); continue
                wanted = next(item for item in FIXTURES['documents'] if item['id']==expected)
                wanted_id = 'guide:'+expected+'.'+wanted['language']+'.txt'
                self.assertIn(wanted_id,[row['id'] for row in found[:5]],[(r['title'],r['excerpt']) for r in found])
                self.assertEqual(found[0]['id'],wanted_id,[(r['title'],r['excerpt']) for r in found])
                if case['domain']=='resilience':
                    filtered = await library.search(case['query'],limit=5,collection=case.get('collection',''),domain='resilience')
                    self.assertIn(wanted_id,[row['id'] for row in filtered[:5]],'Le filtre a perdu la source pertinente.')

    async def test_calibration_requests(self):
        await self.verify_cases(False)

    async def test_verification_requests(self):
        await self.verify_cases(True)

    def test_reference_is_versioned_and_distinct_from_corpus_claims(self):
        self.assertEqual(REFERENCE['schema'],1)
        ids=[case['id'] for case in REFERENCE['cases']]
        self.assertEqual(len(ids),32); self.assertEqual(len(set(ids)),len(ids))
        self.assertEqual(set(ids),set(FIXTURES['expected']))
        self.assertTrue(all(case.get('need') for case in REFERENCE['cases']))
