"""Read-only local knowledge tools and a rebuildable guide index."""
import ast
from fractions import Fraction
from html.parser import HTMLParser
import math
import json
import hashlib
import unicodedata
import os
from pathlib import Path
import re
import zipfile
from urllib.parse import quote, unquote, urljoin, urlparse
import xml.etree.ElementTree as ET

import httpx
from fastapi import HTTPException

from . import store

GUIDES=Path(os.environ.get('GUIDES_DIR','/guides'))
KIWIX=os.environ.get('KIWIX_URL','http://kiwix:8080').rstrip('/')


class Text(HTMLParser):
    def __init__(self):super().__init__();self.parts=[];self.skip=0;self.math=0;self.images=[];self.title=[];self.in_title=False
    def handle_starttag(self,tag,attrs):
        attrs=dict(attrs)
        if tag in ('script','style','nav'):self.skip+=1
        if tag=='title':self.in_title=True
        if tag=='math':
            self.math+=1
            if self.math==1:self.parts.append(' '+attrs.get('alttext','')+' ')
        if tag in ('p','br','h1','h2','h3','li','tr'):self.parts.append('\n')
        if tag=='img' and attrs.get('src'):self.images.append({'src':attrs['src'],'alt':attrs.get('alt','')})
    def handle_endtag(self,tag):
        if tag in ('script','style','nav'):self.skip=max(0,self.skip-1)
        if tag=='math':self.math=max(0,self.math-1)
        if tag=='title':self.in_title=False
        if tag in ('p','h1','h2','h3','li','tr'):self.parts.append('\n')
    def handle_data(self,text):
        if self.in_title:self.title.append(text)
        if not self.skip and not self.math:self.parts.append(text)
    def text(self):return '\n'.join(x.strip() for x in ''.join(self.parts).splitlines() if x.strip())


async def get(path, maximum=2_000_000):
    async with httpx.AsyncClient(trust_env=False,timeout=25,follow_redirects=False) as client:
        async with client.stream('GET',KIWIX+path) as response:
            if response.status_code!=200:raise HTTPException(404,'Document indisponible.')
            body=bytearray()
            async for chunk in response.aiter_bytes():
                body.extend(chunk)
                if len(body)>maximum:raise HTTPException(413,'Ce document est trop volumineux pour cet aperçu.')
            return bytes(body),response.headers.get('content-type','application/octet-stream')


async def books():
    try:
        raw,_=await get('/catalog/v2/entries?count=-1')
        root=ET.fromstring(raw);ns={'a':'http://www.w3.org/2005/Atom'}
        result=[]
        for e in root.findall('a:entry',ns):
            link=next((l.get('href','') for l in e.findall('a:link',ns) if l.get('type')=='text/html'),'')
            result.append({'title':e.findtext('a:title',namespaces=ns),'language':e.findtext('a:language',namespaces=ns),'book':link.removeprefix('/content/')})
        return result
    except (httpx.HTTPError,ET.ParseError,HTTPException):return []


