"""Connectors"""

__copyright__ = "Copyright (C) 2014 Ivan D Vasin"
__docformat__ = "restructuredtext"

import json as _json
from uuid import uuid4 as _uuid4

import memcache as _memcache
from spruce.collections import frozenset as _frozenset

from .. import session as _session
from .. import _info


class MemcacheSessionAuthSupplicant(_session.SessionSupplicant):

    """
    An authentication supplicant that uses an authentication session stored
    in Memcache

    """

    def __init__(self, server, username_key='user', **kwargs):
        super(MemcacheSessionAuthSupplicant, self).__init__(**kwargs)
        self._server = server
        self._username_key = username_key

    def logout(self, session_id):
        cache = _memcache.Client((self.server,))
        cache.delete(session_id)

    @property
    def server(self):
        return self._server

    @server.setter
    def server(self, value):
        self._server = value

    @property
    def username_key(self):
        return self._username_key

    @username_key.setter
    def username_key(self, value):
        self._username_key = value

    def _init_args(self, ordered=False):
        args = super(MemcacheSessionAuthSupplicant, self)\
                ._init_args(ordered=ordered)
        args.update((('server', self.server),
                     ('username_key', self.username_key)))
        return args

    def _process_tokens(self, input, affordances):
        return self._fetch_session_info(affordances=affordances, **input)

    def _provisionsets(self, upstream_affordances, downstream_affordances):
        return (_session.SessionAuth.PROVISIONS,)

    def _realms(self, upstream_affordances, downstream_affordances):
        return '*'


class MemcacheSessionStorageSupplicant(MemcacheSessionAuthSupplicant):

    """
    An authentication supplicant that stores an authentication session in
    Memcache

    """

    _INPUT = _frozenset(('user', 'accepted'))

    _OUTPUT = _frozenset(('user', 'accepted', 'session_id', 'memcache_server',
                          'memcache_username_key'))

    def _fetch_session_info(self, user, accepted, affordances, **other_tokens):

        tokens = other_tokens

        if accepted:
            session_id = _uuid4().hex
            session_info = {'user': user, 'accepted': accepted}
            session_info_json = _json.dumps(session_info)

            cache = _memcache.Client((self.server,))
            cache.set(session_id, session_info_json)

            tokens.update(session_info)
            tokens['session_id'] = session_id

        tokens.update({'user': user,
                       'accepted': _json.dumps(accepted),
                       'memcache_server': self.server,
                       'memcache_username_key': self.username_key})
        return _info.RequestAuthInfo(tokens=tokens,
                                     provisions=
                                         _session.SessionAuth.PROVISIONS,
                                     accepted=accepted)

    def _inputs(self, upstream_affordances, downstream_affordances):
        return (self._INPUT,)

    def _outputs(self, upstream_affordances, downstream_affordances):
        return (self._OUTPUT,)


class MemcacheSessionRecallSupplicant(MemcacheSessionAuthSupplicant):

    """
    An authentication supplicant that recalls an authentication session from
    Memcache

    """

    _INPUT = _frozenset(('session_id',))

    _OUTPUT = _frozenset(('user', 'accepted', 'session_id', 'memcache_server',
                          'memcache_username_key'))

    def _fetch_session_info(self, session_id, affordances, **other_tokens):

        tokens = other_tokens
        accepted = False

        cache = _memcache.Client((self.server,))
        try:
            session_info_json = cache.get(session_id)
        except _memcache.Client.MemcachedKeyError:
            session_info_json = None
        if session_info_json is not None:
            try:
                session_info = _json.loads(session_info_json)
            except (TypeError, ValueError) as exc:
                raise RuntimeError('invalid authentication session info:'
                                    ' cannot load JSON: {}'.format(exc))

            try:
                user = session_info[self.username_key]
            except KeyError as exc:
                raise RuntimeError('invalid authentication session info:'
                                    ' missing value for {!r}'
                                    .format(exc.args[0]))
            except (TypeError, ValueError) as exc:
                raise RuntimeError('invalid authentication session info: {}'
                                    .format(exc))

            tokens.update(session_info)
            tokens.update({'user': user})
            accepted = session_info['accepted']

        tokens.update({'session_id': session_id,
                       'memcache_server': self.server,
                       'memcache_username_key': self.username_key})
        return _info.RequestAuthInfo(tokens=tokens,
                                     provisions=
                                         _session.SessionAuth.PROVISIONS,
                                     accepted=accepted)

    def _inputs(self, upstream_affordances, downstream_affordances):
        return (self._INPUT,)

    def _outputs(self, upstream_affordances, downstream_affordances):
        return (self._OUTPUT,)
