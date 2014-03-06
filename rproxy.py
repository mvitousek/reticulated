def create_proxy(obj, metaclass=type):
    supe = obj.__class__ if isinstance(obj, Exception) else\
        obj.__class__ if isinstance(obj, type) else object
    odir = dir(obj) if not isinstance(obj, type) else [] 
    class Proxy(supe, metaclass=metaclass):
        if '__eq__' in odir:
            def __eq__(self, *args, **kwds):
                return self.__eq__(*args, **kwds)

        if '__ne__' in odir:
            def __ne__(self, *args, **kwds):
                return self.__ne__(*args, **kwds)

        if '__bytes__' in odir:
            def __bytes__(self, *args, **kwds):
                return self.__bytes__(*args, **kwds)

        if '__format__' in odir:
            def __format__(self, *args, **kwds):
                return self.__format__(*args, **kwds)

        if '__str__' in odir:
            def __str__(self, *args, **kwds):
                return self.__str__(*args, **kwds)

        if '__del__' in odir:
            def __del__(self, *args, **kwds):
                return self.__del__(*args, **kwds)

        if '__repr__' in odir:
            def __repr__(self, *args, **kwds):
                return self.__repr__(*args, **kwds)

        if '__str__' in odir:
            def __str__(self, *args, **kwds):
                return self.__str__(*args, **kwds)

        if '__hash__' in odir:
            def __hash__(self, *args, **kwds):
                return self.__hash__(*args, **kwds)

        if '__bool__' in odir:
            def __bool__(self, *args, **kwds):
                return self.__bool__(*args, **kwds)

        if '__getattr__' in odir:
            def __getattr__(self, *args, **kwds):
                return self.__getattr__(*args, **kwds)

        if '__dir__' in odir:
            def __dir__(self, *args, **kwds):
                return self.__dir__(*args, **kwds)

        if '__get__' in odir:
            def __get__(self, *args, **kwds):
                return self.__get__(*args, **kwds)

        if '__set__' in odir:
            def __set__(self, *args, **kwds):
                return self.__set__(*args, **kwds)

        if '__delete__' in odir:
            def __delete__(self, *args, **kwds):
                return self.__delete__(*args, **kwds)

        if '__instancecheck__' in odir:
            def __instancecheck__(self, *args, **kwds):
                return self.__instancecheck__(*args, **kwds)

        if '__subclasscheck__' in odir:
            def __subclasscheck__(self, *args, **kwds):
                return self.__subclasscheck__(*args, **kwds)

        if '__len__' in odir:
            def __len__(self, *args, **kwds):
                return self.__len__(*args, **kwds)

        if '__getitem__' in odir:
            def __getitem__(self, *args, **kwds):
                return self.__getitem__(*args, **kwds)

        if '__delitem__' in odir:
            def __delitem__(self, *args, **kwds):
                return self.__delitem__(*args, **kwds)

        if '__reversed__' in odir:
            def __reversed__(self, *args, **kwds):
                return self.__reversed__(*args, **kwds)

        if '__contains__' in odir:
            def __contains__(self, *args, **kwds):
                return self.__contains__(*args, **kwds)

        if '__add__' in odir:
            def __add__(self, *args, **kwds):
                return self.__add__(*args, **kwds)

        if '__sub__' in odir:
            def __sub__(self, *args, **kwds):
                return self.__sub__(*args, **kwds)

        if '__mul__' in odir:
            def __mul__(self, *args, **kwds):
                return self.__mul__(*args, **kwds)

        if '__truediv__' in odir:
            def __truediv__(self, *args, **kwds):
                return self.__truediv__(*args, **kwds)

        if '__floordiv__' in odir:
            def __floordiv__(self, *args, **kwds):
                return self.__floordiv__(*args, **kwds)

        if '__mod__' in odir:
            def __mod__(self, *args, **kwds):
                return self.__mod__(*args, **kwds)

        if '__divmod__' in odir:
            def __divmod__(self, *args, **kwds):
                return self.__divmod__(*args, **kwds)

        if '__pow__' in odir:
            def __pow__(self, *args, **kwds):
                return self.__pow__(*args, **kwds)

        if '__lshift__' in odir:
            def __lshift__(self, *args, **kwds):
                return self.__lshift__(*args, **kwds)

        if '__rshift__' in odir:
            def __rshift__(self, *args, **kwds):
                return self.__rshift__(*args, **kwds)

        if '__and__' in odir:
            def __and__(self, *args, **kwds):
                return self.__and__(*args, **kwds)

        if '__xor__' in odir:
            def __xor__(self, *args, **kwds):
                return self.__xor__(*args, **kwds)

        if '__or__' in odir:
            def __or__(self, *args, **kwds):
                return self.__or__(*args, **kwds)

        if '__radd__' in odir:
            def __radd__(self, *args, **kwds):
                return self.__radd__(*args, **kwds)

        if '__rsub__' in odir:
            def __rsub__(self, *args, **kwds):
                return self.__rsub__(*args, **kwds)

        if '__rmul__' in odir:
            def __rmul__(self, *args, **kwds):
                return self.__rmul__(*args, **kwds)

        if '__rtruediv__' in odir:
            def __rtruediv__(self, *args, **kwds):
                return self.__rtruediv__(*args, **kwds)

        if '__rfloordiv__' in odir:
            def __rfloordiv__(self, *args, **kwds):
                return self.__rfloordiv__(*args, **kwds)

        if '__rmod__' in odir:
            def __rmod__(self, *args, **kwds):
                return self.__rmod__(*args, **kwds)

        if '__rpow__' in odir:
            def __rpow__(self, *args, **kwds):
                return self.__rpow__(*args, **kwds)

        if '__rdivmod__' in odir:
            def __rdivmod__(self, *args, **kwds):
                return self.__rdivmod__(*args, **kwds)

        if '__rlshift__' in odir:
            def __rlshift__(self, *args, **kwds):
                return self.__rlshift__(*args, **kwds)

        if '__rrshift__' in odir:
            def __rrshift__(self, *args, **kwds):
                return self.__rrshift__(*args, **kwds)

        if '__rand__' in odir:
            def __rand__(self, *args, **kwds):
                return self.__rand__(*args, **kwds)

        if '__rxro__' in odir:
            def __rxro__(self, *args, **kwds):
                return self.__rxro__(*args, **kwds)

        if '__ror__' in odir:
            def __ror__(self, *args, **kwds):
                return self.__ror__(*args, **kwds)

        if '__iadd__' in odir:
            def __iadd__(self, *args, **kwds):
                return self.__iadd__(*args, **kwds)

        if '__isub__' in odir:
            def __isub__(self, *args, **kwds):
                return self.__isub__(*args, **kwds)

        if '__imul__' in odir:
            def __imul__(self, *args, **kwds):
                return self.__imul__(*args, **kwds)

        if '__itruediv__' in odir:
            def __itruediv__(self, *args, **kwds):
                return self.__itruediv__(*args, **kwds)

        if '__ifloordiv__' in odir:
            def __ifloordiv__(self, *args, **kwds):
                return self.__ifloordiv__(*args, **kwds)

        if '__imod__' in odir:
            def __imod__(self, *args, **kwds):
                return self.__imod__(*args, **kwds)

        if '__ipow__' in odir:
            def __ipow__(self, *args, **kwds):
                return self.__ipow__(*args, **kwds)

        if '__ilshift__' in odir:
            def __ilshift__(self, *args, **kwds):
                return self.__ilshift__(*args, **kwds)

        if '__irshift__' in odir:
            def __irshift__(self, *args, **kwds):
                return self.__irshift__(*args, **kwds)

        if '__iand__' in odir:
            def __iand__(self, *args, **kwds):
                return self.__iand__(*args, **kwds)

        if '__ixor__' in odir:
            def __ixor__(self, *args, **kwds):
                return self.__ixor__(*args, **kwds)

        if '__ior__' in odir:
            def __ior__(self, *args, **kwds):
                return self.__ior__(*args, **kwds)

        if '__neg__' in odir:
            def __neg__(self, *args, **kwds):
                return self.__neg__(*args, **kwds)

        if '__pos__' in odir:
            def __pos__(self, *args, **kwds):
                return self.__pos__(*args, **kwds)

        if '__abs__' in odir:
            def __abs__(self, *args, **kwds):
                return self.__abs__(*args, **kwds)

        if '__invert__' in odir:
            def __invert__(self, *args, **kwds):
                return self.__invert__(*args, **kwds)

        if '__complex__' in odir:
            def __complex__(self, *args, **kwds):
                return self.__complex__(*args, **kwds)

        if '__int__' in odir:
            def __int__(self, *args, **kwds):
                return self.__int__(*args, **kwds)

        if '__float__' in odir:
            def __float__(self, *args, **kwds):
                return self.__float__(*args, **kwds)

        if '__round__' in odir:
            def __round__(self, *args, **kwds):
                return self.__round__(*args, **kwds)

        if '__index__' in odir:
            def __index__(self, *args, **kwds):
                return self.__index__(*args, **kwds)

        if '__enter__' in odir:
            def __enter__(self, *args, **kwds):
                return self.__enter__(*args, **kwds)

        if '__exit__' in odir:
            def __exit__(self, *args, **kwds):
                return self.__exit__(*args, **kwds)

        if '__call__' in odir:
            def __call__(self, *args, **kwds):
                return self.__call__(*args, **kwds)

        if '__iter__' in odir:
            def __iter__(self, *args, **kwds):
                return self.__iter__(*args, **kwds)

        if '__setitem__' in odir:
            def __setitem__(self, *args, **kwds):
                return self.__setitem__(*args, **kwds)
    return Proxy

