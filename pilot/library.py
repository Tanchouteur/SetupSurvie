"""Read-only local knowledge tools and a rebuildable guide index."""
import ast
import asyncio
from fractions import Fraction
from html import unescape
from html.parser import HTMLParser
import math
import json
import hashlib
import unicodedata
import os
from pathlib import Path
import re
import zipfile
import threading
import time
import logging
from urllib.parse import quote, unquote, urljoin, urlparse
import xml.etree.ElementTree as ET

import httpx
from fastapi import HTTPException

from . import store,source_metadata,durable,retrieval,archive_index,kiwix_catalog,catalogue,kiwix_queries,search_cache,illustrations

GUIDES=Path(os.environ.get('GUIDES_DIR','/guides'))
KIWIX=os.environ.get('KIWIX_URL','http://kiwix:8080').rstrip('/')


class Text(HTMLParser):
    VOID={'area','base','br','col','embed','hr','img','input','link','meta','param','source','track','wbr'}
    def __init__(self,*,prefer_main=True):
        super().__init__();self.parts=[];self.skip=0;self.math=0;self.images=[];self.title=[];self.in_title=False;self.language=''
        self.prefer_main=prefer_main;self.tags=[];self.sections=[];self.active=[]
    def append(self,text):
        self.parts.append(text)
        for section in self.active:section['parts'].append(text)
    def handle_starttag(self,tag,attrs):
        attrs=dict(attrs)
        if tag not in self.VOID:self.tags.append(tag)
        if self.prefer_main and not self.skip and len(self.sections)<32 and (tag in ('article','main') or attrs.get('role')=='main'):
            section={'kind':'article' if tag=='article' else 'main','depth':len(self.tags),'parts':[]};self.sections.append(section);self.active.append(section)
        if tag=='html':self.language=attrs.get('lang','').split('-')[0]
        if tag in ('script','style','nav'):self.skip+=1
        if tag=='title':self.in_title=True
        if tag=='math':
            self.math+=1
            if self.math==1:self.append(' '+attrs.get('alttext','')+' ')
        if tag in ('p','br','h1','h2','h3','li','tr'):self.append('\n')
        if tag=='img' and attrs.get('src'):self.images.append({'src':attrs['src'],'alt':attrs.get('alt','')})
    def handle_endtag(self,tag):
        if tag in ('script','style','nav'):self.skip=max(0,self.skip-1)
        if tag=='math':self.math=max(0,self.math-1)
        if tag=='title':self.in_title=False
        if tag in ('p','h1','h2','h3','li','tr'):self.append('\n')
        if tag not in self.VOID:
            try:index=len(self.tags)-1-self.tags[::-1].index(tag)
            except ValueError:return
            self.active=[section for section in self.active if section['depth']<=index]
            del self.tags[index:]
    def handle_data(self,text):
        if self.in_title:self.title.append(text)
        if not self.skip and not self.math:self.append(text)
    def text(self):
        clean=lambda parts:'\n'.join(x.strip() for x in ''.join(parts).splitlines() if x.strip())
        if self.prefer_main:
            for kind in ('article','main'):
                choices=[clean(section['parts']) for section in self.sections if section['kind']==kind]
                if any(choices):return max(choices,key=len)
        return clean(self.parts)


class Fetched(tuple):
    def __new__(cls,body,kind,path):
        value=super().__new__(cls,(body,kind));value.path=path;return value


async def get(path, maximum=2_000_000):
    content=path.startswith('/content/')
    current=KIWIX+path;seen=set()
    async with asyncio.timeout(25),httpx.AsyncClient(trust_env=False,timeout=25,follow_redirects=False) as client:
        for step in range(6):
            if current in seen:raise HTTPException(502,'La redirection de ce document tourne en boucle. Essayez son original.')
            seen.add(current)
            async with client.stream('GET',current) as response:
                if content and response.status_code in (301,302,303,307,308):
                    location=response.headers.get('location','')
                    target=urlparse(urljoin(current,location));origin=urlparse(KIWIX)
                    # Only aliases within the same local archive. Never follow
                    # an external website, service endpoint or another book.
                    valid=bool(location) and target.scheme==origin.scheme and target.netloc==origin.netloc and not target.query and target.path.startswith('/content/')
                    if valid:
                        try:
                            resolved=safe_zim_path('zim:'+target.path.removeprefix('/content/'))
                            original=safe_zim_path('zim:'+path.removeprefix('/content/'))
                            valid=resolved.split('/')[0]==original.split('/')[0]
                        except HTTPException:valid=False
                    if not valid:raise HTTPException(502,'Ce document renvoie hors de son archive locale. Ouvrez sa collection pour vérifier le lien.')
                    if step==5:raise HTTPException(502,'Ce document comporte trop de redirections. Essayez son original.')
                    current=target._replace(fragment='').geturl();continue
                if response.status_code!=200:
                    detail='Cet article ne répond pas dans son archive locale. Réessayez ou ouvrez son original.' if content else 'Document indisponible.'
                    error=HTTPException(404,detail);error.upstream_status=response.status_code
                    raise error
                body=bytearray()
                async for chunk in response.aiter_bytes():
                    body.extend(chunk)
                    if len(body)>maximum:raise HTTPException(413,'Ce document est trop volumineux pour cet aperçu.')
                return Fetched(bytes(body),response.headers.get('content-type','application/octet-stream'),urlparse(current).path)


Catalog=kiwix_catalog.Catalog


class SearchResults(list):
    def __init__(self, values=(), coverage=None):
        super().__init__(values);self.coverage=coverage or {}


async def books(*,refresh=False):
    return await kiwix_catalog.load(store.ROOT,KIWIX,get,refresh=refresh)


