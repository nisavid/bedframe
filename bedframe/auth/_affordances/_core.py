"""Affordances core"""

__copyright__ = "Copyright (C) 2014 Ivan D Vasin"
__docformat__ = "restructuredtext"

import abc as _abc
import re as _re

from spruce.collections \
    import frozenuset as _frozenuset, odict as _odict, uset as _uset

from .. import _exc
from .. import _provisions


class AffordanceSetABC(object):

    __metaclass__ = _abc.ABCMeta

    def __init__(self, realms=(), provisionsets=(), algorithms=()):
        self._set_algorithms(algorithms)
        self._set_provisionsets(provisionsets)
        self._set_realms(realms)

    def __and__(self, other):
        return self.__class__\
                (realms=(self._realms & other._realms),
                 provisionsets=
                     self._provisionsets.union_product(other._provisionsets),
                 algorithms=(self._algorithms & other._algorithms))

    def __eq__(self, other):
        if not isinstance(other, AffordanceSetABC):
            return False
        return self._algorithms == other._algorithms \
               and self._provisionsets == other._provisionsets \
               and self._realms == other._realms

    __hash__ = None

    def __ne__(self, other):
        return not self.__eq__(other)

    def __nonzero__(self):
        return bool(self._algorithms and self._provisionsets and self._realms)

    def __or__(self, other):
        return self.__class__\
                (realms=(self._realms | other._realms),
                 provisionsets=(self._provisionsets | other._provisionsets),
                 algorithms=(self._algorithms | other._algorithms))

    def __repr__(self):
        return '{}({})'.format(self.__class__.__name__,
                               ', '.join('{}={!r}'.format(property_, value)
                                         for property_, value
                                         in self._components_map(ordered=True)
                                                .items()))

    def __str__(self):
        properties_strs = []
        for property_, value in self._components_map(ordered=True).items():
            displayname = self._property_displayname(property_)
            if not value.isfinite:
                str_ = 'any ' + displayname
            else:
                str_ = '{} {}'.format(displayname, value)
            properties_strs.append(str_)
        return '{{{}}}'.format(', '.join(properties_strs))

    @property
    def algorithms(self):
        return self._algorithms

    def copy(self):
        return self.__class__(**self._components_map())

    @_abc.abstractmethod
    def frozen(self):
        pass

    @classmethod
    def max(cls):
        """An affordance set that matches all parameter values

        :rtype: :class:`AffordanceSetABC`

        """
        return cls(realms='*', provisionsets='*', algorithms='*')

    @classmethod
    def min(cls):
        """An affordance set that matches no parameter values

        :rtype: :class:`AffordanceSetABC`

        """
        return cls(realms=(), provisionsets=(), algorithms=())

    @property
    def provisionsets(self):
        return self._provisionsets

    @property
    def realms(self):
        return self._realms

    def require_finite(self, message=None, exceptions=()):
        infinite_components = \
            [name for name, value in self._components_map(ordered=True).items()
             if name not in exceptions
                and not getattr(value, 'isfinite', True)]
        if infinite_components:
            raise _exc.InfiniteAffordances(self, infinite_components, message)

    def require_nonempty(self, message=None, exceptions=()):
        empty_components = \
            [name for name, value in self._components_map(ordered=True).items()
             if name not in exceptions and not value]
        if empty_components:
            raise _exc.UnastisfiableAffordances(self, empty_components,
                                                message)

    @_abc.abstractmethod
    def unfrozen(self):
        pass

    @_abc.abstractmethod
    def unfrozen_copy(self):
        pass

    @classmethod
    @_abc.abstractmethod
    def _algorithms_class(cls):
        pass

    @classmethod
    def _frozen_class(cls):
        return FrozenAffordanceSet

    def _components_map(self, ordered=False):
        class_ = _odict if ordered else dict
        return class_((('realms', self.realms),
                       ('provisionsets', self.provisionsets),
                       ('algorithms', self.algorithms)))

    @classmethod
    def _property_displayname(cls, name):
        displayname = name
        displayname = displayname.replace('_', ' ')
        displayname = _re.sub(r'(?<=\w)sets', ' sets', displayname)
        return displayname

    @classmethod
    @_abc.abstractmethod
    def _provisionsets_class(cls):
        pass

    @classmethod
    @_abc.abstractmethod
    def _realms_class(cls):
        pass

    def _set_algorithms(self, value):
        class_ = self._algorithms_class()
        if isinstance(value, class_):
            self._algorithms = value
        else:
            self._algorithms = class_(value)

    def _set_provisionsets(self, value):
        class_ = self._provisionsets_class()
        if isinstance(value, class_):
            self._provisionsets = value
        else:
            self._provisionsets = class_(value)

    def _set_realms(self, value):
        class_ = self._realms_class()
        if isinstance(value, class_):
            self._realms = value
        else:
            self._realms = class_(value)

    @classmethod
    def _unfrozen_class(cls):
        return AffordanceSet


class AffordanceSet(AffordanceSetABC):

    """A set of authentication affordances"""

    def __iand__(self, other):
        self._algorithms &= other._algorithms
        self._provisionsets = \
            self._provisionsets.union_product(other._provisionsets)
        self._realms &= other._realms
        return self

    def __ior__(self, other):
        self._algorithms |= other._algorithms
        self._provisionsets |= other._provisionsets
        self._realms |= other._realms
        return self

    @AffordanceSetABC.algorithms.setter
    def algorithms(self, value):
        self._set_algorithms(value)

    def frozen(self):
        return self._frozen_class()(**self._components_map())

    @AffordanceSetABC.provisionsets.setter
    def provisionsets(self, value):
        self._set_provisionsets(value)

    @AffordanceSetABC.realms.setter
    def realms(self, value):
        self._set_realms(value)

    def unfrozen(self):
        return self

    def unfrozen_copy(self):
        return self.copy()

    @classmethod
    def _algorithms_class(cls):
        return _uset

    @classmethod
    def _provisionsets_class(cls):
        return _provisions.ProvisionSetSet

    @classmethod
    def _realms_class(cls):
        return _uset


class FrozenAffordanceSet(AffordanceSetABC):

    """An immutable set of authentication affordances"""

    def __hash__(self):
        return hash(self._algorithms) ^ hash(self._provisionsets) \
               ^ hash(self._realms)

    def __str__(self):
        return '=' + super(FrozenAffordanceSet, self).__str__()

    def frozen(self):
        return self

    @classmethod
    def max(cls):
        """An immutable affordance set that matches all parameter values

        :rtype: :class:`FrozenAffordanceSet`

        """
        return cls._MAX

    @classmethod
    def min(cls):
        """An immutable affordance set that matches no parameter values

        :rtype: :class:`FrozenAffordanceSet`

        """
        return cls._MIN

    def unfrozen(self):
        return self._unfrozen_class()(**self._components_map())

    def unfrozen_copy(self):
        return self.unfrozen()

    @classmethod
    def _algorithms_class(cls):
        return _frozenuset

    @classmethod
    def _provisionsets_class(cls):
        return _provisions.FrozenProvisionSetSet

    @classmethod
    def _realms_class(cls):
        return _frozenuset

FrozenAffordanceSet._MAX = \
    FrozenAffordanceSet(realms='*', provisionsets='*', algorithms='*')

FrozenAffordanceSet._MIN = \
    FrozenAffordanceSet(realms=(), provisionsets=(), algorithms=())
