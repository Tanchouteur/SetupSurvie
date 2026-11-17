"""Synthetic markup only: formulas must retain their grouping or stay explicit."""
import unittest
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock,patch
from pilot.html_text import Text
from pilot.archive_index import ArticleText


class MathTextTests(unittest.TestCase):
    def read(self,markup,reader=Text):
        p=reader();p.feed('<article>Avant '+markup+' après.</article>');p.close()
        return p.text()

    def test_fraction_and_units_are_not_discarded_or_flattened(self):
        markup='<math><mi>I</mi><mo>=</mo><mfrac><mn>12</mn><mn>4</mn></mfrac><mo>=</mo><mn>3</mn><mi>A</mi></math>'
        value=self.read(markup)
        self.assertIn(r'\frac{12}{4}',value);self.assertIn('3A',value)
        self.assertIn('Avant',value);self.assertIn('après.',value)

    def test_powers_subscripts_and_nested_fractions_retain_grouping(self):
        markup='<math><msub><mi>P</mi><mi>n</mi></msub><mo>=</mo><mfrac><msup><mrow><mi>U</mi><mo>+</mo><mi>V</mi></mrow><mn>2</mn></msup><msub><mi>R</mi><mi>n</mi></msub></mfrac></math>'
        value=self.read(markup)
        self.assertIn(r'{P}_{n}',value);self.assertIn(r'\frac{{U + V}^{2}}{{R}_{n}}',value)
        self.assertNotIn('U + V2',value)

    def test_author_alternative_and_tex_annotation_take_priority_without_duplicate(self):
        self.assertEqual(self.read('<math alttext="L=c/f"><mi>ignored</mi></math>').count('L=c/f'),1)
        value=self.read('<math><semantics><mfrac><mi>a</mi><mi>b</mi></mfrac><annotation encoding="application/x-tex">\\frac{a}{b}</annotation></semantics></math>')
        self.assertEqual(value.count(r'\frac{a}{b}'),1)

    def test_roots_fences_and_matrix_keep_their_layout(self):
        markup='<math><mroot><mi>x</mi><mn>3</mn></mroot><mo>+</mo><mfenced open="[" close="]"><mtable><mtr><mtd><mi>a</mi></mtd><mtd><mi>b</mi></mtd></mtr><mtr><mtd><mi>c</mi></mtd><mtd><mi>d</mi></mtd></mtr></mtable></mfenced></math>'
        value=self.read(markup)
        self.assertIn(r'\sqrt[3]{x}',value);self.assertIn(r'\begin{matrix}a & b \\ c & d\end{matrix}',value)

    def test_unsupported_and_incomplete_math_never_become_silent_gaps(self):
        for markup in ('<math><apply><divide/><ci>a</ci><ci>b</ci></apply></math>',
                       '<math><mfrac><mi>a</mi></mfrac></math>', '<math><mi>unfinished',
                       '<math><maction><mi>x</mi><mi>y</mi></maction></math>'):
            with self.subTest(markup=markup):self.assertIn('Formule non extractible',self.read(markup))

    def test_hidden_navigation_and_scripts_do_not_supply_formulas(self):
        value=self.read('<nav><math alttext="hidden"/></nav><script><math alttext="secret"/></script><math><mi>x</mi></math>')
        self.assertNotIn('hidden',value);self.assertNotIn('secret',value);self.assertIn('x',value)

    def test_non_math_images_are_not_turned_into_formulas(self):
        value=self.read('<img src="chart.png" alt="figure 9"><img class="mwe-math-fallback-image-inline" src="formula.svg" alt="x^2">')
        self.assertNotIn('figure 9',value);self.assertIn('x^2',value)

    def test_native_formula_and_its_fallback_image_are_not_both_extracted(self):
        from pilot.math_text import BLOCKS
        value=self.read('<span class="mwe-math-element"><math alttext="x^2"><mi>x</mi></math><img class="mwe-math-fallback-image-inline" src="formula.svg" alt="x^2"></span><span class="mwe-math-element"><img class="mwe-math-fallback-image-inline" src="other.svg" alt="y^3"></span>')
        self.assertEqual([m['value'] for m in BLOCKS.finditer(value)],['x^2','y^3'])

    def test_bounded_depth_and_size_do_not_crash_or_lose_trailing_text(self):
        for markup in ('<math>'+'<mrow>'*100+'<mi>x</mi>'+'</mrow>'*100+'</math>',
                       '<math><mi>'+('x'*100000)+'</mi></math>'):
            value=self.read(markup);self.assertIn('Formule non extractible',value);self.assertIn('après.',value)

    def test_archive_index_and_reader_expose_the_same_formula(self):
        markup='<math><mfrac><mn>19</mn><mn>7</mn></mfrac></math>'
        for reader in (Text,ArticleText):
            with self.subTest(reader=reader):self.assertIn(r'\frac{19}{7}',self.read(markup,reader))

    def test_formula_blocks_are_atomic_and_preserve_all_source_characters(self):
        from pilot.document_text import chunks
        from pilot.math_text import BLOCKS
        text=('Before the formula. '*15)+self.read('<math><mfrac><mi>alpha</mi><mi>beta</mi></mfrac></math>')+(' After the formula. '*15)
        parts=list(chunks(text,300));self.assertEqual(''.join(parts),text)
        self.assertEqual(sum(len(list(BLOCKS.finditer(p))) for p in parts),1)
        formula=self.read('<math><mfrac><mi>'+('x'*800)+'</mi><mn>7</mn></mfrac></math>')
        parts=list(chunks(formula,300));self.assertEqual(''.join(parts),formula)
        self.assertEqual(sum(len(list(BLOCKS.finditer(p))) for p in parts),1)

    def test_translation_preserves_originals_and_rejects_lost_duplicate_or_reordered_anchors(self):
        from pilot.math_text import ProtectedTranslation,TranslationMismatch,marked,BLOCKS
        source='First. '+marked(r'\frac{19}{7}')+' Second. '+marked(r'x^2')
        protected=ProtectedTranslation(source)
        self.assertNotIn(r'\frac',protected.text)
        restored=protected.restore(protected.text.replace('First','Premier').replace('Second','Deuxième'),'fixture')
        self.assertEqual([m[0] for m in BLOCKS.finditer(restored)],[m[0] for m in BLOCKS.finditer(source)])
        first,second=[p[0] for p in protected.formulas]
        for wrong in (protected.text.replace(first,''),protected.text+first,
                      protected.text.replace(first,'SWAP').replace(second,first).replace('SWAP',second),
                      protected.text.replace(first,first.replace('_A]','_INVENTED]'))):
            with self.subTest(wrong=wrong),self.assertRaises(TranslationMismatch):protected.restore(wrong,'fixture')

    def test_research_windows_never_send_half_a_formula_or_exceed_the_budget(self):
        from pilot.research import passages
        from pilot.math_text import marked,BLOCKS
        text=('A rotor. '*25)+marked(r'\frac{19}{7}=3')+(' Following a rotor. '*80)
        for budget in (81,170,500,900,2000):
            rows=passages(text,'rotor',budget)
            self.assertLessEqual(sum(len(row['text'].encode()) for row in rows),budget)
            for row in rows:
                self.assertEqual(row['text'],text[row['offset']:row['next_offset']])
                self.assertEqual(row['text'].count('```math'),len(list(BLOCKS.finditer(row['text']))))
                if r'\frac' in row['text']:self.assertEqual(len(list(BLOCKS.finditer(row['text']))),1)
        oversized=marked('x'*2400)
        self.assertFalse(any('x'*20 in row['text'] for row in passages('Rotor. '+oversized+' Rotor.', 'rotor',500)))

    def test_symbols_styles_and_invisible_multiplication_are_conserved(self):
        value=self.read('<math><mstyle mathvariant="bold"><mi>u</mi></mstyle><mo>\u2062</mo><mi>v</mi></math>')
        self.assertIn(r'\mathbf{u}',value);self.assertIn(r'\times',value)
        value=self.read('<math><mfrac linethickness="0"><mi>n</mi><mi>k</mi></mfrac></math>')
        self.assertIn(r'\genfrac{}{}{0pt}{}{n}{k}',value)

    def test_prefixed_math_and_generated_translation_pages_keep_formulas(self):
        from pilot.library import TranslationText
        from pilot.math_text import BLOCKS
        p=TranslationText();p.feed('<section id="page=1"><m:math><m:msub><m:mi>R</m:mi><m:mn>1</m:mn></m:msub></m:math></section>')
        self.assertIn(r'{R}_{1}',''.join(p.pages[1]));self.assertEqual(len(list(BLOCKS.finditer(p.text()))),1)


