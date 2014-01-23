"""Algorithms"""

__copyright__ = "Copyright (C) 2014 Ivan D Vasin"
__docformat__ = "restructuredtext"

from base64 import b64encode as _b64encode
from collections import namedtuple as _namedtuple
from hashlib import md5 as _md5
from random import random as _random
from time import time as _time
from urllib import quote as _percent_encode

import pytz as _tz
from spruce.collections import frozenset as _frozenset
import spruce.datetime as _datetime
import spruce.lang as _lang

from ... import _exc as _bedframe_exc
from .. import _algorithms
from .. import _exc
from .. import _info
from .. import _provisions


class DigestAuth(_algorithms.Algorithm):

    PROVISIONS_NO_QOP = _provisions.SECPROV_CLIENT_AUTH \
                        | _provisions.SECPROV_CLIENT_ENCRYPTED_SECRET \
                        | _provisions.SECPROV_SERVER_NONCE

    PROVISIONS_QOP_AUTH = PROVISIONS_NO_QOP \
                          | _provisions.SECPROV_SERVER_NONCE_USE_COUNT \
                          | _provisions.SECPROV_CLIENT_NONCE

    PROVISIONS_QOP_AUTH_INT = \
        PROVISIONS_QOP_AUTH | _provisions.SECPROV_REQUEST_ENTITY_INTEGRITY

    # TODO: add a subclass algorithm with relaxed provisions, and restore the
    #   true provisions here
    #PROVISIONSETS = (_provisions.SECPROV_CLIENT_AUTH, PROVISIONS_NO_QOP,
    #                 PROVISIONS_QOP_AUTH, PROVISIONS_QOP_AUTH_INT)
    PROVISIONSETS = (_provisions.SECPROV_CLIENT_AUTH,)

    TOKENS_NO_QOP = _frozenset(('user', 'realm', 'server_nonce', 'digest_uri',
                                'digest'))

    TOKENS_QOP_AUTH_SPECIFIC = _frozenset(('qop', 'server_nonce_use_count',
                                           'client_nonce'))

    TOKENS_QOP_AUTH = TOKENS_NO_QOP | TOKENS_QOP_AUTH_SPECIFIC

    TOKENS_QOP_AUTH_INT_SPECIFIC = _frozenset(('request_entity_hash',))

    TOKENS_QOP_AUTH_INT = TOKENS_QOP_AUTH | TOKENS_QOP_AUTH_INT_SPECIFIC

    def __init__(self,
                 new_server_nonce_func=None,
                 reuse_server_nonce_func=None,
                 nonce_lifespan=60.,
                 private_key_func=None,
                 private_key_lifespan=300.,
                 *args,
                 **kwargs):
        super(DigestAuth, self).__init__(*args, **kwargs)
        self._new_server_nonce_func = new_server_nonce_func \
                                      or self._default_new_server_nonce_func()
        self._nonce_lifespan = nonce_lifespan
        self._private_key_func = private_key_func \
                                 or self._default_private_key_func()
        self._private_key_lifespan = private_key_lifespan
        self._reuse_server_nonce_func = \
            reuse_server_nonce_func or self._default_reuse_server_nonce_func()
        self._server_nonce_info = {}

    @property
    def current_request(self):
        return self.service.current_request

    def current_request_etag(self, tokens):
        try:
            return tokens['etag']
        except KeyError:
            request = self.current_request
            with self.current_request\
                     .resource\
                     .avoiding_auth('generating entity tag for'
                                     ' authentication'):
                return self.current_request\
                           .method\
                           .withtypes(request.acceptable_mediaranges)\
                           .etag(**request.method_args_prims)

    @property
    def current_request_loc(self):
        return self.current_request.loc

    def current_request_timestamp(self, tokens):
        try:
            return tokens['request_timestamp']
        except KeyError:
            return _datetime.datetime_httpstr(self.current_request
                                                  .timestamp
                                                  .astimezone(_tz.UTC))

    def new_server_nonce(self, tokens, affordances):
        return self._new_server_nonce_func(algorithm=self, tokens=tokens,
                                           affordances=affordances)

    @classmethod
    def phase_classes(cls):
        return (cls.SolicitCredsFromClient, cls.VerifyCredsWithBackend,
                cls.VerifyBackendResponse)

    def private_key(self, tokens, affordances):
        return self._private_key_func(algorithm=self, tokens=tokens,
                                      affordances=affordances)

    def reuse_server_nonce(self, nonce_info, tokens, affordances):
        return self._reuse_server_nonce_func(algorithm=self,
                                             nonce_info=nonce_info,
                                             tokens=tokens,
                                             affordances=affordances)

    @property
    def server_nonce_info(self):
        # FIXME: forget old nonces as time passes
        return self._server_nonce_info

    class ServerNonceInfo(_namedtuple('ServerNonceInfo',
                                      ('value', 'loc', 'etag', 'timestamp',
                                       'use_count'))):
        pass

    class SolicitCredsFromClient(_algorithms.AlgorithmPhase):

        @property
        def input_source(self):
            return 'start'

        @property
        def output_target(self):
            return 'clerk'

        def _affordances_require_qop_auth_int_output\
             (self, upstream_affordances=None, downstream_affordances=None):
            if upstream_affordances is not None \
                   and self.algorithm\
                           ._affordances_require_qop_auth_int_provisions\
                            (upstream_affordances):
                return True
            if downstream_affordances is not None \
                   and (self.algorithm
                            ._affordances_require_qop_auth_int_provisions
                             (downstream_affordances)
                        or self.algorithm
                               ._affordances_require_qop_auth_int_input
                                (downstream_affordances)):
                return True
            return False

        def _affordances_support_qop_auth_int_output\
             (self, upstream_affordances=None, downstream_affordances=None):
            if upstream_affordances is not None \
                   and self.algorithm\
                           ._affordances_support_qop_auth_int_provisions\
                            (upstream_affordances):
                return True
            if downstream_affordances is not None \
                   and (self.algorithm
                            ._affordances_support_qop_auth_int_provisions
                             (downstream_affordances)
                        or self.algorithm
                               ._affordances_support_qop_auth_int_input
                                (downstream_affordances)):
                return True
            return False

        def _inputs(self, upstream_affordances, downstream_affordances):
            return ((),)

        def _outputs(self, upstream_affordances, downstream_affordances):
            return (('realm', 'space_uris', 'server_nonce', 'qop',
                     'digest_algorithm'),)

        def _process_tokens(self, input, affordances):
            return _info.RequestAuthInfo\
                    (tokens=self.algorithm
                                ._challenge_tokens(input,
                                                   affordances=affordances))

    class VerifyCredsWithBackend(_algorithms.AlgorithmPhase):

        @property
        def input_source(self):
            return 'scanner'

        @property
        def output_target(self):
            return 'supplicant'

        def _affordances_require_qop_auth_output(self, upstream_affordances,
                                                 downstream_affordances):
            return self.algorithm\
                       ._affordances_require_qop_auth_provisions\
                        (upstream_affordances) \
                   or self.algorithm\
                          ._affordances_require_qop_auth_provisions\
                           (downstream_affordances) \
                   or self.algorithm\
                          ._affordances_require_qop_auth_input\
                           (downstream_affordances)

        def _affordances_require_qop_auth_int_output\
             (self, upstream_affordances=None, downstream_affordances=None):
            if upstream_affordances is not None \
                   and self.algorithm\
                           ._affordances_require_qop_auth_int_provisions\
                            (upstream_affordances):
                return True
            if downstream_affordances is not None \
                   and (self.algorithm
                            ._affordances_require_qop_auth_int_provisions
                             (downstream_affordances)
                        or self.algorithm
                               ._affordances_require_qop_auth_int_input
                                (downstream_affordances)):
                return True
            return False

        def _affordances_support_qop_auth_int_input(self,
                                                    upstream_affordances,
                                                    downstream_affordances):
            return self.algorithm\
                       ._affordances_support_qop_auth_int_output\
                        (upstream_affordances)

        def _affordances_support_qop_auth_int_output(self,
                                                     upstream_affordances,
                                                     downstream_affordances):
            return self.algorithm\
                       ._affordances_support_qop_auth_int_provisions\
                        (upstream_affordances) \
                       or self.algorithm\
                              ._affordances_support_qop_auth_int_provisions\
                               (downstream_affordances) \
                       or self.algorithm\
                              ._affordances_support_qop_auth_int_input\
                               (downstream_affordances)

        def _inputs(self, upstream_affordances, downstream_affordances):
            if self._affordances_require_qop_auth_int_output\
                (upstream_affordances=upstream_affordances,
                 downstream_affordances=downstream_affordances):
                return (self.algorithm.TOKENS_QOP_AUTH_INT,)
            else:
                return (self.algorithm.TOKENS_QOP_AUTH,)

        def _outputs(self, upstream_affordances, downstream_affordances):
            if self.algorithm\
                   ._affordances_guarantee_qop_auth_int_output\
                    (upstream_affordances):
                return (self.algorithm.TOKENS_QOP_AUTH_INT,)
            elif self.algorithm\
                     ._affordances_support_qop_auth_int_output\
                      (upstream_affordances):
                return (self.algorithm.TOKENS_QOP_AUTH,
                        self.algorithm.TOKENS_QOP_AUTH_INT)
            else:
                return (self.algorithm.TOKENS_QOP_AUTH,)

        def _process_tokens(self, input, affordances):

            tokens = input.copy()

            missing_required_tokens = \
                [name for name in self.algorithm.TOKENS_NO_QOP
                 if name not in tokens]
            if missing_required_tokens:
                raise _exc.MissingTokens(missing_required_tokens)

            tokens['realm'] = iter(affordances.realms).next()

            if 'qop' in tokens:
                qop = tokens['qop']
                if qop.startswith('auth'):
                    missing_required_tokens = \
                        [name
                         for name in self.algorithm.TOKENS_QOP_AUTH_SPECIFIC
                         if name not in tokens]
                    if missing_required_tokens:
                        raise _exc.MissingTokens\
                               (missing_required_tokens,
                                'required due to token qop={}'.format(qop))

                    _lang.require_isinstance(tokens['server_nonce_use_count'],
                                             _lang.hex_intlike)

                    if qop == 'auth-int':
                        missing_required_tokens = \
                            [name
                             for name
                             in self.algorithm.TOKENS_QOP_AUTH_INT_SPECIFIC
                             if name not in tokens]
                        if missing_required_tokens:
                            raise _exc.MissingTokens\
                                   (missing_required_tokens,
                                    'required due to token qop={}'.format(qop))

                        tokens['request_entity_hash'] = \
                            _md5(self.service.current_request.body).hexdigest()

                    else:
                        if self._affordances_require_qop_auth_int_output\
                               (upstream_affordances=affordances):
                            # FIXME
                            raise ValueError
                else:
                    raise ValueError('invalid qop value {!r}: expecting one of'
                                      ' {}'
                                      .format(qop, ('auth', 'auth-int')))
            else:
                if self._affordances_require_qop_auth_output\
                       (upstream_affordances=affordances):
                    # FIXME
                    raise ValueError

            return _info.RequestAuthInfo(tokens=tokens)

    class VerifyBackendResponse(_algorithms.AlgorithmPhase):

        @property
        def input_source(self):
            return 'supplicant'

        @property
        def output_target(self):
            return 'end'

        def _inputs(self, upstream_affordances, downstream_affordances):
            ubi_tokens = list(self.algorithm.TOKENS_NO_QOP)
            return (ubi_tokens + ['actual_digest'],
                    ubi_tokens + ['actual_a1'],
                    ubi_tokens + ['actual_password'],
                    ubi_tokens + ['qop', 'actual_password',
                                  'server_nonce_use_count', 'client_nonce'],
                    ubi_tokens + ['qop', 'actual_password',
                                  'server_nonce_use_count', 'client_nonce',
                                  'request_entity_hash'],
                    )

        def _outputs(self, upstream_affordances, downstream_affordances):
            return tuple(list(input_) + ['accepted', 'stale']
                         for input_
                         in self.inputs(upstream_affordances=
                                            upstream_affordances,
                                        downstream_affordances=
                                            downstream_affordances))

        def _process_tokens(self, input, affordances):

            tokens = input.copy()

            missing_required_tokens = \
                [name for name in self.algorithm.TOKENS_NO_QOP
                 if name not in tokens]
            if missing_required_tokens:
                raise _exc.MissingTokens(missing_required_tokens)

            user = tokens['user']
            realm = tokens['realm']
            server_nonce = tokens['server_nonce']
            digest_uri = tokens['digest_uri']
            digest = tokens['digest']
            digest_algorithm = tokens.get('digest_algorithm', 'MD5')

            provisions = \
                _provisions.ProvisionSet(self.algorithm.PROVISIONS_NO_QOP)

            try:
                server_nonce_info = \
                    self.algorithm.server_nonce_info[server_nonce]
            except KeyError:
                server_nonce_info = None
                server_nonce_stale = True
            else:
                server_nonce_stale = \
                    not self.algorithm\
                            .reuse_server_nonce(nonce_info=server_nonce_info,
                                                tokens=tokens,
                                                affordances=affordances)

            try:
                actual_digest = tokens['actual_digest']
            except KeyError:
                try:
                    actual_a1 = tokens['actual_a1']
                except KeyError:
                    actual_password = tokens['actual_password']

                    if actual_password is None:
                        return _info.RequestAuthInfo(tokens=tokens,
                                                     accepted=False)

                    if digest_algorithm == 'MD5':
                        actual_a1 = '{}:{}:{}'.format(user, realm,
                                                      actual_password)
                    elif digest_algorithm == 'MD5-sess':
                        try:
                            client_nonce = tokens['client_nonce']
                        except KeyError:
                            raise _exc.MissingTokens\
                                   (('client_nonce',),
                                    'required due to token digest_algorithm={}'
                                     .format(digest_algorithm))
                        actual_a1 = \
                            '{}:{}:{}'\
                             .format(_md5('{}:{}:{}'.format(user, realm,
                                                            actual_password),
                                          server_nonce,
                                          client_nonce))
                    else:
                        raise ValueError\
                               ('invalid digest authentication algorithm {!r}:'
                                 ' expecting one of {}'
                                 .format(digest_algorithm,
                                         ('MD5', 'MD5-sess')))

                actual_a1_digest = _md5(actual_a1).hexdigest()

                qop = tokens.get('qop', 'auth')
                impl_method = self.service.current_request.impl_method
                if qop == 'auth':
                    actual_a2 = '{}:{}'.format(impl_method, digest_uri)

                elif qop == 'auth-int':
                    missing_required_tokens = \
                        [name
                         for name
                         in self.algorithm.TOKENS_QOP_AUTH_INT_SPECIFIC
                         if name not in tokens]
                    if missing_required_tokens:
                        raise _exc.MissingTokens\
                               (missing_required_tokens,
                                'required due to token qop={}'.format(qop))

                    provisions |= _provisions.SECPROV_REQUEST_ENTITY_INTEGRITY

                    request_entity_hash = tokens['request_entity_hash']
                    actual_a2 = '{}:{}:{}'.format(impl_method, digest_uri,
                                                  request_entity_hash)

                else:
                    raise ValueError\
                           ('invalid qop value {!r}: expecting one of {}'
                             .format(qop, ('auth', 'auth-int')))

                actual_a2_digest = _md5(actual_a2).hexdigest()

                if 'qop' in tokens:
                    if qop.startswith('auth'):
                        missing_required_tokens = \
                            [name
                             for name
                             in self.algorithm.TOKENS_QOP_AUTH_SPECIFIC
                             if name not in tokens]
                        if missing_required_tokens:
                            raise _exc.MissingTokens\
                                   (missing_required_tokens,
                                    'required due to token qop={}'
                                     .format(missing_required_tokens, qop))

                        server_nonce_use_count_str = \
                            tokens['server_nonce_use_count']
                        server_nonce_use_count = \
                            _lang.hex_int(server_nonce_use_count_str)
                        client_nonce = tokens['client_nonce']

                        if server_nonce_info \
                               and server_nonce_use_count \
                                   < server_nonce_info.use_count:
                            raise _exc.AttackDetected('replay attack')

                        provisions |= \
                            _provisions.SECPROV_SERVER_NONCE_USE_COUNT \
                            | _provisions.SECPROV_CLIENT_NONCE

                        actual_digest = \
                            _md5('{}:{}:{}:{}:{}:{}'
                                  .format(actual_a1_digest,
                                          server_nonce,
                                          server_nonce_use_count_str,
                                          client_nonce,
                                          qop,
                                          actual_a2_digest))\
                             .hexdigest()

                    else:
                        # FIXME
                        raise ValueError

                else:
                    actual_digest = \
                        _md5('{}:{}:{}'.format(actual_a1_digest, server_nonce,
                                               actual_a2_digest))\
                         .hexdigest()

            if digest == actual_digest:
                if server_nonce_stale:
                    tokens['stale'] = 'true'
                    accepted = False
                else:
                    accepted = True
            else:
                tokens['stale'] = 'false'
                accepted = False

            if server_nonce_stale:
                if server_nonce is not None \
                       and server_nonce in self.algorithm.server_nonce_info:
                    del self.algorithm.server_nonce_info[server_nonce]

                new_server_nonce = \
                    self.algorithm.new_server_nonce(tokens=tokens,
                                                    affordances=affordances)
                tokens['server_nonce'] = new_server_nonce
            else:
                server_nonce_info = \
                    self.algorithm\
                        .ServerNonceInfo(value=server_nonce,
                                         loc=server_nonce_info.etag,
                                         etag=server_nonce_info.etag,
                                         timestamp=server_nonce_info.timestamp,
                                         use_count=(server_nonce_info.use_count
                                                    + 1))
                self.algorithm.server_nonce_info[server_nonce] = \
                    server_nonce_info

            if not accepted:
                tokens = \
                    self.algorithm._challenge_tokens(input,
                                                     affordances=affordances)

            return _info.RequestAuthInfo(tokens=tokens, provisions=provisions,
                                         accepted=accepted)

    def _affordances_guarantee_digest_output(self, affordances):
        return affordances.outputs.all_gte(self.TOKENS_NO_QOP)

    def _affordances_guarantee_qop_auth_output(self, affordances):
        return affordances.outputs.all_gte(self.TOKENS_QOP_AUTH)

    def _affordances_guarantee_qop_auth_int_output(self, affordances):
        return affordances.outputs.all_gte(self.TOKENS_QOP_AUTH)

    def _affordances_require_digest_input(self, affordances):
        return affordances.inputs.all_gte(self.TOKENS_NO_QOP)

    def _affordances_require_qop_auth_input(self, affordances):
        return affordances.inputs.all_gte(self.TOKENS_QOP_AUTH)

    def _affordances_require_qop_auth_int_input(self, affordances):
        return affordances.inputs.all_gte(self.TOKENS_QOP_AUTH_INT)

    def _affordances_require_qop_auth_int_provisions(self, affordances):
        return affordances.provisionsets.all_gte(self.PROVISIONS_QOP_AUTH_INT)

    def _affordances_require_qop_auth_provisions(self, affordances):
        return affordances.provisionsets.all_gte(self.PROVISIONS_QOP_AUTH)

    def _affordances_support_digest_input(self, affordances):
        return affordances.inputs.any_gte(self.TOKENS_NO_QOP)

    def _affordances_support_digest_output(self, affordances):
        return affordances.outputs.any_gte(self.TOKENS_NO_QOP)

    def _affordances_support_qop_auth_input(self, affordances):
        return affordances.inputs.any_gte(self.TOKENS_QOP_AUTH)

    def _affordances_support_qop_auth_int_input(self, affordances):
        return affordances.inputs.any_gte(self.TOKENS_QOP_AUTH_INT)

    def _affordances_support_qop_auth_int_output(self, affordances):
        return affordances.outputs.any_gte(self.TOKENS_QOP_AUTH_INT)

    def _affordances_support_qop_auth_int_provisions(self, affordances):
        return affordances.provisionsets.any_gte(self.PROVISIONS_QOP_AUTH_INT)

    def _affordances_support_qop_auth_output(self, affordances):
        return affordances.outputs.any_gte(self.TOKENS_QOP_AUTH)

    def _affordances_support_qop_auth_provisions(self, affordances):
        return affordances.provisionsets.any_gte(self.PROVISIONS_QOP_AUTH)

    def _challenge_tokens(self, tokens, affordances):

        tokens = tokens.unfrozen_copy()

        if 'realm' not in tokens:
            tokens['realm'] = iter(affordances.realms).next()

        if 'space_uris' not in tokens:
            space_locs = \
                self.service\
                    .auth_spaces\
                    .locs(self.service.current_request.auth_space)
            tokens['space_uris'] = ' '.join(_percent_encode(loc.pattern)
                                            for loc in space_locs)

        tokens['server_nonce'] = self.new_server_nonce(tokens=tokens,
                                                       affordances=affordances)

        if 'qop' not in tokens:
            if self.phases[0]\
                   ._affordances_require_qop_auth_int_output\
                    (upstream_affordances=affordances):
                tokens['qop'] = 'auth-int'
            elif self.phases[0]\
                     ._affordances_support_qop_auth_int_output\
                      (upstream_affordances=affordances):
                tokens['qop'] = 'auth, auth-int'
            else:
                tokens['qop'] = 'auth'

        if 'digest_algorithm' not in tokens:
            # TODO: support MD5-sess
            tokens['digest_algorithm'] = 'MD5'

        return tokens

    @classmethod
    def _default_new_server_nonce_func(cls):
        def new_server_nonce(algorithm, tokens, affordances):
            try:
                state_digest = tokens['state_digest']
            except KeyError:
                request_timestamp = \
                    algorithm.current_request_timestamp(tokens=tokens)
                try:
                    etag = algorithm.current_request_etag(tokens=tokens)
                except _bedframe_exc.AvoidingAuth:
                    etag = _b64encode(algorithm.current_request_loc)

                try:
                    private_key = tokens['private_key']
                except KeyError:
                    private_key = \
                        algorithm.private_key(tokens=tokens,
                                              affordances=affordances)

                state_digest = \
                    _md5('{}:{}:{}'.format(request_timestamp, etag,
                                           private_key))\
                     .hexdigest()

            nonce = _b64encode('{}{}'.format(request_timestamp, state_digest))
            algorithm.server_nonce_info[nonce] = \
                algorithm.ServerNonceInfo(value=nonce,
                                          loc=algorithm.current_request_loc,
                                          etag=etag,
                                          timestamp=request_timestamp,
                                          use_count=0)
            return nonce
        return new_server_nonce

    @classmethod
    def _default_private_key_func(cls):
        def private_key(algorithm, tokens, affordances):
            key_create_time = float('-inf')
            while True:
                if _time() - key_create_time > algorithm.private_key_lifespan:
                    key = _b64encode(str(_random()))
                    key_create_time = _time()
                yield key
        return private_key

    @classmethod
    def _default_reuse_server_nonce_func(cls):
        def reuse_server_nonce(nonce_info, algorithm, tokens, affordances):
            while True:
                if _provisions.SECPROV_SERVER_NONCE_PER_REQUEST \
                       in affordances.provisionsets:
                    yield False
                    continue

                if _provisions.SECPROV_SERVER_NONCE_PER_RESOURCE \
                       in affordances.provisionsets \
                       and algorithm.current_request_loc \
                           != algorithm.nonce_info.loc:
                    yield False
                    continue

                if _time() - nonce_info.timestamp > algorithm.nonce_lifespan:
                    yield False
                    continue

                try:
                    etag = algorithm.current_request_etag(tokens=tokens)
                except _bedframe_exc.AvoidingAuth:
                    yield False
                    continue
                else:
                    if etag != nonce_info.etag:
                        yield False
                        continue

                yield True
        return reuse_server_nonce

    def _provisionsets(self, upstream_affordances, downstream_affordances):
        return self.PROVISIONSETS
