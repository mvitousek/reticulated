from retic.opt_transient import *
import unittest


class T(unittest.TestCase):

    def test_t(self):
        self.assertTrue(True)
unittest.main()
print('Own')
t = __retic_check_instance__(__retic_check_instance__(T(), T), T)
print(__retic_check_callable__(t.test_t)())
