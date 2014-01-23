"""Connectors"""

__copyright__ = "Copyright (C) 2014 Ivan D Vasin"
__docformat__ = "restructuredtext"

from urlparse import urlsplit as _urisplit, urlunsplit as _uriunsplit

from .. import ldap as _ldap
from .. import memcache as _memcache
from .. import session as _session
from .. import _provisions


# XXX: couple LdapSimpleSupplicant with MemcacheSessionStoreSupplicant
# FIXME: rewrite Authenticator so that multiple supplicants can be used in one
#   process.  see the related FIXME in :file:`../_algorithms/_session.py`
class LdapSimpleWithMemcacheSessionStorageSupplicant(_session
                                                      .SessionSupplicant):

    def __init__(self, ldap_server, memcache_server, session_manager,
                 basedn=None, username_attr='uid', use_tls=False, realm=None,
                 username_key='user', **kwargs):
        super(LdapSimpleWithMemcacheSessionStorageSupplicant, self)\
         .__init__(session_manager=session_manager, **kwargs)
        self._ldap_supplicant = \
            _ldap.LdapSimpleSupplicant\
             (server=ldap_server, basedn=basedn, username_attr=username_attr,
              use_tls=use_tls, realm=realm, **kwargs)
        self._memcache_supplicant = \
            _memcache.MemcacheSessionStorageSupplicant\
             (server=memcache_server, username_key=username_key,
              session_manager=session_manager, **kwargs)

    @property
    def authenticator(self):
        authenticator = self._ldap_supplicant.authenticator
        assert authenticator == self._memcache_supplicant.authenticator
        return authenticator

    def logout(self, session_id):
        self._memcache_supplicant.logout(session_id)

    _MANGLED_REALM_SCHEME_SUFFIX = '+memcache'

    _PROVISIONS = _provisions.SECPROV_CLIENT_AUTH

    def _inputs(self, upstream_affordances, downstream_affordances):
        return self._ldap_supplicant\
                ._inputs(upstream_affordances=upstream_affordances,
                         downstream_affordances=downstream_affordances)

    def _mangled_realm(self, realm):
        uri_parts = _urisplit(realm)
        if uri_parts.scheme:
            new_uri_parts = ('{}+memcache'.format(uri_parts.scheme),) \
                            + uri_parts[1:]
            return _uriunsplit(new_uri_parts)
        else:
            return realm

    def _outputs(self, upstream_affordances, downstream_affordances):
        return self._memcache_supplicant\
                ._outputs(upstream_affordances=upstream_affordances,
                          downstream_affordances=downstream_affordances)

    def _process_tokens(self, input, affordances):

        ldap_affordances = affordances.unfrozen_copy()
        ldap_affordances.realms = (self._unmangled_realm(realm)
                                   for realm in ldap_affordances.realms)
        auth_info = \
            self._ldap_supplicant\
                ._verify_creds\
                 (**self._ldap_supplicant
                        ._normalized_input(input,
                                           affordances=ldap_affordances))

        auth_info.tokens['accepted'] = auth_info.accepted
        return self._memcache_supplicant\
                   ._fetch_session_info(affordances=affordances,
                                        **auth_info.tokens)

    def _provisionsets(self, upstream_affordances, downstream_affordances):
        return (self._PROVISIONS,)

    def _realms(self, upstream_affordances, downstream_affordances):
        for ldap_realm \
                in self._ldap_supplicant\
                    ._realms(upstream_affordances=upstream_affordances,
                             downstream_affordances=downstream_affordances):
            yield self._mangled_realm(ldap_realm)

    def _unmangled_realm(self, realm):
        uri_parts = _urisplit(realm)
        if uri_parts.scheme \
               and uri_parts.scheme\
                            .endswith(self._MANGLED_REALM_SCHEME_SUFFIX):
            new_uri_parts = \
                (uri_parts.scheme[:-len(self._MANGLED_REALM_SCHEME_SUFFIX)],) \
                + uri_parts[1:]
            return _uriunsplit(new_uri_parts)
        else:
            return realm
