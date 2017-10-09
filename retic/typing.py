# Dummy definitions that can be exported and used by programmers as
# valid Python expressions that represent types, or provide pragmas to
# Reticulated

# Static command: pass the type parser a module prefix to look for before types
def retic_prefix(x):
    pass

# Static command: treat class names as nominal types
def nominal(): 
    pass

# Static decorator: infer the fields of an object type based on its
# constructor
def constructor_fields(func):
    return func

# Static decorator: specify field types for objects
def fields(fields):
    return lambda x: x

# Static decorator: treat function as though it doesnt have named arguments
def positional(func):
    return func

def Alias(x):
    return x

def Function(x,y):
    return None
    
class ClassCollection:
    def __getitem__(self, *n):
        pass
    def __call__(self, *n):
        pass

List = ClassCollection()
Dict = ClassCollection()
Set  = ClassCollection()
Tuple= ClassCollection()
Callable = ClassCollection()
Union= ClassCollection()
Like = ClassCollection()
Trusted = ClassCollection()
FlowVariable = ClassCollection()


# Macro for seeing the static type of an expression
def __typeof(x):
    return x


Any = lambda x: x
Int = None
Void = None
Dyn = None
