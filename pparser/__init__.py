"""Load pages in a headless browser and parse them with BeautifulSoup."""

from pparser.errors import BrowserNotInstalledError, PageLoadError, PParserError
from pparser.main import PParser
from pparser.url_parser import UrlParser

__version__ = '1.0.0'
__all__ = ['PParser', 'UrlParser', 'PParserError', 'PageLoadError', 'BrowserNotInstalledError']
