"""Original identity/captions and constrained selection, without vision or model."""
import json
import unittest
from unittest.mock import AsyncMock
from pilot import engine,illustrations as vi,research,citation_links


class IllustrationTests(unittest.IsolatedAsyncioTestCase):
    def test_captions_nested_markup_and_old_thumbnails_stay_with_their_image(self):
        html='''<nav><img src="logo.png"></nav><figure><img src="../I/diagram.svg" alt="Schéma"><figcaption>Montage <strong>17 mm</strong> — garder la protection.</figcaption></figure><div class="thumb"><div><img src="../I/other.png"></div><div class="thumbcaption">Autre légende.</div></div>'''
        images=vi.html_images(html,'/content/book/A/article')
        self.assertEqual(len(images),2);self.assertEqual(images[0]['id'],'zim:book/I/diagram.svg')
        self.assertEqual(images[0]['caption'],'Montage 17 mm — garder la protection.')
        self.assertEqual(images[1]['caption'],'Autre légende.');self.assertNotIn('logo',str(images))

    def test_external_cross_archive_query_traversal_and_duplicate_media_are_ignored(self):
        html=''.join('<img src="'+value+'">' for value in ['https://outside.invalid/a.png','//outside.invalid/img','/content/other/I/img.png','/content/book/%252e%252e/private','/content/book/I/good.png?x=2','/content/book/I/good.png','/content/book/I/good.png'])
        self.assertEqual([row['id'] for row in vi.html_images(html,'/content/book/A/topic')],['zim:book/I/good.png'])

    def test_page_candidates_preserve_whole_pdf_and_only_known_pages(self):
        source={'id':'guide:manual.pdf#page=21','title':'Notice','classification':{'revision':'a'*64}}
        self.assertEqual(vi.candidates(source)[0]['id'],source['id']);self.assertEqual(vi.candidates(source)[0]['revision'],'a'*64)
        self.assertEqual(vi.candidates({'id':'guide:manual.pdf'}),[])
        self.assertEqual([row['page'] for row in vi.candidates({'id':'guide:manual.pdf','pages':[21,True,0,1201]})],[21])

    async def test_selection_accepts_only_known_ids_and_consulted_sources(self):
        refs={};source={'id':'zim:book/A/topic','title':'Original','text':'Valeur 17 mm.', 'images':[{'id':'zim:book/I/diagram.png','alt':'Schéma technique','caption':'17 mm.'}]}
        engine.reference(refs,source,True,visual=True);engine.reference(refs,{'id':'zim:book/A/unread','title':'Not read','images':source['images']},visual=True)
        inference=AsyncMock(return_value={'selected':['v0']})
        report=await vi.choose('Montre le schéma',refs,inference,5000)
        self.assertEqual(report['selected'],1);self.assertEqual(refs[source['id']]['figures'][0]['id'],'zim:book/I/diagram.png')
        self.assertNotIn('figure_status',refs['zim:book/A/unread'])
        packet=json.loads(inference.await_args.args[0][-1]['content']);self.assertEqual(len(packet['candidates']),1)
        self.assertIn('17 mm',packet['candidates'][0]['source_excerpt'])
        self.assertEqual(engine.cited_sources('Voici le visuel.',refs)[0]['id'],source['id'])
        self.assertNotIn('figure_candidates',engine.read_references(refs)[0])
        for value in ({'selected':['unknown']},{'selected':['v0','v0']},{'selected':[True]},{'selected':['https://outside.invalid/img']}):
            with self.assertRaises(ValueError):vi.selection(value,vi.collect(refs))

    async def test_no_candidate_or_insufficient_context_does_not_call_a_model(self):
        infer=AsyncMock();refs={};engine.reference(refs,{'id':'guide:notice.txt','title':'Text only','text':'Known text'},True,visual=True)
        self.assertEqual((await vi.choose('Schéma',refs,infer,1000))['status'],'none');infer.assert_not_awaited()
        refs['guide:notice.txt']['figure_candidates']=[{'kind':'pdf_page','id':'guide:x.pdf#page=2','caption':'x'*5000}]
        self.assertEqual((await vi.choose('Schéma',refs,infer,1))['status'],'unavailable');infer.assert_not_awaited()

    def test_relevant_late_caption_is_selected_before_a_large_list_of_logos(self):
        refs={};source={'id':'zim:book/A/topic','title':'Notice','text':'Fictional source',
            'images':[{'id':'zim:book/I/logo-'+str(i)+'.png','alt':'Logo sans rapport'} for i in range(80)]+[{'id':'zim:book/I/late.svg','caption':'Montage du générateur à pédales'}]}
        engine.reference(refs,source,True,visual=True)
        selected=vi.collect(refs,question='Montre le schéma du générateur à pédales')
        self.assertEqual(selected[0]['id'],'zim:book/I/late.svg');self.assertLessEqual(len(selected),24)

    def test_showing_instruction_is_separated_from_literal_technical_topic(self):
        self.assertEqual(vi.topic('Montre-moi un schéma du générateur à pédales'),'générateur à pédales')
        self.assertEqual(vi.topic('schéma électrique'),'schéma électrique')
        self.assertFalse(vi.requested('Prépare un plan de lecture.'))
        self.assertTrue(vi.requested('Montre les schémas de ces documents.'))

    def test_composite_citations_include_all_sources_but_not_pages_or_literal_code(self):
        answer='Source [1, p. 21], autre [2; 3], exemple `tableau[99, p. 4]`.'
        self.assertEqual(research.citation_numbers(answer),{1,2,3})
        refs={'a':{'number':1,'consulted':True},'b':{'number':2,'consulted':True}}
        self.assertFalse(research.citations_valid('Texte [1] et source inventée [99, p. 21].',refs))
        self.assertTrue(research.citations_valid('Texte [1, p. 21] et [2].',refs))
        self.assertIn('[référence non vérifiée]',citation_links.unverified(answer,refs))
        self.assertIn('`tableau[99, p. 4]`',citation_links.unverified(answer,refs))
