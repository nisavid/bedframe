########
Bedframe
########

Bedframe is a resource-oriented web services framework.


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
