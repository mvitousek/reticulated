def retic_cast(val, *args):
    return val
def retic_check(val, *args):
    return val

class DelayedStaticTypeError(Exception):
    pass

def retic_error(msg):
    raise DelayedStaticTypeError(msg)

def retic_actual(val):
    return val
