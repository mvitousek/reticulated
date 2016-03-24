tyval = lambda *x, **xs: None

Base = tyval
Structural = tyval
PyType = tyval
Void = tyval
Bool = tyval
InferBottom = tyval
InfoTop = tyval
TypeVariable = tyval
Self = tyval
Dyn = tyval
Bytes = tyval
Int = tyval
Float = tyval
Complex = tyval
String = tyval
Function = tyval
List = tyval
Dict = tyval
Tuple = tyval
Iterable = tyval
Set = tyval
Object = tyval
Class = tyval
ObjectAlias = tyval
ParameterSpec = tyval
DynParameters = tyval
Arb = DynParameters
NamedParameters = tyval
Named = NamedParameters
AnonymousParameters = tyval
Pos = AnonymousParameters
Record = tyval
def infer(k):
    return k

def noinfer(k):
    return k

def parameters(*k):
    return lambda x: x

def returns(k):
    return lambda x: x

def fields(k):
    return lambda x: x

def members(k):
    return lambda x: x


def dyn(v):
    return v
def retic_bindmethod(cls, receiver, attr):
    return getattr(receiver, attr)
