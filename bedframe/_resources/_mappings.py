"""Web resource mappings"""

__copyright__ = "Copyright (C) 2014 Ivan D Vasin"
__docformat__ = "restructuredtext"

from spruce.lang import subclass_of as _subclass_of

from .. import _collections as _coll
from . import _core as _resources_core


class WebResourceMap(_coll.WebResourcePathMapping):

    """A web resource map

    This is a mapping from resource path patterns to web resource classes.
    In addition to the basic mutable mapping functionality, it also

      * accepts path patterns in the form of strings or regular
        expressions and

      * ensures that that its items have valid types and values.

    :param mapping_or_items:
        A mapping or item sequence of initial items.
    :type mapping_or_items:
        ~{~\\ :obj:`re`:
              ^\\ :class:`bedframe.WebResource \
                          <bedframe._resources._core.WebResource>`}

    """

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('valuetype',
                          _subclass_of(_resources_core.WebResource,
                                       'web resource class'))
        kwargs.setdefault('value_converter', False)
        super(WebResourceMap, self).__init__(*args, **kwargs)
