"""Exercise the real HTTP reader with bounded synthetic responses, no network."""
import unittest
from unittest.mock import patch
from unittest.mock import AsyncMock
import httpx
from fastapi import HTTPException
from pilot import library


class LibraryRedirectTests(unittest.IsolatedAsyncioTestCase):
    async def read(self,handler,path='/content/book/Alias',maximum=2000000):
        client=httpx.AsyncClient
        transport=httpx.MockTransport(handler)
        with patch.object(library.httpx,'AsyncClient',side_effect=lambda **kw:client(transport=transport,**kw)):
            return await library.get(path,maximum)

    async def test_redirected_articles_are_read_for_all_standard_redirect_statuses(self):
        for status in (301,302,303,307,308):
            calls=[]
            def handler(request):
                calls.append(str(request.url))
                if request.url.path.endswith('/Alias'):return httpx.Response(status,headers={'Location':'/content/book/Cible_%C3%A9'})
                return httpx.Response(200,content=b'Fictional target',headers={'content-type':'text/html'})
            with self.subTest(status=status):
                raw,kind=await self.read(handler)
                self.assertEqual(raw,b'Fictional target');self.assertEqual(kind,'text/html');self.assertEqual(len(calls),2)

    async def test_relative_redirects_and_chain_within_archive_work(self):
        def handler(request):
            if request.url.path.endswith('/Alias'):return httpx.Response(302,headers={'Location':'sub/Second'})
            if request.url.path.endswith('/Second'):return httpx.Response(307,headers={'Location':'../Final'})
            self.assertEqual(request.url.path,'/content/book/Final')
            return httpx.Response(200,content=b'Final fixture')
        self.assertEqual((await self.read(handler))[0],b'Final fixture')

    async def test_source_preserves_original_reference_and_resolves_images_from_target(self):
        reply=library.Fetched(b'<html lang="fr"><title>Cible</title><p>Texte fictif.</p><img src="image.png"></html>','text/html','/content/book/sub/Target')
        with patch.object(library,'books',AsyncMock(return_value=[{'book':'book','language':'fra'}])),patch.object(library,'get',AsyncMock(return_value=reply)):
            source=await library.source('zim:book/Alias')
        self.assertEqual(source['id'],'zim:book/Alias')
        self.assertEqual(source['title'],'Cible')
        self.assertEqual(source['images'][0]['id'],'zim:book/sub/image.png')

    async def test_external_other_archive_and_non_content_redirects_are_never_contacted(self):
        for location in ['https://outside.invalid/secret','//outside.invalid/path','/content/other/article','/api/private','/content/book/%2e%2e/private','/content/book/x?secret=1','']:
            calls=[]
            def handler(request):
                calls.append(str(request.url));return httpx.Response(302,headers={'Location':location})
            with self.subTest(location=location):
                with self.assertRaises(HTTPException) as caught:await self.read(handler)
                self.assertEqual(caught.exception.status_code,502);self.assertEqual(len(calls),1)
                self.assertNotIn('secret',str(caught.exception.detail))

    async def test_loop_and_overlong_chain_are_bounded(self):
        calls=[]
        def loop(request):
            calls.append(1);return httpx.Response(302,headers={'Location':'/content/book/Alias'})
        with self.assertRaisesRegex(HTTPException,'boucle'):await self.read(loop)
        self.assertEqual(len(calls),1)
        calls=[]
        def chain(request):
            calls.append(1);return httpx.Response(302,headers={'Location':'/content/book/next'+str(len(calls))})
        with self.assertRaisesRegex(HTTPException,'redirections'):await self.read(chain)
        self.assertEqual(len(calls),6)

    async def test_catalog_redirect_and_oversized_target_do_not_bypass_limits(self):
        calls=[]
        def catalog(request):
            calls.append(1);return httpx.Response(302,headers={'Location':'/content/book/Target'})
        with self.assertRaises(HTTPException):await self.read(catalog,'/catalog/v2/entries')
        self.assertEqual(len(calls),1)
        def large(request):
            if request.url.path.endswith('/Alias'):return httpx.Response(302,headers={'Location':'Target'})
            return httpx.Response(200,content=b'x'*30)
        with self.assertRaises(HTTPException) as caught:await self.read(large,maximum=10)
        self.assertEqual(caught.exception.status_code,413)
