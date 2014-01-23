"""Authentication information"""

__copyright__ = "Copyright (C) 2014 Ivan D Vasin"
__docformat__ = "restructuredtext"

from . import _provisions
from . import _tokens


class RequestAuthInfo(object):

    """Request authentication information

    :param tokens:
        The authentication tokens.
    :type tokens: :class:`bedframe.auth._tokens.TokenMap` or null

    :param str realm:
        The authentication realm.
    :type realm: :obj:`str` or null

    :param provisions:
        Authentication security provisions.
    :type provisions:
        ~\ :class:`~bedframe.auth._provisions.ProvisionSet`

    :raise TypeError:
        Raised if non-null *provisions* are given that are of a type that
        cannot be converted to an
        :class:`~bedframe.auth._provisions.ProvisionSet`.

    :raise ValueError:
        Raised if non-null *provisions* are given that cannot be converted
        to an :class:`~bedframe.auth._provisions.ProvisionSet`.

    """

    def __init__(self, tokens=None, space=None, realm=None, provisions=None,
                 algorithm=None, clerk=None, scanner=None, supplicant=None,
                 accepted=None):
        self._accepted = accepted
        self.algorithm = algorithm
        self.clerk = clerk
        self.provisions = provisions
        self.realm = realm
        self.scanner = scanner
        self.space = space
        self.supplicant = supplicant
        self.tokens = tokens or {}

    def __repr__(self):
        return self.repr(insecure=False)

    def accept(self):
        self._accepted = True

    @property
    def accepted(self):
        """
        Whether the authentication tokens were accepted by an authenticator

        :type: :obj:`bool` or null

        """
        return self._accepted

    @property
    def algorithm(self):
        """The authentication algorithm

        :type: :class:`~bedframe.auth._algorithms.Algorithm`

        """
        return self._algorithm

    @algorithm.setter
    def algorithm(self, value):
        self._algorithm = value

    @property
    def clerk(self):
        """The authentication clerk

        :type: :class:`~bedframe.auth._connectors.Clerk`

        """
        return self._clerk

    @clerk.setter
    def clerk(self, value):
        self._clerk = value

    @property
    def provisions(self):
        """The authentication security provisions

        :type: :class:`~bedframe.auth._provisions.ProvisionSet`

        """
        return self._provisions

    @provisions.setter
    def provisions(self, value):
        self._provisions = _provisions.ProvisionSet(value)

    @property
    def realm(self):
        """The authentication realm

        :type: :obj:`str` or null

        """
        return self._realm

    @realm.setter
    def realm(self, value):
        self._realm = value

    def reject(self):
        self._accepted = False

    def repr(self, insecure=False):
        kwargs_items = []
        if insecure:
            kwargs_items.append(('tokens', self.tokens))
        kwargs_items += [('space', self.space),
                         ('realm', self.realm),
                         ('provisions', self.provisions),
                         ('algorithm', self.algorithm),
                         ('clerk', self.clerk),
                         ('scanner', self.scanner),
                         ('supplicant', self.supplicant),
                         ('accepted', self.accepted),
                         ]
        repr_kwargs_items = [(name, value) for name, value in kwargs_items
                             if value is not None]
        return '{}({})'.format(self.__class__.__name__,
                               ', '.join('{}={!r}'.format(name, value)
                                         for name, value in repr_kwargs_items))

    @property
    def scanner(self):
        """The authentication scanner

        :type: :class:`~bedframe.auth._connectors.Scanner`

        """
        return self._scanner

    @scanner.setter
    def scanner(self, value):
        self._scanner = value

    @property
    def space(self):
        """The authentication space

        :type: :class:`~bedframe.auth._spaces.Space` or null

        """
        return self._space

    @space.setter
    def space(self, value):
        self._space = value

    @property
    def supplicant(self):
        """The authentication supplicant

        :type: :class:`~bedframe.auth._connectors.Supplicant`

        """
        return self._supplicant

    @supplicant.setter
    def supplicant(self, value):
        self._supplicant = value

    @property
    def tokens(self):
        """The authentication tokens

        :type: :class:`~bedframe.auth._tokens.TokenMap` or null

        """
        return self._tokens

    @tokens.setter
    def tokens(self, value):
        self._tokens = _tokens.TokenMap(value)

    @property
    def user(self):
        return self.tokens.user

    @property
    def verified(self):
        return self._accepted is not None


class NullRequestAuthInfo(RequestAuthInfo):

    """Null request authentication information

    This represents authentication information about a request that does not
    use authentication.

    """

    @property
    def user(self):
        """The authenticated username

        :type: null

        """
        return None

    @user.setter
    def user(self, value):
        raise TypeError('cannot set user in null request authentication'
                         ' information')
