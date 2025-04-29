from EFA_v2 import *

def fibonacci_recursion():
    efa = EFA([])
    efa.code_level = 'machine'
    # blksize = 64
    # vsize = str(int(24/8))
    debug = True

    state0 = State() # Initial State
    efa.add_initId(state0.state_id)
    efa.add_state(state0)

    # Add events to dictionary
    event_map = {
        'start_fibonacci': 0,
        'compute_fibonacci': 1,
        'write_result': 2,
    }

    # blkbytes = str(int(blksize))
    # blkwords = str(int(blksize/8))
    

    """
        tran0:
        X8(OB_0): n 
        X9(OB_1): current_n (start: 1)
        X10(OB_2): F(current_n) (start: 1)
        X11(OB_3): F(current_n-1) (start: 0)

        X16(UDPR_0): n
        X17(UDPR_1): current_n + 1
        X18(UDPR_2): F(current_n + 1)
        X19(UDPR_3): F(current_n)
        X20(UDPR_4): 
        X21(UDPR_5): 
        X22(UDPR_6): 
        X23(UDPR_7):
        X24(UDPR_8): 
        X25(UDPR_9): 
        X26(UDPR_10): 
        X27(UDPR_11):
        X28(UDPR_12):
        X29(UDPR_13): 
        X30(UDPR_14):
        X31(UDPR_15):
    """


    tran0 = state0.writeTransition("eventCarry", state0, state0, event_map['start_fibonacci'])
    tran0.writeAction("bnei X8 0 compare")                      # if n == 0
    tran0.writeAction("movir X16 1")                            # status (X16) = 1
    tran0.writeAction("movir X17 0")                            # result (X17) = 0
    tran0.writeAction("addi X7 X18 0")                           # X18 = X7
    tran0.writeAction("movrl X16 0(X18) 0 8")                   # LM(0) = status = 1
    tran0.writeAction("movrl X17 8(X18) 0 8")                   # LM(8) = result = 0
    tran0.writeAction("yieldt")

    tran0.writeAction("compare: bne X8 X9 recursion")           # if X8 (n) == X9 (current_n)
    tran0.writeAction("movir X16 1")                            # status (X16) = 1
    tran0.writeAction("addi X10 X17 0")                          # result (X17) = X10 F(current_n)
    tran0.writeAction("addi X7 X18 0")                           # X18 = X7
    tran0.writeAction("movrl X16 0(X18) 0 8")                   # LM(0) = status = 1
    tran0.writeAction("movrl X17 8(X18) 0 8")                   # LM(8) = result = 1
    tran0.writeAction("yieldt")


    tran0.writeAction("recursion: addi X8 X16 0")                # X16 = X8 = n
    tran0.writeAction("addi X9 X17 1")                          # X17 = X9 + 1 = current_n + 1   
    tran0.writeAction("add X10 X11 X18")                        # X18 = X10 + X11 = F(current_n) + F(current_n - 1) = F(current_n + 1)
    tran0.writeAction("addi X10 X19 0")                          # X19 = X10 = F(current_n)
    tran0.writeAction("evii X20 " + str(event_map['start_fibonacci']) + " " + str(event_map['start_fibonacci']) + " 1")
    tran0.writeAction(f"sendops_wret X20 {event_map['start_fibonacci']} X16 4 X30 X31")             # send to "start_fibonacci" event
    tran0.writeAction("yield")

    return efa
