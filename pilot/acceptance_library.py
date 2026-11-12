"""Two real assistant checks on new sources, using a disposable reader account."""
import asyncio
import argparse
import json
import secrets
import time

import httpx
from . import accounts,store

CASES=[
    {'id':'no-doctor','expected':'HES-no-doctor-2025-03',
     'message':'Recherche examiner personne malade dans la bibliothèque sans filtre de langue. Ouvre et lis une page du chapitre How to examine a sick person du manuel Where There Is No Doctor. Réponds en français uniquement avec le titre du manuel, son édition et le titre du chapitre, puis cite la source réellement lue. Ne donne pas de conseil médical.'},
    {'id':'local','expected':'EXT-sollies-dicrim',
     'message':'Recherche le DICRIM de Solliès-Ville dans la bibliothèque, puis ouvre et lis le document trouvé avec read_source. Indique son titre et la commune concernée. Deux phrases en français, avec la citation de la source effectivement lue.'},
    {'id':'bilingual','expected':'EXT-dental-',
     'message':'Recherche dental teeth dans les guides anglais de la bibliothèque (language=en), puis ouvre un chapitre du nouveau guide Where There Is No Dentist avec read_source. Donne en français le titre du guide, la langue originale et un intitulé de rubrique présent dans la page lue, sans donner de conseil de soin. Cite la source effectivement lue.'}
]


async def main(cases=None,report_name='acceptance-library.json'):
    created=None;rows=[];origin={'Origin':'http://127.0.0.1:8000'}
    async with httpx.AsyncClient(base_url='http://127.0.0.1:8000',trust_env=False,timeout=30) as client:
        try:
            email='recette-bibliotheque-'+secrets.token_hex(6)+'@survie.local';password=secrets.token_urlsafe(24)
            created=await accounts.native('/api/v1/auths/add',{'name':'Recette bibliothèque temporaire','email':email,'password':password,'role':'user','profile_image_url':'/user.png'},accounts.emergency_admin_token())
            response=await client.post('/api/auth/login',json={'email':email,'password':password});response.raise_for_status()
            for case in [c for c in CASES if not cases or c['id'] in cases]:
                started=time.monotonic()
                response=await client.post('/api/questions',json={'message':case['message'],'mode':'rapide'},headers=origin);response.raise_for_status()
                job_id=response.json()['id']
                while time.monotonic()-started<180:
                    response=await client.get('/api/jobs/'+job_id);response.raise_for_status();job=response.json()
                    if job['status'] not in ('queued','running'):break
                    await asyncio.sleep(1)
                else:
                    await client.post('/api/jobs/'+job_id+'/cancel',headers=origin)
                    job={'status':'timeout','answer':'','sources':[]}
                trace=store.ROOT/'traces'/(job_id+'.json')
                tools=json.loads(trace.read_text()).get('tools',[]) if trace.exists() else []
                names=[t['tool'] for t in tools]
                passed=job['status']=='done' and 'search_library' in names and 'read_source' in names and any(case['expected'] in s['id'] for s in job.get('sources',[]))
                rows.append({'case':case['id'],'passed':passed,'status':job['status'],'seconds':round(time.monotonic()-started,2),'answer':job['answer'],'sources':job.get('sources',[]),'tools':tools})
                print(case['id'],job['status'],'source lue et citée :',passed,flush=True)
                (store.ROOT/report_name).write_text(json.dumps(rows,ensure_ascii=False,indent=2))
        finally:
            if created:
                with store.connect() as db:
                    ids=[r[0] for r in db.execute('SELECT id FROM jobs WHERE user_id=?',(created['id'],))]
                for identifier in ids:
                    response=await client.post('/api/jobs/'+identifier+'/cancel',headers=origin)
                    if response.status_code not in (200,404):response.raise_for_status()
                await asyncio.sleep(.1)
                with store.connect() as db:
                    db.execute('DELETE FROM jobs WHERE user_id=?',(created['id'],))
                    db.execute('DELETE FROM conversations WHERE user_id=?',(created['id'],))
                for identifier in ids:(store.ROOT/'traces'/(identifier+'.json')).unlink(missing_ok=True)
                response=await client.delete(accounts.WEBUI+'/api/v1/users/'+created['id'],headers={'Authorization':'Bearer '+accounts.emergency_admin_token()});response.raise_for_status()
    if not all(r['passed'] for r in rows):raise SystemExit('Contrôler acceptance-library.json : un essai n’a pas cité la source attendue.')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--case',action='append',choices=[c['id'] for c in CASES])
    args=parser.parse_args()
    name='acceptance-no-doctor.json' if args.case==['no-doctor'] else 'acceptance-library.json'
    asyncio.run(main(args.case,name))
