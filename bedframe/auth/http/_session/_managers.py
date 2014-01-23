"""Managers"""

__copyright__ = "Copyright (C) 2014 Ivan D Vasin"
__docformat__ = "restructuredtext"


class HttpSessionManager(object):

    def __init__(self, service, login_uri=None, logout_uri=None,
                 login_clerk=None, recall_clerk=None, storage_supplicant=None,
                 recall_supplicant=None):
        self._login_clerk = login_clerk
        self._login_uri = login_uri
        self._logout_uri = logout_uri
        self._recall_clerk = recall_clerk
        self._recall_supplicant = recall_supplicant
        self._service = service
        self._storage_supplicant = storage_supplicant

    def clear_current_session(self):

        try:
            session_id = self.current_auth_info.tokens.session_id
        except AttributeError:
            pass
        else:
            self.storage_supplicant.logout(session_id)

        self.login_clerk.logout()

    @property
    def login_clerk(self):
        return self._login_clerk

    @login_clerk.setter
    def login_clerk(self, value):
        self._login_clerk = value

    @property
    def login_realm(self):
        return iter(self.storage_supplicant.realms()).next()

    @property
    def login_uri(self):
        return self._login_uri

    @login_uri.setter
    def login_uri(self, value):
        self._login_uri = value

    @property
    def logout_uri(self):
        return self._logout_uri

    @logout_uri.setter
    def logout_uri(self, value):
        self._logout_uri = value

    @property
    def recall_clerk(self):
        return self._recall_clerk

    @recall_clerk.setter
    def recall_clerk(self, value):
        self._recall_clerk = value

    @property
    def recall_supplicant(self):
        return self._recall_supplicant

    @recall_supplicant.setter
    def recall_supplicant(self, value):
        self._recall_supplicant = value

    @property
    def service(self):
        return self._service

    @property
    def storage_supplicant(self):
        return self._storage_supplicant

    @storage_supplicant.setter
    def storage_supplicant(self, value):
        self._storage_supplicant = value
