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

    if not env:
        return

    env = env.group(0).replace('VERSION', '"VERSION"') \
                .replace('currentUser', '"currentUser"') \
                .replace('serverInfo', '"serverInfo"')

    env = env[6:-1].strip()

    try:
        env = json.loads(env)
    except:
        return

    '''(Env.loadedTarget, {
          environment: Env,
          pathFactories: {
            css: function(file) {
              var fileName = file.file;
              if (R.supportsDataUris && file.versions.datauri) {
                fileName = fileName + '.datauri.' + file.versions.datauri;
              } else if (file.versions.fallback) {
                fileName = fileName + '.' + file.versions.fallback;
              }
              return fileName + '.css'
            }
          },
          targetBase: '/media/client/targets/e5e51c9032f627fcf958ad0e6e310ba7ff84f35b/',
          resourceBases: ['rdio0-a.akamaihd.net', 'rdio1-a.akamaihd.net', 'rdio2-a.akamaihd.net', 'rdio3-a.akamaihd.net'],
          mainOptions: {},
          dev: false,
          unstyled: rule.unstyled
        })'''

    boot = re.search(r'\(\s*Env\.loadedTarget\s*,\s*\{(.*\}\s*)\)\s*;', html, flags=re.M | re.S)

    if not boot:
        return

    boot = boot.group(0)

    targets = [line.strip().strip(u',').strip()
                for line in boot.splitlines() if u'Base' in line]

    targets = [re.sub(r'^([^:\s]+)', r'"\1"', line) for line in targets]

    targets = u'{' + (u',\n'.join(targets)) + u'}'

    targets = targets.replace("'", '"')

    env['targets'] = json.loads(targets)

    return env


def retrieve_rdio_api_version(env):
    rdio_json_url = u'/'.join(
        [u'http://www.rdio.com', env['targets']['targetBase'], u'rdio-marketing.json'])

    rdio_json = requests.get(rdio_json_url).json()

    for rb in env['targets']['resourceBases']:
        core_url = u''.join([
            u'http://',
            rb,
            env['targets']['targetBase'],
            rdio_json['scripts'][0][1][0],
        ])

        core = requests.get(core_url)

        if core.status_code == 200:
            m = re.search(r'var\s+API_VERSION\s?=\s?(?P<version>20\d{6})', core.text)

            if m is not None:
                return m.group('version')
            else:
                break


def extract_rdio_url_groups(url):
    return re.match(URL_GROUPS, url).groupdict()
