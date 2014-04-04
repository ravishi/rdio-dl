IT DOESN'T WORK
===============


Ok, **this doesn't work anymore**! And I can't update it right now. Sorry.


rdio-dl
=======


A **youtube-dl** extension that lets you download songs from Rdio.


Installation
------------


The recommended way to install it is through **pip**.

Since the current published version of **youtube-dl** does not support
external extractors, you'll have to install it from my fork:

.. code:: bash

    $ pip install -e git+https://github.com/ravishi/youtube-dl.git@extractors-entry-points#egg=youtube_dl

Then install **rdio-dl**:

.. code:: bash

    $ pip install -e git+https://github.com/ravishi/rdio-dl.git#egg=rdio_dl


Usage
-----

Simply call **youtube-dl** with your Rdio credentials and a Rdio song
url.

.. code:: bash

    $ youtube-dl -x -u <username> -p <password> "http://rd.io/x/QRmpxDdNqww/"
