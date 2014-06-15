"""
Utilities to deal with a private API, which is the same one used by the
rdio.com site. Doing so allow us to call undocumented methods that aren't
allowed through the usual Rdio public API.
"""
import re
from urlparse import urljoin

import requests


def prepare_api_params(params):
    for key in list(params.keys()):
        if key.endswith('[]'):
            continue
        if isinstance(params[key], (list, tuple)):
            new_key = key + '[]'
            params[new_key] = params.pop(key)
    return params


def _extract_authorization_key(html):
    match = re.search(r'"authorizationKey"\s*:\s*"([^"]+)"', html)
    return match.group(1) if match else None


class RdioSession(requests.Session):
    API_ENDPOINT = 'https://www.rdio.com/api/1/'
    SIGN_IN_URL = 'https://www.rdio.com/account/signin/'

    _authorization_key = None

    def api_call(self, method, **kwargs):

        # TODO support 'referer'

        if not self._authorization_key:
            raise RuntimeError("Unable to call Rdio API on a unsigned session")

        params = {
            #'v': version,
            'method': method,
            '_authorization_key': self._authorization_key,
        }

        params.update(kwargs)

        params = prepare_api_params(params)

        return self.post(urljoin(self.API_ENDPOINT, method), data=params)

    def sign_in(self, username, password):
        # TODO check for errors, raise stuff

        signin_page = self.get(self.SIGN_IN_URL)
        self._authorization_key = _extract_authorization_key(signin_page.content)

        signin = self.api_call('signIn', username=username, password=password,
                               remember=1, referer=signin_page.url)

        result = signin.json().get('result')

        response = self.get(result['redirect_url'])

        self._authorization_key = _extract_authorization_key(response.content)

        return response
