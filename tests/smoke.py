import contextlib
import os
import pathlib
import subprocess
import sys
import tempfile
import unittest
from typing import *


@contextlib.contextmanager
def chdir(path: pathlib.Path):
    cwd = pathlib.Path.cwd()
    try:
        os.chdir(path)
        yield
    finally:
        os.chdir(cwd)


class OjMiniTest(unittest.TestCase):
    def test_download_atcoder(self) -> None:
        url = 'https://atcoder.jp/contests/abc192/tasks/abc192_a'
        cwd = pathlib.Path.cwd()
        with tempfile.TemporaryDirectory() as tempdir_:
            tempdir = pathlib.Path(tempdir_)

            with chdir(tempdir):
                subprocess.check_call([sys.executable, str(cwd / 'oj-mini.py'), 'd', url])

            with open(tempdir / 'test' / 'sample-1.in') as fh:
                self.assertEqual(fh.read(), '140\n')
            with open(tempdir / 'test' / 'sample-1.out') as fh:
                self.assertEqual(fh.read(), '60\n')
            with open(tempdir / 'test' / 'sample-2.in') as fh:
                self.assertEqual(fh.read(), '1000\n')
            with open(tempdir / 'test' / 'sample-2.out') as fh:
                self.assertEqual(fh.read(), '100\n')
            self.assertFalse((tempdir / 'test' / 'sample-3.in').exists())
            self.assertFalse((tempdir / 'test' / 'sample-3.out').exists())

    def test_download_codeforces(self) -> None:
        url = 'https://codeforces.com/contest/1230/problem/A'
        cwd = pathlib.Path.cwd()
        with tempfile.TemporaryDirectory() as tempdir_:
            tempdir = pathlib.Path(tempdir_)

            with chdir(tempdir):
                subprocess.check_call([sys.executable, str(cwd / 'oj-mini.py'), 'd', url])

            with open(tempdir / 'test' / 'sample-1.in') as fh:
                self.assertEqual(fh.read(), '1 7 11 5\n')
            with open(tempdir / 'test' / 'sample-1.out') as fh:
                self.assertEqual(fh.read(), 'YES\n')
            with open(tempdir / 'test' / 'sample-2.in') as fh:
                self.assertEqual(fh.read(), '7 3 2 5\n')
            with open(tempdir / 'test' / 'sample-2.out') as fh:
                self.assertEqual(fh.read(), 'NO\n')
            self.assertFalse((tempdir / 'test' / 'sample-3.in').exists())
            self.assertFalse((tempdir / 'test' / 'sample-3.out').exists())

    def test_test_success(self) -> None:
        cwd = pathlib.Path.cwd()
        with tempfile.TemporaryDirectory() as tempdir_:
            tempdir = pathlib.Path(tempdir_)
            (tempdir / 'test').mkdir()
            with open(tempdir / 'test' / 'sample-1.in', 'w') as fh:
                fh.write('3\n')
            with open(tempdir / 'test' / 'sample-1.out', 'w') as fh:
                fh.write('9\n')
            with open(tempdir / 'test' / 'sample-2.in', 'w') as fh:
                fh.write('4\n')
            with open(tempdir / 'test' / 'sample-2.out', 'w') as fh:
                fh.write('16\n')

            with chdir(tempdir):
                cmd = '{} -c "print(int(input()) ** 2)"'.format(sys.executable)
                subprocess.check_call([sys.executable, str(cwd / 'oj-mini.py'), 't', '-c', cmd])

    def test_test_failure(self) -> None:
        cwd = pathlib.Path.cwd()
        with tempfile.TemporaryDirectory() as tempdir_:
            tempdir = pathlib.Path(tempdir_)
            (tempdir / 'test').mkdir()
            with open(tempdir / 'test' / 'sample-1.in', 'w') as fh:
                fh.write('3\n')
            with open(tempdir / 'test' / 'sample-1.out', 'w') as fh:
                fh.write('9\n')
            with open(tempdir / 'test' / 'sample-2.in', 'w') as fh:
                fh.write('4\n')
            with open(tempdir / 'test' / 'sample-2.out', 'w') as fh:
                fh.write('16\n')

            with chdir(tempdir):
                cmd = '{} -c "print(16)"'.format(sys.executable)
                proc = subprocess.run([sys.executable, str(cwd / 'oj-mini.py'), 't', '-c', cmd], check=False)

            self.assertNotEqual(proc.returncode, 0)
