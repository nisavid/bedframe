"""Web-transmittable data types core"""

__copyright__ = "Copyright (C) 2014 Ivan D Vasin"
__docformat__ = "restructuredtext"

import abc as _abc

import ujson as _json

from . import _util_json


class webobject(object):

    """A web object

    This is an object that is exchanged between web clients and servers.
    It enables web services to be implemented in terms of :term:`native`
    types while guaranteeing a lossless :term:`primitive` representation
    that can be easily converted to plain text for transmission.

    To implement a :class:`!webobject`, implement the complementary methods
    :meth:`fromprim` and :meth:`prim`.

    In addition to the primitive representation, every :class:`!webobject`
    type supports conversion to and from JSON.

    :param object native:
        A :term:`native` object.

    """

    __metaclass__ = _abc.ABCMeta

    def __init__(self, native):
        self._native = native

    def __repr__(self):
        return '{}({!r})'.format(self.__class__.__name__, self.native())

    @classmethod
    def fromjson(cls, string, **kwargs):
        """The web object that is represented by a JSON_ string

        .. _JSON: http://en.wikipedia.org/wiki/JSON

        :param string:
            A JSON representation of this type of web object.
        :type string: :obj:`unicode`

        :param kwargs:
            Keyword arguments to :func:`json.loads`.

        :rtype: :class:`webobject`

        :raise exceptions.ValueError:
            Raised if the given *string* is not a valid JSON representation of
            this type of web object.

        """
        return cls.fromprim(_json.loads(string, **kwargs))

    @classmethod
    @_abc.abstractmethod
    def fromprim(cls, prim):
        """The web object that is represented by a primitive object

        :param prim:
            A primitive representation of this type of web object.
        :type prim:
            null
            or :obj:`bool`
            or :obj:`int`
            or :obj:`float`
            or :obj:`bytes`
            or :obj:`unicode`
            or [null or :obj:`bool` or :obj:`int` or :obj:`float`
                or :obj:`bytes` or :obj:`unicode` or [...] or {...}]
            or {null or :obj:`bool` or :obj:`int` or :obj:`float`
                or :obj:`bytes` or :obj:`unicode` or [...] or {...}:
                    null or :obj:`bool` or :obj:`int` or :obj:`float`
                    or :obj:`bytes` or :obj:`unicode` or [...] or {...}}

        :rtype: :class:`webobject`

        :raise exceptions.ValueError:
            Raised if *prim* is not a valid primitive representation of this
            type of web object.

        """
        pass

    def json(self, **kwargs):
        """A JSON_ representation of this web object

        .. _JSON: http://en.wikipedia.org/wiki/JSON

        This is the result of passing this web object's :meth:`prim`
        representation through a JSON encoder.

        .. seealso:: :func:`~bedframe.webtypes._util_json.json_dumps`

        :rtype: :obj:`unicode`

        """
        return _util_json.json_dumps(self.prim(), **kwargs)

    def native(self):
        """The :term:`native` object that is wrapped by this web object"""
        return self._native

    @_abc.abstractmethod
    def prim(self):
        """A :term:`primitive` representation of this web object

        :rtype:
            null or :obj:`bool` or :obj:`int` or :obj:`float` or :obj:`bytes`
            or :obj:`unicode` or :obj:`list` or :class:`dict`

        """
        pass
