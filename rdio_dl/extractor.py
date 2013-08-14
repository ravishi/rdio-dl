import re
import json
import math
import random
import os.path
import urllib2
import argparse
from urllib import urlencode
from urlparse import urlparse, urljoin, parse_qs
from ConfigParser import ConfigParser
from pyamf.remoting.client import RemotingService
from youtube_dl.utils import ExtractorError
from youtube_dl.extractor.common import InfoExtractor

from .auth import get_auth_verifier_and_cookies
from .rdio_simple import Rdio as RdioSimple


class ConfigurationError(ExtractorError):
    pass


class Rdio(object):
    APP_DOMAIN = 'localhost'
    AMF_ENDPOINT = 'https://www.rdio.com/api/1/amf/'
    USER_AGENT = ('Mozilla/5.0 (X11; Linux i686) AppleWebKit/535.1'
                  ' (KHTML, like Gecko) Chrome/13.0.782.99 Safari/535.1')
    RDIO_PLAYBACK_SECRET = '6JSuiNxJ2cokAK9T2yWbEOPX'
    RDIO_PLAYBACK_SECRET_SEED = 5381

    def __init__(self, consumer, state=None):
        self._state = state or {}
        self._rdio = RdioSimple(consumer, self.auth_token)

    @property
    def auth_token(self):
        return (self._state['auth_token'] if self._state else None)

    @property
    def playback_token(self):
        return (self._state['playback_token'] if self._state else None)

    @property
    def rdio_cookie(self):
        return (self._state['cookies'].get('r', None) if self._state else None)

    def getstate(self):
        return self._state.copy()

    def __getattr__(self, name):
        placeholder = object()
        delegate = getattr(self._rdio, name, placeholder)
        if delegate is not placeholder:
            return delegate
        raise AttributeError(name)

    def get_auth_verifier_and_cookies(self, *args, **kwargs):
        kwargs.setdefault('user_agent', self.USER_AGENT)
        return get_auth_verifier_and_cookies(*args, **kwargs)

    def authenticate(self, username, password):
        auth_url = self._rdio.begin_authentication('oob')

        verifier, cookies = self.get_auth_verifier_and_cookies(
                                                auth_url, username, password)

        self._rdio.complete_authentication(verifier)

        playback_token = self.call('getPlaybackToken',
                                   dict(domain=self.APP_DOMAIN))['result']

        self._state = {
            'cookies': cookies,
            'auth_token': self._rdio.token,
            'playback_token': playback_token,
        }

    def is_authenticated(self):
        return (self._state and self._state.get('auth_token')
                and self._state.get('playback_token'))

    def get_playback_info(self, key):
        svc = RemotingService(self.AMF_ENDPOINT,
                              amf_version=0,
                              user_agent=self.USER_AGENT)

        svc.addHTTPHeader('Cookie', 'r=' + self.rdio_cookie)
        svc.addHTTPHeader('Host', 'www.rdio.com')

        rdio_svc = svc.getService('rdio')

        secret_string = key + self.playback_token + self.RDIO_PLAYBACK_SECRET
        secret = self.RDIO_PLAYBACK_SECRET_SEED

        for c in secret_string:
            secret = ((secret << 5) + secret + ord(c)) % 65536;

        playerName = 'api_%s' % str(int(math.floor(random.random() * 1000000)))

        return rdio_svc.getPlaybackInfo({
            'domain': self.APP_DOMAIN,
            'playbackToken': self.playback_token,
            'manualPlay': False,
            'requiresUnlimited': False,
            'playerName': playerName,
            'type': 'flash',
            'secret': secret,
            'key': key
        })


class RdioInfoExtractor(InfoExtractor):
    def __init__(self, *args, **kwargs):
        super(RdioInfoExtractor, self).__init__(*args, **kwargs)

        self._config = None
        self._rdio = None

    def _load_config_and_state(self):
        config_path = os.path.expanduser('~/.rdio-dl/config.ini')

        config = ConfigParser()
        config.read(config_path)

        if not 'rdio-dl' in config.sections():
            raise ConfigurationError("The `rdio-dl' section is missing")

        self._config = dict(config.items('rdio-dl'))

        apikey = self._config.get('apikey')
        secret = self._config.get('secret')

        if not (apikey and secret):
            raise ConfigurationError(
                "The required values `apikey' and `secret' are missing"
            )

        state_path = os.path.expanduser('~/.rdio-dl/state.json')

        try:
            with open(state_path) as state_file:
                state = json.loads(state_file.read())
            access_token = state.get('access_token', None)
        except IOError:
            state = None
            access_token = None

        self._rdio = Rdio((apikey, secret), state=state)

        username = self._downloader.params.get('username')
        password = self._downloader.params.get('password')

        if not username:
            username = self._config.get('username')
        if not password:
            password = self._config.get('password')

        if not (username and password):
            raise ExtractorError("No username and password specified")

        if not self._rdio.is_authenticated():
            self._rdio.authenticate(username, password)

            state = self._rdio.getstate()

            with open(state_path, 'w') as state_file:
                new_state = json.dumps(state, sort_keys=True,
                                       indent=4, separators=(',', ': '))
                state_file.write(new_state)

    def _prepare_for_extraction(self):
        if not self._rdio:
            self._load_config_and_state()


class RdioIE(RdioInfoExtractor):
    IE_DESC = u'Rdio'
    _VALID_URL = r'''^(?:https?://)?
                      (?:(?:(?:www\.)?rdio.com/artist/(?P<artist>.*)
                          /album/(?P<album>.*)/track/(?P<track>.*)/$)
                       |(?:rd.io/x/[\w\d-]+/$))'''

    @classmethod
    def suitable(cls, url):
        return re.match(cls._VALID_URL, url, flags=re.VERBOSE) is not None

    def _real_extract(self, url):
        self._prepare_for_extraction()

        obj = self._rdio.call('getObjectFromUrl', dict(url=url))

        if not (obj['status'] == u'ok' and obj['result']['type'] == u't'):
            raise ExtractorError(u'Failed to retrieve a Rdio track from'
                                 u' the given URL')

        key = obj['result']['key']
        pi = self._rdio.get_playback_info(key)

        if not pi:
            raise ExtractorError(u'Failed to get playback info from the given'
                                 u' Rdio track URL')

        app = pi['streamApp'][1:]
        url = 'rtmpe://{streamHost}:1935{streamApp}'.format(**pi)
        play_path = u':'.join(['mp3', pi['surl']])

        return {
            'id': 1,
            'url': url,
            'play_path': play_path,
            'app': app,
            'title': 'Dummy',
            'description': 'Dummy',
            'thumbnail': 'dummy.jpg',
            'ext': 'flv',
        }
