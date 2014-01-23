"""Connectors"""

__copyright__ = "Copyright (C) 2014 Ivan D Vasin"
__docformat__ = "restructuredtext"

import abc as _abc
import hashlib as _hashlib
import json as _json
import sys as _sys
import threading as _threading
from functools import wraps as _wraps

import ldap as _ldap
try:
    import memcache as _memcache
except ImportError:
    _memcache = None
from spruce.collections import frozenset as _frozenset

from .. import _connectors
from .. import _info
from .. import _provisions

_LDAP_CREDENTIALS_CACHE_TIME = 60.0 * 60.0 * 2.0  # 2 hours


def _with_lock(lock):
    """

    .. note:: **TODO:**
        generalize and move

    """
    def with_lock(f):
        @_wraps(f)
        def wrapper(*args, **kwargs):
            with lock:
                return f(*args, **kwargs)
        return wrapper
    return with_lock


class LdapSupplicant(_connectors.Supplicant):

    """An authentication supplicant that uses LDAP

    This supplicant treats authentication realms as follows:

      * If the server port is the default LDAP port, then the realm is the
        server domain name.

      * If the server port is not the default LDAP port, then the realm is
        :samp:`{server}:{port}`, where *server* is the server address and
        *port* is the server port.

    If the server is specified prior to authenticating (via the *server*
    argument or the :attr:`server` property), then this supplicant only
    supports the realm that is determined as above.  If the server address
    is left unspecified, then this supplicant supports all realms, and the
    address is determined from the realm specified in the affordances passed
    to :meth:`process_tokens`.

    If the DN components are specified prior to authenticating (via the
    *basedn* or *username_attr* arguments or the :attr:`basedn` or
    :attr:`username_attr` properties), then those are used.  Otherwise, they
    must be specified in the input tokens passed to :meth:`process_tokens`.

    :param server:
        The LDAP server address.
    :type server: :obj:`str` or null

    :param port:
        The LDAP server port.
    :type port: :obj:`int` or null

    :param basedn:
        The DN of the users tree.  It is assumed that users are located one
        level lower in the tree.
    :type basedn: :obj:`str` or null

    :param username_attr:
        The attribute that specifies the username in a user's DN.
    :type username_attr: :obj:`str` or null

    :param bool use_tls:
        Whether to use TLS for the connection to the LDAP server.

    """

    __metaclass__ = _abc.ABCMeta

    def __init__(self, server, basedn=None, username_attr='uid', use_tls=False,
                 realm=None, **kwargs):
        super(LdapSupplicant, self).__init__(**kwargs)
        self._basedn = basedn
        self._realm = realm
        self._server = server
        self._use_tls = use_tls
        self._username_attr = username_attr

    @property
    def basedn(self):
        return self._basedn

    @basedn.setter
    def basedn(self, value):
        self._basedn = value

    @property
    def realm(self):
        if self._realm is not None:
            return self._realm
        else:
            return self.server

    @realm.setter
    def realm(self, value):
        self._realm = value

    @property
    def server(self):
        return self._server

    @server.setter
    def server(self, value):
        self._server = value

    @property
    def use_tls(self):
        return self._use_tls

    @use_tls.setter
    def use_tls(self, value):
        self._use_tls = value

    def user_dn(self, user, basedn=None, username_attr=None):
        return '{}={},{}'.format(username_attr or self.username_attr, user,
                                 basedn or self.basedn)

    @property
    def username_attr(self):
        return self._username_attr

    @username_attr.setter
    def username_attr(self, value):
        self._username_attr = value

    def _handle_ldap_bind_exc(self, exc, traceback, server, bind_dn,
                              bind_password):
        message = 'cannot bind to LDAP server {} as user {}: {}'\
                   .format(server, bind_dn, str(exc))
        raise IOError(message), None, traceback

    def _handle_ldap_conn_exc(self, exc, traceback, server):
        message = 'cannot connect to LDAP server {}: {}'.format(server,
                                                                str(exc))
        raise IOError(message), None, traceback

    def _init_args(self, ordered=False):
        args = super(LdapSupplicant, self)._init_args(ordered=ordered)
        args.update((('server', self.server),
                     ('basedn', self.basedn),
                     ('username_attr', self.username_attr),
                     ('use_tls', self.use_tls),
                     ('realm', self.realm),
                     ))
        return args

    _ldap_library_lock = _threading.RLock()

    def _normalized_input(self, input, affordances):
        tokens = input.copy()
        if 'ldap_server' not in tokens:
            if affordances.realms.isfinite:
                realm = iter(affordances.realms).next()
                if realm is not None:
                    if realm == self.realm:
                        tokens.ldap_server = self.server
                    else:
                        tokens.ldap_server = realm
            if 'ldap_server' not in tokens:
                if self.server:
                    tokens.ldap_server = self.server
                else:
                    assert False
        return tokens

    def _realms(self, upstream_affordances, downstream_affordances):
        return (self.realm,)


