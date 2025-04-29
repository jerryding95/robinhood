from EFA_v2 import *

def sendtest():
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
    }

    # OB_0 NWID to send event to
    # OB_1 repeated for OB count
    tran0 = state0.writeTransition("eventCarry", state0, state0, event_map['launch_events'])
    tran0.writeAction("addi X8 X18 0")                             
    tran0.writeAction("addi X7 X18 0")                             
    tran0.writeAction("evi X2 X16 " + str(event_map['process_events']) + " 1") #  
    tran0.writeAction("evi X16 X16 0 4") #  
    tran0.writeAction("ev X16 X16 X0 X0 8") #  
    tran0.writeAction("sendr X16 X16 X18 X18 X18 0")
    tran0.writeAction("yield")

    tran1 = state0.writeTransition("eventCarry", state0, state0, event_map["process_events"])
    tran1.writeAction("movir X17 1")
    tran1.writeAction("movrl X17 0(X18) 0 8")
    tran1.writeAction("yieldt")
    
    return efa