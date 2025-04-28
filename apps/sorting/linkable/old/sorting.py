from linker.EFAProgram import efaProgram, EFAProgram
from libraries.DistributedSort.distributed_sort import DistributedSort
from Macro import *

TERM_FLAG_ADDR = 0

@efaProgram
def sorting(efa: EFAProgram):

    #  initial event
    #  pass through the arguments and call sort

    taskname = "test_sort"
    dist_sort = DistributedSort(efa, offset = 16000, taskname=taskname, debug_flag=False)
    dist_sort.generate_sort()

    lm_base_reg = "UDPR_1"
    ev_word_reg = "UDPR_2"
    tmp_reg = "UDPR_3"
    temp_reg = "UDPR_4"
    zero = "UDPR_5"

    init_tran = dist_sort.state.writeTransition("eventCarry", dist_sort.state, dist_sort.state, f'updown_init')
    init_tran.writeAction(f"print '[DEBUG][NWID %d] Event <updown_init> getting len = %ld, addr = %ld' {'X0'} {'X8'} {'X9'}")

    init_tran.writeAction(f"mov_imm2reg {ev_word_reg} 0")
    init_tran = set_ev_label(init_tran, ev_word_reg, f'{taskname}::distributed_sort', new_thread = True, label="")
    
    init_tran.writeAction(f"addi {'X7'} {lm_base_reg} 8")
    init_tran.writeAction(f"mov_imm2reg {zero} 0")
    init_tran.writeAction(f"movrl {zero} {TERM_FLAG_ADDR}({lm_base_reg}) 0 8")
    init_tran.writeAction(f"print 'cur_cont = %lu' {'X1'}")

    #  Prepare for the arguments
    init_tran.writeAction(f"movrl {'X8'} 0({lm_base_reg}) 0 8")
    init_tran.writeAction(f"movrl {'X9'} 8({lm_base_reg}) 0 8")
    init_tran.writeAction(f"movrl {'X10'} 16({lm_base_reg}) 0 8")
    init_tran.writeAction(f"movrl {'X11'} 24({lm_base_reg}) 0 8")
    init_tran.writeAction(f"movrl {'X12'} 32({lm_base_reg}) 0 8")
    init_tran.writeAction(f"movrl {'X13'} 40({lm_base_reg}) 0 8")
    # Prepare for return event
    # init_tran.writeAction(f"addi {'X2'} {temp_reg} 0")
    # init_tran.writeAction(f"m 0")
    # init_tran.writeAction(f"evlb {temp_reg} {'updown_terminate'}")
    # Send out the event
    init_tran.writeAction(f"send_wret {ev_word_reg} {'updown_terminate'} {lm_base_reg} {6} {tmp_reg}")
    init_tran.writeAction(f"yield")
    # init_tran.writeAction(f"")




    #  terminate event
    #  sort will return to this after it finishes
    		
    lm_base_reg = "UDPR_1"
    temp_reg = "UDPR_2"
    '''
    User defined continuation event transition to be triggered when the UDKVMSR task finishes.
    '''
    term_tran = dist_sort.state.writeTransition("eventCarry", dist_sort.state, dist_sort.state, f'updown_terminate')
    term_tran.writeAction(f"addi {'X7'} {lm_base_reg} 0")

    term_tran.writeAction(f"print '[DEBUG][NWID %d] Event <updown_terminate> getting len = %ld, addr = %ld' {'X0'} {'X8'} {'X9'}")
    term_tran.writeAction(f"print 'cur_cont = %lu' {'X1'}")

    
    # UpDown program finishes, Signal the top 
    term_tran.writeAction(f"mov_imm2reg {temp_reg} 1")
    term_tran.writeAction(f"move {temp_reg} {TERM_FLAG_ADDR}({lm_base_reg}) 0 8")
    term_tran.writeAction("yield_terminate")
