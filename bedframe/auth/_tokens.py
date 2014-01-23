"""Tokens"""

__copyright__ = "Copyright (C) 2014 Ivan D Vasin"
__docformat__ = "restructuredtext"

import abc as _abc
from collections import Mapping as _Mapping, MutableMapping as _MutableMapping
from itertools import chain as _chain, combinations as _combinations

from spruce.collections \
    import frozendict as _frozendict, frozenset as _frozenset


def tokens_combinations(tokens_or_names):
    names = tokens_names(tokens_or_names)
    return _chain(*(_combinations(names, ntokens)
                    for ntokens in range(len(names) + 1)))


def tokens_names(tokens_or_names):
    try:
        return _frozenset(tokens_or_names)
    except TypeError:
        raise TypeError('invalid tokens type {!r}; expecting a mapping or'
                         ' other iterable'
                         .format(tokens_or_names.__class__))


class TokenMapABC(object):

    """Authentication tokens"""

    __metaclass__ = _abc.ABCMeta

    def __init__(self, tokens=None):
        self.__dict__['_tokens'] = self._tokens_class()(tokens or ())

    def __getattr__(self, name):
        try:
            return self[name]
        except KeyError as exc:
            raise AttributeError(exc.args[0])

    def __getitem__(self, name):
        return self._tokens[name]

    __hash__ = None

    def __iter__(self):
        return iter(self._tokens)

    def __len__(self):
        return len(self._tokens)

    def __repr__(self):
        return '{}({!r})'.format(self.__class__.__name__, self._tokens)

    def __str__(self):
        return str(self._tokens)

    def copy(self):
        return self.__class__(self._tokens)

    @_abc.abstractmethod
    def frozen(self):
        pass

    @_abc.abstractmethod
    def unfrozen(self):
        pass

    @_abc.abstractmethod
    def unfrozen_copy(self):
        pass

    @classmethod
    def _frozen_class(cls):
        return FrozenTokenMap

    @classmethod
    def _unfrozen_class(cls):
        return TokenMap

    @classmethod
    @_abc.abstractmethod
    def _tokens_class(cls):
        pass


class FrozenTokenMap(TokenMapABC, _Mapping):

    """Immutable authentication tokens"""

    def __hash__(self):
        return hash(self._tokens)

    def __str__(self):
        return '=' + super(FrozenTokenMap, self).__str__()

    def frozen(self):
        return self

    def unfrozen(self):
        return self._unfrozen_class()(self._tokens)

    def unfrozen_copy(self):
        return self.unfrozen()

    @classmethod
    def _tokens_class(cls):
        return _frozendict


class TokenMap(TokenMapABC, _MutableMapping):

    """Authentication tokens"""

    def __delattr__(self, name):
        try:
            del self[name]
        except KeyError as exc:
            raise AttributeError(exc.args[0])

    def __delitem__(self, name):
        del self._tokens[name]

    def __setattr__(self, name, value):
        try:
            self[name] = value
        except KeyError as exc:
            raise AttributeError(exc.args[0])

    def __setitem__(self, name, value):
        self._tokens[name] = value

    def frozen(self):
        return self._frozen_class()(self._tokens)

    def unfrozen(self):
        return self

    def unfrozen_copy(self):
        return self.copy()

    @classmethod
    def _tokens_class(cls):
        return dict
