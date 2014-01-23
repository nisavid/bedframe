"""Connectors"""

__copyright__ = "Copyright (C) 2014 Ivan D Vasin"
__docformat__ = "restructuredtext"

from .. import _connectors


class SessionSupplicant(_connectors.Supplicant):

    """An authentication supplicant for session-based HTTP authentication

    :param session_manager:
        The session-based authentication manager.
    :type session_manager:
        :class:`bedframe.auth.http.HttpSessionAuthManager \
                <bedframe.auth.http._session._managers.HttpSessionAuthManager>`

    """

    def __init__(self, session_manager, **kwargs):
        super(SessionSupplicant, self).__init__(**kwargs)
        self._session_manager = session_manager

    @property
    def session_manager(self):
        """The session-based authentication manager

        :type:
            :class:`bedframe.auth.http.HttpSessionAuthManager \
                    <bedframe.auth.http._session._managers.HttpSessionAuthManager>`

        """
        return self._session_manager
