"""Real passage selection and byte budgets on tiny invented documents."""
import asyncio
from pathlib import Path
import tempfile
import unittest
from unittest.mock import AsyncMock,patch

from pilot import engine,research,library,store


class PassageTests(unittest.TestCase):
    def test_initial_topic_is_separate_from_following_answer_instructions(self):
        for suffix in ('Compare les notices et cite leurs valeurs.','Donne une réponse en français.','Explain the differences.'):
            question='Fais une synthèse des documents sur la serre fictive. '+suffix
            self.assertEqual(research.primary_query(question),'Fais une synthèse des documents sur la serre fictive')
        question='Fais une synthèse sur le Dr. Martin et la mesure 2.5. Cite les sources.'
        self.assertEqual(research.primary_query(question),'Fais une synthèse sur le Dr. Martin et la mesure 2.5')
        self.assertEqual(research.primary_query('Capteur 2.5. Compare versions'),'Capteur 2.5. Compare versions')

    def test_answer_late_in_document_replaces_unrelated_introduction_with_exact_offsets(self):
        text=('Historique fictif sans rapport.\n'*300)+'\nCompost : la température fictive mesurée vaut 42 unités.\n'+('Autre contexte.\n'*60)
        parts=research.passages(text,'température du compost',1100)
        self.assertTrue(any('42 unités' in part['text'] for part in parts))
        self.assertTrue(any(part['offset']>5000 for part in parts))
        for part in parts:self.assertEqual(part['text'],text[part['offset']:part['next_offset']])
        self.assertLessEqual(sum(len(part['text'].encode()) for part in parts),1100)

    def test_bilingual_terms_reach_friction_without_requiring_french_in_source(self):
        text=('Introductory fictional background. '*200)+'Fire making by friction: fictional wood observation.'
        self.assertTrue(any('friction' in part['text'] for part in research.passages(text,'allumage du feu au frottement',1000)))

    def test_practical_section_precedes_history_even_when_both_mention_the_topic(self):
        text=('Histoire du générateur à pédales et évolution des objets. '*100)+'\nÉtapes de construction du générateur à pédales. Matériel fictif et outils inventés : repère ZETA, sans consigne de fabrication réelle.'
        parts=research.passages(text,'fabriquer un générateur à pédales',1000)
        self.assertTrue(any('ZETA' in part['text'] for part in parts))

    def test_whole_tiny_source_and_unicode_budget(self):
        text='Échantillon 🧭 et température.'
        self.assertEqual(research.passages(text,'température',500),[{'text':text,'offset':0,'next_offset':len(text)}])
        parts=research.passages(text*300,'température',700)
        self.assertLessEqual(sum(len(part['text'].encode()) for part in parts),700)
        for part in parts:self.assertNotIn('�',part['text'])

    def test_document_and_collection_diversity_keeps_all_remaining_matches(self):
        items=[{'id':'guide:a.pdf#page=1','collection':'A'},{'id':'guide:a.pdf#page=2','collection':'A'},
               {'id':'zim:a/other','collection':'A'},{'id':'zim:b/entry','collection':'B'}]
        order=research.candidates(items)
        self.assertEqual(order[0]['id'],items[0]['id']);self.assertEqual(order[1]['collection'],'B')
        self.assertEqual({row['id'] for row in order},{row['id'] for row in items})

    def test_reference_check_only_checks_markers_and_read_status(self):
        refs={};engine.reference(refs,{'id':'a','title':'A'},True);engine.reference(refs,{'id':'b','title':'B'})
        self.assertTrue(research.citations_valid('Passage [1]',refs))
        for value in ('Sans référence','[2]','[1] et [99]'):self.assertFalse(research.citations_valid(value,refs))


