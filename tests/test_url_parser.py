import pytest

from pparser import UrlParser


URL = 'https://shop.example.com/catalog/shoes?page=1&sort=price#top'


def test_parts():
    url = UrlParser(URL)
    assert url.scheme == 'https'
    assert url.netloc == 'shop.example.com'
    assert url.path == '/catalog/shoes'
    assert url.query == 'page=1&sort=price'
    assert url.root_url == 'https://shop.example.com'
    assert url.url == 'https://shop.example.com/catalog/shoes'
    assert url.full_url == URL


def test_copywith_query():
    url = UrlParser(URL).copywith(query={'page': 3, 'size': 42})
    assert url.query == 'page=3&sort=price&size=42'


def test_copywith_path():
    url = UrlParser(URL)
    assert url.copywith(path='/sale').path == '/sale'
    assert url.copywith(path='boots').path == '/catalog/boots'
    assert url.copywith(path='/sale?page=5').query == 'page=5&sort=price'


def test_original_is_not_changed():
    url = UrlParser(URL)
    url.copywith(path='/x', query={'page': 9})
    assert url.full_url == URL


def test_join():
    assert UrlParser(URL).join('/item/1') == 'https://shop.example.com/item/1'
    assert UrlParser(URL).join('https://cdn.example.com/a.png') == 'https://cdn.example.com/a.png'


@pytest.mark.parametrize('url', ['example.com', '/relative/path', 'ftp://example.com', ''])
def test_invalid(url):
    with pytest.raises(ValueError):
        UrlParser(url)
