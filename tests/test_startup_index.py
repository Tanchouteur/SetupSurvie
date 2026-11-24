import asyncio
import threading
import unittest
from types import SimpleNamespace
from unittest import mock

from pilot import app as gateway


class StartupIndexTest(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        gateway.DEGRADED.clear()
        self.app = SimpleNamespace(state=SimpleNamespace())

    def tearDown(self):
        gateway.DEGRADED.clear()

    async def test_immediate_success_clears_degraded(self):
        gateway.DEGRADED['index'] = True
        with mock.patch.object(gateway.library, 'index_guides'):
            await gateway.prepare_initial_index(self.app)
        self.assertTrue(self.app.state.initial_index_task.done())
        self.assertNotIn('index', gateway.DEGRADED)

    async def test_timeout_then_success_clears_degraded(self):
        started = threading.Event()
        release = threading.Event()

        def index(*, automatic):
            started.set()
            release.wait(5)

        try:
            with mock.patch.object(gateway.library, 'index_guides', side_effect=index), \
                    mock.patch.object(gateway, 'STARTUP_FEATURE_TIMEOUT', 0.05):
                await gateway.prepare_initial_index(self.app)
                self.assertTrue(started.is_set())
                self.assertTrue(gateway.DEGRADED['index'])
                self.assertFalse(self.app.state.initial_index_task.done())
                release.set()
                await asyncio.wait_for(self.app.state.initial_index_task, 2)
                self.assertNotIn('index', gateway.DEGRADED)
        finally:
            release.set()

    async def test_exception_is_consumed_and_marks_degraded(self):
        with mock.patch.object(gateway.library, 'index_guides', side_effect=RuntimeError('private details')), \
                self.assertLogs(gateway.__name__, level='WARNING') as logs:
            await gateway.prepare_initial_index(self.app)
        self.assertTrue(gateway.DEGRADED['index'])
        self.assertIsNone(self.app.state.initial_index_task.exception())
        self.assertNotIn('private details', '\n'.join(logs.output))
