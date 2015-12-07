import eyed3
import eyed3.id3.tag
from youtube_dl.postprocessor.common import PostProcessor


class EyeD3PostProcessor(PostProcessor):
    def run(self, info):
        md = dict()

        if info.get('title') is not None:
            md['title'] = info['title']

        if info.get('artist') is not None:
            md['artist'] = info['artist']
        elif info.get('uploader') is not None:
            md['artist'] = info['uploader']

        if info.get('album_artist') is not None:
            md['album_artist'] = info['album_artist']

        if info.get('album') is not None:
            md['album'] = info['album']

        if info.get('track_number') is not None:
            md['track_num'] = info['track_number']

        if not md:
            self._log(u"There isn't any metadata to fill")
            return [], info

        filename = info['filepath']

        audio_file = eyed3.load(filename)

        if not audio_file:
            self._log(u"Unsupported file format: skipping metadata")
            return [], info

        audio_file.tag = eyed3.id3.tag.Tag()

        for (key, value) in md.items():
            setattr(audio_file.tag, key, value)

        self._log(u'Adding metadata to `{0}\''.format(filename))

        audio_file.tag.save(filename)

        return [], info

    def _log(self, msg):
        self._downloader.to_screen(u'[eyed3] {0}'.format(msg))
