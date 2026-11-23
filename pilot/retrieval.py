"""Small, deterministic query planning and ranking. No model or network required."""
from dataclasses import dataclass, replace
from collections import OrderedDict
from functools import cached_property
from itertools import islice,product
import re
import unicodedata
from urllib.parse import unquote

from . import wiki_structure


def normal(text):
    decomposed=unicodedata.normalize('NFKD',unquote(str(text)))
    return re.sub(r'[^a-z0-9]+',' ',''.join(char for char in decomposed if not unicodedata.combining(char)).lower()).strip()


def search_subject(query):
    """Strip an explicit summary request, preserving technical uses of 'synthesis'."""
    raw=normal(query)
    request=re.match(r'^(?:(?:s il te plait|svp|please)\s+)?(?:(?:peux tu|pourrais tu|pouvez vous|could you|can you)\s+)?(?:(?:me|nous)\s+)?(?:'
                     r'(?:(?:fais|fait|faites|faire|donne|donnez|donner|prepare|preparer|redige|rediger|give|write|make)\s+)(?:(?:moi|nous|me)\s+)?(?:(?:un|une|le|la|a|the)\s+)?(?:(?:court|courte|bref|breve|detaille|detaillee|rapide|short|brief|detailed)\s+)?(?:synthese|resume|summary|recapitulatif|bilan)'
                     r'|resume|resumer|summarize|summarise)\b',raw)
    if not request:return query
    tail=raw[request.end():].strip();changed=False
    framing=set('le la les un une de du des d et and ces mes nos vos informations information info infos documents document sources source articles article videos video transcriptions transcripts captions bibliotheque library the my our these local locaux locale locales disponibles disponible trouves trouvees found available'.split())
    framing.update('notice notices guide guides manuel manuels ouvrage ouvrages livre livres texte textes page pages manual manuals book books'.split())
    # Only after an explicit summary request and document framing. These verbs
    # describe the requested sources, not vocabulary that every source must use.
    boundary_pattern=(r'\b(?:au sujet de|a propos de|sur|concernant|about|of|on|de|des|du|'
                      r'(?:(?:qui )?(?:expliquent|explique|decrivent|decrit|presentent|presente|detaillent|detaille)|'
                      r'expliquant|decrivant|presentant|detaillant)|'
                      r'(?:(?:that |which )?(?:explain|explains|describe|describes)|explaining|describing))\b')
    for _ in range(8):
        boundary=next((m for m in re.finditer(boundary_pattern,tail) if set(tail[:m.start()].split())<=framing),None)
        if boundary is None or not tail[boundary.end():].strip():break
        tail=tail[boundary.end():].strip();changed=True
    return tail if changed else query


