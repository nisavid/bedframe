"""Tornado support

These objects provide support for service implementations based on
:pypi:`Tornado`.

.. seealso:: :mod:`Tornado authentication <bedframe.auth.tornado>`

"""

__copyright__ = "Copyright (C) 2014 Ivan D Vasin"
__docformat__ = "restructuredtext"

import pkg_resources as _pkg_resources

_enable = False
try:
    _pkg_resources.require('bedframe [tornado]')
except _pkg_resources.ResolutionError:
    try:
        _pkg_resources.require('bedframe [tornado_wsgi]')
    except _pkg_resources.ResolutionError:
        pass
    else:
        _enable = True
else:
    _enable = True
if _enable:
    from ._common import *
    from ._handlers import *
    from ._services import *