class ReadingTests(unittest.IsolatedAsyncioTestCase):
    async def test_selected_pdf_reaches_an_indexed_late_page_and_retains_its_page_identity(self):
        with tempfile.TemporaryDirectory() as directory,patch.object(store,'ROOT',Path(directory)):
            store.init()
            with store.connect() as db:
                for identifier,text in [('guide:notice.pdf','Préface seulement.'),('guide:notice.pdf#page=2','Contexte sans mesure.'),('guide:notice.pdf#page=48','Compost et température : valeur fictive 42 unités.'),('guide:other.pdf#page=49','Compost et température : autre mesure fictive 99 unités.')]:
                    table='passages' if '#page=' in identifier else 'documents'
                    db.execute('INSERT INTO '+table+' VALUES(?,?,?,?,?)',(identifier,'Notice fictive','/fixture.pdf','fr',text))
            refs={}
            packet=await research.read(['guide:notice.pdf'],'température du compost',4000,{},lambda item,read:engine.reference(refs,item,read))
            self.assertEqual(packet['results'][0]['id'],'guide:notice.pdf#page=48')
            self.assertIn('42 unités',packet['results'][0]['passages'][0]['text'])
            self.assertTrue(packet['results'][0]['partial_read']);self.assertNotIn('guide:other.pdf#page=49',refs)
            self.assertEqual(library.focused_page('guide:notice.pdf#page=2','température du compost'),'guide:notice.pdf#page=2')
            self.assertEqual(library.focused_page('guide:notice.pdf','sujet inexistant'),'guide:notice.pdf')

    async def test_five_distinct_sources_fit_and_all_refs_address_received_text(self):
        refs={};cache={}
        async def fetch(identifier):return {'id':identifier,'title':identifier,'text':identifier+'\n'+('Préface fictive. '*400)+'\nCompost et température : '+identifier}
        packet=await research.read(['guide:'+str(i) for i in range(5)],'température du compost',9000,cache,lambda item,read:engine.reference(refs,item,read),fetch=fetch)
        self.assertEqual(len(packet['results']),5);self.assertLessEqual(research.size(packet),9000)
        for row in packet['results']:
            self.assertTrue(refs[row['id']]['consulted']);self.assertEqual(row['number'],refs[row['id']]['number'])
            self.assertTrue(row['partial_read'])
            self.assertTrue(any('Compost' in part['text'] for part in row['passages']))
            for part in row['passages']:self.assertEqual(part['text'],cache[row['id']]['text'][part['offset']:part['next_offset']])

    async def test_failed_empty_and_duplicate_source_do_not_block_later_document(self):
        refs={};failed=[]
        async def fetch(identifier):
            if identifier=='bad':raise OSError('private failure')
            return {'id':identifier,'title':identifier,'text':'' if identifier=='empty' else 'same' if identifier in ('a','copy') else 'distinct source'}
        packet=await research.read(['bad','empty','a','copy','b'],'source',3000,{},lambda item,read:engine.reference(refs,item,read),fetch=fetch,on_failed=failed.append)
        self.assertEqual([row['id'] for row in packet['results']],['a','b'])
        self.assertEqual(set(failed),{'bad','empty'});self.assertEqual(packet['failed'],2)
        self.assertEqual(packet['omitted'],1);self.assertNotIn('copy',refs)

    async def test_small_context_omits_docs_without_marking_them_read_and_reuses_loaded_sources(self):
        refs={};cache={};fetch=AsyncMock(side_effect=lambda identifier:{'id':identifier,'title':identifier,'text':identifier+' '+('Document fictif. '*100)})
        packet=await research.read(['a','b','c'],'document',1100,cache,lambda item,read:engine.reference(refs,item,read),fetch=fetch)
        self.assertEqual(len(packet['results']),1);self.assertEqual(len(refs),1)
        self.assertEqual(packet['omitted'],2);self.assertTrue(packet['selection_limited'])
        await research.read(['a','b','c'],'document',6000,cache,lambda item,read:engine.reference(refs,item,read),fetch=fetch)
        self.assertEqual(fetch.await_count,3)

    async def test_limited_memory_does_not_load_any_document(self):
        fetch=AsyncMock()
        packet=await research.read(['a'],'source',100,{},lambda *_:None,fetch=fetch)
        self.assertEqual(packet['results'],[]);self.assertEqual(packet['omitted'],1);fetch.assert_not_awaited()

    async def test_ai_translation_retains_original_identity_and_notice(self):
        source={'id':'derived','title':'Traduction fictive','text':'Valeur fictive 12 unités.','is_ai_translation':True,
                'original_id':'guide:original.en.txt','original_title':'Original fixture','translation_notice':'Traduction non vérifiée.'}
        packet=await research.read(['derived'],'valeur',3000,{},lambda item,read:{'number':1},fetch=AsyncMock(return_value=source))
        row=packet['results'][0];self.assertTrue(row['is_ai_translation'])
        self.assertEqual(row['original_id'],source['original_id']);self.assertEqual(row['translation_notice'],source['translation_notice'])

    async def test_cancellation_propagates_without_marking_a_source_read(self):
        refs={};started=asyncio.Event()
        async def fetch(identifier):started.set();await asyncio.Event().wait()
        task=asyncio.create_task(research.read(['a'],'source',3000,{},lambda item,read:engine.reference(refs,item,read),fetch=fetch))
        await started.wait();task.cancel()
        with self.assertRaises(asyncio.CancelledError):await task
        self.assertEqual(refs,{})


if __name__=='__main__':unittest.main()
