"""Seekable, bounded HTTP reads from the configured local Kiwix service.

Only the backend constructs the descriptor. Archive HTML cannot choose its host.
No video extraction, redirects, cookies, proxies or model dependency here.
"""
import io
import re
import time
from urllib.parse import quote,urlsplit,unquote
import uuid
import xml.etree.ElementTree as ET

import httpx

BLOCK=256*1024
MAX_CATALOGUE=64*1024
DECODE_OPTIONS={'format_whitelist':'mov,matroska,webm,avi,mpeg,mpegts,ogg,asf,flv','protocol_whitelist':''}


class ArchiveMediaError(ValueError):
    def __init__(self,code):self.code=code;super().__init__(code)


def urls(source):
    try:
        endpoint=source['endpoint'];book=source['book'];path=source['path'];size=source['size'];identity=str(uuid.UUID(source['uuid']))
        parsed=urlsplit(endpoint)
        parsed.port  # Validate a configured port before constructing a client.
        if parsed.scheme not in ('http','https') or not parsed.hostname or parsed.username or parsed.password or parsed.query or parsed.fragment:raise ValueError()
        if not isinstance(book,str) or not book or len(book)>1000 or any(c in book for c in '/\\') or book in ('.','..'):raise ValueError()
        if not isinstance(path,str) or len(path)>8000 or path.startswith('/') or '\\' in path or any(part in ('','.','..') for part in path.split('/')):raise ValueError()
        if any(ord(c)<32 or ord(c)==127 for c in endpoint+book+path):raise ValueError()
        if type(size) is not int or not 0<size<2**63:raise ValueError()
        base=endpoint.rstrip('/')
        return base+'/content/'+quote(book,safe='')+'/'+quote(path,safe='/'),base+'/catalog/v2/entry/'+identity,identity,size,book
    except (KeyError,ValueError,TypeError,AttributeError):raise ArchiveMediaError('archive_media_reference_invalid') from None


