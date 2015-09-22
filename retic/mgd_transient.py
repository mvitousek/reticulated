from .runtime import has_type as retic_has_type
from .relations import tyinstance as retic_tyinstance
from . import rtypes
import inspect, weakref
from .exc import RuntimeTypeError
from .rtypes import pinstance
from threading import Thread
from queue import Queue


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

queue = None
manager = None
casts = []

def get_paramtype_by_position(ty, pos):
    params = ty.froms
    if pinstance(params, rtypes.DynParameters):
        return rtypes.Dyn()
    elif pinstance(params, rtypes.NamedParameters):
        return params.parameters[pos][1]
    elif pinstance(params, rtypes.AnonymousParameters):
        return params.parameters[pos]
    else: raise Exception('bad')

# def manage():
#     casts = []
#     while True:
#         ent = queue.get()
#         if ent[0] == 'CHECKFAIL':
#             fval, fmsg, exc = ent[1:]
#             tmsg = ''
#             for cast in casts:
#                 casted, _, _, cmsg = cast
#                 if casted is fval:
#                     tmsg += '\n\n' + cmsg
#             raise exc(fmsg + '\n\n' + tmsg)
#         elif ent[0] == 'CAST':
#             casts.append(ent[1:])
#         elif ent[0] == 'CHECK':
#             if ent[1] == 'GETATTR':
#                 val, attr, res, trg, msg, exc = ent[2:]
#                 if not retic_has_type(res, trg):
#                     tmsg = 'Possible culprits:'
#                     for cast in casts:
#                         casted, csrc, ctrg, cmsg = cast
#                         if casted is val and not retic_has_type(res, csrc.member_type(attr)) and retic_has_type(val, ctrg.member_type(attr)):
#                             tmsg += '\n\n' + cmsg
#                     raise exc(msg + '\n\n' + tmsg)
#             elif ent[1] == 'ARG':
#                 val, fun, position, trg, msg, exc = ent[2:]
#                 if not retic_has_type(val, trg):
#                     tmsg = 'Possible culprits'
#                     for cast in casts:
#                         casted, csrc, ctrg, cmsg = cast
#                         if casted is fun and not retic_has_type(val, get_paramtype_by_position(csrc, position)) \
#                            and retic_has_type(val, get_paramtype_by_position(ctrg, position)):
#                             tmsg += '\n\n' + cmsg
#                     raise exc(msg + '\n\n' + tmsg)
#             else: raise Exception('bad action')
#         else: raise Exception('bad message')

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

dummyref = lambda: None            
def makeref(v):
    try: 
        return weakref.ref(v)
    except TypeError:
        if isinstance(v, list) or isinstance(v, dict) or isinstance(v, tuple):
            return lambda: v
        else: return dummyref

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
    casts.append((makeref(val), src, trg, msg))

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
