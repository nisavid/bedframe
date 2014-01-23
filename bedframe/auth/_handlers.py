"""Parameter handlers"""

__copyright__ = "Copyright (C) 2014 Ivan D Vasin"
__docformat__ = "restructuredtext"

import abc as _abc
from itertools import product as _product

from spruce.collections \
    import frozenuset as _frozenuset, frozenusetset as _frozenusetset

from .. import _exc
from . import _affordances
from . import _provisions
from . import _tokens


class ParamHandler(object):

    __metaclass__ = _abc.ABCMeta

    def affordances(self, upstream=None, downstream=None):
        kwargs = self._affordances_kwargs(upstream=upstream,
                                          downstream=downstream)
        for name in ('realms', 'provisionsets', 'algorithms'):
            if name not in kwargs:
                if upstream is not None:
                    if downstream is not None:
                        kwargs[name] = getattr(upstream, name) \
                                       & getattr(downstream, name)
                    else:
                        kwargs[name] = getattr(upstream, name)
                elif downstream is not None:
                    kwargs[name] = getattr(downstream, name)
                else:
                    kwargs[name] = '*'
        for name in ('inputs', 'outputs'):
            if name not in kwargs:
                kwargs[name] = '*'
        return _affordances.FrozenProcessAffordanceSet(**kwargs)

    @_abc.abstractmethod
    def supports_affordances(self, upstream=None, downstream=None):
        return True

    def supports_any_affordances(self, upstream=None, downstream=None):
        if upstream is not None:
            if downstream is not None:
                return any(self.supports_affordances(one_upstream,
                                                     one_downstream)
                           for one_upstream, one_downstream
                           in _product(upstream, downstream))
            else:
                return any(self.supports_affordances(one_upstream, None)
                           for one_upstream in upstream)
        else:
            if downstream is not None:
                return any(self.supports_affordances(None, one_downstream)
                           for one_downstream in downstream)
            else:
                return True

    @_abc.abstractmethod
    def _affordances_kwargs(self, upstream=None, downstream=None):
        return {}

    def _normalized_affordances(self, upstream, downstream):
        return (upstream
                    if upstream is not None
                    else _affordances.FrozenProcessAffordanceSet.max(),
                downstream
                    if downstream is not None
                    else _affordances.FrozenProcessAffordanceSet.max(),
                )


class AlgorithmHandler(ParamHandler):

    __metaclass__ = _abc.ABCMeta

    def algorithms(self, upstream_affordances=None,
                   downstream_affordances=None):
        upstream_affordances, downstream_affordances = \
            self._normalized_affordances(upstream_affordances,
                                         downstream_affordances)
        return _frozenuset(self._algorithms(upstream_affordances=
                                                upstream_affordances,
                                            downstream_affordances=
                                                downstream_affordances)) \
               & upstream_affordances.algorithms \
               & downstream_affordances.algorithms

    def require_algorithm_supported(self, algorithm, upstream_affordances=None,
                                    downstream_affordances=None):
        if not self.supports_algorithm(algorithm,
                                       upstream_affordances=
                                           upstream_affordances,
                                       downstream_affordances=
                                           downstream_affordances):
            raise _exc.RequiredAlgorithmNotSupported\
                   (algorithm,
                    handler=self,
                    supported_values=
                        self.algorithms
                            (upstream_affordances=upstream_affordances,
                             downstream_affordances=downstream_affordances))

    def requires_algorithm(self, algorithm, upstream_affordances=None,
                           downstream_affordances=None):
        return self.algorithms(upstream_affordances=upstream_affordances,
                               downstream_affordances=downstream_affordances)\
               == (algorithm,)

    def supports_affordances(self, upstream=None, downstream=None):
        if upstream is not None \
               and not self.supports_any_algorithm(upstream.algorithms):
            return False
        if downstream is not None \
               and not self.supports_any_algorithm(downstream.algorithms):
            return False
        return super(AlgorithmHandler, self)\
                .supports_affordances(upstream=upstream, downstream=downstream)

    def supports_algorithm(self, algorithm, upstream_affordances=None,
                           downstream_affordances=None):
        return algorithm \
               in self.algorithms(upstream_affordances=upstream_affordances,
                                  downstream_affordances=
                                      downstream_affordances)

    def supports_any_algorithm(self, algorithms, upstream_affordances=None,
                               downstream_affordances=None):

        if not algorithms:
            return False

        return not algorithms.isfinite \
               or any(self.supports_algorithm(algorithm,
                                              upstream_affordances=
                                                  upstream_affordances,
                                              downstream_affordances=
                                                  downstream_affordances)
                      for algorithm in algorithms.set())

    def _affordances_kwargs(self, upstream=None, downstream=None):
        kwargs = super(AlgorithmHandler, self)\
                  ._affordances_kwargs(upstream=upstream,
                                       downstream=downstream)
        kwargs['algorithms'] = \
            self.algorithms(upstream_affordances=upstream,
                            downstream_affordances=downstream)
        return kwargs

    @_abc.abstractmethod
    def _algorithms(self, upstream_affordances, downstream_affordances):
        pass


