"""Synthetic browser checks; run with Playwright and Chromium installed."""
from pathlib import Path
from urllib.parse import urlparse
from playwright.sync_api import sync_playwright
root=Path(__file__).resolve().parents[1]/'portal'
with sync_playwright() as p:
 browser=p.chromium.launch(headless=True,args=['--no-sandbox'])
 for width,height in [(1280,850),(1280,600),(390,850)]:
  page=browser.new_page(viewport={'width':width,'height':height})
  def route(r):
   path=urlparse(r.request.url).path
   if path.startswith('/api/'):
    key=path[5:]
    data={'auth/me':{'id':'test','name':'Test','role':'user','recovery_ready':True},'status':{'modes':[],'books':[],'guides':0},'conversations':{'conversations':[{'id':'a','title':'Conversation A'},{'id':'b','title':'Conversation B'}]}}
    if key.startswith('conversations/'):
     cid=key.split('/')[1];value={'title':'Conversation '+cid.upper(),'messages':[{'role':'assistant','content':'\n\n'.join('Paragraphe '+str(i)+' : un contenu assez long pour lire et tester le défilement.' for i in range(120)),'sources':[]}],'jobs':[]}
    else:value=data.get(key,{})
    return r.fulfill(json=value)
   f=root/('index.html' if path=='/' else path.lstrip('/'))
   if f.is_file():return r.fulfill(path=str(f))
   r.abort()
  page.route('**/*',route)
  page.goto('http://localhost:8080/#chat',wait_until='networkidle')
  page.evaluate("openConversation('a')")
  page.wait_for_function("S.conversation==='a'&&!S.loadingConversation")
  page.evaluate("document.querySelector('#chat-messages').scrollTop=420;window.scrollTo(0,420)")
  page.wait_for_timeout(100)
  page.reload(wait_until='networkidle')
  page.wait_for_function("S.conversation==='a'&&!S.loadingConversation")
  if width>760:
   assert abs(page.locator('#chat-messages').evaluate('(e)=>e.scrollTop')-420)<5
   assert page.evaluate('document.documentElement.scrollHeight<=innerHeight'),page.evaluate('[document.documentElement.scrollHeight,innerHeight]')
   assert page.locator('#send-question').bounding_box()['y']<height
  else:assert abs(page.evaluate('scrollY')-420)<5
  page.evaluate("view('library');view('chat')")
  if width>760:assert abs(page.locator('#chat-messages').evaluate('(e)=>e.scrollTop')-420)<5
  page.evaluate("openConversation('b')")
  page.wait_for_function("S.conversation==='b'&&!S.loadingConversation")
  page.evaluate("openConversation('a')")
  page.wait_for_function("S.conversation==='a'&&!S.loadingConversation")
  if width>760:assert abs(page.locator('#chat-messages').evaluate('(e)=>e.scrollTop')-420)<5
  page.evaluate('newConversation()')
  page.reload(wait_until='networkidle')
  assert page.evaluate('S.conversation') is None
  print(width,height,'OK : restauration après actualisation, changement de conversation, navigation et nouvelle conversation')
  page.close()
 browser.close()
