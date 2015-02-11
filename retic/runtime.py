import inspect,flags

def retic_bindmethod(cls, receiver, attr):
    val = getattr(receiver, attr)
    if inspect.ismethod(val):
        return lambda *args: getattr(cls, attr)(receiver, *args)
    else: return val

if flags.INITIAL_ENVIRONMENT:
    def dyn(v):
        return v
