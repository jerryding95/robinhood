from EFA_v2 import *

def dram_tests_CHUNK1():
    return dram_tests(CHUNK_SIZE=1)
def dram_tests_CHUNK2():
    return dram_tests(CHUNK_SIZE=2)
def dram_tests_CHUNK3():
    return dram_tests(CHUNK_SIZE=3)
def dram_tests_CHUNK4():
    return dram_tests(CHUNK_SIZE=4)
def dram_tests_CHUNK5():
    return dram_tests(CHUNK_SIZE=5)
def dram_tests_CHUNK6():
    return dram_tests(CHUNK_SIZE=6)
def dram_tests_CHUNK7():
    return dram_tests(CHUNK_SIZE=7)
def dram_tests_CHUNK8():
    return dram_tests(CHUNK_SIZE=8)

def dram_tests(CHUNK_SIZE=8):
    efa = EFA([])
    efa.code_level = "machine"
    state = State()
    efa.add_initId(state.state_id)
    efa.add_state(state)
    event_map = {
        "launch_work_distributor": 0,
        "child_join": 1,
        f"dram_read_{CHUNK_SIZE}": 2,
        f"dram_read_{CHUNK_SIZE}_return": 3,
        f"dram_write_{CHUNK_SIZE}_ack": 4,
    }
    
    def launch_work_distributor():
    # launch_parent
        tran0 = state.writeTransition("eventCarry", state, state, event_map['launch_work_distributor'])
        SRC = "X16"
        DEST = "X17"
        # INIT_OFFSET = "X17"
        NUM_LANES = "X18"
        NUM_THREADS_PER_LANE = "X19"
        NELEMS_PER_THREAD = "X20"
        TOTAL_THREADS = "X21"
        # INIT_OFFSET = "X16"
        # NUM_LANES = "X17"
        # NUM_THREADS_PER_LANE = "X18"
        
        WIDX = "X22"
        I = "X23"
        
        J = "X24"
        TID = "X24"
        
        EVW = "X25"
        CW = "X26"
        # for the return thread
        RESULT = "X27"
        NTHR = "X28"
        SPPTR = "X29"

        TEMP0 = "X30"
        TEMP1 = "X31"
        
        # INIT_OFFSET = "X29"
        # OB_0 = offset, OB_1 = num_lanes, OB_2 = num_threads_per_lane
        printu(tran0, f"'Start, parent thread forking: lid=%ld' LID")
        # write data in the smp
        tran0.writeAction(f"movir {SPPTR} 0")
        tran0.writeAction(f"add X7 {SPPTR} {SPPTR}")
        for i in range(8):
            tran0.writeAction(f"movrl X{8+i} 8({SPPTR}) 1 8") # starting from the second word, offset by 8 bytes
        
        tran0.writeAction(f"addi X8 {SRC} 0")
        tran0.writeAction(f"addi X9 {DEST} 0")
        tran0.writeAction(f"addi X10 {NUM_LANES} 0")
        tran0.writeAction(f"addi X11 {NUM_THREADS_PER_LANE} 0")
        tran0.writeAction(f"addi X12 {NELEMS_PER_THREAD} 0")
        tran0.writeAction(f"addi X13 {TOTAL_THREADS} 0")
        tran0.writeAction(f"movir {NTHR} 0")
        tran0.writeAction(f"movir {RESULT} 0")
        tran0.writeAction(f"movir {WIDX} 0")
        tran0.writeAction(f"evi X2 {CW} 2 1") # send_reply CW
        # loop over num lanes; then loop over num threads per lane
        tran0.writeAction(f"movir {I} 0")
        tran0.writeAction(f"lane_loop: ble {NUM_LANES} {I} lane_done")
        tran0.writeAction(f"movir {J} 0")
        tran0.writeAction(f"thread_loop: ble {NUM_THREADS_PER_LANE} {J} thread_done")
        # construct the event word and the send the event
        
        tran0.writeAction(f"evi X2 {EVW} {event_map[f'dram_read_{CHUNK_SIZE}']} 1") # parent fork
        tran0.writeAction(f"evi {EVW} {EVW} 255 4") # new thread
        tran0.writeAction(f"ev {EVW} {EVW} {I} {I} 8") # lane id
        # printu(tran0, f"'parent thread forking: lid=%ld' LID")
        # tran0.writeAction(f"sendr {EVW} {CW} {WID} {J} 0")
        tran0.writeAction(f"sendr3_wret {EVW} {event_map['child_join']} {WIDX} {TID} {NELEMS_PER_THREAD} {TEMP0}")
        tran0.writeAction(f"addi {WIDX} {WIDX} 1")
        tran0.writeAction(f"addi {J} {J} 1")
        tran0.writeAction(f"jmp thread_loop")
        tran0.writeAction(f"thread_done: addi {I} {I} 1")
        tran0.writeAction(f"jmp lane_loop")
        tran0.writeAction(f"lane_done: yield")
    
    def child_join():
        tran1 = state.writeTransition("eventCarry", state, state, event_map['child_join'])
        SRC = "X16"
        DEST = "X17"
        NUM_LANES = "X18"
        NUM_THREADS_PER_LANE = "X19"
        NELEMS_PER_THREAD = "X20"
        TOTAL_THREADS = "X21"

        WIDX = "X22"
        I = "X23"
        
        J = "X24"
        TID = "X24"
        
        EVW = "X25"
        CW = "X26"
        
        # for the return thread
        TERM_FLAG = "X27"
        NTHR = "X28"
        SPPTR = "X29"
        
        printu(tran1, f"'Child thread joining: lid=%ld, widx=%ld' LID X8")
        tran1.writeAction(f"addi X8 {WIDX} 0")
        tran1.writeAction(f"addi X10 {TID} 0")
        tran1.writeAction(f"addi {NTHR} {NTHR} 1")
        tran1.writeAction(f"beq {NTHR} {TOTAL_THREADS} done")
        tran1.writeAction(f"yield")
        # write results to SP 0
        tran1.writeAction(f"done: movir {SPPTR} 0")
        # tran2.writeAction(f"print 'results: %ld' {RESULT}")
        tran1.writeAction(f"add X7 {SPPTR} {SPPTR}")
        tran1.writeAction(f"movir {TERM_FLAG} 1")
        tran1.writeAction(f"movrl {TERM_FLAG} 0({SPPTR}) 0 8")
        tran1.writeAction(f"yieldt")
        
    
    def dram_read_CHUNK_SIZE(CHUNK_SIZE=8):
        tran2 = state.writeTransition("eventCarry", state, state, event_map[f'dram_read_{CHUNK_SIZE}'])
        # OB_0 = WIDX, OB_1 = TID, OB_2 = NELEMS_PER_THREAD
        SRC = "X16"
        DEST = "X17"
        NUM_LANES = "X18"
        NUM_THREADS_PER_LANE = "X19"
        NELEMS_PER_THREAD = "X20"
        TOTAL_THREADS = "X21"
        # reserved X22
        # reserved X23
        WOFFSET = "X22"
        
        
        WIDX = "X24"
        NREAD = "X25"
        RPTR = "X26"
        CONTW = "X27"
        STPTR = "X28"
        NSTR = "X29"
        ADDR_DIFF = "X30"
        
        
        SPPTR = "X31"
        TEMP0 = "X31"
        tran2.writeAction(f"addi X8 {WIDX} 0")
        printu(tran2, f"'Read event: lid=%ld, widx=%ld' LID X8")
        # read operands from SP 8
        tran2.writeAction(f"movir {SPPTR} 0")
        tran2.writeAction(f"add X7 {SPPTR} {SPPTR}")
        for i in range(8):
            tran2.writeAction(f"movlr 8({SPPTR}) X{16+i} 1 8")
        # now the operands in place, read the data
        tran2.writeAction(f"movir {NREAD} 0")
        tran2.writeAction(f"movir {NSTR} 0")
        # we need an offset to calculate the correct address
        tran2.writeAction(f"sli {WIDX} {WOFFSET} 3") # WOFFSET = WIDX * NELE * 8
        tran2.writeAction(f"mul {WOFFSET} {NELEMS_PER_THREAD} {WOFFSET}")
        tran2.writeAction(f"add {SRC} {WOFFSET} {SRC}")
        tran2.writeAction(f"add {DEST} {WOFFSET} {DEST}")
    
        tran2.writeAction(f"addi {SRC} {RPTR} 0")
        tran2.writeAction(f"addi {DEST} {STPTR} 0")
        # read loop, all send*_wret, this is just easy, unit test should consider all cases for contw
        tran2.writeAction(f"read_loop: ble {NELEMS_PER_THREAD} {NREAD} read_done")
        # use pseudo instruction here
        tran2.writeAction(f"send_dmlm_ld_wret {RPTR} {event_map[f'dram_read_{CHUNK_SIZE}_return']} {CHUNK_SIZE} {TEMP0}") 
        # alternative real instruction
        # tran2.writeAction(f"sendm {RPTR} {event_map['dram_read_return']} {SPPTR} {CHUNK_SIZE} 2") # mode1=1, mode0=0, contlabel
        tran2.writeAction(f"addi {NREAD} {NREAD} {CHUNK_SIZE}") # increment in words
        tran2.writeAction(f"addi {RPTR} {RPTR} {8 * CHUNK_SIZE}") # address still in bytes
        tran2.writeAction(f"jmp read_loop")
        tran2.writeAction(f"read_done: yield") # yield since it will return to the same thread
    
    
    def dram_read_CHUNK_SIZE_return(CHUNK_SIZE=8):
        SRC = "X16"
        DEST = "X17"
        NUM_LANES = "X18"
        NUM_THREADS_PER_LANE = "X19"
        NELEMS_PER_THREAD = "X20"
        TOTAL_THREADS = "X21"
        # reserved X22
        # reserved X23
        
        
        WIDX = "X24"
        NREAD = "X25"
        RPTR = "X26"
        CONTW = "X27"
        STPTR = "X28"
        NSTR = "X29"
        ADDR_DIFF = "X30"
        
        
        SPPTR = "X31"
        TEMP0 = "X31"
        
        RETURN_ADDR_REG = 'X' + str((CHUNK_SIZE + 8) if CHUNK_SIZE < 8 else 3)
        
        tran = state.writeTransition("eventCarry", state, state, event_map[f'dram_read_{CHUNK_SIZE}_return'])
        printu(tran, f"'Read return event: lid=%ld, widx=%ld' LID {WIDX}")
        printu(tran, f"'reg states: src=%ld, dest=%ld, widx=%ld, stptr=%ld, addr_diff=%ld' {SRC} {DEST} {WIDX} {STPTR} {ADDR_DIFF}")
        tran.writeAction(f"sub {RETURN_ADDR_REG} {SRC} {ADDR_DIFF}")
        tran.writeAction(f"add {DEST} {ADDR_DIFF} {STPTR}")
        # tran.writeAction(f"movir {CONTW} {event_map[f'dram_write_{CHUNK_SIZE}_ack']}") # contw
        tran.writeAction(f"sendops_dmlm_wret {STPTR} {event_map[f'dram_write_{CHUNK_SIZE}_ack']} X8 {CHUNK_SIZE} {TEMP0}") # sendm_wret
        # tran.writeAction(f"sendmops {STPTR} {CONTW} X8 {CHUNK_SIZE} 1")
        tran.writeAction(f"yield")
        
    def dram_write_CHUNK_SIZE_ack(CHUNK_SIZE=8):
        # same thread as dram_write
        SRC = "X16"
        DEST = "X17"
        NUM_LANES = "X18"
        NUM_THREADS_PER_LANE = "X19"
        NELEMS_PER_THREAD = "X20"
        TOTAL_THREADS = "X21"
        # reserved X22
        # reserved X23
        
        
        WIDX = "X24"
        NREAD = "X25"
        RPTR = "X26"

        CONTW = "X27"
        TEMP0 = "X27"

        STPTR = "X28"
        NSTR = "X29"
        ADDR_DIFF = "X30"
        
        
        SPPTR = "X31"
        tran = state.writeTransition("eventCarry", state, state, event_map[f'dram_write_{CHUNK_SIZE}_ack'])
        printu(tran, f"'Write ack event: lid=%ld, widx=%ld' LID {WIDX}")
        tran.writeAction(f"addi {NSTR} {NSTR} {CHUNK_SIZE}")
        tran.writeAction(f"ble {NELEMS_PER_THREAD} {NSTR} write_done")
        tran.writeAction(f"yield")
        tran.writeAction(f"write_done: sendr3_reply {WIDX} {WIDX} {WIDX} {TEMP0}")
        # tran.writeAction(f"write_done: addi {TEMP0} {TEMP0} 0")
        # tran.writeAction(f"sendr_reply {WIDX} {WIDX} {WIDX} {TEMP0}")
        tran.writeAction(f"yieldt")
        
    launch_work_distributor()
    child_join()
    dram_read_CHUNK_SIZE(CHUNK_SIZE=CHUNK_SIZE)
    dram_read_CHUNK_SIZE_return(CHUNK_SIZE=CHUNK_SIZE)
    dram_write_CHUNK_SIZE_ack(CHUNK_SIZE=CHUNK_SIZE)
    return efa
    

def printu(tran, msg):
    return None
    return tran.writeAction(f"print {msg}")