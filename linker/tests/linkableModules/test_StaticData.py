from linker.EFAProgram import efaProgram
from EFAlinker import EFAlinker

from linker.Symbol.Symbol import SymbolType

import unittest


@efaProgram
def simpleProgram(self):
    efa = self
    # Create a static variable address of size 100 bytes
    efa.addStaticData("Variable", 100)


@efaProgram
def simpleProgram2(efa):
    state0 = efa.State()  # Initial State?
    state1 = efa.State("newState2")  # tri Count State

    tran0 = state0.writeTransition("eventCarry", state0, state1, "v2_launch")
    # Create the thread context
    tran0.writeAction("mov_ob2reg X0 X14")
    tran0.writeAction("some_label: mov_reg2reg X1 X2")
    tran0.writeAction("some_label: mov_imm2reg X1 Variable")


class testMain(unittest.TestCase):
    def test_efa_program(self):
        linker = EFAlinker("testEFAProgramResult")
        linker.loadConstants()
        lms = linker.loadSymbols()
        lm1_name = list(filter(lambda x: "simpleProgram_" in x.name, lms))
        self.assertEqual(len(lm1_name), 1)
        lm1_name = lm1_name[0].name
        lm2_name = list(filter(lambda x: "simpleProgram2_" in x.name, lms))
        self.assertEqual(len(lm2_name), 1)
        lm2_name = lm2_name[0].name
        self.assertEqual(len(linker._linkableModules), 2)
        res = linker.link()
        res.dump()


if __name__ == "__main__":
    unittest.main()
