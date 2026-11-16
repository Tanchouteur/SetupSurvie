"""Bounded local archive playback; simulated Kiwix, no real corpus."""
import unittest
from unittest.mock import patch

import httpx
from fastapi import HTTPException
from pilot import archive_videos


class Bytes(httpx.AsyncByteStream):
    def __init__(self,content):self.content=content;self.closed=False
    async def __aiter__(self):yield self.content
    async def aclose(self):self.closed=True


class ArchiveMediaTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.payload={'book':'fixture français','path':'media/clip one.webm','media':{'size_bytes':10,'mimetype':'video/webm'}}
        self.requests=[];self.streams=[];self.clients=[];self.reply=(200,{'Content-Length':'10','Content-Type':'video/webm'},b'0123456789')
        client_class=httpx.AsyncClient
        def handler(request):
            if isinstance(self.reply,Exception):raise self.reply
            self.requests.append(request);status,headers,content=self.reply
            stream=Bytes(content);self.streams.append(stream)
            return httpx.Response(status,headers=headers,stream=stream)
        def client(**options):
            result=client_class(transport=httpx.MockTransport(handler),**options);self.clients.append(result);return result
        for target,value in (('pilot.archive_videos.original_revision','fixture'),('pilot.archive_videos.httpx.AsyncClient',client)):
            change=patch(target,return_value=value) if isinstance(value,str) else patch(target,value)
            change.start();self.addCleanup(change.stop)

    async def read(self,range_header=None):
        response=await archive_videos.media_response(self.payload,range_header)
        body=b''.join([part async for part in response.body_iterator])
        self.assertTrue(self.streams[-1].closed);self.assertTrue(self.clients[-1].is_closed)
        return response,body

    async def test_full_and_partial_video_read_from_only_the_configured_local_reader(self):
        response,body=await self.read();self.assertEqual(body,b'0123456789');self.assertEqual(response.status_code,200)
        self.assertEqual(response.headers['content-length'],'10')
        self.assertIn('/content/fixture%20fran%C3%A7ais/media/clip%20one.webm',str(self.requests[-1].url))
        self.assertEqual(self.requests[-1].headers['accept-encoding'],'identity')
        self.reply=(206,{'Content-Range':'bytes 3-6/10','Content-Length':'4'},b'3456')
        response,body=await self.read('bytes=3-6');self.assertEqual(response.status_code,206);self.assertEqual(body,b'3456')
        self.assertEqual(self.requests[-1].headers['range'],'bytes=3-6')
        self.reply=(206,{'Content-Range':'bytes 8-9/10'},b'89')
        self.assertEqual((await self.read('bytes=-2'))[1],b'89')

    async def test_bad_ranges_never_contact_the_reader(self):
        for header in ('bytes=1-2,4-5','bytes=12-','bytes=5-3','bytes=-0','whatever','bytes='):
            with self.subTest(header=header),self.assertRaises(HTTPException) as error:await self.read(header)
            self.assertEqual(error.exception.status_code,416)
        self.assertEqual(self.requests,[])

    async def test_redirect_missing_range_mismatched_size_or_html_cannot_become_video(self):
        for reply in ((302,{'Location':'https://example.invalid/remote'},b''),(200,{'Content-Type':'text/html'},b'0123456789'),
                      (206,{'Content-Range':'bytes 3-6/100'},b'3456'),(206,{'Content-Length':'4'},b'3456'),
                      (200,{'Content-Length':'1'},b'0'),(200,{'Content-Encoding':'gzip'},b'0123456789')):
            self.reply=reply
            with self.subTest(reply=reply),self.assertRaises(HTTPException) as error:await self.read('bytes=3-6')
            self.assertEqual(error.exception.status_code,503);self.assertTrue(self.streams[-1].closed);self.assertTrue(self.clients[-1].is_closed)

    async def test_short_body_or_overflow_closes_both_reader_and_client(self):
        for content in (b'short',b'0123456789extra'):
            self.reply=(200,{},content)
            with self.subTest(content=content),self.assertRaises(httpx.RemoteProtocolError):await self.read()
            self.assertTrue(self.streams[-1].closed);self.assertTrue(self.clients[-1].is_closed)

    async def test_archive_change_and_reader_failure_are_explained_before_playback(self):
        with patch.object(archive_videos,'original_revision',side_effect=['fixture',None]),self.assertRaises(HTTPException) as error:await self.read()
        self.assertEqual(error.exception.status_code,409);self.assertTrue(self.clients[-1].is_closed)
        self.reply=httpx.ConnectError('offline')
        with self.assertRaises(HTTPException) as error:await self.read()
        self.assertEqual(error.exception.status_code,503);self.assertTrue(self.clients[-1].is_closed)
        with patch.object(archive_videos,'original_revision',return_value=None),self.assertRaises(HTTPException) as error:await self.read()
        self.assertEqual(error.exception.status_code,409)