INDEX_LOCK=threading.RLock()


def index_guides():
    with INDEX_LOCK:return _index_guides()


class TranslationText(Text):
    """Our generated HTML has explicit original-page sections, not PDF geometry."""
    def __init__(self):
        super().__init__(prefer_main=False);self.pages={};self.page=None
    def handle_starttag(self,tag,attrs):
        super().handle_starttag(tag,attrs)
        if tag=='section':
            match=re.fullmatch(r'page=(\d+)',dict(attrs).get('id',''))
            if match:self.page=int(match.group(1));self.pages[self.page]=[]
    def handle_data(self,data):
        super().handle_data(data)
        if self.page is not None and not self.skip and not self.math:self.pages[self.page].append(data)
    def handle_endtag(self,tag):
        super().handle_endtag(tag)
        if tag=='section':self.page=None


def _index_guides():
    if not GUIDES.is_dir():raise OSError('Dossier documentaire indisponible ; index précédent conservé.')
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
                        dates=source_metadata.metadata(item)
                        db.execute('INSERT INTO guide_dates VALUES(?,?,?,?) ON CONFLICT(path) DO UPDATE SET document_date=CASE WHEN excluded.document_date!=\'\' THEN excluded.document_date ELSE guide_dates.document_date END,edition=CASE WHEN excluded.edition!=\'\' THEN excluded.edition ELSE guide_dates.edition END,collected_at=CASE WHEN excluded.collected_at!=\'\' THEN excluded.collected_at ELSE guide_dates.collected_at END',
                                   (item['path'],dates['document_date'],dates['edition'] if item.get('edition') else '',dates['collected_at']))
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
            page_texts=[];numbered_pages=None
            try:
                if suffix in ('.txt','.md'):text=path.read_text(errors='replace')
                elif suffix=='.html':
                    p=TranslationText() if relative.startswith('TRAD-') else Text()
                    p.feed(path.read_text(encoding='utf-8',errors='replace'));text=p.text()
                    if isinstance(p,TranslationText):
                        numbered_pages=[(n,'\n'.join(lines)[:24000]) for n,lines in p.pages.items()]
                        page_texts=[text for _,text in numbered_pages]
                elif suffix=='.pdf':
                    from pypdf import PdfReader
                    cache=store.ROOT/'index-cache';durable.mkdir(cache)
                    stat=path.stat();key=hashlib.sha256(('pdf-v1:'+relative+':'+str(stat.st_mtime_ns)+':'+str(stat.st_size)).encode()).hexdigest()
                    cached=cache/(key+'.json')
                    page_texts=None
                    if cached.is_file():
                        try:
                            page_texts=json.loads(cached.read_text(encoding='utf-8'))
                            if not isinstance(page_texts,list) or any(not isinstance(page,str) for page in page_texts):page_texts=None
                        except (OSError,ValueError):pass
                    if page_texts is None:
                        reader=PdfReader(path)
                        if len(reader.pages)>1200:
                            record['status']='page_limit';continue
                        page_texts=[(page.extract_text() or '')[:24000] for page in reader.pages]
                        durable.write_bytes(cached,json.dumps(page_texts,ensure_ascii=False).encode('utf-8'),private=True)
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
            for number,page_text in (numbered_pages if numbered_pages is not None else enumerate(page_texts,1)):
                if page_text.strip():passages.append(('guide:'+relative+'#page='+str(number),title+' — page '+str(number),'/guides/'+quote(relative)+'#page='+str(number),language,page_text))
    with store.connect() as db:
        db.execute('DELETE FROM documents');db.executemany('INSERT INTO documents VALUES(?,?,?,?,?)',documents)
        db.execute('DELETE FROM passages');db.executemany('INSERT INTO passages VALUES(?,?,?,?,?)',passages)
    durable.mkdir(store.ROOT)
    try:durable.write_bytes(store.ROOT/'index-report.json',json.dumps({'documents':report,'indexed':sum(r['status']=='indexed' for r in report)},ensure_ascii=False).encode('utf-8'),private=True)
    except OSError:logging.getLogger(__name__).warning('Rapport documentaire non actualisé ; index de recherche conservé.')
    try:
        emergency={'kind':'SetupSurvie emergency index','documents':[{'title':title,'url':url,'language':language,'id':identifier} for identifier,title,url,language,_ in documents]}
        emergency_path=GUIDES/'_setupsurvie-index.json'
        if emergency_path.exists():
            old=json.loads(emergency_path.read_text(encoding='utf-8'))
            if not isinstance(old,dict) or old.get('kind')!=emergency['kind']:raise ValueError('Fichier non géré par SetupSurvie.')
        durable.write_bytes(emergency_path,json.dumps(emergency,ensure_ascii=False).encode('utf-8'))
    except (OSError,ValueError):
        logging.getLogger(__name__).warning('Liste de secours non actualisée ; index de recherche conservé.')
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
SYNONYMS.update({'feu':['feu','feux','fire','campfire'],'allumer':['allumer','allumage','lighting','ignite'],'camp':['camp','camping','campfire']})
TERM_ALIASES={'feux':'feu','stocker':'stocker','stockage':'stocker','conserver':'conservation','graine':'graines',
              'plante':'plantes','dent':'dents','radios':'radio','batteries':'batterie',
              'pompes':'pompe','velos':'velo','cartes':'carte','soudure':'soudage'}

