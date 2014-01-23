"""Cross-origin resource sharing

.. seealso::
    `Cross-Origin Resource Sharing <http://www.w3.org/TR/cors/>`_

"""

__copyright__ = "Copyright (C) 2014 Ivan D Vasin"
__docformat__ = "restructuredtext"

from spruce.collections import odict as _odict, uset as _uset
from spruce.lang import enum as _enum

from . import _collections as _coll


class CorsAffordanceSet(object):

    """Cross-origin resource sharing affordances

    :param origins:
        The afforded request origins.
    :type origins: u{:obj:`str`}

    :param methods:
        The afforded request methods.
    :type methods: u{:obj:`str`}

    """

    def __init__(self, origins=(), methods=(), request_headers=(),
                 exposed_response_headers=(),
                 client_preflight_cache_lifespan=None):
        self.client_preflight_cache_lifespan = client_preflight_cache_lifespan
        self.exposed_response_headers = exposed_response_headers
        self.methods = methods
        self.origins = origins
        self.request_headers = request_headers

    def __repr__(self):
        return '{}({})'.format(self.__class__.__name__,
                               ', '.join('{}={!r}'.format(property_, value)
                                         for property_, value
                                         in self._components_map(ordered=True)
                                                .items()))

    def __str__(self):
        properties_strs = []
        for property_, value in self._components_map(ordered=True).items():
            if value is None:
                continue

            displayname = self._property_displayname(property_)
            try:
                value_isfinite = value.isfinite
            except AttributeError:
                str_ = '{} {}'.format(displayname, value)
            else:
                if value_isfinite:
                    str_ = '{} {}'.format(displayname, value)
                else:
                    str_ = 'any ' + displayname
            properties_strs.append(str_)
        return '{{{}}}'.format(', '.join(properties_strs))

    @property
    def client_preflight_cache_lifespan(self):
        """The afforded lifespan of each client's preflight result cache

        :type: :class:`datetime.timedelta`

        """
        return self._client_preflight_cache_lifespan

    @client_preflight_cache_lifespan.setter
    def client_preflight_cache_lifespan(self, value):
        self._client_preflight_cache_lifespan = value

    @property
    def exposed_response_headers(self):
        """The afforded exposed response headers

        :type: u{:obj:`str`}

        """
        return self._exposed_response_headers

    @exposed_response_headers.setter
    def exposed_response_headers(self, value):
        self._exposed_response_headers = _uset(value)

    @classmethod
    def max(cls):
        return cls(origins='*', methods='*', request_headers='*',
                   exposed_response_headers='*')

    @property
    def methods(self):
        """The afforded request methods

        :type: u{:obj:`str`}

        """
        return self._methods

    @methods.setter
    def methods(self, value):
        self._methods = _uset(value)

    @classmethod
    def min(cls):
        return cls(origins=(), methods=(), request_headers=(),
                   exposed_response_headers=())

    @property
    def origins(self):
        """The afforded request origins

        :type: u{:obj:`str`}

        """
        return self._origins

    @origins.setter
    def origins(self, value):
        self._origins = _uset(value)

    @property
    def request_headers(self):
        """The afforded request headers

        :type: u{:obj:`str`}

        """
        return self._request_headers

    @request_headers.setter
    def request_headers(self, value):
        self._request_headers = _uset(value)

    def _components_map(self, ordered=False):
        class_ = _odict if ordered else dict
        return class_((('origins', self.origins),
                       ('methods', self.methods),
                       ('request_headers', self.request_headers),
                       ('exposed_response_headers',
                        self.exposed_response_headers),
                       ('client_preflight_cache_lifespan',
                        self.client_preflight_cache_lifespan)))

    @classmethod
    def _property_displayname(cls, name):
        return name.replace('_', ' ')


class CorsAffordanceSetMap(_coll.HereditaryWebResourcePathMapping):
    """A cross-origin resource sharing affordances map

    This is a mapping from resource locations to specifications of their
    cross-origin request sharing affordances.  In addition to the basic
    mutable mapping functionality, it also

      * accepts path patterns in the form of strings or regular
        expressions and

      * ensures that that its items have valid types and values.

    .. seealso::
        :class:`~bedframe._collections.HereditaryResourcePathMapping`

    """
    def __init__(self, *args, **kwargs):
        super(CorsAffordanceSetMap, self).__init__(*args,
                                                   valuetype=CorsAffordanceSet,
                                                   **kwargs)


CorsRequestType = _enum('CORS request type', ('preflight', 'actual'))
