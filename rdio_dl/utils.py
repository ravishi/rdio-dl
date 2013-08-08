import cgi
import urllib2
from urllib import urlencode
from contextlib import closing


# taken from kennethreitz' requests
def get_encoding_from_headers(headers):
    """Returns encodings from given HTTP Header Dict.

    :param headers: dictionary to extract encoding from.
    """

    content_type = headers.get('content-type')

    if not content_type:
        return None

    content_type, params = cgi.parse_header(content_type)

    if 'charset' in params:
        return params['charset'].strip("'\"")

    if 'text' in content_type:
        return 'ISO-8859-1'


# taken from kennethreitz' requests
def get_unicode_from_response(r):
    """Returns the requested content back in unicode.

    :param r: Response object to get unicode content from.

    Tried:

    1. charset from content-type

    2. fall back and replace all unicode characters

    """

    tried_encodings = []

    # Try charset from content-type
    encoding = get_encoding_from_headers(r.headers)

    if encoding:
        try:
            return r.content.decode(encoding)
        except UnicodeError:
            tried_encodings.append(encoding)

    # Fall back:
    try:
        return r.content.decode(encoding, errors='replace')
    except TypeError:
        return r.content


class SimplifiedOpenerDirector(urllib2.OpenerDirector):
    def fetch(url, data=None, headers=None, *args, **kwargs):
        request = urllib2.Request(url)

        if data is not None:
            request.add_data(urlencode(data.items()))

        # http headers should be encoded with latin1
        header_encoding = 'latin1'

        for k, v in (headers or {}).items():
            if isinstance(k, unicode):
                k = k.encode(header_encoding)

            if isinstance(v, unicode):
                v = v.encode(header_encoding)

            request.add_header(k, v)

        with closing(opener.open(request)) as response:
            # XXX we should preserve the read method, but w/e
            response.request = request
            response.content = response.read()
            response.text = get_unicode_from_response(response)

        return response
