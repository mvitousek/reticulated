import unittest
import sys
import ast
from itertools import count
from sympy import *
sys.path.insert(0, '..')
from retic.proposition import *

def myGen(n):
    yield n
    yield n + 1

class TestTransformReduce(unittest.TestCase):
    p1 = Prim_P('x', int)
    p2 = Prim_P('y', str)
    p3 = Prim_P('x', int)

    x1, x2, x3, x4 = symbols('0 1 2 3')

    def test_and_1(self):

        g = count(start=0, step=1)
        p_and1 = AndProp([AndProp([self.p1, self.p2]), self.p2])
        res = p_and1.transform_and_reduce(next, g)
        self.assert_(res[0].equals(And(self.x1, self.x2, self.x3)))

    def test_or_1(self):
        g = count(start=0, step=1)
        p_or1 = OrProp([OrProp([self.p1, self.p2]), self.p2])
        res = p_or1.transform_and_reduce(next, g)
        self.assert_(res[0].equals(Or(self.x1, self.x2, self.x3)))


    def test_all(self):
        g = count(start=0, step=1)
        p_all = NotProp(AndProp([self.p3, self.p1]))
        print(p_all.transform_and_reduce(next, g))

    def test_all2(self):
        p_all = NotProp(AndProp([OrProp([self.p1, self.p2]), self.p3]))
        res = p_all.transform_and_reduce(None)
        print(res)

