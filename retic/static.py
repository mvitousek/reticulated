from . import importer
from . import gatherers
from . import typing
from .typing import Var, tyinstance, Misc
from . import flags
from . import typefinder
from . import inferfinder
from . import typecheck as typecheck_mod
from . import inference
from . import relations
from . import annotation_removal
from . import logging
from .exc import StaticTypeError
from .errors import errmsg

class StaticTypeSystem:
    def typecheck_module(self, mod, filename, depth=0, ext=None):
        if ext is None:
            ext = {}
        return self.typecheck(mod, ext, ext, Misc(filename=filename, depth=depth, static=self))

    def typecheck(self, n, ext, fixed, misc):
        ext, ext_types = separate_bindings_and_types(ext)

        # Import definitions
        logging.debug('Importing starting in %s' % misc.filename, flags.PROC)
        imported = importer.ImportFinder().preorder(n, misc.depth, misc)
        imported, imp_types = separate_bindings_and_types(imported)
        logging.debug('Importing finished in %s' % misc.filename, flags.PROC)

        # Collect class aliases
        logging.debug('Alias search started in %s' % misc.filename, flags.PROC)
        class_aliases = gatherers.Classfinder().preorder(n)
        alias_scope = merge(misc, class_aliases, ext_types)
        alias_scope = merge(misc, alias_scope, imp_types)
        logging.debug('Alias search finished in %s' % misc.filename, flags.PROC)

        # Build inheritance graph
        logging.debug('Inheritance checking started in %s' % misc.filename, flags.PROC)
        inheritance = gatherers.Inheritfinder().preorder(n)
        inheritance = transitive_closure(inheritance)
        logging.debug('Inheritance checking finished in %s' % misc.filename, flags.PROC)

        # Collect nonlocal and global variables
        logging.debug('Globals search started in %s' % misc.filename, flags.PROC)
        externals = gatherers.Killfinder().preorder(n)
        logging.debug('Globals search finished in %s' % misc.filename, flags.PROC)

        # Collect fixed (i.e. statically annotated) variables
        logging.debug('Annotation search started in %s' % misc.filename, flags.PROC)
        annotated = typefinder.Typefinder().preorder(n, False, alias_scope, misc)
        fixed = merge(misc, fixed, annotated)
        fixed, subchecks = propagate_inheritance(fixed, inheritance, externals)
        logging.debug('Annotation search started in %s' % misc.filename, flags.PROC)

        # Resolve aliases
        logging.debug('Alias resolution started in %s' % misc.filename, flags.PROC)
        classes = find_classdefs(class_aliases, fixed)
        classes = mutual_substitution(classes)
        fixed = dealias(fixed, classes)
        classes = merge(misc, classes, imp_types)
        classes = merge(misc, classes, ext_types)
        check_that_subtypes_hold(misc, fixed, subchecks)
        logging.debug('Alias resolution finished in %s' % misc.filename, flags.PROC)

        # Collect variables whose types need to be inferred, and perform inference
        logging.debug('Inference starting in %s' % misc.filename, flags.PROC)
        typechecker = typecheck_mod.Typechecker()
        inferred = inferfinder.Inferfinder(True, misc).preorder(n)
        inferred = exclude_fixed(inferred, fixed)
        env = merge(misc, fixed, imported)
        ext.update(env)
        env = ext
        env = inference.InferVisitor().infer(typechecker, inferred, fixed, n, env, misc)
        env = merge(misc,env, lift(classes))
        logging.debug('Inference finished in %s' % misc.filename, flags.PROC)

        # Typecheck and cast-insert the program
        logging.debug('Typecheck starting for %s' % misc.filename, [flags.ENTRY, flags.PROC])
        prog = typechecker.typecheck(n, env, misc)
        logging.debug('Typecheck finished for %s' % misc.filename, flags.PROC)

        # Remove annotations from output AST
        if flags.REMOVE_ANNOTATIONS:
            logging.debug('Annotation removal starting for %s' % misc.filename, flags.PROC)
            remover = annotation_removal.AnnotationRemovalVisitor()
            prog = remover.preorder(prog)
            logging.debug('Annotation removal finished for %s' % misc.filename, flags.PROC)

        return prog, env

    def classtypes(self, n, ext_types, misc):

        # Collect class aliases
        logging.debug('Alias search started in %s' % misc.filename, flags.PROC)
        class_aliases = gatherers.Classfinder().preorder(n)
        alias_scope = merge(misc,class_aliases, ext_types)
        logging.debug('Alias search finished in %s' % misc.filename, flags.PROC)

        # Build inheritance graph
        logging.debug('Inheritance checking started in %s' % misc.filename, flags.PROC)
        inheritance = gatherers.Inheritfinder().preorder(n)
        inheritance = transitive_closure(inheritance)
        logging.debug('Inheritance checking finished in %s' % misc.filename, flags.PROC)

        # Collect nonlocal and global variables
        logging.debug('Globals search started in %s' % misc.filename, flags.PROC)
        externals = gatherers.Killfinder().preorder(n)
        logging.debug('Globals search finished in %s' % misc.filename, flags.PROC)

        # Collect fixed (i.e. statically annotated) variables
        logging.debug('Annotation search started in %s' % misc.filename, flags.PROC)
        fixed = typefinder.Typefinder().preorder(n, False, alias_scope, misc)
        fixed, subchecks = propagate_inheritance(fixed, inheritance, externals)
        logging.debug('Annotation search started in %s' % misc.filename, flags.PROC)

        # Resolve aliases
        logging.debug('Alias resolution started in %s' % misc.filename, flags.PROC)
        classes = find_classdefs(class_aliases, fixed)
        classes = mutual_substitution(classes)
        fixed = dealias(fixed, classes)
        classes = merge(misc,classes, ext_types)
        check_that_subtypes_hold(misc, fixed, subchecks)
        logging.debug('Alias resolution finished in %s' % misc.filename, flags.PROC)

        # Collect local variables, but don't infer their types -- leave as Dyn
        logging.debug('Inference starting in %s' % misc.filename, flags.PROC)
        typechecker = typecheck_mod.Typechecker()
        inferred = inferfinder.Inferfinder(False, misc).preorder(n)
        inferred = exclude_fixed(inferred, fixed)
        env = merge(misc,inferred, fixed)
        env = merge(misc,env, lift(classes))
        logging.debug('Inference finished in %s' % misc.filename, flags.PROC)

        return env