# Practical and scientific vocabulary shared with the learning entry points.
LEARNING_ENGLISH={'algebre':'algebra','geometrie':'geometry','physique':'physics','chimie':'chemistry','biologie':'biology',
 'ecologie':'ecology','geologie':'geology','unites':'units','balances':'scales','pression':'pressure','humidite':'humidity',
 'etalonnage':'calibration','controle':'control','qualite':'quality','minerais':'ores','argile':'clay','chaux':'lime',
 'charbon':'charcoal','bois':'wood','fibres':'fibers','papier':'paper','affutage':'sharpening','engrenages':'gears',
 'moulins':'mills','tours':'lathe','tolerances':'tolerances','forge':'forge','traitements':'treatment','thermiques':'heat',
 'corrosion':'corrosion','metaux':'metals','savon':'soap','colles':'adhesives','encres':'inks','securite':'safety',
 'couture':'sewing','chaussures':'shoes','cordage':'rope','entretien':'maintenance','fertilite':'fertility',
 'greffage':'grafting','ravageurs':'pests','anatomie':'anatomy','hygiene':'hygiene','diagnostic':'diagnosis',
 'maternite':'maternal health','chirurgie':'surgery','pharmacologie':'pharmacology','enseignement':'education',
 'apprentissage':'apprenticeship','pedagogie':'teaching','biens':'commons','communs':'shared',
 'conflits':'conflicts','comptabilite':'accounting','cooperation':'cooperation','archives':'archives',
 'histoire':'history','techniques':'technology','medecine':'medicine','institutions':'institutions'}
for french,english in LEARNING_ENGLISH.items():
    SYNONYMS[french]=list(dict.fromkeys(SYNONYMS.get(french,[french])+[english]))
SYNONYMS['ph']=['ph','acidity','acidite']
SYNONYMS['cordage']=['cordage','cordages','rope','ropes','cord']
SYNONYMS['couture']=['couture','sewing','stitching','mending']
SYNONYMS['etalonnage']=['etalonnage','calibration','calibrating']
LEARNING_ENGLISH.update({'electromagnetisme':'electromagnetism','moteurs':'motors','roues':'wheels','hydrauliques':'hydraulic'})
for french,english in LEARNING_ENGLISH.items():
    SYNONYMS[french]=list(dict.fromkeys(SYNONYMS.get(french,[french])+[english]))


def index_report():
    path=store.ROOT/'index-report.json'
    if not path.is_file() or path.stat().st_size>2_000_000:
        return {'documents':[],'indexed':0,'status':'not_available'}
    try:return {**json.loads(path.read_text()),'status':'ready'}
    except (OSError,ValueError):return {'documents':[],'indexed':0,'status':'not_available'}


def search_terms(query):
    query=retrieval.search_subject(query)
    words=[unicodedata.normalize('NFKD',w).encode('ascii','ignore').decode().lower() for w in re.findall(r'\w+',query,flags=re.UNICODE)]
    return list(dict.fromkeys(TERM_ALIASES.get(w,w) for w in words if w and w not in STOPWORDS and len(w)>1))[:10]


