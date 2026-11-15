"""Reader scope on synthetic HTML, not a particular vendor's markup."""
import unittest
from pilot.library import Text,TranslationText
from pilot import retrieval


class HTMLMainContentTests(unittest.TestCase):
    def test_main_article_preserves_content_metadata_math_and_table_without_search_panel(self):
        html='''<html lang="fr"><title>Notice originale</title><div>Sommaire et menus sans rapport</div><main><article><h1>Fonctionnement</h1><p>Pour commencer, garder 5 V ; ensuite 1 V.</p><table><tr><td>75 V</td><td>15 A</td></tr></table><math alttext="L=c/f"><mi>L</mi></math></article><article>Aucun résultat trouvé</article></main></html>'''
        text=Text();text.feed(html);value=text.text()
        for expected in ('Fonctionnement','5 V','1 V','75 V','15 A','L=c/f'):self.assertIn(expected,value)
        self.assertNotIn('Aucun résultat',value);self.assertNotIn('Sommaire',value)
        self.assertEqual(text.language,'fr');self.assertEqual(''.join(text.title),'Notice originale')

    def test_plain_pages_and_generated_multi_page_translations_keep_their_content(self):
        plain=Text();plain.feed('<h1>Guide ancien</h1><p>Texte principal et mesures 17 mm.</p>')
        self.assertIn('mesures 17 mm',plain.text())
        translation=TranslationText();translation.feed('<article><section id="page=1">Première page.</section></article><article><section id="page=2">Seconde page et avertissement.</section></article>')
        self.assertIn('Première page',translation.text());self.assertIn('Seconde page',translation.text())
        self.assertEqual(set(translation.pages),{1,2})

    def test_radio_and_antenna_guides_are_not_hidden_from_the_practical_space(self):
        self.assertIn('resilience',retrieval.domains({'title':'Notice radio de communication'}))
        self.assertIn('resilience',retrieval.domains({'title':'Longueur des antennes'}))
        self.assertEqual(set(retrieval.domains({'title':'Histoire de la radio'})),{'resilience','culture'})
