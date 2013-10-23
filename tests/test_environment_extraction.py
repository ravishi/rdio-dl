import pytest
import requests

from rdio_dl import utils


@pytest.fixture(scope='module')
def st(request):
    return State()


class State(object):
    def require(self, attr, provider):
        if not hasattr(self, attr):
            provider(self)
        return getattr(self, attr)


def test_rdio_environment(st):
    signin = requests.get(u'http://www.rdio.com/account/signin')

    st.env = utils.extract_rdio_environment(signin.text)

    assert isinstance(st.env, dict)
    assert 'VERSION' in st.env.keys()
    assert 'version' in st.env['VERSION']


def test_rdio_api_version(st):
    env = st.require('env', test_rdio_environment)

    st.api_version = utils.retrieve_rdio_api_version(env)

    assert st.api_version.isdigit() and len(st.api_version) == 8
