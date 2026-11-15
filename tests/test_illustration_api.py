import unittest
from unittest.mock import AsyncMock,patch
import test_pilot_api as fixture
from pilot import catalogue,library,inventory,operations


class IllustrationAPITests(unittest.TestCase):
    setUp=fixture.PilotAPITests.setUp
    login=fixture.PilotAPITests.login

    def pdf(self):
        from pypdf import PdfWriter
        library.GUIDES.mkdir(exist_ok=True);writer=PdfWriter();writer.add_blank_page(width=200,height=300)
        path=library.GUIDES/'notice.fr.pdf';writer.write(path)
        return path,catalogue.revision('guide:notice.fr.pdf',library.GUIDES,inventory.ZIMS)

    def test_page_access_is_local_versioned_and_refuses_changed_files(self):
        path,revision=self.pdf();query='/api/illustrations/document?id=guide:notice.fr.pdf%23page=1&revision='+revision
        response=self.client.get(query);self.assertEqual(response.status_code,200,response.text)
        self.assertEqual(response.json(),{'url':'/guides/notice.fr.pdf','page':1,'version_checked':True})
        path.write_bytes(path.read_bytes()+b'\n')
        self.assertEqual(self.client.get(query).status_code,409)
        self.assertEqual(self.client.get('/api/illustrations/document?id=guide:absent.pdf%23page=1').status_code,404)
        for identifier in ('https://outside.invalid/a.pdf#page=1','guide:../private.pdf#page=1','guide:%252e%252e/private.pdf#page=1','guide:notice.fr.pdf#page=1201','guide:notice.fr.pdf#page=0'):
            response=self.client.get('/api/illustrations/document',params={'id':identifier})
            self.assertIn(response.status_code,(400,422),response.text)

    def test_image_proxy_retains_type_controls_and_source_archive(self):
        with patch.object(library,'books',AsyncMock(return_value=[{'book':'fixture'}])),patch.object(library,'get',AsyncMock(return_value=(b'<svg/>','image/svg+xml'))) as read:
            result=self.client.get('/api/media',params={'id':'zim:fixture/I/img.svg','source_id':'zim:fixture/A/topic'})
            self.assertEqual(result.status_code,200);self.assertIn('sandbox',result.headers['content-security-policy'])
            self.assertEqual(self.client.get('/api/media',params={'id':'zim:fixture/I/img.svg','source_id':'zim:other/A/topic'}).status_code,400)
            self.assertEqual(read.await_count,1)
        with patch.object(library,'get',AsyncMock(return_value=(b'<html/>','text/html'))),patch.object(library,'books',AsyncMock(return_value=[{'book':'fixture'}])):
            self.assertEqual(self.client.get('/api/media',params={'id':'zim:fixture/I/img.svg'}).status_code,400)

    def test_changed_archive_during_read_is_not_returned_as_the_old_figure(self):
        root=library.GUIDES/'zim';root.mkdir(parents=True);archive=root/'fixture.zim';archive.write_bytes(b'Original fictional archive')
        with patch.object(inventory,'ZIMS',root),patch.object(library,'books',AsyncMock(return_value=[{'book':'fixture'}])):
            revision=catalogue.revision('zim:fixture/A/topic',library.GUIDES,root)
            async def changed(*args,**kwargs):
                archive.write_bytes(b'Replacement fictional archive with different size')
                return b'<svg/>','image/svg+xml'
            with patch.object(library,'get',changed):
                response=self.client.get('/api/media',params={'id':'zim:fixture/I/image.svg','source_id':'zim:fixture/A/topic','revision':revision})
            self.assertEqual(response.status_code,409,response.text)

    def test_originals_remain_accessible_without_the_model_service(self):
        path,revision=self.pdf()
        with patch.object(operations,'status',AsyncMock(side_effect=AssertionError('No inference required'))):
            response=self.client.get('/api/illustrations/document',params={'id':'guide:notice.fr.pdf#page=1','revision':revision})
            self.assertEqual(response.status_code,200,response.text)
            with patch.object(library,'books',AsyncMock(return_value=[{'book':'fixture'}])),patch.object(library,'get',AsyncMock(return_value=(b'<svg/>','image/svg+xml'))):
                self.assertEqual(self.client.get('/api/media',params={'id':'zim:fixture/I/image.svg','source_id':'zim:fixture/A/topic'}).status_code,200)
