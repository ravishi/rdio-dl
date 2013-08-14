import re
import json
import urllib2
from urllib import urlencode
from urlparse import urlparse, parse_qs

from .utils import merge
from .utils import SimplifiedOpenerDirectorWrapper


class InvalidCredentials(Exception):
    pass


class ApprovalError(Exception):
    pass


def extract_api_version(html):
    # we're searching for something like
    # function b(){this.url="/api/1/"}var c=20130730
    m = re.search(
        r'var c ?= ?20(?P<version>\d{6})',
        html,
    )
    return m.group('version')


def extract_authorization_key(html):
    env = re.search('Env = {.*\n\s+};', html, flags=re.M | re.S)
    if env:
        env = env.group(0)
        env = env.replace('VERSION', '"VERSION"')\
                .replace('currentUser', '"currentUser"')\
                .replace('serverInfo', '"serverInfo"')[6:-1].strip()
        env = json.loads(env)
        return env['currentUser']['authorizationKey']

    m = re.search(r'authorizationKey *= *"(?P<authorization_key>[^"]+)";?', html, flags=re.M | re.S)
    if m:
        return m.group('authorization_key')


def fetch_api_version(opener):
    # extract API version
    rdio_json_url = 'http://www.rdio.com/media/fresh/now/targets/rdio.json'

    rdio_json = opener.get(rdio_json_url)
    rdio_json = json.loads(rdio_json.text)

    rdio_core_url = '/'.join([
        'http://rdio2-a.akamaihd.net/media/',
        rdio_json['scripts'][0][0],
        rdio_json['scripts'][0][1][0],
    ])

    rdio_core_page = opener.get(rdio_core_url)

    return extract_api_version(rdio_core_page.text)


def _api_call(opener, method, params, headers=None):
    params.setdefault('method', method)

    headers = merge({
        'X-Requested-With': 'XMLHttpRequest',
        'Host': 'www.rdio.com',
        'Origin': 'https://www.rdio.com',
    }, headers or {})

    url = 'https://www.rdio.com/api/1/' + method

    return opener.post(url, data=params, headers=headers)


def get_auth_verifier_and_cookies(auth_url, username, password, user_agent):
    opener = urllib2.build_opener()
    opener = SimplifiedOpenerDirectorWrapper(opener)

    auth_page = opener.get(auth_url)

    version = fetch_api_version(opener)

    def apicall(method, **kwargs):
        referer = kwargs.pop('referer', None)

        headers = {
            'User-Agent': user_agent,
        }

        if referer:
            headers['Referer'] = referer

        params = merge({
            'extras[]': '*.WEB',
            'method': method,
            'v': version,
        }, kwargs)

        return _api_call(opener, method, params, headers=headers)

    oauth_token = parse_qs(urlparse(auth_page.url).query)['oauth_token'][0]

    akey = extract_authorization_key(auth_page.text)
    oauth_state = apicall('getOAuth1State',
                            token=oauth_token,
                            referer=auth_page.url,
                            _authorization_key=akey)

    oauth_state = json.loads(oauth_state.text)

    # 491: Requires login
    if oauth_state['code'] == 491:
        login_url = u'?'.join([
            'https://www.rdio.com/account/signin/',
            urlencode({'allowCreate': 1, 'next': auth_page.url}),
        ])

        login_page = opener.get(login_url)

        akey = extract_authorization_key(login_page.text)
        login = apicall('signIn',
                        username=username,
                        password=password,
                        remember=1,
                        nextUrl=auth_page.url,
                        _authorization_key=akey)

        login = json.loads(login.text)

        if not login['status'] == u'ok':
            raise InvalidCredentials()

        auth_page = opener.get(login['result']['redirect_url'])

        akey = extract_authorization_key(auth_page.text)
        oauth_state = apicall('getOAuth1State',
                                token=oauth_token,
                                referer=auth_page.url,
                                _authorization_key=akey)

        oauth_state = json.loads(oauth_state.text)

    if not oauth_state.get('result'):
        raise RuntimeError('Failed to authenticate')

    verifier = oauth_state['result']['verifier']

    if not oauth_state['result']['isAuthorized']:
        approve = apicall('approveOAuth1App',
                            token=oauth_token,
                            verifier=verifier,
                            referer=auth_page.url)

        approve = json.loads(approve.text)

        if not approve['status'] == 'ok':
            raise ApprovalError()

    return verifier, dict(session.cookies)