async def search_archives(pattern_for, language, limit, *, query_plan=None,diagnostic=False,on_update=None,budget=12):
    """Explicit homogeneous archive sets; multilingual archives queried separately.

    Bounded fallbacks isolate a rejected archive instead of hiding an entire language.
    """
    from urllib.parse import urlencode
    report={'status':'complete','searched':0,'failed':0,'without_fulltext':0,'not_searched':0}
    try:
        available=await asyncio.wait_for(books(),timeout=6)
    except (TimeoutError,httpx.HTTPError,HTTPException):
        available=Catalog(available=False)
    report['catalog']=available.info() if isinstance(available,Catalog) else {'state':'live','collections':len(available)}
    if not getattr(available,'available',True):
        return [],{**report,'status':'unavailable','warning':'Les encyclopédies n’ont pas pu être interrogées. Les résultats des guides seuls ne prouvent pas l’absence d’information dans la bibliothèque.'}
    requested={'fr':'fra','en':'eng'}.get(language,language)
    groups={};eligible=[];selected_books=[];incompatible=[]
    saved_labels=catalogue.snapshot()
    manifests={Path(r['archive']).stem:r for r in archive_index.manifest(store.ROOT/'archive-index',Path(os.environ.get('ZIM_DIR','/zim'))).values()}
    generation=await asyncio.to_thread(search_cache.snapshot,Path(os.environ.get('ZIM_DIR','/zim')),available,store.ROOT/'archive-index')
    # Metadata tags can be absent or stale even when an index exists. Query
    # announced indexes first, but probe the other archives within the same budget.
    def priority(book):
        name=retrieval.normal(str(book.get('book',''))+' '+str(book.get('title','')))
        known=manifests.get(book.get('book',''),{})
        indexed=known.get('has_fulltext_index') is True or book.get('fulltext') is not False
        preferred=next((i for i,term in enumerate(('wikibooks','wikihow','appropedia','wikipedia','outdoors','diy','gardening','bicycles','trueprepper')) if term in name),20)
        subjects=' '.join(query_plan.words) if query_plan else ''
        targeted=any(re.search(pattern,subjects) and any(term in name for term in sources) for pattern,sources in (
            (r'\b(velo|velos|bicycle|bicycles|crevaison|puncture)\b',('bicycles','wikibooks','wikihow')),
            (r'\b(couture|vetement|recoudre|clothes|mending)\b',('crafts','wikihow','wikibooks')),
            (r'\b(graines|semences|seed|seeds|compost|jardin)\b',('gardening','wikihow','wikibooks')),
            (r'\b(generateur|generator|pedale|pedales|solaire|solar)\b',('appropedia','energypedia','lowtech')),
            (r'\b(plomberie|fuite|leak)\b',('diy','wikihow'))))
        return (not indexed,not targeted,preferred,'fra' not in str(book.get('language','')))
    report['locally_indexed']=0
    for original in sorted(available,key=priority):
        book=dict(original)
        known=manifests.get(book.get('book',''),{})
        if known.get('has_fulltext_index') is True:book['fulltext']=True
        if query_plan and query_plan.collection and not catalogue.matches_collection(book,query_plan.collection,GUIDES,Path(os.environ.get('ZIM_DIR','/zim')),saved_labels):continue
        languages=archive_index.languages(book.get('language') or '')
        if requested and requested not in languages:continue
        selected_books.append(book)
        if book.get('fulltext') is False and known.get('status')!='ready':
            report['without_fulltext']+=1
        if known.get('status')=='ready' and (known.get('has_fulltext_index') is False or known.get('kiwix_language_compatible') is False or len(languages)!=1):
            report['locally_indexed']+=1;continue
        if len(languages)!=1 or known.get('kiwix_language_compatible') is False:
            incompatible.append({'book':book['book'],'languages':list(languages),'has_fulltext_index':known.get('has_fulltext_index',book.get('fulltext'))})
            continue
        if not book.get('book'):continue
        key='books.id' if book.get('search_id') else 'books.name'
        value=book.get('search_id') or book['book']
        entry=(len(eligible),book,key,value);eligible.append(entry)
        # Unknown/multilingual metadata must never contaminate a monolingual batch.
        large=known.get('bytes',0)>=10_000_000_000 or 'wikipedia_' in book['book'].lower()
        group=(languages,key,book.get('fulltext'), value if len(languages)!=1 or large else '')
        groups.setdefault(group,[]).append(entry)
    # Preserve priority across language groups. Previously every French batch
    # preceded the first English practical collection. Large archives get their
    # own request so their timeout cannot hide the five small archives beside it.
    batches=sorted([items[i:i+12] for items in groups.values() for i in range(0,len(items),12)],key=lambda batch:batch[0][0])
    terms=[word for _,word in sorted(enumerate(query_plan.words),key=lambda pair:(-len(query_plan.groups[pair[0]]),pair[0]))[:2]] if query_plan else []
    # The long progressive search must allow one primary and at most two existing
    # refinements per batch. Its deadline and shared lanes still bound the work.
    # Keep the short assistant/legacy path's existing ceiling.
    request_limit=32 if budget<=12 else max(32,len(batches)*(1+len(terms)))
    done=set();failed=set();records={};calls=0;semaphore=asyncio.Semaphore(2);title_semaphore=asyncio.Semaphore(2);refinements=[];refinement_attempted=0;refinement_failed=0;refinement_finished=0
    errors=[];error_counts={};cache_hits=0;trace=[]
    async def notify():
        if on_update:await on_update(list(records.values()),{'status':'partial','running':True,'searched':len(done),'failed':len(failed),
            'not_searched':max(0,len(eligible)-len(done)-len(failed)),'collections_selected':len(selected_books),'locally_indexed':report['locally_indexed'],
            'native_incompatible':len(incompatible),'deadline_ms':round(budget*1000)})
    def traced(stage,books,pattern,started,**outcome):
        if diagnostic and len(trace)<40:
            trace.append({'stage':stage,'collections':[str(book.get('book',''))[:300] for book in books],
                          'languages':[str(book.get('language',''))[:100] for book in books],
                          'pattern':str(pattern)[:200],'elapsed_ms':round((time.monotonic()-started)*1000),**outcome})
    def failure(error,kind,books,elapsed):
        status=getattr(error,'upstream_status',getattr(error,'status_code',None))
        if isinstance(error,httpx.HTTPStatusError):status=error.response.status_code
        reason='timeout' if isinstance(error,(TimeoutError,httpx.TimeoutException)) else 'invalid_response' if isinstance(error,(ET.ParseError,ValueError,TypeError)) else 'http_error' if status else 'connection_error'
        error_counts[reason]=error_counts.get(reason,0)+1
        if len(errors)<12:errors.append({'stage':kind,'reason':reason,'http_status':status if type(status) is int else None,'collections':[str(b.get('book',''))[:300] for b in books],
                                      'elapsed_ms':round((time.monotonic()-elapsed)*1000)})
        return status,reason
    async def run(batch, fallback=True, pattern_override=None):
        nonlocal calls,refinement_attempted,refinement_failed,refinement_finished,cache_hits
        lang=requested or ('eng' if all('eng' in re.split(r'[,;\s]+',str(e[1].get('language',''))) for e in batch) else '')
        params=[(batch[0][2],entry[3]) for entry in batch]
        pattern=pattern_override if pattern_override is not None else pattern_for(lang)
        params += [('pattern',pattern),('format','xml'),('pageLength',limit)]
        started=time.monotonic()
        try:
            async with semaphore:
                if calls>=request_limit:return
                calls+=1
                if pattern_override is not None:refinement_attempted+=1
                (raw,_),cached=await kiwix_queries.request(store.ROOT,KIWIX,'/search?'+urlencode(params),'fulltext',get,generation=generation,timeout=10 if budget>12 else 3);cache_hits+=cached
                tree=ET.fromstring(raw)
                traced('refinement' if pattern_override is not None else 'fulltext',[e[1] for e in batch],pattern,started,
                       outcome='success',results=len(tree.findall('./channel/item')),response_bytes=len(raw),cached=cached)
                if pattern_override is not None:refinement_finished+=1
                # This pinned Kiwix version does not parse Boolean OR reliably.
                # Gather shorter literal queries for a second pass, after every
                # archive has had its primary query and title lookup.
                if not tree.findall('./channel/item') and pattern_override is None and query_plan and (len(query_plan.words)>1 or query_plan.action in ('repair','preserve','purify','install','sharpen')):
                    refinements.append((batch,lang))
            done.update(entry[0] for entry in batch)
            for position,item in enumerate(tree.findall('./channel/item')):
                link=item.findtext('link','')
                if not link.startswith('/content/'):continue
                stem=unquote(link.removeprefix('/content/')).split('/')[0]
                book=next((e[1] for e in batch if e[1]['book']==stem),None)
                if book is None:continue
                try:identifier=safe_zim_path('zim:'+link.removeprefix('/content/'))
                except HTTPException:continue
                text=Text();description=item.find('description')
                if description is not None:
                    # Native RSS mixes XML highlight nodes with surrounding text;
                    # findtext alone drops every match after the first child.
                    # Keep escaped HTML and actual child markup readable, while
                    # Text still excludes scripts and styles from the excerpt.
                    text.feed(description.text or '')
                    for child in description:text.feed(ET.tostring(child,encoding='unicode',method='html'))
                record={'id':'zim:'+identifier,'_rank':position,'title':item.findtext('title',''),
                    '_query_complete':pattern_override is None,
                    'excerpt':text.text()[:600],'kind':item.findtext('book/title','Encyclopédie'),
                    'language':book.get('language',''),'url':link,'collection':book.get('title',''),'book':book['book'],**source_metadata.metadata(book)}
                prior=records.get(record['id'])
                if prior is None or prior.get('match')=='title':records[record['id']]=record
            await notify()
        except (TimeoutError,httpx.HTTPError,ET.ParseError,HTTPException,ValueError) as error:
            status,reason=failure(error,'refinement' if pattern_override is not None else 'fulltext',[e[1] for e in batch],started)
            traced('refinement' if pattern_override is not None else 'fulltext',[e[1] for e in batch],pattern,started,
                   outcome='error',reason=reason,http_status=status)
            if pattern_override is not None:refinement_failed+=1;refinement_finished+=1;return
            if len(batch)>1 and fallback and status in (400,404,413):
                await asyncio.gather(*(run([entry],False) for entry in batch))
            else:failed.update(entry[0] for entry in batch)
            await notify()
    title_done=0;title_failed=0
    async def title_lookup(book):
        nonlocal title_done,title_failed,cache_hits
        if not query_plan:return
        lang='eng' if 'eng' in str(book.get('language','')) and 'fra' not in str(book.get('language','')) else ''
        term=query_plan.title_en if lang=='eng' else query_plan.title_fr
        if not term:return
        started=time.monotonic()
        try:
            async with title_semaphore:
                (raw,_),cached=await kiwix_queries.request(store.ROOT,KIWIX,'/suggest?'+urlencode({'content':book['book'],'term':term,'count':12}),'title',get,generation=generation,timeout=5 if budget>12 else 2);cache_hits+=cached
                values=json.loads(raw)
                if not isinstance(values,list):raise ValueError('Invalid suggestions')
            title_done+=1
            traced('title',[book],term,started,outcome='success',results=len(values),response_bytes=len(raw),cached=cached)
            for position,value in enumerate(values[:12]):
                if not isinstance(value,dict) or value.get('kind')!='path' or not isinstance(value.get('path'),str):continue
                # Kiwix 3.8.1 HTML-escapes paths inside its JSON suggestions.
                # Decode that layer before URL validation, not after unquoting:
                # a percent-encoded literal "&amp;" remains part of an entry name.
                raw_path=unescape(value['path'])
                if raw_path.startswith('//') or re.match(r'^[a-z][a-z0-9+.-]*://',raw_path,re.I):continue
                path=raw_path.lstrip('/')
                # Namespace colons (Wikijunior:...) are valid local entry paths.
                if not path or path.startswith('content/'):continue
                try:identifier=safe_zim_path('zim:'+book['book']+'/'+path)
                except HTTPException:continue
                title=Text();title.feed(str(value.get('value') or value.get('label') or path))
                record={'id':'zim:'+identifier,'_rank':position,'title':title.text(),'excerpt':'Correspondance dans le titre ; ouvrir la source pour en vérifier le contenu.',
                        'kind':'article','language':book.get('language',''),'url':'/content/'+quote(identifier,safe='/'),
                        'collection':book.get('title',''),'book':book['book'],'match':'title',**source_metadata.metadata(book)}
                records.setdefault(record['id'],record)
            await notify()
        except (TimeoutError,httpx.HTTPError,HTTPException,ValueError,TypeError) as error:
            title_failed+=1;status,reason=failure(error,'title',[book],started)
            traced('title',[book],term,started,outcome='error',reason=reason,http_status=status)
            await notify()
    title_books=[]
    if query_plan and query_plan.words:
        def title_priority(book):return next((i for i,name in enumerate(('wikipedia','appropedia','wikibooks','wikihow')) if name in str(book.get('book','')).lower()),10)
        ordered_books=sorted(selected_books,key=title_priority);families=set()
        for book in ordered_books:
            family=next((name for name in ('wikipedia','appropedia','wikibooks','wikihow') if name in str(book.get('book','')).lower()),book['book'])
            if family not in families:title_books.append(book);families.add(family)
            if len(title_books)==4:break
        for book in ordered_books:
            if len(title_books)==4:break
            if book not in title_books:title_books.append(book)
    refinement_planned=0;deadline_exceeded=False
    import heapq
    pending=[(1,index,batch,None) for index,batch in enumerate(batches)]
    heapq.heapify(pending);scheduled=set();sequence=len(pending)
    def schedule_refinements(core_only):
        nonlocal sequence,refinement_planned
        for batch,lang in refinements:
            core=any(any(name in entry[1]['book'].lower() for name in ('wikibooks','wikihow','appropedia','outdoors','diy','crafts','gardening','bicycles','trueprepper')) for entry in batch)
            if core_only and not core:continue
            for word in terms:
                pattern=pattern_for(lang,[word]);key=(tuple(entry[0] for entry in batch),pattern)
                if pattern==pattern_for(lang):continue
                if key in scheduled:continue
                scheduled.add(key);sequence+=1;refinement_planned+=1
                heapq.heappush(pending,(0 if core else 2,sequence,batch,pattern))
    async def consume():
        while pending:
            _,_,batch,pattern=heapq.heappop(pending)
            await run(batch,pattern is None,pattern)
            schedule_refinements(True)
    try:
        async with asyncio.timeout(budget):
            await asyncio.gather(*(title_lookup(book) for book in title_books),consume(),consume())
            schedule_refinements(False)
            await asyncio.gather(consume(),consume())
    except TimeoutError:deadline_exceeded=True
    report.update(refinement_attempted=refinement_attempted,refinement_failed=refinement_failed,refinement_not_searched=max(0,refinement_planned-refinement_finished))
    report.update(title_searched=title_done,title_failed=title_failed,title_not_searched=len(title_books)-title_done-title_failed)
    report.update(searched=len(done),failed=len(failed),not_searched=len(eligible)-len(done)-len(failed))
    report['collections_selected']=len(selected_books)
    report['native_incompatible']=len(incompatible)
    report.update(errors=errors,error_counts=error_counts,cache_hits=cache_hits,cache_ttl_seconds=kiwix_queries.TTL,cache_disk_ttl_seconds=search_cache.MAX_AGE,cache_generation=generation[:16],deadline_exceeded=deadline_exceeded,deadline_ms=round(budget*1000),primary_requests=calls-refinement_attempted,request_limit=request_limit,batch_limit=12,concurrency={'fulltext':2,'titles':2,'shared_across_requests':True})
    messages=[]
    if report['catalog']['state']=='stale':
        report['status']='partial';messages.append('Le catalogue répond mal ; la dernière liste connue est utilisée. Sa date figure dans le diagnostic.')
    if not selected_books and not (query_plan and query_plan.collection):
        report['status']='partial';messages.append('Aucune encyclopédie disponible dans le catalogue interrogé ; les guides restent consultables.')
    if query_plan and query_plan.collection and not selected_books:
        report['status']='partial';messages.append('La collection demandée n’est pas disponible dans le catalogue interrogé. Cela ne prouve pas que le sujet est absent des autres documents.')
    if refinement_failed or report['refinement_not_searched']:
        report['status']='partial';messages.append('Certaines reformulations n’ont pas pu être interrogées ; les autres résultats sont conservés.')
    if title_failed or report['title_not_searched']:
        report['status']='partial';messages.append('La recherche dans certains titres n’a pas abouti ; les autres résultats sont conservés.')
    if report['failed'] or report['not_searched']:
        report['status']='partial';messages.append('Recherche partielle : certaines encyclopédies n’ont pas pu être interrogées. Aucun résultat ne permet de conclure que le sujet est absent du fonds.')
    if report['without_fulltext']:
        report['status']='partial';messages.append(str(report['without_fulltext'])+' collection(s) n’annoncent pas d’index de texte. Elles ont été interrogées dans la limite du budget ; la lecture directe reste disponible dans Collections.')
    if incompatible:
        report['status']='partial';messages.append(str(len(incompatible))+' collection(s) ne sont pas interrogeables par Kiwix avec leurs langues annoncées. Utilisez « Créer ou reprendre les index » pour préparer leur recherche locale ; les originaux restent accessibles dans Collections.')
    if error_counts:
        labels={'timeout':'délai dépassé','http_error':'réponse HTTP en erreur','connection_error':'connexion impossible','invalid_response':'réponse illisible'}
        messages.append('Appels documentaires en erreur : '+', '.join(str(count)+' '+labels[reason] for reason,count in sorted(error_counts.items()))+'. Le rapport de vérification conserve leurs causes et collections.')
    if messages:report['warning']=' '.join(messages)
    if diagnostic:report.update(trace=trace,index_requirements=incompatible[:40],trace_notice='Délais client, attente comprise ; charge CPU et temps interne du serveur non mesurés.')
    return list(records.values()),report


