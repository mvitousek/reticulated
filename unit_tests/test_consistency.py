import unittest
import sys

sys.path.insert(0, '..')

from retic.retic_ast import Dyn, Union, Int, Str, Float, List, Function
from retic.consistency import consistent

class TestConsistency(unittest.TestCase):

  def test_consis(self):
      assert consistent(Dyn(), Dyn())
      assert consistent(Float(), Float())
      assert consistent(Union([Int(), Str()]), Union([Str(), Int()]))
      assert consistent(Union([Int(), Str()]), Union([Str(), Str(), Int()]))

      ##TODO: do not want to union with Dyn
      # assert consistent(Union([Function(Int(), Str()), Dyn()]), Union([Function(Dyn(), Dyn()), Dyn()]))

      assert not consistent(Float(), Int())
      assert not consistent(Int(), List(Int))



if __name__ == '__main__':
    unittest.main()