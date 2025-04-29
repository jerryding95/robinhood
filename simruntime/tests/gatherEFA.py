from EFA import *

def structArray():
    efa = EFA([])
    efa.code_level = 'machine'
    
    state0 = State() #Initial State
    efa.add_initId(state0.state_id)
    efa.add_state(state0)

    #Add events to dictionary 
    event_map = {
        'gather':0,
        'read_return':1,
    }

    tran0 = state0.writeTransition("eventCarry", state0, state0, event_map['gather'])
    tran0.writeAction("mov_ob2ear OB_0_1 EAR_0")                        #0 DRAM src addr
    tran0.writeAction("mov_ob2reg OB_2 UDPR_2")                         #2 Initial offset to memory
    tran0.writeAction("mov_ob2reg OB_4 UDPR_4")                         #4 Number of elements to fetch
    tran0.writeAction("mov_imm2reg UDPR_5 0")                           # Initialize loop counter

    tran0.writeAction("send_loop: ble UDPR_4 UDPR_5 reads_done")                       # Loop comparison
    tran0.writeAction(f"send_dmlm_ld_wret UDPR_2 {event_map['read_return']} 4 0")      # Read 4 bytes from EAR_0 plus UDPR_2 offset
    tran0.writeAction("add OB_3 UDPR_2 UDPR_2")                                         # Increment offset by distance between elements
    tran0.writeAction("addi UDPR_5 UDPR_5 1")                                          # Increment iteration variable
    tran0.writeAction("jmp send_loop")                                                 # Back to beginning of loop
    tran0.writeAction("reads_done: mov_imm2reg UDPR_5 0")                              # Reset iteration variable for when reads come back
    tran0.writeAction("lshift_add_imm LID UDPR_6 16 4")                                # Set memory location to store elements in SPmemory. Skip first element, it is a flag
    tran0.writeAction("yield 5")                                                       # Yield and consume 5 elements from the Operand buffer

    tran1 = state0.writeTransition("eventCarry", state0, state0, event_map['read_return'])
    
    tran1.writeAction("mov_reg2lm OB_0 UDPR_6 4")                       # Store value to local memory
    tran1.writeAction("addi UDPR_5 UDPR_5 1")                           # Increment read counter
    tran1.writeAction("addi UDPR_6 UDPR_6 4")                           # Increment local memory pointer
    tran1.writeAction("bge UDPR_5 UDPR_4 reads_done")                   # Check if we are done receiving elements
    tran1.writeAction("yield 1")                                        # We have not finished. Yield for next event
    tran1.writeAction("reads_done: lshift_add_imm LID UDPR_1 16 0")     # We are finished, set pointer to beginning of local memory
    tran1.writeAction("mov_imm2reg UDPR_2 1")                           # Set register to 1
    tran1.writeAction("mov_reg2lm UDPR_2 UDPR_1 4")                     # Set flag to 1
    tran1.writeAction("yield_terminate 1")                              # Terminate event

    return efa