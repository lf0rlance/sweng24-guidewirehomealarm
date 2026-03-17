import unittest

from db.disarm_codes import _generate_code


class TestDisarmCodes(unittest.TestCase):
    def test_generate_code_length_and_charset(self):
        code = _generate_code(8)
        self.assertEqual(len(code), 8)
        # Should avoid ambiguous characters
        self.assertNotIn("0", code)
        self.assertNotIn("1", code)
        self.assertNotIn("O", code)
        self.assertNotIn("I", code)

