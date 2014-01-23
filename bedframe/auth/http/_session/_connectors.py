"""Connectors"""

__copyright__ = "Copyright (C) 2014 Ivan D Vasin"
__docformat__ = "restructuredtext"

import abc as _abc

from .... import _exc
from ... import session as _session
from ... import _connectors


# core ------------------------------------------------------------------------


class HttpSessionConnector(_connectors.Connector):

    """An authentication connector for session-based HTTP authentication

    :param session_manager:
        The session-based authentication manager.
    :type session_manager:
        :class:`~bedframe.auth.http._session._managers.HttpSessionManager`

    """

    __metaclass__ = _abc.ABCMeta

    def __init__(self, session_manager, **kwargs):
        super(HttpSessionConnector, self).__init__(**kwargs)
        self._session_manager = session_manager

    @property
    def login_uri(self):
        return self.session_manager.login_uri

    @property
    def logout_uri(self):
        return self.session_manager.logout_uri

    @property
    def session_manager(self):
        """The session-based authentication manager.

        :type:
            :class:`~bedframe.auth.http._session._managers.HttpSessionManager`

        """
        return self._session_manager

    def _provisionsets(self, upstream_affordances, downstream_affordances):
        return (_session.SessionAuth.PROVISIONS,)


class HttpSessionClerk(HttpSessionConnector, _connectors.Clerk):
    """An authentication clerk for session-based HTTP authentication

    .. seealso:: :class:`HttpSessionConnector`

    """
    __metaclass__ = _abc.ABCMeta


class HttpSessionScanner(HttpSessionConnector, _connectors.Scanner):
    """An authentication scanner for session-based HTTP authentication

    .. seealso:: :class:`HttpSessionConnector`

    """
    __metaclass__ = _abc.ABCMeta


# login -----------------------------------------------------------------------


_SESSION_LOGIN_USER_TOKENS = ('user', 'password')


class HttpSessionLoginClerk(HttpSessionClerk):

    """
    An authentication clerk for login in session-based HTTP authentication

    .. seealso:: :class:`HttpSessionClerk`

    """

    __metaclass__ = _abc.ABCMeta

    def _confirm_auth_info(self, auth_info, affordances):
        if auth_info.accepted:
            try:
                redirect_uri = auth_info.tokens.redirect
            except AttributeError:
                pass
            else:
                raise _exc.ResponseRedirection(redirect_uri, 'login succeeded')
        else:
            redirect_exc = \
                _exc.ResponseRedirection(self.login_uri,
                                         'unrecognized login credentials;'
                                          ' login is required to proceed')
            raise _exc.AuthTokensNotAccepted(affordances=affordances,
                                             redirection=redirect_exc)

    def _inputs(self, upstream_affordances, downstream_affordances):
        return ((),)

    def _outputs(self, upstream_affordances, downstream_affordances):
        return (_SESSION_LOGIN_USER_TOKENS,)

    def _process_tokens(self, input, affordances):
        redirect_exc = \
            _exc.ResponseRedirection(self.login_uri,
                                     'login is required to proceed')
        raise _exc.AuthTokensNotGiven(affordances=affordances,
                                      redirection=redirect_exc)


class HttpSessionLoginScanner(HttpSessionScanner):

    """
    An authentication scanner for login in session-based HTTP authentication

    .. seealso:: :class:`HttpSessionScanner`

    """

    __metaclass__ = _abc.ABCMeta

    def _outputs(self, upstream_affordances, downstream_affordances):
        return (_SESSION_LOGIN_USER_TOKENS,)


# recall ----------------------------------------------------------------------


_SESSION_RECALL_USER_TOKENS = ('session_id',)


class HttpSessionRecallClerk(HttpSessionClerk):

    """
    An authentication clerk for session recall in session-based HTTP
    authentication

    .. seealso:: :class:`HttpSessionClerk`

    """

    __metaclass__ = _abc.ABCMeta

    def _confirm_auth_info(self, auth_info, affordances):
        if auth_info.accepted:
            # FIXME: send appropriate auth info
            pass
        else:
            redirect_exc = \
                _exc.ResponseRedirection(self.login_uri,
                                         'unrecognized authentication session'
                                          ' ID; login is required to proceed')
            raise _exc.AuthTokensNotAccepted(affordances=affordances,
                                             redirection=redirect_exc)

    def _inputs(self, upstream_affordances, downstream_affordances):
        return ((),)

    def _outputs(self, upstream_affordances, downstream_affordances):
        return (_SESSION_RECALL_USER_TOKENS,)

    def _process_tokens(self, input, affordances):
        redirect_exc = _exc.ResponseRedirection(self.login_uri,
                                                'login is required')
        raise _exc.AuthTokensNotGiven(affordances=affordances,
                                      redirection=redirect_exc)


class HttpSessionRecallScanner(HttpSessionScanner):

    """
    An authentication scanner for session recall in session-based HTTP
    authentication

    .. seealso:: :class:`HttpSessionScanner`

    """

    __metaclass__ = _abc.ABCMeta

    def _outputs(self, upstream_affordances, downstream_affordances):
        return (_SESSION_RECALL_USER_TOKENS,)
