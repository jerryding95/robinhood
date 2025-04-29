from common.helper import (
    UpDownInstructions,
    isRegister,
    isNumericLiteral,
    isSymbol,
    hasTargetLabel,
)
from random import randint

import unittest


class TestStringMethods(unittest.TestCase):
    def test_isRegister(self) -> bool:
        """Test the isRegister function"""
        randRegisterNames = [f"X{i}" for i in range(32)]
        for name in randRegisterNames:
            self.assertTrue(isRegister(name))

    def test_isNumericLiteral(self) -> bool:
        """Test the isNumericLiteral function"""
        randLiterals = [str(randint(-10000, 10000)) for i in range(100)]
        randFloats = [
            str(randint(-10000, 10000) / randint(1, 10000)) for i in range(100)
        ]
        randHex = [hex(randint(-10000, 10000)) for i in range(100)]
        randBin = [bin(randint(-10000, 10000)) for i in range(100)]
        randLiterals.extend(randFloats)
        randLiterals.extend(randHex)
        randLiterals.extend(randBin)

        for literal in randLiterals:
            self.assertTrue(isNumericLiteral(literal)[0])
            self.assertTrue(isNumericLiteral(literal)[1] is not None)

    def test_isSymbol(self) -> bool:
        """Test the isSymbol function"""
        not_labels = ["132132", "1test", "test test"]
        true_labels = [
            "test",
            "test1",
            "test_test",
            "test_test1",
            "test1_1_test",
            "__test__",
        ]

        for label in not_labels:
            self.assertFalse(isSymbol(label))

        for label in true_labels:
            self.assertTrue(isSymbol(label))

    def test_hasTargetLabel(self) -> bool:
        """Test the hasTargetLabel function"""
        tests_true = [
            "test: a b c",
            "test34: abc abc abc",
            "test_test: abc abc abc",
        ]
        tests_false = [
            "test a b c",
            "test34 abc abc abc",
            "test_test abc abc abc",
        ]

        for test in tests_true:
            self.assertTrue(hasTargetLabel(test))

        for test in tests_false:
            self.assertFalse(hasTargetLabel(test))

    def test_instruction(self) -> bool:
        """Dumps all the instructions"""
        for inst in UpDownInstructions:
            print(inst)
        return True


if __name__ == "__main__":
    unittest.main()
