import os
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest

PAGES = {
    # the list is added by JavaScript after a short delay
    '/': '''<!doctype html><html><head><title>Shop</title></head><body>
        <h1>Shop</h1><ul id="items"></ul>
        <a class="next" href="/page2">Next</a>
        <script>
          setTimeout(() => {
            const items = [['Kettle', 20], ['Lamp', 35], ['Chair', 50]]
            document.getElementById('items').innerHTML = items
              .map(([name, price]) => `<li class="item"><span class="name">${name}</span>
                 <span class="price">${price}</span><a href="/item/${name.toLowerCase()}">open</a></li>`)
              .join('')
          }, 300)
        </script></body></html>''',
    '/page2': '<!doctype html><html><body><li class="item"><span class="name">Table</span></li></body></html>',
}


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        path, _, query = self.path.partition('?')
        if path == '/echo':
            body, status = f'<html><body><p id="query">{query}</p></body></html>', 200
        elif path in PAGES:
            body, status = PAGES[path], 200
        else:
            body, status = '<html><body>Not found</body></html>', 404
        data = body.encode()
        self.send_response(status)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.send_header('Content-Length', str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, *args):
        pass


@pytest.fixture(scope='session')
def server():
    httpd = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    yield f'http://127.0.0.1:{httpd.server_address[1]}'
    httpd.shutdown()


@pytest.fixture(scope='session')
def browser_options():
    """Use PPARSER_CHANNEL=chrome or msedge to test with an installed browser."""
    channel = os.environ.get('PPARSER_CHANNEL')
    return {'channel': channel} if channel else {}


@pytest.fixture(scope='session')
def browser(server, browser_options):
    """Skip browser tests when Playwright has no browser to run."""
    from pparser import BrowserNotInstalledError, PParser

    with PParser(server + '/', **browser_options) as parser:
        try:
            parser.html(path='/page2')
        except BrowserNotInstalledError as error:
            pytest.skip(str(error))


@pytest.fixture
def pp(browser, server, browser_options):
    from pparser import PParser

    with PParser(server + '/', timeout=10, **browser_options) as parser:
        yield parser
