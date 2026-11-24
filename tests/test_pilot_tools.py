import asyncio
from pathlib import Path
import tempfile
import time
import unittest
from unittest.mock import patch

from fastapi import HTTPException
from pilot import engine,library,store


class ToolBoundaryTests(unittest.TestCase):
    def test_source_traversal_and_nested_encoding_rejected(self):
        for value in ['zim:book/../secret','zim:book/%2e%2e/secret','zim:book/%252e%252e/secret','zim:book/%252525252e%252525252e/secret','zim:book/..\\secret','https://example.com/']:
            with self.assertRaises(HTTPException):library.safe_zim_path(value)
        self.assertEqual(library.safe_zim_path('zim:book/Loi_d%27Ohm'),"book/Loi_d'Ohm")

    def test_exact_calculation_and_unit_safety(self):
        self.assertEqual(library.calculate('600 % 18')['value'],6)
        self.assertEqual(library.calculate('12 * 100 * 0.8 * 0.8')['exact'],'768')
        self.assertEqual(library.convert(2.5,'kWh','MJ')['value'],9)
        for value in ["__import__('os').getcwd()",'2 ** 1000000','True + 1','[1]*10000000','1e999','1/0']:
            with self.assertRaises(ValueError):library.calculate(value)
        for value in ['1/0','7 % 0','7 // 0','0 ** -1']:
            with self.assertRaisesRegex(ValueError,'zéro'):library.calculate(value)
        for args in [(1,'kg','L'),(float('inf'),'m','cm'),(True,'m','cm')]:
            with self.assertRaises(ValueError):library.convert(*args)


class CancelTests(unittest.IsolatedAsyncioTestCase):
    async def test_cancel_before_coroutine_start_releases_active_entry(self):
        with tempfile.TemporaryDirectory() as root,patch.object(store,'ROOT',Path(root)):
            store.init()
            with store.connect() as db:
                db.execute('INSERT INTO conversations VALUES(?,?,?,?)',('c','u','t',time.time()))
                db.execute('INSERT INTO jobs(id,user_id,conversation_id,mode,status,created,updated) VALUES(?,?,?,?,?,?,?)',('j','u','c','rapide','queued',time.time(),time.time()))
            engine.launch('j','u','c','rapide');task=engine.ACTIVE['j'];engine.cancel('j')
            await asyncio.gather(task,return_exceptions=True);await asyncio.sleep(0)
            self.assertNotIn('j',engine.ACTIVE)
            with store.connect() as db:self.assertEqual(db.execute('SELECT status FROM jobs WHERE id="j"').fetchone()[0],'cancelled')


if __name__=='__main__':unittest.main()
