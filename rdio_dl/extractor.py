import re
import math
import random
from os.path import expanduser

from pyamf.remoting.client import RemotingService

from youtube_dl.utils import ExtractorError
from youtube_dl.extractor.common import InfoExtractor

from .oauth import RdioOAuth1Session
from .config import config_load
from .authorization import RdioAuthorizationSession


RDIO_HOST = u'www.rdio.com'

RDIO_PLAYBACK_SECRET = u'6JSuiNxJ2cokAK9T2yWbEOPX'

RDIO_PLAYBACK_SECRET_SEED = 5381

AMF_ENDPOINT = u'https://www.rdio.com/api/1/amf/'


class RdioIE(InfoExtractor):
    IE_DESC = u'Rdio'
    _VALID_URL = r'''^(?:https?://)?
                      (?:(?:(?:www\.)?rdio.com/artist/(?P<artist>.*)
                          /album/(?P<album>.*)/track/(?P<track>.*)/$)
                       |(?:rd.io/x/[\w\d-]+/$))'''

    CONFIG_FILE = expanduser(u'~/.rdio-dl/config.ini')

    APP_DOMAIN = u'localhost'

    @classmethod
    def suitable(cls, url):
        return re.match(cls._VALID_URL, url, flags=re.VERBOSE) is not None

    def get_param(self, param, default=None):
        return self._downloader.params.get(param, default)

    def _get_playback_information(self, key):
        secret_string = key + self.playback_token + RDIO_PLAYBACK_SECRET
        secret = RDIO_PLAYBACK_SECRET_SEED

        for c in secret_string:
            secret = ((secret << 5) + secret + ord(c)) % 65536;

        player_id = unicode(int(math.floor(random.random() * 1000000)))
        player_name = u'api_{0}'.format(player_id)

        params = {
            'key': key,
            'secret': secret,
            'domain': self.APP_DOMAIN,
            'playerName': player_name,
            'playbackToken': self.playback_token,
            'requiresUnlimited': False,
            'manualPlay': False,
            'type': u'flash',
        }

        # PyAMF can't deal with unicode
        for (k, v) in params.items():
            if isinstance(v, unicode):
                params[k] = v.encode('utf-8')

        return self.remoting_service.getPlaybackInfo(params)

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

        if state is not None:
            self.oauth.set_access_token(state.get('access_token'))
            self.session.cookies = state.get('cookies', {})
            self.playback_token = state.get('playback_token')

        else:
            token = self.oauth.fetch_request_token()

            login_url = token.pop('login_url')

            authorization_url = self.oauth.authorization_url(login_url)

            verifier = self.session\
                    .authorize_oauth_token(authorization_url, username, password)

            self.oauth.set_authorization_pin(verifier)

            self.oauth.fetch_access_token()

            params = dict(domain=self.APP_DOMAIN)

            get_playback_token = \
                    self.oauth.api_post('getPlaybackToken', params=params)

            self.playback_token = get_playback_token.json().get('result')

        svc = RemotingService(AMF_ENDPOINT.encode('utf-8'),
                              amf_version=0,
                              user_agent=self.session.user_agent,)

        rdio_cookie = self.session.cookies.get('r')

        svc.addHTTPHeader('Cookie', 'r=' + rdio_cookie.encode('utf-8'))
        svc.addHTTPHeader('Host', RDIO_HOST.encode('utf-8'))

        self.remoting_service = svc.getService('rdio')

        config['storage'].save(username, {
            'cookies': dict(self.session.cookies),
            'access_token': self.oauth.get_access_token(),
            'playback_token': self.playback_token,
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

        playback_info = self._get_playback_information(track['key'])

        if not playback_info:
            raise ExtractorError(u"Failed to get playback information")

        app = playback_info['streamApp'][1:]
        url = u'rtmpe://{streamHost}:1935{streamApp}'.format(**playback_info)
        play_path = u':'.join(['mp3', playback_info['surl']])

        return {
            'id': track['key'],
            'url': url,
            'play_path': play_path,
            'app': app,
            'title': track['name'],
            'uploader': track['artist'],
            'description': u'',
            'thumbnail': track['icon'],
            'ext': 'flv',
        }
