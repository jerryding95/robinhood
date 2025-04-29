from linker.EFAProgram import efaProgram
from EFAlinker import EFAlinker

from linker.Symbol.Symbol import SymbolType

import unittest


@efaProgram
def simpleProgram(self):
    efa = self
    efa.code_level = "machine"

    state0 = efa.State()  # Initial State?
    efa.add_initId(state0.state_id)
    state1 = efa.State("newState")  # tri Count State
    state1.alphabet = [1, 3]


@efaProgram
def simpleProgram2(efa):
    efa.code_level = "machine"

    state0 = efa.State()  # Initial State?
    efa.add_initId(state0.state_id)
    state1 = efa.State("newState2")  # tri Count State
    state1.alphabet = [1, 2, 3]


class testMain(unittest.TestCase):
    def test_efa_program(self):
        linker = EFAlinker("testEFAProgramResult")
        linker.loadConstants([])
        lms = linker.loadSymbols()
        lm1_name = list(filter(lambda x: "simpleProgram_" in x.name, lms))
        self.assertEqual(len(lm1_name), 1)
        lm1_name = lm1_name[0].name
        lm2_name = list(filter(lambda x: "simpleProgram2_" in x.name, lms))
        self.assertEqual(len(lm2_name), 1)
        lm2_name = lm2_name[0].name
        self.assertEqual(len(linker._linkableModules), 2)
        res = linker.link()
        for symbol in res.stateSymbols:
            if symbol.name[-1 * len("newState") :] == "newState":
                self.assertEqual(symbol.section.alphabet, [1, 3])
            elif symbol.name[-1 * len("newState2") :] == "newState2":
                self.assertEqual(symbol.section.alphabet, [1, 2, 3])


if __name__ == "__main__":
    unittest.main()
