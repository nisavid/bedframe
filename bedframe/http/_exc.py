"""Exceptions"""

__copyright__ = "Copyright (C) 2014 Ivan D Vasin"
__docformat__ = "restructuredtext"

from .. import _exc as _bedframe_exc


class HttpMethodNotAllowed(_bedframe_exc.ClientError):

    def __init__(self, httpmethod, allowed_httpmethods, message=None, *args):
        allowed_httpmethods = sorted(allowed_httpmethods)
        super(HttpMethodNotAllowed, self).__init__(httpmethod,
                                                   allowed_httpmethods,
                                                   message, *args)
        self._allowed_httpmethods = allowed_httpmethods
        self._message = message
        self._httpmethod = httpmethod

    def __str__(self):
        message = 'HTTP method {!r} is not allowed'.format(self.httpmethod)
        if self.message:
            message += ': {}'.format(self.message)
        message += '; allowed HTTP methods are {}'\
                    .format(self.allowed_httpmethods)
        return message

    @property
    def allowed_httpmethods(self):
        return self._allowed_httpmethods

    @property
    def httpmethod(self):
        return self._httpmethod

    @property
    def message(self):
        return self._message
