"""JSON utilities for web-transmittable types"""

__copyright__ = "Copyright (C) 2014 Ivan D Vasin"
__docformat__ = "restructuredtext"

from collections \
    import Callable as _Callable, Mapping as _Mapping, Sequence as _Sequence

import ujson as _json


def json_dumps(obj, **kwargs):
    """A JSON_ representation of an object

    .. _JSON: http://en.wikipedia.org/wiki/JSON

    :rtype: :obj:`unicode`

    """
    if 'default' not in kwargs:
        kwargs['default'] = _json_dumps_default
    return _json.dumps(obj, **kwargs)


def _json_dumps_default(obj):
    if isinstance(obj, bool):
        return bool(obj)
    elif isinstance(obj, int):
        return int(obj)
    elif isinstance(obj, float):
        return float(obj)
    elif isinstance(obj, bytes):
        return bytes(obj)
    elif isinstance(obj, unicode):
        return unicode(obj)
    elif isinstance(obj, _Sequence):
        return list(obj)
    elif isinstance(obj, _Mapping):
        return dict(obj)
    elif hasattr(obj, 'prim') and isinstance(obj.prim, _Callable):
        return obj.prim()
    else:
        raise TypeError
