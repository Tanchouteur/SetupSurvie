"""Single portal entrypoint, its control template and the retired legacy addresses."""
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


class PortalBuildTests(unittest.TestCase):
    def test_generated_entrypoint_matches_template_controls_and_build(self):
        spec=importlib.util.spec_from_file_location('portal_builder',ROOT/'scripts/build_portal.py')
        builder=importlib.util.module_from_spec(spec);spec.loader.exec_module(builder)
        expected=builder.build()
        self.assertEqual((ROOT/'portal/index.html').read_text(),expected)
        template=IDs((ROOT/'portal/interface/modele.html').read_text());new=IDs(expected)
        self.assertEqual(set(template.ids),set(new.ids));self.assertEqual(len(new.ids),len(set(new.ids)))
        self.assertLess(next(i for i,s in enumerate(new.scripts) if s.startswith('/interface/layout.js')), next(i for i,s in enumerate(new.scripts) if s.startswith('/app.js')))
        self.assertTrue(new.scripts[-1].startswith('/interface/navigation.js'))
        self.assertIn('/vendor/marked.js',expected)

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
        self.assertGreater(html.index('/design/system.css'),html.index('/interface/motion.css'))
        for page in ('cartes.html','pdf.html','secours.html','suivi-copie.html'):
            self.assertIn('/design/pages.css',(ROOT/'portal'/page).read_text(),page)

    def test_legacy_addresses_only_redirect_to_the_single_portal(self):
        for folder in ('classique','nouveau'):
            self.assertEqual(sorted(p.name for p in (ROOT/'portal'/folder).iterdir()),['index.html'],folder)
            text=(ROOT/'portal'/folder/'index.html').read_text()
            self.assertIn("location.replace('/'+location.search+location.hash)",text)
            self.assertNotIn('<script src',text)
        for path in ROOT.joinpath('portal').rglob('*'):
            if path.suffix in ('.js','.html','.css') and path.parent.name not in ('classique','nouveau','vendor'):
                text=path.read_text(encoding='utf-8')
                for legacy in ('/classique/','interface=nouveau','"/nouveau/','\'/nouveau/'):
                    self.assertFalse(legacy in text,f'{legacy} in {path}')
