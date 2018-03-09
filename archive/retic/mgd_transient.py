from .runtime import has_type as retic_has_type
from .relations import tyinstance as retic_tyinstance
from . import rtypes, relations, flags
import inspect, weakref
from .exc import RuntimeTypeError
from .rtypes import pinstance
from threading import Thread
from queue import Queue

GETATTR = 0
GETITEM = 1
ARG = 2
RETURN = 3

class LabeledType: pass

class DynLabeled(LabeledType): pass

class BaseLabeled(LabeledType):
    def __init__(self, ty, info):
        self.ty = ty
        self.info = info

class CallableLabeled(LabeledType):
    def __init__(self, froms, to, info):
        self.froms = froms
        self.to = to
        self.info = info
        
class ListLabeled(LabeledType):
    def __init__(self, type, info):
        self.type = type
        self.info = info

class BotLabeled(LabeledType):
    def __init__(self):
        pass
        

def meet(ty1, ty2):
    if isinstance(ty1, DynLabeled):
        return ty2
    elif isinstance(ty2, DynLabeled):
        return ty1
    elif isinstance(ty1, BaseLabeled):
        if isinstance(ty2, BaseLabeled):
            if isinstance(ty1.type, type(ty2.type)):
                return ty1
            else: 
                return BotLabeled()
        else: raise Exception()
    elif isinstance(ty1, CallableLabeled):
        pass
# L ::= B^l | _|_^{Ls} | L -> ^l L
#  use 3some labeled types in a set

class CastError(RuntimeTypeError):
    pass
class FunctionCastTypeError(CastError, TypeError):
    pass
class ObjectTypeAttributeCastError(CastError, AttributeError):
    pass
class CheckError(RuntimeTypeError):
    pass
class FunctionCheckTypeError(CastError, TypeError):
    pass
class ObjectTypeAttributeCheckError(CastError, AttributeError):
    pass

casts = []

castdata = {} #weakref.WeakKeyDictionary()


dummyref = lambda: None            
def makeref(v):
    try: 
        return weakref.ref(v)
    except TypeError:
        if isinstance(v, list) or isinstance(v, dict) or isinstance(v, tuple):
            return lambda: v
        else: return dummyref

def do_not_track(v):
    return any(isinstance(v, t) for t in [int, str, bool, float, complex])

def update_casts(val, src, trg, msg):
    if do_not_track(val):
        return
    ref = id(val)
    if ref in castdata:
        meet, ids = castdata[ref]
    else:
        meet = rtypes.Dyn
        ids = []
    new_meet = relations.n_info_join(meet, src, trg)
    if new_meet != meet:
        ids.append(msg)
        castdata[ref] = new_meet, ids

def get_cast_history(val):
    return castdata[id(val)]

def matches(val, ident):
    return id(val) == ident

def get_paramtype_by_position(ty, pos):
    params = ty.froms
    if pinstance(params, rtypes.DynParameters):
        return rtypes.Dyn()
    elif pinstance(params, rtypes.NamedParameters):
        return params.parameters[pos][1]
    elif pinstance(params, rtypes.AnonymousParameters):
        return params.parameters[pos]
    else: raise Exception('bad')

# Improved part
# def blame_getattr(val, attr, res, trg, msg, exc):
#     tmsg = 'Possible culprits:'
#     meet, msgs = get_cast_history(val
#     for cast in casts:
#         casted, csrc, ctrg, cmsg = cast
#         if matches(val, casted) and not retic_has_type(res, csrc.member_type(attr, default=rtypes.Dyn()))
#             tmsg += '\n\n' + cmsg
#     raise exc(msg + '\n\n' + tmsg)

def blame_getattr(val, attr, res, trg, msg, exc):
    tmsg = 'Possible culprits:'
    for cast in casts:
        casted, csrc, ctrg, cmsg = cast
        if casted() is val and (retic_has_type(res, csrc.member_type(attr, default=rtypes.Dyn())) !=
           retic_has_type(val, ctrg.member_type(attr, default=rtypes.Dyn()))):
            tmsg += '\n\n' + cmsg
    raise exc(msg + '\n\n' + tmsg)

def blame_getitem(val, provider, trg, msg, exc):
    tmsg = 'Possible culprits:'
    for cast in casts:
        casted, csrc, ctrg, cmsg = cast
        if casted() is provider and not retic_has_type(provider, csrc) and\
           retic_has_type(provider, ctrg):
            tmsg += '\n\n' + cmsg
    raise exc(msg + '\n\n' + tmsg)

