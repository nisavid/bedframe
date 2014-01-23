"""Web-transmittable built-in Python types"""

__copyright__ = "Copyright (C) 2014 Ivan D Vasin"
__docformat__ = "restructuredtext"

import __builtin__

from .. import _core


class primitive(_core.webobject):

    """A web-transmittable :term:`primitive` object"""

    @classmethod
    def fromprim(cls, prim):
        prim_ctor = cls._prim_class() or (lambda x: x)
        return cls(prim_ctor(prim))

    def prim(self):
        return self.native()

    @classmethod
    def _prim_class(cls):
        return None


class bool(primitive):
    """A web-transmittable :obj:`bool`"""
    @classmethod
    def _prim_class(cls):
        return __builtin__.bool


class bytes(primitive):
    """A web-transmittable :obj:`bytes` object"""
    @classmethod
    def _prim_class(cls):
        return __builtin__.bytes


_dict_classes = {}
def dict(keytype, valuetype):
    """A web-transmittable :class:`dict`

    :param keytype:
        The web-transmittable data type of this container's keys.
    :type keytype: :class:`~bedframe.webtypes._core.webobject`

    :param valuetype:
        The web-transmittable data type of this container's values.
    :type keytype: :class:`~bedframe.webtypes._core.webobject`

    """
    if (keytype, valuetype) not in _dict_classes:
        @classmethod
        def fromprim(cls, prim):
            return cls({keytype.fromprim(key).native():
                            valuetype.fromprim(value).native()
                        for key, value in prim.iteritems()})

        def prim(self):
            return {keytype(key).prim(): valuetype(value).prim()
                    for key, value in self.native().iteritems()}

        _dict_classes[(keytype, valuetype)] = \
            type('dict({}.{}, {}.{})'
                  .format(keytype.__module__, keytype.__name__,
                          valuetype.__module__, valuetype.__name__),
                 (primitive,),
                 {'keytype': keytype, 'valuetype': valuetype,
                  'fromprim': fromprim, 'prim': prim})
    return _dict_classes[(keytype, valuetype)]


class float(primitive):
    """A web-transmittable :obj:`float`"""
    @classmethod
    def _prim_class(cls):
        return __builtin__.float


class int(primitive):
    """A web-transmittable :obj:`int`"""
    @classmethod
    def _prim_class(cls):
        return __builtin__.int


_list_classes = {}
def list(itemtype):
    """A web-transmittable :obj:`list`

    :param itemtype:
        The web-transmittable data type of this container's items.
    :type itemtype: :class:`~bedframe.webtypes._core.webobject`

    """
    if itemtype not in _list_classes:
        @classmethod
        def fromprim(cls, prim):
            return cls([itemtype.fromprim(item).native()
                        for item in iter(prim)])

        def prim(self):
            return [itemtype(item).prim() for item in iter(self.native())]

        _list_classes[itemtype] = \
            type('list({}.{})'.format(itemtype.__module__, itemtype.__name__),
                 (primitive,), {'itemtype': itemtype, 'fromprim': fromprim,
                                'prim': prim})
    return _list_classes[itemtype]


class null(primitive):
    """A web-transmittable :obj:`None`"""
    @classmethod
    def fromprim(cls, prim):
        if prim is None:
            return cls(prim)
        else:
            raise TypeError('invalid {}.{} type {!r}; expecting {!r}'
                             .format(cls.__module__, cls.__name__,
                                     prim.__class__, None.__class__))


class unicode(primitive):
    """A web-transmittable :obj:`unicode`"""
    @classmethod
    def _prim_class(cls):
        return _normalized_unicode


def _normalized_unicode(value):
    if isinstance(value, str):
        return value.decode('utf8')
    else:
        return __builtin__.unicode(value)
