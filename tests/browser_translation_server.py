"""Browser fixture server only: tiny documents, fake identity and inference, no real accounts/model.
Run in an isolated test environment: python tests/browser_translation_server.py
"""
import asyncio
from contextlib import closing
import json
import sqlite3
from pathlib import Path
import sys
import tempfile
import time
BASE=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(BASE))
from fastapi.staticfiles import StaticFiles
from pilot import accounts,app as gateway,engine,library,operations,store,translations,learning,inventory,assistant_metrics,durable,documentary,summaries
engine.POLICY=BASE/'deploy/assistant-system.fr.txt'
temporary=tempfile.TemporaryDirectory(prefix='translation-browser-');root=Path(temporary.name)
store.ROOT=root/'state';library.GUIDES=root/'guides';library.GUIDES.mkdir()
inventory.ZIMS=root/'zim';inventory.ZIMS.mkdir()
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
from pypdf import PdfWriter
from pypdf.generic import DecodedStreamObject,DictionaryObject,NameObject
writer=PdfWriter()
for number in range(1,7):
    page=writer.add_blank_page(width=300,height=400)
    page[NameObject('/Resources')]=DictionaryObject({NameObject('/Font'):DictionaryObject({NameObject('/F1'):DictionaryObject({NameObject('/Type'):NameObject('/Font'),NameObject('/Subtype'):NameObject('/Type1'),NameObject('/BaseFont'):NameObject('/Helvetica')})})})
    text=('Page '+str(number)+'. Shelter dimensions and construction warnings. ')*100
    if number==6:text+=' Appendix rotor calibration.'
    stream=DecodedStreamObject();stream.set_data(('BT /F1 12 Tf 20 100 Td ('+text+') Tj ET').encode());page[NameObject('/Contents')]=stream
writer.write(library.GUIDES/'shelter.en.pdf')
(library.GUIDES/'metadata.json').write_text(json.dumps([{'path':'shelter.en.txt','title':'Shelter fixture','language':'en',
    'document_date':'2010-05','edition':'Deuxième édition','collected_at':'2026-11-12','provenance':'Fixture synthétique'}]))

async def native(path,payload=None,token=None):
    if path=='/api/v1/auths/signin':return {'id':'browser','name':'Test','role':'admin','email':'browser@test.invalid','token':'fixture-only'}
    if path=='/api/v1/auths/':return {'id':'browser','name':'Test','role':'admin','email':'browser@test.invalid'}
    if path=='/api/v1/auths/signout':return {'ok':True}
    raise ValueError(path)
accounts.native=native
async def books(**kwargs):return []
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
    if on_update:await on_update(library.SearchResults([first],{'status':'partial','running':True,'domain':'all','searched':1,'collections_selected':3}))
    gate=progress_gates.get(query)
    if gate:await gate.wait()
    else:await asyncio.sleep(.8)
    if query.endswith('error'):raise RuntimeError('PRIVATE FIXTURE FAILURE')
    return library.SearchResults([first,final],{'status':'complete','domain':'all','searched':3,'collections_selected':3})
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
async def translate(text,mode):
    await asyncio.sleep(.5)
    if text.startswith('Use 10 mg.'):return 'Utilisez 100 mg. Ne dépassez pas la limite.',engine.MODES[mode]['model']
    if text.startswith('Quality short fixture.'):return 'Débranchez le courant.',engine.MODES[mode]['model']
    return 'Construction d’un abri. Conservez les dimensions et les avertissements.\n'+text.replace('Page','Section').replace('Shelter','Abri').replace('construction warnings','avertissements de construction'),engine.MODES[mode]['model']
translations.translate=translate
# Chat is simulated separately; it never contacts a real model.
def launch(identifier,*args,domain='all',source_ids=None):
    engine.PENDING.pop(identifier,None)
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
base=BASE
gateway.app.mount('/guides',StaticFiles(directory=str(library.GUIDES)),name='fixture-guides')
gateway.app.mount('/',StaticFiles(directory=str(base/'portal'),html=True),name='fixture-portal')
import uvicorn
try:uvicorn.run(gateway.app,host='0.0.0.0',port=8769,log_level='warning')
finally:temporary.cleanup()
