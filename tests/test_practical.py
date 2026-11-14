"""Source-grounded reading dossiers, with tiny fictional files and no inference."""
import asyncio
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import AsyncMock,patch
from fastapi import HTTPException
from pilot import catalogue,inventory,learning,library,practical,store


class PracticalTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        temporary=tempfile.TemporaryDirectory();self.addCleanup(temporary.cleanup)
        self.root=Path(temporary.name);self.guides=self.root/'guides';self.guides.mkdir();self.zims=self.root/'zim';self.zims.mkdir()
        self.source_id='guide:pedal.fr.txt';self.file=self.guides/'pedal.fr.txt';self.file.write_text('Fictional assembly diagram, no real instructions.',encoding='utf-8')
        (self.guides/'metadata.json').write_text(json.dumps([{'path':'pedal.fr.txt','title':'Mécanisme fictif','language':'fr','document_date':'2001','edition':'Fictive'}]))
        for target,name,value in [(store,'ROOT',self.root/'state'),(library,'GUIDES',self.guides),(inventory,'ZIMS',self.zims),(library,'books',AsyncMock(return_value=[]))]:
            p=patch.object(target,name,value);p.start();self.addCleanup(p.stop)
        store.init();library.index_guides();self.revision=catalogue.revision(self.source_id,self.guides,self.zims)

    async def save(self,**changes):
        values={'identifier':'generateur-pedales','source_id':self.source_id,'expected_source':self.revision,'expected_dossier':practical.dossier(changes.get('identifier','generateur-pedales'))['revision'],
                'sections':['plans','materials'],'note':'Le passage fictif contient un dessin, sans méthode réelle.','locator':'Section dessin fictif','reviewed':True}
        return await practical.save(**{**values,**changes})

    def test_six_objectives_have_queries_and_explicit_unexamined_sections(self):
        data=practical.overview();self.assertEqual({d['id'] for d in data['dossiers']},{'feu','eau','abri','generateur-pedales','velo','graines'})
        for item in data['dossiers']:
            self.assertEqual(item['reviewed_sections'],0);self.assertEqual(len(item['queries']),2)
            detail=practical.dossier(item['id']);self.assertEqual(len(detail['sections']),6);self.assertFalse(detail['evidence'])
            self.assertTrue(all(not section['has_reviewed_reference'] for section in detail['sections']))

    async def test_explicit_source_read_creates_shared_dated_references_without_changing_source(self):
        before=self.file.read_bytes();data=await self.save();self.assertEqual(data['reviewed_sections'],2)
        entry=data['evidence'][0];self.assertEqual(entry['state'],'reviewed');self.assertEqual(entry['document_date'],'2001')
        self.assertEqual(entry['title'],'Mécanisme fictif');self.assertEqual(entry['locator'],'Section dessin fictif')
        self.assertEqual(self.file.read_bytes(),before)
        exported=practical.export();self.assertNotIn('Fictional assembly diagram',json.dumps(exported));self.assertNotIn('user_id',json.dumps(exported))
        self.assertEqual(practical.dossier('generateur-pedales')['revision'],1)
        updated=await self.save(note='Repère fictif revu.');self.assertEqual(len(updated['evidence']),1);self.assertEqual(updated['evidence'][0]['id'],entry['id'])

    async def test_review_and_locator_are_required_and_unknown_sections_rejected(self):
        for values in ({'reviewed':False},{'locator':''},{'sections':[]},{'sections':['invented']},{'note':' '},{'source_id':'collection:fixture'}):
            with self.subTest(values=values),self.assertRaises(HTTPException):await self.save(**values)
        self.assertEqual(practical.dossier('generateur-pedales')['reviewed_sections'],0)

    async def test_changed_or_missing_source_keeps_old_note_but_does_not_cover_a_section(self):
        await self.save();self.file.write_text('Changed fictional edition, including different material.',encoding='utf-8')
        data=practical.dossier('generateur-pedales');self.assertEqual(data['reviewed_sections'],0);self.assertEqual(data['evidence'][0]['state'],'source_changed')
        with self.assertRaises(HTTPException):await self.save()
        self.file.unlink();data=practical.dossier('generateur-pedales');self.assertEqual(data['evidence'][0]['state'],'unavailable');self.assertTrue(data['evidence'][0]['note'])

    async def test_network_read_failure_does_not_save_a_reference(self):
        with patch.object(library,'source',AsyncMock(side_effect=HTTPException(503,'Unavailable fixture'))):
            with self.assertRaises(HTTPException):await self.save()
        self.assertEqual(practical.dossier('generateur-pedales')['revision'],0)

    async def test_two_editors_and_source_change_during_read_cannot_overwrite_review(self):
        await self.save()
        with self.assertRaises(HTTPException) as caught:await self.save(expected_dossier=0,note='Stale editor')
        self.assertEqual(caught.exception.status_code,409)
        original=library.source
        async def changed(identifier):
            value=await original(identifier);self.file.write_text('Changed while reading fictional source.');return value
        with patch.object(library,'source',side_effect=changed):
            with self.assertRaises(HTTPException):await self.save()
        self.assertEqual(practical.dossier('generateur-pedales')['revision'],1)

    async def test_remove_only_its_reference_and_preserves_document_and_other_dossier(self):
        first=await self.save();await self.save(identifier='velo',locator='Autre section fictive')
        result=practical.remove('generateur-pedales',first['evidence'][0]['id'],first['revision']);self.assertEqual(result['reviewed_sections'],0)
        self.assertTrue(self.file.is_file());self.assertEqual(practical.dossier('velo')['reviewed_sections'],2)
        with self.assertRaises(HTTPException):practical.remove('velo',practical.dossier('velo')['evidence'][0]['id'],0)

    async def test_search_preserves_partial_results_and_does_not_call_model_or_mark_reviewed(self):
        expected={'id':self.source_id,'title':'Mécanisme fictif','language':'fr','excerpt':'Fictional only.','classification':{'document_type':'unknown'}}
        responses=[library.SearchResults([expected],{'status':'partial','warning':'Not all archives.'}),HTTPException(503,'Fixture unavailable')]
        with patch.object(library,'search',AsyncMock(side_effect=responses)) as search:
            result=await practical.search('generateur-pedales');self.assertEqual(len(result['results']),1);self.assertEqual(result['coverage'][1]['status'],'unavailable')
            self.assertEqual(search.await_args.kwargs['domain'],'resilience')
        self.assertEqual(practical.dossier('generateur-pedales')['reviewed_sections'],0)

    async def test_references_are_bounded_and_corruption_does_not_hide_other_dossiers(self):
        for i in range(24):await self.save(locator='Repère fictif '+str(i))
        with self.assertRaises(HTTPException):await self.save(locator='Excess')
        self.assertEqual(len(practical.dossier('generateur-pedales')['evidence']),24)
        with store.connect() as db:db.execute('INSERT OR REPLACE INTO settings VALUES(?,?)',(practical.PREFIX+'feu','corrupt fixture'))
        with self.assertRaises(HTTPException):practical.dossier('feu')
        data=practical.overview();self.assertEqual(len(data['dossiers']),6);self.assertIsNone(next(d for d in data['dossiers'] if d['id']=='feu')['reviewed_sections'])

    async def test_pdf_page_ids_share_revision_but_keep_their_precise_locator(self):
        source=await library.source(self.source_id)
        with patch.object(library,'source',AsyncMock(return_value={**source,'id':self.source_id+'#page=2'})):
            data=await self.save(source_id=self.source_id+'#page=2',locator='Page 2')
        self.assertEqual(data['evidence'][0]['source_id'],self.source_id+'#page=2');self.assertEqual(data['evidence'][0]['state'],'reviewed')

    async def test_export_whitelists_only_reference_fields_even_if_unknown_state_fields_exist(self):
        await self.save()
        with store.connect() as db:
            key=practical.PREFIX+'generateur-pedales';raw=json.loads(db.execute('SELECT value FROM settings WHERE key=?',(key,)).fetchone()['value'])
            raw['evidence'][0]['text']='PRIVATE EXTRA FIELD';raw['conversation']='PRIVATE EXTRA FIELD'
            db.execute('UPDATE settings SET value=? WHERE key=?',(json.dumps(raw),key))
        self.assertNotIn('PRIVATE EXTRA FIELD',json.dumps(practical.export()))
