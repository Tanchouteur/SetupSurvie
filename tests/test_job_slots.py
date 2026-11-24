"""Rows left 'running' by a crash must not fill the video job queues."""
import asyncio
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from pilot import caption_acquisition,captions,store,transcriptions


class StaleJobSlotTests(unittest.IsolatedAsyncioTestCase):
    async def test_only_jobs_alive_in_this_process_count_against_the_limit(self):
        with tempfile.TemporaryDirectory() as folder:
            for module in (captions,transcriptions,caption_acquisition):
                with self.subTest(module=module.__name__),patch.object(store,'ROOT',Path(folder)/module.__name__),patch.object(module,'ACTIVE',{}):
                    with module.connect() as db:
                        columns=[row[1] for row in db.execute('PRAGMA table_info(jobs)')]
                        for identifier,state in (('crashed','running'),('waiting','queued'),('alive','running')):
                            values={name:'' for name in columns};values.update(id=identifier,status=state)
                            db.execute(f"INSERT INTO jobs({','.join(columns)}) VALUES({','.join('?'*len(columns))})",[values[name] for name in columns])
                        db.commit()
                        self.assertEqual(module.busy(db),0)
                        alive=asyncio.create_task(asyncio.sleep(10));module.ACTIVE['alive']=alive
                        try:self.assertEqual(module.busy(db),1)
                        finally:alive.cancel()


if __name__=='__main__':unittest.main()
