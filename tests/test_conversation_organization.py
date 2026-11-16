"""Folders are additive and cannot move or reveal another profile's history."""
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from fastapi import HTTPException
from pilot import store,conversation_organization as organization


class ConversationOrganizationTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.patch=patch.object(store,'ROOT',Path(self.temp.name));self.patch.start();self.addCleanup(self.patch.stop)
        store.init()
        with store.connect() as db:
            db.execute('INSERT INTO conversations VALUES(?,?,?,?)',('a','alice','Jardin',1))
            db.execute('INSERT INTO conversations VALUES(?,?,?,?)',('b','bob','Autre profil',2))
            db.execute('INSERT INTO messages(conversation_id,role,content,sources,created) VALUES(?,?,?,?,?)',('a','user','Arroser les semis','[]',1))

    def test_folders_move_rename_and_delete_keep_messages_and_old_table_shape(self):
        folder=organization.save_folder('alice','Potager')
        organization.move('alice','a',folder['id'])
        self.assertEqual(organization.listing('alice',folder=folder['id'])['conversations'][0]['id'],'a')
        organization.save_folder('alice','Jardin familial',folder['id'])
        self.assertEqual(organization.folders('alice')['folders'][0]['count'],1)
        organization.rename('alice','a','Semis de printemps')
        self.assertEqual(organization.listing('alice',q='semis')['conversations'][0]['title'],'Semis de printemps')
        organization.delete_folder('alice',folder['id'])
        self.assertEqual(organization.listing('alice',folder='unfiled')['conversations'][0]['id'],'a')
        self.assertEqual(len(store.messages('a')),1)
        with store.connect() as db:self.assertEqual(len(db.execute('PRAGMA table_info(conversations)').fetchall()),4)

    def test_profile_ownership_and_literal_search(self):
        folder=organization.save_folder('alice','Personnel')
        for action in [lambda:organization.move('alice','b',folder['id']),lambda:organization.move('bob','b',folder['id']),lambda:organization.rename('bob','a','Wrong'),lambda:organization.delete_folder('bob',folder['id'])]:
            with self.assertRaises(HTTPException) as error:action()
            self.assertEqual(error.exception.status_code,404)
        self.assertEqual(organization.folders('bob')['folders'],[])
        self.assertEqual(organization.listing('alice',q='Autre profil')['conversations'],[])
        self.assertEqual(organization.listing('alice',q='%')['conversations'],[])
        self.assertEqual(organization.listing('alice',q='Arroser')['conversations'][0]['id'],'a')

    def test_pagination_can_reach_old_conversations(self):
        with store.connect() as db:
            db.executemany('INSERT INTO conversations VALUES(?,?,?,?)',[(str(i),'alice','Titre '+str(i),i+3) for i in range(105)])
        first=organization.listing('alice');last=organization.listing('alice',offset=100)
        self.assertTrue(first['has_more']);self.assertFalse(last['has_more'])
        self.assertEqual(len(first['conversations'])+len(last['conversations']),106)
