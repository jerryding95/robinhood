from linker.EFAProgram import efaProgram
from linker.EFAsections.StaticDataSection import staticDataType


@efaProgram
def simpleProgram(self):
    efa = self
    efa.code_level = "machine"

    efa.addStaticData("variable", 100)
    efa.addStaticData("variable2", 100, staticDataType.DRAM_SHARED)
    efa.addStaticData("variable3", 100, staticDataType.LANE_PRIVATE)
    efa.addStaticData("variable4", 100, staticDataType.UPDOWN_PRIVATE)

    state0 = efa.State()
    efa.add_initId(state0.state_id)
    state1 = efa.State("newState")

    tran0 = state0.writeTransition("eventCarry", state0, state1, "v1_launch")
    tran0 = efa.writeTransition("eventCarry", state0, state1, "v2_launch")
    tran0 = efa.writeEventTransition("eventCarry", state1, "v3_launch")
    tran0 = efa.writeEvent("v4_launch")

    tran0.writeAction("mov_ob2reg X0 X14")
    tran0.writeAction("some_label: mov_reg2reg X1 X2")
    tran0.writeAction("mov_reg2reg X1 v1_launch")
    tran0.writeAction("TranCarry_goto block_2")

    efa.appendBlockAction("block_1", "beq UDPR_9 UDPR_12 alldone")
    efa.appendBlockAction("block_1", "alldone: mov_reg2ob X0 X14")

    efa.linkBlocktoState("block_1", state0)
