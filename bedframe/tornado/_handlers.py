"""Request handlers"""

__copyright__ = "Copyright (C) 2014 Ivan D Vasin"
__docformat__ = "restructuredtext"

from datetime import datetime as _datetime
import re as _re
import sys as _sys
from urllib import unquote_plus as _percent_plus_decode
from urlparse import urlsplit as _urisplit

from spruce.collections import odict as _odict, oset as _oset
from spruce.datetime import now_localtime as _now_localtime
from spruce.lang import bool as _bool
import spruce.logging as _logging
from spruce.pprint import indented as _indented
import tornado.web as _tnd_web

from .. import http as _http
from .. import _cors
from .. import _debug
from .. import _exc
from .. import _requests


class TornadoRequestHandler(_tnd_web.RequestHandler):

    def __init__(self, *args, **kwargs):
        super(TornadoRequestHandler, self).__init__(*args, **kwargs)
        self._bedframe_request = None
        self._client_disconnected = True
        self._cors_expose_all_response_headers_ = False
        self._request_acceptable_mediaranges = None
        self._request_body_args_prims = None
        self._request_cors_affordances = None
        self._request_cors_request_type = None
        self._request_pathparts_jsons_ = None
        self._request_pathparts_prims = None
        self._request_query_args_prims = None
        self._request_resource = None
        self._request_resource_args_prims = None
        self._request_timestamp = None
        self._request_webmethod = None
        self._request_webmethod_args_prims = None

    @property
    def bedframe_request(self):
        if self._bedframe_request is None:
            self._bedframe_request = \
                _requests.WebRequest(service=self.service,
                                     uri=self.request.uri,
                                     loc=self.request.path,
                                     resource=self.request_resource,
                                     method=self.request_webmethod,
                                     acceptable_mediaranges=
                                         self.request_acceptable_mediaranges,
                                     timestamp=self.request_timestamp,
                                     impl_method=self.request.method,
                                     resource_args_prims=
                                         self.request_resource_args_prims,
                                     method_args_prims=
                                         self.request_webmethod_args_prims)
        return self._bedframe_request

    @property
    def client_disconnected(self):
        return self._client_disconnected

    def finish(self, *args, **kwargs):

        if self._cors_expose_all_response_headers:
            # XXX: use ``self._headers`` because
            #   :class:`tornado.web.RequestHandler` doesn't otherwise expose
            #   the response headers
            self.set_header('Access-Control-Expose-Headers',
                            ', '.join(self._headers.keys()))

        try:
            super(TornadoRequestHandler, self).finish(*args, **kwargs)
        except IOError:
            if self.client_disconnected:
                return
            else:
                raise

    def get_new_cookie(self, name, default=None):
        try:
            return self._new_cookie[name].value
        except (AttributeError, KeyError):
            return self.get_cookie(name, default=default)

    @property
    def logger(self):
        return self.service.logger

    def on_connection_close(self):
        self._client_disconnected = True

    @property
    def request_acceptable_mediaranges(self):
        if self._request_acceptable_mediaranges is None:
            try:
                accept_header = self.request.headers['Accept']
            except KeyError:
                accept_header = '*'
            accept_patterns = [pattern.strip()
                               for pattern in accept_header.split(',')]
            self._request_acceptable_mediaranges = \
                self.service._acceptable_mediaranges(accept_patterns)
        return self._request_acceptable_mediaranges

    @property
    def request_body_args_prims(self):
        if self._request_body_args_prims is None:
            try:
                mediatype = self.request.headers['Content-Type']
            except KeyError:
                self._request_body_args_prims = {}
            else:
                self._request_body_args_prims = \
                    self.service\
                     ._request_body_args_prims_frombody\
                     (self.request.body, mediatype=mediatype,
                      httpmethod=self.request.method)
        return self._request_body_args_prims

    @property
    def request_cors_affordances(self):
        if self._request_cors_affordances is None:
            try:
                self._request_cors_affordances = \
                    self.service.cors_affordancesets[self.request.path]
            except KeyError:
                raise _exc.CorsPolicyUndefined(self.request_resource,
                                               self.request_origin)
        return self._request_cors_affordances

    @property
    def request_cors_request_type(self):
        if self._request_cors_request_type is None:
            if self.request_origin is None:
                pass
            elif self.request_webmethod.name == 'options' \
                 and 'Access-Control-Request-Method' \
                     in self.request.headers:
                self._request_cors_request_type = \
                    _cors.CorsRequestType('preflight')
            else:
                request_origin_parts = _urisplit(self.request_origin)
                if not (request_origin_parts.scheme == self.request.protocol
                        and request_origin_parts.netloc == self.request.host):
                    self._request_cors_request_type = \
                        _cors.CorsRequestType('actual')
        return self._request_cors_request_type

    @property
    def request_origin(self):
        return self.request.headers.get('Origin', None)

    @property
    def request_pathparts_prims(self):
        if self._request_pathparts_prims is None:
            self._request_pathparts_prims = \
                {name: self.service._pathpart_prim_fromjson(name, json)
                 for name, json in self._request_pathparts_jsons.items()}
        return self._request_pathparts_prims

    @property
    def request_pathpart_args_prims(self):
        return _odict(self.request_pathpart_args_prims_items_iter)

    @property
    def request_pathpart_args_prims_items_iter(self):
        for name, json in self._request_pathpart_args_jsons_items_iter:
            yield (name, self.service._pathpart_arg_prim_fromjson(name, json))

    @property
    def request_query_args_prims(self):
        if self._request_query_args_prims is None:
            self._request_query_args_prims = \
                {name: self.service._query_arg_prim_frompercentjson(name, json)
                 for name, json
                 in [arg_with_json.split('=',1)
                     for arg_with_json
                     in sum((a.split(';')
                             for a in self.request.query.split('&')
                             if '=' in a),
                            [])]}
        return self._request_query_args_prims

    @property
    def request_resource(self):
        return self._request_resource

    @property
    def request_resource_args_prims(self):
        if self._request_resource_args_prims is None:
            self._request_resource_args_prims = {}
            self._request_resource_args_prims\
                .update(self.request_pathparts_prims)
            self._request_resource_args_prims\
                .update(self.request_pathpart_args_prims)
        return self._request_resource_args_prims

    @property
    def request_timestamp(self):
        return self._request_timestamp

    @property
    def request_webmethod(self):
        if self._request_webmethod is None:
            webmethodname = \
                self.service._request_webmethodname(self.request.method,
                                                    self.request.path,
                                                    self.request.query)
            try:
                webmethod = getattr(self.request_resource, webmethodname)
            except AttributeError:
                if self.request.method \
                       in self.service._all_supported_httpmethods:
                    raise _http.HttpMethodNotAllowed\
                           (self.request.method,
                            allowed_httpmethods=
                                self.service._all_supported_httpmethods)
                else:
                    raise _exc.WebMethodNotImplemented\
                           (self.request.method,
                            allowed_webmethods=self.request_resource
                                                   .allowed_webmethodnames)
            self._request_webmethod = \
                webmethod.withtypes(self.request_acceptable_mediaranges)
        return self._request_webmethod

    @property
    def request_webmethod_args_prims(self):
        if self._request_webmethod_args_prims is None:
            self._request_webmethod_args_prims = {}
            self._request_webmethod_args_prims\
                .update(self.request_query_args_prims)
            self._request_webmethod_args_prims\
                .update(self.request_body_args_prims)
        return self._request_webmethod_args_prims

    @property
    def _cors_expose_all_response_headers(self):
        return self._cors_expose_all_response_headers_

    @_cors_expose_all_response_headers.setter
    def _cors_expose_all_response_headers(self, value):
        self._cors_expose_all_response_headers_ = _bool(value)

    def _ensure_cors_actual_request_allowed(self):

        assert self.request_cors_request_type \
               == _cors.CorsRequestType('actual')

        self._ensure_request_origin_allowed()

        origin = self.request_origin
        affordances = self.request_cors_affordances

        request_httpmethod = self.request.method.lower()
        if request_httpmethod not in affordances.methods:
            raise _exc.CorsMethodForbidden(self.request_resource,
                                           origin,
                                           self.request.httpmethod,
                                           cors_request_type=
                                               _cors.CorsRequestType('actual'),
                                           affordances=affordances)

        forbidden_request_headers = _oset(self.request.headers.keys()) \
                                    - affordances.request_headers
        if forbidden_request_headers:
            raise _exc.CorsHeadersForbidden\
                   (self.request_resource, origin, forbidden_request_headers,
                    cors_request_type=_cors.CorsRequestType('actual'),
                    affordances=affordances)

        self.set_header('Access-Control-Allow-Origin', self.request_origin)
        if self.request.path in self.service.auth_spaces:
            self.set_header('Access-Control-Allow-Credentials', 'true')
        if affordances.exposed_response_headers.isfinite:
            self.set_header('Access-Control-Expose-Headers',
                            affordances.exposed_response_headers)
        else:
            self.cors_expose_all_response_headers = True

    def _ensure_cors_preflight_request_allowed(self):

        assert self.request_cors_request_type \
               == _cors.CorsRequestType('preflight')

        self._ensure_request_origin_allowed()

        origin = self.request_origin
        affordances = self.request_cors_affordances

        preflight_requested_method = \
            self.request.headers['Access-Control-Request-Method']
        if preflight_requested_method not in affordances.methods:
            raise _exc.CorsMethodForbidden\
                   (self.request_resource, origin, preflight_requested_method,
                    cors_request_type=_cors.CorsRequestType('preflight'),
                    affordances=affordances)

        try:
            preflight_requested_headers = \
                [part.strip()
                 for part
                 in self.request
                        .headers['Access-Control-Request-Headers']
                        .split(',')]
        except KeyError:
            preflight_requested_headers = ()
        allowed_requested_headers = _oset()
        forbidden_requested_headers = _oset()
        for header in preflight_requested_headers:
            if header in affordances.request_headers:
                allowed_requested_headers.add(header)
            else:
                forbidden_requested_headers.add(header)
        if forbidden_requested_headers:
            raise _exc.CorsHeadersForbidden\
                   (self.request_resource, origin, forbidden_requested_headers,
                    cors_request_type=_cors.CorsRequestType('preflight'),
                    affordances=affordances)

        self.set_header('Access-Control-Allow-Origin', origin)
        if self.request.path in self.service.auth_spaces:
            self.set_header('Access-Control-Allow-Credentials', 'true')
        if affordances.client_preflight_cache_lifespan is not None:
            self.set_header('Access-Control-Max-Age',
                            affordances.client_preflight_cache_lifespan
                                       .total_seconds())
        self.set_header('Access-Control-Allow-Methods',
                        ', '.join(affordances.methods
                                  & set(self.SUPPORTED_METHODS)))
        if allowed_requested_headers:
            self.set_header('Access-Control-Allow-Headers',
                            ', '.join(allowed_requested_headers))

    def _ensure_request_cors_allowed(self):
        if self.request_cors_request_type \
               == _cors.CorsRequestType('preflight'):
            self._ensure_cors_preflight_request_allowed()
        elif self.request_cors_request_type \
                 == _cors.CorsRequestType('actual'):
            self._ensure_cors_actual_request_allowed()

    def _ensure_request_origin_allowed(self):
        if self.request_origin not in self.request_cors_affordances.origins:
            raise _exc.CorsOriginForbidden\
                   (self.request_resource, self.request_origin,
                    cors_request_type=self.request_cors_request_type,
                    affordances=self.request_cors_affordances)

    def _handle_request(self):

        self.logger.cond((_logging.DEBUG,
                          self._request_received_debuglog_message))

        with self.request_webmethod.resource.provided_by_service(self.service):
            try:
                self._ensure_request_cors_allowed()

                # FIXME: obey Accept-Charset header

                # FIXME: obey Accept-Encoding header

                # FIXME: obey TE header

                # FIXME: obey If-Modified-Since, If-Unmodified-Since headers

                # FIXME: obey If-Match, If-None-Match headers

                # FIXME: obey Expect header

                # FIXME: obey Range header

            except _exc.CorsRequestRejected as exc:
                raise _exc.WebMethodException\
                       (self.request_webmethod, exc, _sys.exc_info()[2],
                        traceback_entries_filter=
                            self._service_code_traceback_entries)

            self._send_webmethod_response()

    @property
    def _ordered_pathpart_arg_sep(self):
        return self.service.resources.ordered_arg_sep

    @property
    def _pathsep(self):
        return self.service.resources.pathsep

    def _service_code_traceback_entries(self, traceback_entries, debug_flags):
        if _debug.DEBUG_EXC_TRACEBACK_INCLUDING_SERVICE_CODE \
                in self.service.debug_flags:
            return traceback_entries
        else:
            return ()

    @property
    def _request_pathparts_jsons(self):
        return self._request_pathparts_jsons_

    @property
    def _request_pathpart_arg_clause_re(self):
        return _re.compile\
                (r'[{argseps}](?P<name>[a-zA-Z_]\w*)='
                  r'(?P<value>[^{seps}]*)'
                  .format(argseps=''.join((self._ordered_pathpart_arg_sep,
                                           self._unordered_pathpart_arg_sep)),
                          seps=''.join((self._pathsep,
                                        self._ordered_pathpart_arg_sep,
                                        self._unordered_pathpart_arg_sep))))

    @property
    def _request_pathpart_args_jsons(self):
        return _odict(self._request_pathpart_args_jsons_items_iter)

    @property
    def _request_pathpart_args_jsons_items_iter(self):
        for match in self._request_pathpart_arg_clause_re\
                         .finditer(self.request.path):
            yield (match.group('name'),
                   _percent_plus_decode(match.group('value')))

    def _request_received_debuglog_message(self):
        message = '{} {} {}'.format(self.request.remote_ip,
                                    self.request.method, self.request.path)
        if self.request.arguments:
            args_strs = ['{}: {}'.format(name, value[0])
                         for name, value in self.request.arguments.items()]
            message += ' {{{}}}'.format(', '.join(args_strs))
        message += ' {!r}'.format(self.request.headers['Accept'])
        if self.request.body:
            message += '\n' + _indented(self.request.body, size=2)
        return message

    def _send_response(self, response):

        # FIXME: send Accept-Ranges header

        # FIXME: send Allow header

        # FIXME: send Cache-Control header

        # FIXME: send Content-Range header (if applicable)

        # FIXME: send Expires header (if applicable)

        # FIXME: send ETag header with persistent value (if applicable)

        # FIXME: send Warning header (if applicable)

        try:
            redirect_facet = response.data['response_redirect']
        except KeyError:
            pass
        else:
            self.set_header('Location', redirect_facet.loc)

        try:
            exc_facet = response.data['exc']
        except KeyError:
            pass
        else:
            statuscode = self.service._exc_http_statuscode()

            try:
                exc_class = getattr(__import__(exc_facet.class_def_module,
                                               fromlist=[exc_facet.name]),
                                    exc_facet.name)
            except (ImportError, AttributeError):
                message = \
                    'cannot import exception class {}:{} to determine'\
                     ' appropriate response status code; falling back to {}'\
                     .format(exc_facet.class_def_module, exc_facet.name,
                             statuscode)
                self.logger.error(message)
            else:
                statuscode = self.service._exc_http_statuscode(exc_class)

            self.set_status(statuscode)

        if response.content and self.request.method != 'HEAD':
            try:
                self.write(response.content)
            except IOError:
                if self.client_disconnected:
                    return
                else:
                    raise

        if response.mediatype:
            self.set_header('Content-Type', response.mediatype)
        else:
            self.clear_header('Content-Type')

    def _send_unhandled_error_response(self, exc, traceback):

        self.set_status(self.service._exc_http_statuscode(exc))

        try:
            response = self.request_webmethod.response_fromexc(exc, traceback)
        except:
            exc_str = '{}: {}\n{}'.format(exc.__class__.__name__, exc,
                                          traceback)
            try:
                for mediarange in self.request_acceptable_mediaranges:
                    mediarange, _, _ = mediarange.partition(';')
                    range_major, range_minor = mediarange.split('/', 1)
                    if range_major == '*' \
                           or (range_major == 'text'
                               and range_minor in ('*', 'plain')):
                        try:
                            self.write(exc_str)
                        except IOError:
                            if self.client_disconnected:
                                return
                            else:
                                raise
                        self.set_header('Content-Type', 'text/plain')
            except IOError:
                self.logger.error('no acceptable representation for unhandled'
                                   ' exception:\n{}'.format(_indented(exc_str,
                                                                      size=2)))
        else:
            if response.content and self.request.method != 'HEAD':
                try:
                    self.write(response.content)
                except IOError:
                    if self.client_disconnected:
                        return
                    else:
                        raise

            if response.mediatype:
                self.set_header('Content-Type', response.mediatype)
            else:
                self.clear_header('Content-Type')

    def _send_webmethod_response(self):
        with self.request_webmethod\
                 .resource\
                 .provided_for_request(self.bedframe_request):
            response = \
                self.request_webmethod(**self.request_webmethod_args_prims)
            self._send_response(response)

    def _set_request_timestamp(self):
        try:
            self._request_timestamp = \
                _datetime.strptime(self.request.headers['Date'],
                                   '%a, %d %b %Y %H:%M:%S GMT')
        except KeyError:
            self._request_timestamp = _now_localtime()

    @property
    def _unordered_pathpart_arg_sep(self):
        return self.service.resources.unordered_arg_sep
