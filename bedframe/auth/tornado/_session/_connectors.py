"""Connectors"""

__copyright__ = "Copyright (C) 2014 Ivan D Vasin"
__docformat__ = "restructuredtext"

import abc as _abc
import sys as _sys

from .... import _exc as _bedframe_exc
from ... import http as _http
from ... import session as _session
from ... import _exc
from ... import _info


# common ----------------------------------------------------------------------


_SESSION_ID_COOKIE_KEY = 'session_id'


# login -----------------------------------------------------------------------


_SESSION_PASSWORD_ARG_NAME = 'password'

_SESSION_REALM_ARG_NAME = 'realm'

_SESSION_USER_ARG_NAME = 'user'


class TornadoSessionAuthClerk(_http.HttpSessionClerk):

    """
    An authentication clerk for session-based HTTP authentication on a
    :mod:`Tornado <tornado>` server

    """

    __metaclass__ = _abc.ABCMeta

    def logout(self):
        self.service.current_tornado_request_handler.clear_cookie('session_id')


class TornadoSessionLoginClerk(TornadoSessionAuthClerk,
                               _http.HttpSessionLoginClerk):
    """
    An authentication clerk for login in session-based HTTP authentication
    on a :mod:`Tornado <tornado>` server

    """
    def _confirm_auth_info(self, auth_info, affordances):

        exc = None
        traceback = None

        try:
            super(TornadoSessionLoginClerk, self)\
             ._confirm_auth_info(auth_info, affordances)
        except (_bedframe_exc.Unauthenticated, _bedframe_exc.Redirection) as exc:
            traceback = _sys.exc_info()[2]

        if auth_info.accepted:
            self.service\
                .current_tornado_request_handler\
                .set_cookie(_SESSION_ID_COOKIE_KEY,
                            auth_info.tokens.session_id)

        if exc:
            raise exc, None, traceback


class TornadoSessionLoginScanner(_http.HttpSessionLoginScanner):

    """
    An authentication scanner for login in session-based HTTP
    authentication on a :mod:`Tornado <tornado>` server

    """

    _SESSION_PASSWORD_ARG_NAME = _SESSION_PASSWORD_ARG_NAME

    _SESSION_REALM_ARG_NAME = _SESSION_REALM_ARG_NAME

    _SESSION_USER_ARG_NAME = _SESSION_USER_ARG_NAME

    def _process_tokens(self, input, affordances):

        handler = self.service.current_tornado_request_handler
        method_args_prims = handler.request_webmethod_args_prims
        try:
            user = method_args_prims[self._SESSION_USER_ARG_NAME]
            password = method_args_prims[self._SESSION_PASSWORD_ARG_NAME]
        except KeyError as exc:
            raise _exc.NoValidTokensScanned\
                   (self,
                    'missing session login method argument {!r}'
                     .format(exc.args[0]))

        tokens = {'user': user, 'password': password}
        return _info.RequestAuthInfo(tokens=tokens,
                                     provisions=
                                         _session.SessionAuth.PROVISIONS)

    def _realms(self, upstream_affordances, downstream_affordances):
        # XXX: this uses out-of-band information.  the current request state
        #   should be ignored here.  only the given args should be used
        # FIXME: rewrite realm resolution so that the realm info is in-band
        #   here
        handler = self.service.current_tornado_request_handler
        method_args_prims = handler.request_webmethod_args_prims
        try:
            return (method_args_prims[self._SESSION_REALM_ARG_NAME],)
        except KeyError:
            return super(TornadoSessionLoginScanner, self)\
                    ._realms(upstream_affordances=upstream_affordances,
                             downstream_affordances=downstream_affordances)


# recall ----------------------------------------------------------------------


class TornadoSessionRecallClerk(TornadoSessionAuthClerk,
                                _http.HttpSessionRecallClerk):
    """
    An authentication clerk for session recall in session-based HTTP
    authentication on a :mod:`Tornado <tornado>` server

    """
    def logout(self):
        self.service.current_tornado_request_handler.clear_cookie('session_id')


class TornadoSessionRecallScanner(_http.HttpSessionRecallScanner):

    """
    An authentication scanner for session recall in session-based HTTP
    authentication on a :mod:`Tornado <tornado>` server

    """

    _SESSION_ID_COOKIE_KEY = _SESSION_ID_COOKIE_KEY

    def _process_tokens(self, input, affordances):

        handler = self.service.current_tornado_request_handler
        session_id = handler.get_new_cookie(self._SESSION_ID_COOKIE_KEY)
        if not session_id:
            raise _exc.NoValidTokensScanned\
                   (self,
                    'missing session recall cookie {!r}'
                     .format(self._SESSION_ID_COOKIE_KEY))

        tokens = {'session_id': session_id}
        return _info.RequestAuthInfo(tokens=tokens,
                                     provisions=
                                         _session.SessionAuth.PROVISIONS)
