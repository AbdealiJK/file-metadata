# -*- coding: utf-8 -*-

from __future__ import (division, absolute_import, unicode_literals,
                        print_function)

import json
import logging
import os
import subprocess

import magic

from file_metadata.utilities import PropertyCached
from file_metadata.utilities import app_dir, download, targz_decompress


class GenericFile:
    """
    Object corresponding to a single file. An abstract class that can be
    used for any mimetype/media-type (depending of the file itself). Provides
    helper functions to open files, and analyze basic data common to all
    types of files.

    Any class that inherits from this abstract class would probably want to
    set the ``mimetypes`` and override the ``analyze()`` or write their
    own ``analyze_*()`` methods depending on the file type and analysis
    routines that should be run.

    :ivar mimetypes: Set of mimetypes (strings) applicable to this class
        based on the official standard by IANA.
    """
    mimetypes = ()

    def __init__(self, fname):
        self.filename = fname

    @classmethod
    def create(cls, *args, **kwargs):
        """
        Create an object which best suits the given file. It first opens the
        file as a GenericFile and then uses the mimetype analysis to suggest
        the best class to use.

        :param args:   The args to pass to the file class.
        :parak kwargs: The kwargs to pass to the file class.
        :return:       A class inheriting from GenericFile.
        """
        cls_file = cls(*args, **kwargs)
        mime = cls_file.analyze_mimetype()['File:MIMEType']
        _type, subtype = mime.split('/', 1)

        if _type == 'image' or mime == 'application/x-xcf':
            from file_metadata.image.image_file import ImageFile
            return ImageFile.create(*args, **kwargs)
        elif _type == 'audio':
            from file_metadata.audio.audio_file import AudioFile
            return AudioFile.create(*args, **kwargs)
        elif _type == 'video':
            from file_metadata.video.video_file import VideoFile
            return VideoFile.create(*args, **kwargs)

        return cls_file

    def analyze(self, prefix='analyze_', suffix='', methods=None):
        """
        Analyze the given file and create metadata information appropriately.
        Search and use all methods that have a name starting with
        ``analyze_*`` and merge the doctionaries using ``.update()``
        to get the cumulative set of metadata.

        :param prefix:  Use only methods that have this prefix.
        :param suffix:  Use only methods that have this suffix.
        :param methods: A list of method names to choose from. If not given,
                        a sorted list of all methods from the class is used.
        :return: A dict containing the cumulative metadata.
        """
        data = {}
        methods = methods or sorted(dir(self))
        for method in methods:
            if method.startswith(prefix) and method.endswith(suffix):
                data.update(getattr(self, method)())
        return data

    @PropertyCached
    def metadata(self):
        """
        A python dictionary of all the metadata identified by analyzing
        the given file. This property is read-only and cannot be modified.

        :return: All the metadata found about the given file.
        """
        return self.analyze()

    @PropertyCached
    def exiftool(self):
        """
        The exif data from the given file using ``exiftool``. The data it
        fetches includes:

         - Basic file information
         - Exif data
         - XMP data
         - ICC Profile data
         - Composite data
         - GIMP, Adobe, Inkscape specific file data
         - Vorbis data for audio files
         - JFIF data
         - SVG data

        and many more types of information. For more information see
        <http://www.sno.phy.queensu.ca/~phil/exiftool/>.

        :return:      A dictionary containing the exif information.
        """
        folder = 'Image-ExifTool-10.15'
        arch = folder + '.tar.gz'
        arch_path = app_dir('user_data_dir', arch)
        bin_path = app_dir('user_data_dir', folder, 'exiftool')

        if not os.path.exists(bin_path):
            logging.info('Downloading `exiftool` to analyze exif data.'
                         'Hence, the first run may take longer than normal.')
            url = 'http://www.sno.phy.queensu.ca/~phil/exiftool/' + arch
            download(url, arch_path)
            targz_decompress(arch_path, app_dir('user_data_dir'))

        command = ('perl', bin_path, '-G', '-j',
                   os.path.abspath(self.filename))
        try:
            proc = subprocess.check_output(command)
        except subprocess.CalledProcessError as proc_error:
            output = proc_error.output.decode('utf-8').rstrip('\r\n')
        else:
            output = proc.decode('utf-8').rstrip('\r\n')

        data = json.loads(output)

        assert len(data) == 1
        return data[0]

    def analyze_os_stat(self):
        """
        Use the python ``os`` library to find file-system related metadata.

        :return: dict with the keys:

                  - Size of file - The size of the file in bytes.
        """
        stat_data = os.stat(self.filename)
        return {"File:FileSize": str(stat_data.st_size) + " bytes"}

    def analyze_mimetype(self):
        """
        Use libmagic to identify the mimetype of the file. This analysis is
        done using multiple methods. The list (in priority order) is:

         - python-magic pypi library.
         - python-magic provided by ``file`` utility (Not supported, but
           provided for better compatibility with system packages).
         - Python's builtin ``mimetypes`` module.

        :return: dict with the keys:

                 - MIME type - The IANA mimetype string for this file.
        """
        if hasattr(magic, "from_file"):
            # Use https://pypi.python.org/pypi/python-magic
            mime = magic.from_file(self.filename, mime=True)
        elif hasattr(magic, "open"):
            # Use the python-magic library in distro repos from the `file`
            # command - http://www.darwinsys.com/file/
            magic_instance = magic.open(magic.MAGIC_MIME)
            magic_instance.load()
            mime = magic_instance.file(self.filename)
        else:
            raise ImportError('The `magic` module that was found is not the '
                              'expected pypi package python-magic '
                              '(https://pypi.python.org/pypi/python-magic) '
                              'nor file\'s (http://www.darwinsys.com/file/) '
                              'package.')
        return {"File:MIMEType": mime}

    def analyze_exiftool(self, ignored_keys=()):
        """
        Use ``exiftool`` and return metadata from it.

        :return: dict containing all the data from ``exiftool``.
        """
        # We remove unimportant data as this is an analysis routine for the
        # file. The method `exiftool` continues to have all the data.
        ignored_keys = set(ignored_keys + (
            'SourceFile', 'ExifTool:ExifToolVersion', 'ExifTool:Error',
            'ExifTool:Warning' 'File:FileName', 'File:Directory',
            'File:MIMEType'))
        return dict((key, val) for key, val in self.exiftool.items()
                    if key not in ignored_keys)
