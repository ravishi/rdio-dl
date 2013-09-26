import re
import json
import requests
from urllib import urlencode
from urlparse import urlparse, parse_qsl


class AuthorizationError(Exception):
    pass


class RdioSession(requests.Session):

    user_agent = (u'Mozilla/5.0 (X11; Linux i686) AppleWebKit/535.1'
                  u' (KHTML, like Gecko) Chrome/13.0.782.99 Safari/535.1')

    api_url = u'https://www.rdio.com/api/1/'
    api_version = None

    def __init__(self, *args, **kwargs):
        self.user_agent = kwargs.pop('user_agent', self.user_agent)
        self.api_url = kwargs.pop('api_url', self.api_url)
        self.api_version = kwargs.pop('api_version', self.api_version)

        self.env = kwargs.pop('env', None)
        self.authorization_key = kwargs.pop('authorization_key', None)

        super(RdioSession, self).__init__(*args, **kwargs)

    def request(self, method, url, **kwargs):
        headers = kwargs.pop('headers', None) or {}
        headers.setdefault('User-Agent', self.user_agent)

        resp = super(RdioSession, self)\
                .request(method, url, headers=headers, **kwargs)

        if u'://www.rdio.com' in resp.request.url and u'Env' in resp.text:
            self.env = extract_env(resp.text)
            self.authorization_key = self.env['currentUser']['authorizationKey']

        return resp

    def api_post(self, method, params, headers=None):
        default_params = {
            'v': self.api_version,
            'method': method,
            '_authorization_key': self.authorization_key,
        }

        default_headers = {
            'X-Requested-With': u'XMLHttpRequest',
            'Host': u'www.rdio.com',
            'Origin': u'https://www.rdio.com',
        }

        url = self.api_url + method

        params = merge(default_params, params)
        headers = merge(default_headers, headers)

        return self.post(url, data=params, headers=headers)

    def authorize_oauth_token(self, authorization_url, username, password):
        auth_page = self.get(authorization_url)

        api_version = self.api_version

        if not api_version:
            api_version = fetch_api_version(self.env['version']['version'])
            self.api_version = api_version

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


def extract_env(html):
    env = re.search(r'Env = {.*\n\s+};', html, flags=re.M | re.S)

    if env:
        env = env.group(0).replace('VERSION', '"version"')\
                .replace('currentUser', '"currentUser"')\
                .replace('serverInfo', '"serverInfo"')[6:-1].strip()

        return json.loads(env)

    else:
        return None


def extract_api_version(html):
    m = re.search(r'var API_VERSION ?= ?(?P<version>20\d{6})', html)
    return m.group('version')


def fetch_api_version(version):
    rdio_json_url = u'/'.join(
        [u'http://www.rdio.com/media/client/targets', version, u'rdio.json'])

    rdio_json = requests.get(rdio_json_url).json()

    rdio_core_url = u''.join([
        u'http://rdio0-a.akamaihd.net/media/',
        rdio_json['scripts'][0][0],
        rdio_json['scripts'][0][1][0],
    ])

    rdio_core_page = requests.get(rdio_core_url)

    return extract_api_version(rdio_core_page.text)
