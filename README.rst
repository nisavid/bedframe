.. admonition::
    :class: note
    ⚰️ **Dead:** This project is unmaintained.

########
Bedframe
########

Bedframe is a resource-oriented web services framework.


************
Installation
************

A Bedframe service runs on an underlying web server.  Support for each
particular web server is provided via a corresponding plugin.  Bedframe
releases include some web server plugins, which are activated by
installing their corresponding package extras.  These are the currently
supported extras:

  ``tornado``
    Support for the Tornado_ web server (via tornado.web.Application_).

  ``tornado_wsgi``
    Support for the Tornado_ WSGI web server
    (via tornado.wsgi.WSGIApplication_).

For example, to install Bedframe with support for the Tornado WSGI web
server, you can run

.. code-block:: bash

    pip install bedframe[tornado_wsgi]

In addition, Bedframe supports these other extras:

  ``ldap``
    Support for the `Lightweight Directory Access Protocol`_ (LDAP) for
    authentication (via python-ldap_).

  ``memcached``
    Support for memcached_ for authentication (via python-memcached_).

  ``test_ldap``
    Support for the `Lightweight Directory Access Protocol`_ (LDAP) for
    automated testing (via Spruce-ldap_ and OpenLDAP_).


.. _Lightweight Directory Access Protocol:
    https://tools.ietf.org/html/rfc4510

.. _memcached: http://www.memcached.org/

.. _OpenLDAP: http://www.openldap.org/

.. _python-ldap: https://pypi.python.org/pypi/python-ldap

.. _python-memcached: https://pypi.python.org/pypi/python-memcached

.. _Spruce-ldap: https://pypi.python.org/pypi/Spruce-ldap

.. _Tornado: http://www.tornadoweb.org/

.. _tornado.web.Application:
    http://www.tornadoweb.org/en/stable/web.html#tornado.web.Application

.. _tornado.wsgi.WSGIApplication:
    http://www.tornadoweb.org/en/stable/wsgi.html#tornado.wsgi.WSGIApplication


********
Examples
********

"Hello, world" service
======================

.. code-block:: python

    import bedframe as _bedframe
    import bedframe.webtypes as _webtypes

    class HelloWorldResource(_bedframe.WebResource):
        @_bedframe.webmethod(_webtypes.unicode)
        def get(self):
            return u'Hello, world!'

    service = _bedframe.WebService(uris=('http://localhost:8080',))
    service.resources[r'/helloworld'] = HelloWorldResource
    service.start()

Example usage (Napper):

.. code-block:: python

    >>> import bedframe.webtypes as _webtypes
    >>> import napper as _napper
    >>> uri = 'http://localhost:8080/helloworld'
    >>> response = _napper.request_uri('get', uri)
    >>> hello = _napper.extract_retval(response, _webtypes.unicode)
    >>> print hello
    Hello, world!

Example usage (`Requests <https://pypi.python.org/pypi/requests>`_):

.. code-block:: python

    >>> import requests as _requests
    >>> uri = 'http://localhost:8080/helloworld'
    >>> headers = {'Accept': ', '.join(('application/json', '*/*; q=0.01'))}
    >>> response = _requests.get(uri, headers=headers)
    >>> hello = response.json()['retval']
    >>> print hello
    Hello, world!

Example usage (`HTTPie <https://pypi.python.org/pypi/httpie>`_):

.. code-block:: bash

    $ uri='http://localhost:8080/helloworld'
    $ http get "$uri" Accept:'application/json,*/*; q=0.01' --body
    {
        "auth_info": {
            "accepted": null,
            "realm": null,
            "user": null
        },
        "retval": "Hello, world!",
        "type": "bedframe._responses._return:WebReturnResponse"
    }
