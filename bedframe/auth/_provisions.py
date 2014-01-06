"""Security provisions."""

__copyright__ = "Copyright (C) 2014 Ivan D Vasin"
__docformat__ = "restructuredtext"

import abc as _abc
from functools import reduce as _reduce
from itertools import chain as _chain, combinations as _combinations
from operator import or_ as _or

from spruce.collections \
    import frozenusetset as _frozenusetset, usetset as _usetset
from spruce.lang import namedflagset_classes as _namedflagset_classes


def provisionsets_combinations(provisionsets, choose0=True):

    """
    The authentication security provision sets that are yielded by
    combinations of given sets.

    :param provisionsets:
        A set of security provision sets.
    :type provisionsets: ~[:class:`ProvisionSetABC`]

    :param bool choose0:
        Whether to include the empty choice.  If true, then the empty set of
        security provisions is always included in the result.  Otherwise, it
        is included only if *provisionsets* contains it.

    :rtype: :class:`ProvisionSetABC`

    """

    if choose0:
        yield iter(provisionsets).next().__class__()

    for combination \
            in _chain(*(_combinations(provisionsets, nchoices)
                        for nchoices in range(1, len(provisionsets) + 1))):
        yield _reduce(_or, combination)


_ProvisionSet_doc_body = \
    """
    An :class:`!ProvisionSet` object is a set of security properties
    that is could be provided by an authentication mechanism.

    Example usage::

        auth_provisions = \\
            ProvisionSet(SECPROV_SERVER_NONCE
                         & SECPROV_SERVER_NONCE_USE_COUNT)

        if SECPROV_SERVER_NONCE not in auth_provisions:
            print 'vulnerability to a simple replay attack'
        if SECPROV_SERVER_NONCE_USE_COUNT not in auth_provisions:
            print 'vulnerability to a simple online replay attack'
        if SECPROV_CLIENT_NONCE not in auth_provisions:
            print 'vulnerability to a chosen plaintext attack'
        if SECPROV_REQUEST_ENTITY_INTEGRITY not in auth_provisions:
            print 'vulnerability to a mangled request entity'

    .. seealso::
        :class:`spruce.lang.NamedFlagSet \
                <spruce.lang._datatypes._misc.NamedFlagSet>`

    """
_ProvisionSet_doc = \
    """Authentication security provisions.
    """ \
    + _ProvisionSet_doc_body
_FrozenProvisionSet_doc = \
    """Immutable authentication security provisions.
    """ \
    + _ProvisionSet_doc_body
ProvisionSetABC, ProvisionSet, FrozenProvisionSet = \
    _namedflagset_classes('ProvisionSet', doc=_ProvisionSet_doc,
                          frozendoc=_ProvisionSet_doc)


