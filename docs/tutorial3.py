#!/usr/bin/env retic

# The sum of squares function, which takes a list 
# of floats
def ss(inlist:List(float))->float:
  _ss = 0
  for item in inlist:
    _ss = _ss + item*item
  return _ss

# We're being imprecise here so we don't have to
# stress about floating point errors.
sqsum1 = ss([3.2, 5.4, 2.5])
assert sqsum1 > 45 and sqsum1 < 46

try:
  ss([3.5, 3.2, 'hello world!'])
except RuntimeTypeError:
  # Try removing this try/catch block to see
  # what exception is raised.
  print('An exception has been raised!')

# Mutating a list
def append_to_list(lst:List(int), newitem):
  lst.append(newitem)

try:
  append_to_list([1,2,3], '42')
except RuntimeTypeError:
  # Try removing this try/catch block to see
  # what exception is raised.
  print('An exception has been raised!')

# The list-flattening function
def flat(l:List(List(Dyn)))->List(Dyn):
  newl = []
  for l1 in l:
    for j in l1:
      newl.append(j)
  return newl

# Must pass in a list of lists, but any kind of value can be 
# in the inner lists.
assert flat([[2,5,3], [6,3,2]]) == [2,5,3,6,3,2]
assert flat([['a', 'b', 'c'], [1,2,3]]) == ['a', 'b', 'c', 1, 2, 3]
assert flat([[[]], [[]]]) == [[],[]]

## We get a static type error if we pass in something that's not a 
## list of lists, though.
## Uncomment the following and then run this file to see what 
# happens:
#
#flat([1,2,3])
#
