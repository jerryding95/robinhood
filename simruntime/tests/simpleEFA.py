
from EFA import *

def simpleEFA():
    efa = EFA([])
    efa.code_level = 'machine'
    
    state0 = State() #Initial State? 
    efa.add_initId(state0.state_id)
    efa.add_state(state0)
    state1 = State() #Initial State? 

    #Add events to dictionary 
    event_map = {
        'add_1':0
    }

    tran0 = state0.writeTransition("eventCarry", state0, state1, event_map['add_1'])
    tran0.writeAction("mov_ob2reg OB_0 UDPR_1")
    tran0.writeAction("addi UDPR_1 UDPR_1 1")
    tran0.writeAction("mov_imm2reg UDPR_2 0")
    tran0.writeAction("mov_reg2lm UDPR_1 UDPR_2 4")
    tran0.writeAction("yield_terminate 2" )
    return efa

if __name__=="__main__":
    efa = simpleEFA()
    #efa.printOut(error)
    
