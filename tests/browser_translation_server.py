"""Browser fixture server only: tiny documents, fake identity and inference, no real accounts/model.
Run in an isolated test environment: python tests/browser_translation_server.py
"""
import asyncio
import os
from contextlib import closing
import json
import sqlite3
from pathlib import Path
import sys
import tempfile
import time
import zlib
BASE=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(BASE))
from fastapi.staticfiles import StaticFiles
from pilot import accounts,app as gateway,engine,library,operations,store,translations,learning,inventory,assistant_metrics,durable,documentary,summaries,illustrations
from pilot import videos,captions,transcriptions,caption_acquisition,provider_subtitles
import re
import shutil
engine.POLICY=BASE/'deploy/assistant-system.fr.txt'
temporary=tempfile.TemporaryDirectory(prefix='translation-browser-');root=Path(temporary.name)
store.ROOT=root/'state';library.GUIDES=root/'guides';library.GUIDES.mkdir()
inventory.ZIMS=root/'zim';inventory.ZIMS.mkdir()
videos.ROOT=root/'video'
acquisition_gate=None
acquisition_blocked=False
class AcquisitionWorker:
    async def fetch(self,command):
        if acquisition_gate:await acquisition_gate.wait()
        if acquisition_blocked:raise ValueError('provider_blocked')
        rows=[{'start':1,'duration':2,'text':'Fictional bearing 17 mm.'},{'start':4,'duration':2,'text':'Fictional bearing 19 mm.'}]
        cues,changes=provider_subtitles.checked_cues(rows)
        return {'video_id':command['id'],'provider':'youtube','tool_version':'fixture','track':{'language':'en','origin':'provided'},
            'available_tracks':[],'raw_provider_cues':rows,'cues':cues,'timing_adjustments':changes,'human_review':'not_performed','online_translation_requested':False}
    async def close(self):pass
caption_acquisition.FetchWorker=AcquisitionWorker

@gateway.app.post('/fixture/acquisitions')
async def fixture_acquisitions(hold:bool=True,blocked:bool=False,enabled:bool=True,reset:bool=False):
    global acquisition_gate,acquisition_blocked
    await caption_acquisition.stop_all();acquisition_gate=asyncio.Event() if hold else None;acquisition_blocked=blocked
    videos.ROOT.mkdir(exist_ok=True)
    if reset:
        with caption_acquisition.connect() as db:db.execute('DELETE FROM jobs')
    if enabled and (reset or not (videos.ROOT/'acquisition.webm').exists()):
        shutil.copyfile(BASE/'tests/fixtures/video/solid-green.webm',videos.ROOT/'acquisition.webm')
        (videos.ROOT/'acquisition.info.json').write_text(json.dumps({'title':'Récupération source fictive','language':'en','duration':12,'extractor':'Youtube','id':'abcDEF_12-3'}))
    elif not enabled:
        for path in videos.ROOT.glob('acquisition.*'):path.unlink()
    videos.STOP.clear();await asyncio.to_thread(videos.scan);return {'ready':enabled}

@gateway.app.post('/fixture/acquisitions-release')
async def fixture_acquisitions_release():
    global acquisition_gate,acquisition_blocked
    acquisition_blocked=False
    if acquisition_gate:acquisition_gate.set()
    acquisition_gate=None;return {'released':True}

