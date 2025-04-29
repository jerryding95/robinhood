from EFA_v2 import *

def sendpolicy_test():
    efa = EFA([])
    efa.code_level = "machine"
    blksize = 64

    state0 = State()  # Initial State?
    efa.add_initId(state0.state_id)
    efa.add_state(state0)

    # Add events to dictionary
    event_map = {
        "launch_events": 0,
        "process_events": 1,
        "term": 2,
    }

    # OB_0 NWID to send event to
    # OB_1 repeated for OB count
    tran0 = state0.writeTransition("eventCarry", state0, state0, event_map['launch_events'])
    tran0.writeAction("addi X8 X23 0")  # number of events
    tran0.writeAction("addi X9 X18 0")  # policy
    tran0.writeAction("movir X21 0")  # nmber of lanes   
    tran0.writeAction(f"addi X8 X17 0")  # iterator
    tran0.writeAction(f"print 'Sending out %lu events to lanes' X17")
    tran0.writeAction(f"send_loop: beqi X17 0 loop_done")
    tran0.writeAction("evi X2 X16 " + str(event_map['process_events']) + " 1") #  
    tran0.writeAction("evi X16 X16 255 4") #
    tran0.writeAction(f"addi X0 X19 1")
    tran0.writeAction("ev X16 X16 X19 X19 8") #  
    tran0.writeAction(f"sendr_wret X16 {event_map['term']} X21 X21 X30")
    tran0.writeAction("addi X21 X21 1")  # nmber of lanes   
    tran0.writeAction("subi X17 X17 1")  # nmber of lanes   
    tran0.writeAction("jmp send_loop")
    tran0.writeAction(f"loop_done: muli X8 X17 2")  # iterator
    tran0.writeAction(f"print 'Sending out %lu events to lanes' X17")
    tran0.writeAction(f"send_loop1: beqi X17 0 loop_done1")
    tran0.writeAction("evi X2 X16 " + str(event_map['process_events']) + " 1") #  
    tran0.writeAction("evi X16 X16 255 4") #
    tran0.writeAction(f"addi X0 X19 2")
    tran0.writeAction("ev X16 X16 X19 X19 8") #  
    tran0.writeAction(f"sendr_wret X16 {event_map['term']} X21 X21 X30")
    tran0.writeAction("addi X21 X21 1")  # nmber of lanes   
    tran0.writeAction("subi X17 X17 1")  # nmber of lanes   
    tran0.writeAction("jmp send_loop1")
    
    # Policy based send
    tran0.writeAction("loop_done1: evi X2 X16 " + str(event_map['process_events']) + " 1") #  
    tran0.writeAction(f"print 'Sending out 1 event to policy:%lu lane' X18 ")
    tran0.writeAction(f"addi X18 X20 0")
    tran0.writeAction(f"sli X20 X20 27")
    tran0.writeAction("evi X16 X16 255 4") #
    tran0.writeAction(f"add X19 X20 X19")
    tran0.writeAction("ev X16 X16 X19 X19 8") #  
    tran0.writeAction(f"sendr_wret X16 {event_map['term']} X21 X21 X30")
    tran0.writeAction("addi X21 X21 1")  # nmber of lanes   
    tran0.writeAction("yield")

    tran1 = state0.writeTransition("eventCarry", state0, state0, event_map["process_events"])
    tran1.writeAction(f"print '[NWID %lu] processing:%lu event ' X0 X8")
    tran1.writeAction("movir X17 1")
    tran1.writeAction("addi X7 X18 1")
    tran1.writeAction("movrl X17 0(X18) 0 8")
    tran1.writeAction(f"sendr_reply X8 X8 X30")
    tran1.writeAction("yieldt")
    
    tran2 = state0.writeTransition("eventCarry", state0, state0, event_map["term"])
    tran2.writeAction(f"print '[NWID %lu] returned:%lu event ' X0 X8")
    tran2.writeAction("subi X21 X21 1")
    tran2.writeAction("blei X21 0 term2")
    tran2.writeAction("yield")
    tran2.writeAction("term2: movir X17 1")
    tran2.writeAction("addi X7 X18 0")
    tran2.writeAction("movrl X17 0(X18) 0 8")
    tran2.writeAction("yieldt")
    return efa