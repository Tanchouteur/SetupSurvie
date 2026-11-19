"""Quality gates on realistic tiny text; no inference or downloaded corpus."""
import asyncio
import json
import unittest
from unittest.mock import AsyncMock,patch
from pilot import translation_quality as quality,translations,store,publications
import test_translations as fixtures


class TokenChecksTests(unittest.TestCase):
    def test_protected_references_restore_exactly_and_reject_bad_anchors(self):
        from pilot.math_text import marked
        original='See https://example.org/a?q=2. DOI: 10.1234/abc-42\n'+marked('https://example.org/3')
        protected=quality.ProtectedReferences(original)
        self.assertEqual(len(protected.references),2)
        self.assertFalse(protected.only_references)
        self.assertEqual(protected.restore(protected.text),original)
        first,second=(item[0] for item in protected.references)
        for candidate in (protected.text.replace(first,''),protected.text.replace(first,first+first),protected.text.replace(first,'[broken]'),protected.text.replace(first,'TEMP').replace(second,first).replace('TEMP',second)):
            with self.assertRaises(ValueError):protected.restore(candidate)
        for text in ('https://example.org/path.', '10.1234/abc', 'Smith, J. (2020). A fictional title.'):
            reference=quality.ProtectedReferences(text)
            self.assertTrue(reference.only_references)
            self.assertEqual(reference.restore(reference.text),text)
        self.assertFalse(quality.ProtectedReferences('Water boils at 100 degrees.').references)
        self.assertFalse(quality.ProtectedReferences(marked('10.1234/abc')).references)

    def test_short_unchanged_english_and_reference_numbers(self):
        self.assertEqual(quality.assess('Keep the water clean.','Keep the water clean.',source_language='en')['status'],'blocked')
        self.assertNotEqual(quality.assess('https://example.org/123','https://example.org/123',source_language='en')['status'],'blocked')
        self.assertEqual(quality.assess('See figure 4.','Voir la figure 5.')['status'],'warning')
        self.assertEqual(quality.assess('Use 4 mg.','Utilisez 5 mg.')['status'],'blocked')

    def test_historical_ordinals_and_roman_centuries(self):
        source='World War 2 ended in the 20th century. The date was 1945.'
        target='La Seconde Guerre mondiale a fini au XXe siècle. La date était 1945.'
        self.assertEqual(quality.assess(source,target,source_language='en')['status'],'checked')
        self.assertEqual(quality.assess(source,target.replace('XXe','XIXe'),source_language='en')['status'],'warning')
        for changed in (target.replace('1945','1946'),target.replace('Seconde','Première')):
            self.assertEqual(quality.assess(source,changed,source_language='en')['status'],'blocked')

    def test_english_document_grouping_keeps_values_and_units(self):
        original='About 400,000 years ago. That is 1,500.25 meters.'
        correct='Il y a environ 400\u202f000 ans. Cela fait 1 500,25 mètres.'
        def assess(candidate):
            return quality.assess(original,candidate,source_language='eng',english_grouping=True)
        self.assertEqual(assess(correct)['status'],'checked')
        for candidate in (correct.replace('400\u202f000','400'),correct.replace('mètres','millimètres'),
                          correct.replace('1 500,25','1,50025')):
            self.assertEqual(assess(candidate)['status'],'blocked')
        french=quality.assess('La distance est de 400,000 mètres.','La distance est de 400 000 mètres.',
                             source_language='fr',english_grouping=True)
        self.assertEqual(french['status'],'blocked')

    def test_english_dollar_grouping_keeps_the_amount_and_other_decimal_checks(self):
        source='The budget is $70,000. Measure 70,000 ml.'
        for budget in ('70 000 dollars','$70,000'):
            result=quality.assess(source,f'Le budget est de {budget}. Mesurez 70 ml.',source_language='en-US')
            self.assertEqual(result['status'],'checked')
        for budget,measure in (('70 dollars','70 ml'),('70 000 dollars','70 000 ml')):
            result=quality.assess(source,f'Le budget est de {budget}. Mesurez {measure}.',source_language='en')
            self.assertEqual(result['status'],'blocked')
        self.assertEqual(quality.assess('Budget de 70,000 $.','Budget de 70 000 dollars.')['status'],'blocked')

    def test_formulas_keep_grouping_even_when_all_numbers_still_match(self):
        from pilot.math_text import marked
        source='Formula follows. '+marked(r'\frac{12}{4}=3')
        for formula in (r'\frac{4}{12}=3',r'12+4=3',r'\frac{12}{4}=3^{2}'):
            with self.subTest(formula=formula):
                report=quality.assess(source,'La formule suit. '+marked(formula))
                self.assertEqual(report['status'],'blocked')
                self.assertIn('formulas',{row['code'] for row in report['issues']})
        self.assertEqual(quality.assess(source,'La formule suit. '+marked(r'\frac{12}{4}=3'))['status'],'checked')
        self.assertEqual(quality.assess(source,'La formule a disparu.')['status'],'blocked')

    def test_missing_formula_warns_without_fabricating_a_replacement(self):
        from pilot.math_text import UNREADABLE
        for source in ('The current is '+UNREADABLE,'where    is the total current'):
            report=quality.assess(source,'La formule est à consulter dans l’original.')
            self.assertEqual(report['status'],'warning')
            self.assertIn('source_math_gaps',{row['code'] for row in report['issues']})

    def test_device_button_labels_are_kept_or_flagged_without_certifying_other_words(self):
        source='Press the CALL button. Press the EXIT key to cancel.'
        self.assertEqual(quality.assess(source,'Appuyez sur le bouton CALL. Appuyez sur EXIT pour annuler.')['status'],'checked')
        report=quality.assess(source,'Appuyez sur le bouton APPEL. Appuyez sur SORTIE pour annuler.')
        self.assertEqual(report['status'],'warning');self.assertEqual(report['issues'][0]['code'],'control_labels')

    def test_joined_pdf_labels_keep_their_numbers_when_french_restores_a_space(self):
        result=quality.assess('See Chapter4. The indicator X7 is off.','Voir le Chapitre 4. Le voyant X7 est éteint.')
        self.assertEqual(result['status'],'checked')
        self.assertEqual(quality.assess('See Chapter4. The indicator X7 is off.','Voir le Chapitre 5. Le voyant X7 est éteint.')['status'],'warning')
        self.assertEqual(quality.assess('See Chapter4. The indicator X7 is off.','Voir le Chapitre 4. Le voyant X8 est éteint.')['status'],'blocked')

    def test_numbers_and_units_allow_decimal_comma_spacing_and_translated_names(self):
        for source,target in [
            ('Use 1.5 liters for 1 000 grams.','Utilisez 1,5 litre pour 1000 grammes.'),
            ('At -10 °C, use 10–20 mm.','À −10 °C, utilisez 10 à 20 mm.'),
            ('Use 5 mg/kg. Wait 2 minutes.','Utilisez 5 mg/kg. Attendez 2 minutes.'),
            ('Use 5 mg / kg at 20 ° C.','Utilisez 5 mg/kg à 20 °C.'),
            ('Use 20 meters of cable.','Utilisez 20 mètres de câble.'),
            ('Pressure 1.00 bar.','Pression 1 bar.')]:
            with self.subTest(source=source):self.assertEqual(quality.assess(source,target)['status'],'checked')

    def test_unit_check_ignores_prose_after_a_reference_but_still_checks_amperes(self):
        self.assertEqual(quality.assess('Figure 4 shows the tray.',
            'La figure 4 a pour objet le plateau.')['status'],'checked')
        self.assertEqual(quality.assess('Observe panel 4 if it moves.',
            'Observez le panneau 4 s’il bouge.')['status'],'checked')
        self.assertEqual(quality.assess('The current is 4 A.',
            'Le courant est de 4 mA.')['status'],'blocked')
        self.assertEqual(quality.assess('47\nA fictional example begins here.',
            '47\nUn exemple fictif commence ici.')['status'],'checked')
        self.assertEqual(quality.assess('The current is 4\nA in the circuit.',
            'Le courant dans le circuit est de 4 mA.')['status'],'blocked')

    def test_numbered_ordinals_can_be_written_in_french_without_masking_a_missing_value(self):
        source='The students first note the 1st and 3rd marks. Wait 1 min.'
        for target in ('Les élèves notent d’abord les première et troisième marques. Attendez 1 min.',
                       'Les élèves notent d’abord les 1re et 3e marques. Attendez 1 min.'):
            self.assertEqual(quality.assess(source,target)['status'],'checked')
        for target in ('Les élèves notent les première et troisième marques. Attendez 1 min.',
                       'Les élèves notent d’abord les première et quatrième marques. Attendez 1 min.'):
            self.assertEqual(quality.assess(source,target)['status'],'warning')
        self.assertEqual(quality.assess(source,'Les élèves notent d’abord les première et troisième marques. Attendez une minute.')['status'],'blocked')
        self.assertEqual(quality.assess('See the 3rd tray.','Voir le bac 3.')['status'],'warning')

    def test_expand_ordinal_abbreviations_and_keep_the_missing_rank_blocked(self):
        source='Note the 1st shelf and the 3rd tray. It contains 7 pieces.'
        self.assertEqual(quality.spell_numbered_ordinals(source),
            'Note the first shelf and the third tray. It contains 7 pieces.')
        self.assertEqual(quality.spell_numbered_ordinals('See the 11th tray.'),'See the 11th tray.')
        report=quality.assess(source,'Notez l’étagère et le troisième bac. Il contient 7 pièces.')
        self.assertEqual([i['code'] for i in report['issues']],['ordinals'])
        self.assertEqual(report['status'],'warning')

    def test_critical_numeric_errors_are_blocked(self):
        for source,target in [
            ('Use 10 mg.','Utilisez 100 mg.'),
            ('Use 10 mg.','Utilisez 10 g.'),
            ('Use 10 mg/kg.','Utilisez 10 mg.'),
            ('Keep at -10 °C.','Conservez à 10 °C.'),
            ('Keep at - 10 °C.','Conservez à 10 °C.'),
            ('Ref 1234567890123456789012345678901.','Réf 1234567890123456789012345678902.'),
            ('Mix 2 liters then 2 liters.','Mélangez 2 litres.'),
            ('Use 2 liters.','Utilisez 2 litres pendant 5 minutes.'),
            ('Use 5 mg, then 10 ml.','Utilisez 10 mg, puis 5 ml.')]:
            with self.subTest(source=source):self.assertEqual(quality.assess(source,target)['status'],'blocked')

    def test_completeness_and_negation_signals_are_warnings_not_certificates(self):
        report=quality.assess('Do not touch the wire. '+'Disconnect the power and check the installation. '*10,'Touchez le fil.')
        self.assertEqual(report['status'],'warning')
        self.assertEqual({i['code'] for i in report['issues']},{'short','negation'})
        self.assertEqual(quality.assess('Do not touch.','Ne touchez pas.')['status'],'checked')
        # Same numbers cannot prove the meaning: deliberately document this limit.
        self.assertEqual(quality.assess('Heat to 20 °C.','Ne chauffez pas à 20 °C.')['status'],'checked')

    def test_unchanged_long_source_is_blocked(self):
        source='Disconnect the installation and check the cable. '*4
        self.assertEqual(quality.assess(source,source)['status'],'blocked')

    def test_missing_pdf_key_glyphs_warn_even_with_all_numbers_preserved(self):
        for text in ['Press the         key to enter the menu.', 'Enter                 on the numerical keypad.', 'Appuyez sur la touche         pour confirmer.', 'An unknown glyph: \ufffd.']:
            report=quality.assess(text,'Traduction fictive sans restitution des touches.')
            self.assertEqual(report['version'],quality.VERSION)
            self.assertIn('source_gaps',{row['code'] for row in report['issues']})
        self.assertNotIn('source_gaps',{row['code'] for row in quality.assess('Press the MENU key.','Appuyez sur MENU.')['issues']})


