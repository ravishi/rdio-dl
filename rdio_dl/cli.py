# -*- coding: utf-8 -*-
import click
import youtube_dl

from .config import storage_load
from .extractor import RdioIE


def add_info_extractor_above_generic(ydl, ie):
    generic = ydl._ies.pop()
    ydl.add_info_extractor(ie)
    ydl.add_info_extractor(generic)


@click.command()
@click.option(u'-u', u'--user', help=u'A Rdio user')
@click.option(u'-p', u'--password', help=u'The password')
@click.option(u'-q', u'--quality',
              type=click.Choice([u'high', u'very-high']),
              default=u'high',
              help=(u'The desired quality of the song.'
                    u' high is 192kbps mp3, very-high is'
                    u' 320kbps mp4. Default is high.'))
@click.argument(u'urls', required=True, nargs=-1)
def main(user, password, urls, quality):
    storage = storage_load()
    with youtube_dl.YoutubeDL() as ydl:
        add_info_extractor_above_generic(ydl, RdioIE(storage, user, password, quality=quality))
        ydl.download(urls)
