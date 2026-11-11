"""Real WebKit layout checks, no account and no LLM request.

PLAYWRIGHT_BASE_URL=http://server:8080 PLAYWRIGHT_OUTPUT=/ssd/results python tests/browser_mobile.py
Requires Playwright and its WebKit browser in an isolated environment.
"""
import json
import os
from pathlib import Path
from playwright.sync_api import sync_playwright

URL=os.environ.get('PLAYWRIGHT_BASE_URL','http://127.0.0.1:8080')
OUTPUT=Path(os.environ.get('PLAYWRIGHT_OUTPUT','/tmp/setupsurvie-mobile'))
FIXTURE='''## Préparer un abri

| Étape | Gestes à prévoir | Explication | Matériel |
| --- | --- | --- | --- |
| 1. Couverture | Prévoir une bâche imperméable | Garder les mots et les phrases lisibles sur un téléphone. | Bâche et cordes |
| 2. Ventilation | Conserver les ouvertures nécessaires | Exemple de mise en page uniquement, aucune instruction technique validée. | Tente |
'''+('\nUn paragraphe de réponse pour vérifier une longue conversation.\n'*60)+'''
```text
une_ligne_de_code_tres_longue_qui_doit_defiler_sans_elargir_la_page_0123456789_0123456789_0123456789
```
'''


def main():
    OUTPUT.mkdir(parents=True,exist_ok=True);results=[]
    with sync_playwright() as p:
        browser=p.webkit.launch(headless=True)
        device={k:v for k,v in p.devices['iPhone 14'].items() if k!='default_browser_type'}
        context=browser.new_context(**device);page=context.new_page();errors=[]
        page.on('pageerror',lambda e:errors.append(str(e)))
        page.goto(URL+'/?mobile-regression=0.1.5#chat');page.wait_for_function("typeof message==='function' && typeof marked==='object'")
        page.evaluate("text=>{document.getElementById('chat-messages').replaceChildren();message('assistant',text);}",FIXTURE)
        for width in (320,375,390,430,768):
            page.set_viewport_size({'width':width,'height':750});page.wait_for_timeout(100)
            layout=page.evaluate('''()=>{
              const box=document.getElementById('chat-messages'),composer=document.getElementById('chat-form'),table=document.querySelector('.message-table');
              return {width:innerWidth,document:document.documentElement.scrollWidth,composer:composer.getBoundingClientRect().height,
                reading:box.clientHeight,tableScroll:table.scrollWidth>table.clientWidth,cell:document.querySelector('td').getBoundingClientRect().width,
                overlap:box.getBoundingClientRect().bottom>composer.getBoundingClientRect().top+1,
                outerScroll:document.documentElement.scrollHeight>innerHeight+2};
            }''')
            assert layout['document']<=width,layout
            if width<=760:
                assert layout['composer']<=180 and layout['reading']>=300,layout
                assert layout['tableScroll'] and layout['cell']>=150,layout
            assert not layout['overlap'] and not layout['outerScroll'],layout
            results.append(layout)
        page.set_viewport_size({'width':390,'height':750});page.wait_for_timeout(250)
        assert page.locator('#main-navigation').evaluate('e=>e.getBoundingClientRect().right')<=0
        page.locator('#chat-messages').evaluate('e=>e.scrollTop=0')
        page.screenshot(path=str(OUTPUT/'iphone-table.png'))
        page.locator('.message-table').evaluate('e=>e.scrollLeft=e.scrollWidth')
        assert page.locator('.message-table').evaluate('e=>e.scrollLeft')>0
        page.locator('#chat-input').focus();page.set_viewport_size({'width':390,'height':390});page.wait_for_timeout(100)
        assert page.locator('#send-question').is_visible()
        assert page.locator('#chat-messages').evaluate('e=>e.clientHeight')>=100
        page.screenshot(path=str(OUTPUT/'iphone-keyboard-height.png'))
        assert not errors,errors
        (OUTPUT/'mobile-regression.json').write_text(json.dumps({'passed':True,'engine':'WebKit','physical_device':False,'layouts':results,'keyboard_height_emulated':True,'errors':errors},indent=2))
        print(json.dumps({'passed':True,'layouts':results}))
        context.close();browser.close()


if __name__=='__main__':main()