class QualityWorkerTests(unittest.IsolatedAsyncioTestCase):
    async def test_english_grouping_works_for_new_and_legacy_translation_jobs(self):
        from pilot import library
        (library.GUIDES/'manual.en.txt').write_text('About 400,000 years ago.',encoding='utf-8')
        library.index_guides()
        for legacy in (False,True):
            with self.subTest(legacy=legacy):
                item=await self.create()
                if legacy:
                    with store.connect() as db:
                        db.execute("UPDATE translation_publications SET source_meta='{}' WHERE translation_id=?",(item['id'],))
                with patch.object(translations,'publish_automatic',AsyncMock()),patch.object(translations,'translate',AsyncMock(return_value=('Il y a environ 400\u202f000 ans.','fixture'))):
                    await translations.run(item['id'])
                state=translations.status(item['id'],'alice')
                self.assertEqual((state['status'],state['done']),('completed',1))

    async def test_invalid_formula_anchors_keep_rejected_proposal_and_never_publish(self):
        from pilot.math_text import marked,TranslationMismatch
        source='Fictional equation. '+marked('19/7')
        with patch.object(translations,'extract',AsyncMock(return_value=({'id':'guide:test','title':'Fixture'},[(1,source,'pending')]))):
            item=await translations.create('alice','guide:test',None,'rapide')
        candidate='Repère supprimé.'
        with patch.object(translations,'translate',AsyncMock(side_effect=TranslationMismatch(candidate,'fixture'))):await translations.run(item['id'])
        result=translations.status(item['id'],'alice')
        self.assertEqual((result['status'],result['done'],result['deferred']),('completed',0,1))
        self.assertEqual(result['parts'][0]['candidate'],candidate)
        self.assertIn('formula_anchors',{i['code'] for i in result['parts'][0]['quality']['issues']})
    asyncSetUp=fixtures.TranslationTests.asyncSetUp
    asyncTearDown=fixtures.TranslationTests.asyncTearDown
    create=fixtures.TranslationTests.create
    async def test_formula_change_with_same_numbers_is_not_published(self):
        from pilot import library
        from pilot.math_text import marked
        source='Original fictional formula. '+marked(r'\frac{19}{7}')
        (library.GUIDES/'manual.en.txt').write_text(source);library.index_guides()
        item=await self.create()
        candidate='Formule fictive traduite. '+marked(r'\frac{7}{19}')
        with patch.object(translations,'translate',AsyncMock(return_value=(candidate,'fixture'))):await translations.run(item['id'])
        result=translations.status(item['id'],'alice')
        self.assertEqual((result['status'],result['done'],result['deferred']),('completed',0,1))
        self.assertIn('formulas',{i['code'] for i in result['parts'][0]['quality']['issues']})
        self.assertEqual(result['parts'][0]['candidate'],candidate)
        self.assertIsNone(result['publication']['source_id'])
    async def test_source_gaps_warning_survives_publication_and_export(self):
        from pilot import library
        (library.GUIDES/'manual.en.txt').write_text('Press the         key to enter the menu.',encoding='utf-8');library.index_guides()
        item=await self.create()
        with patch.object(translations,'translate',AsyncMock(return_value=('Appuyez sur la touche         pour accéder au menu.','fixture'))):await translations.run(item['id'])
        state=translations.status(item['id'],'alice');self.assertEqual(state['status'],'completed');self.assertEqual(state['quality']['warnings'],1)
        self.assertIn('touches dessinées',translations.export(item['id'],'alice'))
        published=await library.source(state['publication']['source_id'])
        self.assertIn('touches dessinées',published['text'])
    async def test_bad_measure_stays_private_and_retry_uses_original_snapshot(self):
        (self.root/'guides/manual.en.txt').write_text('Use 10 mg. Do not exceed the limit.',encoding='utf-8')
        from pilot import library
        library.index_guides();item=await self.create()
        with patch.object(translations,'translate',AsyncMock(return_value=('Utilisez 100 mg. Ne dépassez pas la limite.','fixture'))):
            await translations.run(item['id'])
        state=translations.status(item['id'],'alice')
        self.assertEqual((state['status'],state['done'],state['deferred']),('completed',0,1))
        self.assertEqual(state['parts'][0]['translated'],'')
        self.assertIn('100 mg',state['parts'][0]['candidate'])
        self.assertEqual(state['quality']['blocked'],1)
        self.assertEqual(state['parts'][0]['quality']['model'],'fixture')
        self.assertIsNone(state['publication']['source_id'])
        self.assertIn('passage refusé',translations.export(item['id'],'alice'))
        store.init()
        self.assertEqual(translations.status(item['id'],'alice')['quality']['blocked'],1)
        with patch.object(translations,'launch'):await translations.resume(item['id'],'alice','moyenne')
        with patch.object(translations,'translate',AsyncMock(return_value=('Utilisez 10 mg. Ne dépassez pas la limite.','fixture-two'))):
            await translations.run(item['id'])
        state=translations.status(item['id'],'alice')
        self.assertEqual(state['status'],'completed');self.assertEqual(state['quality']['blocked'],0)
        self.assertEqual(state['parts'][0]['candidate'],'');self.assertEqual(state['quality']['checked'],1)
        self.assertIsNotNone(state['publication']['source_id'])

    async def test_warning_is_visible_in_saved_status_export_and_public_document(self):
        item=await self.create()
        with patch.object(translations,'translate',AsyncMock(return_value=('Gardez l’eau propre.','fixture'))):await translations.run(item['id'])
        state=translations.status(item['id'],'alice')
        self.assertGreater(state['quality']['warnings'],0)
        self.assertIn('beaucoup plus courte',translations.export(item['id'],'alice'))
        from pilot import library
        content=(library.GUIDES/state['publication']['source_id'].removeprefix('guide:')).read_text(encoding='utf-8')
        self.assertIn('À relire',content);self.assertIn('aucune relecture humaine',content)
        self.assertNotIn('Keep water clean',content)

    async def test_failed_checker_cannot_accept_passage_or_break_the_other_documents(self):
        item=await self.create()
        with patch.object(translations,'translate',AsyncMock(return_value=('Texte français.','fixture'))),patch.object(quality,'assess',side_effect=RuntimeError('fixture checker failure')):
            await translations.run(item['id'])
        state=translations.status(item['id'],'alice')
        self.assertEqual(state['status'],'error');self.assertEqual(state['done'],0)
        from pilot import library
        self.assertEqual((await library.source(self.source))['id'],self.source)

    async def test_legacy_completed_translation_is_not_claimed_checked(self):
        item=await self.create()
        with store.connect() as db:
            db.execute("UPDATE translation_parts SET status='done',translated='Texte ancien.' WHERE translation_id=?",(item['id'],))
        state=translations.status(item['id'],'alice')
        self.assertEqual(state['parts'][0]['quality']['status'],'unchecked')
        self.assertIn('aucun contrôle automatique',translations.export(item['id'],'alice'))

    async def test_publication_rechecks_checked_parts_before_writing_public_file(self):
        item=await self.create()
        with patch.object(translations,'translate',AsyncMock(return_value=('Gardez l’eau propre.','fixture'))),patch.object(publications,'automatic',AsyncMock()):
            await translations.run(item['id'])
        with store.connect() as db:
            db.execute("UPDATE translation_parts SET translated='Ajout de 999 mg.' WHERE translation_id=? AND position=0",(item['id'],))
        from fastapi import HTTPException
        with self.assertRaises(HTTPException) as error:await publications.publish(item['id'],'alice')
        self.assertEqual(error.exception.status_code,409)
        from pilot import library
        self.assertFalse((library.GUIDES/('TRAD-'+item['id']+'.fr.html')).exists())
        self.assertEqual(translations.status(item['id'],'alice')['status'],'completed')


if __name__=='__main__':unittest.main()
