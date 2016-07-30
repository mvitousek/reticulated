_len = len
def len(x:List[Any])->int:
    return _len(x)

def mean(inlist:List[Any])->int:
    return 0

def ss(inlist:List[Any])->int:
    """
Squares each value in the passed list, adds up these squares and
returns the result.

Usage:   lss(inlist)
"""
    _ss = 0
    for item in inlist:
        _ss = _ss + item*item
    return _ss
