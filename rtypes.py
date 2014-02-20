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
    def bottom_free(self):
        return True
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
    def bottom_free(self):
        return False
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
    def to_ast(self):
        return ast.Call(func=super(TypeVariable,self).to_ast(), args=[ast.Str(s=self.name)],
                        keywords=[], starargs=None, kwargs=None)
    def bottom_free(self):
        return True
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
        if isinstance(froms, ParameterSpec):
            self.froms = froms
        elif tyinstance(froms, Dyn) or froms == None:
            self.froms = DynParameters
        else: self.froms = AnonymousParameters(froms)
        self.to = to
    def __eq__(self, other):
        return (super(Function, self).__eq__(other) and  
                self.froms == other.froms and
                self.to == other.to)
    def static(self):
        return self.froms.static() and \
            self.to.static()
    def bottom_free(self):
        return self.froms.bottom_free() and \
            self.to.bottom_free()
    def to_ast(self):
        return ast.Call(func=super(Function, self).to_ast(), args=[self.froms.to_ast(), self.to.to_ast()], 
                        keywords=[], starargs=None, kwargs=None)
    def __str__(self):
        return 'Function(%s, %s)' % (self.froms, self.to)
    def structure(self):
        return Record({key: Dyn for key in dir(lambda x: None)})
    def substitute(self, var, ty, shallow):
        self.froms = self.froms.substitute(var, ty, shallow)
        self.to = self.to.substitute(var, ty, shallow)
        return self
    def substitute_alias(self, var, ty):
        self.froms = self.froms.substitute_alias(var, ty)
        self.to = self.to.substitute_alias(var, ty)
        return self
    def copy(self):
        froms = self.froms.copy()
        to = self.to.copy()
        return Function(froms, to)
    def bind(self):
        return Function(self.froms.bind(), self.to)
class List(PyType):
    def __init__(self, type):
        self.type = type
    def __eq__(self, other):
        return super(List, self).__eq__(other) and self.type == other.type
    def static(self):
        return self.type.static()
    def bottom_free(self):
        return self.type.bottom_free()
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
        return Object('',obj)
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
    def bottom_free(self):
        return self.keys.bottom_free() and self.values.bottom_free()
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
        obj['get'] = Function(DynParameters, self.values)
        obj['items'] = Function([], Dyn)
        obj['keys'] = Function([], Dyn)
        obj['pop'] = Function([self.keys], self.values)
        obj['popitem'] = Function([], Tuple(self.keys,self.values))
        obj['update'] = Function([Dict(self.keys, self.values)], Void)
        obj['values'] = Function([], Dyn)
        return Object('',obj)
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
    def bottom_free(self):
        return all([e.bottom_free() for e in self.elements])
    def to_ast(self):
        return ast.Call(func=super(Tuple, self).to_ast(), args=list(map(lambda x:x.to_ast(), self.elements)),
                        keywords=[], starargs=None, kwargs=None)
    def __str__(self):
        return 'Tuple(%s)' % (','.join([str(elt) for elt in self.elements]))
    def structure(self):
        # Not yet defining specific types
        obj = {key: Dyn for key in dir(())}
        return Object('',obj)
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
    def bottom_free(self):
        return self.type.bottom_free()
    def to_ast(self):
        return ast.Call(func=super(Iterable, self).to_ast(), args=[self.type.to_ast()], keywords=[],
                        starargs=None, kwargs=None)
    def __str__(self):
        return 'Iterable(%s)' % str(self.type)
    def structure(self):
        # Not yet defining specific types
        return Object({'__iter__': Iterable(self.type)})
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
    def bottom_free(self):
        return self.type.bottom_free()
    def to_ast(self):
        return ast.Call(func=super(Set, self).to_ast(), args=[self.type.to_ast()], keywords=[],
                        starargs=None, kwargs=None)
    def __str__(self):
        return 'Set(%s)' % str(self.type)
    def structure(self):
        # Not yet defining specific types
        obj = {key: Dyn for key in dir({1})}
        return Object('',obj)
    def substitute(self, var, ty, shallow):
        self.type = self.type.substitute(var, ty, shallow)
        return self
    def substitute_alias(self, var, ty):
        self.type = self.type.substitute_alias(var, ty)
        return self
    def copy(self):
        return Set(self.type.copy())
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
    def static(self):
        return all(self.members[m].static() for m in self.members)
    def bottom_free(self):
        return all(self.members[m].bottom_free() for m in self.members)
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
    def static(self):
        return all(self.members[m].static() for m in self.members)
    def bottom_free(self):
        return all(self.members[m].bottom_free() for m in self.members)
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
            if tyinstance(f, Function):
                inst_dict[k] = f.bind()
            else: inst_dict[k] = f
        return Object(self.name, inst_dict)
    def copy(self):
        return Class(self.name, {k:self.members[k].copy() for k in self.members})
    def member_type(self, member):
        return self.members[member].copy().substitute(self.name, self.instance(), True)


