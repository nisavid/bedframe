"""Web services"""

__copyright__ = "Copyright (C) 2014 Ivan D Vasin"
__docformat__ = "restructuredtext"

import abc as _abc
import os as _os
import signal as _signal
from urlparse import urlsplit as _urlsplit

import psutil as _ps
import raven as _sentry
from spruce.lang import bool as _bool, enum as _enum, int as _int
import spruce.logging as _logging
import spruce.settings as _settings
import ujson as _json

from . import auth as _auth
from . import _cors
from . import _debug
from . import _exc
from . import _resources


class WebService(object):

    """A web service

    A :class:`!WebService` provides an interface to an underlying web service
    implementation.

    This class provides an entry point to any service implementation that is
    available in the current environment.  It exposes the interface of the
    chosen implementation, which is a :class:`WebServiceImpl` subclass.

    To instantiate a service using any available implementation, omit
    *impl*.  To instantiate a service using a particular implementation,
    provide a registered *impl* name.  To register a new implementation, use
    :meth:`register_impl`.

    These implementations are available by default if their corresponding
    dependencies are met:

    ================ ==================== ===================
    Name             Class                Dependencies
    ================ ==================== ===================
    ``tornado``      |TornadoService|     :pypi:`tornado`
    ``tornado-wsgi`` |TornadoWsgiService| |tornado-bedframe|_
    ================ ==================== ===================

    .. |TornadoService| replace::
        :class:`bedframe.tornado.TornadoService \
                <bedframe.tornado._services.TornadoService>`

    .. |TornadoWsgiService| replace::
        :class:`bedframe.tornado.TornadoWsgiService \
                <bedframe.tornado._services.TornadoWsgiService>`

    .. |tornado-bedframe| replace::
        tornado-bedframe
    .. _tornado-bedframe:
        http://github.com/nisavid/tornado-bedframe

    :param impl:
        The name of a :class:`!WebService` implementation.
    :type impl: :obj:`str` or null

    :param uris:
        The URIs at which this service will be accessible.
    :type uris: ~[:obj:`str`] or null

    :param resources:
        A mapping of resource paths to resource objects.
    :type resources:
        ~{~\ :obj:`re`: :class:`~bedframe._resources._core.WebResource`}

    :param auth_spaces:
        Authentication spaces.
    :type auth_spaces:
        ~\ :class:`bedframe.auth.SpaceMap <bedframe.auth._spaces.SpaceMap>`

    :param debug_flags:
        Debugging flags.
    :type debug_flags: :class:`~bedframe._debug.DebugFlagSet`

    :param kwargs:
        Additional arguments to the service implementation.

    """

    def __init__(self, impl=None, uris=None, resources=None, auth_spaces=None,
                 debug_flags=_debug.DEBUG_DEFAULT, **kwargs):
        if impl is None:
            try:
                impl = self._impls.keys()[0]
            except IndexError:
                raise RuntimeError('cannot find any implementations of {}.{}'
                                    .format(self.__module__,
                                            self.__class__.__name__))
        self.__dict__['_impl'] = \
            self._impls[impl](uris=uris, resources=resources,
                              auth_spaces=auth_spaces, debug_flags=debug_flags,
                              **kwargs)

    def __getattr__(self, name):
        try:
            return getattr(self.impl, name)
        except AttributeError as exc:
            try:
                return object.__getattr__(self, name)
            except AttributeError:
                raise exc

    def __setattr__(self, name, value):
        if hasattr(self.impl, name):
            setattr(self.impl, name, value)
        else:
            object.__setattr__(self, name, value)

    @property
    def impl(self):
        """This web service's implementation

        :type: :class:`WebServiceImpl`

        """
        return self._impl

    @classmethod
    def register_impl(cls, name, impl):
        """Register a web service implementation

        :param str name:
            The implementation's name.

        :param impl:
            The implementation.
        :type impl: :class:`WebServiceImpl`

        """
        cls._impls[name] = impl

    _impls = {}


