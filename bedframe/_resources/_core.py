"""Web resources core"""

__copyright__ = "Copyright (C) 2014 Ivan D Vasin"
__docformat__ = "restructuredtext"

import cgi as _cgi
from textwrap import dedent as _dedent

from spruce.collections import odict as _odict
from spruce.pprint import indented as _indented

from .. import _debug
from .. import _exc
from .. import _metadata
from .. import _methods as _meth
from .. import _responses
from .. import webtypes as _webtypes


class WebResource(object):

    """A web resource"""

    @_meth.webmethod()
    def __init__(self):
        self._currently_avoiding_auth = False
        self._currently_avoiding_auth_reason = None
        self._current_request = None
        self._current_service = None

    @__init__.type('application/json')
    def __init__(self, value, **args):
        return self._return_response_json_content(value, **args)

    @__init__.type('application/json', _responses.WebExceptionResponse)
    def __init__(self, data):
        return self._exc_response_json_content(data)

    @__init__.type('application/json', _responses.WebResponseRedirectionResponse)
    def __init__(self, data):
        return self._response_redirect_response_json_content(data)

    @__init__.type('text/html')
    def __init__(self, value, **args):
        return self._return_response_html_content(value, **args)

    @__init__.type('text/html', _responses.WebExceptionResponse)
    def __init__(self, data):
        return self._exc_response_html_content(data)

    @__init__.type('text/html', _responses.WebResponseRedirectionResponse)
    def __init__(self, data):
        return self._exc_response_html_content(data)

    def __repr__(self):
        # FIXME: include args
        return '{}()'.format(self.__class__.__name__)

    @classmethod
    def all_webmethodnames(cls):
        """The names of the web methods defined for this resource

        :type: [:obj:`str`]

        """
        return [name for name in dir(cls)
                if name != '__init__'
                   and isinstance(getattr(cls, name), _meth.WebMethod)]

    @classmethod
    def allowed_webmethodnames(cls):
        """The names of the web methods allowed for this resource

        :type: [:obj:`str`]

        """
        names = []
        for name in dir(cls):
            attr = getattr(cls, name)
            if name != '__init__' \
                   and isinstance(attr, _meth.WebMethod) \
                   and not isinstance(attr, _meth.DisallowedWebMethod):
                names.append(name)
        return names

    def avoiding_auth(self, reason=None):
        return self._AvoidingAuthContext(self, reason)

    @property
    def current_auth_info(self):
        """The current request's authentication information

        If this resource is not currently being provided for any request, then
        this is :obj:`None`.

        :type: :class:`~bedframe.auth._info.RequestAuthInfo` or null

        """
        if self.current_request:
            return self.current_request.auth_info
        else:
            return None

    @property
    def current_debug_flags(self):
        """The current debugging flags

        If no service is currently servicing a request for this resource, then
        this is :obj:`None`.

        :type: :class:`~bedframe._debug.DebugFlagSet` or null

        """
        if self.current_service:
            return self.current_service.debug_flags
        else:
            return None

    @property
    def current_request(self):
        """The current request

        If this resource is not currently being provided for any request, then
        this is :obj:`None`.

        :type: :class:`~bedframe._requests.WebRequest` or null

        """
        if self.current_service:
            return self.current_service.current_request
        else:
            return None

    @property
    def current_service(self):
        """The current service

        If no service is currently servicing a request for this resource, then
        this is :obj:`None`.

        :type: :class:`~bedframe._services.WebService` or null

        """
        return self._current_service

    @property
    def currently_avoiding_auth(self):
        return self._currently_avoiding_auth

    @property
    def currently_avoiding_auth_reason(self):
        return self._currently_avoiding_auth_reason

    @_meth.disallowed_webmethod
    def delete(self):
        pass

    @delete.type('application/json')
    def delete(self, value, **args):
        return self._return_response_json_content(value, **args)

    @delete.type('application/json', _responses.WebExceptionResponse)
    def delete(self, data):
        return self._exc_response_json_content(data)

    @delete.type('application/json', _responses.WebResponseRedirectionResponse)
    def delete(self, data):
        return self._response_redirect_response_json_content(data)

    @delete.type('text/html')
    def delete(self, value, **args):
        return self._return_response_html_content(value, **args)

    @delete.type('text/html', _responses.WebExceptionResponse)
    def delete(self, data):
        return self._exc_response_html_content(data)

    @delete.type('text/html', _responses.WebResponseRedirectionResponse)
    def delete(self, data):
        return self._exc_response_html_content(data)

    def ensure_auth(self, **kwargs):
        """Ensure authentication

        .. seealso::
            :meth:`WebRequest.ensure_auth()
                   <bedframe._requests.WebRequest.ensure_auth>`

        """
        if self.currently_avoiding_auth:
            raise _exc.AvoidingAuth(self)
        else:
            self.current_request.ensure_auth(**kwargs)

    @_meth.disallowed_webmethod
    def get(self):
        pass

    @get.type('application/json')
    def get(self, value, **args):
        return self._return_response_json_content(value, **args)

    @get.type('application/json', _responses.WebExceptionResponse)
    def get(self, data):
        return self._exc_response_json_content(data)

    @get.type('application/json', _responses.WebResponseRedirectionResponse)
    def get(self, data):
        return self._response_redirect_response_json_content(data)

    @get.type('text/html')
    def get(self, value, **args):
        return self._return_response_html_content(value, **args)

    @get.type('text/html', _responses.WebExceptionResponse)
    def get(self, data):
        return self._exc_response_html_content(data)

    @get.type('text/html', _responses.WebResponseRedirectionResponse)
    def get(self, data):
        return self._exc_response_html_content(data)

    def has_auth(self, **kwargs):
        """Whether the current request is authenticated

        .. seealso::
            :meth:`WebRequest.has_auth()
                   <bedframe._requests.WebRequest.has_auth>`

        """
        return self.current_request.has_auth(**kwargs)

    @_meth.webmethod()
    def options(self):
        pass

    @options.type('application/json')
    def options(self, value, **args):
        return self._return_response_json_content(value, **args)

    @options.type('application/json', _responses.WebExceptionResponse)
    def options(self, data):
        return self._exc_response_json_content(data)

    @options.type('application/json', _responses.WebResponseRedirectionResponse)
    def options(self, data):
        return self._response_redirect_response_json_content(data)

    @options.type('text/html')
    def options(self, value, **args):
        return self._return_response_html_content(value, **args)

    @options.type('text/html', _responses.WebExceptionResponse)
    def options(self, data):
        return self._exc_response_html_content(data)

    @options.type('text/html', _responses.WebResponseRedirectionResponse)
    def options(self, data):
        return self._exc_response_html_content(data)

    @classmethod
    def partial_inst(cls, *args, **kwargs):
        @classmethod
        def unpartial_class(cls_):
            return cls
        attrs = {'__init__': cls.__init__.partial(*args, **kwargs),
                 'unpartial_class': unpartial_class}
        return type('{}_PartialInst'.format(cls.__name__), (cls,), attrs)

    @_meth.disallowed_webmethod
    def patch(self):
        pass

    @patch.type('application/json')
    def patch(self, value, **args):
        return self._return_response_json_content(value, **args)

    @patch.type('application/json', _responses.WebExceptionResponse)
    def patch(self, data):
        return self._exc_response_json_content(data)

    @patch.type('application/json', _responses.WebResponseRedirectionResponse)
    def patch(self, data):
        return self._response_redirect_response_json_content(data)

    @patch.type('text/html')
    def patch(self, value, **args):
        return self._return_response_html_content(value, **args)

    @patch.type('text/html', _responses.WebExceptionResponse)
    def patch(self, data):
        return self._exc_response_html_content(data)

    @patch.type('text/html', _responses.WebResponseRedirectionResponse)
    def patch(self, data):
        return self._exc_response_html_content(data)

    @_meth.disallowed_webmethod
    def post(self):
        pass

    @post.type('application/json')
    def post(self, value, **args):
        return self._return_response_json_content(value, **args)

    @post.type('application/json', _responses.WebExceptionResponse)
    def post(self, data):
        return self._exc_response_json_content(data)

    @post.type('application/json', _responses.WebResponseRedirectionResponse)
    def post(self, data):
        return self._response_redirect_response_json_content(data)

    @post.type('text/html')
    def post(self, value, **args):
        return self._return_response_html_content(value, **args)

    @post.type('text/html', _responses.WebExceptionResponse)
    def post(self, data):
        return self._exc_response_html_content(data)

    @post.type('text/html', _responses.WebResponseRedirectionResponse)
    def post(self, data):
        return self._exc_response_html_content(data)

    def provided_by_service(self, service):
        """
        A context whereby this resource is provided by a particular service

        :param service:
            A service.
        :type request: :class:`~bedframe._services.WebService`

        :rtype: context

        """
        return self._ProvidedByServiceContext(self, service)

    def provided_for_request(self, request):
        """
        A context whereby this resource is provided for a particular request

        :param request:
            A request.
        :type request: :class:`~bedframe._requests.WebRequest`

        :rtype: context

        """
        return self._ProvidedForRequestContext(self, request)

    @_meth.disallowed_webmethod
    def put(self):
        pass

    @put.type('application/json')
    def put(self, value, **args):
        return self._return_response_json_content(value, **args)

    @put.type('application/json', _responses.WebExceptionResponse)
    def put(self, data):
        return self._exc_response_json_content(data)

    @put.type('application/json', _responses.WebResponseRedirectionResponse)
    def put(self, data):
        return self._response_redirect_response_json_content(data)

    @put.type('text/html')
    def put(self, value, **args):
        return self._return_response_html_content(value, **args)

    @put.type('text/html', _responses.WebExceptionResponse)
    def put(self, data):
        return self._exc_response_html_content(data)

    @put.type('text/html', _responses.WebResponseRedirectionResponse)
    def put(self, data):
        return self._exc_response_html_content(data)

    @classmethod
    def webmethodnames(cls):
        """The names of this resource's defined web methods

        :type: [:obj:`str`]

        """
        return [name for name in dir(cls)
                if isinstance(getattr(cls, name), _meth.WebMethod)]

    def _auth_info_facet_html(self, facet):
        if facet is not None and facet.realm is not None:
            html = '<h2>Authentication information</h2>'\
                    '\n\n<dl class="auth_info">\n\n  '
            html += \
                '\n\n  '.join\
                 ('<dt><code class="auth_info_attr_name">{}</code></dt>'
                   '\n  <dd><code class="auth_info_attr_value">{}</code></dd>'
                   .format(_cgi.escape(name), _cgi.escape(value.json()))
                  for name, value
                  in (('realm', facet.realm), ('user', facet.user),
                      ('accepted', facet.accepted)))
            html += '\n\n</dl>'
        else:
            html = ''
        return html

    def _exc_response_html_content(self, data):

        def indented(string, level=1):
            return _indented(string, level, size=2)

        html = '''\
               <!DOCTYPE html>
               <html>

               <head>

                 <title>{title}</title>

                 <style type="text/css">
               {css}
                 </style>

               </head>

               <body>

                 <h1>{title}</h1>

               {message_html}

               {tech_details_html}

               {auth_info_html}

               </body>

               </html>
               '''
        html = _dedent(html)
        css_blocks = []

        exc_facet = data['exc']

        if _debug.DEBUG_EXC_NAME in exc_facet.debug_flags:
            displayname = exc_facet.displayname or exc_facet.name
            title = displayname[0].upper()
            if len(displayname) > 1:
                title += displayname[1:]
        else:
            title = 'Error'

        class_def_info_css = '''\
                             dl.class_def_info > dt {
                               font-weight: bold;
                             }
                             '''
        css_blocks.append(_dedent(class_def_info_css))

        if exc_facet.message \
               and _debug.DEBUG_EXC_MESSAGE in exc_facet.debug_flags:
            message_html = '<p class="exc_str">{}</p>'\
                            .format(_cgi.escape(exc_facet.message))
            message_html = indented(message_html)
        else:
            message_html = ''

        if _debug.DEBUG_EXC_INSTANCE_INFO in exc_facet.debug_flags:
            tech_details_html = \
                '''\
                <h2>Technical details</h2>

                <h3>Exception class</h3>

                <dl class="exc_class_def_info">

                  <dt>Module</dt>
                  <dd><code class="exc_class_def_module">{class_def_module}</code></dd>

                  <dt>Name</dt>
                  <dd><code class="exc_name">{name}</code></dd>

                </dl>

                {args_html}

                {traceback_html}
                '''
            tech_details_html = indented(_dedent(tech_details_html))

            if exc_facet.args:
                css = '''\
                      ol.exc_args {
                        padding: 0;
                        list-style: none;
                        counter-reset: arg -1;
                      }

                      ol.exc_args > li::before {
                        font-family: monospace;
                        counter-increment: arg;
                        content: "args[" counter(arg) "]: ";
                      }
                      '''
                css_blocks.append(_dedent(css))

                args_html = \
                    '<h3>Exception arguments</h3>'\
                     '\n\n<ol class="exc_args">\n\n  '
                args_html += \
                    '\n  '.join('<li><code class="exc_arg">{}</code></li>'
                                 .format(_cgi.escape(arg))
                                for arg in exc_facet.args)
                args_html += '\n\n</ol>'
                args_html = indented(args_html)
            else:
                args_html = ''

            if exc_facet.traceback \
                   and _debug.DEBUG_EXC_TRACEBACK in exc_facet.debug_flags:
                traceback_html = \
                    '<h3>Traceback</h3>'\
                     '\n\n<pre><code class="exc_traceback">{}</code></pre>'\
                     .format(_cgi.escape(exc_facet.traceback))
                traceback_html = indented(traceback_html)
            else:
                traceback_html = ''

            tech_details_html = \
                tech_details_html\
                    .format(class_def_module=
                                _cgi.escape(exc_facet.class_def_module),
                            name=_cgi.escape(exc_facet.name),
                            args_html=args_html,
                            traceback_html=traceback_html)

        try:
            auth_info_facet = data['auth_info']
        except KeyError:
            auth_info_html = ''
        else:
            auth_info_html = \
                indented(self._auth_info_facet_html(auth_info_facet))

        css = ''.join(indented(block, 2) for block in css_blocks)
        html = html.format(title=_cgi.escape(title),
                           css=css,
                           message_html=message_html,
                           tech_details_html=tech_details_html,
                           auth_info_html=auth_info_html)
        return html

    def _exc_response_json_content(self, data):

        struct = \
            _odict((('type',
                     _webtypes.ClassDefInfo
                      (_metadata.ClassDefInfo.fromclass(data.response_type))
                      .prim()),
                    ))

        exc_facet = data['exc']
        if _debug.DEBUG_EXC_NAME in exc_facet.debug_flags:
            struct['name'] = exc_facet.name
            struct['displayname'] = exc_facet.displayname
        if _debug.DEBUG_EXC_MESSAGE in exc_facet.debug_flags:
            struct['message'] = exc_facet.message
        if _debug.DEBUG_EXC_INSTANCE_INFO in exc_facet.debug_flags:
            struct['class_def_module'] = exc_facet.class_def_module
            struct['args'] = exc_facet.args
        if exc_facet.traceback is not None \
               and _debug.DEBUG_EXC_TRACEBACK in exc_facet.debug_flags:
            struct['traceback'] = exc_facet.traceback

        try:
            auth_info_facet = data['auth_info']
        except KeyError:
            pass
        else:
            struct['auth_info'] = \
                _odict((('realm', auth_info_facet.realm),
                        ('user', auth_info_facet.user),
                        ('accepted', auth_info_facet.accepted)))

        return _webtypes.json_dumps(struct)

    def _response_redirect_response_json_content(self, data):
        struct = \
            _odict((('type',
                     _webtypes.ClassDefInfo
                      (_metadata.ClassDefInfo.fromclass(data.response_type))
                      .prim()),
                    ))

        redirect_facet = data['response_redirect']
        struct['loc'] = redirect_facet.loc
        struct['message'] = redirect_facet.message

        exc_facet = data['exc']
        if _debug.DEBUG_EXC_NAME in exc_facet.debug_flags:
            struct['exc_name'] = exc_facet.name
            struct['exc_displayname'] = exc_facet.displayname
        if _debug.DEBUG_EXC_MESSAGE in exc_facet.debug_flags:
            struct['exc_message'] = exc_facet.message
        if _debug.DEBUG_EXC_INSTANCE_INFO in exc_facet.debug_flags:
            struct['exc_class_def_module'] = exc_facet.class_def_module
            struct['exc_args'] = exc_facet.args
        if exc_facet.traceback is not None \
               and _debug.DEBUG_EXC_TRACEBACK in exc_facet.debug_flags:
            struct['exc_traceback'] = exc_facet.traceback

        try:
            auth_info_facet = data['auth_info']
        except KeyError:
            pass
        else:
            struct['auth_info'] = \
                _odict((('realm', auth_info_facet.realm),
                        ('user', auth_info_facet.user),
                        ('accepted', auth_info_facet.accepted)))

        return _webtypes.json_dumps(struct)

    def _return_response_html_content(self, value, **args):

        def indented(string, level=1):
            return _indented(string, level, size=2)

        html = '''\
               <!DOCTYPE html>
               <html>

               <head>
                 <title>{resource_name}</title>
               </head>

               <body>

                 <h1>{resource_name}</h1>

               {retval_html}

               {args_html}

               {auth_info_html}

               </body>

               </html>
               '''
        html = _dedent(html)

        if value:
            retval_html = \
                '<h2>Return value</h2>'\
                 '\n\n<p><code class="retval">{}</code></p>'\
                 .format(_cgi.escape(value.json()))
        else:
            retval_html = ''

        if args:
            args_html = '<h2>Given arguments</h2>\n\n<dl class="args">\n\n  '
            args_html += \
                '\n\n  '.join('<dt><code class="arg_name">{}</code></dt>'
                               '\n  <dd><code class="arg_value">{}</code></dd>'
                               .format(_cgi.escape(name),
                                       _cgi.escape(value.json()))
                              for name, value in sorted(args.items()))
            args_html += '\n\n</dl>'
        else:
            args_html = ''

        # XXX: use out-of-band current auth info
        # FIXME: use in-band auth info via auth info facet
        auth_info = self.current_auth_info
        auth_info_html = indented(self._auth_info_facet_html(auth_info))

        html = html.format(resource_name=_cgi.escape(self.__class__.__name__),
                           retval_html=retval_html, args_html=args_html,
                           auth_info_html=auth_info_html)
        return html

    def _return_response_json_content(self, value, **args):

        struct = _odict((('type',
                          _webtypes.ClassDefInfo
                           (_metadata.ClassDefInfo
                             .fromclass(_responses.WebReturnResponse))
                           .prim()),
                         ('retval', value.prim()),
                         ))

        # XXX: use out-of-band current auth info
        # FIXME: use in-band auth info via auth info facet
        auth_info = self.current_auth_info
        if auth_info:
            realm = auth_info.realm
            try:
                user = auth_info.user
            except AttributeError:
                user = None
            accepted = auth_info.accepted
        else:
            realm = None
            user = None
            accepted = False
        struct['auth_info'] = _odict((('realm', realm), ('user', user),
                                      ('accepted', accepted)))

        return _webtypes.json_dumps(struct)

    class _AvoidingAuthContext(object):

        def __init__(self, resource, reason=None):
            self._reason = reason
            self._resource = resource

        def __enter__(self):
            self.resource._currently_avoiding_auth = True
            self.resource._currently_avoiding_auth_reason = self.reason

        def __exit__(self, exc_type, exc_val, exc_tb):
            self.resource._currently_avoiding_auth = False
            self.resource._currently_avoiding_auth_reason = None

        @property
        def reason(self):
            return self._reason

        @property
        def resource(self):
            return self._resource

    class _ProvidedByServiceContext(object):

        def __init__(self, resource, service):
            self._service = service
            self._resource = resource

        def __enter__(self):
            self.resource._current_service = self.service

        def __exit__(self, exc_type, exc_val, exc_tb):
            self.resource._current_service = None

        @property
        def resource(self):
            return self._resource

        @property
        def service(self):
            return self._service

    class _ProvidedForRequestContext(object):

        def __init__(self, resource, request):
            self._request = request
            self._resource = resource

        def __enter__(self):

            if not self.resource.current_service:
                raise RuntimeError('cannot set request context without prior'
                                    ' service context')

            self.resource.current_service.current_request = self.request

        def __exit__(self, exc_type, exc_val, exc_tb):
            if self.resource.current_service:
                self.resource.current_service.current_request = None

        @property
        def request(self):
            return self._request

        @property
        def resource(self):
            return self._resource
