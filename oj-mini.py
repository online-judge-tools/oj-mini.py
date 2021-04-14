#!/usr/bin/env python3
import argparse
import html.parser
import pathlib
import platform
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request
from logging import DEBUG, INFO, basicConfig, getLogger
from typing import *

__version__ = '1.0.0'

logger = getLogger(__file__)


def subcommand_download_add_subparser(subparsers: 'argparse._SubParsersAction') -> None:
    subparser = subparsers.add_parser('download', aliases=['d', 'dl'], help='download sample cases')
    subparser.add_argument('url')


class AtCoderHTMLParser(html.parser.HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.history: List[Tuple[Any, ...]] = []
        self.pres: List[Tuple[str, bytes]] = []

    def handle_starttag(self, tag: str, attrs: List[Tuple[str, Optional[str]]]) -> None:
        self.history.append(('starttag', tag, attrs))

    def handle_endtag(self, tag: str) -> None:
        self.history.append(('endtag', tag))

    def handle_data(self, data: str) -> None:
        if len(self.history) >= 4 and self.history[-4] == ('starttag', 'h3', []) and self.history[-3][0] == 'data' and self.history[-2] == ('endtag', 'h3') and self.history[-1] == ('starttag', 'pre', []):
            name = self.history[-3][1]
            if name.startswith('Sample Input ') or name.startswith('Sample Output '):
                logger.debug('found:\n<h3>%s</h3><pre>%s</pre>', name, data)
                kind = name.split()[1].lower()
                assert kind in ('input', 'output')
                self.pres.append((kind, data.encode()))

        self.history.append(('data', data))


class CodeforcesHTMLParser(html.parser.HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.stack: List[Tuple[str, List[Tuple[str, Optional[str]]]]] = []
        self.pres: List[Tuple[str, bytes]] = []

    def handle_starttag(self, tag: str, attrs: List[Tuple[str, Optional[str]]]) -> None:
        self.stack.append((tag, attrs))

    def handle_endtag(self, tag: str) -> None:
        self.stack.pop()

    def handle_data(self, data: str) -> None:
        if len(self.stack) >= 2 and self.stack[-2][0] == 'div' and self.stack[-2][1] == [('class', 'input')] and self.stack[-1][0] == 'pre':
            logger.debug('found:\n<div class="input"> ... <pre>%s</pre> ... </div>', data)
            self.pres.append(('input', data.lstrip().encode()))
        if len(self.stack) >= 2 and self.stack[-2][0] == 'div' and self.stack[-2][1] == [('class', 'output')] and self.stack[-1][0] == 'pre':
            logger.debug('found:\n<div class="output"> ... <pre>%s</pre> ... </div>', data)
            self.pres.append(('output', data.lstrip().encode()))


class SampleParseError(Exception):
    pass


def subcommand_download(*, url: str) -> bool:
    # parse URL
    try:
        result = urllib.parse.urlparse(url)
    except ValueError as e:
        logger.error('not a URL: %s', e)
        return False
    if result.hostname == 'atcoder.jp' in url:
        parser: html.parser.HTMLParser = AtCoderHTMLParser()
    elif result.hostname == 'codeforces.com':
        parser = CodeforcesHTMLParser()
    else:
        logger.error('invalid URL: only AtCoder and Codeforces are supported in %s', __file__)
        return False

    # get HTML
    try:
        resp = urllib.request.urlopen(url)
        content = resp.read()
    except urllib.error.HTTPError as e:
        logger.error('failed to download HTML: %s', e)
        logger.info("%s doesn't work in running contests. Using the full oj may solve this.", __file__)
        return False

    # parse HTML
    parser.feed(content.decode())
    parser.close()
    pres: List[Tuple[str, bytes]] = parser.pres  # type: ignore

    # parse sample cases
    try:
        if not pres:
            raise SampleParseError('no samples found')
        if len(pres) % 2 != 0:
            raise SampleParseError('an odd number of <pre> found')
        samples = []
        for i in range(len(pres) // 2):
            name_in, pre_in = pres[2 * i]
            name_out, pre_out = pres[2 * i + 1]
            if name_in != 'input':
                raise SampleParseError('<pre>...</pre> is expected in <div class="input"> but found in <div class="output">')
            if name_out != 'output':
                raise SampleParseError('<pre>...</pre> is expected in <div class="output"> but found in <div class="input">')
            samples.append((pre_in, pre_out))
    except SampleParseError as e:
        logger.error('failed to parse sample cases: %s', e)
        logger.info("%s supports only few problems. Using the full oj may solve this.", __file__)
        return False

    # write sample cases
    test_dir = pathlib.Path('test')
    if test_dir.exists():
        logger.error('test/ directory already exists')
        return False
    test_dir.mkdir(parents=True)
    for i, (sample_in, sample_out) in enumerate(samples):
        path_in = test_dir / 'sample-{}.in'.format(i + 1)
        path_out = test_dir / 'sample-{}.out'.format(i + 1)
        try:
            logger.info('write: %s\n%s', str(path_in), sample_in.decode())
        except UnicodeDecodeError as e:
            logger.info('write: %s\n%s', str(path_in), e)
        try:
            logger.info('write: %s\n%s', str(path_out), sample_out.decode())
        except UnicodeDecodeError as e:
            logger.info('write: %s\n%s', str(path_out), e)
        with open(path_in, 'wb') as fh:
            fh.write(sample_in)
        with open(path_out, 'wb') as fh:
            fh.write(sample_out)

    return True


def subcommand_test_add_subparser(subparsers: 'argparse._SubParsersAction') -> None:
    subparser = subparsers.add_parser('test', aliases=['t'], help='test your code')
    subparser.add_argument('-c', '--command')


def subcommand_test(*, command: Optional[str]) -> bool:
    if command is None:
        if platform.system() == 'Windows':
            command = '.\\a.exe'
        else:
            command = './a.out'

    # collect sample cases
    test_dir = pathlib.Path('test')
    samples: Dict[str, Dict[str, pathlib.Path]] = {}
    for path in test_dir.glob('*.in'):
        samples[path.stem] = {'in': path}
    for path in test_dir.glob('*.out'):
        if path.stem not in samples:
            logger.error('no corresponding input case: %s', str(path))
            return False
        samples[path.stem]['out'] = path

    # run tests
    ac_count = 0
    for name, sample in sorted(samples.items()):
        logger.info('test %s', name)

        # read the test case
        with open(sample['in'], 'rb') as fh:
            test_in = fh.read()
        expected_out = None
        if 'out' in sample:
            with open(sample['out'], 'rb') as fh:
                expected_out = fh.read()

        # execute the command
        try:
            proc = subprocess.run(command, shell=True, check=False, input=test_in, stdout=subprocess.PIPE)
        except subprocess.SubprocessError as e:
            logger.error('failed to run the command: %s', e)
            return False
        actual_out = proc.stdout

        # print the verdict
        verdict = 'AC'
        if expected_out is not None:
            if actual_out != expected_out:
                if actual_out.split() == expected_out.split():
                    logger.info('It was AC if it ignored white-space charactors. Use $ oj t --ignore-spaces-and-newlines')
                verdict = 'WA'
        if proc.returncode != 0:
            logger.info('The return code is %s', proc.returncode)
            verdict = 'RE'
        if verdict == 'AC':
            ac_count += 1
        else:
            try:
                logger.info('input:\n%s', test_in.decode())
            except UnicodeDecodeError as e:
                logger.error('input: %s', e)
            if expected_out is not None:
                try:
                    logger.info('expected output:\n%s', expected_out.decode())
                except UnicodeDecodeError as e:
                    logger.error('expected output: %s', e)
            try:
                logger.info('actual output:\n%s', actual_out.decode())
            except UnicodeDecodeError as e:
                logger.error('actual output: %s', e)
        logger.info('%s', verdict)

    logger.info('%s AC / %s cases', ac_count, len(samples))
    return ac_count == len(samples)


def get_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description='A portable and restricted version of https://github.com/online-judge-tools/oj', )
    parser.add_argument('-v', '--verbose', action='store_true')
    parser.add_argument('--version', action='store_true')

    subparsers = parser.add_subparsers(dest='subcommand', help='for details, see "{} COMMAND --help"'.format(sys.argv[0]))
    subcommand_download_add_subparser(subparsers)
    subcommand_test_add_subparser(subparsers)
    subparsers.add_parser('login', aliases=['l'], help='not supported in {}'.format(__file__))
    subparsers.add_parser('submit', aliases=['s'], help='not supported in {}'.format(__file__))
    subparsers.add_parser('generate-output', aliases=['g/o'], help='not supported in {}'.format(__file__))
    subparsers.add_parser('generate-input', aliases=['g/i'], help='not supported in {}'.format(__file__))
    subparsers.add_parser('test-reactive', aliases=['t/r'], help='not supported in {}'.format(__file__))

    return parser


def main() -> 'NoReturn':
    parser = get_parser()
    parsed = parser.parse_args()
    if parsed.verbose:
        basicConfig(level=DEBUG)
    else:
        basicConfig(level=INFO)

    if parsed.version:
        print(__file__, __version__)
        sys.exit(0)

    if parsed.subcommand in ['download', 'd', 'dl']:
        if not subcommand_download(url=parsed.url):
            sys.exit(1)
    elif parsed.subcommand in ['test', 't']:
        if not subcommand_test(command=parsed.command):
            sys.exit(1)
    elif parsed.subcommand is not None:
        logger.error('The subcommand "%s" is not supported in %s. Please use the full version: https://github.com/online-judge-toolgs/oj', parsed.subcommand, __file__)
        sys.exit(1)
    else:
        parser.print_help(file=sys.stderr)
        sys.exit(1)
    sys.exit(0)


if __name__ == '__main__':
    main()
