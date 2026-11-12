"""Learning requirements, catalogue audit and bilingual retrieval, with tiny fixtures."""
import asyncio
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import AsyncMock,patch
from urllib.parse import parse_qs,urlsplit

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import audit_learning
import content
import kiwix_select as ks
from pilot import learning,library,store


class LearningTests(unittest.TestCase):
    def test_pathways_cover_the_requested_axes_with_concrete_subjects_and_existing_guide_ids(self):
        data=learning.pathways();rules=ks.themes()
        expected={'sciences','mesure','materiaux','machines','metallurgie','chimie-pratique','textile','agriculture','sante','education','organisation','histoire-techniques','reparation','energie'}
        self.assertEqual({d['id'] for d in data['domains']},expected)
        self.assertEqual(data['domains'][0]['id'],'sciences')
        self.assertEqual([v['id'] for v in data['levels']],['principle','current','local','transmit'])
        self.assertEqual([s['label'] for s in data['steps']],['Comprendre','Mesurer','Réaliser','Contrôler','Entretenir','Transmettre'])
        guide_ids={item['id'] for item in content.catalog()}
        for domain in data['domains']:
            self.assertTrue(domain['summary']);self.assertGreaterEqual(len(domain['subjects']),4)
            for subject in domain['subjects']:
                self.assertTrue(subject['label']);self.assertTrue(subject['query']);self.assertLessEqual(len(subject['query']),200)
            self.assertTrue(set(rules[domain['id']].get('guides',[]))<=guide_ids)

    def test_metadata_audit_distinguishes_unknown_presence_from_present_files_and_deduplicates_editions(self):
        def entry(month,lang='eng'):
            return f'<entry><name>sewing_en_all</name><title>Sewing</title><summary>Sewing and rope making</summary><language>{lang}</language><updated>2026-{month}-01</updated><link type="application/x-zim" length="1024" href="https://download.kiwix.org/zim/other/sewing_en_all_2026-{month}.zim.meta4"/></entry>'
        raw=('<feed xmlns="http://www.w3.org/2005/Atom"><totalResults>3</totalResults>'+entry('01')+entry('02')+entry('03','deu')+'</feed>').encode()
        with patch.object(content,'catalog',return_value=[]):
            report=audit_learning.audit(raw)
            row=next(r for r in report['coverage'] if r['id']=='textile')
            self.assertEqual(row['references'],1);self.assertIsNone(row['local_references'])
            self.assertEqual(row['status'],'references_to_review')
            with tempfile.TemporaryDirectory() as folder:
                root=Path(folder);path=root/'library/zim/sewing_en_all_2026-02.zim';path.parent.mkdir(parents=True);path.write_bytes(b'tiny fixture')
                report=audit_learning.audit(raw,root)
                self.assertEqual(next(r for r in report['coverage'] if r['id']=='textile')['local_references'],1)
            self.assertEqual(next(r for r in report['coverage'] if r['id']=='metallurgie')['status'],'references_missing')

    def test_learning_queries_retrieve_english_local_passages(self):
        with tempfile.TemporaryDirectory() as folder,patch.object(library,'books',AsyncMock(return_value=[])):
            root=Path(folder);guides=root/'guides';guides.mkdir()
            (guides/'manual.en.txt').write_text('Sewing rope calibration accounting clay sharpening.',encoding='utf-8')
            with patch.object(store,'ROOT',root/'state'),patch.object(library,'GUIDES',guides):
                store.init();library.index_guides()
                for word in ['couture','cordage','étalonnage','comptabilité','argile','affûtage']:
                    with self.subTest(word=word):self.assertTrue(asyncio.run(library.search(word)))

    def test_learning_queries_are_translated_for_english_kiwix_search(self):
        requests=[]
        async def get(path,**kw):
            requests.append(path)
            return b'<rss><channel/></rss>','application/xml'
        with tempfile.TemporaryDirectory() as folder,patch.object(store,'ROOT',Path(folder)),patch.object(library,'books',AsyncMock(return_value=[{'book':'test','language':'eng'}])),patch.object(library,'get',get):
            store.init();asyncio.run(library.search('comptabilité'))
        self.assertEqual(parse_qs(urlsplit(requests[0]).query)['pattern'],['accounting'])


if __name__=='__main__':unittest.main()
