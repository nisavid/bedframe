"""HTTP authentication.

These objects provide support for authentication on an HTTP server.

.. seealso:: :mod:`HTTP <bedframe.http>`

"""

__copyright__ = "Copyright (C) 2013 Ivan D Vasin and Cogo Labs"
__docformat__ = "restructuredtext"

from ._basic import *
from ._digest import *
from ._session import *
from ._std import *
