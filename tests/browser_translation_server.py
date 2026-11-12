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
BASE=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(BASE))
from fastapi.staticfiles import StaticFiles
from pilot import accounts,app as gateway,engine,library,operations,store,translations
engine.POLICY=BASE/'deploy/assistant-system.fr.txt'
temporary=tempfile.TemporaryDirectory(prefix='translation-browser-');root=Path(temporary.name)
store.ROOT=root/'state';library.GUIDES=root/'guides';library.GUIDES.mkdir()
accounts.DB_PATH=str(root/'webui-fixture.db')
with closing(sqlite3.connect(accounts.DB_PATH)) as db:
    db.execute('CREATE TABLE user(id TEXT,name TEXT,email TEXT,role TEXT,created_at INTEGER)')
    db.execute('INSERT INTO user VALUES(?,?,?,?,?)',('browser','Test','browser@test.invalid','admin',0))
    db.commit()
(library.GUIDES/'shelter.en.txt').write_text('Shelter construction. Preserve dimensions and warnings.\n'*1800)
from pypdf import PdfWriter
from pypdf.generic import DecodedStreamObject,DictionaryObject,NameObject
writer=PdfWriter()
for number in range(1,7):
    page=writer.add_blank_page(width=300,height=400)
    page[NameObject('/Resources')]=DictionaryObject({NameObject('/Font'):DictionaryObject({NameObject('/F1'):DictionaryObject({NameObject('/Type'):NameObject('/Font'),NameObject('/Subtype'):NameObject('/Type1'),NameObject('/BaseFont'):NameObject('/Helvetica')})})})
    text=('Page '+str(number)+'. Shelter dimensions and construction warnings. ')*100
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
async def books():return []
library.books=books
async def status(fresh=False):return {'online':True,'paused':False,'message':'Simulation CPU','models':[],'gpus':[],'memory':{},'disk':{},'jobs':{},'control_available':False}
operations.status=status
async def translate(text,mode):
    await asyncio.sleep(.5)
    return 'Construction d’un abri. Conservez les dimensions et les avertissements.\n'+text[:25],engine.MODES[mode]['model']
translations.translate=translate
# Chat is simulated separately; it never contacts a real model.
def launch(identifier,*args):
    refs=[];answer='Réponse simulée, aucun modèle lancé.'
    if args[-1]:
        with store.connect() as db:
            row=db.execute('SELECT title FROM documents WHERE id=?',(args[-1],)).fetchone()
            if row:refs=[{'id':args[-1],'title':row['title'],'number':1,**library.guide_metadata(db,args[-1])}]
        if refs:answer+=' Le document indique des conditions de construction [1].'
    with store.connect() as db:
        db.execute('INSERT INTO messages(conversation_id,role,content,sources,created) VALUES(?,?,?,?,?)',(args[1],'assistant',answer,json.dumps(refs),0))
    engine.update(identifier,status='done',answer=answer,sources=refs)
engine.launch=launch
base=BASE
gateway.app.mount('/guides',StaticFiles(directory=str(library.GUIDES)),name='fixture-guides')
gateway.app.mount('/',StaticFiles(directory=str(base/'portal'),html=True),name='fixture-portal')
import uvicorn
try:uvicorn.run(gateway.app,host='0.0.0.0',port=8769,log_level='warning')
finally:temporary.cleanup()
