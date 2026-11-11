"""Publish versioned, shared Open WebUI profiles without copying model weights."""
import asyncio

from . import accounts, engine

BUILTIN_TOOLS={name:name in {'time','user_input','files','knowledge'} for name in (
    'time','user_input','files','knowledge','chats','subagents','memory','web_search',
    'image_generation','code_interpreter','notes','channels','skills','tasks',
    'automations','calendar','notifications')}


async def configure():
    token=accounts.emergency_admin_token()
    db=accounts.sqlite3.connect('file:'+accounts.DB_PATH+'?mode=ro',uri=True)
    try:ids={row[0] for row in db.execute('SELECT id FROM model')}
    finally:db.close()
    profiles=[('survie-'+key,profile,profile['model']) for key,profile in engine.MODES.items()]
    # Raw Ollama entries remain selectable in the advanced UI; constrain them too.
    base_profiles={p['model']:p for p in engine.MODES.values() if p.get('think') is not False}
    for identifier,profile in base_profiles.items():
        profiles.append((identifier,{**profile,'name':'Essai direct · '+identifier},None))
    for identifier,profile,base in profiles:
        payload={'id':identifier,'base_model_id':base,'name':profile['name'],
                 'meta':{'builtinTools':BUILTIN_TOOLS,'description':profile.get('description','Modèle alternatif pour les essais comparatifs.')},
                 'params':{'num_ctx':engine.PROFILE_CONFIG['context'],'num_predict':engine.PROFILE_CONFIG['output_tokens'],
                           'think':profile['think'],'system':engine.POLICY.read_text()},
                 'access_grants':[{'principal_type':'user','principal_id':'*','permission':'read'}],
                 'is_active':True}
        endpoint='/api/v1/models/model/update' if identifier in ids else '/api/v1/models/create'
        await accounts.native(endpoint,payload,token)
    print(f'{len(engine.MODES)} profils partagés et {len(base_profiles)} modèles directs configurés dans Open WebUI.')


if __name__=='__main__':asyncio.run(configure())