def blame_arg(val, fun, position, trg, msg, exc):
    tmsg = 'Possible culprits'
    for cast in casts:
        casted, csrc, ctrg, cmsg = cast
        if casted() is fun and not retic_has_type(val, get_paramtype_by_position(csrc, position)) \
           and retic_has_type(val, get_paramtype_by_position(ctrg, position)):
            tmsg += '\n\n' + cmsg
    raise exc(msg + '\n\n' + tmsg)

def blame_return(val, fun, trg, msg, exc):
    tmsg = 'Possible culprits'
    for cast in casts:
        casted, csrc, ctrg, cmsg = cast
        print(fun, casted(), csrc, ctrg, cmsg[:20])
        if casted() is fun and retic_has_type(val, csrc.to) \
           and not retic_has_type(val, ctrg.to):
            tmsg += '\n\n' + cmsg
    raise exc(msg + '\n\n' + tmsg)

# def start_manager():
#     global queue
#     global manager
#     queue = Queue()
#     manager = Thread(target=manage, args=())
#     manager.start()

def retic_assert(bool, val, msg, ulval, exc=None):
    if not bool:
        if exc is None:
            exc = CastError
        # if ulval is not None:
        #     # if queue is None:
        #     #     start_manager()
        #     queue.put(('CHECKFAIL', ulval, msg % ('\'%s\'' % str(val)), exc))
        else:
            raise exc(msg % ('\'%s\'' % str(val)))

def retic_cast(val, src, trg, msg):
    # if queue is None:
    #     start_manager()
    #casts.append((makeref(val), src, trg, msg))
    
    update_casts(val, src, trg, msg)

    if retic_tyinstance(trg, rtypes.Object):
        exc = ObjectTypeAttributeCastError
    elif retic_tyinstance(trg, rtypes.Function) and retic_tyinstance(src, rtypes.Dyn):
        exc = FunctionCastTypeError
    else: exc = CastError
    retic_assert(retic_has_type(val, trg), val, msg, None, exc)
    return val

def retic_check(ulval, val, trg, msg):
    if retic_tyinstance(trg, rtypes.Object):
        exc = ObjectTypeAttributeCheckError
    elif retic_tyinstance(trg, rtypes.Function):
        exc = FunctionCheckTypeError
    else: exc = CheckError
    retic_assert(retic_has_type(val, trg), val, msg, ulval, exc)
    return val


def retic_mgd_check(val, act, args, trg, msg):
    if retic_tyinstance(trg, rtypes.Object):
        exc = ObjectTypeAttributeCheckError
    elif retic_tyinstance(trg, rtypes.Function):
        exc = FunctionCheckTypeError
    else: exc = CheckError

    if act == 'GETATTR':
        (attr,) = args
        res = getattr(val, attr)
        if not retic_has_type(res, trg):
            blame_getattr(val, attr, res, trg, msg, exc)
        else:
            for cast in casts:
                casted, csrc, ctrg, cmsg = cast
                if casted() is val:
                    casts.append((makeref(res), ctrg.member_type(attr, default=rtypes.Dyn()), 
                                  csrc.member_type(attr, default=rtypes.Dyn()), cmsg))
    elif act == 'ARG':
        (fun, position) = args
        res = val
        if not retic_has_type(res, trg):
            blame_arg(val, fun, position, trg, msg, exc)
        else:
            for cast in casts:
                casted, csrc, ctrg, cmsg = cast
                if casted() is fun:
                    casts.append((makeref(res), get_paramtype_by_position(csrc, position), 
                                  get_paramtype_by_position(ctrg, position), 'ACO' + cmsg))
                    casts.append((makeref(res), get_paramtype_by_position(ctrg, position), 
                                  get_paramtype_by_position(csrc, position), 'ACON' + cmsg))
    elif act == 'RETURN':
        (fun,) = args
        res = val
        if not retic_has_type(res, trg):
            blame_return(val, fun, trg, msg, exc)
        else:
            for cast in casts:
                casted, csrc, ctrg, cmsg = cast
                if casted() is fun:
                    casts.append((makeref(res), csrc.to, ctrg.to, cmsg))
    elif act == 'GETITEM':
        (provider,) = args
        res = val
        if not retic_has_type(res, trg):
            blame_getitem(val, provider, trg, msg, exc)
        else:
            for cast in casts:
                casted, csrc, ctrg, cmsg = cast
                if casted() is provider:
                    casts.append((makeref(res), getattr(ctrg, 'type', rtypes.Dyn()), 
                                  getattr(csrc, 'type', rtypes.Dyn()), cmsg))
            
    else: raise Exception('bad action')

    return res

