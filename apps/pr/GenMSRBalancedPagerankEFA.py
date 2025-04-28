from typing import Tuple
from EFA_v2 import *
import sys
PROJ = "/scratch/yqwang/udgem5sim"
sys.path.append(f"{PROJ}/ext/updown/install/updown/libraries")

from EFA_v2 import Transition
from KVMapShuffleReduceTPL_part import UDKeyValueMapShuffleReduceTemplate
from KeyValueSetTPL import KeyValueSetTemplate
from math import log2
from Macro import *

WORD_SIZE = 8
LOG2_WORD_SIZE = 3

'''
Below is an naive map reduce example. The map function masks the input key by the number of workerand send it with input value to the reducer.
The reducer takes the intermediate key-value pairs and sums up all the values correspond to the same key.
To write a map reduce program using the template, one needs to implement the two abstract method, namely kv_map() and kv_reduce(),
instantiate the map reduce task, and set up the metadata required by the template using the provided helper functions.
'''
class PagerankMapShuffleReduce(UDKeyValueMapShuffleReduceTemplate):
    BATCH_SIZE = 8

    def kv_map(self, tran: Transition, key: str, values: list, map_ret_ev_label: str) -> int:
        '''
        values[0]: degree
        values[1]: neighbor list pointer
        values[2]: PageRank value
        '''
        ld_ret_ev_label = self.get_event_mapping("map_load_return")
        
        degree    = values[0]   # value[0] stores the degree of the node
        pr_value  = values[2]   # value[2] stores the PageRank value of the node
        nbor_list = "UDPR_0"    # Register UDPR_0 stores the pointer to the neighbor list 
        nbor_bnd  = "UDPR_1"    # Register UDPR_1 stores the bound of the neighbor list
        vid       = "UDPR_2"    # Register UDPR_2 stores the degree in floating point format
        new_pr_value = "UDPR_3" # Register UDPR_3 stores the new PageRank value
        degree_reg   = "UDPR_4" # Register UDPR_4 stores the vertex degree
        dest_id   = "UDPR_5"    # Register UDPR_5 stores the lane id where the intermediate kvmap will be sent to
        nbor_reg  = "UDPR_6"    # Register UDPR_6 stores the neighbors[0] pointer
        ctr       = "UDPR_7"    # Register UDPR_7 stores the counter for the number of neighbors finished
        scratch   = ["UDPR_12", "UDPR_13"]  # Scratch registers
        ld_loop_label = "array_load"        # Label for the load loop
        ld_fin_label  = "array_load_fin"    # Label for finishing load
        empty_label   = "empty"             # Label for empty neighbor list
        bcst_cont_label = "broadcast_continue" # Label for broadcast continue
        # user defined map code
        if self.debug_flag:
            tran.writeAction(f"addi {key} {vid} 0")
            tran.writeAction(f"addi {values[1]} {nbor_reg} 0")
            tran.writeAction(f"print '[DEBUG][NWID %d] Start map task for vertex %d degree %d neighbor list 0x%x' {'X0'} {key} {values[0]} {nbor_reg}")
        tran.writeAction(f"addi {values[0]} {degree_reg} 0")
        tran.writeAction(f"beq {degree} 0 {empty_label}")
        tran.writeAction(f"addi {values[1]} {nbor_list} 0")
        tran.writeAction(f"lshift {degree} {nbor_bnd} {LOG2_WORD_SIZE}")
        tran.writeAction(f"add {nbor_list} {nbor_bnd} {nbor_bnd}")
        tran.writeAction(f"{ld_loop_label}: bge {nbor_list} {nbor_bnd} {ld_fin_label}")
        tran.writeAction(f"send_dmlm_ld_wret {nbor_list} {ld_ret_ev_label} {self.BATCH_SIZE} {scratch[0]}")
        tran.writeAction(f"addi {nbor_list} {nbor_list} {WORD_SIZE << LOG2_WORD_SIZE}")
        tran.writeAction(f"jmp {ld_loop_label}")
        tran.writeAction(f"{ld_fin_label}: mov_reg2reg {pr_value} {new_pr_value}")
        tran.writeAction(f"mov_imm2reg {ctr} 0")
        if self.debug_flag:
            tran.writeAction(f"print '[DEBUG][NWID %d] Vertex %d outgoing PageRank value = %f' {'X0'} {key} {new_pr_value}")
        tran.writeAction(f"yield")
        if self.debug_flag:
            tran.writeAction(f"{empty_label}: print '[DEBUG][NWID %d] Vertex %d empty neighbor list return to lane master ' {'X0'} {key}")
            self.msr_return(tran, ret_label=map_ret_ev_label, temp_reg=scratch[0])
        else:
            self.msr_return(tran, ret_label=map_ret_ev_label, branch_label=empty_label, temp_reg=scratch[0])
        tran.writeAction(f"yield")
        
        bcst_fin_label  = "finish_broadcast"    # Label for finishing broadcast to all neighbors
        ld_tran = self.state.writeTransition("eventCarry", self.state, self.state, ld_ret_ev_label)
        if self.debug_flag:
            ld_tran.writeAction(f"print ' '")
            ld_tran.writeAction(f"print '[DEBUG][NWID %d] Event <map_load_return> ev_word = %d vertex %d degree = %d nlist_addr = 0x%x nlist_bound = 0x%x' \
                {'X0'} {'EQT'} {vid} {degree} {'X3'} {nbor_bnd}")
        ld_tran.writeAction(f"addi {'X3'} {nbor_list} 0")
        for k in range(self.BATCH_SIZE):
            ld_tran.writeAction(f"bge {nbor_list} {nbor_bnd} {bcst_cont_label}")
            self.kv_emit(ld_tran, f"OB_{k}", [new_pr_value], dest_id, scratch[0], scratch[1])
            if self.debug_flag:
                ld_tran.writeAction(f"print '[DEBUG][NWID %d] Map generates intermediate key = %d, send to lane %d' {'X0'} {f'OB_{k}'} {dest_id}")
            ld_tran.writeAction(f"addi {nbor_list} {nbor_list} {WORD_SIZE}")
            ld_tran.writeAction(f"addi {ctr} {ctr} 1")
            ld_tran.writeAction(f"bge {ctr} {degree_reg} {bcst_fin_label}")
        # ld_tran.writeAction(f"bge {nbor_list} {nbor_bnd} {bcst_fin_label}")
        ld_tran.writeAction(f"{bcst_cont_label}: yield")
        if self.debug_flag:
            ld_tran.writeAction(f"{bcst_fin_label}: print '[DEBUG][NWID %d] Finish broadcasting to %d neighbors' {'X0'} {degree_reg}")
            self.msr_return(ld_tran, ret_label=map_ret_ev_label, operands=f'{vid} {nbor_reg}', temp_reg=scratch[0]) 
        else:
            self.msr_return(ld_tran, ret_label=map_ret_ev_label, branch_label=bcst_fin_label, temp_reg=scratch[0]) 
        ld_tran.writeAction("yield")
        
        return 


    def kv_reduce(self, tran: Transition, key: str, values: list, reduce_ret_ev_label: str) -> Transition:
        # user defined reduce code
        '''
        Helper function for atomic operation using scratchpad. Requires kv_merge_op() to be implemented and cache enabled.
        Parameter:
            key:        name of the operand buffer entries/registers containing the key to the cache entry
            values:     name of the operand buffer entries/registers containing the value to be merged
            reduce_ret_ev_label:    return event label to the udkvmsr library
            regs:       scratch registers, by default is all the 16 general purposed registers
        '''
        return self.kv_merge(tran, key, values, reduce_ret_ev_label)

    def kv_merge_op(self, tran: Transition, in_key: str, in_values: list, old_values: list, regs: list) -> list:
        for in_val, old_val, result in zip(in_values, old_values, regs):
            tran.writeAction(f"fadd.64 {in_val} {old_val} {result}")
            if self.debug_flag:
                tran.writeAction(f"print '[DEBUG][NWID %d] Merge values for key = %d incoming value = %f old value = %f result = %f' {'X0'} {in_key} {in_val} {old_val} {result}")
        return regs