class FormulaPipelineTests(unittest.IsolatedAsyncioTestCase):
    async def test_article_reading_snapshot_and_passages_keep_the_same_equation(self):
        from pilot import library,store,document_text,research
        from pilot.math_text import BLOCKS
        raw=b'<html lang="en"><title>Fictional notice</title><article><p>Rotor test formula:</p><math><mi>k</mi><mo>=</mo><mfrac><mn>19</mn><mn>7</mn></mfrac></math></article></html>'
        with tempfile.TemporaryDirectory() as directory,patch.object(store,'ROOT',Path(directory)/'state'),\
             patch.object(library,'books',AsyncMock(return_value=[{'book':'fixture','language':'en','title':'Fixture'}])),\
             patch.object(library,'get',AsyncMock(return_value=(raw,'text/html'))):
            store.init();source=await library.source('zim:fixture/rotor')
            self.assertIn(r'\frac{19}{7}',source['text'])
            snapshot,parts=await document_text.extract(source['id'])
            self.assertEqual(''.join(text for _,text,_ in parts),source['text'])
            packet=await research.read([source['id']],'rotor test formula',5000,{},lambda row,read:{'number':1},fetch=AsyncMock(return_value=source))
            self.assertEqual(sum(len(list(BLOCKS.finditer(part['text']))) for row in packet['results'] for part in row['passages']),1)
            await library.kiwix_queries.close()


if __name__=='__main__':unittest.main()
