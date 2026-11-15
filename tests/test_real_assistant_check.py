"""The optional real-model recipe must never accidentally use the rented GPU."""
import json
import unittest
import httpx
from real_assistant_check import TestTransport


class RealTransportTests(unittest.IsolatedAsyncioTestCase):
    async def test_generation_and_preload_are_cpu_only_without_changing_selected_model(self):
        requests=[]
        def handler(request):requests.append(json.loads(request.content));return httpx.Response(200,json={'done':True})
        transport=TestTransport(640);await transport.inner.aclose();transport.inner=httpx.MockTransport(handler)
        async with httpx.AsyncClient(transport=transport) as client:
            for messages in ([],[{'role':'user','content':'Fictional question'}]):
                await client.post('http://127.0.0.1:11434/api/chat',json={'model':'fixture:local','messages':messages,'options':{'num_ctx':16384,'num_predict':4096}})
        for request in requests:
            self.assertEqual(request['model'],'fixture:local');self.assertEqual(request['options'],{'num_ctx':16384,'num_predict':640,'num_gpu':0,'num_thread':2})
            self.assertEqual(request['keep_alive'],'15s')
        self.assertEqual(requests[0]['messages'],[])

    async def test_metadata_request_is_not_modified(self):
        seen=[]
        def handler(request):seen.append((request.method,request.url.path));return httpx.Response(200,json={'models':[]})
        transport=TestTransport(640);await transport.inner.aclose();transport.inner=httpx.MockTransport(handler)
        async with httpx.AsyncClient(transport=transport) as client:await client.get('http://127.0.0.1:11434/api/ps')
        self.assertEqual(seen,[('GET','/api/ps')])

    async def test_gpu_offload_is_only_applied_when_explicitly_selected(self):
        requests=[]
        def handler(request):requests.append(json.loads(request.content));return httpx.Response(200,json={'done':True})
        transport=TestTransport(640,gpu_layers=6,threads=4);await transport.inner.aclose();transport.inner=httpx.MockTransport(handler)
        async with httpx.AsyncClient(transport=transport) as client:
            await client.post('http://127.0.0.1:11434/api/chat',json={'model':'fixture','messages':[]})
        self.assertEqual(requests[0]['options'],{'num_gpu':6,'num_thread':4})


if __name__=='__main__':unittest.main()
