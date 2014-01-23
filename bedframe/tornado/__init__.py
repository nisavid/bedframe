"""Tornado support

These objects provide support for service implementations based on
:pypi:`Tornado`.

.. seealso:: :mod:`Tornado authentication <bedframe.auth.tornado>`

"""

__copyright__ = "Copyright (C) 2014 Ivan D Vasin"
__docformat__ = "restructuredtext"

import pkg_resources as _pkg_resources

try:
    _pkg_resources.require('bedframe [tornado]')
except _pkg_resources.ResolutionError:
    pass
else:
    from ._common import *
    from ._handlers import *
    from ._services import *
