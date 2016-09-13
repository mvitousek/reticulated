import unittest
import sys
import ast
from itertools import count
from sympy import *
sys.path.insert(0, '..')
from retic.proposition import *

# Creating our own generator
# instead of using uuid.uuid3()
# in order to be able to test the
# generated symbols
#
# However all generated symbols in this
# test suite are unique. So we do not
# test different instances of a
# proposition class being equal using
# that transformer.


def myGen(n):
    yield n
    yield n + 1

class TestTransformReduce(unittest.TestCase):
    p1 = Prim_P('x', int)
    p2 = Prim_P('y', str)
    p3 = Prim_P('x', int)

    x1, x2, x3 = symbols('0 1 2')

    def test_and_1(self):

        g = count(start=0, step=1)
        p_and1 = AndProp([AndProp([self.p1, self.p2]), self.p2])
        res = p_and1.transform_and_reduce(next, g)
        self.assert_(res[0].equals(And(self.x1, self.x2, self.x3)))

    def test_or_1(self):
        g = count(start=0, step=1)
        p_or1 = OrProp([OrProp([self.p1, self.p2]), self.p2])
        res = p_or1.transform_and_reduce(next, g)
        self.assert_(res[0].equals(Or(self.x2, self.x3, self.x1)))


    def test_all(self):
        p_all = NotProp(AndProp([self.p3, self.p1]))
        res = p_all.transform_and_reduce(None)
        assert len(res[1]) == 1