def index_guides():
    documents=[];passages=[];report=[]
    if GUIDES.exists():
        seed=GUIDES/'metadata.json'
        if seed.is_file() and not seed.is_symlink() and seed.stat().st_size<1_000_000:
            try:
                entries=json.loads(seed.read_text())
                with store.connect() as db:
                    for item in entries:
                        if not isinstance(item,dict) or not isinstance(item.get('path'),str):continue
                        db.execute('INSERT INTO guide_meta VALUES(?,?,?,?,?) ON CONFLICT(path) DO UPDATE SET title=excluded.title,language=excluded.language,provenance=excluded.provenance,licence=excluded.licence',tuple(str(item.get(key,''))[:2000] for key in ('path','title','language','provenance','licence')))
            except (ValueError,TypeError):pass
        with store.connect() as db:metadata={r['path']:dict(r) for r in db.execute('SELECT * FROM guide_meta')}
        for path in sorted(GUIDES.rglob('*')):
            if not path.is_file() or path.is_symlink() or not path.resolve().is_relative_to(GUIDES.resolve()):continue
            relative=path.relative_to(GUIDES).as_posix();suffix=path.suffix.lower()
            if suffix not in ('.txt','.md','.html','.pdf','.epub') or relative.startswith(('box.','boite.')):continue
            record={'path':relative,'bytes':path.stat().st_size,'status':'pending'}
            report.append(record)
            if record['bytes']>300_000_000:
                record['status']='too_large';continue
            page_texts=[]
            try:
                if suffix in ('.txt','.md'):text=path.read_text(errors='replace')
                elif suffix=='.html':p=Text();p.feed(path.read_text(errors='replace'));text=p.text()
                elif suffix=='.pdf':
                    from pypdf import PdfReader
                    cache=store.ROOT/'index-cache';cache.mkdir(exist_ok=True)
                    stat=path.stat();key=hashlib.sha256(('pdf-v1:'+relative+':'+str(stat.st_mtime_ns)+':'+str(stat.st_size)).encode()).hexdigest()
                    cached=cache/(key+'.json')
                    if cached.is_file():page_texts=json.loads(cached.read_text())
                    else:
                        reader=PdfReader(path)
                        if len(reader.pages)>1200:
                            record['status']='page_limit';continue
                        page_texts=[(page.extract_text() or '')[:24000] for page in reader.pages]
                        temporary=cached.with_suffix('.tmp');temporary.write_text(json.dumps(page_texts,ensure_ascii=False));temporary.replace(cached)
                    text='\n'.join(page_texts[:4])
                elif suffix=='.epub':
                    with zipfile.ZipFile(path) as z:
                        entries=[e for e in z.infolist() if e.filename.endswith(('.html','.xhtml')) and e.file_size<2_000_000]
                        if sum(e.file_size for e in entries)>20_000_000:
                            record['status']='too_large';continue
                        p=Text()
                        for e in entries:p.feed(z.read(e).decode(errors='replace'))
                        text=p.text()
                else:continue
            except Exception as exc:
                record['status']='extraction_failed';record['error']=type(exc).__name__;continue
            characters=sum(len(p.strip()) for p in page_texts) if suffix=='.pdf' else len(text.strip())
            record.update(status='indexed' if characters else 'needs_ocr' if suffix=='.pdf' else 'no_text',
                          characters=characters,pages=len(page_texts),searchable_pages=sum(bool(p.strip()) for p in page_texts),
                          truncated_pages=sum(len(p)>=24000 for p in page_texts))
            meta=metadata.get(relative,{})
            heading=''.join(p.title) if suffix=='.html' else text.split('\n',1)[0][2:].strip() if suffix=='.md' and text.startswith('# ') else ''
            title=meta.get('title') or heading[:200] or path.stem.replace('.fr','').replace('.en','').replace('_',' ')
            if relative.startswith(('box.','boite.')):title='La boîte ALPHA — démonstration'
            if relative.startswith(('box.','boite.')):continue
            language=meta.get('language') or ('fr' if '.fr.' in path.name else 'en' if '.en.' in path.name else '')
            documents.append(('guide:'+relative,title,'/guides/'+quote(relative),language,text[:500000]))
            for number,page_text in enumerate(page_texts,1):
                if page_text.strip():passages.append(('guide:'+relative+'#page='+str(number),title+' — page '+str(number),'/guides/'+quote(relative)+'#page='+str(number),language,page_text))
    with store.connect() as db:
        db.execute('DELETE FROM documents');db.executemany('INSERT INTO documents VALUES(?,?,?,?,?)',documents)
        db.execute('DELETE FROM passages');db.executemany('INSERT INTO passages VALUES(?,?,?,?,?)',passages)
    store.ROOT.mkdir(parents=True,exist_ok=True)
    temporary=store.ROOT/'index-report.tmp'
    temporary.write_text(json.dumps({'documents':report,'indexed':sum(r['status']=='indexed' for r in report)},ensure_ascii=False))
    temporary.replace(store.ROOT/'index-report.json')
    return len(documents)


