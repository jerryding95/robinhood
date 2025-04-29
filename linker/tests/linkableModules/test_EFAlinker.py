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

    tran0 = state0.writeTransition("eventCarry", state0, state1, "v1_launch")
    tran0 = efa.writeTransition("eventCarry", state0, state1, "v2_launch")
    tran0 = efa.writeEventTransition("eventCarry", state1, "v3_launch")
    tran0 = efa.writeEvent("v4_launch")

    # Create the thread context
    tran0.writeAction("mov_ob2reg X0 X14")
    tran0.writeAction("some_label: mov_reg2reg X1 X2")
    tran0.writeAction("some_label: mov_reg2reg X1 v1_launch")

    efa.appendBlockAction(
        "block_1", "alldone: beq UDPR_9 UDPR_12 alldone"
    )  # check v1 iterator


@efaProgram
def simpleProgram2(efa):
    efa.code_level = "machine"

    state0 = efa.State()  # Initial State?
    efa.add_initId(state0.state_id)
    state1 = efa.State("newState2")  # tri Count State

    tran0 = state0.writeTransition("eventCarry", state0, state1, "v5_launch")
    # Create the thread context
    tran0.writeAction("mov_ob2reg X0 X14")
    tran0.writeAction("some_label: mov_reg2reg X1 X2")
    tran0.writeAction("some_label: mov_reg2reg X1 v1_launch")


    efa.appendBlockAction(
        "block_2", "beq UDPR_9 UDPR_12 v2_launch"
    )  # check v1 iterator


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
        self.assertEqual(res.getSymbol(lm1_name+"_newState").symbolType, SymbolType.STATE)
        self.assertEqual(res.getSymbol(lm2_name+"_newState2").symbolType, SymbolType.STATE)
        self.assertEqual(res.getSymbol("v2_launch").symbolType, SymbolType.TRANSITION)
        self.assertEqual(res.getSymbol("v1_launch").symbolType, SymbolType.TRANSITION)
        self.assertEqual(res.getSymbol("block_1").symbolType, SymbolType.SHARED_BLOCK)
        self.assertEqual(res.getSymbol("block_2").symbolType, SymbolType.SHARED_BLOCK)

if __name__ == "__main__":
    unittest.main()
