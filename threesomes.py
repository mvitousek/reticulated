#!/usr/bin/python3

from rtypes import *
import pypat, relations
from pypat import Or, Guard, As
from adt import ADT
import traceback

class Threesome(pypat.PureMatchable):
    def __init__(self, s, m, l, t):
        self.src = s
        self.mid = m
        self.trg = t
        self.labels = l
    @classmethod
    def from_twosome(cls, s, t, msg, line):
        mid = relations.info_join(s, t)
        exc = make_blame(msg, line)
        if not mid.top_free():
            blame(exc)
        label = make_label(s, t, exc)
        return Threesome(s, mid, label, t)
    def __str__(self):
        return '{0} ={1}/{2}=> {3}'.format(self.src, self.mid, self.labels, self.trg)

Label = ADT(name='Label')
Labeled = ADT(name='Labeled')
ParamLabeled = ADT(name='ParamLabeled')
RefLabels = ADT(name='RefLabels')
FieldLabels = ADT(name='FieldLabels')
ImmutFieldLabels = ADT(name='ImmutFieldLabels')

LLabel = Label(Exception, name='LLabel')
LNone = Label(name='LNone')

LDyn = Labeled(name='LDyn')
LBase = Labeled(Base, Label, name='LBase')
LFunction = Labeled(ParamLabeled, Label, Labeled, name='LFunction')
LList = Labeled(RefLabels, Label, name='LList')
LDict = Labeled(RefLabels, RefLabels, Label, name='LDict')
LTuple = Labeled(list, Label, name='LTuple')
LSet = Labeled(RefLabels, Label, name='LSet')
LObject = Labeled(dict, Label, name='LObject')
LClass = Labeled(dict, dict, Label, name='LClass')

LDynParams = ParamLabeled(name='LDynParams')
LNamedParams = ParamLabeled(list, Label, name='LNamedParams')
LAnonParams = ParamLabeled(list, Label, name='LAnonParams')

LRef = RefLabels(Labeled, Labeled, name='LRef')

LField = FieldLabels(RefLabels, Label, name='LField') 
LImmutField = ImmutFieldLabels(Labeled, Label, name='LImmutField')

def labelize(ty, exc):
    match = pypat.Match()
    parmatch = pypat.Match()

    def memberinj(members):
        ret = {}
        for x in members:
            ret[x] = LField(LRef(match(members[x]), match(members[x])), exc)
        return ret
    def imemberinj(members):
        ret = {}
        for x in members:
            ret[x] = (match(members[x]), exc)

    match.add(Dyn, lambda: LDyn())
    match.add(As('x', Base), lambda x: LBase(x, exc))
    match.add(As('x', Set), lambda x: LSet(LRef(match(x.type), match(x.type)), exc))
    match.add(As('x', List), lambda x: LList(LRef(match(x.type), match(x.type)), exc))
    match.add(As('x', Function), lambda x: LFunction(parmatch(x.froms), exc, match(x.to)))
    match.add(As('x', Dict), lambda x: LDict(LRef(match(x.keys), match(x.values)),
                                             LRef(match(x.keys), match(x.values)), exc))
    match.add(As('x', Tuple), lambda x: LTuple([match(e) for e in x.elements], exc))
    match.add(As('x', Object), lambda x: LObject(memberinj(x.members), exc))
    match.add(As('x', Class), lambda x: LClass(memberinj(x.members), imemberinj(x.instance_members), exc))

    parmatch.add(DynParameters, lambda: LDynParams())
    parmatch.add(As('x', NamedParameters), 
                 lambda x: LNamedParams([(k, match(v)) for k,v in x.parameters], exc)) 
    parmatch.add(As('x', AnonymousParameters), 
                 lambda x: LAnonParams([match(v) for v in x.parameters], exc))
    return match(ty)

def make_blame(msg, line):
    return LLabel(Exception())

def make_label(s, t, exc):
    s = labelize(s, LNone())
    t = labelize(t, LNone())
    
    _ = '_'
    return pypat.match((s, t),
                       ((LBase('ty', _), LBase('ty', _)), 
                        lambda ty: LBase(ty, LNone())),
                       ((LBase('ty1', _), LBase('ty2', _)),
                        lambda ty: blame(exc)),
                       ((LDyn, LDyn), 
                        lambda: LDyn()),
                       ((LDyn, LBase('ty', _)),
                        lambda ty: LBase(ty, exc)),
                       ((LDyn, LFunction('_', 'p', 't')), 
                        lambda p,t: LFunction(make_param_label(p, LDynParams(), exc), exc, make_label(LDyn(), t, exc))),
                       ((LBase('ty', _), LDyn),
                        lambda ty: LBase(ty, LNone())),
                       ((LFunction('p', _, 't'), LDyn),
                        lambda p,t: LFunction(make_param_label(LDynParams(), p, exc), LNone(), make_label(t, LDyn(), exc))),
                       ((LFunction('p1', _, 't1'), LFunction('p2', _, 't2')),
                        lambda p1,t1,p2,t2: LFunction(make_param_label(p2, p1, exc), LNone(), make_label(t1, t2, exc))),
                       ((LObject('m', _), LDyn), 
                        lambda m: make_obj_label(m, LDyn(), LNone())),
                       ((LDyn, LObject('m', _)),
                        lambda m: make_obj_label(LDyn(), m)),
                       ((LObject('m1', _), LObject('m2', 'i2')),
                        make_obj_label),
                       ((LClass('m','i', _), LDyn), 
                        lambda m: make_class_label(m, i, LDyn(), LDyn())),
                       ((LDyn, LObject('m','i')),
                        lambda m: make_class_label(LDyn(), LDyn(), m, i)),
                       ((LClass('m1', 'i1', _), LClass('m2', 'i2', _)),
                        make_class_label),
                       ('_', lambda: blame(exc)))

