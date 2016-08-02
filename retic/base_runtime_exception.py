
# We don't store this in exc.py because this will be imported by
# transient.py, which is used at runtime, and we don't want the
# overhead of importing the other stuff used in exc.py

class NormalRuntimeError(BaseException): pass

