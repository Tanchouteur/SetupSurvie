"""Small, deterministic query planning and ranking. No model or network required."""
from dataclasses import dataclass
from collections import OrderedDict
from functools import cached_property
import re
import unicodedata
from urllib.parse import unquote


def normal(text):
    decomposed=unicodedata.normalize('NFKD',unquote(str(text)))
    return re.sub(r'[^a-z0-9]+',' ',''.join(char for char in decomposed if not unicodedata.combining(char)).lower()).strip()


def search_subject(query):
    """Strip an explicit summary request, preserving technical uses of 'synthesis'."""
    raw=normal(query)
    request=re.match(r'^(?:(?:s il te plait|svp|please)\s+)?(?:(?:peux tu|pourrais tu|pouvez vous|could you|can you)\s+)?(?:(?:me|nous)\s+)?(?:'
                     r'(?:(?:fais|fait|faites|faire|donne|donnez|donner|prepare|preparer|redige|rediger|give|write|make)\s+)(?:(?:moi|nous|me)\s+)?(?:(?:un|une|le|la|a|the)\s+)?(?:synthese|resume|summary|recapitulatif|bilan)'
                     r'|resume|resumer|summarize|summarise)\b',raw)
    if not request:return query
    tail=raw[request.end():].strip();changed=False
    framing=set('le la les un une de du des d ces mes nos vos informations information info infos documents document sources source articles article the my our these local locaux locale locales disponibles disponible trouves trouvees found available'.split())
    for _ in range(8):
        boundary=next((m for m in re.finditer(r'\b(?:au sujet de|a propos de|sur|concernant|about|of|on|de|des|du)\b',tail) if set(tail[:m.start()].split())<=framing),None)
        if boundary is None or not tail[boundary.end():].strip():break
        tail=tail[boundary.end():].strip();changed=True
    return tail if changed else query


class NormalCache:
    """Per-search normalization, discarded after completion; no stale global text."""
    MAX_BYTES=32_000_000
    MAX_ENTRIES=4096

    def __init__(self):self.values=OrderedDict();self.bytes=0;self.hits=0;self.misses=0

    def __call__(self,text):
        text=str(text)
        prior=self.values.get(text)
        if prior is not None:
            self.hits+=1;self.values.move_to_end(text);return prior[0]
        self.misses+=1;value=normal(text);size=len(text.encode('utf-8',errors='surrogatepass'))+len(value.encode('utf-8',errors='surrogatepass'))
        if size<=self.MAX_BYTES:
            self.values[text]=(value,size);self.bytes+=size
            while len(self.values)>self.MAX_ENTRIES or self.bytes>self.MAX_BYTES:
                _,(_,removed)=self.values.popitem(last=False);self.bytes-=removed
        return value


