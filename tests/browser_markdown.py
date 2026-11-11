"""Run with an isolated Python environment containing Playwright and Chromium; uses synthetic data only."""
from playwright.sync_api import sync_playwright
from pathlib import Path
import json
root=Path(__file__).resolve().parents[1]/'portal'
sample='''#### Points clés
*guide synthétique* avec **gras** et ~~barré~~ [1]

- Premier
- Deuxième
  - Sous-liste

1. Un
2. Deux

| Étape | Détails |
| --- | --- |
| Toit | Ligne 1<br>Ligne 2 |

> Une citation

```html
<br><script>alert(1)</script> [1]
```

[Site](https://example.org) [Danger](javascript:alert(1))
<img src="https://example.org/tracker" onerror="window.hacked=true">
<script>window.hacked=true</script><iframe src="https://example.org"></iframe>
'''
with sync_playwright() as p:
 browser=p.chromium.launch(headless=True,args=['--no-sandbox'])
 for width in (1280,390):
  page=browser.new_page(viewport={'width':width,'height':850});errors=[];external=[]
  page.on('pageerror',lambda e:errors.append(str(e)))
  def route(r):
   from urllib.parse import urlparse
   path=urlparse(r.request.url).path
   if path.startswith('/api/'):
    value={'auth/me':{'id':'t','name':'Test','role':'user','recovery_ready':True},'conversations':{'conversations':[]},'status':{'modes':[],'books':[],'guides':0}}.get(path[5:],{})
    return r.fulfill(json=value)
   file=root/('index.html' if path=='/' else path.lstrip('/'))
   if file.is_file():return r.fulfill(path=str(file))
   external.append(r.request.url);r.abort()
  page.route('**/*',route);page.goto('http://localhost:8080/',wait_until='networkidle')
  page.evaluate('(text)=>{view("chat");message("assistant",text,[{number:1,id:"test",title:"Source"}]);}',sample)
  body=page.locator('.message').last
  assert body.locator('h4').inner_text()=='Points clés'
  assert body.locator('em').inner_text()=='guide synthétique'
  assert body.locator('ul ul li').inner_text()=='Sous-liste'
  assert body.locator('ol li').count()==2
  assert body.locator('thead th').count()==2
  assert body.locator('td br').count()==1
  assert body.locator('pre code').inner_text().startswith('<br><script>')
  assert body.locator('.citation').count()==1
  assert body.locator('script,iframe,img,[onerror]').count()==0
  assert body.locator('a').last.get_attribute('href') is None
  assert not page.evaluate('window.hacked || false')
  assert not errors,errors
  assert not external,external
  assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
  print(width,'OK: titres, listes, tableau, HTML, code, citations, sécurité, aucune requête externe')
  page.close()
 browser.close()
