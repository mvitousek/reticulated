import math

_pow = pow
_abs = abs
_round = round

def pow(x:float, y:float)->float:
    return _pow(x,y)

def sqrt(x:float)->float:
    try:
        return math.sqrt(x)
    except ValueError as e:
        raise ValueError(e, x, type(x))
    return 0

def exp(x:float)->float:
    return math.exp(x)

def abs(x:float)->float:
    return _abs(x)

def fabs(x:float)->float:
    return math.fabs(x)

def log(x:float)->float:
    return math.log(x)

def round(*args)->float:
    return _round(*args)

pi = float(math.pi)