class ProvisionSetHandler(ParamHandler):

    __metaclass__ = _abc.ABCMeta

    def guarantees_provisions(self, provisions, upstream_affordances=None,
                              downstream_affordances=None):
        provisions = _provisions.FrozenProvisionSet(provisions)
        return self.provisionsets(upstream_affordances=upstream_affordances,
                                  downstream_affordances=
                                      downstream_affordances)\
                   .all_gte(provisions)

    def provisionsets(self, upstream_affordances=None,
                      downstream_affordances=None):

        upstream_affordances, downstream_affordances = \
            self._normalized_affordances(upstream_affordances,
                                         downstream_affordances)

        provisionsets = \
            _provisions.FrozenProvisionSetSet\
                (self._provisionsets(upstream_affordances=upstream_affordances,
                                     downstream_affordances=
                                         downstream_affordances))
        return _provisions.FrozenProvisionSetSet\
                   (provisions for provisions in provisionsets
                    if upstream_affordances.provisionsets.any_gte(provisions)
                       and downstream_affordances.provisionsets
                                                 .any_gte(provisions))

    def require_provisions_supported(self, provisions,
                                     upstream_affordances=None,
                                     downstream_affordances=None):
        if not self.supports_provisions(provisions,
                                        upstream_affordances=
                                            upstream_affordances,
                                        downstream_affordances=
                                            downstream_affordances):
            raise _exc.RequiredProvisionsNotSupported\
                   (provisions,
                    handler=self,
                    supported_values=
                        self.provisionsets
                            (upstream_affordances=upstream_affordances,
                             downstream_affordances=downstream_affordances))

    def supports_affordances(self, upstream=None, downstream=None):
        if upstream is not None \
               and not self.supports_any_provisions(upstream.provisionsets):
            return False
        if downstream is not None \
               and not self.supports_any_provisions(downstream.provisionsets):
            return False
        return super(ProvisionSetHandler, self)\
                .supports_affordances(upstream=upstream, downstream=downstream)

    def supports_any_provisions(self, provisionsets, upstream_affordances=None,
                                downstream_affordances=None):

        if not provisionsets:
            return False

        provisionsets = _provisions.FrozenProvisionSetSet(provisionsets)
        return not provisionsets.isfinite \
               or any(self.supports_provisions(provisions,
                                               upstream_affordances=
                                                   upstream_affordances,
                                               downstream_affordances=
                                                   downstream_affordances)
                      for provisions in provisionsets.set())

    def supports_provisions(self, provisions, upstream_affordances=None,
                            downstream_affordances=None):
        provisions = _provisions.FrozenProvisionSet(provisions)
        return self.provisionsets(upstream_affordances=upstream_affordances,
                                  downstream_affordances=
                                      downstream_affordances)\
                   .any_gte(provisions)

    def _affordances_kwargs(self, upstream=None, downstream=None):
        kwargs = super(ProvisionSetHandler, self)\
                  ._affordances_kwargs(upstream=upstream,
                                       downstream=downstream)
        kwargs['provisionsets'] = \
            self.provisionsets(upstream_affordances=upstream,
                               downstream_affordances=downstream)
        return kwargs

    @_abc.abstractmethod
    def _provisionsets(self, upstream_affordances, downstream_affordances):
        pass


