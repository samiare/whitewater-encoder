# Whitewater Encoder

A command line utility that converts short videos into the Whitewater format.

## Description

Together, Whitewater Encoder and [Whitewater Player](https://github.com/samiare/whitewater-player) give you the ability to play inline video in mobile web browsers complete with programatic playback controls and events.

# Installation

## From [PyPI](http://pypi.python.org)

```bash
$ pip install whitewater
```

## Manual installation

[Download the package](https://github.com/samiare/whitewater-encoder/releases/latest) and run the setup script:

```bash
$ cd path/to/module
$ python setup.py install
```

# Usage

## Command Line

The Whitewater package contains a simple command line interface.

```bash
$ whitewater <file> [options]
$ whitewater (-h | --help | --version)
```

**Basic Example**

```bash
$ whitewater path/to/video.mp4
```

### Options

The script can take a handful of options:

```
--blocksize <size>   The width/height of a single grid cell when
                     checking one frame against the previous one.
--grid <size>        The size of the diffmap images in rows and
                     columns, not absolute pixels.
--quality <percent>  JPEG quality setting.
--threshold <rms>    RMS threshold for determining whether a
                     single cell of a frame is different from
                     the previous one.
--format <filetype>  File format to save diffmap images as.
```

For a full explanation of what these do and when you might want to use them, check [the documentation](https://github.com/samiare/whitewater-encoder/wiki/Appendix#how-the-encoder-works).

## Python Module

Whitewater can also be used as a module in your own Python scripts. The `Whitewater()` class and its options are described in detail in the [full documentation](https://github.com/samiare/whitewater-encoder/wiki).

```python
from whitewater import Whitewater

video = Whitewater('path/to/video.mp4')
video.encode()
```

## Full Documentation

[Check out the wiki](https://github.com/samiare/whitewater-encoder/wiki).

✌︎
