import ast
from . import flags, typing

def errmsg(code, file, location, *args):
    if flags.SQUELCH_ERROR_STRINGS:
        return ''
    if isinstance(location, ast.AST):
        line = location.lineno
        try:
            column = ':%d' % location.col_offset
        except AttributeError:
            column = ''
    elif isinstance(location, tuple):
        line, column = location
        column = ':%d' % column
    elif isinstance(location, typing.Var) and hasattr(location, 'location'):
        line = location.location.lineno
        try:
            column = ':%d' % location.location.col_offset
        except AttributeError:
            column = ''
    else: 
        line = location
        column = ''
    msg = codes[code] % args
    return '%s:%s%s: %s (code %s)' % (file, line, column, msg, code)

def static_val(t):
    return 'of type %s' % t

codes = {
    'BINOP_INCOMPAT': '%s and %s are invalid operand types for the binary operator %s.',
    'LIST_STORE_TARGET': 'Attempting to assign to a list whose elements have types %s. ' + \
        'When using a list of typed variables as an assignment target, ' + \
        'the types of all the variables must be compatible with each other.',
    'WIDTH_DOWNCAST': 'Accessing nonexistant object attribute %s from value %%s.',
    'UNSCOPED_SELF': 'Cannot use a value of type Self outside of an object method context.',
    'TYPED_ATTR_DELETE': 'Cannot delete attribute %s because value\'s type %s ' + \
        'contains information about it.',
    'TYPED_VAR_DELETE': 'Cannot delete variable %s because it has a static type %s.',
    'NON_OBJECT_DEL': 'Cannot delete attribute %s from value %%s because it is not an object.',
    'NON_OBJECT_WRITE': 'Cannot write to attribute %s in value %%s because it is not an object.',
    'NON_OBJECT_READ': 'Cannot read from attribute %s in value %%s because it is not an object.',
    'ACCESS_CHECK': 'Attribute %s was expected to have type %s but instead has value %%s.',
    'COMP_CHECK': 'Comprehension was expected to have type %s but instead has value %%s.',
    'RETURN_CHECK': 'Result of function call was expected to have type %s but instead has value %%s.',
    'SUBSCRIPT_CHECK': 'Result of subscription was expected to have type %s but instead has value %%s.',
    'BAD_INDEX': 'Cannot use a value %%s as an index into a %s, use a value of type %s instead.',
    'NON_INDEXABLE': 'Cannot index into a value of type %s',
    'NON_SLICEABLE': 'Cannot slice a value of type %s',
    'BAD_FUNCTION_INJECTION': 'Function %%s does not match specified type %s. ' +\
        'Consider changing the type or setting it to Dyn.',
    'DEFAULT_MISMATCH': 'Parameter %s has a default value %%s which does not match specified type %s.',
    'RETURN_ERROR': 'A return value of type %s was expected but a value %%s was returned instead.',
    'RETURN_NONEXISTANT': 'A return value of type %s was expected but no value was returned.',
    'SINGLE_ASSIGN_ERROR': 'Right hand side of assignment was expected to be of type %s, but value %%s provided instead.',
    'MULTI_ASSIGN_ERROR': 'Right hand side of assignment was expected to be compatible with types %s, but value %%s provided instead.',
    'ITER_ERROR': 'Iteration target was expected to be of type %s, but value %%s was provided instead.',
    'BAD_CLASS_INJECTION': 'Class %%s does not match specified type %s. Consider changing the type or setting it to Dyn.',
    'EXCEPTION_ERROR': 'Variable %s has type %s and so the exception class caught as %s must have that type as well, but value %%s provided instead.',
    'FUNC_ERROR': 'Expected function of type %s at call site but but value %%s was provided instead.',
    'ARG_ERROR': 'Expected argument of type %s but value %%s was provided instead.',
    'OBJCALL_ERROR': 'Cannot call value %%s as a function because it lacks a __call__ method.',
    'BAD_OBJECT_INJECTION': 'Constructed object value %%s does not match type %s,  expected for instances of %s. Consider changing the type or setting it to Dyn.',
    'BAD_CALL': 'Cannot use a value of type %s as a function.',
    'BAD_ARG_COUNT': 'Expected %s arguments to function call but only %s were provided.',
    'FALLOFF': 'Function %s must return a value of type %s but not all paths of execution return a value.',
    'ARG_CHECK': 'Parameter %s is expected to have type %s but value %%s was provided instead.',
    'ITER_CHECK': 'Target of iteration expected to be assigned type %s but value %%s was provided instead.',
    'BAD_DEFINITION': 'Variable %s must have type %s but a value of type %s was provided instead.'
}
