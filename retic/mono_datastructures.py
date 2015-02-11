from .monotonic import retic_cast
from .relations import info_join
from . import rtypes

class MonoList(list):
    def __init__(self, *x, error=None, line=None, type=Dyn):
        super().__init__(*x)
        assert error is not None
        assert line is not None
        self.__error__ = error
        self.__line__ = line
        self.__fastsetitem__ = super().__setitem__
        self.__fastgetitem__ = super().__getitem__
        self.__monotonic__ = type
    
    def __setitem__(self, k, v):
        v = retic_cast(v, rtypes.Dyn, self.__monotonic__, self.__error__, line=self.__line__)
        super().__setitem__(k, v)
        
    def __setitem_attype__(self, k, v, t):
        v = retic_cast(v, t, self.__monotonic__, self.__error__, line=self.__line__)
        super().__setitem__(k, v)

    def __getitem__(self, k):
        v = super().__getitem__(k)
        return retic_cast(v, self.__monotonic__, rtypes.Dyn, self.__error__, line=self.__line__)
        
    def __getitem_attype__(self, k, t):
        v = super().__getitem__(k)
        return retic_cast(v, self.__monotonic__, t, self.__error__, line=self.__line__)

    def __monotonic_cast__(self, ty, error, line):
        newmono = info_join(ty, self.__monotonic__)
        if newmono != self.__monotonic__:
            for i in range(self):
                v = retic_cast(self.__fastgetitem__(i), self.__monotonic__, newmono, error, line=self.line)
                self.__fastsetitem__(i, v)
            self.__monotonic__ = newmono
            self.__line__ = line
            self.__error__ = error
