from linker.EFAProgram import efaProgram, EFAProgram

from libraries.UDMapShuffleReduce.linkable.LinkableKVMapShuffleCombineTPL import UDKeyValueMapShuffleReduceTemplate
from libraries.UDMapShuffleReduce.utils.OneDimArrayKeyValueSet import OneDimKeyValueSet
from libraries.UDMapShuffleReduce.utils.IntermediateKeyValueSet import IntermediateKeyValueSet
from libraries.LMStaticMaps.LMStaticMap import *
from libraries.UDMapShuffleReduce.KVMSRMachineConfig import *
from libraries.UDMapShuffleReduce.linkable.LinkableGlobalSync import Broadcast

VECTOR_POINTER_OFFSET = HEAP_OFFSET
SPMV_HEAP = VECTOR_POINTER_OFFSET + WORD_SIZE

EXTENSION = 'load_balancer'
test_ws = False
test_random = True
DEBUG_FLAG = False
LB_TYPE = ['mapper','reducer']
rtype = 'lane' if test_ws else 'ud'
multi = not test_ws
map_ws = test_ws
red_ws = test_ws


class SPMVMapShuffleReduce(UDKeyValueMapShuffleReduceTemplate):
    
    def kv_combine_op(self, tran: EFAProgram.Transition, key: str, in_values: list, old_values: list, results: list) -> EFAProgram.Transition:
        '''
        User defined operation used by the kv_combine to combine values to be emitted to the output kv set in the reduce task. 
        It takes an intermediate key-value pair and updates the output key value pair for that key accordingly.
        Parameters
            tran:       transition.
            key:        the name of the register storing the intermediate key.
            in_values:  the name of the register storing intermediate value to be combined with the current output kvpair's value corresponding with the incoming intermediate key
            old_values: the name of the register storing the current output kvpair's value corresponding with the incoming intermediate key
            results: a list of register names containing the combined values to be stored back
        '''

        # user defined combine function
        # tran.writeAction(f"fadd.64 {in_values[0]} {old_values[0]} {results[0]}")
        if DEBUG_FLAG:
            tran.writeAction(f"print 'combine_op key %ld value %lx::' {key} {in_values[0]}")
        for in_val, old_val, result in zip(in_values, old_values, results):
            tran.writeAction(f"fadd.64 {in_val} {old_val} {result}")
            # for i in range(100):
            #     tran.writeAction(f"fadd.64 {in_val} {result} {result}")
            #     tran.writeAction(f"fsub.64 {result} {in_val} {result}")
            # tran.writeAction(f"print '[DEBUG][NWID %d] Combine key %ld value %llu -> %llu(result)' {'X0'} {key} {in_val} {result}")
        return tran

def kv_map(state: EFAProgram.State, task: str):
    
    row = "X16"
    val = "X17"
    col = "X18"
    addr = "X19"
    ev_word_reg = "X30"
    tmp = "X31"

    '''
    Event:      Map task
                Locate and read corresponding entry in vector
    Operands:   X8: Higher 32 bit - row
                    Lower 32 bit - col
                X9: Value in fp64
    '''
    map_tran: EFAProgram.Transition = state.writeTransition("eventCarry", state, state, f"{task}::kv_map")

    # Save row id and value in registers
    map_tran.writeAction(f"sri {'X8'} {row} {32}")
    map_tran.writeAction(f"addi {'X9'} {val} {0}")

    # Get col id
    map_tran.writeAction(f"movir {tmp} {1}")
    map_tran.writeAction(f"sli {tmp} {tmp} {32}")
    map_tran.writeAction(f"subi {tmp} {tmp} {1}")
    map_tran.writeAction(f"and {'X8'} {tmp} {col}")

    # Get address of the corresponding vector entry
    map_tran.writeAction(f"movir {addr} {VECTOR_POINTER_OFFSET}")
    map_tran.writeAction(f"add {'X7'} {addr} {addr}")
    map_tran.writeAction(f"movlr 0({addr}) {addr} 0 {WORD_SIZE}")
    # map_tran.writeAction(f"print '[SPMV MULT] key = %ld, col %ld, vector base address %lu(0x%lx)' {row} {col} {addr} {addr}")
    map_tran.writeAction(f"muli {col} {tmp} {WORD_SIZE}")
    map_tran.writeAction(f"add {tmp} {addr} {addr}")
    # map_tran.writeAction(f"print '[SPMV MULT] key = %ld, col %ld, vector entry address %lu(0x%lx)' {row} {col} {addr} {addr}")
    map_tran.writeAction(f"send_dmlm_ld_wret {addr} {'kv_map_calc'} {1} {tmp}")
    map_tran.writeAction(f"yield")


    '''
    Event:      Map calculate task
    Operands:   X8: Vector entry value
                X9: Address of entry
    '''
    calc_tran: EFAProgram.Transition = state.writeTransition("eventCarry", state, state, f"kv_map_calc")

    # Calculate new values
    calc_tran.writeAction(f"fmul.64 {'X8'} {val} {'X20'}")
    if DEBUG_FLAG:
        calc_tran.writeAction(f"print '[SPMV MULT] key = %ld, mat value %lu(0x%lx), vector value 0x%lx, result value %lu(%lx)' {row} {val} {val} {'X8'} {'X20'} {'X20'}")
    calc_tran.writeAction(f"fmul.64 {'X8'} {val} {val}")
    if DEBUG_FLAG:
        calc_tran.writeAction(f"print '[SPMV MULT] result value 0x%lx' {val}")
    
    # Emit the intermediate key-value pair to reduce task
    calc_tran.writeAction(f"evii {ev_word_reg} {f'{task}::kv_map_emit'} {255} {5}")
    calc_tran.writeAction(f"sendr_wcont {ev_word_reg} {'X2'} {row} {val}")

    # Return to UDKVMSR library
    calc_tran.writeAction(f"addi {'X2'} {ev_word_reg} 0")
    calc_tran.writeAction(f"evlb {ev_word_reg} {f'{task}::kv_map_return'}")
    calc_tran.writeAction(f"sendr_wcont {ev_word_reg} {'X2'} {row} {val}")

    calc_tran.writeAction("yield")

    return 

