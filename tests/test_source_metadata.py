"""Bibliographic metadata and backward compatibility; tiny synthetic documents only."""
import asyncio
import json
from pathlib import Path
import sqlite3
import tempfile
import unittest
from unittest.mock import AsyncMock,patch

from pilot import library,source_metadata,store


class MetadataTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name);self.guides=self.root/'guides';self.guides.mkdir()
        self.state=patch.object(store,'ROOT',self.root/'state');self.state.start();self.addCleanup(self.state.stop)
        self.path=patch.object(library,'GUIDES',self.guides);self.path.start();self.addCleanup(self.path.stop)

    def test_legacy_database_is_extended_without_changing_five_column_metadata_or_history(self):
        store.ROOT.mkdir()
        with sqlite3.connect(store.ROOT/'pilot.db') as db:
            db.execute('CREATE TABLE guide_meta(path TEXT PRIMARY KEY,title TEXT,language TEXT,provenance TEXT,licence TEXT)')
            db.execute('INSERT INTO guide_meta VALUES(?,?,?,?,?)',('old.fr.txt','Ancienne notice','fr','Organisme — édition 2009',''))
        store.init();store.init()
        (self.guides/'old.fr.txt').write_text('La boîte contient une bouteille.')
        library.index_guides()
        with store.connect() as db:
            self.assertEqual(len(db.execute('PRAGMA table_info(guide_meta)').fetchall()),5)
            db.execute('INSERT INTO guide_meta VALUES(?,?,?,?,?)',('still-compatible','T','fr','',''))
            db.execute('INSERT INTO conversations VALUES(?,?,?,?)',('c','owner','Histoire conservée',0))
            db.execute('INSERT INTO messages(conversation_id,role,content,sources,created) VALUES(?,?,?,?,?)',('c','assistant','Ancienne réponse','[{"id":"guide:old.fr.txt","number":1,"title":"Ancienne notice"}]',0))
        source=asyncio.run(library.source('guide:old.fr.txt'))
        self.assertEqual(source['edition'],'2009')
        self.assertEqual(source['document_date'],'')
        self.assertEqual(source['collected_at'],'')
        self.assertNotIn('document_date',store.messages('c')[0]['sources'][0])

    def test_dates_survive_reindex_and_reach_search_and_read_without_using_file_mtime(self):
        store.init()
        (self.guides/'notice.fr.txt').write_text('Boîte fictive. Volume : 40 litres.')
        item={'path':'notice.fr.txt','title':'Notice BETA','language':'fr','document_date':'2010-05',
              'edition':'Deuxième édition','collected_at':'2026-11-12','provenance':'Fixture','licence':'Test'}
        (self.guides/'metadata.json').write_text(json.dumps([item]))
        with patch.object(library,'books',AsyncMock(return_value=[])):
            library.index_guides();library.index_guides()
            found=asyncio.run(library.search('volume'))[0]
        source=asyncio.run(library.source(found['id']))
        for key in ('document_date','edition','collected_at'):
            self.assertEqual(found[key],item[key]);self.assertEqual(source[key],item[key])
        # An old seed without dates must not erase facts already preserved in the DB.
        old={k:v for k,v in item.items() if k not in source_metadata.FIELDS}
        old['provenance']='Fixture — édition ancienne'
        (self.guides/'metadata.json').write_text(json.dumps([old]))
        library.index_guides()
        self.assertEqual(asyncio.run(library.source(found['id']))['document_date'],'2010-05')
        self.assertEqual(asyncio.run(library.source(found['id']))['edition'],'Deuxième édition')

    def test_catalogue_archive_update_is_never_used_as_article_publication_date(self):
        xml=b'''<feed xmlns="http://www.w3.org/2005/Atom"><entry><title>Collection test</title><language>fra</language><updated>2026-05-02T08:00:00Z</updated><link type="text/html" href="/content/test"/></entry></feed>'''
        with patch.object(library,'get',AsyncMock(return_value=(xml,'application/xml'))):
            books=asyncio.run(library.books())
        self.assertEqual(books[0]['archive_date'],'2026-05-02')
        with patch.object(library,'books',AsyncMock(return_value=books)),patch.object(library,'get',AsyncMock(return_value=(b'<title>Article</title><p>Texte ancien.</p>','text/html'))):
            source=asyncio.run(library.source('zim:test/Article'))
        self.assertEqual(source['document_date'],'')
        self.assertEqual(source['archive_date'],'2026-05-02')

    def test_invalid_or_missing_dates_are_not_invented(self):
        for value in ('2026-02-30','2026-13','0000','inconnue',2020,None):
            self.assertEqual(source_metadata.date_value(value),'')
        self.assertEqual(source_metadata.date_value('2024-02-29'),'2024-02-29')
        self.assertEqual(source_metadata.date_value('2026-02'),'2026-02')
        item=source_metadata.metadata({'provenance':'Archive collectée en 2026 ; fichier modifié en 2025'})
        self.assertTrue(all(not value for value in item.values()))


if __name__=='__main__':unittest.main()