class RealmHandler(ParamHandler):

    __metaclass__ = _abc.ABCMeta

    def realms(self, upstream_affordances=None, downstream_affordances=None):
        upstream_affordances, downstream_affordances = \
            self._normalized_affordances(upstream_affordances,
                                         downstream_affordances)
        return _frozenuset(self._realms(upstream_affordances=
                                            upstream_affordances,
                                        downstream_affordances=
                                            downstream_affordances)) \
               & upstream_affordances.realms \
               & downstream_affordances.realms

    def require_realm_supported(self, realm, upstream_affordances=None,
                                downstream_affordances=None):
        if not self.supports_realm(realm,
                                   upstream_affordances=upstream_affordances,
                                   downstream_affordances=
                                       downstream_affordances):
            raise _exc.RequiredrealmsNotSupported\
                      (realm,
                       handler=self,
                       supported_values=
                           self.realms(upstream_affordances=
                                           upstream_affordances,
                                       downstream_affordances=
                                           downstream_affordances))

    def requires_realm(self, realm, upstream_affordances=None,
                       downstream_affordances=None):
        return self.realms(upstream_affordances=upstream_affordances,
                           downstream_affordances=downstream_affordances) \
               == (realm,)

    def supports_affordances(self, upstream=None, downstream=None):
        if upstream is not None \
               and not self.supports_any_realm(upstream.realms):
            return False
        if downstream is not None \
               and not self.supports_any_realm(downstream.realms):
            return False
        return super(RealmHandler, self)\
                   .supports_affordances(upstream=upstream,
                                         downstream=downstream)

    def supports_any_realm(self, realms, upstream_affordances=None,
                           downstream_affordances=None):

        if not realms:
            return False

        return not realms.isfinite \
               or any(self.supports_realm(realm,
                                          upstream_affordances=
                                              upstream_affordances,
                                          downstream_affordances=
                                              downstream_affordances)
                      for realm in realms.set())

    def supports_realm(self, realm, upstream_affordances=None,
                       downstream_affordances=None):
        return realm in self.realms(upstream_affordances=upstream_affordances,
                                    downstream_affordances=
                                        downstream_affordances)

    def _affordances_kwargs(self, upstream=None, downstream=None):
        kwargs = super(RealmHandler, self)\
                  ._affordances_kwargs(upstream=upstream,
                                       downstream=downstream)
        kwargs['realms'] = \
            self.realms(upstream_affordances=upstream,
                        downstream_affordances=downstream)
        return kwargs

    @_abc.abstractmethod
    def _realms(self, upstream_affordances, downstream_affordances):
        pass


