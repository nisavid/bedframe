"""Exceptions"""

__copyright__ = "Copyright (C) 2014 Ivan D Vasin"
__docformat__ = "restructuredtext"

import exceptions as _exceptions
import traceback as _traceback

from . import _metadata
from . import _responses


# core ------------------------------------------------------------------------


def unhandled_exception(exc, traceback=None, *args, **kwargs):

    if traceback is True:
        tb_entries = _traceback.extract_stack()
        tb_entries = tb_entries[:-1]
        traceback = ''.join(_traceback.format_list(tb_entries))

    base_class = UnhandledException
    exc_class = exc.__class__
    unhandled_exc_class = type('{} {}:{}'.format(base_class.__name__,
                                                 exc_class.__module__,
                                                 exc_class.__name__),
                               (base_class, exc_class), {})
    return unhandled_exc_class(exc, traceback=traceback, *args, **kwargs)


class Exception(_exceptions.Exception):
    pass


class WebMethodException(Exception):

    def __init__(self, method, exc, orig_raw_traceback,
                 traceback_entries_filter, *args):
        super(WebMethodException, self)\
         .__init__(method, exc, orig_raw_traceback, traceback_entries_filter,
                   *args)

    def __str__(self):
        return 'exception in method {}: {}'.format(self.method, self.exc)

    @property
    def exc(self):
        return self.args[1]

    @property
    def method(self):
        return self.args[0]

    @property
    def orig_raw_traceback(self):
        return self.args[2]

    @property
    def orig_traceback_entries(self):
        return _traceback.extract_tb(self.orig_raw_traceback)

    def response(self, debug_flags):
        return self.method.response_fromexc(self.exc,
                                            self.traceback(debug_flags=
                                                               debug_flags),
                                            debug_flags=debug_flags)

    def traceback(self, debug_flags):
        return ''.join(_traceback
                        .format_list(self.traceback_entries(debug_flags=
                                                                debug_flags)))

    def traceback_entries(self, debug_flags):
        return self.traceback_entries_filter(self.orig_traceback_entries,
                                             debug_flags=debug_flags)

    @property
    def traceback_entries_filter(self):
        return self.args[3]


class Error(RuntimeError, Exception):
    pass


# redirections ----------------------------------------------------------------


class Redirection(Exception):
    pass


class EntityChoiceRedirection(Redirection):

    """Multiple entities exist that could satisfy the request

    The request was processed, but it did not include enough information to
    specify a single corresponding response entity.  The redirection
    response indicates the locations of entities that could satisfy the
    request, optionally the location of a single suggested or preferred
    entity, and optionally some metadata about each entity.

    """

    def __init__(self, locs, message=None, preferred_loc=None,
                 locs_metadata=None, *args):
        super(EntityChoiceRedirection, self)\
         .__init__(tuple(locs), message, preferred_loc, locs_metadata or {},
                   *args)

    def __str__(self):

        if self.locs_metadata:
            locs_str = str(tuple(loc + (' {}'.format(self.locs_metadata[loc])
                                        if loc in self.locs_metadata
                                        else '')
                                 for loc in self.locs))
        else:
            locs_str = str(self.locs)

        message = 'choose among entities {}'.format(locs_str)
        if self.preferred_loc:
            message += ' (preferred: {})'.format(self.preferred_loc)
        if self.message:
            message += ': {}'.format(self.message)
        return message

    @property
    def locs(self):
        return self.args[0]

    @property
    def preferred_loc(self):
        return self.args[1]

    @property
    def message(self):
        return self.args[2]


class EntityUnchanged(Redirection):

    """The requested entity has not changed

    The request was conditional on the corresponding entity having changed
    from some specified state, and the entity has not actually changed from
    that state.  If the client previously cached the entity or some derived
    representation of it, then it may treat that cached data as current,
    modulo any ambiguity in the request's specification of prior state.

    """

    def __init__(self, message=None, *args):
        super(EntityUnchanged, self).__init__(message, *args)

    def __str__(self):
        message = 'entity unchanged from specified state'
        if self.message:
            message += ': {}'.format(self.message)
        return message

    @property
    def message(self):
        return self.args[0]


