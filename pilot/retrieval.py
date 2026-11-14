"""Small, deterministic query planning and ranking. No model or network required."""
from dataclasses import dataclass
from functools import cached_property
import re
import unicodedata
from urllib.parse import unquote


def normal(text):
    return re.sub(r'[^a-z0-9]+',' ',unicodedata.normalize('NFKD',unquote(str(text))).encode('ascii','ignore').decode().lower()).strip()


# Intent words are useful for ranking, but must not exclude a book that uses
# "production" instead of "allumer", or "construction" instead of "fabriquer".
ACTIONS=set('allumer allumage fabriquer fabrication construire construction reparer reparation entretenir entretien apprendre preparer preparation produire production faire realiser comment technique techniques tutoriel methode methodes proceder procedure rendre'.split())
EXTRA_STOP=set('source sources aucun aucune autres autre resultat resultats merci ok oui bonjour salut tu ne j aimerais savoir aimerai existe existent existez trouve trouves trouvee trouvez rien quelque chose ce cette cet cela ca bien aussi alors donc dans wikipedia wikipédia appropedia wikihow wikibooks wikilivres encyclopedie encyclopedies francais francaise anglais anglaise ni article articles explication explications expliquer explique expliquez expliquerais marche fonctionne fonctionne t il possible peut on s y'.split())
COLLECTIONS={'wikipedia':('wikipedia','wikipédia'),'appropedia':('appropedia',),'wikihow':('wikihow',),'wikibooks':('wikibooks','wikilivres')}
# Related technical expressions, not links to hand-picked documents. These also
# apply to guide retrieval and ranking; a match never certifies a procedure.
CONCEPTS={
 'feu':{'terms':['feu','feux','fire','campfire','allumage','amadou','tinder'],'fr':['production de feu','allumage feu'],'en':['fire making','fire starting']},
 'generateur':{'terms':['generateur','generatrice','generator','alternateur'],'fr':['generateur'],'en':['generator']},
 'pedale':{'terms':['pedale','pedales','pedal','pedals','pedaling'],'fr':['pedales'],'en':['pedal']},
 'potable':{'terms':['potable','potabilisation','purification','drinking','purifying'],'fr':['potabilisation eau'],'en':['drinking water']},
 'reparation':{'terms':['reparation','reparer','repair','repairing'],'fr':['reparation'],'en':['repair']},
 'conservation':{'terms':['conservation','conserver','preservation','preserving','storage'],'fr':['conservation'],'en':['preservation']},
 'batterie':{'terms':['batterie','batteries','battery'],'fr':['batterie'],'en':['battery']},
 'semences':{'terms':['semences','semence','graines','graine','seed','seeds'],'fr':['semences'],'en':['seeds']},
 'velo':{'terms':['velo','velos','bicycle','bicycles','bike','bikes'],'fr':['velo'],'en':['bicycle']},
 'eau':{'terms':['eau','water'],'fr':['eau'],'en':['water']},
 'abri':{'terms':['abri','abris','shelter','shelters'],'fr':['abri'],'en':['shelter']},
}


@dataclass
class Plan:
    original:str
    words:list
    groups:list
    practical:bool
    collection:str=''
    title_fr:str=''
    title_en:str=''
    action:str=''

    @cached_property
    def token_groups(self):
        return [[set(normal(term).split()) for term in group] for group in self.groups]

    def fts(self,relaxed=False):
        groups=['('+' OR '.join('"'+s.replace('"','')+'"' for s in group[:12])+')' for group in self.groups]
        return (' OR ' if relaxed else ' AND ').join(groups)


def plan(query,words,synonyms,collection=''):
    raw=normal(query)
    detected=next((key for key,aliases in COLLECTIONS.items() if any(re.search(r'\b'+re.escape(normal(alias))+r'\b',raw) for alias in aliases)), '')
    practical=bool(re.search(r'\b(comment|faire|allumer|allumage|fabriquer|fabrication|construire|construction|reparer|reparation|entretenir|entretien|realiser|techniques|how|build|make|making|repair|tutorial)\b',raw)) and not re.search(r'\b(histoire|archeologie|history|origines)\b',raw)
    vocabulary=set(synonyms)|{word for concept in CONCEPTS.values() for word in concept['terms']}
    terms=[w[:-1] if w not in vocabulary and w.endswith('s') and w[:-1] in vocabulary else w for w in words if w not in EXTRA_STOP]
    meaningful=[w for w in terms if w not in ACTIONS]
    if meaningful:terms=meaningful
    action=next((name for name,pattern in INTENTS.items() if re.search(pattern,raw)), '')
    if action in ('repair','preserve'):
        terms=[w for w in terms if w not in CONCEPTS['reparation' if action=='repair' else 'conservation']['terms']] or terms
    groups=[];dedup=[]
    for word in terms:
        concept=next((value for value in CONCEPTS.values() if word in value['terms']),None)
        group=list(dict.fromkeys([word]+synonyms.get(word,[])+(concept['terms'] if concept else [])))
        if any(set(group)&set(g) for g in groups):continue
        groups.append(group);dedup.append(word)
    title_fr=[];title_en=[]
    for word,group in zip(dedup,groups):
        concept=next((c for c in CONCEPTS.values() if word in c['terms']),None)
        title_fr.append(concept['fr'][0] if concept else word)
        title_en.append(concept['en'][0] if concept else (next((x for x in reversed(group) if x!=word),word)))
    return Plan(query,dedup,groups,practical,normal(collection).replace(' ','') or detected,' '.join(title_fr),' '.join(title_en),action)


