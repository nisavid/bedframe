"""Collections"""

__copyright__ = "Copyright (C) 2014 Ivan D Vasin"
__docformat__ = "restructuredtext"

import re as _re

from spruce.collections import typedodict as _typedodict
from spruce.lang \
    import bool as _bool, regex as _regex, regex_class as _regex_class


class WebResourcePathMapping(_typedodict):

    """A mapping keyed by web resource locations

    .. note:: **TODO:**
        generalize to notions of resource location other than URI path

    """

    def __init__(self,
                 mapping_or_items=None,
                 auto_optional_trailing_pathsep=True,
                 pathsep='/',
                 pathterms=('?', '#', '[', ']'),
                 ordered_arg_sep='&',
                 unordered_arg_sep=';',
                 **kwargs):
        self._auto_optional_trailing_pathsep = auto_optional_trailing_pathsep
        self._ordered_arg_sep = ordered_arg_sep
        self._pathsep = pathsep
        self._pathterms = pathterms
        self._unordered_arg_sep = unordered_arg_sep
        kwargs.setdefault('keytype', _regex_class)
        kwargs.setdefault('key_converter', _regex)
        super(WebResourcePathMapping, self).__init__(mapping_or_items,
                                                     **kwargs)

    @property
    def argseps(self):
        return ''.join((self.ordered_arg_sep, self.unordered_arg_sep))

    @property
    def auto_optional_trailing_pathsep(self):
        return self._auto_optional_trailing_pathsep

    @auto_optional_trailing_pathsep.setter
    def auto_trailing_pathsep(self, value):
        self._auto_optional_trailing_pathsep = _bool(value)

    @property
    def ordered_arg_sep(self):
        return self._ordered_arg_sep

    @property
    def pathsep(self):
        return self._pathsep

    @property
    def pathterms(self):
        return self._pathterms

    @property
    def seps(self):
        return ''.join(self.pathterms
                        + (self.pathsep, self.ordered_arg_sep,
                           self.unordered_arg_sep))

    @property
    def unordered_arg_sep(self):
        return self._unordered_arg_sep

    def _key_pattern(self, key):
        try:
            return key.pattern
        except AttributeError:
            return unicode(key)

    def _setitem(self, key, value):
        if self.auto_optional_trailing_pathsep:
            pattern = self._key_pattern(key)
            if not any(pattern.endswith(ending)
                       for ending in (self.pathsep, self.pathsep + '?')):
                key = '{}{}?'.format(pattern, self.pathsep)
        super(WebResourcePathMapping, self)._setitem(key, value)


class HereditaryWebResourcePathMapping(WebResourcePathMapping):

    """A hereditary resource path mapping

    .. seealso:: :class:`WebResourcePathMapping`

    """

    def __contains__(self, loc):
        return bool(self.loc_lineage(loc))

    def __getitem__(self, loc):
        lineage = self.loc_lineage(loc)
        if not lineage:
            raise KeyError('no mapped web resource location is an ancestor of'
                            ' {!r}'.format(loc))
        return self._flatten_lineage(lineage)

    def __repr__(self):
        return '{}({!r}, keytype={!r}, valuetype={!r})'\
                .format(self.__class__.__name__,
                        '({})'.format(', '.join('({!r}, {!r})'
                                                 .format(loc_re.pattern, value)
                                                for loc_re, value in
                                                self.items())),
                        self.keytype,
                        self.valuetype)

    def __str__(self):
        return '>{{{}}}'.format(', '.join('{!r}: {}'.format(loc_re.pattern,
                                                            value)
                                          for loc_re, value
                                          in self.items()))

    def items(self):
        return [(loc_re,
                 super(HereditaryWebResourcePathMapping, self)
                     .__getitem__(loc_re))
                for loc_re in self]

    def iter_loc_lineage(self, loc):
        for self_loc in sorted(sorted(self,
                                      key=(lambda loc: len(loc.pattern))),
                               key=(lambda loc:
                                    loc.pattern.count(self.pathsep))):
            if any(self_loc.pattern.endswith(sep)
                   for sep in (self.pathsep, self.unordered_arg_sep,
                               self.ordered_arg_sep)):
                self_loc_ancestor_pattern = self_loc.pattern
            else:
                self_loc_ancestor_pattern = \
                    self_loc.pattern \
                    + '(?:{}.+)?$'\
                       .format('(?:{})'
                                .format('|'.join((self.pathsep,
                                                  self.unordered_arg_sep,
                                                  self.ordered_arg_sep))))
            if _re.match(self_loc_ancestor_pattern, loc):
                yield (self_loc,
                       super(HereditaryWebResourcePathMapping, self)
                           .__getitem__(self_loc))

    def loc_lineage(self, loc):
        return list(self.iter_loc_lineage(loc))

    def locs(self, value):
        return [loc for loc, loc_value in self.items() if loc_value == value]

    def _flatten_lineage(self, lineage):
        return max(((loc_re.pattern, value) for loc_re, value in lineage),
                   key=(lambda item: item[0].count(self.pathsep)))\
                   [1]
