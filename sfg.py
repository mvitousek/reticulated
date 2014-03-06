key = '''{1}{1}if '__{0}__' in odir:
{1}{1}{1}def __{0}__(self, *args, **kwds):
{1}{1}{1}{1}return self.__{0}__(*args, **kwds)
'''

funs = ['next', 'eq', 'ne', 'le', 'lt', 'ge', 'gt', 'bytes', 'format', 'str', 'del', 'repr', 'str', 'hash', 'bool', 'getattr', 'dir', 'get', 'set', 'delete', 'instancecheck', 'subclasscheck', 'len', 'getitem', 'delitem', 'reversed', 'contains', 'add', 'sub', 'mul', 'truediv', 'floordiv', 'mod', 'divmod', 'pow', 'lshift', 'rshift', 'and', 'xor', 'or', 'radd', 'rsub', 'rmul', 'rtruediv', 'rfloordiv', 'rmod', 'rpow', 'rdivmod', 'rlshift', 'rrshift', 'rand', 'rxro', 'ror', 'iadd', 'isub', 'imul', 'itruediv', 'ifloordiv', 'imod', 'ipow', 'ilshift', 'irshift', 'iand', 'ixor', 'ior', 'neg', 'pos', 'abs', 'invert', 'complex', 'int', 'float', 'round', 'index', 'enter', 'exit', 'call', 'iter', 'setitem']

for fun in funs:
    print(key.format(fun,'    '))
