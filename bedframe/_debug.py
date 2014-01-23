"""Debugging"""

__copyright__ = "Copyright (C) 2014 Ivan D Vasin"
__docformat__ = "restructuredtext"

from spruce.lang import namedflagset_classes as _namedflagset_classes


_DebugFlagSet_doc_body = \
    """
    A :class:`!DebugFlagSet` object is a set of debugging flags that could
    be associated with a :class:`~bedframe._services.Service`

    """
_DebugFlagSet_doc = \
    """Debugging flags
    """ \
    + _DebugFlagSet_doc_body
_FrozenDebugFlagSet_doc = \
    """Immutable debugging flags
    """ \
    + _DebugFlagSet_doc_body
DebugFlagSetABC, DebugFlagSet, FrozenDebugFlagSet = \
    _namedflagset_classes('DebugFlagSet', doc=_DebugFlagSet_doc,
                          frozendoc=_DebugFlagSet_doc)


DEBUG_EXC_NAME = DebugFlagSet.register_flag('DEBUG_EXC_NAME', 'exception name')


DEBUG_EXC_MESSAGE = \
    DebugFlagSet.register_flag('DEBUG_EXC_MESSAGE', 'exception message',
                               implied=DEBUG_EXC_NAME)


DEBUG_EXC_INSTANCE_INFO = \
    DebugFlagSet.register_flag('DEBUG_EXC_INSTANCE_INFO',
                               'exception instance info',
                               implied=(DEBUG_EXC_NAME | DEBUG_EXC_MESSAGE))


DEBUG_EXC_TRACEBACK = \
    DebugFlagSet.register_flag('DEBUG_EXC_TRACEBACK', 'exception traceback',
                               implied=DEBUG_EXC_INSTANCE_INFO)


DEBUG_EXC_TRACEBACK_INCLUDING_SERVICE_CODE = \
    DebugFlagSet.register_flag('DEBUG_EXC_TRACEBACK_INCLUDING_SERVICE_CODE',
                               'exception traceback including service code',
                               implied=DEBUG_EXC_TRACEBACK)


DEBUG_EXC_TRACEBACK_INCLUDING_RESOURCE_CODE = \
    DebugFlagSet.register_flag('DEBUG_EXC_TRACEBACK_INCLUDING_RESOURCE_CODE',
                               'exception traceback including resource code',
                               implied=DEBUG_EXC_TRACEBACK)


DEBUG_EXC_SECURE = DebugFlagSet(DEBUG_EXC_NAME | DEBUG_EXC_MESSAGE)


DEBUG_EXC_DEFAULT = DebugFlagSet(DEBUG_EXC_NAME | DEBUG_EXC_MESSAGE
                                 | DEBUG_EXC_INSTANCE_INFO
                                 | DEBUG_EXC_TRACEBACK)


DEBUG_EXC_FULL = \
    DebugFlagSet(DEBUG_EXC_NAME
                 | DEBUG_EXC_MESSAGE
                 | DEBUG_EXC_INSTANCE_INFO
                 | DEBUG_EXC_TRACEBACK
                 | DEBUG_EXC_TRACEBACK_INCLUDING_SERVICE_CODE
                 | DEBUG_EXC_TRACEBACK_INCLUDING_RESOURCE_CODE)


DEBUG_SECURE = DebugFlagSet(DEBUG_EXC_SECURE)


DEBUG_DEFAULT = DebugFlagSet(DEBUG_EXC_DEFAULT)


DEBUG_FULL = DebugFlagSet(DEBUG_EXC_FULL)
