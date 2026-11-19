import asyncio
import json
import unittest
from unittest.mock import patch

import httpx
from fastapi import HTTPException

from pilot.model_downloads import ModelDownloads


class Events(httpx.AsyncByteStream):
    def __init__(self, rows, gate=None):
        self.rows = rows
        self.gate = gate
        self.entered = asyncio.Event()
        self.closed = False

    async def __aiter__(self):
        for row in self.rows:
            yield (json.dumps(row) + '\n').encode()
        self.entered.set()
        if self.gate:
            await self.gate.wait()

    async def aclose(self):
        self.closed = True


class ModelDownloadTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.service = ModelDownloads('http://fixture', {
            'profiles': [
                {'model': 'fixture:small', 'category': 'recommended', 'name': 'Rapide · Petit'},
                {'model': 'fixture:small', 'category': 'recommended', 'name': 'Long · Petit'},
                {'model': 'fixture:large', 'category': 'comparison', 'name': 'Comparer · Grand'},
            ],
            'download_sizes': {'fixture:small': 100, 'fixture:large': 1000},
        })
        self.installed = []
        self.pulls = []
        self.offline = False
        self.events = Events([])
        client = httpx.AsyncClient
        mock = patch('pilot.model_downloads.httpx.AsyncClient',
                     side_effect=lambda **kwargs: client(transport=httpx.MockTransport(self.ollama), **kwargs))
        mock.start()
        self.addCleanup(mock.stop)

    def ollama(self, request):
        if request.url.path == '/api/tags':
            if self.offline:
                raise httpx.ConnectError('offline', request=request)
            return httpx.Response(200, json={'models': self.installed})
        self.assertEqual(request.url.path, '/api/pull')
        self.pulls.append(json.loads(request.content))
        return httpx.Response(200, stream=self.events)

    async def test_inventory_deduplicates_modes_and_reuses_installed_model(self):
        self.installed = [{'name': 'fixture:small', 'size': 101}]
        result = await self.service.status()
        self.assertEqual(result['models'], [
            {'model': 'fixture:small', 'category': 'recommended', 'name': 'Petit', 'installed': True, 'size': 101},
            {'model': 'fixture:large', 'category': 'comparison', 'name': 'Grand', 'installed': False, 'size': 1000},
        ])
        self.assertEqual((await self.service.start('fixture:small'))['state'], 'complete')
        with self.assertRaises(HTTPException) as unsupported:
            await self.service.start('elsewhere:cloud')
        self.assertEqual(unsupported.exception.status_code, 400)
        self.assertEqual(self.pulls, [])

    async def test_active_download_aggregates_layers_and_can_be_cancelled(self):
        self.events = Events([
            {'digest': 'one', 'completed': 10, 'total': 20},
            {'digest': 'one', 'completed': 20, 'total': 20},
            {'digest': 'two', 'completed': 30, 'total': 60},
        ], gate=asyncio.Event())
        job = await self.service.start('fixture:small')
        await asyncio.wait_for(self.events.entered.wait(), 1)
        self.assertEqual((await self.service.start('fixture:small'))['id'], job['id'])
        with self.assertRaises(HTTPException) as conflict:
            await self.service.start('fixture:large')
        self.assertEqual(conflict.exception.status_code, 409)
        self.assertEqual((await self.service.status())['download']['completed'], 50)
        with self.assertRaises(HTTPException) as stale:
            await self.service.cancel('old')
        self.assertEqual(stale.exception.status_code, 409)
        self.assertEqual((await self.service.cancel(job['id']))['state'], 'cancelled')
        self.assertTrue(self.events.closed)
        self.assertEqual(self.pulls, [{'model': 'fixture:small', 'stream': True}])

    async def test_download_can_recover_after_registry_error(self):
        self.events = Events([{'error': 'no space left on device: internal file path'}])
        await self.service.start('fixture:small')
        await self.service.task
        failed = (await self.service.status())['download']
        self.assertEqual(failed['state'], 'error')
        self.assertIn('disque', failed['message'])
        self.assertNotIn('internal', failed['message'])
        self.events = Events([{'status': 'success'}])
        await self.service.start('fixture:small')
        await self.service.task
        self.assertEqual((await self.service.status())['download']['state'], 'complete')

    async def test_unavailable_engine_leaves_inventory_unknown(self):
        self.offline = True
        status = await self.service.status()
        self.assertFalse(status['available'])
        self.assertIsNone(status['models'][0]['installed'])
        with self.assertRaises(HTTPException) as offline:
            await self.service.start('fixture:small')
        self.assertEqual(offline.exception.status_code, 503)
