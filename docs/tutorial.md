Reticulated Python
==================
A New User's Guide
------------------

#### Introduction ####

Reticulated Python is a dialect of Python 3 that provides static
typing where you need it and preserves dynamic flexibility when you
don't. It works as both a linter and as a runtime library. It finds
static type errors where possible, and can also insert runtime checks
at the border of typed and untyped code to make sure that your type
annotations mean what you think they mean.

In this tutorial, I'll guide you through developing programs with
Reticulated Python through examples. I'll assume that you're a
reasonably experienced, but not necessarily expert, Python 3
programmer. (I aim to release a version of this tutorial for Python
2.7 as well.) Feel free to contact me at mmvitousek@gmail.com if you
have questions or suggestions!

#### Getting Started ####

Installing and running Reticulated Python

#### Using Reticulated Python ####

Most of the time, writing programs in Reticulated Python is just like
writing programs in normal Python. In fact, almost every working
"normal" Python 3 program is also a valid Reticulated Python program!
(The only exceptions are programs that use Python 3's function
annotations, since Reticulated Python uses those as type
annotations. If you're not sure what I'm referring to here, don't
worry about it.) The only difference between writing Python code and
writing Reticulated Python code is that in Reticulated Python you have
the option -- and it's only ever an option, never required -- to
specify what types of data should be allowed to be passed into, or
returned from, a function. 

Let's start with a simple example, to show why Reticulated Python is
useful:

    def is_odd(num):
      return num % 2 

The person who wrote this function probably expected it to take
integers, and then return 0 if the integer is even and 1 if it's
odd. The function works perfectly if it's only ever passed whole
numbers:

    >>> is_odd(42)
    0
    >>> is_odd(1001)
    1

Since this is Python, other kinds of values can be passed
in as well, and when this happens, the results can be confusing:

    >>> is_odd('42')
    Traceback (most recent call last):
      File "<stdin>", line 1, in <module>
      File "<stdin>", line 2, in is_odd
    TypeError: not all arguments converted during string formatting
    >>>> is_odd(4.2)
    0.2

In the first case, the error message refers to "string formatting",
due to Python's dual use of the % operator for both mathematical
modulus and string formatting. If this error message occured deep
within some library, the programmer might find themselves very
confused as to why string formatting is occurring when they thought
they were only writing math!

The second case could be even more confusing, since (by interpreting
non-zero numbers as true) it is essentially saying that 4.2 is an odd
number, when in reality non-whole numbers are neither odd nor
even. Therefore this function is returning nonsense, and other
functions that use it could return incorrect answers because of it. It
would be much better for the program to halt altogether and alert the
user of the problem.

To fix this, Reticulated Python allows the programmer to specify the
expected type of each parameter in the function definition itself:

    def is_odd(num: int):
      return num % 2 

The `: int` specifies that `num` has to be an integer. When this
program is run with Reticulated, it will initially check to see if any
calls to `is_odd` are _definitely_ wrong, and if it finds any, it will
report an error.

    :>> is_odd('42')
    ====STATIC TYPE ERROR=====
    tutorial.py:4:6: Expected argument of type Int but value of type String was provided instead. (code ARG_ERROR)
    :>> is_odd(4.2)
    ====STATIC TYPE ERROR=====
    tutorial.py:4:6: Expected argument of type Int but value of type Float was provided instead. (code ARG_ERROR)


If it doesn't find anything definitely wrong, it will
run the program as usual, but perform extra checks at runtime to make
sure that every time `is_odd` is called, it is given an integer as an
argument. For example,

    SUGGESTION: use interaction between static and dynamic functions instead of eval weirdness, and vice versa
    :>> is_odd(eval(input()))
   
Reticulated's analyzer can't say for sure that `eval(input())` is
going to be an int, but it might be, so it lets the program run. This
is one way that Reticulated Python differs from many statically typed
languages that you might be used to, which prevent programs from
running unless they're _definitely_ have no type mismatches, while
Reticulated lets programs run if they _might_ be correctly typed and
then double checks at runtime that the types do match up. Therefore,
this program has different results depending on what we call it with:

    :>> is_odd(eval(input()))
    42 # The string being given to input()
    1
    :>> is_odd(eval(input()))
    4.2 # The string being given to input()
    Traceback (most recent call last):
      File "tutorial.py", line 4, in <module>
        is_odd(eval(input()))
    transient.CastError: tutorial.py:4:6: Expected argument of type Int but value '4.2' was provided instead. (code ARG_ERROR)

NEXT STEP: objects/classes

### Why not assertions? ###

Another way to accomplish this is for the programmer to manually add
runtime checks or assertions to the program, to make sure that `num`
really is an integer:

    >>> def is_odd(num):
    ...   assert isinstance(num, int)
    ...   return num % 2 
    >>> is_odd('42')
    Traceback (most recent call last):
      File "<stdin>", line 1, in <module>
      File "<stdin>", line 2, in is_odd
    AssertionError
    >>> is_odd(4.2)
    Traceback (most recent call last):
      File "<stdin>", line 1, in <module>
      File "<stdin>", line 2, in is_odd
    AssertionError

This solves our problem, but several issues remain. Adding such
assertions wherever needed is a significant burden on the programmer,
especially when more complicated checks are needed -- for instance, if
a parameter needed to be a list of integers, or an object with a
particular set of fields. Additionally, if a value is mutated after
the assertion has occurred -- for example, if a string was added to a
list that's supposed to contain only integers, after the check has
happened -- the assertion won't be enough to detect the
problem. Finally, this kind of check only happens when the program is
executing, and cannot detect any errors ahead of time, increasing the
potential for edge-case bugs that escape testing to show up in
production code.

<!-- Optional Typing for Python by Guido -->