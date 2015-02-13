Reticulated Python
==================
A New User's Guide (UNDER CONSTRUCTION)
------------------
by Mike Vitousek

### Introduction ###

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
2.7 as well.) Feel free to contact me at <mmvitousek@gmail.com> if you
have questions or suggestions!

### Getting Started ###

To start off, make sure you have Python 3.2 or later installed. If you
have Python 3 installed, you can check the version on the command line
by typing `python3 --version`. Modern versions of Python 3 can be
downloaded from the [Python project website](http://python.org).

Next, [download Reticulated][] to somewhere easy to get to on the
command line, like your home folder or the desktop. Then go ahead and
unzip the package.

Now open a command line and navigate to the folder that you just
unzipped everything to. What to do next depends on your operating
system:

##### Linux and Mac #####

If you have root, type:

    sudo python3 setup.py install

If you don't have root, or you prefer not to authorize it, type:

    python3 setup.py install --user

##### Windows #####

DUNNO


### Using Reticulated Python ###

### Writing Reticulated Python Code ###

Most of the time, writing programs in Reticulated Python is just like
writing programs in normal Python. In fact, almost every working
"normal" Python 3 program is also a valid Reticulated Python program!
(The only exceptions are programs that use Python 3's function
annotations, since Reticulated Python uses those as type
annotations. If you're not sure what I'm referring to here, don't
worry about it.) The only difference between writing Python code and
writing Reticulated Python code is that in Reticulated Python you have
the option -- and it's only ever an option, never required -- to
specify what types of data should go where (for example, what is
allowed to be passed into, or returned from, a function).

_To help you follow along, this tutorial includes the Reticulated
Python files that I'm working from in these examples. Italicized notes
like this one will tell you when to switch to a new file. To start
off, open [tutorial1.py](tutorial1.py)._

#### The basics: function annotations ####

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
      File "tutorial1.py", line 14, in <module>
        is_odd('42')
      File "tutorial1.py", line 5, in is_odd
        return num % 2
    TypeError: not all arguments converted during string formatting
    >>> is_odd(4.2)
    0.2

In the first case, the error message refers to "string formatting",
due to Python's dual use of the % operator for both mathematical
modulus and string formatting. If this error message occurred deep
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

To fix this, Reticulated Python enables the programmer to specify the
expected type of each parameter in the function definition
itself. 

_Open [tutorial2.py](tutorial2.py)._

    def is_odd(num: int):
      return num % 2 

The _type annotation_ `: int` specifies that `num` has to be an
integer. When this program is run with Reticulated, it will initially
check to see if any calls to `is_odd` are _definitely_ wrong, and if
it finds any, it will report an error.

    :>> is_odd('42')
    ====STATIC TYPE ERROR=====
    tutorial2.py:17:6: Expected argument of type Int but value of type String was provided instead. (code ARG_ERROR)
    :>> is_odd(4.2)
    ====STATIC TYPE ERROR=====
    tutorial2.py:21:6: Expected argument of type Int but value of type Float was provided instead. (code ARG_ERROR)


If it doesn't find anything definitely wrong, it will run the program
as usual, but perform extra checks at runtime to make sure that every
time `is_odd` is called, it is given an integer as an argument. This
can happen when code with type annotations is called by code without:

    def pow(b, n):
      if n == 0:
        return 1
      elif n == 1:
        return b
      elif is_odd(n):
        return b * pow(b*b, (n-1)//2)
      else: 
        return pow(b*b, n//2)
   
This implementation of the efficient exponentiation function doesn't
have a type annotation on `n`, even though it calls
`is_odd(n)`. That's ok -- it's totally fine to call code with
annotations from code that doesn't have any. In this case,
Reticulated's analyzer can't say for sure that `n` is going to be an
int, but it might be, so it lets the program run. This is one way that
Reticulated Python differs from many statically typed languages that
you might be used to, which prevent programs from running unless they
_definitely_ have no type mismatches, while Reticulated lets programs
run if they _might_ be correctly typed and then double checks at
runtime that the types do match up. Therefore, this program has
different results depending on what we call it with:

    :>> pow(42,5)
    130691232
    :>> pow(42,4.2)
    Traceback (most recent call last):
      File "tutorial2.py", line 44, in <module>
        pow(42,4.2)
      File "tutorial2.py", line 32, in pow
        elif is_odd(n):
    retic.transient.CastError: 
    tutorial2.py:32:13: Expected argument of type Int but value '4.2' was provided instead. (code ARG_ERROR)

Variables that have been given type annotations can also be passed
into functions that don't have them:

    def raise_to_own_power(n:int):
      return pow(n, n)

    :>> raise_to_own_power(5)
    3125

Finally, you can also add annotations that specify what kind of value
a function should return:

    import math
    def choose(n:int, k:int)-> int:
      return math.factorial(n)/(math.factorial(k) * math.factorial(n-k))

(Note that we can import the usual Python libraries in the usual way
from Reticulated Python code without any problem.) The `-> int` in the
function declaration means that the function must return an
int. Reticulated can use a function's return type annotations in
typechecking other functions that call it, and it will make sure that
the function actually returns a value of that type. In fact, the above
definition has a slight bug, which Reticulated detects thanks to the
return type annotation:

    :>> choose(5,3)
    Traceback (most recent call last):
      File "./tutorial2.py", line 59, in <module>
        choose(5,3)
      File "./tutorial2.py", line 57, in choose
        return math.factorial(n)/(math.factorial(k) * math.factorial(n-k))
    retic.transient.CastError: 
    ./tutorial2.py:57:2: A return value of type Int was expected but a value '10.0' was returned instead. (code RETURN_ERROR)

In Python 3, the `/` operator always returns a floating point number,
and so would `choose(5,3)`. Instead, since `choose` has a return type
annotation, Reticulated detects the problem at its source and reports it.

#### Aside: why not assertions? ####

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

#### Collections ####

At this point, we've only used `int` as a type annotation, and you're
probably wondering what else there is. Reticulated Python supports
lots of other types -- you can skip ahead to the [quick
reference](#reference) to take a look -- but for now lets move on to
Reticulated's _collection types_: types for lists, sets, dictionaries,
and tuples. 

_Open [tutorial3.py](tutorial3.py)._

Let's start off with a function that takes a list of floats and
returns a float, the sum of squares function<sup>[1](#foot1)</sup>.

    def ss(inlist:List(float))->float:
      _ss = 0
      for item in inlist:
        _ss = _ss + item*item
      return _ss

This program uses the type annotation `List(float)`, which represents
(as you might guess) a Python list containing floating point
values. It's easy to define types representing lists of whatever
element type you want: if `T` is any type, then `List(T)` is a list of
that kind of value. This `T` can even be another list --
`List(List(int))` is the type of a two-dimensional list containing
integers. Similarly, unordered sets containing things of type `T` are
written `Set(T)`, dictionaries with keys of type `T` and values of
type `S` are written `Dict(T, S)`, and tuples (of any number of
elements) are written `Tuple(T, S, ...)`, with the number of types
provided matching the number of elements in the tuple.

One important way that values of these types differ from simple
integers, strings, etc. in Python is that these values are _mutable_
-- the number 42 will always be the number 42, but an empty list can
have things added to it. This means that a value that was, at one
time, a list of ints can later have a string added to it:



MUTATION EXAMPLE

You might also want to declare that a variable is a list, but you
don't care what kinds of elements it has. In this case, you can use
the "type" `Dyn`. `Dyn` is the dynamic type, the type of anything in a
Python program. You can sort of think of `Dyn` as the type that
everything has in normal, non-Reticulated Python. So, to write a
list-flattening function that takes a 2D list and returns a 1D list,
you could do the following<sup>[1](#foot1)</sup>:

    def flat(l:List(List(Dyn)))->List(Dyn):
      newl = []
      for l1 in l:
        for j in l1:
          newl.append(j)
      return newl

    :>> flat([[2,5,3], [6,3,2]])
    [2,5,3,6,3,2]
    :>> flat([['a', 'b', 'c'], [1,2,3]])
    ['a', 'b', 'c', 1, 2, 3]
    :>> flat([[[]], [[]]])
    [[], []]
    :>> flat([1,2,3])
    ====STATIC TYPE ERROR=====
    ./tutorial3.py:35:4: Expected argument of type List(List(Dyn)) but value of type List(Int) was provided instead. (code ARG_ERROR)

The fact that we can pass a `List(List(int))` like `[[2,5,3],
[6,3,2]]` into a function that expects something of type
`List(List(Dyn))` reveals probably the most important thing to
understand about how Reticulated Python's types interact with each
other: the idea of _type consistency_. We've already seen that it's
possible to pass something with static type `int` into a function with
no type annotations at all, and vice versa. 


#### Objects and classes ####

#### Higher-order functions ####

#### Advanced topics ####

To include: self types, explanation of type inference, generics (in the future), what else?

### Quick reference for types <a id="reference"></a>###

For a full reference to Reticulated Python's types and operators and
what they do, see the [Reticulated manual][]. Here, `T`, `S`, and `U` are standins
for types.

_Basic types_: `int, str, float, complex, bytes`

_The dynamic/any type_: `Dyn`

_Collection types_: `List(T), Set(T), Dict(S,T), Tuple(T,S,...)`

_Object types_: Class name, or `{"fieldname": T, "fieldname": S, ...}`

_Self type_: `Self`

_Function types_: `Function([S, T, ...], U)`

_Object field annotation_: `@fields({"fieldname": T, "fieldname": S, ...})`

_Class member annotation_: `@members({"membername": T, "membername": S, ...})`

-------------------------

<sup>1</sup><a id="foot1"></a> Adapted from Gary Strangman's statistics library, <https://code.google.com/p/python-statlib/>

[download Reticulated]: https://github.com/mvitousek/reticulated/archive/master.zip
[Reticulated manual]: manual.md

<!-- Optional Typing for Python by Guido -->
