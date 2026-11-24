"""Cancellation of local disk reads, without Kiwix or a real archive."""
import asyncio
import threading
import unittest

from pilot import kiwix_queries


class DiskIoCancellationTests(unittest.TestCase):
    def test_timeout_wins_over_a_failure_after_cancellation_and_waits_for_the_thread(self):
        finished=threading.Event()
        def slow_failure():
            threading.Event().wait(.2);finished.set()
            raise ValueError('fixture failure after the deadline')
        async def run():
            with self.assertRaises(TimeoutError):
                await asyncio.wait_for(kiwix_queries.disk_io(slow_failure),.05)
        asyncio.run(run())
        # The SQLite thread must be finished before the caller continues.
        self.assertTrue(finished.is_set())

    def test_failure_before_any_cancellation_is_reported_as_is(self):
        def failure():raise ValueError('fixture failure')
        async def run():
            with self.assertRaises(ValueError):await kiwix_queries.disk_io(failure)
        asyncio.run(run())


if __name__=='__main__':unittest.main()
