"""Web methods"""

__copyright__ = "Copyright (C) 2014 Ivan D Vasin"
__docformat__ = "restructuredtext"

from hashlib import md5 as _md5
from inspect import getargspec as _getargspec
import logging as _logging
import sys as _sys

from . import _debug
from . import _exc
from . import _responses
from . import webtypes as _webtypes


def disallowed_webmethod(func):
    return DisallowedWebMethod(func)


def webmethod(returntype=_webtypes.null, **argtypes):
    def inner(func):
        return WebMethod(func, returntype, argtypes)
    return inner


class TypedWebMethod(object):

    def __init__(self, general, mediaranges):
        self._general = general
        self._mediaranges = mediaranges

    def __call__(self, **args_prims):
        try:
            mediatype = self.best_mediatype()

            argnames = set(args_prims.keys())
            missing_argnames = set(self.required_argnames) - argnames
            if missing_argnames:
                raise _exc.MissingRequiredArgs(list(sorted(missing_argnames)),
                                               method=self)

            if self.kwargs_type is None:
                expected_argnames = set(self.argnames)
                unexpected_argnames = argnames - expected_argnames
                if unexpected_argnames:
                    raise _exc.UnexpectedArgs\
                           (list(sorted(unexpected_argnames)),
                            method=self)

            args = {}
            args_native = {}

            for name, arg_prim in args_prims.items():
                try:
                    argtype = self.argtypes[name]
                except KeyError:
                    argtype = self.kwargs_type
                    assert argtype

                try:
                    arg = argtype.fromprim(arg_prim)
                except (AttributeError, TypeError) as exc:
                    raise _exc.ArgPrimTypeError(name, arg_prim.__class__,
                                                str(exc))
                except ValueError as exc:
                    raise _exc.ArgPrimValueError(name, arg_prim, str(exc))

                args[name] = arg
                args_native[name] = arg.native()

            if self.ispartial:
                args_native['$mediaranges'] = self.mediaranges

            retval_native = self.func(self.resource, **args_native)

            if self.returns_response:
                if self.returntype:
                    retval = self.returntype(retval_native)
                else:
                    retval = _webtypes.null(None)
                auth_info = self.resource.current_auth_info
                return self.response_fromdata\
                        (_responses.WebReturnResponseData
                          .fromvalue(retval, mediatype=mediatype,
                                     request_args=args, auth_info=auth_info))
            else:
                return retval_native

        except Exception as exc:
            raise _exc.WebMethodException\
                   (self, exc, _sys.exc_info()[2],
                    traceback_entries_filter=
                        self._method_code_traceback_entries)

    def __getattr__(self, name):
        try:
            return getattr(self._general, name)
        except AttributeError as exc:
            try:
                return object.__getattr__(self, name)
            except AttributeError:
                raise exc

    def __repr__(self):
        return repr(self._general)

    def best_mediatype(self, response_type=_responses.WebReturnResponse):
        mediatypes = self.supported_mediatypes(response_type=response_type)
        try:
            return iter(mediatypes).next()
        except StopIteration:
            raise _exc.NoAcceptableMediaType\
                   (self,
                    response_type,
                    acceptable_mediaranges=self.mediaranges,
                    supported_mediatypes=
                        self.general.supported_mediatypes(response_type=
                                                              response_type))

    def etag(self, **args_prims):
        return self.general.variant_etag(_mediatype=self.best_mediatype(),
                                         **args_prims)

    @property
    def general(self):
        return self._general

    @property
    def mediaranges(self):
        return self._mediaranges

    def response_fromdata(self, data):
        content = self.response_content(data)
        return _responses.WebResponse.fromdata(data, content)

    def response_fromexc(self, exc, traceback, debug_flags):

        try:
            auth_info = self.resource.current_auth_info
        # CAVEAT: some ``resource`` attributes may be uninitialized if ``exc``
        #   was raised from/for ``resource.__init__()``
        except AttributeError:
            auth_info = None

        try:
            mediatype = \
                self.best_mediatype(response_type=
                                        _responses.WebExceptionResponse)
        except _exc.NoAcceptableMediaType as new_exc:
            webmethod_str = '{}.{}.{}'.format(self.resource.__module__,
                                              self.resource.__class__.__name__,
                                              self.name)
            message = 'no acceptable {} exception response content'\
                       ' representation; original exception:\n{}'\
                       .format(webmethod_str, exc)
            if traceback:
                message += '\n' + traceback
            _logging.error(message)

            data = _responses.WebExceptionResponseData\
                    .fromexc(new_exc, traceback=traceback,
                             debug_flags=debug_flags, auth_info=auth_info)
            return _responses.WebResponse.fromdata(data)
        else:
            try:
                effective_exc = exc.redirection
            except AttributeError:
                effective_exc = exc
            else:
                if not effective_exc:
                    effective_exc = exc

            if isinstance(effective_exc, _exc.ResponseRedirection):
                data = _responses.WebResponseRedirectionResponseData\
                        .fromexc(effective_exc, traceback=traceback,
                                 debug_flags=debug_flags, mediatype=mediatype,
                                 auth_info=auth_info)
            else:
                data = _responses.WebExceptionResponseData\
                        .fromexc(effective_exc, traceback=traceback,
                                 debug_flags=debug_flags, mediatype=mediatype,
                                 auth_info=auth_info)
            return self.response_fromdata(data)

    def supported_mediatypes(self, response_type=_responses.WebReturnResponse):
        for mediarange in self.mediaranges:
            for mediatype \
                    in self._general\
                           .supported_mediatypes(response_type=response_type):
                if self._mediarange_matches_type(mediarange, mediatype):
                    yield mediatype

    @classmethod
    def _mediarange_matches_type(self, mediarange, mediatype):
        range_name, _, _ = mediarange.partition(';')
        range_major, range_minor = range_name.split('/', 1)
        type_major, type_minor = mediatype.split('/', 1)
        return (range_major == '*' or range_major == type_major) \
               and (range_minor == '*' or range_minor == type_minor)

    def _method_code_traceback_entries(self, traceback_entries, debug_flags):
        if _debug.DEBUG_EXC_TRACEBACK in debug_flags:
            if _debug.DEBUG_EXC_TRACEBACK_INCLUDING_RESOURCE_CODE \
                   in debug_flags:
                return traceback_entries
            else:
                return traceback_entries[1:]
        else:
            return ()


