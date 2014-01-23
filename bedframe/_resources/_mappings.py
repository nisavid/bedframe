"""Web resource mappings"""

__copyright__ = "Copyright (C) 2014 Ivan D Vasin"
__docformat__ = "restructuredtext"

import re as _re

from spruce.lang import subclass_of as _subclass_of

from .. import _collections as _coll
from .. import _methods as _meth
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

    @property
    def _args_clauses_pattern(self):
        return '(?:[{}][^{}]*)'.format(''.join((self.ordered_arg_sep,
                                                self.unordered_arg_sep)),
                                       self.pathsep)

    def _setitem(self, key, value):
        init_meth = value.__init__
        if isinstance(init_meth, _meth.WebMethod):
            pattern = self._key_pattern(key)
            key_base = pattern
            key_ending = ''
            for ending in (self.pathsep, self.pathsep + '?'):
                if pattern.endswith(ending):
                    key_base = pattern[:-len(ending)]
                    key_ending = ending
                    break

            # XXX: there's no clean, correct way to do this using this approach
            # FIXME: reimplement or replace this class so that resources are
            #     explicitly organized in a tree and there is no question about
            #     which path parts might take arguments (since that is then the
            #     set of terminal path parts of all resources)
            key = ''
            pathpart_sep_re = _re.compile(r'(?=.)/(?![^\[\]]*(?<!\\)\])')
            prev_pathpart_end = 0
            for pathpart_sep_match in pathpart_sep_re.finditer(key_base):
                key += key_base[prev_pathpart_end:pathpart_sep_match.start()] \
                       + self._args_clauses_pattern + '?' \
                       + pathpart_sep_match.group(0)
                prev_pathpart_end = pathpart_sep_match.end()
            key += key_base[prev_pathpart_end:] \
                   + self._args_clauses_pattern + '?' + key_ending
        super(WebResourceMap, self)._setitem(key, value)
