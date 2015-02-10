import importer
import gatherers
import typing
from typing import Var, tyinstance
import flags
import fixed_typefinder as typefinder
import inferfinder
import new_typecheck as typecheck_mod
import inference

class NoGLB(Exception):
    pass

def typecheck(n, filename, import_depth, ext_aliases, inference_enabled=True):
    # Import definitions
    typing.debug('Importing starting in %s' % filename, flags.PROC)
    imported = importer.ImportFinder().preorder(n, import_depth)
    imported, imp_types = separate_bindings_and_types(imported)
    typing.debug('Importing finished in %s' % filename, flags.PROC)
    
    # Collect class aliases
    typing.debug('Alias search started in %s' % filename, flags.PROC)
    class_aliases = gatherers.Classfinder().preorder(n)
    alias_scope = merge(class_aliases, ext_aliases)
    alias_scope = merge(alias_scope, imp_types)
    typing.debug('Alias search finished in %s' % filename, flags.PROC)

    # Build inheritance graph
    typing.debug('Inheritance checking started in %s' % filename, flags.PROC)
    inheritance = gatherers.Inheritfinder().preorder(n)
    inheritance = transitive_closure(inheritance)
    typing.debug('Inheritance checking finished in %s' % filename, flags.PROC)

    # Collect nonlocal and global variables
    typing.debug('Globals search started in %s' % filename, flags.PROC)
    externals = gatherers.Killfinder().preorder(n)
    typing.debug('Globals search finished in %s' % filename, flags.PROC)
    
    # Collect fixed (i.e. statically annotated) variables
    typing.debug('Annotation search started in %s' % filename, flags.PROC)
    fixed = typefinder.Typefinder().preorder(n, alias_scope)
    fixed = merge(fixed, imported)
    fixed, subchecks = propagate_inheritance(fixed, inheritance)
    typing.debug('Annotation search started in %s' % filename, flags.PROC)

    typing.debug('Alias resolution started in %s' % filename, flags.PROC)
    classes = find_classdefs(class_aliases, fixed)
    classes = mutual_substitution(classes)
    fixed = dealias(fixed, classes)
    check_that_subtypes_hold(fixed, subchecks)
    typing.debug('Alias resolution finished in %s' % filename, flags.PROC)

    typing.debug('Inference starting in %s' % filename, flags.PROC)
    typechecker = typecheck_mod.Typechecker()
    inferred = inferfinder.Inferfinder(inference_enabled).preorder(n)
    inferred = exclude_fixed(inferred, fixed)
    env = merge(inferred, fixed)
    env = inference.InferVisitor().infer(typechecker, inferred, fixed, n, env, typecheck_mod.Misc())
    typing.debug('Inference finished in %s' % filename, flags.PROC)
    
    prog, ty = typechecker.typecheck(n, filename, import_depth, env)
    return prog, ty

def separate_bindings_and_types(imported):
    bindings = {}
    types = {}
    for k in imported:
        if isinstance(k, typing.TypeVariable):
            types[k.var] = imported[k]
        else:
            bindings[k] = imported[k]
    return bindings, types

def merge(map1, map2):
    out = {}
    for k in map1:
        if k in map2:
            stronger = relations.info_join(map1[k], map2[k])
            if stronger.top_free():
                out[k] = stronger
            else: raise NoGLB()
        else:
            out[k] = map1[k]
    for k in map2:
        if k not in map1:
            out[k] = map2[k]
    return out

def transitive_closure(inheritance):
    inheritance = {(0, k, v) for k, v in inheritance}
    while True:
        new = {(max(k1, k2) + 1, x, w) for k1,x,y in inheritance\
               for k2,z,w in inheritance if y == z and\
               not any((a == x and b == w) for _, a, b in inheritance)}
        new_inherit = inheritance | new
        if new_inherit == inheritance:
            break
        else:
            inheritance = new_inherit
    return inheritance

def propagate_inheritance(defs, inheritance):
    subchecks = []
    defs = defs.copy()
    for (_, cls, supe) in sorted(list(inheritance)):
        if Var(cls) in defs and tyinstance(defs[Var(cls)], typing.Class):
            if Var(supe) in defs and supe not in externals:
                src = defs[Var(supe)]
            else: continue
            if not tyinstance(src, typing.Class):
                continue
            mems = src.members.copy()
            mems.update(defs[Var(cls)].members)
            defs[Var(cls)].members.clear()
            defs[Var(cls)].members.update(mems)
            subchecks.append((Var(cls), src))
    return defs, subchecks

def find_classdefs(aliases, defs):
    classmap = {}
    for alias in aliases:
        cls = defs[typing.Var(alias)]
        inst = cls.instance() if tyinstance(cls, typing.Class) else typing.Dyn
        classmap[alias] = inst
        classmap[alias + '.Class'] = cls
    return classmap

def mutual_substitution(alias_map):
    orig_map = alias_map.copy()
    while True:
        new_map = alias_map.copy()
        for alias1 in new_map:
            for alias2 in orig_map:
                if alias1 == alias2:
                    continue
                else:
                    new_map[alias1] = new_map[alias1].copy().\
                                      substitute_alias(alias2, orig_map[alias2].copy())
        if new_map == alias_map:
            break
        else: alias_map = new_map
    return alias_map

def dealias(map, new_map):
    for var in map:
        for alias in new_map:
            if isinstance(var, typing.StarImport):
                if map[var] is not map:
                    dealias(map[var])
            else:
                map[var] = map[var].substitute_alias(alias, new_map[alias])
    return map

def check_that_subtypes_hold(defs, subchecks):
    for (var, supty) in subchecks:
        subty = defs[var]
        lenv = env.copy()
        lenv.update(indefs)
        lenv.update(defs)
        lenv.update({TypeVariable(k):new_map[k] for k in new_map})
        if (flags.SUBCLASSES_REQUIRE_SUBTYPING and not\
            subtype(lenv, InferBottom, subty.instance(), supty.instance())) or\
                (not flags.SUBCLASSES_REQUIRE_SUBTYPING and\
                 not subcompat(subty.instance(), supty.instance())):
            raise StaticTypeError('Subclass %s is not a subtype in file %s' % (var.var, filename))

def remove_nonlocals(env, killset):
    pass

def exclude_fixed(infers, fixed):
    return {x:infers[x] for x in infers if x not in fixed}
