"""Process affordances"""

__copyright__ = "Copyright (C) 2014 Ivan D Vasin"
__docformat__ = "restructuredtext"

import abc as _abc

from spruce.collections \
    import frozenusetset as _frozenusetset, usetset as _usetset

from . import _core as _affordances_core


class ProcessAffordanceSetABC(_affordances_core.AffordanceSetABC):

    __metaclass__ = _abc.ABCMeta

    def __init__(self, inputs=(), outputs=(), _general=None, **kwargs):

        if _general is not None:
            if kwargs:
                general_init_args = _general._components_map()
                general_init_args.update(kwargs)
                _general = self._general_class()(**general_init_args)
            self.__dict__['_general'] = _general
        else:
            self.__dict__['_general'] = self._general_class()(**kwargs)

        self._set_inputs(inputs)
        self._set_outputs(outputs)

    def __and__(self, other):
        return self.__class__\
                (inputs=self._inputs.intersection_product(other._inputs),
                 outputs=self._outputs.union_product(other._outputs),
                 _general=(self._general & other._general))

    def __eq__(self, other):
        if not isinstance(other, ProcessAffordanceSetABC):
            return False
        return self._general == other._general \
               and self._outputs == other._outputs \
               and self._inputs == other._inputs

    def __getattr__(self, name):
        return getattr(self._general, name)

    def __nonzero__(self):
        return bool(self._general and self._outputs and self._inputs)

    def __or__(self, other):
        return self.__class__\
                (inputs=(self._inputs | other._inputs),
                 outputs=(self._outputs | other._outputs),
                 _general=(self._general | other._general))

    def __setattr__(self, name, value):
        if hasattr(self._general, name):
            setattr(self._general, name, value)
        else:
            object.__setattr__(self, name, value)

    @classmethod
    @_abc.abstractmethod
    def from_general(cls, affordances, **kwargs):
        pass

    @property
    def general(self):
        return self._general

    @classmethod
    def min(cls):
        """An affordance set that accepts no parameter values

        :rtype: :class:`ProcessAffordanceSetABC`

        """
        return cls(inputs=(), outputs=(), _general=cls._general_class().min())

    @classmethod
    def max(cls):
        """An affordance set that accepts all parameter values

        :rtype: :class:`ProcessAffordanceSetABC`

        """
        return cls(inputs='*', outputs='*',
                   _general=cls._general_class().max())

    @property
    def inputs(self):
        return self._inputs

    @property
    def outputs(self):
        return self._outputs

    @classmethod
    def _frozen_class(cls):
        return FrozenProcessAffordanceSet

    @classmethod
    @_abc.abstractmethod
    def _general_class(cls):
        pass

    def _components_map(self, ordered=False):
        components = super(ProcessAffordanceSetABC, self)\
                      ._components_map(ordered=ordered)
        components.update((('inputs', self.inputs),
                           ('outputs', self.outputs)))
        return components

    @classmethod
    @_abc.abstractmethod
    def _inputs_class(cls):
        pass

    @classmethod
    @_abc.abstractmethod
    def _outputs_class(cls):
        pass

    def _set_inputs(self, value):
        class_ = self._inputs_class()
        if isinstance(value, class_):
            self._inputs = value
        else:
            self._inputs = class_(value)

    def _set_outputs(self, value):
        class_ = self._outputs_class()
        if isinstance(value, class_):
            self._outputs = value
        else:
            self._outputs = class_(value)

    @classmethod
    def _unfrozen_class(cls):
        return ProcessAffordanceSet


class ProcessAffordanceSet(ProcessAffordanceSetABC):

    """A set of authentication process affordances"""

    def __iand__(self, other):
        self._general &= other._general
        self._inputs = self._inputs.intersection_product(other._inputs)
        self._outputs = self._outputs.union_product(other._outputs)
        return self

    def __ior__(self, other):
        self._general |= other._general
        self._inputs |= other._inputs
        self._outputs |= other._outputs
        return self

    @classmethod
    def _general_class(cls):
        return _affordances_core.AffordanceSet

    @classmethod
    def from_general(cls, affordances, **kwargs):
        return cls(_general=affordances.unfrozen(), **kwargs)

    def frozen(self):
        return self._frozen_class()(**self._components_map())

    @ProcessAffordanceSetABC.inputs.setter
    def inputs(self, value):
        self._set_inputs(value)

    @ProcessAffordanceSetABC.outputs.setter
    def outputs(self, value):
        self._set_outputs(value)

    def unfrozen(self):
        return self

    def unfrozen_copy(self):
        return self.copy()

    @classmethod
    def _inputs_class(cls):
        return _usetset

    @classmethod
    def _outputs_class(cls):
        return _usetset


class FrozenProcessAffordanceSet(ProcessAffordanceSetABC):

    """An immutable set of authentication process affordances"""

    def __hash__(self):
        return hash(self._general) ^ hash(self._inputs) ^ hash(self._outputs)

    def __str__(self):
        return '=' + super(FrozenProcessAffordanceSet, self).__str__()

    @classmethod
    def from_general(cls, affordances, **kwargs):
        return cls(_general=affordances.frozen(), **kwargs)

    def frozen(self):
        return self

    @classmethod
    def max(cls):
        """An immutable affordance set that matches all parameter values

        :rtype: :class:`FrozenProcessAffordanceSet`

        """
        return cls._MAX

    @classmethod
    def min(cls):
        """
        An immutable process affordance set that matches no parameter values

        :rtype: :class:`FrozenProcessAffordanceSet`

        """
        return cls._MIN

    def unfrozen(self):
        return self._unfrozen_class()(**self._components_map())

    def unfrozen_copy(self):
        return self.unfrozen()

    @classmethod
    def _general_class(cls):
        return _affordances_core.FrozenAffordanceSet

    @classmethod
    def _inputs_class(cls):
        return _frozenusetset

    @classmethod
    def _outputs_class(cls):
        return _frozenusetset

FrozenProcessAffordanceSet._MAX = \
    FrozenProcessAffordanceSet(realms='*', provisionsets='*', algorithms='*',
                               inputs='*', outputs='*')

FrozenProcessAffordanceSet._MIN = \
    FrozenProcessAffordanceSet(realms=(), provisionsets=(), algorithms=(),
                               inputs=(), outputs=())
