def map(f : Function([int],int), ls : List[int]) -> List[int]:
  return [f(x) for x in ls]

def inc(x) -> int:    # Function([Dyn], int)
  return x + 1

ls = map(inc, [1,2,3])
print(ls)
