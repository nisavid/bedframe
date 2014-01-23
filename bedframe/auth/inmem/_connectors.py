"""Connectors"""

__copyright__ = "Copyright (C) 2014 Ivan D Vasin"
__docformat__ = "restructuredtext"

from spruce.collections import frozenset as _frozenset

from .. import _connectors
from .. import _info
from .. import _provisions


class InMemoryPlainSupplicant(_connectors.Supplicant):

    """
    An authentication supplicant that uses an in-memory mapping of users to
    passwords

    :param users_passwords:
        The mapping of user names to passwords.
    :type users_passwords: {:obj:`str`: :obj:`str`}

    """

    def __init__(self, users_passwords, realm, **kwargs):
        super(InMemoryPlainSupplicant, self).__init__(**kwargs)
        self._realm = realm
        self._users_passwords = users_passwords

    def _inputs(self, upstream_affordances, downstream_affordances):
        return (self._INPUT,)

    def _outputs(self, upstream_affordances, downstream_affordances):
        return (self._OUTPUT,)

    def _process_tokens(self, input, affordances):
        return self._verify_creds(**input)

    def _provisionsets(self, upstream_affordances, downstream_affordances):
        return (self._PROVISIONS,)

    def _realms(self, upstream_affordances, downstream_affordances):
        return (self._realm,)

    def _verify_creds(self, user, password, **other_tokens):

        try:
            actual_password = self._users_passwords[user]
        except KeyError:
            accepted = False
        else:
            accepted = password == actual_password

        tokens = dict(other_tokens)
        tokens['user'] = user
        return _info.RequestAuthInfo(tokens=tokens,
                                     provisions=self._PROVISIONS,
                                     accepted=accepted)

    _INPUT = _frozenset(('user', 'password'))

    _OUTPUT = _frozenset(('user', 'accepted'))

    _PROVISIONS = _provisions.SECPROV_CLIENT_AUTH


class InMemoryGetPasswordSupplicant(_connectors.Supplicant):

    """
    An authentication supplicant that uses an in-memory mapping of users to
    passwords

    :param users_passwords:
        The mapping of user names to passwords.
    :type users_passwords: {:obj:`str`: :obj:`str`}

    """

    def __init__(self, users_passwords, realm, **kwargs):
        super(InMemoryGetPasswordSupplicant, self).__init__(**kwargs)
        self._realm = realm
        self._users_passwords = users_passwords

    def _fetch_password(self, user, **other_tokens):

        try:
            password = self._users_passwords[user]
        except KeyError:
            password = None

        tokens = dict(other_tokens)
        tokens['user'] = user
        tokens['actual_password'] = password
        return _info.RequestAuthInfo(tokens=tokens,
                                     provisions=self._PROVISIONS)

    def _inputs(self, upstream_affordances, downstream_affordances):
        return (self._INPUT,)

    def _outputs(self, upstream_affordances, downstream_affordances):
        return (self._OUTPUT,)

    def _process_tokens(self, input, affordances):
        return self._fetch_password(**input)

    def _provisionsets(self, upstream_affordances, downstream_affordances):
        return (self._PROVISIONS,)

    def _realms(self, upstream_affordances, downstream_affordances):
        return (self._realm,)

    _INPUT = _frozenset(('user',))

    _OUTPUT = _frozenset(('user', 'actual_password'))

    _PROVISIONS = _provisions.SECPROV_CLIENT_AUTH
