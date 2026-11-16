"""Provider identity/timing policy, no network, decoder or model."""
import math
from types import SimpleNamespace
import unittest
from pilot import provider_subtitles as subtitles

ID='abcDEF_12-3'

def track(language,generated=False):return SimpleNamespace(language_code=language,language=language,is_generated=generated)


class ProviderSubtitleTests(unittest.TestCase):
    def test_only_video_ids_and_public_youtube_references_are_accepted(self):
        for value in (ID,'https://www.youtube.com/watch?v='+ID,'https://youtu.be/'+ID,'https://youtube.com/shorts/'+ID,'https://m.youtube.com/embed/'+ID):
            self.assertEqual(subtitles.video_id(value),ID)
        for value in ('http://youtube.com/watch?v='+ID,'https://localhost/watch?v='+ID,'https://youtube.com.invalid/watch?v='+ID,
                      'https://user:pass@youtube.com/watch?v='+ID,'https://youtube.com:8443/watch?v='+ID,
                      'https://youtube.com/watch?v='+ID+'&v='+ID,'https://youtu.be/../'+ID,True,None):
            with self.subTest(value=value),self.assertRaises(ValueError):subtitles.video_id(value)

    def test_metadata_cannot_turn_an_arbitrary_extractor_id_into_youtube(self):
        self.assertEqual(subtitles.identity({'source':{'extractor':'Youtube','id':ID}}),{'id':ID,'basis':'source_metadata'})
        with self.assertRaisesRegex(ValueError,'source_reference_required'):subtitles.identity({'source':{'extractor':'another-site','id':ID}})
        self.assertEqual(subtitles.identity({'source':{'url':'https://youtu.be/'+ID}})['basis'],'source_url')
        self.assertEqual(subtitles.identity({},ID)['basis'],'user_reference')

    def test_available_french_then_speech_language_and_human_within_language(self):
        french=track('fr');automatic=track('fr',True);english=track('en');spanish=track('es')
        self.assertIs(subtitles.choose([english,automatic,french],'en'),french)
        self.assertIs(subtitles.choose([spanish,english],'es'),spanish)
        self.assertIs(subtitles.choose([track('de'),english]),english)
        self.assertEqual(subtitles.metadata(automatic)['origin'],'automatic')
        with self.assertRaisesRegex(ValueError,'no_provider_captions'):subtitles.choose([])

    def test_display_overlap_is_shortened_without_losing_words_or_changing_starts(self):
        rows=[{'start':1.2,'duration':5,'text':'Do not open.'},{'start':3.5,'duration':2,'text':'Blue rotor 17 mm.'}]
        cues,changes=subtitles.checked_cues(rows)
        self.assertEqual(cues,[{'start_ms':1200,'end_ms':3500,'text':'Do not open.'},{'start_ms':3500,'end_ms':5500,'text':'Blue rotor 17 mm.'}])
        self.assertEqual(changes,[{'position':0,'kind':'display_end_clipped','original_end_ms':6200,'end_ms':3500}])
        self.assertEqual(rows[0]['duration'],5)

    def test_equal_starts_join_text_and_keep_the_original_longest_end(self):
        cues,changes=subtitles.checked_cues([{'start':1,'duration':2,'text':'First line'},{'start':1,'duration':3,'text':'Not the second part.'}])
        self.assertEqual(cues,[{'start_ms':1000,'end_ms':4000,'text':'First line\nNot the second part.'}])
        self.assertEqual(changes,[{'position':1,'kind':'same_start_joined'}])

    def test_malformed_timing_text_or_order_is_not_published_as_empty(self):
        bad=[[],[{'start':True,'duration':1,'text':'x'}],[{'start':1,'duration':math.nan,'text':'x'}],
             [{'start':2,'duration':1,'text':'Second'},{'start':1,'duration':1,'text':'First'}],
             [{'start':0,'duration':1,'text':''}],[{'start':0,'duration':1,'text':'\x00'}],
             [{'start':0,'duration':1,'text':'a'*4000},{'start':0,'duration':1,'text':'b'*4000}]]
        for rows in bad:
            with self.subTest(rows=str(rows)[:100]),self.assertRaises(ValueError):subtitles.checked_cues(rows)


class ProviderRetrievalTests(unittest.TestCase):
    def environment(self,*,url='https://www.youtube.com/watch?v='+ID,large=False,track_language='fr'):
        import contextlib
        import importlib.metadata
        import itertools
        import sys
        from unittest.mock import patch
        calls=[];closed=[]
        class Response:
            def iter_content(self,size):
                yield from itertools.repeat(b'x'*65536,306) if large else (b'fixture',)
            def close(self):closed.append(True)
        class Session:
            def __enter__(self):return self
            def __exit__(self,*args):pass
            def send(self,request,**kw):calls.append((request.url,kw));return Response()
        class API:
            def __init__(self,http_client):self.http_client=http_client
            def list(self,identifier):
                assert identifier==ID and not self.http_client.trust_env and self.http_client.max_redirects==4
                self.http_client.send(SimpleNamespace(url=url))
                french=track(track_language);french.fetch=lambda:SimpleNamespace(to_raw_data=lambda:[{'start':1,'duration':2,'text':'Ne pas ouvrir le capot.'}])
                return [french]
        stack=contextlib.ExitStack();stack.enter_context(patch.dict(sys.modules,{'requests':SimpleNamespace(Session=Session),'youtube_transcript_api':SimpleNamespace(YouTubeTranscriptApi=API)}))
        stack.enter_context(patch.object(importlib.metadata,'version',return_value='1.2.4-fixture'))
        return stack,calls,closed

    def test_explicit_fetch_keeps_provenance_original_rows_and_complete_checked_track(self):
        context,calls,closed=self.environment()
        with context:result=subtitles.retrieve(ID,'en')
        self.assertEqual(result['track']['origin'],'provided');self.assertEqual(result['track']['language'],'fr')
        self.assertEqual(result['cues'][0]['text'],'Ne pas ouvrir le capot.');self.assertEqual(result['raw_provider_cues'][0]['start'],1)
        self.assertFalse(result['online_translation_requested']);self.assertEqual(result['human_review'],'not_performed')
        self.assertEqual(calls[0][1],{'timeout':(10,15),'stream':True});self.assertEqual(closed,[True])

    def test_french_choice_accepts_a_provider_regional_variant_and_honors_origin(self):
        context,calls,closed=self.environment(track_language='fr-FR')
        with context:result=subtitles.retrieve(ID,language='fr',origin='provided')
        self.assertEqual(result['track']['language'],'fr-FR')
        context,calls,closed=self.environment(track_language='fr-FR')
        with context,self.assertRaisesRegex(ValueError,'provider_track_unavailable'):subtitles.retrieve(ID,origin='automatic')

    def test_arbitrary_endpoint_is_rejected_before_transport(self):
        context,calls,closed=self.environment(url='https://127.0.0.1/private')
        with context,self.assertRaisesRegex(ValueError,'unexpected_provider_endpoint'):subtitles.retrieve(ID)
        self.assertEqual(calls,[]);self.assertEqual(closed,[])

    def test_oversized_response_is_closed_and_not_returned_as_empty_captions(self):
        context,calls,closed=self.environment(large=True)
        with context,self.assertRaisesRegex(ValueError,'provider_response_too_large'):subtitles.retrieve(ID)
        self.assertEqual(len(calls),1);self.assertEqual(closed,[True])
