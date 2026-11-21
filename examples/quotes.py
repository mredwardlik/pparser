"""Quotes rendered by JavaScript: a plain HTTP request gets an empty page.

https://quotes.toscrape.com/js/ builds the list in the browser, so pparser
waits for the quotes to appear and then follows the "Next" link.

    python examples/quotes.py
"""

import os

from pparser import PParser

# set PPARSER_CHANNEL=chrome (or msedge) to use an installed browser
OPTIONS = {'channel': os.environ['PPARSER_CHANNEL']} if os.environ.get('PPARSER_CHANNEL') else {}


def main(pages: int = 3) -> None:
    with PParser('https://quotes.toscrape.com/js/', **OPTIONS) as pp:
        path = None
        for number in range(1, pages + 1):
            soup = pp.soup(path=path, wait_for='.quote')
            print(f'── page {number} ' + '─' * 50)
            for quote in soup.select('.quote'):
                text = quote.select_one('.text').get_text(strip=True)
                author = quote.select_one('.author').get_text(strip=True)
                tags = ', '.join(tag.get_text() for tag in quote.select('.tag'))
                print(f'{text}\n    — {author}  [{tags}]')

            next_link = soup.select_one('li.next a')
            if next_link is None:
                break
            path = next_link['href']


if __name__ == '__main__':
    main()
