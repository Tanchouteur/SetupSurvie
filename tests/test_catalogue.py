"""Metadata overlays on tiny fictional files; no corpus, model or network."""
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import AsyncMock,patch

from fastapi import HTTPException
from pilot import catalogue,library,retrieval,store,inventory,archive_index


class CatalogueTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        temporary=tempfile.TemporaryDirectory();self.addCleanup(temporary.cleanup)
        self.root=Path(temporary.name);self.guides=self.root/'guides';self.zims=self.root/'zim';self.guides.mkdir();self.zims.mkdir()
        self.item={'id':'guide:mechanism.fr.txt','title':'Mécanisme à pédales','excerpt':'Principe du mécanisme. Fictional fixture.'}
        (self.guides/'mechanism.fr.txt').write_text('Principe du mécanisme. Fictional fixture.',encoding='utf-8')
        for target,name,value in [(store,'ROOT',self.root/'state'),(library,'GUIDES',self.guides),(inventory,'ZIMS',self.zims),(library,'books',AsyncMock(return_value=[]))]:
            patched=patch.object(target,name,value);patched.start();self.addCleanup(patched.stop)
        env=patch.dict(os.environ,{'ZIM_DIR':str(self.zims)});env.start();self.addCleanup(env.stop)
        store.init();library.index_guides()

    def save(self,item=None,domains=None,kind='procedure',status='reviewed'):
        item=item or self.item;fingerprint=catalogue.revision(item['id'],self.guides,self.zims)
        return catalogue.save(item['id'],{'domains':domains if domains is not None else ['resilience','culture'],'document_type':kind,'status':status},fingerprint,self.guides,self.zims)

    async def test_human_correction_controls_both_scopes_and_survives_reindex(self):
        self.assertEqual(await library.search('mécanisme pédales',domain='resilience'),[])
        self.save();library.index_guides()
        for domain in ('all','resilience','culture'):
            found=await library.search('mécanisme pédales',domain=domain)
            self.assertEqual(found[0]['id'],self.item['id']);self.assertEqual(found[0]['classification']['method'],'human')
        source=await library.source(self.item['id'])
        self.assertEqual(source['classification']['document_type'],'procedure')
        catalogue.reset(self.item['id']);self.assertEqual(await library.search('mécanisme pédales',domain='resilience'),[])

    async def test_no_domains_does_not_hide_from_entire_library_and_new_edition_loses_review(self):
        self.save(domains=[])
        self.assertEqual((await library.search('mécanisme'))[0]['domains'],[])
        self.assertEqual(await library.search('mécanisme',domain='culture'),[])
        (self.guides/'mechanism.fr.txt').write_text('New edition. Fictional mechanism text.',encoding='utf-8')
        result=catalogue.classification(self.item,self.guides,self.zims)
        self.assertEqual(result['method'],'automatic');self.assertEqual(result['status'],'source_changed');self.assertNotEqual(result['document_type'],'procedure')

    def test_stale_editor_cannot_save_and_pdf_pages_share_document_annotation(self):
        old=catalogue.revision(self.item['id'],self.guides,self.zims)
        (self.guides/'mechanism.fr.txt').write_text('Changed edition with different size.')
        with self.assertRaises(HTTPException) as error:
            catalogue.save(self.item['id'],{'domains':['culture'],'document_type':'manual','status':'corrected'},old,self.guides,self.zims)
        self.assertEqual(error.exception.status_code,409)
        (self.guides/'manual.pdf').write_bytes(b'Fictional PDF')
        self.save({'id':'guide:manual.pdf#page=3'})
        info=catalogue.classification({'id':'guide:manual.pdf#page=8'},self.guides,self.zims)
        self.assertEqual(info['method'],'human');self.assertEqual(list(catalogue.snapshot()),['guide:manual.pdf'])

    def test_bad_record_or_metadata_failure_does_not_break_automatic_search_metadata(self):
        self.save()
        with store.connect() as db:db.execute('INSERT INTO settings VALUES(?,?)',(catalogue.PREFIX+'guide:bad','[]'))
        saved=catalogue.snapshot();self.assertFalse(saved.available)
        self.assertEqual(catalogue.classification(self.item,self.guides,self.zims,saved)['method'],'human')
        with self.assertRaises(HTTPException):catalogue.export()

    async def test_collection_labels_keep_ids_paths_filters_and_original_reference(self):
        stem='example-channel_en_energy_2026-01';(self.zims/(stem+'.zim')).write_bytes(b'Fictional archive')
        before=catalogue.collection_labels(stem,'Example Channel',self.guides,self.zims)
        catalogue.save('collection:'+stem,{'family':'Énergie familiale','variant':'Panneaux et batteries'},before['labels_revision'],self.guides,self.zims)
        book={'book':stem,'title':'Example Channel','language':'eng','fulltext':True}
        with patch.object(library,'books',AsyncMock(return_value=[book])),patch.object(library,'get',AsyncMock(return_value=(b'<rss><channel/></rss>','application/xml'))) as get:
            data=await inventory.inventory();found=await library.search('panneaux',collection='group:energiefamiliale')
        row=data['books'][0];self.assertEqual(row['family'],'Énergie familiale');self.assertEqual(row['variant'],'Panneaux et batteries')
        self.assertEqual(row['id'],stem);self.assertEqual(row['url'],'/content/'+stem+'/');self.assertEqual(row['archive_name'],stem+'.zim')
        self.assertEqual(found.coverage['collections_selected'],1);self.assertTrue(get.await_count)
        self.assertTrue(catalogue.matches_collection(book,'examplechannel',self.guides,self.zims))
        (self.zims/(stem+'.zim')).write_bytes(b'Another, changed archive edition')
        self.assertEqual(catalogue.collection_labels(stem,'Example Channel',self.guides,self.zims)['labels_status'],'source_changed')

    def test_grouping_is_generic_and_editorial_types_are_not_certified_from_titles(self):
        rows=[catalogue.automatic_labels('example-channel_en_'+topic+'_2026-01','Example Channel') for topic in ('energy','food')]
        self.assertEqual(rows[0]['family'],rows[1]['family']);self.assertNotEqual(rows[0]['variant'],rows[1]['variant'])
        self.assertEqual(catalogue.classification({'id':'guide:unknown','title':'Guide de construction'},self.guides,self.zims)['document_type'],'unknown')
        self.assertEqual(catalogue.classification({'id':'guide:unknown','title':'Quiz botanique'},self.guides,self.zims)['document_type'],'exercise')
        self.assertEqual(retrieval.domains({'title':'Histoire du traitement de l’eau'}),['resilience','culture'])

    def test_export_whitelists_metadata_and_does_not_include_other_settings_or_document_text(self):
        self.save()
        with store.connect() as db:
            db.execute('INSERT INTO settings VALUES(?,?)',('unrelated-private-setting','not-for-export'))
            key=catalogue.PREFIX+self.item['id'];raw=json.loads(db.execute('SELECT value FROM settings WHERE key=?',(key,)).fetchone()[0]);raw['unexpected']='not-for-export'
            db.execute('UPDATE settings SET value=? WHERE key=?',(json.dumps(raw),key))
        report=catalogue.export();encoded=json.dumps(report)
        self.assertEqual(len(report['records']),1);self.assertNotIn('not-for-export',encoded);self.assertNotIn(str(self.root),encoded);self.assertNotIn('Fictional fixture',encoded)

    async def test_local_archive_index_uses_renamed_group_without_catalogue_registration(self):
        try:from libzim.writer import Creator,Item,StringProvider,Hint
        except ImportError:self.skipTest('Lecteur d’archive optionnel absent.')
        class Article(Item):
            def get_path(self):return 'Mechanism'
            def get_title(self):return 'Pedal mechanism'
            def get_mimetype(self):return 'text/html'
            def get_contentprovider(self):return StringProvider('<html lang="en"><title>Pedal mechanism</title><body>Pedal mechanism. Fictional fixture.</body></html>')
            def get_hints(self):return {Hint.FRONT_ARTICLE:True}
        stem='example-channel_en_mechanisms_2026-01';path=self.zims/(stem+'.zim')
        with Creator(path).config_indexing(False,'eng') as creator:
            for key,value in {'Name':stem,'Title':'Example Channel','Language':'eng','Creator':'Synthetic test','Publisher':'SetupSurvie tests','Date':'2026-11-14','Description':'Fictional fixture'}.items():creator.add_metadata(key,value)
            creator.set_mainpath('Mechanism');creator.add_item(Article())
        archive_index.build_archive(path,store.ROOT/'archive-index')
        revision=catalogue.revision('collection:'+stem,self.guides,self.zims)
        catalogue.save('collection:'+stem,{'family':'Mécanismes','variant':'À pédales'},revision,self.guides,self.zims)
        found=await library.search('pedal mechanism',collection='group:mecanismes')
        self.assertEqual(found[0]['id'],'zim:'+stem+'/Mechanism');self.assertEqual(found[0]['match'],'local_index')
        self.assertEqual(await library.search('pedal mechanism',collection='group:autregroupe'),[])

    async def test_unreadable_metadata_does_not_remove_search_results(self):
        with store.connect() as db:db.execute('INSERT INTO settings VALUES(?,?)',(catalogue.PREFIX+'guide:bad','not json'))
        found=await library.search('mécanisme')
        self.assertEqual(found[0]['id'],self.item['id']);self.assertEqual(found.coverage['metadata_status'],'degraded');self.assertEqual(found.coverage['status'],'partial')

    def test_unsafe_paths_and_missing_sources_cannot_be_annotated(self):
        for identifier in ('guide:../private','zim:book/%2e%2e/private','collection:../private','guide:/etc/passwd','zim:book\\private'):
            with self.subTest(identifier=identifier),self.assertRaises(HTTPException):catalogue.canonical(identifier)
        with self.assertRaises(HTTPException) as error:self.save({'id':'guide:missing'})
        self.assertEqual(error.exception.status_code,404)