STOPWORDS=set('a au aux avec ce ces cette dans de des du elle en est et eux faire fais fait for from how il ils je la le les leur lui ma mais me mes moi mon nous of on or ou par pas pour qu que quel quelle qui sa se ses si sois sort sortir sous sur ta te tes the this to toi ton un une vos votre vous what quel quels quelles comment document documents guide guides efficacement peux peut voudrais veux donne donnez montre'.split())
SYNONYMS={'toit':['toit','toiture','roof','roofing'],'toiture':['toiture','toit','roof'],'abri':['abri','abris','shelter'],'bache':['bache','tarpaulin','sheeting'],'eau':['eau','water'],'potable':['potable','drinking'],'apprendre':['apprendre','learning'],'enfant':['enfant','enfants','children'],'maths':['maths','mathematiques','mathematics']}
STOPWORDS.update('comment pourquoi trouver rechercher recherche cherche expliquer explique informations information sujet concernant utiliser utilise voudrais besoin besoin les leurs pouvez pourrait pouvez avoir quand contient contient moi documenter faire preparer correctement sujet bon bonne'.split())
SYNONYMS.update({
    'semences':['semences','graines','seeds'],'graines':['graines','semences','seeds'],
    'stocker':['stocker','stockage','storage','storing'],'conservation':['conservation','preservation','storage'],
    'jardin':['jardin','jardins','garden','gardening'],'potager':['potager','vegetable','garden'],
    'irrigation':['irrigation','arrosage','watering'],'sol':['sol','soil'],'compost':['compost','composting'],
    'greffe':['greffe','grafting'],'abeilles':['abeilles','bees'],'poules':['poules','poultry','chickens'],
    'dents':['dents','tooth','teeth'],'dentaire':['dentaire','dental'],'douleur':['douleur','pain'],
    'psychologique':['psychologique','psychological'],'stress':['stress'],'enfants':['enfants','children'],
    'plantes':['plantes','plants'],'champignons':['champignons','mushrooms'],'toxiques':['toxiques','toxic','poisonous'],
    'radio':['radio','radiotelephonie'],'antenne':['antenne','antennes','antenna'],
    'batterie':['batterie','batteries','battery'],'pompe':['pompe','pompes','pump'],
    'menuiserie':['menuiserie','woodworking','carpentry'],'couture':['couture','sewing'],
    'soudage':['soudage','soudure','welding'],'plomberie':['plomberie','plumbing'],
    'velo':['velo','bicycle','bike'],'reparation':['reparation','repair'],'electricite':['electricite','electrical'],
    'lecture':['lecture','reading'],'ecriture':['ecriture','writing'],'calcul':['calcul','arithmetic'],
    'carte':['carte','cartes','map'],'incendie':['incendie','incendies','fire'],
    'inondation':['inondation','inondations','flood'],'sollies':['sollies'],'ville':['ville'],
    'puits':['puits','well','wells'],'desinfection':['desinfection','disinfection','disinfecting'],
    'risques':['risques','risque','risks','risk'],'fractions':['fractions','fraction']
})
SYNONYMS.update({'examiner':['examiner','examine','examining','examination'],
                 'malade':['malade','malades','sick','patient'],
                 'personne':['personne','person','people']})
TERM_ALIASES={'stocker':'stocker','stockage':'stocker','conserver':'conservation','graine':'graines',
              'plante':'plantes','dent':'dents','radios':'radio','batteries':'batterie',
              'pompes':'pompe','velos':'velo','cartes':'carte','soudure':'soudage'}


def index_report():
    path=store.ROOT/'index-report.json'
    if not path.is_file() or path.stat().st_size>2_000_000:
        return {'documents':[],'indexed':0,'status':'not_available'}
    try:return {**json.loads(path.read_text()),'status':'ready'}
    except (OSError,ValueError):return {'documents':[],'indexed':0,'status':'not_available'}


