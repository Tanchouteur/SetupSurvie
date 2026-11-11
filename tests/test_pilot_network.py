import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import xml.etree.ElementTree as ET

from fastapi import HTTPException
from pilot import network


class ConnectionCardTests(unittest.TestCase):
    def test_public_status_and_qr_only_expose_connection_fields(self):
        with tempfile.TemporaryDirectory() as root,patch.object(network,'CATALOG',Path(root)):
            fallback=network.status('localhost');self.assertFalse(fallback['lan_enabled'])
            (Path(root)/'network.json').write_text(json.dumps({'name':'survie.local','http_url':'http://survie.local:8080/','direct_url':'http://192.168.1.50:8080/','https_url':'https://survie.local:8443/','ready':True,'lan_enabled':True,'secret':'never expose'}))
            value=network.status('localhost');self.assertNotIn('secret',value);self.assertTrue(value['ready'])
            raw=network.qr(value,'direct');svg=ET.fromstring(raw)
            self.assertTrue(svg.tag.endswith('svg'));self.assertGreater(len(raw),1000)
            with self.assertRaises(HTTPException):network.qr(value,'http://external.example/')


if __name__=='__main__':unittest.main()
