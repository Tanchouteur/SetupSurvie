"""Select measured HTTPS mirrors from a size/SHA-256 checked Kiwix Metalink."""
import ipaddress
import re
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

import setup

KIWIX = {'download.kiwix.org', 'lb.download.kiwix.org', 'mirror.download.kiwix.org'}
NS = {'m': 'urn:ietf:params:xml:ns:metalink'}


def https_url(value):
    parsed = urllib.parse.urlsplit(value)
    if parsed.scheme != 'https' or not parsed.hostname or parsed.username or parsed.password or parsed.fragment:
        return False
    if parsed.hostname == 'localhost' or parsed.hostname.endswith(('.local', '.localhost')):
        return False
    try:
        if not ipaddress.ip_address(parsed.hostname).is_global:
            return False
    except ValueError:
        pass
    return True


class SecureRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        if not https_url(newurl):
            raise setup.SetupError('Redirection de miroir non HTTPS refusée.')
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def network_open(request, timeout=10):
    return urllib.request.build_opener(urllib.request.ProxyHandler({}), SecureRedirect()).open(request, timeout=timeout)


def metalink_urls(raw, item):
    if len(raw) > 2_000_000 or b'<!DOCTYPE' in raw.upper():
        raise ValueError('Metalink trop volumineux ou déclaration XML refusée.')
    root = ET.fromstring(raw)
    files = [f for f in root.findall('m:file', NS) if f.get('name') == item['path'].rsplit('/', 1)[-1]]
    if len(files) != 1:
        raise ValueError('Archive absente ou ambiguë dans le Metalink.')
    file = files[0]
    digest = file.findtext("m:hash[@type='sha-256']", namespaces=NS)
    if int(file.findtext('m:size', default='', namespaces=NS)) != item['bytes'] or digest != item['sha256']:
        raise ValueError('Le Metalink ne correspond pas à la taille et à l’empreinte figées.')
    return list(dict.fromkeys(u.text.strip() for u in file.findall('m:url', NS)
                             if u.text and https_url(u.text.strip())))[:6]


class Selector:
    def __init__(self, root, *, opener=network_open, clock=time.monotonic, sample=2*1024*1024, ttl=300):
        self.root, self.opener, self.clock = root, opener, clock
        self.sample, self.ttl = sample, ttl
        self.lock = threading.RLock()
        self.hosts = {}
        self.files = {}

    def probe(self, url, item, offset, check):
        size = min(self.sample, item['bytes'])
        start = min(offset, item['bytes']-size)
        end = start+size-1
        request = urllib.request.Request(url, headers={'Range': f'bytes={start}-{end}',
            'Accept-Encoding': 'identity', 'User-Agent': 'SetupSurvie-offline-library/0.1'})
        begin = self.clock(); received = 0
        try:
            check()
            with self.opener(request, timeout=3) as response:
                if (response.status != 206 or response.headers.get('Content-Range') != f'bytes {start}-{end}/{item["bytes"]}'
                        or response.headers.get('Content-Encoding', 'identity') != 'identity'
                        or not https_url(response.geturl())):
                    return 0
                while received < size and self.clock()-begin < 3:
                    check()
                    block = response.read(min(65536, size-received))
                    if not block:
                        break
                    received += len(block)
            return received/max(self.clock()-begin, .001) if received >= min(65536, size) else 0
        except (OSError, ValueError, setup.SetupError):
            return 0

    def ranked(self, item, offset, check=lambda: None):
        with self.lock:
            key = item['sha256']
            saved = self.files.get(key)
            if saved and 'at' in saved and self.clock()-saved['at'] < self.ttl:
                return saved['urls']
            metadata = item.get('source_meta4', item['url']+'.meta4')
            parsed = urllib.parse.urlsplit(metadata)
            if parsed.hostname not in KIWIX or not https_url(metadata):
                return [item['url']]
            try:
                check()
                with self.opener(urllib.request.Request(metadata, headers={'User-Agent': 'SetupSurvie-offline-library/0.1'}), timeout=10) as response:
                    urls = metalink_urls(response.read(2_000_001), item)
            except (OSError, ValueError, ET.ParseError, setup.SetupError):
                return [item['url']]
            rates = {}
            for url in urls:
                check()
                host = urllib.parse.urlsplit(url).hostname
                cached = self.hosts.get(host)
                if cached and self.clock()-cached['at'] < self.ttl:
                    speed = cached['speed']
                else:
                    speed = self.probe(url, item, offset, check)
                    self.hosts[host] = {'at': self.clock(), 'speed': speed}
                rates[url] = speed
            ordered = sorted(urls, key=lambda u: rates[u], reverse=True)
            if item['url'] not in ordered:
                ordered.append(item['url'])
            self.files[key] = {'at': self.clock(), 'urls': ordered, 'rates': rates,
                               'id': item['id'], 'sha256': key}
            return ordered

    def open(self, item, request, timeout=60, check=lambda: None):
        header = request.get_header('Range', 'bytes=0-')
        match = re.fullmatch(r'bytes=(\d+)-', header)
        if not match:
            raise setup.SetupError('Plage de reprise du miroir non valide.')
        offset = int(match.group(1))
        errors = []
        for url in self.ranked(item, offset, check):
            check()
            try:
                response = self.opener(urllib.request.Request(url, headers=dict(request.header_items())), timeout=timeout)
                valid = (https_url(response.geturl()) and response.headers.get('Content-Encoding', 'identity') == 'identity'
                         and ((response.status == 206 and response.headers.get('Content-Range') == f'bytes {offset}-{item["bytes"]-1}/{item["bytes"]}')
                              or (offset == 0 and response.status == 200)))
                if not valid:
                    response.close()
                    raise setup.SetupError('Miroir incompatible avec la reprise ; partiel conservé.')
                with self.lock:
                    record = self.files.setdefault(item['sha256'], {'id': item['id']})
                    record.update(selected=url, offset=offset)
                    try:
                        setup.write_json(self.root/'catalog/content-mirrors.json', {'files': list(self.files.values())})
                    except BaseException:
                        response.close()
                        raise
                return response
            except (OSError, setup.SetupError) as exc:
                errors.append(str(exc))
                with self.lock:
                    self.hosts.pop(urllib.parse.urlsplit(url).hostname, None)
                    self.files.pop(item['sha256'], None)
        raise setup.SetupError('Aucun miroir disponible pour reprendre ; partiel conservé. '+('; '.join(errors[-2:])))


_selectors = {}
_lock = threading.Lock()


def opener_for(root, item, check):
    if urllib.parse.urlsplit(item['url']).hostname not in KIWIX or not item['path'].endswith('.zim'):
        return None
    with _lock:
        selector = _selectors.setdefault(str(root), Selector(root))
    return lambda request, timeout=60: selector.open(item, request, timeout, check)
