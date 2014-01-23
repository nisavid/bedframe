""":mod:`Web service <bedframe._services>` testing"""

__copyright__ = "Copyright (C) 2014 Ivan D Vasin"
__docformat__ = "restructuredtext"

import abc as _abc
from collections import Iterable as _Iterable, Mapping as _Mapping
from functools import partial as _partial
from itertools import chain as _chain
from operator import itemgetter as _itemgetter
from pprint import pformat as _pformat
import re as _re
import socket as _socket
import sys as _sys
import time as _time
import unittest as _unittest
from urlparse \
    import urljoin as _urijoin, \
           urlsplit as _urisplit, \
           urlunsplit as _uriunsplit
from xml.etree import ElementTree as _ElementTree

import napper as _napper
import requests as _requests
from spruce.collections import frozenuset as _frozenuset, odict as _odict
import spruce.http.status as _http_status
from spruce.lang import regex_class as _regex_class
import spruce.ldap.testing as _ldaptest
from spruce.pprint import indented as _indented
import spruce.validation as _validation

import bedframe.auth.ldap as _bedframe_ldap_auth
from ._auth import _connectors as _bedtest_auth_connectors


class WebServiceTestCase(_unittest.TestCase):

    """Web service tests"""

    __metaclass__ = _abc.ABCMeta

    def __init__(self, *args, **kwargs):
        super(WebServiceTestCase, self).__init__(*args, **kwargs)
        self._requests_session = None
        self._webservice = None
        self._webservice_pid = None
        self.webservice_ready_max_sleep_duration = 1.
        self.webservice_ready_sleep_iter_duration = 0.025

    def assert_conflict_response(self, response,
                                 exc_class_def_module='bedframe._exc',
                                 exc_name='ResourceConflict', **kwargs):
        """
        Assert that *response* is an :term:`exception response` that
        indicates a resource state conflict

        .. seealso:: :meth:`assert_exc_response`

        :param response:
            A web service response.
        :type response: :class:`requests.Response`

        :param exc_class_def_module:
            The absolute module path of the module that defines the expected
            exception class.
        :type exc_class_def_module: :obj:`str`

        :param exc_name:
            The name of the expected exception class.
        :type exc_name: :obj:`str` or null

        :raise AssertionError:
            Raised if the *response* is not a resource state conflict exception
            response or any of the other parameters does not match the
            corresponding aspect of the *response*.

        """
        self.assert_exc_response(response,
                                 status=_http_status.CONFLICT,
                                 class_def_module=exc_class_def_module,
                                 name=exc_name,
                                 **kwargs)

    def assert_cors_preflight_accepted_response\
            (self,
             response,
             allowed_origins=None,
             allowed_methods=None,
             allowed_headers=None,
             allowed_credentials=None,
             exposed_headers=None,
             cache_lifespan=None,
             headers=None,
             description='accepted cross-origin preflight request',
             **kwargs):
        """
        Assert that *response* is an :term:`return response` that
        indicates an accepted cross-origin preflight request

        .. seealso:: :meth:`assert_return_response`

        :param response:
            A web service response.
        :type response: :class:`requests.Response`

        :raise AssertionError:
            Raised if the *response* is not an accepted cross-origin preflight
            request response or any of the other parameters does not match the
            corresponding aspect of the *response*.

        """

        if not description:
            description = 'accepted cross-origin preflight request'

        headers = _odict(headers or ())
        if allowed_origins is not None:
            allowed_origins = _frozenuset(allowed_origins or ())
            if allowed_origins.isfinite:
                if allowed_origins:
                    headers['Access-Control-Allow-Origin'] = \
                        ', '.join(allowed_origins)
                else:
                    headers['Access-Control-Allow-Origin'] = 'null'
            else:
                headers['Access-Control-Allow-Origin'] = '*'
        if allowed_methods:
            headers['Access-Control-Allow-Methods'] = \
                ', '.join(allowed_methods)
        if allowed_headers:
            headers['Access-Control-Allow-Headers'] = \
                ', '.join(allowed_headers)
        if exposed_headers:
            headers['Access-Control-Expose-Headers'] = \
                ', '.join(exposed_headers)
        if allowed_credentials:
            headers['Access-Control-Allow-Credentials'] = 'true'
        if cache_lifespan:
            headers['Access-Control-Max-Age'] = cache_lifespan.total_seconds()

        self.assert_return_response(response, status=_http_status.OK,
                                    headers=headers, **kwargs)

    def assert_cors_rejected_response(self,
                                      response,
                                      exc_class_def_module=
                                          'bedframe._exc',
                                      exc_name='CorsRequestRejected',
                                      **kwargs):
        """
        Assert that *response* is an :term:`exception response` that
        indicates a rejected cross-origin request

        .. seealso:: :meth:`assert_exc_response`

        :param response:
            A web service response.
        :type response: :class:`requests.Response`

        :param exc_class_def_module:
            The absolute module path of the module that defines the expected
            exception class.
        :type exc_class_def_module: :obj:`str`

        :param exc_name:
            The name of the expected exception class.
        :type exc_name: :obj:`str`

        :raise AssertionError:
            Raised if the *response* is not a rejected cross-origin request
            response or any of the other parameters does not match the
            corresponding aspect of the *response*.

        """
        self.assert_exc_response(response, status=_http_status.FORBIDDEN,
                                 class_def_module=exc_class_def_module,
                                 name=exc_name, **kwargs)

    def assert_entity_choice_redirect_response(self, response, locs=None,
                                                  preferred_loc=None,
                                                  locs_metadata=None,
                                                  **kwargs):
        if preferred_loc is not None:
            headers = kwargs.pop('headers', {})
            headers['Location'] = preferred_loc
        self.assert_exc_response(response,
                                 status=_http_status.MULTIPLE_CHOICES,
                                 class_def_module='bedframe._exc',
                                 name='EntityChoiceRedirection',
                                 headers=headers,
                                 **kwargs)

    def assert_exc_response(self,
                            response,
                            status=None,
                            contenttype='application/json',
                            class_def_module=None,
                            name=None,
                            message_pattern=None,
                            headers=None,
                            description=None):

        """Assert that *response* is an :term:`exception response`

        :param response:
            A web service response.
        :type response: :class:`requests.Response`

        :param status:
            The expected response :term:`status code`.

            .. seealso:: :mod:`spruce.http.status`
        :type status: :obj:`int` or null

        :param class_def_module:
            The absolute module path of the module that defines the expected
            exception class.
        :type class_def_module: :obj:`str` or null

        :param name:
            The name of the expected exception class.
        :type name: :obj:`str` or null

        :param message_pattern:
            A pattern that is expected to match the exception message.
        :type message_pattern: ~\ :obj:`re` or null

        :raise AssertionError:
            Raised if the *response* is not an exception response or any of the
            other parameters does not match the corresponding aspect of the
            *response*.

        """

        if not description:
            description_str_items = []
            if status is not None:
                status_str = \
                    'status {!r}'.format(_http_status.status_messages[status])
                description_str_items.append(status_str)

            if name is not None:
                exc_str = 'exception '
                if class_def_module is not None:
                    exc_str += class_def_module + '.'
                exc_str += name

                if message_pattern is not None:
                    exc_str += \
                        ' with message pattern {!r}'.format(message_pattern)

                description_str_items.append(exc_str)

            if description_str_items:
                description = 'response with ' \
                              + ', '.join(description_str_items)

        headers = _odict(headers or ())
        headers['Content-Type'] = contenttype

        try:
            contenttype_name, _, _ = contenttype.partition(';')
            meth = \
                self._assert_exc_response_meth_by_contenttype[contenttype_name]
        except KeyError:
            supported_contenttypes = \
                self._assert_exc_response_meth_by_contenttype.keys()
            raise ValueError('unsupported response content type {!r}:'
                              ' expecting one of {}'
                              .format(contenttype, supported_contenttypes))

        try:
            self.assert_response_with_status(response, status, headers=headers,
                                             description=description,
                                             wrapexc=False)
            meth(self, response, class_def_module=class_def_module, name=name,
                 message_pattern=message_pattern)
        except AssertionError as exc:
            exc.args = (self._unexpected_response_assertionerror_message
                         (response, exc, description=description),)
            raise

    def assert_forbidden_response(self, response,
                                  exc_class_def_module='bedframe._exc',
                                  exc_name='AccessForbidden', **kwargs):
        """
        Assert that *response* is an :term:`exception response` that
        indicates forbidden access

        .. seealso:: :meth:`assert_exc_response`

        :param response:
            A web service response.
        :type response: :class:`requests.Response`

        :param exc_class_def_module:
            The absolute module path of the module that defines the expected
            exception class.
        :type exc_class_def_module: :obj:`str`

        :param exc_name:
            The name of the expected exception class.
        :type exc_name: :obj:`str`

        :raise AssertionError:
            Raised if the *response* is not a forbidden access exception
            response or any of the other parameters does not match the
            corresponding aspect of the *response*.

        """
        self.assert_exc_response(response,
                                 status=_http_status.FORBIDDEN,
                                 class_def_module=exc_class_def_module,
                                 name=exc_name,
                                 **kwargs)

    def assert_permanent_redirect_response\
            (self,
             response,
             loc=None,
             message_pattern=None,
             contenttype='application/json',
             exc_class_def_module='bedframe._exc',
             exc_name='PermanentRedirection',
             exc_message_pattern=None,
             status=_http_status.PERMANENT_REDIRECT,
             headers=None,
             description=None):

        headers = headers or {}
        if loc is not None:
            headers['Location'] = loc

        if exc_message_pattern is None:
            exc_message_pattern = 'resource moved permanently to '
            if loc is not None:
                exc_message_pattern += _re.escape(loc)
            if message_pattern is not None:
                exc_message_pattern += ': {}'.format(message_pattern)

        if not description:
            description_str_items = []
            if status is not None:
                status_str = \
                    'status {!r}'.format(_http_status.status_messages[status])
                description_str_items.append(status_str)

            redirect_str = 'permanent redirection'
            if loc is not None:
                redirect_str += ' to {}'.format(loc)
            if message_pattern is not None:
                redirect_str += ' with message pattern {!r}'\
                                 .format(exc_message_pattern)
            description_str_items.append(redirect_str)

            if exc_name is not None:
                exc_str = 'exception '
                if exc_class_def_module is not None:
                    exc_str += exc_class_def_module + '.'
                exc_str += exc_name

                if exc_message_pattern is not None:
                    exc_str += \
                        ' with message pattern {!r}'\
                         .format(exc_message_pattern)

                description_str_items.append(exc_str)

            if description_str_items:
                description = 'response with ' \
                              + ', '.join(description_str_items)

        headers = _odict(headers or ())
        headers['Content-Type'] = contenttype

        try:
            contenttype_name, _, _ = contenttype.partition(';')
            meth = \
                self._assert_permanent_redirect_response_meth_by_contenttype\
                     [contenttype_name]
        except KeyError:
            supported_contenttypes = \
                self._assert_permanent_redirect_response_meth_by_contenttype\
                    .keys()
            raise ValueError('unsupported response content type {!r}:'
                              ' expecting one of {}'
                              .format(contenttype, supported_contenttypes))

        try:
            self.assert_response_with_status(response, status, headers=headers,
                                             description=description,
                                             wrapexc=False)
            meth(self, response, loc=loc, message_pattern=message_pattern,
                 exc_class_def_module=exc_class_def_module, exc_name=exc_name,
                 exc_message_pattern=exc_message_pattern)
        except AssertionError as exc:
            exc.args = (self._unexpected_response_assertionerror_message
                         (response, exc, description=description),)
            raise

    def assert_proxy_redirect_response\
            (self,
             response,
             loc=None,
             message_pattern=None,
             contenttype='application/json',
             exc_class_def_module='bedframe._exc',
             exc_name='ProxyRedirection',
             exc_message_pattern=None,
             status=_http_status.USE_PROXY,
             headers=None,
             description=None):

        headers = headers or {}
        if loc is not None:
            headers['Location'] = loc

        if exc_message_pattern is None:
            exc_message_pattern = 'repeat request through proxy at '
            if loc is not None:
                exc_message_pattern += _re.escape(loc)
            if message_pattern is not None:
                exc_message_pattern += ': {}'.format(message_pattern)

        if not description:
            description_str_items = []
            if status is not None:
                status_str = \
                    'status {!r}'.format(_http_status.status_messages[status])
                description_str_items.append(status_str)

            redirect_str = 'proxy redirection'
            if loc is not None:
                redirect_str += ' to {}'.format(loc)
            if message_pattern is not None:
                redirect_str += ' with message pattern {!r}'\
                                 .format(exc_message_pattern)
            description_str_items.append(redirect_str)

            if exc_name is not None:
                exc_str = 'exception '
                if exc_class_def_module is not None:
                    exc_str += exc_class_def_module + '.'
                exc_str += exc_name

                if exc_message_pattern is not None:
                    exc_str += \
                        ' with message pattern {!r}'\
                         .format(exc_message_pattern)

                description_str_items.append(exc_str)

            if description_str_items:
                description = 'response with ' \
                              + ', '.join(description_str_items)

        headers = _odict(headers or ())
        headers['Content-Type'] = contenttype

        try:
            contenttype_name, _, _ = contenttype.partition(';')
            meth = \
                self._assert_proxy_redirect_response_meth_by_contenttype\
                     [contenttype_name]
        except KeyError:
            supported_contenttypes = \
                self._assert_proxy_redirect_response_meth_by_contenttype\
                    .keys()
            raise ValueError('unsupported response content type {!r}:'
                              ' expecting one of {}'
                              .format(contenttype, supported_contenttypes))

        try:
            self.assert_response_with_status(response, status, headers=headers,
                                             description=description,
                                             wrapexc=False)
            meth(self, response, loc=loc, message_pattern=message_pattern,
                 exc_class_def_module=exc_class_def_module, exc_name=exc_name,
                 exc_message_pattern=exc_message_pattern)
        except AssertionError as exc:
            exc.args = (self._unexpected_response_assertionerror_message
                         (response, exc, description=description),)
            raise

    def assert_response_redirect_response\
            (self,
             response,
             loc=None,
             message_pattern=None,
             contenttype='application/json',
             exc_class_def_module='bedframe._exc',
             exc_name='ResponseRedirection',
             exc_message_pattern=None,
             status=_http_status.SEE_OTHER,
             headers=None,
             description=None):

        headers = headers or {}
        if loc is not None:
            headers['Location'] = loc

        if exc_message_pattern is None:
            exc_message_pattern = 'response can be found at '
            if loc is not None:
                exc_message_pattern += _re.escape(loc)
            if message_pattern is not None:
                exc_message_pattern += ': {}'.format(message_pattern)

        if not description:
            description_str_items = []
            if status is not None:
                status_str = \
                    'status {!r}'.format(_http_status.status_messages[status])
                description_str_items.append(status_str)

            redirect_str = 'response redirection'
            if loc is not None:
                redirect_str += ' to {}'.format(loc)
            if message_pattern is not None:
                redirect_str += ' with message pattern {!r}'\
                                 .format(exc_message_pattern)
            description_str_items.append(redirect_str)

            if exc_name is not None:
                exc_str = 'exception '
                if exc_class_def_module is not None:
                    exc_str += exc_class_def_module + '.'
                exc_str += exc_name

                if exc_message_pattern is not None:
                    exc_str += \
                        ' with message pattern {!r}'\
                         .format(exc_message_pattern)

                description_str_items.append(exc_str)

            if description_str_items:
                description = 'response with ' \
                              + ', '.join(description_str_items)

        headers = _odict(headers or ())
        headers['Content-Type'] = contenttype

        try:
            contenttype_name, _, _ = contenttype.partition(';')
            meth = \
                self._assert_response_redirect_response_meth_by_contenttype\
                     [contenttype_name]
        except KeyError:
            supported_contenttypes = \
                self._assert_response_redirect_response_meth_by_contenttype\
                    .keys()
            raise ValueError('unsupported response content type {!r}:'
                              ' expecting one of {}'
                              .format(contenttype, supported_contenttypes))

        try:
            self.assert_response_with_status(response, status, headers=headers,
                                             description=description,
                                             wrapexc=False)
            meth(self, response, loc=loc, message_pattern=message_pattern,
                 exc_class_def_module=exc_class_def_module, exc_name=exc_name,
                 exc_message_pattern=exc_message_pattern)
        except AssertionError as exc:
            exc.args = (self._unexpected_response_assertionerror_message
                         (response, exc, description=description),)
            raise

    def assert_response_with_status(self, response, statuscode,
                                    description=None, headers=None,
                                    wrapexc=True):
        """Assert that a *response* has a particular *status*

        :param response:
            A web service response.
        :type response: :class:`requests.Response`

        :param statuscode:
            The expected response :term:`status code`.

            .. seealso:: :mod:`spruce.http.status`
        :type status: :obj:`int` or null

        :raise AssertionError:
            Raised if the *response*'s status does not match the given
            *status*.

        """

        headers = _odict(headers or ())
        if not description:
            description = \
                'response with status {!r}'\
                 .format(_http_status.status_messages
                          .get(statuscode, 'code {}'.format(statuscode)))

        try:
            if response.status_code in _http_status.status_messages \
                   and statuscode in _http_status.status_messages:
                response_status = \
                    _http_status.status_messages[response.status_code]
                status = _http_status.status_messages[statuscode]
                self.assertEqual(response_status, status)
            self.assertEqual(response.status_code, statuscode)
            for name, value in headers.items():
                self.assertIn(name, response.headers)
                self.assertEqual(response.headers[name], value)
        except AssertionError as exc:
            if wrapexc:
                exc.args = (self._unexpected_response_assertionerror_message
                             (response, exc, description=description),)
            raise

    def assert_return_response(self, response, status=_http_status.OK,
                               contenttype='application/json', headers=None,
                               description=None, wrapexc=True):

        """Assert that *response* is a :term:`return response`

        :param response:
            A web service response.
        :type response: :class:`requests.Response`

        :param status:
            The expected response :term:`status code`.

            .. seealso:: :mod:`spruce.http.status`
        :type status: :obj:`int` or null

        :param contenttype:
            The expected :term:`media type` of the response content.
        :type contenttype: :obj:`str` or null

        :raise AssertionError:
            Raised if the *response* is not a return response or any of the
            other parameters does not match the corresponding aspect of the
            *response*.

        """

        headers = _odict(headers or ())
        headers['Content-Type'] = contenttype

        contenttype_name, _, _ = contenttype.partition(';')
        try:
            meth = self._assert_return_response_meth_by_contenttype\
                        [contenttype_name]
        except KeyError:
            supported_contenttypes = \
                self._assert_return_response_meth_by_contenttype.keys()
            raise ValueError('unsupported response content type {!r}:'
                              ' expecting one of {}'
                              .format(contenttype, supported_contenttypes))

        try:
            self.assert_response_with_status(response, status, headers=headers,
                                             description=description,
                                             wrapexc=False)
            meth(self, response)
        except AssertionError as exc:
            if wrapexc:
                exc.args = (self._unexpected_response_assertionerror_message
                             (response, exc, description=description),)
            raise

    def assert_return_response_with_value_prim(self, response, prim,
                                               description=None, wrapexc=True,
                                               **kwargs):

        """
        Assert that *response* is a JSON :term:`return response` with a
        particular result value

        .. seealso:: :meth:`assert_return_response`

        :param response:
            A web service response.
        :type response:
            :class:`requests.Response`

        :param prim:
            A primitive representation of the expected result value.
        :type prim:
            null \
            or :obj:`bool` \
            or :obj:`int` \
            or :obj:`float` \
            or :obj:`bytes` \
            or :obj:`unicode` \
            or [null or :obj:`bool` or :obj:`int` or :obj:`float` \
                or :obj:`bytes` or :obj:`unicode` or [...] or {...}] \
            or {null or :obj:`bool` or :obj:`int` or :obj:`float` \
                or :obj:`bytes` or :obj:`unicode` or [...] or {...}: \
                    null or :obj:`bool` or :obj:`int` or :obj:`float` \
                    or :obj:`bytes` or :obj:`unicode` or [...] or {...}}

        :raise AssertionError:
            Raised if the *response* is not a JSON return response or any of
            the other parameters does not match the corresponding aspect of
            the *response*.

        """

        try:
            self.assert_return_response(response, wrapexc=False, **kwargs)
        except AssertionError as exc:
            if wrapexc:
                exc.args = (self._unexpected_response_assertionerror_message
                             (response, exc, description=description),)
            raise

        actual_prim = response.json()['retval']
        try:
            self.assertEquals(actual_prim, prim)
        except AssertionError as exc:
            if wrapexc:
                exc.args = (self._unexpected_response_message
                                (response, str(exc), description=description),)
            raise

    def assert_return_response_with_value_prim_submap(self,
                                                      response,
                                                      submap,
                                                      description=None,
                                                      wrapexc=True,
                                                      **kwargs):

        """
        Assert that *response* is a JSON :term:`return response` wherein the
        primitive representation of the result value is a mapping that
        contains the items in *submap*

        .. seealso:: :meth:`assert_return_response`

        :param response:
            A web service response.
        :type response:
            :class:`requests.Response`

        :param submap:
            A primitive mapping or an iterable thereof.
        :type submap:
            {:obj:`str`:
                 null
                 or :obj:`bool`
                 or :obj:`int`
                 or :obj:`float`
                 or :obj:`bytes`
                 or :obj:`unicode`
                 or [null or :obj:`bool` or :obj:`int` or :obj:`float`
                     or :obj:`bytes` or :obj:`unicode` or [...] or {...}]
                 or {null or :obj:`bool` or :obj:`int` or :obj:`float`
                     or :obj:`bytes` or :obj:`unicode` or [...] or {...}:
                         null or :obj:`bool` or :obj:`int` or :obj:`float`
                         or :obj:`bytes` or :obj:`unicode` or [...] or {...}}}
            or ~[{:obj:`str`:
                      null
                      or :obj:`bool`
                      or :obj:`int`
                      or :obj:`float`
                      or :obj:`bytes`
                      or :obj:`unicode`
                      or [null or :obj:`bool` or :obj:`int` or :obj:`float`
                          or :obj:`bytes` or :obj:`unicode` or [...] or {...}]
                      or {null or :obj:`bool` or :obj:`int` or :obj:`float`
                          or :obj:`bytes` or :obj:`unicode` or [...] or {...}:
                              null or :obj:`bool` or :obj:`int` or :obj:`float`
                              or :obj:`bytes` or :obj:`unicode` or [...]
                              or {...}}}]

        :raise AssertionError:
            Raised if the *response* is not a JSON return response or any of
            the other parameters does not match the corresponding aspect of
            the *response*.

        """

        try:
            self.assert_return_response(response, wrapexc=False, **kwargs)
        except AssertionError as exc:
            if wrapexc:
                exc.args = (self._unexpected_response_assertionerror_message
                             (response, exc, description=description),)
            raise

        prim = response.json()['retval']
        unexpected_submap, failed_expectation_message = \
            self._unexpected_response_value_prim_submap(prim,
                                                        expected_submap=submap)

        try:
            self.assertFalse(unexpected_submap)
        except AssertionError as exc:
            if wrapexc:
                exc.args = (self._unexpected_response_message
                             (response, failed_expectation_message,
                              description=description),)
            raise

    def assert_temporary_redirect_response\
            (self,
             response,
             loc=None,
             message_pattern=None,
             contenttype='application/json',
             exc_class_def_module='bedframe._exc',
             exc_name='TemporaryRedirection',
             exc_message_pattern=None,
             status=_http_status.TEMPORARY_REDIRECT,
             headers=None,
             description=None):

        headers = headers or {}
        if loc is not None:
            headers['Location'] = loc

        if exc_message_pattern is None:
            exc_message_pattern = 'resource moved temporarily to '
            if loc is not None:
                exc_message_pattern += _re.escape(loc)
            if message_pattern is not None:
                exc_message_pattern += ': {}'.format(message_pattern)

        if not description:
            description_str_items = []
            if status is not None:
                status_str = \
                    'status {!r}'.format(_http_status.status_messages[status])
                description_str_items.append(status_str)

            redirect_str = 'temporary redirection'
            if loc is not None:
                redirect_str += ' to {}'.format(loc)
            if message_pattern is not None:
                redirect_str += ' with message pattern {!r}'\
                                 .format(exc_message_pattern)
            description_str_items.append(redirect_str)

            if exc_name is not None:
                exc_str = 'exception '
                if exc_class_def_module is not None:
                    exc_str += exc_class_def_module + '.'
                exc_str += exc_name

                if exc_message_pattern is not None:
                    exc_str += \
                        ' with message pattern {!r}'\
                         .format(exc_message_pattern)

                description_str_items.append(exc_str)

            if description_str_items:
                description = 'response with ' \
                              + ', '.join(description_str_items)

        headers = _odict(headers or ())
        headers['Content-Type'] = contenttype

        try:
            contenttype_name, _, _ = contenttype.partition(';')
            meth = \
                self._assert_temporary_redirect_response_meth_by_contenttype\
                     [contenttype_name]
        except KeyError:
            supported_contenttypes = \
                self._assert_temporary_redirect_response_meth_by_contenttype\
                    .keys()
            raise ValueError('unsupported response content type {!r}:'
                              ' expecting one of {}'
                              .format(contenttype, supported_contenttypes))

        try:
            self.assert_response_with_status(response, status, headers=headers,
                                             description=description,
                                             wrapexc=False)
            meth(self, response, loc=loc, message_pattern=message_pattern,
                 exc_class_def_module=exc_class_def_module, exc_name=exc_name,
                 exc_message_pattern=exc_message_pattern)
        except AssertionError as exc:
            exc.args = (self._unexpected_response_assertionerror_message
                         (response, exc, description=description),)
            raise

    def assert_unauth_with_no_creds_response(self, response):
        """
        Assert that *response* is an :term:`exception response` that indicates
        an unauthenticated request with no credentials

        :param response:
            A web service response.
        :type response: :class:`requests.Response`

        :raise AssertionError:
            Raised if the *response* is not an exception response that
            indicates an unauthenticated request with no credentials.

        """
        self.assert_exc_response\
            (response, status=_http_status.UNAUTHORIZED,
             class_def_module='bedframe._exc', name='AuthTokensNotGiven',
             message_pattern='unauthenticated.*no tokens given')

    def assert_unauth_with_wrong_creds_response(self, response):
        """
        Assert that *response* is an :term:`exception response` that indicates
        an unauthenticated request with incorrect credentials

        :param response:
            A web service response.
        :type response: :class:`requests.Response`

        :raise AssertionError:
            Raised if the *response* is not an exception response that
            indicates an unauthenticated request with incorrect credentials.

        """
        self.assert_exc_response\
            (response,
             status=_http_status.UNAUTHORIZED,
             class_def_module='bedframe._exc',
             name='AuthTokensNotAccepted',
             message_pattern='unauthenticated.*tokens not accepted')

    def create_request(self, method, *args, **kwargs):
        return _napper.WebRequest(method, self.webservice_uri, *args,
                                  session=self.requests_session, **kwargs)

    def request(self, method, *args, **kwargs):
        return _napper.request(method, self.webservice_uri, *args,
                               session=self.requests_session, **kwargs)

    def request_args_from_resource(self, method, *args, **kwargs):
        return _napper.request_args_from_resource(method, self.webservice_uri,
                                                  *args, **kwargs)

    def request_cors_preflight(self, method, *args, **kwargs):
        return _napper.request_cors_preflight(method,
                                              self.webservice_uri,
                                              *args,
                                              session=self.requests_session,
                                              **kwargs)

    @property
    def requests_session(self):
        if not self._requests_session:
            self._requests_session = self._create_requests_session()
        return self._requests_session

    def setUp(self):
        super(WebServiceTestCase, self).setUp()
        self._setup_webservice()

    def tearDown(self):
        self._teardown_webservice()
        super(WebServiceTestCase, self).tearDown()

    @property
    def webservice(self):
        return self._webservice

    @_abc.abstractproperty
    def webservice_auth_realm_base(self):
        pass

    @property
    def webservice_host(self):
        return 'localhost'

    @property
    def webservice_host_uri(self):
        return 'http://{}:{}'.format(self.webservice_host,
                                     self.webservice_port)

    @property
    def webservice_path(self):
        return '/'

    @property
    def webservice_port(self):
        # FIXME: randomize
        return 8080

    @property
    def webservice_probe_path(self):
        return '/'

    @property
    def webservice_ready_max_sleep_duration(self):
        return self._webservice_ready_max_sleep_duration

    @webservice_ready_max_sleep_duration.setter
    def webservice_ready_max_sleep_duration(self, value):
        self._webservice_ready_max_sleep_duration = value

    @property
    def webservice_ready_sleep_iter_duration(self):
        return self._webservice_ready_sleep_iter_duration

    @webservice_ready_sleep_iter_duration.setter
    def webservice_ready_sleep_iter_duration(self, value):
        self._webservice_ready_sleep_iter_duration = value

    @property
    def webservice_uri(self):
        webservice_uri = self.webservice_host_uri
        if not webservice_uri.endswith('/'):
            webservice_uri += '/'
        return _urijoin(webservice_uri, self.webservice_path)

    def _assert_exc_response_as_html(self, response, class_def_module, name,
                                     message_pattern):

        html_tree = self._asserted_html_response_content_tree(response)

        exc_str_tree = html_tree.find('body//*[@class="exc_str"]')
        self.assertIsNot(exc_str_tree, None)
        if message_pattern is not None:
            self.assertRegexpMatches(exc_str_tree.text, message_pattern)

        exc_class_def_module_tree = \
            html_tree.find('body//*[@class="exc_class_def_module"]')
        self.assertIsNot(exc_class_def_module_tree, None)
        if class_def_module is not None:
            self.assertEquals(exc_class_def_module_tree.text,
                              class_def_module)

        exc_name_tree = html_tree.find('body//*[@class="exc_name"]')
        self.assertIsNot(exc_name_tree, None)
        if name is not None:
            self.assertEquals(exc_name_tree.text, name)

    def _assert_exc_response_as_json(self, response, class_def_module, name,
                                     message_pattern):

        prim = self._asserted_json_response_content_prim(response)

        self.assertIsNot(prim, None)
        self.assertIn('type', prim)
        self.assertEqual(prim['type'],
                         'bedframe._responses._exc'
                          ':WebExceptionResponse')

        self.assertIn('class_def_module', prim)
        if class_def_module is not None:
            self.assertEqual(prim['class_def_module'], class_def_module)

        self.assertIn('name', prim)
        if name is not None:
            self.assertEqual(prim['name'], name)

        self.assertIn('message', prim)
        if message_pattern is not None:
            self.assertRegexpMatches(prim['message'], message_pattern)

    _assert_exc_response_meth_by_contenttype = {}

    def _assert_oneloc_redirect_response_as_html\
            (self, response, loc, message_pattern, exc_class_def_module,
             exc_name, exc_message_pattern):
        self._assert_exc_response_as_html\
         (response, class_def_module=exc_class_def_module, name=exc_name,
          message_pattern=exc_message_pattern)

    def _assert_oneloc_redirect_response_as_json\
            (self, response, response_type, loc, message_pattern,
             exc_class_def_module, exc_name, exc_message_pattern):

        prim = self._asserted_json_response_content_prim(response)

        self.assertIsNot(prim, None)
        self.assertIn('type', prim)
        self.assertEqual(prim['type'], response_type)

        self.assertIn('message', prim)
        if message_pattern is not None:
            self.assertRegexpMatches(prim['message'], message_pattern)

        self.assertIn('exc_class_def_module', prim)
        if exc_class_def_module is not None:
            self.assertEqual(prim['exc_class_def_module'],
                             exc_class_def_module)

        self.assertIn('exc_name', prim)
        if exc_name is not None:
            self.assertEqual(prim['exc_name'], exc_name)

        self.assertIn('exc_message', prim)
        if exc_message_pattern is not None:
            self.assertRegexpMatches(prim['exc_message'], exc_message_pattern)

    _assert_permanent_redirect_response_meth_by_contenttype = {}

    _assert_proxy_redirect_response_meth_by_contenttype = {}

    _assert_response_redirect_response_meth_by_contenttype = {}

    _assert_temporary_redirect_response_meth_by_contenttype = {}

    def _assert_return_response_as_html(self, response):
        html_tree = self._asserted_html_response_content_tree(response)
        retval_tree = html_tree.find('body//*[@class="retval"]')
        self.assertIsNot(retval_tree, None)

    def _assert_return_response_as_json(self, response):

        prim = self._asserted_json_response_content_prim(response)

        self.assertIsNot(prim, None)
        self.assertIn('type', prim)
        self.assertEqual(prim['type'],
                         'bedframe._responses._return:WebReturnResponse')

        self.assertIn('retval', prim)

    _assert_return_response_meth_by_contenttype = {}

    def _asserted_html_response_content_tree(self, response):
        try:
            return _ElementTree.fromstring(response.text)
        except _ElementTree.ParseError as exc:
            self.fail('invalid response HTML: {}'.format(exc))

    def _asserted_json_response_content_prim(self, response):
        try:
            return response.json()
        except (TypeError, ValueError) as exc:
            self.fail('invalid response content JSON: {}'.format(exc))

    def _create_requests_session(self):
        return _napper.WebRequestSession()

    @_abc.abstractmethod
    def _create_webservice(self):
        pass

    def _create_webservice_auth_supplicants(self):
        authenticator = self.webservice.authenticator
        realm = 'inmemory.{}'.format(self.webservice_auth_realm_base)
        return (_bedtest_auth_connectors.InMemoryPlainSupplicant
                 (_ldaptest.USERS, realm=realm, authenticator=authenticator),
                _bedtest_auth_connectors.InMemoryGetPasswordSupplicant
                 (_ldaptest.USERS, realm=realm, authenticator=authenticator),
                )

    def _message_content_str(self, mediatype, content):
        if mediatype is not None \
               and (mediatype.startswith('text/')
                    or mediatype == 'application/x-www-form-urlencoded'):
            return content
        elif content:
            return '<{} bytes of {} data>'.format(len(content),
                                                  mediatype or 'untyped')
        else:
            return '<empty response>'

    def _setup_webservice(self):
        self._webservice = self._create_webservice()
        self.webservice.auth_supplicants\
            .extend(self._create_webservice_auth_supplicants())
        self._start_webservice()

    def _start_webservice(self):

        pid = self.webservice.start(fork=True)
        if pid == 0:
            _sys.exit()
        else:
            self._webservice_pid = pid

        def webservice_ready():
            try:
                response = self.request('get', self.webservice_probe_path)
            except (_requests.RequestException, _socket.error):
                return False
            except:
                self.webservice.stop()
                raise
            else:
                # download content to appease the service
                response.text
                return True

        webservice_ready_sleep_duration = 0.
        while not webservice_ready() \
              and webservice_ready_sleep_duration \
                  < self.webservice_ready_max_sleep_duration:
            _time.sleep(self.webservice_ready_sleep_iter_duration)
            webservice_ready_sleep_duration += \
                self.webservice_ready_sleep_iter_duration
        if webservice_ready_sleep_duration \
               >= self.webservice_ready_max_sleep_duration:
            raise RuntimeError\
                      ('web service did not start within {:.2f} s'
                        .format(self.webservice_ready_max_sleep_duration))

    def _teardown_webservice(self):
        self.webservice.stop()

    def _unexpected_response_assertionerror_message(self, response, exc,
                                                    description=None):
        return self._unexpected_response_message\
                (response,
                 'failed assertion:\n' + _indented(str(exc), size=2),
                 description=description)

    def _unexpected_response_message(self, response,
                                     failed_expectation_message,
                                     description=None):

        clauses = []
        clauses.append('unexpected response')
        if description:
            clauses.append('expected {}'.format(description))
        clauses.append('failed expectation')
        message = '; '.join(clauses) + ':\n'

        message += _indented(failed_expectation_message, size=2)

        message += '\n  request:\n'
        request = response.request
        uriparts = _urisplit(request.url)
        request_str = \
            _uriunsplit((uriparts.scheme, uriparts.netloc, '', '', '')) \
             + '\n  {} {}'.format(request.method, uriparts.path)
        if uriparts.query:
            request_str += '\n' + _indented('?' + uriparts.query, size=2)
        if uriparts.fragment:
            request_str += '\n' + _indented('#' + uriparts.fragment, size=2)
        request_str += '\n'
        request_str += \
            '\n'.join('{}: {}'.format(name, value)
                      for name, value
                      in sorted(((name.title(), value)
                                 for name, value in request.headers.items()),
                                key=_itemgetter(0)))
        if request.body:
            request_str += \
                '\n\n' \
                + self._message_content_str(request.headers.get('Content-Type',
                                                                None),
                                            request.body)
        message += _indented(request_str, 2, size=2)

        message += '\n  response:\n'
        response_str = \
            '\n'.join('{}: {}'.format(name, value)
                      for name, value
                      in sorted(((name.title(), value)
                                 for name, value in response.headers.items()),
                                key=_itemgetter(0)))
        response_str += '\n\n'
        contenttype = response.headers.get('Content-Type', None)
        if contenttype is not None \
               and contenttype.startswith('application/json'):
            prim = response.json()
            try:
                exc_name = prim['name']
                exc_message = prim['message']

            except KeyError:
                response_str += \
                    '<JSON content; parsed primitive follows>\n' \
                    + _pformat(prim)

            else:
                try:
                    exc_traceback = prim['traceback']
                except KeyError:
                    exc_traceback = None

                response_str += \
                    '<JSON exception representation; parsed representation'\
                     ' follows>\n'\
                     '\n{}: {}'.format(exc_name, exc_message)
                if exc_traceback:
                    response_str += '\n' + exc_traceback
        elif contenttype is not None and contenttype.startswith('text/'):
            response_str += response.text
        else:
            response_str += self._message_content_str(contenttype,
                                                      response.content)
        message += _indented(response_str, 2, size=2)

        return message

    def _unexpected_response_value_prim_submap(self, prim, expected_submap):

        def unexpected_submap(actual_map, expected_submap):
            submap = {}
            for key, expected_value in expected_submap.items():
                actual_value = actual_map[key]
                if isinstance(expected_value, _regex_class):
                    match = expected_value.match(actual_value)
                else:
                    match = actual_value == expected_value
                if not match:
                    submap[key] = \
                        _validation.UnexpectedValue(actual=actual_value,
                                                    expected=expected_value)
            return submap

        def unexpected_submap_items_strs(submap):
            def expected_value_str(value):
                if isinstance(value, _regex_class):
                    return 'a string that matches regex {!r}'\
                            .format(expected_value.pattern)
                else:
                    return repr(value)
            return ['unexpected mapping of {!r} to {!r}; expected {}'
                     .format(key, actual_value,
                             expected_value_str(expected_value))
                    for key, (actual_value, expected_value) in submap.items()]

        if isinstance(expected_submap, _Mapping):
            unexpected_items = \
                unexpected_submap(actual_map=prim,
                                  expected_submap=expected_submap)

            failed_expectation_message = \
                'unexpected attributes:\n' \
                + _indented('\n'.join(unexpected_submap_items_strs
                                          (unexpected_items)),
                            size=2)

        elif isinstance(expected_submap, _Iterable):
            unexpected_items = []
            for submap_alt in expected_submap:
                unexpected_items\
                    .append(unexpected_submap(actual_map=prim,
                                              expected_submap=submap_alt))

            failed_expectation_message = 'unexpected items:'
            for i, alt_unexpected_items in enumerate(unexpected_items):
                alt_unexpected_items_message = \
                    '\nexpected alternative {}:\n'.format(i) \
                    + _indented('\n'.join(unexpected_submap_items_strs
                                              (alt_unexpected_items)),
                                size=2)
                failed_expectation_message += \
                    _indented(alt_unexpected_items_message, size=2)

            if any(not submap for submap in unexpected_items):
                unexpected_items = ()

        else:
            raise TypeError('invalid expected submap type {}; expected a'
                            ' primitive mapping or an iterable thereof'
                             .format(expected_submap.__class__.__name__))

        return unexpected_items, failed_expectation_message

