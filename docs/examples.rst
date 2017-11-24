Coding Samples
==============

There are many ways to use this library. Please be responsible and not be "that
guy" who uses it as a jackhammer to pound the crap out of the API.

A primer on the API behavior
----------------------------

Let's start with the basics. Search all players for me (Kamakazi Rusher)

.. code:: python

    >>> from wotconsole import WOTXSession as Session
    >>> sess = Session() # We'll use the 'demo' API key for now
    >>> kr = sess.player_search('Kamakazi Rusher')
    >>> kr.data
    [{u'nickname': u'Kamakazi Rusher', u'account_id': 2631240}]

Easy enough! You'll notice that the JSON returned by the API is saved as the
attribute ``WOTXResponse.data``. For this method, it returns it as a nested
dictionary within a list. This is because the API can return multiple items.
If we instead search for all player names starting with "Kamakazi R", we will
get at least two players back.

.. code:: python

    >>> ks = sess.player_search('Kamakazi R')
    >>> ks.data
    [{u'nickname': u'Kamakazi Rebel', u'account_id': 4900488},
     {u'nickname': u'Kamakazi Rusher', u'account_id': 2631240}]

Not all methods will return lists. Some will return just nested dictionaries.

.. code:: python

    >>> t = sess.vehicle_info(tank_id=1, fields=['short_name', 'type'])
    >>> t.data
    {u'1': {u'type': u'mediumTank', u'short_name': u'T-34'}}

Be careful with methods that return dictionaries. You'll notice that while we
asked for a tank using an int, it returns it in the dictionary as a str instead

.. code:: python

    >>> t.data[1]  # KeyError will be thrown
    Traceback (most recent call last):
      File "<stdin>", line 1, in <module>
    KeyError: 1
    >>> t.data['1'] # No errors!
    {u'1': {u'type': u'mediumTank', u'short_name': u'T-34'}}

This is the default behavior of the API. I will *not* support automatic
conversion of keys in the dictionaries!

If information for a player/tank/etc. is requested but does not exist in the
database, it will be returned as a None value.

.. code:: python

    >>> p = sess.player_data(1)
    >>> p.data
    {u'1': None}

Exceeding parameter limits
--------------------------

Some methods have limitations on how many items you can request information for
in one go. To accomodate for this, these methods will automagically split up
the parameter into multiple requests and return them as one object.

For example, ``wotconsole.player_data`` has a max limit of 100 player IDs per
request as per the API documentation. If you attempt to send more than 100
directly to the API, it will return an error code.

.. code:: python

    >>> import requests
    >>> res = requests.get('https://api-xbox-console.worldoftanks.com/wotx/account/info/', params={
    ...   'application_id': 'demo',
    ...   'account_id': ','.join(map(str, range(5000,5101)))  # 101 IDs
    ... },
    ... timeout=10).json()
    >>> res
    {u'status': u'error', u'error': {u'field': u'account_id', u'message': u'ACCOUNT_ID_LIST_LIMIT_EXCEEDED', u'code': 407, . . . }

As of release v0.4, the library will auto-split parameters that have these
limitations. For example,

.. code:: python

    >>> players = sess.player_data(range(5000, 5101), fields=['nickname'])
    >>> players.meta
    {u'count': 101}
    >>> players.meta['count'] == len(players.data)
    True

