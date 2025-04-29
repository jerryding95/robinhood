from linker.EFAProgram import efaProgram
from linker.EFAsections.StaticDataSection import staticDataType


@efaProgram
def simpleProgram(self):
    efa = self
    efa.code_level = "machine"

    state0 = efa.State()
    efa.add_initId(state0.state_id)
    state1 = efa.State("newState")

    tran0 = state0.writeTransition("eventCarry", state0, state1, "v1_launch")
    tran0.writeAction(f"{'X'}: print 'Y: Z'")
    tran0.writeAction(f"{'X'}: print 'Y: : : Z'")
    tran0.writeAction(f"{'X'}: print '(Y: Z)'")
    tran0.writeAction(f"{'X'}: print '(Y:' ")



