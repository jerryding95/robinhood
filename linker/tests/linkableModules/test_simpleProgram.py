from linker.EFAProgram import EFAProgram

import unittest


class testEFAProgram(EFAProgram):
    def __init__(self):
        super().__init__("testEFAProgram")

    def simpleProgram(self):
        efa = self
        efa.code_level = "machine"

        state0 = efa.State()  # Initial State?
        state1 = efa.State("newState")  # tri Count State

        tran0 = state0.writeTransition("eventCarry", state0, state1, "v1_launch")
        # Create the thread context
        tran0.writeAction("mov_ob2reg X0 X14")
        tran0.writeAction("some_label: mov_reg2reg X1 X2")

        efa.appendBlockAction(
            "block_1", "beq UDPR_9 UDPR_12 alldone"
        )  # check v1 iterator


class testMain(unittest.TestCase):
    def test_efa_program(self):
        efa = testEFAProgram()
        self.assertEqual(efa.name, "testEFAProgram")
        self.assertEqual(efa.code_level, "machine")
        efa.dump()


if __name__ == "__main__":
    unittest.main()
