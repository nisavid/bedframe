"""Connectors"""

__copyright__ = "Copyright (C) 2014 Ivan D Vasin"
__docformat__ = "restructuredtext"

import abc as _abc

from .... import _exc
from ... import _connectors


class HttpStandardClerk(_connectors.Clerk):

    """An authentication clerk for standard HTTP authentication"""

    __metaclass__ = _abc.ABCMeta

    @_abc.abstractmethod
    def _append_response_auth_challenge_header(self, value):
        pass

    @_abc.abstractmethod
    def _append_response_auth_confirmation_header(self, value):
        pass

    @_abc.abstractmethod
    def _append_response_auth_challenge(self, realm, input, affordances):
        pass

    def _confirm_auth_info(self, auth_info, affordances):
        if auth_info.accepted:
            # FIXME: send Authentication-Info header
            pass
        else:
            for realm in (affordances.realms
                          if affordances.realms.isfinite
                          else ('',)):
                self._append_response_auth_challenge\
                    (realm=realm, input=auth_info.tokens,
                     affordances=affordances)
            raise _exc.AuthTokensNotAccepted(affordances=affordances)

    def _process_tokens(self, input, affordances):
        realms = affordances.realms
        for realm in (realms if realms and realms.isfinite else ('',)):
            self._append_response_auth_challenge(realm, input=input,
                                                 affordances=affordances)
        raise _exc.AuthTokensNotGiven(affordances=affordances)


class HttpStandardScanner(_connectors.Scanner):
    """An authentication scanner for standard HTTP authentication"""
    __metaclass__ = _abc.ABCMeta