class OneDimKeyValueSet(KeyValueSetTemplate):
    '''
    Example implementation of an one dimensional key value set.
    '''

    def __init__(self, name: str, key_size: int, value_size: int):
        super().__init__(name, key_size, value_size)
        self.log2_pair_size = int(log2(self.pair_size))
        self.pair_bsize = self.pair_size * WORD_SIZE
        self.log2_pair_bsize = int(log2(self.pair_bsize))

    def get_next_pair(self, tran: Transition, curr_pair: str, regs: list) -> Tuple[Transition, str]:
        tran.writeAction(f"addi {curr_pair} {curr_pair} {self.pair_bsize}")
        return tran, curr_pair

    def get_pair(self, tran: Transition, key: str, addr_reg: str, regs: list) -> Transition:
        tran.writeAction(f"move {self.meta_data_offset}(X7) {regs[0]} 0 {WORD_SIZE}")
        tran.writeAction(f"lshift {key} {addr_reg} {self.log2_pair_size + LOG2_WORD_SIZE}")
        tran.writeAction(f"add {addr_reg} {regs[0]} {addr_reg}")
        return tran

    def generate_partitions(self, tran: Transition, num_partitions: int, part_arry_base: str):
        pass
    
class IntermediateKeyValueSet(KeyValueSetTemplate):
    '''
    Example implementation of an non-materialized key value set for intermediate output of kv_map.
    '''

    def __init__(self, name: str, key_size: int, value_size: int):
        super().__init__(name, key_size, value_size)

    def get_next_pair(self, tran: Transition, curr_pair: str, regs: list) -> Tuple[Transition, str]:
        pass

    def get_pair(self, tran: Transition, key: str, addr_reg: str, regs: list) -> Transition:
        pass
    
    def generate_partitions(self, tran: Transition, num_partitions: int, part_arry_base: str):
        pass


