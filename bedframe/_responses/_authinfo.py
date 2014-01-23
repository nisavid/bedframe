"""Authentication information responses"""

__copyright__ = "Copyright (C) 2014 Ivan D Vasin"
__docformat__ = "restructuredtext"

from . import _core as _responses_core


class WebAuthInfoResponseFacet(_responses_core.WebResponseFacet):

    def __init__(self, auth_info, **kwargs):

        super(WebAuthInfoResponseFacet, self).__init__(**kwargs)

        self._accepted = auth_info.accepted
        self._realm = auth_info.realm

        try:
            user = auth_info.user
        except AttributeError:
            user = None
        self._user = user

    @property
    def accepted(self):
        return self._accepted

    @property
    def realm(self):
        return self._realm

    @property
    def user(self):
        return self._user
