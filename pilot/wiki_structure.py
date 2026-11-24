"""Subject evidence from local MediaWiki HTML, independently of the search query."""
from html.parser import HTMLParser
import re
from urllib.parse import unquote

MAX_HTML = 1_100_000
MAX_LABELS = 40
WIKIPEDIA = re.compile(r'^wikipedia_[a-z0-9-]+_', re.I)
_BACK = (r'notes|r[eé]f[eé]rences|sources|annexes|bibliograph(?:ie|y)|voir aussi|liens externes|see also|external links'
         r'|other websites|related pages|more reading|further reading|articles connexes')
# The whole heading must be back matter: "Références culturelles" or
# "Notes de musique" are ordinary article sections.
BACK_MATTER = re.compile(r'^(?:' + _BACK + r')(?:\s*(?:,|et|and|&)\s*(?:' + _BACK + r'))*\s*:?$', re.I)


def wikipedia(item):
    identifier = item.get('id', '')
    return identifier.startswith('zim:') and bool(WIKIPEDIA.match(identifier[4:].split('/', 1)[0]))


class ArticleStructure(HTMLParser):
    def __init__(self):
        super().__init__()
        self.categories = []
        self.sections = []
        self.subsections = []
        self.heading = None
        self.parts = []
        self.ignored = []
        self.back_matter = False
        self.category_divs = 0

    def handle_starttag(self, tag, attrs):
        attrs = {key: value or '' for key, value in attrs}
        if tag in ('nav', 'script', 'style'):
            self.ignored.append(tag)
        if self.ignored:
            return
        if tag == 'div':
            if self.category_divs or attrs.get('id') == 'mw-normal-catlinks':
                self.category_divs += 1
        category_link = tag == 'link' and 'mw:PageProp/Category' in attrs.get('rel', '').split()
        if category_link or (tag == 'a' and self.category_divs):
            self.add_category(attrs.get('href', ''))
        if tag in ('h2', 'h3') and not self.back_matter:
            self.heading = tag
            self.parts = []

    def handle_endtag(self, tag):
        if self.ignored:
            if tag == self.ignored[-1]:
                self.ignored.pop()
            return
        if tag == 'div' and self.category_divs:
            self.category_divs -= 1
        if tag == self.heading:
            label = ' '.join(''.join(self.parts).split())[:160]
            if BACK_MATTER.match(label):
                self.back_matter = tag == 'h2'
            elif label:
                labels = self.sections if tag == 'h2' else self.subsections
                if len(labels) < MAX_LABELS:
                    labels.append(label)
            self.heading = None

    def add_category(self, href):
        if len(self.categories) >= MAX_LABELS:
            return
        path = unquote(href.split('#', 1)[0].split('?', 1)[0])
        label = re.search(r'(?:^|/)(?:Category|Catégorie):([^/]+)$', path, re.I)
        if label:
            name = label[1].replace('_', ' ').strip()[:160]
            if name and name not in self.categories:
                self.categories.append(name)

    def handle_data(self, data):
        if self.heading and not self.ignored and len(self.parts) < 32:
            self.parts.append(data[:160])


def extract(raw):
    parser = ArticleStructure()
    parser.feed(raw.decode('utf-8', errors='replace'))
    parser.close()
    return {'categories': parser.categories, 'sections': parser.sections, 'subsections': parser.subsections}
