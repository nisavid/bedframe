"""Exception responses"""

__copyright__ = "Copyright (C) 2014 Ivan D Vasin"
__docformat__ = "restructuredtext"

from .. import _metadata
from . import _authinfo as _authinfo_responses
from . import _core as _responses_core


WebExceptionResponseFacetType = \
    _responses_core.web_response_facettype_enum\
     ('web exception response facet type', ('exc',))


class WebExceptionResponse(_responses_core.WebResponse):
    """A web exception response

    This type of response indicates a raised exception.

    """
    pass


class WebExceptionResponseData(_responses_core.WebResponseData):

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('keytype', WebExceptionResponseFacetType)
        super(WebExceptionResponseData, self).__init__(*args, **kwargs)

    @classmethod
    def fromexc(cls, exc, traceback, debug_flags, mediatype=None,
                auth_info=None, **kwargs):

        data = {}

        data[WebExceptionResponseFacetType('exc')] = \
            WebExceptionResponseFacet.fromexc(exc, traceback,
                                              debug_flags=debug_flags,
                                              mediatype=mediatype, **kwargs)

        if auth_info:
            data[WebExceptionResponseFacetType('auth_info')] = \
                _authinfo_responses.WebAuthInfoResponseFacet\
                 (auth_info, mediatype=mediatype, **kwargs)

        return cls(data, mediatype=mediatype)

    response_type = WebExceptionResponse


class WebExceptionResponseFacet(_responses_core.WebResponseFacet):

    """The data that specifies an exception response"""

    # FIXME: get rid of __init__(..., exc, ...) and :attr:`_exc`; see the
    #   corresponding FIXME in :mod:`bedframe._services._tornado`

    def __init__(self, exc, traceback, debug_flags, class_def_module, name,
                 displayname=None, message=None, args=(), **kwargs):
        super(WebExceptionResponseFacet, self).__init__(**kwargs)
        self._args = args
        self._class_def_module = class_def_module
        self._debug_flags = debug_flags
        self._displayname = displayname
        self._exc_ = exc
        self._message = message
        self._name = name
        self._traceback = traceback

    @property
    def args(self):
        return self._args

    @property
    def class_def_module(self):
        return self._class_def_module

    @property
    def debug_flags(self):
        return self._debug_flags

    @property
    def displayname(self):
        return self._displayname

    @classmethod
    def fromexc(cls, exc, traceback, debug_flags, mediatype=None):
        exc_info = _metadata.ExceptionInfo.fromexc(exc, traceback)
        return WebExceptionResponseFacet\
                (exc=exc,
                 traceback=exc_info.traceback,
                 debug_flags=debug_flags,
                 class_def_module=exc_info.class_def_info.module,
                 name=exc_info.class_def_info.name,
                 displayname=exc_info.displayname,
                 message=exc_info.message,
                 args=[repr(arg) for arg in exc_info.args],
                 mediatype=mediatype)

    @property
    def message(self):
        return self._message

    @property
    def name(self):
        return self._name

    @property
    def traceback(self):
        return self._traceback

    @property
    def _exc(self):
        return self._exc_
