import ast

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

def Alias(x):
    return x

def Function(x,y):
    return None
    
class ClassCollection:
    def __getitem__(self, n):
        pass

List = ClassCollection()
Dict = ClassCollection()


