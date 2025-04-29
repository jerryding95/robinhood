from typing import Tuple
from EFA_v2 import *
from abc import *
import sys
PROJ = "/scratch/yqwang/udgem5sim"
sys.path.append(f"{PROJ}/ext/updown/install/updown/libraries")

from EFA_v2 import Transition
from KVMapShuffleReduceTPL_basim import UDKeyValueMapShuffleReduceTemplate
from KeyValueSetTPL import KeyValueSetTemplate
from math import log2

WORD_SIZE = 8
LOG2_WORD_SIZE = 3

'''
Below is an naive map reduce example. The map function masks the input key by the number of workerand send it with input value to the reducer.
The reducer takes the intermediate key-value pairs and sums up all the values correspond to the same key.
To write a map reduce program using the template, one needs to implement the two abstract method, namely kv_map() and kv_reduce(),
instantiate the map reduce task, and set up the metadata required by the template using the provided helper functions.
'''
class TestMapShuffleReduce(UDKeyValueMapShuffleReduceTemplate):

    def kv_map(self, tran: Transition, key: str, values: list, map_ret_ev_label: str) -> int:
        dest_id = "UDPR_5"      # Register UDPR_5 stores the lane id where the intermediate kvmap will be sent to
        inter_key = "UDPR_6"    # Register UDPR_6 stores the intermediate key
        # user defined map code
        # tran.writeAction(f"movir {self.scratch[0]} 255")
        # tran.writeAction(f"beq {key}")
        # tran.writeAction(f"divi {key} {inter_key} {4}")

        # tran.writeAction(f"modi {key} {inter_key} {64}")
        tran.writeAction(f"addi {key} {inter_key} {0}")
        '''
        Helper function kv_emit() will compute the destination reduce lane id and
        send the intermediate key-value pair to the destination lane. It takes the following arguments:
            tran:       the current transition
            inter_key:  register name storing the intermediate key
            values:     list of register names storing the intermediate values
            dest_id:    register name to be stored the destination lane id. 
                        kv_emit() will compute the destination lane id from the kv_reduce_loc() function.
            scratch:    two additional scratch register names
        '''
        self.kv_emit(tran, inter_key, values, dest_id, self.scratch[0], self.scratch[1])
        if self.debug_flag:
            tran.writeAction(f"print '  map generate intermediate key = %d from key = %d' {inter_key} {key}")
        '''
        Helper function msr_return() is used to return from the user-defined map function to the UDKVMSR library.
        It takes the following arguments:
            tran:       the current transition
            ret_label:  the label of the return event
            operands:   operands to be sent back to the UDKVMSR library (optional), default is current event word
            cont_label: continuation event label for UDKVMSR (optional), default is the current event label
        '''
        self.msr_return_temp(tran, ret_label=map_ret_ev_label, temp_reg = self.scratch[0]) 
        tran.writeAction("yield")

        return self.in_kvpair_size # intermediate key value pair size (in words)


    def kv_reduce(self, tran: Transition, key: str, values: list, reduce_ret_ev_label: str, regs = [f"X{i}" for i in range(16, 32)]) -> Transition:
        # user defined reduce code
        '''
        Helper function for atomic operation using scratchpad. Requires kv_merge_op() to be implemented and cache enabled.
        Parameter:
            key:        name of the operand buffer entries/registers containing the key to the cache entry
            values:     name of the operand buffer entries/registers containing the value to be merged
            reduce_ret_ev_label:    return event label to the udkvmsr library
            regs:       scratch registers, by default is all the 16 general purposed registers
        '''

        pair_addr = regs[0]
        cached_values = [regs[1]]
        ev_word = regs[2]

        self.kv_merge(tran, key, values, reduce_ret_ev_label, regs)
        # ln_worker_matererialize_ret_ev_label = self.get_event_mapping("worker_materialize_ret")

        # tran = self.out_kvset.get_pair(tran, key, pair_addr, cached_values)
        # tran.writeAction(f"sendr2_dmlm_wret {pair_addr} {ln_worker_matererialize_ret_ev_label} {key} {values[0]} {self.scratch[0]}")
        # tran.writeAction(f"movir {pair_addr} 654321")
        # tran.writeAction(f"addi X2 {ev_word} 0")
        # tran.writeAction(f"evlb {ev_word} {reduce_ret_ev_label}")
        # tran.writeAction(f"sendr_wcont {ev_word} X2 {pair_addr} {pair_addr}")


        return

    def kv_merge_op(self, tran: Transition, in_key: str, in_values: list, old_values: list, regs: list) -> list:
        for in_val, old_val, result in zip(in_values, old_values, regs):
            tran.writeAction(f"add {in_val} {old_val} {result}")
        return regs

