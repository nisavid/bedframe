"""Prospective process affordances"""

__copyright__ = "Copyright (C) 2014 Ivan D Vasin"
__docformat__ = "restructuredtext"

import abc as _abc

from spruce.collections import frozenuset as _frozenuset, uset as _uset

from . import _process as _process_affordances


class ProcessProspectiveAffordanceSetABC(_process_affordances
                                          .ProcessAffordanceSetABC):

    def __init__(self, scanners=(), clerks=(), supplicants=(), _general=None,
                 **kwargs):

        if _general is not None:
            if kwargs:
                general_init_args = _general._components_map()
                general_init_args.update(kwargs)
                _general = self._general_class()(**general_init_args)
            self.__dict__['_general'] = _general
        else:
            self.__dict__['_general'] = self._general_class()(**kwargs)

        self._set_clerks(clerks)
        self._set_scanners(scanners)
        self._set_supplicants(supplicants)

    def __and__(self, other):
        return self.__class__\
                   .from_general(self.general & other.general,
                                 scanners=(self.scanners & other.scanners),
                                 clerks=(self.clerks & other.clerks),
                                 supplicants=(self.supplicants
                                              & other.supplicants))

    def __eq__(self, other):
        if not isinstance(other, ProcessProspectiveAffordanceSetABC):
            return False
        return self.clerks == other.clerks \
               and self.general == other.general \
               and self.scanners == other.scanners \
               and self.supplicants == other.supplicants

    __hash__ = None

    def __getattr__(self, name):
        return getattr(self._general, name)

    def __nonzero__(self):
        return bool(self.clerks and self.scanners and self.supplicants
                    and self.general)

    def __or__(self, other):
        return self.__class__\
                   .from_general(self.general | other.general,
                                 scanners=(self.scanners | other.scanners),
                                 clerks=(self.clerks | other.clerks),
                                 supplicants=(self.supplicants
                                              | other.supplicants))

    def __setattr__(self, name, value):
        if hasattr(self._general, name):
            setattr(self._general, name, value)
        else:
            object.__setattr__(self, name, value)

    @property
    def clerks(self):
        return self._clerks

    @classmethod
    @_abc.abstractmethod
    def from_general(cls, affordances, **kwargs):
        pass

    @_abc.abstractmethod
    def frozen(self):
        pass

    @property
    def general(self):
        return self._general

    @classmethod
    def min(cls):
        return cls.from_general(cls._general_class().min(), scanners=(),
                                clerks=(), supplicants=())

    @classmethod
    def max(cls):
        return cls.from_general(cls._general_class().max(), scanners='*',
                                clerks='*', supplicants='*')

    @property
    def scanners(self):
        return self._scanners

    @property
    def supplicants(self):
        return self._supplicants

    @_abc.abstractmethod
    def unfrozen(self):
        pass

    @_abc.abstractmethod
    def unfrozen_copy(self):
        pass

    @classmethod
    @_abc.abstractmethod
    def _clerks_class(cls):
        pass

    @classmethod
    def _frozen_class(self):
        return FrozenProcessProspectiveAffordanceSet

    @classmethod
    @_abc.abstractmethod
    def _general_class(cls):
        pass

    def _components_map(self, ordered=False):
        components = super(ProcessProspectiveAffordanceSetABC, self)\
                      ._components_map(ordered=ordered)
        components.update((('scanners', self.scanners),
                           ('clerks', self.clerks),
                           ('supplicants', self.supplicants)))
        return components

    @classmethod
    @_abc.abstractmethod
    def _scanners_class(cls):
        pass

    def _set_clerks(self, value):
        class_ = self._clerks_class()
        if isinstance(value, class_):
            self._clerks = value
        else:
            self._clerks = class_(value)

    def _set_general(self, value):
        class_ = self._general_class()
        if isinstance(value, class_):
            self._general = value
        else:
            self._general = class_(value)

    def _set_scanners(self, value):
        class_ = self._scanners_class()
        if isinstance(value, class_):
            self._scanners = value
        else:
            self._scanners = class_(value)

    def _set_supplicants(self, value):
        class_ = self._supplicants_class()
        if isinstance(value, class_):
            self._supplicants = value
        else:
            self._supplicants = class_(value)

    @classmethod
    @_abc.abstractmethod
    def _supplicants_class(cls):
        pass

    @classmethod
    def _unfrozen_class(self):
        return ProcessProspectiveAffordanceSet


class ProcessProspectiveAffordanceSet(ProcessProspectiveAffordanceSetABC):

    def __iand__(self, other):
        self._clerks &= other._clerks
        self._scanners &= other._scanners
        self._supplicants &= other._supplicants
        return self

    def __ior__(self, other):
        self._general |= other._general
        self._clerks |= other._clerks
        self._scanners |= other._scanners
        self._supplicants |= other._supplicants
        return self

    @ProcessProspectiveAffordanceSetABC.clerks.setter
    def clerks(self, value):
        self._set_clerks(value)

    @classmethod
    def from_general(cls, affordances, **kwargs):
        return cls(_general=affordances.unfrozen(), **kwargs)

    def frozen(self):
        return self._frozen_class().from_general(self.general,
                                                 scanners=self.scanners,
                                                 clerks=self.clerks,
                                                 supplicants=self.supplicants)

    @ProcessProspectiveAffordanceSetABC.general.setter
    def general(self, value):
        self._set_general(value)

    @ProcessProspectiveAffordanceSetABC.scanners.setter
    def scanners(self, value):
        self._set_scanners(value)

    @ProcessProspectiveAffordanceSetABC.supplicants.setter
    def supplicants(self, value):
        self._set_supplicants(value)

    def unfrozen(self):
        return self

    def unfrozen_copy(self):
        return self.copy()

    @classmethod
    def _clerks_class(cls):
        return _uset

    @classmethod
    def _general_class(cls):
        return _process_affordances.ProcessAffordanceSet

    @classmethod
    def _scanners_class(cls):
        return _uset

    @classmethod
    def _supplicants_class(cls):
        return _uset


class FrozenProcessProspectiveAffordanceSet\
       (ProcessProspectiveAffordanceSetABC):

    def __hash__(self):
        return hash(self.general) ^ hash(self.clerks) ^ hash(self.scanners) \
               ^ hash(self.supplicants)

    @classmethod
    def from_general(cls, affordances, **kwargs):
        return cls(_general=affordances.frozen(), **kwargs)

    def frozen(self):
        return self

    def unfrozen(self):
        return self._unfrozen_class()\
                   .from_general(self.general, scanners=self.scanners,
                                 clerks=self.clerks,
                                 supplicants=self.supplicants)

    def unfrozen_copy(self):
        return self.unfrozen()

    @classmethod
    def _clerks_class(cls):
        return _frozenuset

    @classmethod
    def _general_class(cls):
        return _process_affordances.FrozenProcessAffordanceSet

    @classmethod
    def _scanners_class(cls):
        return _frozenuset

    @classmethod
    def _supplicants_class(cls):
        return _frozenuset