def author_subject(query):
    """Retrieve the named work before answering who wrote it or what it is about."""
    match=re.fullmatch(r'(?:qui a ecrit|who wrote) (.+?)'
                       r'(?: et (?:ca raconte quoi|de quoi (?:ca|il|elle) parle|quel est (?:le sujet|le resume))'
                       r'| and what is (?:it|the book) about)?',normal(query))
    return match[1] if match else ''


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
ACTIONS=set('allumer allumage fabriquer fabrication construire construction reparer reparation entretenir entretien apprendre preparer preparation produire production faire realiser comment technique techniques tutoriel methode methodes proceder procedure rendre installer installation identifier reconnaitre identification recognize recognise identify'.split())
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
 'reparation':{'terms':['reparation','reparer','repair','repairing','remplacer','remplacement','replace','replacement'],'fr':['reparation'],'en':['repair']},
 'conservation':{'terms':['conservation','conserver','preservation','preserving','storage'],'fr':['conservation'],'en':['preservation']},
 'batterie':{'terms':['batterie','batteries','battery'],'fr':['batterie'],'en':['battery']},
 'semences':{'terms':['semences','semence','graines','graine','seed','seeds'],'fr':['semences'],'en':['seeds']},
 'velo':{'terms':['velo','velos','bicycle','bicycles','bike','bikes'],'fr':['velo'],'en':['bicycle']},
 'crevaison':{'terms':['crevaison','crevaisons','puncture','punctures','rustine','patching'],'fr':['crevaison'],'en':['puncture']},
 'filtration':{'terms':['filtrer','filtration','filter','filtering','filteration'],'fr':['filtration'],'en':['filtering']},
 'fuite':{'terms':['fuite','fuites','leak','leaks','leaking'],'fr':['fuite'],'en':['leak']},
 'tuyau':{'terms':['tuyau','tuyaux','pipe','pipes'],'fr':['tuyau'],'en':['pipe']},
 'eau':{'terms':['eau','water'],'fr':['eau'],'en':['water']},
 'abri':{'terms':['abri','abris','shelter','shelters'],'fr':['abri'],'en':['shelter']},
 'couture':{'terms':['couture','coudre','recoudre','ravauder','sewing','mending'],'fr':['couture'],'en':['sewing']},
 'vetement':{'terms':['vetement','vetements','garment','garments','clothes','clothing'],'fr':['vetement'],'en':['clothes']},
 'panneau':{'terms':['panneau','panneaux','panel','panels'],'fr':['panneau'],'en':['panel']},
 'solaire':{'terms':['solaire','solaires','solar','photovoltaic','photovoltaique'],'fr':['solaire'],'en':['solar']},
 'aliment':{'terms':['aliment','aliments','alimentaire','alimentaires','nourriture','food','foods'],'fr':['aliments'],'en':['food']},
 'conserves':{'terms':['conserve','conserves','canning'],'fr':['conserves'],'en':['canning']},
 'legume':{'terms':['legume','legumes','vegetable','vegetables'],'fr':['legumes'],'en':['vegetables']},
 'affutage':{'terms':['affutage','affuter','aiguiser','sharpening','sharpen'],'fr':['affutage'],'en':['sharpening']},
 'outil':{'terms':['outil','outils','tool','tools'],'fr':['outil'],'en':['tool']},
 'fixation':{'terms':['fixer','fixation','fixing','attach','attaching','securing'],'fr':['fixation'],'en':['fixing']},
}


# Number variants, not arbitrary prefix matching or a translation dictionary.
# Preserve ambiguous/invariant words and identifiers; explicit concepts above
# retain their curated aliases. Unusual inflections still require the source form.
INVARIABLE_WORDS={'corps','cours','discours','parcours','secours','poids','sens','temps','pays',
                  'siemens','https','news','taux','faux','chaux','deux','mieux','vieux','epoux'}
AL_WITH_S={'bal','carnaval','chacal','etal','festival','recital','regal','fatal','naval','banal'}
# Do not join normalized "émail" with "email": accents are already folded here.
AIL_WITH_AUX={'bail':'baux','corail':'coraux','soupirail':'soupiraux',
              'travail':'travaux','vantail':'vantaux','vitrail':'vitraux'}
AIL_SINGULAR={plural:single for single,plural in AIL_WITH_AUX.items()}
OU_WITH_X={'bijou','caillou','chou','genou','hibou','joujou','pou'}


