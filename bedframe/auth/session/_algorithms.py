"""Algorithms"""

__copyright__ = "Copyright (C) 2014 Ivan D Vasin"
__docformat__ = "restructuredtext"

import abc as _abc

from spruce.collections import frozenset as _frozenset

from .. import _algorithms
from .. import _info
from .. import _provisions


class SessionAuth(_algorithms.Algorithm):

    __metaclass__ = _abc.ABCMeta

    PROVISIONS = _provisions.SECPROV_CLIENT_AUTH

    def _provisionsets(self, upstream_affordances, downstream_affordances):
        return (self.PROVISIONS,)


class SessionLoginAuth(SessionAuth):

    @classmethod
    def phase_classes(cls):
        return (cls.SolicitLogin, cls.VerifyLoginAndStoreSessionInfo,
                cls.SendSessionId)

    class SolicitLogin(_algorithms.AlgorithmPhase):

        @property
        def input_source(self):
            return 'start'

        @property
        def output_target(self):
            return 'clerk'

        def _inputs(self, upstream_affordances, downstream_affordances):
            return ((),)

        def _outputs(self, upstream_affordances, downstream_affordances):
            return ((),)

        def _process_tokens(self, input, affordances):
            tokens = input
            return _info.RequestAuthInfo(tokens=tokens,
                                         provisions=self.algorithm.PROVISIONS)

    # XXX: couple VerifyLogin with StoreSessionInfo
    # FIXME: rewrite Authenticator to support multiple supplicants in one
    #   process, then split this into two steps.  see the related FIXME in
    #   :file:`../_connectors/_ldap_memcache.py`
    class VerifyLoginAndStoreSessionInfo(_algorithms.AlgorithmPhase):

        @property
        def input_source(self):
            return 'scanner'

        @property
        def output_target(self):
            return 'supplicant'

        _TOKENS = _frozenset(('user', 'password'))

        def _inputs(self, upstream_affordances, downstream_affordances):
            return (self._TOKENS,)

        def _outputs(self, upstream_affordances, downstream_affordances):
            return (self._TOKENS,)

        def _process_tokens(self, input, affordances):
            tokens = input
            return _info.RequestAuthInfo(tokens=tokens,
                                         provisions=self.algorithm.PROVISIONS)

    class SendSessionId(_algorithms.AlgorithmPhase):

        @property
        def input_source(self):
            return 'supplicant'

        @property
        def output_target(self):
            return 'end'

        _TOKENS = _frozenset(('user', 'accepted', 'session_id'))

        def _inputs(self, upstream_affordances, downstream_affordances):
            return (self._TOKENS,)

        def _outputs(self, upstream_affordances, downstream_affordances):
            return (self._TOKENS,)

        def _process_tokens(self, input, affordances):
            tokens = input
            return _info.RequestAuthInfo(tokens=tokens,
                                         provisions=self.algorithm.PROVISIONS,
                                         accepted=(tokens['accepted']
                                                   == 'True'))


class SessionRecallAuth(SessionAuth):

    @classmethod
    def phase_classes(cls):
        return (cls.SolicitSessionId, cls.FetchSessionInfo,
                cls.VerifySessionInfo)

    class SolicitSessionId(_algorithms.AlgorithmPhase):

        @property
        def input_source(self):
            return 'start'

        @property
        def output_target(self):
            return 'clerk'

        def _inputs(self, upstream_affordances, downstream_affordances):
            return ((),)

        def _outputs(self, upstream_affordances, downstream_affordances):
            return ((),)

        def _process_tokens(self, input, affordances):
            tokens = input
            return _info.RequestAuthInfo(tokens=tokens,
                                         provisions=self.algorithm.PROVISIONS)

    class FetchSessionInfo(_algorithms.AlgorithmPhase):

        @property
        def input_source(self):
            return 'scanner'

        @property
        def output_target(self):
            return 'supplicant'

        _TOKENS = _frozenset(('session_id',))

        def _inputs(self, upstream_affordances, downstream_affordances):
            return (self._TOKENS,)

        def _outputs(self, upstream_affordances, downstream_affordances):
            return (self._TOKENS,)

        def _process_tokens(self, input, affordances):
            tokens = input
            return _info.RequestAuthInfo(tokens=tokens,
                                         provisions=self.algorithm.PROVISIONS)

    class VerifySessionInfo(_algorithms.AlgorithmPhase):

        @property
        def input_source(self):
            return 'supplicant'

        @property
        def output_target(self):
            return 'end'

        _TOKENS = _frozenset(('user', 'accepted'))

        def _inputs(self, upstream_affordances, downstream_affordances):
            return (self._TOKENS,)

        def _outputs(self, upstream_affordances, downstream_affordances):
            return (self._TOKENS,)

        def _process_tokens(self, input, affordances):
            tokens = input
            return _info.RequestAuthInfo(tokens=tokens,
                                         provisions=self.algorithm.PROVISIONS,
                                         accepted=(tokens['accepted']
                                                   == 'True'))
