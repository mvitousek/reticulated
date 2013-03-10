def answer(f, *x, ans):
    try:
        val = f(*x)
    except AssertionError as err:
        assert False, 'test of %s%s FAILED: expected %s, got runtime type error with message: %s' % (f.__name__, x, ans, err.args[0])
    assert val == ans, 'test of %s%s FAILED: expected %s, got %s' % (f.__name__, x, ans, val)
    print('test of %s%s ok (succeeded as expected)' % (f.__name__, x))
def error(f, *x):
    try:
        val = f(*x)
    except AssertionError as err:
        print('test of %s%s ok (failed as expected with message: %s)' % (f.__name__, x, err.args[0]))
        return
    assert False, 'test of %s%s FAILED: expected runtime type error, got %s' % (f.__name__, x, val)
