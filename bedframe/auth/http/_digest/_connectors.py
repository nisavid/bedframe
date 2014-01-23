"""Connectors"""

__copyright__ = "Copyright (C) 2014 Ivan D Vasin"
__docformat__ = "restructuredtext"

import abc as _abc
from base64 import b64encode as _b64encode
from itertools import chain as _chain, combinations as _combinations
import re as _re

from spruce.collections import frozenusetset as _frozenusetset

from ... import digest as _digest
from .. import _std as _std_http


_DIGEST_USER_OPTIONAL_TOKENS = ('qop', 'digest_algorithm', 'client_nonce',
                                'opaque', 'server_nonce_use_count')

_DIGEST_USER_REQUIRED_TOKENS = ('user', 'realm', 'server_nonce', 'digest_uri',
                                'digest')

_DIGEST_USER_TOKENSETS = \
    _frozenusetset(_chain(_DIGEST_USER_REQUIRED_TOKENS, optional_tokens)
                   for optional_tokens
                   in _chain((),
                             *(_combinations(_DIGEST_USER_OPTIONAL_TOKENS,
                                             n + 1)
                               for n
                               in range(len(_DIGEST_USER_OPTIONAL_TOKENS)))))


class HttpDigestClerk(_std_http.HttpStandardClerk):

    """An authentication clerk for HTTP Digest authentication"""

    __metaclass__ = _abc.ABCMeta

    _DIGEST_USER_OPTIONAL_TOKENS = _DIGEST_USER_OPTIONAL_TOKENS

    _DIGEST_USER_REQUIRED_TOKENS = _DIGEST_USER_REQUIRED_TOKENS

    _DIGEST_USER_TOKENSETS = _DIGEST_USER_TOKENSETS

    def _append_response_auth_challenge(self, realm, input, affordances):
        auth_subfields = ['{}="{}"'.format(directivename, input[tokenname])
                          for tokenname, directivename
                          in (('realm', 'realm'),
                              ('space_uris', 'domain'),
                              ('server_nonce', 'nonce'),
                              ('stale', 'stale'),
                              ('digest_algorithm', 'algorithm'),
                              ('qop', 'qop'),
                              )
                          if tokenname in input]
        if '__' in input:
            auth_subfields.append('opaque="{}"'
                                   .format(_b64encode(input['__'])))
        challenge_header_value = 'Digest ' + ', '.join(auth_subfields)
        self._append_response_auth_challenge_header(challenge_header_value)

    def _inputs(self, upstream_affordances, downstream_affordances):
        return (('realm', 'qop', 'server_nonce'),)

    def _outputs(self, upstream_affordances, downstream_affordances):
        return _DIGEST_USER_TOKENSETS

    def _provisionsets(self, upstream_affordances, downstream_affordances):
        return _digest.DigestAuth.PROVISIONSETS


class HttpDigestScanner(_std_http.HttpStandardScanner):

    """An authentication scanner for HTTP Digest authentication"""

    __metaclass__ = _abc.ABCMeta

    _AUTHORIZATION_HEADER_CLAUSE_PATTERN = \
        r'\s*(?:'\
        r'(?P<user_clause>username\s*=\s*"(?P<user>[^"]*)")'\
        r'|(?P<realm_clause>realm\s*=\s*"(?P<realm>[^"]*)")'\
        r'|(?P<server_nonce_clause>nonce\s*=\s*"(?P<server_nonce>[^"]*)")'\
        r'|(?P<uri_clause>uri\s*=\s*"(?P<digest_uri>[^"]*)")'\
        r'|(?P<digest_clause>response\s*=\s*"(?P<digest>[^"]*)")'\
        r'|(?P<algorithm_clause>algorithm\s*='\
        r'\s*"?(?P<digest_algorithm>[^\s,"]*)"?)'\
        r'|(?P<client_nonce_clause>cnonce\s*=\s*"(?P<client_nonce>[^"]*)")'\
        r'|(?P<opaque_clause>opaque\s*=\s*"(?P<opaque>[^"]*)")'\
        r'|(?P<qop_clause>qop\s*=\s*"?(?P<qop>[^\s,"]*)"?)'\
        r'|(?P<server_nonce_use_count_clause>nc\s*='\
        r'\s*(?P<server_nonce_use_count>[0-9a-f]*))'\
        r'|.*'\
        r'),?\s*'

    _AUTHORIZATION_HEADER_RE = \
        _re.compile(r'\s*Digest(?:{})+'
                     .format(_AUTHORIZATION_HEADER_CLAUSE_PATTERN),
                    _re.MULTILINE)

    _DIGEST_USER_OPTIONAL_TOKENS = _DIGEST_USER_OPTIONAL_TOKENS

    _DIGEST_USER_REQUIRED_TOKENS = _DIGEST_USER_REQUIRED_TOKENS

    _DIGEST_USER_TOKENSETS = _DIGEST_USER_TOKENSETS

    def _outputs(self, upstream_affordances, downstream_affordances):
        return _DIGEST_USER_TOKENSETS

    def _provisionsets(self, upstream_affordances, downstream_affordances):
        return _digest.DigestAuth.PROVISIONSETS