class ProvisionSetSetABC(object):

    __metaclass__ = _abc.ABCMeta

    def __repr__(self):
        if not self:
            items_repr = ''
        elif self == self._universe():
            items_repr = '*'
        else:
            ubi_provisionsets, nonubi_provisionsets = \
                self._condensed_repr_provisionsets()
            if ubi_provisionsets:
                ubi_provisionsets = sorted(ubi_provisionsets)
                ubi_provisionsets_repr = \
                    ' | '.join(repr(provisions)
                               for provisions in ubi_provisionsets)
                if nonubi_provisionsets == '*':
                    items_repr = '{}*'.format(ubi_provisionsets_repr)
                elif nonubi_provisionsets in ((), (FrozenProvisionSet(),)):
                    items_repr = ubi_provisionsets_repr
                else:
                    nonubi_provisionsets = sorted(nonubi_provisionsets)
                    items_repr = \
                        '(({}) | {{p}} for p in {{{}}})'\
                         .format(ubi_provisionsets_repr,
                                 ', '.join(repr(provisions)
                                           for provisions
                                           in nonubi_provisionsets))
            else:
                items_repr = repr(self._items)
        return '{}({})'.format(self.__class__.__name__, items_repr)

    def __str__(self):
        if not self:
            return '{}'
        elif self == self._universe():
            return '*'
        else:
            ubi_provisionsets, nonubi_provisionsets = \
                self._condensed_repr_provisionsets()
            if ubi_provisionsets:
                ubi_provisionsets = sorted(ubi_provisionsets)
                ubi_provisionsets_str = \
                    ', '.join(str(provisions)
                              for provisions in ubi_provisionsets)
                if nonubi_provisionsets == '*':
                    items_str = 'any with ' + ubi_provisionsets_str
                elif nonubi_provisionsets == (FrozenProvisionSet(),):
                    items_str = ubi_provisionsets_str
                else:
                    nonubi_provisionsets = sorted(nonubi_provisionsets)
                    nonubi_provisionsets_str = \
                        ' or '.join(str(provisions)
                                    for provisions in nonubi_provisionsets)

                    if ubi_provisionsets:
                        if nonubi_provisionsets:
                            if len(ubi_provisionsets) > 1:
                                ubi_provisionsets_str = \
                                    '({})'.format(ubi_provisionsets_str)
                            if len(nonubi_provisionsets) > 1:
                                nonubi_provisionsets_str = \
                                    'any of ({})'\
                                     .format(nonubi_provisionsets_str)

                            items_str = \
                                '{} with {}'.format(ubi_provisionsets_str,
                                                    nonubi_provisionsets_str)
                        else:
                            items_str = ubi_provisionsets_str
                    elif nonubi_provisionsets:
                        items_str = nonubi_provisionsets_str
                    else:
                        items_str = ''
                return '{{{}}}'.format(items_str)
            elif nonubi_provisionsets:
                return '{{{}}}'.format(' or '.join(str(provisions)
                                                   for provisions
                                                   in nonubi_provisionsets))
            else:
                return str(self._items)

    def all_contain(self, provisions):
        return all(provisions <= self_provisions for self_provisions in self)

    def any_contain(self, provisions):
        return any(provisions <= self_provisions for self_provisions in self)

    def _condensed_repr_provisionsets(self):

        if not self._items:
            return set(), set()

        ubi_provisionsets = set()
        ubi_mask = 0
        items = [ProvisionSet(item) for item in self._items]
        for provisions in reversed(sorted(ProvisionSet.valid_flags(),
                                          key=int)):
            if all(provisions <= item for item in items):
                ubi_provisionsets.add(provisions)
                ubi_mask |= int(provisions)

                for item in items:
                    item &= ~int(provisions)

        nonubi_provisionsets = set()
        for item in set(provisionsets_combinations
                            (ProvisionSet.valid_flags())):
            item_ = FrozenProvisionSet(item & ~ubi_mask)
            if item_ in items:
                nonubi_provisionsets.add(item_)

        if len(nonubi_provisionsets) == 1 \
               and not iter(nonubi_provisionsets).next():
            nonubi_provisionsets = ()
        elif nonubi_provisionsets \
               == set(set(provisionsets_combinations
                           (ProvisionSet.valid_flags()))
                      - ubi_provisionsets):
            nonubi_provisionsets = '*'

        return ubi_provisionsets, nonubi_provisionsets

    @classmethod
    @_abc.abstractmethod
    def _item_class(cls):
        pass

    @classmethod
    def _universe(cls):
        if cls._universe_ is None:
            cls._universe_ = \
                cls(provisionsets_combinations
                     (ProvisionSet.valid_flags()))\
                 ._items
        return cls._universe_

    _universe_ = None


class ProvisionSetSet(ProvisionSetSetABC, _usetset):
    """A set of provision sets.

    .. seealso::
        :class:`spruce.collections.usetset \
                <spruce.collections._sets._universalizable.usetset>`

    """
    @classmethod
    def _item_class(cls):
        return FrozenProvisionSet


class FrozenProvisionSetSet(ProvisionSetSetABC, _frozenusetset):
    """An immutable set of provision sets.

    .. seealso::
        :class:`spruce.collections.frozenusetset \
                <spruce.collections._sets._universalizable.frozenusetset>`

    """
    @classmethod
    def _item_class(cls):
        return FrozenProvisionSet


SECPROV_CLIENT_AUTH = ProvisionSet.register_flag('SECPROV_CLIENT_AUTH',
                                                 'client authentication')
