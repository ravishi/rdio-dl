import re
import math
import random
import requests
import requests.cookies

from youtube_dl.utils import ExtractorError
from youtube_dl.extractor.common import InfoExtractor

from .config import storage_load
from .private_api import RdioSession


USER_AGENT = (u"Mozilla/5.0 (X11; Linux i686) AppleWebKit/535.1"
              u" (KHTML, like Gecko) Chrome/13.0.782.99 Safari/535.1")

URL_GROUPS = (r'^(?P<full>https?://(?:www\.)?rdio\.com/'
              r'(?P<track>(?P<album>(?P<artist>artist/[^\/]+/)album/[^\/]+/)track/[^\/]+/?))')


def extract_rdio_url_groups(url):
    return re.match(URL_GROUPS, url).groupdict()


def random_player_id():
    return unicode(int(math.floor(random.random() * 10000000)))


class BaseRdioIE(InfoExtractor):

    def _real_initialize(self):
        username = self._downloader.params.get('username')
        password = self._downloader.params.get('password')

        if not (username and password):
            raise ExtractorError(u"Please specify your Rdio credentials")

        storage = storage_load()

        user_state = storage.load(username)

        self.rdio = RdioSession()

        if user_state:
            self.rdio._authorization_key = user_state.get('authorization_key')

            cookies = user_state.get('cookies', {})
            self.rdio.cookies = requests.cookies.cookiejar_from_dict(cookies)

        if not self.rdio._authorization_key:
            self.rdio.sign_in(username, password)

            storage.save(username, {
                'cookies': dict(self.rdio.cookies),
                'authorization_key': self.rdio._authorization_key,
            })


class RdioIE(BaseRdioIE):
    IE_DESC = u'Rdio'
    _VALID_URL = r'''^(?:https?://)?(?:(?:(?:www\.)?rdio.com/
                      artist/(?P<artist>.*)/album/(?P<album>.*)/track/(?P<track>.*)/$)|(?:rd\.io/x/[-\w\d]+/$))'''

    @classmethod
    def suitable(cls, url):
        return re.match(cls._VALID_URL, url, flags=re.VERBOSE) is not None

    def _get_track_object(self, url):
        """Get the track object from the given Rdio track *page*.
        """
        urls = extract_rdio_url_groups(url)

        album = self.rdio.api_call('getObjectFromUrl', url=urls['album'],
                                   extras=['tracks'], referer=url)

        album = album.json()

        if not album.get('result'):
            return

        tracks = album['result'].get('tracks', [])

        # XXX sometimes tracks are listed inside `result.tracks`, while
        # sometimes they are listd inside `result.tracks.items`
        if isinstance(tracks, dict):
            tracks = tracks.get('items', [])

        for track in tracks:
            if track['url'][1:] == urls['track']:
                return track

    def _get_playback_info_through_http(self, key):
        player_name = '_web_{0}'.format(random_player_id())

        playback_info = self.rdio.api_call('getPlaybackInfo',
                                           key=key,
                                           manualPlay=False,
                                           playerName=player_name,
                                           requiresUnlimited=False,
                                           finishedAd=False,
                                           type='mp3-high')

        playback_info = playback_info.json()

        if not playback_info.get('result'):
            reason = playback_info.get('message', "Unknown error")
            raise ExtractorError(
                "Failed to get playback information: `{0}'".format(reason))

        return dict(url=playback_info['result']['surl'])

    def _real_extract(self, url):
        track_page = self.rdio.get(url)

        track = self._get_track_object(track_page.url)

        info = {
            'id': track['key'],
            'ext': u'mp3',
            'title': track['name'],
            'uploader': track['artist'],
            'description': u'',
            'thumbnail': track['icon'],
        }

        playback_info = self._get_playback_info_through_http(track['key'])

        info.update(playback_info)

        return info


class RdioPlaylistIE(BaseRdioIE):
    IE_DESC = u'Rdio Playlist'
    _VALID_URL = r'''^(?:https?://)?(?:www\.)?rdio.com/people/(?P<owner>.*)/playlists/(?P<playlist_id>.*)/(?P<title>.*)/?$'''

    def _real_extract(self, url):
        playlist = self.rdio.api_call('getObjectFromUrl', url=url,
                                      extras=['tracks'])

        playlist = playlist.json()['result']

        tracks = playlist.get('tracks', [])

        if isinstance(tracks, dict):
            tracks = tracks.get('items', [])

        entries = [self.url_result(t['shortUrl'], video_id=t['key'])
                   for t in tracks]

        return self.playlist_result(entries, playlist['key'], playlist['name'])
