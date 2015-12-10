"""Whitewater

This module contains one public facing class -- Whitewater -- along with a
helper class and custom Exception. It provides the main logic of converting a
video into the format read by the Whitewater Video Decoder Javascript library.
"""


import os
import sys
import math
import json
import tempfile
import shutil
import imageio

from PIL import Image, ImageChops


class Whitewater(object):
    """A video to be encoded.

    Args:
        path_to_file (str): A path to a video file.
        **kwargs: Initialization options.

    Keyword Args:
        blocksize (int): The width/height of a single grid cell when checking
            one frame against the previous one. *Default:* ``8``
        grid (int): The size of the diffmap images in rows and columns, not
            absolute pixels. *Default:* ``256``
        quality (int): JPEG quality setting (only applicable when format is set
            to JPEG). *Default:* ``75``
        threshold (float): RMS threshold for determining whether a single cell
            of a frame is different from the previous one. *Default:* ``1.0``
        format (str): File format to save diffmap images as. *Default:* ``"JPEG"``

    Example:
        >>> encoder = Whitewater('path/to/video.mp4', options)
        >>> encoder.encode()
        "Successfully encoded <video>"

    """

    _DIGITS_64 = ('ABCDEFGHIJKLMNOPQRSTUVWXYZ'
                  'abcdefghijklmnopqrstuvwxyz'
                  '0123456789+/')
    _OPTION_DEFAULTS = {'blocksize': 8,
                        'grid': 256,
                        'quality': 75,
                        'threshold': 1.0,
                        'format': 'JPEG',
                        'debug': False}

    def __init__(self, path_to_file, **kwargs):
        self.debug = kwargs['debug'] if 'debug' in kwargs else False
        self.paths = {'input': path_to_file,
                      'output': self._get_output_directory(path_to_file)}
        self.options = self._get_options(kwargs)
        self.tracker = FrameTracker(self.options['blocksize'], self.options['grid'])

        try:
            self.video = imageio.get_reader(self.paths['input'])
        except IOError:
            self.exit('video not found')

        self.frame_maps = []
        self.consecutive = 0

    def encode(self):
        """Encode a video file into the whitewater format.

        When called, cycles through each frame of a video, preparing and then
        saving output files to the selected directory.

        """

        self._pre_encode_hook()
        for frame in enumerate(self.video):
            frame_number = frame[0] + 1

            self._pre_frame_hook(frame_number)
            self._process_frame(frame)
            self._post_frame_hook(frame_number)

        self._pre_save_hook()
        self._create_output_directory()
        self._save_images()
        self._save_manifest()
        self._copy_temp_directory()
        self._post_save_hook(os.listdir(self.paths['output']))
        self._post_encode_hook()

        return 'Successfully encoded \'%s\'' % self.paths['output']

    def exit(self, message):
        """Exit the process and print an error message.

        Args:
            message (str): error message

        """

        if hasattr(self, 'temp_dir') and self.paths['temp']:
            shutil.rmtree(self.paths['temp'])

        if not self.debug:
            sys.tracebacklimit = 0

        raise ProgramEnd(message)


    # start _private methods

    def _add_to_diffmap(self, block):
        """Adds an image block to the current diffmap.

        Args:
            block (``PIL.Image.Image``): a pixel block

        """

        x_0 = self.tracker.x_val * self.options['blocksize']
        y_0 = self.tracker.y_val * self.options['blocksize']
        x_1 = x_0 + self.options['blocksize']
        y_1 = y_0 + self.options['blocksize']

        self.tracker.diffmap.paste(block, (x_0, y_0, x_1, y_1))
        self.tracker.next_cell()

    def _add_to_framemap(self, position):
        """Converts position and consecutive values to a base64 representation.

        Args:
            position (int): the location that a block originated from on a frame

        Returns:
            str: a 5-character representation of the placement and consecutive
                number of blocks added to a diffmap in base64

        """

        consecutive_64 = self._get_base64_from_base10(self.consecutive)
        consecutive_64 = self._get_padded_string(consecutive_64, 2, 'A')
        position_64 = self._get_base64_from_base10(position)
        position_64 = self._get_padded_string(position_64, 3, 'A')

        return position_64 + consecutive_64

    def _compare_images(self, im1, im2):
        """Compares two images for similarity.

        Args:
            im1 (``PIL.Image.Image``): an image to be compared
            im2 (``PIL.Image.Image``): an image to be compared

        Returns:
            bool: ``False`` if similar and ``True`` if not.

        """

        diff = ImageChops.difference(im1, im2)
        bbox = diff.getbbox()
        if not bbox:
            return False
        else:
            histogram = diff.histogram()
            squares = (value * ((idx % 256) ** 2) for idx, value in enumerate(histogram))
            sum_of_squares = sum(squares)
            rms = math.sqrt(sum_of_squares/float(im1.size[0] * im1.size[1]))

            if rms <= self.options['threshold']:
                return False
            else:
                return True

    def _compare_to_previous_frame(self):
        """Compare current frame to the previous one.

        Loops through the blocks of each frame pair, appends frame data to
        ``self.frame_maps`` and adds image data to diffmaps.

        """

        size = self.video.get_meta_data()['source_size']
        columns = int(math.ceil(size[0] / float(self.options['blocksize'])))
        rows = int(math.ceil(size[1] / float(self.options['blocksize'])))

        position = 0
        frame_map = ''

        for row in xrange(0, rows):
            # for each row of a video frame
            self.consecutive = 0

            for column in xrange(0, columns):
                # for each column in a row of the video frame
                box = self._get_box_coords(row, column, self.options['blocksize'])

                temp_0 = Image.new('RGB', (self.options['blocksize'], self.options['blocksize']))
                temp_0.paste(self.tracker.previous_frame.crop(box))

                temp_1 = Image.new('RGB', (self.options['blocksize'], self.options['blocksize']))
                temp_1.paste(self.tracker.current_frame.crop(box))

                if self._compare_images(temp_0, temp_1):
                    self.consecutive += 1
                    self._add_to_diffmap(temp_1)

                    if self.tracker.x_val == 0:
                        frame_map += self._add_to_framemap(position - self.consecutive + 1)
                        self.consecutive = 0

                elif self.consecutive > 0:
                    frame_map += self._add_to_framemap(position - self.consecutive)
                    self.consecutive = 0

                temp_0.close()
                temp_1.close()
                position += 1

            if self.consecutive > 0:
                frame_map += self._add_to_framemap(position - self.consecutive)
                self.consecutive = 0

        self.frame_maps.append(frame_map)

    def _copy_temp_directory(self):
        """Copy the temp directory to the output directory."""

        if os.path.exists(self.paths['output']):

            oldfiles = [f for f in os.listdir(self.paths['output'])]
            for oldfile in oldfiles:
                os.remove(os.path.join(self.paths['output'], oldfile))

            newfiles = [f for f in os.listdir(self.paths['temp'])]
            for newfile in newfiles:
                shutil.copy2(os.path.join(self.paths['temp'], newfile), self.paths['output'])

        else:
            try:
                shutil.copytree(self.paths['temp'], self.paths['output'])
            except shutil.Error as err:
                self.exit(err)

        shutil.rmtree(self.paths['temp'])

    def _create_output_directory(self):
        """Creates the output directory."""

        try:
            self.paths['temp'] = tempfile.mkdtemp()
        except OSError as err:
            self.exit(err)

    def _get_image_from_frame_data(self, frame_data):
        """Convert an image from data to a usable format.

        Args:
            frame_data (``imageio.core.util.Image``): an imageio image

        Returns:
            ``PIL.Image.Image``: and image object

        """

        mode = 'RGB'
        size = self.video.get_meta_data()['source_size']
        decoder = 'raw'

        return Image.frombuffer(mode, size, frame_data, decoder, mode, 0, 1)

    def _get_options(self, kwargs):
        """Set video encoder options

        Args:
            **kwargs: A list of options.

        Returns:
            dict: a dict of options

        """
        try:
            options = Whitewater._OPTION_DEFAULTS
            for key, value in kwargs.iteritems():
                if key == 'threshold':
                    if not isinstance(options[key], bool):
                        options[key] = float(value)
                elif key == 'format':
                    if not isinstance(options[key], bool):
                        options[key] = str(value)
                else:
                    if not isinstance(options[key], bool):
                        options[key] = int(value)
        except ValueError as err:
            self.exit(err)

        return options

    def _save_image_as(self, image, name):
        """Create and save a diffmap image file.

        Args:
            image (``PIL.Image.Image`` instance): the image to save
            name (str): the name to save the image as

        """

        try:
            if self.options['format'] == 'JPEG':
                filename = name + '.jpg'
                image.save(os.path.join(self.paths['temp'], filename),
                           'JPEG',
                           quality=self.options['quality'],
                           subsampling=1,
                           optimize=True)

            elif self.options['format'] == 'PNG':
                filename = name + '.png'
                image.save(os.path.join(self.paths['temp'], filename),
                           'PNG',
                           optimize=True)

            else:
                filename = name + '.gif'
                image.save(os.path.join(self.paths['temp'], filename), 'GIF')

        except IOError as err:
            self.exit(err)

    def _save_images(self):
        """Loops through the stored images and saves them."""

        for i, image in enumerate(self.tracker.diffmaps):
            if i == 0:
                name = 'first'
            else:
                suffix = self._get_padded_string(str(i), 3, '0')
                name = 'diff_' + suffix
            self._save_image_as(image, name)

    def _save_manifest(self):
        """Create and save the manifest.json file."""

        meta = self.video.get_meta_data()
        with open(self.paths['temp'] + '/manifest.json', 'w') as manifest:
            json.dump({'version': 1,
                       'frameCount': int(meta['nframes']),
                       'blockSize': self.options['blocksize'],
                       'imagesRequired': self.tracker.diffmap_count,
                       'videoWidth': meta['source_size'][0],
                       'videoHeight': meta['source_size'][1],
                       'sourceGrid': self.options['grid'],
                       'framesPerSecond': meta['fps'],
                       'format': self.options['format'],
                       'frames': self.frame_maps}, manifest, indent=4)

    def _process_frame(self, frame):
        """Prepare a frame to be processed.

        Args:
            frame (int, ``imageio.core.util.Image``): a tuple containing
                frame data

        """

        frame_number = frame[0] + 1
        data = frame[1]

        image = self._get_image_from_frame_data(data)
        self.tracker.set_next_frame(image)

        if frame_number == 1:
            self.tracker.set_first_image(image)
        else:
            self._compare_to_previous_frame()


    # hooks

    def _pre_encode_hook(self):
        """Hook that runs at start of `encode()`"""

        pass

    def _post_encode_hook(self):
        """Hook that runs at end of `encode()`"""

        pass

    def _pre_frame_hook(self, frame):
        """Hook that runs before `_process_and_return_frame()`

        Args:
            frame (int): a frame number

        """

        pass

    def _post_frame_hook(self, frame):
        """Hook that runs after `_process_and_return_frame()`

        Args:
            frame (int): a frame number

        """

        pass

    def _pre_save_hook(self):
        """Hook that runs before `_create_output_directory()`"""

        pass

    def _post_save_hook(self, file_structure):
        """Hook that runs after `_copy_temp_directory()`

        Args:
            file_structure (list): a list of file names

        """

        pass


    # static methods

    @staticmethod
    def _get_output_directory(input_file):
        """Return the output file path.

        Args:
            input_file (str): the input file path

        Returns:
            str: the output file path

        """

        path, filename = os.path.split(input_file)
        name = os.path.splitext(filename)[0]
        return os.path.join(path, name)

    @staticmethod
    def _get_padded_string(string, length, char):
        """Pad a string by prepending characters.

        Args:
            string (str): the string to format
            length (int): the final length of the string to output
            char (str): the padding character to us

        Returns:
            str: a new string

        """

        string_len = len(string)
        if string_len == length:
            return string

        padding = ''

        for i in range(1, length):
            padding += char

            if length - string_len == i:
                string = padding + string
                return string

    @staticmethod
    def _get_box_coords(row, column, blocksize):
        """Get coordinates to copy an image from.

        Args:
            row (int): The row of the image.
            column (int): The column of the image.
            blocksize (int): The size of a grid cell.

        Returns:
            (int, int, int, int): The coordinates of a box to copy from, in the
                form top-left x, top-left y, bottom-right x, bottom-right y.
        """
        x_0 = column * blocksize
        y_0 = row * blocksize
        x_1 = x_0 + blocksize
        y_1 = y_0 + blocksize

        return (x_0, y_0, x_1, y_1)


    # class methods

    @classmethod
    def _get_base64_from_base10(cls, num):
        """Convert a number from base64 to base10.

        Args:
            num (int): the number to convert

        Returns:
            str: a base64 number represented as a string

        """

        if num < 0:
            sign = -1
        elif num == 0:
            return cls._DIGITS_64[0]
        else:
            sign = 1

        num *= sign
        digits = []

        while num:
            digits.append(cls._DIGITS_64[num % 64])
            num /= 64
        if sign < 0:
            digits.append('-')

        digits.reverse()
        return ''.join(digits)


