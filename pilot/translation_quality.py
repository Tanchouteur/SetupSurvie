"""Conservative text checks, never a certificate of semantic fidelity.

No model/network: compare protected tokens and flag weaker completeness signals.
"""
from collections import Counter
from decimal import Decimal, InvalidOperation
import hashlib
import re
import unicodedata
from .math_text import BLOCKS,UNREADABLE

VERSION=11
# PDF extraction often joins a label and its number ("Chapter4", "X7").
# Count that number on both sides, including when French restores the space.
# A dash after a number and a space is a range ("10 – 20"), not a sign.
NUMBER=r'(?<!\d)(?:(?<!\d[ \u00a0\u202f])[-+−]\s*)?\d+(?:[ \u00a0\u202f]\d{3})*(?:[.,]\d+)?'
NUMBERS=re.compile(NUMBER)
ENGLISH_DOLLAR_AMOUNT=re.compile(r'(\$\s*)([+-]?\d{1,3}(?:,\d{3})+(?:\.\d+)?)(?!\d|[.,]\d)')
ENGLISH_GROUPED_NUMBER=re.compile(r'(?<![\d.,])\d{1,3}(?:,\d{3})+(?:\.\d+)?(?!\d|[.,]\d)')
EN_ORDINAL=re.compile(r'(?<!\w)([0-9]+)(?:st|nd|rd|th)(?!\w)',re.I)
FR_ORDINAL=re.compile(r'(?<!\w)([0-9]+)(?:er|re|ère|e|ème|eme|ᵉ|ᵉʳ|ʳᵉ)s?(?!\w)',re.I)
FR_ROMAN_CENTURY=re.compile(r'(?<!\w)((?=[IVX])X{0,3}(?:IX|IV|V?I{1,3}|V)?)(?:e|ème|eme|ᵉ)\s+siècle\b',re.I)
ORDINAL_WORDS={
    '1':('first',r"premi(?:er|ère)s?|d[’']abord"),
    '2':('second',r'second(?:e)?s?|deuxièmes?'),
    '3':('third',r'troisièmes?'),
    '4':('fourth',r'quatrièmes?'),
    '5':('fifth',r'cinquièmes?'),
    '6':('sixth',r'sixièmes?'),
    '7':('seventh',r'septièmes?'),
    '8':('eighth',r'huitièmes?'),
    '9':('ninth',r'neuvièmes?'),
    '10':('tenth',r'dixièmes?'),
}

UNIT_ALIASES={
    'mètres':'m','mètre':'m','centimeters':'cm','centimetres':'cm','centimètres':'cm','centimeter':'cm','centimetre':'cm','centimètre':'cm',
    'millimeters':'mm','millimetres':'mm','millimètres':'mm','millimeter':'mm','millimetre':'mm','millimètre':'mm',
    'liters':'l','liter':'l','litres':'l','litre':'l','ml':'ml','cl':'cl','dl':'dl','l':'l',
    'milligrams':'mg','milligrammes':'mg','milligram':'mg','milligramme':'mg','mg':'mg',
    'grams':'g','grammes':'g','gram':'g','gramme':'g','g':'g',
    'kilograms':'kg','kilogrammes':'kg','kilogram':'kg','kilogramme':'kg','kg':'kg',
    'meters':'m','metres':'m','meter':'m','metre':'m','m':'m','mm':'mm','cm':'cm','km':'km',
    'seconds':'s','secondes':'s','second':'s','seconde':'s','s':'s',
    'minutes':'min','minute':'min','min':'min','hours':'h','heures':'h','hour':'h','heure':'h','h':'h',
    '°c':'°c','°f':'°f','%':'%','volts':'v','volt':'v','v':'v','watts':'w','watt':'w','w':'w',
    'ma':'ma','a':'a','kw':'kw','kwh':'kwh','wh':'wh','hz':'hz','bar':'bar','pa':'pa','kpa':'kpa','mpa':'mpa',
    'psi':'psi','rpm':'rpm','mm²':'mm²','cm²':'cm²','m²':'m²','cm³':'cm³','m³':'m³',
    'kcal':'kcal','kilocalories':'kcal','kilocalorie':'kcal','calories':'cal','calorie':'cal','cal':'cal',
    'kj':'kj','kilojoules':'kj','kilojoule':'kj','joules':'j','joule':'j',
    'mv':'mv','millivolts':'mv','millivolt':'mv','µv':'µv','μv':'µv','microvolts':'µv','microvolt':'µv','kv':'kv',
    'µg':'µg','μg':'µg','mcg':'µg','micrograms':'µg','microgram':'µg','microgrammes':'µg','microgramme':'µg',
    'µm':'µm','μm':'µm','micrometers':'µm','micromètres':'µm','nm':'nm','ms':'ms','milliseconds':'ms','millisecondes':'ms',
    'iu':'ui','ui':'ui','mmhg':'mmhg','mah':'mah','ah':'ah','kva':'kva','mw':'mw',
    'ft':'ft','feet':'ft','foot':'ft','pieds':'ft','pied':'ft','inches':'in','inch':'in','pouces':'in','pouce':'in',
    'miles':'mi','mile':'mi','mph':'mph','gallons':'gal','gallon':'gal','gal':'gal','oz':'oz','ounces':'oz','ounce':'oz','onces':'oz','lb':'lb','lbs':'lb'}
