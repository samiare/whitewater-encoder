Whitewater Encoder
==================

A command line utility that converts short videos a format that can be played on mobile websites with the Whitewater Player Javascript library.

→ `Full Documentation <https://github.com/samiare/whitewater-encoder/wiki>`__

Together, `Whitewater Encoder <https://github.com/samiare/whitewater-encoder>`__ and `Whitewater
Player <https://github.com/samiare/whitewater-mobile-video>`__ give you the
ability to play inline video in mobile web browsers complete with
programatic playback controls and events.

→ `Example Site <https://samiare.github.io/whitewater-player/>`__


Installation
------------

.. code:: bash

    $ pip install whitewater


Usage
-----

.. code:: bash

    $ whitewater <file> [options]
    $ whitewater (-h | --help | --version)

**Example:**

.. code:: bash

    $ whitewater path/to/video.mp4

Options
~~~~~~~

::

    --blocksize <size>   The width/height of a single grid cell when
                         checking one frame against the previous one.
    --grid <size>        The size of the diffmap images in rows and
                         columns, not absolute pixels.
    --quality <percent>  JPEG quality setting.
    --threshold <rms>    RMS threshold for determining whether a
                         single cell of a frame is different from
                         the previous one.
    --format <filetype>  File format to save diffmap images as.

For a full explanation of what these do and when you might want to use
them, check `the documentation <https://github.com/samiare/whitewater-encoder/wiki/How It Works>`__.

Python Module
-------------

Whitewater can also be used as a module in your own Python scripts. The ``Whitewater()`` class and its options are described in detail in the `full
documentation <https://github.com/samiare/whitewater-encoder/wiki>`__.

.. code:: python

    from whitewater import Whitewater

    video = Whitewater('path/to/video.mp4')
    video.encode()