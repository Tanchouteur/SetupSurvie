"""Query-focused, byte-budgeted source passages, without model inference.

Offsets always address the original extracted text. Loading a document is not
counted as reading it: only passages admitted to the model packet are evidence.
"""
import asyncio
import hashlib
import json
import re

from . import library,retrieval,illustrations


def size(value):return len(json.dumps(value,ensure_ascii=False).encode('utf-8'))


def synthesis(query):return retrieval.search_subject(query)!=query


def primary_query(query):
    """Use the primary topic for the initial search, retaining the full user
    request in conversation for comparisons and any complementary tool calls.
    Do not split abbreviations or decimals, or ordinary literal searches.
    """
    query=illustrations.topic(query)
    if not synthesis(query):return query
    parts=re.split(r'[.!?;]\s+(?=(?:compare|comparez|cite|citez|donne|donnez|presente|présente|redige|rédige|explique|expliquez|reponds|réponds|utilise|detaille|détaille|fais|montre|write|give|explain|include|use)\b)',query,maxsplit=1,flags=re.I)
    return parts[0] if len(parts)>1 and subject(parts[0]).words else query


def clip(text,maximum):return text.encode('utf-8')[:max(0,maximum)].decode('utf-8',errors='ignore')


def subject(query):return retrieval.plan(query,library.search_terms(query),library.SYNONYMS)