# Rates keep both sides: "5 mg/h" and "5 mg/min" differ by a factor 60.
DENOMINATOR_ALIASES={'day':'jour','days':'jour','jour':'jour','jours':'jour','j':'jour','d':'jour',
    'week':'semaine','weeks':'semaine','semaine':'semaine','semaines':'semaine','month':'mois','mois':'mois',
    'year':'an','years':'an','an':'an','ans':'an','année':'an','dose':'dose','doses':'dose'}
UNIT_LOOKUP={key.casefold():value for key,value in UNIT_ALIASES.items()}
_UNIT_NAMES='|'.join(re.escape(k).replace('°','°'+r'\s*') for k in sorted(UNIT_ALIASES,key=len,reverse=True))
UNIT=re.compile('('+NUMBER+r')\s*((?:'+_UNIT_NAMES+r')(?:\s*/\s*(?:\d+\s*)?[^\W\d_]+[²³]?)?)(?![^\W_]|[²³])',re.I)


def unit_key(text):
    """Canonical unit, including compound rates; never fails on a new spelling."""
    parts=re.sub(r'\s','',text).casefold().split('/',1)
    key=UNIT_LOOKUP.get(parts[0],parts[0])
    if len(parts)>1:
        denominator=parts[1]
        key+='/'+UNIT_LOOKUP.get(denominator,DENOMINATOR_ALIASES.get(denominator,denominator))
    return key


# Match complete structured bibliography lines only when author initials and a
# year provide strong evidence; ordinary prose containing a date is excluded.
REFERENCE=re.compile(
    r"(?im)(?P<bibliography>^[ \t]*(?:[A-ZÀ-ÖØ-Þ][a-zà-öø-ÿ'’-]+,?[ \t]+(?:[A-Z]\.[ \t]*)+)(?:[&,;][ \t]*[A-ZÀ-ÖØ-Þ][a-zà-öø-ÿ'’-]+,?[ \t]+(?:[A-Z]\.[ \t]*)+)*[ \t]*\((?:18|19|20)\d{2}\)\.[ \t]+[^\n]{3,})"
    r"|(?i:https?)://[^\s<>\[\]{}]+"
    r"|(?<![\w/])(?i:(?:doi:\s*)?10\.\d{4,9}/[-._;()/:A-Z0-9]+)")
REFERENCE_NUMBER=re.compile(r"\b(?:fig(?:ure)?|figura|table|tableau|chapter|chapitre|section|page|p)\.?\s*(\d{1,4})(?!\w|[.,]\d)",re.I)


