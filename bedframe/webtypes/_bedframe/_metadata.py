"""Web-transmittable web service metadata."""

__copyright__ = "Copyright (C) 2013 Ivan D Vasin and Cogo Labs"
__docformat__ = "restructuredtext"

from ... import _metadata
from .. import _core


class ClassDefInfo(_core.webobject):

    """Web-transmittable class definition metadata.

    This wraps a :class:`bedframe.ClassDefInfo
    <bedframe._metadata.ClassDefInfo>` object.

    """

    @classmethod
    def fromprim(cls, prim):
        module, name = prim.split(':', 2)
        return cls(_metadata.ClassDefInfo(module, name))

    def prim(self):
        return u'{}:{}'.format(self.native().module, self.native().name)
