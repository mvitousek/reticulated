from . import copy_visitor, flags
from .typecheck import fixup
import ast

def extract_check_args_elts(args):
    if flags.SEMANTICS == 'TRANS':
        val = args[0]
        elts = [e.s for e in args[1].elts]
        return val, None, None, elts
    elif flags.SEMANTICS == 'MGDTRANS':
        val = args[0]
        elts = [e.s for e in args[3].elts]
        return val, args[1], args[2], elts

def make_cast_function(name, elts):
    check_stmts = '\n'.join('    val.{}'.format(attr) for attr in elts)

    if flags.SEMANTICS == 'TRANS':
        updater = '    '
        err = '    raise CheckError(val)'
        params = ''
    elif flags.SEMANTICS == 'MGDTRANS':
        updater = '    add_blame_pointer(val, elim, act)'
        err = '    blame(val, elim, act)'
        params = ', elim, act'
    else: raise Exception()

    checker = '''
def {}(val, src, b, trg):
  try:
{}
    add_blame_cast(val, src, b, trg)
    return val
  except:
    do_blame([b])
    '''.format(name, check_stmts)

    checker = ast.parse(checker).body[0]
    return checker
        
def make_check_function(name, elts):
    check_stmts = '\n'.join('    val.{}'.format(attr) for attr in elts)

    if flags.SEMANTICS == 'TRANS':
        updater = '    '
        err = '    raise CheckError(val)'
        params = ''
        
 #       err = ast.Raise(exc=ast.Call(func=ast.Name(id='CheckError', ctx=ast.Load()),
 #                                    args=[ast.Name(id='val', ctx=ast.Load())], keywords=[],
 #                                    starargs=None, kwargs=None), cause=None)
    elif flags.SEMANTICS == 'MGDTRANS':
        updater = '    add_blame_pointer(val, elim, act)'
        err = '    blame(val, elim, act)'
        params = ', elim, act'
 #       err = ast.Expr(value=ast.Call(func=ast.Name(id='blame', ctx=ast.Load()),
 #                                     args=[ast.Name(id='val', ctx=ast.Load()), elim, act],
 #                                     keywords=[], starargs=None, kwargs=None))
    else: raise Exception()

    checker = '''
def {}(val{}):
  try:
{}
{}
    return val
  except:
{}
    '''.format(name, params, check_stmts, updater, err)

    checker = ast.parse(checker).body[0]
    # # Patch in the correct error handler
    # checker.body[0].handlers[0].body[0] = err
    
    # if flags.SEMANTICS == 'MGDTRANS':
    #     updater = ast.Expr(value=ast.Call(func=ast.Name(id='add_blame_pointer', ctx=ast.Load()),
    #                                       args=[ast.Name(id='val', ctx=ast.Load()),
    #                                             elim, act], keywords=[], starargs=None, 
    #                                       kwargs=None))
    #     # Patch in call to add_blame_pointer
    #     checker.body[0].body.insert(-1, updater)

    return checker
    
def get_check_call():
    if flags.SEMANTICS == 'TRANS':
        return 'check_type_object'
    else:
        return 'mgd_check_type_object'

def args(val, elim, act):
    if flags.SEMANTICS == 'TRANS':
        return [val]
    else:
        return [val, elim, act]

class CheckCollectionVisitor(copy_visitor.CopyVisitor):
    examine_functions = True

    def visitCall(self, n, checks, casts, counter):
        check_call = get_check_call()
        if isinstance(n.func, ast.Name) and \
           n.func.id == check_call:
            val, elim, act, elts = extract_check_args_elts(n.args)
            val = self.dispatch(val, checks, casts, counter)
            
            if frozenset(elts) in checks:
                name, _ = checks[frozenset(elts)]
            else:
                name = 'check' + str(counter[0])
                counter[0] += 1
                checker = make_check_function(name, elts)
                checks[frozenset(elts)] = (name, checker)
            
            return fixup(ast.Call(func=ast.Name(id=name, ctx=ast.Load()),
                            args=args(val, elim, act), keywords=[], starargs=None, kwargs=None,
                            lineno=n.lineno))
        if flags.SEMANTICS == 'MGDTRANS' and \
           isinstance(n.func, ast.Name) and \
           n.func.id == 'mgd_cast_type_object':
            
            val = self.dispatch(n.args[0], checks, casts, counter)
            src = n.args[1]
            b = n.args[2]
            trg = n.args[3]
            elts = [e.s for e in n.args[4].elts]
            
            if frozenset(elts) in casts:
                name, _ = casts[frozenset(elts)]
            else:
                name = 'cast' + str(counter[0])
                counter[0] += 1
                caster = make_cast_function(name, elts)
                casts[frozenset(elts)] = (name, caster)
            
            return fixup(ast.Call(func=ast.Name(id=name, ctx=ast.Load()),
                            args=[val, src, b, trg], keywords=[], starargs=None, kwargs=None,
                            lineno=n.lineno))
            
        else:
            return super().visitCall(n, checks, casts, counter)

    def visitModule(self, n):
        checks = {}
        casts = {}
        body = self.dispatch_scope(n.body, checks, casts, [0])
        if len(body) > 0 and isinstance(body[0], ast.ImportFrom) and body[0].module == '__future__':
            prebody = [body[0]]
            body = body[1:]
        else:
            prebody = []
        checkfuns = [checks[k][1] for k in checks]
        castfuns = [casts[k][1] for k in casts]
        return ast.Module(body=prebody+checkfuns+castfuns+body)

if __name__ == '__main__':
    mod = '''
def f(x, y):
  check_type_object(x, ['a', 'b'])
  foo(check_type_object(y, ['a', 'b']))

class C:
  def __init__(self):
    check_type_object(self, ['z', 'g'])
'''
    collect = CheckCollectionVisitor()
    m = collect.preorder(ast.parse(mod))
    from . import unparse
    unparse.unparse(m)

    flags.SEMANTICS = 'MGDTRANS'
    mod = '''
def f(x, y):
  mgd_cast_type_object(x, int, "a", dyn, ['a', 'b'])
  mgd_check_type_object(x, f, (1, 2), ['a', 'b'])
  foo(mgd_check_type_object(y, g, (2, 3), ['a', 'b']))

class C:
  def __init__(self):
    mgd_check_type_object(self, self.__init__, 6, ['z', 'g'])
'''
    collect = CheckCollectionVisitor()
    m = collect.preorder(ast.parse(mod))
    from . import unparse
    unparse.unparse(m)
    
  