class LdapSimpleSupplicant(LdapSupplicant):

    """An authentication supplicant that uses LDAP Simple BIND

    .. seealso:: :class:`LdapSupplicant`

    """

    def __init__(self, *args, **kwargs):
        super(LdapSimpleSupplicant, self).__init__(*args, **kwargs)
        if _memcache:
            # XXX - TODO - FIXME - subclass/mixin the memcache logic,
            #                      look for memcache server in settings
            self._memcache = _memcache.Client(['localhost:11211'])
        else:
            self._memcache = None

    _OUTPUT = _frozenset(('user', 'accepted', 'password', 'ldap_server',
                          'ldap_basedn', 'ldap_username_attr', 'ldap_user_dn'))

    _PROVISIONS = _provisions.SECPROV_CLIENT_AUTH

    def _inputs(self, upstream_affordances, downstream_affordances):

        tokens = {'user', 'password'}
        if self.basedn is None:
            tokens.add('ldap_basedn')
        if self.username_attr is None:
            tokens.add('ldap_username_attr')

        if self.server is None and not upstream_affordances.realms.isfinite:
            tokens_with_server = tokens.copy()
            tokens_with_server.add('ldap_server')
            tokens_with_realm = tokens.copy()
            tokens_with_realm.add('realm')
            return (tokens_with_server, tokens_with_realm)
        else:
            return (tokens,)

    def _normalized_input(self, input, affordances):
        tokens = super(LdapSimpleSupplicant, self)\
                  ._normalized_input(input, affordances=affordances)
        if 'ldap_basedn' not in tokens:
            tokens.ldap_basedn = self.basedn
        if 'ldap_username_attr' not in tokens:
            tokens.ldap_username_attr = self.username_attr
        return tokens

    def _outputs(self, upstream_affordances, downstream_affordances):
        return (self._OUTPUT,)

    def _process_tokens(self, input, affordances):
        return self._verify_creds(**self._normalized_input(input,
                                                           affordances=
                                                               affordances))

    def _provisionsets(self, upstream_affordances, downstream_affordances):
        return (self._PROVISIONS,)

    @_with_lock(LdapSupplicant._ldap_library_lock)
    def _verify_creds(self, user, password, ldap_server, ldap_user_dn=None,
                      ldap_username_attr=None, ldap_basedn=None,
                      **other_tokens):

        if not ldap_user_dn:
            ldap_user_dn = self.user_dn(user, basedn=ldap_basedn,
                                        username_attr=ldap_username_attr)

        def memcache_key(ldap_user_dn, password):
            raw_key = (str(ldap_user_dn), password)
            return _hashlib.md5(_json.dumps(raw_key)).hexdigest()

        def handle_conn_exc(exc, traceback):
            if ldap_server == self.server:
                self._handle_ldap_conn_exc(exc, traceback, server=ldap_server)
            else:
                return result(accepted=False)

        def result(accepted, update_memcache=True):
            if self._memcache and update_memcache:
                key = memcache_key(ldap_user_dn, password)
                self._memcache.set(key, accepted, _LDAP_CREDENTIALS_CACHE_TIME)
            tokens = dict(other_tokens)
            tokens['user'] = user
            tokens['accepted'] = _json.dumps(accepted)
            tokens['password'] = password
            tokens['ldap_server'] = ldap_server
            tokens['ldap_basedn'] = ldap_basedn
            tokens['ldap_username_attr'] = ldap_username_attr
            tokens['ldap_user_dn'] = ldap_user_dn
            return _info.RequestAuthInfo(tokens=tokens,
                                         provisions=self._PROVISIONS,
                                         accepted=accepted)

        # short circuit if there's a cache hit
        if self._memcache:
            key = memcache_key(ldap_user_dn, password)
            accepted = self._memcache.get(key)
            if accepted is not None:
                # only update memcache when we've actually authenticated
                return result(accepted=bool(accepted), update_memcache=False)

        try:
            ldap = _ldap.initialize(ldap_server)
        except _ldap.LDAPError as exc:
            return handle_conn_exc(exc, _sys.exc_info()[2])
        else:
            # FIXME: make values configurable
            ldap.set_option(_ldap.OPT_NETWORK_TIMEOUT, 6.)
            ldap.timeout = 6.

            try:
                ldap.simple_bind_s(ldap_user_dn, password)
            except _ldap.SERVER_DOWN as exc:
                return handle_conn_exc(exc, _sys.exc_info()[2])
            except (_ldap.INVALID_CREDENTIALS, _ldap.INVALID_DN_SYNTAX,
                    _ldap.UNWILLING_TO_PERFORM):
                accepted = False
            else:
                accepted = True
            finally:
                ldap.unbind_ext_s()

        return result(accepted=accepted)