class RangeReader(io.RawIOBase):
    def __init__(self,source,*,transport=None):
        super().__init__();self.url,self.catalogue,self.identity,self.size,self.book=urls(source)
        self.position=0;self.cache=b'';self.cache_start=0;self.etag=None;self.failure=None
        self.metrics={'source':'kiwix_byte_ranges','http_requests':0,'catalogue_bytes':0,'media_bytes':0,'cache_hits':0,'largest_range_bytes':0,'http_ms':0}
        self.client=httpx.Client(trust_env=False,follow_redirects=False,timeout=httpx.Timeout(15,connect=5),headers={'Accept-Encoding':'identity'},transport=transport)
        try:self.check_catalogue()
        except BaseException:self.close();raise

    def readable(self):return not self.closed
    def seekable(self):return not self.closed
    def tell(self):self._checkClosed();return self.position
    def seek(self,offset,whence=io.SEEK_SET):
        self._checkClosed()
        if type(offset) is not int or whence not in (io.SEEK_SET,io.SEEK_CUR,io.SEEK_END):raise ValueError('invalid_seek')
        position=offset+(self.position if whence==io.SEEK_CUR else self.size if whence==io.SEEK_END else 0)
        if position<0:raise ValueError('negative_seek')
        self.position=position;return position

    def fail(self,code):
        self.failure=code;raise ArchiveMediaError(code)

    def request(self,url,maximum,*,headers=None,check=None):
        began=time.monotonic();self.metrics['http_requests']+=1
        try:
            with self.client.stream('GET',url,headers=headers) as response:
                if response.status_code in (301,302,303,307,308):self.fail('archive_media_redirect_refused')
                if response.headers.get('Content-Encoding','identity')!='identity':self.fail('archive_media_response_invalid')
                if check:check(response)
                elif response.status_code!=200:self.fail('archive_edition_unavailable')
                length=response.headers.get('Content-Length')
                if length is not None and (not length.isdecimal() or int(length)>maximum):self.fail('archive_media_response_invalid')
                body=bytearray()
                for chunk in response.iter_raw(65536):
                    if len(body)+len(chunk)>maximum:self.fail('archive_media_response_invalid')
                    body.extend(chunk)
                if length is not None and len(body)!=int(length):self.fail('archive_media_response_invalid')
                return bytes(body)
        except httpx.HTTPError:self.fail('archive_reader_unavailable')
        finally:self.metrics['http_ms']+=round((time.monotonic()-began)*1000)

    def check_catalogue(self):
        data=self.request(self.catalogue,MAX_CATALOGUE);self.metrics['catalogue_bytes']+=len(data)
        try:
            if b'<!DOCTYPE' in data or b'<!ENTITY' in data:raise ValueError()
            # Kiwix 3.8.1's isolated entry uses dc:issued without declaring dc.
            # Bind only known catalogue namespaces; identity/link checks stay strict.
            body=data.removeprefix(b'\xef\xbb\xbf').lstrip()
            if body.startswith(b'<?xml'):
                declaration,separator,body=body.partition(b'?>')
                if not separator:raise ValueError()
            wrapper=ET.fromstring(b'<kiwix-entry xmlns:dc="http://purl.org/dc/terms/" xmlns:atom="http://www.w3.org/2005/Atom">'+body+b'</kiwix-entry>')
            if len(wrapper)!=1:raise ValueError()
            entry=wrapper[0]
            if entry.tag.rsplit('}',1)[-1]!='entry':raise ValueError()
            identity=next(node.text for node in entry if node.tag.rsplit('}',1)[-1]=='id')
            link=next(node.attrib['href'] for node in entry if node.tag.rsplit('}',1)[-1]=='link' and node.get('type')=='text/html')
            parsed=urlsplit(link)
            if identity!='urn:uuid:'+self.identity or parsed.scheme or parsed.netloc or parsed.query or parsed.fragment or unquote(parsed.path).rstrip('/')!='/content/'+self.book:raise ValueError()
        except (ET.ParseError,ValueError,KeyError,StopIteration):self.fail('archive_edition_unavailable')

    def load(self):
        start=self.position;end=min(self.size,start+BLOCK)-1
        def check(response):
            match=re.fullmatch(r'bytes (\d+)-(\d+)/(\d+)',response.headers.get('Content-Range',''))
            if response.status_code!=206 or not match or tuple(map(int,match.groups()))!=(start,end,self.size):self.fail('archive_media_range_unavailable')
            mime=response.headers.get('Content-Type','').split(';')[0]
            if mime and not mime.startswith('video/') and mime!='application/octet-stream':self.fail('archive_media_response_invalid')
            etag=response.headers.get('ETag')
            if self.etag is not None and etag!=self.etag:self.fail('archive_edition_unavailable')
            if etag:self.etag=etag
        headers={'Range':f'bytes={start}-{end}'}
        if self.etag:headers['If-Range']=self.etag
        data=self.request(self.url,end-start+1,headers=headers,check=check)
        if len(data)!=end-start+1:self.fail('archive_media_response_invalid')
        self.metrics['media_bytes']+=len(data);self.metrics['largest_range_bytes']=max(self.metrics['largest_range_bytes'],len(data))
        self.cache=data;self.cache_start=start

    def read(self,size=-1):
        self._checkClosed()
        if size is None:size=-1
        if type(size) is not int:raise TypeError('read_size_required')
        if size<0:
            if self.size-self.position>BLOCK:raise ValueError('unbounded_archive_read_refused')
            size=max(0,self.size-self.position)
        if not size or self.position>=self.size:return b''
        if self.cache_start<=self.position<self.cache_start+len(self.cache):self.metrics['cache_hits']+=1
        else:self.load()
        offset=self.position-self.cache_start;data=self.cache[offset:offset+min(size,BLOCK)]
        self.position+=len(data);return data

    def readinto(self,buffer):
        data=self.read(len(buffer));buffer[:len(data)]=data;return len(data)

    def close(self):
        try:
            if hasattr(self,'client'):self.client.close()
        finally:self.cache=b'';super().close()
