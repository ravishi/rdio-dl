import re
import math
import random
import time

from os.path import expanduser

from youtube_dl.utils import ExtractorError
from youtube_dl.extractor.common import InfoExtractor

from .config import storage_load
from .session import RdioSession


API_VERSION_EXPIRATION = 24 * 3600       # should last for one day


def random_player_id():
    return unicode(int(math.floor(random.random() * 1000000)))


def retrieve_api_version_if_not_expired(state,
                                        expiration=API_VERSION_EXPIRATION):
    timestamp = state.get('api_version_timestamp')

    if not timestamp:
        return

    if time.time() < (timestamp + expiration):
        return state.get('api_version')

    return None


class RdioIE(InfoExtractor):
    IE_DESC = u'Rdio'
    _VALID_URL = r'''^(?:https?://)?
                      (?:(?:(?:www\.)?rdio.com/artist/(?P<artist>.*)
                          /album/(?P<album>.*)/track/(?P<track>.*)/$)
                       |(?:rd.io/x/[\w\d-]+/$))'''

    URLINFO = r'(?P<full>https?://(?:www\.)?rdio\.com/(?P<track>(?P<album>(?P<artist>artist/[^\/]+/)album/[^\/]+/)track/[^\/]+/?))'

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

        storage = storage_load()

        state = storage.load(username)

        if state is not None:
            self.session = RdioSession(
                cookies=state.get('cookies', {}),
                api_version=retrieve_api_version_if_not_expired(state),
            )
        else:
            self.session = RdioSession()
            self.session.signin(username, password)

        storage.save(username, {
            'cookies': dict(self.session.cookies),
            'api_version': self.session.api_version,
            'api_version_timestamp': time.time(),
        })

    def _real_extract(self, url):
        # short urls will end in redirect to the right page
        # this will also update the authorization key of the session
        album_page = self.session.get(url)

        urlinfo = re.match(self.URLINFO, album_page.url)

        album = self.session.api_post('getObjectFromUrl', {
            'url': urlinfo.group('album'),
            'extras[]': ['*.WEB', 'bigIcon', 'bigIcon1200', 'tracks',
                         'playCount', 'copyrights', 'labels', '-Label.*',
                         'Label.name', 'Label.url', 'review', 'playlistCount'],
        }, headers={'Referer': album_page.url}).json()

        # XXX seems like this is not consistent? sometimes tracks has an
        # 'items' list, sometimes not. weird.
        tracks = album['result']['tracks']
        if 'items' in tracks:
            tracks = tracks['items']

        for track in tracks:
            if track['url'][1:] == urlinfo.group('track'):
                break

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
