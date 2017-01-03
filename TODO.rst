.. module::wotconsole

TODO
====

v0.2
^^^^

* Finish documentation
* Unit tests

v0.3
^^^^

* Client-side parameter checking
* Split queries with parameters that exceed max limit
   * Ex. :py:func:`vehicle_info` with more than 100 tanks is split into two API queries
   * Results are rejoined and returned

v0.4
^^^^

* :py:func:`WOTXResponse` removes outer "shells" surrounding the actual data

v0.5
^^^^

* Convenience session class, `WOTXSession`, for auto-passing preferences like
  API key, language, and platform/realm
  