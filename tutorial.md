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

`Dict(T_1, T_2)`: a dictionary mapping keys of type `T_1` to values of type T_2 

Running Reticulated
-------------------

###Runtime semantics###

###Options###

###Internal settings###