@gateway.app.post('/fixture/videos')
def fixture_videos(extra_track:bool=False):
    videos.ROOT.mkdir(exist_ok=True)
    shutil.copyfile(BASE/'tests/fixtures/video/solid-green.webm',videos.ROOT/'cours.webm')
    shutil.copyfile(BASE/'tests/fixtures/video/solid-green.webm',videos.ROOT/'sans-piste.webm')
    (videos.ROOT/'cours.info.json').write_text(json.dumps({'title':'Fabrication du rotor fictif','language':'en','duration':12,'channel':'Chaîne de test','description':'Vidéo synthétique, aucun guide pratique.'}))
    (videos.ROOT/'cours.fr.srt').write_text('1\n00:00:01,000 --> 00:00:03,000\nIntroduction fictive.\n\n2\n00:00:08,000 --> 00:00:10,000\nMontage du rotor fictif, cote inventée 17 mm.\n')
    (videos.ROOT/'cours.en.vtt').write_text('WEBVTT\n\n00:08.000 --> 00:10.000\nImaginary rotor assembly, fictional 17 mm.\n')
    for name,title,audio,subtitle in (
        ('english','Vidéo de test en anglais','eng','en-GB'),
        ('french','Vidéo de test en français','fr-FR','fr'),
    ):
        shutil.copyfile(BASE/'tests/fixtures/video/solid-green.webm',videos.ROOT/(name+'.webm'))
        (videos.ROOT/(name+'.info.json')).write_text(json.dumps({'title':title,'language':audio,'duration':12}))
        (videos.ROOT/(name+'.'+subtitle+'.vtt')).write_text('WEBVTT\n\n00:01.000 --> 00:02.000\nFixture.\n')
    if extra_track:
        (videos.ROOT/'cours.de.vtt').write_text('WEBVTT\n\n00:01.000 --> 00:02.000\nTest.\n')
    return {'ready':True}

caption_gate=None
@gateway.app.post('/fixture/captions')
async def fixture_captions(enabled:bool=True,hold:bool=True):
    global caption_gate
    await captions.stop_all()
    if not enabled:
        for path in videos.ROOT.glob('caption-preparation.*'):path.unlink()
        videos.STOP.clear();await asyncio.to_thread(videos.scan);return {'ready':False}
    videos.ROOT.mkdir(exist_ok=True)
    shutil.copyfile(BASE/'tests/fixtures/video/solid-green.webm',videos.ROOT/'caption-preparation.webm')
    (videos.ROOT/'caption-preparation.info.json').write_text(json.dumps({'title':'Préparation française fictive','language':'en','duration':12}))
    (videos.ROOT/'caption-preparation.en.srt').write_text('\n\n'.join(str(i+1)+'\n'+captions.stamp(i*200).replace('.',',')+' --> '+captions.stamp(i*200+150).replace('.',',')+'\n'+f'Fictional bearing {17+i} mm.' for i in range(40))+'\n')
    caption_gate=asyncio.Event() if hold else None
    videos.STOP.clear();await asyncio.to_thread(videos.scan)
    import hashlib
    return {'ready':True,'video':'video:'+hashlib.sha256(b'caption-preparation.webm').hexdigest()}

@gateway.app.post('/fixture/captions-release')
async def fixture_captions_release():
    global caption_gate
    if caption_gate:caption_gate.set()
    caption_gate=None;return {'released':True}

async def caption_translation(parts,mode):
    if caption_gate is not None and parts[0]['position']>=16:await caption_gate.wait()
    await asyncio.sleep(.2)
    return [{'id':row['position'],'text':'Roulement fictif de '+re.search(r'(\d+) mm',row['source_text'])[1]+' mm.'} for row in parts],'fixture-caption-model',{'context':16384}
captions.translate_batch=caption_translation
audio_gate=None
audio_enabled=False
transcriptions.UNIT_MS=2000
transcriptions.model_config=lambda:({'available':True,'model_path':'/fixture/not-a-model','model':{'repository':'fixture','revision':'fixture'},
    'runtime':{},'device':'cpu','compute_type':'int8','threads':1} if audio_enabled else {'available':False,'message':'Reconnaissance simulée non activée.'})
