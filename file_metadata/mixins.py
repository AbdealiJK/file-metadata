# -*- coding: utf-8 -*-
"""
Mixins to add functionalities to some File classes. Meant for analysis
methods which are not completely generic, but can be used for multiple
formats.
"""

from __future__ import (division, absolute_import, unicode_literals,
                        print_function)

import glob
import json
import logging
import os
import platform
import subprocess
from xml.etree import cElementTree

from whichcraft import which

from file_metadata.utilities import (app_dir, download, tarxz_decompress,
                                     DictNoNone, memoized)
from file_metadata._compat import ffprobe_parser


class FFProbeMixin(object):

    @memoized
    def ffprobe(self):
        """
        Read multimedia streams and give information about it using the
        ffmpeg utility ffprobe (or avprobe from libav-tools, a fork of
        ffmpeg).
        """
        executable = None
        platform_arch = platform.architecture()[0]
        if (platform.system() == 'Linux' and
                platform_arch in ('32bit', '64bit')):
            # Fetch static binaries
            arch = 'ffmpeg-release-{0}-static.tar.xz'.format(platform_arch)
            arch_path = app_dir('user_data_dir', arch)
            bin_path = app_dir('user_data_dir',
                               'ffmpeg-*-{0}-static'.format(platform_arch),
                               'ffprobe')

            bins = glob.glob(bin_path)
            if len(bins) == 0:
                logging.info('Downloading `ffmpeg`\'s `ffprobe` to analyze '
                             'media streams and formats. Hence, the first '
                             'run may take longer than normal.')
                url = 'http://johnvansickle.com/ffmpeg/releases/' + arch
                download(url, arch_path)
                tarxz_decompress(arch_path, app_dir('user_data_dir'))
                bins = glob.glob(bin_path)

            executable = sorted(bins)[-1]  # Last one would be highest version

        if executable is None:
            # Choose executable to use
            if which('avprobe') is not None:
                executable = 'avprobe'
            elif which('ffprobe') is not None:
                executable = 'ffprobe'
            else:
                raise OSError('Neither avprobe nor ffprobe were found.')

        # Check whether json is supported
        json_support = False if subprocess.call([
            executable, '-v', '0', os.devnull, '-of', 'json']) == 1 else True

        command = (executable, '-v', '0', '-show_format', '-show_streams',
                   self.filename) + (('-of', 'json') if json_support else ())

        try:
            proc = subprocess.check_output(command)
        except subprocess.CalledProcessError:
            return {}
        else:
            output = proc.decode('utf-8')

        data = json.loads(output) if json_support else ffprobe_parser(output)
        return data

    def analyze_ffprobe(self):
        """
        Use ``ffprobe`` and return streams and format from it.

        :return: dict containing all the data from ``ffprobe``.
        """
        if not self.ffprobe():
            return {}

        def fmt(key):
            return self.ffprobe()['format'].get(key, None)

        data = DictNoNone({
            'FFProbe:Format': fmt('format_name'),
            'FFProbe:Duration': float(fmt('duration')),
            'FFProbe:NumStreams': int(fmt('nb_streams'))})

        streams = []
        for stream in self.ffprobe()['streams']:
            def strm(key, default=None):
                return stream.get(key, default)

            rate = width = height = None
            if strm("codec_type") == "video":
                rate = strm("avg_frame_rate")
                width, height = int(strm("width")), int(strm("height"))
            elif strm("codec_type") == "audio":
                rate = '%s/%s/%s' % (strm("channels", '-'),
                                     strm("sample_fmt", '-'),
                                     int(float(strm("sample_rate", '-'))))

            streams.append(DictNoNone({
                'Format': '{0}/{1}'.format(strm('codec_type'),
                                           strm('codec_name')),
                'Width': width,
                'Height': height,
                # 'Channels': strm('channels'),
                # 'SampleRate': strm('sample_rate'),
                # 'AvgFrameRate': (None if strm('avg_frame_rate') == '0/0'
                #                  else strm('avg_frame_rate')),
                'Rate': rate,
                'Duration': (None if strm('duration').lower() == 'n/a'
                             else float(strm('duration')))}))

        data['FFProbe:Streams'] = streams or None
        return data


def is_svg(_file):
    """
    Check is a given file is SVG or not. A file is considered to be SVG if:

    - Its mimetype is "application/svg+xml" or "image/svg+xml".
    - Its mimetype is "text/html" or "application/xml" or "text/xml" or
      "text/plain" and it has the svg tag with xmlns http://www.w3.org/2000/svg

    :param _file: A GenericFile object that should be checked for SVG.
    :return:      Boolean corresponding to whether the file is SVG.
    """
    mime = _file.mime()
    if mime in ('application/svg+xml', 'image/svg+xml'):
        return True
    elif mime in ('application/xml', 'text/xml', 'text/html', 'text/plain'):
        tag = None
        with open(_file.fetch('filename'), "r") as f:
            # cElementTree needs the events as bytes in python2
            items = cElementTree.iterparse(f, events=(str('start'),))
            try:
                _, el = items.next()
                tag = el.tag
            except cElementTree.ParseError:
                return False
        return tag == '{http://www.w3.org/2000/svg}svg'