class ObjectAlias(PyType):
    def __init__(self, name, children):
        self.name = name
        self.children = children
    def __getattr__(self, k):
        if k == 'Class':
            return ObjectAlias(self.name + '.Class', {})
        elif k in self.children:
            return self.children[k]
        else: raise AttributeError('\'ObjectAlias\' object has no attribute \'%s\'' % k)
    def __str__(self):
        return 'OBJECTALIAS(%s)' % self.name
    def __eq__(self, other):
        return isinstance(other, ObjectAlias) and other.name == self.name
    def substitute_alias(self, var, ty):
        if self.name == var:
            return ty
        else: return self
    def substitute(self, var, ty, shallow):
        return self
    def copy(self):
        return self

class ParameterSpec(object):
    def __str__(self):
        return self.__class__.__name__
    __repr__ = __str__
class DynParameters(ParameterSpec):
    def __str__(self):
        return 'DynParameters'
    def __eq__(self, other):
        return isinstance(other, self.__class__)
    def to_ast(self):
        return ast.Name(id='DynParameters', ctx=ast.Load())
    def bottom_free(self):
        return True
    def static(self):
        return False
    def substitute_alias(self, var, ty):
        return self
    def substitute(self, var, ty, shallow):
        return self
    def copy(self):
        return self
    def bind(self):
        return self
    def lenmatch(self, ln):
        return [(l, Dyn) for l in ln]
class NamedParameters(ParameterSpec):
    def __init__(self, parameters):
        self.parameters = parameters
        assert isinstance(parameters, list)
        assert len(parameters) == 0 or isinstance(parameters[0], tuple)
    def __str__(self):
        return str(['%s:%s' % (name, ty) for name, ty in self.parameters])
    def __eq__(self, other):
        return isinstance(other, NamedParameters) and\
            len(self.parameters) == len(other.parameters) and\
            all(((n1 == n2) and (t1 == t2)) for (n1, t1), (n2, t2) in\
                    zip(self.parameters, other.parameters))
    def to_ast(self):
        return ast.Call(func=ast.Name(id='NamedParameters', ctx=ast.Load()), 
                        args=[ast.List(elts=[ast.Tuple(elts=[ast.Str(s=name),
                                                             ty.to_ast()],
                                                       ctx=ast.Load())\
                                                 for name, ty in self.parameters],
                                       ctx=ast.Load())],
                        keywords=[], starargs=None, kwargs=None)
    def bottom_free(self):
        return all(ty.bottom_free() for _, ty in self.parameters)
    def static(self):
        return all(ty.static() for _, ty in self.parameters)
    def substitute_alias(self, var, ty):
        self.parameters = [(k, t.substitute_alias(var, ty)) for\
                               k, t in self.parameters]
        return self
    def substitute(self, var, ty, shallow):
        self.parameters = [(k, t.substitute(var, ty,shallow)) for\
                               k, t in self.parameters]
        return self
    def copy(self):
        return NamedParameters([(k, t.copy()) for k, t in self.parameters])
    def bind(self):
        return NamedParameters(self.parameters[1:])
    def lenmatch(self, ln):
        if len(ln) == len(self.parameters):
            return list(zip(ln, [ty for _, ty in self.parameters]))
        else: return None
class AnonymousParameters(ParameterSpec):
    def __init__(self, parameters):
        assert isinstance(parameters, list)
        assert len(parameters) == 0 or not isinstance(parameters[0], tuple)
        self.parameters = parameters
    def __str__(self):
        return str(['%s' % ty for ty in self.parameters])
    def __eq__(self, other):
        return isinstance(other, AnonymousParameters) and\
            len(self.parameters) == len(other.parameters) and\
            all((t1 == t2) for t1, t2 in\
                    zip(self.parameters, other.parameters))
    def to_ast(self):
        return ast.Call(func=ast.Name(id='AnonymousParameters', ctx=ast.Load()), 
                        args=[ast.List(elts=[ty.to_ast() for ty in self.parameters],
                                       ctx=ast.Load())],
                        keywords=[], starargs=None, kwargs=None)
    def bottom_free(self):
        return all(ty.bottom_free() for ty in self.parameters)
    def static(self):
        return all(ty.static() for ty in self.parameters)
    def substitute_alias(self, var, ty):
        self.parameters = [t.substitute_alias(var, ty) for\
                               t in self.parameters]
        return self
    def substitute(self, var, ty, shallow):
        self.parameters = [t.substitute(var, ty,shallow) for\
                               t in self.parameters]
        return self
    def copy(self):
        return AnonymousParameters([t.copy() for t in self.parameters])
    def bind(self):
        if len(self.parameters) > 0:
            return AnonymousParameters(self.parameters[1:])
        else: raise UnexpectedTypeError('binding non-unbound-method function type')
    def lenmatch(self, ln):
        if len(ln) == len(self.parameters):
            return list(zip(ln, self.parameters))
        else: return None

def Record(dct):
    return Object('', dct)

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
Top = Top()

DynParameters = DynParameters()

def tyinstance(ty, tyclass):
    if tyclass == Record:
        return tyinstance(ty, Object)
    return (not inspect.isclass(tyclass) and ty == tyclass) or \
        (inspect.isclass(tyclass) and isinstance(ty, tyclass)) 
       
def pinstance(ty, tyclass):
    return (not isinstance(tyclass, type) and ty == tyclass) or \
        (inspect.isclass(tyclass) and isinstance(ty, tyclass))            
   
