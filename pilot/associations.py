"""Resolve an explicit document selection without invoking or requiring a model."""
import asyncio
from fastapi import HTTPException
from . import library,store


async def resolve(identifiers,known=()):
    known={item['id']:item for item in known};loaded={};semaphore=asyncio.Semaphore(3)
    async def load(identifier):
        if identifier in known:return known[identifier]
        async with semaphore:
            try:source=await asyncio.wait_for(library.source(identifier),8)
            except HTTPException:raise
            except (TimeoutError,OSError):raise HTTPException(503,'Un document n’a pas pu être ouvert pour l’ajouter. Votre sélection actuelle est conservée.') from None
            loaded[source['id']]=source
            return {'id':source['id'],'title':source['title']}
    # Structured concurrency joins remaining readers on failure/cancellation.
    tasks=[asyncio.create_task(load(identifier)) for identifier in dict.fromkeys(identifiers)]
    try:
        choices=await asyncio.gather(*tasks)
        return list({item['id']:item for item in choices}.values()),loaded
    finally:
        for task in tasks:
            if not task.done():task.cancel()
        await asyncio.gather(*tasks,return_exceptions=True)


def save(db,identifier,sources):
    try:store.set_conversation_source_choices(db,identifier,sources)
    except store.AssociationUnavailable as error:raise HTTPException(503,str(error)) from None
