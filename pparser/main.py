# -*- coding: utf-8 -*-

'''
pparser.main
~~~~~~~~~~~~

This module provides a PParser object to manage
BeautifulSoup and a headless browser together.
'''

from __future__ import annotations

import typing as t

from bs4 import BeautifulSoup
from bs4.element import ResultSet, Tag

from pparser.pbrowser import PBrowser, WaitUntil
from pparser.url_parser import UrlParser
from pparser.utils import Query

__all__ = ['PParser']


class PParser:
    """Load pages in a real browser and parse them with BeautifulSoup.

    Pages are rendered by a headless browser first, so content added by
    JavaScript is there too. The browser starts on the first request and is
    reused for the next ones.

    >>> with PParser('https://quotes.toscrape.com/js/') as pp:   # doctest: +SKIP
    ...     for quote in pp.select('.quote', wait_for='.quote'):
    ...         print(quote.select_one('.text').get_text())

    :param url: base URL. Every request can change its path and query.
    :param browser_options: see :class:`pparser.pbrowser.PBrowser`:
        ``headless``, ``width``, ``height``, ``timeout``, ``user_agent``,
        ``locale``, ``browser``, and Playwright launch options like ``channel``.
    """

    def __init__(self, url: str, **browser_options: t.Any):
        self._url_parser: UrlParser = UrlParser(url)
        self._pbrowser: PBrowser = PBrowser(**browser_options)

    def __repr__(self) -> str:
        return f'PParser({self._url_parser.full_url!r})'

    @property
    def base_url(self) -> UrlParser:
        return self._url_parser

    def url(self, path: t.Optional[str] = None, query: Query = None) -> str:
        """The URL a request with these ``path`` and ``query`` opens.

        >>> PParser('https://example.com/list?page=1').url(query={'page': 3})
        'https://example.com/list?page=3'
        """
        return self._url_parser.copywith(path=path, query=query).full_url

    def html(
        self,
        path: t.Optional[str] = None,
        query: Query = None,
        wait_for: t.Optional[str] = None,
        wait_until: WaitUntil = 'load',
        delay: float = 0,
        timeout: t.Optional[float] = None,
    ) -> str:
        """Rendered HTML of the page.

        :param path: another path on the same site, absolute (``/page/2/``)
            or relative to the base URL (``page/2/``).
        :param query: query parameters to add or replace, as a ``dict`` or a
            string. ``None`` as a value removes the parameter.
        :param wait_for: CSS selector to wait for. Use it for content that
            is loaded by JavaScript.
        :param wait_until: ``load`` (default), ``domcontentloaded``,
            ``networkidle`` or ``commit``.
        :param delay: extra pause in seconds after the page is ready.
        :param timeout: timeout in seconds, instead of the default one.
        :raises pparser.PageLoadError: network error, HTTP error or timeout.
        """
        return self._pbrowser.get_content(
            self.url(path, query), wait_for=wait_for, wait_until=wait_until,
            delay=delay, timeout=timeout)

    def soup(self, path: t.Optional[str] = None, query: Query = None, **load_options: t.Any) -> BeautifulSoup:
        """Load the page and return it as :class:`bs4.BeautifulSoup`.

        Takes the same arguments as :meth:`html`.
        """
        return BeautifulSoup(self.html(path, query, **load_options), 'html.parser')

    def select(self, selector: str, *, limit: t.Optional[int] = None, **load_options: t.Any) -> ResultSet:
        """Load the page and return all elements that match a CSS selector.

        Takes the same keyword arguments as :meth:`html`. To run several
        selectors on one page, load it once with :meth:`soup`.
        """
        return self.soup(**load_options).select(selector, limit=limit)

    def select_one(self, selector: str, **load_options: t.Any) -> t.Optional[Tag]:
        """Load the page and return the first element that matches, or ``None``."""
        return self.soup(**load_options).select_one(selector)

    def screenshot(self, path: str, full_page: bool = True) -> None:
        """Save a screenshot of the last loaded page, handy for debugging."""
        self._pbrowser.screenshot(path, full_page=full_page)

    def close(self) -> None:
        """Stop the browser. The next request starts it again."""
        self._pbrowser.close()

    def __enter__(self) -> PParser:
        return self

    def __exit__(self, *exc: t.Any) -> None:
        self.close()
