import unittest
import sys
import ast
from itertools import count
from sympy import *
sys.path.insert(0, '..')
from retic.proposition import *
import ast
from retic import retic_ast, typeparser


class TestProp(unittest.TestCase):

    t_map={}

    loi = retic_ast.List(retic_ast.Int())
    los = retic_ast.List(retic_ast.Str())

    p1 = PrimP('x', retic_ast.Int())
    p2 = PrimP('y', retic_ast.Str())
    p3 = PrimP('x', retic_ast.Int())
    p4 = PrimP('z', retic_ast.Str())
    p5 = PrimP('f', retic_ast.Str())
    p7 = PrimP('x', retic_ast.Bool())
    p8 = PrimP('g', los)
    p9 = PrimP('g', retic_ast.TopList())
    p10 = PrimP('g', loi)


    and_1 = AndProp([p1, p2])
    not_1 = NotProp(p4)
    not_2 = NotProp(p5)
    not_3 = NotProp(p7)
    not_4 = NotProp(p2)
    not_5 = NotProp(p9)
    not_6 = NotProp(p10)
    and_2 = AndProp([not_1, p1])
    and_3 = AndProp([not_1, not_2])
    and_4 = AndProp([not_3, not_4])

    or_1 = OrProp([p1, p7])
    or_2 = OrProp([p2, p4])

    x1, x2, x3, x4= symbols('1 2 3 4')

    def test_and_1(self):
        res, t_map = self.p1.transform_and_reduce(self.t_map)

        self.assert_(res == self.x1)
        p_and1 = AndProp([AndProp([self.p1, self.p1]), self.p2])
        res, t_map = p_and1.transform_and_reduce(t_map)
        self.assert_(res.equals(And(self.x1, self.x2)))


    def test_or_1(self):
        p_or1 = OrProp([OrProp([self.p1, self.p2]), self.p2])
        res, t_map = p_or1.transform_and_reduce(self.t_map)
        self.assert_(res.equals(Or(self.x2, self.x1)))

    def test_all(self):
        p_all = NotProp(AndProp([self.p3, self.p1]))
        res, t_map = p_all.transform_and_reduce(self.t_map)
        self.assert_(res.equals(Not(self.x1)))

    def test_trans_back(self):
        self.assert_(Proposition.transform_back(self.x1, self.t_map) == self.p1)

        self.assert_(Proposition.transform_back(And(self.x1, self.x2), self.t_map) ==
                     AndProp([self.p1, self.p2]))
        self.assert_(Proposition.transform_back(Not(self.x1), self.t_map) == NotProp(self.p1))
        self.assert_(Proposition.transform_back(Or(Not(self.x1), Not(self.x2)), self.t_map) ==
                     OrProp([NotProp(self.p1), NotProp(self.p2)]))

    def test_simplify(self):
        t_map={self.p3:self.x1, self.p1:self.x1}
        p_all = NotProp(AndProp([self.p3, self.p1]))
        self.assert_(p_all.simplify(t_map) == (NotProp(self.p3)))


    def test_transform_prim(self):
        type_env = {}
        rem, new_env = self.p1.transform(type_env, {})
        self.assert_(rem == TrueProp())
        self.assert_(new_env == {'x': retic_ast.Int()})

    def test_transform_not(self):
        type_env = {'z':retic_ast.Str()}
        rem, new_env = self.not_1.transform(type_env, {})
        self.assert_(rem == TrueProp())
        self.assert_(new_env == {})

    def test_transform_not2(self):
        type_env = {'z':retic_ast.Union([retic_ast.Int(), retic_ast.Str()])}
        rem, new_env = self.not_1.transform(type_env, {})
        self.assert_(rem == TrueProp())
        self.assert_(new_env['z'] == retic_ast.Int())

    def test_transform_not3(self):
        type_env = {'z':retic_ast.Union([retic_ast.Int(), retic_ast.Str(), retic_ast.Bool()])}
        rem, new_env = self.not_1.transform(type_env, {})
        self.assert_(rem == TrueProp())
        self.assert_(new_env['z'] == retic_ast.Union([retic_ast.Int(), retic_ast.Bool()]))

    def test_transform_and(self):
        type_env = {'x':retic_ast.Union([retic_ast.Int(), retic_ast.Str()])}
        rem, new_env = self.and_1.transform(type_env, {})
        self.assert_(rem == TrueProp())
        self.assert_(len(new_env) == 2 and new_env['x'] == retic_ast.Int() and new_env['y'] == retic_ast.Str())

    def test_transform_and2(self):
        type_env = {}
        rem, new_env = self.and_2.transform(type_env, {})
        self.assert_(rem == self.not_1)
        self.assert_(new_env == {'x': retic_ast.Int()})

    def test_transform_and3(self):
        type_env = {'z':retic_ast.Union([retic_ast.Int(), retic_ast.Str()]),
                    'f':retic_ast.Union([retic_ast.Int(), retic_ast.Str()])}

        rem, new_env = self.and_3.transform(type_env, {})

        self.assert_(rem == TrueProp())
        self.assert_(new_env['z'] == retic_ast.Int())
        self.assert_(new_env['f'] == retic_ast.Int())


    def test_transform_and4(self):
        type_env = {'x':retic_ast.Union([retic_ast.Bool(), retic_ast.Str()]),
                    'y':retic_ast.Union([retic_ast.Bool(), retic_ast.Str()])}
        rem, new_env = self.and_4.transform(type_env, {})
        self.assert_(new_env['x'] == retic_ast.Str())
        self.assert_(new_env['y'] == retic_ast.Bool())

    def test_transform_or2(self):
        type_env = {}
        rem, new_env = self.or_2.transform(type_env, {})
        self.assert_(rem == self.or_2)
        self.assert_(new_env == {})

    def test_transform_or1(self):
        type_env = {}
        res_env = {"x":retic_ast.Union([retic_ast.Int(), retic_ast.Bool()])}
        rem, new_env = self.or_1.transform(type_env, {})
        self.assert_(rem == TrueProp())
        self.assert_(new_env == res_env)

    def test_transform_true(self):
        type_env = {}
        assert OrProp([TrueProp()]).transform_and_reduce(type_env)


    def test_transform_occ(self):
        type_env = {'g':retic_ast.TopList()}
        rem, new_env = self.p8.transform(type_env, {})
        assert rem == TrueProp()
        assert type_env['g'] == self.los


    def test_transform_lists(self):
        type_env = {'g':retic_ast.Union([self.loi, self.los, retic_ast.Int()])}
        rem, new_env = self.p9.transform(type_env, {})
        assert rem == TrueProp()
        assert type_env['g'] == retic_ast.Union([self.loi, self.los])

    def test_transform_lists2(self):
        type_env = {'g':retic_ast.Union([retic_ast.Int(), self.loi])}
        rem, new_env = self.p9.transform(type_env, {})
        assert rem == TrueProp()
        assert type_env['g'] == self.loi

    def test_transform_not_lists(self):
        type_env = {'g':retic_ast.Union([self.loi, self.los, retic_ast.Int()])}
        rem, new_env = self.not_5.transform(type_env, {})
        assert rem == TrueProp()
        assert new_env['g'] == retic_ast.Int()

    def test_transform_not_lists2(self):
        type_env = {'g':retic_ast.Union([retic_ast.Int(), retic_ast.TopList()])}
        rem, new_env = self.not_6.transform(type_env, {})
        assert rem == TrueProp()
        assert new_env['g'] == retic_ast.Int()

    # #??????????????
    # def test_transform_bot(self):
    #     type_env = {'g':retic_ast.Int()}
    #     rem, new_env = self.p9.transform(type_env, {})
    #     assert rem == TrueProp()
    #     assert new_env['g'] != retic_ast.Bot()


    #??????????????
    def test_transform_bot2(self):
        type_env = {'y':retic_ast.Int()}
        rem, new_env = self.p2.transform(type_env, {})
        assert rem == TrueProp()
        assert new_env['y'] != retic_ast.Bot()