class LdapGetPasswordSupplicant(LdapSupplicant):

    """
    An authentication supplicant that retrieves the user's password from an
    LDAP directory

    """

    def __init__(self, server, bind_dn=None, bind_password=None,
                 password_attr='userPassword', **kwargs):
        super(LdapGetPasswordSupplicant, self).__init__(server, **kwargs)
        self._bind_dn = bind_dn
        self._bind_password = bind_password
        self._password_attr = password_attr

    @property
    def bind_dn(self):
        return self._bind_dn

    @bind_dn.setter
    def bind_dn(self, value):
        self._bind_dn = value

    @property
    def bind_password(self):
        return self._bind_password

    @bind_password.setter
    def bind_password(self, value):
        self._bind_password = value

    @property
    def password_attr(self):
        return self._password_attr

    @password_attr.setter
    def password_attr(self, value):
        self._password_attr = value

    _OUTPUT = _frozenset(('user',
                          'actual_password',
                          'ldap_server',
                          'ldap_bind_dn',
                          'ldap_bind_password',
                          'ldap_basedn',
                          'ldap_username_attr',
                          'ldap_password_attr',
                          'ldap_user_dn',
                          ))

    _PROVISIONS = _provisions.SECPROV_CLIENT_AUTH

    @_with_lock(LdapSupplicant._ldap_library_lock)
    def _fetch_password(self,
                        user,
                        ldap_server,
                        ldap_bind_dn,
                        ldap_bind_password,
                        ldap_password_attr,
                        ldap_user_dn=None,
                        ldap_basedn=None,
                        ldap_username_attr=None,
                        **other_tokens):

        if not ldap_user_dn:
            ldap_user_dn = self.user_dn(user, basedn=ldap_basedn,
                                        username_attr=ldap_username_attr)

        def handle_conn_exc(exc, traceback):
            if ldap_server == self.server:
                self._handle_ldap_conn_exc(exc, traceback, server=ldap_server)
            else:
                return result(password=None)

        def handle_bind_exc(exc, traceback):
            if ldap_server == self.server \
                   and ldap_bind_dn == self.bind_dn \
                   and ldap_bind_password == self.bind_password:
                self._handle_ldap_bind_exc(exc, traceback, server=ldap_server,
                                           bind_dn=ldap_bind_dn,
                                           bind_password=ldap_bind_password)
            else:
                return result(password=None)

        def result(password):
            tokens = dict(other_tokens)
            tokens['user'] = user
            tokens['actual_password'] = password
            tokens['ldap_server'] = ldap_server
            tokens['ldap_bind_dn'] = ldap_basedn
            tokens['ldap_bind_password'] = ldap_bind_password
            tokens['ldap_basedn'] = ldap_basedn
            tokens['ldap_username_attr'] = ldap_username_attr
            tokens['ldap_user_dn'] = ldap_user_dn
            return _info.RequestAuthInfo(tokens=tokens,
                                         provisions=self._PROVISIONS)

        try:
            ldap = _ldap.initialize(ldap_server)
        except _ldap.LDAPError as exc:
            return handle_conn_exc(exc, _sys.exc_info()[2])

        else:
            # FIXME: make values configurable
            ldap.set_option(_ldap.OPT_NETWORK_TIMEOUT, 6.)
            ldap.timeout = 6.

            try:
                ldap.simple_bind_s(ldap_bind_dn, ldap_bind_password)
            except _ldap.SERVER_DOWN as exc:
                return handle_conn_exc(exc, _sys.exc_info()[2])
            except (_ldap.INVALID_CREDENTIALS, _ldap.INVALID_DN_SYNTAX,
                    _ldap.UNWILLING_TO_PERFORM) as exc:
                return handle_bind_exc(exc, _sys.exc_info()[2])
            else:
                try:
                    search_results = ldap.search_s(ldap_user_dn,
                                                   _ldap.SCOPE_BASE)
                except _ldap.NO_SUCH_OBJECT:
                    password = None
                else:
                    try:
                        password = search_results[0][1][ldap_password_attr][0]
                    except (IndexError, KeyError):
                        password = None

                return result(password=password)

            finally:
                ldap.unbind_ext_s()

    def _inputs(self, upstream_affordances, downstream_affordances):

        tokens = {'user'}
        if self.bind_dn is None:
            tokens.add('ldap_bind_dn')
        if self.bind_password is None:
            tokens.add('ldap_bind_password')
        if self.basedn is None:
            tokens.add('ldap_basedn')
        if self.username_attr is None:
            tokens.add('ldap_username_attr')
        if self.password_attr is None:
            tokens.add('ldap_password_attr')

        if self.server is None and not upstream_affordances.realms.isfinite:
            tokens_with_server = tokens.copy()
            tokens_with_server.add('ldap_server')
            tokens_with_realm = tokens.copy()
            tokens_with_realm.add('realm')
            return (tokens_with_server, tokens_with_realm)
        else:
            return (tokens,)

    def _normalized_input(self, input, affordances):
        tokens = super(LdapGetPasswordSupplicant, self)\
                  ._normalized_input(input, affordances=affordances)
        if 'ldap_bind_dn' not in tokens:
            tokens.ldap_bind_dn = self.bind_dn
        if 'ldap_bind_password' not in tokens:
            tokens.ldap_bind_password = self.bind_password
        if 'ldap_basedn' not in tokens:
            tokens.ldap_basedn = self.basedn
        if 'ldap_username_attr' not in tokens:
            tokens.ldap_username_attr = self.username_attr
        if 'ldap_password_attr' not in tokens:
            tokens.ldap_password_attr = self.password_attr
        return tokens

    def _outputs(self, upstream_affordances, downstream_affordances):
        return (self._OUTPUT,)

    def _process_tokens(self, input, affordances):
        return self._fetch_password(**self._normalized_input(input,
                                                             affordances=
                                                                 affordances))

    def _provisionsets(self, upstream_affordances, downstream_affordances):
        return (self._PROVISIONS,)