class ProxyRedirection(Redirection):

    """The request should be repeated through a proxy

    The request was not processed.  The redirection response indicates the
    location of the appropriate proxy.  The client should continue to use
    the original location for future requests for the resource, but it must
    send them through the indicated proxy.  An interactive client may
    automatically request the resource through the indicated proxy without
    user confirmation.

    """

    def __init__(self, loc, message=None, *args):
        super(ProxyRedirection, self).__init__(loc, message, *args)

    def __str__(self):
        message = 'repeat request through proxy at {}'.format(self.loc)
        if self.message:
            message += ': {}'.format(self.message)
        return message

    @property
    def loc(self):
        return self.args[0]

    @property
    def message(self):
        return self.args[1]


class ResourceLocationRedirection(Redirection):

    """The requested resource has been moved

    The request was not processed.  The redirection response indicates the
    resource's new location.

    """

    def __init__(self, qualifier, loc, message=None, *args):
        super(PermanentRedirection, self).__init__(qualifier, loc, message,
                                                   *args)

    def __str__(self):
        message = 'resource moved {} to {}'.format(self.qualifier, self.loc)
        if self.message:
            message += ': {}'.format(self.message)
        return message

    @property
    def loc(self):
        return self.args[1]

    @property
    def message(self):
        return self.args[2]

    @property
    def qualifier(self):
        return self.args[0]


class ResponseRedirection(Redirection):

    """The response can be found at another location

    The request was processed.  The redirection response indicates the
    location of the actual response.  The client should continue to use the
    original location for future requests for the resource.  An interactive
    client may automatically request the actual response at the indicated
    location without user confirmation.

    """

    def __init__(self, loc, message=None, *args):
        super(ResponseRedirection, self).__init__(loc, message, *args)

    def __str__(self):
        message = 'response can be found at {}'.format(self.loc)
        if self.message:
            message += ': {}'.format(self.message)
        return message

    @property
    def loc(self):
        return self.args[0]

    @property
    def message(self):
        return self.args[1]


class PermanentRedirection(ResourceLocationRedirection):
    """The requested resource has been moved permanently

    The request was not processed.  The redirection response indicates the
    resource's new location.  The client should take note of this location
    and use it in all future requests for the resource.  An interactive
    client may automatically request the resource at the new location with
    safe methods, but it must not do so with unsafe methods without user
    confirmation.

    """
    def __init__(self, loc, message=None, *args):
        super(PermanentRedirection, self).__init__('permanently', loc, message,
                                                   *args)


class TemporaryRedirection(ResourceLocationRedirection):
    """The requested resource has been moved temporarily

    The request was not processed.  The redirection response indicates the
    resource's new location.  The client should continue to use the original
    location for future requests for the resource.  An interactive client
    may automatically request the resource at the new location with safe
    methods, but it must not do so with unsafe methods without user
    confirmation.

    """
    def __init__(self, loc, message=None, *args):
        super(TemporaryRedirection, self).__init__('temporarily', loc, message,
                                                   *args)


# general client errors -------------------------------------------------------


class ClientError(Error):
    pass


class BadRequest(ClientError):
    pass


class NoAcceptableMediaType(ClientError):

    def __init__(self, webmethod, response_type=_responses.WebReturnResponse,
                 message=None, acceptable_mediaranges=None,
                 supported_mediatypes=None, *args):
        super(NoAcceptableMediaType, self)\
         .__init__(webmethod, response_type, message, acceptable_mediaranges,
                   supported_mediatypes, *args)

    def __str__(self):

        webmethod_str = \
            '{}.{}.{}'.format(self.webmethod.resource.__class__.__module__,
                              self.webmethod.resource.__class__.__name__,
                              self.webmethod.name)

        message = 'content representation of {} {} is not implemented for any'\
                   ' of the requested media type ranges'\
                   .format(webmethod_str, self.response_type.displayname())
        if self.message:
            message += ': {}'.format(self.message)
        message_extras = []
        if self.acceptable_mediaranges:
            message_extras.append('requested {}'
                                   .format(self.acceptable_mediaranges))
        if self.supported_mediatypes:
            message_extras.append('supported {}'
                                   .format(self.supported_mediatypes))
        if message_extras:
            message += '; ' + ', '.join(message_extras)
        return message

    @property
    def acceptable_mediaranges(self):
        return self.args[3]

    @property
    def message(self):
        return self.args[2]

    @property
    def response_type(self):
        return self.args[1]

    @property
    def supported_mediatypes(self):
        return self.args[4]

    @property
    def webmethod(self):
        return self.args[0]


