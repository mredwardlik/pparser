from __future__ import annotations

import typing as t
from urllib.parse import ParseResult, urljoin, urlparse, urlunparse

from pparser.utils import Query, merge_queries

__all__ = ['UrlParser']


class UrlParser:
    """An immutable URL with helpers to change the path and the query.

    >>> url = UrlParser('https://example.com/catalog?page=1&sort=price')
    >>> url.copywith(query={'page': 2}).full_url
    'https://example.com/catalog?page=2&sort=price'
    >>> url.copywith(path='/search').full_url
    'https://example.com/search?page=1&sort=price'
    """

    def __init__(self, url: str):
        parsed = urlparse(url)
        if parsed.scheme not in ('http', 'https', 'file') or (parsed.scheme != 'file' and not parsed.netloc):
            raise ValueError(f'{url!r} is not an absolute http(s) URL.')
        self._parse_result: ParseResult = parsed

    def __repr__(self) -> str:
        return f'UrlParser({self.full_url!r})'

    def __str__(self) -> str:
        return self.full_url

    def __eq__(self, other: object) -> bool:
        return isinstance(other, UrlParser) and self.full_url == other.full_url

    @property
    def full_url(self) -> str:
        return self._parse_result.geturl()

    @property
    def root_url(self) -> str:
        return urlunparse((self.scheme, self.netloc, '', '', '', ''))

    @property
    def url(self) -> str:
        """URL without the query and the fragment."""
        return urlunparse((self.scheme, self.netloc, self.path, '', '', ''))

    @property
    def query(self) -> str:
        return self._parse_result.query

    @property
    def path(self) -> str:
        return self._parse_result.path

    @property
    def netloc(self) -> str:
        return self._parse_result.netloc

    @property
    def scheme(self) -> str:
        return self._parse_result.scheme

    def copywith(self, path: t.Optional[str] = None, query: Query = None) -> UrlParser:
        """A new URL with another path (absolute or relative) and with
        ``query`` merged into the current query."""
        result = self._parse_result
        if path is not None:
            joined = urlparse(urljoin(self.full_url, path))
            result = result._replace(path=joined.path)
            if joined.query:
                result = result._replace(query=merge_queries(result.query, joined.query))
        if query is not None:
            result = result._replace(query=merge_queries(result.query, query))
        return UrlParser(result.geturl())

    def join(self, link: str) -> str:
        """Absolute URL for a link found on the page.

        >>> UrlParser('https://example.com/catalog/').join('item/5')
        'https://example.com/catalog/item/5'
        """
        return urljoin(self.full_url, link)
