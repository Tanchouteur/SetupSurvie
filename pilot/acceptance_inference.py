"""Real application tool/RAG checks, using disposable accounts and conversations."""
import argparse
import asyncio
import json
import re
import secrets
import time

import httpx

from . import accounts,engine,store

CASES={
 'calculator':{'message':'Vérifie séparément 600 // 18 et 600 % 18 avec ton outil calculate. Donne ensuite le nombre de jours complets pour 600 litres consommés à raison de 18 litres par jour, et le reste en litres. Réponse courte en français.'},
 'wikipedia':{'message':'Recherche la loi d’Ohm dans la bibliothèque, ouvre et lis un résultat de Wikipédia (identifiant zim:). Explique brièvement la relation entre tension, résistance et courant, puis vérifie avec calculate le courant pour 12 V et 4 ohms. Cite la source que tu as réellement lue.'},
 'english_guide':{'message':'Dans l’exemple du moteur de résistance 1 ohm branché à 12 V de ce manuel anglais, quel courant circule et le fil prévu pour 10 A convient-il ? Vérifie le calcul avec ton outil et cite le manuel. Réponds brièvement en français.','source_id':'guide:BOOK-EN-OHM.en.txt'},
}


async def main(modes,cases):
    created=None;rows=[];origin={'Origin':'http://127.0.0.1:8000'}
    async with httpx.AsyncClient(base_url='http://127.0.0.1:8000',trust_env=False,timeout=30) as client:
        try:
            email='recette-outils-'+secrets.token_hex(5)+'@survie.local';password=secrets.token_urlsafe(24)
            created=await accounts.native('/api/v1/auths/add',{'name':'Recette outils temporaire','email':email,'password':password,'role':'user','profile_image_url':'/user.png'},accounts.emergency_admin_token())
            response=await client.post('/api/auth/login',json={'email':email,'password':password});response.raise_for_status()
            for mode in modes:
                for case in cases:
                    started=time.monotonic()
                    response=await client.post('/api/questions',json={**CASES[case],'mode':mode},headers=origin);response.raise_for_status()
                    identifier=response.json()['id'];library_seconds=None
                    while time.monotonic()-started<240:
                        response=await client.get('/api/jobs/'+identifier);response.raise_for_status();job=response.json()
                        if library_seconds is None:
                            before=time.monotonic();check=await client.get('/api/inventory');check.raise_for_status();library_seconds=time.monotonic()-before
                        if job['status'] not in ('queued','running'):break
                        await asyncio.sleep(1)
                    else:
                        await client.post('/api/jobs/'+identifier+'/cancel',headers=origin);job['status']='timeout'
                    trace_path=store.ROOT/'traces'/(identifier+'.json')
                    trace=json.loads(trace_path.read_text()) if trace_path.exists() else {'tools':[]}
                    values=[t.get('result',{}).get('value') for t in trace['tools'] if t['tool']=='calculate' and isinstance(t.get('result'),dict)]
                    names=[t['tool'] for t in trace['tools']]
                    if case=='calculator':passed=33 in values and 6 in values and bool(re.search(r'\b33\b',job['answer'])) and bool(re.search(r'\b6\b',job['answer']))
                    elif case=='wikipedia':passed='search_library' in names and 'read_source' in names and any(s['id'].startswith('zim:') for s in job['sources']) and 3 in values and '[' in job['answer']
                    else:passed=12 in values and any(s['id']=='guide:BOOK-EN-OHM.en.txt' for s in job['sources']) and bool(re.search(r'\b12\b',job['answer'])) and '[' in job['answer'] and bool(re.search(r"ne.{0,100}pas|n[’'].{0,100}pas|insuffisant|dépasse|trop faible|\bnon\b",job['answer'],re.I))
                    rows.append({'mode':mode,'model':engine.MODES[mode]['model'],'think':engine.MODES[mode]['think'],'case':case,'passed':passed and job['status']=='done','status':job['status'],'seconds':round(time.monotonic()-started,2),'inventory_during_inference_seconds':round(library_seconds,3),'answer':job['answer'],'sources':job['sources'],'trace':trace})
                    (store.ROOT/'acceptance-inference.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2))
                    print('PILOT',mode,case,rows[-1]['passed'],rows[-1]['status'],rows[-1]['seconds'],flush=True)
            # Cancel a request immediately, including the before-first-await case.
            response=await client.post('/api/questions',json={'message':'Explique longuement la loi d’Ohm.','mode':modes[0]},headers=origin);response.raise_for_status();identifier=response.json()['id']
            response=await client.post('/api/jobs/'+identifier+'/cancel',headers=origin);response.raise_for_status();await asyncio.sleep(.2)
            assert (await client.get('/api/jobs/'+identifier)).json()['status']=='cancelled'
            print('CANCEL_OK',flush=True)
        finally:
            if created:
                with store.connect() as db:
                    jobs=[r['id'] for r in db.execute('SELECT id FROM jobs WHERE user_id=?',(created['id'],))]
                for identifier in jobs:engine.cancel(identifier)
                await asyncio.sleep(.1)
                with store.connect() as db:
                    db.execute('DELETE FROM jobs WHERE user_id=?',(created['id'],));db.execute('DELETE FROM conversations WHERE user_id=?',(created['id'],))
                result=await client.delete(accounts.WEBUI+'/api/v1/users/'+created['id'],headers={'Authorization':'Bearer '+accounts.emergency_admin_token()});result.raise_for_status()
    if not all(r['passed'] for r in rows):raise SystemExit('Des essais applicatifs nécessitent une correction ; voir acceptance-inference.json.')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--modes',nargs='+',choices=list(engine.MODES),default=['rapide','moyenne','approfondie']);p.add_argument('--cases',nargs='+',choices=list(CASES),default=list(CASES));args=p.parse_args();asyncio.run(main(args.modes,args.cases))