class OneDimKeyValueSet(KeyValueSetTemplate):
    '''
    Example implementation of an one dimensional key value set.
    '''

    def __init__(self, name: str, key_size: int, value_size: int, extension):
        super().__init__(name, key_size, value_size, extension)
        self.log2_pair_size = int(log2(self.pair_size))
        self.pair_bsize = self.pair_size * WORD_SIZE
        self.log2_pair_bsize = int(log2(self.pair_bsize))

    def get_next_pair(self, tran: Transition, curr_pair: str, regs: list) -> Tuple[Transition, str]:
        tran.writeAction(f"addi {curr_pair} {curr_pair} {self.pair_bsize}")
        return tran, curr_pair

    def get_pair(self, tran: Transition, key: str, addr_reg: str, regs: list) -> Transition:
        print(f"move {self.meta_data_offset}(X7) {regs[0]} 0 {WORD_SIZE}")
        tran.writeAction(f"move {self.meta_data_offset}(X7) {regs[0]} 0 {WORD_SIZE}")


        tran.writeAction(f"lshift {key} {addr_reg} {self.log2_pair_size + LOG2_WORD_SIZE}")
        tran.writeAction(f"add {addr_reg} {regs[0]} {addr_reg}")
        return tran

    def generate_partitions(self, tran: Transition, num_partitions: int, part_arry_base: str):
        pass


def lbTestEFA():

    TERM_FLAG_ADDR = 512

    input_kvset = OneDimKeyValueSet("Test input", key_size=1, value_size=1, extension = OneDimKeyValueSet.AvailableExtensions.lb_test)
    input_kvset.set_meta_data(size=2, offset=0)

    output_kvset = OneDimKeyValueSet("Test output", key_size=1, value_size=1, extension = OneDimKeyValueSet.AvailableExtensions.lb_test)
    output_kvset.set_meta_data(size=2, offset=16)

    '''
    Initialize the map reduce task. The following parameters are required:
        task_name:      name of the task, unique for each task
        num_workers:    number of updown lanes used in this task
        partition_parm: parameter controlling the number of partitions each level of hierarchy has (optional), default is 1
        enable_cache:   enable cache for the kv_merge() function (optional), default is False
        lm_mode:        scratchpad addressing mode, determines the value in X7 (optional), default is 1
        debug_flag:     enable debug print (optional), default is False
    '''
    testMSR = TestMapShuffleReduce(task_name="test", num_workers=64, partition_parm = 1, enable_cache = True, lm_mode = 1, debug_flag = False, extension = TestMapShuffleReduce.AvailableExtensions.lb_test)
    # Setup the input and output key value set. 
    testMSR.set_input_kvset(input_kvset)
    testMSR.set_output_kvset(output_kvset)
    # Reserve 4 words for UDKVMSR library storing its bookkeeping data. 
    testMSR.set_bookkeeping_ctrs(offset=64)
    # If kv_merge() is used, the cache must be enabled and the cache size must be set.
    testMSR.setup_cache(cache_offset=16384, num_entries=16, entry_size=2, ival=0xffffffffffffffff)
    # Set the maximum number of map and reduce threads concurrently running on each lane. Should be less than the max hardware threads supported.
    testMSR.set_max_thread_per_lane(max_map_th_per_lane=4, max_reduce_th_per_lane=10)

    '''
    Entry event transition to be triggered by the top program. Updown program starts from here.
      operands
      OB_0: Pointer to the partition array (64-bit DRAM address)
      OB_1: Pointer to inKVMap (64-bit DRAM address)
      OB_2: Input kvmap length
      OB_3: Pointer to outKVMap (64-bit DRAM address)
      OB_4: Output kvmap length (== number of unique keys in the inKBMap)
      OB_5: Pointer to interKVMap
    '''
    init_tran = testMSR.state.writeTransition("eventCarry", testMSR.state, \
        testMSR.state, testMSR.get_event_mapping('updown_init'))
    term_tran = testMSR.state.writeTransition("eventCarry", testMSR.state, \
        testMSR.state, testMSR.get_event_mapping('updown_terminate'))

    # init_tran.writeAction(f"send_dmlm_ld_wret OB_0 {testMSR.get_event_mapping('updown_terminate')} 8 UDPR_0")
    # init_tran.writeAction(f"yield")

    # for i in range(8):
    #     term_tran.writeAction(f"addi OB_{i} X16 0")

    # init_tran.writeAction(f"movir UDPR_0 0")
    # init_tran.writeAction(f"add OB_5 UDPR_0 OB_6")


    init_tran.writeAction(f"evii UDPR_9 {testMSR.get_event_mapping(testMSR.task)} 255 5")
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
    init_tran.writeAction(f"sendops_wret UDPR_9 {testMSR.get_event_mapping('updown_terminate')} OB_0 6 UDPR_0")
    init_tran.writeAction("movir UDPR_0 0")
    init_tran.writeAction(f"addi X7 UDPR_1 0")
    init_tran.writeAction(f"movrl UDPR_0 {TERM_FLAG_ADDR}(UDPR_1) 0 8")
    init_tran.writeAction("yield")


    # '''
    # User defined continuation event transition to be triggered when the mapreduce task finishes.
    # '''
    # term_tran = testMSR.state.writeTransition("eventCarry", testMSR.state, \
    #     testMSR.state, testMSR.get_event_mapping('updown_terminate'))

    term_tran.writeAction("movir UDPR_5 1")
    term_tran.writeAction(f"addi X7 UDPR_1 0")
    term_tran.writeAction(f"movrl UDPR_5 {TERM_FLAG_ADDR}(UDPR_1) 0 8")
    term_tran.writeAction("yieldt")

    testMSR.generate_udkvmsr_task()

    # print out the event mapping (for debugging)
    print("Event mapping: ", testMSR.event_map)

    return testMSR.efa
