"""Redirection responses"""

__copyright__ = "Copyright (C) 2014 Ivan D Vasin"
__docformat__ = "restructuredtext"

from . import _authinfo as _authinfo_responses
from . import _core as _responses_core
from . import _exc as _exc_responses


WebResponseRedirectionResponseFacetType = \
    _responses_core.web_response_facettype_enum\
     ('web redirection response facet type', ('exc', 'response_redirect'))


class WebResponseRedirectionResponse(_responses_core.WebResponse):
    """A response redirection response

    This type of response indicates a response redirection.

    .. seealso:: :exc:`~bedframe._exc.ResponseRedirection`

    """
    pass


class WebResponseRedirectionResponseData(_responses_core.WebResponseData):

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('keytype', WebResponseRedirectionResponseFacetType)
        super(WebResponseRedirectionResponseData, self).__init__(*args,
                                                                 **kwargs)

    @classmethod
    def fromexc(cls, exc, traceback, debug_flags, mediatype=None,
                auth_info=None, **kwargs):

        data = {}

        data[WebResponseRedirectionResponseFacetType('exc')] = \
            _exc_responses.WebExceptionResponseFacet\
             .fromexc(exc, traceback, debug_flags=debug_flags,
                      mediatype=mediatype, **kwargs)

        data[WebResponseRedirectionResponseFacetType('response_redirect')] = \
            WebResponseRedirectionResponseFacet\
             .fromexc(exc, traceback, debug_flags=debug_flags,
                      mediatype=mediatype, **kwargs)

        if auth_info:
            data[WebResponseRedirectionResponseFacetType('auth_info')] = \
                _authinfo_responses.WebAuthInfoResponseFacet\
                 (auth_info, mediatype=mediatype, **kwargs)

        return cls(data, mediatype=mediatype)

    response_type = WebResponseRedirectionResponse


class WebResponseRedirectionResponseFacet(_responses_core.WebResponseFacet):

    """The data that specifies a response redirection response"""

    def __init__(self, loc, message=None, **kwargs):
        super(WebResponseRedirectionResponseFacet, self).__init__(**kwargs)
        self._loc = loc
        self._message = message

    @classmethod
    def fromexc(cls, exc, traceback, debug_flags, mediatype=None):
        return WebResponseRedirectionResponseFacet(loc=exc.loc,
                                                   message=exc.message,
                                                   mediatype=mediatype)

    @property
    def loc(self):
        return self._loc

    @property
    def message(self):
        return self._message
