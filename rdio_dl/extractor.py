import re
import math
import random
from os.path import expanduser

from youtube_dl.utils import ExtractorError
from youtube_dl.extractor.common import InfoExtractor

from .oauth import RdioOAuth1Session
from .config import config_load
from .authorization import RdioAuthorizationSession

from requests.cookies import cookiejar_from_dict


RDIO_HOST = u'www.rdio.com'

RDIO_PLAYBACK_SECRET = u'6JSuiNxJ2cokAK9T2yWbEOPX'

RDIO_PLAYBACK_SECRET_SEED = 5381

AMF_ENDPOINT = u'https://www.rdio.com/api/1/amf/'


def random_player_id():
    return unicode(int(math.floor(random.random() * 1000000)))[:6]


class RdioIE(InfoExtractor):
    IE_DESC = u'Rdio'
    _VALID_URL = r'''^(?:https?://)?
                      (?:(?:(?:www\.)?rdio.com/artist/(?P<artist>.*)
                          /album/(?P<album>.*)/track/(?P<track>.*)/$)
                       |(?:rd.io/x/[\w\d-]+/$))'''

    CONFIG_FILE = expanduser(u'~/.rdio-dl/config.ini')

    @classmethod
    def suitable(cls, url):
        return re.match(cls._VALID_URL, url, flags=re.VERBOSE) is not None

    def get_param(self, param, default=None):
        return self._downloader.params.get(param, default)

    def _real_initialize(self):
        username = self.get_param('username')
        password = self.get_param('password')

        if not (username and password):
            raise ExtractorError(u"Please specify a username and password pair")

        config = config_load(self.CONFIG_FILE)

        self.oauth = RdioOAuth1Session(client_key=config['apikey'],
                                       client_secret=config['secret'],
                                       callback_uri='oob')
        self.session = RdioAuthorizationSession()

        state = config['storage'].load(username)
        state = None

        if state is not None:
            self.oauth.set_access_token(state.get('access_token'))

            cookies = state.get('cookies', {})
            self.session.cookies = cookiejar_from_dict(cookies)

        else:
            token = self.oauth.fetch_request_token()

            login_url = token.pop('login_url')

            authorization_url = self.oauth.authorization_url(login_url)

            verifier = self.session\
                    .authorize_oauth_token(authorization_url, username, password)

            self.oauth.set_authorization_pin(verifier)

            self.oauth.fetch_access_token()

        # update the authorization_key
        self.session.get(u'http://www.rdio.com')

        config['storage'].save(username, {
            'cookies': dict(self.session.cookies),
            'access_token': self.oauth.get_access_token(),
        })

    def _real_extract(self, url):
        params = dict(url=url)
        get_object = self.oauth.api_post('getObjectFromUrl', params=params)
        get_object = get_object.json()

        if not (get_object.get('status') == u'ok'):
            message = get_object.get('message', '')
            if message:
                message = u": `{0}'".format(message)
            raise ExtractorError(u"Failed to retrieve a Rdio track from the"
                                 u" given url" + message)

        track = get_object['result']

        player_name = u'_web_{0}'.format(random_player_id())

        playback_info = self.session.api_post('getPlaybackInfo', {
            'key': track['key'],
            'manualPlay': False,
            'playerName': player_name,
            'requiresUnlimited': False,
            'finishedAd': False,
            'type': u'mp3-high',
        }).json()

        if not playback_info.get('result'):
            reason = playback_info.get('message', u"Unknown error")
            raise ExtractorError(
                u"Failed to get playback information: `{0}'".format(reason))

        return {
            'id': track['key'],
            'title': track['name'],
            'uploader': track['artist'],
            'description': u'',
            'thumbnail': track['icon'],
            'ext': 'mp3',
            'url': playback_info['result']['surl'],
        }
