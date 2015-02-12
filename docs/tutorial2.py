#!/usr/bin/env retic

# Now we've added a type annotation to is_odd:

def is_odd(num: int):
  return num % 2

# We still get the same good behavior with correct inputs...
assert is_odd(42) == 0
assert is_odd(1001) == 1
print('42 is even and 1001 is odd, so far so good')

## And when we provide bad inputs, we get alerted immediately.
## Uncomment the following and then run this fileto see what 
# happens:
#
#is_odd('42')
#
## Re-comment the above code, and then do the same for this:
#
#is_odd(4.2)
#

# Errors that aren't immediately obvious can be caught too, 
# but they're caught at runtime rather than ahead of time:

def pow(b, n):
  if n == 0:
    return 1
  elif n == 1:
    return b
  elif is_odd(n):
    return b * pow(b*b, (n-1)//2) # Reminder: // is integer division, rounding down
  else: 
    return pow(b*b, n//2)

assert pow(42,5) == 130691232
print('So far, so good')

# Now, Reticulated will detect that pow is trying
# to pass 4.2 into is_odd, but at runtime.
# This call should cause an exception.
try:
  pow(42,4.2)
except RuntimeTypeError:
  print('An exception has been raised!')
  raise
