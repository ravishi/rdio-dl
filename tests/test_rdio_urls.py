import pytest

from rdio_dl.extractor import RdioIE


def test_valid_urls():

    valid_urls = (
        # a track
        'http://www.rdio.com/artist/Magic!/album/Rude/track/Rude/',

        # an album
        'http://www.rdio.com/artist/Os_Mutantes/album/%22Os_Mutantes%22/',

        # a playlist
        'http://www.rdio.com/people/Billboard/playlists/5087254/Billboard_Hot_100/',

        # and of course, a short url
        'http://rd.io/x/QRmpxCJc1D4/',
    )

    for url in valid_urls:
        assert RdioIE.suitable(url)

        # also, every valid url should also work without the trailing slash
        assert RdioIE.suitable(url.rstrip('/'))

        # ...and in https form
        assert RdioIE.suitable(url.replace('http', 'https', 1))
