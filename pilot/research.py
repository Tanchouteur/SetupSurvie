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
    # The full request stays in history; a second question must not become
    # mandatory vocabulary for retrieving the first subject. Decimal points
    # and abbreviations are not sentence separators here.
    first=re.split(r'[?!]\s+(?=\S)',query,maxsplit=1)[0]
    if first!=query and subject(first).words:return first
    if not synthesis(query):return query
    parts=re.split(r'[.!?;]\s+(?=(?:compare|comparez|cite|citez|donne|donnez|presente|présente|redige|rédige|explique|expliquez|reponds|réponds|utilise|detaille|détaille|fais|montre|write|give|explain|include|use)\b)',query,maxsplit=1,flags=re.I)
    return parts[0] if len(parts)>1 and subject(parts[0]).words else query


def clip(text,maximum):return text.encode('utf-8')[:max(0,maximum)].decode('utf-8',errors='ignore')


def subject(query):
    plan=retrieval.plan(query,library.search_terms(query,maximum=None),library.SYNONYMS)
    # Reading a section must recognise ordinary action wording as well as its
    # heading. This expands passage scoring, not global search requirements.
    phases=[['demarrage','demarrer','commencer','commence','commencera','start','starting','startup'],
            ['continuer','continuation','poursuivre','poursuite','continue','continuing']]
    plan.groups=[list(dict.fromkeys(group+[term for phase in phases if set(group)&set(phase) for term in phase])) for group in plan.groups]
    return plan


def passages(text,query,maximum):
    if not text.strip() or maximum<80:return []
    if len(text.encode('utf-8'))<=maximum:return [{'offset':0,'text':text,'next_offset':len(text)}]
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
    first=[];later=[];pages=[];documents=set();collections={};seen=set()
    for item in items:
        identifier=item['id'];base=identifier.split('#page=')[0]
        if identifier in seen:continue
        seen.add(identifier)
        for extra in item.get('other_matches',[])[:5]:
            page=extra.get('id','')
            if identifier.startswith('guide:') and base.lower().endswith('.pdf') and re.fullmatch(re.escape(base)+r'#page=[1-9]\d{0,3}',page) and page not in seen:
                pages.append({**item,**extra,'excerpt':'','other_matches':[]});seen.add(page)
        collection=item.get('collection') or item.get('provenance') or identifier.split('/',1)[0]
        count=collections.get(collection,0);collections[collection]=count+1
        if base in documents or count>=2:later.append(item)
        else:first.append(item)
        documents.add(base)
    return first+later+pages


async def read(identifiers,query,maximum,cache,reference,*,fetch=None,on_failed=None,prefer_documents=False):
    """Read concurrently, then admit balanced passages in deterministic order."""
    identifiers=list(dict.fromkeys(str(value) for value in identifiers))[:12]
    requested=len(identifiers)
    # Leave enough room per document for identity, offsets and a useful passage.
    wanted=min(len(identifiers),12,max(1,maximum//650)) if maximum>=650 else 0
    semaphore=asyncio.Semaphore(3)
    async def load(identifier):
        async with semaphore:
            try:
                actual=await library.kiwix_queries.disk_io(library.focused_page,identifier,primary_query(query)) if fetch is None and identifier.lower().endswith('.pdf') else identifier
                if actual not in cache:cache[actual]=await asyncio.wait_for((fetch or library.source)(actual),timeout=8)
                return cache[actual]
            except Exception:return None
    loaded=await asyncio.gather(*(load(identifier) for identifier in identifiers)) if wanted else []
    # Several indexed pages can be grouped under one search hit. Within a
    # book prefer the section matching the requested topic, not the repeated
    # device name in every page title. Read other documents before extra pages.
    groups=subject(primary_query(query)).token_groups
    def focus(item):
        if not item or not isinstance(item.get('text'),str):return (-1,-1)
        title=set(retrieval.normal(re.sub(r' — page \d+$','',item.get('title',''))).split())
        specific=[group for group in groups if not any(term<=title for term in group)] or groups
        head=set(retrieval.normal(item['text'][:400]).split());body=set(retrieval.normal(item['text']).split())
        return (sum(any(term<=head for term in group) for group in specific),sum(any(term<=body for term in group) for group in specific))
    paired=list(zip(identifiers,loaded));buckets={}
    for position,(identifier,item) in enumerate(paired):
        base=identifier.split('#page=')[0]
        if identifier.startswith('guide:') and '#page=' in identifier:buckets.setdefault(base,[]).append(position)
    for positions in buckets.values() if prefer_documents else ():
        if len(positions)>1:
            best=max(positions,key=lambda position:focus(paired[position][1]))
            paired[positions[0]],paired[best]=paired[best],paired[positions[0]]
    # One best page per PDF first, then alternatives if budget permits.
    first=[];extras=[];seen=set()
    for pair in paired:
        identifier=pair[0];base=identifier.split('#page=')[0]
        if '#page=' in identifier and base in seen:extras.append(pair)
        else:first.append(pair)
        seen.add(base)
    if prefer_documents:wanted=min(wanted,len(first))
    ordered=first+extras if prefer_documents else paired
    identifiers=[identifier for identifier,_ in ordered];loaded=[item for _,item in ordered]
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


def source_id_citations(answer):
    code=code_spans(answer)
    return [match for match in re.finditer(r'\[((?:guide|zim):[^\]\n]{1,2000})\]',answer) if not any(start<=match.start()<end for start,end in code)]


def citation_source(identifier,references):
    source=references.get(identifier)
    if source:return source
    page=re.fullmatch(r'(guide:.+\.pdf)#page=([1-9]\d{0,3})',identifier,re.I)
    if page:
        source=references.get(page[1])
        if source and int(page[2]) in source.get('pages',[]):return source
    return None


def normalize_citations(answer,references):
    for match in reversed(source_id_citations(answer)):
        source=citation_source(match[1],references)
        if source and source.get('consulted'):
            page=re.search(r'#page=([1-9]\d{0,3})$',match[1])
            label=str(source['number'])+(', p. '+page[1] if page else '')
            answer=answer[:match.start()]+'['+label+']'+answer[match.end():]
    return answer


def unsupported_citations(answer,references):
    read={item['number'] for item in references.values() if item.get('consulted')}
    return bool(citation_numbers(answer)-read) or any(not (citation_source(match[1],references) or {}).get('consulted') for match in source_id_citations(answer))


def citations_valid(answer,references):
    read={item['number'] for item in references.values() if item.get('consulted')}
    citations=citation_numbers(answer)
    return bool(citations&read) and not unsupported_citations(answer,references)


def fallback(references):
    if not any(item.get('consulted') for item in references.values()):return 'Les références trouvées n’ont pas fourni de passage lisible pour vérifier cette réponse. Ouvrez les documents depuis la bibliothèque ou réessayez la lecture ; un extrait de recherche ne suffit pas à valider une procédure.'
    lines=['L’IA n’a pas terminé une synthèse avec des références vérifiables. Voici les extraits effectivement consultés ; ils ne constituent pas une synthèse validée.']
    for item in list(references.values()):
        if not item.get('consulted'):continue
        title=re.sub(r'[\[\]<>*_`\\]','',str(item.get('title','Document')))
        lines.append(f"\n[{item['number']}] **{title}** — {item.get('document_date') or 'date du document inconnue'}.\n")
        lines.append('\n'.join('> '+line for line in str(item.get('excerpt',''))[:600].splitlines()))
        if len(lines)>=19:break
    return '\n'.join(lines)
