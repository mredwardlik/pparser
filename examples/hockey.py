"""Search and pagination through query parameters.

The base URL keeps the search query, and every request changes only the page
number: pparser merges the query parameters for you.

    python examples/hockey.py
"""

import os

from pparser import PParser

OPTIONS = {'channel': os.environ['PPARSER_CHANNEL']} if os.environ.get('PPARSER_CHANNEL') else {}


def main() -> None:
    url = 'https://www.scrapethissite.com/pages/forms/?q=new+york&per_page=25'
    with PParser(url, **OPTIONS) as pp:
        print(f'{"Team":<24} {"Year":>4} {"Wins":>5} {"Losses":>7}')
        for page in (1, 2):
            print(f'── {pp.url(query={"page_num": page})}')
            for team in pp.select('tr.team', query={'page_num': page}, wait_for='tr.team'):
                name, year, wins, losses = (
                    team.select_one(cell).get_text(strip=True)
                    for cell in ('.name', '.year', '.wins', '.losses'))
                print(f'{name:<24} {year:>4} {wins:>5} {losses:>7}')


if __name__ == '__main__':
    main()
