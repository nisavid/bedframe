"""Web resource collections"""

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
from . import _core as _resources_core


class WebResourceCollection(_resources_core.WebResource):

    """A web resource collection"""

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
