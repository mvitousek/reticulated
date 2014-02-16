import inspect, ast

class Base(object):
    def __call__(self):
        return self
    def substitute_alias(self, var, ty):
        return self
    def substitute(self, var, ty, shallow):
        return self
    def copy(self):
        return self # no need to create new instances of bases
class Structural(object):
    pass
class PyType(object):
    def to_ast(self):
        return ast.Name(id=self.__class__.__name__, ctx=ast.Load())
    def static(self):
        return True
    def __str__(self):
        return self.__class__.__name__
    def __repr__(self):
        return self.__str__()
    def __eq__(self, other):
        return (self.__class__ == other.__class__ or 
                (hasattr(self, 'builtin') and self.builtin == other))
class Void(PyType, Base):
    builtin = type(None)
class Bottom(PyType,Base):
    pass
class Top(PyType,Base):
    pass
class TypeVariable(PyType):
    def __init__(self, name):
        self.name = name
    def __str__(self):
        return 'TypeVar(%s)' % self.name
    def copy(self):
        return TypeVariable(self.name)
    def substitute_alias(self, var, ty):
        return self
    def substitute(self, var, ty, shallow):
        if var == self.name:
            return ty
        else: return self
    def __eq__(self, other):
        return isinstance(other, TypeVariable) and other.name == self.name
    def __hash__(self):
        return hash(self.name)
class Self(PyType, Base):
    def substitute(self, var, ty, shallow):
        if shallow:
            return ty
        else: return self
class Dyn(PyType, Base):
    builtin = None
    def static(self):
        return False
class Int(PyType, Base):
    builtin = int
class Float(PyType, Base):
    builtin = float
class Complex(PyType, Base):
    builtin = complex
class String(PyType, Base):
    builtin = str
    def structure(self):
        obj = Record({key: Dyn for key in dir('Hello World')})
        return obj
class Bool(PyType, Base):
    builtin = bool
    def structure(self):
        obj = Record({key: Dyn for key in dir(True)})
        return obj
class Function(PyType):
    def __init__(self, froms, to):
        self.froms = froms
        self.to = to
    def __eq__(self, other):
        return (super(Function, self).__eq__(other) and  
                all(map(lambda p: p[0] == p[1], zip(self.froms, other.froms))) and
                self.to == other.to)
    def static(self):
        return all([f.static() for f in self.froms]) and \
            self.to.static()
    def to_ast(self):
        return ast.Call(func=super(Function, self).to_ast(), args=[ast.List(elts=[x.to_ast() for x in self.froms], 
                                                              ctx=ast.Load()), self.to.to_ast()], 
                        keywords=[], starargs=None, kwargs=None)
    def __str__(self):
        return 'Function([%s], %s)' % (','.join(str(elt) for elt in self.froms), self.to)
    def structure(self):
        return Record({key: Dyn for key in dir(lambda x: None)})
    def substitute(self, var, ty, shallow):
        self.froms = [f.substitute(var, ty, shallow) for f in self.froms]
        self.to = self.to.substitute(var, ty, shallow)
        return self
    def substitute_alias(self, var, ty):
        self.froms = [f.substitute_alias(var, ty) for f in self.froms]
        self.to = self.to.substitute_alias(var, ty)
        return self
    def copy(self):
        froms = [ty.copy() for ty in self.froms]
        to = self.to.copy()
        return Function(froms, to)
    def bind(self):
        if len(froms) > 0:
            n = self.copy()
            n.froms = n.froms[1:]
            return n
        else: raise UnexpectedTypeError('binding non-unbound-method function type')
class List(PyType):
    def __init__(self, type):
        self.type = type
    def __eq__(self, other):
        return super(List, self).__eq__(other) and self.type == other.type
    def static(self):
        return self.type.static()
    def to_ast(self):
        return ast.Call(func=super(List, self).to_ast(), args=[self.type.to_ast()], 
                        keywords=[], starargs=None, kwargs=None)
    def __str__(self):
        return 'List(%s)' % self.type
    def structure(self):
        obj = {key: Dyn for key in dir([])}
        obj['__setitem__'] = Function([Int, self.type], Void)
        obj['__getitem__'] = Function([Int], self.type)
        obj['append'] = Function([self.type], Void)
        obj['extend'] = Function([List(self.type)], Void)
        obj['index'] = Function([self.type], Int)
        obj['insert'] = Function([Int, self.type], Void)
        obj['pop'] = Function([], self.type)
        return obj
    def substitute(self, var, ty, shallow):
        self.type = self.type.substitute(var, ty, shallow)
        return self
    def substitute_alias(self, var, ty):
        self.type = self.type.substitute_alias(var, ty)
        return self
    def copy(self):
        return List(self.type.copy())
