Reticulated Python:
===================
Types for Python 2.7, 3.2, and 3
--------------------------------

Reticulated lets you use statically annotated types in your Python
programs, but without sacrificing any of the dynamic flexibility of
Python when that's what you want. 

While programming, annotate your code with static types (as described
below) wherever you feel like it. You can also leave off annotations
and program in normal Python when you prefer -- within the same
program, module, class, or even function! Reticulated will attempt to
detect any violations of these types when your code is compiled, and
will report an error message if it finds any type errors. In other
cases, when it can't find errors at compile time, they will be
detected at runtime by checks and casts that Reticulated inserts into
your program.

Major To-Do Items
----------------

* Testing! While Reticulated contains typechecking rules for all AST
  nodes in Python 2.7, 3.2, and 3.3, NOT ALL HAVE BEEN TESTED.  

* Typechecking of imports: currently only the main file of a Python
  program is typechecked. Naturally, this is insufficient. Imports
  will probably be typechecked at the import site at runtime by using
  an import hook, if feasible.

* Non-trivial function parameters: currently only positional arguments
  without defaults are typechecked, and function calls with keywords
  or other advanced features will result in a type error.

* Object aliases: the ability to use the name of a class as an alias
  for the structural type of its instances needs to be added.

* More typing modes: at the moment, only casts-as-assertions (see
  below) is implemented. This is a useful, lightweight form of typing,
  but has limitations. Integration with the Gradual module is a high
  priority.

* Local variable typing: currently, only function parameters and
  return types can be annotated with static types. 

#Lower priority items:#

* Writing out typechecked AST: instead of immediately compiling and
  running the target program after casts have been inserted, it could
  be useful to write the AST back out as a .py file including
  casts. Without switching to lib2to3, however, formatting and
  comments would be lost.

Annotations
-----------

You can annotate function parameters and return types with primitve
types (int, str, complex), collection types (List, Set, Dictionary,
Tuple, Iterable), function types (currently only with positional
arguments), structural object types, and the dynamic "type." The
specific set of types that you can use is in typing.py.

Types are recursively defined, so Function([List(int)], Object({'a':
int})) is the type of a function that takes a list of ints and returns
an object with an attribute 'a' of type int.

You can think of the dynamic "type," Dyn, as the type of everything in
normal Python. You don't need to annotate variables as type Dyn -- you
can just not put an annotation on them instead -- but Dyn can be
useful for specifying types like List(Dyn), which is the type of lists
that may contain anything as elements.

##Python 3.2, 3.3:##

Annotations are placed directly on function arguments, and the return
type is specified at the location of a function definition. For
example, a function that expects a single int parameter and returns a
list of ints could look like

       def f(x: int) -> List(int):
         return [x, x]

The ": int" after the parameter x is the type of x, and the
"List(int)" after the arrow ("->") is the return type of the
function. Overall, this function would have the type Function([int],
List(int)).

###Python 2.7, 3.2, 3.3:###

In Python 2.7, these annotations are not syntactically
available. Instead, you apply the @retic_typed decorator to any
function you want to be statically typed, and give it the type you
want the function to have as an argument. For instance, the program
above would be written in Python 2.7 as

       @retic_typed(Function([int], List(int)))
       def f(x):
         return [x, x]

This style of annotation is also available in Python 3.2 and 3.3.

Usage
-----

Run your annotated program by running retic.py with your selected
typing mode (casts-as-checks is default) and your target program as an
argument (e.g. "python3 retic.py --casts-as-checks
my_typed_program.py").

Typing modes
------------

Reticulated's algorithm for static typechecking is mostly astandard
implementation of gradual typing (see "Gradual typing for functional
languages," Siek and Taha 2006), but there will eventually be
semantics available for the casts and checks that are inserted to find
type errors at runtime. Currently, the only implemented system is
Casts-as-Checks.

####Casts-as-Checks:####

This mode, which inserts typechecks at certain operations such as
function calls and attribute accesse, is less precise and may provide
less useful debugging information than other modes, but it requires a
smaller memory overhead because it does not install wrappers or
proxies on values.


Copyright and license
---------------------

(C) 2012, 2013 Michael M. Vitousek. Released under the MIT license.