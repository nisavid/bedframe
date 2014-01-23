"""Algorithms"""

__copyright__ = "Copyright (C) 2014 Ivan D Vasin"
__docformat__ = "restructuredtext"

from spruce.collections import frozenset as _frozenset

from .. import _algorithms
from .. import _info
from .. import _provisions


class PlainAuth(_algorithms.Algorithm):

    PROVISIONS = _provisions.SECPROV_CLIENT_AUTH

    @classmethod
    def phase_classes(cls):
        return (cls.SolicitCredsFromClient, cls.VerifyCredsWithBackend,
                cls.VerifyBackendResponse)

    class SolicitCredsFromClient(_algorithms.AlgorithmPhase):

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

    class VerifyCredsWithBackend(_algorithms.AlgorithmPhase):

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

    class VerifyBackendResponse(_algorithms.AlgorithmPhase):

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
                                         accepted=input['accepted'] == 'True')

    def _provisionsets(self, upstream_affordances, downstream_affordances):
        return (self.PROVISIONS,)