def number_forms(word):
    """Bounded aliases on whole tokens; never drop a separate query constraint."""
    if not re.fullmatch(r'[a-z]{3,}',word) or word in INVARIABLE_WORDS:return [word]
    if word in AIL_SINGULAR:forms=[word,AIL_SINGULAR[word],AIL_SINGULAR[word]+'s']
    elif word in AIL_WITH_AUX:forms=[word,AIL_WITH_AUX[word],word+'s']
    elif word.endswith('eaux'):forms=[word,word[:-1]]
    elif word.endswith('aux'):
        forms=[word,word[:-1]]
        singular=word[:-3]+'al'
        if singular not in AL_WITH_S:forms.append(singular)
    elif word.endswith('eux'):forms=[word,word[:-1]]
    elif word.endswith('oux'):
        forms=[word]+([word[:-1]] if word[:-1] in OU_WITH_X else [])
    elif word.endswith('s'):
        if len(word)<4 or word.endswith(('is','us','os','ss','ais','ois')):return [word]
        forms=[word,word[:-1]]
    elif word.endswith(('x','z')):return [word]
    elif word.endswith(('eau','au','eu')):forms=[word,word+'x',word+'s']
    elif word in OU_WITH_X:forms=[word,word+'x']
    elif len(word)>3 and word.endswith('al') and word not in AL_WITH_S:forms=[word,word[:-2]+'aux',word+'s']
    else:forms=[word,word+'s']
    return list(dict.fromkeys(forms))


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
    action=next((name for name,pattern in INTENTS.items() if re.search(pattern,raw)), '')
    detected=next((key for key,aliases in COLLECTIONS.items() if any(re.search(r'\b'+re.escape(normal(alias))+r'\b',raw) for alias in aliases)), '')
    practical=bool(action or re.search(r'\b(comment|faire|allumer|allumage|fabriquer|fabrication|construire|construction|reparer|reparation|entretenir|entretien|realiser|installer|installation|recoudre|coudre|affuter|aiguiser|techniques|how|build|make|making|repair|tutorial)\b',raw)) and not re.search(r'\b(histoire|archeologie|history|origines)\b',raw)
    if re.search(r'\b(pourquoi|why)\b',raw) and not re.search(r'\b(comment|how)\b',raw):practical=False
    vocabulary=set(synonyms)|{word for concept in CONCEPTS.values() for word in concept['terms']}
    terms=[w[:-1] if w not in vocabulary and w.endswith('s') and w[:-1] in vocabulary else w for w in words if w not in EXTRA_STOP]
    if re.search(r'\bprotection civile\b',raw):
        terms=['protection civile' if w=='protection' else w for w in terms if w!='civile']
        if 'en temps de' in raw:terms=[w for w in terms if w!='temps']
        synonyms={**synonyms,'protection civile':['consignes','sauvegarde','civil protection']}
    meaningful=[w for w in terms if w not in ACTIONS]
    if meaningful:terms=meaningful
    if any(w in CONCEPTS['feu']['terms'] for w in terms):terms=[w for w in terms if w not in ('start','starting','make','making','produce')]
    if 'radio' in terms:terms=[w for w in terms if w!='poste']
    if practical and any(word in CONCEPTS['feu']['terms'] for word in terms) and not action:action='ignite'
    if action in ('repair','preserve'):
        terms=[w for w in terms if w not in CONCEPTS['reparation' if action=='repair' else 'conservation']['terms']] or terms
    groups=[];dedup=[]
    for word in terms:
        concept=next((value for value in CONCEPTS.values() if word in value['terms']),None)
        group=list(dict.fromkeys([word]+synonyms.get(word,[])+(concept['terms'] if concept else [])))
        if (concept is CONCEPTS['potable'] and any(term in CONCEPTS['eau']['terms'] for term in terms)):
            group.extend(('traitement', 'treatment', 'potabiliser'))
        if not concept and word not in synonyms:group=number_forms(word)
        if any(set(group)&set(g) for g in groups):continue
        groups.append(group);dedup.append(word)
    title_fr=[];title_en=[]
    for word,group in zip(dedup,groups):
        concept=next((c for c in CONCEPTS.values() if word in c['terms']),None)
        french = concept['fr'][0] if concept else word
        title_fr.append(word if word in number_forms(french) else french)
        title_en.append(concept['en'][0] if concept else next((x for x in reversed(synonyms.get(word,[])) if x!=word),word))
    if action=='preserve' and len(dedup)==1 and dedup[0] in CONCEPTS['aliment']['terms']:
        title_fr=['conservation des aliments'];title_en=['food preservation']
    scope=('group:'+normal(collection[6:]).replace(' ','')) if collection.startswith('group:') else normal(collection).replace(' ','') or detected
    return Plan(query,dedup,groups,practical,scope,' '.join(title_fr),' '.join(title_en),action)


def title_forms(query,english=False):
    """Try the original first, then at most four whole-token singular variants."""
    original=query.title_en if english else query.title_fr
    if not original:return []
    changes=[]
    literal = original == ' '.join(query.words)
    for word,group in zip(query.words,query.groups):
        if not word.endswith(('s','x')) or not re.search(r'\b'+re.escape(word)+r'\b',original):continue
        forms = number_forms(word)
        if group != forms and not literal:
            continue
        alternatives=[form for form in forms[1:] if form in group and not form.endswith(('s','x'))]
        if alternatives:changes.append((word,alternatives))
    values=[original]
    if changes:
        for combination in islice(product(*(forms for _,forms in changes)),4):
            value=original
            for (word,_),form in zip(changes,combination):value=re.sub(r'\b'+re.escape(word)+r'\b',form,value)
            if value not in values:values.append(value)
    return values


