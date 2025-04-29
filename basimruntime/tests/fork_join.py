from EFA_v2 import *

def fork_join():
    efa = EFA([])
    efa.code_level = "machine"
    state = State()
    efa.add_initId(state.state_id)
    efa.add_state(state)
    event_map = {
        "launch_parent": 0,
        "forked_child": 1,
        "child_join": 2,
    }
    
    # launch_parent
    tran0 = state.writeTransition("eventCarry", state, state, event_map['launch_parent'])
    INIT_OFFSET = "X16"
    NUM_LANES = "X17"
    NUM_THREADS_PER_LANE = "X18"
    
    WID = "X19"
    I = "X20"
    J = "X21"
    EVW = "X22"
    CW = "X23"
    RESULT = "X24"
    TOTAL_THREADS = "X25"
    NTHR = "X26"
    XTEMP0 = "X27"
    XTEMP1 = "X28"
    # OB_0 = offset, OB_1 = num_lanes, OB_2 = num_threads_per_lane
    # printu(tran0, f"'Start, parent thread forking: lid=%ld' LID")
    tran0.writeAction(f"addi X8 {INIT_OFFSET} 0")
    tran0.writeAction(f"addi X9 {NUM_LANES} 0")
    tran0.writeAction(f"addi X10 {NUM_THREADS_PER_LANE} 0")
    tran0.writeAction(f"addi X11 {TOTAL_THREADS} 0")
    tran0.writeAction(f"movir {NTHR} 0")
    tran0.writeAction(f"movir {RESULT} 0")
    tran0.writeAction(f"movir {WID} 0")
    tran0.writeAction(f"evi X2 {CW} 2 1") # send_reply CW
    # loop over num lanes; then loop over num threads per lane
    tran0.writeAction(f"movir {I} 0")
    tran0.writeAction(f"lane_loop: ble {NUM_LANES} {I} lane_done")
    tran0.writeAction(f"movir {J} 0")
    tran0.writeAction(f"thread_loop: ble {NUM_THREADS_PER_LANE} {J} thread_done")
    # construct the event word and the send the event
    
    tran0.writeAction(f"evi X2 {EVW} {event_map['forked_child']} 1") # parent fork
    tran0.writeAction(f"evi {EVW} {EVW} 255 4") # new thread
    tran0.writeAction(f"ev {EVW} {EVW} {I} {I} 8") # lane id
    
    # tran0.writeAction(f"sendr {EVW} {CW} {WID} {J} 0")
    tran0.writeAction(f"sendr3_wret {EVW} {event_map['child_join']} {WID} {J} {INIT_OFFSET} {XTEMP0} {XTEMP1}")
    tran0.writeAction(f"addi {WID} {WID} 1")
    tran0.writeAction(f"addi {J} {J} 1")
    tran0.writeAction(f"jmp thread_loop")
    tran0.writeAction(f"thread_done: addi {I} {I} 1")
    tran0.writeAction(f"jmp lane_loop")
    tran0.writeAction(f"lane_done: yield")
    
    tran1 = state.writeTransition("eventCarry", state, state, event_map['forked_child'])
    # OB_0 WID, OB_1 = INIT_OFFSET
    SPPTR = "X16"
    OFFSET = "X17"
    V = "X18"
    WID = "X19"
    TID = "X20"
    V0 = "X21"
    XTEMP0 = "X31"
    tran1.writeAction(f"addi X8 {WID} 0")
    tran1.writeAction(f"addi X9 {TID} 0")
    # printu(tran1, f"'Start, child thread:lid=%ld wid=%ld tid=%ld' LID {WID} {TID}")
    # get the ptr for the SP
    tran1.writeAction(f"movir {SPPTR} 8") # init_offset = 8
    tran1.writeAction(f"sli {TID} {OFFSET} 3") # offset = tid << 3
    tran1.writeAction(f"add X7 {OFFSET} {SPPTR}") # SPTR = init_offset + offset
    tran1.writeAction(f"movlr 8({SPPTR}) {V} 0 8") # read the value from SPTR, first is used for flag
    # arithmetics, v = (v + 127 - 64) * 3 / 3 + v + v + v - v
    tran1.writeAction(f"addi {V} {V} 127")
    tran1.writeAction(f"subi {V} {V} 64")
    tran1.writeAction(f"muli {V} {V} 3")
    tran1.writeAction(f"divi {V} {V} 3")
    tran1.writeAction(f"addi {V} {V0} 0")
    tran1.writeAction(f"add {V} {V} {V}")
    tran1.writeAction(f"add {V} {V} {V}")
    tran1.writeAction(f"add {V} {V} {V}")
    tran1.writeAction(f"sub {V} {V0} {V}")
    tran1.writeAction(f"sendr3_reply {WID} {V} {TID} {XTEMP0}")
    tran1.writeAction(f"yieldt")
    
    tran2 = state.writeTransition("eventCarry", state, state, event_map['child_join'])
    # OB_0 = WID, OB_1 = V, OB_2 = TID
    SPPTR = "X16"
    RESULT = "X24"
    TOTAL_THREADS = "X25" # from t0
    
    NTHR = "X26"
    WID = "X19"
    V = "X20"
    TID = "X21"
    
  
    
    tran2.writeAction(f"addi X8 {WID} 0")
    tran2.writeAction(f"addi X9 {V} 0")
    tran2.writeAction(f"addi X10 {TID} 0")
   
    tran2.writeAction(f"add {RESULT} {V} {RESULT}")
    tran2.writeAction(f"addi {NTHR} {NTHR} 1")
    tran2.writeAction(f"beq {NTHR} {TOTAL_THREADS} done")
    tran2.writeAction(f"yield")
    # write results to SP 0
    tran2.writeAction(f"done: movir {SPPTR} 0")
    # tran2.writeAction(f"print 'results: %ld' {RESULT}")
    tran2.writeAction(f"add X7 {SPPTR} {SPPTR}")
    tran2.writeAction(f"movrl {RESULT} 0({SPPTR}) 0 8")
    # printu(tran2, f"'Done, result = %ld' {RESULT}")
    tran2.writeAction(f"yieldt")
    return efa
    
# def printu(tran, msg):
#     return None
#     return tran.writeAction(f"print {msg}")