class Dict(PyType):
    def __init__(self, keys, values):
        self.keys = keys
        self.values = values
    def __eq__(self, other):
        return super(Dict, self).__eq__(other) and self.keys == other.keys and \
            self.values == other.values
    def static(self):
        return self.keys.static() and self.values.static()
    def to_ast(self):
        return ast.Call(func=super(Dict, self).to_ast(), args=[self.keys.to_ast(), self.values.to_ast()], 
                        keywords=[], starargs=None, kwargs=None)
    def __str__(self):
        return 'Dict(%s, %s)' % (self.keys, self.values)    
    def structure(self):
        obj = {key: Dyn for key in dir({})}
        obj['__setitem__'] = Function([self.keys, self.values], Void)
        obj['__getitem__'] = Function([self.keys], self.values)
        obj['copy'] = Function([], Dict(self.keys, self.values))
        obj['get'] = Function([self.keys], self.values)
        obj['items'] = Function([], Iterable(Tuple(self.keys, self.values)))
        obj['keys'] = Function([], Iterable(self.keys))
        obj['pop'] = Function([self.keys], self.values)
        obj['popitem'] = Function([], Tuple(self.keys,self.values))
        obj['update'] = Function([Dict(self.keys, self.values)], Void)
        obj['values'] = Function([], Iterable(self.values))
        return obj
    def substitute(self, var, ty, shallow):
        self.keys = self.keys.substitute(var, ty, shallow)
        self.values = self.values.substitute(var, ty, shallow)
        return self
    def substitute_alias(self, var, ty):
        self.keys = self.keys.substitute_alias(var, ty)
        self.values = self.values.substitute_alias(var, ty)
        return self
    def copy(self):
        return Dict(self.keys.copy(), self.values.copy())
class Tuple(PyType):
    def __init__(self, *elements):
        self.elements = elements
    def __eq__(self, other):
        return super(Tuple, self).__eq__(other) and len(self.elements) == len(other.elements) and \
            all(map(lambda p: p[0] == p[1], zip(self.elements, other.elements)))
    def static(self):
        return all([e.static() for e in self.elements])
    def to_ast(self):
        return ast.Call(func=super(Tuple, self).to_ast(), args=list(map(lambda x:x.to_ast(), self.elements)),
                        keywords=[], starargs=None, kwargs=None)
    def __str__(self):
        return 'Tuple(%s)' % (','.join([str(elt) for elt in self.elements]))
    def structure(self):
        # Not yet defining specific types
        obj = {key: Dyn for key in dir(())}
        return obj
    def substitute(self, var, ty, shallow):
        self.elements = [e.substitute(var, ty, shallow) for e in self.elements]
        return self
    def substitute_alias(self, var, ty):
        self.elements = [e.substitute_alias(var, ty) for e in self.elements]
        return self
    def copy(self):
        return Tuple(*[ty.copy() for ty in self.elements])
class Iterable(PyType):
    def __init__(self, type):
        self.type = type
    def __eq__(self, other):
        return super(Iterable, self).__eq__(other) and self.type == other.type
    def static(self):
        return self.type.static()
    def to_ast(self):
        return ast.Call(func=super(Iterable, self).to_ast(), args=[self.type.to_ast()], keywords=[],
                        starargs=None, kwargs=None)
    def __str__(self):
        return 'Iterable(%s)' % str(self.type)
    def structure(self):
        # Not yet defining specific types
        return {'__iter__': Iterable(self.type)}
    def substitute(self, var, ty, shallow):
        self.type = self.type.substitute(var, ty, shallow)
        return self
    def substitute_alias(self, var, ty):
        self.type = self.type.substitute_alias(var, ty)
        return self
    def copy(self):
        return Iterable(self.type.copy())
class Set(PyType):
    def __init__(self, type):
        self.type = type
    def __eq__(self, other):
        return super(Set, self).__eq__(other) and self.type == other.type
    def static(self):
        return self.type.static()
    def to_ast(self):
        return ast.Call(func=super(Set, self).to_ast(), args=[self.type.to_ast()], keywords=[],
                        starargs=None, kwargs=None)
    def __str__(self):
        return 'Set(%s)' % str(self.type)
    def structure(self):
        # Not yet defining specific types
        obj = {key: Dyn for key in dir({1})}
        return obj
    def substitute(self, var, ty, shallow):
        self.type = self.type.substitute(var, ty, shallow)
        return self
    def substitute_alias(self, var, ty):
        self.type = self.type.substitute_alias(var, ty)
        return self
    def copy(self):
        return Set(self.type.copy())