WebServiceTestCase\
 ._assert_exc_response_meth_by_contenttype\
 .update({'application/json': WebServiceTestCase._assert_exc_response_as_json,
          'text/html': WebServiceTestCase._assert_exc_response_as_html})

WebServiceTestCase\
 ._assert_response_redirect_response_meth_by_contenttype\
 .update({'application/json':
              _partial(WebServiceTestCase
                        ._assert_oneloc_redirect_response_as_json,
                       response_type='bedframe._responses._redirect:'
                                      'WebResponseRedirectionResponse'),
          'text/html':
              WebServiceTestCase._assert_oneloc_redirect_response_as_html})

WebServiceTestCase\
 ._assert_return_response_meth_by_contenttype\
 .update({'application/json':
              WebServiceTestCase._assert_return_response_as_json,
          'text/html': WebServiceTestCase._assert_return_response_as_html})


class WebServiceWithLdapTestCase(_ldaptest.LdapServiceTestCase,
                                 WebServiceTestCase):

    __metaclass__ = _abc.ABCMeta

    def _create_webservice_auth_supplicants(self):
        realm = 'ldap.{}'.format(self.webservice_auth_realm_base)
        authenticator = self.webservice.authenticator
        return _chain(super(WebServiceWithLdapTestCase, self)
                       ._create_webservice_auth_supplicants(),
                      (_bedframe_ldap_auth.LdapSimpleSupplicant
                        (self.ldapservice_uris[0], realm=realm,
                         basedn=self.ldapservice_users_dn,
                         authenticator=authenticator),
                       _bedframe_ldap_auth.LdapGetPasswordSupplicant
                        (self.ldapservice_uris[0],
                         realm=realm,
                         basedn=self.ldapservice_users_dn,
                         bind_dn=self.ldapservice_root_dn,
                         bind_password=self.ldapservice_root_password,
                         authenticator=authenticator),
                       ))
