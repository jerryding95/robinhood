from EFA_v2 import *
enable_debug = True
def multilevel_fork_join():
    efa = EFA([])
    efa.code_level = "machine"
    state = State()
    efa.add_initId(state.state_id)
    efa.add_state(state)
    event_map = {
        "fork": 0,
        "join": 1,
        "task": 2,
    }
    
    tran0 = state.writeTransition("eventCarry", state, state, event_map['fork'])
    # OB_0 = LOG2_NUM_FORKS, OB_1 = LEVEL, OB_2 = NUM_DEVICES, OB_3 = RANDOM_NUM
    LOG2_NUM_FORKS = "X16"
    LEVEL = "X17"
    NUM_DEVICES = "X18"
    RANDOM_NUM = "X19"
    MAX_LEVEL = "X27"
    
    NUM_FORKS = "X20"
    I = "X21"
    TNWID = "X22"
    TEMP = "X23"
    SPPTR = "X24"
    RESULT = "X25"
    NUM_JOIN = "X26"

    TEMP0 = "X31"
    TEMP1 = "X30"
    
    
    # do the fork of first level, check if the level is 0
    tran0.writeAction(f"addi X8 {LOG2_NUM_FORKS} 0")
    tran0.writeAction(f"addi X9 {LEVEL} 0")
    tran0.writeAction(f"addi X10 {NUM_DEVICES} 0")
    tran0.writeAction(f"addi X11 {RANDOM_NUM} 0")
    tran0.writeAction(f"addi X12 {MAX_LEVEL} 0")
    
    tran0.writeAction(f"movir {RESULT} 0")
    tran0.writeAction(f"movir {NUM_JOIN} 0")
    printu(tran0, f"'==========================LEVEL %ld=========================' {LEVEL}")
    printu(tran0, f"'Start, parent thread forking: lid=%ld, LOG2_NUM_FORKS=%ld, LEVEL=%ld, NUM_DEVICES=%ld, RANDOM_NUM=%ld' LID {LOG2_NUM_FORKS} {LEVEL} {NUM_DEVICES} {RANDOM_NUM}")
    tran0.writeAction(f"beqi {LEVEL} 0 do_task")
    # write values to the spm for further send instruction
    tran0.writeAction(f"movir {SPPTR} 8") # reset the spm ptr
    tran0.writeAction(f"add X7 {SPPTR} {SPPTR}") # SPTR = base(X7)
    tran0.writeAction(f"movrl {LOG2_NUM_FORKS} 0({SPPTR}) 0 8") # write log2_num_forks, starting by offset=8
    tran0.writeAction(f"subi {LEVEL} {TEMP} 1") # temp = level - 1
    tran0.writeAction(f"movrl {TEMP} 8({SPPTR}) 0 8") # write level, starting by offset=16
    tran0.writeAction(f"movrl {NUM_DEVICES} 16({SPPTR}) 0 8") # write num_devices, starting by offset=24
    tran0.writeAction(f"movrl {RANDOM_NUM} 24({SPPTR}) 0 8") # write random_num, starting by offset=32 
    tran0.writeAction(f"movrl {MAX_LEVEL} 32({SPPTR}) 0 8") # write max_level, starting by offset=40
    
    # fork; num_forks this level = 1 << log2_num_forks; tnwid = LID + 1 << log2_num_forks * (level - 1)
    tran0.writeAction(f"movir {NUM_FORKS} 1")
    tran0.writeAction(f"sl {NUM_FORKS} {LOG2_NUM_FORKS} {NUM_FORKS}")
    printu(tran0, f"'NUM_FORKS = %ld, LOG2=%ld' {NUM_FORKS} {LOG2_NUM_FORKS}")
    # loop over num_forks and send the event
    tran0.writeAction(f"movir {I} 0")
    tran0.writeAction(f"fork_loop: ble {NUM_FORKS} {I} fork_done")
    # first get the tnwid = LID + 1 << log2_num_forks << (level - 1)
    tran0.writeAction(f"movir {TNWID} 1")
    tran0.writeAction(f"subi {LEVEL} {TEMP} 1") # temp = level - 1
    tran0.writeAction(f"mul {LOG2_NUM_FORKS} {TEMP} {TEMP}") # temp = log2_num_forks * (level - 1)
    tran0.writeAction(f"sl {I} {TEMP} {TNWID}") # tnwid = 1 << temp
    tran0.writeAction(f"add {TNWID} NWID {TNWID}") # tnwid = tnwid + LID(NWID?)
    tran0.writeAction(f"mod {TNWID} {NUM_DEVICES} {TNWID}") # tnwid = tnwid % num_devices
    # contruct the event word and send the event, write the data to the spm
    tran0.writeAction(f"evi X2 {TEMP} {event_map['fork']} 1") # label = fork
    tran0.writeAction(f"evi {TEMP} {TEMP} 255 4") # new thread
    tran0.writeAction(f"ev {TEMP} {TEMP} {TNWID} {TNWID} 8") # lane id
    printu(tran0, f"'Forking: lid=%ld, TNWID=%ld, LOG2_NUM_FORKS=%ld, I=%ld, NUM_FORKS=%ld' LID {TNWID} {LOG2_NUM_FORKS} {I} {NUM_FORKS}")
    tran0.writeAction(f"send_wret {TEMP} {event_map['join']} {SPPTR} 5 {TEMP0} {TEMP1}") # send the event with return
    tran0.writeAction(f"addi {I} {I} 1")
    tran0.writeAction(f"jmp fork_loop")
    tran0.writeAction(f"fork_done: yield")
    
    tran0.writeAction(f"do_task: movir {SPPTR} 8") # reset the spm ptr = 8
    tran0.writeAction(f"add X7 {SPPTR} {SPPTR}") # SPTR = base(X7) + 8
    # do some arithmetics on the random number, then save to the spm, send_reply back reading that number
    tran0.writeAction(f"movrl {RANDOM_NUM} 0({SPPTR}) 0 8") # write random_num, starting by offset=8
    tran0.writeAction(f"evi X2 {TEMP} {event_map['task']} 1") # label = task
    tran0.writeAction(f"evi {TEMP} {TEMP} 255 4") # new thread
    tran0.writeAction(f"movir {NUM_FORKS} 1") # only expect one reply
    tran0.writeAction(f"send_wret {TEMP} {event_map['join']} {SPPTR} 1 {TEMP0} {TEMP1}") # send this random number to task event
    tran0.writeAction(f"yield")
    
    tran1 = state.writeTransition("eventCarry", state, state, event_map['join'])
    # OB_0 = RESULT or RANDOM_NUM
    LEVEL = "X17"
    NUM_FORKS = "X20"
    RESULT = "X25"
    NUM_JOIN = "X26"
    MAX_LEVEL = "X27"
    TEMP0 = "X31"
    TEMP1 = "X30"
    tran1.writeAction(f"add X8 {RESULT} {RESULT}")
    tran1.writeAction(f"addi {NUM_JOIN} {NUM_JOIN} 1")
    printu(tran1, f"'Joining: Level=%ld, lid=%ld, RESULT=%ld, NUM_JOIN=%ld' {LEVEL} LID {RESULT} {NUM_JOIN}")
    tran1.writeAction(f"beq {NUM_JOIN} {NUM_FORKS} done")
    tran1.writeAction(f"yield")
    tran1.writeAction(f"done: movir {SPPTR} 8")
    tran1.writeAction(f"add X7 {SPPTR} {SPPTR}")
    tran1.writeAction(f"movrl {RESULT} 0({SPPTR}) 0 8")
    printu(tran1, f"'LEVEL=%ld, NUM_JOIN=%ld, NUM_FORKS=%ld' {LEVEL} {NUM_JOIN} {NUM_FORKS}")
    tran1.writeAction(f"beq {LEVEL} {MAX_LEVEL} terminate")
    printu(tran1, f"'Done, result = %ld' {RESULT}")
    tran1.writeAction(f"send_reply {SPPTR} 1 {TEMP0}")
    tran1.writeAction(f"yieldt")
    tran1.writeAction(f"terminate: print 'Root Done, result = %ld' {RESULT}")
    tran1.writeAction(f"movir {SPPTR} 0")
    tran1.writeAction(f"add X7 {SPPTR} {SPPTR}")
    tran1.writeAction(f"movir {TEMP} 1")
    tran1.writeAction(f"movrl {RESULT} 0({SPPTR}) 0 8")
    tran1.writeAction(f"yieldt")
    
    
    
    tran2 = state.writeTransition("eventCarry", state, state, event_map['task'])
    # OB_0 = RADOM_NUM
    V = "X28"
    V0 = "X29"
    TEMP0 = "X31"
    TEMP1 = "X30"
    tran2.writeAction(f"movir {SPPTR} 8") # reset the spm ptr = 8
    tran2.writeAction(f"add X7 {SPPTR} {SPPTR}")
    tran2.writeAction(f"addi X8 {V} 0")
    printu(tran2, f"'Task: lid=%ld, V=%ld' LID {V}")
    tran2.writeAction(f"addi {V} {V} 127")
    tran2.writeAction(f"subi {V} {V} 64")
    tran2.writeAction(f"muli {V} {V} 3")
    tran2.writeAction(f"divi {V} {V} 3")
    tran2.writeAction(f"addi {V} {V0} 0")
    tran2.writeAction(f"add {V} {V} {V}")
    tran2.writeAction(f"add {V} {V} {V}")
    tran2.writeAction(f"add {V} {V} {V}")
    tran2.writeAction(f"sub {V} {V0} {V}")
    tran2.writeAction(f"movrl {V} 0({SPPTR}) 0 8") # write random_num, starting by offset=8
    printu(tran2, f"'Task Done, result = %ld' {V}")
    tran2.writeAction(f"send_reply {SPPTR} 1 {TEMP0}")
    tran2.writeAction(f"yieldt")
    
    return efa

def printu(tran, msg):
    if enable_debug:
        tran.writeAction(f"print {msg}")
    else:
        return None
    # return tran.writeAction(f"print {msg}")