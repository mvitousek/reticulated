import ast
from . import flags

# Single API to generate correct AST nodes in different versions of Python

def Call(*, func, args, keywords, starargs, kwargs, lineno=None, col_offset=None):
    if flags.PY3_VERSION >= 5:
        if starargs is not None:
            args += [ast.Starred(starargs, ast.Load())]
        if kwargs is not None:
            keywords += [ast.keyword(arg=None, value=kwargs)]
        if lineno is not None and col_offset is not None:
            return ast.Call(func=func, args=args, keywords=keywords, lineno=lineno, col_offset=col_offset)
        else:
            return ast.Call(func=func, args=args, keywords=keywords)
    else:
        return ast.Call(func=func, args=args, keywords=keywords, 
                        starargs=starargs, kwargs=kwargs, lineno=lineno, col_offset=col_offset)

def FunctionDef(*, name, args, body, decorator_list, returns, lineno=None, col_offset=None):
    if flags.PY_VERSION == 2:
        # Ignore returns
        if lineno is not None and col_offset is not None:
            return ast.FunctionDef(name=name, args=args, body=body, 
                                   decorator_list=decorator_list, lineno=lineno, col_offset=col_offset)
        else:
            return ast.FunctionDef(name=name, args=args, body=body, 
                                   decorator_list=decorator_list)
    elif flags.PY_VERSION == 3:
        if lineno is not None and col_offset is not None:
            return ast.FunctionDef(name=name, args=args, body=body, 
                                   decorator_list=decorator_list, returns=returns,
                                   lineno=lineno, col_offset=col_offset)
        else:
            return ast.FunctionDef(name=name, args=args, body=body, 
                                   decorator_list=decorator_list, returns=returns)
                                    
def ClassDef(*, name, bases, keywords, starargs, kwargs, body, decorator_list, lineno=None, col_offset=None):
    if flags.PY_VERSION == 2:
        # Ignore keywords and starargs, they shouldnt be there in the first place if Py2
        return ast.ClassDef(name=name, bases=bases, body=body, 
                            decorator_list=decorator_list, lineno=lineno, col_offset=col_offset)
    elif flags.PY_VERSION == 3:
        if flags.PY3_VERSION >= 5:
            if starargs is not None:
                bases += [ast.Starred(starargs, ast.Load())]
            if kwargs is not None:
                keywords += [ast.keyword(arg=None, value=kwargs)]
            if lineno is not None and col_offset is not None:
                return ast.ClassDef(name=name, bases=bases, keywords=keywords, body=body,
                                    decorator_list=decorator_list, lineno=lineno, col_offset=col_offset)
            else:
                return ast.ClassDef(name=name, bases=bases, keywords=keywords, body=body,
                                    decorator_list=decorator_list)
        else: 
            if lineno is not None and col_offset is not None:
                return ast.ClassDef(name=name, bases=bases, keywords=keywords, 
                                    starargs=starargs, kwargs=kwargs, body=body,
                                    decorator_list=decorator_list, lineno=lineno, col_offset=col_offset)
            else:
                return ast.ClassDef(name=name, bases=bases, keywords=keywords, 
                                    starargs=starargs, kwargs=kwargs, body=body,
                                    decorator_list=decorator_list)
            
def starargs(n):
    if flags.PY3_VERSION >= 5:
        if isinstance(n, ast.ClassDef):
            args = n.bases
        else:
            args = n.args
        for arg in args:
            if isinstance(arg, ast.Starred):
                return arg.value
        return None
    else:
        return n.starargs

                
def kwargs(n):
    if flags.PY3_VERSION >= 5:
        for kw in n.keywords:
            if kw.arg is None:
                return kw.value
        return None
    else:
        return n.kwargs
