from linker.EFAProgram import efaProgram
from sht import SHT


@efaProgram
def SHTExampleEFA(efa):
    """
    1. Initialize the SHT
    2. Upon initialization finish, Launch one update operation
    3. Upon update finish, Launch one get operation
    """
    efa.code_level = 'machine'

    state0 = efa.State()
    efa.add_initId(state0.state_id)
    efa.add_state(state0)

    tran_entry_init = state0.writeTransition("eventCarry", state0, state0, "entry_init")
    tran_init_ret = state0.writeTransition("eventCarry", state0, state0, "init_ret")
    tran_update_ret = state0.writeTransition("eventCarry", state0, state0, "update_ret")
    tran_get_ret = state0.writeTransition("eventCarry", state0, state0, "get_ret")

    # Code injection
    # SHT.setup(state0, debug=False)
    SHT.setup(state0, debug=True)

    INIT_NUM_OPS = 8

    REG_SHT_DESC_LM_OFFSET = 'X16'
    REG_LM_BUF_OFFSET = 'X17'
    REG_TMP0 = 'X18'
    REG_TMP1 = 'X19'
    REG_TMP2 = 'X21'
    REG_LM_BUF_ADDR = 'X20'

    # TRAN - ENTRY init
    ENTRY_OB_SHT_DESC_LM_OFFSET = 'X8'
    ENTRY_OB_SHT_LM_BUF_OFFSET = 'X9'

    tran_entry_init.writeAction(f"print '[NWID %d] => ENTRY SHT init: X8 = %d, X9 = %d' {'X0'} {'X8'} {'X9'}")
    tran_entry_init.writeAction(f"perflog 1 0 'init started, nwid = %d' {'X0'}")
    tran_entry_init.writeAction(f"mov_reg2reg {ENTRY_OB_SHT_DESC_LM_OFFSET} {REG_SHT_DESC_LM_OFFSET}")  # save SHT descriptor LM addr
    tran_entry_init.writeAction(f"mov_imm2reg {REG_TMP0} {INIT_NUM_OPS}")  # REG_TMP0 = number of operands needed by SHT init call
    tran_entry_init.writeAction(f"mov_reg2reg {ENTRY_OB_SHT_LM_BUF_OFFSET} {REG_LM_BUF_OFFSET}")  # 64 Bytes LM send buffer address
    tran_entry_init.writeAction(f"add {ENTRY_OB_SHT_LM_BUF_OFFSET} {'X7'} {REG_LM_BUF_ADDR}")  # 64 Bytes LM send buffer address
    tran_entry_init.writeAction(f"bcopy_ops {'X8'} {REG_LM_BUF_ADDR} {REG_TMP0}")  # copy the operands to LM buffer for calling SHT init
    SHT.initialize(tran=tran_entry_init,
                   ret=tran_init_ret.getLabel(),
                   tmp_reg0=REG_TMP0,
                   tmp_reg1=REG_TMP2,
                   arg_lm_addr_reg=REG_LM_BUF_ADDR)  # call SHT init
    tran_entry_init.writeAction("yield")

    # TRAN - init return
    tran_init_ret.writeAction(f"print '[NWID %d] => SHT init return: X8 = %d, X9 = %d' {'X0'} {'X8'} {'X9'}")
    tran_init_ret.writeAction(f"move {REG_SHT_DESC_LM_OFFSET} {0}({REG_LM_BUF_ADDR}) 0 8")  # SHT_DESC_LM_ADDR
    tran_init_ret.writeAction(f"move {REG_LM_BUF_OFFSET} {8}({REG_LM_BUF_ADDR}) 0 8")  # TMP_BUF_LM_ADDR
    tran_init_ret.writeAction(f"mov_imm2reg {REG_TMP0} {123}")
    tran_init_ret.writeAction(f"move {REG_TMP0} {16}({REG_LM_BUF_ADDR}) 0 8")  # KEY
    tran_init_ret.writeAction(f"move {REG_TMP0} {24}({REG_LM_BUF_ADDR}) 0 8")  # VAL
    tran_init_ret.writeAction(f"print '[NWID %d] => launching SHT update' {'X0'}")
    SHT.update(tran=tran_init_ret,
               ret=tran_update_ret.getLabel(),
               tmp_reg0=REG_TMP1,
               tmp_reg1=REG_TMP2,
               arg_lm_addr_reg=REG_LM_BUF_ADDR)
    tran_init_ret.writeAction("yield")

    # TRAN - update return
    tran_update_ret.writeAction(f"print '[NWID %d] => SHT update return: X8 = %d, X9 = %d' {'X0'} {'X8'} {'X9'}")
    tran_update_ret.writeAction(f"mov_imm2reg {REG_TMP0} {123}")  # KEY
    tran_update_ret.writeAction(f"print '[NWID %d] => launching SHT get' {'X0'}")
    SHT.get(tran=tran_update_ret,
            ret=tran_get_ret.getLabel(),
            tmp_reg0=REG_TMP1,
            tmp_reg1=REG_TMP2,
            desc_lm_offset_reg=REG_SHT_DESC_LM_OFFSET,
            key_reg=REG_TMP0)
    tran_update_ret.writeAction("yield")

    # TRAN - get return
    tran_get_ret.writeAction(f"print '[NWID %d] => SHT get return: X8 = %d, X9 = %d' {'X0'} {'X8'} {'X9'}")
    tran_get_ret.writeAction(f"print '[NWID %d] => signaling TOP & terminating...' {'X0'}")
    tran_get_ret.writeAction(f"mov_imm2reg {REG_TMP0} {1}")
    tran_get_ret.writeAction(f"move {REG_TMP0} {0}({'X7'}) 0 8")  # write 1 as termination flag
    tran_get_ret.writeAction("yield_terminate")

    return efa

