"""Return responses"""

__copyright__ = "Copyright (C) 2014 Ivan D Vasin"
__docformat__ = "restructuredtext"

from . import _authinfo as _authinfo_responses
from . import _core as _responses_core


WebReturnResponseFacetType = \
    _responses_core.web_response_facettype_enum\
     ('web return response facet type', ('return',))


class WebReturnResponse(_responses_core.WebResponse):
    """A web return response

    This type of response indicates a return from a function.

    """
    pass


class WebReturnResponseData(_responses_core.WebResponseData):

    """The data that specifies a return response"""

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('keytype', WebReturnResponseFacetType)
        super(WebReturnResponseData, self).__init__(*args, **kwargs)

    @classmethod
    def fromvalue(cls, value, request_args=None, mediatype=None,
                  auth_info=None, **kwargs):

        data = {}

        data[WebReturnResponseFacetType('return')] = \
            WebReturnResponseFacet(value, request_args=request_args,
                                   mediatype=mediatype, **kwargs)

        if auth_info:
            data[WebReturnResponseFacetType('auth_info')] = \
                _authinfo_responses.WebAuthInfoResponseFacet\
                 (auth_info, mediatype=mediatype, **kwargs)

        return cls(data, mediatype=mediatype)

    response_type = WebReturnResponse


class WebReturnResponseFacet(_responses_core.WebResponseFacet):

    def __init__(self, value, request_args=None, **kwargs):
        super(WebReturnResponseFacet, self).__init__(**kwargs)
        self._request_args = request_args.copy() if request_args else {}
        self._value = value

    @property
    def request_args(self):
        return self._request_args

    @property
    def value(self):
        return self._value
