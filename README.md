Reticulated Python is a tool for experimenting with [gradual
typing](https://en.wikipedia.org/wiki/Gradual_typing) in Python 3.
Reticulated Python adds optional static and runtime typechecking to
Python. It lets programmers annotate functions and classes with types,
and it enforces these types both before and during the execution of
the program, providing early detection of errors. Crucially,
Reticulated does not require that all parts of a program be given
static types, or even any of it. In places where typed and untyped
code interact - for example, when an untyped variable is passed into a
function whose argument type is `Int` - Reticulated can perform
runtime checks, to ensure that the values in variables always
correspond to their expected types, even when this can't be guaranteed
statically.

Reticulated Python runs on Python 3.5 and lower, using the syntactic
annotations provided by Python 3 as type annotations. The absence of
an annotation implies that the parameters or return values are
dynamically typed, as in standard Python. We also provide "type
functions" for creating types that correspond to higher-order values
in Python, like functions and lists, and we provide the type `Any`
(for dynamic) to allow for, for example, heterogeneous lists, which
have the type `List[Any]`.

Reticulated Python itself is written in Python 3. Its static,
compile-time component is both a "linter" or static analyzer, and a
source-to-source translator. This component parses source files (using
the Python `ast` package) and searches for type errors, rejecting
programs that have statically detectable errors and syntactically
inserting runtime checks or casts at boundaries between typed and
untyped code, where type errors may occur.