class WebServiceImpl(object):

    """A :class:`WebService` implementation

    :param resources:
        A mapping of resource paths to resource objects.
    :type resources:
        ~{~\ :obj:`re`: :class:`~bedframe._resources._core.WebResource`}

    :param auth_spaces:
        Authentication spaces.
    :type auth_spaces:
        ~\ :class:`bedframe.auth.SpaceMap <bedframe.auth._spaces.SpaceMap>`

    :param debug_flags:
        Debugging flags.
    :type debug_flags: :class:`~bedframe._debug.DebugFlagSet`

    .. note:: **TODO:**
        encapsulate the components that are common to this and
        :class:`spruce.ldap.ServiceImpl \
                <spruce.ldap._services.ServiceImpl>`

    """

    __metaclass__ = _abc.ABCMeta

    def __init__(self, uris=None, resources=None, authenticator=None,
                 auth_spaces=None, cors_affordancesets=None, settings=None,
                 logger=None, debug_flags=_debug.DEBUG_DEFAULT,
                 stop_on_del=True):

        self._cors_affordancesets = \
            _cors.CorsAffordanceSetMap(cors_affordancesets)
        self.current_request = None
        self.current_request_resource = None
        self.debug_flags = debug_flags
        self._logger = logger or _logging.getLogger('bedframe')
        self._resources = _resources.WebResourceMap(resources)
        self._settings = settings or _settings.Settings('bedframe')
        self.stop_on_del = stop_on_del
        self._uris = tuple(uris or ())

        auth_spaces = _auth.SpaceMap(auth_spaces)
        if authenticator:
            if auth_spaces:
                authenticator.auth_spaces.clear()
                authenticator.auth_spaces.update(auth_spaces)
            self._authenticator = authenticator
        else:
            self._authenticator = _auth.Authenticator(service=self,
                                                      spaces=auth_spaces)

        # FIXME: parametrize better
        sentry_server = self.settings.value('sentry/server')
        self._sentryclient = _sentry.Client(sentry_server) \
                                 if sentry_server is not None else None

        self._set_status('stopped')

    def __del__(self):

        try:
            stop = self.stop_on_del and self.status == 'running'
        except AttributeError:
            stop = False

        if stop:
            self.stop()

    @property
    def auth_algorithms(self):
        """The authentication algorithms

        :type: [:class:`bedframe.auth.Algorithm \
                        <bedframe.auth._algorithms.Algorithm>`]

        """
        return self.authenticator.algorithms

    @property
    def auth_clerks(self):
        """The authentication clerks

        :type: [:class:`bedframe.auth.Clerk \
                        <bedframe.auth._connectors.Clerk>`]

        """
        return self.authenticator.clerks

    @property
    def auth_scanners(self):
        """The authentication scanners

        :type: [:class:`bedframe.auth.Scanner \
                        <bedframe.auth._connectors.Scanner>`]

        """
        return self.authenticator.scanners

    @property
    def auth_spaces(self):
        """The authentication spaces

        :type: :class:`bedframe.auth.SpaceMap <bedframe.auth._spaces.SpaceMap>`

        """
        return self.authenticator.spaces

    @property
    def auth_supplicants(self):
        """The authentication supplicants

        :type: [:class:`bedframe.auth.Supplicant \
                        <bedframe.auth._connectors.Supplicant>`]

        """
        return self.authenticator.supplicants

    @property
    def authenticator(self):
        """The authenticator

        :type: :class:`bedframe.auth.Authenticator \
                       <bedframe.auth._authenticators.Authenticator>`

        """
        return self._authenticator

    @property
    def cors_affordancesets(self):
        """The cross-origin resource sharing affordances map

        :type: :class:`~bedframe._cors.CorsAffordanceSetMap`

        """
        return self._cors_affordancesets

    @property
    def current_auth_info(self):
        """Authentication information for the current request

        If no request is currently being handled, this is :obj:`None`.

        :type: :class:`bedframe.auth.RequestAuthInfo \
                       <bedframe.auth._info.RequestAuthInfo>`
               or null

        """
        return self.current_request.auth_info if self.current_request else None

    @current_auth_info.setter
    def current_auth_info(self, value):
        self.current_request.auth_info = value

    @property
    def current_request(self):
        """The current request

        If no request is currently being handled, this is :obj:`None`.

        Normally this is set by :meth:`WebResource.provided_for_request()
        <bedframe._resources._core.WebResource.provided_for_request>`.

        :type: :class:`~bedframe._requests.WebRequest` or null

        """
        return self._current_request

    @current_request.setter
    def current_request(self, value):
        self._current_request = value

    @property
    def debug_flags(self):
        """The debugging flags

        :type: :class:`~bedframe._debug.DebugFlagSet`

        """
        return self._debug_flags

    @debug_flags.setter
    def debug_flags(self, value):
        self._debug_flags = value

    def ensure_auth(self, loc=None, **kwargs):

        """Ensure authentication

        .. seealso::
            :meth:`bedframe.auth.Authenticator.ensure_auth() \
                   <bedframe.auth._authenticators.Authenticator.ensure_auth>`

        """
        if loc:
            self.authenticator.ensure_auth(loc=loc, **kwargs)
        else:
            self.current_request.ensure_auth(**kwargs)

    def has_auth(self, loc=None, **kwargs):

        """Whether this request is authenticated

        .. seealso::
            :meth:`bedframe.auth.Authenticator.has_auth() \
                   <bedframe.auth._authenticators.Authenticator.has_auth>`

        """
        if loc:
            return self.authenticator.has_auth(loc=loc, **kwargs)
        else:
            return self.current_request.has_auth(**kwargs)

    @property
    def hostname(self):
        return _urlsplit(self.uri).hostname

    @property
    def sentryclient(self):
        return self._sentryclient

    @property
    def logger(self):
        return self._logger

    @property
    def pid(self):
        return self._pid

    @property
    def port(self):
        return _urlsplit(self.uri).port

    @property
    def resources(self):
        """The web resource map

        :type: :class:`bedframe.WebResourceMap \
                       <bedframe._resources._mappings.WebResourceMap>`

        """
        return self._resources

    @property
    def settings(self):
        return self._settings

    def start(self, fork=False):
        """Start this web service

        Listen for requests on the given *port*, responding according to
        the configured :attr:`resources` and :attr:`auth_spaces`.

        :param int port:
            The port on which to listen for requests.

        :param bool fork:
            Whether to run in the background.

        """

        if self.status == 'running':
            raise _exc.InvalidServiceOperation(self, 'start',
                                               'the service is already'
                                                ' running')

        self._start(fork=fork)

    @property
    def status(self):
        self._probe_status()
        return self._status

    def stop(self):

        if self.status != 'running':
            raise _exc.InvalidServiceOperation(self, 'stop',
                                               'the service is not running')

        try:
            _os.kill(self.pid, _signal.SIGTERM)
        except OSError as exc:
            if exc.errno == _os.errno.ESRCH:
                self._set_status('gone')
                raise _exc.InvalidServiceOperation\
                       (self, 'stop',
                        'the service went away before it could be stopped')
            else:
                raise
        else:
            _os.waitpid(self.pid, 0)
            self._set_status('stopped')

    @property
    def stop_on_del(self):
        return self._stop_on_del

    @stop_on_del.setter
    def stop_on_del(self, value):
        self._stop_on_del = _bool(value)

    @property
    def uri(self):

        if len(self.uris) != 1:
            raise RuntimeError('cannot identify unique service URI: expecting'
                                ' service URIs to be a singleton sequence, but'
                                ' found {!r}'.format(self.uris))

        return self.uris[0]

    @property
    def uris(self):
        return self._uris

    def _arg_prim_fromjson(self, name, json, fallback_to_passthrough=False):
        try:
            return _json.loads(json)
        except ValueError as exc:
            if fallback_to_passthrough:
                return json
            else:
                raise _exc.ArgJsonValueError(name, json, str(exc))

    def _probe_status(self):
        if self._status == 'running':
            gone = False
            if _ps.pid_exists(self.pid):
                if _ps.Process(self.pid).status == _ps.STATUS_ZOMBIE:
                    gone = True
                    _os.waitpid(self.pid, 0)
            else:
                gone = True
            if gone:
                self._set_status('gone')

    def _set_status(self, status, pid=None):

        if status == 'running' and pid is None:
            raise ValueError('missing arg pid: required by status {!r}'
                              .format(status))

        if status == 'running':
            pid = _int(pid)
        else:
            pid = None

        self._pid = pid
        self._status = status

        if pid is not None:
            self._probe_status()

    def _start(self, fork=False):

        if fork:
            pid = _os.fork()
            if pid != 0:
                self._set_status('running', pid=pid)
                return pid

        self._start_nofork()
        self._set_status('running', pid=_os.getpid())

    @_abc.abstractmethod
    def _start_nofork(self):
        pass


WebServiceStatus = _enum('web service status', ('stopped', 'running', 'gone'))
