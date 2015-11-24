rdio-dl
=======


**rdio-dl** download songs from Rdio_.


WARNING
-------


This program is based on unofficial and undocumented methods and APIs.
This means it can stop working any time. Last time I heard it was working,
but I have no means of testing it right now.


Installation
------------


The recommended way to install it is through **pip**:

.. code:: bash

    $ pip install 'git+https://github.com/ravishi/rdio-dl.git#egg=rdio_dl'


Usage
-----

Simply call **rdio-dl** with your Rdio_ credentials and Rdio_ URLs. They can
be either songs, albums or playlists.

.. code:: bash

    $ rdio-dl -u <username> -p <password> "http://rd.io/x/QRmpxDdNqww/"


For more information, ask for help:

.. code:: bash
    
    $ rdio-dl --help


.. _Rdio: https://rdio.com/
