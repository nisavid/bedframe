"""Tornado authentication.

These objects provide support for authentication for service
implementations based on :pypi:`Tornado`.

.. seealso:: :mod:`Tornado support <bedframe.tornado>`

"""

__copyright__ = "Copyright (C) 2013 Ivan D Vasin and Cogo Labs"
__docformat__ = "restructuredtext"

from ._basic import *
from ._digest import *
from ._session import *
from ._std_http import *
