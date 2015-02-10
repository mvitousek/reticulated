_len = len
def len(x:List(Dyn))->int:
    return _len(x)

def mean(inlist:List(float))->float:
    return 0.0

def ss(inlist:List(float))->float:
    """
Squares each value in the passed list, adds up these squares and
returns the result.

Usage:   lss(inlist)
"""
    _ss = 0
    for item in inlist:
        _ss = _ss + item*item
    return _ss
