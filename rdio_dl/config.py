import json
import sqlite3
from os.path import exists, expanduser
from ConfigParser import ConfigParser
from youtube_dl.utils import ExtractorError


DEFAULT_STATE_FILE = u'~/.rdio-dl/state'


class ConfigurationError(Exception):
    pass


def config_load(path):

    config = ConfigParser()
    config.read(path)

    if not 'rdio-dl' in config.sections():
        raise ConfigurationError(u"Missing `rdio-dl' section")

    config = dict(config.items('rdio-dl'))

    apikey = config.get('apikey')
    secret = config.get('secret')

    if not (apikey and secret):
        raise ConfigurationError(
            u"Required values `apikey' and `secret' are missing"
        )

    statefile = config.get('statefile', DEFAULT_STATE_FILE)

    statefile = expanduser(statefile)

    storage = StateStorage(statefile)

    return {
        'apikey': apikey,
        'secret': secret,
        'storage': storage,
    }


class StateStorage(object):
    def __init__(self, path):
        self.db = sqlite3.connect(path)

        self.db.execute("""
        create table if not exists state (
            username varchar primary key,
            state varchar
        )""")

        self.db.commit()

    def save(self, username, state):
        data = json.dumps(state)

        insert = "insert or replace into state (username, state) values (?, ?)"
        self.db.execute(insert, (username, data))

        self.db.commit()

    def load(self, username):
        select = "select state from state where username = ?"

        select = self.db.execute(select, (username,))
        data = select.fetchone()

        if data is not None:
            return json.loads(data[0])
        else:
            return None
