import inspect

def curry(func, *args, **kwargs):

    '''
    This decorator make your functions and methods curried.

    Usage:
    >>> adder = curry(lambda (x, y): (x + y))
    >>> adder(2, 3)
    >>> adder(2)(3)
    >>> adder(y = 3)(2)
    '''

    assert inspect.getargspec(func)[1] == None, 'Currying can\'t work with *args syntax'
    assert inspect.getargspec(func)[2] == None, 'Currying can\'t work with *kwargs syntax'
    assert inspect.getargspec(func)[3] == None, 'Currying can\'t work with defaults arguments'

    if (len(args) + len(kwargs)) >= func.__code__.co_argcount:

        return func(*args, **kwargs)

    return (lambda *x, **y: curry(func, *(args + x), **dict(kwargs, **y)))