"""Tornado support, common components"""

__copyright__ = "Copyright (C) 2014 Ivan D Vasin"
__docformat__ = "restructuredtext"

import spruce.logging as _logging


TORNADO_LOGGER = _logging.getLogger('tornado')


def tornado_log_request(handler):
    if handler.get_status() < 400:
        log_method = TORNADO_LOGGER.info
    elif handler.get_status() < 500:
        log_method = TORNADO_LOGGER.warning
    else:
        log_method = TORNADO_LOGGER.error
    log_method('{:d} {}   {:.2f} ms'.format(handler.get_status(),
                                            handler._request_summary(),
                                            handler.request.request_time()))
