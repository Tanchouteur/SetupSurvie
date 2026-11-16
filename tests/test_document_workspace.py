import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from pilot import store,document_workspace


class DocumentWorkspaceTests(unittest.TestCase):
    def test_work_is_scoped_to_profile_and_original_without_returning_private_parts(self):
        with tempfile.TemporaryDirectory() as folder,patch.object(store,'ROOT',Path(folder)):
            store.init()
            with store.connect() as db:
                for c,owner in [('a','alice'),('b','bob')]:
                    db.execute('INSERT INTO conversations VALUES(?,?,?,?)',(c,owner,'Discussion',1))
                for i,c,owner,source in [('one','a','alice','guide:book.en.pdf'),('page','a','alice','guide:book.en.pdf#page=4'),('other','a','alice','guide:book2.en.pdf'),('private','b','bob','guide:book.en.pdf')]:
                    db.execute('INSERT INTO translations VALUES(?,?,?,?,?,?,?,?,?,?)',(i,owner,c,source,'Livre','rapide','paused',None,1,1))
                db.execute('INSERT INTO translation_parts VALUES(?,?,?,?,?,?,?)',('one',0,1,'PRIVATE SOURCE','PRIVATE DRAFT','done','fake'))
            data=document_workspace.work('alice','guide:book.en.pdf#page=9')
            self.assertEqual({row['id'] for row in data['translations']},{'one','page'})
            self.assertNotIn('PRIVATE',str(data));self.assertNotIn('parts',str(data))

            recent=document_workspace.recent('alice')
            self.assertEqual({row['id'] for row in recent['translations']},{'one','page','other'})
            self.assertNotIn('PRIVATE',str(recent));self.assertNotIn('parts',str(recent))