EQUIPMENT = r'kits?|trousses?|materiel|equipements?|outils?|outillage|fournitures?|equipment|tools?|supplies|materials?'
EQUIPMENT_REQUEST = re.compile(rf'\b(?:{EQUIPMENT}|pieces?|parts?)\b')
EQUIPMENT_HEADING = re.compile(rf'^(?:{EQUIPMENT})\b|\b(?:kits?|tools and supplies)\s*$')


def rank(item,query,position=0,*,normalizer=None):
    normalize=normalizer or normal
    title=normalize(item.get('title',''));text=normalize(item.get('excerpt','')+' '+item.get('_text',''))
    if not query.groups:return 0
    title_tokens=set(title.split());text_tokens=set(text.split())
    title_hits=sum(any(term<=title_tokens for term in group) for group in query.token_groups)/len(query.groups)
    text_hits=sum(any(term<=text_tokens for term in group) for group in query.token_groups)/len(query.groups)
    score=65*title_hits+25*text_hits+8/(1+item.get('_rank',position))
    if title_hits<1 and text_hits<1:score-=35
    if 'protection civile' in query.words and re.search(r'\b(engagement majeur|menace d origine etatique|conflit arme)\b',text):
        score+=55
    if 'abri' in query.words and {'bombardement','bombardements'} & set(query.words) and source_role(item)=='practical':
        if 'en cas d alerte' in text and text_tokens & {'consigne','consignes'}:score+=55
    if query.action:
        evidence=INTENTS[query.action]
        if re.search(evidence,title):
            # An explicit task title should beat a broad subject title whose
            # excerpt merely mentions the action. This is still a reading lead,
            # never evidence that the article contains a verified procedure.
            contextual=bool(re.search(r'\b(pourquoi|why|histoire|history|historical|origines?|origins?|risques?|dangers?|hazards?|safety|combien)\b|\b((should|do|can) (i|we|you)|does|how (many|much)|faut il|dois je|puis je)\b',title))
            instruction=bool(re.search(r'\b(comment|guide|tutorial|tutoriels?|manuels?|manuals?|instructions|etapes|steps|methode|method)\b|\bhow (to|(can|do|should) (i|we|you|one))\b',title))
            # A price guide can mention the action without teaching it. Keep it
            # searchable, while explicit how-to titles may still discuss costs.
            prices=bool(re.search(r'\b(prix|tarifs?|couts?|prices?|pricing|costs?)\b',title))
            steps=bool(re.search(r'\b(comment|tutorial|tutoriels?|instructions|etapes|steps|methode|method)\b|\bhow (to|(can|do|should) (i|we|you|one))\b',title))
            heading=normalize(item.get('title','').rsplit('/',1)[-1])
            equipment=(query.practical and EQUIPMENT_HEADING.search(heading)
                       and not EQUIPMENT_REQUEST.search(normalize(query.original)))
            # The heading carries the article's subject. A breadcrumb may
            # contain the action even when the leaf is a list of supplies.
            if (prices or equipment) and not steps:contextual=True;instruction=False
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
    if query.practical and query.action=='preserve' and not query.collection:
        # A practical preservation query first needs documents on the subject.
        # A targeted dictionary or Wikisource search retains its normal ranking.
        book=item.get('book') or str(item.get('id','')).split('/',1)[0].removeprefix('zim:')
        reference=book.startswith('wiktionary_') or (book.startswith('wikisource_') and re.search(r'(?:^|/)Page:',path,re.I))
        if reference and not re.search(r'\b(definition|dictionnaire|thesaurus|wiktionnaire|wiktionary|wikisource)\b',normalize(query.original)):
            score-=60
    if query.practical:
        classification=item.get('classification',{})
        if classification.get('method')=='human' and classification.get('document_type') in ('procedure','manual'):score+=10
        if (title_hits == 1 and query.action and re.search(INTENTS[query.action], title)
                and item.get('id', '').startswith('guide:') and source_role(item) == 'practical'):
            score += 24
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


PASSAGE_WINDOW = 40


# Words that describe a concern rather than a subject cannot anchor a guide title.
GENERIC_ANCHORS = frozenset({'securite', 'regle', 'regles', 'eviter', 'prevention', 'risque', 'risques',
                             'domicile', 'maison', 'guide', 'conseils', 'safety', 'rules', 'home'})


