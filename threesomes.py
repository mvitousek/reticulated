from rtypes import *

class Threesome:
    def __init__(self, s, m, l, t):
        self.src = s
        self.mid = m
        self.trg = t
        self.labels = l

class Label:
    pass

class LBase(Label):
    def __init__(self, exc):
        self.exc = exc
class LFunction(Label):
    def __init__(self, lparams, exc, lret):
        self.lparams = lparams
        self.exc = exc
        self.lret = lret
class LList(Label):
    def __init__(self, exc, lty):
        self.exc = exc
        self.lty = 

def blame(t):
    pass

def compose_threesome(t1, t2):
    assert(subtype(t1.trg, t2.src))
    return Threesome(t1.src, tymeet(t1.mid, t2.mid), compose_labels(t1.labels, t2.labels), t2.trg)

def compose_labels(p1, p2):
    

