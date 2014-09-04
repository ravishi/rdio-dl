rdio-dl
=======


A **youtube-dl** extension that lets you download songs from Rdio.


Installation
------------


The recommended way to install it is through **pip**.

Since the current published version of **youtube-dl** does not support
external extractors, a forked version must be installed.

.. code:: bash

    $ pip install 'git+https://github.com/ravishi/youtube-dl.git@extractors-entry-points#egg=youtube_dl'
    $ pip install 'git+https://github.com/ravishi/rdio-dl.git#egg=rdio_dl'


Usage
-----

Simply call **youtube-dl** with your Rdio credentials and a Rdio song url.

.. code:: bash

    $ youtube-dl -u <username> -p <password> "http://rd.io/x/QRmpxDdNqww/"
