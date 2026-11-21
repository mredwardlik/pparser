"""Command line interface: ``pparser URL SELECTOR``."""

from __future__ import annotations

import argparse
import json
import sys
import typing as t

from bs4.element import Tag

from pparser import __version__
from pparser.errors import PParserError
from pparser.main import PParser

LINK_ATTRS = ('href', 'src', 'action', 'data-src')


class Field(t.NamedTuple):
    name: str
    selector: t.Optional[str]
    attr: t.Optional[str]


def parse_field(text: str) -> Field:
    """``title=h3 a@title`` → ``Field('title', 'h3 a', 'title')``.

    >>> parse_field('price=.price_color')
    Field(name='price', selector='.price_color', attr=None)
    >>> parse_field('link=@href')
    Field(name='link', selector=None, attr='href')
    """
    name, sep, rest = text.partition('=')
    if not sep or not name.strip() or not rest.strip():
        raise argparse.ArgumentTypeError(
            f'Field {text!r} must look like NAME=SELECTOR, NAME=SELECTOR@ATTR or NAME=@ATTR.')
    selector, _, attr = rest.partition('@')
    return Field(name.strip(), selector.strip() or None, attr.strip() or None)


def parse_query(text: str) -> t.Tuple[str, str]:
    key, sep, value = text.partition('=')
    if not sep or not key:
        raise argparse.ArgumentTypeError(f'Query {text!r} must look like KEY=VALUE.')
    return key, value


def extract(element: Tag, selector: t.Optional[str], attr: t.Optional[str], pp: PParser) -> t.Optional[str]:
    target = element.select_one(selector) if selector else element
    if target is None:
        return None
    if attr is None:
        return target.get_text(' ', strip=True)
    value = target.get(attr)
    if value is None:
        return None
    if isinstance(value, list):
        value = ' '.join(value)
    return pp.base_url.join(value) if attr in LINK_ATTRS else value


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog='pparser',
        description='Open a page in a headless browser and print the elements that match a CSS selector.',
        epilog='examples:\n'
               '  pparser https://quotes.toscrape.com/js/ ".quote .text"\n'
               '  pparser https://books.toscrape.com/ "article.product_pod" '
               '-f title="h3 a@title" -f price=.price_color -f link="h3 a@href"',
        formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('url', help='page URL')
    parser.add_argument('selector', help='CSS selector of the elements')
    parser.add_argument('-a', '--attr', help='print this attribute instead of the text (links become absolute)')
    parser.add_argument('-f', '--field', dest='fields', type=parse_field, action='append', default=[],
                        metavar='NAME=SELECTOR[@ATTR]',
                        help='collect a field inside every element; prints JSON objects. Can be repeated')
    parser.add_argument('-q', '--query', type=parse_query, action='append', default=[], metavar='KEY=VALUE',
                        help='add or replace a query parameter. Can be repeated')
    parser.add_argument('-n', '--limit', type=int, help='stop after this many elements')
    parser.add_argument('--json', action='store_true', help='print a JSON array')
    parser.add_argument('-w', '--wait-for', metavar='SELECTOR',
                        help='wait for this element before reading the page (default: the selector itself)')
    parser.add_argument('--no-wait', action='store_true', help="don't wait for any element")
    parser.add_argument('-t', '--timeout', type=float, default=15, help='timeout in seconds (default: %(default)s)')
    parser.add_argument('--screenshot', metavar='FILE', help='also save a screenshot of the page')
    browser = parser.add_argument_group('browser')
    browser.add_argument('--browser', choices=('chromium', 'firefox', 'webkit'), default='chromium')
    browser.add_argument('--channel', help='use an installed browser: chrome, msedge ...')
    browser.add_argument('--headed', action='store_true', help='show the browser window')
    parser.add_argument('--version', action='version', version=f'%(prog)s {__version__}')
    return parser


def main(argv: t.Optional[t.Sequence[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    if not sys.stdout.isatty() and hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')  # type: ignore[union-attr]

    options: t.Dict[str, t.Any] = {'browser': args.browser, 'headless': not args.headed, 'timeout': args.timeout}
    if args.channel:
        options['channel'] = args.channel

    try:
        with PParser(args.url, **options) as pp:
            wait_for = None if args.no_wait else (args.wait_for or args.selector)
            soup = pp.soup(query=dict(args.query) or None, wait_for=wait_for)
            if args.screenshot:
                pp.screenshot(args.screenshot)
            elements = soup.select(args.selector, limit=args.limit)
            if args.fields:
                rows: t.List[t.Any] = [
                    {f.name: extract(el, f.selector, f.attr, pp) for f in args.fields} for el in elements]
            else:
                rows = [extract(el, None, args.attr, pp) for el in elements]
    except PParserError as error:
        print(f'pparser: error: {error}', file=sys.stderr)
        return 1
    except Exception as error:  # invalid selector and similar
        print(f'pparser: error: {error}', file=sys.stderr)
        return 1

    if args.fields or args.json:
        print(json.dumps(rows, ensure_ascii=False, indent=2))
    else:
        for row in rows:
            if row is not None:
                print(row)
    if not elements:
        print(f'pparser: nothing matches "{args.selector}"', file=sys.stderr)
        return 3
    return 0


if __name__ == '__main__':
    sys.exit(main())