class ResourceNotFound(ClientError):

    def __init__(self, message=None, *args):
        super(ResourceNotFound, self).__init__(message, *args)

    def __str__(self):
        message = 'resource not found'
        if self.message:
            message += ': {}'.format(self.message)
        return message

    @property
    def message(self):
        return self.args[0]


# general type and value errors -----------------------------------------------


class TypeError(BadRequest, _exceptions.TypeError):
    pass


class ArgPrimTypeError(TypeError):

    def __init__(self, name, type, message=None, expected_type=None, *args):
        super(ArgPrimTypeError, self).__init__(name, type, message,
                                               expected_type, *args)

    def __str__(self):
        message = 'invalid {!r} primitive type {!r}'.format(self.name,
                                                            self.type)
        if self.message:
            message += ': {}'.format(self.message)
        if self.expected_type:
            message += '; expecting ' + self.expected_type
        return message

    @property
    def displayname(self):
        return 'argument type error'

    @property
    def expected_type(self):
        return self.args[3]

    @property
    def message(self):
        return self.args[2]

    @property
    def name(self):
        return self.args[0]

    @property
    def type(self):
        return self.args[1]


class MissingRequiredArgs(TypeError):

    def __init__(self, names, method, *args):
        if not names:
            raise RuntimeError('raised {!r} with no arguments'
                                .format(self.__class__))
        super(MissingRequiredArgs, self).__init__(list(names), method, *args)

    def __str__(self):
        message = 'missing required '
        if len(self.names) > 1:
            message += 'arguments {}'.format(self.names)
        elif len(self.names) == 1:
            message += 'argument {!r}'.format(self.names[0])
        else:
            assert False
        message += ' in method {}'.format(self.method)
        return message

    @property
    def displayname(self):
        name = 'missing required argument'
        if len(self.names) > 1:
            name += 's'
        return name

    @property
    def method(self):
        return self.args[1]

    @property
    def names(self):
        return self.args[0]


class UnexpectedArgs(TypeError):

    def __init__(self, names, method, *args):
        if not names:
            raise RuntimeError('raised {!r} with no arguments'
                                .format(self.__class__))
        super(UnexpectedArgs, self).__init__(list(names), method, *args)

    def __str__(self):
        message = 'unexpected '
        if len(self.names) > 1:
            message += 'arguments {}'.format(self.names)
        elif len(self.names) == 1:
            message += 'argument {!r}'.format(self.names[0])
        else:
            assert False
        message += ' in method {}'.format(self.method)
        return message

    @property
    def displayname(self):
        name = 'unexpected argument'
        if len(self.names) > 1:
            name += 's'
        return name

    @property
    def method(self):
        return self.args[1]

    @property
    def names(self):
        return self.args[0]


class ValueError(BadRequest, _exceptions.ValueError):
    pass


class ArgJsonValueError(ValueError):

    def __init__(self, name, value, message=None, *args):
        super(ArgJsonValueError, self).__init__(name, value, message, *args)

    def __str__(self):
        message = 'invalid {!r} JSON {!r}'.format(self.name, self.value)
        if self.message:
            message += ': {}'.format(self.message)
        return message

    @property
    def displayname(self):
        return 'argument JSON value error'

    @property
    def message(self):
        return self.args[2]

    @property
    def name(self):
        return self.args[0]

    @property
    def value(self):
        return self.args[1]


class ArgPrimValueError(ValueError):

    def __init__(self, name, value, message=None, expected_value=None, *args):
        super(ArgPrimValueError, self).__init__(name, value, message,
                                                expected_value, *args)

    def __str__(self):
        message = 'invalid {!r} primitive {!r}'.format(self.name, self.value)
        if self.message:
            message += ': {}'.format(self.message)
        if self.expected_value:
            message += '; expecting ' + self.expected_value
        return message

    @property
    def displayname(self):
        return 'argument value error'

    @property
    def expected_value(self):
        return self.args[3]

    @property
    def message(self):
        return self.args[2]

    @property
    def name(self):
        return self.args[0]

    @property
    def value(self):
        return self.args[1]


# authentication --------------------------------------------------------------


