from EFA import *

def t2u_signal():
    """
    This program spin waits on a memory location in the
    scratchpad memory waiting for the top to send a 99. 
    Once the top sends 99, another memory location in the 
    scratchpad is set to 0. This helps test that the updown
    emulator can return the control flow to the top program,
    even when there are events left to execute. 
    
    This is a terrible idea for a real program. Events are a
    much better way to make the updown wait. This is just for
    testing purposes. If you want to create a signal from top
    to updown, just create an event.
    
    @rtype: EFA()
    @return: Returns the EFA handler with the UpDown program
    """
    efa = EFA([])
    efa.code_level = 'machine'
    
    state0 = State() #Initial State
    efa.add_initId(state0.state_id)
    efa.add_state(state0)

    #Add events to dictionary 
    event_map = {
        'start':0,
        'spinwait':1,
        'noreach':2
    }

    tran0 = state0.writeTransition("eventCarry", state0, state0, event_map['start'])
    tran0.writeAction("mov_imm2reg UDPR_5 0")                           # Initialize loop counter

    tran0.writeAction("mov_imm2reg UDPR_12 0")                                  # Tmp var for 0
    tran0.writeAction(f"ev_update_1 EQT UDPR_11 {event_map['spinwait']} 1")     # Change the event
    tran0.writeAction(f"send4_wret UDPR_11 LID {event_map['noreach']} UDPR_12") # Send the event to the same lane

    tran0.writeAction("yield 1")

    tran1 = state0.writeTransition("eventCarry", state0, state0, event_map['spinwait'])
    tran1.writeAction("addi UDPR_5 UDPR_5 1")                           # Increment loop
    tran1.writeAction("lshift_add_imm LID UDPR_1 16 4")                 # Set address to local memory
    tran1.writeAction("mov_lm2reg UDPR_1 UDPR_2 4")                     # Read location to see if it has the 99 value
    tran1.writeAction("mov_imm2reg UDPR_3 99")                          # Set register to 99
    tran1.writeAction("beq UDPR_3 UDPR_1 wait_done")                    # Check if the value is 99
    tran1.writeAction(f"send4_wret UDPR_11 LID {event_map['noreach']} UDPR_12") # Send the event to the same lane
    tran1.writeAction('yield 1')
    tran1.writeAction("wait_done: lshift_add_imm LID UDPR_1 16 0")      # We are finished, set pointer to beginning of local memory
    tran1.writeAction("mov_imm2reg UDPR_2 1")                           # Set register to 1
    tran1.writeAction("mov_reg2lm UDPR_2 UDPR_1 4")                     # Set flag to 1
    tran1.writeAction("yield_terminate 1")                              # Terminate event

    return efa