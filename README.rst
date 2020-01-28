`WOTConsole <https://bitbucket.org/kamakazikamikaze/wotconsole>`_
=================================================================

Introduction
------------

WOTConsole is a Python module for interacting with the Wargaming's developer
API, specifically for the `World of Tanks - Console 
<https://console.wargaming.com>`_  game. It is a tool designed for convenience
and ease-of-use.

|docs|

Why create another API wrapper?
-------------------------------

While Wargaming offers their own API wrapper, and another was built by a
third-party, they respectively do not have the WOTX (World of Tanks Console)
endpoints or do not have sufficient documentation to understand how to fully
utilize their libraries. As such, I took it upon myself to create one that was
thorough and easy to use.

Why not stick with `requests <https://pypi.org/project/requests/>`?
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

While the ``requests`` library may suffice for
general use, it can be a bit of a pain having to remember what parameters
should be sent and what the URL endpoint is. It's also inconvenient when
trying to code offline. This module has all of this documented and will track
the URLs for you.

`Eww, Python! <https://goo.gl/3rsOt4>`_
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Grow up ;)

What can it do?
---------------

WOTConsole is designed for convenience to the developer. Let's say that you're
needing to search for a tank.

This module intends to address some of these issues and even those that most
developers may not care for. We can rewrite the code as follows:

.. code:: python

    >>> from __future__ import print_function
    >>> from copy import copy
    >>> from wotconsole import tank_info

    >>> apikey = 'demo'

    # You can specify the platform and language you want.
    >>> psinfo = vehicle_info(apikey, tank_id='1', fields=['short_name',
    ... 'tier', 'type', 'nation'], api_realm='ps4', language='ru')

    # Some parameters accept lists of multiple types
    >>> xinfo = tank_info(apikey, tank_id=[1, '257'])
    >>> print type(psinfo)
    <class 'wotconsole.WOTXResponse'>

    # The data returned was a dictionary; the WOTXResponse will behave as one
    >>> for tank_id, data in psinfo.iteritems(): 
    ...    print(tank_id, data)
    1 {u'tier': 5, u'type': u'mediumTank', u'short_name': u'T-34',
       u'nation': u'ussr'}
    
    # You can directly access the data using indices
    >>> print(xinfo['1']['short_name'])
    T-34
    >>> print(xinfo['257']['short_name'])
    SU-85

    # Should you need to `copy` the data, access it as an attribute
    >>> copied = copy(xinfo.data)
    >>> print(type(copied))
    <type 'dict'>

    >>> try:
    ...     vehicle_info(apikey, tank_id='A')
    
    >>> except WOTXResponseError as wat:
    # If an error occurs from bad parameters being sent to the API, the
    # `Exception` will instead use the error message sent back in the JSON.
    ...     print(wat)
    INVALID_TANK_ID
    
    # The JSON becomes part of the `Exception`, allowing for debugging even
    # outside of a method's scope.
    ...     print(wat.error['code'])
    407
    ...     print(wat.error['field'])
    tank_id

    # Both `WOTXResponse` and `WOTXResponseError` save the original
    # `requests` instance, just in case the developer wishes to review the
    # parameters, URL, etc.
    ...     print(type(wat.raw))
    <class 'requests.models.Response'>

What improvements will we see?
------------------------------

An up-to-date list of planned features will always be in the TODO.rst
file.

.. |docs| image:: https://readthedocs.org/projects/docs/badge/?version=latest
    :alt: Documentation Status
    :scale: 100%
    :target: https://wotconsole.readthedocs.io/en/latest/?badge=latest
