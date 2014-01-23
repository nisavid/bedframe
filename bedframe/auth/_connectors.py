"""Connectors"""

__copyright__ = "Copyright (C) 2014 Ivan D Vasin"
__docformat__ = "restructuredtext"

import abc as _abc

from spruce.collections import odict as _odict

from . import _handlers


class Connector(_handlers.TokenHandler):

    """An authentication connector

    A connector is a functional unit in an authentication process.
    Different types of connectors are responsible for different parts of the
    process.

    :param authenticator:
        The authenticator.
    :type authenticator:
        :class:`~bedframe.auth._authenticators.Authenticator`

    """

    __metaclass__ = _abc.ABCMeta

    def __init__(self, authenticator):
        self._authenticator = authenticator

    def __repr__(self):
        return '{}({})'.format(self.__class__.__name__,
                               ', '.join('{}={!r}'.format(property_, value)
                                         for property_, value
                                         in self._init_args(ordered=True)
                                                .items()))

    def __str__(self):
        return self.__class__.__name__

    @property
    def authenticator(self):
        return self._authenticator

    def _init_args(self, ordered=False):
        class_ = _odict if ordered else dict
        return class_((('authenticator', self.authenticator),))


class Clerk(Connector, _handlers.ProvisionSetHandler):

    """An authentication clerk

    A clerk communicates with clients, sending authentication tokens to them
    and soliciting tokens from them.

    """

    __metaclass__ = _abc.ABCMeta

    def confirm_auth_info(self, auth_info, affordances=None):
        affordances, _ = self._normalized_affordances(affordances, None)
        self._confirm_auth_info(auth_info, affordances=affordances)

    @property
    def input_source(self):
        return 'algorithm'

    @property
    def output_target(self):
        return 'scanner'

    @property
    def service(self):
        return self.authenticator.service

    @_abc.abstractmethod
    def _confirm_auth_info(self, auth_info, affordances):
        pass


class Scanner(Connector, _handlers.ProvisionSetHandler):

    """An authentication scanner

    A scanner examines requests and extracts authentication tokens from
    them.

    """

    __metaclass__ = _abc.ABCMeta

    @property
    def input_source(self):
        return 'clerk'

    @property
    def output_target(self):
        return 'algorithm'

    @property
    def service(self):
        return self.authenticator.service

    def _inputs(self, upstream_affordances, downstream_affordances):
        return self._outputs(upstream_affordances=upstream_affordances,
                             downstream_affordances=downstream_affordances)


class Supplicant(Connector, _handlers.ProvisionSetHandler,
                 _handlers.RealmHandler):

    """An authentication supplicant

    A supplicant communicates with an authentication backend, sending it the
    client's authentication tokens for verification.

    """

    __metaclass__ = _abc.ABCMeta

    @property
    def input_source(self):
        return 'algorithm'

    @property
    def output_target(self):
        return 'algorithm'

    def _opaque_passthrough(self, upstream_affordances,
                            downstream_affordances):
        return True

    def _tokens_passthrough(self, upstream_affordances,
                            downstream_affordances):
        return True