class AudioWorker:
    async def call(self,command):
        if command['action']=='probe':return {'audio_present':True,'duration_ms':4000}
        start=command['start_ms']
        if audio_gate is not None and start>=2000:await audio_gate.wait()
        await asyncio.sleep(.2)
        return {'cues':[{'start_ms':start+100,'end_ms':start+800,'text':f'Fictional bearing {17+start//2000} mm.'}],
            'language':'en','language_probability':.99,'eof':start>=2000,'last_decoded_ms':4000,'warnings':[],'raw_segments':[],
            'media_io':{'source':'kiwix_byte_ranges','media_bytes':1135,'http_requests':2} if 'archive' in command else {'source':'local_file','read_bytes_measured':False}}
    async def close(self):pass
transcriptions.Worker=AudioWorker

@gateway.app.post('/fixture/transcriptions')
async def fixture_transcriptions(hold:bool=True,enabled:bool=True):
    global audio_gate,audio_enabled
    await transcriptions.stop_all();audio_enabled=enabled;audio_gate=asyncio.Event() if hold else None
    if enabled:
        videos.ROOT.mkdir(exist_ok=True)
        shutil.copyfile(BASE/'tests/fixtures/video/solid-green.webm',videos.ROOT/'audio-preparation.webm')
        (videos.ROOT/'audio-preparation.info.json').write_text(json.dumps({'title':'Paroles fictives sans piste','language':'en','duration':12}))
    else:
        for path in videos.ROOT.glob('audio-preparation.*'):path.unlink()
    videos.STOP.clear();await asyncio.to_thread(videos.scan)
    return {'enabled':enabled,'real_recognition':False}

@gateway.app.post('/fixture/transcriptions-release')
async def fixture_transcriptions_release():
    global audio_gate
    if audio_gate:audio_gate.set()
    audio_gate=None;return {'released':True}
os.environ['ZIM_DIR']=str(inventory.ZIMS)
(inventory.ZIMS/'figure-fixture.zim').write_bytes(b'Fictional media identity, not a real archive.')
for topic in ('energy','food'):(inventory.ZIMS/('fixture-channel_en_'+topic+'_2026-01.zim')).write_bytes(b'Fictional archive metadata fixture, not a real ZIM.')
accounts.DB_PATH=str(root/'webui-fixture.db')
with closing(sqlite3.connect(accounts.DB_PATH)) as db:
    db.execute('CREATE TABLE user(id TEXT,name TEXT,email TEXT,role TEXT,created_at INTEGER)')
    db.execute('INSERT INTO user VALUES(?,?,?,?,?)',('browser','Test','browser@test.invalid','admin',0))
    db.commit()
(library.GUIDES/'shelter.en.txt').write_text('Shelter construction. Preserve dimensions and warnings.\n'*1800)
(library.GUIDES/'craft.en.txt').write_text('Sewing and mending clothes. Rope making and tool sharpening. Tiny fictional fixture, not a practical manual.',encoding='utf-8')
(library.GUIDES/'quality-bad.en.txt').write_text('Use 10 mg. Do not exceed the limit.',encoding='utf-8')
(library.GUIDES/'quality-short.en.txt').write_text('Quality short fixture. '+'Disconnect the power and inspect the wiring. '*12,encoding='utf-8')
(library.GUIDES/'quality-gaps.en.txt').write_text('Press the         key to enter the menu.',encoding='utf-8')
from pypdf import PdfReader,PdfWriter
from pypdf.generic import DecodedStreamObject,DictionaryObject,EncodedStreamObject,NameObject,NumberObject
writer=PdfWriter()
for number in range(1,7):
    page=writer.add_blank_page(width=300,height=400)
    page[NameObject('/Resources')]=DictionaryObject({NameObject('/Font'):DictionaryObject({NameObject('/F1'):DictionaryObject({NameObject('/Type'):NameObject('/Font'),NameObject('/Subtype'):NameObject('/Type1'),NameObject('/BaseFont'):NameObject('/Helvetica')})})})
    text=('Page '+str(number)+'. Shelter dimensions and construction warnings. ')*100
    if number==6:text+=' Appendix rotor calibration.'
    stream=DecodedStreamObject();stream.set_data(('BT /F1 12 Tf 20 100 Td ('+text+') Tj ET'+(' 20 40 80 30 re S 160 40 80 30 re S 100 55 m 160 55 l S' if number==6 else '')).encode());page[NameObject('/Contents')]=stream