def kv_reduce(state: EFAProgram.State, task: str):
    # user defined reduce code
    reduce_tran: EFAProgram.Transition = state.writeTransition("eventCarry", state, state, f"{task}::kv_reduce")
    
    '''
    Event:      Reduce task 
    Operands:   Intermediate key-value pair
    '''
    cont = "UDPR_10"
    ev_word_reg = "UDPR_9"
    '''
    Call kv_combine to combine the intermediate key-value pair with the output key-value pair, using the customized combine function (defined in kv_combine_op).
    kv_combine is a functionality provided by UDKVMSR to do atomic update of the output key-value pair.
    '''

    # Return to UDKVMSR library
    # reduce_tran.writeAction(f"addi {'X2'} {ev_word_reg} 0")
    # reduce_tran.writeAction(f"evlb {ev_word_reg} {f'{task}::kv_combine'}")
    reduce_tran.writeAction(f"addi X1 {cont} 0")
    reduce_tran.writeAction(f"evii {ev_word_reg} {f'{task}::kv_combine'} 255 5")
    reduce_tran.writeAction(f"print 'reducing key = %ld, value = 0x%lx' {'X8'} {'X9'}")
    reduce_tran.writeAction(f"sendops_wret {ev_word_reg} {f'combine_return'} {'X8'} 2 {'X16'}")
    reduce_tran.writeAction("yield")

    tran = state.writeTransition("eventCarry", state, state, 'combine_return')
    ev_word_reg = "UDPR_9"
    cont = "UDPR_10"
    tran.writeAction(f"addi X2 {ev_word_reg} 0")
    tran.writeAction(f"evlb {ev_word_reg} {f'{task}::kv_reduce_return'}")
    tran.writeAction(f"sendr_wcont {ev_word_reg} {cont} {'X16'} {'X16'}")
    tran.writeAction("yield")
    
    return 

