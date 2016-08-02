def ss(inlist:List[int])->int:
  ss = 0
  for item in inlist:
    ss = ss + item*item
  return ss

print(ss([2]))
