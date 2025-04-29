from linker.EFAProgram import efaProgram


@efaProgram
def simpleProgram2(efa):
    efa.code_level = "machine"

    state0 = efa.State()
    efa.add_initId(state0.state_id)
    state1 = efa.State("newState2")

    tran0 = state0.writeTransition("eventCarry", state0, state1, "v5_launch")

    tran0.writeAction("mov_ob2reg X0 X14")
    tran0.writeAction("some_label: mov_reg2reg X1 X2")
    tran0.writeAction("mov_imm2reg X1 variable")
    tran0.writeAction("mov_imm2reg X1 variable2")
    tran0.writeAction("mov_imm2reg X1 variable3")
    tran0.writeAction("mov_imm2reg X1 variable4")
    tran0.writeAction("mov_reg2reg X1 v1_launch")
    tran0.writeAction("TranCarry_goto block_1")

    efa.appendBlockAction("block_2", "beq UDPR_9 UDPR_12 v2_launch")

    efa.linkBlocktoState("block_2", state0)
