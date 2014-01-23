"""Web services"""

__copyright__ = "Copyright (C) 2014 Ivan D Vasin"
__docformat__ = "restructuredtext"

import abc as _abc
import sys as _sys
import traceback as _traceback

# CAVEAT
import gevent.pywsgi as _gevent_wsgi
import tornado.web as _tnd_web

import tornado.ioloop as _tnd_ioloop
# FIXME - this import monkeypatches tornado.asynchttpclient to
# work within a WSGIApplication.  keep it here until we fix the
# UI servers.
import tornado.wsgi as _tnd_wsgi

from .. import http as _http
from .. import _debug
from .. import _exc
from .. import _services
from ..auth import tornado as _tnd_auth
from . import _common as _tnd_common
from . import _handlers as _tnd_handlers


class TornadoServiceABC(_http.HttpService):

    """A web service that uses :mod:`Tornado <tornado>`

    .. seealso::
        :class:`bedframe.http.HttpService \
                <bedframe.http._services.HttpService>`

    """

    __metaclass__ = _abc.ABCMeta

    def __init__(self, **kwargs):

        super(TornadoServiceABC, self).__init__(**kwargs)

        self._all_supported_httpmethods = set()
        self._current_tornado_request_handler = None

        self.auth_scanners\
            .extend([_tnd_auth.TornadoHttpBasicScanner
                      (authenticator=self.authenticator),
                     _tnd_auth.TornadoHttpDigestScanner
                      (authenticator=self.authenticator),
                     _tnd_auth.TornadoSessionLoginScanner
                      (authenticator=self.authenticator,
                       session_manager=self.session_auth_manager),
                     _tnd_auth.TornadoSessionRecallScanner
                      (authenticator=self.authenticator,
                       session_manager=self.session_auth_manager),
                     ])
        self.auth_clerks\
            .extend([_tnd_auth.TornadoHttpBasicClerk
                      (authenticator=self.authenticator),
                     _tnd_auth.TornadoHttpDigestClerk
                      (authenticator=self.authenticator),
                     _tnd_auth.TornadoSessionLoginClerk
                      (authenticator=self.authenticator,
                       session_manager=self.session_auth_manager),
                     _tnd_auth.TornadoSessionRecallClerk
                      (authenticator=self.authenticator,
                       session_manager=self.session_auth_manager),
                     ])

    @property
    def current_tornado_request_handler(self):
        return self._current_tornado_request_handler

    def _resource_tornado_request_handler_class(self, resource_class):

        webmethodnames = set(resource_class.allowed_webmethodnames())
        httpmethods = self._supported_httpmethods(webmethodnames)

        self._all_supported_httpmethods |= set(httpmethods)

        attrs = {'service': self, 'SUPPORTED_METHODS': httpmethods}

        for httpmethod in httpmethods:
            attrs[httpmethod.lower()] = \
                self._resource_tornado_request_handler_method(resource_class,
                                                              httpmethod)

        return type('{}_TornadoRequestHandler'.format(resource_class.__name__),
                    (_tnd_handlers.TornadoRequestHandler,), attrs)

    def _resource_tornado_request_handler_method(self, resource_class,
                                                 httpmethod):

        def method(handler, **pathparts_jsons):
            try:
                self._current_tornado_request_handler = handler
                handler._set_request_timestamp()
                handler._client_disconnected = False
                handler._request_pathparts_jsons_ = pathparts_jsons

                # CAVEAT: call ``resource_class.__new__()`` explicitly so that
                #   the acceptable media ranges of the bound
                #   ``resource.__init__()`` can be set prior to calling it.
                #   this ensures that a web resource's ``__init__()`` method is
                #   defined in the same way as a web method and behaves
                #   likewise, albeit having no return value and being used for
                #   a special purpose.
                resource = resource_class\
                            .__new__(resource_class,
                                     **handler.request_resource_args_prims)
                resource.__init__\
                        .withtypes(handler.request_acceptable_mediaranges)\
                         (**handler.request_resource_args_prims)
                handler._request_resource = resource

                handler._handle_request()

            except _exc.WebMethodException as exc:
                if self.sentryclient:
                    self.sentryclient.captureException()
                handler._send_response(exc.response(debug_flags=
                                                        self.debug_flags))

            except _exc.UnhandledException as exc:
                if self.sentryclient:
                    self.sentryclient.captureException()
                handler._send_unhandled_error_response(exc,
                                                       traceback=exc.traceback)

            except Exception as exc:
                if self.sentryclient:
                    self.sentryclient.captureException()
                if _debug.DEBUG_EXC_TRACEBACK in self.debug_flags:
                    tb_entries = _traceback.extract_tb(_sys.exc_info()[2])
                    if _debug.DEBUG_EXC_TRACEBACK_INCLUDING_SERVICE_CODE \
                           not in self.debug_flags:
                        tb_entries = tb_entries[1:]
                    tb_str = ''.join(_traceback.format_list(tb_entries))
                else:
                    tb_str = None
                handler._send_unhandled_error_response(exc, traceback=tb_str)
        method.__name__ = httpmethod.lower()
        return method


class TornadoService(TornadoServiceABC):
    def _start_nofork(self):
        handlers = \
            [(path_re.pattern,
              self._resource_tornado_request_handler_class(resource_class))
             for path_re, resource_class in self.resources.items()]
        app = _tnd_web.Application(handlers,
                                   log_function=
                                       _tnd_common.tornado_log_request)
        app.listen(self.port)
        _tnd_ioloop.IOLoop.instance().start()

_services.WebService.register_impl('tornado', TornadoService)


class TornadoWsgiService(TornadoServiceABC):

    @property
    def wsgi_app(self):
        handlers = \
            [(path_re.pattern,
              self._resource_tornado_request_handler_class(resource_class))
             for path_re, resource_class in self.resources.items()]
        app = _tnd_wsgi.WSGIApplication(handlers,
                                        log_function=
                                            _tnd_common.tornado_log_request)
        return app

    def _start_nofork(self):
        server = _gevent_wsgi.WSGIServer((self.hostname, self.port),
                                         self.wsgi_app, log=None)
        server.serve_forever()

_services.WebService.register_impl('tornado-wsgi', TornadoWsgiService)
