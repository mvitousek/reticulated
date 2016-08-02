import unittest

class T(unittest.TestCase):
    def test_t(self):
        self.assertTrue(True)

unittest.main()

print('Own')
t = T()
print(t.test_t())