def make_obj_label(*args):
    raise Exception('undefined')

def make_class_label(*args):
    raise Exception('undefined')

@pypat.matchable(LLabel('t'))
def blame(t):
    raise t
    
def compose_threesome(t1, t2):
    assert(relations.subtype({}, None, t1.trg, t2.src))
    labels = compose_labels(t1.labels, t2.labels)
    mid = relations.info_join(t1.mid, t2.mid)
    assert mid.top_free() # If goes to top, compose_labels should already have blamed someone
    return Threesome(t1.src, mid, labels, t2.trg)

def compose_labels(p1, p2):
    return pypat.match((p1, p2),
                       ((LDyn, 'x'), Or(('x', LDyn)), 
                                  lambda x: x),
                       ((LBase('t', 'p'), LBase('t', '_')), 
                                  lambda p,t: p1),
                       ((LBase('t1', '_'), LBase('t2', 'p')), 
                                  lambda p, t1, t2: blame(p)),
                       ((LFunction('p', 'a1', 't1'), LFunction('_', 'a2', 't2')),
                                  lambda p,a1,t1,a2,t2: LFunction(p, compose_params(a1, a2), 
                                                                  compose_labels(t1, t2))),
                       ((LSet('p','l1'), LSet('_','l2')), Or((LList('p','l1'), LList('_','l2'))),
                                  lambda p,l1,l2: p1.__class__(p,compose_labels(l1,l2))),
                       ((LDict('p', 'l1k','l1v'), LDict('_', 'l2k', 'l2v')),
                                  lambda p,l1k,l1v,l2k,l2v: LDict(p, compose_labels(l1k, l2k), 
                                                                  compose_labels(l1v, l2v))),
                       ((LObject('p', 'm1'), LObject('_', 'm2')),
                                  lambda p,m1,m2: LObject(p, compose_map(m1,m2))),
                       ((LClass('p', 'm1', 'i1'), LClass('_', 'm2', 'i2')),
                                  lambda p,m1,m2,i1,i2: LObject(p, compose_map(m1,m2), 
                                                                compose_map(i1, i2))),
                       ((LTuple, LTuple),
                                  lambda: LTuple(p1.exc, compose_tuple(p1.lelements, p2.lelements))),
                       ('_',      lambda: blame(p2.exc)))

@pypat.matchable(LDynParams, 'x', Or(('x', LDynParams)))
def compose_params(x):
    return x

@compose_params.case(LNamedParams('p', 'p1'), LNamedParams('q','p2'))
def compose_params(p, q, p1, p2):
    if len(p1) != len(p2):
        blame(q)
    elif [k for k,v in p1] != [k for k,v in p2]:
        return LAnonParams(p, [compose_labels(v2, v1) for (_,v2),(_,v1) in zip(p2,p1)])
    else:
        return LNamedParams(p, [(k, compose_labels(v2, v1)) for (k,v2),(_,v1) in zip(p2,p1)])

@compose_params.case(LAnonParams('p', 'p1'), LAnonParams('q','p2'))
def compose_params(p, q, p1, p2):
    if len(p1) != len(p2):
        blame(q)
    else:
        return LAnonParams(p, [compose_labels(v2, v1) for v2,v1 in zip(p2,p1)])

@compose_params.case(LNamedParams('p', 'p1'), LAnonParams('q','p2'))
def compose_params(p, q, p1, p2):
    if len(p1) != len(p2):
        blame(q)
    else:
        return LAnonParams(p, [compose_labels(v2, v1) for v2,(_, v1) in zip(p2,p1)])

@compose_params.case(LAnonParams('p', 'p1'), LNamedParams('q','p2'))
def compose_params(p, q, p1, p2):
    if len(p1) != len(p2):
        blame(q)
    else:
        return LAnonParams(p, [compose_labels(v2, v1) for (_, v2),v1 in zip(p2,p1)])

@compose_params.case('_', 'y')
def compose_params(y):
    blame(y.exc)
    
if __name__ == '__main__':
    inj = Threesome.from_twosome(Int, Dyn, 'hella', 42)
    proj = Threesome.from_twosome(Dyn, Int, 'rad', 33)
    inout = compose_threesome(inj, proj)
    print(inj, proj, inout)