class AvoidingAuth(Exception):

    def __init__(self, resource, reason=None, *args):
        super(AvoidingAuth, self)\
         .__init__(resource,
                   reason if reason is not None
                          else resource.currently_avoiding_auth_reason,
                   *args)

    def __str__(self):
        message = 'cannot ensure authentication: resource {} is avoiding'\
                   ' authentication'\
                   .format(self.resource)
        if self.reason:
            message += ' ({})'.format(self.reason)
        return message

    @property
    def displayname(self):
        return 'resource is avoiding authentication'

    @property
    def reason(self):
        return self.args[1]

    @property
    def resource(self):
        return self.args[0]


class Unauthenticated(ClientError):

    def __init__(self, message=None, affordances=None, redirection=None,
                 *args):
        super(Unauthenticated, self).__init__(message, affordances,
                                              redirection, *args)

    def __str__(self):
        message = 'request is unauthenticated'
        if self.message:
            message += ': {}'.format(self.message)
        message += '; authentication is required'
        if self.affordances is not None:
            message += ' with affordances {}'.format(self.affordances)
        if self.redirection is not None:
            message += '; authenticate at {}'.format(self.redirection.loc)
            if self.redirection.message:
                message += ' ({})'.format(self.redirection.message)
        return message

    @property
    def affordances(self):
        return self.args[1]

    @property
    def message(self):
        return self.args[0]

    @property
    def redirection(self):
        return self.args[2]


class AuthTokensNotAccepted(Unauthenticated):

    def __init__(self, message=None, *args, **kwargs):
        message_ = 'tokens not accepted'
        if message:
            message_ += ': {}'.format(message)
        super(AuthTokensNotAccepted, self).__init__(message_, *args, **kwargs)

    @property
    def displayname(self):
        return 'authentication tokens not accepted'


class AuthTokensNotGiven(Unauthenticated):

    def __init__(self, message=None, *args, **kwargs):
        message_ = 'no tokens given'
        if message:
            message_ += ': {}'.format(message)
        super(AuthTokensNotGiven, self).__init__(message_, *args, **kwargs)

    @property
    def displayname(self):
        return 'authentication tokens not given'


# denied actions --------------------------------------------------------------


class ActionDenied(ClientError):

    def __init__(self, resource, action, message=None, *args):
        super(ActionDenied, self).__init__(resource, action, message, *args)

    def __str__(self):
        message = 'cannot {} {}'.format(self.action, self.resource)
        if self.message:
            message += ': {}'.format(self.message)
        return message

    @property
    def action(self):
        return self.args[1]

    @property
    def message(self):
        return self.args[2]

    @property
    def resource(self):
        return self.args[0]


class AccessForbidden(ActionDenied):
    def __init__(self, resource, action, message=None, *args):
        message_ = 'access forbidden'
        if message:
            message_ += ': {}'.format(message)
        super(AccessForbidden, self).__init__(resource, action, message_,
                                              *args)


class ResourceConflict(ActionDenied):
    def __init__(self, resource, action, message=None, *args):
        message_ = 'resource state conflict'
        if message:
            message_ += ': {}'.format(message)
        super(ResourceConflict, self).__init__(resource, action, message_,
                                               *args)


# cross-origin resource sharing -----------------------------------------------


class CorsRequestRejected(AccessForbidden):

    def __init__(self, resource, origin, reason=None, message=None,
                 cors_request_type=None, affordances=None, *args):
        super(CorsRequestRejected, self).__init__(resource, origin, reason,
                                                  message, cors_request_type,
                                                  affordances, *args)

    def __str__(self):
        message = '{} by {} from origin {!r}'.format(self.base_message,
                                                     self.resource,
                                                     self.origin)
        if self.reason:
            message += ': ' + self.reason
        if self.message:
            message += ': ' + self.message
        # CAVEAT: do not expose the affordances, since this could be a security
        #   vulnerability
        return message

    @property
    def affordances(self):
        return self.args[5]

    @property
    def base_message(self):
        message = 'cross-origin'
        if self.cors_request_type:
            message += ' {}'.format(self.cors_request_type)
        message += ' request rejected'
        return message

    @property
    def cors_request_type(self):
        return self.args[4]

    @property
    def displayname(self):
        return self.base_message

    @property
    def message(self):
        return self.args[3]

    @property
    def origin(self):
        return self.args[1]

    @property
    def reason(self):
        return self.args[2]

    @property
    def resource(self):
        return self.args[0]


