"""Timing/protocol regressions without an ASR model or audio dependency."""
import io
import json
from pathlib import Path
from types import SimpleNamespace
import tempfile
import unittest
from unittest.mock import patch
from pilot import speech_worker as speech


def word(start,end,text):return SimpleNamespace(start=start,end=end,word=text)
def segment(start,end,words=None,text='fallback'):
    return SimpleNamespace(start=start,end=end,words=words,text=text,avg_logprob=-.2,no_speech_prob=.01,compression_ratio=1.1)


class SpeechWorkerTests(unittest.TestCase):
    def test_midpoint_ownership_keeps_boundary_words_once_with_original_timeline(self):
        part=segment(59,61,[word(59.5,60.2,' Before'),word(60.1,60.8,' after')])
        left,raw,_=speech.aligned_cues([part],0,0,60000)
        right,_,_=speech.aligned_cues([part],0,60000,120000)
        self.assertEqual(left,[{'start_ms':59500,'end_ms':60000,'text':'Before'}])
        self.assertEqual(right,[{'start_ms':60100,'end_ms':60800,'text':'after'}])
        self.assertEqual(raw[0]['end_ms'],61000)

    def test_overlap_context_is_offset_before_ownership_and_preserves_negation(self):
        cues,_,warnings=speech.aligned_cues([segment(1,4,[word(1,2,' Do'),word(2,3,' not'),word(3,4,' open.')])],58000,60000,120000)
        self.assertEqual(cues,[{'start_ms':60000,'end_ms':62000,'text':'not open.'}]);self.assertEqual(warnings,[])

    def test_estimated_segment_fallback_is_explicit_and_clipped(self):
        cues,_,warnings=speech.aligned_cues([segment(0,3,text='Fallback words')],59000,60000,120000)
        self.assertEqual(cues,[{'start_ms':60000,'end_ms':62000,'text':'Fallback words'}])
        self.assertEqual(warnings,['word_timestamps_unavailable'])

    def test_recognition_overlap_remains_an_anomaly(self):
        cues,_,warnings=speech.aligned_cues([segment(1,3,[word(1,3,'first')]),segment(2,4,[word(2,4,'second')])],0,0,60000)
        self.assertEqual(len(cues),2);self.assertEqual(warnings,['recognition_overlap'])

    def test_long_silence_inside_recognizer_segment_becomes_separate_cues(self):
        cues,_,warnings=speech.aligned_cues([segment(6,59,[word(6,7,' blue'),word(7,8,' wheel.'),word(57,59,' Final check.')])],60000,60000,120000)
        self.assertEqual(cues,[{'start_ms':66000,'end_ms':68000,'text':'blue wheel.'},{'start_ms':117000,'end_ms':119000,'text':'Final check.'}])
        self.assertEqual(warnings,[])

    def test_local_input_refuses_remote_relative_missing_and_link_paths(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'own.wav';path.write_bytes(b'fixture');self.assertEqual(speech.local(str(path)),path)
            for name in ('https://invalid.example/audio.mp4','own.wav',str(path.with_name('missing.wav'))):
                with self.subTest(name=name),self.assertRaises(ValueError):speech.local(name)
            link=path.with_name('linked.wav')
            try:link.symlink_to(path)
            except OSError:return
            with self.assertRaises(ValueError):speech.local(link)

    def test_child_protocol_keeps_provider_output_and_exceptions_out_of_json(self):
        def dispatch(command):
            print('PRIVATE provider detail')
            if command['action']=='fail':raise RuntimeError('PRIVATE source path')
            return {'audio_present':False}
        output=io.StringIO()
        with patch.object(speech,'dispatch',dispatch),patch('sys.stdin',io.StringIO('{"action":"probe"}\n{"action":"fail"}\n')),patch('sys.stdout',output),patch('sys.stderr',io.StringIO()):speech.main()
        rows=[json.loads(line) for line in output.getvalue().splitlines()]
        self.assertTrue(rows[0]['ok']);self.assertEqual(rows[1],{'ok':False,'reason':'audio_processing_failed'})
        self.assertNotIn('PRIVATE',output.getvalue())