def passages(text,query,maximum):
    if not text.strip() or maximum<80:return []
    if len(text)<=1800 and len(text.encode('utf-8'))<=maximum:return [{'offset':0,'text':text,'next_offset':len(text)}]
    plan=subject(query);groups=plan.token_groups
    width=min(1800,max(80,maximum//2));stride=max(40,width//2)
    procedure=set('etape etapes materiel outils montage construction fabrication procedure instructions steps materials tools assembly construction building repairing'.split())
    candidates=[]
    for start in range(0,len(text),stride):
        value=text[start:start+width];normalized=retrieval.normal(value);words=set(normalized.split())
        matches=sum(any(group<=words for group in variants) for variants in groups)
        anchors=[]
        for variants in groups:
            matched=next((group for group in variants if group<=words),set())
            anchors.extend(match.start() for word in matched if (match:=re.search(r'\b'+re.escape(word)+r'\b',normalized)))
        center=sum(anchors)/len(anchors) if anchors else 0
        centrality=min(center,max(0,len(normalized)-center))/max(1,len(normalized))
        practical=len(words&procedure) if matches and plan.practical and plan.action else 0
        score=matches*10+(10 if groups and matches==len(groups) else 0)+practical+centrality
        candidates.append((score,start,value))
    candidates.sort(key=lambda row:(-row[0],row[1]));selected=[];remaining=maximum
    for score,start,value in candidates:
        if selected and candidates[0][0]>=10 and score<10:break
        if any(start<part['next_offset'] and start+len(value)>part['offset'] for part in selected):continue
        value=clip(value,remaining)
        if not value.strip():continue
        selected.append({'offset':start,'text':value,'next_offset':start+len(value)})
        remaining-=len(value.encode('utf-8'))
        if len(selected)>=2 or remaining<120:break
    return sorted(selected,key=lambda part:part['offset'])


def candidates(items):
    """Distinct documents before extra PDF pages; preserve the first result.

    Prefer another collection before a third document from the same collection,
    but never remove the remaining matches when only one collection is useful.
    """
    first=[];later=[];documents=set();collections={}
    for item in items:
        identifier=item['id'];base=identifier.split('#page=')[0]
        collection=item.get('collection') or item.get('provenance') or identifier.split('/',1)[0]
        count=collections.get(collection,0);collections[collection]=count+1
        if base in documents or count>=2:later.append(item)
        else:first.append(item)
        documents.add(base)
    return first+later


async def read(identifiers,query,maximum,cache,reference,*,fetch=None,on_failed=None):
    """Read concurrently, then admit balanced passages in deterministic order."""
    identifiers=list(dict.fromkeys(str(value) for value in identifiers))[:12]
    requested=len(identifiers)
    # Leave enough room per document for identity, offsets and a useful passage.
    wanted=min(len(identifiers),12,max(1,maximum//950)) if maximum>=650 else 0
    semaphore=asyncio.Semaphore(3)
    async def load(identifier):
        async with semaphore:
            try:
                actual=await library.kiwix_queries.disk_io(library.focused_page,identifier,primary_query(query)) if fetch is None and identifier.lower().endswith('.pdf') else identifier
                if actual not in cache:cache[actual]=await asyncio.wait_for((fetch or library.source)(actual),timeout=8)
                return cache[actual]
            except Exception:return None
    loaded=await asyncio.gather(*(load(identifier) for identifier in identifiers)) if wanted else []
    result={'results':[],'failed':0,'omitted':0,'reading':'selected_passages','selection_limited':False}
    fingerprints=set()
    for index,(identifier,item) in enumerate(zip(identifiers,loaded)):
        if len(result['results'])>=wanted:break
        if item is None or not isinstance(item.get('text'),str) or not item['text'].strip():
            result['failed']+=1
            if on_failed:on_failed(identifier)
            continue
        digest=hashlib.sha256(item['text'].encode('utf-8')).digest()
        if digest in fingerprints:continue
        remaining=maximum-size(result)-150
        allocation=remaining//max(1,min(wanted-len(result['results']),len(loaded)-index))
        # Reserve source metadata before selecting text. Do not mark it read yet.
        metadata={key:item.get(key,'') for key in ('id','title','language','document_date','edition','archive_date','collected_at','provenance')}
        metadata.update({key:item[key] for key in ('is_ai_translation','original_id','original_title','original_document_date','original_edition','translation_notice') if key in item})
        parts=passages(item['text'],query,max(0,allocation-size(metadata)-220))
        if not parts:continue
        entry={**metadata,'passages':parts,'partial_read':bool(item.get('preview') or item.get('text_truncated') or sum(len(p['text']) for p in parts)<len(item['text'])),'text_limit_reached':bool(item.get('text_truncated'))}
        # References can contain extra private metadata; transmit a compact view.
        probe={**entry,'number':999}
        if size({**result,'results':result['results']+[probe]})>maximum:continue
        received='\n[…]\n'.join(part['text'] for part in parts)
        excerpt='\n[…]\n'.join(part['text'] for part in passages(received,query,600))
        ref=reference({**item,'excerpt':excerpt},True)
        entry['number']=ref['number'];result['results'].append(entry);fingerprints.add(digest)
    result['omitted']=requested-len(result['results'])-result['failed']
    result['selection_limited']=bool(result['omitted'] or result['failed'])
    return result


def code_spans(answer):
    return [match.span() for match in re.finditer(r'```[\s\S]*?(?:```|\Z)|~~~[\s\S]*?(?:~~~|\Z)|`[^`\n]*`',answer)]


CITATION=re.compile(r'(?<![\w\\])\[(\d{1,3}(?:\s*[,;]\s*\d{1,3})*)(?:\s*,\s*p(?:age)?s?\.?\s*(\d{1,4}))?\]',re.I)


def citation_spans(answer):
    spans=code_spans(answer)
    return [{'start':match.start(),'end':match.end(),'numbers':{int(n) for n in re.split(r'\s*[,;]\s*',match[1])},
             'page':int(match[2]) if match[2] else None}
            for match in CITATION.finditer(answer) if not any(start<=match.start()<end for start,end in spans)]


def citation_numbers(answer):
    return {number for part in citation_spans(answer) for number in part['numbers']}


def citations_valid(answer,references):
    read={item['number'] for item in references.values() if item.get('consulted')}
    citations=citation_numbers(answer)
    return bool(citations&read) and citations<=read


def fallback(references):
    lines=['L’IA n’a pas terminé une synthèse avec des références vérifiables. Voici les extraits effectivement consultés ; ils ne constituent pas une synthèse validée.']
    for item in list(references.values()):
        if not item.get('consulted'):continue
        title=re.sub(r'[\[\]<>*_`\\]','',str(item.get('title','Document')))
        lines.append(f"\n[{item['number']}] **{title}** — {item.get('document_date') or 'date du document inconnue'}.\n")
        lines.append('\n'.join('> '+line for line in str(item.get('excerpt',''))[:600].splitlines()))
        if len(lines)>=19:break
    return '\n'.join(lines)
