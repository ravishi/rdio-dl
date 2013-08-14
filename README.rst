rdio-dl
=======


A youtube-dl extension that lets you download songs from Rdio.


Usage
-----

In order to use *rdio-dl* you must have an API key and a secret for the
Rdio API.

Put that information in a file named `~/.rdio-dl/config.ini` like this:

.. code:: ini

    [rdio-dl]
    apikey = XXXXXXXXXXX
    secret = XXXXXXXXXXX


Now, just run youtube-dl with your Rdio credentials and a song URL:

.. code:: bash

    $ youtube-dl -x -u username -p password "http://rd.io/x/QRmpxDdNqww/"


Enjoy!
