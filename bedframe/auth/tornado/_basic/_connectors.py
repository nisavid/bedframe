"""Connectors"""

__copyright__ = "Copyright (C) 2014 Ivan D Vasin"
__docformat__ = "restructuredtext"

from base64 import b64decode as _b64decode

from ... import plain as _plain
from ... import http as _http
from ... import _exc
from ... import _info
from .. import _std_http


class TornadoHttpBasicClerk(_std_http.TornadoHttpStandardClerk,
                                _http.HttpBasicClerk):
    """
    An authentication clerk for HTTP Basic authentication on a :mod:`Tornado
    <tornado>` server

    """
    pass


class TornadoHttpBasicScanner(_std_http.TornadoHttpStandardScanner,
                              _http.HttpBasicScanner):

    """
    An authentication scanner for HTTP Basic authentication on a
    :mod:`Tornado <tornado>` server

    """

    def _process_tokens(self, input, affordances):

        handler = self.service.current_tornado_request_handler

        try:
            authz_header_value = handler.request.headers['Authorization']
        except KeyError:
            raise _exc.NoValidTokensScanned\
                   (self, 'no Authorization header field')
        match = self._AUTHORIZATION_HEADER_RE.match(authz_header_value)

        if not match:
            raise _exc.NoValidTokensScanned\
                   (self, 'unrecognized Authorization header field value')

        creds_base64 = match.group('creds_base64')
        try:
            creds = _b64decode(creds_base64)
        except TypeError:
            raise _exc.NoValidTokensScanned\
                   (self, 'credentials string is not a valid Base64 string')

        try:
            user, password = creds.split(':', 1)
        except ValueError:
            raise _exc.NoValidTokensScanned\
                   (self, 'invalid decoded credentials string')

        tokens = {'user': user, 'password': password}
        return _info.RequestAuthInfo(tokens=tokens,
                                     provisions=_plain.PlainAuth.PROVISIONS)
