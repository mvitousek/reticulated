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

Usage
-----

Python 3.2, 3.3:



Python 2.7:

In Python