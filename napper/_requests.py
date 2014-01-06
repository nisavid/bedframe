"""Web service requests.

This module facilitates constructing requests on the client side, sending
them to a server, and processing the subsequent responses.

.. seealso::
    For server-side request handling objects, see :mod:`the corresponding
    Bedframe module <bedframe._requests>`.

"""

__copyright__ = "Copyright (C) 2014 Ivan D Vasin"
__docformat__ = "restructuredtext"

import re as _re
from urllib import urlencode as _urlencode
from urlparse import urljoin as _urljoin

import bedframe.webtypes as _webtypes
import requests as _requests
import requests.auth as _requests_auth
from spruce.collections import odict as _odict
import spruce.http as _http
from spruce.lang import bool as _bool


def extract_retval(response, type):
    """Extract a native return value object from a JSON return response.

    :param response:
        A return response with JSON content.
    :type response: :class:`requests.Response <requests.models.Response>`

    :param type:
        The webtype of the result.
    :type type: :class:`bedframe.webtypes.webobject
                        <bedframe.webtypes._core.webobject>`

    :rtype: :obj:`object`

    """
    return type.fromprim(response.json()['retval']).native()


def request(*args, **kwargs):
    """

    .. seealso:: :meth:`WebRequest.from_resource`, :func:`send_request`

    """
    send_kwargs, rest_kwargs = _extract_send_kwargs(**kwargs)
    return send_request(WebRequest.from_resource(*args, **rest_kwargs),
                        **send_kwargs)


def request_args_from_resource(method, service, resource, *args, **kwargs):
    """

    :rtype:
        (:func:`str`, :func:`str`, :obj:`object`\ ...),
        {:func:`str`: :obj:`object`}

    """
    uri = _urljoin(service + ('/' if not service.endswith('/') else ''),
                   resource)
    postext_match = _re.match('post(.+)', method)
    if postext_match:
        method = 'post'
        uri += '?' + postext_match.group(1)
    return (method, uri) + args, kwargs


def request_cors_preflight(*args, **kwargs):
    """

    .. seealso::
        :meth:`WebRequest.cors_preflight_from_resource`,
        :func:`send_request`

    """
    send_kwargs, rest_kwargs = _extract_send_kwargs(**kwargs)
    return send_request(WebRequest.cors_preflight_from_resource(*args,
                                                                **rest_kwargs),
                        **send_kwargs)


def request_uri(*args, **kwargs):
    """

    .. seealso:: :class:`WebRequest`, :func:`send_request`

    """
    send_kwargs, rest_kwargs = _extract_send_kwargs(**kwargs)
    return send_request(WebRequest(*args, **rest_kwargs), **send_kwargs)


def request_uri_cors_preflight(*args, **kwargs):
    """

    .. seealso:: :meth:`WebRequest.cors_preflight`, :func:`send_request`

    """
    send_kwargs, rest_kwargs = _extract_send_kwargs(**kwargs)
    return send_request(WebRequest.cors_preflight(*args, **rest_kwargs),
                        **send_kwargs)


def send_request(request, session=None, timeout=6., verify_server_cert=True):
    """

    .. seealso:: :meth:`requests.Session.send`

    """
    if not session:
        session = _requests.Session()
    return session.send(request.prepare(), timeout=timeout,
                        verify=verify_server_cert)