class FrameTracker(object):
    """Tracks diffmaps for ``Whitewater``.

    Args:
        block_size (int): Size of cell square sides.
        max_size (int): Size of diffmap sides.
    """

    def __init__(self, block_size, max_size):
        self.__block_size = block_size
        self.__max_size = max_size
        self.__target = {'x': 0, 'y': 0}
        self.__previous_frame = None
        self.__current_frame = None
        self.__images = []

    @property
    def x_val(self):
        """The current diffmap's x value."""

        return self.__target['x']

    @property
    def y_val(self):
        """The current diffmap's y value."""

        return self.__target['y']

    @property
    def previous_frame(self):
        """The previous frame."""

        return self.__previous_frame

    @property
    def current_frame(self):
        """The current frame."""

        return self.__current_frame

    @property
    def diffmap(self):
        """The current diffmap."""

        return self.__images[-1]

    @property
    def diffmaps(self):
        """A list of all diffmaps."""

        return self.__images

    @property
    def diffmap_count(self):
        """The number of diffmaps."""

        return len(self.__images) - 1

    def set_first_image(self, image):
        """Set the first image and create a blank diffmap.

        Args:
            image (``PIL.Image.Image``): The first image.
        """

        self.__images.append(image)
        self._create_diffmap()

    def set_next_frame(self, frame):
        """Set the previous and current frames.

        Args:
            image (``PIL.Image.Image``): An image.
        """

        self.__previous_frame = self.__current_frame
        self.__current_frame = frame

    def reset(self):
        """Reset x and y values to 0."""

        self.__target['x'] = 0
        self.__target['y'] = 0

    def next_cell(self):
        """Advance to the next cell in the diffmap"""

        self.__target['x'] += 1
        if self.__target['x'] >= self.__max_size:
            self.__target['x'] = 0
            self.__target['y'] += 1
            if self.__target['y'] >= self.__max_size:
                self.__target['y'] = 0
                self._create_diffmap()

    def _create_diffmap(self):
        """Create a new diffmap."""

        self.reset()
        size = self.__block_size * self.__max_size
        self.__images.append(Image.new('RGB', (size, size), None))


class ProgramEnd(Exception):
    """Exception is raised to end program execution.

    Args:
        message (str): An exit message to print.
    """

    def __init__(self, message):
        super(ProgramEnd, self).__init__()
        self.message = message
        print message
