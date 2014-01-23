"""Algorithms"""

__copyright__ = "Copyright (C) 2014 Ivan D Vasin"
__docformat__ = "restructuredtext"

import abc as _abc

from . import _connectors
from . import _handlers


class Algorithm(_handlers.ProvisionSetHandler):

    __metaclass__ = _abc.ABCMeta

    def __init__(self, authenticator):
        self._authenticator = authenticator
        self._phases = None

    def __repr__(self):
        return '{}(authenticator={!r})'.format(self.__class__.__name__,
                                               self.authenticator)

    def __str__(self):
        return self.__class__.__name__

    @property
    def authenticator(self):
        return self._authenticator

    def next_phase(self, upstream_affordances=None,
                   downstream_affordances=None):
        for phase in reversed(self.phases):
            if phase.supports_affordances(upstream=upstream_affordances,
                                          downstream=downstream_affordances):
                return phase
        return None

    @classmethod
    @_abc.abstractmethod
    def phase_classes(cls):
        pass

    @property
    def phases(self):
        if self._phases is None:
            self._phases = tuple(phase_class(algorithm=self)
                                 for phase_class in self.phase_classes())
        return self._phases

    @property
    def service(self):
        return self.authenticator.service


class AlgorithmPhase(_connectors.Connector, _handlers.AlgorithmHandler,
                     _handlers.ProvisionSetHandler):

    __metaclass__ = _abc.ABCMeta

    def __init__(self, algorithm):
        self._algorithm = algorithm
        self._index = None

    def __repr__(self):
        return '{}(algorithm={!r})'.format(self.__class__.__name__,
                                           self.algorithm)

    def __str__(self):
        return '{}.{}'.format(self.algorithm.__class__.__name__,
                              self.__class__.__name__)

    @property
    def algorithm(self):
        return self._algorithm

    @property
    def authenticator(self):
        return self.algorithm.authenticator

    @property
    def index(self):
        if self._index is None:
            self._index = self.algorithm.phases.index(self)
        return self._index

    @property
    def next_phase(self):
        try:
            return self.algorithm.phases[self.index + 1]
        except IndexError:
            return None

    @property
    def prev_phase(self):
        try:
            return self.algorithm.phases[self.index - 1]
        except IndexError:
            return None

    @property
    def service(self):
        return self.algorithm.service

    def _algorithms(self, upstream_affordances, downstream_affordances):
        return (self.algorithm,)

    def _provisionsets(self, upstream_affordances, downstream_affordances):
        return self.algorithm\
                   .provisionsets(upstream_affordances=upstream_affordances,
                                  downstream_affordances=
                                      downstream_affordances)

    def _opaque_passthrough(self, upstream_affordances,
                            downstream_affordances):
        return True

    def _tokens_passthrough(self, upstream_affordances,
                            downstream_affordances):
        return True
