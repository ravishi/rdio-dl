import re
import math
import random
import requests
import requests.cookies

from youtube_dl.utils import ExtractorError
from youtube_dl.extractor.common import InfoExtractor

from . import utils
from .config import storage_load


USER_AGENT = (u"Mozilla/5.0 (X11; Linux i686) AppleWebKit/535.1"
              u" (KHTML, like Gecko) Chrome/13.0.782.99 Safari/535.1")

SIGN_IN_URL = u"https://www.rdio.com/account/signin/"


def random_player_id():
    return unicode(int(math.floor(random.random() * 1000000)))


class RdioIE(InfoExtractor):
    IE_DESC = u'Rdio'
    _VALID_URL = r'''^(?:https?://)?(?:(?:(?:www\.)?rdio.com/
                      artist/(?P<artist>.*)/album/(?P<album>.*)/track/(?P<track>.*)/$)|(?:rd\.io/x/[-\w\d]+/$))'''

    @classmethod
    def suitable(cls, url):
        return re.match(cls._VALID_URL, url, flags=re.VERBOSE) is not None

    def _real_initialize(self):
        username = self._downloader.params.get('username')
        password = self._downloader.params.get('password')

        if not (username and password):
            raise ExtractorError(u"Please specify your Rdio credentials")

        storage = storage_load()

        user_state = storage.load(username)

        self.session = requests.Session()
        self.api_version = None

        cookies = user_state.get('cookies')
        if cookies is not None:
            self.session.cookies = requests.cookies.cookiejar_from_dict(cookies)

    def _rdio_api_call(self, method, env, referer=None, **kwargs):
        if self.api_version is None:
            self.api_version = utils.retrieve_rdio_api_version(env)

        authorization_key = env['currentUser']['authorizationKey']

        req_kwargs = utils.rdio_api_request(method, version=self.api_version,
                                            authorization_key=authorization_key, **kwargs)

        if referer is not None:
            req_kwargs.setdefault('headers', {}).update({'Referer': referer})

        response = self.session.request(**req_kwargs)

        return response.json()

    def _sign_in(self, username, password):
        signin_page = self.session.get(SIGN_IN_URL)

        env = utils.extract_rdio_environment(signin_page.text)

        signin = self._rdio_api_call('signIn', env, referer=signin_page.url,
                                     username=username, password=password, remember=1, nextUrl=u'')

        result = signin.get('result')

        if result is None:
            reason = signin.get('message', u"Unknown reason")
            raise ExtractorError(u"Failed to sign in: `{0}'".format(reason))

        if not result['success']:
            raise ExtractorError(u"Invalid credentials")

        return self.session.get(signin['result']['redirect_url'])

    def _get_track_object(self, url, env):
        """Get the track object from the given Rdio track *page*.
        """
        urls = utils.extract_rdio_url_groups(url)

        album = self._rdio_api_call('getObjectFromUrl', env, referer=url, url=urls['album'], extras=[
            '*.WEB', 'bigIcon', 'bigIcon1200', 'tracks', 'playCount', 'copyrights',
            'labels', '-Label.*', 'Label.name', 'Label.url', 'review', 'playlistCount'
        ])

        tracks = album['result']['tracks']

        # XXX sometimes the tracks are listed inside result.tracks, sometimes
        # they're inside result.tracks.items. Don't ask me why.
        if 'items' in tracks:
            tracks = tracks['items']

        for track in tracks:
            if track['url'][1:] == urls['track']:
                return track

        return None

    def _real_extract(self, url):
        track_page = self.session.get(url)

        env = utils.extract_rdio_environment(track_page.text)

        track = self._get_track_object(track_page.url, env)

        player_name = u'_web_{0}'.format(random_player_id())

        playback_info = self._rdio_api_call('getPlaybackInfo', env, key=track['key'],
                                            manualPlay=True, playerName=player_name, requiresUnlimited=False,
                                            finishedAd=False, type=u'mp3-high', extras=['*.WEB'])

        if not playback_info.get('result'):
            reason = playback_info.get('message', u"Unknown error")
            raise ExtractorError(u"Failed to get playback information: `{0}'".format(reason))

        return {
            'id': track['key'],
            'ext': u'mp3',
            'url': playback_info['result']['surl'],
            'title': track['name'],
            'uploader': track['artist'],
            'description': u'',
            'thumbnail': track['icon'],
        }
