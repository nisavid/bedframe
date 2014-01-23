"""Connectors"""

__copyright__ = "Copyright (C) 2014 Ivan D Vasin"
__docformat__ = "restructuredtext"

from base64 import b64decode as _b64decode

from ... import digest as _digest
from ... import http as _http
from ... import _exc
from ... import _info
from .. import _std_http


class TornadoHttpDigestClerk(_std_http.TornadoHttpStandardClerk,
                             _http.HttpDigestClerk):
    """
    An authentication clerk for HTTP Digest authentication on a
    :mod:`Tornado <tornado>` server

    """
    pass


class TornadoHttpDigestScanner(_std_http.TornadoHttpStandardScanner,
                               _http.HttpDigestScanner):

    """
    An authentication scanner for HTTP Digest authentication on a
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

        tokens = {}
        for name in self._DIGEST_USER_REQUIRED_TOKENS:
            token = match.group(name)

            if token is None:
                raise _exc.NoValidTokensScanned\
                       (self,
                        'missing required authentication token {!r}'
                         .format(name))

            tokens[name] = token
        for name in self._DIGEST_USER_OPTIONAL_TOKENS:
            token = match.group(name)
            if token is not None:
                tokens[name] = token
        opaque_data = match.group('opaque')
        if opaque_data is not None:
            tokens['__'] = _b64decode(opaque_data)

        provisions = None
        if all(token in tokens
               for token in _digest.DigestAuth.TOKENS_NO_QOP):
            provisions = _digest.DigestAuth.PROVISIONS_NO_QOP
            if all(token in tokens
                   for token in _digest.DigestAuth.TOKENS_QOP_AUTH):
                provisions = _digest.DigestAuth.PROVISIONS_QOP_AUTH
                if all(token in tokens
                       for token in _digest.DigestAuth.TOKENS_QOP_AUTH_INT):
                    provisions = _digest.DigestAuth.PROVISIONS_QOP_AUTH_INT

        return _info.RequestAuthInfo(tokens=tokens, provisions=provisions)
