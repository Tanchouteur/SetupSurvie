"""Small synthetic sidecars and fake media bytes; no decoder, network or model."""
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

SCRIPT = Path(__file__).resolve().parents[1] / 'scripts/library_videos.py'
SPEC = importlib.util.spec_from_file_location('library_videos', SCRIPT)
videos = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(videos)
SRT = '1\n00:00:00,000 --> 00:00:01,000\nBonjour\n'
VTT = 'WEBVTT\n\nchapitre\n00:00.000 --> 00:01.000 align:start\nHello\n'


class VideoInventoryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.root = self.base / 'library' / 'video'
        self.root.mkdir(parents=True)

    def write(self, name, data=b'fake media'):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data.encode('utf-8') if isinstance(data, str) else data)
        return path

    def info(self, name='cours', **extra):
        return self.write(name + '.info.json', json.dumps({
            'id': 'fictif', 'extractor_key': 'Youtube', 'title': 'Un cours fictif',
            'language': 'en', 'duration': 5, 'height': 480, 'channel': 'Chaîne fictive', **extra}))

    def one(self, **kwargs):
        result = videos.inventory(self.root, **kwargs)
        self.assertEqual(result['errors'], [])
        self.assertEqual(len(result['videos']), 1)
        return result['videos'][0]

    def test_french_available_does_not_validate_translation_or_sync(self):
        self.write('cours.mp4')
        self.info()
        self.write('cours.fr.srt', SRT)
        report = self.one()
        self.assertEqual(report['subtitle_status'], 'french_available')
        self.assertEqual(report['title'], 'Un cours fictif')
        self.assertEqual(report['media']['height_declared'], 480)
        self.assertIsNone(report['media']['audio_present'])
        self.assertEqual(report['tracks'][0]['technical_status'], 'passed')
        self.assertFalse(report['tracks'][0]['language_verified'])
        self.assertEqual(report['validation']['synchronization'], 'not_verified')
        self.assertEqual(report['validation']['translation'], 'not_verified')

    def test_source_only_vtt_and_origin_evidence(self):
        self.write('cours.webm')
        self.write('cours.en.vtt', VTT)
        self.info(requested_subtitles={'en': {'url': 'fictif:caption', 'filepath': r'C:\video\cours.en.vtt'}},
                  automatic_captions={'en': [{'url': 'fictif:caption'}]})
        report = self.one()
        self.assertEqual(report['subtitle_status'], 'source_only')
        self.assertEqual(report['tracks'][0]['origin'], 'automatic')
        self.assertEqual(report['tracks'][0]['cue_count'], 1)

    def test_remote_french_is_not_a_local_track(self):
        self.write('cours.mp4')
        self.info(subtitles={'fr': [{'url': 'fictif:remote'}]})
        report = self.one()
        self.assertEqual(report['subtitle_status'], 'missing')
        self.assertEqual(report['remote_tracks_advertised_only']['provided'], ['fr'])
        self.assertEqual(report['tracks'], [])

    def test_no_metadata_and_unknown_language_are_explicit(self):
        self.write('leçon finale.MP4')
        self.write('leçon finale.srt', SRT)
        report = self.one()
        self.assertEqual(report['title'], 'leçon finale')
        self.assertEqual(report['metadata']['status'], 'missing')
        self.assertEqual(report['subtitle_status'], 'unknown')
        self.assertIn('langue_source_inconnue', report['unknowns'])
        self.assertEqual(report['tracks'][0]['origin'], 'unknown')

    def test_non_source_language_not_called_source(self):
        self.write('cours.mp4')
        self.info()
        self.write('cours.de.vtt', VTT)
        self.assertEqual(self.one()['subtitle_status'], 'unknown')

    def test_corrupt_or_unexpected_metadata_does_not_abort(self):
        self.write('cours.mp4')
        for content in ('{broken', '[]', '{"duration":NaN,"language":[],"title":3}',
                        '{"requested_subtitles":{"en":7},"subtitles":[],"duration":true}',
                        r'{"title":"\ud800"}'):
            with self.subTest(content=content):
                self.write('cours.info.json', content)
                report = self.one()
                self.assertIsNone(report['media']['duration_seconds_declared'])
                json.dumps(report, allow_nan=False)

    def test_bom_crlf_regional_french_and_vtt_metadata(self):
        self.write('cours.mkv')
        self.info()
        self.write('cours.fr-CA.vtt', '\ufeffWEBVTT\r\nKind: captions\r\n\r\nNOTE note\r\n\r\n'
                   '00:00.000 --> 00:01.000\r\nBonjour\r\n')
        self.assertEqual(self.one()['subtitle_status'], 'french_available')

    def test_bad_subtitles_remain_invalid(self):
        cases = {
            'empty.srt': '',
            'reverse.srt': '1\n00:00:02,000 --> 00:00:01,000\nTexte',
            'emptycue.srt': '1\n00:00:00,000 --> 00:00:01,000\n<i></i>',
            'broken.srt': 'un texte sans intervalle',
            'range.srt': '1\n00:99:00,000 --> 00:99:01,000\nTexte',
            'overlap.srt': SRT + '\n2\n00:00:00,500 --> 00:00:02,000\nSuite',
            'unordered.srt': '1\n00:00:02,000 --> 00:00:03,000\nA\n\n' + SRT,
            'duration.srt': '1\n00:00:04,000 --> 00:00:06,000\nSuite',
            'header.vtt': '00:00.000 --> 00:01.000\nTexte',
            'joined.vtt': 'WEBVTT\n00:00.000 --> 00:01.000\nTexte',
            'unnumbered.srt': '00:00:00,000 --> 00:00:01,000\nTexte',
            'comma.vtt': 'WEBVTT\n\n00:00,000 --> 00:01,000\nTexte',
            'encoding.srt': b'\xff\xfe',
            'nul.srt': SRT + '\x00',
        }
        for filename, content in cases.items():
            with self.subTest(filename=filename):
                path = self.write(filename, content)
                self.assertEqual(videos.inspect_subtitle(path, 5)['technical_status'], 'invalid')
        self.write('cours.mp4')
        self.write('cours.fr.srt', cases['reverse.srt'])
        self.assertEqual(self.one()['subtitle_status'], 'invalid')

    def test_gaps_do_not_claim_missing_speech(self):
        path = self.write('gap.srt', SRT + '\n2\n00:00:03,000 --> 00:00:04,000\nSuite')
        report = videos.inspect_subtitle(path, 5)
        self.assertEqual(report['technical_status'], 'passed')
        self.assertEqual(report['gap_count'], 1)
        self.assertIn('intervalles_sans_texte_paroles_non_verifiees', report['warnings'])

    def test_very_large_integer_metadata_does_not_crash(self):
        self.write('cours.mp4')
        self.info(duration=10 ** 400)
        self.assertEqual(self.one()['media']['duration_seconds_declared'], 10 ** 400)

    def test_size_limit_is_bounded_and_marks_invalid(self):
        path = self.write('cours.fr.srt', SRT)
        with patch.object(videos, 'MAX_SIDECAR_BYTES', 10):
            self.assertIn('fichier_annexe_trop_gros', videos.inspect_subtitle(path)['errors'])

    def test_completed_names_with_pending_markers_are_excluded(self):
        for name in ('a.mp4.part', 'b.webm.ytdl', 'c.mp4.tmp', 'd.f137.mp4',
                     'e.mp4', 'e.mp4.part', 'f.webm', 'f.f248.webm.part',
                     'g.mp4', 'g.ytdl'):
            self.write(name)
        self.write('final.mp4')
        result = videos.inventory(self.root)
        self.assertEqual([v['path'] for v in result['videos']], ['final.mp4'])
        self.assertEqual(len(result['skipped']), 10)

    def test_recursive_matching_does_not_mix_prefixes_or_directories(self):
        for name in ('cours.mp4', 'cours.long.mp4', 'cours.en.mp4', 'autre/cours.mp4'):
            self.write(name)
        self.write('cours.en.srt', SRT)
        self.write('cours.long.fr.srt', SRT)
        self.write('autre/cours.fr.vtt', VTT)
        result = {r['path']: r for r in videos.inventory(self.root)['videos']}
        self.assertEqual(result['cours.mp4']['tracks'], [])
        self.assertEqual(len(result['cours.en.mp4']['tracks']), 1)
        self.assertEqual(result['cours.long.mp4']['subtitle_status'], 'french_available')
        self.assertEqual(len(result['autre/cours.mp4']['tracks']), 1)

    def test_identity_revision_and_source_grouping_preserve_copies(self):
        self.write('cours.mp4')
        self.write('copy/cours.mp4')
        self.info()
        self.info('copy/cours')
        first = videos.inventory(self.root, hash_media=True)
        second = videos.inventory(self.root, hash_media=True)
        self.assertEqual([{k: v for k, v in r.items() if k != 'generated_at'} for r in first['videos']],
                         [{k: v for k, v in r.items() if k != 'generated_at'} for r in second['videos']])
        self.assertEqual(len(first['videos']), 2)
        self.assertEqual(first['videos'][0]['media']['sha256'], hashlib.sha256(b'fake media').hexdigest())
        self.assertEqual(len(first['videos'][0]['same_source_paths']), 2)
        old_id = first['videos'][0]['inventory_id']
        self.write(first['videos'][0]['path'], b'new fake media')
        changed = videos.inventory(self.root, hash_media=True)['videos'][0]
        self.assertEqual(changed['inventory_id'], old_id)
        self.assertNotEqual(changed['media']['sha256'], first['videos'][0]['media']['sha256'])

    def test_symlinks_are_not_followed(self):
        self.write('cours.mp4')
        outside = self.base / 'outside'
        outside.mkdir()
        (outside / 'other.mp4').write_bytes(b'fake')
        try:
            (self.root / 'link').symlink_to(outside, target_is_directory=True)
            (self.root / 'linked.mp4').symlink_to(outside / 'other.mp4')
            (self.root / 'cours.fr.srt').symlink_to(outside / 'other.mp4')
        except OSError:
            self.skipTest('Symlinks unavailable on this host')
        result = videos.inventory(self.root)
        self.assertEqual(len(result['videos']), 1)
        self.assertEqual(result['videos'][0]['subtitle_status'], 'invalid')
        self.assertEqual(result['errors'][0]['reason'], 'lien_exclu')
        self.assertIn({'path': 'link', 'reason': 'lien_exclu'}, result['skipped'])

    def test_changing_media_or_unreadable_directory_is_reported(self):
        self.write('cours.mp4')
        original = videos.regular
        calls = 0

        def changing(path):
            nonlocal calls
            if path.suffix == '.mp4':
                calls += 1
                if calls == 2:
                    path.write_bytes(b'changed fake')
            return original(path)

        with patch.object(videos, 'regular', side_effect=changing):
            result = videos.inventory(self.root)
        self.assertEqual(result['videos'], [])
        self.assertEqual(result['errors'][0]['reason'], 'media_modifie_pendant_inventaire')

        def failed_walk(root, **kwargs):
            kwargs['onerror'](PermissionError(13, 'denied', str(root / 'blocked')))
            return iter(())

        with patch.object(videos.os, 'walk', side_effect=failed_walk):
            result = videos.inventory(self.root)
        self.assertEqual(result['errors'][0]['path'], 'blocked')
        self.assertFalse(result['exhaustive'])

    def test_cli_export_preserves_all_original_bytes_and_mtimes(self):
        self.write('cours.mp4')
        self.info()
        self.write('cours.fr.srt', SRT)
        before = {p: (p.read_bytes(), p.stat().st_mtime_ns) for p in self.root.iterdir()}
        output = self.base / 'reports'
        run = subprocess.run([sys.executable, str(SCRIPT), '--video-dir', str(self.root),
                              '--output-dir', str(output)], capture_output=True, text=True)
        self.assertEqual(run.returncode, 0, run.stderr)
        summary = json.loads((output / 'inventory.json').read_text(encoding='utf-8'))
        self.assertEqual(summary['video_count'], 1)
        report = json.loads((output / summary['videos'][0]['report']).read_text(encoding='utf-8'))
        self.assertEqual(report['subtitle_status'], 'french_available')
        self.assertEqual(before, {p: (p.read_bytes(), p.stat().st_mtime_ns) for p in self.root.iterdir()})
        self.assertEqual(videos.main(['--video-dir', str(self.root), '--output-dir', str(output)]), 2)

    def test_output_inside_source_and_missing_root_are_rejected(self):
        with self.assertRaises(ValueError):
            videos.export_reports(videos.inventory(self.root), self.root / 'reports')
        self.assertFalse((self.root / 'reports').exists())
        self.assertEqual(videos.main(['--video-dir', str(self.base / 'absent'),
                                     '--output-dir', str(self.base / 'report')]), 2)

    def test_incomplete_directories_and_orphans_are_visible(self):
        self.write('transfer.part/hidden.mp4')
        self.write('orphan.fr.srt', SRT)
        self.write('orphan.info.json', '{}')
        self.write('unknown.xyz', 'not examined')
        result = videos.inventory(self.root)
        self.assertEqual(result['videos'], [])
        self.assertEqual(result['skipped'][0]['reason'], 'repertoire_telechargement_incomplet')
        self.assertEqual(len(result['unexamined']), 3)

    def test_zero_byte_media_has_error_exit_with_summary(self):
        self.write('empty.mp4', b'')
        output = self.base / 'reports'
        self.assertEqual(videos.main(['--video-dir', str(self.root), '--output-dir', str(output)]), 1)
        summary = json.loads((output / 'inventory.json').read_text())
        self.assertEqual(summary['errors'][0]['reason'], 'media_vide')


if __name__ == '__main__':
    unittest.main()
