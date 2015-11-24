rdio-dl
=======


**rdio-dl** download songs from Rdio_.


WARNING
-------

Some people have reported that **this is not working anymore.** The download method used here is based on
a lot of unnoficial and undocummented stuff, so it has to be updated constatly to keep up with Rdio
updates. I am not using Rdio anymore, so it's hard for me to try to fix it right now. If you're interested
in fixing it you can drop me an e-mail and I'll be glad to help.


Installation
------------


The recommended way to install it is through **pip**:

.. code:: bash

    $ pip install 'git+https://github.com/ravishi/rdio-dl.git#egg=rdio_dl'


Usage
-----

Simply call **rdio-dl** with your Rdio_ credentials and some song URLs.

.. code:: bash

    $ rdio-dl -u <username> -p <password> http://rd.io/x/QRmpxDdNqww/


For more information, ask for help:

.. code:: bash
    
    $ rdio-dl --help


.. _Rdio: https://rdio.com/
