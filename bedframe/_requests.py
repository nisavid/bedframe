"""Web service requests

This module facilitates processing requests on the server side.

.. seealso::
    For client-side request handling objects, see :mod:`the corresponding
    Napper module <napper._requests>`.

"""

__copyright__ = "Copyright (C) 2014 Ivan D Vasin"
__docformat__ = "restructuredtext"

from . import auth as _auth


class WebRequest(object):

    """A web service request

    :param service:
        The web service.
    :type service: :class:`~bedframe._services.WebServiceImpl`

    :param str loc:
        The requested resource location.

    :param resource:
        The requested resource.
    :type resource: :class:`~bedframe._resources._core.WebResource`

    :param method:
        The requested web method.
    :type method: :class:`~bedframe._methods.WebMethod`

    :param method_args_prims:
        Primitive representations of the request's web method arguments.
    :type args_prims: {:obj:`str`: :obj:`object`}

    :param auth_info:
        Authentication information about the requesting user.
    :type auth_info:
        :class:`bedframe.auth.RequestAuthInfo \
                <bedframe.auth._info.RequestAuthInfo>`

    """

    def __init__(self,
                 service,
                 uri,
                 loc,
                 resource,
                 method,
                 acceptable_mediaranges,
                 timestamp,
                 impl_method,
                 resource_args_prims=None,
                 method_args_prims=None,
                 auth_info=None):
        self._acceptable_mediaranges = acceptable_mediaranges
        self._auth_info = auth_info or _auth.RequestAuthInfo()
        self._impl_method = impl_method
        self._loc = loc
        self._method = method
        self._method_args_prims = method_args_prims
        self._resource = resource
        self._resource_args_prims = resource_args_prims
        self._service = service
        self._timestamp = timestamp
        self._uri = uri

    @property
    def acceptable_mediaranges(self):
        """The media type ranges that are acceptable to the client

        :type: ~[str]

        """
        return self._acceptable_mediaranges

    @property
    def auth_info(self):
        """Authentication information for the current request

        :type: :class:`bedframe.auth.RequestAuthInfo \
                       <bedframe.auth._info.RequestAuthInfo>`

        """
        return self._auth_info

    @auth_info.setter
    def auth_info(self, value):
        self._auth_info = value

    @property
    def auth_space(self):
        """The authentication space

        :type: :class:`bedframe.auth.Space <bedframe.auth._spaces.Space>`

        """
        return self.service.auth_spaces[self.loc]

    def ensure_auth(self, **kwargs):
        """Ensure authentication

        .. seealso::
            :meth:`bedframe.WebServiceImpl.ensure_auth() \
                   <bedframe._services.WebServiceImpl.ensure_auth>`

        """
        self.service.ensure_auth(loc=self.loc, **kwargs)

    def has_auth(self, **kwargs):
        """Whether this request is authenticated

        .. seealso::
            :meth:`bedframe.WebServiceImpl.has_auth() \
                   <bedframe._services.WebServiceImpl.has_auth>`

        """
        return self.service.has_auth(loc=self.loc, **kwargs)

    @property
    def impl_method(self):
        return self._impl_method

    @property
    def loc(self):
        """The requested location

        :type: :obj:`str`

        """
        return self._loc

    @property
    def method(self):
        """The requested :term:`web method`

        :type: :class:`~bedframe._methods.WebMethod`

        """
        return self._method

    @property
    def method_args_prims(self):
        """Primitive representations of the requested web method arguments

        :type: {:obj:`str`: :obj:`object`}

        """
        return self._method_args_prims

    @property
    def resource(self):
        """The requested :term:`web resource`

        :type: :class:`~bedframe._resources._core.WebResource`

        """
        return self._resource

    @property
    def resource_args_prims(self):
        """Primitive representations of the requested web resource arguments

        :type: {:obj:`str`: :obj:`object`}

        """
        return self._resource_args_prims

    @property
    def service(self):
        """The web service

        :type: :class:`~bedframe._services.WebServiceImpl`

        """
        return self._service

    @property
    def timestamp(self):
        """The timestamp

        If the request specifies the date and time at which it was originated,
        then that should be used as the timestamp.  Otherwise, the timestamp
        should be the date and time at which the request was received.

        :type: :class:`datetime.datetime`

        """
        return self._timestamp

    @property
    def uri(self):
        """The requested URI

        :type: :obj:`str`

        """
        return self._uri