def search_terms(query):
    words=[unicodedata.normalize('NFKD',w).encode('ascii','ignore').decode().lower() for w in re.findall(r'\w+',query,flags=re.UNICODE)]
    return list(dict.fromkeys(TERM_ALIASES.get(w,w) for w in words if w and w not in STOPWORDS and len(w)>1))[:10]


async def search(query,language='',limit=8):
    words=search_terms(query)
    results=[]
    if words:
        groups=['('+' OR '.join('"'+s+'"' for s in SYNONYMS.get(w,[w]))+')' for w in words]
        expression=' AND '.join(groups)
        with store.connect() as db:
            for table in ('documents','passages'):
                rows=db.execute(f"SELECT id,title,url,language,snippet({table},4,'','', '…',30) AS excerpt FROM {table} WHERE {table} MATCH ? AND (?='' OR language=?) AND lower(id) NOT LIKE '%.pdf' ORDER BY bm25({table}) LIMIT ?",(expression,language,language,limit)).fetchall()
                results.extend([{**dict(r),'kind':'guide'} for r in rows])
    available=await books()
    langs=sorted({x['language'] for x in available if x['language'] and (not language or x['language']=={'fr':'fra','en':'eng'}.get(language,language))})
    for lang in langs:
        try:
            from urllib.parse import urlencode
            english={'toit':'roof','toiture':'roof','abri':'shelter','bache':'tarpaulin','eau':'water','potable':'drinking',
                     'apprendre':'learning','enfant':'children','enfants':'children','maths':'mathematics',
                     'semences':'seeds','graines':'seeds','stocker':'storage','conservation':'preservation','jardin':'garden',
                     'potager':'vegetable garden','sol':'soil','greffe':'grafting','abeilles':'bees','poules':'chickens',
                     'dents':'teeth','dentaire':'dental','douleur':'pain','psychologique':'psychological','plantes':'plants',
                     'champignons':'mushrooms','toxiques':'poisonous','antenne':'antenna','batterie':'battery','pompe':'pump',
                     'menuiserie':'carpentry','couture':'sewing','soudage':'welding','plomberie':'plumbing',
                     'velo':'bicycle','reparation':'repair','electricite':'electrical','lecture':'reading','ecriture':'writing',
                     'calcul':'arithmetic','carte':'map','incendie':'fire','inondation':'flood',
                     'puits':'wells','desinfection':'disinfecting','risques':'risks'}
            english.update({'examiner':'examine','malade':'sick','personne':'person'})
            translated=[english.get(w,w) if lang=='eng' else w for w in words]
            pattern=' '.join(translated) if translated else query
            raw,_=await get('/search?'+urlencode({'books.filter.lang':lang,'pattern':pattern,'format':'xml','pageLength':limit}))
            for item in ET.fromstring(raw).findall('./channel/item'):
                link=item.findtext('link','')
                if not link.startswith('/content/'):continue
                p=Text();p.feed(item.findtext('description',''))
                results.append({'id':'zim:'+link.removeprefix('/content/'),'title':item.findtext('title',''),
                    'excerpt':p.text()[:600],'kind':item.findtext('book/title','Encyclopédie'),'language':lang,'url':link})
        except (httpx.HTTPError,ET.ParseError,HTTPException):continue
    norm=lambda s:unquote(s).casefold().replace('é','e').replace('è','e')
    results.sort(key=lambda r:norm(r['title'])!=norm(query))
    return results[:limit*2]


def safe_zim_path(identifier):
    path=identifier.removeprefix('zim:')
    for _ in range(3):path=unquote(path)
    if not identifier.startswith('zim:') or '\\' in path or re.search(r'%[0-9a-fA-F]{2}',path) or any(part in ('.','..') for part in path.split('/')) or '\x00' in path:raise HTTPException(400,'Référence de document non valide.')
    return path


