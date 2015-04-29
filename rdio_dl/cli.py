import click
import youtube_dl

from .config import storage_load
from .extractor import RdioIE

@click.command()
@click.option(u'-u', u'--user', help=u'A Rdio user')
@click.option(u'-p', u'--password', help=u'The password')
@click.argument(u'urls', required=True, nargs=-1)
def main(user, password, urls):
    storage = storage_load()
    with youtube_dl.YoutubeDL() as ydl:
        ydl.add_info_extractor(RdioIE(storage, user, password))
        ydl.download(urls)
