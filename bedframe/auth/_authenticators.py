"""Authenticators"""

__copyright__ = "Copyright (C) 2014 Ivan D Vasin"
__docformat__ = "restructuredtext"

from functools import partial as _partial
from itertools import chain as _chain
import re as _re
import sys as _sys

import spruce.collections as _coll
from spruce.collections \
    import frozenset as _frozenset, frozenuset as _frozenuset, set as _set
import spruce.logging as _logging

from .. import _exc as _bedframe_exc
from . import _affordances
from . import _exc
from . import _info
from . import _spaces
from . import _tokens


class Authenticator(object):

    """An authenticator

    :param service:
        The web service.
    :type service:
        :class:`bedframe.WebServiceImpl <bedframe._services.WebServiceImpl>`

    """

    def __init__(self, service, spaces=None, algorithms=None, scanners=None,
                 clerks=None, supplicants=None, logger=None):
        self._algorithms = list(algorithms or ())
        self._clerks = list(clerks or ())
        self._current_auth_info = _info.RequestAuthInfo()
        self._logger = logger or service.logger.getChild('auth')
        self._scanners = list(scanners or ())
        self._spaces = _spaces.SpaceMap(spaces)
        self._supplicants = list(supplicants or ())
        self._service = service

    @property
    def algorithms(self):
        return self._algorithms

    @property
    def clerks(self):
        return self._clerks

    @property
    def current_auth_info(self):
        """Authentication information for the current request

        If no request is currently being handled, this is :obj:`None`.

        :type: :class:`~bedframe.auth._info.RequestAuthInfo` or null

        """
        return self.service.current_auth_info

    @current_auth_info.setter
    def current_auth_info(self, value):
        self.service.current_auth_info = value

    def ensure_auth(self, loc, realms='*', provisionsets='*', algorithms='*'):

        """Ensure authentication

        This method returns successfully if the request includes authentication
        information wherein the realm, security provisions, and algorithm
        satisfy the affordances of the authentication space defined for the
        given *loc*.  If additional *realms*, *provisionsets*, or *algorithms*
        are given, then those are applied as additional constraints beyond
        those imposed by the authentication space's affordances.

        .. note::
            Normally, the caller should not handle the
            :class:`bedframe.Unauthenticated <bedframe._exc.Unauthenticated>`
            exception or any of its subclasses
            (:class:`bedframe.AuthTokensNotGiven
            <bedframe._exc.AuthTokensNotGiven>` and
            :class:`bedframe.AuthTokensNotAccepted
            <bedframe._exc.AuthTokensNotAccepted>`).  These exceptions should
            be handled by the :class:`bedframe.WebServiceImpl
            <bedframe._services.WebServiceImpl>` so that it can respond
            accordingly.  To test whether the current request has appropriate
            authentication information, use :meth:`has_auth`.

        :param realms:
            Allowed realms.  This should be a subset of the realms afforded by
            the authentication space defined for the given *loc*.
        :type realms: ~u{str}

        :param provisionsets:
            Allowed security provision sets.  This should be a superset of the
            provision sets afforded by the authentication space defined for the
            given *loc*.
        :type provisionsets:
            ~\ :class:`~bedframe.auth._provisions.ProvisionSetSet`

        :param algorithms:
            Allowed algorithms.  This should be a subset of the
            algorithms afforded by the authentication space defined for the
            given *loc*.
        :type algorithms:
            ~u{:class:`~bedframe.auth._algorithms.Algorithm`}

        :raise bedframe.AuthTokenNotGiven:
            Raised if the request does not include an authentication token.

        :raise bedframe.AuthTokenNotAccepted:
            Raised if the request includes an authentication token that was not
            accepted by the authenticator.

        """

        if self.has_auth(loc=loc, realms=realms, provisionsets=provisionsets,
                         algorithms=algorithms):
            return

        affordances = \
            _affordances.AffordanceSet\
             (realms=(realms if realms is not None else '*'),
              provisionsets=(provisionsets if provisionsets is not None
                                           else '*'),
              algorithms=(algorithms if algorithms is not None else '*'))

        space = self.spaces.get(loc, None)

        def logmessage():
            message = 'authentication required at {}'.format(loc)
            if space:
                message += ' in space {}'.format(space)
            if affordances != _affordances.FrozenAffordanceSet.max():
                message += ' with {}'.format(affordances)
            return message
        self.logger.cond((_logging.DEBUG, logmessage))

        if algorithms:
            algorithms = _frozenuset(algorithms) & _frozenuset(self.algorithms)
        else:
            algorithms = _frozenuset(self.algorithms)
        clerks = _frozenuset(self.clerks)
        scanners = _frozenuset(self.scanners)
        supplicants = _frozenuset(self.supplicants)
        if space:
            algorithms = space.algorithms() & algorithms
            clerks = space.clerks & clerks
            scanners = space.scanners & scanners
            supplicants = space.supplicants & supplicants

        if space:
            affordances = space.affordances(upstream=affordances).unfrozen()
        else:
            affordances = _affordances.ProcessAffordanceSet.max()
        affordances.inputs = '*'
        affordances.outputs = '*'
        general_affordances = affordances.general
        general_affordances.require_nonempty()
        self.logger.cond((_logging.DEBUG,
                          lambda: 'given affordances {}'
                                   .format(general_affordances)))

        # filter connectors by general affordances
        resolution_affordances = \
            _affordances.ProcessProspectiveAffordanceSet\
             .from_general(affordances)
        algorithms_list = \
            [algorithm for algorithm in algorithms
             if algorithm.supports_affordances(upstream=affordances)]
        resolution_affordances.algorithms = algorithms_list
        resolution_affordances.clerks = \
            [clerk for clerk in clerks
             if clerk.supports_affordances(upstream=affordances)]
        resolution_affordances.scanners = \
            [scanner for scanner in scanners
             if scanner.supports_affordances(upstream=affordances)]
        resolution_affordances.supplicants = \
            [supplicant for supplicant in supplicants
             if supplicant.supports_affordances(upstream=affordances)]

        for connector_type in ('algorithm', 'clerk', 'scanner', 'supplicant'):
            if not getattr(resolution_affordances, connector_type + 's'):
                raise _exc.Error('no {} meets the necessary affordances {}'
                                  .format(connector_type, affordances))

        self.logger.cond((_logging.DEBUG,
                          lambda: 'considering algorithms {}'
                                   .format(resolution_affordances.algorithms)))
        self.logger.cond((_logging.DEBUG,
                          lambda: 'considering clerks {}'
                                   .format(resolution_affordances.clerks)))
        self.logger.cond((_logging.DEBUG,
                          lambda: 'considering scanners {}'
                                   .format(resolution_affordances.scanners)))
        self.logger\
            .cond((_logging.DEBUG,
                   lambda: 'considering supplicants {}'
                            .format(resolution_affordances.supplicants)))

        prospective_affordances = resolution_affordances.copy()
        prospective_affordances.outputs = ((),)
        prospective_affordances.scanners = \
            resolution_affordances.scanners.copy()
        scanned_auth_info = None
        for scanner in resolution_affordances.scanners:
            try:
                scanned_auth_info = \
                    scanner.process_tokens(affordances=resolution_affordances)
            except _exc.NoValidTokensScanned:
                pass
            else:
                scanned_tokens = scanned_auth_info.tokens
                message = 'scanner {} recognized tokens {}'
                self.logger\
                    .cond((_logging.INSECURE,
                           lambda: message.format(scanner, scanned_tokens)),
                          (_logging.DEBUG,
                           lambda: message.format(scanner,
                                                  scanned_tokens.keys())))
                prospective_affordances.outputs.add(scanned_tokens.frozen())
        if not prospective_affordances.scanners:
            prospective_affordances.scanners = resolution_affordances.scanners
        if not prospective_affordances.outputs:
            prospective_affordances.outputs.add(())

        prospective_affordances, phase = \
            self._best_resolved_prospective_affordances_and_phase\
             (prospective_affordances)

        if prospective_affordances is None:
            raise _exc.Error('cannot resolve an acceptable authentication'
                              ' process')
        prospective_affordances.require_nonempty()

        if scanned_auth_info:
            auth_info = scanned_auth_info
        else:
            auth_info = _info.RequestAuthInfo()

        prospective_affordances = prospective_affordances.unfrozen()
        self._update_afforded_tokens_from_auth_info(prospective_affordances,
                                                    auth_info)

        prospective_affordances.require_nonempty()
        prospective_affordances.require_finite(exceptions=('outputs'))

        realm = iter(prospective_affordances.realms).next()
        algorithm = iter(prospective_affordances.algorithms).next()
        clerk = iter(prospective_affordances.clerks).next()
        scanner = iter(prospective_affordances.scanners).next()
        supplicant = iter(prospective_affordances.supplicants).next()
        process_affordances = prospective_affordances.general

        auth_info.space = space
        auth_info.realm = realm
        auth_info.algorithm = algorithm
        auth_info.clerk = clerk
        auth_info.scanner = scanner
        auth_info.supplicant = supplicant

        self.logger.cond((_logging.DEBUG,
                          lambda: 'chose realm {}'.format(realm)))
        self.logger.cond((_logging.DEBUG,
                          lambda: 'chose algorithm {!r}'.format(algorithm)))
        self.logger.cond((_logging.DEBUG,
                          lambda: 'chose clerk {!r}'.format(clerk)))
        self.logger.cond((_logging.DEBUG,
                          lambda: 'chose scanner {!r}'.format(scanner)))
        self.logger.cond((_logging.DEBUG,
                          lambda: 'chose supplicant {!r}'.format(supplicant)))

        self.logger.cond((_logging.DEBUG,
                          lambda: 'starting authentication with phase {} and'
                                   ' affordances {}'
                                   .format(phase, process_affordances)))
        unauth_exc = None
        unauth_traceback = None
        try:
            auth_info = self._process_phase(phase,
                                            clerk=clerk,
                                            scanner=scanner,
                                            supplicant=supplicant,
                                            affordances=process_affordances,
                                            auth_info=auth_info)
        except _bedframe_exc.Unauthenticated as unauth_exc:
            unauth_traceback = _sys.exc_info()[2]

        self.current_auth_info = auth_info

        message = 'final info {}'
        self.logger\
            .cond((_logging.INSECURE,
                   lambda: message.format(auth_info.repr(insecure=True))),
                  (_logging.DEBUG,
                   lambda: message.format(auth_info.repr(insecure=False))))

        if unauth_exc:
            raise unauth_exc, None, unauth_traceback

        affordances = process_affordances.general
        if auth_info.verified:
            clerk.confirm_auth_info(auth_info, affordances=affordances)

            if not auth_info.accepted:
                raise _bedframe_exc.AuthTokensNotAccepted(affordances=affordances)

        else:
            # FIXME
            raise _exc.Error

    def has_auth(self, loc, realms='*', provisionsets='*', algorithms='*'):

        """Whether this request is authenticated

        This method returns :obj:`True` if the request includes authentication
        information wherein the realm, security provisions, and algorithm
        satisfy the affordances of the authentication space defined for the
        given *loc*.  If additional *realms*, *provisionsets*, or *algorithms*
        are given, then those are applied as additional constraints beyond
        those imposed by the authentication space's affordances.

        .. note::
            Normally, the caller should not handle the
            :class:`bedframe.Unauthenticated <bedframe._exc.Unauthenticated>`
            exception or any of its subclasses
            (:class:`bedframe.AuthTokensNotGiven
            <bedframe._exc.AuthTokensNotGiven>` and
            :class:`bedframe.AuthTokensNotAccepted
            <bedframe._exc.AuthTokensNotAccepted>`).  These exceptions should
            be handled by the :class:`bedframe.WebServiceImpl
            <bedframe._services.WebServiceImpl>` so that it can respond
            accordingly.  To test whether the current request has appropriate
            authentication information, use :meth:`has_auth`.

        :param realms:
            Allowed realms.  This should be a subset of the realms afforded by
            the authentication space defined for the given *loc*.
        :type realms: ~u{str}

        :param provisionsets:
            Allowed security provision sets.  This should be a superset of the
            provision sets afforded by the authentication space defined for the
            given *loc*.
        :type provisionsets:
            ~\ :class:`~bedframe.auth._provisions.ProvisionSetSet`

        :param algorithms:
            Allowed algorithms.  This should be a subset of the
            algorithms afforded by the authentication space defined for the
            given *loc*.
        :type algorithms:
            ~u{:class:`~bedframe.auth._algorithms.Algorithm`}

        :rtype: :obj:`bool`

        """

        affordances = \
            _affordances.AffordanceSet(realms=realms,
                                           provisionsets=provisionsets,
                                           algorithms=algorithms)

        return self.current_auth_info \
                   and self.current_auth_info.accepted \
                   and (not self.current_auth_info.space
                        or any(_re.match(spaceloc, loc)
                               for spaceloc
                               in self.spaces
                                      .locs(self.current_auth_info.space))) \
                   and self.current_auth_info.realm in affordances.realms \
                   and self.current_auth_info.provisions \
                       in affordances.provisionsets \
                   and self.current_auth_info.algorithm \
                       in affordances.algorithms

    @property
    def logger(self):
        return self._logger

    @property
    def scanners(self):
        return self._scanners

    @property
    def service(self):
        return self._service

    @property
    def spaces(self):
        return self._spaces

    @property
    def supplicants(self):
        return self._supplicants

    def _affordances_score(self, affordances):
        best_provisions_score = float('-inf')
        for provisions in affordances.provisionsets:
            score = self._provisions_score(provisions)
            if score > best_provisions_score:
                best_provisions_score = score
        return best_provisions_score

    def _best_resolved_prospective_affordances_and_phase(self, affordances):

        affordancesets_and_phases = \
            self._resolved_affordancesets_and_phases(affordances)

        best_affordances_score = float('-inf')
        best_phase_progress = float('-inf')
        best_affordances_and_phase = (None, None)
        for affordancesets, phase in affordancesets_and_phases:
            index = phase.index

            if index > best_phase_progress:
                best_affordances_score = float('-inf')
                best_affordances_and_phase = (None, None)

            best_phase_progress = max(best_phase_progress, index)

            if index == best_phase_progress:
                for affordances_ in affordancesets:
                    score = self._affordances_score(affordances_)
                    if score > best_affordances_score:
                        best_affordances_score = score
                        best_affordances_and_phase = (affordances_, phase)
        return best_affordances_and_phase

    def _considering_handlers_logmessage(self, *handlers):
        return 'considering connection ' \
               + ' --> '.join(str(handler) for handler in handlers)

    def _interconnect_affordances(self, connector, next_connector=None,
                                  affordances=None, auth_info=None):

        self._update_afforded_tokens_from_auth_info(affordances, auth_info)
        if next_connector:
            next_affordances = \
                next_connector.affordances(upstream=affordances)
            new_affordances = next_affordances.unfrozen()
            new_affordances.outputs = next_affordances.inputs
            new_affordances.inputs = affordances.inputs
            return new_affordances
        else:
            return affordances

    def _process_phase(self, phase, scanner, clerk, supplicant, affordances,
                       auth_info=None):

        affordances = affordances.unfrozen()
        auth_info = auth_info or _info.RequestAuthInfo()

        if phase.output_target == 'clerk':
            affordances = \
                self._interconnect_affordances(phase, clerk,
                                               affordances=affordances,
                                               auth_info=auth_info)
            auth_info = \
                self._process_tokens_updating_info(phase, auth_info,
                                                   affordances=affordances)

            affordances = \
                self._interconnect_affordances(clerk, scanner,
                                               affordances=affordances,
                                               auth_info=auth_info)
            return self._process_tokens_updating_info(clerk, auth_info,
                                                      affordances=affordances)

        elif phase.output_target == 'supplicant':
            affordances = \
                self._interconnect_affordances(phase, supplicant,
                                               affordances=affordances,
                                               auth_info=auth_info)
            auth_info = \
                self._process_tokens_updating_info(phase, auth_info,
                                                   affordances=affordances)

            affordances = \
                self._interconnect_affordances(supplicant, phase.next_phase,
                                               affordances=affordances,
                                               auth_info=auth_info)
            auth_info = \
                self._process_tokens_updating_info(supplicant, auth_info,
                                                   affordances=affordances)

            self._update_afforded_tokens_from_auth_info(affordances, auth_info)
            return self._process_phase(phase.next_phase,
                                       scanner=scanner,
                                       clerk=clerk,
                                       supplicant=supplicant,
                                       affordances=affordances,
                                       auth_info=auth_info)

        elif phase.output_target == 'end':
            self._update_afforded_tokens_from_auth_info(affordances, auth_info)
            return self._process_tokens_updating_info(phase, auth_info,
                                                      affordances=affordances)

        else:
            assert False, \
                   'invalid output target {!r} for authentication algorithm'\
                    ' phase {!r}; expecting one of {}'\
                    .format(phase.output_target, phase,
                            ('clerk', 'supplicant', 'end'))

        return _info.RequestAuthInfo()

    def _process_tokens_updating_info(self, connector, auth_info, affordances):

        input_ = auth_info.tokens

        def processing_logmessage(insecure):
            message = 'processing {} --> {}'\
                       .format(input_ if insecure else input_.keys(),
                               connector)
            if affordances.outputs != ((),):
                message += ' --> {}'.format(affordances.outputs)
            return message
        self.logger.cond((_logging.INSECURE,
                          _partial(processing_logmessage, insecure=True)),
                         (_logging.DEBUG,
                          _partial(processing_logmessage, insecure=False)),
                         )

        new_auth_info = connector.process_tokens(input=input_,
                                                 affordances=affordances)

        def processed_logmessage(insecure):
            message_ = 'processed {} --> {}'\
                        .format(input_ if insecure else input_.keys(),
                                connector)
            if affordances.outputs != ((),):
                message_ += ' --> {}'.format(new_auth_info.tokens
                                             if insecure
                                             else new_auth_info.tokens.keys())
            if new_auth_info.verified:
                message_ += ', {}'.format('accepted' if new_auth_info.accepted
                                                     else 'rejected')
            return message_
        self.logger.cond((_logging.INSECURE,
                          _partial(processed_logmessage, insecure=True)),
                         (_logging.DEBUG,
                          _partial(processed_logmessage, insecure=False)),
                         )

        if new_auth_info.realm is None:
            new_auth_info.realm = auth_info.realm
        new_auth_info.provisions &= auth_info.provisions
        if not new_auth_info.algorithm:
            new_auth_info.algorithm = auth_info.algorithm
        return new_auth_info

    def _resolved_entry_phase_affordancesets(self, phase, affordances):

        upstream_affordancesets = _set()
        downstream_affordances = affordances.unfrozen_copy()
        downstream_affordances.inputs = '*'
        downstream_affordances.outputs = '*'
        for resolved_input_affordances \
                in self._resolved_phase_input_affordancesets\
                    (phase, 'upstream',
                     reverse_affordances=downstream_affordances):
            upstream_affordances = resolved_input_affordances.unfrozen()
            upstream_affordances.inputs = '*'
            upstream_affordances.outputs = affordances.outputs
            upstream_affordancesets.add(upstream_affordances.frozen())

        self.logger.cond((_logging.DEBUG,
                          lambda: 'resolved upstream affordance sets {}'
                                   .format(upstream_affordancesets)))

        downstream_affordancesets = \
            _frozenset(_chain(*[self._resolved_phase_output_affordancesets
                                 (phase, 'downstream',
                                  reverse_affordances=upstream_affordances)
                                for upstream_affordances
                                in upstream_affordancesets]))

        self.logger.cond((_logging.DEBUG,
                          lambda: 'resolved downstream affordance sets {}'
                                   .format(downstream_affordancesets)))

        return downstream_affordancesets

    def _resolved_phase_input_affordancesets(self, phase, direction,
                                             reverse_affordances):

        if direction == 'upstream':
            phase_affordances = \
                _affordances.FrozenProcessProspectiveAffordanceSet\
                 .from_general\
                  (phase.affordances(downstream=reverse_affordances),
                   scanners=reverse_affordances.scanners,
                   clerks=reverse_affordances.clerks,
                   supplicants=reverse_affordances.supplicants)

            connector_inputs = None
            phase_inputs = phase_affordances.inputs
            phase_outputs = reverse_affordances.inputs
            try:
                phase_inputs = phase_inputs.set()
            except _coll.UnsupportedUniversalSetOperation:
                raise RuntimeError\
                       ('invalid acceptable inputs {!r} for authentication'
                         ' algorithm phase {!r}; expected a finite set of'
                         ' token sets'
                         .format(phase_inputs, phase))
        elif direction == 'downstream':
            if phase.input_source == 'start':
                pass
            elif phase.input_source == 'supplicant':
                connector_inputs = reverse_affordances.inputs
            else:
                connector_inputs = reverse_affordances.outputs
            phase_outputs = None
        else:
            raise ValueError('invalid direction {!r}: expecting {!r} or {!r}'
                              .format(direction, 'upstream', 'downstream'))

        def resolving_logmessage():
            message = 'walking {}, resolving input affordances for phase {}'\
                       ' (input from {}, output to {})'\
                       .format(direction, phase, phase.input_source,
                               phase.output_target)
            if connector_inputs:
                message += ' with {} inputs {}'.format(phase.input_source,
                                                       connector_inputs)
            elif phase_outputs:
                message += ' with outputs {}'.format(phase_outputs)
            return message
        self.logger.cond((_logging.DEBUG, resolving_logmessage))

        reverse_affordances = reverse_affordances.unfrozen_copy()
        if phase.input_source == 'start':
            if direction == 'upstream':
                return _frozenset((phase_affordances,))
            else:
                assert False
        elif phase.input_source == 'scanner':
            reverse_affordances.scanners = \
                reverse_affordances.scanners.unfrozen_copy()
            connectors = reverse_affordances.scanners
        elif phase.input_source == 'supplicant':
            reverse_affordances.supplicants = \
                reverse_affordances.supplicants.unfrozen_copy()
            connectors = reverse_affordances.supplicants
        else:
            assert False, \
                   'invalid input source {!r} for authentication'\
                    ' algorithm phase {!r}; expecting one of {}'\
                    .format(phase.input_source, phase,
                            ('start', 'scanner', 'supplicant'))

        affordancesets = _set()
        for connector in connectors.frozen():
            connector_useful = False
            if direction == 'upstream':
                for phase_input in phase_inputs:
                    if connector.supports_output(phase_input,
                                                 downstream_affordances=
                                                     phase_affordances):
                        self.logger.cond\
                         ((_logging.DEBUG,
                           _partial(self._considering_handlers_logmessage,
                                    connector, phase_input, phase)))
                        phase_connection_affordances = \
                            phase_affordances.unfrozen_copy()
                        phase_connection_affordances.inputs = (phase_input,)
                        connector_affordances = \
                            _affordances.ProcessProspectiveAffordanceSet\
                             .from_general\
                              (connector.affordances
                                (downstream=phase_connection_affordances),
                               scanners=reverse_affordances.scanners,
                               clerks=reverse_affordances.clerks,
                               supplicants=reverse_affordances.supplicants)
                        setattr(connector_affordances,
                                '{}s'.format(phase.input_source), (connector,))

                        if connector_affordances:
                            connector_useful = True
                            prev_phase = phase.prev_phase
                            if prev_phase:
                                prev_phase_affordancesets = \
                                    self._resolved_phase_output_affordancesets\
                                     (prev_phase, 'upstream',
                                      reverse_affordances=
                                          connector_affordances)
                                for prev_affordances \
                                        in prev_phase_affordancesets:
                                    affordances = prev_affordances.unfrozen()
                                    affordances.inputs = \
                                        connector_affordances.outputs
                                    affordances.outputs = phase_outputs
                                    affordancesets.add(affordances.frozen())
                            else:
                                affordancesets.add(connector_affordances
                                                    .frozen())
            else:
                if phase.input_source == 'scanner':
                    connector_affordances = \
                        _affordances.FrozenProcessProspectiveAffordanceSet\
                         .from_general\
                          (connector.affordances(upstream=reverse_affordances),
                           scanners=(connector,),
                           clerks=reverse_affordances.clerks,
                           supplicants=reverse_affordances.supplicants)
                elif phase.input_source == 'supplicant':
                    connector_affordances = reverse_affordances
                else:
                    assert False

                if connector_affordances:
                    connector_outputs = connector_affordances.outputs
                    for connector_output in connector_outputs:
                        if phase.supports_input(connector_output,
                                                upstream_affordances=
                                                    connector_affordances):
                            connector_useful = True
                            self.logger.cond\
                             ((_logging.DEBUG,
                               _partial(self._considering_handlers_logmessage,
                                        connector, connector_output, phase)),
                              )
                            connection_affordances = \
                                connector_affordances.unfrozen_copy()
                            connection_affordances.outputs = \
                                (connector_output,)
                            affordancesets |= \
                                self._resolved_phase_output_affordancesets\
                                 (phase, 'downstream',
                                  reverse_affordances=connection_affordances)

            if not connector_useful:
                connectors.remove(connector)
        return affordancesets

    def _resolved_phase_output_affordancesets(self, phase, direction,
                                              reverse_affordances):

        if direction == 'upstream':
            if phase.output_target == 'supplicant':
                connector_outputs = reverse_affordances.outputs
            elif phase.output_target == 'end':
                phase_affordances = \
                    phase.affordances(downstream=reverse_affordances)
            else:
                connector_outputs = reverse_affordances.inputs
            phase_inputs = None
        elif direction == 'downstream':
            phase_affordances = \
                _affordances.FrozenProcessProspectiveAffordanceSet\
                 .from_general\
                  (phase.affordances(upstream=reverse_affordances),
                   scanners=reverse_affordances.scanners,
                   clerks=reverse_affordances.clerks,
                   supplicants=reverse_affordances.supplicants)

            connector_outputs = None
            phase_inputs = reverse_affordances.outputs
            phase_outputs = phase_affordances.outputs
            try:
                phase_outputs = phase_outputs.set()
            except _coll.UnsupportedUniversalSetOperation:
                raise RuntimeError\
                       ('invalid acceptable outputs {!r} for authentication'
                         ' algorithm phase {!r}; expected a finite set of'
                         ' token sets'
                         .format(phase_outputs, phase))
        else:
            raise ValueError('invalid direction {!r}: expecting {!r} or {!r}'
                              .format(direction, 'upstream', 'downstream'))

        def resolving_logmessage():
            message = 'walking {}, resolving output affordances for phase {}'\
                       ' (input from {}, output to {})'\
                       .format(direction, phase, phase.input_source,
                               phase.output_target)
            if connector_outputs:
                message += ' with {} outputs {}'.format(phase.output_target,
                                                        connector_outputs)
            elif phase_inputs:
                message += ' with inputs {}'.format(phase_inputs)
            return message
        self.logger.cond((_logging.DEBUG, resolving_logmessage))

        reverse_affordances = reverse_affordances.unfrozen_copy()
        if phase.output_target == 'clerk':
            reverse_affordances.clerks = \
                reverse_affordances.clerks.unfrozen_copy()
            connectors = reverse_affordances.clerks
        elif phase.output_target == 'supplicant':
            reverse_affordances.supplicants = \
                reverse_affordances.supplicants.unfrozen_copy()
            connectors = reverse_affordances.supplicants
        elif phase.output_target == 'end':
            if direction == 'downstream':
                return _frozenset((phase_affordances,))
            else:
                assert False
        else:
            assert False, \
                   'invalid output target {!r} for authentication'\
                   ' algorithm phase {!r}; expecting one of {}'\
                    .format(phase.input_source, phase,
                            ('clerk', 'supplicant', 'end'))

        affordancesets = _set()
        for connector in connectors.frozen():
            connector_useful = False
            if direction == 'upstream':
                if phase.output_target == 'clerk':
                    connector_affordances = \
                        _affordances.FrozenProcessProspectiveAffordanceSet\
                         .from_general\
                          (connector.affordances(downstream=
                                                     reverse_affordances),
                           scanners=reverse_affordances.scanners,
                           clerks=(connector,),
                           supplicants=reverse_affordances.supplicants)
                elif phase.output_target == 'supplicant':
                    connector_affordances = reverse_affordances
                else:
                    assert False

                if connector_affordances:
                    connector_inputs = connector_affordances.inputs
                    for connector_input in connector_inputs:
                        if phase.supports_output(connector_input,
                                                 downstream_affordances=
                                                     connector_affordances):
                            connector_useful = True
                            self.logger.cond\
                             ((_logging.DEBUG,
                               _partial(self._considering_handlers_logmessage,
                                        phase, connector_input, connector)))
                            connection_affordances = \
                                connector_affordances.unfrozen_copy()
                            connection_affordances.inputs = (connector_input,)
                            affordancesets |= \
                                self._resolved_phase_input_affordancesets\
                                 (phase, 'upstream',
                                  reverse_affordances=connector_affordances)
            else:
                for phase_output in phase_outputs:
                    if connector.supports_input(phase_output,
                                                upstream_affordances=
                                                    phase_affordances):
                        self.logger.cond\
                         ((_logging.DEBUG,
                           _partial(self._considering_handlers_logmessage,
                                    phase, phase_output, connector)))
                        phase_connection_affordances = \
                            phase_affordances.unfrozen_copy()
                        phase_connection_affordances.outputs = (phase_output,)
                        connector_affordances = \
                            _affordances.ProcessProspectiveAffordanceSet\
                             .from_general\
                              (connector.affordances
                                (upstream=phase_connection_affordances),
                               scanners=reverse_affordances.scanners,
                               clerks=reverse_affordances.clerks,
                               supplicants=reverse_affordances.supplicants)
                        setattr(connector_affordances,
                                '{}s'.format(phase.output_target),
                                (connector,))

                        if connector_affordances:
                            connector_useful = True
                            next_phase = phase.next_phase
                            if next_phase:
                                next_phase_affordancesets = \
                                    self._resolved_phase_input_affordancesets\
                                     (next_phase, 'downstream',
                                      reverse_affordances=
                                          connector_affordances)
                                for next_affordances \
                                        in next_phase_affordancesets:
                                    affordances = next_affordances.unfrozen()
                                    affordances.inputs = phase_inputs
                                    affordances.outputs = \
                                        connector_affordances.inputs
                                    affordancesets.add(affordances.frozen())
                            else:
                                affordancesets.add(connector_affordances
                                                    .frozen())

            if not connector_useful:
                connectors.remove(connector)
        return affordancesets

    def _resolved_affordancesets_and_phases(self, affordances):
        affordancesets_and_phases = []
        for algorithm in affordances.algorithms:
            phase = algorithm.next_phase(upstream_affordances=affordances)

            def logmessage():
                message = 'algorithm {}'.format(algorithm)
                if phase:
                    message += ' recognized the next phase {}'.format(phase)
                else:
                    message += ' did not recognize a next phase'
                return message
            self.logger.cond((_logging.DEBUG, logmessage))

            if not phase:
                continue

            affordancesets_and_phases\
             .append((self._resolved_entry_phase_affordancesets
                       (phase, affordances=affordances),
                      phase))
        return affordancesets_and_phases

    def _provisions_score(self, provisions):
        # FIXME
        return provisions._flags

    def _update_afforded_tokens_from_auth_info(self, affordances, auth_info):
        affordances.inputs = _tokens.tokens_combinations(auth_info.tokens)
        affordances.outputs = '*'
