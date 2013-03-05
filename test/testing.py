def answer(f, x, ans):
    return answer_t(f, (x,), ans)
def error(f, x):
    return error_t(f, (x,))

def answer_t(f, x, ans):
    try:
        val = f(*x)
    except AssertionError:
        assert False, 'test of %s%s FAILED: expected %s, got runtime type error' % (f.__name__, x, ans)
    assert val == ans, 'test of %s%s FAILED: expected %s, got %s' % (f.__name__, x, ans, val)
    print('test of %s%s ok (succeeded as expected)' % (f.__name__, x))
def error_t(f, x):
    try:
        val = f(*x)
    except AssertionError:
        print('test of %s%s ok (failed as expected)' % (f.__name__, x))
        return
    assert False, 'test of %s%s FAILED: expected runtime type error, got %s' % (f.__name__, x, val)
