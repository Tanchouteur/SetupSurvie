"""Bounded MathML to source notation, never calculation, OCR or a CAS.

Prefer an author's alternative; otherwise retain supported presentation grouping.
Unknown structures fail explicitly instead of guessing their mathematical meaning.
"""
import re
import hashlib

UNREADABLE='[Formule non extractible : consultez l’original illustré.]'
MAX_CHARS=16384
BLOCKS=re.compile(r'(?m)^(?P<fence>`{3,})math[ \t]*\n(?P<value>[\s\S]*?)\n(?P=fence)[ \t]*(?=\n|$)')
OPENINGS=re.compile(r'(?m)^`{3,}math[ \t]*(?:\n|$)')


def safe_prefix(text,maximum):
    """Never retain a formula cut by a preview limit, including old snapshots."""
    end=min(len(text),maximum);complete={m.start():m.end() for m in BLOCKS.finditer(text)};covered=0
    for opening in OPENINGS.finditer(text):
        if opening.start()<covered:continue
        if opening.start()>=end:break
        if complete.get(opening.start(),len(text)+1)>end:
            end=opening.start();break
        covered=complete[opening.start()]
    return text[:end]


def reading_window(text,offset,maximum):
    """Contiguous bounded source slice, never a partial protected equation.

    Rewind a requested offset inside a small formula. Skip an oversized formula
    rather than exceeding the budget; callers must announce that omission.
    """
    start=min(max(0,offset),len(text));skipped=False
    spans=[m.span() for m in BLOCKS.finditer(text)]
    for first,last in spans:
        if first<start<last:
            start=first if last-first<=maximum else last
            skipped=last-first>maximum
            break
    for first,last in spans:
        if last<=start:continue
        end=min(len(text),start+maximum)
        if first>=end:break
        if first<=start and last>end:
            start=last;skipped=True
        elif first<end<last:break
    end=min(len(text),start+maximum)
    # safe_prefix has absolute source coordinates, including old unclosed blocks.
    prefix=safe_prefix(text,end)
    value=prefix[start:] if len(prefix)>=start else ''
    return {'text':value,'offset':start,'next_offset':start+len(value),
            'formula_omitted':skipped or len(prefix)<end}


def marked(value):
    fence='`'*max(3,1+max((len(m[0]) for m in re.finditer(r'`+',value)),default=0))
    return '\n'+fence+'math\n'+value+'\n'+fence+'\n'


class TranslationMismatch(ValueError):
    def __init__(self,candidate,model):
        super().__init__('Les repères des formules ont été modifiés ou déplacés. Le passage reste à traduire.')
        self.candidate=candidate;self.model=model


class ProtectedTranslation:
    """Translate prose around immutable formulas; require each anchor in order.

    No approximation or repair when an anchor is missing. The worker preserves
    that rejected proposal, just as it does a numerical quality failure.
    """
    def __init__(self,text):
        digest=hashlib.sha256(text.encode()).hexdigest()[:12].translate(str.maketrans('0123456789','ghijklmnop'))
        self.prefix='SS_FORMULE_'+digest+'_'
        while self.prefix in text:self.prefix+='X'
        self.formulas=[]
        def replace(match):
            # Alphabetic positions avoid introducing extra numbers to translate.
            number=len(self.formulas);letters=''
            while True:
                letters=chr(65+number%26)+letters;number=number//26-1
                if number<0:break
            token='['+self.prefix+letters+']'
            self.formulas.append((token,match[0]));return token
        self.text=BLOCKS.sub(replace,text)
        self.pattern=re.compile(r'\['+re.escape(self.prefix)+r'[^\]\n]*\]')
    def restore(self,text,model):
        if not self.formulas:return text
        if self.pattern.findall(text)!=[token for token,_ in self.formulas]:raise TranslationMismatch(text,model)
        values=dict(self.formulas)
        # Newlines keep original blocks valid even if the model joins prose.
        return self.pattern.sub(lambda m:'\n'+values[m[0]]+'\n',text)


def style(value,attrs):
    variant=attrs.get('mathvariant','')
    styles={'normal':'mathrm','bold':'mathbf','italic':'mathit','bold-italic':'boldsymbol',
            'double-struck':'mathbb','script':'mathcal','fraktur':'mathfrak','monospace':'mathtt','sans-serif':'mathsf'}
    if not variant:return value
    if variant not in styles:raise ValueError()
    return '\\'+styles[variant]+'{'+value+'}'


def name(tag):return tag.rsplit(':',1)[-1]


def literal(value):
    return re.sub(r'([\\{}%&#_$])',lambda m:'\\'+m[0],value)


