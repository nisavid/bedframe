"""Connectors"""

__copyright__ = "Copyright (C) 2014 Ivan D Vasin"
__docformat__ = "restructuredtext"

import abc as _abc

from ... import http as _http


class TornadoHttpStandardClerk(_http.HttpStandardClerk):

    """
    An authentication clerk for standard HTTP authentication on a
    :mod:`Tornado <tornado>` server

    """

    __metaclass__ = _abc.ABCMeta

    def _append_response_auth_challenge_header(self, value):
        self.service.current_tornado_request_handler\
                    .set_header('WWW-Authenticate', value)

    def _append_response_auth_confirmation_header(self, value):
        self.service.current_tornado_request_handler\
                    .set_header('Authentication-Info', value)


class TornadoHttpStandardScanner(_http.HttpStandardScanner):
    """
    An authentication scanner for standard HTTP authentication on a
    :mod:`Tornado <tornado>` server

    """
    __metaclass__ = _abc.ABCMeta