"""Authentication verifies the identity of the client."""


SECPROV_SERVER_AUTH = ProvisionSet.register_flag('SECPROV_SERVER_AUTH',
                                                 'server authentication')
"""Authentication verifies the identity of the server."""


SECPROV_CLIENT_ENCRYPTED_SECRET = \
    ProvisionSet.register_flag('SECPROV_CLIENT_ENCRYPTED_SECRET',
                               'encrypted client secret')
"""Client authentication uses an encrypted secret.

The client never sends its authentication secret in cleartext or in an
insecure coding.  It either sends the secret in an encrypted form or it
sends some derived certificate of its identity.

"""


SECPROV_CLIENT_NEVER_SENDS_SECRET = \
    ProvisionSet.register_flag('SECPROV_CLIENT_NEVER_SENDS_SECRET',
                               'client never sends secret',
                               implied=SECPROV_CLIENT_ENCRYPTED_SECRET)
"""The client never sends its secret in any form.

The client sends a verifiable claim of its authentication secret rather
than sending the secret itself in any form.

.. note::
    This implies :const:`SECPROV_CLIENT_ENCRYPTED_SECRET`.

"""


SECPROV_SERVER_NONCE = ProvisionSet.register_flag('SECPROV_SERVER_NONCE',
                                                  'server-side nonce')
"""Authentication uses a server-side nonce.

The server challenges the client with a nonce value and requires it in
the client's response.

When serving a response to a request with a particular server-side
nonce, the server verifies that it is valid for the request.  This flag
does not identify how such validity is determined.

"""


SECPROV_SERVER_NONCE_PER_RESOURCE = \
    ProvisionSet.register_flag('SECPROV_SERVER_NONCE_PER_RESOURCE',
                               'server-side nonce per resource',
                               implied=SECPROV_SERVER_NONCE)
"""Authentication uses a unique server-side nonce for each resource.

.. note::
    This implies :const:`SECPROV_SERVER_NONCE`.

"""


SECPROV_SERVER_NONCE_PER_REQUEST = \
    ProvisionSet\
     .register_flag('SECPROV_SERVER_NONCE_PER_REQUEST',
                    'server-side nonce per request',
                    implied=(SECPROV_SERVER_NONCE
                             | SECPROV_SERVER_NONCE_PER_RESOURCE))
"""Authentication uses a unique server-side nonce for each request.

The server does not allow a previously used server-side nonce to be
reused, even if the client's authentication token is otherwise valid.
In other words, each server-side nonce expires after its first use.

As a consequence, every request involves a challenge-response handshake.

.. note::
    This implies :const:`SECPROV_SERVER_NONCE` and
    :const:`SECPROV_SERVER_NONCE_PER_RESOURCE`.

"""


SECPROV_SERVER_NONCE_USE_COUNT = \
    ProvisionSet.register_flag('SECPROV_SERVER_NONCE_USE_COUNT',
                               'server-side nonce use count',
                               implied=SECPROV_SERVER_NONCE)
"""Authentication verifies the server-side nonce use count.

The server maintains a record of how many times each nonce has been
used and requires each subsequent use to identify itself with an
incremented count.

When serving a response to a request with a particular nonce use count,
the server includes the same count.  The client should verify that the
counts match.

.. note::
    This implies :const:`SECPROV_SERVER_NONCE`.

"""


SECPROV_CLIENT_NONCE = ProvisionSet.register_flag('SECPROV_CLIENT_NONCE',
                                                  'client-side nonce')
"""Authentication uses a client-side nonce.

The client challenges the server with a nonce value and requires it in
the server's response.

When serving a response to a request with a particular client-side
nonce, the server includes the same nonce.  The client should verify
that the nonce is valid.

"""


SECPROV_REQUEST_ENTITY_INTEGRITY = \
    ProvisionSet.register_flag('SECPROV_REQUEST_ENTITY_INTEGRITY',
                               'request entity integrity')
"""Authentication verifies the integrity of each request entity.

The client provides an authentication token that includes information
that the server uses to verify the integrity of any entity that is
included in the request.

"""