def rank(item,query,position=0):
    title=normal(item.get('title',''));text=normal(item.get('excerpt','')+' '+item.get('_text',''))
    if not query.groups:return 0
    title_tokens=set(title.split());text_tokens=set(text.split())
    title_hits=sum(any(term<=title_tokens for term in group) for group in query.token_groups)/len(query.groups)
    text_hits=sum(any(term<=text_tokens for term in group) for group in query.token_groups)/len(query.groups)
    score=65*title_hits+25*text_hits+8/(1+item.get('_rank',position))
    if title_hits<1 and text_hits<1:score-=35
    if query.action:
        evidence=INTENTS[query.action]
        if re.search(evidence,title):score+=28
        elif re.search(evidence,text):score+=12
        else:score-=12
    path=str(item.get('id','')).split('/',1)[-1]
    if re.search(r'(?:^|/)(?:Category:|Special:|questions/tagged/|tags/)',path,re.I):score-=45
    if re.search(r'(highest voted|questions tagged|category|categorie)',title):score-=35
    if item.get('language') in ('fr','fra'):score+=2
    canonical=' '.join(query.words)
    if canonical and canonical==title:score+=5 if query.practical else 30
    if query.practical:
        if any('feu' in group for group in query.groups) and re.search(r'\b(production de feu|faire du feu|allumage|fire making|fire starting|start a fire)\b',title):score+=20
        if re.search(r'\b(construction|fabrication|allumage|production|techniques|guide|instructions|tutorial|making|build|repair|starting)\b',title):score+=15
        if re.search(r'\b(quiz|questionnaire|qcm)\b',title+' '+text):score-=24
        if re.search(r'\b(risques|prevention|incendies|reglementation|histoire|history)\b',title):score-=12
    # Query terms should occur together; a long book mentioning each in unrelated
    # chapters must not beat an actual matching passage.
    if len(query.groups)>1:
        last={}
        for index,word in enumerate(text.split()):
            for number,group in enumerate(query.token_groups):
                if any(term=={word} for term in group):last[number]=index
            if len(last)==len(query.groups) and index-min(last.values())<60:
                score+=6;break
    return score


def match_quality(item,query):
    title=set(normal(item.get('title','')).split())
    text=set(normal(item.get('excerpt','')+' '+item.get('_text','')).split())
    title_hits=sum(any(term<=title for term in group) for group in query.token_groups)
    text_hits=sum(any(term<=text for term in group) for group in query.token_groups)
    if title_hits==len(query.groups) and title_hits:return 'subject'
    if text_hits:return 'mention'
    return 'uncertain'


def ordered(items,query,limit):
    ranked=sorted(enumerate(items),key=lambda pair:(-rank(pair[1],query,pair[0]),pair[1].get('id','')))
    result=[];seen=set();parents={}
    for _,item in ranked:
        if item.get('match')=='title' and re.search(r'(song|single|album)',normal(item.get('excerpt',''))) and query.practical:continue
        if item['id'] in seen:continue
        seen.add(item['id'])
        clean={k:v for k,v in item.items() if not k.startswith('_')}
        clean['match_quality']=match_quality(item,query)
        parent=item['id'].split('#page=')[0]
        if '/appropedia' in item['id'] or item['id'].startswith('zim:appropedia'):
            parent=re.sub(r'/(?:[a-z]{2,3}(?:-[a-z]+)?)$','',parent)
        if item['id'].startswith('zim:') and parent in parents:
            continue
        if '#page=' in item['id'] and parent in parents:
            others=parents[parent].setdefault('other_matches',[])
            if len(others)<5:others.append({k:item.get(k,'') for k in ('id','title','url')})
            continue
        parents[parent]=clean;result.append(clean)
    return result[:limit]


INTENTS={
 'repair':r'\b(reparer|reparation|repair|repairing|maintenance|entretien|entretenir)\b',
 'preserve':r'\b(conserver|conservation|stocker|storage|preserving|preservation|saving|save)\b',
 'purify':r'\b(potable|potabilisation|potabiliser|purifier|purification|filtrer|filtration|disinfection|desinfection|purifying|treatment|traitement)\b',
 'build':r'\b(fabriquer|fabrication|construire|construction|build|building|assembly|assemble|diy)\b',
}

def article_language(item):
    """Wiki translation suffixes describe the article, not its archive language."""
    language=item.get('language','')
    if 'appropedia' in item.get('book',item.get('id','')).lower():
        suffix=re.search(r'/([a-z]{2})(?:-[a-z]+)?$',item.get('id',''))
        if suffix:return suffix[1]
    return {'fra':'fr','eng':'en'}.get(language,language)

def domains(item):
    # Conservative automatic indication; never certifies a procedure.
    text=normal(item.get('title','')+' '+item.get('excerpt','')+' '+item.get('_text','')[:4000])
    resilience=bool(re.search(r'\b(eau|water|feu|fire|abri|shelter|potager|semences|seed|seeds|survie|survival|repair|reparation|reparer|maintenance|batterie|battery|generator|generateur|premiers secours|first aid|compost|plomberie|plumbing|couture|sewing|conservation alimentaire|food preservation)\b',text))
    return ['resilience'] if resilience else ['culture']
