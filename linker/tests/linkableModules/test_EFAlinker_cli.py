from EFAlinker import EFAlinker
from linker.Symbol.Symbol import SymbolType

import unittest

class testMain(unittest.TestCase):
    def test_efa_program(self):
        linker = EFAlinker("testEFAProgramResult")
        linker.loadFiles(["tests/linkableModules/testInput.py", "tests/linkableModules/testInput2.py"], [])
        lms = linker.getLinkableModules()
        lm1_name = list(filter(lambda x: "simpleProgram_" in x.name, lms))
        print(f"lm1_name: {lm1_name}")
        self.assertEqual(len(lm1_name), 1)
        lm1_name = lm1_name[0].name
        lm2_name = list(filter(lambda x: "simpleProgram2_" in x.name, lms))
        self.assertEqual(len(lm2_name), 1)
        lm2_name = lm2_name[0].name
        self.assertEqual(len(linker._linkableModules), 2)
        res = linker.link()
        self.assertEqual(res.getSymbol(lm1_name+"_newState").symbolType, SymbolType.STATE)
        self.assertEqual(res.getSymbol(lm2_name+"_newState2").symbolType, SymbolType.STATE)
        self.assertEqual(res.getSymbol("v2_launch").symbolType, SymbolType.TRANSITION)
        self.assertEqual(res.getSymbol("v1_launch").symbolType, SymbolType.TRANSITION)
        self.assertEqual(res.getSymbol("block_1").symbolType, SymbolType.SHARED_BLOCK)
        self.assertEqual(res.getSymbol("block_2").symbolType, SymbolType.SHARED_BLOCK)

        linker.dumpPython()
        ## Check if file exists
        import os
        self.assertTrue(os.path.exists("testEFAProgramResult.py"))

        ## Check if file is valid
        import ast
        with open("testEFAProgramResult.py", "r") as f:
            tree = ast.parse(f.read())
            self.assertTrue(tree)

if __name__ == "__main__":
    unittest.main()
