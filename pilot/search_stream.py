"""Bounded live search snapshots. Disconnect cancels only this client's work."""
import asyncio
import json
from . import library

BUDGET=60


async def packets(query,language='',limit=8,**options):
    queue=asyncio.Queue(maxsize=1)
    def put(value):
        if queue.full():queue.get_nowait()
        queue.put_nowait(value)
    async def update(value):put({'state':'results','results':list(value),'coverage':value.coverage})
    async def work():
        try:
            value=await library.search(query,language,limit=limit,on_update=update,budget=BUDGET,**options) if query.strip() or options.get('kind')=='videos' else []
            put({'state':'done','results':list(value),'coverage':getattr(value,'coverage',{})})
        except asyncio.CancelledError:raise
        except Exception:put({'state':'error','message':'La recherche a été interrompue. Les résultats reçus restent consultables ; réessayez pour compléter.'})
    task=asyncio.create_task(work())
    try:
        yield 'data: '+json.dumps({'state':'working','budget_seconds':BUDGET})+'\n\n'
        while True:
            try:value=await asyncio.wait_for(queue.get(),2)
            except TimeoutError:
                yield ': recherche en cours\n\n';continue
            yield 'data: '+json.dumps(value,ensure_ascii=False,separators=(',',':'))+'\n\n'
            if value['state'] in ('done','error'):break
    finally:
        task.cancel();await asyncio.gather(task,return_exceptions=True)
