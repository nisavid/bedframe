"""Web service metadata"""

__copyright__ = "Copyright (C) 2014 Ivan D Vasin"
__docformat__ = "restructuredtext"

import re as _re


class ClassDefInfo(object):

    """Class definition metadata"""

    def __init__(self, module, name):
        self._module = module
        self._name = name

    def __repr__(self):
        return '{}(module={!r}, name={!r})'.format(self.__class__.__name__,
                                                   self.module, self.name)

    @classmethod
    def fromclass(cls, class_):
        return cls(module=class_.__module__, name=class_.__name__)

    @property
    def module(self):
        return self._module

    @property
    def name(self):
        return self._name


class ExceptionInfo(object):

    """Exception metadata"""

    def __init__(self, class_def_info, displayname=None, message=None, args=(),
                 traceback=None):
        self._args = args
        self._class_def_info = class_def_info
        self._displayname = displayname
        self._message = message
        self._traceback = traceback

    @property
    def args(self):
        return self._args

    @property
    def class_def_info(self):
        return self._class_def_info

    @property
    def displayname(self):
        return self._displayname

    @classmethod
    def fromexc(cls, exc, traceback=None):
        class_def_info = ClassDefInfo.fromclass(exc.__class__)
        try:
            displayname = exc.displayname
        except AttributeError:
            words_pattern = \
                r'((?P<first_lower>[a-z])?'\
                r'(?(first_lower)|(?P<first_upper>[A-Z])?'\
                r'(?(first_upper)|(?P<first_num>[0-9])))'\
                r'(?(first_lower)[a-z]*'\
                r'|(?(first_upper)(?P<second_upper>[A-Z])?'\
                r'(?(second_upper)[A-Z]*(?![a-z])|[a-z]*)'\
                r'|(?(first_num)[0-9]*|))))'\
                r'(?=\Z|(?(first_lower)[^a-z]'\
                r'|(?(first_upper)(?(second_upper)'\
                r'(?P<next_capword>[A-Z][a-z])?'\
                r'(?(next_capword)|[^A-Z])|[^a-z])'\
                r'|(?(first_num)[^0-9]|))))'
            name_words = \
                [matches[0].lower()
                 for matches
                 in _re.findall(words_pattern, class_def_info.name)]
            displayname = ' '.join(name_words)
        message = str(exc)
        return cls(class_def_info=class_def_info, displayname=displayname,
                   message=message, args=exc.args, traceback=traceback)

    @property
    def message(self):
        return self._message

    @property
    def traceback(self):
        return self._traceback
