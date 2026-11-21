import pytest

from pparser.utils import merge_queries, stringify_query


def test_stringify():
    assert stringify_query({'q': 'red shoes', 'page': 2}) == 'q=red+shoes&page=2'
    assert stringify_query('a=1&b=2') == 'a=1&b=2'
    assert stringify_query(None) == ''
    assert stringify_query({'tag': ['a', 'b']}) == 'tag=a&tag=b'


def test_stringify_type_error():
    with pytest.raises(TypeError):
        stringify_query(42)


def test_merge_replaces_and_adds():
    assert merge_queries('page=1&sort=price', {'page': 2}) == 'page=2&sort=price'
    assert merge_queries('page=1', 'q=shoes') == 'page=1&q=shoes'


def test_merge_removes_with_none():
    assert merge_queries('page=1&sort=price', {'sort': None}) == 'page=1'


def test_merge_keeps_blank_values_and_repeated_keys():
    assert merge_queries('q=&tag=a&tag=b', {'page': 1}) == 'q=&tag=a&tag=b&page=1'
