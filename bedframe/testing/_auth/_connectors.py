"""Connectors"""

__copyright__ = "Copyright (C) 2014 Ivan D Vasin"
__docformat__ = "restructuredtext"

import bedframe.auth.inmem as _bedframe_auth_inmem


class InMemoryPlainSupplicant\
       (_bedframe_auth_inmem.InMemoryPlainSupplicant):
    def __init__(self, users, **kwargs):
        super(InMemoryPlainSupplicant, self)\
         .__init__({user.name: user.password for user in users}, **kwargs)


class InMemoryGetPasswordSupplicant\
       (_bedframe_auth_inmem.InMemoryGetPasswordSupplicant):
    def __init__(self, users, **kwargs):
        super(InMemoryGetPasswordSupplicant, self)\
         .__init__({user.name: user.password for user in users}, **kwargs)
