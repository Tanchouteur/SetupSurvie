"""Conservative text checks, never a certificate of semantic fidelity.

No model/network: compare protected tokens and flag weaker completeness signals.
"""
from collections import Counter
from decimal import Decimal, InvalidOperation
import re
import unicodedata

VERSION=3
# PDF extraction often joins a label and its number ("Chapter4", "X7").
# Count that number on both sides, including when French restores the space.
NUMBER=r'(?<!\d)(?:[-+−]\s*)?\d+(?:[ \u00a0\u202f]\d{3})*(?:[.,]\d+)?'
NUMBERS=re.compile(NUMBER)
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


def assess(source,translated):
    source=normalized(source);translated=normalized(translated)
    issues=[]
    def add(code,severity,message):issues.append({'code':code,'severity':severity,'message':message})
    # PDF manuals sometimes draw key names as images; extraction leaves a hole
    # in "Press the         key". Numeric equality cannot validate that command.
    if re.search(r'\b(?:press|enter|push|appuyez|appuyer|saisissez|entrez)[^\n.!?]{0,60}[ \t]{4,}(?:keys?|buttons?|to|on|and|pour|sur|et)\b',source,re.I) or '\ufffd' in source:
        add('source_gaps','warning','Le texte original extrait contient des blancs ou caractères manquants, possiblement des touches dessinées. Comparez la page originale ; les commandes manquantes ne sont pas reconstituées.')
    left=Counter(number(m.group()) for m in NUMBERS.finditer(source))
    right=Counter(number(m.group()) for m in NUMBERS.finditer(translated))
    if left!=right:add('numbers','error','Des nombres ont disparu, été ajoutés ou changé. Comparez le passage à l’original et reprenez avec un autre mode.')
    def measures(text):
        return Counter((number(m.group(1)),UNIT_ALIASES[re.sub(r'\s','',m.group(2)).lower()]) for m in UNIT.finditer(text))
    if measures(source)!=measures(translated):add('units','error','Des associations nombre/unité diffèrent de l’original. Aucune conversion silencieuse n’est acceptée.')
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
