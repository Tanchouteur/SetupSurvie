#!/usr/bin/env python3
"""Extract attributed local articles for real-document retrieval evaluations."""
import hashlib
from html.parser import HTMLParser
import json
import re
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

import linux_lab as lab

SOURCES = (
    ('WIKI-FR-OHM', 'fra', 'wikipedia_fr_all_maxi_2026-05', "Loi_d'Ohm"),
    ('WIKI-FR-KWH', 'fra', 'wikipedia_fr_all_maxi_2026-05', 'Kilowatt-heure'),
    ('WIKI-FR-FOOD', 'fra', 'wikipedia_fr_all_maxi_2026-05', 'Conservation_des_aliments'),
    ('BOOK-EN-OHM', 'eng', 'wikibooks_en_all_maxi_2026-10', "Ohm's law"),
    ('BOOK-EN-BOIL', 'eng', 'wikibooks_en_all_maxi_2026-10', 'Cookbook Boiling'),
)


class Text(HTMLParser):
    def __init__(self):
        super().__init__(); self.parts = []; self.skip = 0; self.math_depth = 0

    def handle_starttag(self, tag, attrs):
        if tag in ('script', 'style'):
            self.skip += 1
        if tag == 'math':
            self.math_depth += 1
            if self.math_depth == 1:
                self.parts.append(' ' + dict(attrs).get('alttext', '') + ' ')
        if tag in ('p', 'h1', 'h2', 'h3', 'li', 'tr', 'br'):
            self.parts.append('\n')

    def handle_endtag(self, tag):
        if tag in ('script', 'style'):
            self.skip = max(0, self.skip - 1)
        if tag == 'math':
            self.math_depth = max(0, self.math_depth - 1)
        if tag in ('p', 'li', 'h1', 'h2', 'h3', 'tr'):
            self.parts.append('\n')

    def handle_data(self, data):
        if not self.skip and not self.math_depth:
            self.parts.append(data)


def read(url):
    for attempt in range(4):
        try:
            with urllib.request.urlopen(url, timeout=40) as response:
                return response.read().decode()
        except (urllib.error.URLError, ConnectionError):
            if attempt == 3:
                raise
            time.sleep(attempt + 1)


def main():
    lab.checked_mount()
    output = lab.MOUNT / 'data/research/sources'
    output.mkdir(parents=True, exist_ok=True)
    manifest = []
    for identifier, language, book, page in SOURCES:
        if book.startswith('wikipedia'):
            url = 'http://127.0.0.1:8081/content/' + book + '/' + urllib.parse.quote(page)
        else:
            query = urllib.parse.urlencode({'books.name': book, 'pattern': page, 'format': 'xml', 'pageLength': 5})
            xml = ET.fromstring(read('http://127.0.0.1:8081/search?' + query))
            items = xml.findall('./channel/item')
            if not items:
                print('NO_SOURCE', identifier, flush=True)
                continue
            # Prefer the matching subject/title, keeping the chosen title and URL in the manifest.
            selected = max(items, key=lambda item: sum(word in item.findtext('title', '').lower()
                for word in page.lower().replace("'", ' ').split()))
            url = urllib.parse.urljoin('http://127.0.0.1:8081/', selected.findtext('link'))
        html = read(url)
        parser = Text(); parser.feed(html)
        text = '\n'.join(line.strip() for line in ''.join(parser.parts).splitlines() if line.strip())
        title = re.search(r'<title>(.*?)</title>', html, re.S)
        title = title.group(1) if title else identifier
        header = (f'Identifiant de source : {identifier}\nTitre : {title}\nLangue : {language}\n'
                  f'Original illustré local : {url.replace("127.0.0.1", "localhost")}\n'
                  f'Archive : {book}\nAttribution et licence : consulter les mentions de la page originale.\n\n')
        path = output / (identifier + '.txt')
        path.write_text(header + text, encoding='utf-8')
        entry = {'id': identifier, 'title': title, 'language': language, 'url': url,
                 'book': book, 'characters': len(text), 'sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
                 'file': str(path)}
        manifest.append(entry)
        print(json.dumps(entry, ensure_ascii=False), flush=True)
    lab.setup.write_json(lab.MOUNT / 'results/research-sources.json', manifest)


if __name__ == '__main__':
    main()
