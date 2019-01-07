def merge(d1, d2, merge_fn=lambda x,y:y):
    """
    Merges two dictionaries, non-destructively, combining 
    values on duplicate keys as defined by the optional merge
    function.  The default behavior replaces the values in d1
    with corresponding values in d2.  (There is no other generally
    applicable merge strategy, but often you'll have homogeneous 
    types in your dicts, so specifying a merge technique can be 
    valuable.)

    Examples:

    >>> d1
    {'a': 1, 'c': 3, 'b': 2}
    >>> merge(d1, d1)
    {'a': 1, 'c': 3, 'b': 2}
    >>> merge(d1, d1, lambda x,y: x+y)
    {'a': 2, 'c': 6, 'b': 4}

    """
    result = dict(d1)
    for k,v in d2.iteritems():
        if k in result:
            result[k] = merge_fn(result[k], v)
        else:
            result[k] = v
    return result

a = {'a': 1, 'c': 3, 'b': 2}
b = {'d': 4, 'c': 3}

c = merge(a, b, lambda x,y: x+y)

print(c)