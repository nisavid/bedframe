"""Web-transmittable data types miscellany"""

__copyright__ = "Copyright (C) 2014 Ivan D Vasin"
__docformat__ = "restructuredtext"

from . import _core as _webtypes_core


class nonweb(_webtypes_core.webobject):

    """A non-web object"""

    def __init__(self, native):
        self._native = native

    def __repr__(self):
        return '{}({!r})'.format(self.__class__.__name__, self.native())

    @classmethod
    def fromjson(cls, string, **kwargs):
        raise RuntimeError('cannot create non-web object from JSON')

    @classmethod
    def fromprim(cls, prim):
        return cls(prim)

    def json(self, **kwargs):
        raise RuntimeError('cannot convert non-web object to JSON')

    def prim(self):
        return self.native()
