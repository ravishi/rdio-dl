import re
import json
import requests
from urllib import urlencode
from urlparse import urlparse, parse_qsl


class AuthorizationError(Exception):
    pass


class RdioAuthorizationSession(requests.Session):

    api_url = u'https://www.rdio.com/api/1/'

    api_version = u'20130823'

    authorization_key = None

    user_agent = (u'Mozilla/5.0 (X11; Linux i686) AppleWebKit/535.1'
                  u' (KHTML, like Gecko) Chrome/13.0.782.99 Safari/535.1')

    def __init__(self, *args, **kwargs):
        self.user_agent = kwargs.pop('user_agent', self.user_agent)
        self.api_version = kwargs.pop('api_version', self.api_version)
        self.authorization_key = kwargs.pop('authorization_key', self.authorization_key)
        super(RdioAuthorizationSession, self).__init__(*args, **kwargs)

    def request(self, method, url, **kwargs):
        headers = kwargs.pop('headers', None) or {}
        headers.setdefault('User-Agent', self.user_agent)

        resp = super(RdioAuthorizationSession, self).request(method, url,
                                                             headers=headers,
                                                             **kwargs)

        if u'Env' in resp.text:
            self.authorization_key = extract_authorization_key(resp.text)

        return resp

    def api_post(self, method, params, headers=None):

        headers = merge({
            'X-Requested-With': u'XMLHttpRequest',
            'Host': u'www.rdio.com',
            'Origin': u'https://www.rdio.com',
        }, headers or {})

        params = merge({
            'v': self.api_version,
            'method': method,
            'extras[]': u'*.WEB',
            '_authorization_key': self.authorization_key,
        }, params or {})

        return self.post(self.api_url + method, data=params, headers=headers)

    def fetch_api_version(self):
        rdio_json_url = u'http://www.rdio.com/media/fresh/now/targets/rdio.json'

        rdio_json = self.get(rdio_json_url).json()

        rdio_core_url = '/'.join([
            'http://rdio2-a.akamaihd.net/media/',
            rdio_json['scripts'][0][0],
            rdio_json['scripts'][0][1][0],
        ])

        rdio_core_page = self.get(rdio_core_url)

        return extract_api_version(rdio_core_page.text)

    def authorize_oauth_token(self, authorization_url, username, password):
        api_version = self.api_version or self.fetch_api_version()

        auth_page = self.get(authorization_url)

        oauth_token = dict(parse_qsl(urlparse(auth_page.url).query))
        oauth_token = oauth_token.get('oauth_token')

        oauth_state = self.api_post('getOAuth1State', {
            'token': oauth_token,
        }, headers={'Referer': auth_page.url}).json()

        # 491: Requires login
        if oauth_state['code'] == 491:
            login_url = u'?'.join([
                u'https://www.rdio.com/account/signin/',
                urlencode({'allowCreate': 1, 'next': auth_page.url}),
            ])

            login_page = self.get(login_url)

            login = self.api_post('signIn', {
                'username': username,
                'password': password,
                'remember': 1,
                'nextUrl': auth_page.url,
            }).json()

            if not login['status'] == u'ok':
                raise AuthorizationError(u'Invalid credentials')

            auth_page = self.get(login['result']['redirect_url'])

            oauth_state = self.api_post('getOAuth1State', {
                'token': oauth_token,
            }, headers={'Referer': auth_page.url}).json()

        if not oauth_state.get('result'):
            raise AuthorizationError(u"Failed to authorize application: `{0}'"\
                            .format(oauth_state['message']))

        oauth_verifier = oauth_state['result']['verifier']

        if not oauth_state['result']['isAuthorized']:
            approve = self.api_post('approveOAuth1App', {
                'token': oauth_token,
                'verifier': oauth_verifier,
            }, headers={'Referer': auth_page.url}).json()

            if not approve['status'] == u'ok':
                raise AuthorizationError(u"Failed to approve application.")

        return oauth_verifier


def merge(*args):
    """Merges the given dicts in reverse order.

    ::

        >>> a = {'foo': 'bar'}
        >>> b = {'foo': 'BAR', 'ham': 'SPAM'}
        >>> merge(a, b)
        ... {'foo': 'bar', 'ham': 'SPAM'}
    """
    r = {}
    for d in reversed(args):
        r.update(d)
    return r


def extract_api_version(html):
    m = re.search(r'var API_VERSION ?= ?(?P<version>20\d{6})', html)
    return m.group('version')


def extract_authorization_key(html):
    env = re.search(r'Env = {.*\n\s+};', html, flags=re.M | re.S)

    if env:
        env = env.group(0)
        env = env.replace('VERSION', '"VERSION"')\
                .replace('currentUser', '"currentUser"')\
                .replace('serverInfo', '"serverInfo"')[6:-1].strip()
        env = json.loads(env)
        return env['currentUser']['authorizationKey']

    math = re.search(r'authorizationKey *= *"(?P<authorization_key>[^"]+)";?',
                  html, flags=re.M | re.S)

    if match:
        return m.group('authorization_key')

    return None
