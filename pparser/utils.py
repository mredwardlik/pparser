from __future__ import annotations

import typing as t
from urllib.parse import parse_qsl, urlencode

__all__ = [
    'Query',
    'stringify_query',
    'merge_queries',
]

Query = t.Union[str, t.Mapping[str, t.Any], None]


def _pairs(query: Query) -> t.List[t.Tuple[str, t.Any]]:
    if query is None:
        return []
    if isinstance(query, str):
        return parse_qsl(query.lstrip('?'), keep_blank_values=True)
    if isinstance(query, t.Mapping):
        return list(query.items())
    raise TypeError(
        f'Query must be a "str" or a "dict", not {query.__class__.__name__!r}.')


def stringify_query(query: Query) -> str:
    """``{'page': 2, 'q': 'red shoes'}`` → ``'page=2&q=red+shoes'``.

    Lists become repeated keys and ``None`` values are dropped.

    >>> stringify_query({'page': 2, 'tag': ['a', 'b'], 'skip': None})
    'page=2&tag=a&tag=b'
    """
    pairs = []
    for key, value in _pairs(query):
        if value is None:
            continue
        if isinstance(value, (list, tuple)):
            pairs.extend((key, str(item)) for item in value)
        else:
            pairs.append((key, str(value)))
    return urlencode(pairs)


def merge_queries(base: Query, update: Query) -> str:
    """Merge two queries. Keys from ``update`` replace keys from ``base``, and
    ``None`` removes a key.

    >>> merge_queries('page=1&sort=price', {'page': 2, 'sort': None, 'q': 'shoes'})
    'page=2&q=shoes'
    """
    merged: t.Dict[str, t.Any] = {}
    for key, value in _pairs(base):
        merged.setdefault(key, []).append(value)
    updates: t.Dict[str, t.Any] = {}
    for key, value in _pairs(update):
        updates.setdefault(key, []).append(value)
    for key, values in updates.items():
        merged[key] = values[0] if len(values) == 1 else values
    flat = {key: (value[0] if isinstance(value, list) and len(value) == 1 else value)
            for key, value in merged.items()}
    return stringify_query(flat)
