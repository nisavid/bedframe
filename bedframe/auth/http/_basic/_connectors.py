"""Connectors"""

__copyright__ = "Copyright (C) 2014 Ivan D Vasin"
__docformat__ = "restructuredtext"

import abc as _abc
import re as _re

from ... import plain as _plain
from .. import _std as _std_http


_BASIC_USER_TOKENS = ('user', 'password')


class HttpBasicClerk(_std_http.HttpStandardClerk):

    """An authentication clerk for HTTP Basic authentication"""

    __metaclass__ = _abc.ABCMeta

    _BASIC_USER_TOKENS = _BASIC_USER_TOKENS

    def _inputs(self, upstream_affordances, downstream_affordances):
        return ((),)

    def _append_response_auth_challenge(self, realm, input=None,
                                        affordances=None):
        self._append_response_auth_challenge_header('Basic realm="{}"'
                                                     .format(realm))

    def _outputs(self, upstream_affordances, downstream_affordances):
        return (_BASIC_USER_TOKENS,)

    def _provisionsets(self, upstream_affordances, downstream_affordances):
        return (_plain.PlainAuth.PROVISIONS,)


class HttpBasicScanner(_std_http.HttpStandardScanner):

    """An authentication scanner for HTTP Basic authentication"""

    __metaclass__ = _abc.ABCMeta

    _AUTHORIZATION_HEADER_RE = \
        _re.compile(r'\s*Basic\s*(?P<creds_base64>[^\s]*)')

    _BASIC_USER_TOKENS = _BASIC_USER_TOKENS

    def _outputs(self, upstream_affordances, downstream_affordances):
        return (self._BASIC_USER_TOKENS,)

    def _provisionsets(self, upstream_affordances, downstream_affordances):
        return (_plain.PlainAuth.PROVISIONS,)
