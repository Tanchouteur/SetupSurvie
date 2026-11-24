"""Public connection card; only public host names and addresses are exposed."""
import io
import json
import os
from pathlib import Path

from fastapi import HTTPException

CATALOG=Path(os.environ.get('CATALOG_DIR','/catalog'))


def status(host):
    path=CATALOG/'network.json'
    if path.is_file() and not path.is_symlink() and path.stat().st_size<16000:
        try:
            value=json.loads(path.read_text())
            keys=('name','ip','ready','lan_enabled','http_url','https_url','direct_url','direct_https_url','warning')
            if isinstance(value,dict):return {key:value.get(key) for key in keys}
        except (ValueError,OSError):pass
    return {'name':host,'ip':host,'ready':False,'lan_enabled':False,
            'http_url':f'http://{host}:8080/','https_url':f'https://{host}:8443/',
            'direct_url':f'http://{host}:8080/','direct_https_url':f'https://{host}:8443/',
            'warning':'L’accès aux autres appareils doit être préparé sur le PC serveur.'}


def qr(value,kind):
    key={'direct':'direct_url','name':'http_url','secure':'https_url'}.get(kind)
    if key is None:raise HTTPException(400,'Type de code non valide.')
    import qrcode
    import qrcode.image.svg
    image=qrcode.make(value[key],image_factory=qrcode.image.svg.SvgPathImage,box_size=8,border=4)
    stream=io.BytesIO();image.save(stream)
    return stream.getvalue()
