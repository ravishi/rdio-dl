# -*- coding: utf-8 -*-
import click
import youtube_dl

from rdio_dl.postprocessor import EyeD3PostProcessor
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
                    u' 320kbps mp4. Default is high.'))
@click.option(u'-v', u'--verbose', 'verbose', flag_value=True, default=False)
@click.argument(u'urls', required=True, nargs=-1)
def main(user, password, urls, quality, verbose):
    storage = storage_load()

    ydl_opts = {
        'verbose': verbose,
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
        ydl.add_post_processor(EyeD3PostProcessor())
        ydl.download(urls)
