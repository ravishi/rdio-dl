# -*- coding: utf-8 -*-
import click
import youtube_dl
from youtube_dl.postprocessor import EmbedThumbnailPP

from rdio_dl.postprocessor import FFmpegAudioMetadataPP
from .config import storage_load
from .extractor import RdioIE


def add_info_extractor_above_generic(ydl, ie):
    generic = ydl._ies.pop()
    ydl.add_info_extractor(ie)
    ydl.add_info_extractor(generic)


@click.command()
@click.option(u'-u', u'--user', help=u'A Rdio user')
@click.option(u'-p', u'--password', help=u'The password')
@click.option(u'-t', u'--quality',
              type=click.Choice([u'high', u'very-high']),
              default=u'high',
              help=(u'The desired quality of the song.'
                    u' high is 192kbps mp3, very-high is'
                    u' 320kbps m4a. Default is high.'))
@click.option(u'-i', u'--embed-thumbnail',
              flag_value=True, default=False,
              help=(u'Embed thumbnail images. This requires'
                    u' ffmpeg and AtomicParsley (only for m4a)'
                    u' to be installed.'))
@click.option(u'--ignore-errors',
              flag_value=True, default=False,
              help=(u'Continue on download errors, for example'
                    u'to skip unavailable videos in a playlist'))
@click.option(u'-v', u'--verbose', 'verbose', flag_value=True, default=False)
@click.argument(u'urls', required=True, nargs=-1)
def main(user, password, quality, embed_thumbnail, ignore_errors, verbose, urls):
    storage = storage_load()

    ydl_opts = {
        'verbose': verbose,
        'writethumbnail': embed_thumbnail,
        'ignoreerrors': ignore_errors,
    }

    if quality == u'very-high':
        ydl_opts['postprocessors'] = [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': u'best',
            'preferredquality': 0,
            'nopostoverwrites': False,
        }]

    with youtube_dl.YoutubeDL(params=ydl_opts) as ydl:
        add_info_extractor_above_generic(
            ydl, RdioIE(storage, user, password, quality=quality))
        ydl.add_post_processor(FFmpegAudioMetadataPP(ydl))
        if embed_thumbnail:
            ydl.add_post_processor(EmbedThumbnailPP(ydl))
        ydl.download(urls)
