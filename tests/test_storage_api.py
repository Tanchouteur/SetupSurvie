"""Portal side of the disk analysis: a read for every profile, a new scan for Famille."""
import unittest
from unittest.mock import AsyncMock, patch

import httpx
from pilot import app as gateway, operations


class StorageApiTests(unittest.IsolatedAsyncioTestCase):
    async def test_every_profile_reads_but_only_family_starts_a_scan(self):
        headers = {'Origin': 'http://test'}
        report = {'schema': 1, 'available': True, 'scanning': False, 'report': None, 'disks': []}
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=gateway.app), base_url='http://test') as client:
            gateway.app.dependency_overrides[gateway.user] = lambda: {'id': 'reader', 'role': 'reader'}
            try:
                with patch.object(operations, 'storage', AsyncMock(return_value=report)):
                    response = await client.get('/api/storage')
                self.assertEqual((response.status_code, response.json()), (200, report))
                with patch.object(operations, 'storage_scan', AsyncMock(return_value={'accepted': True})) as scan:
                    self.assertEqual((await client.post('/api/admin/storage/scan', headers=headers)).status_code, 403)
                    scan.assert_not_called()
                    gateway.app.dependency_overrides[gateway.user] = lambda: {'id': 'family', 'role': 'admin'}
                    response = await client.post('/api/admin/storage/scan', headers=headers)
                    self.assertEqual((response.status_code, response.json()), (200, {'accepted': True}))
                    scan.assert_awaited_once()
            finally:
                gateway.app.dependency_overrides.clear()

    async def test_missing_controller_is_reported_without_error(self):
        with patch.object(operations, 'TOKEN', ''):
            self.assertEqual(await operations.storage(), {'available': False, 'reason': 'not_configured'})
        responses = {'/storage': httpx.Response(404, json={'detail': 'Route inconnue.'})}
        transport = httpx.MockTransport(lambda request: responses[request.url.path])
        real = httpx.AsyncClient
        with patch.object(operations, 'TOKEN', 'fixture'), \
                patch.object(operations.httpx, 'AsyncClient', lambda **kwargs: real(transport=transport, **kwargs)):
            self.assertEqual(await operations.storage(), {'available': False, 'reason': 'controller_update_required'})
            responses['/storage'] = httpx.Response(200, json={'schema': 1, 'scanning': True, 'report': None, 'disks': []})
            self.assertTrue((await operations.storage())['available'])
            responses['/storage/scan'] = httpx.Response(409, json={'detail': 'Transfert en cours.'})
            with self.assertRaises(Exception) as error:
                await operations.storage_scan()
            self.assertEqual(error.exception.status_code, 409)


if __name__ == '__main__':
    unittest.main()