writer.write(library.GUIDES/'shelter.en.pdf')
# A small file with a genuinely large image, compressed without allocating its
# complete RGB bitmap in the fixture server.
writer=PdfWriter();page=writer.add_blank_page(width=500,height=720)
compressor=zlib.compressobj();chunks=[];remaining=5000*7200
while remaining:
    pixels=min(remaining,300000)
    chunks.append(compressor.compress(b'\x00\x00\xff'*pixels));remaining-=pixels
chunks.append(compressor.flush())
image=EncodedStreamObject();image._data=b''.join(chunks)
image.update({NameObject('/Type'):NameObject('/XObject'),NameObject('/Subtype'):NameObject('/Image'),
              NameObject('/Width'):NumberObject(5000),NameObject('/Height'):NumberObject(7200),
              NameObject('/ColorSpace'):NameObject('/DeviceRGB'),NameObject('/BitsPerComponent'):NumberObject(8),
              NameObject('/Filter'):NameObject('/FlateDecode')})
page[NameObject('/Resources')]=DictionaryObject({NameObject('/XObject'):DictionaryObject({NameObject('/Im0'):writer._add_object(image)})})
stream=DecodedStreamObject();stream.set_data(b'q 500 0 0 720 0 0 cm /Im0 Do Q');page[NameObject('/Contents')]=stream
for number in (2,3):
    page=writer.add_blank_page(width=500,height=720)
    page[NameObject('/Resources')]=DictionaryObject({NameObject('/Font'):DictionaryObject({NameObject('/F1'):DictionaryObject({NameObject('/Type'):NameObject('/Font'),NameObject('/Subtype'):NameObject('/Type1'),NameObject('/BaseFont'):NameObject('/Helvetica')})})})
    stream=DecodedStreamObject();stream.set_data(f'BT /F1 12 Tf 20 680 Td (High resolution fixture page {number}.) Tj ET'.encode());page[NameObject('/Contents')]=stream
high_resolution=library.GUIDES/'high-resolution.en.pdf';writer.write(high_resolution)
assert high_resolution.stat().st_size<200000
source_image=PdfReader(high_resolution).pages[0]['/Resources']['/XObject']['/Im0']
assert (source_image['/Width'],source_image['/Height'])==(5000,7200)
(library.GUIDES/'metadata.json').write_text(json.dumps([{'path':'shelter.en.txt','title':'Shelter fixture','language':'en',
    'document_date':'2010-05','edition':'Deuxième édition','collected_at':'2026-11-12','provenance':'Fixture synthétique'}]))

async def native(path,payload=None,token=None):
    if path=='/api/v1/auths/signin':return {'id':'browser','name':'Test','role':'admin','email':'browser@test.invalid','token':'fixture-only'}
    if path=='/api/v1/auths/':return {'id':'browser','name':'Test','role':'admin','email':'browser@test.invalid'}
    if path=='/api/v1/auths/signout':return {'ok':True}
    raise ValueError(path)
accounts.native=native
figures_enabled=False
reader_article_enabled=False
async def books(**kwargs):return ([{'book':'figure-fixture','title':'Collection fictive illustrée','language':'fr'}] if figures_enabled else [])+([{'book':'reader-fixture','title':'Collection fictive anglaise','language':'en'}] if reader_article_enabled else [])
@gateway.app.post('/fixture/reader-article')
async def reader_article(enabled:bool=False):
    global reader_article_enabled
    reader_article_enabled=enabled
    if enabled:(inventory.ZIMS/'reader-fixture.zim').write_bytes(b'Fictional article archive identity.')
    return {'enabled':enabled}
@gateway.app.post('/fixture/figures')
async def fixture_figures(enabled:bool=False):
    global figures_enabled
    figures_enabled=enabled;return {'enabled':enabled}
