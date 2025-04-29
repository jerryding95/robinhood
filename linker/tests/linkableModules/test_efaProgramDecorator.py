from linker.EFAProgram import EFAProgram, efaProgram

import unittest


@efaProgram
def simpleProgram(self):
    return 10

@efaProgram
def simpleProgram2(self):
    return 20


class testEFAdecorator(unittest.TestCase):
    def test_efa_program(self):
        efaClasses = EFAProgram.getEFAclasses()
        self.assertEqual(len(efaClasses), 2)
        res = []
        for efaClass in efaClasses:
            print(f"efaClass: {efaClass.__name__}")
            obj = efaClass(efaClass.__name__)
            programs = efaClass.getEFAPrograms()
            for program in programs:
                print(f"program: {program}")
                method = getattr(obj, program)
                res.append(method())
        self.assertEqual(res, [10, 20])


if __name__ == "__main__":
    unittest.main()
