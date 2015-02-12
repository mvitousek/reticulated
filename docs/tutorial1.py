#!/usr/bin/env retic

import traceback

# Without type checking, issues arise!
def is_odd(num):
    return num % 2

# Works fine when we only pass in integers...
assert is_odd(42) == 0
assert is_odd(1001) == 1
print('42 is even and 1001 is odd, so far so good')

# ...but confusing if other things passed in.
try:
    is_odd('42')
except TypeError:
    traceback.print_exc() # String formatting??

assert bool(is_odd(4.2))
if is_odd(4.2):
    print('Apparently, 4.2 is an odd number?')

# So let's add in some type annotations.
# Flip to tutorial2.py