def separate_bindings_and_types(imported):
    bindings = {}
    types = {}
    for k in imported:
        if isinstance(k, typing.TypeVariable):
            types[k.name] = imported[k]
        else:
            bindings[k] = imported[k]
    return bindings, types

def merge(misc, map1, map2):
    out = {}
    for k in map1:
        if k in map2:
            stronger = relations.info_join(map1[k], map2[k])
            if stronger.top_free():
                out[k] = stronger
            else: 
                raise StaticTypeError(errmsg('BAD_DEFINITION', misc.filename, k, k, map1[k], map2[k]))
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

def propagate_inheritance(defs, inheritance, externals):
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
                    dealias(map[var], new_map)
            else:
                map[var] = map[var].substitute_alias(alias, new_map[alias])
    return map

def check_that_subtypes_hold(misc, defs, subchecks):
    for (var, supty) in subchecks:
        subty = defs[var]
        lenv = defs.copy()
        if (flags.SUBCLASSES_REQUIRE_SUBTYPING and not\
            relations.subtype(lenv, InferBottom, subty.instance(), supty.instance())) or\
                (not flags.SUBCLASSES_REQUIRE_SUBTYPING and\
                 not relations.subcompat(subty.instance(), supty.instance())):
            raise StaticTypeError('Subclass %s is not a subtype in file %s' % (var.var, misc.filename))

def lift(map):
    return {typing.TypeVariable(k):map[k] for k in map}

def exclude_fixed(infers, fixed):
    return {x:infers[x] for x in infers if x not in fixed}
