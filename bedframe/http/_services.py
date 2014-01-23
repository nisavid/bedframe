"""Web services"""

__copyright__ = "Copyright (C) 2014 Ivan D Vasin"
__docformat__ = "restructuredtext"

import abc as _abc
import httplib as _httplib
import logging as _logging
import re as _re
from urllib import unquote_plus as _percent_plus_decode
from urlparse \
    import parse_qs as _parse_urlencoded, \
           urlsplit as _urlsplit, \
           urlunsplit as _urlunsplit

import spruce.http as _http
import spruce.http.status as _http_status
import ujson as _json

from .. import _debug
from .. import _exc as _bedframe_exc
from .. import _services
from ..auth import http as _http_auth
from . import _exc


class HttpService(_services.WebServiceImpl):

    """A web service that uses HTTP


    **Multi-purpose POST**

    The :rfc:`HTTP message body specification <2616#section-4.3>` recommends
    to ignore message bodies for HTTP methods that do not specify semantics
    for entity bodies.  This class adheres to this recommendation.

    This leaves those methods with one way to pass data to the server: the
    URI query string.  But some clients and some servers do not handle URIs
    that are over some length.  The :rfc:`HTTP URI syntax specification \
    <2616#section-3.2.1>` recommends,

        Servers ought to be cautious about depending on URI lengths above
        255 bytes, because some older client or proxy implementations might
        not properly support these lengths.

    To overcome this limitation, this class exposes the web methods that
    correspond to the affected HTTP methods as HTTP POST requests in which
    the query string starts with the name of the web method, separated from
    the rest of the query string by ``&`` if applicable.  By passing data in
    the bodies of such HTTP POST requests, clients can avoid the URI length
    limitation.

    This applies to the following web methods, which are shown with their
    naturally corresponding HTTP methods and POST query string prefixes:

        ================= ====== =============
        |Resource method| HTTP   POST query
                          method string prefix
        ================= ====== =============
        |Resource.get|    GET    ``get``
        ================= ====== =============

    .. |Resource method| replace::
        :class:`bedframe.WebResource
        <bedframe._resources._core.WebResource>` method

    .. |Resource.get| replace::
        :meth:`bedframe.WebResource.get() \
               <bedframe._resources._core.WebResource.get>`

    When interacting with these :class:`bedframe.WebResource
    <bedframe._resources._core.WebResource>` methods via this service,
    clients should use the naturally corresponding HTTP methods with query
    arguments for requests whose URIs are 255 characters long or less, and
    they should use HTTP POST with body arguments and the corresponding
    query string prefix for requests with longer URIs.

    For example, with short arguments a request might look like ::

        GET /widgets/bar?a=1&b=2

    With arguments that would result in a long URI, a request to the same
    resource might look like ::

        POST /widgets/bar?get

        {
            "hash0":
                "f974901ff661b943a83870af043496b4614b4ebfdb9e8662cab2876ec8adcdc9fcde8f19ec83afac66156a6fa904e3abdeb6bc82615152f3022883aae65384de"
            "hash1":
                "2597050bf7724b838790f9c935a7fa51246ed3efc82290585bfcbe82324a16f59da62076eaa9cc05d8696e801c1aa509c39a9e3cad2e7d50b9407ed0ef4d8f0c"
        }

    """

    __metaclass__ = _abc.ABCMeta

    def __init__(self, uris, session_auth_manager=None, **kwargs):

        if not uris:
            raise ValueError('invalid HTTP service URIs: expecting a sequence'
                              ' of HTTP URIs')

        canon_uris = []
        for uri in uris:
            uri_parts = _urlsplit(uri)
            netloc = uri_parts.netloc if uri_parts.port is not None \
                                      else '{}:{}'.format(uri_parts.netloc,
                                                          _httplib.HTTP_PORT)
            canon_uris.append(_urlunsplit((uri_parts.scheme, netloc,
                                           uri_parts.path, uri_parts.query,
                                           uri_parts.fragment)))

        super(HttpService, self).__init__(uris=canon_uris, **kwargs)

        self._session_auth_manager = \
            session_auth_manager \
            or _http_auth.HttpSessionManager(service=self)

    @property
    def session_auth_manager(self):
        return self._session_auth_manager

    @classmethod
    def _acceptable_mediaranges(cls, accept_patterns):

        ranges_qvalues = []

        # use insertion sort because it's simple, it has minimal memory
        # footprint, and we presume that the number of patterns will always be
        # small
        def add_range(range, qvalue):
            for i, (other_range, other_qvalue) in enumerate(ranges_qvalues):
                if qvalue > other_qvalue:
                    ranges_qvalues.insert(i, (range, qvalue))
                    return
            ranges_qvalues.append((range, qvalue))

        for pattern in accept_patterns:
            qvalue = 1.

            params_match = _re.match(r'\s*([^\s;]+)\s*;\s*(.*)\s*$', pattern)
            if params_match:
                range_ = params_match.group(1)
                params = _re.split(r'\s*;\s*', params_match.group(2))
                for param in params:
                    name, _, value = param.partition('=')
                    if name == 'q':
                        qvalue = float(value)
                        # 'q' and all params after it are Accept params; we
                        # only support 'q', so ignore the rest
                        break
                    else:
                        range_ += ';{}={}'.format(name, value)

            else:
                range_ = pattern

            add_range(range_, qvalue=qvalue)

        return [range_ for range_, _ in ranges_qvalues]

    @classmethod
    def _exc_http_statuscode(cls, exc=None):

        """The HTTP response status code for an exception

        If *exc* is one of the :mod:`Bedframe exceptions <bedframe._exc>` that
        corresponds to an HTTP response status code, then that code is
        returned.  Otherwise the result is a generic error code.

        :param exc:
            An exception.
        :type exc: :class:`Exception` or null

        :rtype: :obj:`int`

        """

        statuscode = _http_status.INTERNAL_SERVER_ERROR

        if exc:
            if isinstance(exc, _bedframe_exc.UnhandledException):
                exc = exc.exc

            if isinstance(exc, Exception):
                exc_class = exc.__class__
            elif issubclass(exc, Exception):
                exc_class = exc
            else:
                _logging.warning('invalid exception {!r}; falling back to'
                                  ' status code {}'
                                  .format(exc, statuscode))
                return statuscode

            for known_exc_class, known_statuscode \
                    in cls._HTTP_STATUS_CODE_BY_EXC_CLASS.items():
                if issubclass(exc_class, known_exc_class):
                    statuscode = known_statuscode

        return statuscode

    _HTTP_STATUS_CODE_BY_EXC_CLASS = \
        {_bedframe_exc.AccessForbidden: _http_status.FORBIDDEN,
         _bedframe_exc.BadRequest: _http_status.BAD_REQUEST,
         _bedframe_exc.EntityChoiceRedirection: _http_status.MULTIPLE_CHOICES,
         _bedframe_exc.EntityUnchanged: _http_status.NOT_MODIFIED,
         _exc.HttpMethodNotAllowed: _http_status.METHOD_NOT_ALLOWED,
         _bedframe_exc.NoAcceptableMediaType: _http_status.NOT_ACCEPTABLE,
         _bedframe_exc.NotImplementedError: _http_status.NOT_IMPLEMENTED,
         _bedframe_exc.PermanentRedirection: _http_status.PERMANENT_REDIRECT,
         _bedframe_exc.ProxyRedirection: _http_status.USE_PROXY,
         _bedframe_exc.ResourceConflict: _http_status.CONFLICT,
         _bedframe_exc.ResourceNotFound: _http_status.NOT_FOUND,
         _bedframe_exc.ResponseRedirection: _http_status.SEE_OTHER,
         _bedframe_exc.TemporaryRedirection: _http_status.TEMPORARY_REDIRECT,
         TypeError: _http_status.BAD_REQUEST,
         _bedframe_exc.Unauthenticated: _http_status.UNAUTHORIZED,
         ValueError: _http_status.BAD_REQUEST,
         }

    def _mediarange_arg_prim_fromjson(self, name, json):
        return self._arg_prim_fromjson(name, json)

    @classmethod
    def _natural_httpmethod(cls, webmethodname):
        """The HTTP method that naturally corresponds to a web method name

        :param str webmethodname:
            The name of a web method.

        :rtype: :obj:`str`

        """
        return webmethodname.upper()

    def _pathpart_arg_prim_fromjson(self, name, json):
        return self._arg_prim_fromjson(name, json,
                                       fallback_to_passthrough=True)

    def _pathpart_prim_fromjson(self, name, json):
        return self._arg_prim_fromjson(name, json,
                                       fallback_to_passthrough=True)

    def _query_arg_prim_fromjson(self, name, json):
        return self._arg_prim_fromjson(name, json,
                                       fallback_to_passthrough=True)

    def _query_arg_prim_frompercentjson(self, name, percentjson):
        return self._query_arg_prim_fromjson(name,
                                             _percent_plus_decode(percentjson))

    def _request_body_args_prims_from_json(self, json):
        if json:
            if _re.match(r'\A\s*{(.*)}\s*\Z', json,
                         _re.DOTALL | _re.MULTILINE):
                json = json.strip()
                try:
                    return _json.loads(json)
                except ValueError:
                    pass

            if _debug.DEBUG_EXC_TRACEBACK_INCLUDING_SERVICE_CODE \
                   in self.debug_flags:
                traceback = True
            else:
                traceback = None

            raise _bedframe_exc.unhandled_exception\
                      (_bedframe_exc.BadRequest
                        ('invalid request body; expecting a JSON object whose'
                          ' fields are request arguments'),
                       traceback=traceback,
                       show_unhandled=False)
        else:
            return {}

    def _request_body_args_prims_from_urlencoded(self, urlencoded):
        if urlencoded:
            return {name: self._arg_prim_fromjson(name, values_jsons[0],
                                              fallback_to_passthrough=True)
                    for name, values_jsons
                    in _parse_urlencoded(urlencoded, keep_blank_values=True,
                                         strict_parsing=True)
                        .items()}
        else:
            return {}

    def _request_body_args_prims_frombody(self, body, mediatype, httpmethod):

        # CAVEAT: handle the request body only for HTTP methods that define
        #   semantics for the body.  :rfc:`2616#section-4.3` recommends to
        #   ignore message bodies for methods that do not specify semantics for
        #   entity bodies
        if not _http.method_defines_body_semantics(httpmethod):
            return {}

        try:
            mediatype_name, _, _ = mediatype.partition(';')
            meth = self._request_body_args_prims_frombody_meth_by_mediatype\
                    [mediatype_name]
        except KeyError:
            supported_mediatypes = \
                self._request_body_args_prims_frombody_func_by_mediatype.keys()
            raise ValueError('unsupported body media type {!r}: expecting one'
                              ' of {}'
                              .format(mediatype, supported_mediatypes))
        return meth(self, body)

    _request_body_args_prims_frombody_meth_by_mediatype = {}

    @classmethod
    def _request_webmethodname(cls, httpmethod, path, query):

        if httpmethod == 'HEAD':
            return 'get'

        # CAVEAT: examine the query string to convert HTTP POST to calls to
        #   corresponding web method names whose HTTP implementations do not
        #   reliably support message bodies
        if httpmethod == 'POST':
            query_method_pattern = r'^{}(&|$)'
            for name in (cls._webmethodname(httpmethod)
                         for httpmethod in _http.METHODS
                         if not _http.method_defines_body_semantics
                                    (httpmethod)):
                if _re.match(query_method_pattern.format(name), query):
                    return name

        return httpmethod.lower()

    @classmethod
    def _supported_httpmethods(cls, webmethodnames):

        """The HTTP methods that should be supported by this service

        .. note::
            This does not return the same result as calling
            :meth:`_natural_httpmethod` on each of the given *webmethodnames*.
            Some allowed web methods imply support for more than their
            naturally corresponding HTTP method.

        :param webmethodnames:
            The names of the supported web methods.
        :type webmethodnames: ~[:obj:`str`]

        :rtype: {:obj:`str`}

        """

        httpmethods = {cls._natural_httpmethod(methodname)
                       for methodname in webmethodnames}

        # CAVEAT: expose HTTP POST as a means to submit long arguments to web
        #   methods whose HTTP implementations do not reliably support message
        #   bodies
        if any(not _http.method_defines_body_semantics(method)
               for method in httpmethods):
            httpmethods.add('POST')

        if 'GET' in httpmethods:
            httpmethods.add('HEAD')

        return httpmethods

    @classmethod
    def _webmethodname(cls, httpmethod):
        """The web method name that corresponds to an HTTP method

        :param str httpmethod:
            An HTTP method.

        :rtype: :obj:`str`

        """
        return httpmethod.lower()

HttpService\
 ._request_body_args_prims_frombody_meth_by_mediatype\
 .update({'application/json': HttpService._request_body_args_prims_from_json,
          'application/x-www-form-urlencoded':
              HttpService._request_body_args_prims_from_urlencoded})
