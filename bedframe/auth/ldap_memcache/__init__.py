"""LDAP-memcached authentication

These objects provide support for authentication using an LDAP backend
together with a memcached backend.

.. seealso::
    :rfc:`Lightweight Directory Access Protocol (LDAP): Technical
          Specification Road Map <4510>`,
    `memcached <http://www.memcached.org/>`

"""

__copyright__ = "Copyright (C) 2014 Ivan D Vasin"
__docformat__ = "restructuredtext"

from ._connectors import *