async def search(query,language='',limit=8,*,favorite_user=None,translations_only=False,collection='',domain='all',diagnostic=False,on_update=None,budget=12):
    query_plan=retrieval.plan(query,search_terms(query),SYNONYMS,collection)
    words=query_plan.words
    candidate_limit=min(80,max(20,limit*4))
    results=[]
    if words:
        expression=query_plan.fts()
        with store.connect() as db:
            for table in ('documents','passages'):
                restriction='';parameters=[expression,language,language]
                if favorite_user is not None:
                    restriction+=f" AND EXISTS(SELECT 1 FROM favorites f WHERE f.user_id=? AND f.source_id=CASE WHEN instr({table}.id,'#page=')>0 THEN substr({table}.id,1,instr({table}.id,'#page=')-1) ELSE {table}.id END)"
                    parameters.append(favorite_user)
                if translations_only:restriction+=" AND id LIKE 'guide:TRAD-%'"
                rows=db.execute(f"SELECT id,title,url,language,substr(text,1,20000) AS _text,snippet({table},4,'','', '…',45) AS excerpt FROM {table} WHERE {table} MATCH ? AND (?='' OR language=?) AND lower(id) NOT LIKE '%.pdf' {restriction} ORDER BY bm25({table}) LIMIT ?",(*parameters,candidate_limit)).fetchall()
                strict_ids={row['id'] for row in rows}
                if len(rows)<limit and len(words)>1:
                    relaxed=[query_plan.fts(relaxed=True),*parameters[1:]]
                    rows+=db.execute(f"SELECT id,title,url,language,substr(text,1,20000) AS _text,snippet({table},4,'','', '…',45) AS excerpt FROM {table} WHERE {table} MATCH ? AND (?='' OR language=?) AND lower(id) NOT LIKE '%.pdf' {restriction} ORDER BY bm25({table}) LIMIT ?",(*relaxed,candidate_limit)).fetchall()
                results.extend([{**dict(r),'_rank':position,'_query_complete':r['id'] in strict_ids,'kind':'guide',**guide_metadata(db,r['id'])} for position,r in enumerate(rows)])
            if favorite_user is not None and not translations_only:
                rows=db.execute("SELECT id,title,url,language,snippet(favorite_articles,5,'','', '…',30) AS excerpt FROM favorite_articles WHERE favorite_articles MATCH ? AND user_id=? AND (?='' OR language IN (?,?)) ORDER BY bm25(favorite_articles) LIMIT ?",(expression,favorite_user,language,language,{'fr':'fra','en':'eng'}.get(language,language),limit)).fetchall()
                results.extend([{**dict(row),'kind':'article'} for row in rows])
    if query_plan.collection:results=[r for r in results if query_plan.collection in retrieval.normal(str(r.get('provenance',''))+' '+r['title']+' '+r['id']).replace(' ','')]
    if favorite_user is not None or translations_only:
        catalogue.annotate(results,GUIDES,Path(os.environ.get('ZIM_DIR','/zim')))
        if domain!='all':results=[r for r in results if domain in r['domains']]
        return retrieval.ordered(results,query_plan,limit*2)
    def pattern_for(lang,selected_words=None):
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
        english.update(LEARNING_ENGLISH)
        english.update({'feu':'fire','allumer':'lighting','camp':'campfire','generateur':'generator','generatrice':'generator','pedale':'pedal','pedales':'pedal'})
        # Same vocabulary for archive requests and local FTS; do not rely only
        # on title suggestions to bridge a French question and English text.
        for key in ('couture','vetement','panneau','solaire','conserves','legume','affutage','outil'):
            concept=retrieval.CONCEPTS[key]
            for term in concept['terms']:english[term]=concept['en'][0]
        translated=[]
        for word in (words if selected_words is None else selected_words):
            concept=next((c for c in retrieval.CONCEPTS.values() if word in c['terms']),None)
            if lang=='eng':translated.append(english.get(word,concept['en'][0] if concept else word))
            else:translated.append(concept['fr'][0] if concept and word not in concept['fr'] else word)
        action={'repair':('reparation','repair'),'preserve':('conservation','storage'),'purify':('purification','purification'),'build':('construction','construction'),'install':('installation','installation'),'sharpen':('affutage','sharpening')}.get(query_plan.action)
        if action and selected_words is None and query_plan.action!='build':translated.append(action[lang=='eng'])
        return ' '.join(translated) if translated else query
    saved_metadata=catalogue.snapshot();zims=Path(os.environ.get('ZIM_DIR','/zim'))
    local_rows=[];current_articles=[];current_coverage={'status':'partial','running':True,'searched':0,'collections_selected':None};update_lock=asyncio.Lock()
    annotations=catalogue.SearchAnnotations(GUIDES,zims,saved_metadata);normalize=retrieval.NormalCache()
    processing={'snapshots':0,'selection_ms':0.0,'selection_cpu_ms':0.0}
    def selected_sync(items,fresh):
        started=time.monotonic();cpu=time.thread_time()
        combined=[dict(row) for row in items]
        for item in combined:item['language']=retrieval.article_language(item)
        metadata_available=annotations.annotate(combined,fresh=fresh)
        allowed={'fr','fra','en','eng'} if not language else {language,{'fr':'fra','en':'eng','fra':'fr','eng':'en'}.get(language,language)}
        combined=[r for r in combined if not r.get('language') or allowed.intersection(re.split(r'[,;\s]+',r['language']))]
        if domain!='all':combined=[r for r in combined if domain in r['domains']]
        ordered=retrieval.ordered(combined,query_plan,limit*2,normalizer=normalize)
        processing['snapshots']+=1;processing['selection_ms']+=(time.monotonic()-started)*1000;processing['selection_cpu_ms']+=(time.thread_time()-cpu)*1000
        return ordered,metadata_available
    async def selected(items,*,fresh=False):return await kiwix_queries.disk_io(selected_sync,items,fresh)
    async def notify():
        if not on_update:return
        async with update_lock:
            rows,_=await selected(results+local_rows+current_articles)
            await on_update(SearchResults(rows,{**current_coverage,'domain':domain,'collection':query_plan.collection}))
    async def native_update(rows,coverage):
        nonlocal current_articles,current_coverage
        current_articles=rows;current_coverage=coverage;await notify()
    async def read_local():
        found=await asyncio.to_thread(archive_index.search,store.ROOT/'archive-index',query_plan,language,candidate_limit,zims,
            collection_match=lambda book,selection:catalogue.matches_collection(book,selection,GUIDES,zims,saved_metadata))
        local_rows.extend(found);await notify();return found
    local_task=asyncio.create_task(read_local())
    try:
        await notify()
        articles,coverage=await search_archives(pattern_for,language,candidate_limit,query_plan=query_plan,diagnostic=diagnostic,on_update=native_update if on_update else None,budget=budget)
        local=await local_task
    finally:
        if not local_task.done():local_task.cancel()
        await asyncio.gather(local_task,return_exceptions=True)
    ordered,metadata_available=await selected(results+local+articles,fresh=True)
    if diagnostic:coverage['processing']={**{key:round(value,2) for key,value in processing.items()},'metadata_evaluations':annotations.evaluated,'source_revision_checks':annotations.source_checks,'normalizations':normalize.misses,'normalization_hits':normalize.hits,'normalization_cache_bytes':normalize.bytes}
    coverage['local_query']=getattr(local,'coverage',{})
    if any(coverage['local_query'].get(key,0) for key in ('failed','outdated')):
        if coverage['status']=='complete':coverage['status']='partial'
        coverage['warning']=coverage.get('warning','')+' Certains index locaux sont indisponibles ou périmés ; relancez leur préparation.'
    coverage['coverage_scope']='searchable_text'
    coverage['domain']=domain
    coverage['metadata_status']='ready' if metadata_available else 'degraded'
    if not metadata_available:
        if coverage['status']=='complete':coverage['status']='partial'
        coverage['warning']=coverage.get('warning','')+' Certains classements corrigés ne sont pas disponibles ; le classement automatique reste utilisé pour ces documents.'
    progress=archive_index.status(store.ROOT/'archive-index')
    coverage['local_index']={key:progress[key] for key in ('phase','archives','completed','articles','workers','started','reader_probe','error_summary') if key in progress}
    coverage['parallelism']=4
    coverage['collection']=query_plan.collection
    coverage['query_terms']=words
    return SearchResults(ordered,coverage)




