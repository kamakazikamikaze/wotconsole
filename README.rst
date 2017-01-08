WOTConsole
===========

Introduction
------------

WOTConsole is a Python module for interacting with the Wargaming's developer
API, specifically for the `World of Tanks - Console <console.wargaming.com>`_ 
game. It is a tool designed for convenience and ease-of-use.

Why create another API wrapper?
-------------------------------

While Wargaming offers their own API wrapper, and another was built by a
third-party, they respectively do not have the WOTX (World of Tanks Console)
endpoints or do not have sufficient documentation to understand how to fully
utilize their libraries. As such, I took it upon myself to create one that was
thorough and easy to use.

Why not stick with `requests <http://docs.python-requests.org/en/master/>`_?
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

While the ``requests`` library may suffice for
general use, it can be a bit of a pain having to remember what parameters
should be sent and what the URL endpoint is. It's also inconvenient when
trying to code offline. This module has all of this documented and will track
the URLs for you.

`Eww, Python! <http://forum-console.worldoftanks.com/index.php?/topic/164306-spending-time-with-family-this-holiday-drove-me-to-tears-so-i-created-a-python-wrapper-for-the-console-api-instead/page__pid__3409786#entry3409786>`_
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Grow up ;)

What can it do?
---------------

WOTConsole is designed for convenience to the developer. Let's say that you're
needing to search for a tank. A regular ``requests`` implementation would be
akin to:

.. code:: python

    from __future__ import print_function
    import requests

    apikey = 'some string'

    r = requests.get(
        'https://api-xbox-console.worldoftanks.com/wotx/encyclopedia/vehicles',
        params={
          'application_id': apikey,
          'tank_id': '1' # This is the Russian T-34
        }
    )

    try:
        r.raise_for_status() # Verify we have a valid response
        info = r.json()
        print(info['data']['1']['short_name']) # T-34
    except Exception as e:
       print r.content

This is very simple, but there are some inconveniences:

1. The developer would need to track the platform API (Xbox vs PS4) per call
2. The developer needs to manually enter the endpoint
3. `'tank_id'` is designated as a list on the API, so the user(s) may enter
   more than one tank. What if it's a mix of `int` and `str`?
4. The amount of nested dictionaries can be cumbersome and code length can be
   rather long
5. If this were a function and the `Exception` was not caught, those variables
   are lost once the program leaves the scope. This may make debugging a little
   tricky as programs grow in size

This module intends to address some of these issues and even those that most
developers may not care for. We can rewrite the code as follows:

.. code:: python

    from __future__ import print_function
    from copy import copy
    from wotconsole import tank_info

    apikey = 'some string'

    try:
        # You can specify the platform and language you want.
        psinfo = tank_info(apikey, tank_id='1', api_realm='ps4', language='ru')
        # Some parameters accept lists of multiple types
        xinfo = tank_info(apikey, tank_id=[1, '257'])

        print type(psinfo) # This is a WOTXResponse
        # The data returned was a dictionary; the instance will behave as one
        for tank_id, data in psinfo.iteritems(): 
            print(tank_id, data)

        # You can directly access the data using indices
        print(xinfo['1']['short_name'])
        print(xinfo['257']['short_name'])

        # Should you need to `copy` the data, access it as an attribute
        copied = copy(xinfo.data)
        print(type(copied))
    
    except WOTXResponseError as wat:
        # If an error occurs from bad parameters being sent to the API, the
        # `Exception` will instead use the error message sent back in the JSON.
        print(wat)
        # The JSON becomes part of the `Exception`, allowing for debugging even
        # outside of a method's scope.
        print(wat.error['code'])
        print(wat.error['field'])

        # Both `WOTXResponse` and `WOTXResponseError` save the original
        # `requests` instance, just in case the developer wishes to review the
        # parameters, URL, etc.
        print(type(wat.raw))

.. include:: TOOD.rst