@gateway.app.post('/fixture/figures-change')
async def fixture_figures_change():
    path=library.GUIDES/'shelter.en.pdf';path.write_bytes(path.read_bytes()+b'\n');return {'changed':True}
async def fixture_get(path,**kwargs):
    if '/reader-fixture/' in path:return library.Fetched(b'<html lang="en"><title>English article fixture</title><article><h1>English article fixture</h1><p>The fictional rotor has 17 marks.</p></article></html>','text/html',path)
    if path.endswith('/schema.svg'):return library.Fetched(b'<svg xmlns="http://www.w3.org/2000/svg" width="300" height="180"><rect x="20" y="30" width="80" height="80" fill="green"/><path d="M100 70 L240 70" stroke="black"/><text x="20" y="150">17 mm - fixture only</text></svg>','image/svg+xml',path)
    if path.endswith('/logo.svg'):return library.Fetched(b'<svg xmlns="http://www.w3.org/2000/svg" width="100" height="100"><circle cx="50" cy="50" r="40" fill="blue"/></svg>','image/svg+xml',path)
    return library.Fetched(b'<html lang="fr"><title>Montage fictif</title><p>Montage fictif de rotor, valeur 17 mm.</p><figure><img src="../I/schema.svg" alt="Schema du rotor fictif"><figcaption>Schema original du montage : 17 mm, garder la protection.</figcaption></figure><figure><img src="../I/logo.svg" alt="Logo"><figcaption>Logo publicitaire.</figcaption></figure></html>','text/html',path)
library.get=fixture_get
library.books=books
original_search=library.search
@gateway.app.post('/fixture/documentary')
async def documentary_fixture(state:str='partial',read_source:bool=True,running:bool=False):
    if state not in ('partial','complete','unavailable','empty','legacy'):return {'error':'Unknown fixture'}
    conversation,job=store.new_id(),store.new_id();observed=documentary.Evidence();now=time.time()
    source=await library.source('guide:shelter.en.txt')
    if state!='legacy':
        observed.record('search_library',{}, {'results':[] if state in ('empty','unavailable') else [source], 'coverage':{'status':'complete' if state=='empty' else state}})
        if read_source and state not in ('empty','unavailable'):observed.record('read_source',{'id':source['id']},{**source,'text':source['text'][:200],'partial_read':True})
    text='Aucun document n’existe, affirmation fictive volontairement erronée du modèle.'
    with store.connect() as db:
        db.execute('INSERT INTO conversations VALUES(?,?,?,?)',(conversation,'browser','Suivi documentaire fictif',now))
        db.execute('INSERT INTO messages(conversation_id,role,content,created) VALUES(?,?,?,?)',(conversation,'user','Question documentaire fictive',now))
        db.execute('INSERT INTO jobs(id,user_id,conversation_id,mode,status,answer,created,updated) VALUES(?,?,?,?,?,?,?,?)',(job,'browser',conversation,'rapide','running' if running else 'done',text,now,now))
        message=None if running else db.execute('INSERT INTO messages(conversation_id,role,content,created) VALUES(?,?,?,?)',(conversation,'assistant',text,now)).lastrowid
        if state!='legacy':documentary.save(job,observed.summary(),sources=list(observed.consulted.values()),message_id=message,db=db)
    return {'conversation':conversation,'job':job}

@gateway.app.post('/fixture/documentary-finish')
async def documentary_finish(job:str):
    with store.connect() as db:
        row=db.execute('SELECT * FROM jobs WHERE id=?',(job,)).fetchone()
        if not row:return {'finished':False}
        stored=documentary.for_job(job)
        message=db.execute('INSERT INTO messages(conversation_id,role,content,created) VALUES(?,?,?,?)',(row['conversation_id'],'assistant',row['answer'],0)).lastrowid
        db.execute("UPDATE jobs SET status='done' WHERE id=?",(job,))
        if stored:documentary.save(job,stored,sources=stored.get('consulted_sources'),message_id=message,db=db)
    return {'finished':True}

