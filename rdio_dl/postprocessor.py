import os
from youtube_dl.postprocessor import FFmpegMetadataPP
from youtube_dl.utils import prepend_extension, encodeFilename


class FFmpegAudioMetadataPP(FFmpegMetadataPP):
    def run(self, info):
        metadata = self._extract_metadata(info)

        if not metadata:
            self._downloader.to_screen('[ffmpeg] There isn\'t any metadata to add')
            return [], info

        filename = info['filepath']
        temp_filename = prepend_extension(filename, 'temp')

        if info['ext'] == 'm4a':
            options = ['-vn', '-acodec', 'copy']
        else:
            options = ['-c', 'copy']

        for (name, value) in metadata.items():
            options.extend(['-metadata', '%s=%s' % (name, value)])

        self._downloader.to_screen('[ffmpeg] Adding metadata to \'%s\'' % filename)
        self.run_ffmpeg(filename, temp_filename, options)
        os.remove(encodeFilename(filename))
        os.rename(encodeFilename(temp_filename), encodeFilename(filename))
        return [], info

    def _extract_metadata(self, info):
        md = {}

        if info.get('title') is not None:
            md['title'] = info['title']

        if info.get('upload_date') is not None:
            md['date'] = info['upload_date']

        if info.get('artist') is not None:
            md['artist'] = info['artist']
        elif info.get('uploader') is not None:
            md['artist'] = info['uploader']
        elif info.get('uploader_id') is not None:
            md['artist'] = info['uploader_id']

        if info.get('album') is not None:
            md['album'] = info['album']

        if info.get('album_artist') is not None:
            md['album_artist'] = info['album_artist']

        if info.get('description') is not None:
            md['description'] = info['description']
            md['comment'] = info['description']

        if info.get('webpage_url') is not None:
            md['purl'] = info['webpage_url']

        if info.get('track_number') is not None:
            md['track'] = info['track_number']

        return md
