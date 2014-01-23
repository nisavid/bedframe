"""Spaces

An authentication space is a directory of resources with a defined set
of acceptable authentication realms, security provisions, and
algorithms.

"""

__copyright__ = "Copyright (C) 2014 Ivan D Vasin"
__docformat__ = "restructuredtext"

import re as _re

from spruce.collections import odict as _odict, uset as _uset
from spruce.lang import instance_of as _instance_of

from .. import _collections as _coll
from . import _affordances
from . import _handlers
from . import _provisions


class Space(_handlers.AlgorithmHandler, _handlers.ProvisionSetHandler,
            _handlers.RealmHandler):

    def __init__(self, realms='*', provisionsets=None, algorithms='*',
                 scanners='*', clerks='*', supplicants='*'):

        self.set_algorithms(algorithms)
        self._clerks = _uset(clerks)

        if provisionsets is None:
            provisionsets = \
                _provisions.FrozenProvisionSetSet('*')\
                 .union_product(_provisions.SECPROV_CLIENT_AUTH)\
                 .unfrozen()
        self.set_provisionsets(provisionsets)

        self.set_realms(realms)
        self._scanners = _uset(scanners)
        self._supplicants = _uset(supplicants)

    def __repr__(self):
        return '{}({})'\
                .format(self.__class__.__name__,
                        ', '.join('{}={!r}'.format(property_, value)
                                  for property_, value
                                  in self._init_args(ordered=True).items()))

    def __str__(self):
        properties_strs = []
        max_affordances = \
            _affordances.FrozenProcessProspectiveAffordanceSet.max()
        for property_, value in self._init_args(ordered=True).items():
            displayname = self._property_displayname(property_)
            if value == getattr(max_affordances, property_):
                str_ = 'any ' + displayname
            else:
                str_ = '{} {}'.format(displayname, value)
            properties_strs.append(str_)
        return '<authentication space with {}>'\
                .format(', '.join(properties_strs))

    @property
    def clerks(self):
        return self._clerks

    @property
    def scanners(self):
        return self._scanners

    def set_algorithms(self, value):
        self._algorithms_ = _uset(value)

    def set_provisionsets(self, value):
        self._provisionsets_ = _provisions.ProvisionSetSet(value)

    def set_realms(self, value):
        self._realms_ = _uset(value)

    @property
    def supplicants(self):
        return self._supplicants

    def _algorithms(self, upstream_affordances, downstream_affordances):
        return self._algorithms_

    def _init_args(self, ordered=False):
        class_ = _odict if ordered else dict
        max_affordances = _affordances.FrozenAffordanceSet.max()
        return class_((('realms',
                        self.realms(upstream_affordances=max_affordances)),
                       ('provisionsets',
                        self.provisionsets(upstream_affordances=
                                               max_affordances)),
                       ('algorithms',
                        self.algorithms(upstream_affordances=max_affordances)),
                       ('clerks', self.clerks),
                       ('scanners', self.scanners),
                       ('supplicants', self.supplicants),
                       ))

    @classmethod
    def _property_displayname(cls, name):
        displayname = name
        displayname = displayname.replace('_', ' ')
        displayname = _re.sub(r'(?<=\w)sets', ' sets', displayname)
        return displayname

    def _provisionsets(self, upstream_affordances, downstream_affordances):
        return self._provisionsets_

    def _realms(self, upstream_affordances, downstream_affordances):
        return self._realms_


class SpaceMap(_coll.HereditaryWebResourcePathMapping):
    """An authentication space map

    This is a mapping from authentication spaces' locations to
    specifications of their affordances and behavior.  In addition to the
    basic mutable mapping functionality, it also

      * accepts path patterns in the form of strings or regular
        expressions and

      * ensures that that its items have valid types and values.

    :param mapping_or_items:
        A mapping or item sequence of initial items.
    :type mapping_or_items: ~{~:obj:`re`: :class:`Space`}

    """
    def __init__(self, *args, **kwargs):
        super(SpaceMap, self)\
         .__init__(*args,
                   valuetype=_instance_of(Space, 'authentication space'),
                   value_converter=False, **kwargs)
