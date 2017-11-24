from collections import Iterable
from functools import wraps
from itertools import islice


def validate_realm(func):
    r"""
    Checks the API realm for validity
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            realm = kwargs['api_realm']
            if not isinstance(realm, str) or realm.lower() not in (
                    'xbox', 'ps4'):
                raise ValueError('Argument "api_realm" is invalid!')
        except KeyError:
            pass
        return func(*args, **kwargs)
    return wrapper


def automerge(checkparam, limit, index=None):
    r"""
    Auto-split requests into chunk sizes accepted by the API.

    :param checkparam: Parameter to check
    :param int limit: Maximum length allowed (by API) for "checkparam"
    :param int index: Index of parameter if it is a positional argument
    """
    def decorate(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if index is not None:
                param = args[index]
            else:
                try:
                    param = kwargs[checkparam]
                except KeyError:
                    return func(*args, **kwargs)
            try:
                if len(param) > limit:
                    first = None
                    for l in chunker(param, limit):
                        if not first:
                            if index is None:
                                kwargs[checkparam] = l
                            else:
                                args = (args[:index] +
                                        (l, ) + args[index + 1:])
                            first = func(*args, **kwargs)
                        else:
                            if index is None:
                                kwargs[checkparam] = l
                            else:
                                args = (args[:index] +
                                        (l, ) + args[index + 1:])
                            res = func(*args, **kwargs)
                            first += res
                    return first
                else:
                    return func(*args, **kwargs)
            except TypeError:
                return func(*args, **kwargs)
        return wrapper
    return decorate


def _join_param(param):
    r"""
    Utility method to perform a :py:func:`join` on parameters, if necessary
    """
    return param if _not_iter(param) else ','.join(map(str, param))


def _not_iter(item):
    r"""
    Helper function to determine if the object can be iterated over. Used for
    protecting against invalid input by user for parameters that need to be
    `join`'d
    """
    return item is None or any(isinstance(item, i) for i in [str, int])


def chunker(seq, size):
    r"""
    Break data down into sizable chunks.

    All credit goes to https://stackoverflow.com/a/434328
    :param seq: Iterable data
    :type seq: list or tuple
    :param int size: Maximum length per chunk
    :return: Segmented data
    :rtype: list
    """
    for pos in range(0, len(seq), size):
        if isinstance(seq, Iterable):
            yield [s for s in islice(seq, pos, pos + size)]
        else:
            yield seq[pos:pos + size]
