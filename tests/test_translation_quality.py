"""Quality gates on realistic tiny text; no inference or downloaded corpus."""
import asyncio
import json
import unittest
from unittest.mock import AsyncMock,patch
from pilot import translation_quality as quality,translations,store,publications
import test_translations as fixtures


class TokenChecksTests(unittest.TestCase):
    def test_numbers_and_units_allow_decimal_comma_spacing_and_translated_names(self):
        for source,target in [
            ('Use 1.5 liters for 1 000 grams.','Utilisez 1,5 litre pour 1000 grammes.'),
            ('At -10 °C, use 10–20 mm.','À −10 °C, utilisez 10 à 20 mm.'),
            ('Use 5 mg/kg. Wait 2 minutes.','Utilisez 5 mg/kg. Attendez 2 minutes.'),
            ('Use 5 mg / kg at 20 ° C.','Utilisez 5 mg/kg à 20 °C.'),
            ('Use 20 meters of cable.','Utilisez 20 mètres de câble.'),
            ('Pressure 1.00 bar.','Pression 1 bar.')]:
            with self.subTest(source=source):self.assertEqual(quality.assess(source,target)['status'],'checked')

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
            self.assertEqual(report['version'],2)
            self.assertIn('source_gaps',{row['code'] for row in report['issues']})
        self.assertNotIn('source_gaps',{row['code'] for row in quality.assess('Press the MENU key.','Appuyez sur MENU.')['issues']})


class QualityWorkerTests(unittest.IsolatedAsyncioTestCase):
    asyncSetUp=fixtures.TranslationTests.asyncSetUp
    asyncTearDown=fixtures.TranslationTests.asyncTearDown
    create=fixtures.TranslationTests.create
    async def test_source_gaps_warning_survives_publication_and_export(self):
        from pilot import library
        (library.GUIDES/'manual.en.txt').write_text('Press the         key to enter the menu.',encoding='utf-8');library.index_guides()
        item=await self.create()
        with patch.object(translations,'translate',AsyncMock(return_value=('Appuyez sur la touche         pour accéder au menu.','fixture'))):await translations.run(item['id'])
        state=translations.status(item['id'],'alice');self.assertEqual(state['status'],'completed');self.assertEqual(state['quality']['warnings'],1)
        self.assertIn('touches dessinées',translations.export(item['id'],'alice'))
        published=await library.source(state['publication']['source_id'])
        self.assertIn('touches dessinées',published['text'])
    async def test_bad_measure_stays_pending_private_and_retry_uses_original_snapshot(self):
        (self.root/'guides/manual.en.txt').write_text('Use 10 mg. Do not exceed the limit.',encoding='utf-8')
        from pilot import library
        library.index_guides();item=await self.create()
        with patch.object(translations,'translate',AsyncMock(return_value=('Utilisez 100 mg. Ne dépassez pas la limite.','fixture'))):
            await translations.run(item['id'])
        state=translations.status(item['id'],'alice')
        self.assertEqual(state['status'],'error');self.assertEqual(state['done'],0)
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
