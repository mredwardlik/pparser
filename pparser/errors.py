from __future__ import annotations

import typing as t

__all__ = ['PParserError', 'BrowserNotInstalledError', 'PageLoadError']


class PParserError(Exception):
    """Base class for pparser errors."""


class BrowserNotInstalledError(PParserError):
    """Playwright is installed, but the browser it needs is not."""


class PageLoadError(PParserError):
    """The page could not be loaded: network error, timeout or HTTP error."""

    def __init__(self, url: str, reason: str, status: t.Optional[int] = None):
        self.url = url
        self.reason = reason
        self.status = status
        super().__init__(f'Cannot load {url}: {reason}')
