TODO
----

* v0.3

  * Better documentation examples
  * PEP8 adherence
  * Client-side parameter checking

* v0.4

  * Split queries with parameters that exceed max limit

    * Ex. :py:func:`~.vehicle_info` with more than 100 tanks is split into two
      API queries
    * Results are rejoined and returned

  * :py:mod:`~.WOTXResponse` removes outer "shells" surrounding the actual data
  * Add operator support for combining :py:mod:`~.WOTXResponse` from queries

* v0.5

  * Convenience session class, :py:mod:`WOTXSession`, for auto-passing
    settings (API key, language, and platform/realm)
  
* v0.6

  * Unit tests