class TokenHandler(ParamHandler):

    __metaclass__ = _abc.ABCMeta

    def guarantees_output(self, names, upstream_affordances=None,
                          downstream_affordances=None):
        try:
            names = set(names)
        except TypeError:
            raise TypeError('invalid token names type {!r}: expecting an'
                            ' iterable; token names {!r}'
                             .format(names.__class__, names))
        return self.outputs(upstream_affordances=upstream_affordances,
                            downstream_affordances=downstream_affordances)\
                   .all_gte(names)

    @_abc.abstractproperty
    def input_source(self):
        pass

    def inputs(self, upstream_affordances=None, downstream_affordances=None):

        upstream_affordances, downstream_affordances = \
            self._normalized_affordances(upstream_affordances,
                                         downstream_affordances)

        inputs = _frozenusetset(self._inputs(upstream_affordances=
                                                 upstream_affordances,
                                             downstream_affordances=
                                                 downstream_affordances))
        if inputs.isfinite:
            return _frozenusetset(input_ for input_ in inputs
                                  if upstream_affordances.outputs
                                                         .any_gte(input_))
        else:
            return upstream_affordances.outputs

    def opaque_passthrough(self, upstream_affordances=None,
                           downstream_affordances=None):
        upstream_affordances, downstream_affordances = \
            self._normalized_affordances(upstream_affordances,
                                         downstream_affordances)
        if '__' not in upstream_affordances.outputs:
            return False
        return self._opaque_passthrough(upstream_affordances=
                                            upstream_affordances,
                                        downstream_affordances=
                                            downstream_affordances)

    @_abc.abstractproperty
    def output_target(self):
        pass

    def outputs(self, upstream_affordances=None, downstream_affordances=None):

        upstream_affordances, downstream_affordances = \
            self._normalized_affordances(upstream_affordances,
                                         downstream_affordances)

        outputs = _frozenusetset(self._outputs(upstream_affordances=
                                                   upstream_affordances,
                                               downstream_affordances=
                                                   downstream_affordances))
        if self.tokens_passthrough(upstream_affordances=
                                       upstream_affordances,
                                   downstream_affordances=
                                       downstream_affordances):
            outputs = upstream_affordances.outputs.union_product(outputs)
        if self.opaque_passthrough(upstream_affordances=
                                       upstream_affordances,
                                   downstream_affordances=
                                       downstream_affordances):
            outputs = outputs.union_product((('__',),))
        if outputs.isfinite:
            return _frozenusetset(output for output in outputs
                                  if downstream_affordances.inputs
                                                           .any_lte(output))
        else:
            return outputs

    def process_tokens(self, input=(), affordances=None):

        if not isinstance(input, _tokens.TokenMapABC):
            input = _tokens.FrozenTokenMap(input)
        affordances, _ = self._normalized_affordances(affordances, None)

        if self.opaque_passthrough(upstream_affordances=affordances) \
               and '__' in input:
            opaque_passthrough = True
            opaque_data = input['__']
        else:
            opaque_passthrough = False

        auth_info = self._process_tokens(input=input, affordances=affordances)

        if auth_info.verified:
            auth_info.tokens['accepted'] = str(auth_info.accepted)
        if opaque_passthrough:
            auth_info.tokens['__'] = opaque_data

        return auth_info

    def require_any_input_supported(self, inputs, upstream_affordances=None,
                                    downstream_affordances=None):
        if not self.supports_any_input(inputs,
                                       upstream_affordances=
                                           upstream_affordances,
                                       downstream_affordances=
                                           downstream_affordances):
            raise _exc.RequiredInputsNotSupported\
                   (_tokens.tokens_names(inputs),
                    handler=self,
                    supported_values=
                        self.inputs(upstream_affordances=upstream_affordances,
                                    downstream_affordances=
                                        downstream_affordances))

    def require_any_output_supported(self, outputs, upstream_affordances=None,
                                     downstream_affordances=None):
        if not self.supports_any_output(outputs,
                                        upstream_affordances=
                                            upstream_affordances,
                                        downstream_affordances=
                                            downstream_affordances):
            raise _exc.RequiredOutputsNotSupported\
                   (outputs,
                    handler=self,
                    supported_values=
                        self.outputs(upstream_affordances=upstream_affordances,
                                     downstream_affordances=
                                         downstream_affordances))

    def require_input_supported(self, tokens_or_names,
                                upstream_affordances=None,
                                downstream_affordances=None):
        if not self.supports_input(tokens_or_names,
                                   upstream_affordances=upstream_affordances,
                                   downstream_affordances=
                                       downstream_affordances):
            raise _exc.RequiredInputNotSupported\
                   (_tokens.tokens_names(tokens_or_names),
                    handler=self,
                    supported_values=
                        self.inputs(upstream_affordances=upstream_affordances,
                                    downstream_affordances=
                                        downstream_affordances))

    def require_output_supported(self, output, upstream_affordances=None,
                                 downstream_affordances=None):
        if not self.supports_output(output,
                                    upstream_affordances=upstream_affordances,
                                    downstream_affordances=
                                        downstream_affordances):
            raise _exc.RequiredOutputNotSupported\
                   (output,
                    handler=self,
                    supported_values=
                        self.outputs(upstream_affordances=upstream_affordances,
                                     downstream_affordances=
                                         downstream_affordances))

    def requires_input(self, tokens_or_names, upstream_affordances=None,
                       downstream_affordances=None):
        names = _tokens.tokens_names(tokens_or_names)
        return self.inputs(upstream_affordances=upstream_affordances,
                           downstream_affordances=downstream_affordances)\
                   .all_gte(names)

    def supports_affordances(self, upstream=None, downstream=None):
        if upstream is not None \
               and not self.supports_any_input(upstream.outputs):
            return False
        if downstream is not None \
               and not self.supports_any_output(downstream.inputs):
            return False
        return super(TokenHandler, self)\
                .supports_affordances(upstream=upstream, downstream=downstream)

    def supports_any_input(self, inputs, upstream_affordances=None,
                           downstream_affordances=None):

        if not inputs:
            return False

        return not inputs.isfinite \
               or any(self.supports_input(input,
                                          upstream_affordances=
                                              upstream_affordances,
                                          downstream_affordances=
                                              downstream_affordances)
                      for input in inputs.set())

    def supports_any_output(self, outputs, upstream_affordances=None,
                            downstream_affordances=None):

        if not outputs:
            return False

        return not outputs.isfinite \
               or any(self.supports_output(output,
                                           upstream_affordances=
                                               upstream_affordances,
                                           downstream_affordances=
                                               downstream_affordances)
                      for output in outputs.set())

    def supports_input(self, tokens_or_names, upstream_affordances=None,
                       downstream_affordances=None):
        names = _tokens.tokens_names(tokens_or_names)
        return self.inputs(upstream_affordances=upstream_affordances,
                           downstream_affordances=downstream_affordances)\
                   .any_lte(names)

    def supports_output(self, names, upstream_affordances=None,
                        downstream_affordances=None):
        try:
            names = set(names)
        except TypeError:
            raise TypeError('invalid token names type {!r}: expecting an'
                             ' iterable; given token names {!r}'
                             .format(names.__class__, names))
        return self.outputs(upstream_affordances=upstream_affordances,
                            downstream_affordances=downstream_affordances)\
                   .any_gte(names)

    def tokens_passthrough(self, upstream_affordances=None,
                           downstream_affordances=None):
        upstream_affordances, downstream_affordances = \
            self._normalized_affordances(upstream_affordances,
                                         downstream_affordances)
        return self._tokens_passthrough(upstream_affordances=
                                            upstream_affordances,
                                        downstream_affordances=
                                            downstream_affordances)

    def _affordances_kwargs(self, upstream=None, downstream=None):
        kwargs = super(TokenHandler, self)\
                  ._affordances_kwargs(upstream=upstream,
                                       downstream=downstream)
        kwargs['inputs'] = \
            self.inputs(upstream_affordances=upstream,
                        downstream_affordances=downstream)
        kwargs['outputs'] = \
            self.outputs(upstream_affordances=upstream,
                         downstream_affordances=downstream)
        return kwargs

    @_abc.abstractmethod
    def _inputs(self, upstream_affordances, downstream_affordances):
        pass

    def _opaque_passthrough(self, upstream_affordances,
                            downstream_affordances):
        return self._tokens_passthrough(upstream_affordances=
                                            upstream_affordances,
                                        downstream_affordances=
                                            downstream_affordances)

    @_abc.abstractmethod
    def _outputs(self, upstream_affordances, downstream_affordances):
        pass

    @_abc.abstractmethod
    def _process_tokens(self, input, affordances):
        pass

    def _tokens_passthrough(self, upstream_affordances,
                            downstream_affordances):
        return False
