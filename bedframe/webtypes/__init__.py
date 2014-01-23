"""Web-transmittable data types

An object of one of these classes wraps an object of the corresponding
:term:`native` type.  It provides a means to convert the native object
to a form that can be transmitted via web communications.  The recipient
can then use the transmitted object as received or convert it back to
its native type.

.. seealso:: :class:`~bedframe.webtypes._core.webobject`


Glossary
--------
.. glossary::
    :sorted:

    native
      A native type is a data type that is used in application code on
      the client and server side.

      A native object is an instance of a native type.

    primitive
      These are the primitive types:

        * :obj:`types.NoneType`

        * :obj:`bool`

        * :obj:`int`

        * :obj:`float`

        * :obj:`bytes`

        * :obj:`unicode`

        * :obj:`list` whose items are primitive

        * :class:`dict` whose keys and values are primitive

      A primitive object is an instance of a primitive type.

"""

__copyright__ = "Copyright (C) 2014 Ivan D Vasin"
__docformat__ = "restructuredtext"

from ._bedframe import *
from ._core import *
from ._misc import *
from ._python import *
from ._util_json import *