class WebMethod(object):

    def __init__(self, func, returntype=_webtypes.null, argtypes=None):

        if not _getargspec(func).args:
            raise TypeError('{} func must take at least one argument (the'
                             ' \'self\' reference to its resource)'
                             .format(self.__class__.__name__))

        self._argtypes = argtypes.copy() if argtypes else {}
        self._func = func
        self._resource = None
        self._resource_class = None
        self._response_content_funcs_own = {}
        self._returntype = returntype

    def __get__(self, instance, owner):
        if instance:
            self._resource = instance
        self._resource_class = owner
        return self

    def __call__(self, **args_prims):
        return self.withtypes((self.DEFAULT_MEDIA_TYPE,))(**args_prims)

    def __repr__(self):
        if self.resource:
            return '{!r}.{}'.format(self.resource, self.name)
        elif self.resource_class:
            return '{}.{}'.format(self.resource_class.__name__, self.name)
        else:
            return self.name

    @property
    def argdefaults(self):
        argspec = _getargspec(self.func)
        return dict(zip(reversed(argspec.args),
                        reversed(argspec.defaults or ())))

    @property
    def argnames(self):
        return self.argtypes.keys()

    @property
    def argtypes(self):
        return self._argtypes

    @property
    def current_debug_flags(self):
        return self.resource.current_debug_flags

    DEFAULT_MEDIA_TYPE = 'application/json'

    def etagger(self, mediatype):
        def set_ettagger(func):
            self._etaggers_own[mediatype] = func
            return self
        return set_ettagger

    @property
    def func(self):
        return self._func

    @property
    def ispartial(self):
        return False

    @property
    def kwargs_argname(self):
        return _getargspec(self.func).keywords

    @property
    def kwargs_type(self):
        return self.argtypes.get(self.kwargs_argname, None)

    @property
    def name(self):
        return self.func.__name__

    def partial(self, *args, **kwargs):
        def func(resource, *args_, **kwargs_):

            mediaranges = kwargs_.pop('$mediaranges', None)

            args__ = args + args_
            kwargs__ = kwargs.copy()
            kwargs__.update(kwargs_)

            meth = getattr(self.resource_class, self.name)
            meth._resource = resource
            meth._resource_class = resource.__class__
            if mediaranges is not None:
                return meth.withtypes(mediaranges)(*args__, **kwargs__)
            else:
                return meth(*args__, **kwargs__)
        func.__name__ = self.name
        meth = PartialWebMethod(self, func, self.returntype, self.argtypes)
        return meth

    @property
    def required_argnames(self):
        argspec = _getargspec(self.func)
        # trim ``self`` off the beginning, defaultable args off the end
        return argspec.args[1:][:-len(argspec.defaults or ())]

    @property
    def resource(self):
        return self._resource

    @property
    def resource_class(self):
        return self._resource_class

    def response_content(self, data):
        response_content = self._response_content_funcs[(data.mediatype,
                                                         data.response_type)]
        if issubclass(data.response_type, _responses.WebReturnResponse):
            return_facet = data['return']
            return response_content(self.resource, return_facet.value,
                                    **return_facet.request_args)
        else:
            return response_content(self.resource, data)

    @property
    def returntype(self):
        return self._returntype

    @property
    def returns_response(self):
        return self.name != '__init__'

    def supported_mediatypes(self, response_type=_responses.WebReturnResponse):
        return [mediatype
                for mediatype, other_response_type
                in self._response_content_funcs
                if other_response_type is response_type]

    def type(self, mediatype, response_type=_responses.WebReturnResponse):
        def set_response_content_func(func):
            self._response_content_funcs_own[(mediatype, response_type)] = func
            return self
        return set_response_content_func

    def variant_etag(self, _mediatype, **args_prims):
        try:
            etagger = self._etaggers[_mediatype]
        except KeyError:
            etagger = self._default_etagger
        try:
            return etagger(self.resource, _mediatype=_mediatype, **args_prims)
        except _exc.WebMethodException as exc:
            raise exc.exc, None, exc.orig_raw_traceback

    def withtypes(self, mediaranges):
        return TypedWebMethod(self, mediaranges)

    def _default_etagger(self, resource, _mediatype, **args_prims):
        return _md5(self.withtypes((_mediatype,))(**args_prims).content)

    @property
    def _etaggers(self):
        funcs = {}
        for resource_ancestor_class \
                in reversed(self.resource.__class__.__mro__):
            try:
                ancestor_webmethod = getattr(resource_ancestor_class,
                                             self.name)
                funcs.update(ancestor_webmethod._etaggers_own)
            except AttributeError:
                pass
        return funcs

    @property
    def _response_content_funcs(self):
        funcs = {}
        for resource_ancestor_class in reversed(self.resource_class.__mro__):
            try:
                ancestor_webmethod = getattr(resource_ancestor_class,
                                             self.name)
                funcs.update(ancestor_webmethod._response_content_funcs_own)
            except AttributeError:
                pass
        return funcs


class DisallowedWebMethod(WebMethod):
    @property
    def func(self):
        def func_(resource, **args_prims):
            raise _exc.MethodNotAllowed\
                   (self.name,
                    allowed_methods=self.resource.allowed_webmethodnames)
        return func_


class PartialWebMethod(WebMethod):

    def __init__(self, unpartial, *args, **kwargs):
        super(PartialWebMethod, self).__init__(*args, **kwargs)
        self._unpartial = unpartial

    @property
    def ispartial(self):
        return True

    @property
    def unpartial(self):
        return self._unpartial
