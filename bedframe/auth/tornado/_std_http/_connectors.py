"""Connectors."""

__copyright__ = "Copyright (C) 2013 Ivan D Vasin and Cogo Labs"
__docformat__ = "restructuredtext"

import abc as _abc

from ... import http as _http


class TornadoHttpStandardClerk(_http.HttpStandardClerk):

    """
    An authentication clerk that uses HTTP authentication on a :mod:`Tornado
    <tornado>` server.

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
    An authentication scanner that uses HTTP authentication on a
    :mod:`Tornado <tornado>` server.

    """
    __metaclass__ = _abc.ABCMeta