async def source(identifier):
    if identifier.startswith('guide:'):
        with store.connect() as db:
            table='passages' if '#page=' in identifier else 'documents'
            row=db.execute('SELECT * FROM '+table+' WHERE id=?',(identifier,)).fetchone()
            meta=db.execute('SELECT provenance,licence FROM guide_meta WHERE path=?',(identifier.removeprefix('guide:').split('#page=')[0],)).fetchone()
        if not row:raise HTTPException(404,'Guide introuvable.')
        return {**dict(row),**(dict(meta) if meta else {}),'kind':'guide','images':[],
                'preview':identifier.lower().split('#page=')[0].endswith('.pdf')}
    path=safe_zim_path(identifier)
    if path.split('/')[0] not in {b['book'] for b in await books()}:raise HTTPException(404,'Collection introuvable.')
    raw,_=await get('/content/'+quote(path,safe='/'))
    p=Text();p.feed(raw.decode(errors='replace'))
    images=[]
    for image in p.images:
        target=urljoin('/content/'+quote(path,safe='/'),image['src'])
        if target.startswith('/content/'):
            images.append({'id':'zim:'+target.removeprefix('/content/'),'alt':image['alt']})
    return {'id':identifier,'title':''.join(p.title) or path.split('/')[-1].replace('_',' '),'text':p.text()[:100000],
            'url':'/content/'+quote(path,safe='/'),'kind':'article','images':images[:10]}


def calculate(expression):
    if not isinstance(expression,str) or len(expression)>160:raise ValueError('Expression trop longue.')
    tree=ast.parse(expression,mode='eval')
    if sum(1 for _ in ast.walk(tree))>45:raise ValueError('Expression trop complexe.')
    def visit(node):
        if isinstance(node,ast.Constant) and type(node.value) in (int,float):value=Fraction(str(node.value))
        elif isinstance(node,ast.UnaryOp) and isinstance(node.op,(ast.UAdd,ast.USub)):value=visit(node.operand)*(1 if isinstance(node.op,ast.UAdd) else -1)
        elif isinstance(node,ast.BinOp):
            a,b=visit(node.left),visit(node.right)
            if isinstance(node.op,ast.Add):value=a+b
            elif isinstance(node.op,ast.Sub):value=a-b
            elif isinstance(node.op,ast.Mult):value=a*b
            elif isinstance(node.op,ast.Div):value=a/b
            elif isinstance(node.op,ast.FloorDiv):value=Fraction(a//b)
            elif isinstance(node.op,ast.Mod):value=a%b
            elif isinstance(node.op,ast.Pow) and b.denominator==1 and abs(b)<=12:value=a**int(b)
            else:raise ValueError('Opération non prise en charge.')
        else:raise ValueError('Seuls les nombres et opérations arithmétiques sont autorisés.')
        if abs(value)>10**30 or value.denominator>10**30:raise ValueError('Valeur hors limites.')
        return value
    value=visit(tree.body)
    return {'expression':expression,'value':int(value) if value.denominator==1 else float(value),'exact':str(value)}


def convert(value,from_unit,to_unit):
    units={'mm':('length',Fraction(1,1000)),'cm':('length',Fraction(1,100)),'m':('length',1),'km':('length',1000),
           'mL':('volume',Fraction(1,1000)),'L':('volume',1),'m3':('volume',1000),
           'g':('mass',Fraction(1,1000)),'kg':('mass',1),'J':('energy',1),'kJ':('energy',1000),
           'MJ':('energy',1000000),'Wh':('energy',3600),'kWh':('energy',3600000),
           's':('time',1),'min':('time',60),'h':('time',3600)}
    if from_unit not in units or to_unit not in units or units[from_unit][0]!=units[to_unit][0]:raise ValueError('Unités incompatibles ou inconnues.')
    if type(value) not in (int,float) or abs(value)>10**20 or not math.isfinite(value):raise ValueError('Valeur non valide.')
    result=Fraction(str(value))*units[from_unit][1]/units[to_unit][1]
    return {'value':float(result),'unit':to_unit,'exact':str(result)}
