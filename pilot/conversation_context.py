"""Bounded pointers to the last exchange, never inherited evidence or citations."""
import json
import re
from . import documentary,retrieval


def refers_back(question):
    text=retrieval.normal(question)
    return bool(re.search(r'\b(ce|cet|cette|ces|meme|memes) (documents?|guides?|notices?|procedures?|sources?|reglages?|etapes?|appareils?|textes?|calculs?|valeurs?|resultats?|chiffres?|mesures?)\b|\b(ci dessus|precedemment|cela)\b',text)
                or re.search(r'^et (?:a|avec|sans|si|ensuite|pour cette|les conditions|les precautions)\b',text))


def previous_sources(history):
    current=max((i for i,row in enumerate(history) if row.get('role')=='user'),default=-1)
    prior=next((i for i in range(current-1,-1,-1) if history[i].get('role')=='assistant'),None)
    if prior is None:return None
    row=history[prior];evidence=row.get('documentary') or {}
    # An explicit empty evidence record takes precedence over legacy citations.
    sources=documentary.clean_sources(evidence.get('consulted_sources') if evidence else row.get('sources'))[:6]
    if not sources:return None
    question=next((message.get('content','') for message in reversed(history[:prior]) if message.get('role')=='user'),'')
    result={'previous_question':question[:1000],'historical_sources':[]}
    for source in sources:
        candidate={**source,'title':source['title'][:240],'consulted':False}
        if len(json.dumps(result,ensure_ascii=False))+len(json.dumps(candidate,ensure_ascii=False))>5000:break
        result['historical_sources'].append(candidate)
    return result if result['historical_sources'] else None
