"""Compressed archive indexes (0.88.0): same results, smaller file, safe conversion."""
import json
import os
from contextlib import closing
from pathlib import Path
import sqlite3
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from pilot import archive_index, category_index  # noqa: E402

WORDS = ('eau potable filtre charbon sable gravier ébullition chlore source puits pluie citerne '
         'feu bois foyer allumage silex braise abri toit bâche corde nœud tente isolation '
         'jardin semis compost potager tomate pomme terre arrosage paillage récolte graine').split()


def article_text(number):
    # Varied, accented and long enough to be split into several rows.
    words = [WORDS[(number * 7 + i * (number % 5 + 1)) % len(WORDS)] for i in range(40 + number % 90)]
    return (' '.join(words) + ' ') * (1 + number % 4)


def plan(query):
    return SimpleNamespace(groups=[query], collection='', fts=lambda relaxed=False: query)


def legacy_index(path, articles=300, domains=True):
    """The format written before 0.88.0: the text lives in the FTS table."""
    with closing(sqlite3.connect(path)) as db, db:
        db.execute('CREATE TABLE metadata(key TEXT PRIMARY KEY,value TEXT)')
        db.execute('INSERT INTO metadata VALUES(?,?)', ('source', json.dumps(
            {'book': 'essai_fr', 'title': 'Essai', 'language': 'fra', 'fingerprint': '2:u:s:1:1'})))
        db.execute("INSERT INTO metadata VALUES('articles',?)", (str(articles),))
        extra = ',domains UNINDEXED' if domains else ''
        db.execute(f"CREATE VIRTUAL TABLE articles USING fts5(path UNINDEXED,title,text,language UNINDEXED{extra},{archive_index.TOKENIZE})")
        for number in range(articles):
            text = article_text(number)
            choice = [['resilience'], ['culture'], ['resilience', 'culture'], []][number % 4]
            suffix = (json.dumps(choice),) if domains else ()
            language = 'fr' if number % 6 else 'en'
            for start in range(0, len(text), 2200):
                db.execute(f"INSERT INTO articles VALUES({','.join('?' * (4 + domains))})",
                           (f'A/Article_{number}', f'Article {number} {WORDS[number % len(WORDS)]}',
                            text[start:start + 2400], language, *suffix))
        db.execute("INSERT INTO articles(articles) VALUES('optimize')")


QUERIES = ('eau', 'filtre OR charbon', '"eau potable"', 'feu AND bois', 'jardin NOT tomate',
           'ebullition', 'récolte', 'abri OR toit OR bâche', 'puits*', 'citerne AND pluie AND chlore')


class CompressedIndexTest(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.root = Path(self.directory.name)
        self.index = self.root / 'abc.sqlite'

    def tearDown(self):
        self.directory.cleanup()

    def results(self, **options):
        found = {}
        for query in QUERIES:
            for category in (None, 'resilience', 'culture'):
                for language in ('', 'fra'):
                    rows = archive_index.search(self.root, plan(query), language, limit=15,
                                                category=category, index_paths=[self.index], **options)
                    self.assertEqual(rows.coverage['failed'], 0, query)
                    found[query, category, language] = [
                        (row['id'], row['title'], row['language'], row['excerpt'], row['_text'],
                         row.get('_indexed_domains')) for row in rows]
        return found

    def test_conversion_keeps_every_result_identical_and_shrinks_the_file(self):
        legacy_index(self.index)
        before, size = self.results(), self.index.stat().st_size
        self.assertTrue(any(before.values()))
        self.assertLess(archive_index.compress(self.index, reserve=0), size)
        with archive_index.connect(self.index, True) as db:
            self.assertTrue(archive_index.is_compressed(db))
            self.assertEqual(json.loads(db.execute("SELECT value FROM metadata WHERE key='source'").fetchone()[0])['book'], 'essai_fr')
        self.assertEqual(self.results(), before)
        self.assertIsNone(archive_index.compress(self.index, reserve=0))  # already converted
        self.assertFalse(self.index.with_suffix('.compressing').exists())

    def test_index_without_domains_and_ifixit_language_rule_stay_identical(self):
        legacy_index(self.index, articles=120, domains=False)
        with closing(sqlite3.connect(self.index)) as db, db:
            db.execute("UPDATE metadata SET value=? WHERE key='source'", (json.dumps(
                {'book': 'ifixit_fr_all_2026-03', 'title': 'iFixit', 'fingerprint': '2:u:1:1'}),))
        before = {query: archive_index.search(self.root, plan(query), 'fra', index_paths=[self.index]) for query in QUERIES}
        archive_index.compress(self.index, reserve=0)
        after = {query: archive_index.search(self.root, plan(query), 'fra', index_paths=[self.index]) for query in QUERIES}
        self.assertEqual(after, before)

    def test_pause_and_lack_of_space_keep_the_old_index_published(self):
        legacy_index(self.index, articles=60)
        original = self.index.read_bytes()
        cancel = self.root / 'cancel'
        cancel.touch()
        with self.assertRaises(archive_index.Paused):
            archive_index.compress(self.index, cancel=cancel, reserve=0, batch=10)
        with self.assertRaises(archive_index.StorageReserve):
            archive_index.compress(self.index, reserve=10**18)
        self.assertEqual(self.index.read_bytes(), original)
        self.assertFalse(self.index.with_suffix('.compressing').exists())

    def test_republished_index_during_conversion_is_not_overwritten(self):
        legacy_index(self.index, articles=60)
        real = archive_index._insert

        def republish(*args):
            real(*args)
            os.utime(self.index, ns=(1, 1))  # a new build was published meanwhile
        with mock.patch.object(archive_index, '_insert', republish):
            with self.assertRaises(archive_index.ArchiveChanged):
                archive_index.compress(self.index, reserve=0)
        with archive_index.connect(self.index, True) as db:
            self.assertFalse(archive_index.is_compressed(db))

    def test_prepare_step_converts_ready_indexes_and_updates_their_record(self):
        legacy_index(self.index, articles=60)
        record = self.root / 'record.json'
        record.write_text(json.dumps({'phase': 'completed', 'bytes': self.index.stat().st_size}), encoding='utf-8')
        source = SimpleNamespace(stem='essai_fr', name='essai_fr.zim')
        report, failures, saves = {}, [], []
        with mock.patch.object(category_index, '_record', return_value=record):
            category_index.compress_ready(self.root, [source], {'essai_fr': self.index}, report, failures,
                                          lambda: saves.append(dict(report)), reserve=0)
        self.assertEqual(failures, [])
        self.assertEqual(json.loads(record.read_text(encoding='utf-8'))['bytes'], self.index.stat().st_size)
        self.assertEqual(report['bytes'], self.index.stat().st_size)
        self.assertNotIn('step', report)
        self.assertEqual(saves[0]['step'], 'compression')

    def test_prepare_step_reports_a_failure_without_stopping_the_index(self):
        self.index.write_bytes(b'not a database')
        report, failures = {}, []
        source = SimpleNamespace(stem='essai_fr', name='essai_fr.zim')
        category_index.compress_ready(self.root, [source], {'essai_fr': self.index}, report, failures, lambda: None, reserve=0)
        self.assertEqual(failures[0]['step'], 'compression')


if __name__ == '__main__':
    unittest.main()