def safe_zim_path(identifier):
    path=identifier.removeprefix('zim:')
    for _ in range(3):path=unquote(path)
    if not identifier.startswith('zim:') or '\\' in path or re.search(r'%[0-9a-fA-F]{2}',path) or any(part in ('.','..') for part in path.split('/')) or '\x00' in path:raise HTTPException(400,'Référence de document non valide.')
    return path


def guide_metadata(db,identifier):
    path=identifier.removeprefix('guide:').split('#page=')[0]
    row=db.execute('SELECT m.provenance,m.licence,d.document_date,d.edition,d.collected_at FROM guide_meta m LEFT JOIN guide_dates d ON m.path=d.path WHERE m.path=?',(path,)).fetchone()
    item=dict(row) if row else {}
    return {**item,**source_metadata.metadata(item),**source_metadata.translation_metadata(db,path)}


def focused_page(identifier,query):
    """Choose an already indexed page inside this PDF only, never a new corpus.

    Keep explicit page selections literal. Missing index/matches preserve the
    original limited preview; this does not claim that every page was read.
    """
    if not identifier.startswith('guide:') or not identifier.lower().endswith('.pdf'):return identifier
    plan=retrieval.plan(query,search_terms(query),SYNONYMS)
    if not plan.words:return identifier
    with store.connect() as db:
        for relaxed in (False,True):
            rows=db.execute("SELECT id,title,url,language,text AS _text FROM passages WHERE passages MATCH ? AND substr(id,1,?)=? AND substr(id,?,6)='#page=' ORDER BY bm25(passages) LIMIT 12",
                (plan.fts(relaxed=relaxed),len(identifier),identifier,len(identifier)+1)).fetchall()
            if rows:
                ordered=retrieval.ordered([dict(row) for row in rows],plan,1)
                if ordered:return ordered[0]['id']
    return identifier


