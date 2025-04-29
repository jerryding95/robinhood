
from EFA import *

def memcpyEFA():
    efa = EFA([])
    efa.code_level = 'machine'
    
    state0 = State() #Initial State? 
    efa.add_initId(state0.state_id)
    efa.add_state(state0)

    #Add events to dictionary 
    event_map = {
        'memcpy':0,
        'read_return':1,
        'write_return':2
    }

    tran0 = state0.writeTransition("eventCarry", state0, state0, event_map['memcpy'])
    tran0.writeAction("mov_ob2ear OB_0_1 EAR_0")                        #0 DRAM src addr
    tran0.writeAction("mov_ob2ear OB_2_3 EAR_1")                        #1 DRAM dst addr
    tran0.writeAction("mov_ob2reg OB_4 UDPR_2")                         #2 # Size in bytes
    tran0.writeAction("mov_imm2reg UDPR_3 0")                           #3 # iterator
    tran0.writeAction("mov_imm2reg UDPR_4 0")                           #3 # write iterator

    tran0.writeAction("send_loop: ble UDPR_2 UDPR_3 reads_done")                          #4  l1
    tr_str = "send_dmlm_ld_wret UDPR_3 " + str(event_map["read_return"]) + " 8 0"     #5 Read from EAR_0 plus UDPR_3 offset
    tran0.writeAction(tr_str)
    tran0.writeAction("addi UDPR_3 UDPR_3 8")
    tran0.writeAction("jmp send_loop")                                         #7
    tran0.writeAction("reads_done: mov_imm2reg UDPR_3 0")                           #7
    tran0.writeAction("mov_imm2reg UDPR_3 0")                           #3 # iterator
    tran0.writeAction("yield 5")                                        #8

    tran1 = state0.writeTransition("eventCarry", state0, state0, event_map['read_return'])
    
    tran1.writeAction("mov_ob2reg OB_0 UDPR_5")
    tran1.writeAction("mov_ob2reg OB_1 UDPR_6")
    tran1.writeAction("mov_imm2reg UDPR_7 4")                           #3 # iterator
    tran1.writeAction("mov_reg2lm UDPR_5 UDPR_7 4")                           #3 # iterator
    tran1.writeAction("mov_imm2reg UDPR_7 8")                           #3 # iterator
    tran1.writeAction("mov_reg2lm UDPR_6 UDPR_7 4")                           #3 # iterator
    tran1.writeAction("mov_imm2reg UDPR_7 4")                           #3 # iterator
    tran1.writeAction(f"send_dmlm_wret UDPR_3 {event_map['write_return']} UDPR_7 8 1")
    tran1.writeAction("addi UDPR_3 UDPR_3 8")
    tran1.writeAction("yield 2")
    
    tran2 = state0.writeTransition("eventCarry", state0, state0, event_map['write_return'])
    tran2.writeAction("addi UDPR_4 UDPR_4 8")
    tran2.writeAction("bge UDPR_4 UDPR_2 writes_done")
    tran2.writeAction("yield 1")
    tran2.writeAction("writes_done: mov_imm2reg UDPR_1 0")
    tran2.writeAction("mov_imm2reg UDPR_2 1")
    tran2.writeAction("mov_reg2lm UDPR_2 UDPR_1 4")
    tran2.writeAction("yield_terminate 1")
    return efa

if __name__=="__main__":
    efa = memcpyEFA()
    
