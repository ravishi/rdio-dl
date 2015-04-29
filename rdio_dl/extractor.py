import re
import math
import random
import requests
import requests.cookies

from youtube_dl.utils import ExtractorError
from youtube_dl.extractor.common import InfoExtractor

from .private_api import RdioSession


USER_AGENT = (u"Mozilla/5.0 (X11; Linux i686) AppleWebKit/535.1"
              u" (KHTML, like Gecko) Chrome/13.0.782.99 Safari/535.1")


def random_player_id():
    return unicode(int(math.floor(random.random() * 10000000)))


class RdioIE(InfoExtractor):
    IE_DESC = u'Rdio'

    @classmethod
    def suitable(cls, url):
        valid_urls = {
            'track': (
                r'^(?:https?://)?(?:www\.)?rdio\.com/artist/(?P<artist>[^\/]+)/'
                r'album/(?P<album>[^\/]+)/track/(?P<track>[^\/]+)/?$'
            ),
            'album': (
                r'^(?:https?://)?(?:www\.)?rdio\.com/artist/(?P<artist>[^\/]+)/'
                r'album/(?P<album>[^\/]+)/?$'
            ),
            'playlist': (
                r'^(?:https?://)?(?:www\.)?rdio\.com/people/(?P<owner>[^\/]+)/'
                r'playlists/(?P<playlist_id>[^\/]+)/'
                r'(?P<playlist_name>[^\/]+)/?$'
            ),
            'short': r'^(?:https?://)?rd\.io/x/[^\/]+/?$',
            }

        return any((re.match(test_re, url) for test_re in valid_urls.values()))

    def __init__(self, storage, username, password):
        super(RdioIE, self).__init__(self)

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

    def _get_object_from_url(self, url):
        """Get a object (track, album, playlist) from the given URL.
        """
        result = self.rdio.api_call('getObjectFromUrl', url=url,
                                    extras=['tracks'], referer=url)
        return result.json()

        if not result.get('result'):
            raise ExtractorError(result.get('message', u"Unknown error"))

        return result.get('result')

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
        obj = self._get_object_from_url(url)

        obj = obj.get('result')

        typ = obj['type']

        if typ == 't':
            return self._extract_track(obj)

        elif typ not in ('a', 'p'):
            raise ExtractorError("Unknown object type: `{0}'".format(typ))

        # deal with playlists and albums
        tracks = obj.get('tracks', [])

        # XXX sometimes the result is a list, sometimes its a dict with an
        # items item
        if isinstance(tracks, dict):
            tracks = tracks.get('items', [])

        entries = [self.url_result(t['shortUrl'], video_id=t['key'])
                   for t in tracks]

        return self.playlist_result(entries, obj['key'], obj['name'])

    def _extract_track(self, track):
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
