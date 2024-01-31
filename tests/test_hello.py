import unittest

class HelloTestCase(unittest.TestCase):
    def setUp(self):
        # Setup any necessary data or state before each test
        pass

    def test_addition(self):
        self.assertEqual(1+2, 3)

    def tearDown(self):
        # Tear down any temporary data or state after each test
        pass