def retic_error(msg):
    raise CastError(msg)

def retic_actual(v):
    return v

#=============================================

blame_set = []

GETATTR = 0 # include attr
ARG = 1 #include position
RET = 2
GETITEM = 3

def mgd_check_type_int(val, elim, act):
    if isinstance(val, int):
        return val
    elif not flags.FLAT_PRIMITIVES:
        return mgd_check_type_bool(val, elim, act)
    else:
        blame(val, elim, act)

def mgd_check_type_void(val, elim, act):
    if val is None:
        return val
    else: 
        blame(val, elim, act)

def mgd_check_type_bytes(val, elim, act):
    if isinstance(val, bytes):
        return val
    else: 
        blame(val, elim, act)

def mgd_check_type_bool(val, elim, act):
    if isinstance(val, bool):
        return val
    else: 
        blame(val, elim, act)

def mgd_check_type_float(val, elim, act):
    if isinstance(val, float):
        return val
    elif not flags.FLAT_PRIMITIVES:
        return mgd_check_type_int(val, elim, act)
    else:
        blame(val, elim, act)

def mgd_check_type_complex(val, elim, act):
    if isinstance(val, complex):
        return val
    elif not flags.FLAT_PRIMITIVES:
        return mgd_check_type_float(val, elim, act)
    else:
        blame(val, elim, act)

def mgd_check_type_string(val, elim, act):
    if isinstance(val, str):
        return val
    else: 
        blame(val, elim, act)

def mgd_check_type_function(val, elim, act):
    if callable(val):
        add_blame_pointer(val, elim, act)
        return val
    else: 
        blame(val, elim, act)

def mgd_check_type_list(val, elim, act):
    if isinstance(val, list):
        add_blame_pointer(val, elim, act)
        return val
    else: 
        blame(val, elim, act)

def mgd_check_type_tuple(val, elim, act, n):
    if isinstance(val, tuple) and len(val) == n:
        add_blame_pointer(val, elim, act)
        return val
    else: 
        blame(val, elim, act)

def mgd_check_type_dict(val, elim, act):
    if isinstance(val, dict):
        add_blame_pointer(val, elim, act)
        return val
    else: 
        blame(val, elim, act)

def mgd_check_type_object(val, elim, act, mems):
    for k in mems:
        if not hasattr(val, k):
            blame(val, elim, act)
    add_blame_pointer(val, elim, act)
    return val

def mgd_check_type_class(val, elim, act, mems):
    if val.__class__ is not type:
        blame(val, elim, act)
    for k in mems:
        if not hasattr(val, k):
            blame(val, elim, act)
    add_blame_pointer(val, elim, act)
    return val

# ========================

def mgd_cast_type_dyn(val, src, b, trg):
    add_blame_cast(val, src, b, trg)
    return val

def mgd_cast_type_int(val, src, b, trg):
    if isinstance(val, int):
        return val
    elif not flags.FLAT_PRIMITIVES:
        return mgd_cast_type_bool(val, src, b, trg)
    else:
        do_blame([b])

def mgd_cast_type_void(val, src, b, trg):
    if val is None:
        return val
    else: 
        do_blame([b])

def mgd_cast_type_bytes(val, src, b, trg):
    if isinstance(val, bytes):
        return val
    else: 
        do_blame([b])

def mgd_cast_type_bool(val, src, b, trg):
    if isinstance(val, bool):
        return val
    else: 
        do_blame([b])

def mgd_cast_type_float(val, src, b, trg):
    if isinstance(val, float):
        return val
    elif not flags.FLAT_PRIMITIVES:
        return mgd_cast_type_int(val, src, b, trg)
    else:
        do_blame([b])

def mgd_cast_type_complex(val, src, b, trg):
    if isinstance(val, complex):
        return val
    elif not flags.FLAT_PRIMITIVES:
        return mgd_cast_type_float(val, src, b, trg)
    else:
        do_blame([b])

def mgd_cast_type_string(val, src, b, trg):
    if isinstance(val, str):
        return val
    else: 
        do_blame([b])

def mgd_cast_type_function(val, src, b, trg):
    if callable(val):
        add_blame_cast(val, src, b, trg)
        return val
    else: 
        do_blame([b])

