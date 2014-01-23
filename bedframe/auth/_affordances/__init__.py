"""Affordances

An affordance is a set of allowed parameter values.  Affordances are
defined over the following types of parameters:

  * realms

  * security provision sets

  * algorithms

For all of these parameter types, an
:class:`~bedframe.auth._affordances._core.AffordanceSet` may contain
multiple afforded values.  In fact, since it uses a
:class:`spruce.collections.uset
<spruce.collections._sets._universalizable.uset>` to define the values
for each such type, it is possible for an :class:`!AffordanceSet` to
afford all possible values for a parameter without listing them
explicitly.

An :class:`~bedframe.auth._affordances._process.ProcessAffordanceSet`
additionally contains affordances for these types of parameters:

  * required input token names

  * output token names

If some parameter types are left unspecified when creating an affordance
set, then those parameters' affordance sets are set to the values that
they are assigned by the corresponding class's :meth:`!max` method
(either :meth:`AffordanceSetABC.max()
<bedframe.auth._affordances._core.AffordanceSetABC.max>` or
:meth:`ProcessAffordanceSetABC.max()
<bedframe.auth._affordances._process.ProcessAffordanceSetABC.max>`).
This maximal affordance set specifies that

  * no input tokens are required,

  * no security provisions are guaranteed, and

  * for all other parameter types, all values are accepted.

For example, the code below creates a process affordance set that
affords

  * any input token sets that contain either

    * both a ``domain`` and ``user`` token or

    * a ``uid`` token,

  * a ``password`` output token,

  * the realms ``foo.net`` and ``bar.net``,

  * client authentication with no further security provisions, and

  * any authentication algorithms.

::

    import bedframe.auth as _bedframe_auth

    affordances = \\
        _bedframe_auth.ProcessAffordanceSet\\
         (inputs=(('domain', 'user',), ('uid',)),
          outputs=('password',),
          realms=('foo.net', 'bar.net'),
          provisionsets=_bedframe_auth.SECPROV_CLIENT_AUTH)

"""

__copyright__ = "Copyright (C) 2014 Ivan D Vasin"
__docformat__ = "restructuredtext"

from ._core import *
from ._process import *
from ._prospective import *
