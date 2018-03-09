def ss(inlist:List(float))->float:
  ss = 0
  for item in inlist:
    ss = ss + item*item
  return ss

ss([2.3])
