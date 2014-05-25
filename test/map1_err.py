
def map(f : Function([Dyn],Int)) -> Void:
  pass

map(lambda x: False) # should be a static type error
