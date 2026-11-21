import hashlib
import io
import json
from pathlib import Path
import sys
import tempfile
import threading
import unittest
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import content
import content_mirrors as mirrors
import setup

class Response(io.BytesIO):
    def __init__(self,body,url,status=206,headers=None):
        super().__init__(body);self.url=url;self.status=status;self.headers=headers or {}
    def geturl(self):return self.url

class MirrorTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup);self.root=Path(self.temp.name)
        self.raw=b'abcdefghi'
        self.item=dict(id='a',title='A',path='library/zim/a.zim',url='https://download.kiwix.org/a.zim',bytes=9,sha256=hashlib.sha256(self.raw).hexdigest())
        self.urls=['https://slow.example/a.zim','https://fast.example/a.zim']
    def metalink(self,**changes):
        item={**self.item,**changes}
        return ('<metalink xmlns="urn:ietf:params:xml:ns:metalink"><file name="a.zim"><size>'+str(item['bytes'])+'</size><hash type="sha-256">'+item['sha256']+'</hash>'+''.join('<url>'+u+'</url>' for u in self.urls)+'</file></metalink>').encode()
    def test_metadata_requires_pinned_hash_size_and_https(self):
        self.assertEqual(mirrors.metalink_urls(self.metalink(),self.item),self.urls)
        for changes in ({'bytes':10},{'sha256':'0'*64}):
            with self.assertRaises(ValueError):mirrors.metalink_urls(self.metalink(**changes),self.item)
        self.urls+=['http://unsafe.example/a','https://127.0.0.1/a']
        self.assertEqual(len(mirrors.metalink_urls(self.metalink(),self.item)),2)
        with self.assertRaises(setup.SetupError):mirrors.SecureRedirect().redirect_request(None,None,302,'',{},'http://example.org')
    def test_large_metalink_keeps_the_verified_mirror_selection(self):
        # A real >200 GB archive has over 3 MB of piece hashes before its URLs.
        raw = self.metalink().replace(b'<url>', b'<!--' + b'x' * 3_100_000 + b'--><url>', 1)
        selector = mirrors.Selector(self.root, opener=lambda request, **kwargs: Response(raw, request.full_url, 200))
        with patch.object(selector, 'probe', side_effect=(1, 10)):
            self.assertEqual(selector.ranked(self.item, 3)[0], self.urls[1])
        with self.assertRaises(ValueError):
            mirrors.metalink_urls(b'x' * (mirrors.MAX_METALINK_BYTES + 1), self.item)

    def test_measured_rank_cache_and_failover(self):
        calls=[]
        def open(req,**kwargs):
            calls.append(req.full_url)
            if req.full_url.endswith('.meta4'):return Response(self.metalink(),req.full_url,200)
            if req.full_url==self.urls[1]:raise OSError('fast server unavailable')
            return Response(self.raw[3:],req.full_url,headers={'Content-Range':'bytes 3-8/9'})
        selector=mirrors.Selector(self.root,opener=open)
        with patch.object(selector,'probe',side_effect=[1,10]) as probe:
            self.assertEqual(selector.ranked(self.item,3)[0],self.urls[1])
            self.assertEqual(selector.ranked(self.item,3)[0],self.urls[1]);self.assertEqual(probe.call_count,2)
            request=__import__('urllib.request',fromlist=['Request']).Request(self.item['url'],headers={'Range':'bytes=3-'})
            with selector.open(self.item,request) as response:self.assertEqual(response.read(),self.raw[3:])
        self.assertEqual(calls[-2:],list(reversed(self.urls)))
    def test_mirror_ignoring_resume_never_truncates_existing_partial(self):
        part=self.root/(self.item['path']+'.part');part.parent.mkdir(parents=True);part.write_bytes(self.raw[:3])
        selector=mirrors.Selector(self.root,opener=lambda req,**kw:Response(self.raw,req.full_url,200))
        with patch.object(selector,'ranked',return_value=self.urls),patch.object(mirrors,'opener_for',return_value=lambda req,**kw:selector.open(self.item,req)):
            with self.assertRaises(setup.SetupError):content.transfer(self.root,self.item)
        self.assertEqual(part.read_bytes(),self.raw[:3]);self.assertFalse((self.root/self.item['path']).exists())
    def test_valid_resume_keeps_prefix_and_checks_final_hash(self):
        part=self.root/(self.item['path']+'.part');part.parent.mkdir(parents=True);part.write_bytes(self.raw[:3])
        selector=mirrors.Selector(self.root,opener=lambda req,**kw:Response(self.raw[3:],req.full_url,headers={'Content-Range':'bytes 3-8/9'}))
        with patch.object(selector,'ranked',return_value=self.urls),patch.object(mirrors,'opener_for',return_value=lambda req,**kw:selector.open(self.item,req)):
            content.transfer(self.root,self.item)
        self.assertEqual((self.root/self.item['path']).read_bytes(),self.raw)
        # A diagnostic record from a metadata fallback must not break next ranking.
        selector.files[self.item['sha256']]={'id':'a','selected':self.urls[0]}
        with patch.object(selector,'probe',return_value=1):
            self.assertEqual(selector.ranked(self.item,0),[self.item['url']])

class ParallelTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup);self.root=Path(self.temp.name)
        self.items=[dict(id=n,title=n,path='library/guides/'+n+'.txt',url='https://example.org/'+n,bytes=3,
            sha256=hashlib.sha256(b'abc').hexdigest(),language='fr',publisher='Fixture',edition='2026',licence='test') for n in ('a','b')]
    def test_network_overlaps_and_both_receipts_survive(self):
        barrier=threading.Barrier(2);observed=[]
        def transfer(root,item,**kwargs):
            kwargs['progress'](1,3)
            barrier.wait(timeout=5)
            observed.append(json.loads((root/'catalog/content-progress.json').read_text())['active'])
            path=root/item['path'];path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(b'abc')
            return 'downloaded'
        with patch.object(content,'transfer',side_effect=transfer):
            results=content.download(self.root,self.items,workers=2,reserve=0)
        self.assertEqual(len(results),2)
        self.assertTrue(any(len(a)==2 for a in observed))
        self.assertEqual(len(content.catalog(self.root/'catalog/downloaded-content.json')),2)
        self.assertEqual(len(json.loads((self.root/'library/guides/metadata.json').read_text())),2)
    def test_failure_continues_other_item_and_keeps_partial(self):
        def transfer(root,item,**kwargs):
            if item['id']=='a':
                part=root/(item['path']+'.part');part.parent.mkdir(parents=True,exist_ok=True);part.write_bytes(b'a');raise OSError('offline')
            return 'downloaded'
        with patch.object(content,'transfer',side_effect=transfer):
            results=content.download(self.root,self.items,workers=2,reserve=0,continue_on_error=True)
        self.assertEqual({r['status'] for r in results},{'failed','downloaded'})
        self.assertEqual((self.root/(self.items[0]['path']+'.part')).read_bytes(),b'a')
        self.assertEqual([i['id'] for i in content.catalog(self.root/'catalog/downloaded-content.json')],['b'])
    def test_fail_fast_joins_sibling_before_releasing_lock(self):
        barrier=threading.Barrier(2);joined=threading.Event()
        def transfer(root,item,**kwargs):
            barrier.wait(timeout=5)
            if item['id']=='a':raise OSError('offline')
            while not kwargs['cancelled']():joined.wait(.001)
            joined.set();raise content.DownloadPaused()
        with patch.object(content,'transfer',side_effect=transfer):
            with self.assertRaises(OSError):content.download(self.root,self.items,workers=2,reserve=0)
        self.assertTrue(joined.is_set());self.assertFalse((self.root/'catalog/content.lock').exists())
    def test_capacity_check_and_write_share_one_lock(self):
        barrier=threading.Barrier(2)
        actual=content.transfer
        state={'in_guard':0,'peak':0}
        guard_lock=threading.Lock()
        def guard(*args,**kwargs):
            with guard_lock:
                state['in_guard']+=1;state['peak']=max(state['peak'],state['in_guard'])
            threading.Event().wait(.01)
            with guard_lock:state['in_guard']-=1
        class Stream(Response):
            def read(self,*args):
                if self.tell()==0:barrier.wait(timeout=5)
                return super().read(*args)
        def transfer(root,item,**kwargs):
            return actual(root,item,opener=lambda req,**kw:Stream(b'abc',req.full_url,200),**kwargs)
        with patch.object(content,'transfer',side_effect=transfer),patch.object(content,'check_capacity',side_effect=guard):
            content.download(self.root,self.items,workers=2,reserve=0)
        self.assertEqual(state['peak'],1)
        self.assertEqual(len(content.catalog(self.root/'catalog/downloaded-content.json')),2)

    def test_tls_retry_and_jobs_validation(self):
        from unittest.mock import Mock
        repair=Mock()
        with patch.object(content,'transfer',side_effect=[OSError('CERTIFICATE_VERIFY_FAILED'),'downloaded']):
            content.download(self.root,self.items[:1],workers=2,reserve=0,repair_tls=repair)
        repair.assert_called_once_with(self.items[0]['url'])
        for count in (0,4,True):
            with self.assertRaises(setup.SetupError):content.download(self.root,[],workers=count)

if __name__=='__main__':unittest.main()