# Intent words are useful for ranking, but must not exclude a book that uses
# "production" instead of "allumer", or "construction" instead of "fabriquer".
ACTIONS=set('allumer allumage fabriquer fabrication construire construction reparer reparation entretenir entretien apprendre preparer preparation produire production faire realiser comment technique techniques tutoriel methode methodes proceder procedure rendre installer installation'.split())
EXTRA_STOP=set('source sources aucun aucune autres autre resultat resultats merci ok oui bonjour salut tu ne j aimerais savoir aimerai existe existent existez trouve trouves trouvee trouvez rien quelque chose ce cette cet cela ca bien aussi alors donc dans wikipedia wikipédia appropedia wikihow wikibooks wikilivres encyclopedie encyclopedies francais francaise anglais anglaise ni article articles explication explications expliquer explique expliquez expliquerais marche fonctionne fonctionne t il possible peut on s y pourquoi why'.split())
EXTRA_STOP.update('comme dois doit doivent devrais devrait devraient pourrais pourrait pouvons pouvez utiliser utilisez utilise utilisation puis ensuite'.split())
COLLECTIONS={'wikipedia':('wikipedia','wikipédia'),'appropedia':('appropedia',),'wikihow':('wikihow',),'wikibooks':('wikibooks','wikilivres')}
# Related technical expressions, not links to hand-picked documents. These also
# apply to guide retrieval and ranking; a match never certifies a procedure.
CONCEPTS={
 'feu':{'terms':['feu','feux','fire','campfire','allumage','amadou','tinder'],'fr':['production de feu','allumage feu'],'en':['fire making','fire starting']},
 'friction':{'terms':['friction','frottement','frottements'],'fr':['frottement'],'en':['friction']},
 'generateur':{'terms':['generateur','generatrice','generator','alternateur'],'fr':['generateur'],'en':['generator']},
 'pedale':{'terms':['pedale','pedales','pedal','pedals','pedaling'],'fr':['pedales'],'en':['pedal']},
 'potable':{'terms':['potable','potabilisation','purification','drinking','purifying'],'fr':['potabilisation eau'],'en':['drinking water']},
 'reparation':{'terms':['reparation','reparer','repair','repairing'],'fr':['reparation'],'en':['repair']},
 'conservation':{'terms':['conservation','conserver','preservation','preserving','storage'],'fr':['conservation'],'en':['preservation']},
 'batterie':{'terms':['batterie','batteries','battery'],'fr':['batterie'],'en':['battery']},
 'semences':{'terms':['semences','semence','graines','graine','seed','seeds'],'fr':['semences'],'en':['seeds']},
 'velo':{'terms':['velo','velos','bicycle','bicycles','bike','bikes'],'fr':['velo'],'en':['bicycle']},
 'crevaison':{'terms':['crevaison','crevaisons','puncture','punctures','rustine','patching'],'fr':['crevaison'],'en':['puncture']},
 'filtration':{'terms':['filtrer','filtration','filter','filtering','filteration'],'fr':['filtration'],'en':['filtering']},
 'fuite':{'terms':['fuite','fuites','leak','leaks','leaking'],'fr':['fuite'],'en':['leak']},
 'eau':{'terms':['eau','water'],'fr':['eau'],'en':['water']},
 'abri':{'terms':['abri','abris','shelter','shelters'],'fr':['abri'],'en':['shelter']},
 'couture':{'terms':['couture','coudre','recoudre','ravauder','sewing','mending'],'fr':['couture'],'en':['sewing']},
 'vetement':{'terms':['vetement','vetements','garment','garments','clothes','clothing'],'fr':['vetement'],'en':['clothes']},
 'panneau':{'terms':['panneau','panneaux','panel','panels'],'fr':['panneau'],'en':['panel']},
 'solaire':{'terms':['solaire','solaires','solar','photovoltaic','photovoltaique'],'fr':['solaire'],'en':['solar']},
 'conserves':{'terms':['conserve','conserves','canning'],'fr':['conserves'],'en':['canning']},
 'legume':{'terms':['legume','legumes','vegetable','vegetables'],'fr':['legumes'],'en':['vegetables']},
 'affutage':{'terms':['affutage','affuter','aiguiser','sharpening','sharpen'],'fr':['affutage'],'en':['sharpening']},
 'outil':{'terms':['outil','outils','tool','tools'],'fr':['outil'],'en':['tool']},
 'fixation':{'terms':['fixer','fixation','fixing','attach','attaching','securing'],'fr':['fixation'],'en':['fixing']},
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
    practical=bool(re.search(r'\b(comment|faire|allumer|allumage|fabriquer|fabrication|construire|construction|reparer|reparation|entretenir|entretien|realiser|installer|installation|recoudre|coudre|affuter|aiguiser|techniques|how|build|make|making|repair|tutorial)\b',raw)) and not re.search(r'\b(histoire|archeologie|history|origines)\b',raw)
    if re.search(r'\b(pourquoi|why)\b',raw) and not re.search(r'\b(comment|how)\b',raw):practical=False
    vocabulary=set(synonyms)|{word for concept in CONCEPTS.values() for word in concept['terms']}
    terms=[w[:-1] if w not in vocabulary and w.endswith('s') and w[:-1] in vocabulary else w for w in words if w not in EXTRA_STOP]
    meaningful=[w for w in terms if w not in ACTIONS]
    if meaningful:terms=meaningful
    if any(w in CONCEPTS['feu']['terms'] for w in terms):terms=[w for w in terms if w not in ('start','starting','make','making','produce')]
    if 'radio' in terms:terms=[w for w in terms if w!='poste']
    action=next((name for name,pattern in INTENTS.items() if re.search(pattern,raw)), '')
    if practical and any(word in CONCEPTS['feu']['terms'] for word in terms) and not action:action='ignite'
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
    scope=('group:'+normal(collection[6:]).replace(' ','')) if collection.startswith('group:') else normal(collection).replace(' ','') or detected
    return Plan(query,dedup,groups,practical,scope,' '.join(title_fr),' '.join(title_en),action)


def rank(item,query,position=0,*,normalizer=None):
    normalize=normalizer or normal
    title=normalize(item.get('title',''));text=normalize(item.get('excerpt','')+' '+item.get('_text',''))
    if not query.groups:return 0
    title_tokens=set(title.split());text_tokens=set(text.split())
    title_hits=sum(any(term<=title_tokens for term in group) for group in query.token_groups)/len(query.groups)
    text_hits=sum(any(term<=text_tokens for term in group) for group in query.token_groups)/len(query.groups)
    score=65*title_hits+25*text_hits+8/(1+item.get('_rank',position))
    if title_hits<1 and text_hits<1:score-=35
    if query.action:
        evidence=INTENTS[query.action]
        if re.search(evidence,title):
            # An explicit task title should beat a broad subject title whose
            # excerpt merely mentions the action. This is still a reading lead,
            # never evidence that the article contains a verified procedure.
            contextual=bool(re.search(r'\b(pourquoi|why|histoire|history|historical|origines?|origins?|risques?|dangers?|hazards?|safety|combien)\b|\b((should|do|can) (i|we|you)|does|how (many|much)|faut il|dois je|puis je)\b',title))
            instruction=bool(re.search(r'\b(comment|guide|tutorial|tutoriels?|manuels?|manuals?|instructions|etapes|steps|methode|method)\b|\bhow (to|(can|do|should) (i|we|you|one))\b',title))
            direct=query.practical and title_hits==1 and len(title_tokens)>1 and (not contextual or instruction)
            score+=55 if direct else 12 if query.practical and contextual and not instruction else 28
            if direct and (instruction or title.startswith('diy ')):score+=12 # A reading lead, never a verified procedure.
        elif re.search(evidence,text):score+=12
        else:score-=12
    path=str(item.get('id','')).split('/',1)[-1]
    if re.search(r'(?:^|/)(?:Category:|Special:|questions/tagged/|tags/)',path,re.I):score-=45
    if re.search(r'(highest voted|questions tagged|category|categorie)',title):score-=35
    if item.get('language') in ('fr','fra'):score+=2
    canonical=' '.join(query.words)
    if canonical and (canonical==title or normalize(query.original)==title):score+=5 if query.practical else 30
    if query.practical:
        classification=item.get('classification',{})
        if classification.get('method')=='human' and classification.get('document_type') in ('procedure','manual'):score+=10
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


def match_quality(item,query,*,normalizer=None):
    normalize=normalizer or normal
    title=set(normalize(item.get('title','')).split())
    text=set(normalize(item.get('excerpt','')+' '+item.get('_text','')).split())
    title_hits=sum(any(term<=title for term in group) for group in query.token_groups)
    text_hits=sum(any(term<=text for term in group) for group in query.token_groups)
    if title_hits==len(query.groups) and title_hits:return 'subject'
    if text_hits:return 'mention'
    return 'uncertain'


def ordered(items,query,limit,*,normalizer=None):
    normalize=normalizer or NormalCache()
    ranked=sorted(enumerate(items),key=lambda pair:(-rank(pair[1],query,pair[0],normalizer=normalize),pair[1].get('id','')))
    result=[];seen=set();parents={}
    for _,item in ranked:
        exercise=item.get('classification',{}).get('document_type')=='exercise' or re.search(r'\b(quiz|qcm|questionnaire|exercises?|exercices?)\b',normalize(item.get('title','')))
        if exercise and query.practical and not re.search(r'\b(quiz|qcm|questionnaire|exercises?|exercices?)\b',normalize(query.original)):continue
        combined=normalize(item.get('title','')+' '+item.get('excerpt','')+' '+item.get('_text',''))
        tokens=set(combined.split())
        hits=sum(any(term<=tokens for term in group) for group in query.token_groups)
        required=max(1,(2*len(query.groups)+2)//3)
        excerpt=normalize(item.get('excerpt','')+' '+item.get('_text',''))
        title_tokens=set(normalize(item.get('title','')).split())
        title_hits=sum(any(term<=title_tokens for term in group) for group in query.token_groups)
        native_without_excerpt=item.get('_query_complete') and not excerpt and title_hits>0
        if hits<required and not native_without_excerpt:continue
        if query.practical and query.action:
            evidence=INTENTS[query.action]
            named_device=query.action=='build' and (not excerpt or item.get('match')=='title') and len(query.groups)>1 and title_hits==len(query.groups)
            classification=item.get('classification',{})
            human_manual=title_hits>0 and classification.get('method')=='human' and classification.get('document_type') in ('procedure','manual')
            if not re.search(evidence,combined) and not named_device and not human_manual:continue
        template=bool(re.search(r'\b(modele a remplir|modele a completer|template to fill|fill in this template)\b',excerpt[:2000]))
        if query.practical and template and not title_hits and not re.search(r'\b(modele|template|inventaire|inventory)\b',normalize(query.original)):continue
        if item.get('match')=='title' and re.search(r'(song|single|album)',normalize(item.get('excerpt',''))) and query.practical:continue
        if item['id'] in seen:continue
        seen.add(item['id'])
        clean={k:v for k,v in item.items() if not k.startswith('_')}
        clean['match_quality']=match_quality(item,query,normalizer=normalize)
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
 'repair':r'\b(reparer|reparation|repair|repairing|maintenance|entretien|entretenir|recoudre|ravauder|mending|sewing|couture|stitching|rustine|remplacer|remplacement|changement|replace|replacement)\b',
 'preserve':r'\b(conserver|conservation|stocker|stockage|storage|store|storing|preserve|preserving|preservation|saving|save)\b',
 'purify':r'\b(potable|potabilisation|potabiliser|purifier|purification|filtrer|filtration|disinfection|desinfection|purifying|treatment|traitement)\b',
 'build':r'\b(fabriquer|fabrication|construire|construction|build|building|assembly|assemble|diy)\b',
 'install':r'\b(installer|installation|install|installing)\b',
 'sharpen':r'\b(affutage|affuter|aiguiser|sharpen|sharpening)\b',
 'ignite':r'\b(allumer|allumage|amadou|tinder|campfire|feu de camp|ignition|ignite|friction|percussion|production de feu|faire du feu|fire making|fire starting|start a fire|lighting a fire|making a fire)\b',
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
    resilience=bool(re.search(r'\b(eau|water|feu|fire|abri|shelter|potager|semences|seed|seeds|survie|survival|repair|reparation|reparer|maintenance|batterie|battery|generator|generateur|premiers secours|first aid|compost|plomberie|plumbing|couture|sewing|mending|conservation alimentaire|food preservation|conserves|canning|solaire|solar|photovoltaic|photovoltaique|radio|radios|antenne|antennes|communications|telecommunications|affutage|sharpening)\b',text))
    cultural=bool(re.search(r'\b(histoire|history|science|sciences|physique|physics|biologie|biology|mathematiques|mathematics|enseignement|education|geographie|geography|litterature|literature|philosophie|philosophy)\b',text))
    return (['resilience'] if resilience else [])+(['culture'] if cultural or not resilience else [])
