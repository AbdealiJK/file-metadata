# -*- coding: utf-8 -*-

from __future__ import (division, absolute_import, unicode_literals,
                        print_function)

import bz2
import imghdr
import os
import shutil
import socket
import tempfile
from io import StringIO

from six.moves.urllib.error import URLError

from file_metadata.utilities import (app_dir, bz2_decompress, make_temp,
                                     download, md5sum, memoized, retry,
                                     DictNoNone)
from tests import mock, unittest


def active_internet(host="8.8.8.8", port=53, timeout=3):
    try:
        socket.setdefaulttimeout(timeout)
        socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect((host, port))
        return True
    except socket.error:
        return False


class DownloadTest(unittest.TestCase):

    @mock.patch('file_metadata.utilities.urlopen')
    def test_text_data(self, mock_urlopen):
        mock_urlopen.return_value = StringIO()
        with make_temp() as filename:
            os.remove(filename)
            download('https://httpbin.org/ip', filename)
            self.assertTrue(mock_urlopen.called)

    @mock.patch('file_metadata.utilities.urlopen')
    def test_overwrite(self, mock_urlopen):
        mock_urlopen.return_value = StringIO()
        with make_temp() as filename:
            download('https://httpbin.org/ip', filename)
            mock_urlopen.assert_not_called()
            os.remove(filename)
            download('https://httpbin.org/ip', filename, overwrite=True)
            self.assertTrue(mock_urlopen.called)

    @unittest.skipIf(not active_internet(), 'Internet connection not found.')
    def test_binary_data(self):
        # Use this test to ensure that the data is appropriately caught from
        # the internet.
        with make_temp() as filename:
            os.remove(filename)
            download('https://httpbin.org/image/png', filename)
            self.assertEqual(imghdr.what(filename), "png")

    def test_timeout(self):
        with make_temp() as filename:
            os.remove(filename)
            self.assertRaises(URLError, download,
                              'https://httpbin.org/delay/3', filename,
                              timeout=1e-50)


class BZ2DecompressTest(unittest.TestCase):

    def setUp(self):
        self.testdir = tempfile.mkdtemp(prefix='abdeali_')
        self.bzfile = os.path.join(self.testdir, 'bz2file')

    def tearDown(self):
        shutil.rmtree(self.testdir)

    def test_bz2(self):
        with open(self.bzfile + '.txt', 'w') as _file:
            _file.write('hello world')
        with open(self.bzfile + '.txt', 'rb') as textfile:
            _file = bz2.BZ2File(self.bzfile + '.bz2', 'wb')
            _file.write(textfile.read())
            _file.close()
        os.remove(self.bzfile + '.txt')

        bz2_decompress(self.bzfile + '.bz2', self.bzfile + '.txt')

        with open(self.bzfile + '.txt') as _file:
            self.assertEqual(_file.read().decode('utf-8'), 'hello world')


class MD5SumTest(unittest.TestCase):

    def test_md5sum_small_file(self):
        with make_temp() as filename:
            with open(filename, 'w') as _file:
                _file.write('hello world!')
            self.assertEqual(md5sum(filename),
                             'fc3ff98e8c6a0d3087d515c0473f8677')

    def test_md5sum_large_file(self):
        with make_temp() as filename:
            with open(filename, 'w') as _file:
                _file.write('hello world!')
            self.assertEqual(md5sum(filename, blocksize=1),
                             'fc3ff98e8c6a0d3087d515c0473f8677')


class DictNoNoneTest(unittest.TestCase):

    def test_constructor(self):
        self.assertEqual(DictNoNone({'a': 1, 'b': None, 'c': 3}),
                         {'a': 1, 'c': 3})

    def test_addition(self):
        data = DictNoNone()
        data['a'] = 1
        data['b'] = None
        self.assertEqual(data, {'a': 1})

    def test_existing_key(self):
        data = DictNoNone()
        data['a'] = 1
        self.assertEqual(data, {'a': 1})
        data['a'] = None
        self.assertEqual(data, {})


class AppDirTest(unittest.TestCase):

    def setUp(self):
        self.testdir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.testdir)

    def test_invalid_dirtype(self):
        self.assertEqual(app_dir('unknown_function'), None)

    @mock.patch('file_metadata.utilities.appdirs')
    def test_check_paths(self, mock_appdirs):
        confdir = os.path.join(self.testdir, 'appdirs', 'configdir')
        mock_appdirs.user_config_dir = mock.Mock(return_value=confdir)

        self.assertFalse(os.path.exists(confdir))
        self.assertEqual(app_dir('user_config_dir'), confdir)
        self.assertTrue(os.path.exists(confdir))

        self.assertEqual(app_dir('user_config_dir', 'a', 'path'),
                         os.path.join(confdir, 'a', 'path'))

    def test_integration(self):
        self.assertTrue(os.path.exists(app_dir('user_data_dir')))


class MemoizedTest(unittest.TestCase):

    def test_memoized_decorator(self):

        class AbcClass:
            val = 0

            @memoized
            def inc_val(self, arg):
                self.val += 1
                return self.val + arg

        uut = AbcClass()
        self.assertEqual(uut.inc_val(2), uut.inc_val(2))
        self.assertNotEqual(AbcClass.inc_val(uut, 2), AbcClass.inc_val(uut, 2))


class RetryTest(unittest.TestCase):

    def test_retry_tries(self):
        def func():
            func.count += 1
            if func.count > 5:
                return True
            else:
                raise AssertionError

        func.count = 0
        uut = retry(tries=6)(func)
        self.assertTrue(uut())
        self.assertEqual(func.count, 6)

        func.count = 0
        uut = retry(tries=2)(func)
        self.assertRaises(AssertionError, uut)
        self.assertEqual(func.count, 2)