def subject_in_passage(item, query, normalize=normal):
    """A PDF page matches when the query concepts appear in its title or excerpt, or
    close together in the page text (a long manual names everything somewhere).
    When the guide title already names a subject word of the query, two thirds of
    the concepts suffice: a natural question carries generic words besides the subject."""
    groups = query.token_groups
    if not groups:
        return False
    title = set(normalize(item.get('title', '')).split())
    in_title = {number for number, group in enumerate(groups) if any(term <= title for term in group)}
    anchored = any(not any(term <= GENERIC_ANCHORS for term in groups[number]) for number in in_title)
    required = max(1, (2 * len(groups) + 2) // 3) if anchored else len(groups)
    topic = title | set(normalize(item.get('excerpt', '')).split())
    if sum(any(term <= topic for term in group) for group in groups) >= required:
        return True
    need = required - len(in_title)
    last = {}
    for index, word in enumerate(normalize(item.get('_text', '')).split()):
        for number, group in enumerate(groups):
            if number not in in_title and any(term == {word} for term in group):
                last[number] = index
        if sum(index - position < PASSAGE_WINDOW for position in last.values()) >= need:
            return True
    return False


def encyclopedic_matches(items, query, limit, *, normalizer=None):
    normalize = normalizer or NormalCache()
    candidates = []
    for item in items:
        label = item.get('title', '').strip()
        if label.casefold().endswith((' (homonymie)', ' (disambiguation)')):
            continue
        title = set(normalize(label).split())
        if query.token_groups and all(any(term <= title for term in group) for group in query.token_groups):
            candidates.append({**item, 'reference_fallback': True})
    if len(query.words) == 1:
        # Accent folding lets an unaccented query find an accented title. When
        # the typed spelling has an exact subject heading, discard homographs
        # with a different spelling (for example Ruche and Ruché).
        spelling = unicodedata.normalize('NFC', query.original.casefold())
        labels = {word for word in re.findall(r'[^\W_]+', spelling) if normalize(word) == query.words[0]}
        headings = [(item, unicodedata.normalize('NFC', item.get('title', '').strip().casefold()))
                    for item in candidates]
        if any(heading in labels for _, heading in headings):
            candidates = [item for item, heading in headings
                          if heading in labels or normalize(heading) != query.words[0]]
    # An encyclopedia can introduce the subject even if its excerpt does not
    # describe the requested action.
    return ordered(candidates, replace(query, action=''), limit, normalizer=normalize)


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
        pdf_passage = item.get('kind') == 'guide' and re.search(r'\.pdf#page=\d+$', item['id'], re.I)
        if pdf_passage and not subject_in_passage(item, query, normalize):
            continue
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
        parent=item['id'].split('#page=')[0].split('#t=')[0]
        if '/appropedia' in item['id'] or item['id'].startswith('zim:appropedia'):
            parent=re.sub(r'/(?:[a-z]{2,3}(?:-[a-z]+)?)$','',parent)
        if item['id'].startswith('zim:') and parent in parents:
            continue
        if ('#page=' in item['id'] or item['id'].startswith('video:')) and parent in parents:
            others=parents[parent].setdefault('other_matches',[])
            if len(others)<5:
                fields=('id','title','url')+(('kind','position_ms','language') if item['id'].startswith('video:') else ())
                others.append({k:item.get(k,'') for k in fields})
            continue
        parents[parent]=clean;result.append(clean)
    return result[:limit]


INTENTS={
 'repair':r'\b(reparer|reparation|repair|repairing|maintenance|entretien|entretenir|recoudre|ravauder|mending|sewing|couture|stitching|rustine|remplacer|remplacement|changement|replace|replacement)\b',
 'preserve':r'\b(conserver|conservation|stocker|stockage|storage|store|storing|preserve|preserving|preservation|saving|save)\b',
 'purify':r'\b(potable|potabilisation|potabiliser|purifier|purification|filtrer|filtration|disinfection|desinfection|purifying|treatment|traitement)\b',
 'build':r'\b(fabriquer|fabrication|construire|construction|build|building|assembly|assemble|diy)\b',
 'install':r'\b(installer|installation|install|installing)\b',
 'recognize':r'\b(reconnaitre|reconnaissance|identifier|identification|recognize|recognise|identify|distinguish)\b',
 'sharpen':r'\b(affutage|affuter|aiguiser|sharpen|sharpening)\b',
 'ignite':r'\b(allumer|allumage|amadou|tinder|campfire|feu de camp|ignition|ignite|friction|percussion|production de feu|faire du feu|fire making|fire starting|start a fire|lighting a fire|making a fire)\b',
}

ENGLISH_PROSE = frozenset('the and of with for this that from which when into each'.split())
FRENCH_PROSE = frozenset('les une des avec pour dans cette qui sur est sont aux'.split())
LOWTECH_ARCHIVE = 'solar.lowtechmagazine.com'
LOWTECH_ARTICLE_PATH = re.compile(
    r'(?:solar\.lowtechmagazine\.com/)?(?:(en|fr|de|nl|es|it|pt|pl|ar|vi|ko)/)?'
    r'\d{4}/(?:0[1-9]|1[0-2])/[^/]+/?$'
)


ARCHIVE_ROLES = {
    'appropedia': 'practical', 'ifixit': 'practical', 'wikihow': 'practical',
    LOWTECH_ARCHIVE: 'practical', 'wikipedia': 'reference',
    'vikidia': 'reference', 'encyclopedie-environnement.org': 'reference',
    'encyclopedie-environnement': 'reference', 'environment-encyclopedia': 'reference',
    'wiktionary': 'language', 'gutenberg': 'culture', 'wikisource': 'culture',
    'wikivoyage': 'culture', 'alexandria.dk': 'culture',
}
PRACTICAL_PUBLISHERS = frozenset({
    'who wedc', 'hesperian health guides', 'msf', 'ifrc', 'unhcr', 'inrs',
    'ministere de l interieur securite civile sgdsn', 'croix rouge francaise ifrc',
    'oms war trauma foundation world vision', 'usda nchfp university of georgia',
    'victron energy', 'fao', 'anfr', 'baofeng radioddity',
    'ademe', 'anses', 'direction generale de l armement', 'dirm mediterranee', 'djepva', 'ffessm',
    'gouvernement de la polynesie francaise dag', 'itavi ministere de l agriculture', 'ministere de la mer',
    'ministere de la sante dgs', 'prefecture de la gironde',
})


def source_role(item):
    """Recognise established source families and publishers by stable metadata."""
    identifier = item.get('id', '')
    if identifier.startswith('guide:'):
        publisher = normal(item.get('provenance', '').partition(' — ')[0])
        return 'practical' if publisher in PRACTICAL_PUBLISHERS else ''
    book = item.get('book') or identifier.removeprefix('zim:').split('/', 1)[0]
    family = book.lower().split('_', 1)[0]
    if family.endswith('.stackexchange.com'):
        return 'reference'
    return ARCHIVE_ROLES.get(family, '')


def fallback_encyclopedia(book):
    return book.lower().partition('_')[0] in ('wikipedia', 'vikidia')


PRACTICAL_FORUMS = frozenset({
    'bicycles.stackexchange.com', 'crafts.stackexchange.com', 'diy.stackexchange.com',
    'gardening.stackexchange.com', 'mechanics.stackexchange.com', 'woodworking.stackexchange.com',
})


def practical_forum(book):
    return book.lower().partition('_')[0] in PRACTICAL_FORUMS


CULTURE_SOURCE_ROLES = frozenset({'reference', 'language', 'culture'})


def application_domains(item, indexed=None):
    role = source_role(item)
    if role in CULTURE_SOURCE_ROLES:
        return ['culture']
    found = domains(item) if indexed is None else indexed
    # Pages of a practical guide (MSF, OMS, SGDSN…) belong to Autonomie, whatever
    # words a single page happens to contain (« histoire », « échec du traitement »…).
    if role == 'practical':
        return ['resilience']
    return found


def ifixit_edition(book):
    match = re.match(r'ifixit_(en|fr)_all(?:_|$)', book)
    return match[1] if match else ''


def article_language(item):
    """Prefer available evidence about the page over a general metadata hint."""
    identifier = item.get('id', '')
    book = (item.get('book') or identifier.removeprefix('zim:').split('/', 1)[0]).lower()
    language = item.get('language', '')
    if book.partition('_')[0] == LOWTECH_ARCHIVE:
        # Translated articles share the English HTML shell and article slugs.
        article = LOWTECH_ARTICLE_PATH.fullmatch(identifier.partition('/')[2])
        if article:
            return article[1] or 'en'
    if 'appropedia' in book:
        suffix = re.search(r'/([a-z]{2})(?:-[a-z]+)?$', identifier)
        if suffix:
            return suffix[1]
    edition = ifixit_edition(book)
    if edition:
        # Both iFixit editions can declare html lang=fr. Keep the edition
        # language unless the content gives a strong signal of the other language.
        content = item.get('_text') or item.get('text') or item.get('excerpt') or ''
        tokens = set(normal(content[:4_000]).split())
        english = len(tokens & ENGLISH_PROSE)
        french = len(tokens & FRENCH_PROSE)
        if english >= max(3, 2 * french):
            return 'en'
        if french >= max(3, 2 * english):
            return 'fr'
        return edition
    return {'fra':'fr','eng':'en'}.get(language,language)

def legacy_domains(item):
    # Conservative automatic indication; never certifies a procedure.
    text=normal(item.get('title','')+' '+item.get('excerpt','')+' '+item.get('_text','')[:4000])
    resilience=bool(re.search(r'\b(eau|water|feu|fire|abri|shelter|potager|semences|seed|seeds|survie|survival|repair|reparation|reparer|maintenance|batterie|battery|generator|generateur|premiers secours|first aid|compost|plomberie|plumbing|couture|sewing|mending|conservation alimentaire|(?:(?:conservation|stockage) de(?:s| la) |(?:conserver|stocker) (?:les? |des? |la )?)(?:aliments?|nourriture)|food (?:preservation|storage)|conserves|canning|solaire|solar|photovoltaic|photovoltaique|radio|radios|antenne|antennes|communications|telecommunications|affutage|sharpening)\b',text))
    cultural=bool(re.search(r'\b(histoire|history|science|sciences|physique|physics|biologie|biology|mathematiques|mathematics|enseignement|education|geographie|geography|litterature|literature|philosophie|philosophy)\b',text))
    return (['resilience'] if resilience else [])+(['culture'] if cultural or not resilience else [])


# Broad terms like water, fire or radio need context on Wikipedia. Use
# concrete practices, equipment and techniques as subject evidence.
PRACTICAL_SUBJECT = re.compile(
    r'\b(potabilisation|eau potable|drinking water|water purification|water treatment|'
    r'collecte (?:d eau de pluie|des eaux? pluviales?)|recuperation de l eau de pluie|'
    r'rainwater harvesting|chateaux? d eau|water towers?|reservoirs? d eau|water tanks?|'
    r'conservation (?:des? aliments?|de la viande|du poisson)|food preservation|conservation alimentaire|'
    r'entreposage des aliments|lavage des mains|hand washing|handwashing|'
    r'compostage|compost|potager|vegetable garden|permaculture|semis|sowing|stockage des semences|'
    r'plomberie|plumbing|premiers secours|first aid|sutures? (?:en )?medecine|radioamateur|amateur radio|'
    r'antennes? (?:radioelectriques?|de reception)|radio antennas?|dynamo|generateurs? electriques?|electrical generators?|'
    r'batteries? (?:electriques?|rechargeables?|au lithium)|rechargeable batter(?:y|ies)|'
    r'photovoltaique|panneaux? solaires?|solar panels?|solar power|energie solaire|eoliennes?|wind turbines?|'
    r'traitement de l eau|filtration|couture|sewing|reparation|repair|desinfection|disinfection|'
    r'isolation thermique|thermal insulation|habitat passif|maison passive|passive house|charpentes?|roof framing|'
    r'reanimation cardiopulmonaire|cardiopulmonary resuscitation|premiers soins|first aid|'
    r'nouage|noeuds? (?:de chaise|de cabestan|d ecoute|plats?)|bowline|clove hitches?|reef knots?|'
    r'generateur a pedales|pedal generator|affutage|sharpening|construire un abri|shelter building|'
    r'rustine|mending|semences|seed saving|abri de survie|survival shelter|soudage|welding|extincteurs?|'
    r'fire extinguishers?|peche a la ligne|angling|navigation astronomique|celestial navigation|'
    r'couteaux? de poche|pocket (?:knife|knives)|pistolets? a colle|glue guns?|'
    r'domestication du feu|fire making|fire starting|allumage du feu)\b'
)
CULTURAL_SUBJECT = re.compile(
    r'\b(histoire|history|sciences?|physique|physics|biologie|biology|culture|'
    r'symbolique|symbolism|patrimoine|heritage|aspects historiques|'
    r'mathematiques|mathematics|astronom(?:ie|ique|y|ical)|epidemiolog(?:ie|y)|litterature|literature)\b'
)
RADIO_EQUIPMENT = re.compile(r'\b(antenne|antenna|transmission|montage|circuit|receiver|recepteur|equipement|equipment)\b')
CULTURAL_FORMAT = re.compile(
    r'\b(synopsis|intrigue|distribution artistique|contenu musical|homophonies|'
    r'plot summary|cast and characters|disambiguation)\b'
)
CULTURAL_TITLE = re.compile(
    r'\b(systeme solaire|solar system|rayonnement solaire|solar radiation|'
    r'instrument de musique|musical instrument|batterie instrument|'
    r'homonymie|disambiguation|cycle de l eau|water cycle|eau de cologne)\b'
)


GENERAL_PHENOMENON = {
    'eau', 'water', 'pluie', 'rain', 'maree', 'tide', 'vent', 'wind',
}
TECHNICAL_HEADINGS = re.compile(
    r'\b(techniques? (?:de |d )?(?:construction|reparation|transmission|fabrication)|'
    r'mise en oeuvre|mode d emploi|instructions|premiers soins|first aid|'
    r'installation du systeme|assembly instructions|how to)\b'
)


def wiki_normal(label):
    # Unicode NFKD does not expand the French œ ligature.
    return normal(label.casefold().replace('œ', 'oe'))


def domains(item):
    structure = item.get('_wiki_structure')
    if not wiki_structure.wikipedia(item) or not structure:
        return legacy_domains(item)

    title = wiki_normal(item.get('title', ''))
    sections = [wiki_normal(label) for label in structure['sections']]
    categories = [wiki_normal(label) for label in structure['categories']]
    disambiguation = any(label.endswith(' au singulier') for label in sections) and any(
        label.endswith(' au pluriel') for label in sections
    )
    if disambiguation or CULTURAL_TITLE.search(title) or any(CULTURAL_FORMAT.fullmatch(label) for label in sections):
        return ['culture']

    practical_title = bool(PRACTICAL_SUBJECT.search(title))
    practical_category = any(PRACTICAL_SUBJECT.search(label) for label in categories)
    # Minor headings can describe useful detail, but don't define the subject.
    practical_sections = sum(bool(PRACTICAL_SUBJECT.search(label)) for label in sections)
    methods = any(TECHNICAL_HEADINGS.search(label) or label in (
        'domestication du feu', 'fire making', 'fire starting') for label in sections)
    device_title = re.search(r'\b(bicyclette|bicycle|velo|radio|batterie|battery|antenne|antenna|generateur|generator)\b', title)
    maintenance = device_title and any(
        wiki_normal(label) in ('entretien', 'maintenance') for label in structure['sections'] + structure['subsections']
    )
    practical = practical_title or practical_category or practical_sections >= 2 or methods or maintenance

    general = bool(CULTURAL_SUBJECT.search(title)) or any(CULTURAL_SUBJECT.search(label) for label in categories)
    historical = any(re.match(r'^(?:historique|histoire|history|aspects historiques)(?:$| d[eu]s? | of )', label)
                     for label in sections)
    general_section = any(CULTURAL_SUBJECT.search(label) for label in sections)
    cultural = general or historical or (general_section and not practical_title)
    previous = legacy_domains(item)
    if practical:
        return ['resilience', 'culture'] if cultural or 'culture' in previous else ['resilience']

    # Only clear evidence about the subject may remove practical membership.
    # Weak or unfamiliar evidence should not hide sources the old rule found.
    radio_history = historical and title.startswith('radio ') and not any(RADIO_EQUIPMENT.search(label) for label in sections)
    if (title in GENERAL_PHENOMENON and sections) or radio_history:
        return ['culture']
    if cultural and 'culture' not in previous:
        return [*previous, 'culture']
    return previous
