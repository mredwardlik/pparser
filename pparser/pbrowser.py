from __future__ import annotations

import typing as t
import weakref

from playwright.sync_api import Browser, BrowserContext, Error, Page, Playwright, sync_playwright
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

from pparser.errors import BrowserNotInstalledError, PageLoadError

__all__ = ['PBrowser', 'DEFAULT_BROWSER_OPTIONS']

DEFAULT_BROWSER_OPTIONS: t.Dict[str, t.Any] = {
    'browser': 'chromium',
    'headless': True,
    'width': 1920,
    'height': 1080,
    'timeout': 15.0,
    'user_agent': None,
    'locale': None,
}

WaitUntil = t.Literal['load', 'domcontentloaded', 'networkidle', 'commit']


def _shutdown(state: t.Dict[str, t.Any]) -> None:
    for name in ('context', 'browser'):
        obj = state.pop(name, None)
        if obj is not None:
            try:
                obj.close()
            except Exception:  # the browser may already be gone
                pass
    playwright = state.pop('playwright', None)
    if playwright is not None:
        try:
            playwright.stop()
        except Exception:
            pass


class PBrowser:
    """A headless browser with one tab that is reused for every page.

    The browser starts on the first request and stops on :meth:`close`, at
    the end of a ``with`` block or when the program exits.

    :param browser: ``chromium``, ``firefox`` or ``webkit``.
    :param headless: run without a window.
    :param width: viewport width in pixels.
    :param height: viewport height in pixels.
    :param timeout: default timeout for loading and waiting, in seconds.
    :param user_agent: custom ``User-Agent`` header.
    :param locale: browser locale, for example ``ru-RU``.
    :param launch_options: passed to Playwright's ``launch()``, for example
        ``channel='chrome'`` or ``executable_path='...'``.
    """

    def __init__(self, **options: t.Any):
        known = {key: options.pop(key) for key in list(options) if key in DEFAULT_BROWSER_OPTIONS}
        self.options: t.Dict[str, t.Any] = {**DEFAULT_BROWSER_OPTIONS, **known}
        self.launch_options: t.Dict[str, t.Any] = options
        if self.options['browser'] not in ('chromium', 'firefox', 'webkit'):
            raise ValueError('browser must be "chromium", "firefox" or "webkit".')
        self._state: t.Dict[str, t.Any] = {}
        self._page: t.Optional[Page] = None
        self._finalizer = weakref.finalize(self, _shutdown, self._state)

    @property
    def started(self) -> bool:
        return self._page is not None

    def _start(self) -> Page:
        if self._page is not None:
            return self._page
        playwright: Playwright = sync_playwright().start()
        self._state['playwright'] = playwright
        try:
            browser: Browser = getattr(playwright, self.options['browser']).launch(
                headless=self.options['headless'], **self.launch_options)
        except Error as error:
            _shutdown(self._state)
            if "Executable doesn't exist" in str(error) or 'playwright install' in str(error):
                raise BrowserNotInstalledError(
                    f'The {self.options["browser"]} browser for Playwright is not installed. '
                    f'Run: python -m playwright install {self.options["browser"]}') from None
            raise
        self._state['browser'] = browser
        context: BrowserContext = browser.new_context(
            viewport={'width': self.options['width'], 'height': self.options['height']},
            user_agent=self.options['user_agent'],
            locale=self.options['locale'],
        )
        context.set_default_timeout(self.options['timeout'] * 1000)
        self._state['context'] = context
        self._page = context.new_page()
        return self._page

    def get_content(
        self,
        url: str,
        wait_for: t.Optional[str] = None,
        wait_until: WaitUntil = 'load',
        delay: float = 0,
        timeout: t.Optional[float] = None,
    ) -> str:
        """Open ``url`` and return the HTML after scripts have run.

        :param wait_for: CSS selector to wait for before taking the HTML.
        :param wait_until: when navigation counts as finished.
        :param delay: extra pause in seconds after the page is ready.
        :param timeout: timeout in seconds for this page.
        """
        page = self._start()
        ms = (timeout if timeout is not None else self.options['timeout']) * 1000
        try:
            response = page.goto(url, wait_until=wait_until, timeout=ms)
            if response is not None and response.status >= 400:
                raise PageLoadError(url, f'HTTP {response.status} {response.status_text}'.strip(), response.status)
            if wait_for:
                page.wait_for_selector(wait_for, timeout=ms)
            if delay:
                page.wait_for_timeout(delay * 1000)
            return page.content()
        except PlaywrightTimeoutError:
            what = f'element "{wait_for}" did not appear' if wait_for else 'the page did not load'
            raise PageLoadError(url, f'{what} in {ms / 1000:g} s') from None
        except Error as error:
            raise PageLoadError(url, str(error).splitlines()[0]) from None

    def screenshot(self, path: str, full_page: bool = True) -> None:
        """Save a screenshot of the last opened page."""
        if self._page is None:
            raise RuntimeError('Open a page first.')
        self._page.screenshot(path=path, full_page=full_page)

    def close(self) -> None:
        """Stop the browser. It starts again on the next request."""
        self._page = None
        _shutdown(self._state)

    def __enter__(self) -> PBrowser:
        return self

    def __exit__(self, *exc: t.Any) -> None:
        self.close()