class WebRequest(_requests.Request):

    """A web service request."""

    def __init__(self,
                 method,
                 uri,
                 args=None,
                 argtypes=None,
                 args_as=None,
                 accept_mediaranges=('application/json', '*/*; q=0.01'),
                 auth=None,
                 authtype='basic',
                 origin=None,
                 headers=None,
                 **kwargs):

        method_kwargs = {}

        headers = _odict(headers or ())
        method_kwargs['headers'] = headers
        if origin is not None:
            headers['Origin'] = origin
        headers.setdefault('Accept', ', '.join(accept_mediaranges))

        if args:
            if argtypes:
                untyped_args = [arg for arg in args if arg not in argtypes]
            else:
                untyped_args = args.keys()
            if untyped_args:
                raise ValueError('missing type specifications for request'
                                  ' arguments {}'.format(untyped_args))

            if args_as is None:
                if _http.method_defines_body_semantics(method.upper()):
                    args_as = 'body'
                else:
                    args_as = 'query'

            if args_as == 'query':
                args_json = {name: argtypes[name](value).json()
                             for name, value in args.items()}
                method_kwargs['params'] = args_json

            elif args_as == 'body':
                args_webobjects = {name: argtypes[name](value)
                                   for name, value in args.items()}
                body = _webtypes.json_dumps(args_webobjects)
                method_kwargs['data'] = body

                headers['Content-Type'] = 'application/json'

            elif args_as == 'body_urlencoded':
                args_json = {name: argtypes[name](value).json()
                             for name, value in args.items()}
                body = _urlencode(args_json)
                method_kwargs['data'] = body

                headers['Content-Type'] = 'application/x-www-form-urlencoded'

            else:
                raise ValueError('invalid argument mechanism {!r}; expected'
                                  ' one of {}'
                                  .format(args_as,
                                          ('query', 'body',
                                           'body_urlencoded')))

        if auth is not None:
            try:
                auth_class = _requests_auth_classmap[authtype]
            except KeyError:
                raise ValueError('invalid authentication type {!r}; expected'
                                  ' one of {}'
                                  .format(authtype, ('basic', 'digest')))
            method_kwargs['auth'] = auth_class(*auth)

        method_kwargs.update(kwargs)

        super(WebRequest, self).__init__(method, uri, **method_kwargs)

    @classmethod
    def cors_preflight(cls, method, uri, args=None, origin=None,
                       accept_mediaranges=('application/json', '*/*; q=0.01'),
                       auth=None, headers=None, *args_, **kwargs):

        if origin is None:
            raise TypeError('missing origin')

        headers = _odict(headers or ())
        preflight_headers = {'Access-Control-Request-Method': method}
        if headers:
            preflight_headers['Access-Control-Request-Headers'] = \
                ', '.join((name.lower() for name in headers.keys()))
            try:
                preflight_headers['Accept'] = headers['Accept']
            except KeyError:
                pass

        return cls('options', uri, *args_, origin=origin,
                   accept_mediaranges=accept_mediaranges,
                   headers=preflight_headers, **kwargs)

    @classmethod
    def cors_preflight_from_resource(cls, method, service, resource, *args,
                                     **kwargs):
        args_, kwargs_ = request_args_from_resource(method, service, resource,
                                                    *args, **kwargs)
        return cls.cors_preflight(*args_, **kwargs_)

    @classmethod
    def from_resource(cls, method, service, resource, *args, **kwargs):
        args_, kwargs_ = request_args_from_resource(method, service, resource,
                                                    *args, **kwargs)
        return cls(*args_, **kwargs_)


class WebRequestSession(_requests.Session):

    def __init__(self, follow_redirects=True, *args, **kwargs):
        super(WebRequestSession, self).__init__(*args, **kwargs)
        self.follow_redirects = follow_redirects

    @property
    def follow_redirects(self):
        return self._follow_redirects

    @follow_redirects.setter
    def follow_redirects(self, value):
        self._follow_redirects = _bool(value)

    def resolve_redirects(self, resp, *args, **kwargs):
        if self.follow_redirects:
            return super(WebRequestSession, self)\
                    .resolve_redirects(resp, *args, **kwargs)
        else:
            return (resp,)


def _extract_send_kwargs(**kwargs):
    send_kwargs = {}
    rest_kwargs = {}
    for name, value in kwargs.items():
        if name in ('session', 'timeout', 'verify_server_cert'):
            send_kwargs[name] = value
        else:
            rest_kwargs[name] = value
    return send_kwargs, rest_kwargs


_requests_auth_classmap = {'basic': _requests_auth.HTTPBasicAuth,
                           'digest': _requests_auth.HTTPDigestAuth}
