"""Actual seek/read semantics on a simulated local service, no model or corpus."""
import io
import unittest
from unittest.mock import patch
import uuid

import httpx
from pilot import archive_media


def response(status,*,headers=None,content=b''):
    return httpx.Response(status,headers={'Content-Length':str(len(content)),**(headers or {})},stream=httpx.ByteStream(content))


class ArchiveMediaTests(unittest.TestCase):
    def setUp(self):
        self.data=bytes(range(256))*5000;self.calls=[];self.identity=str(uuid.uuid4());self.mode='normal';self.closed=[]
        self.source={'endpoint':'http://kiwix:8080','book':'cours français','path':'media/cours film.mp4','size':len(self.data),'uuid':self.identity}

    def handler(self,request):
        self.calls.append(request)
        self.assertEqual(request.url.host,'kiwix');self.assertEqual(request.headers['accept-encoding'],'identity')
        if '/catalog/' in request.url.path:
            identity='00000000-0000-0000-0000-000000000000' if self.mode=='old_edition' else self.identity
            book='another-book' if self.mode=='wrong_book' else 'cours%20fran%C3%A7ais'
            data=('<entry><id>urn:uuid:'+identity+'</id><link type="text/html" href="/content/'+book+'"/></entry>').encode()
            if self.mode=='redirect_catalogue':return response(302,headers={'Location':'https://external.invalid/'})
            if self.mode=='oversize_catalogue':data=b'x'*(archive_media.MAX_CATALOGUE+1)
            return response(200,content=data)
        first,last=map(int,request.headers['range'].removeprefix('bytes=').split('-'))
        headers={'Content-Range':f'bytes {first}-{last}/{len(self.data)}','Content-Type':'video/mp4','ETag':'"edition-1"'}
        data=self.data[first:last+1]
        if self.mode=='redirect_media':return response(302,headers={'Location':'https://external.invalid/'})
        if self.mode=='offline':raise httpx.ConnectError('local unavailable')
        if self.mode=='no_ranges':return response(200,content=self.data)
        if self.mode=='bad_total':headers['Content-Range']=f'bytes {first}-{last}/{len(self.data)+1}'
        if self.mode=='bad_mime':headers['Content-Type']='text/html'
        if self.mode=='new_etag':headers['ETag']='"edition-2"'
        if self.mode=='short':data=data[:-1]
        if self.mode=='long':data+=b'overflow'
        return response(206,headers=headers,content=data)

    def reader(self):return archive_media.RangeReader(self.source,transport=httpx.MockTransport(self.handler))

    def test_seeks_reuse_bounded_cache_and_can_jump_to_end_without_downloading_the_video(self):
        with self.reader() as stream:
            self.assertTrue(stream.seekable());self.assertTrue(stream.readable())
            self.assertEqual(stream.read(12),self.data[:12]);self.assertEqual(stream.read(31),self.data[12:43])
            self.assertEqual(len(self.calls),2);self.assertEqual(stream.metrics['cache_hits'],1)
            self.assertEqual(stream.seek(-37,io.SEEK_END),len(self.data)-37);self.assertEqual(stream.read(),self.data[-37:])
            self.assertEqual(stream.read(1),b'');self.assertEqual(stream.readinto(bytearray(5)),0)
            stream.seek(0);buffer=bytearray(8);self.assertEqual(stream.readinto(buffer),8);self.assertEqual(bytes(buffer),self.data[:8])
            self.assertLess(stream.metrics['media_bytes'],len(self.data));self.assertLessEqual(stream.metrics['largest_range_bytes'],archive_media.BLOCK)
            self.assertIn('/media/cours%20film.mp4',str(self.calls[1].url))
            self.assertEqual(self.calls[2].headers['if-range'],'"edition-1"')
        self.assertTrue(stream.closed);self.assertTrue(stream.client.is_closed)

    def test_invalid_and_unbounded_reads_are_refused_without_fetching_media(self):
        with self.reader() as stream:
            with self.assertRaises(ValueError):stream.read()
            with self.assertRaises(ValueError):stream.seek(-1)
            with self.assertRaises(ValueError):stream.seek(0,100)
            with self.assertRaises(TypeError):stream.read('all')
            self.assertEqual(len(self.calls),1);stream.seek(len(self.data)+3);self.assertEqual(stream.read(10),b'')

    def test_invalid_descriptor_cannot_turn_into_a_file_or_an_archive_chosen_network_host(self):
        for changes in ({'endpoint':'file:///tmp/media'},{'endpoint':'https://user:secret@host.invalid'},
                        {'endpoint':'http://kiwix:8080/?redirect=http://other.invalid'},{'uuid':'not-uuid'},
                        {'path':'../private'},{'path':'/etc/passwd'},{'book':'other/../../book'},{'size':True}):
            with self.subTest(changes=changes),patch.object(archive_media.httpx,'Client') as client:
                with self.assertRaises(archive_media.ArchiveMediaError):archive_media.RangeReader({**self.source,**changes})
                client.assert_not_called()

    def test_reader_edition_and_book_must_match_before_any_media_read(self):
        for mode in ('old_edition','wrong_book','redirect_catalogue','oversize_catalogue'):
            self.mode=mode;self.calls=[]
            with self.subTest(mode=mode),self.assertRaises(archive_media.ArchiveMediaError):self.reader()
            self.assertEqual(len(self.calls),1)

    def test_media_redirects_ignored_ranges_wrong_size_and_truncation_never_return_fake_audio(self):
        for mode in ('redirect_media','no_ranges','bad_total','bad_mime','short','long','offline'):
            self.mode=mode
            with self.subTest(mode=mode),self.reader() as stream:
                with self.assertRaises(archive_media.ArchiveMediaError):stream.read(12)
                self.assertIsNotNone(stream.failure);self.assertEqual(stream.tell(),0)

    def test_an_edition_change_between_ranges_is_not_mixed_with_the_previous_bytes(self):
        with self.reader() as stream:
            stream.read(10);self.mode='new_etag';stream.seek(-10,io.SEEK_END)
            with self.assertRaises(archive_media.ArchiveMediaError) as error:stream.read(10)
            self.assertEqual(error.exception.code,'archive_edition_unavailable')
