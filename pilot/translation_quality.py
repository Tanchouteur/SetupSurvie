"""Conservative text checks, never a certificate of semantic fidelity.

No model/network: compare protected tokens and flag weaker completeness signals.
"""
from collections import Counter
from decimal import Decimal, InvalidOperation
import re
import unicodedata
from .math_text import BLOCKS,UNREADABLE

VERSION=8
# PDF extraction often joins a label and its number ("Chapter4", "X7").
# Count that number on both sides, including when French restores the space.
NUMBER=r'(?<!\d)(?:[-+−]\s*)?\d+(?:[ \u00a0\u202f]\d{3})*(?:[.,]\d+)?'
NUMBERS=re.compile(NUMBER)
ENGLISH_DOLLAR_AMOUNT=re.compile(r'(\$\s*)([+-]?\d{1,3}(?:,\d{3})+(?:\.\d+)?)(?!\d|[.,]\d)')
ENGLISH_GROUPED_NUMBER=re.compile(r'(?<![\d.,])\d{1,3}(?:,\d{3})+(?:\.\d+)?(?!\d|[.,]\d)')
EN_ORDINAL=re.compile(r'(?<!\w)([0-9]+)(?:st|nd|rd|th)(?!\w)',re.I)
FR_ORDINAL=re.compile(r'(?<!\w)([0-9]+)(?:er|re|ère|e|ème|eme|ᵉ|ᵉʳ|ʳᵉ)s?(?!\w)',re.I)
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
    'mg/kg':'mg/kg','g/l':'g/l','mg/l':'mg/l','ml/min':'ml/min','km/h':'km/h','m/s':'m/s'}
UNIT=re.compile('('+NUMBER+r')\s*('+ '|'.join(re.escape(k).replace('/',r'\s*/\s*').replace('°','°'+r'\s*') for k in sorted(UNIT_ALIASES,key=len,reverse=True))+r')(?![a-zà-ÿ\d²³])',re.I)


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
    # Count only additional French words. Ordinary written-out ordinals from
    # the source must not also satisfy a missing numbered ordinal.
    for value,missing in (expected-received).items():
        if value not in ORDINAL_WORDS:continue
        english,french=ORDINAL_WORDS[value]
        old=len(re.findall(r'\b'+english+r'(?:ly)?\b',source,re.I))
        new=len(re.findall(r'\b(?:'+french+r')\b',translated,re.I))
        received[value]+=min(missing,max(0,new-old))
    return EN_ORDINAL.sub(' ',source),FR_ORDINAL.sub(' ',translated),expected==received


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
    source=normalized(source);translated=normalized(translated)
    issues=[]
    def add(code,severity,message):issues.append({'code':code,'severity':severity,'message':message})
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
    source_numbers,translated_numbers,ordinals_match=separate_ordinals(measure_source,translated)
    if not ordinals_match:add('ordinals','error','Un rang indiqué par un nombre dans l’original a disparu, été ajouté ou changé.')
    if numbers(source_numbers)!=numbers(translated_numbers):add('numbers','error','Des nombres ont disparu, été ajoutés ou changé. Comparez le passage à l’original et reprenez avec un autre mode.')
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
            pairs[number(match.group(1)),UNIT_ALIASES[unit.lower()]]+=1
        return pairs
    if measures(measure_source)!=measures(translated):add('units','error','Des associations nombre/unité diffèrent de l’original. Aucune conversion silencieuse n’est acceptée.')
    if len(source.strip())>=160 and len(translated.strip())<len(source.strip())*.4:
        add('short','warning','Traduction beaucoup plus courte : résumé ou passages omis possibles.')
    if len(source.strip())>=160 and len(translated.strip())>len(source.strip())*3:
        add('long','warning','Traduction beaucoup plus longue : ajouts ou répétitions possibles.')
    if len(source.strip())>=100 and re.sub(r'\s+',' ',source).strip().casefold()==re.sub(r'\s+',' ',translated).strip().casefold():
        add('unchanged','error','Le passage est identique à l’original ; aucune traduction exploitable détectée.')
    if re.search(r'\b(not|never|without|neither|no)\b|\b\w+n[’\x27]t\b',source,re.I) and not re.search(r'\b(pas|jamais|sans|aucun|aucune|ni|interdit|interdite|éviter|évitez|non)\b|\bn[’\x27]',translated,re.I):
        add('negation','warning','Une négation de l’original n’a pas d’équivalent français repéré. Vérifiez le sens de la consigne.')
    labels=set()
    for match in re.finditer(r'\b([A-Z][A-Z0-9_/-]{1,19})\s+(?:buttons?|keys?)\b|\b(?:[Bb]utton|[Kk]ey)\s+([A-Z][A-Z0-9_/-]{1,19})\b',source):
        labels.add(match.group(1) or match.group(2))
    missing=[label for label in sorted(labels) if not re.search(r'(?<!\w)'+re.escape(label)+r'(?!\w)',translated,re.I)]
    if missing:add('control_labels','warning','Une inscription de touche ou bouton n’a pas été retrouvée : '+', '.join(missing)+'. Comparez l’original et les inscriptions sur l’appareil.')
    return {'version':VERSION,'status':'blocked' if any(i['severity']=='error' for i in issues) else 'warning' if issues else 'checked','issues':issues}
