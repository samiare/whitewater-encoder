# -*- coding: utf-8 -*-


"""
\n\r
------------------------------\033[7m Whitewater Encoder \033[0m------------------------------

\033[1mUsage:\033[0m
  whitewater <file>... [options]
  whitewater (-h | --help | --version)

\033[1mOptions:\033[0m
  --blocksize <size>    The width/height of a single grid cell when checking one
                        frame against the previous one. [default: 8]
  --grid <size>         The size of the diffmap images in rows and columns, not
                        absolute pixels. [default: 256]
  --quality <percent>   JPEG quality setting. [default: 75]
  --threshold <rms>     RMS threshold for determining whether a single cell of a
                        frame is different from the previous one. [default: 1.0]
  --format <filetype>   File format to save diffmap images as. [default: JPEG]

\033[1mHomepage:\033[0m
  \033[4mhttps://github.com/samiare/whitewater-encoder\033[0m

\033[1mBug Reports:\033[0m
  \033[4mhttps://github.com/samiare/whitewater-encoder/issues\033[0m

\033[1mLicense:\033[0m
  The MIT License (MIT)

\033[1mAuthor:\033[0m
  Samir Zahran <sayhello@samiare.net>


The output program directories of this program are intended for use with the
Whitewater Player Javascript library. More information can be found here:
\033[4mhttps://github.com/samiare/whitewater-player\033[0m
\n\r

"""


import sys

from .__init__ import __version__
from .whitewater import Whitewater
from docopt import docopt


class Encoder(Whitewater):
    """Subclass of Whitewater."""

    LINE_LENGTH = 80

    def _pre_encode_hook(self):
        message = u'\033[92mSTART\033[0m %s' % self.paths['input']
        print Encoder.pad_line(message)

    def _post_encode_hook(self):
        message = u'\033[92mFINISHED\033[0m\a'
        print Encoder.pad_line(message)

    def _pre_frame_hook(self, frame):
        frames = int(self.video.get_meta_data()['nframes'])
        message = u'Processing frame %d of %d...' % (frame, frames)
        sys.stdout.write(Encoder.pad_line(message) + '\r')
        sys.stdout.flush()

    def _post_save_hook(self, file_structure):
        print Encoder.pad_line('\033[0;96m' + self.paths['input'] + '\033[0m')
        for idx, filename in enumerate(file_structure):
            pre = u'├──'
            if idx == len(file_structure) - 1:
                pre = u'└──'
            print Encoder.pad_line('\033[0;96m  %s\033[0m %s' % (pre, filename))

    @staticmethod
    def pad_line(value):
        value = value.rstrip(' ')
        length = len(value)
        to_add = Encoder.LINE_LENGTH - length

        if to_add > 0:
            spaces = ' ' * to_add
            value = value + spaces

        return value


def get_arguments():
    """Parse command line input."""

    arguments = docopt(__doc__, version=__version__)

    options = {'blocksize': int(arguments['--blocksize']),
               'quality': int(arguments['--quality']),
               'threshold': float(arguments['--threshold']),
               'format': str(arguments['--format']),
               'grid': int(arguments['--grid'])}

    files = arguments['<file>']

    return files, options

def main():
    """Run the main program."""

    paths, options = get_arguments()

    for path in paths:
        encoder = Encoder(path, **options)
        try:
            encoder.encode()
        except KeyboardInterrupt:
            message = Encoder.pad_line('\033[0;96m%s\033[0m' % 'exiting whitewater...')
            encoder.exit(message)