class ProtectedReferences:
    """Protect confidently identified references without touching formula blocks."""
    def __init__(self,text):
        digest=hashlib.sha256(text.encode()).hexdigest()[:12].translate(str.maketrans('0123456789','ghijklmnop'))
        self.prefix='SS_REFERENCE_'+digest+'_'
        while self.prefix in text:self.prefix+='X'
        self.references=[]
        self.bibliography=set()
        formulas=[m.span() for m in BLOCKS.finditer(text)]
        pieces=[];prose=[];start=0
        for match in REFERENCE.finditer(text):
            if any(match.start()<end and match.end()>begin for begin,end in formulas):continue
            end=match.end()
            # Sentence punctuation is not part of a URL or DOI.
            if match['bibliography'] is None:
                while end>match.start():
                    last=text[end-1];value=text[match.start():end]
                    if last not in '.,;:!?' and not (last==')' and value.count(')')>value.count('(')):break
                    end-=1
            if end==match.start():continue
            index=len(self.references);letters=''
            while True:
                letters=chr(65+index%26)+letters;index=index//26-1
                if index<0:break
            token='['+self.prefix+letters+']'
            self.references.append((token,text[match.start():end]))
            if match['bibliography'] is not None:self.bibliography.add(token)
            gap=text[start:match.start()]
            prose.extend((gap,' '));pieces.extend((gap,token));start=end
        pieces.append(text[start:]);self.text=''.join(pieces)
        prose.append(text[start:]);self.prose=''.join(prose)
        self.only_references=bool(self.references) and not re.sub(r'[\s.,;:!?()\[\]{}–—-]','',self.prose)
        self.pattern=re.compile(r'\['+re.escape(self.prefix)+r'[^\]\n]*\]')

    def restore(self,result):
        if self.pattern.findall(result)!=[token for token,_ in self.references]:
            raise ValueError('Les repères des références ont été modifiés ou déplacés.')
        values=dict(self.references)
        def restore_match(match):
            value=values[match[0]]
            if match[0] not in self.bibliography:return value
            before=result[result.rfind('\n',0,match.start())+1:match.start()]
            after=result[match.end():].split('\n',1)[0]
            return ('\n' if before.strip() else '')+value+('\n' if after.strip() else '')
        restored=self.pattern.sub(restore_match,result)
        if self.prefix in restored:raise ValueError('Repère de référence incorrect.')
        return restored


REFUSAL = re.compile(
    r"^(?:(?:(?:je suis )?d[ée]sol[ée],? (?:mais )?)?"
    r"je ne peux pas (?:traduire|vous aider|t[’']aider|r[ée]pondre)"
    r"|(?:i[’']?m sorry,? (?:but )?)?i (?:cannot|can[’']t) (?:help|translate|assist|provide))",
    re.I,
)


def normalized(text):
    # Preserve superscripts in units; NFKC would silently change m² into m2.
    return unicodedata.normalize('NFC',text).replace('−','-').replace('–','-').replace('—','-')


def number(token):
    token=re.sub(r'\s','',token).replace(',','.')
    try:
        value=Decimal(token)
        if not value:return '0'
        fixed=format(value,'f')
        return fixed.rstrip('0').rstrip('.') if '.' in fixed else fixed
    except InvalidOperation:return token


def spell_numbered_ordinals(text):
    """Expand familiar English abbreviations while preserving the original check."""
    def expand(match):
        words=ORDINAL_WORDS.get(number(match[1]))
        return words[0] if words else match[0]
    return EN_ORDINAL.sub(expand,text)


def separate_ordinals(source,translated):
    """Compare written ordinals separately so they cannot replace a cardinal."""
    expected=Counter(number(match[1]) for match in EN_ORDINAL.finditer(source))
    if not expected:return source,translated,True
    received=Counter(number(match[1]) for match in FR_ORDINAL.finditer(translated))
    def roman_value(match):
        digits={'I':1,'V':5,'X':10}
        value=match[1].upper()
        return str(sum(-digits[c] if i+1<len(value) and digits[c]<digits[value[i+1]] else digits[c] for i,c in enumerate(value)))
    received.update(roman_value(match) for match in FR_ROMAN_CENTURY.finditer(translated))
    # Count only additional French words. Ordinary written-out ordinals from
    # the source must not also satisfy a missing numbered ordinal.
    for value,missing in (expected-received).items():
        if value not in ORDINAL_WORDS:continue
        english,french=ORDINAL_WORDS[value]
        old=len(re.findall(r'\b'+english+r'(?:ly)?\b',source,re.I))
        new=len(re.findall(r'\b(?:'+french+r')\b',translated,re.I))
        received[value]+=min(missing,max(0,new-old))
    return EN_ORDINAL.sub(' ',source),FR_ORDINAL.sub(' ',FR_ROMAN_CENTURY.sub(' siècle',translated)),expected==received


def normalize_english_grouping(text):
    # Formula text is restored verbatim by the translator.
    def convert(prose):return ENGLISH_GROUPED_NUMBER.sub(lambda match:match[0].replace(',',''),prose)
    start=0;pieces=[]
    for formula in BLOCKS.finditer(text):
        pieces.extend((convert(text[start:formula.start()]),formula[0]))
        start=formula.end()
    pieces.append(convert(text[start:]))
    return ''.join(pieces)


