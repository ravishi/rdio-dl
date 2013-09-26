import pytest
import requests

from rdio_dl.session import extract_env, fetch_api_version


@pytest.fixture(scope='module')
def st(request):
    return State()


class State(object):
    def require(self, attr, provider):
        if not hasattr(self, attr):
            provider(self)
        return getattr(self, attr)


def test_extract_env(st):
    signin = requests.get(u'http://www.rdio.com/account/signin')

    st.env = extract_env(signin.text)

    assert isinstance(st.env, dict)
    assert 'version' in st.env.keys()


def test_extract_api_version(st):
    env = st.require('env', test_extract_env)

    st.api_version = fetch_api_version(env['version']['version'])

    assert st.api_version.isdigit() and len(st.api_version) == 8
