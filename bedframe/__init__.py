"""Bedframe, a resource-oriented web services framework


********
Examples
********

"Hello, world" service
======================

::

    import bedframe as _bedframe
    import bedframe.webtypes as _webtypes

    class HelloWorldResource(_bedframe.WebResource):
        @_bedframe.webmethod(_webtypes.unicode)
        def get(self):
            return u'Hello, world!'

    service = _bedframe.WebService(uris=('http://localhost:8080',))
    service.resources[r'/helloworld'] = HelloWorldResource
    service.start()

Example usage (:mod:`Napper <napper>`):

    >>> import bedframe.webtypes as _webtypes
    >>> import napper as _napper
    >>> uri = 'http://localhost:8080/helloworld'
    >>> response = _napper.request_uri('get', uri)
    >>> hello = _napper.extract_retval(response, _webtypes.unicode)
    >>> print hello
    Hello, world!

Example usage (:pypi:`Requests`):

    >>> import requests as _requests
    >>> uri = 'http://localhost:8080/helloworld'
    >>> headers = {'Accept': ', '.join(('application/json', '*/*; q=0.01'))}
    >>> response = _requests.get(uri, headers=headers)
    >>> hello = response.json()['retval']
    >>> print hello
    Hello, world!

Example usage (:pypi:`HTTPie`):

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


********
Glossary
********

.. glossary::
    :sorted:

    delete
        A :term:`web method` that removes the identified resource if it
        exists.

        Delete is :term:`idempotent <idempotent web method>`.

        In HTTP, this corresponds to the ``DELETE`` method.

        .. seealso::
            :meth:`WebResource.delete() \
                   <bedframe._resources._core.WebResource.delete>`

    exception response
        A :term:`response` that indicates an exception in the execution
        of the action described by the corresponding :term:`request`.

        In addition to an appropriate :term:`status code`, an exception
        response may include

          * an identification of the exception type,

          * the exception message, or

          * a full or limited traceback of the exception.

        .. seealso::
            :class:`WebExceptionResponse
                    <bedframe._responses._exc.WebExceptionResponse>`

    get
        A :term:`web method` that retrieves a :term:`representation
        <web resource representation>` of the identified resource.

        Get is :term:`safe <safe web method>` and :term:`idempotent
        <idempotent web method>`.

        In HTTP, this corresponds to one of the following:

          * the ``GET`` method

          * the ``HEAD`` method (if the response metadata is desired
            without the resource representation)

          * a special invocation of the ``POST`` method (if the method
            arguments might cause the URI to exceed the maximum length
            allowed by HTTP if passed as a query string)

        .. seealso::
            :meth:`WebResource.get() \
                   <bedframe._resources._core.WebResource.get>`

    idempotent web method
        A :term:`web method` that produces the same effect from
        multiple identical requests as it does from one request.

    media type
    Internet media type
        A type of content that can be transmitted in a message.

        A media type is identified by a string that consists of a major
        type, a minor type, and zero or more parameters.

        Common examples include :mimetype:`application/json` and
        :mimetype:`text/html; charset=utf8`.

        Formerly known as a "MIME type".

    options
        A :term:`web method` that retrieves the capabilities of the
        identified resource.

        Options is :term:`safe <safe web method>` and :term:`idempotent
        <idempotent web method>`.

        In HTTP, this corresponds to the ``OPTIONS`` method.

        .. seealso::
            :meth:`WebResource.options() \
                   <bedframe._resources._core.WebResource.options>`

    patch
        A :term:`web method` that modifies a subset of the attributes
        of the identified resource.

        Patch is :term:`idempotent <idempotent web method>`.

        In HTTP, this corresponds to the ``PATCH`` method.

        .. seealso::
            :meth:`WebResource.patch() \
                   <bedframe._resources._core.WebResource.patch>`

    post
        A :term:`web method` that creates a new resource in the
        identified :term:`resource collection <web resource
        collection>` or a new application-specific entry in the
        identified resource.

        In HTTP, this corresponds to the ``POST`` method.

        .. seealso::
            :meth:`WebResource.post() \
                   <bedframe._resources._core.WebResource.post>`

    put
        A :term:`web method` that modifies the entire state of the
        identified resource.

        Put is :term:`idempotent <idempotent web method>`.

        In HTTP, this corresponds to the ``PUT`` method.

        .. seealso::
            :meth:`WebResource.put() \
                   <bedframe._resources._core.WebResource.put>`

    resource-oriented
        A style of distributed software architecture that focuses on
        nouns (resources and representations of their state) as the
        fundamental units of interface design.  It is characterized by
        the following tenets:

          * Interfaces are conceived, organized, and extended by
            exposing a rich set of resources accessible via a simple set
            of methods.

          * Resources may correspond to some underlying content,
            systems, or activities, or they may be abstract entities.

          * Resources may be structured via relational patterns, such as
            collections, hierarchies, or histories.

          * Each resource supports a subset of basic, common operations
            (methods).  Typically the methods perform the tasks of
            creating (:term:`post`, :term:`put`), reading (:term:`get`),
            updating (:term:`put`, :term:`patch`, :term:`post`), and
            deleting (:term:`delete`) resources.

          * A representation of a resource is a description of some of
            its state.  This may include the state of some underlying
            objects or the state of its relations to other resources.

          * Messages consist of exchanges of information about resource
            state, queries to discover it, intents to modify it, and the
            status of previously attempted operations.

        Resource-oriented architectures are often also :term:`RESTful`
        and vice versa, but there are exceptions.  The definition of
        resource-oriented architecture focuses on expressing and
        manipulating remote state via objects that correspond directly
        to that state, exposing complexity via the
        relationships among distinct objects, and using only basic
        operations to avoid the complications application-specific
        constraints and side effects.

    REST
    representational state transfer
        The style of distributed software architecture that is described
        by Roy Fielding in his doctoral dissertation
        [FieldingTaylor2002]_.

        It is defined by several constraints applied to an architecture:

          * Interactions happen between clients and servers.

          * Responses are stateless.

          * Responses are cacheable.

          * Servers can be layered.

          * Servers can provide clients with executable code.

          * Resources are identified separately from their
            representations.

          * Resources are manipulated via their representations.

          * Each message provides enough metadata to describe how to
            process it.

          * Application state and state transitions are expressed only
            in resource representations.

        :term:`RESTful` architectures are often also
        :term:`resource-oriented` and vice versa, but there are
        exceptions.  The definition of REST focuses on establishing a
        common vocabulary for messages, enabling simplifying assumptions
        to be made using little or no application-specific knowledge,
        and mandating the context-free expression of state transitions
        to avoid some of the complications of managing unpredictable
        application state over resource-constrained networks.

        .. [FieldingTaylor2002] Fielding, Roy T.; Taylor, Richard
           N. (2002-05), `"Principled Design of the Modern Web
           Architecture"`_ (PDF), ACM Transactions on Internet
           Technology (TOIT) (New York: Association for Computing
           Machinery) 2 (2): 115--150, doi:10.1145/514183.514185, ISSN
           1533-5399

        .. _"Principled Design of the Modern Web Architecture": \
           http://www.ics.uci.edu/~taylor/documents/2002-REST-TOIT.pdf

    RESTful
        Adhering to the architectural constraints defined by the
        :term:`REST` style.

    return response
        A :term:`response` that contains a requested :term:`resource
        representation <web resource representation>`.

        .. seealso::
            :class:`WebReturnResponse \
                    <bedframe._responses._return.WebReturnResponse>`

    safe web method
        A :term:`web method` that does not change the state of any of
        the :term:`service <web service>`\ 's :term:`resources <web
        resource>`.

    status code
        The part of a :term:`response` that identifies the status of the
        action described by the corresponding :term:`request`.

        In HTTP, the status code is an integer.  All HTTP status codes
        are named and listed in :mod:`spruce.http.status`.

    web API
        An API that is accessed via HTTP or a similar protocol.

    web method
        A type of action that can be performed on a :term:`web
        resource`.  One of :term:`options`, :term:`get`, :term:`post`,
        :term:`put`, :term:`patch`, or :term:`delete`.

        .. seealso:: :class:`~bedframe._methods.WebMethod`

    web request
        A message from a client to a :term:`web service` that indicates
        an intent to perform some action on some :term:`resource <web
        resource>`.

        .. seealso::
            :class:`~bedframe._requests.WebRequest`,
            :class:`napper.WebRequest <napper._requests.WebRequest>`

    web resource
        An object that is exposed by a :term:`web service`.  The service
        allows clients to invoke some :term:`methods <web method>` on
        the resource, some of which entail sending a
        :term:`representation <web resource representation>` of the
        resource to the client or receiving one from it.

        .. seealso:: :class:`~bedframe._resources._core.WebResource`

    web resource collection
        A :term:`web resource` that contains other web resources.

    web resource representation
        Message content that represents a :term:`web resource`.

        The semantics of a resource representation are identified by its
        :term:`media type`.

    web response
        A message from a server to a client that is sent in response to
        a :term:`web request`.  It indicates the status of the requested
        action.  If the action entails the retrieval of some content,
        then the response includes this content if the retrieval is
        successful.

        .. seealso::
            :class:`~bedframe._requests.WebResponse`,
            :class:`requests.Response`

    web service
        An application that provides a :term:`web API`.

        .. seealso:: :class:`~bedframe._services.WebService`


"""

__copyright__ = "Copyright (C) 2014 Ivan D Vasin"
__credits__ = ["Ivan D Vasin"]
__maintainer__ = "Ivan D Vasin"
__email__ = "nisavid@gmail.com"
__docformat__ = "restructuredtext"

from ._collections import *
from ._cors import *
from ._debug import *
from ._exc import *
from ._metadata import *
from ._methods import *
from ._requests import *
from ._resources import *
from ._responses import *
from ._services import *

# FIXME
from . import tornado
