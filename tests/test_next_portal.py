"""Compatibility of packaged entrypoints and the immutable classic control set."""
from html.parser import HTMLParser
import importlib.util
from pathlib import Path
import unittest
ROOT=Path(__file__).resolve().parents[1]


class IDs(HTMLParser):
    def __init__(self,text):
        super().__init__();self.ids=[];self.scripts=[];self.feed(text)
    def handle_starttag(self,tag,attrs):
        values=dict(attrs)
        if 'id' in values:self.ids.append(values['id'])
        if tag=='script' and values.get('src'):self.scripts.append(values['src'])


class NextPortalTests(unittest.TestCase):
    def test_generated_entrypoints_match_classic_controls_and_build(self):
        spec=importlib.util.spec_from_file_location('next_builder',ROOT/'scripts/build_next_portal.py')
        builder=importlib.util.module_from_spec(spec);spec.loader.exec_module(builder)
        expected=builder.build()
        for name in ('portal/index.html','portal/nouveau/index.html'):
            self.assertEqual((ROOT/name).read_text(),expected,name)
        old=IDs((ROOT/'portal/classique/index.html').read_text());new=IDs(expected)
        self.assertEqual(set(old.ids),set(new.ids));self.assertEqual(len(new.ids),len(set(new.ids)))
        self.assertLess(next(i for i,s in enumerate(new.scripts) if s.startswith('/nouveau/layout.js')), next(i for i,s in enumerate(new.scripts) if s.startswith('/app.js')))
        self.assertTrue(new.scripts[-1].startswith('/nouveau/navigation.js'))

    def test_design_assets_are_local_licensed_and_loaded_last(self):
        design=ROOT/'portal/design'
        for name in ('tokens.css','system.css','pages.css'):
            without_svg=(design/name).read_text().replace('http://www.w3.org/2000/svg','')
            self.assertNotIn('http://',without_svg,name);self.assertNotIn('https://',without_svg,name)
        for font in ('fraunces-latin-wght','atkinson-next-latin-wght','atkinson-next-latin-wght-italic'):
            self.assertEqual((design/'fonts'/(font+'.woff2')).read_bytes()[:4],b'wOF2')
        for licence in ('LICENSE-Fraunces.txt','LICENSE-Atkinson-Hyperlegible-Next.txt'):
            self.assertIn('SIL Open Font License',(design/'fonts'/licence).read_text())
        html=(ROOT/'portal/index.html').read_text()
        self.assertGreater(html.index('/design/system.css'),html.index('/nouveau/motion.css'))
        for page in ('cartes.html','pdf.html','secours.html','suivi-copie.html'):
            self.assertIn('/design/pages.css',(ROOT/'portal'/page).read_text(),page)

    def test_classic_has_its_own_scripts_and_styles_and_shared_reader_assets(self):
        text=(ROOT/'portal/classique/index.html').read_text()
        for name in ('app.js','documents.js','settings.js','style.css'):
            self.assertIn('/classique/'+name,text)
            self.assertTrue((ROOT/'portal/classique'/name).is_file())
        self.assertNotIn('/nouveau/layout.js',text)
        self.assertIn('/vendor/marked.js',text)