def GeneratePageRankMapShuffleReduceEFA(PART_PARM) -> EFA:

    input_kvset = OneDimKeyValueSet("Input", key_size=1, value_size=3)
    input_kvset.set_meta_data(size=1, offset=0)

    inter_kvset = IntermediateKeyValueSet("Test intermediate", key_size=1, value_size=1)

    output_kvset = OneDimKeyValueSet("Output", key_size=1, value_size=1)
    output_kvset.set_meta_data(size=1, offset=8)

    '''
    Initialize the map reduce task. The following parameters are required:
        task_name:      name of the task, unique for each task
        num_workers:    number of updown lanes used in this task
        partition_parm: parameter controlling the number of partitions each level of hierarchy has (optional), default is 1
        enable_cache:   enable cache for the kv_merge() function (optional), default is False
        lm_mode:        scratchpad addressing mode, determines the value in X7 (optional), default is 1
        debug_flag:     enable debug print (optional), default is False
    '''
    pagerankMSR = PagerankMapShuffleReduce(task_name="pr", meta_data_offset=64, debug_flag=False, partition_parm=PART_PARM)
    # Setup the input and output key value set. 
    pagerankMSR.set_input_kvset(input_kvset)
    pagerankMSR.set_intermediate_kvset(inter_kvset)
    pagerankMSR.set_output_kvset(output_kvset)
    # If kv_merge() is used, the cache must be enabled and the cache size must be set.
    pagerankMSR.setup_cache(cache_offset=1024, num_entries=256, entry_size=2, ival=0xffffffffffffffff)
    # Set the maximum number of map and reduce threads concurrently running on each lane. Should be less than the max hardware threads supported.
    pagerankMSR.set_max_thread_per_lane(max_map_th_per_lane=16, max_reduce_th_per_lane=230)

    '''
    Entry event transition to be triggered by the top program. Updown program starts from here.
      operands
      OB_0: Pointer to the partition array (64-bit DRAM address)
      OB_1: Number of lanes
      OB_2: Pointer to inKVMap (64-bit DRAM address)
      OB_3: Pointer to outKVMap (64-bit DRAM address)
      OB_4: Top flag offset in the scratchpad (in Bytes)
    '''
    top_flag_addr = "UDPR_0"
    temp_val = "UDPR_1"
    init_tran = pagerankMSR.state.writeTransition("eventCarry", pagerankMSR.state, \
        pagerankMSR.state, pagerankMSR.get_event_mapping('updown_init'))
    init_tran.writeAction(f"ev_update_2 UDPR_9 {pagerankMSR.get_event_mapping('map_shuffle_reduce')} 255 5")
    '''
    Send the entry event to UDKVMSR library to start the mapreduce task. The destination lane id is assume to be the first worker lane.
    The event requires the following operands:
        OB_0: Pointer to the partition array (64-bit DRAM address)
        The rest of OBs: Meta data for input and output kv set, will be stored in the scratchpad by UDKVMSR library initialization routine. 
                        Number of operands sent should be the same as the meta data size in the kv set.
                        The order should be input kv set meta data, followed by the output kv set meta data.
                        The data will be stored starting from the offset specified in the kv set.
    User must provides the continuation event for the UDKVMSR library to return to.
    '''
    init_tran.writeAction(f"sendops_wret UDPR_9 {pagerankMSR.get_event_mapping('updown_terminate')} X8 4 {temp_val}")
    init_tran.writeAction(f"movir {temp_val} 0")
    init_tran.writeAction(f"add OB_4 X7 {top_flag_addr}")
    init_tran.writeAction(f"move {temp_val} {0}({top_flag_addr}) 0 8")
    init_tran.writeAction("yield")

    '''
    User defined continuation event transition to be triggered when the mapreduce task finishes.
    '''
    term_tran = pagerankMSR.state.writeTransition("eventCarry", pagerankMSR.state, \
        pagerankMSR.state, pagerankMSR.get_event_mapping('updown_terminate'))
    term_tran.writeAction(f"mov_imm2reg {temp_val} 1")
    term_tran.writeAction(f"move {temp_val} {0}({top_flag_addr}) 0 8")
    term_tran.writeAction(f"print '[DEBUG][NWID %d] UDKVMSR pagerank program finishes, number of reduce tasks = %d, signal top at addr = %d(0x%x)' {'X0'} {'X8'} {top_flag_addr} {top_flag_addr}")
    term_tran.writeAction("yield_terminate")

    pagerankMSR.generate_udkvmsr_task()

    return pagerankMSR.efa


def GeneratePageRankMapShuffleReduceEFA_2p():
    return GeneratePageRankMapShuffleReduceEFA(PART_PARM=2)

def GeneratePageRankMapShuffleReduceEFA_4p():
    return GeneratePageRankMapShuffleReduceEFA(PART_PARM=4)

def GeneratePageRankMapShuffleReduceEFA_8p():
    return GeneratePageRankMapShuffleReduceEFA(PART_PARM=8)