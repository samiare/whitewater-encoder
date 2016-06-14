# -*- coding: utf-8 -*-

import re
import os

from setuptools import setup, find_packages


version = re.search('^__version__\s*=\s*\'(.*)\'',
                    open('whitewater/__init__.py').read(),
                    re.M).group(1)

long_desription = open(os.path.join(os.path.dirname(__file__), 'README.rst')).read()

setup(name = 'whitewater',
      version = version,
      description = ('Convert videos into a format readable by the '
                     'Whitewater Player Javascript library.'),
      long_description = long_desription,
      url = 'https://github.com/samiare/whitewater-encoder',
      author = 'Samir Zahran',
      author_email = 'sayhello@samiare.net',
      license = 'MIT',
      classifiers = ['Development Status :: 5 - Production/Stable',
                     'Environment :: Console',
                     'Intended Audience :: Developers',
                     'License :: OSI Approved :: MIT License',
                     'Programming Language :: Python :: 2.7',
                     'Topic :: Multimedia :: Video',
                     'Topic :: Utilities'],
      keywords = 'video mobile',
      install_requires = ['docopt>=0.6.2',
                          'imageio>=1.4',
                          'numpy>=1.10.2',
                          'Pillow>=3.0.0'],
      packages = find_packages(),
      entry_points = {'console_scripts': ['whitewater = whitewater.__main__:main']})
