import re
import json
import requests


RDIO_API_ENDPOINT = u'https://www.rdio.com/api/1/'

URL_GROUPS = (r'^(?P<full>https?://(?:www\.)?rdio\.com/'
              r'(?P<track>(?P<album>(?P<artist>artist/[^\/]+/)album/[^\/]+/)track/[^\/]+/?))')


def prepare_rdio_api_params(params):
    keys = list(params.keys())
    for key in keys:
        if key.endswith(u'[]'):
            continue
        if isinstance(params[key], (list, tuple)):
            new_key = u'{0}[]'.format(key)
            params[new_key] = params.pop(key)
    return params


def rdio_api_request(method, version, authorization_key, **kwargs):
    """Create a `Request` object for the given *method* call over
    the Rdio web API. The given *version* and *authorization_key*
    will also be used. Keyword arguments will be used as parameters
    to the method call.
    """
    kwargs.update({
        'v': version,
        'method': method,
        '_authorization_key': authorization_key,
    })

    params = prepare_rdio_api_params(kwargs)

    headers = {
        'Host': u'www.rdio.com',
        'Origin': u'https://www.rdio.com',
        'X-Requested-With': u'XMLHttpRequest',
    }

    return dict(method='POST', url=RDIO_API_ENDPOINT, data=params, headers=headers)


def extract_rdio_environment(html):
    """Extract the `Env` object from the *html* content of a Rdio page
    and return it as a loaded json object.

    Also, the original first-level `VERSION` key will be lowercased during
    this process (it becomes `version`).
    """
    env = re.search(r'Env = {.*\n\s+};', html, flags=re.M | re.S)

    if env:
        env = env.group(0).replace('VERSION', '"VERSION"') \
                  .replace('currentUser', '"currentUser"') \
                  .replace('serverInfo', '"serverInfo"')
        env = env[6:-1].strip()
        return json.loads(env)

    return None


def retrieve_rdio_api_version(env):
    client_version = env['VERSION']['version']

    rdio_json_url = u'/'.join(
        [u'http://www.rdio.com/media/client/targets', client_version, u'rdio.json'])

    rdio_json = requests.get(rdio_json_url).json()

    core_url = u''.join([
        u'http://rdio0-a.akamaihd.net/media/',
        rdio_json['scripts'][0][0],
        rdio_json['scripts'][0][1][0],
    ])

    core = requests.get(core_url)

    m = re.search(r'var API_VERSION ?= ?(?P<version>20\d{6})', core.text)

    return m.group('version')


def extract_rdio_url_groups(url):
    return re.match(URL_GROUPS, url).groupdict()
