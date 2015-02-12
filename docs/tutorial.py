# Without type checking, issues arise!
def is_odd(num):
    return num % 2

# Works fine when we only pass in integers...
assert is_odd(42) == 0
assert is_odd(1001) == 1

# ...but confusing if other things passed in.
try:
    is_odd('42')
except TypeError as e:
    print(e) # String formatting??

assert bool(is_odd(4.2))
if is_odd(4.2):
    print('Apparently, 4.2 is an odd number?')

# So let's add in some type annotations.
def is_odd(num: int):
    return num % 2

