# Now we've added a type annotation to is_odd:

def is_odd(num: int):
  return num % 2

# We still get the same good behavior with correct inputs...
assert is_odd(42) == 0
assert is_odd(1001) == 1
print('42 is even and 1001 is odd, so far so good')

## And when we provide bad inputs, we get alerted immediately.
## Uncomment the following to see what happens:
#
#is_odd('42')
#
## Re-comment the above code, and then do the same for this:
#
#is_odd(4.2)
#
