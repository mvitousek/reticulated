Tutorial for Reticulated Python
===============================
Under Construction!
-------------------

This will contain an intro for using Reticulated. It is super under
construction right now.

Getting Set Up
--------------

You need Python 3.2.X or Python 3.3.X installed. To see what version
of Python 3 you have installed, go to the command line and type
`python3 --version`. (Note that the command is Python 3 -- in most
operating systems `python` alone defaults to Python 2.X.) 

You need Reticulated downloaded. Clone the git repo at
https://github.com/mvitousek/reticulated. Place it anywhere on your
machine.


Annotating Your Programs
------------------------

You can annotate programs with the below types. Annotations can be
placed only in function definitions. If you start with the function 

       def dist_from_zero(x, y):
         return math.sqrt(x * x + y * y)

you can specify that `x` and `y` are integers and that the function
returns a floating point number by adding the annotations like so:

       def dist_from_zero(x: Int, y: Int) -> Float:
         return math.sqrt(x * x + y * y)

###Types###

Reticulated types are different than Python runtime types. For
example, `42` is type `int` in Python but statically has the
Reticulated type `Int`. `[1,2,3]` has Python type `list` but
Reticulated type `List(Int)`, so Reticulated's types are more precise.

`Dyn` is the dynamic type. It can be left off of type annotations at
the top level, but you write it down if you want something like a list
of any kind of value --- this would be `List(Dyn)`.

`Int`, `Float`, `String`, `Bool`, `Complex`: correspond to base Python
types. `Int` is a subtype of `Float`.

`Void`: the type of Python's `None` value.

`List(T)`: a list of type `T`, where `T` is any Reticulated type.

`Dict(T1, T2)`: a dictionary mapping keys of type `T1` to values of type `T2`.

Simple object types are written `{ "x1": T1, "x2": T2, "x3": T3,
... }` where the 'x's are names of attributes and the 'T's are their
types. For example, the type of an object with integer fields `x` and
`y` would be `{ "x": Int, "y": Int }`. 

TODO FOR MIKE: talk about objects with self reference and class types.

Simple function types are written `Function([T1, T2, T3, ...], TR)`
where `T1,T2,T3` etc are the types of parameters and `TR` is the
function's return type. So, a function that takes two ints and returns
a float could be `Function([Int, Int], Float)`. 

With some functions, it's hard to give a simple list of parameters
when specifying a type. For example,

     def f(x, y=42, *args, **kwargs):
       ...

We can't really give a list of types that specify `f`'s parameters,
because it can take any number of arguments, as well as keyword
arguments. In the future, we totally want to have more refined
function types that precisely describe what kind of parameters `f`
takes. But for now, we can let `f`'s parameters be dynamic, while
still giving a static return type Int, by saying that `f` has type
`Function(DynParameters, Int)`. `DynParameters` replaces the list of
types in the usual type definition, and will let any number of
parameters be passed to `f`.

TODO FOR MIKE: talk about named parameters.
 

Running Reticulated
-------------------

You can run your annotated Python program with Reticulated's
typechecking on the command line by using `retic.py` instead of
`python3`. So, if you were trying to run `a.py`, and you usually ran
it on the command line with `python3 a.py`, you would instead run it
with `/path/to/reticulated/retic.py a.py`. If `a.py` takes command
line arguments or flags, put them in quotes immediately after the name
of the function: `python3 a.py -k -v arg1 arg2` becomes
`/path/to/reticulated/retic.py a.py "-k -v arg1 arg2"`

###Runtime semantics###

###Options###

###Internal settings###