class CorsHeadersForbidden(CorsRequestRejected):

    def __init__(self, resource, origin, forbidden_headers, *args, **kwargs):
        super(CorsHeadersForbidden, self)\
         .__init__(resource, origin,
                   'headers {} forbidden'.format(list(forbidden_headers)),
                   *args, **kwargs)
        self._forbidden_headers = forbidden_headers

    @property
    def forbidden_headers(self):
        return self._forbidden_headers

    @property
    def displayname(self):
        return 'cross-origin request headers forbidden'


class CorsMethodForbidden(CorsRequestRejected):

    def __init__(self, resource, origin, method, *args, **kwargs):
        super(CorsMethodForbidden, self)\
         .__init__(resource, origin, 'method {!r} forbidden'.format(method),
                   *args, **kwargs)
        self._method = method

    @property
    def displayname(self):
        return 'cross-origin request method forbidden'

    @property
    def method(self):
        return self._method


class CorsOriginForbidden(CorsRequestRejected):

    def __init__(self, resource, origin, *args, **kwargs):
        super(CorsOriginForbidden, self).__init__(resource, origin,
                                                  'origin forbidden', *args,
                                                  **kwargs)

    @property
    def displayname(self):
        return 'cross-origin request origin forbidden'


class CorsPolicyUndefined(CorsRequestRejected):

    def __init__(self, resource, origin, message=None, *args):
        super(CorsPolicyUndefined, self)\
         .__init__(resource,
                   origin,
                   'no cross-origin sharing policy is defined for this'
                   ' resource',
                   message,
                   *args)

    @property
    def displayname(self):
        return 'cross-origin resource sharing policy undefined'


# server errors ---------------------------------------------------------------


class ServerError(Error):
    pass


class InternalServerError(ServerError):
    pass


class NotImplementedError(ServerError):

    def __init__(self, object, message=None, *args):
        super(WebMethodNotImplemented, self).__init__(object, message, *args)

    def __str__(self):
        message = '{} is not implemented'.format(self.object)
        if self.message:
            message += ': {}'.format(self.message)
        return message

    @property
    def message(self):
        return self.args[1]

    @property
    def object(self):
        return self.args[0]


class WebMethodNotImplemented(NotImplementedError):

    def __init__(self, webmethod, allowed_webmethods, message=None, *args):
        allowed_webmethods = sorted(allowed_webmethods)
        super(WebMethodNotImplemented, self)\
         .__init__('web method {!r}'.format(webmethod), message, webmethod,
                   allowed_webmethods, *args)

    def __str__(self):
        message = super(WebMethodNotImplemented, self).__str__()
        message += '; allowed web methods are {}'\
                    .format(self.allowed_webmethods)
        return message

    @property
    def allowed_webmethods(self):
        return self.args[3]

    @property
    def webmethod(self):
        return self.args[2]


class UnhandledException(ServerError):

    """
    An unhandled exception was encountered in the implementation of the
    server

    :param Exception exc:
        The unhandled exception.

    :param str traceback:
        The traceback at the point of the exception, formatted as a string.

    :param bool show_unhandled:
        Whether to show the exception as an "unhandled" exception in string
        representations of this object.  If :obj:`False`, this object's
        string representations mimic those of *exc*.

    """

    def __init__(self, exc, traceback=None, show_unhandled=True, *args):
        super(UnhandledException, self)\
         .__init__(exc, traceback,
                   _metadata.ExceptionInfo.fromexc(exc, traceback),
                   show_unhandled, *args)

    def __str__(self):
        return ('unhandled exception: ' if self.show_unhandled else '') \
               + str(self.exc)

    @property
    def displayname(self):
        return ('unhandled ' if self.show_unhandled else '') \
               + self.exc_info.displayname

    @property
    def exc(self):
        return self.args[0]

    @property
    def exc_args(self):
        return self.exc.args

    @property
    def exc_info(self):
        return self.args[2]

    @property
    def show_unhandled(self):
        return self.args[3]

    @property
    def traceback(self):
        return self.args[1]


# misc ------------------------------------------------------------------------


class InvalidServiceOperation(Error):

    def __init__(self, service, operation, message=None, *args):
        super(InvalidServiceOperation, self).__init__(service, operation,
                                                      message, *args)

    def __str__(self):
        message = 'cannot {} service {!r}'.format(self.operation, self.service)
        if self.message:
            message += ': ' + self.message
        return message

    @property
    def message(self):
        return self.args[2]

    @property
    def operation(self):
        return self.args[1]

    @property
    def service(self):
        return self.args[0]
