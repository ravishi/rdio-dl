rdio-dl
=======


A **youtube-dl** extension that lets you download songs from Rdio.


WARNING
-------

Some people have reported that **this is not working anymore.** The download method used here is based on
a lot of unnoficial and undocummented stuff, so it has to be updated constatly to keep up with Rdio
updates. I am not using Rdio anymore, so it's hard for me to try to fix it right now. If you're interested
in fixing it you can drop me an e-mail and I'll be glad to help.


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
