"""Local HTML text extraction shared by readers and archive indexes. No network."""
from html.parser import HTMLParser
from .math_text import Formula,UNREADABLE,marked,name as tag_name


class Text(HTMLParser):
    VOID={'area','base','br','col','embed','hr','img','input','link','meta','param','source','track','wbr'}
    def __init__(self,*,prefer_main=True):
        super().__init__();self.parts=[];self.skip=0;self.math=None;self.images=[];self.title=[];self.in_title=False;self.language=''
        self.formulas=0;self.unreadable_formulas=0
        self.prefer_main=prefer_main;self.tags=[];self.sections=[];self.active=[];self.math_wrappers=[]
    def append(self,text):
        self.parts.append(text)
        for section in self.active:section['parts'].append(text)
    def handle_starttag(self,tag,attrs):
        # A valueless attribute (<span class>) arrives as None from HTMLParser.
        attrs={k:v or '' for k,v in attrs}
        if self.math:
            self.math.start(tag,attrs);return
        if tag_name(tag)=='math' and not self.skip:
            self.math=Formula(attrs);return
        if tag not in self.VOID:self.tags.append(tag)
        if 'mwe-math-element' in attrs.get('class','').split():
            self.math_wrappers.append({'depth':len(self.tags),'native':False})
        if self.prefer_main and not self.skip and len(self.sections)<32 and (tag in ('article','main') or attrs.get('role')=='main'):
            section={'kind':'article' if tag=='article' else 'main','depth':len(self.tags),'parts':[]};self.sections.append(section);self.active.append(section)
        if tag=='html':self.language=attrs.get('lang','').split('-')[0]
        if tag in ('script','style','nav'):self.skip+=1
        if tag=='title':self.in_title=True
        if tag in ('p','br','h1','h2','h3','li','tr'):self.append('\n')
        if tag=='img' and attrs.get('src'):self.images.append({'src':attrs['src'],'alt':attrs.get('alt','')})
        if tag=='img' and not self.skip and any(c.startswith('mwe-math-fallback-image') or c=='tex' for c in attrs.get('class','').split()):
            if self.math_wrappers and self.math_wrappers[-1]['native']:return
            # Only an explicit formula image's own alternative, never a guess
            # from its filename or an arbitrary figure's caption.
            value=attrs.get('alt','').strip()
            self.emit_formula(marked(value) if value and len(value)<=16384 else UNREADABLE)
    def handle_endtag(self,tag):
        if self.math:
            if self.math.end(tag):
                value=self.math.text();self.math=None;self.emit_formula(value)
                if self.math_wrappers:self.math_wrappers[-1]['native']=value!=UNREADABLE
            return
        if tag in ('script','style','nav'):self.skip=max(0,self.skip-1)
        if tag=='title':self.in_title=False
        if tag in ('p','h1','h2','h3','li','tr'):self.append('\n')
        if tag not in self.VOID:
            try:index=len(self.tags)-1-self.tags[::-1].index(tag)
            except ValueError:return
            self.active=[section for section in self.active if section['depth']<=index]
            self.math_wrappers=[wrapper for wrapper in self.math_wrappers if wrapper['depth']<=index]
            del self.tags[index:]
    def handle_data(self,text):
        if self.math:self.math.data(text);return
        if self.in_title:self.title.append(text)
        if not self.skip and not self.math:self.append(text)
    def text(self):
        if self.math:
            self.math=None;self.emit_formula(UNREADABLE)
        clean=lambda parts:'\n'.join(x.strip() for x in ''.join(parts).splitlines() if x.strip())
        if self.prefer_main:
            for kind in ('article','main'):
                choices=[clean(section['parts']) for section in self.sections if section['kind']==kind]
                if any(choices):return max(choices,key=len)
        return clean(self.parts)
    def emit_formula(self,value):
        self.formulas+=1;self.unreadable_formulas+=int(value==UNREADABLE)
        self.handle_data(' '+value+' ')

