import json
import sqlite3
from os import mkdir
from os.path import dirname, exists, expanduser, mkdir
from ConfigParser import ConfigParser
from youtube_dl.utils import ExtractorError


DBPATH = u'~/.rdio-dl/session.sqlite'


def storage_load():

    path = expanduser(DBPATH)

    if not exists(dirname(path)):
        mkdir(dirname(path))

    return StateStorage(path)


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