def render(node):
    tag,attrs,children=node
    nodes=[c for c in children if not isinstance(c,str)]
    def body():return ''.join(c if isinstance(c,str) else render(c) for c in children)
    def arguments(count):
        if len(nodes)!=count or any(c.strip() for c in children if isinstance(c,str)):raise ValueError()
        values=[render(c) for c in nodes]
        if any(not value.strip() for value in values):raise ValueError()
        return values
    if tag in ('mi','mn','mo','mtext','ms'):
        if nodes:raise ValueError()
        value=''.join(children).strip()
        if not value:raise ValueError()
        value=literal(value)
        if tag=='mo':
            value=value.replace('\u2061',r'\,').replace('\u2062',r'\times ').replace('\u2063',',').replace('\u2064','+')
            return ' '+value+' '
        if tag in ('mtext','ms'):return r'\text{'+value+'}'
        return style(value,attrs)
    if tag in ('math','mrow','mstyle','mpadded','mtd'):return style(body(),attrs)
    if tag=='mspace':return ' '
    if tag=='mphantom':return ''
    if tag=='semantics':
        annotations=[c for c in nodes if c[0]=='annotation' and c[1].get('encoding','').lower() in ('application/x-tex','application/x-latex','math/tex')]
        for annotation in annotations:
            if all(isinstance(c,str) for c in annotation[2]):
                value=''.join(annotation[2]).strip()
                if value:return value
        presentation=[c for c in nodes if c[0] not in ('annotation','annotation-xml')]
        if len(presentation)!=1:raise ValueError()
        return render(presentation[0])
    if tag=='mfrac':
        a,b=arguments(2)
        if re.fullmatch(r'0+(?:\.0+)?(?:px|pt|em|ex|%)?',attrs.get('linethickness','')):
            return r'\genfrac{}{}{0pt}{}{'+a+'}{'+b+'}'
        return r'\frac{'+a+'}{'+b+'}'
    if tag in ('msub','msup'):
        a,b=arguments(2);return '{'+a+'}'+('_' if tag=='msub' else '^')+'{'+b+'}'
    if tag=='msubsup':
        a,b,c=arguments(3);return '{'+a+'}_{'+b+'}^{'+c+'}'
    if tag=='msqrt':
        value=body()
        if not value.strip():raise ValueError()
        return r'\sqrt{'+value+'}'
    if tag=='mroot':
        a,b=arguments(2);return r'\sqrt['+b+']{'+a+'}'
    if tag in ('munder','mover'):
        a,b=arguments(2);return ('\\underset' if tag=='munder' else '\\overset')+'{'+b+'}{'+a+'}'
    if tag=='munderover':
        a,b,c=arguments(3);return r'\overset{'+c+r'}{\underset{'+b+'}{'+a+'}}'
    if tag=='mfenced':
        if any(c.strip() for c in children if isinstance(c,str)):raise ValueError()
        values=[render(c) for c in nodes];separators=re.sub(r'\s','',attrs.get('separators',','));parts=[]
        for i,value in enumerate(values):
            if i and separators:parts.append(literal(separators[min(i-1,len(separators)-1)]))
            parts.append(value)
        return literal(attrs.get('open','('))+''.join(parts)+literal(attrs.get('close',')'))
    if tag=='mtable':
        if not nodes or any(c[0]!='mtr' for c in nodes) or any(c.strip() for c in children if isinstance(c,str)):raise ValueError()
        rows=[]
        for row in nodes:
            cells=[c for c in row[2] if not isinstance(c,str)]
            if not cells or any(c[0]!='mtd' or c[1].get('rowspan','1')!='1' or c[1].get('columnspan','1')!='1' for c in cells) or any(c.strip() for c in row[2] if isinstance(c,str)):raise ValueError()
            rows.append(' & '.join(render(c) for c in cells))
        return r'\begin{matrix}'+r' \\ '.join(rows)+r'\end{matrix}'
    raise ValueError('Unsupported mathematical structure')


class Formula:
    """Events from HTMLParser, with a bounded tree and no external resolution."""
    ATTRS={'alttext','encoding','linethickness','mathvariant','open','close','separators','rowspan','columnspan'}
    def __init__(self,attrs):
        self.bad=False;self.chars=0;self.nodes=0;self.level=0;self.math_depth=0;self.stack=[];self.root=None
        self.start('math',attrs)
    def start(self,tag,attrs):
        tag=name(tag);self.level+=1;self.math_depth+=int(tag=='math');self.nodes+=1
        attrs={k:v or '' for k,v in dict(attrs).items() if k in self.ATTRS}
        self.chars+=sum(len(v) for v in attrs.values())
        if self.chars>MAX_CHARS or self.nodes>2048 or self.level>48:self.bad=True
        if self.bad:return
        node=(tag,attrs,[])
        if self.stack:self.stack[-1][2].append(node)
        else:self.root=node
        self.stack.append(node)
    def data(self,text):
        self.chars+=len(text)
        if self.chars>MAX_CHARS:self.bad=True
        if not self.bad and self.stack:self.stack[-1][2].append(text)
    def end(self,tag):
        tag=name(tag);self.level-=1;self.math_depth-=int(tag=='math')
        if not self.bad:
            if not self.stack or self.stack[-1][0]!=tag:self.bad=True
            else:self.stack.pop()
        return tag=='math' and self.math_depth==0
    def text(self,complete=True):
        if self.bad or not complete or not self.root or self.stack:return UNREADABLE
        try:
            value=self.root[1].get('alttext','').strip() or render(self.root).strip()
            if not value or len(value)>MAX_CHARS:raise ValueError()
            return marked(value)
        except (ValueError,RecursionError):return UNREADABLE