def init_event(state, task):
    temp_reg    = "UDPR_0"
    lm_base_reg = "UDPR_1"
    send_buffer = "UDPR_2"
    ev_word_reg = "UDPR_9"
    addr        = "UDPR_10"
    broadcast_ev_word   = "UDPR_11"
    
    part_ptr    = "UDPR_3"
    part_per_lane = "UDPR_4"
    num_lanes   = "UDPR_5"


    broadcast = Broadcast(state=state, identifier=task, debug_flag=DEBUG_FLAG)
    init_tran = state.writeTransition("eventCarry", state, state, 'updown_init')
    setv_tran = state.writeTransition("eventCarry", state, state, 'set_vector_ptr')
    msr_init_tran = state.writeTransition("eventCarry", state, state, 'msr_init')
    '''
    Entry event transition to be triggered by the top program. Updown program starts from here.
      operands
      X8:   Pointer to the partition array (64-bit DRAM address)
      X9:   Number of partitions per lane
      X10:  Number of lanes
      X11:  Poitner to the vector array
      X12:  Local offset to input metadata
      X13:  Local offset to output metadata
      X14:  Local offset to intermediate metadata

      ##############
      X11:  Pointer to input kvset (64-bit DRAM address)
      X12:  Number of elements in the input kvset (1D array)
      X13:  Pointer to outKVMap (64-bit DRAM address)
      X14:  Number of elements in the output kvset (1D array)
      (If load balancer is enabled) X15:    Pointer to interKVMap (64-bit DRAM address)
      ##############
    '''
    
    # init_tran.writeAction(f"print '[DEBUG][NWID %d] Event <updown_init> ' {'X0'} ")
    init_tran.writeAction(f"perflog 1 0 'Updown Init'")

    # # Reset TOP_FLAG to 0
    # init_tran.writeAction(f"movir {temp_reg} 0")
    # init_tran.writeAction(f"addi {'X7'} {lm_base_reg} {TOP_FLAG_OFFSET}")
    # init_tran.writeAction(f"move {temp_reg} 0({lm_base_reg}) 0 {WORD_SIZE}")

    # Move the UDKVMSR call parameters to registers and HEAP area.
    # init_tran.writeAction(f"print 'START'")
    init_tran.writeAction(f"addi {'X8'} {part_ptr} {0}")
    init_tran.writeAction(f"addi {'X9'} {part_per_lane} {0}")
    init_tran.writeAction(f"addi {'X10'} {num_lanes} {0}")

    init_tran.writeAction(f"addi {'X7'} {lm_base_reg} {SPMV_HEAP}")

    init_tran.writeAction(f"add {'X7'} {'X12'} {addr}")
    init_tran.writeAction(f"movlr 0({addr}) {temp_reg} 1 {WORD_SIZE}")
    init_tran.writeAction(f"movrl {temp_reg} 0({lm_base_reg}) 1 {WORD_SIZE}")
    init_tran.writeAction(f"movlr 0({addr}) {temp_reg} 1 {WORD_SIZE}")
    init_tran.writeAction(f"movrl {temp_reg} 0({lm_base_reg}) 1 {WORD_SIZE}")

    init_tran.writeAction(f"add {'X7'} {'X13'} {addr}")
    init_tran.writeAction(f"movlr 0({addr}) {temp_reg} 1 {WORD_SIZE}")
    init_tran.writeAction(f"movrl {temp_reg} 0({lm_base_reg}) 1 {WORD_SIZE}")
    init_tran.writeAction(f"movlr 0({addr}) {temp_reg} 1 {WORD_SIZE}")
    init_tran.writeAction(f"movrl {temp_reg} 0({lm_base_reg}) 1 {WORD_SIZE}")

    init_tran.writeAction(f"add {'X7'} {'X14'} {addr}")
    init_tran.writeAction(f"movlr 0({addr}) {temp_reg} 1 {WORD_SIZE}")
    init_tran.writeAction(f"movrl {temp_reg} 0({lm_base_reg}) 1 {WORD_SIZE}")
    
    # Broadcast vector pointer
    init_tran.writeAction(f"evii {ev_word_reg} {broadcast.get_broadcast_ev_label()} {255} {5}")
    init_tran.writeAction(f"addi {'X2'} {broadcast_ev_word} {0}")
    init_tran.writeAction(f"evlb {broadcast_ev_word} {'set_vector_ptr'}")
    init_tran.writeAction(f"addi {'X7'} {addr} {SEND_BUFFER_OFFSET}")
    init_tran.writeAction(f"movrl {num_lanes} 0({addr}) 1 {WORD_SIZE}")
    init_tran.writeAction(f"movrl {broadcast_ev_word} 0({addr}) 1 {WORD_SIZE}")
    init_tran.writeAction(f"movrl {'X11'} 0({addr}) 1 {WORD_SIZE}")
    init_tran.writeAction(f"addi {'X7'} {addr} {SEND_BUFFER_OFFSET}")
    init_tran.writeAction(f"send_wret {ev_word_reg} {'msr_init'} {addr} {8} {temp_reg}")
    init_tran.writeAction(f"yield")


    '''
    Event:  Set vector pointer on scratchpad
    '''
    setv_tran = state.writeTransition("eventCarry", state, state, 'set_vector_ptr')
    setv_tran.writeAction(f"addi {'X7'} {lm_base_reg} {VECTOR_POINTER_OFFSET}")
    setv_tran.writeAction(f"movrl {'X8'} 0({lm_base_reg}) 0 {WORD_SIZE}")
    setv_tran.writeAction(f"sendr_reply X0 X16 X16")
    setv_tran.writeAction(f"yieldt")



    '''
    Event:  Returned from broadcasting vector pointer, start SPMV MSR.

    Operands:
        OB_0: Pointer to the partition array (64-bit DRAM address)
        OB_1: Number of partitions per lane
        OB_2: Number of lanes
        OB_3: Scratchapd addr storing the input kvset metadata (base address and size)
        OB_4: Scratchapd addr storing the output kvset metadata (base address and size)
        (If load balancer is enabled) OB_5: Scratchapd addr storing the intermediate kvset metadata (base address)

    '''

    # Move the UDKVMSR call parameters to scratchpad.
    msr_init_tran.writeAction(f"perflog 1 0 'MSR init'")
    msr_init_tran.writeAction(f"movir {send_buffer} {SEND_BUFFER_OFFSET}")
    msr_init_tran.writeAction(f"add {'X7'} {send_buffer} {send_buffer}")
    msr_init_tran.writeAction(f"addi {'X7'} {lm_base_reg} {SPMV_HEAP}")

    
    # Partition pointer
    msr_init_tran.writeAction(f"movrl {part_ptr} 0({send_buffer}) 1 {WORD_SIZE}")
    # Num partition per lane
    msr_init_tran.writeAction(f"movrl {part_per_lane} 0({send_buffer}) 1 {WORD_SIZE}")
    if DEBUG_FLAG:
        msr_init_tran.writeAction(f"print '[DEBUG][NWID %d] Partition array %lu(0x%lx) and number of partition per lane = %ld' {'X0'} {part_ptr} {part_ptr} {part_per_lane}")
    # Num of lanes
    msr_init_tran.writeAction(f"movrl {num_lanes} 0({send_buffer}) 1 {WORD_SIZE}")
    # Local pointer to input metadata
    msr_init_tran.writeAction(f"movrl {lm_base_reg} 0({send_buffer}) 1 {WORD_SIZE}")
    # Local pointer to output metadata
    msr_init_tran.writeAction(f"addi {lm_base_reg} {lm_base_reg} {2*WORD_SIZE}")
    msr_init_tran.writeAction(f"movrl {lm_base_reg} 0({send_buffer}) 1 8")
    # Local pointer to intermedaite metadata
    msr_init_tran.writeAction(f"addi {lm_base_reg} {lm_base_reg} {2*WORD_SIZE}")
    msr_init_tran.writeAction(f"movrl {lm_base_reg} 0({send_buffer}) 1 8")


    # Start MSR
    msr_init_tran.writeAction(f"movir {send_buffer} {SEND_BUFFER_OFFSET}")
    msr_init_tran.writeAction(f"add {'X7'} {send_buffer} {send_buffer}")
    msr_init_tran.writeAction(f"ev_update_2 {ev_word_reg} {f'{task}::map_shuffle_reduce'} 255 5")
    msr_init_tran.writeAction(f"send_wret {ev_word_reg} {'updown_terminate'} {send_buffer} {8} {temp_reg}")


    msr_init_tran.writeAction(f"yield")

    return