def mgd_cast_type_list(val, src, b, trg):
    if isinstance(val, list):
        add_blame_cast(val, src, b, trg)
        return val
    else: 
        do_blame([b])

def mgd_cast_type_tuple(val, src, b, trg, n):
    if isinstance(val, tuple) and len(val) == n:
        add_blame_cast(val, src, b, trg)
        return val
    else: 
        do_blame([b])

def mgd_cast_type_dict(val, src, b, trg):
    if isinstance(val, dict):
        add_blame_cast(val, src, b, trg)
        return val
    else: 
        blame(val, elim, act)

def mgd_cast_type_object(val, src, b, trg, mems):
    for k in mems:
        if not hasattr(val, k): 
            do_blame([b])
    add_blame_cast(val, src, b, trg)
    return val

def mgd_cast_type_class(val, src, b, trg, mems):
    if val.__class__ is not type:
        do_blame([b])
    for k in mems:
        if not hasattr(val, k):
            do_blame([b])
    add_blame_cast(val, src, b, trg)
    return val

casted = {}
pointed = {}

def add_blame_cast(val, src, b, trg):
    key = id(val)
    if key in casted:
        cid = id(b)
        if cid in casted[key]:

            return
        else: casted[key][cid] = 0
    else: casted[key] = {}

    cast = (src, b, trg)
    blame_set.append((key, cast))

def add_blame_pointer(val, elim, act):
    key = id(val)
    eid = id(elim)
    if key in pointed:
        if eid in pointed[key]:
            if act in pointed[key][eid]:
                return
            else: pointed[key][eid].append(act)
        else: pointed[key][eid] = []
    else: pointed[key] = {}
    blame_set.append((key, (eid, act)))

def blame(val, elim, act):
#    print(blame_set)
    new_blame_set = cleanup_blame_data()
#    print(new_blame_set)
    candidates = []
    for elt in new_blame_set[id(elim)]:
        candidates += collectblame([act], new_blame_set, elt)
    do_blame(resolve(val, candidates))

class BlamePtr:
    def __init__(self, addr, act):
        self.addr = addr
        self.act = act
    def __str__(self):
        return 'Ptr %s %s' % (self.addr, self.act)
    __repr__ = __str__
class BlameCast:
    def __init__(self, src, b, trg, attr=None):
        self.src = src.copy()
        self.b = b
        self.trg = trg.copy()
        self.attr = attr
    def __str__(self):
        return 'Cast %s =%s=> %s (%s)' % (self.src, self.b, self.trg, self.attr)
    __repr__ = __str__
    def extract(self, ls):
        if len(ls) == 0:
            return self
        else:
            act = ls[0]
            ls = ls[1:]
            if isinstance(act, tuple):
                arg = act[1]
                act = act[0]
                if act == GETATTR:
                    return BlameCast(
                        self.src.member_type(arg, default=rtypes.Dyn()), self.b,
                        self.trg.member_type(arg, default=rtypes.Dyn())).extract(ls)
                elif act == ARG:
                    return BlameCast(get_paramtype_by_position(self.src, arg), self.b,
                                     get_paramtype_by_position(self.trg, arg)).extract(ls)
                else: raise Exception()
            elif act == RET:
                return BlameCast(getattr(self.src, 'to', rtypes.Dyn()), self.b,
                                 getattr(self.trg, 'to', rtypes.Dyn())).extract(ls)
            elif act == GETITEM:
                return BlameCast(getattr(self.src, 'to', rtypes.Dyn()), self.b,
                                 getattr(self.trg, 'to', rtypes.Dyn())).extract(ls)
                
                

def cleanup_blame_data():
    print (blame_set)
    data = {}
    for k, v in blame_set:
        if k not in data:
            data[k] = []
        if len(v) == 2:
            data[k].append(BlamePtr(*v))
        else: data[k].append(BlameCast(*v))
    return data

def collectblame(rs, blame_set, elt):
    if isinstance(elt, BlameCast):
        return [elt.extract(rs)]
    else:
        ret = []
        elts = blame_set.get(elt.addr, [])
        for nelt in elts:
            ret += collectblame([elt.act] + rs, blame_set, nelt)
        return ret

def resolve(val, cands):
    reslv = []
    for cast in cands:
#        print(cast)
        if retic_has_type(val, cast.src) != retic_has_type(val, cast.trg):
            reslv.append(cast.b)
    return reslv

def do_blame(bs):
    msg = ''
    for b in bs:
        msg += b + ' '
    raise Exception(msg)