progress_gates={}
@gateway.app.post('/fixture/search-gate')
async def search_gate(query:str,hold:bool=False):
    if not query.startswith('fixture-progress-'):return {'held':False}
    if hold:progress_gates[query]=asyncio.Event()
    else:
        event=progress_gates.pop(query,None)
        if event:event.set()
    return {'held':hold}

async def progressive_search(query,*args,on_update=None,**kwargs):
    if not query.startswith('fixture-progress'):return await original_search(query,*args,on_update=on_update,**kwargs)
    first={'id':'guide:shelter.en.txt','title':'Premier document fictif','kind':'guide','language':'en','excerpt':'First synthetic document.',
           'other_matches':[{'id':'guide:shelter.en.pdf#page=2','title':'Passage fictif'}]}
    final={'id':'guide:craft.en.txt','title':'Second document fictif','kind':'guide','language':'en','excerpt':'Second synthetic document.'}
    empty=query.startswith('fixture-progress-empty')
    if on_update:await on_update(library.SearchResults([] if empty else [first],{'status':'partial','running':True,'domain':'all','searched':1,'collections_selected':3}))
    gate=progress_gates.get(query)
    if gate:await gate.wait()
    else:await asyncio.sleep(.8)
    if query.endswith('error'):raise RuntimeError('PRIVATE FIXTURE FAILURE')
    return library.SearchResults([] if empty else [first,final],{'status':'partial' if query.endswith('partial') else 'complete','domain':'all','searched':3,'collections_selected':3})
library.search=progressive_search
async def status(fresh=False):return {'online':True,'paused':False,'message':'Simulation CPU','models':[],'gpus':[],'memory':{},'disk':{},'jobs':{},'control_available':False}
operations.status=status
async def library_command(action=None,payload=None):
    from fastapi import HTTPException
    if action not in (None,'status'):raise HTTPException(409,'Cette fixture ne télécharge aucun contenu.')
    rules=json.loads(learning.RULES.read_text(encoding='utf-8'))['themes']
    return {'available':True,'phase':'planned','id':'a'*32,'themes':[{'id':k,'label':v['label']} for k,v in rules.items()],
            'plan':{'count':0,'remaining_download_bytes':0,'library_bytes':0,'missing_themes':[],'candidates':[],
                    'learning_coverage':[{'id':'sciences','label':rules['sciences']['label'],'references':1,'local_references':0,'skills_to_review':['Algèbre'],'status':'references_to_review'}]}}
operations.library_command=library_command
async def translate(text,mode,*,on_metrics=None,guidance=None,correction=None,spell_ordinals=False):
    await asyncio.sleep(.5)
    if on_metrics:on_metrics({'context':16384,'requested_context':16384,'runtime_after':{'running':{'context_length':16384}},
        'model_calls':[{'prompt_eval_count':300,'eval_count':400,'load_ms':2,'eval_ms':450}]})
    if text.startswith('Use 10 mg.'):return 'Utilisez 100 mg. Ne dépassez pas la limite.',engine.MODES[mode]['model']
    if text.startswith('Quality short fixture.'):return 'Débranchez le courant.',engine.MODES[mode]['model']
    if text.startswith('Press the         key'):return 'Appuyez sur la touche         pour accéder au menu.',engine.MODES[mode]['model']
    if text.startswith('English article fixture'):return 'Article fictif : le rotor comporte 17 repères. <img src=x onerror=fixture()>',engine.MODES[mode]['model']
    return 'Construction d’un abri. Conservez les dimensions et les avertissements.\n'+text.replace('Page','Section').replace('Shelter','Abri').replace('construction warnings','avertissements de construction'),engine.MODES[mode]['model']
