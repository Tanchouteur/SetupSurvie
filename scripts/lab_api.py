"""Authenticated local WebUI client; credentials and bearer tokens stay in memory."""
import json
import urllib.request

import linux_lab as lab


class WebUI:
    def __init__(self):
        lab.checked_mount()
        _, self.config = lab.configuration()
        self.token = None
        self.opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
        result = self.request('/api/v1/auths/signin', {'email': self.config['admin_email'],
                                                     'password': self.config['admin_password']})
        self.token = result['token']

    def request(self, path, payload=None, *, data=None, content_type='application/json'):
        if payload is not None:
            data = json.dumps(payload).encode()
        headers = {'Content-Type': content_type}
        if self.token:
            headers['Authorization'] = 'Bearer ' + self.token
        req = urllib.request.Request('http://127.0.0.1:3000' + path, data=data, headers=headers)
        with self.opener.open(req, timeout=900) as response:
            return json.load(response)
