import pytest

from pparser import PageLoadError, PParser
from pparser.cli import main


def test_waits_for_javascript(pp):
    items = pp.select('.item', wait_for='.item')
    assert [item.select_one('.name').get_text() for item in items] == ['Kettle', 'Lamp', 'Chair']


def test_without_waiting_the_list_is_empty(pp):
    assert pp.select('.item', wait_until='domcontentloaded') == []


def test_select_one_and_soup(pp):
    assert pp.select_one('h1').get_text() == 'Shop'
    assert pp.soup().title.string == 'Shop'
    assert pp.select_one('.missing') is None


def test_path_and_query(pp):
    assert pp.select_one('.name', path='page2').get_text() == 'Table'
    assert pp.select_one('#query', path='/echo', query={'page': 2, 'q': 'red shoes'}).get_text() == 'page=2&q=red+shoes'


def test_http_error(pp):
    with pytest.raises(PageLoadError) as error:
        pp.html(path='/missing')
    assert error.value.status == 404


def test_wait_timeout(pp):
    with pytest.raises(PageLoadError, match='did not appear'):
        pp.html(wait_for='.never', timeout=1)


def test_browser_is_reused_and_restarts_after_close(browser, server, browser_options):
    with PParser(server + '/', **browser_options) as pp:
        pp.html(path='/page2')
        page = pp._pbrowser._page
        pp.html(path='/page2')
        assert pp._pbrowser._page is page
        pp.close()
        assert not pp._pbrowser.started
        assert pp.select_one('.name', path='/page2').get_text() == 'Table'


def test_cli_fields(browser, server, browser_options, capsys):
    args = [server + '/', '.item', '-f', 'name=.name', '-f', 'price=.price', '-f', 'link=a@href', '--json']
    if browser_options:
        args += ['--channel', browser_options['channel']]
    assert main(args) == 0
    out = capsys.readouterr().out
    assert '"name": "Kettle"' in out
    assert f'"link": "{server}/item/kettle"' in out


def test_cli_text_and_errors(browser, server, browser_options, capsys):
    extra = ['--channel', browser_options['channel']] if browser_options else []
    assert main([server + '/', '.item .name'] + extra) == 0
    assert capsys.readouterr().out.split() == ['Kettle', 'Lamp', 'Chair']
    assert main([server + '/missing', 'h1'] + extra) == 1
    assert 'HTTP 404' in capsys.readouterr().err
    assert main([server + '/page2', '.none', '--no-wait'] + extra) == 3
