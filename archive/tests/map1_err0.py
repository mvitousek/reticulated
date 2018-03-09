def map(f : Function([Int],Bool), ls : List(Int)) -> List(Int):
  return [f(x) for x in ls]

def inc(x) -> Int:    # Function([Dyn], Int)
  return x + 1

ls = map(inc, [1,2,3])
print(ls)