async def source(identifier):
    if identifier.startswith('guide:'):
        with store.connect() as db:
            table='passages' if '#page=' in identifier else 'documents'
            row=db.execute('SELECT * FROM '+table+' WHERE id=?',(identifier,)).fetchone()
            meta=guide_metadata(db,identifier)
        if not row:raise HTTPException(404,'Guide introuvable.')
        result={**dict(row),**meta,'kind':'guide','images':[],
                'text_truncated':len(row['text']) >= (24000 if table=='passages' else 500000),
                'preview':identifier.lower().split('#page=')[0].endswith('.pdf')}
        catalogue.annotate([result],GUIDES,Path(os.environ.get('ZIM_DIR','/zim')));return result
    path=safe_zim_path(identifier)
    available=await books()
    if not getattr(available,'available',True):raise HTTPException(503,'La liste des collections est momentanément indisponible. Réessayez ou ouvrez le document d’origine.')
    book=next((b for b in available if b['book']==path.split('/')[0]),None)
    if book is None:raise HTTPException(404,'Collection introuvable.')
    try:fetched=await get('/content/'+quote(path,safe='/'))
    except (TimeoutError,httpx.TimeoutException):raise HTTPException(504,'Le lecteur a dépassé son délai de réponse. Réessayez ou ouvrez le document d’origine.')
    except httpx.HTTPError:raise HTTPException(503,'Le lecteur ne parvient pas à joindre cette archive. Réessayez ou ouvrez le document d’origine.')
    raw,_=fetched
    resolved_path=getattr(fetched,'path','/content/'+quote(path,safe='/'))
    p=Text();p.feed(raw.decode(errors='replace'))
    text=p.text()
    images=illustrations.html_images(raw.decode(errors='replace'),resolved_path)
    result={'id':identifier,'title':''.join(p.title) or path.split('/')[-1].replace('_',' '),'text':text[:100000],'text_truncated':len(text)>100000,
            'url':'/content/'+quote(path,safe='/'),'kind':'article','images':images,'language':p.language or retrieval.article_language({'id':identifier,'language':book.get('language','')}),'collection':book.get('title',''),'book':book['book'],**source_metadata.metadata(book)}
    catalogue.annotate([result],GUIDES,Path(os.environ.get('ZIM_DIR','/zim')));return result


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
