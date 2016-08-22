import unittest
import sys
import ast

sys.path.insert(0, '..')

from retic.retic_ast import Dyn, Union, Int, Str, Float, List, Function, PosAT, Bool
from retic.consistency import consistent, param_consistent, assignable, param_assignable

class TestConsistency(unittest.TestCase):

    def test_consis(self):
        assert consistent(Dyn(), Dyn())
        assert consistent(Float(), Float())
        assert consistent(Union([Int(), Str()]), Union([Str(), Int()]))

        assert consistent(Union([Int(), Str()]), Union([Str(), Str(), Int()]))
        assert param_consistent(PosAT([Union([Int(), Str()])]), PosAT([Union([Str(), Int()])]))

        assert not param_consistent(PosAT([Int(), Int()]), PosAT([Int(), Float()]))
        assert not consistent(Float(), Int())
        assert not consistent(Int(), List(Int))

    def test_assign(self):
        assert assignable(Int(), Int())
        assert assignable(Float(), Int())
        assert assignable(Union([Float(), Float()]), Dyn())
        assert assignable(Union([Float(), Float()]), Int())
        assert assignable(Float(), Bool())
        assert assignable(Union([Float(), Str()]), Float())


        assert not assignable(Union([Float(), Str()]), Union([Str(), Int()]))
        assert not assignable(Union([Int(), Str()]), Union([Str(), Float()]))
        assert not assignable(Union([Float(), Int()]), Str())
        assert not assignable(Int(), Float())




if __name__ == '__main__':
    unittest.main()