def assess(source,translated,*,source_language=None,english_grouping=False):
    issues=[]
    def add(code,severity,message):issues.append({'code':code,'severity':severity,'message':message})
    original_refs=ProtectedReferences(source)
    new_refs=ProtectedReferences(translated)
    if [value for _,value in original_refs.references]!=[value for _,value in new_refs.references]:
        add('references','error','Une référence reconnue a disparu, été modifiée ou déplacée.')
    source=normalized(original_refs.prose);translated=normalized(new_refs.prose)
    # PDF manuals sometimes draw key names as images; extraction leaves a hole
    # in "Press the         key". Numeric equality cannot validate that command.
    if re.search(r'\b(?:press|enter|push|appuyez|appuyer|saisissez|entrez)[^\n.!?]{0,60}[ \t]{4,}(?:keys?|buttons?|to|on|and|pour|sur|et)\b',source,re.I) or '\ufffd' in source:
        add('source_gaps','warning','Le texte original extrait contient des blancs ou caractères manquants, possiblement des touches dessinées. Comparez la page originale ; les commandes manquantes ne sont pas reconstituées.')
    if UNREADABLE in source or re.search(r'\b(?:where|o[uù])[ \t]{4,}(?:is|est)\b',source,re.I):
        add('source_math_gaps','warning','Une formule est illisible ou semble manquer dans le texte extrait. Comparez l’original illustré ; aucun calcul ou symbole manquant n’est reconstitué.')
    def formulas(text):return Counter(re.sub(r'\s+',' ',m['value']).strip() for m in BLOCKS.finditer(text))
    if formulas(source)!=formulas(translated):
        add('formulas','error','Une formule extraite a disparu, été ajoutée ou modifiée. Elle doit être conservée avec ses groupes, indices et puissances ; comparez l’original avant reprise.')
    english=(source_language or '').lower().split('-')[0] in ('en','eng')
    def numbers(text):
        if english and not english_grouping:
            # A leading dollar sign and English grouping make $70,000 a
            # dollar amount of 70000. Other comma decimals keep their meaning.
            text=ENGLISH_DOLLAR_AMOUNT.sub(lambda m:m[1]+m[2].replace(',',''),text)
        return Counter(number(m.group()) for m in NUMBERS.finditer(text))
    measure_source=normalize_english_grouping(source) if english and english_grouping else source
    if english:
        # Established historical names may translate their numeral as an ordinal word.
        historical=((r'\bWorld War (?:II|2)\b',r'\b(?:Seconde|Deuxième) Guerre mondiale\b'),
                    (r'\bWorld War (?:I|1)\b',r'\bPremière Guerre mondiale\b'))
        for original,french in historical:
            if len(re.findall(original,measure_source,re.I))==len(re.findall(french,translated,re.I)):
                measure_source=re.sub(original,'événement historique',measure_source,flags=re.I)
    source_numbers,translated_numbers,ordinals_match=separate_ordinals(measure_source,translated)
    if not ordinals_match:add('ordinals','warning','Un rang indiqué par un nombre dans l’original a disparu, été ajouté ou changé.')
    if not ordinals_match:
        # An ordinal can become a bare reference number in French. Only
        # consume equal values when no cardinal or measurement is at stake.
        ordinal_values=Counter(number(m[1]) for m in EN_ORDINAL.finditer(measure_source))
        cardinal_values=numbers(source_numbers)
        def ambiguous_bare(match):
            value=number(match[0])
            if ordinal_values[value] and not cardinal_values[value] and not UNIT.match(translated_numbers,match.start()):
                ordinal_values[value]-=1
                return ' '
            return match[0]
        translated_numbers=NUMBERS.sub(ambiguous_bare,translated_numbers)
    # A figure/section number can be renumbered or rendered as a word. Keep
    # it visible as a warning while cardinal values and measurements stay strict.
    source_refs=Counter(number(m[1]) for m in REFERENCE_NUMBER.finditer(source_numbers))
    target_refs=Counter(number(m[1]) for m in REFERENCE_NUMBER.finditer(translated_numbers))
    source_cardinals=numbers(REFERENCE_NUMBER.sub(' référence ',source_numbers))
    target_cardinals=numbers(REFERENCE_NUMBER.sub(' référence ',translated_numbers))
    # A translated label may move away from its number ("page 12" to
    # "page suivante, 12"). Pair only surplus cardinals with unmatched references.
    moved_to_target=(source_refs-target_refs)&(target_cardinals-source_cardinals)
    moved_to_source=(target_refs-source_refs)&(source_cardinals-target_cardinals)
    if moved_to_target and moved_to_source:
        # Moves in both directions are a swap ("5 tablets, page 12" to
        # "12 tablets, page 5"): a quantity changed, so keep both strict.
        moved_to_target=moved_to_source=Counter()
    if source_refs-moved_to_target!=target_refs-moved_to_source:
        add('numbers','warning','Un numéro de référence a changé ou disparu. Comparez l’original.')
    if source_cardinals-moved_to_source!=target_cardinals-moved_to_target:
        add('numbers','error','Des nombres ont disparu, été ajoutés ou changé. Comparez le passage à l’original et reprenez avec un autre mode.')
    def measures(text):
        pairs=Counter()
        for match in UNIT.finditer(text):
            unit=re.sub(r'\s','',match.group(2))
            # Lowercase a is usually an article or a verb after a reference.
            # Single-letter elisions such as l’ or s’il are also prose.
            if unit=='a' or (len(unit)==1 and text[match.end():match.end()+1] in ("'",'’')):
                continue
            if unit=='A':
                # An extracted page number can be followed by a new English
                # sentence starting with the article "A".
                line_start=text.rfind('\n',0,match.start(1))+1
                gap=text[match.end(1):match.start(2)]
                rest=text[match.end(2):]
                if '\n' in gap and not text[line_start:match.start(1)].strip() and re.match(r'[ 	]+[^\W\d_]',rest):
                    continue
            pairs[number(match.group(1)),unit_key(unit)]+=1
        return pairs
    if measures(measure_source)!=measures(translated):add('units','error','Des associations nombre/unité diffèrent de l’original. Aucune conversion silencieuse n’est acceptée.')
    if len(source.strip())>=160 and len(translated.strip())<len(source.strip())*.4:
        add('short','warning','Traduction beaucoup plus courte : résumé ou passages omis possibles.')
    if len(source.strip())>=160 and len(translated.strip())>len(source.strip())*3:
        add('long','warning','Traduction beaucoup plus longue : ajouts ou répétitions possibles.')
    source_prose=BLOCKS.sub(' ',source)
    target_prose=BLOCKS.sub(' ',translated)
    compact=lambda text: ' '.join(text.casefold().split())
    short_english=(english or not source_language) and re.search(
        r'\b(?:the|and|is|are|use|press|keep|do|not|water|please|this|that|with|for|to|of|see|read|look|turn|avoid|never|without)\b',source_prose,re.I)
    if (len(source_prose.strip())>=100 or (short_english and len(source_prose.split())>=2)) and compact(source_prose)==compact(target_prose):
        add('unchanged','error','Le passage est identique à l’original ; aucune traduction exploitable détectée.')
    if re.search(r'\b(not|never|without|neither|no)\b|\b\w+n[’\x27]t\b',source,re.I) and not re.search(r'\b(pas|jamais|sans|aucun|aucune|ni|interdit|interdite|éviter|évitez|non)\b|\bn[’\x27]',translated,re.I):
        add('negation','warning','Une négation de l’original n’a pas d’équivalent français repéré. Vérifiez le sens de la consigne.')
    labels=set()
    for match in re.finditer(r'\b([A-Z][A-Z0-9_/-]{1,19})\s+(?:buttons?|keys?)\b|\b(?:[Bb]utton|[Kk]ey)\s+([A-Z][A-Z0-9_/-]{1,19})\b',source):
        labels.add(match.group(1) or match.group(2))
    missing=[label for label in sorted(labels) if not re.search(r'(?<!\w)'+re.escape(label)+r'(?!\w)',translated,re.I)]
    if missing:add('control_labels','warning','Une inscription de touche ou bouton n’a pas été retrouvée : '+', '.join(missing)+'. Comparez l’original et les inscriptions sur l’appareil.')
    return {'version':VERSION,'status':'blocked' if any(i['severity']=='error' for i in issues) else 'warning' if issues else 'checked','issues':issues}