def term_event(state, task):
    temp_reg    = "UDPR_0"
    lm_base_reg = "UDPR_1"
    send_buffer = "UDPR_2"
    '''
    User defined continuation event transition to be triggered when the UDKVMSR task finishes.
    '''
    term_tran = state.writeTransition("eventCarry", state, state, 'updown_terminate')
    # UpDown program finishes, Signal the top 
    term_tran.writeAction(f"perflog 1 0 'MSR terminate'")
    term_tran.writeAction(f"mov_imm2reg {temp_reg} 1")
    term_tran.writeAction(f"addi {'X7'} {lm_base_reg} 0")
    term_tran.writeAction(f"move {temp_reg} {TOP_FLAG_OFFSET}({lm_base_reg}) 0 8")
    term_tran.writeAction("yield_terminate")

    return

@efaProgram
def spmvMSREFA(efa):

    task_name = "spmv"
    # spmvMSR = SPMVMapShuffleReduce(efa=efa, task_name=task_name, meta_data_offset=UDKVMSR_0_OFFSET, debug_flag=DEBUG_FLAG, extension = EXTENSION, load_balancer_type = ['mapper','reducer'], claim_multiple_work=True)
    spmvMSR = SPMVMapShuffleReduce(efa=efa, task_name=task_name, meta_data_offset=UDKVMSR_0_OFFSET, debug_flag=DEBUG_FLAG, 
                                    extension = EXTENSION, load_balancer_type = LB_TYPE, grlb_type = rtype, 
                                    claim_multiple_work = multi, test_map_ws=map_ws, test_reduce_ws=red_ws, random_lb=test_random)
    spmvMSR.set_input_kvset(OneDimKeyValueSet("Test input", element_size=2) )
    spmvMSR.set_intermediate_kvset(IntermediateKeyValueSet("Test intermediate", key_size=1, value_size=1))
    spmvMSR.set_output_kvset(OneDimKeyValueSet("Test output", element_size=1) )
    spmvMSR.setup_cache(cache_offset=SPMV_HEAP, num_entries=717, entry_size=2, intermediate_cache_size = 512)
    spmvMSR.set_max_thread_per_lane(max_map_th_per_lane=32, max_reduce_th_per_lane=32)
    spmvMSR.generate_udkvmsr_task()
    
    init_event(spmvMSR.state, task_name)
    kv_map(spmvMSR.state, task_name)
    # kv_reduce(spmvMSR.state, task_name)
    term_event(spmvMSR.state, task_name)
    
    return efa


