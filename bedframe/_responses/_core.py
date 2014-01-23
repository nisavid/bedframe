"""Responses core"""

__copyright__ = "Copyright (C) 2014 Ivan D Vasin"
__docformat__ = "restructuredtext"

from spruce.collections import typedodict as _typedodict
from spruce.lang import enum as _enum


WebResponseFacetType = _enum('web response facet type',
                             ('return', 'children', 'auth_info', 'exc',
                              'proxy_redirect', 'resource_redirect',
                              'choice_redirect', 'response_redirect'))


OmniWebResponseFacetType = _enum('universal web response facet type',
                                 ('auth_info',))


class web_response_facettype_enum(_enum):
    def __init__(self, enum_displayname, values, **kwargs):
        values = tuple(values) + tuple(OmniWebResponseFacetType.enum_values)
        super(web_response_facettype_enum, self).__init__(enum_displayname,
                                                          values, **kwargs)


class WebResponse(object):

    """A web response

    This is a response to a web service request.

    :param data:
        The data that specifies the response.
    :type data: {:class:`WebResponseFacetType`: :class:`WebResponseFacet`}

    :param content:
        The response's content.
    :type content: :obj:`unicode` or null

    """

    def __init__(self, data, content=None):
        self._content = content
        self._data = WebResponseData(data)

    @property
    def content(self):
        """The response's content

        :type: :obj:`unicode` or null

        """
        return self._content

    @classmethod
    def displayname(cls):
        return 'web response'

    @property
    def data(self):
        return self._data

    @classmethod
    def fromdata(cls, data, content=None):
        """Create a response that contains some given data

        The class of the resulting response is specified by
        :samp:`{data}.response_type`.

        :param data:
            The data that is contained in the response.
        :type data:
            {:class:`WebResponseFacetType`: :class:`WebResponseFacet`}

        :param content:
            The response's content.
        :type content: :obj:`unicode` or null

        :rtype: :class:`WebResponse`

        """
        return data.response_type(data, content)

    @property
    def mediatype(self):
        """The media type of the response's content

        :type: :obj:`str` or null

        """
        return self.data.mediatype


class WebResponseFacet(object):

    """A web response facet

    :param mediatype:
        The media type of the response's content.
    :type mediatype: :obj:`str` or null

    """

    def __init__(self, mediatype=None):
        self._mediatype = mediatype

    @property
    def mediatype(self):
        return self._mediatype


class WebResponseFacetMap(_typedodict):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault('keytype', WebResponseFacetType)
        kwargs.setdefault('valuetype', WebResponseFacet)
        kwargs.setdefault('value_converter', False)
        super(WebResponseFacetMap, self).__init__(*args, **kwargs)


class WebResponseData(WebResponseFacetMap):

    """The data that specify a web response

    :param mediatype:
        The media type of the response's content.
    :type mediatype: :obj:`str` or null

    """

    def __init__(self, mapping_or_items=None, mediatype=None, **kwargs):

        super(WebResponseData, self).__init__(mapping_or_items, **kwargs)

        if mediatype is None:
            try:
                mediatype = mapping_or_items.mediatype
            except AttributeError:
                pass
        self._mediatype = mediatype

    @property
    def mediatype(self):
        return self._mediatype

    response_type = WebResponse