class Record(PyType, Structural):
    def __init__(self, members):
        self.members = members
    def __eq__(self, other):
        return (super(Record, self).__eq__(other) and self.members == other.members) or \
            self.members == other
    def static(self):
        return all([m.static() for m in self.members.values()])
    def to_ast(self):
        return ast.Call(func=super(Record, self).to_ast(), 
                        args=[ast.Dict(keys=list(map(lambda x: ast.Str(s=x), self.members.keys())),
                                       values=list(map(lambda x: x.to_ast(), self.members.values())))],
                        keywords=[], starargs=None, kwargs=None)
    def __str__(self):
        return 'Record(%s)' % str(self.members)
    def substitute(self, var, ty, shallow):
        self.members = {k:self.members[k].substitute(var, ty, shallow) for k in self.members}
        return self
    def substitute_alias(self, var, ty):
        self.members = {k:self.members[k].substitute_alias(var, ty) for k in self.members}
        return self
    def copy(self):
        return Record({k:self.members[k].copy() for k in self.members})
class Object(PyType, Structural):
    def __init__(self, name, members):
        self.name = name
        self.members = members.copy()
    def __str__(self):
        return 'Obj(%s)%s' % (self.name, str(self.members))
    def __eq__(self, other):
        if isinstance(other, Object):
            other = other.copy().substitute(other.name, TypeVariable(self.name), False)
            return other.members == self.members
        else: return False
    def to_ast(self):
        return ast.Call(func=super(Object, self).to_ast(), 
                        args=[ast.Str(s=self.name),
                              ast.Dict(keys=list(map(lambda x: ast.Str(s=x), self.members.keys())),
                                       values=list(map(lambda x: x.to_ast(), self.members.values())))],
                        keywords=[], starargs=None, kwargs=None)
    def substitute_alias(self, var, ty):
        ty = ty.copy()
        ty = ty.substitute_alias(self.name, TypeVariable(self.name))
        self.members = {k:self.members[k].substitute_alias(var, ty) for k in self.members}
        return self
    def substitute(self, var, ty, shallow):
        self.members = {k:self.members[k].substitute(var, ty, False) for k in self.members}
        return self
    def copy(self):
        return Object(self.name, {k:self.members[k].copy() for k in self.members})
    def member_type(self, member):
        return self.members[member].copy().substitute(self.name, self, True)
class Class(PyType, Structural):
    def __init__(self, name, members):
        self.name = name
        self.members = members.copy()
    def __str__(self):
        return 'Class(%s)%s' % (self.name, str(self.members))
    def __eq__(self, other):
        if isinstance(other, Class):
            other = other.copy().substitute(other.name, TypeVariable(self.name), False)
            return other.members == self.members
        else: return False
    def to_ast(self):
        return ast.Call(func=super(Class, self).to_ast(), 
                        args=[ast.Str(s=self.name),
                              ast.Dict(keys=list(map(lambda x: ast.Str(s=x), self.members.keys())),
                                       values=list(map(lambda x: x.to_ast(), self.members.values())))],
                        keywords=[], starargs=None, kwargs=None)
    def substitute_alias(self, var, ty):
        ty = ty.copy()
        ty = ty.substitute_alias(self.name, TypeVariable(self.name))
        self.members = {k:self.members[k].substitute_alias(var, ty) for k in self.members}
        return self
    def substitute(self, var, ty, shallow):
        self.members = {k:self.members[k].substitute(var, ty, False) for k in self.members}
        return self
    def instance(self):
        inst_dict = {}
        for k in self.members:
            f = self.members[k]
            if isinstance(f, Function):
                if len(f.froms) < 1:
                    raise UnknownTypeError('Method with no self-reference')
                else: inst_dict[k] = Function(f.froms[1:], f.to)
            else: inst_dict[k] = f
        return Object(self.name, inst_dict)
    def copy(self):
        return Class(self.name, {k:self.members[k].copy() for k in self.members})
    def member_type(self, member):
        return self.members[member].copy().substitute(self.name, self.instance(), True)

# We want to be able to refer to base types without constructing them
Void = Void()
Dyn = Dyn()
Int = Int()
Float = Float()
Complex = Complex()
String = String()
Bool = Bool()
Bottom = Bottom()
Self = Self()

def tyinstance(ty, tyclass):
    return (not inspect.isclass(tyclass) and ty == tyclass) or \
        (inspect.isclass(tyclass) and isinstance(ty, tyclass))            