translations.translate=translate
# Chat is simulated separately; it never contacts a real model.
def launch(identifier,*args,domain='all',source_ids=None):
    engine.PENDING.pop(identifier,None)
    if store.messages(args[1])[-1]['content'].startswith('Montre les schémas fixture'):
        asyncio.create_task(figure_answer(identifier,args[1],args[2]));return
    refs=[];answer='Réponse simulée, aucun modèle lancé.'
    if args[-1]:
        with store.connect() as db:
            row=db.execute('SELECT title FROM documents WHERE id=?',(args[-1],)).fetchone()
            if row:refs=[{'id':args[-1],'title':row['title'],'number':1,**library.guide_metadata(db,args[-1])}]
        if refs:answer+=' Le document indique des conditions de construction [1].'
    with store.connect() as db:
        db.execute('INSERT INTO messages(conversation_id,role,content,sources,created) VALUES(?,?,?,?,?)',(args[1],'assistant',answer,json.dumps(refs),0))
    engine.update(identifier,status='done',answer=answer,sources=refs)
    measured=assistant_metrics.Measurement(identifier,engine.MODES['rapide']['model'],'rapide',16384).finish('done')
    measured.update(simulated=True,total_ms=6500,first_text_ms=4400,phases_ms={'queue':100,'search':120,'reading':80,'model_preparation':4100,'writing':2100})
    durable.write_bytes(assistant_metrics.path(identifier),json.dumps(measured).encode(),private=True)
engine.launch=launch
async def summary_infer(item,messages,*,schema=None,output=2048):
    await asyncio.sleep(1.5)
    data=json.loads(messages[-1]['content'])
    if 'units' in data:return {'notes':[{'unit':unit['position'],'quote':unit['text'].strip()[:100],'text':'Note fictive : '+unit['text'].strip()[:100]} for unit in data['units']]},'fixture-model'
    if 'sources' in data:return 'Synthèse fictive des documents examinés [1].','fixture-model'
    return {'notes':[{'text':'Regroupement fictif.','supports':[child['id'] for child in data['notes']][:8]}]},'fixture-model'
summaries.infer=summary_infer
async def figure_answer(identifier,conversation,mode):
    refs={}
    for identifier_source in ('guide:shelter.en.pdf#page=6','zim:figure-fixture/A/article'):
        source=await library.source(identifier_source);engine.reference(refs,source,True,visual=True)
    picked=[item for item in illustrations.collect(refs) if item['kind']=='pdf_page' or item['id'].endswith('/schema.svg')]
    illustrations.attach(refs,picked,'selected');sources=engine.read_references(refs)
    answer='Montage fictif du rotor [1, p. 6] ; illustration et légende [2].'
    with store.connect() as db:db.execute('INSERT INTO messages(conversation_id,role,content,sources,created,model,mode) VALUES(?,?,?,?,?,?,?)',(conversation,'assistant',answer,json.dumps(sources),time.time(),'fixture-model',mode))
    engine.update(identifier,status='done',answer=answer,sources=sources)
base=BASE
@gateway.app.get('/fixture/procedure-review')
def procedure_review_fixture():
    from pilot import procedure_review
    parts=[{'id':'condition-0','source_number':1,'text':'Avant : <img src=x> [1] ![x](https://external.invalid/)'}]
    text,_=procedure_review.apply('Choisir le canal fictif avec `MENU → 27` [1].',{'missing_conditions':['condition-0']},parts)
    return {'answer':text,'sources':[{'id':'guide:shelter.en.pdf#page=6','title':'Fixture source','number':1,'pages':[6]}]}
from archive_video_browser_fixture import install as install_archive_video_fixture
install_archive_video_fixture(gateway.app,root,BASE)
gateway.app.mount('/guides',StaticFiles(directory=str(library.GUIDES)),name='fixture-guides')
gateway.app.mount('/',StaticFiles(directory=str(base/'portal'),html=True),name='fixture-portal')
import uvicorn
try:uvicorn.run(gateway.app,host='0.0.0.0',port=8769,log_level='warning')
finally:temporary.cleanup()
