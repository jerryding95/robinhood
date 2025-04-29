from typing import Tuple
from EFA_v2 import *
from math import log2, ceil
from Macro import *
from abc import abstractmethod, ABCMeta
from GlobalSync import *
from KeyValueSetTPL import *
from enum import Enum

WORD_SIZE           = 8
LOG2_WORD_SIZE      = int(log2(WORD_SIZE))
LANE_PER_UD         = 64
UD_PER_NODE         = 32
LOG2_LANE_PER_UD    = int(log2(LANE_PER_UD))
LOG2_UD_PER_NODE    = int(log2(UD_PER_NODE))

class UDKeyValueMapShuffleReduceTemplate(metaclass=ABCMeta):
    """
    UpDown KeyValue MapShuffleReduce Library

    Usage:
    1. Import the module into UpDown source code file.
        import os, sys
        sys.path.append("<UPDOWN_INSTALL_DIR>/updown/libraries")
        from KVMapShuffleReduceTPL import UDKeyValueMapShuffleReduceTemplate
    2. Extend the UDKeyValueMapShuffleReduceTemplate class and implement kv_map() and kv_reduce().
       (Optionally, overwrite key mapping functions for e.g. customized work distribution.)
    3. Instantiate the child UDMapShuffleReduce class and wrap in customized GenerateEFA() function to generate UpDown assembly code.

    Example:

    class ExampleUDKeyValueMapShuffleReduce(UDMapShuffleReduceTemplate):

        def kv_map(self, tran, key, values, ret_ev_label):
            # user defined map code
            return ...

        def kv_reduce(self, tran, key, values, ret_ev_label):
            # user defined reduce code
            return ...

    Example UpDown KVMSR programs can be find in updown/apps/msr_examples.
    """
    FLAG    = 1

    class AvailableExtensions(Enum):
        original = 0
        load_balancer = 1
        lb_test = 2

    def __init__(self, task_name, num_workers, partition_parm = 1, enable_cache = False, lm_mode = 1, debug_flag = False, extension = AvailableExtensions.original):
        '''
        Parameters
            task_name:      String label of the event to initialize the map reduce task.
            num_workers:    Number of the workers (UpDown lanes) allocated to this map reduce task.
            partition_parm: Parameter controlling the number of partitions assgined to each level of master.
                            (= paramter x the number of partitions in next level, base level = number of lane per updown), default is 1.
                            Should be the same as the parameter used to initialize the input key-value map.
                            Total number of partitions = num_workers * (partition_parm ** 3)
            enable_cache:   Whether enable the cache to merge Read-Modify-Write updates, default is False.
            lm_mode:        Local memory access mode, 0: X7 uses updown base, 1: X7 uses lane bank base, default is 1.
                            Please use the same mode as the updown machine configuration.
            debug_flag:     Flag to enable debug print, default is False.
        '''
        self.extension = extension

        print(f"extention: {self.extension}, {self.extension.__class__}, {self.extension == self.AvailableExtensions.lb_test}")
        if self.extension == self.AvailableExtensions.load_balancer or self.extension == self.AvailableExtensions.lb_test:
            self._finish_flag = -1
            self._map_finish_flag = -2
            self._map_flag = -3
            self._reduce_flag = -4
            self.intermediate_kvpair_size = 2
            print(f"extension set")
            
            print(f"finish flag: {self._finish_flag}")

        self.task = task_name
        self.efa = EFA([])
        self.efa.code_level = 'machine'

        self.state = State()
        self.efa.add_initId(self.state.state_id)
        self.efa.add_state(self.state)

        self.num_workers = num_workers
        self.num_lane_per_ud = min(self.num_workers, LANE_PER_UD)
        self.num_uds = ceil(self.num_workers / LANE_PER_UD)
        self.num_ud_per_node = min(self.num_uds, UD_PER_NODE)
        self.num_nodes = ceil(self.num_uds / UD_PER_NODE)

        self.num_partitions = self.num_workers * (partition_parm ** 3)
        self.part_pram = partition_parm

        self.lm_mode = lm_mode
        self.enable_cache = enable_cache
        self.debug_flag = debug_flag
        self.print_level = 0
        self.send_temp_reg_flag = True
        print(f"Initialize MapShuffleReduce task {self.task} - number of workers = {self.num_workers}, number of updowns = {self.num_uds}, number of nodes = {self.num_nodes}")

        self.threads = {}
        self.event_map = {}
        self.num_events = 0
        self.get_event_mapping(self.task)

        # Shared register names for debugging reasons
        # To be reused by threads/events such that
        # register names match functioning of the registers
        self.part_array_ptr = "UDPR_0"
        self.num_part_issued    = "UDPR_1"
        self.part_array_stride  = "UDPR_2"
        self.num_map_gen    = "UDPR_3"
        self.part_stride    = "UDPR_4"
        self.ev_word    = "UDPR_14"
        self.saved_cont = "UDPR_15"
        self.scratch = ["UDPR_12", "UDPR_13"]

        # New added fixed scratchpad offset
        self.intermediate_cache_size = 3 * 1024 * WORD_SIZE
        self.claim_queue_size = 1024 * WORD_SIZE
        self.ob_cache_offset = 65536 - WORD_SIZE*9                                  #   for send with more than 3 operands
        self.intermediate_cache_offset = self.ob_cache_offset - self.intermediate_cache_size
        self.claim_queue_offset = self.intermediate_cache_offset - self. claim_queue_size
        self.intermediate_ptr_offset = 32
        self.push_key_cont_offset = 40
        self.assert_claimed_key_offset = 48
        self.claimed_key_ptr_offset = 56
        self.materializing_metadata_offset = 512
        self.local_tid_cache_offset = 128
        print(f"ob_cache_offset: {self.ob_cache_offset}, intermediate_ptr_offset: {self.intermediate_ptr_offset}")
        print(f"{self.debug_flag}")


    '''
    Helper functions
    '''
    def get_event_mapping(self, label):
        '''
        Given a string label, retrieve the corresponding event id.
        If the event label does not exist in the mapping, add it to the mapping and return the event id.
        Parameter
            label:          string label
        Ouput
            the corresponding event id (integer) mapped to the input label
        '''

        ev_label = f"{self.task}_{label}"
        if ev_label not in self.event_map:
            self.event_map[ev_label] = self.num_events
            self.num_events += 1
        return self.event_map[ev_label]

    def __get_lm_base(self, tran: Transition, reg = "") -> str:
        if self.lm_mode:
            if not reg:
                return "X7"
            else:
                tran.writeAction(f"addi X7 {reg} 0")
                return reg
        else:
            if not reg: reg = self.scratch[0]
            tran.writeAction(f"andi NWID {reg} {0x3F}")
            tran.writeAction(f"sli  {reg} {reg} {16}")
            # tran.writeAction(f"lshift_and_imm NWID {reg} 16 {0x3f << 16}")
            tran.writeAction(f"add {reg} X7 {reg}")
            return reg
    



    ##############################################################################
    '''
    Setting Functions exposed to user, to be called to setup parameters
    '''
    def set_max_thread_per_lane(self, max_map_th_per_lane, max_reduce_th_per_lane):
        self.max_map_th_per_lane = max_map_th_per_lane
        self.max_reduce_th_per_lane = max_reduce_th_per_lane

    def set_input_kvset(self, kvset: KeyValueSetTemplate):
        '''
        Set up the input key-value map's metadata, the kvmap is stored in DRAM.
        Parameters
            kvset:  Instance of key-value set. Input to UDKVMSR.
        '''

        self.in_kvset = kvset
        self.in_kvset_offset = kvset.meta_data_offset
        self.in_kvset_meta_size = kvset.meta_data_size
        self.in_kvpair_size = kvset.pair_size
        self.log2_in_kvpair_size = ceil(log2(self.in_kvpair_size))
        if hasattr(kvset, "get_partition"):
            self.in_kvset_linear = True
        if (2 ** self.log2_in_kvpair_size) == self.in_kvpair_size:
            self.in_kvpair_pow2 = True
        else:
            self.in_kvpair_pow2 = False
            print("Warning: Input key value pair size is not a power of 2. This would impede the performance of UDKVMSR.")
            print(f"       Suggest to increase it to the next power of two, i.e., {2 ** self.log2_in_kvpair_size}")
        print(f"Set up {kvset.name} kvmap - meta_data_offset: {kvset.meta_data_offset},  meta_data_size: {kvset.meta_data_size}, pair_size: {kvset.pair_size}, log2 pair_size: {self.log2_in_kvpair_size}")

    def set_output_kvset(self, kvset: KeyValueSetTemplate):
        '''
        Set up the output key-value map's metadata, the kvmap is stored in DRAM.
        Parameters
            kvset:  Instance of key-value set. Output of UDKVMSR.
        '''

        self.out_kvset = kvset
        self.out_kvset_offset = kvset.meta_data_offset
        self.out_kvset_meta_size = kvset.meta_data_size
        self.out_kvpair_size = kvset.pair_size
        self.log2_out_kvpair_size = ceil(log2(self.out_kvpair_size))
        if (2 ** self.log2_out_kvpair_size) == self.out_kvpair_size:
            self.out_kvpair_pow2 = True
        else:
            self.out_kvpair_pow2 = False
            print("Warning: Output key value pair size is not a power of 2. This would impede the performance of UDKVMSR.")
            print(f"       Suggest to increase it to the next power of two, i.e., {2 ** self.log2_out_kvpair_size}")
        print(f"Set up {kvset.name} kvmap - meta_data_offset: {kvset.meta_data_offset},  meta_data_size: {kvset.meta_data_size}, pair_size: {kvset.pair_size}, log2 pair_size: {self.log2_out_kvpair_size}")

        # if self.extension == self.AvailableExtensions.load_balancer or self.extension == self.AvailableExtensions.lb_test:
        #     self.intermediate_kvset = KeyValueSetTemplate()
            # TODO: define intermediate kv_set

    def set_bookkeeping_ctrs(self, offset):
        '''
        Setup the buffer for UDKVMSR's metadata, requires the Bytes offset to lane private bank base, meta data are per lane (worker) private.
        Minimum size of the buffer is 32 Bytes / 4 words.
        Parameters
            ctr_base_offset:    offset to the local bank for bookkeeping data
        '''

        self.map_ctr_offset = offset
        self.reduce_ctr_offset = self.map_ctr_offset + WORD_SIZE
        self.cond_save_offset = self.reduce_ctr_offset + WORD_SIZE
        self.num_reduce_th_offset = self.cond_save_offset + WORD_SIZE
            

    def setup_cache(self, cache_offset, num_entries, entry_size, enable_cache=True, ival=0xffffffffffffffff):
        '''
        If the reduce function involves read-modify-write to a DRAM location, initiates a per-lane-private software write through
        cache to merge updates to the same location (i.e. intermediate kvpair with the same key)
        Parameters
            cache_offset:   per lane local cache base (Bytes offset relative to the local bank, limited to the 64KB bank size)
            num_entries:    number of entries for each of lane-private cache segment
            entry_size:     the size of a cache entry in bytes
            enable_cache:   whether enable the cache
            ival:           default value for invalid cache entry
        '''

        self.enable_cache = enable_cache
        self.cache_offset = cache_offset
        self.cache_size = num_entries
        self.cache_entry_bsize = entry_size << LOG2_WORD_SIZE
        self.cache_entry_size = entry_size
        self.INACTIVE_MASK_SHIFT = 63
        self.INACTIVE_MASK = (1 << self.INACTIVE_MASK_SHIFT)
        self.cache_ival = ival | self.INACTIVE_MASK

        if self.extension == self.AvailableExtensions.lb_test:
            self.materialize_kv_cache_offset = self.cache_offset + self.cache_size * self.cache_entry_size * WORD_SIZE
            self.materialize_kv_cache_size = 512 * 2 * WORD_SIZE

    ##############################################################################




    ##############################################################################
    '''
    Main function exposed to user, to be called to write UDKVMSR UpDownprograms
    '''
    def generate_udkvmsr_task(self):
        self.__gen_init_scratchpad()
        self.__gen_masters()
        self.__gen_map_thread()
        self.__gen_reduce_thread()

        if self.extension == self.AvailableExtensions.lb_test:
            self.__gen_helper_worker_thread()
            self.__gen_assign_shuffle_dest_thread()
            self.__gen_worker_update_claimed_key_thread()
            self.__gen_worker_assert_claimed_key_thread()
        else:
            self.__gen_global_sync()
        return
 
    ##############################################################################




    ##############################################################################

    '''
    Initializing local scratchpad, generating local counters
    '''

    def __gen_init_scratchpad(self):
        '''
        Generate the initialization code for the scratchpad memory.
        '''
        self.__gen_init_scratchpad_global_th()
        self.__gen_init_scratchpad_node_th()
        self.__gen_init_scratchpad_updown_th()
        self.__gen_init_scratchpad_lane_th()
        
        return
    ##############################################################################


    ##############################################################################
    '''
    Thread/Event functions initializing scratchpad at each level of the structure
    '''
    def __gen_init_scratchpad_global_th(self):
        '''
        Event:      UDKVMSR entry point, start initializing scratchpad
        Operands:   OB_0: partitions array
                    OB_1 ~ OB_n: input and output key-value set metadata
        '''
        node_sp_init_ev_label  = self.get_event_mapping(f"init_sp_node")
        global_master_ev_label = self.get_event_mapping(f"global_master")

        tran = self.state.writeTransition("eventCarry", self.state, self.state, self.get_event_mapping(self.task))

        part_array_ptr = self.part_array_ptr    # UDPR_0                thread reg
        num_finished = "UDPR_10"                # UDPR_10               thread reg
        saved_cont = self.saved_cont            # UDPR_15               thread reg

        scratch = self.scratch                  # UDPR_12 & UDPR_13     local reg
        ev_word = self.ev_word                  # UDPR_14               local reg

        if self.extension == self.AvailableExtensions.load_balancer or self.extension == self.AvailableExtensions.lb_test:
            '''
            Additional operand: OB_{n+1} intermediate key-value set metadata
            '''

            glb_mstr_push_key_ev_label = self.get_event_mapping(f"master_global_push_key")

            num_keys = "UDPR_9"                 #                       thread reg
            intermediate_ptr = 'UDPR_3'         #                       thread reg

            tran.writeAction(f"addi OB_4 {num_keys} 0")
            tran.writeAction(f"addi OB_{1 + self.in_kvset_meta_size + self.out_kvset_meta_size} {intermediate_ptr} 0")

            # tran.writeAction(f"divi {num_keys} {scratch[0]} 4")
            tran.writeAction(f"sli {num_keys} {scratch[0]} {LOG2_WORD_SIZE}")
            tran.writeAction(f"add {scratch[0]} {intermediate_ptr} UDPR_4")


            # tran.writeAction(f"sli {num_keys} {num_keys} {LOG2_WORD_SIZE}")
            # tran.writeAction(f"add {num_keys} {intermediate_ptr} UDPR_4")
            # tran.writeAction(f"sri {num_keys} {num_keys} {LOG2_WORD_SIZE}")

            tran.writeAction(f"movir UDPR_0 0")
            tran.writeAction(f"addi X2 UDPR_1 0")
            tran.writeAction(f"evlb UDPR_1 {glb_mstr_push_key_ev_label}")
            # tran.writeAction(f"add UDPR_0 UDPR_1 OB_{self.in_kvset_meta_size + self.out_kvset_meta_size + 2}")


        if self.debug_flag:
            tran.writeAction(f"print ' '")
            tran.writeAction(f"print '[DEBUG][NWID %d] Event <kvmsr_global_sp_init> ev_word=%d' {'X0'} {'EQT'}")
            tran.writeAction(f"print '[DEBUG][NWID %d] Operands: part_array = %d(0x%x)' {'X0'} {'OB_0'} {'OB_0'}")
            tran.writeAction(f"print '[DEBUG][NWID %d] Operands: in_kvset = %d(0x%x)' {'X0'} {'OB_1'} {'OB_1'}")
            tran.writeAction(f"print '[DEBUG][NWID %d] Operands: out_kvset = %d(0x%x)' {'X0'} {'OB_3'} {'OB_3'}")
        tran.writeAction(f"addi OB_0 {part_array_ptr} 0")   # save the base of global partition array
        tran.writeAction(f"addi X1 {saved_cont} 0")
        tran = set_ev_label(tran, ev_word, node_sp_init_ev_label, new_thread = True)

        if self.extension == self.AvailableExtensions.lb_test:
            lm_reg = self.__get_lm_base(tran, scratch[0])
            tran.writeAction(f"movir {scratch[1]} {self.ob_cache_offset}")
            tran.writeAction(f"add {lm_reg} {scratch[1]} UDPR_2")
            tran = broadcast(tran, ev_word, self.num_nodes, global_master_ev_label, \
                (LOG2_LANE_PER_UD + LOG2_UD_PER_NODE), ["OB_1", "OB_2", "OB_3", "OB_4", "UDPR_4", "UDPR_1"], \
                scratch, 'any', self.send_temp_reg_flag, ob_buff_addr = "UDPR_2")
        else:
            tran = broadcast(tran, ev_word, self.num_nodes, global_master_ev_label, \
                (LOG2_LANE_PER_UD + LOG2_UD_PER_NODE), f"OB_1 {self.in_kvset_meta_size + self.out_kvset_meta_size}", scratch, 'ops', self.send_temp_reg_flag)
        

        tran.writeAction(f"mov_imm2reg {num_finished} 0")
        tran.writeAction("yield")
        return


    def __gen_init_scratchpad_node_th(self):
        node_sp_init_ev_label  = self.get_event_mapping(f"init_sp_node")    # Already initialized
        node_sp_init_fin_ev_label  = self.get_event_mapping(f"init_sp_node_fin")

        node_sp_init_tran   = self.state.writeTransition("eventCarry", self.state, self.state, node_sp_init_ev_label)
        node_sp_init_fin_tran   = self.state.writeTransition("eventCarry", self.state, self.state, node_sp_init_fin_ev_label)

        self.__gen_init_scratchpad_node(node_sp_init_tran)
        self.__gen_init_scratchpad_node_fin(node_sp_init_fin_tran)

        return

    def __gen_init_scratchpad_node(self, tran):
        '''
        Event:      Initialize node scratchpad
        Operands:   OB_0 ~ OB_4: input and output key-value set metadata
        '''
        node_sp_init_fin_ev_label  = self.get_event_mapping(f"init_sp_node_fin")    # Already initialized
        ud_sp_init_ev_label    = self.get_event_mapping(f"init_sp_ud")

        scratch = self.scratch                  # UDPR_12 & UDPR_13,    local reg
        ev_word = self.ev_word                  # UDPR_14,              local reg
        saved_cont = self.saved_cont            # UDPR_15,              thread reg
        num_finished    = "UDPR_10"             #                       thread reg

        if self.debug_flag and self.print_level > 3:
            tran.writeAction(f"print ' '")
            tran.writeAction(f"print '[DEBUG][NWID %d] Event <kvmsr_node_sp_init> ev_word=%d' {'X0'} {'EQT'}")
        tran.writeAction(f"addi X1 {saved_cont} 0")
        tran = set_ev_label(tran, ev_word, ud_sp_init_ev_label, new_thread = True)
        ob_len = self.in_kvset_meta_size + self.out_kvset_meta_size + 2 \
            if self.extension == self.AvailableExtensions.lb_test \
            else self.in_kvset_meta_size + self.out_kvset_meta_size
        tran = broadcast(tran, ev_word, self.num_ud_per_node, node_sp_init_fin_ev_label, \
            (LOG2_LANE_PER_UD), f"OB_0 {ob_len}", scratch, 'ops', self.send_temp_reg_flag)
        tran.writeAction(f"mov_imm2reg {num_finished} 0")
        tran.writeAction("yield")
        return

    def __gen_init_scratchpad_node_fin(self, tran):
        '''
        Event:      Node updown scratchpad initialized return event
        Operands:   OB_0 ~ OB_1: sender event word
        '''
        num_finished    = "UDPR_10"     # Already initialized           thread reg
        scratch_0 = self.scratch[0]     #                               local reg

        continue_label = "continue"

        if self.debug_flag and self.print_level > 3:
            tran.writeAction(f"print ' '")
            tran.writeAction(f"print '[DEBUG][NWID %d] Event <kvmsr_node_sp_init_fin> ev_word=%d num_finished=%d' {'X0'} {'EQT'} {num_finished}")
        tran.writeAction(f"addi {num_finished} {num_finished} 1")
        tran.writeAction(f"blti {num_finished} {self.num_ud_per_node} {continue_label}")
        tran.writeAction(format_pseudo("sendr_reply X0 X16", scratch_0, self.send_temp_reg_flag))
        tran.writeAction("yield_terminate")
        tran.writeAction(f"{continue_label}: yield")
        return
    

    def __gen_init_scratchpad_updown_th(self):
        ud_sp_init_ev_label    = self.get_event_mapping(f"init_sp_ud")      # Already initialized
        ud_sp_init_fin_ev_label    = self.get_event_mapping(f"init_sp_ud_fin")

        ud_sp_init_tran     = self.state.writeTransition("eventCarry", self.state, self.state, ud_sp_init_ev_label)
        ud_sp_init_fin_tran = self.state.writeTransition("eventCarry", self.state, self.state, ud_sp_init_fin_ev_label)

        self.__gen_init_scratchpad_updown(ud_sp_init_tran)
        self.__gen_init_scratchpad_updown_fin(ud_sp_init_fin_tran)

        return

    def __gen_init_scratchpad_updown(self, tran):
        '''
        Event:      Initialize updown scratchpad
        Operands:   OB_0 ~ OB_n: input and output key-value set metadata
        '''
        ud_sp_init_fin_ev_label    = self.get_event_mapping(f"init_sp_ud_fin")  # Already initialized
        lane_sp_init_ev_label  = self.get_event_mapping(f"init_sp_lane")

        scratch = self.scratch                  # UDPR_12 & UDPR_13     local reg
        ev_word = self.ev_word                  # UDPR_14               local reg
        saved_cont = self.saved_cont            # UDPR_15               thread reg
        num_finished    = "UDPR_10"             #                       thread reg
        num_ln_per_ud   = "UDPR_11"             #                       thread reg

        if self.debug_flag and self.print_level > 3:
            tran.writeAction(f"print ' '")
            tran.writeAction(f"print '[DEBUG][NWID %d] Event <kvmsr_updown_sp_init> ev_word=%d' {'X0'} {'EQT'}")
        tran.writeAction(f"addi X1 {saved_cont} 0")
        tran = set_ev_label(tran, ev_word, lane_sp_init_ev_label, new_thread = True)
        tran.writeAction(f"mov_imm2reg {num_ln_per_ud} {self.num_lane_per_ud}")
        ob_len = self.in_kvset_meta_size + self.out_kvset_meta_size + 2 \
            if self.extension == self.AvailableExtensions.lb_test \
            else self.in_kvset_meta_size + self.out_kvset_meta_size
        tran = broadcast(tran, ev_word, num_ln_per_ud, ud_sp_init_fin_ev_label, 0, \
            f"OB_0 {ob_len}", scratch, 'ops', self.send_temp_reg_flag)
        tran.writeAction(f"mov_imm2reg {num_finished} 0")
        tran.writeAction("yield")
        return

    def __gen_init_scratchpad_updown_fin(self, tran):
        '''
        Event:      Updown lane scratchpad initialized return event
        Operands:   OB_0 ~ OB_1: sender event word
        '''
        num_finished    = "UDPR_10"     # Already initialized       thread reg
        num_ln_per_ud   = "UDPR_11"     # Already initialized       thread reg
        scratch_0 = self.scratch[0]     #                           local reg
        
        continue_label = "continue"

        if self.debug_flag and self.print_level > 3:
            tran.writeAction(f"print ' '")
            tran.writeAction(f"print '[DEBUG][NWID %d] Event <kvmsr_updown_sp_init_fin> ev_word=%d num_finished=%d' {'X0'} {'EQT'} {num_finished}")
        tran.writeAction(f"addi {num_finished} {num_finished} 1")
        tran.writeAction(f"blt {num_finished} {num_ln_per_ud} {continue_label}")
        tran.writeAction(format_pseudo(f"sendr_reply X0 X16", scratch_0, self.send_temp_reg_flag))
        tran.writeAction("yield_terminate")
        tran.writeAction(f"{continue_label}: yield")
        return

    
    def __gen_init_scratchpad_lane_th(self):
        '''
        Event:      Initialize lane scratchpad
        Operands:   OB_0: number of workers
        Operands:   OB_0 ~ OB_n: input and output key-value set metadata
        '''
        lane_sp_init_ev_label  = self.get_event_mapping(f"init_sp_lane")    # Already initialized

        tran = self.state.writeTransition("eventCarry", self.state, self.state, lane_sp_init_ev_label)

        scratch_0 = self.scratch[0]                  # UDPR_12

        if self.debug_flag and self.print_level > 3:
            tran.writeAction(f"print ' '")
            tran.writeAction(f"print '[DEBUG][NWID %d] Event <kvmsr_lane_sp_init> ev_word=%d' {'X0'} {'EQT'}")
        tran = self.__init_updown(tran)
        tran.writeAction(format_pseudo(f"sendr_reply X0 X16", scratch_0, self.send_temp_reg_flag))
        tran.writeAction("yield_terminate")
        return

    def __init_updown(self, tran):

        scratch = self.scratch

        tran.writeAction("mov_imm2reg UDPR_0 0")
        # Initialize termination counters (private per worker lane)
        lm_base = self.__get_lm_base(tran)
        tran.writeAction(f"addi {lm_base} UDPR_1 0")
        tran.writeAction(f"move UDPR_0 {self.map_ctr_offset}(UDPR_1) 0 8")
        tran.writeAction(f"move UDPR_0 {self.reduce_ctr_offset}(UDPR_1) 0 8")
        for i in range(self.in_kvset_meta_size):
            tran.writeAction(f"move {f'OB_{i}'} {self.in_kvset_offset + i * WORD_SIZE}(UDPR_1) 0 8")
        for i in range(self.out_kvset_meta_size):
            tran.writeAction(f"move {f'OB_{self.in_kvset_meta_size + i}'} {self.out_kvset_offset + i * WORD_SIZE}(UDPR_1) 0 8")

        if self.extension == self.AvailableExtensions.lb_test:
            tran.writeAction(f"movrl OB_{self.in_kvset_meta_size + self.out_kvset_meta_size} {self.intermediate_ptr_offset}(UDPR_1) 0 8")
            tran.writeAction(f"movrl OB_{self.in_kvset_meta_size + self.out_kvset_meta_size + 1} {self.push_key_cont_offset}(UDPR_1) 0 8")

            tran.writeAction(f"movir {scratch[0]} {self.materializing_metadata_offset}")
            tran.writeAction(f"add UDPR_1 {scratch[0]} {scratch[0]}")
            tran.writeAction(f"movir {scratch[1]} {self.materialize_kv_cache_offset}")
            tran.writeAction(f"add UDPR_1 {scratch[1]} {scratch[1]}")
            tran.writeAction(f"movrl {scratch[1]} 0({scratch[0]}) 1 {WORD_SIZE}")
            tran.writeAction(f"movrl {scratch[1]} 0({scratch[0]}) 1 {WORD_SIZE}")
            tran.writeAction(f"movir {scratch[1]} 1")
            tran.writeAction(f"movrl {scratch[1]} 0({scratch[0]}) 1 {WORD_SIZE}")

        # Initialize the per lane private cache in scratchpad to merge Read-Modify-Write updates and ensure TSO
        if self.enable_cache:
            cache_init_loop_label = "init_cache_loop"
            ival        = "UDPR_0"
            cache_base  = "UDPR_1"
            init_ctr    = "UDPR_2"
            lm_base     = "UDPR_3"
            cache_size  = "UDPR_4"
            tran.writeAction(f"mov_imm2reg {ival} {(1<<21)-1}")
            tran.writeAction(f"sli {ival} {ival} {self.INACTIVE_MASK_SHIFT-20}")
            # print(f"Initialize lane {n}'s cache in scratchpad memory")
            lm_base = self.__get_lm_base(tran, lm_base)
            tran.writeAction(f"addi {lm_base} {cache_base} {self.cache_offset}")
            if self.debug_flag:
                tran.writeAction(f"print '[DEBUG][NWID %d] Initialize scratchpad cache base addr = %d(0x%x) initial value = %d' {'X0'} {cache_base} {cache_base} {ival}")
            tran.writeAction(f"mov_imm2reg {init_ctr} 0")
            tran.writeAction(f"movir {cache_size} {self.cache_size}")       # Added by: Jerry
            tran.writeAction(f"{cache_init_loop_label}: movwrl {ival} {cache_base}({init_ctr},1,{int(log2(self.cache_entry_size))})")
            tran.writeAction(f"blt {init_ctr} {cache_size} {cache_init_loop_label}")    # Modified by: Jerry

        return tran

    ##############################################################################




    ##############################################################################
    '''
    Main procedure function generating masters
    '''
    def __gen_masters(self):
        self.__gen_global_master_th()
        self.__gen_node_master_th()
        self.__gen_updown_master_th()
        self.__gen_lane_master_th()
    ##############################################################################


    ##############################################################################
    '''
    Thread/Event functions generating masters at each level of the structure
    '''


    ###     Global master thread
    ###     Same thread as `__gen_init_scratchpad_global_th`
    def __gen_global_master_th(self):
        global_master_ev_label = self.get_event_mapping(f"global_master")   # Already initialized
        glb_mstr_loop_ev_label = self.get_event_mapping(f"master_global")

        glb_mstr_init_tran = self.state.writeTransition("eventCarry", self.state, self.state, global_master_ev_label)
        glb_mstr_loop_tran   = self.state.writeTransition("eventCarry", self.state, self.state, glb_mstr_loop_ev_label)

        self.__gen_global_master_init(glb_mstr_init_tran)
        self.__gen_global_master_loop(glb_mstr_loop_tran)

        if self.extension == self.AvailableExtensions.load_balancer:
            glb_mstr_set_part_ev_label = self.get_event_mapping(f"master_global_set_partition")
            glb_mstr_claim_work_ev_label = self.get_event_mapping(f"master_global_claim_work")
            glb_mstr_claim_work_send_map_label = self.get_event_mapping(f"master_global_claim_work_send_map")
            glb_mstr_claim_work_send_reduce_label = self.get_event_mapping(f"master_global_claim_work_send_reduce")
            
            glb_mstr_set_part_tran = self.state.writeTransition("eventCarry", self.state, self.state, glb_mstr_set_part_ev_label)
            glb_mstr_claim_work_tran = self.state.writeTransition("eventCarry", self.state, self.state, glb_mstr_claim_work_ev_label)
            send_map_tran = self.state.writeTransition("eventCarry", self.state, self.state, glb_mstr_claim_work_send_map_label)
            send_reduce_tran = self.state.writeTransition("eventCarry", self.state, self.state, glb_mstr_claim_work_send_reduce_label)

            self.__gen_global_master_set_part(glb_mstr_set_part_tran)
            self.__gen_global_master_claim_work(glb_mstr_claim_work_tran)
            self.__gen_global_master_claim_work_send_map(send_map_tran)
            self.__gen_global_master_claim_work_send_reduce(send_reduce_tran)

        elif self.extension == self.AvailableExtensions.lb_test:
            glb_mstr_set_part_ev_label = self.get_event_mapping(f"master_global_set_partition")
            glb_mstr_claim_work_ev_label = self.get_event_mapping(f"master_global_claim_work")
            glb_mstr_claim_work_send_reduce_label = self.get_event_mapping(f"master_global_claim_work_send_reduce")
            glb_mstr_push_key_ev_label = self.get_event_mapping(f"master_global_push_key")
            glb_mstr_push_key_ret_ev_label = self.get_event_mapping(f"master_global_push_key_ret")
            
            glb_mstr_set_part_tran = self.state.writeTransition("eventCarry", self.state, self.state, glb_mstr_set_part_ev_label)
            glb_mstr_claim_work_tran = self.state.writeTransition("eventCarry", self.state, self.state, glb_mstr_claim_work_ev_label)
            send_reduce_tran = self.state.writeTransition("eventCarry", self.state, self.state, glb_mstr_claim_work_send_reduce_label)
            push_key_tran = self.state.writeTransition("eventCarry", self.state, self.state, glb_mstr_push_key_ev_label)
            push_key_ret_tran = self.state.writeTransition("eventCarry", self.state, self.state, glb_mstr_push_key_ret_ev_label)

            self.__gen_global_master_set_part(glb_mstr_set_part_tran)
            self.__gen_global_master_claim_work(glb_mstr_claim_work_tran)
            self.__gen_global_master_claim_work_send_reduce(send_reduce_tran)
            self.__gen_blobal_master_push_key(push_key_tran)
            self.__gen_global_master_push_key_ret(push_key_ret_tran)

        return

    def __gen_global_master_init(self, tran):
    
        '''
        Event:      Global master initializing event, returned from Node scratchpad initializing event
        Operands:   OB_0 ~ OB_1: sender event word
        '''
        nd_mstr_init_ev_label = self.get_event_mapping(f"init_master_node")
        
        init_fin_label = "global_init_finish"
        glb_mstr_loop_label = "glb_master_loop"
        continue_label = "continue"

        # Returned from Node scratchpad initializing event
        # determing whether all node scratchpads finish initializing

        num_finished = "UDPR_10"                # UDPR_10               thread reg -> local reg

        if self.debug_flag and self.print_level > 3:
            tran.writeAction(f"print ' '")
            tran.writeAction(f"print '[DEBUG][NWID %d] Event <kvmsr_global_master_init> ev_word=%d num_finished=%d' {'X0'} {'EQT'} {num_finished}")
        tran.writeAction(f"addi {num_finished} {num_finished} 1")
        tran.writeAction(f"blti {num_finished} {self.num_nodes} {continue_label}")
        tran.writeAction(f"jmp {init_fin_label}")
        tran.writeAction(f"{continue_label}: yield")

        # All node scratchpads finish initializing
        # Start global master initializing

        if self.extension == self.AvailableExtensions.load_balancer:
            glb_mstr_loop_ev_label = self.get_event_mapping(f"master_global")   # Already initialized!
            glb_mstr_set_part_ev_label = self.get_event_mapping("master_global_set_partition")  # Already initialized
            glb_mstr_claim_work_ev_label = self.get_event_mapping(f"master_global_claim_work")  # Already initialized
            
            part_array_ptr = self.part_array_ptr    # UDPR_0    Already initialized!    thread reg
            num_node_active = "UDPR_5"              #                                   thread reg
            ndid_stride     = "UDPR_6"              #                                   thread reg
            num_part_reg    = "UDPR_8"              #                                   thread reg
            partition_active = "UDPR_9"             #                                   thread reg
            intermediate_ptr = 'UDPR_11'            #                                   thread reg
            part_stride = self.part_stride          # UDPR_14                           thread reg -> local reg
            saved_cont = self.saved_cont            # UDPR_15,                          thread reg

            nd_mstr_nwid    = "UDPR_7"              #                                   local reg
            num_finished    = "UDPR_10"             #                                   local reg
            scratch = self.scratch                  # [UDPR_12, UDPR_13]                local reg
            ev_word = self.ev_word                  # UDPR_14                           local reg
            cont_word = "UDPR_12"                   #                                   local reg
            
            tran.writeAction(f"{init_fin_label}: movir {num_node_active} 0")
            tran.writeAction(f"movir {num_part_reg} {self.num_partitions}")
            tran.writeAction(f"movir {partition_active} 0")
            tran.writeAction(f"send_dmlm_ld_wret {part_array_ptr} {glb_mstr_set_part_ev_label} {'2'} {scratch[0]}")

            tran.writeAction(f"addi X2 {cont_word} 0")
            tran.writeAction(f"evlb {cont_word} {glb_mstr_claim_work_ev_label}")
            tran.writeAction(f"movir {ndid_stride} {self.num_ud_per_node * self.num_lane_per_ud}")
            tran.writeAction(f"muli {ndid_stride} {part_stride} {self.part_pram ** 2}")
            tran.writeAction(f"addi X0 {nd_mstr_nwid} 0")
            tran = set_ev_label(tran, ev_word, nd_mstr_init_ev_label, new_thread=True)

            tran.writeAction(f"{glb_mstr_loop_label}: ev {ev_word} {ev_word} {nd_mstr_nwid} {nd_mstr_nwid} 8")

            tran.writeAction(f"sendr_wret {ev_word} {glb_mstr_loop_ev_label} {cont_word} {ndid_stride} {scratch[0]}")
            tran.writeAction(f"add {ndid_stride} {nd_mstr_nwid} {nd_mstr_nwid}")
            tran.writeAction(f"addi {num_node_active} {num_node_active} 1")
            tran.writeAction(f"blti {num_node_active} {self.num_nodes} {glb_mstr_loop_label}")
            tran.writeAction("yield")

        elif self.extension == self.AvailableExtensions.lb_test:

            glb_mstr_loop_ev_label = self.get_event_mapping(f"master_global")   # Already initialized!
            glb_mstr_claim_work_ev_label = self.get_event_mapping(f"master_global_claim_work")  # Already initialized

            part_array_ptr = self.part_array_ptr            # UDPR_0    Already initialized!    thread reg -> local reg
            intermediate_ptr = 'UDPR_3'                     # UDPR_3                            thread reg
            num_node_active = "UDPR_5"                      # UDPR_5                            thread reg
            num_keys = "UDPR_9"                             # UDPR_9                            thread reg -> local reg
            part_ptr = "UDPR_10"                            # UDPR_10                           thread reg
            part_end_ptr = "UDPR_11"                        # UDPR_11                           thread reg
            saved_cont = self.saved_cont                    # UDPR_15   Already initialized!    thread reg
            
            part_array_stride = self.part_array_stride      # UDPR_2                            local reg
            part_stride = self.part_stride                  # UDPR_4                            local reg
            ndid_stride     = "UDPR_6"                      # UDPR_6                            local reg
            nd_mstr_nwid    = "UDPR_7"                      # UDPR_7                            local reg
            num_part_reg    = "UDPR_8"                      # UDPR_8                            local reg
            cont_word = "UDPR_1"                            # UDPR_1                            local reg
            scratch = self.scratch                          # [UDPR_12, UDPR_13]                local reg
            ev_word = self.ev_word                          # UDPR_14                           local reg

            tran.writeAction(f"{init_fin_label}: movir {num_node_active} 0")
            tran.writeAction(f"movir {ndid_stride} {self.num_ud_per_node * self.num_lane_per_ud}")
            tran.writeAction(f"muli {ndid_stride} {part_stride} {self.part_pram ** 2}")
            tran.writeAction(f"sli {part_stride} {part_array_stride} {LOG2_WORD_SIZE}")
            tran.writeAction(f"addi X0 {nd_mstr_nwid} 0 ")
            tran.writeAction(f"movir {num_part_reg} {self.num_partitions}")

            # Save pointer to intermediate kv in part_ptr
            tran.writeAction(f"addi {intermediate_ptr} {part_ptr} 0")
            tran.writeAction(f"sli {num_keys} {num_keys} {LOG2_WORD_SIZE}")
            tran.writeAction(f"add {num_keys} {part_ptr} {intermediate_ptr}")
            tran.writeAction(f"addi {part_ptr} {part_end_ptr} 0")

            tran.writeAction(f"addi X2 {cont_word} 0")
            tran.writeAction(f"evlb {cont_word} {glb_mstr_claim_work_ev_label}")
            tran = set_ev_label(tran, ev_word,
                nd_mstr_init_ev_label, new_thread=True)

            # Create the node master on each node and send out a partition of input kv pairs
            str_kv_regs = " ".join([f"{part_array_ptr} {part_array_stride} {cont_word} {intermediate_ptr}"])

            tran.writeAction(f"{glb_mstr_loop_label}: ev {ev_word} {ev_word} {nd_mstr_nwid} {nd_mstr_nwid} 8")
            lm_reg = self.__get_lm_base(tran, scratch[0])
            tran.writeAction(f"movir {scratch[1]} {self.ob_cache_offset}")
            # tran.writeAction(f"print '[DEBUG] ob_cache_offset=%d' X29")
            tran.writeAction(f"add {lm_reg} {scratch[1]} {scratch[1]}")
            tran.writeAction(f"send_any_wret {ev_word} {glb_mstr_loop_ev_label} {scratch[1]} {scratch[0]} {str_kv_regs}")
            print(f"send_any_wret {ev_word} {glb_mstr_loop_ev_label} {scratch[1]} {scratch[0]} {str_kv_regs}")

            tran.writeAction(f"add {ndid_stride} {nd_mstr_nwid} {nd_mstr_nwid}")
            tran.writeAction(f"add {part_array_stride} {part_array_ptr} {part_array_ptr} ")
            tran.writeAction(f"addi {num_node_active} {num_node_active} 1")
            tran.writeAction(f"blti {num_node_active} {self.num_nodes} {glb_mstr_loop_label}")

            # Set the num_finished_count register to 0
            reduce_finished_count = "UDPR_1"                # UDPR_1                            thread reg
            map_finished_count = "UDPR_6"                   # UDPR_6                            thread reg
            claim_queue_start = "UDPR_7"                    # UDPR_7                            thread reg
            claim_queue_end = "UDPR_8"                      # UDPR_8                            thread reg

            tran.writeAction(f"movir {reduce_finished_count} 0")
            tran.writeAction(f"movir {map_finished_count} 0")
            tran.writeAction(f"movir {claim_queue_start} {self.claim_queue_offset}")
            tran.writeAction(f"add X7 {claim_queue_start} {claim_queue_start}")
            tran.writeAction(f"addi {claim_queue_start} {claim_queue_end} 0")
            tran.writeAction("yield")

        else:

            glb_mstr_loop_ev_label = self.get_event_mapping(f"master_global")   # Already initialized!

            part_array_ptr = self.part_array_ptr            # UDPR_0    Already initialized!    thread reg
            part_stride = self.part_stride                  # UDPR_14                           thread reg
            num_node_active = "UDPR_5"                      #                                   thread reg
            ndid_stride     = "UDPR_6"                      #                                   thread reg
            num_part_reg    = "UDPR_8"                      #                                   thread reg
            num_part_issued = self.num_part_issued          # UDPR_1                            thread reg
            part_array_stride = self.part_array_stride      # UDPR_2                            thread reg
            num_map_gen = self.num_map_gen                  # UDPR_3                            thread reg
            saved_cont = self.saved_cont                    # UDPR_15   Already initialized     thread reg
            nd_mstr_nwid    = "UDPR_7"                      #                                   local reg
            num_finished    = "UDPR_10"                     #                                   local reg
            scratch = self.scratch                          # [UDPR_12, UDPR_13]                local reg
            ev_word = self.ev_word                          # UDPR_14                           local reg

            tran.writeAction(f"{init_fin_label}: mov_imm2reg {num_node_active} 0")
            if self.debug_flag or self.print_level >= 1:
                tran.writeAction(f"print ' '")
                tran.writeAction(f"print '[DEBUG][NWID %d] Finish initialize the scratchpad. Number of partitions = {self.num_partitions}' {'X0'}")
            tran.writeAction(f"mov_imm2reg {ndid_stride} {self.num_ud_per_node * self.num_lane_per_ud}")
            tran.writeAction(f"muli {ndid_stride} {part_stride} {self.part_pram ** 2}")
            tran.writeAction(f"lshift {part_stride} {part_array_stride} {LOG2_WORD_SIZE}")
            tran.writeAction(f"mov_reg2reg X0 {nd_mstr_nwid}")
            tran.writeAction(f"mov_imm2reg {num_part_reg} {self.num_partitions}")
            tran = set_ev_label(tran, ev_word,
                nd_mstr_init_ev_label, new_thread=True)

            # Create the node master on each node and send out a partition of input kv pairs
            tran.writeAction(f"{glb_mstr_loop_label}: ev_update_reg_2 \
                {ev_word} {ev_word} {nd_mstr_nwid} {nd_mstr_nwid} 8")
            tran.writeAction(format_pseudo(f"sendr3_wret {ev_word} {glb_mstr_loop_ev_label} \
                {part_array_ptr} {part_array_stride} {ndid_stride}", scratch[0], self.send_temp_reg_flag))
            tran.writeAction(f"add {ndid_stride} {nd_mstr_nwid} {nd_mstr_nwid}")
            tran.writeAction(f"add {part_array_stride} {part_array_ptr} {part_array_ptr} ")
            tran.writeAction(f"addi {num_node_active} {num_node_active} 1")
            tran.writeAction(f"blti {num_node_active} {self.num_nodes} {glb_mstr_loop_label}")

            tran.writeAction(f"rshift {part_array_stride} {num_part_issued} {LOG2_WORD_SIZE}")
            tran.writeAction(f"mov_imm2reg {num_map_gen} 0")    # UDPR_9 <- total number of kv_pair generated by mapper
            if self.debug_flag:
                tran.writeAction(f"print '[DEBUG][NWID %d] num_partitions = {self.num_partitions}, num_part_issued = %d' {'X0'} {num_part_issued}")
            tran.writeAction("yield")

        return

    def __gen_global_master_loop(self, tran):

        glb_mstr_loop_ev_label = self.get_event_mapping(f"master_global")   # Already initialized
        nd_mstr_term_ev_label  = self.get_event_mapping(f"master_node_term")

        glb_mstr_fin_fetch_label = "global_master_fin_fetch"

        if self.extension == self.AvailableExtensions.load_balancer or self.extension == self.AvailableExtensions.lb_test:

            num_node_active = "UDPR_5"              #           Already initialized     thread reg
            map_finished_count = "UDPR_6"           #           Already initialized     thread reg
            part_ptr = "UDPR_10"                    #           Already initialized     thread reg
            part_end_ptr = "UDPR_11"                #           Already initialized     thread reg
            saved_cont = self.saved_cont            # UDPR_15   Already initialized     thread reg
            
            scratch_0 = self.scratch[0]             # UDPR_12                           local reg
            ev_word = self.ev_word                  # UDPR_14                           local reg
            
            # If OB_0 is self._finish_flag, node finished
            # Otherwise, node finishes with all map tasks
            tran.writeAction(f"beqi OB_0 {self._finish_flag} node_terminate")
            tran.writeAction(f"addi {map_finished_count} {map_finished_count} 1")
            tran.writeAction(f"yield")

            # terminate the node master thread
            tran.writeAction(f"node_terminate: subi {num_node_active} {num_node_active} 1")
            tran.writeAction(f"bgti {num_node_active} 0 worker_remaining")
            # tran = set_ev_label(tran, ev_word, nd_mstr_term_ev_label, "X1")
            # tran.writeAction(f"sendr_wcont {ev_word} X2 {scratch_0} {scratch_0}")
            tran.writeAction(f"sendr_wcont {saved_cont} X2 {scratch_0} {scratch_0}")
            tran.writeAction(f"yield_terminate")

            tran.writeAction(f"worker_remaining: yield")
        else:
            '''
            Event:      Global master loop
            Operands:   OB_0: Number of map tasks generated
                        OB_1: Return node master thread loop event word
            '''
            glb_sync_init_ev_label = self.get_event_mapping(f"init_global_snyc")

            part_array_ptr = self.part_array_ptr            # UDPR_0    Already initialized!                thread reg
            num_part_issued = self.num_part_issued          # UDPR_1    Already initialized!                thread reg
            part_array_stride = self.part_array_stride      # UDPR_2    Already initialized!                thread reg
            num_map_gen = self.num_map_gen                  # UDPR_3    Already initialized!                thread reg
            part_stride = self.part_stride                  # UDPR_4    Already initialized!                thread reg
            saved_cont = self.saved_cont                    # UDPR_15   Already initialized!                thread reg
            num_node_active = "UDPR_5"                      # Already initialized                           thread reg
            ndid_stride     = "UDPR_6"                      # Already initialized                           thread reg
            num_part_reg    = "UDPR_8"                      # Already initialized                           thread reg
            scratch = self.scratch                          # [UDPR_12, UDPR_13]                            local reg
            ev_word = self.ev_word                          # UDPR_14                                       local reg

            glb_mstr_init_sync_label = "global_master_init_sync"

            if self.debug_flag:
                tran.writeAction(f"print ' '")
                tran.writeAction(f"print '[DEBUG][NWID %d] Event <kvmsr_global_master_loop> ev_word=%d income_cont = %d' {'X0'} {'EQT'} {'X1'}")
            tran.writeAction(f"add OB_0 {num_map_gen} {num_map_gen}")
            tran.writeAction(f"bge {num_part_issued} {num_part_reg} {glb_mstr_fin_fetch_label}")

            # Send next non-assigned partitions to the node
            tran.writeAction(format_pseudo(f"sendr3_wret X1 {glb_mstr_loop_ev_label} \
                {part_array_ptr} {part_array_stride} {ndid_stride}", scratch[0], self.send_temp_reg_flag))
            tran.writeAction(f"add {part_stride} {num_part_issued} {num_part_issued}")
            tran.writeAction(f"add {part_array_stride} {part_array_ptr} {part_array_ptr} ")
            if self.debug_flag:
                tran.writeAction(f"print '[DEBUG][NWID %d] num_partitions = {self.num_partitions}, num_part_issued = %d' {'X0'} {self.num_part_issued}")
                tran.writeAction(f"print '[DEBUG][NWID %d] num_map_generated = %d' {'X0'} {self.num_map_gen}")
            tran.writeAction(f"yield")

            # Finish issuing all the partitions of input kv set, terminate the node master thread
            tran.writeAction(f"{glb_mstr_fin_fetch_label}: subi {num_node_active} {num_node_active} 1")
            tran = set_ev_label(tran, ev_word, nd_mstr_term_ev_label, "X1")
            tran.writeAction(f"sendr_wcont {ev_word} X2 {part_array_ptr} {ndid_stride}")
            if self.debug_flag:
                tran.writeAction(f"print '[DEBUG][NWID %d] num_map_generated = %d' {'X0'} {self.num_map_gen}")
            tran.writeAction(f"beqi {num_node_active} 0 {glb_mstr_init_sync_label}")
            tran.writeAction(f"yield")

            # All the map master threads are termianted, call the global synchronization event
            tran = set_ev_label(tran, ev_word, glb_sync_init_ev_label, src_ev="X2", new_thread=True, label=glb_mstr_init_sync_label)
            tran.writeAction(f"sendr_wcont {ev_word} {saved_cont} {saved_cont} {num_map_gen}")
            if self.debug_flag or self.print_level >= 1:
                tran.writeAction(f"print '[DEBUG][NWID %d] Finish dispatch all the map tasks. Start the global synchronization, ev_word = %d' {'X0'} {self.ev_word}")
            tran.writeAction(f"yield_terminate")

        return

    ####### Load balancer events #######

    def __gen_global_master_claim_work(self, tran):
        '''
        Event: master_global_claim_work
            Returning from map thread. Call get_n_pair and return a kv_pair
            If input kv_pairs left, return to map thread, map event; else return to reduce event
        X1: worker event on the map thread
        '''

        if self.extension == self.AvailableExtensions.lb_test:

            glb_mstr_set_part_ev_label = self.get_event_mapping(f"master_global_set_partition")
            glb_mstr_claim_work_send_map_label = self.get_event_mapping(f"master_global_claim_work_send_map")
            glb_mstr_claim_work_send_reduce_label = self.get_event_mapping(f"master_global_claim_work_send_reduce")


            intermediate_ptr = 'UDPR_3'             # UDPR_3                            thread reg            
            num_node_active = "UDPR_5"              # UDPR_5    Already initialized     thread reg
            map_finished_count = "UDPR_6"           # UDPR_6    Already initialized     thread reg
            claim_queue_start = "UDPR_7"            # UDPR_7    Already initialized     thread reg
            claim_queue_end = "UDPR_8"              # UDPR_8    Already initialized     thread reg
            part_ptr = "UDPR_10"                    # UDPR_10   Already initialized     thread reg
            part_end_ptr = "UDPR_11"                # UDPR_11   Already initialized     thread reg
            saved_cont = self.saved_cont            # UDPR_15   Already initialized     thread reg
            
            scratch = self.scratch                  # [UDPR_12, UDPR_13]                local reg

            # claim key for reducer
            tran.writeAction(f"beq {part_ptr} {part_end_ptr} queue_empty") # check intermediate key-value count

            # tran.writeAction(f"blt {claim_queue_end} {claim_queue_start} claim_queue_end_before_start")

            # # Claim queue start pointer before end pointer, compare queue size with max size
            # tran.writeAction(f"sub {claim_queue_end} {claim_queue_start} {scratch[0]}")
            # tran.writeAction(f"movir {scratch[1]} {self.claim_queue_size}")
            # tran.writeAction(f"beq {scratch[0]} {scratch[1]} claim_queue_full")
            # tran.writeAction(f"jmp cache_claim_cont")

            # # Claim queue end pointer before start pointer, compare queue size with max size
            # tran.writeAction(f"claim_queue_end_before_start: movir {scratch[0]} {self.claim_queue_size}")
            # tran.writeAction(f"add {claim_queue_end} {scratch[0]} {scratch[0]}")
            # tran.writeAction(f"sub {scratch[0]} {claim_queue_start} {scratch[0]}")
            # tran.writeAction(f"movir {scratch[1]} {self.claim_queue_size}")
            # tran.writeAction(f"beq {scratch[0]} {scratch[1]} claim_queue_full")
            # tran.writeAction(f"jmp cache_claim_cont")

            # # Claim queue is full, spin lock
            # tran.writeAction(f"claim_queue_full: sendr_wcont X2 X1 OB_0 OB_1")
            # tran.writeAction(f"yield")

            # # Claim queue is not full
            # # Cache the cont word and claim from key queue
            # tran.writeAction(f"cache_claim_cont: movir {scratch[0]} {self.claim_queue_offset + self.claim_queue_size}")
            # tran.writeAction(f"add X7 {scratch[0]} {scratch[0]}")
            # tran.writeAction(f"blt {claim_queue_end} {scratch[0]} claim_queue_end_not_at_limit")
            # tran.writeAction(f"movir {claim_queue_end} {self.claim_queue_offset}")
            # tran.writeAction(f"add X7 {claim_queue_end} {claim_queue_end}")
            # tran.writeAction(f"claim_queue_end_not_at_limit: movrl X1 0({claim_queue_end}) 1 {WORD_SIZE}")
            # tran.writeAction(f"send_dmlm_ld_wret {part_ptr} {glb_mstr_claim_work_send_reduce_label} {1} {scratch[0]}")
            # tran.writeAction(f"addi {part_ptr} {part_ptr} {WORD_SIZE}")
            # tran.writeAction(f"yield")

            # Send pointer to key in push_key queue to worker
            tran.writeAction(f"addi {part_ptr} {scratch[0]} 0")
            tran.writeAction(f"movir {scratch[1]} {self._reduce_flag}")
            tran.writeAction(f"sendr_wcont X1 X2 {scratch[1]} {part_ptr} {scratch[0]}")
            tran.writeAction(f"addi {part_ptr} {part_ptr} {WORD_SIZE}")
            tran.writeAction(f"yield")


            # If queue is empty but not all map tasks finished yet
            # Spin lock
            tran.writeAction(f"queue_empty: beqi {map_finished_count} {self.num_nodes} reduce_finished")
            tran.writeAction(f"sendr_wcont X2 X1 OB_0 OB_0")
            tran.writeAction(f"yield")

            # All intermediate kv pairs claimed, sending finish flag back
            tran.writeAction(f"reduce_finished: movir {scratch[0]} {self._finish_flag}")
            tran.writeAction(f"sendr_reply {scratch[0]} {scratch[0]} {scratch[1]}")
            tran.writeAction(f"yield")

        else:

            glb_mstr_set_part_ev_label = self.get_event_mapping(f"master_global_set_partition")
            glb_mstr_claim_work_send_map_label = self.get_event_mapping(f"master_global_claim_work_send_map")
            glb_mstr_claim_work_send_reduce_label = self.get_event_mapping(f"master_global_claim_work_send_reduce")

            part_array_ptr = self.part_array_ptr    # UDPR_0    Already initialized!    thread reg
            num_node_active = "UDPR_5"              # Already initialized               thread reg
            num_part_reg    = "UDPR_8"              # Already initialized               thread reg
            partition_active = "UDPR_9"             # Already initialized               thread reg
            part_ptr = "UDPR_10"                    #                                   thread reg
            part_end_ptr = "UDPR_11"                #                                   thread reg
            scratch = self.scratch                  # [UDPR_12, UDPR_13]                local reg


            # If current partition hasn't been set, spin lock
            tran.writeAction(f"beqi {partition_active} 1 claim_work")
            tran.writeAction(f"sendr_wcont X2 X1 X8 X9")
            tran.writeAction(f"yield")

            tran.writeAction(f"claim_work: bequ {num_part_reg} 0 reduce_claim")
            tran.writeAction(f"send_dmlm_ld_wret {part_ptr} {glb_mstr_claim_work_send_map_label} {self.in_kvpair_size} {scratch[0]}")
            tran.writeAction(f"beq {part_ptr} {part_end_ptr} load_next_partition")
            self.in_kvset.get_next_pair(tran, part_ptr, scratch)
            tran.writeAction(f"yield")

            tran.writeAction(f"load_next_partition: subi {num_part_reg} {num_part_reg} 1")
            tran.writeAction(f"movir {partition_active} 0")
            tran.writeAction(f"bequ {num_part_reg} 0 load_reduce")
            tran.writeAction(f"addi {part_array_ptr} {part_array_ptr} {WORD_SIZE}")
            tran.writeAction(f"send_dmlm_ld_wret {part_array_ptr} {glb_mstr_set_part_ev_label} {'2'} {scratch[0]}")
            tran.writeAction(f"yield")

            # TODO: prepare metadata for reduce_claim
            tran.writeAction(f"load_reduce: ")

            self.intermediate_kvset.get_next_pair(tran, part_ptr, self.scratch)

            # claim key for reducer
            tran.writeAction(f"reduce_claim: beq {part_ptr} {part_end_ptr} reduce_finished") # check intermediate key-value count
            tran.writeAction(f"send_dmlm_ld_wret {part_ptr} {glb_mstr_claim_work_send_reduce_label} {self.intermediate_kvpair_size} {scratch[0]}")
            tran.writeAction(f"yield")

            # All intermediate kv pairs claimed, sending finish flag back
            tran.writeAction(f"reduce_finished: movir {scratch[0]} {self._finish_flag}")
            tran.writeAction(f"sendr_reply {scratch[0]} {scratch[0]} {scratch[1]}")
            tran.writeAction(f"yield")

        return

    def __gen_global_master_set_part(self, tran):
        '''
        Event: master_global_set_partition
            Returning from reading pointer of partition. Setting the start and end pointer to current partition.
        OB_0: Start pointer
        OB_1: End pointer
        '''

        part_array_ptr = self.part_array_ptr    # UDPR_0    Already initialized!    thread reg
        saved_cont = self.saved_cont            # UDPR_15   Already initialized     thread reg
        part_stride = self.part_stride          # UDPR_14   Already initialized     thread reg
        num_node_active = "UDPR_5"              # Already initialized               thread reg
        ndid_stride     = "UDPR_6"              # Already initialized               thread reg
        num_part_reg    = "UDPR_8"              # Already initialized               thread reg
        partition_active = "UDPR_9"             # Already initialized               thread reg
        part_ptr = "UDPR_10"                    #                                   thread reg
        part_end_ptr = "UDPR_11"                #                                   thread reg

        tran.writeAction(f"addi X8 {part_ptr} 0")
        tran.writeAction(f"addi X9 {part_end_ptr} 1")
        tran.writeAction(f"movir {partition_active} 1")
        tran.writeAction(f"yield")

        return

    def __gen_global_master_claim_work_send_map(self, tran):

        scratch = self.scratch              # UDPR_12, UDPR_13        local reg
        lm_reg = self.scratch[0]
        
        lm_reg = self.__get_lm_base(send_map_tran, lm_reg)
        send_map_tran.writeAction(f"addi {lm_reg} {scratch[1]} {self.ob_cache_offset}")
        send_map_tran.writeAction(f"movir {scratch[0]} 0")
        send_map_tran.writeAction(f"move {scratch[0]} 0({scratch[1]}) 0 8")
        for i in range(self.in_kvpair_size):
            send_map_tran.writeAction(f"move OB_{i} {8*i + 8}({scratch[1]}) 0 8")
        send_map_tran.writeAction(f"movir {scratch[0]} 0")
        send_map_tran.writeAction(f"send_reply {scratch[0]} {self.in_kvpair_size + 1}")
        send_map_tran.writeAction(f"yield")
        return

    def __gen_global_master_claim_work_send_reduce(self, tran):

        if self.extension == self.AvailableExtensions.load_balancer:
            scratch = self.scratch              # UDPR_12, UDPR_13        local reg
            lm_reg = self.scratch[0]

            lm_reg = self.__get_lm_base(tran, lm_reg)
            tran.writeAction(f"addi {lm_reg} {scratch[1]} {self.ob_cache_offset}")
            tran.writeAction(f"movir {scratch[0]} 1")
            tran.writeAction(f"move {scratch[0]} 0({scratch[1]}) 0 8")
            for i in range(self.intermediate_kvpair_size):
                tran.writeAction(f"move OB_{i} {8*i + 8}({scratch[1]}) 0 8")
            tran.writeAction(f"movir {scratch[0]} 0")
            tran.writeAction(f"send_reply {scratch[1]} {self.intermediate_kvpair_size + 1}")
            tran.writeAction(f"yield")
        elif self.extension == self.AvailableExtensions.lb_test:

            '''
            Event:              returned from dram request sent by claim work
            Operands:   OB_0    claimed key
            '''
            ln_worker_update_claimed_key_ev_label = self.get_event_mapping("worker_update_claimed_key")

            intermediate_ptr = 'UDPR_3'             # UDPR_3                            thread reg
            num_node_active = "UDPR_5"              # UDPR_5    Already initialized     thread reg
            map_finished_count = "UDPR_6"           # UDPR_6    Already initialized     thread reg
            claim_queue_start = "UDPR_7"            # UDPR_7    Already initialized     thread reg
            claim_queue_end = "UDPR_8"              # UDPR_8    Already initialized     thread reg
            part_ptr = "UDPR_10"                    # UDPR_10   Already initialized     thread reg
            part_end_ptr = "UDPR_11"                # UDPR_11   Already initialized     thread reg
            saved_cont = self.saved_cont            # UDPR_15   Already initialized     thread reg

            scratch = self.scratch
            ev_word = self.ev_word

            # Load cached ret cont word from scratchpad
            # And update cache counter
            tran.writeAction(f"movir {scratch[0]} {self.claim_queue_offset + self.claim_queue_size}")
            tran.writeAction(f"add X7 {scratch[0]} {scratch[0]}")
            tran.writeAction(f"blt {claim_queue_start} {scratch[0]} claim_queue_start_not_at_limit")
            tran.writeAction(f"movir {claim_queue_start} {self.claim_queue_offset}")
            tran.writeAction(f"add X7 {claim_queue_start} {claim_queue_start}")
            tran.writeAction(f"claim_queue_start_not_at_limit: movlr 0({claim_queue_start}) {scratch[0]} 1 {WORD_SIZE}")

            # Send dram request to read intermediate kv
            tran.writeAction(f"muli OB_0 {scratch[1]} {self.intermediate_kvpair_size*WORD_SIZE}")
            tran.writeAction(f"add {intermediate_ptr} {scratch[1]} {scratch[1]}")
            tran.writeAction(f"send_dmlm_ld {scratch[1]} {scratch[0]} {self.intermediate_kvpair_size}")

            # Send message to static hashed location indicating key claimed
            self.kv_reduce_loc(tran, "OB_0", scratch[1])
            tran.writeAction(f"addi X2 {ev_word} 0")
            tran.writeAction(f"evii {ev_word} {ln_worker_update_claimed_key_ev_label} 255 5")
            tran.writeAction(f"ev {ev_word}  {ev_word}  {scratch[1]} {scratch[1]} 8")
            tran.writeAction(f"sendr_wcont {ev_word} X2 OB_0 {scratch[0]}")


            tran.writeAction(f"yield")


        return

    def __gen_blobal_master_push_key(self, tran):
        '''
        Event:      returned from worker_receive_kv, push returned key into global queue
        Operands:   OB_0: key
        '''

        glb_mstr_push_key_ret_ev_label = self.get_event_mapping(f"master_global_push_key_ret")

        num_node_active = "UDPR_5"              # UDPR_5    Already initialized     thread reg
        part_ptr = "UDPR_10"                    # UDPR_10   Already initialized     thread reg
        part_end_ptr = "UDPR_11"                # UDPR_11   Already initialized     thread reg
        saved_cont = self.saved_cont            # UDPR_15   Already initialized     thread reg

        scratch = self.scratch                  # [UDPR_12, UDPR13]                 local reg

        tran.writeAction(f"print '        key %u pushed' OB_0")

        lm_reg = self.__get_lm_base(tran, scratch[0])
        tran.writeAction(f"movir {scratch[1]} {self.ob_cache_offset}")
        tran.writeAction(f"add {lm_reg} {scratch[1]} {scratch[1]}")
        tran.writeAction(f"movrl OB_0 0({scratch[1]}) 0 8")
        tran.writeAction(f"send_dmlm_wret {part_end_ptr} {glb_mstr_push_key_ret_ev_label} {scratch[1]} 1 {scratch[0]}")
        tran.writeAction(f"addi {part_end_ptr} {part_end_ptr} {WORD_SIZE}")

        tran.writeAction(f"yield")

        return

    def __gen_global_master_push_key_ret(self,tran):
        tran.writeAction(f"yield")
        return


    ##### End Load balancer events #####


    ###     Node master thread
    def __gen_node_master_th(self):
        nd_mstr_init_ev_label  = self.get_event_mapping(f"init_master_node")
        nd_mstr_loop_ev_label  = self.get_event_mapping(f"master_node")
        nd_mstr_term_ev_label  = self.get_event_mapping(f"master_node_term")

        nd_mstr_init_tran   = self.state.writeTransition("eventCarry", self.state, self.state, nd_mstr_init_ev_label)
        nd_mstr_loop_tran   = self.state.writeTransition("eventCarry", self.state, self.state, nd_mstr_loop_ev_label)
        nd_mstr_term_tran   = self.state.writeTransition("eventCarry", self.state, self.state, nd_mstr_term_ev_label)

        self.__gen_node_master_init(nd_mstr_init_tran)
        self.__gen_node_master_loop(nd_mstr_loop_tran)
        self.__gen_node_master_term(nd_mstr_term_tran)

        return

    def __gen_node_master_init(self, tran):

        ud_mstr_init_ev_label  = self.get_event_mapping(f"init_master_updown")
        nd_mstr_loop_ev_label  = self.get_event_mapping(f"master_node")

        if self.extension == self.AvailableExtensions.load_balancer:

            '''
            Event:      Initialize node master
            Operands:   OB_0: Global master claim_work event_word
                        OB_1: Number of updowns * lane in the node
            '''

            saved_cont = self.saved_cont                # UDPR_15               thread reg
            num_ud_active   = "UDPR_5"                  #                       thread reg
            udid_stride     = "UDPR_6"                  #                       local reg
            ud_mstr_nwid    = "UDPR_7"                  #                       local reg
            scratch_0 = self.scratch[0]                 # UDPR_12               local reg
            ev_word = self.ev_word                      # UDPR_14               local reg

            nd_mstr_loop_label = "node_master_loop"
            nd_mstr_fin_fetch_label = "node_master_fin_fetch"
            nd_mstr_fin_part_label= "node_master_fin_partition"

            tran.writeAction(f"addi X1 {saved_cont} 0")
            tran.writeAction(f"movir {udid_stride} {self.num_lane_per_ud}")
            tran.writeAction(f"movir {num_ud_active} 0")
            tran.writeAction(f"addi X0 {ud_mstr_nwid} 0")
            tran = set_ev_label(tran, ev_word, ud_mstr_init_ev_label, new_thread=True)

            # Create the node master on each node and send out event word of claim_work
            tran.writeAction(f"{nd_mstr_loop_label}: ev {ev_word} {ev_word} {ud_mstr_nwid} {ud_mstr_nwid} 8")
            tran.writeAction(f"sendr_wret {ev_word} {nd_mstr_loop_ev_label} OB_0 {udid_stride} {scratch_0}")
            tran.writeAction(f"add {udid_stride} {ud_mstr_nwid} {ud_mstr_nwid}")
            tran.writeAction(f"addi {num_ud_active} {num_ud_active} 1")
            tran.writeAction(f"blti {num_ud_active} {self.num_ud_per_node} {nd_mstr_loop_label}")
            tran.writeAction("yield")

        elif self.extension == self.AvailableExtensions.lb_test:

            '''
            Event:      Initialize node master
            Operands:   OB_0: Pointer to the base address of the initial partition
                        OB_1: Number of partitions assigned to this node x WORD_SIZE (partition stride)
                        OB_2: Event word of global claim work event
                        OB_3: Pointer to the base address of intermediate kv
            '''

            part_array_ptr = self.part_array_ptr        # UDPR_0                thread reg
            num_ud_active   = "UDPR_5"                  # UDPR_5                thread reg
            udid_stride     = "UDPR_6"                  # UDPR_6                thread reg
            part_array_end  = "UDPR_8"                  # UDPR_8                thread reg
            map_finished_count = "UDPR_10"              # UDPR_10               thread reg
            part_array_stride = self.part_array_stride  # UDPR_12               thread reg
            num_map_gen = self.num_map_gen              # UDPR_13               thread reg
            saved_cont = self.saved_cont                # UDPR_15               thread reg

            part_stride = self.part_stride              # UDPR_4                local reg
            ud_mstr_nwid    = "UDPR_7"                  # UDPR_7                local reg
            scratch = self.scratch                      # [UDPR_12, UDPR_13]    local reg
            ev_word = self.ev_word                      # UDPR_14               local reg

            nd_mstr_loop_label = "node_master_loop"

            tran.writeAction(f"addi X1 {saved_cont} 0")
            tran.writeAction(f"addi OB_0 {part_array_ptr} 0")
            tran.writeAction(f"add OB_1 {part_array_ptr} {part_array_end}")
            tran.writeAction(f"movir {udid_stride} {self.num_lane_per_ud}")
            tran.writeAction(f"movir {num_ud_active} 0")
            tran.writeAction(f"movir {map_finished_count} 0")
            tran.writeAction(f"muli {udid_stride} {part_stride} {self.part_pram}")
            tran.writeAction(f"sli {part_stride} {part_array_stride} {LOG2_WORD_SIZE}")
            tran.writeAction(f"addi X0 {ud_mstr_nwid} 0")
            tran = set_ev_label(tran, ev_word, ud_mstr_init_ev_label, new_thread=True)

            # Create the node master on each node and send out a partition of input kv pairs
            tran.writeAction(f"{nd_mstr_loop_label}: ev \
                {ev_word} {ev_word} {ud_mstr_nwid} {ud_mstr_nwid} 8")

            lm_reg = self.__get_lm_base(tran, scratch[0])
            tran.writeAction(f"movir {scratch[1]} {self.ob_cache_offset}")
            tran.writeAction(f"add {lm_reg} {scratch[1]} {scratch[1]}")
            tran.writeAction(f"send_any_wret {ev_word} {nd_mstr_loop_ev_label} {scratch[1]} {scratch[0]} {part_array_ptr} {part_array_stride} OB_2 OB_3")

            tran.writeAction(f"add {udid_stride} {ud_mstr_nwid} {ud_mstr_nwid}")
            tran.writeAction(f"add {part_array_stride} {part_array_ptr} {part_array_ptr} ")
            tran.writeAction(f"addi {num_ud_active} {num_ud_active} 1")
            tran.writeAction(f"addi {map_finished_count} {map_finished_count} 1")
            tran.writeAction(f"blti {num_ud_active} {self.num_ud_per_node} {nd_mstr_loop_label}")

            tran.writeAction(f"mov_imm2reg {num_map_gen} 0")
            tran.writeAction("yield")

        else:

            '''
            Event:      Initialize node master
            Operands:   OB_0: Pointer to the base address of the initial partition
                        OB_1: Number of partitions assigned to this node x WORD_SIZE (partition stride)
                        OB_2: Number of updowns * lane in the node
            '''

            part_array_ptr = self.part_array_ptr        # UDPR_0                thread reg
            part_array_stride = self.part_array_stride  # UDPR_12               thread reg
            num_map_gen = self.num_map_gen              # UDPR_13               thread reg
            saved_cont = self.saved_cont                # UDPR_15               thread reg
            num_ud_active   = "UDPR_5"                  #                       thread reg
            udid_stride     = "UDPR_6"                  #                       thread reg
            part_array_end  = "UDPR_8"                  #                       thread reg
            ud_mstr_nwid    = "UDPR_7"                  #                       local reg
            part_stride = self.part_stride              # UDPR_14               local reg
            scratch = self.scratch                      # [UDPR_12, UDPR_13]    local reg
            ev_word = self.ev_word                      # UDPR_14               local reg

            nd_mstr_loop_label = "node_master_loop"

            if self.debug_flag:
                tran.writeAction(f"print ' '")
                tran.writeAction(f"print '[DEBUG][NWID %d] Event <node_master_init> ev_word = %d income_cont = %d' {'X0'} {'EQT'} {'X1'}")

                tran.writeAction(f"rshift {'OB_1'} {self.scratch[0]} {LOG2_WORD_SIZE}")
                tran.writeAction(f"print '[DEBUG][NWID %d] Operands: partition_base = %d(0x%x) num_part_assigned = %d num_lane_per_node = %d' \
                    {'X0'} {'OB_0'} {'OB_0'} {self.scratch[0]} {'OB_2'}")
            tran.writeAction(f"mov_reg2reg X1 {saved_cont}")
            tran.writeAction(f"mov_reg2reg OB_0 {part_array_ptr}")
            tran.writeAction(f"add OB_1 {part_array_ptr} {part_array_end}")
            tran.writeAction(f"mov_imm2reg {udid_stride} {self.num_lane_per_ud}")
            tran.writeAction(f"mov_imm2reg {num_ud_active} 0")
            tran.writeAction(f"muli {udid_stride} {part_stride} {self.part_pram}")
            tran.writeAction(f"lshift {part_stride} {part_array_stride} {LOG2_WORD_SIZE}")
            if self.debug_flag:
                tran.writeAction(f"print '[DEBUG][NWID %d] udid_stride = %d part_stride = %d' {'X0'} {udid_stride} {self.part_stride}")
            tran.writeAction(f"mov_reg2reg X0 {ud_mstr_nwid}")
            tran = set_ev_label(tran, ev_word, ud_mstr_init_ev_label, new_thread=True)

            # Create the node master on each node and send out a partition of input kv pairs
            tran.writeAction(f"{nd_mstr_loop_label}: ev_update_reg_2 \
                {ev_word} {ev_word} {ud_mstr_nwid} {ud_mstr_nwid} 8")
            tran.writeAction(format_pseudo(f"sendr3_wret {ev_word} {nd_mstr_loop_ev_label} \
                {part_array_ptr} {part_array_stride} {udid_stride}", scratch[0], self.send_temp_reg_flag))
            if self.debug_flag or self.print_level >= 2:
                tran.writeAction(f"print '[DEBUG][NWID %d] Node master sends part to ud %d master part_array_ptr = %d(0x%x)' \
                    {'X0'} {ud_mstr_nwid} {part_array_ptr} {part_array_ptr}")
            tran.writeAction(f"add {udid_stride} {ud_mstr_nwid} {ud_mstr_nwid}")
            tran.writeAction(f"add {part_array_stride} {part_array_ptr} {part_array_ptr} ")
            tran.writeAction(f"addi {num_ud_active} {num_ud_active} 1")
            tran.writeAction(f"blti {num_ud_active} {self.num_ud_per_node} {nd_mstr_loop_label}")
            tran.writeAction(f"mov_imm2reg {num_map_gen} 0")
            tran.writeAction("yield")

        return
        
    def __gen_node_master_loop(self, tran):
        if self.extension == self.AvailableExtensions.load_balancer or self.extension == self.AvailableExtensions.lb_test:
            '''
            Event:      Node master loop, returned from Updown master, indicating that UD is finished
            Operands:   OB_0: Number of map tasks executed
                        OB_1: Number of reduce tasks executed
            '''
            nd_mstr_term_ev_label  = self.get_event_mapping(f"master_node_term")

            num_ud_active   = "UDPR_5"                  # UDPR_5                thread reg
            map_finished_count = "UDPR_10"              # UDPR_10               thread reg
            saved_cont = self.saved_cont                # UDPR_15               thread reg
            
            scratch_0 = self.scratch[0]                 # UDPR_12               local reg
            ev_word = self.ev_word                      # UDPR_14               local reg

            tran.writeAction(f"beqi OB_0 {self._finish_flag} lane_finished")
            tran.writeAction(f"subi {map_finished_count} {map_finished_count} 1")
            tran.writeAction(f"blei {map_finished_count} 0 map_all_finished")
            tran.writeAction(f"yield")

            tran.writeAction(f"map_all_finished: movir {scratch_0} {self._map_finish_flag}")
            tran.writeAction(f"sendr_wcont {saved_cont} X2 {scratch_0} {scratch_0}")
            tran.writeAction(f"yield")

            # Finish issuing the assigned input kv set, terminate all the lane master threads
            tran.writeAction(f"lane_finished: subi {num_ud_active} {num_ud_active} 1")
            tran.writeAction(f"blei {num_ud_active} 0 node_finished")
            tran.writeAction(f"yield")

            tran.writeAction(f"node_finished: movir {scratch_0} {self._finish_flag}")
            tran.writeAction(f"sendr_wcont {saved_cont} X2 {scratch_0} {scratch_0}")
            tran.writeAction(f"addi X2 {ev_word} 0")
            tran.writeAction(f"evlb {ev_word} {nd_mstr_term_ev_label}")
            tran.writeAction(f"sendr_wcont {ev_word} X2 {scratch_0} {scratch_0}")

            tran.writeAction(f"yield")

        else:
            
            '''
            Event:      Node master loop
            Operands:   OB_0: Number of map tasks generated
                        OB_1: Return updown master thread loop event word
            '''
            nd_mstr_init_ev_label  = self.get_event_mapping(f"init_master_node")
            nd_mstr_loop_ev_label  = self.get_event_mapping(f"master_node")
            ud_mstr_term_ev_label  = self.get_event_mapping(f"master_updown_term")

            part_array_ptr = self.part_array_ptr        # UDPR_0                thread reg
            part_array_stride = self.part_array_stride  # UDPR_12               thread reg
            num_map_gen = self.num_map_gen              # UDPR_13               thread reg
            saved_cont = self.saved_cont                # UDPR_15               thread reg
            num_ud_active   = "UDPR_5"                  #                       thread reg
            udid_stride     = "UDPR_6"                  #                       thread reg
            part_array_end  = "UDPR_8"                  #                       thread reg
            scratch = self.scratch                      # [UDPR_12, UDPR_13]    local reg
            ev_word = self.ev_word                      # UDPR_14               local reg

            nd_mstr_fin_fetch_label = "node_master_fin_fetch"
            nd_mstr_fin_part_label= "node_master_fin_partition"

            if self.debug_flag:
                tran.writeAction(f"print ' '")
                tran.writeAction(f"print '[DEBUG][NWID %d] Event <node_master_loop> ev_word = %d income_cont = %d' {'X0'} {'EQT'} {'X1'}")
            if self.debug_flag or self.print_level >= 1:
                tran.writeAction(f"rshift {'X1'} {scratch[0]} {32 + 6}")
                tran.writeAction(f"print '[DEBUG][NWID %d] Updown %d master returns. Number of map generated = %d' {'X0'}  {self.scratch[0]} {'OB_0'}")
            tran.writeAction(f"add OB_0 {num_map_gen} {num_map_gen}")
            tran.writeAction(f"bge {part_array_ptr} {part_array_end} {nd_mstr_fin_fetch_label}")
            # Send next non-assigned partition to the updown
            tran.writeAction(format_pseudo(f"sendr3_wret X1 {nd_mstr_loop_ev_label} \
                {part_array_ptr} {part_array_stride} {udid_stride}", scratch[0], self.send_temp_reg_flag))
            if self.debug_flag:
                tran.writeAction(f"rshift {'X1'} {self.scratch[0]} {32}")
                tran.writeAction(f"rshift {'X1'} {self.scratch[1]} {24}")
                tran.writeAction(f"andi {self.scratch[1]} {self.scratch[1]}  {0xFF}")
                tran.writeAction(f"print '[DEBUG][NWID %d] Node master sends part to ud %d master tid = %d ev_word=%d part_array_ptr = %d(0x%x) node_part_end = %d(0x%x)' \
                    {'X0'} {self.scratch[0]} {self.scratch[1]} {'X1'} {self.part_array_ptr} {self.part_array_ptr} {part_array_end} {part_array_end}")
                tran.writeAction(f"print '[DEBUG][NWID %d] Node master num_map_generated = %d' {'X0'} {self.num_map_gen}")
            tran.writeAction(f"add {part_array_stride} {part_array_ptr} {part_array_ptr} ")
            tran.writeAction(f"yield")
            # Finish issuing all the partitions of input kv set, terminate all the updown master threads
            tran.writeAction(f"{nd_mstr_fin_fetch_label}: subi {num_ud_active} {num_ud_active} 1")
            tran = set_ev_label(tran, ev_word, ud_mstr_term_ev_label, "X1")
            tran.writeAction(f"sendr_wcont {ev_word} X2 {part_array_ptr} {udid_stride}")
            tran.writeAction(f"beqi {num_ud_active} 0 {nd_mstr_fin_part_label}")
            tran.writeAction(f"yield")
            tran.writeAction(format_pseudo(f"{nd_mstr_fin_part_label}: sendr_wret {saved_cont} {nd_mstr_init_ev_label} {num_map_gen} {num_map_gen}", \
                scratch[0], self.send_temp_reg_flag))
            tran.writeAction(f"mov_imm2reg {num_map_gen} 0")
            tran.writeAction(f"yield")

        return

    def __gen_node_master_term(self, tran):
        if self.debug_flag:
            tran.writeAction(f"print ' '")
            tran.writeAction(f"print '[DEBUG][NWID %d] Event <node_master_term> ev_word = %d income_cont = %d' {'X0'} {'EQT'} {'X1'}")
        tran.writeAction(f"yield_terminate")

        return


    ###     UpDown master thread
    def __gen_updown_master_th(self):
        ud_mstr_init_ev_label  = self.get_event_mapping(f"init_master_updown")
        ud_mstr_loop_ev_label  = self.get_event_mapping(f"master_updown")
        ud_mstr_term_ev_label  = self.get_event_mapping(f"master_updown_term")

        ud_mstr_init_tran   = self.state.writeTransition("eventCarry", self.state, self.state, ud_mstr_init_ev_label)
        ud_mstr_loop_tran   = self.state.writeTransition("eventCarry", self.state, self.state, ud_mstr_loop_ev_label)
        ud_mstr_term_tran   = self.state.writeTransition("eventCarry", self.state, self.state, ud_mstr_term_ev_label)

        self.__gen_updown_master_init(ud_mstr_init_tran)
        self.__gen_updown_master_loop(ud_mstr_loop_tran)
        self.__gen_updown_master_term(ud_mstr_term_tran)

        return

    def __gen_updown_master_init(self, tran):

        ud_mstr_loop_ev_label  = self.get_event_mapping(f"master_updown")
        ln_mstr_init_ev_label  = self.get_event_mapping(f"init_master_lane")

        if self.extension == self.AvailableExtensions.load_balancer:


            '''
            Event:      Initialize updown master
            Operands:   OB_0: Global master claim_work event_word
            '''

            saved_cont = self.saved_cont                    # UDPR_15               thread reg
            num_ln_active       = "UDPR_5"                  #                       thread reg
            ln_mstr_nwid        = "UDPR_6"                  #                       local reg
            part_array_end      = "UDPR_7"                  #                       local reg
            scratch_0 = self.scratch[0]                     # UDPR_12               local reg
            ev_word = self.ev_word                          # UDPR_14               local reg


            ud_mstr_loop_label = "updown_master_loop"

            tran.writeAction(f"mov_reg2reg X1 {saved_cont}")
            tran.writeAction(f"movir {num_ln_active} {0}")
            tran.writeAction(f"mov_reg2reg X0 {ln_mstr_nwid}")
            tran = set_ev_label(tran, ev_word, ln_mstr_init_ev_label, new_thread=True)
            # Create the node master on each node and send out a partition of input kv pairs
            tran.writeAction(f"{ud_mstr_loop_label}: ev_update_reg_2 {ev_word} {ev_word} {ln_mstr_nwid} {ln_mstr_nwid} 8")
            tran.writeAction(format_pseudo(f"sendr_wret {ev_word} {ud_mstr_loop_ev_label} X8 {num_ln_active}", scratch_0, self.send_temp_reg_flag))
            tran.writeAction(f"addi {ln_mstr_nwid} {ln_mstr_nwid} {1}")
            tran.writeAction(f"addi {num_ln_active} {num_ln_active} 1")
            tran.writeAction(f"blti {num_ln_active} {self.num_lane_per_ud} {ud_mstr_loop_label}")
            tran.writeAction("yield")

        elif self.extension == self.AvailableExtensions.lb_test:

            '''
            Event:      Initialize updown master
            Operands:   OB_0: Pointer to the base address of the initial partition
                        OB_1: Number of partitions assigned to this updown x WORD_SIZE
                        OB_2: Event word of global claim work event
                        OB_3: Pointer to the base address of the intermediate kv
            '''    

            part_array_ptr = self.part_array_ptr            # UDPR_0                thread reg -> local reg
            part_array_stride = self.part_array_stride      # UDPR_2                thread reg -> local reg
            num_map_gen = self.num_map_gen                  # UDPR_3                thread reg -> local reg
            num_ln_active       = "UDPR_5"                  # UDPR_5                thread reg
            num_part_assigned   = "UDPR_6"                  # UDPR_6                thread reg -> local reg
            part_array_end      = "UDPR_8"                  # UDPR_8                thread reg -> local reg
            map_finished_count = "UDPR_10"                  # UDPR_10               thread reg
            saved_cont = self.saved_cont                    # UDPR_15               thread reg
    
            ln_mstr_nwid        = "UDPR_7"                  # UDPR_7                local reg
            num_ln_per_ud       = "UDPR_9"                  # UDPR_9                local reg
            scratch = self.scratch                          # [UDPR_12, UDPR_13]    local reg
            ev_word = self.ev_word                          # UDPR_14               local reg
            




            # ud_mstr_term_ev_label  = self.get_event_mapping(f"master_updown_term")
            # tran.writeAction(f"addi OB_3 {scratch[0]} 0")
            # tran.writeAction(f"movir {scratch[0]} {self._finish_flag}")
            # tran.writeAction(f"evlb {ev_word} {ud_mstr_term_ev_label}")
            # tran.writeAction(f"sendr_wcont {ev_word} X2 {scratch[0]} {scratch[0]}")
            # tran.writeAction(f"sendr_wcont X1 X2 {scratch[0]} {scratch[0]}")
            # tran.writeAction(f"yield")



            ud_mstr_loop_label = "updown_master_loop"

            tran.writeAction(f"mov_reg2reg X1 {saved_cont}")
            tran.writeAction(f"mov_reg2reg OB_0 {part_array_ptr}")
            tran.writeAction(f"add OB_1 {part_array_ptr} {part_array_end}")
            tran.writeAction(f"mov_imm2reg {num_ln_active} {0}")
            tran.writeAction(f"movir {map_finished_count} 0")
            tran.writeAction(f"mov_imm2reg {num_ln_per_ud} {self.num_lane_per_ud}")
            tran.writeAction(f"mov_imm2reg {part_array_stride} {WORD_SIZE}")
            tran.writeAction(f"mov_reg2reg X0 {ln_mstr_nwid}")
            tran = set_ev_label(tran, ev_word, ln_mstr_init_ev_label, new_thread=True)

            # Create the node master on each node and send out a partition of input kv pairs
            tran.writeAction(f"{ud_mstr_loop_label}: ev_update_reg_2 \
                {ev_word} {ev_word} {ln_mstr_nwid} {ln_mstr_nwid} 8")

            lm_reg = self.__get_lm_base(tran, scratch[0])
            tran.writeAction(f"movir {scratch[1]} {self.ob_cache_offset}")
            tran.writeAction(f"add {lm_reg} {scratch[1]} {scratch[1]}")
            tran.writeAction(f"send_any_wret {ev_word} {ud_mstr_loop_ev_label} {scratch[1]} {scratch[0]} {part_array_ptr} {part_array_stride} OB_2 OB_3")

            tran.writeAction(f"addi {ln_mstr_nwid} {ln_mstr_nwid} {1}")
            tran.writeAction(f"add {part_array_stride} {part_array_ptr} {part_array_ptr} ")
            tran.writeAction(f"addi {num_ln_active} {num_ln_active} 1")
            tran.writeAction(f"addi {map_finished_count} {map_finished_count} 1")
            tran.writeAction(f"blt {num_ln_active} {num_ln_per_ud} {ud_mstr_loop_label}")
            tran.writeAction(f"mov_imm2reg {num_map_gen} 0")
            tran.writeAction(f"addi {num_ln_active} {num_part_assigned} 0")
            tran.writeAction("yield")

        else:

            '''
            Event:      Initialize updown master
            Operands:   OB_0: Pointer to the base address of the initial partition
                        OB_1: Number of partitions assigned to this updown x WORD_SIZE
                        OB_2: Number of lane in the updown
            '''        

            part_array_ptr = self.part_array_ptr            # UDPR_0                thread reg
            part_array_stride = self.part_array_stride      # UDPR_2                thread reg
            num_map_gen = self.num_map_gen                  # UDPR_3                thread reg
            saved_cont = self.saved_cont                    # UDPR_15               thread reg
            num_ln_active       = "UDPR_5"                  #                       thread reg
            num_part_assigned   = "UDPR_6"                  #                       thread reg
            part_array_end      = "UDPR_8"                  #                       thread reg
            ln_mstr_nwid        = "UDPR_7"                  #                       local reg
            num_ln_per_ud       = "UDPR_9"                  #                       local reg
            ev_word = self.ev_word                          # UDPR_14               local reg
            scratch = self.scratch                          # [UDPR_12, UDPR_13]    local reg

            ud_mstr_loop_label = "updown_master_loop"

            if self.debug_flag:
                tran.writeAction("print ' '")
                tran.writeAction(f"print '[DEBUG][NWID %d] Event <updown_master_init> ev_word = %d income_cont = %d' {'X0'} {'EQT'} {'X1'}")
                tran.writeAction(f"rshift {'OB_1'} {scratch[0]} {LOG2_WORD_SIZE}")
                tran.writeAction(f"print '[DEBUG][NWID %d] Operands: partition_base = %d(0x%x) num_part = %d part_stride = %d num_lane_per_updown = %d' \
                    {'X0'} {'OB_0'} {'OB_0'} {scratch[0]} {'OB_1'} {'OB_2'}")
            tran.writeAction(f"mov_reg2reg X1 {saved_cont}")
            tran.writeAction(f"mov_reg2reg OB_0 {part_array_ptr}")
            tran.writeAction(f"add OB_1 {part_array_ptr} {part_array_end}")
            tran.writeAction(f"mov_imm2reg {num_ln_active} {0}")
            tran.writeAction(f"mov_imm2reg {num_ln_per_ud} {self.num_lane_per_ud}")
            tran.writeAction(f"mov_imm2reg {part_array_stride} {WORD_SIZE}")
            tran.writeAction(f"mov_reg2reg X0 {ln_mstr_nwid}")
            tran = set_ev_label(tran, ev_word, ln_mstr_init_ev_label, new_thread=True)
            # Create the node master on each node and send out a partition of input kv pairs
            tran.writeAction(f"{ud_mstr_loop_label}: ev_update_reg_2 \
                {ev_word} {ev_word} {ln_mstr_nwid} {ln_mstr_nwid} 8")
            tran.writeAction(format_pseudo(f"sendr3_wret {ev_word} {ud_mstr_loop_ev_label} \
                {part_array_ptr} {part_array_stride} {num_ln_active}", scratch[0], self.send_temp_reg_flag))
            if self.debug_flag:
                tran.writeAction(f"print '[DEBUG][NWID %d] Send partition to lane %d master part_array_ptr = %d(0x%x) num_part_assigned = %d' \
                    {'X0'} {ln_mstr_nwid} {part_array_ptr} {part_array_ptr} {num_ln_active}")
            tran.writeAction(f"addi {ln_mstr_nwid} {ln_mstr_nwid} {1}")
            tran.writeAction(f"add {part_array_stride} {part_array_ptr} {part_array_ptr} ")
            tran.writeAction(f"addi {num_ln_active} {num_ln_active} 1")
            tran.writeAction(f"blt {num_ln_active} {num_ln_per_ud} {ud_mstr_loop_label}")
            tran.writeAction(f"mov_imm2reg {num_map_gen} 0")
            tran.writeAction(f"addi {num_ln_active} {num_part_assigned} 0")
            tran.writeAction("yield")

        return

    def __gen_updown_master_loop(self, tran):
        if self.extension == self.AvailableExtensions.load_balancer or self.extension == self.AvailableExtensions.lb_test:

            '''
            Event:      Updown master loop, returned from lane master
            Operands:   OB_0:   if is self._map_finished_flag, indicating that all map tasks are finished on that lane
                                if is self._finish_flag, indicating that all workers are finished on that lane
            '''

            ud_mstr_term_ev_label  = self.get_event_mapping(f"master_updown_term")

            num_ln_active = "UDPR_5"                        # UDPR_5    Already initialized     thread reg
            map_finished_count = "UDPR_10"                  # UDPR_10   Already initialized     thread reg
            saved_cont = self.saved_cont                    # UDPR_15   Already initialized     thread reg
            
            num_map_gen = self.num_map_gen                  # UDPR_3                            local reg
            scratch_0 = self.scratch[0]                     # UDPR_12                           local reg
            ev_word = self.ev_word                          # UDPR_14                           local reg

            ud_mstr_fin_part_label = "updown_master_fin_partition"

            tran.writeAction(f"beqi OB_0 {self._finish_flag} lane_finished")
            tran.writeAction(f"subi {map_finished_count} {map_finished_count} 1")
            tran.writeAction(f"blei {map_finished_count} 0 map_all_finished")
            tran.writeAction(f"yield")

            tran.writeAction(f"map_all_finished: movir {scratch_0} {self._map_finish_flag}")
            tran.writeAction(f"sendr_wcont {saved_cont} X2 {scratch_0} {scratch_0}")
            tran.writeAction(f"yield")

            # Finish issuing the assigned input kv set, terminate all the lane master threads
            tran.writeAction(f"lane_finished: subi {num_ln_active} {num_ln_active} 1")

            tran.writeAction(f"print 'LANE %u TERMINATES' OB_1")

            tran.writeAction(f"blei {num_ln_active} 0 ud_finished")
            tran.writeAction(f"yield")

            tran.writeAction(f"ud_finished: movir {scratch_0} {self._finish_flag}")
            tran.writeAction(f"sendr_wcont {saved_cont} X2 {scratch_0} {scratch_0}")
            tran.writeAction(f"addi X2 {ev_word} 0")
            tran.writeAction(f"evlb {ev_word} {ud_mstr_term_ev_label}")
            tran.writeAction(f"sendr_wcont {ev_word} X2 {scratch_0} {scratch_0}")

            tran.writeAction(f"yield")

        else:
            '''
            Event:      Updown master loop
            Operands:   OB_0: Number of map tasks generated
                        OB_1: Return lane master thread loop event word
            '''

            ud_mstr_init_ev_label  = self.get_event_mapping(f"init_master_updown")
            ud_mstr_loop_ev_label  = self.get_event_mapping(f"master_updown")
            ln_mstr_term_ev_label  = self.get_event_mapping(f"master_lane_term")

            part_array_ptr = self.part_array_ptr            # UDPR_0    Already initialized     thread reg
            part_array_stride = self.part_array_stride      # UDPR_2    Already initialized     thread reg
            num_map_gen = self.num_map_gen                  # UDPR_3    Already initialized     thread reg
            saved_cont = self.saved_cont                    # UDPR_15   Already initialized     thread reg
            num_ln_active       = "UDPR_5"                  #           Already initialized     thread reg
            num_part_assigned   = "UDPR_6"                  #           Already initialized     thread reg
            part_array_end      = "UDPR_8"                  #           Already initialized     thread reg
            ev_word = self.ev_word                          # UDPR_14                           local reg
            scratch = self.scratch                          # [UDPR_12, UDPR_13]                local reg

            ud_mstr_fin_fetch_label = "updown_master_fin_fetch"
            ud_mstr_fin_part_label = "updown_master_fin_partition"

            if self.debug_flag:
                tran.writeAction("print ' '")
                tran.writeAction(f"print '[DEBUG][NWID %d] Event <updown_master_loop> ev_word = %d income_cont = %d' {'X0'} {'EQT'} {'X1'}")
            if self.debug_flag or self.print_level >= 2:
                tran.writeAction(f"rshift {'X1'} {self.scratch[0]} {32}")
                tran.writeAction(f"print '[DEBUG][NWID %d] Lane %d master returns. Number of map generated = %d' {'X0'}  {self.scratch[0]} {'OB_0'}")
            tran.writeAction(f"add OB_0 {num_map_gen} {num_map_gen}")
            tran.writeAction(f"bge {part_array_ptr} {part_array_end} {ud_mstr_fin_fetch_label}")
            # Send next non-assigned partition to the lane
            tran.writeAction(format_pseudo(f"sendr3_wret X1 {ud_mstr_loop_ev_label} \
                {part_array_ptr} {part_array_stride} {num_part_assigned}", scratch[0], self.send_temp_reg_flag))
            if self.debug_flag:
                tran.writeAction(f"rshift {'X1'} {self.scratch[0]} {32}")
                tran.writeAction(f"rshift {'X1'} {self.scratch[1]} {24}")
                tran.writeAction(f"andi {self.scratch[1]} {self.scratch[1]}  {0xFF}")
                tran.writeAction(f"print '[DEBUG][NWID %d] Send partition to lane %d master tid %d part_array_ptr = %d(0x%x) num_part_assigned = %d' \
                    {'X0'} {self.scratch[0]} {self.scratch[1]} {self.part_array_ptr} {self.part_array_ptr} {num_part_assigned}")
            if self.debug_flag or self.print_level >= 2:
                tran.writeAction(f"print '[DEBUG][NWID %d] Updown master assignes %d partition.' {'X0'} {num_part_assigned}")
            tran.writeAction(f"addi {num_part_assigned} {num_part_assigned} 1")
            tran.writeAction(f"add {part_array_stride} {part_array_ptr} {part_array_ptr} ")
            if self.debug_flag:
                tran.writeAction(f"print '[DEBUG][NWID %d] Updown master num_map_generated = %d' {'X0'} {self.num_map_gen}")
            tran.writeAction(f"yield")
            # Finish issuing the assigned input kv set, terminate all the lane master threads
            tran.writeAction(f"{ud_mstr_fin_fetch_label}: subi {num_ln_active} {num_ln_active} 1")
            if self.debug_flag or self.print_level >= 2:
                tran.writeAction(f"print '[DEBUG][NWID %d] Updown master assigned all partitions, number of lane master remains active = %d' {'X0'} {num_ln_active}")
            tran = set_ev_label(tran, ev_word, ln_mstr_term_ev_label, "X1")
            tran.writeAction(f"sendr_wcont {ev_word} X2 {part_array_ptr} {num_part_assigned}")
            if self.debug_flag:
                tran.writeAction(f"rshift {'X1'} {self.scratch[0]} {32}")
                tran.writeAction(f"rshift {'X1'} {self.scratch[1]} {24}")
                tran.writeAction(f"andi {self.scratch[1]} {self.scratch[1]}  {0xFF}")
                tran.writeAction(f"print '[DEBUG][NWID %d] Updown master %d finishes assign all pairs. Terminates lane %d master tid %d, remain_active_lane = %d' \
                    {'X0'} {'X0'} {self.scratch[0]} {self.scratch[1]} {num_ln_active}")
            tran.writeAction(f"blei {num_ln_active} 0 {ud_mstr_fin_part_label}")
            tran.writeAction(f"yield")
            tran.writeAction(format_pseudo(f"{ud_mstr_fin_part_label}: sendr_wret {saved_cont} \
                {ud_mstr_init_ev_label} {num_map_gen} {num_map_gen}", scratch[0], self.send_temp_reg_flag))
            if self.debug_flag:
                tran.writeAction(f"rshift {'X2'} {self.scratch[0]} {32}")
                tran.writeAction(f"rshift {'X1'} {self.scratch[1]} {24}")
                tran.writeAction(f"andi {self.scratch[1]} {self.scratch[1]}  {0xFF}")
                tran.writeAction(f"print '[DEBUG][NWID %d] Updown master %d tid %d finishes issue num_map_generated = %d' \
                    {'X0'} {self.scratch[0]} {self.scratch[1]} {self.num_map_gen}")
                tran.writeAction(f"rshift {self.saved_cont} {self.scratch[0]} {32}")
                tran.writeAction(f"rshift {self.saved_cont} {self.scratch[1]} {24}")
                tran.writeAction(f"andi {self.scratch[1]} {self.scratch[1]}  {0xFF}")
                tran.writeAction(f"print '[DEBUG][NWID %d] Return to node master %d tid %d' \
                    {'X0'} {self.scratch[0]} {self.scratch[1]}")
            tran.writeAction(f"mov_imm2reg {num_map_gen} 0")
            tran.writeAction(f"yield")

    def __gen_updown_master_term(self, tran):
        if self.debug_flag:
            tran.writeAction(f"print ' '")
            tran.writeAction(f"print '[DEBUG][NWID %d] Event <updown_master_term> ev_word = %d income_cont = %d' {'X0'} {'EQT'} {'X1'}")
        tran.writeAction(f"yield_terminate")



    ###     Lane master thread
    def __gen_lane_master_th(self):
        ln_mstr_init_ev_label  = self.get_event_mapping(f"init_master_lane")
        ln_mstr_rd_part_ev_label  = self.get_event_mapping(f"master_lane_read_partition")
        ln_mstr_loop_ev_label  = self.get_event_mapping(f"master_lane")
        ln_mstr_term_ev_label  = self.get_event_mapping(f"master_lane_term")

        ln_mstr_init_tran   = self.state.writeTransition("eventCarry", self.state, self.state, ln_mstr_init_ev_label)
        ln_mstr_rd_part_tran = self.state.writeTransition("eventCarry", self.state, self.state, ln_mstr_rd_part_ev_label)
        ln_mstr_loop_tran   = self.state.writeTransition("eventCarry", self.state, self.state, ln_mstr_loop_ev_label)
        ln_mstr_term_tran   = self.state.writeTransition("eventCarry", self.state, self.state, ln_mstr_term_ev_label)

        self.__gen_lane_master_init(ln_mstr_init_tran)
        self.__gen_lane_master_rd_part(ln_mstr_rd_part_tran)
        self.__gen_lane_master_loop(ln_mstr_loop_tran)
        self.__gen_lane_master_term(ln_mstr_term_tran)

        return

    def __gen_lane_master_init(self, tran):
        if self.extension == self.AvailableExtensions.load_balancer:

            ln_mstr_loop_ev_label  = self.get_event_mapping(f"master_lane")
            ln_map_init_th_ev_label  = self.get_event_mapping(f"init_lane_map_thread")

            saved_cont = self.saved_cont                # UDPR_15               thread reg
            num_th_active   = "UDPR_5"                  #                       thread reg
            lm_base_reg = "UDPR_6"                      #                       local reg
            scratch_0 = self.scratch[0]                 # UDPR_12               local reg
            ev_word = self.ev_word                      # UDPR_14               local reg

            ln_mstr_loop_label = "lane_master_loop"

            tran.writeAction(f"addi X1 {saved_cont} 0")
            tran.writeAction(f"movir {num_th_active} 0")
            tran.writeAction(f"evii {ev_word} {ln_map_init_th_ev_label} 255 5")

            # Create the worker threads on this lane
            tran.writeAction(f"{ln_mstr_loop_label}: sendr_wret {ev_word} {ln_mstr_loop_ev_label} OB_0 {scratch_0} {scratch_0}")
            tran.writeAction(f"addi {num_th_active} {num_th_active} 1")
            tran.writeAction(f"blti {num_th_active} {self.max_map_th_per_lane} {ln_mstr_loop_label}")

            # Initialize local counter
            lm_base_reg = self.__get_lm_base(ln_mstr_rd_part_tran, lm_base_reg)
            tran.writeAction(f"addi {lm_base_reg} {scratch_0} 0")
            tran.writeAction(f"move {num_th_active} {self.map_ctr_offset}({scratch_0}) 0 8")

            tran = set_ev_label(tran, ev_word, ln_mstr_loop_ev_label)
            tran.writeAction(f"move {ev_word} {self.cond_save_offset}({scratch_0}) 0 8")

            # Send the worker counter back to ud master
            # tran.writeAction(f"evi X1 {ev_word} {self.ud_mstr_loop_ev_label} 0 1")
            # tran.writeAction(f"sendr_wret {ev_word} {self.ln_mstr_init_ev_label} {num_th_active} {num_th_active} {scratch_0}")
            tran.writeAction(f"yield")

        elif self.extension == self.AvailableExtensions.lb_test:

            '''
            Event:      Initialize lane master
            Operands:   OB_0: Pointer to the base address of the initial partition
                        OB_1: Number of partitions assigned to this lane x WORD_SIZE
                        OB_2: claim_work event word
                        OB_3: pointer to the base address of the intermediate kv set
            '''

            print("lane master added")
            ln_mstr_rd_part_ev_label  = self.get_event_mapping(f"master_lane_read_partition")

            map_finished_count = "UDPR_10"              # UDPR_10               thread reg
            claim_work_cont = "UDPR_11"                 # UDPR_11               thread reg
            saved_cont = self.saved_cont                # UDPR_15               thread reg

            scratch_0 = self.scratch[0]                 # UDPR_12               local reg
            scratch_1 = self.scratch[1]

            tran.writeAction(f"mov_reg2reg X1 {saved_cont}")
            tran.writeAction(f"addi OB_2 {claim_work_cont} 0")
            tran.writeAction(f"movir {map_finished_count} 0")
            lm_reg = self.__get_lm_base(tran, scratch_0)

            tran.writeAction(f"movir {scratch_1} 0")
            tran.writeAction(f"movrl {scratch_1} {self.local_tid_cache_offset}({lm_reg}) 0 8")

            # tran.writeAction(f"movir {scratch_1} {self.intermediate_ptr_offset}")
            # tran.writeAction(f"add {lm_reg} {scratch_1} {scratch_0}")
            # tran.writeAction(f"movrl OB_3 0({scratch_0}) 0 8")
            tran.writeAction(format_pseudo(f"send_dmlm_ld_wret OB_0 {ln_mstr_rd_part_ev_label} {'2'}", scratch_0, self.send_temp_reg_flag))
            tran.writeAction(f"yield")

        else:

            '''
            Event:      Initialize node master
            Operands:   OB_0: Pointer to the base address of the initial partition
                        OB_1: Number of partitions assigned to this lane x WORD_SIZE
                        OB_2: nth partition assigned to the lane
            '''
            ln_mstr_rd_part_ev_label  = self.get_event_mapping(f"master_lane_read_partition")

            saved_cont = self.saved_cont                # UDPR_15               thread reg
            scratch_0 = self.scratch[0]                 # UDPR_12               local reg

            if self.debug_flag:
                tran.writeAction(f"print ' '")
                tran.writeAction(f"print '[DEBUG][NWID %d] Event <lane_master_init> ev_word = %d income_cont = %d' {'X0'} {'EQT'} {'X1'}")
                tran.writeAction(f"print '[DEBUG][NWID %d] Operands: %d partition assigned partition_base = %d(0x%x) partition_stride = %d ' \
                    {'X0'} {'OB_2'} {'OB_0'} {'OB_0'} {'OB_1'}")
            tran.writeAction(f"mov_reg2reg X1 {saved_cont}")
            tran.writeAction(format_pseudo(f"send_dmlm_ld_wret OB_0 {ln_mstr_rd_part_ev_label} {'2'}", scratch_0, self.send_temp_reg_flag))
            tran.writeAction(f"yield")

        return

    def __gen_lane_master_rd_part(self, tran):
        '''
        Event:      Read the start and end address of the assigned partition
        Operands:   OB_0: The base address of the first key-value pair in the partition
                    OB_1: The base address of the first key-value pair in the next partition / or the end address of the key-value set
        '''

        ln_mstr_init_ev_label  = self.get_event_mapping(f"init_master_lane")
        ln_mstr_loop_ev_label  = self.get_event_mapping(f"master_lane")
        ln_map_init_th_ev_label  = self.get_event_mapping(f"init_lane_map_thread")

        num_th_active   = "UDPR_5"                  #                                   thread reg
        part_ptr    = "UDPR_6"                      #                                   thread reg
        part_end    = "UDPR_8"                      #                                   thread reg
        num_map_gen = self.num_map_gen              # UDPR_13                           thread reg
        saved_cont = self.saved_cont                # UDPR_15   Already initialized     thread reg

        lm_base_reg = "UDPR_7"                      #                                   local reg
        scratch = self.scratch                      # [UDPR_12, UDPR_13]                local reg
        ev_word = self.ev_word                      # UDPR_14                           local reg

        empty_part_label = "lane_master_empty_partition"
        ln_mstr_loop_label = "lane_master_loop"
        ln_mstr_fin_fetch_label = "lane_master_fin_fetch"

        if self.debug_flag:
            tran.writeAction(f"print ' '")
            tran.writeAction(f"print '[DEBUG][NWID %d] Event <lane_master_read_partition> ev_word = %d income_cont = %d' {'X0'} {'EQT'} {'X1'}")
            tran.writeAction(f"print '[DEBUG][NWID %d] Operands: part[0] = %d(0x%x) next_part[0] = %d(0x%x)' {'X0'} {'OB_0'} {'OB_0'} {'OB_1'} {'OB_1'}")
        tran.writeAction(f"bge OB_0 OB_1 {empty_part_label}")

        tran.writeAction(f"mov_reg2reg OB_0 {part_ptr}")
        tran.writeAction(f"mov_reg2reg OB_1 {part_end}")
        tran.writeAction(f"mov_imm2reg {num_th_active} 0")
        tran = set_ev_label(tran, ev_word, ln_map_init_th_ev_label, new_thread=True)

        # Create the map worker threads on this lane and send out a key-value pair
        tran.writeAction(format_pseudo(f"{ln_mstr_loop_label}: sendr_wret {ev_word} {ln_mstr_loop_ev_label} \
            {part_ptr} {part_ptr}", scratch[0], self.send_temp_reg_flag))
        if self.debug_flag:
            tran.writeAction(f"print '[DEBUG][NWID %d] Send kvpair to new map thread ev_word=%d pair_ptr = %d(0x%x)' \
                {'X0'} {self.ev_word} {part_ptr} {part_ptr}")
        tran.writeAction(f"addi {num_th_active} {num_th_active} 1")

        if self.extension == self.AvailableExtensions.lb_test:
            map_finished_count = "UDPR_10"              # UDPR_10   Already initialized     thread reg
            tran.writeAction(f"addi {map_finished_count} {map_finished_count} 1")

        tran, part_ptr = self.in_kvset.get_next_pair(tran, part_ptr, scratch)
        tran.writeAction(f"bge {part_ptr} {part_end} {ln_mstr_fin_fetch_label}")
        tran.writeAction(f"blti {num_th_active} {self.max_map_th_per_lane} {ln_mstr_loop_label}")

        tran.writeAction(f"{ln_mstr_fin_fetch_label}: mov_imm2reg {num_map_gen} 0")
        # Initialize local counter and master thread event word.
        lm_base_reg = self.__get_lm_base(tran, lm_base_reg)
        tran.writeAction(f"addi {lm_base_reg} {scratch[1]} 0")
        tran.writeAction(f"move {num_map_gen} {self.map_ctr_offset}({scratch[1]}) 0 8")
        tran = set_ev_label(tran, scratch[0], ln_mstr_loop_ev_label)
        if self.debug_flag:
            tran.writeAction(f"print '[DEBUG][NWID %d] lane master event word = %d' {'X0'} {scratch[0]}")
        tran.writeAction(f"move {scratch[0]} {self.cond_save_offset}({scratch[1]}) 0 8")
        tran.writeAction("yield")

        tran.writeAction(f"{empty_part_label}: mov_imm2reg {self.num_map_gen} 0")
        tran.writeAction(format_pseudo(f"sendr_wret {saved_cont} {ln_mstr_init_ev_label} {num_map_gen} {num_map_gen}", \
            scratch[0], self.send_temp_reg_flag))
        if self.debug_flag:
            tran.writeAction(f"print '[DEBUG][NWID %d] Lane %d master receives empty partition, end_pair_addr = %d(0x%x)' \
                {'X0'} {'X0'} {part_end} {part_end}")
            tran.writeAction(f"rshift {saved_cont} {scratch[0]} {32}")
            tran.writeAction(f"rshift {'X1'} {self.scratch[1]} {24}")
            tran.writeAction(f"andi {self.scratch[1]} {self.scratch[1]}  {0xFF}")
            tran.writeAction(f"print '[DEBUG][NWID %d] Return to updown master %d tid %d' \
                {'X0'} {self.scratch[0]} {self.scratch[1]}")
        tran.writeAction(f"yield")

        return

    def __gen_lane_master_loop(self, tran):
        if self.extension == self.AvailableExtensions.load_balancer:
            '''
            Event:      Lane master loop event, returned from worker thread, indicating that worker is finished
            Operands:
            '''
            ln_mstr_term_ev_label  = self.get_event_mapping(f"master_lane_term")

            saved_cont = self.saved_cont                # UDPR_15   Already initialized     thread reg
            num_th_active   = "UDPR_5"                  #           Already initialized     thread reg
            scratch_0 = self.scratch[0]                 # UDPR_12                           local reg
            ev_word = self.ev_word                      # UDPR_14               local reg

            tran.writeAction(f"subi {num_th_active} {num_th_active} 1")
            tran.writeAction(f"sendr_reply {self.scratch[0]} {self.scratch[0]} {self.scratch[0]}")
            tran.writeAction(f"beqi {num_th_active} 0 lane_finished")
            tran.writeAction(f"yield")

            tran.writeAction(f"lane_finished: sendr_wret {saved_cont} {self.ln_mstr_init_ev_label} {scratch_0} {scratch_0} {scratch_0}")
            tran.writeAction(f"addi X2 {ev_word} 0")
            tran.writeAction(f"evlb {ev_word} {ln_mstr_term_ev_label}")
            tran.writeAction(f"sendr_wcont {ev_word} {saved_cont} {scratch_0} {scratch_0}")
            tran.writeAction(f"yield")

        elif self.extension == self.AvailableExtensions.lb_test:
            ln_mstr_init_ev_label  = self.get_event_mapping(f"init_master_lane")
            ln_map_th_term_ev_label  = self.get_event_mapping(f"terminate_lane_map_thread")
            ln_worker_work_ev_label = self.get_event_mapping(f"worker_work")
            ln_mstr_term_ev_label  = self.get_event_mapping(f"master_lane_term")

            num_th_active   = "UDPR_5"                  # UDPR_5                            thread reg
            part_ptr    = "UDPR_6"                      # UDPR_6                            thread reg
            part_end    = "UDPR_8"                      # UDPR_8                            thread reg
            map_finished_count = "UDPR_10"              # UDPR_10   Already initialized     thread reg
            claim_work_cont = "UDPR_11"                 # UDPR_11   Already initialized     thread reg
            num_map_gen = self.num_map_gen              # UDPR_13                           thread reg
            saved_cont = self.saved_cont                # UDPR_15   Already initialized     thread reg

            lm_base_reg = "UDPR_7"                      #                                   local reg
            scratch = self.scratch                      # [UDPR_12, UDPR_13]                local reg
            ev_word = self.ev_word                      # UDPR_14                           local reg

            ln_mstr_fin_fetch_label = "lane_master_fin_fetch"
            ln_mstr_cont_label = "lane_master_loop_cont"

            tran.writeAction(f"bge {part_ptr} {part_end} {ln_mstr_fin_fetch_label}")

            # Send next non-assigned partition to the lane
            tran.writeAction(f"send_dmlm_ld {part_ptr} {'X1'} {self.in_kvpair_size}")
            tran, part_ptr = self.in_kvset.get_next_pair(tran, part_ptr, scratch)
            tran.writeAction(f"yield")

            # Finish issuing the assigned input kv set
            tran.writeAction(f"{ln_mstr_fin_fetch_label}: beqi OB_0 {self._finish_flag} worker_finished")
            tran.writeAction(f"subi {map_finished_count} {map_finished_count} 1")

            # Get tid of the thread sending message in
            lm_reg = self.__get_lm_base(tran, scratch[1])
            tran.writeAction(f"movlr {self.local_tid_cache_offset + WORD_SIZE}({lm_reg}) {scratch[0]} 0 8")
            tran.writeAction(f"movir {scratch[1]} {0xFF}")
            tran.writeAction(f"srandi X1 {scratch[1]} {24}")

            # If it's not the thread cached in scratchpad, terminate
            tran.writeAction(f"beq {scratch[1]} {scratch[0]} start_worker")
            tran.writeAction(f"evi X1 {ev_word} {ln_map_th_term_ev_label} 1")
            tran.writeAction(f"sendr_wcont {ev_word} X2 {scratch[0]} {scratch[0]}")
            tran.writeAction(f"subi {num_th_active} {num_th_active} 1")
            tran.writeAction(f"jmp check_map_finish_cond")

            # If it is, launch the worker_work event
            tran.writeAction(f"start_worker: movir {scratch[0]} {123456}")
            tran.writeAction(f"evi X1 {ev_word} {ln_worker_work_ev_label} 1")
            tran.writeAction(f"sendr3_wcont {ev_word} X2 {scratch[0]} {claim_work_cont} X2")

            tran.writeAction(f"check_map_finish_cond: blei {map_finished_count} 0 map_all_finished")
            tran.writeAction(f"yield")

            tran.writeAction(f"map_all_finished: movir {scratch[0]} {self._map_finish_flag}")
            tran.writeAction(f"sendr_wcont {saved_cont} X2 {scratch[0]} {scratch[0]}")
            tran.writeAction(f"yield")

            tran.writeAction(f"worker_finished: subi {num_th_active} {num_th_active} 1")
            tran.writeAction(f"beqi {num_th_active} 0 lane_finished")
            tran.writeAction(f"yield")

            tran.writeAction(f"lane_finished: movir {scratch[0]} {self._finish_flag}")
            tran.writeAction(f"sendr_wcont {saved_cont} X2 {scratch[0]} X0")
            tran.writeAction(f"addi X2 {ev_word} 0")
            tran.writeAction(f"evlb {ev_word} {ln_mstr_term_ev_label}")
            tran.writeAction(f"sendr_wcont {ev_word} X2 {scratch[0]} {scratch[0]}")
            tran.writeAction(f"yield")


        else:

            '''
            Event:      Lane master loop
            Operands:   OB_0: Map thread event word
            '''

            ln_mstr_init_ev_label  = self.get_event_mapping(f"init_master_lane")
            ln_map_th_term_ev_label  = self.get_event_mapping(f"terminate_lane_map_thread")

            num_map_gen = self.num_map_gen              # UDPR_13                           thread reg
            saved_cont = self.saved_cont                # UDPR_15   Already initialized     thread reg
            num_th_active   = "UDPR_5"                  #                                   thread reg
            part_ptr    = "UDPR_6"                      #                                   thread reg
            part_end    = "UDPR_8"                      #                                   thread reg
            lm_base_reg = "UDPR_7"                      #                                   local reg
            scratch = self.scratch                      # [UDPR_12, UDPR_13]                local reg
            ev_word = self.ev_word                      # UDPR_14                           local reg

            ln_mstr_fin_fetch_label = "lane_master_fin_fetch"
            ln_mstr_cont_label = "lane_master_loop_cont"

            if self.debug_flag:
                tran.writeAction(f"print ' '")
                tran.writeAction(f"print '[DEBUG][NWID %d] Event <lane_master_loop> ev_word = %d income_cont = %d' {'X0'} {'EQT'} {'X1'}")
                tran.writeAction(f"rshift {'X1'} {self.scratch[0]} {24}")
                tran.writeAction(f"andi {self.scratch[0]} {self.scratch[0]}  {0xFF}")
                tran.writeAction(f"print '[DEBUG][NWID %d] Source map thread tid = %d return ops: OB_0 = %d OB_1 = %d' \
                    {'X0'} {self.scratch[0]} {'OB_0'} {'OB_1'}")
            tran.writeAction(f"bge {part_ptr} {part_end} {ln_mstr_fin_fetch_label}")

            # Send next non-assigned partition to the lane
            tran.writeAction(f"send_dmlm_ld {part_ptr} {'X1'} {self.in_kvpair_size}")
            if self.debug_flag:
                tran.writeAction(f"rshift {'X1'} {self.scratch[1]} {24}")
                tran.writeAction(f"andi {self.scratch[1]} {self.scratch[1]}  {0xFF}")
                tran.writeAction(f"print '[DEBUG][NWID %d] Send kvpair to map thread %d ev_word=%d pair_ptr = %d(0x%x)' \
                    {'X0'} {self.scratch[1]} {'X1'} {part_ptr} {part_ptr}")
            tran, part_ptr = self.in_kvset.get_next_pair(tran, part_ptr, scratch)
            tran.writeAction(f"yield")

            # Finish issuing the assigned input kv set, terminate the lane map thread
            tran.writeAction(f"{ln_mstr_fin_fetch_label}: subi {num_th_active} {num_th_active} 1")
            tran = set_ev_label(tran, ev_word, ln_map_th_term_ev_label, src_ev="X1")
            tran.writeAction(f"sendr_wcont {ev_word} X2 {scratch[0]} {scratch[0]}")
            if self.debug_flag:
                tran.writeAction(f"rshift {'X1'} {self.scratch[1]} {24}")
                tran.writeAction(f"andi {self.scratch[1]} {self.scratch[1]}  {0xFF}")
                tran.writeAction(f"print '[DEBUG][NWID %d] Lane master terminates map thread %d ev_word=%d remain_active_thread = %d' \
                    {'X0'} {self.scratch[1]} {self.ev_word} {num_th_active}")

            tran.writeAction(f"bnei {num_th_active} 0 {ln_mstr_cont_label}")

            # Finish issuing all the assigned input kv set, return to the updown master with the number of map tasks generated
            lm_base_reg = self.__get_lm_base(tran, lm_base_reg)
            tran.writeAction(f"addi {lm_base_reg} {scratch[1]} 0")
            tran.writeAction(f"move {self.map_ctr_offset}({scratch[1]}) {num_map_gen} 0 8")
            tran.writeAction(format_pseudo(f"sendr_wret {saved_cont} {ln_mstr_init_ev_label} {num_map_gen} {num_map_gen}", scratch[0], self.send_temp_reg_flag))
            if self.debug_flag:
                tran.writeAction(f"print '[DEBUG][NWID %d] Lane %d master finishes all pairs assigned, num_map_generated = %d, end_pair_addr = %d(0x%x)' \
                    {'X0'} {'X0'} {self.num_map_gen} {part_end} {part_end}")
                tran.writeAction(f"rshift {self.saved_cont} {self.scratch[0]} {32}")
                tran.writeAction(f"rshift {'X1'} {self.scratch[1]} {24}")
                tran.writeAction(f"andi {self.scratch[1]} {self.scratch[1]}  {0xFF}")
                tran.writeAction(f"print '[DEBUG][NWID %d] Return to updown master %d tid %d' \
                    {'X0'} {self.scratch[0]} {self.scratch[1]}")

            tran.writeAction(f"{ln_mstr_cont_label}: yield")

        return

    def __gen_lane_master_term(self, tran):
        if self.debug_flag:
            tran.writeAction(f"print ' '")
            tran.writeAction(f"print '[DEBUG][NWID %d] Event <lane_master_term> ev_word = %d income_cont = %d' {'X0'} {'EQT'} {'X1'}")
        tran.writeAction(f"yield_terminate")

        return

    ##############################################################################





    ##############################################################################
    '''
    Thread/Event functions of map/reduce worker threads
    '''

    ###     Map thread
    def __gen_map_thread(self):
        ln_map_init_th_ev_label  = self.get_event_mapping(f"init_lane_map_thread")
        ln_map_th_ev_label = self.get_event_mapping("lane_map_thread")
        ln_map_ret_ev_label = self.get_event_mapping("map_thread_return")
        ln_map_th_term_ev_label  = self.get_event_mapping(f"terminate_lane_map_thread")
            

        ln_map_init_th_tran = self.state.writeTransition("eventCarry", self.state, self.state, ln_map_init_th_ev_label)
        ln_map_th_tran = self.state.writeTransition("eventCarry", self.state, self.state, ln_map_th_ev_label)
        ln_map_th_ret_tran = self.state.writeTransition("eventCarry", self.state, self.state, ln_map_ret_ev_label)
        ln_map_th_term_tran = self.state.writeTransition("eventCarry", self.state, self.state, ln_map_th_term_ev_label)

        self.__gen_map_init(ln_map_init_th_tran)
        self.__gen_map_function(ln_map_th_tran)
        self.__gen_map_ret(ln_map_th_ret_tran)
        self.__gen_map_term(ln_map_th_term_tran)

        if self.extension == self.AvailableExtensions.lb_test:
            ln_worker_work_ev_label = self.get_event_mapping(f"worker_work")
            ln_worker_matererialize_ret_ev_label = self.get_event_mapping("worker_materialize_ret")
            ln_worker_fetched_key_ev_label = self.get_event_mapping("worker_fetched_key")
            ln_worker_fetched_kv_ptr_ev_label = self.get_event_mapping("worker_fetched_kv_ptr")

            ln_worker_work_tran = self.state.writeTransition("eventCarry", self.state, self.state, ln_worker_work_ev_label)
            ln_worker_matererialize_ret_tran = self.state.writeTransition("eventCarry", self.state, self.state, ln_worker_matererialize_ret_ev_label)
            ln_worker_fetched_key_tran = self.state.writeTransition("eventCarry", self.state, self.state, ln_worker_fetched_key_ev_label)
            ln_worker_fetched_kv_ptr_tran = self.state.writeTransition("eventCarry", self.state, self.state, ln_worker_fetched_kv_ptr_ev_label)

            self.__gen_worker_work(ln_worker_work_tran)
            self.__gen_worker_materialize_ret(ln_worker_matererialize_ret_tran)
            self.__gen_worker_fetched_key(ln_worker_fetched_key_tran)
            self.__gen_worker_fetched_kv_ptr(ln_worker_fetched_kv_ptr_tran)
            

        return

    def __gen_map_init(self, tran):
        '''
        Event:      Initialize map thread
        '''
        ln_map_th_ev_label = self.get_event_mapping("lane_map_thread")

        scratch_0 = self.scratch[0]                 # UDPR_12                           local reg

        if self.extension == self.AvailableExtensions.load_balancer:
            '''
            Operands:   OB_0 Global claim_work event word
            '''
            tran.writeAction(f"sendr_wret OB_0 {ln_map_th_ev_label} {scratch_0} {scratch_0} {scratch_0}")
            tran.writeAction(f"yield")
        elif self.extension == self.AvailableExtensions.lb_test:
            scratch = self.scratch

            # Update local alive map/worker thread count
            tran.writeAction(f"movlr {self.local_tid_cache_offset}(X7) {scratch[0]} 0 8")
            tran.writeAction(f"beqi {scratch[0]} 1 not_first_thread")
            tran.writeAction(f"addi {scratch[0]} {scratch[0]} 1")
            tran.writeAction(f"addi X7 {scratch[1]} 0")
            tran.writeAction(f"movrl {scratch[0]} {self.local_tid_cache_offset}({scratch[1]}) 0 8")

            # Cache current tid
            tran.writeAction(f"muli {scratch[0]} {scratch[1]} {WORD_SIZE}")
            tran.writeAction(f"add X7 {scratch[1]} {scratch[1]}")
            tran.writeAction(f"movir {scratch[0]} {0xFF}")
            tran.writeAction(f"srandi X2 {scratch[0]} {24}")
            tran.writeAction(f"movrl {scratch[0]} {self.local_tid_cache_offset}({scratch[1]}) 0 8")

            tran.writeAction(format_pseudo(f"not_first_thread: send_dmlm_ld_wret {f'OB_0'} {ln_map_th_ev_label} {self.in_kvpair_size}", \
                scratch_0, self.send_temp_reg_flag))
            tran.writeAction(f"yield")
        else:
            '''
            Operands:   OB_0: Pair address
            '''
            if self.debug_flag and self.print_level > 2:
                tran.writeAction(f"print ' '")
                tran.writeAction(f"print '[DEBUG][NWID %d] Event <init_map_thread> pair_addr = %d(0x%x)' \
                    {'X0'} {f'OB_0'} {f'OB_0'}")
            tran.writeAction(format_pseudo(f"send_dmlm_ld_wret {f'OB_0'} {ln_map_th_ev_label} {self.in_kvpair_size}", \
                scratch_0, self.send_temp_reg_flag))
            tran.writeAction(f"yield")

        return

    def __gen_map_function(self, tran):
        '''
        Event:      Map thread
        Operands:   Input key-value pair
        '''

        if self.extension == self.AvailableExtensions.load_balancer:

            '''
            Returned from claim_work
            Operands:   OB_0    flag indicating map/reduce kv_pair, 0 is map, 1 is reduce
                        OB_1~n  the kv_pair
            '''
            ln_map_init_th_ev_label  = self.get_event_mapping(f"init_lane_map_thread")
            ln_map_ret_ev_label = self.get_event_mapping("map_thread_return")
            ln_reduce_th_ev_label = self.get_event_mapping("init_lane_reduce_thread")

            lm_reg = "UDPR_5"                           #                       local reg
            scratch_0 = self.scratch[0]                 # UDPR_12               local reg
            ev_word = self.ev_word                      # UDPR_14               local reg


            nreg = " ".join([f"OB_{i+2}" for i in range(self.in_kvpair_size-1)])

            tran.writeAction(f"beqi OB_0 1 send_reduce")
            self.inter_kvpair_size = self.kv_map(tran, "OB_0", [f"OB_{n+1}" for n in range((self.in_kvpair_size) - 1)], ln_map_init_th_ev_label)

            tran.writeAction(f"send_reduce: addi X2 {ev_word} 0")
            tran.writeAction(f"evlb {ev_word} {ln_reduce_th_ev_label}")
            tran.writeAction(f"send_any_wcont {ev_word} X1 OB_1 {scratch_0} {nreg}")
            tran.writeAction(f"yield")

        else:

            ln_map_ret_ev_label = self.get_event_mapping("map_thread_return")

            saved_cont = self.saved_cont                # UDPR_15               thread reg

            # Set up the map code
            if self.debug_flag:
                tran.writeAction(f"print ' '")
                tran.writeAction(f"print '[DEBUG][NWID %d] Event <map_thread> pair_addr = %d(0x%x)' \
                    {'X0'} {f'OB_{self.in_kvpair_size}'} {f'OB_{self.in_kvpair_size}'}")
                tran.writeAction(f"addi {f'OB_{self.in_kvpair_size}'} {saved_cont} 0")


            scratch = self.scratch

            self.inter_kvpair_size = self.kv_map(tran, "OB_0", [f"OB_{n+1}" for n in range((self.in_kvpair_size) - 1)], ln_map_ret_ev_label)

        return

    def __gen_map_ret(self, tran):
        '''
        Event:      Map thread return event
        Operands:
        '''
        ln_map_th_ev_label = self.get_event_mapping("lane_map_thread")

        lm_base_reg = self.scratch[0]                   # UDPR_12                           local reg
        scratch = self.scratch                          # [UDPR_12, UDPR_13]                local reg

        # Return to lane master
        if self.debug_flag:
            tran.writeAction(f"print ' '")
            tran.writeAction(f"print '[DEBUG][NWID %d] Event <map_thread_return> ev_word = %d income_cont = %d' {'X0'} {'EQT'} {'X1'}")
            tran.writeAction(f"rshift {'X2'} {self.scratch[1]} {24}")
            tran.writeAction(f"andi {self.scratch[1]} {self.scratch[1]}  {0xFF}")
            tran.writeAction(f"print '[DEBUG][NWID %d] Map thread %d finishes pair %d(0x%x)' {'X0'} {self.scratch[1]} {self.saved_cont} {self.saved_cont}")
        lm_base_reg = self.__get_lm_base(tran)
        tran.writeAction(f"move {self.cond_save_offset}({lm_base_reg}) {scratch[1]} 0 8")
        tran.writeAction(format_pseudo(f"sendops_wret {scratch[1]} {ln_map_th_ev_label} OB_0 2", scratch[0], self.send_temp_reg_flag))
        if self.debug_flag:
            tran.writeAction(f"rshift {'X1'} {self.scratch[1]} {24}")
            tran.writeAction(f"andi {self.scratch[1]} {self.scratch[1]}  {0xFF}")
            tran.writeAction(f"print '[DEBUG][NWID %d] Map thread returns operands: OB_0 = %d OB_1 = %d to lane master tid %d' \
                {'X0'} {'OB_0'} {'OB_1'} {self.scratch[0]}")
        tran.writeAction("yield")

        return

    def __gen_map_term(self, tran):
        if self.debug_flag and self.print_level > 3:
            tran.writeAction(f"print ' '")
            tran.writeAction(f"print '[DEBUG][NWID %d] Event <map_thread_term> ev_word = %d income_cont = %d' {'X0'} {'EQT'} {'X1'}")
        tran.writeAction(f"yield_terminate")



    ###     Reduce thread
    def __gen_reduce_thread(self):

        ln_reduce_th_ev_label = self.get_event_mapping("init_lane_reduce_thread")
        ln_reduce_th_ret_ev_label = self.get_event_mapping("lane_reduce_thread_return")

        ln_reduce_tran      = self.state.writeTransition("eventCarry", self.state, self.state, ln_reduce_th_ev_label)
        ln_reduce_ret_tran  = self.state.writeTransition("eventCarry", self.state, self.state, ln_reduce_th_ret_ev_label)

        self.__gen_reduce_function(ln_reduce_tran)
        self.__gen_reduce_ret(ln_reduce_ret_tran)

        if self.extension == self.AvailableExtensions.load_balancer:
            ln_reduce_receive_kv_ev_label = self.get_event_mapping("lane_reduce_thread_receive_intermediate_kv_pair")
            rec_tran = self.state.writeTransition("eventCarry", self.state, self.state, ln_reduce_receive_kv_ev_label)
            self.__gen_reduce_receive_kv(rec_tran)

        return

    def __gen_reduce_function(self, tran):

        
        '''
        Event:      Reduce thread
        Operands:   Intermediate key-value pair
        '''

        ln_reduce_th_ret_ev_label = self.get_event_mapping("lane_reduce_thread_return")

        if self.extension == self.AvailableExtensions.load_balancer:
            ln_map_init_th_ev_label  = self.get_event_mapping(f"init_lane_map_thread")
            self.kv_reduce(tran, inter_key, inter_values, ln_map_init_th_ev_label)

        elif self.extension == self.AvailableExtensions.lb_test:

            kv_count = "UDPR_1"                         # UDPR_1                            thread reg
            cur_kv_count = "UDPR_2"                     # UDPR_2                            thread reg
            intermediate_ptr = "UDPR_3"                 # UDPR_3                            thread reg
            reduce_left_count = "UDPR_4"                # UDPR_4                            thread reg
            claim_work_cont = "UDPR_11"                 # UDPR_11                           thread reg
            saved_cont = self.saved_cont                # UDPR_15                           thread reg


            inter_key       = "OB_0"
            inter_values    = [f"OB_{n+1}" for n in range((self.inter_kvpair_size) - 1)]

            tran.writeAction(f"print 'Lane %u reduces key %u value %llu' X0 OB_0 OB_1")

            self.kv_reduce(tran, inter_key, inter_values, ln_reduce_th_ret_ev_label, 
                ["UDPR_0", "UDPR_12", "UDPR_13", "UDPR_14"] + [f"UDPR_{i}" for i in range(5, 11)])

        else:

            inter_key       = "OB_0"
            inter_values    = [f"OB_{n+1}" for n in range((self.inter_kvpair_size) - 1)]

            temp_value      = self.scratch[0]           # UDPR_12               local reg
            scratch_1       = self.scratch[1]           # UDPR_13               local reg
            lm_base_reg     = self.scratch[1]           # UDPR_13               local reg
            ev_word = self.ev_word                      # UDPR_14               local reg
            
            max_th_label = "push_back_to_queue"

            # Check the thread name space usage
            if self.debug_flag and self.print_level > 2:
                tran.writeAction(f"print ' '")
                tran.writeAction(f"print '[DEBUG][NWID %d] Event <lane_reduce_thread> ev_word = %d income_cont = %d' {'X0'} {'EQT'} {'X1'}")
            lm_base_reg = self.__get_lm_base(tran, lm_base_reg)
            tran.writeAction(f"move {self.num_reduce_th_offset}({lm_base_reg}) {temp_value} 0 8")
            tran.writeAction(f"bgei {temp_value} {self.max_reduce_th_per_lane} {max_th_label}")
            tran.writeAction(f"addi {temp_value} {temp_value} 1")
            tran.writeAction(f"move {temp_value}  {self.num_reduce_th_offset}({scratch_1}) 0 8")

            self.kv_reduce(tran, inter_key, inter_values, ln_reduce_th_ret_ev_label)

            tran.writeAction(f"{max_th_label}: ev_update_1 EQT {ev_word} {255} {0b0100}")
            tran.writeAction(f"sendops_wcont {ev_word} X1 {'OB_0'} {self.inter_kvpair_size}")
            tran.writeAction(f"yield_terminate")

        return

    def __gen_reduce_ret(self, tran):


        if self.extension == self.AvailableExtensions.lb_test:
            ln_worker_work_ev_label = self.get_event_mapping(f"worker_work")

            kv_count = "UDPR_1"                         # UDPR_1                            thread reg
            cur_kv_count = "UDPR_2"                     # UDPR_2                            thread reg
            intermediate_ptr = "UDPR_3"                 # UDPR_3                            thread reg
            reduce_left_count = "UDPR_4"                # UDPR_4                            thread reg
            claim_work_cont = "UDPR_11"                 # UDPR_11                           thread reg
            saved_cont = self.saved_cont                # UDPR_15                           thread reg

            tid = "UDPR_14"                             # UDPR_10                           local reg
            scratch = self.scratch                      # UDPR_12, UDPR_13                  local reg
            ev_word = self.ev_word                      # UDPR_14                           local reg

            tran.writeAction(f"addi X7 {scratch[1]} {0}")
            tran.writeAction(f"movlr {self.local_tid_cache_offset + WORD_SIZE}({scratch[1]}) {scratch[0]} 0 8")
            tran.writeAction(f"movir {tid} {0xFF}")
            tran.writeAction(f"srandi X2 {tid} {24}")
            tran.writeAction(f"bne {tid} {scratch[0]} redirected_reducer")

            tran.writeAction(f"subi {reduce_left_count} {reduce_left_count} 1")

            tran.writeAction(f"bgti {reduce_left_count} 0 waiting_for_reducers")
            tran.writeAction(f"addi X7 {scratch[1]} 0")
            tran.writeAction(f"movlr {self.assert_claimed_key_offset}({scratch[1]}) {scratch[0]} 0 {WORD_SIZE}")
            tran.writeAction(f"bnei {scratch[0]} 2 waiting_for_reducers")

            tran.writeAction(f"addi X2 {ev_word} 0")
            tran.writeAction(f"evlb {ev_word} {ln_worker_work_ev_label}")
            tran.writeAction(f"movir {scratch[0]} 654321")
            tran.writeAction(f"sendr_wcont {ev_word} X2 {scratch[0]} {scratch[0]}")
            tran.writeAction(f"waiting_for_reducers: yield")

            tran.writeAction(f"redirected_reducer: yieldt")

        else:

            temp_value      = self.scratch[0]           # UDPR_12               local reg
            scratch_1       = self.scratch[1]           # UDPR_13               local reg
            lm_base_reg     = self.scratch[1]           # UDPR_13               local reg


            if self.debug_flag and self.print_level > 2:
                tran.writeAction(f"print ' '")
                tran.writeAction(f"print '[DEBUG][NWID %d] Event <lane_reduce_thread_return> ev_word = %d income_cont = %d' {'X0'} {'EQT'} {'X1'}")
            lm_base_reg = self.__get_lm_base(tran, lm_base_reg)
            tran.writeAction(f"addi {lm_base_reg} {scratch_1} 0")
            # Increment the number of reduce tasks processed
            tran.writeAction(f"move {self.reduce_ctr_offset}({scratch_1}) {temp_value} 0 8")
            tran.writeAction(f"addi {temp_value} {temp_value} 1")
            tran.writeAction(f"move {temp_value} {self.reduce_ctr_offset}({scratch_1}) 0 8")
            if self.debug_flag and self.print_level > 2:
                tran.writeAction(f"print '[DEBUG][NWID %d] Lane %d processed %d reduce tasks' {'X0'} {'X0'} {temp_value}")

            # Decrement the number of active reduce threads
            tran.writeAction(f"move {self.num_reduce_th_offset}({scratch_1}) {temp_value} 0 8")
            tran.writeAction(f"subi {temp_value} {temp_value} 1")
            tran.writeAction(f"move {temp_value}  {self.num_reduce_th_offset}({scratch_1}) 0 8")
            if self.debug_flag and self.print_level > 2:
                tran.writeAction(f"print '[DEBUG][NWID %d] Lane %d has %d reduce thread remain active' {'X0'} {'X0'} {temp_value}")

            tran.writeAction("yield_terminate")

    ####### Load balancer events #######
    #   TODO: unfinished
    def __gen_reduce_receive_kv(self, tran):

        scratch_0 = self.scratch[0]                 # UDPR_12               local reg
        lm_base_reg     = self.scratch[1]           # UDPR_13               local reg

        lm_base_reg = self.__get_lm_base(tran, lm_base_reg)
        tran.writeAction(f"movir {scratch_0} {self.ob_cache_offset}")
        tran.writeAction(f"add {lm_base_reg} {scratch_0} {scratch_0}")
        for i in range(self.intermediate_kvpair_size):
            tran.writeAction(f"movrl OB_{i} {8*i}({scratch_0}) 0 8")
        # TODO: store the intermediate kv pair into dram
        self.intermediate_kvset.store(tran, scratch_0, self.intermediate_kvset)
        tran.writeAction("yield")

        return
    ##### End Load balancer events #####
    


    ###     Worker thread, same thread as map thread
    def __gen_worker_work(self, tran):

        '''
        Event: worker event after mapper is finished
        Operands:   if returned from lane_master_loop
                        OB_0:   123456  checking flag for the first time this event is envoked
                        OB_1:   event word of the claim work event
                        OB_2:   event word of lane master loop

                    if returned from claim work
                        OB_0:   if == self._finish_flag, no keys left in the dram
                                else, the key of the intermediate kv
                        OB_1~n: the values

                    if returned from fetched_kv_pair
                        OB_0:   654321, jump to claim_work
        '''

        ln_map_th_term_ev_label  = self.get_event_mapping(f"terminate_lane_map_thread")
        ln_worker_fetched_key_ev_label = self.get_event_mapping("worker_fetched_key")

        kv_count = "UDPR_1"                         # UDPR_1                            thread reg
        cur_kv_count = "UDPR_2"                     # UDPR_2                            thread reg
        intermediate_ptr = "UDPR_3"                 # UDPR_3                            thread reg
        reduce_left_count = "UDPR_4"                # UDPR_4                            thread reg
        claiming_work = "UDPR_5"                    # UDPR_5                            thread reg
        claim_work_cont = "UDPR_11"                 #                                   thread reg
        saved_cont = self.saved_cont                # UDPR_15                           thread reg

        scratch = self.scratch                      # UDPR_12, UDPR_13                  local reg
        ev_word = self.ev_word                      # UDPR_14                           local reg

        str_kv_regs = " ".join([f"OB_{i}" for i in range(self.intermediate_kvpair_size)])

        # If OB_0 == 123456
        # First time this event is launched
        tran.writeAction(f"movir {scratch[0]} 123456")
        tran.writeAction(f"bne OB_0 {scratch[0]} after_set_claim_work_cont")
        tran.writeAction(f"addi OB_2 {saved_cont} 0")
        tran.writeAction(f"addi OB_1 {claim_work_cont} 0")
        tran.writeAction(f"movir {reduce_left_count} 0")
        tran.writeAction(f"movir {claiming_work} 0")
        tran.writeAction(f"jmp claim_work")

        # If not the first time, keep checking OB_0
        tran.writeAction(f"after_set_claim_work_cont: beqi OB_0 {self._finish_flag} reduce_finished")
        tran.writeAction(f"movir {scratch[0]} 654321 ")
        tran.writeAction(f"beq OB_0 {scratch[0]} claim_work")
        # tran.writeAction(f"movir {scratch[0]} {self._map_flag}")
        # tran.writeAction(f"beq OB_0 {scratch[0]} received_input_kv_ptr")

        # If OB_0 not in [123456, 654321, self._finish_flag, self._map_flag]
        # Returned from global claimed work
        # Set claiming_work bit to 0
        # OB_0 = self._reduce_flag
        # OB_1 = ptr to key in dram
        # Fetch the key and send it to worker_fetched_key
        lm_reg = self.__get_lm_base(tran, scratch[1])
        tran.writeAction(f"movrl OB_1 {self.claimed_key_ptr_offset}({lm_reg}) 0 {WORD_SIZE}")
        tran.writeAction(f"send_dmlm_ld_wret OB_1 {ln_worker_fetched_key_ev_label} 1 {scratch[0]}")
        tran.writeAction(f"movir {claiming_work} 0")
        tran.writeAction(f"yield")


        # If OB_0 == 123456 or 654321
        # Either first time or returned from global claim work
        # If not currently claiming work, call claim work, set assert_claimed_key_flag = 0 and claiming_work = 1
        tran.writeAction(f"claim_work: beqi {claiming_work} 1 claiming_work")
        tran.writeAction(f"sendr_wcont {claim_work_cont} X2 {scratch[0]} {scratch[0]}")
        tran.writeAction(f"movir {claiming_work} 1")
        tran.writeAction(f"movir {scratch[0]} 0")
        lm_reg = self.__get_lm_base(tran, scratch[1])
        tran.writeAction(f"movrl {scratch[0]} {self.assert_claimed_key_offset}({lm_reg}) 0 {WORD_SIZE}")
        tran.writeAction(f"claiming_work: yield")

        # If OB_0 == self._finished_flag
        # Returned from global claim work but all intermediate kv are resolved
        # Entering terminating sequence
        # Check if all left reduce tasks have finished
        # If not, spin lock
        tran.writeAction(f"reduce_finished: bgti {reduce_left_count} 0 reduce_not_all_finished")
        tran.writeAction(f"addi X2 {ev_word} 0")
        tran.writeAction(f"evlb {ev_word} {ln_map_th_term_ev_label}")
        tran.writeAction(f"sendr_wcont {saved_cont} X2 OB_0 OB_0")
        tran.writeAction(f"sendr_wcont {ev_word} X2 OB_0 OB_0")
        tran.writeAction(f"yield")

        tran.writeAction(f"reduce_not_all_finished: sendr_wcont X2 X1 OB_0 OB_1")
        tran.writeAction(f"yield")

        return

    def __gen_worker_fetched_key(self, tran):
        '''
        Event:      return from dram request sent by worker_work
        Operands:   OB_0:   claimed key
        '''
    
        ln_worker_fetched_kv_ptr_ev_label = self.get_event_mapping("worker_fetched_kv_ptr")
        ln_worker_update_claimed_key_ev_label = self.get_event_mapping("worker_update_claimed_key")
        ln_worker_assert_claimed_key_ev_label = self.get_event_mapping("worker_assert_claimed_key")
        ln_reduce_th_ev_label = self.get_event_mapping("init_lane_reduce_thread")

        kv_count = "UDPR_1"                         # UDPR_1                            thread reg
        cur_kv_count = "UDPR_2"                     # UDPR_2                            thread reg
        intermediate_ptr = "UDPR_3"                 # UDPR_3                            thread reg
        reduce_left_count = "UDPR_4"                # UDPR_4                            thread reg
        claiming_work = "UDPR_5"                    # UDPR_5                            thread reg
        claim_work_cont = "UDPR_11"                 #                                   thread reg
        saved_cont = self.saved_cont                # UDPR_15                           thread reg

        cont_word = "UDPR_9"                        # UDPR_9
        intermediate_ptr = "UDPR_10"                # UDPR_10                           local reg
        scratch = self.scratch                      # UDPR_12, UDPR_13                  local reg
        ev_word = self.ev_word                      # UDPR_14                           local reg

        tran.writeAction(f"print '        key %u claimed by lane %u' OB_0 X0")

        # Send dram request to read intermediate kv
        tran.writeAction(f"movir {scratch[0]} {self.intermediate_ptr_offset}")
        lm_reg = self.__get_lm_base(tran, scratch[1])
        tran.writeAction(f"add {scratch[0]} {lm_reg} {lm_reg} ")
        tran.writeAction(f"movlr 0({lm_reg}) {intermediate_ptr} 0 8")

        tran.writeAction(f"muli OB_0 {scratch[0]} {2*WORD_SIZE}")
        tran.writeAction(f"add {intermediate_ptr} {scratch[0]} {intermediate_ptr}")
        tran.writeAction(f"send_dmlm_ld_wret {intermediate_ptr} {ln_worker_fetched_kv_ptr_ev_label} 2 {scratch[0]}")

        # Send message to static hashed lane indicating this thread has claimed the key
        self.kv_reduce_loc(tran, "OB_0", scratch[1])
        tran.writeAction(f"evii {ev_word} {ln_worker_update_claimed_key_ev_label} 255 5")
        tran.writeAction(f"ev {ev_word}  {ev_word}  {scratch[1]} {scratch[1]} 8")
        tran.writeAction(f"evii {cont_word} {ln_worker_assert_claimed_key_ev_label} 255 5")
        tran.writeAction(f"evi X2 {scratch[0]} {ln_reduce_th_ev_label} 1")
        tran.writeAction(f"sendr_wcont {ev_word} {cont_word} OB_0 {scratch[0]}")

        tran.writeAction(f"movir {cur_kv_count} 0")

        tran.writeAction(f"yield")

        return

    def __gen_worker_fetched_kv_ptr(self, tran):
        '''
        Event:      Three returned situation
                    1)  returned from dram read request sent by fetched_key / this event
                        OB_0: Count of kv pairs
                        OB_1: Dram Pointer to kv array
                        OB_2: Dram Pointer to the entry [OB_0, OB_1]
                    2)  returned from spin lock of this event, 
                        waiting for asserting claimed_key from static hashed lane
                        OB_0: 654321
        '''

        ln_worker_work_ev_label = self.get_event_mapping(f"worker_work")
        ln_reduce_th_ev_label = self.get_event_mapping("init_lane_reduce_thread")

        kv_count = "UDPR_1"                         # UDPR_1                            thread reg
        cur_kv_count = "UDPR_2"                     # UDPR_2                            thread reg
        intermediate_ptr = "UDPR_3"                 # UDPR_3                            thread reg
        reduce_left_count = "UDPR_4"                # UDPR_4                            thread reg
        claiming_work = "UDPR_5"                    # UDPR_5                            thread reg
        claim_work_cont = "UDPR_11"                 # UDPR_11                           thread reg
        saved_cont = self.saved_cont                # UDPR_15                           thread reg

        scratch = self.scratch                      # UDPR_12, UDPR_13                  local reg
        ev_word = self.ev_word                      # UDPR_14                           local reg

        # If returned from spin lock,
        # indicating the materialized count read from dram is all resolved
        # check assert_claimed_key bit
        tran.writeAction(f"movir {scratch[0]} 654321")
        tran.writeAction(f"beq OB_0 {scratch[0]} claimed_kv_resolved")

        # If return from dram read request
        # Update the materialized count and cache pointer to the entry
        tran.writeAction(f"addi OB_0 {kv_count} 0")
        tran.writeAction(f"addi OB_2 {intermediate_ptr} 0")

        # cur_kv_count == number of dram request has been sent to read kvs
        # kv_count == updated count of materialized kvs
        # If cur_kv_count != kv_count, then there are materialized kvs need to be read, start resolving
        # Else, the materialized count read from dram is all resolved
        # check assert_claimed_key bit
        tran.writeAction(f"resolving_kv: beq {cur_kv_count} {kv_count} claimed_kv_resolved")
        tran.writeAction(f"muli {cur_kv_count} {scratch[1]} {self.intermediate_kvpair_size * WORD_SIZE}")
        tran.writeAction(f"add OB_1 {scratch[1]} {scratch[1]}")
        tran.writeAction(f"send_dmlm_ld_wret {scratch[1]} {ln_reduce_th_ev_label} {self.intermediate_kvpair_size} {scratch[0]}")
        tran.writeAction(f"addi {scratch[1]} {scratch[1]} {self.intermediate_kvpair_size * WORD_SIZE}")
        tran.writeAction(f"addi {reduce_left_count} {reduce_left_count} 1")
        tran.writeAction(f"addi {cur_kv_count} {cur_kv_count} 1")
        tran.writeAction(f"jmp resolving_kv")

        # The materialized count read from dram is all resolved
        # Check assert_claimed_key bit
        tran.writeAction(f"claimed_kv_resolved: addi X7 {scratch[1]} 0")
        tran.writeAction(f"movlr {self.assert_claimed_key_offset}({scratch[1]}) {scratch[0]} 0 {WORD_SIZE}")
        tran.writeAction(f"beqi {scratch[0]} 1 asserted_claimed_key")
        tran.writeAction(f"beqi {scratch[0]} 2 updated_kv_count")
        tran.writeAction(f"movir {scratch[0]} 654321")
        tran.writeAction(f"sendr_wcont X2 X1 {scratch[0]} {scratch[0]}")
        tran.writeAction(f"yield")

        # If assert_claimed_key bit == 1
        # Meaning the assertation message from static hashed lane has come back
        # Read the most current materialized count from dram
        # And set assert_claimed_key bit to 2
        tran.writeAction(f"asserted_claimed_key: addi X7 {scratch[1]} 0")
        tran.writeAction(f"send_dmlm_ld {intermediate_ptr} X2 {2}")
        tran.writeAction(f"addi X7 {scratch[1]} 0")
        tran.writeAction(f"movir {scratch[0]} 2")
        tran.writeAction(f"movrl {scratch[0]} {self.assert_claimed_key_offset}({scratch[1]}) 0 {WORD_SIZE}")
        tran.writeAction(f"yield")

        # If assert_claimed_key bit == 2
        # Meaning all materialized kvs are resolved
        # Send message to worker_work to claim work
        
        tran.writeAction(f"updated_kv_count: bgti {reduce_left_count} 0 waiting_for_reducers")

        tran.writeAction(f"addi X2 {ev_word} 0")
        tran.writeAction(f"evlb {ev_word} {ln_worker_work_ev_label}")
        tran.writeAction(f"movir {scratch[0]} 654321")
        tran.writeAction(f"sendr_wcont {ev_word} X2 {scratch[0]} {scratch[0]}")
        tran.writeAction(f"waiting_for_reducers: yield")

    def __gen_worker_materialize_ret(self, tran):
        tran.writeAction(f"yield")
        return

    ##############################################################################





    ##############################################################################
    '''
    Thread/Event functions of helper threads that receive kvs from kv_emit and process them
    '''

    def __gen_helper_worker_thread(self):
        ln_worker_receive_kv_ev_label = self.get_event_mapping(f"worker_receive_intermediate_kv_pair")
        ln_worker_fetched_kv_ptr_for_cache_ev_label = self.get_event_mapping("worker_fetched_kv_ptr_for_cache")
        ln_worker_cache_materializing_kv_ev_label = self.get_event_mapping("worker_cache_materializing_kv")
        ln_helper_worker_materialize_ret_ev_label = self.get_event_mapping("helper_worker_materialize_ret")

        ln_worker_receive_kv_tran = self.state.writeTransition("eventCarry", self.state, self.state, ln_worker_receive_kv_ev_label)
        ln_worker_fetched_kv_ptr_for_cache_tran = self.state.writeTransition("eventCarry", self.state, self.state, ln_worker_fetched_kv_ptr_for_cache_ev_label)
        ln_worker_cache_materializing_kv_tran = self.state.writeTransition("eventCarry", self.state, self.state, ln_worker_cache_materializing_kv_ev_label)
        ln_helper_worker_materialize_ret_tran = self.state.writeTransition("eventCarry", self.state, self.state, ln_helper_worker_materialize_ret_ev_label)

        self.__gen_worker_receive_kv(ln_worker_receive_kv_tran)
        self.__gen_worker_fetched_kv_ptr_for_cache(ln_worker_fetched_kv_ptr_for_cache_tran)
        self.__gen_worker_cache_materializing_kv(ln_worker_cache_materializing_kv_tran)
        self.__gen_helper_worker_materialize_ret(ln_helper_worker_materialize_ret_tran)

        return


    def __gen_worker_receive_kv(self, tran):

        '''
        Event:  returned from kv_emit, to decide whether materialize the intermediate kv or send to worker that claimed it
        Operands:   OB_0-n  intermediate kv pair

        2 cache space:
        intermediate_cache: Each entry contains three words, [key*, num_materialized, ptr to materize array]
                            key* here is key shifted left one bit, with lowest bit as is_claimed bit
        materialize_kv_cache: each entry contains self.intermediate_kvpair_size words, kv pairs to be materialized
        '''

        ln_helper_worker_matererialize_ret_ev_label = self.get_event_mapping("helper_worker_materialize_ret")
        glb_mstr_push_key_ev_label = self.get_event_mapping(f"master_global_push_key")
        ln_worker_cache_materializing_kv_ev_label = self.get_event_mapping("worker_cache_materializing_kv")
        ln_worker_fetched_kv_ptr_for_cache_ev_label = self.get_event_mapping("worker_fetched_kv_ptr_for_cache")

        materializing_cache_start = "UDPR_0"        # UDPR_0                            local reg
        materializing_cache_end = "UDPR_1"          # UDPR_1                            local reg
        materializing_cache_empty = "UDPR_2"        # UDPR_2                            local reg
        cache_count = "UDPR_6"                      # UDPR_6                            local reg
        addr = "UDPR_7"                             # UDPR_7                            local reg
        intermediate_ptr = "UDPR_8"                 # UDPR_8                            local reg
        is_claimed = "UDPR_9"                       # UDPR_9                            local reg
        key = "UDPR_10"                             # UDPR_10                           local reg
        scratch = self.scratch                      # [UDPR_12, UDPR_13]                local reg
        lm_reg = self.scratch[1]                    # UDPR_13                           local reg
        ev_word = self.ev_word                      # UDPR_14                           local reg

        
        tran.writeAction(f"print 'Lane %u receives key %u value %llu' X0 OB_0 OB_1")

        str_kv_regs = " ".join([f"OB_{i}" for i in range(self.intermediate_kvpair_size)])

        # Get number of keys that have been materialized
        tran.writeAction(f"movir {addr} {self.intermediate_cache_offset}")
        lm_reg = self.__get_lm_base(tran, lm_reg)
        tran.writeAction(f"add {lm_reg} {addr} {addr}")
        tran.writeAction(f"movlr 0({addr}) {cache_count} 1 8")

        # Locate returned key in the intermediate_cache
        tran.writeAction(f"find_cached_key: blei {cache_count} 0 cache_all_visited")
        tran.writeAction(f"movlr 0({addr}) {key} 1 8")
        tran.writeAction(f"andi {key} {is_claimed} 1")
        tran.writeAction(f"sri {key} {key} 1")
        tran.writeAction(f"beq {key} OB_0 cache_hit")
        tran.writeAction(f"addi {addr} {addr} {2*WORD_SIZE}")
        tran.writeAction(f"subi {cache_count} {cache_count} 1")
        tran.writeAction(f"jmp find_cached_key")

        # If found, check if the key is claimed
        # if claimed, send the intermediate kv to cached location
        # if not claimed, check if the materializing pointer is cached
        tran.writeAction(f"cache_hit: beqi {is_claimed} 0 check_materializing_ptr")
        # if claimed, send to cached event word
        tran.writeAction(f"movlr 0({addr}) {ev_word} 1 8")
        tran.writeAction(f"evi {ev_word} {ev_word} 255 4")
        tran.writeAction(f"sendops_wcont {ev_word} X2 OB_0 {self.intermediate_kvpair_size}")
        tran.writeAction(f"yieldt")

        # If found but not claimed, check if the materializing pointer is cached
        num = key                       # UDPR_10                           local reg
        tran.writeAction(f"check_materializing_ptr: movlr 0({addr}) {num} 0 {WORD_SIZE}")
        # If the materializing pointer is cached, materialize the kv
        tran.writeAction(f"bgti {num} 0 store_kv")
        # If the materializing pointer is NOT cached, push the kv to the end of materializing cache
        tran.writeAction(f"jmp init_cache_kv")

        # If not found, 
        # 1. send dram request to fecth the stored number (should be 0) and materializing ptr
        tran.writeAction(f"cache_all_visited: movir {scratch[0]} {self.intermediate_ptr_offset}")
        lm_reg = self.__get_lm_base(tran, scratch[1])
        tran.writeAction(f"add {scratch[0]} {lm_reg} {lm_reg} ")
        tran.writeAction(f"movlr 0({lm_reg}) {intermediate_ptr} 0 8")
        tran.writeAction(f"muli OB_0 {scratch[0]} {self.intermediate_kvpair_size*8}")
        tran.writeAction(f"add {intermediate_ptr} {scratch[0]} {intermediate_ptr}")
        tran.writeAction(f"evii {ev_word} {ln_worker_fetched_kv_ptr_for_cache_ev_label} 255 5")
        tran.writeAction(f"send_dmlm_ld {intermediate_ptr} {ev_word} 2")

        # 2. send the key to global master to push it into queue
        lm_reg = self.__get_lm_base(tran, lm_reg)
        tran.writeAction(f"movlr {self.push_key_cont_offset}({lm_reg}) {ev_word} 0 8")
        tran.writeAction(f"sendr_wcont {ev_word} X2 OB_0 OB_0")

        # 3. set is_claim bit to 0
        tran.writeAction(f"sli OB_0 {key} 1")

        # 4. cache the key in scratchpad at the end of the intermediate_cache
        lm_reg = self.__get_lm_base(tran, lm_reg)
        tran.writeAction(f"movir {scratch[0]} {self.intermediate_cache_offset}")
        tran.writeAction(f"add {lm_reg} {scratch[0]} {scratch[0]}")
        # Update cached key count
        tran.writeAction(f"movlr 0({scratch[0]}) {scratch[1]} 0 8")
        tran.writeAction(f"addi {scratch[1]} {scratch[1]} 1")
        tran.writeAction(f"movrl {scratch[1]} 0({scratch[0]}) 1 8")
        # Cache new key
        tran.writeAction(f"subi {scratch[1]} {scratch[1]} 1")
        tran.writeAction(f"muli {scratch[1]} {scratch[1]} {3*WORD_SIZE}")
        tran.writeAction(f"add {scratch[0]} {scratch[1]} {scratch[0]}")
        tran.writeAction(f"movrl {key} 0({scratch[0]}) 1 8")
        # Set number materialized as 0 indicating materializing address hasn't returned
        tran.writeAction(f"movir {key} 0")
        tran.writeAction(f"movrl {key} 0({scratch[0]}) 1 8")

        # 5. push the kv to the end of materializing cache
        #    and fetch the stored number (should be 0) and materializing ptr (By setting 0 in OB_0)
        tran.writeAction(f"init_cache_kv: movir {scratch[0]} {self.materializing_metadata_offset}")
        lm_reg = self.__get_lm_base(tran, scratch[1])
        tran.writeAction(f"add {lm_reg} {scratch[0]} {scratch[0]}")
        tran.writeAction(f"movlr 0({scratch[0]}) {materializing_cache_start} 0 {WORD_SIZE}")
        tran.writeAction(f"movlr {WORD_SIZE}({scratch[0]}) {materializing_cache_end} 0 {WORD_SIZE}")
        tran.writeAction(f"movlr {WORD_SIZE * 2}({scratch[0]}) {materializing_cache_empty} 0 {WORD_SIZE}")

        #   If cache start equals the end, check if the cache is empty
        tran.writeAction(f"beq {materializing_cache_start} {materializing_cache_end} cache_start_equals_end")
        #   elif cache start larger than the end, meaning there is definitely space
        tran.writeAction(f"bgt {materializing_cache_start} {materializing_cache_end} cache_kv")
        #   elif cache start smaller than the end, check if end - start < cache_size
        tran.writeAction(f"sub {materializing_cache_end} {materializing_cache_start} {scratch[0]}")
        tran.writeAction(f"movir {scratch[1]} {self.materialize_kv_cache_size}")
        #   If end - start == cache_size, spin lock
        tran.writeAction(f"beq {scratch[0]} {scratch[1]} spin_lock")
        lm_reg = self.__get_lm_base(tran, scratch[1])
        tran.writeAction(f"movir {scratch[0]} {self.materialize_kv_cache_offset + self.materialize_kv_cache_size}")
        tran.writeAction(f"add {scratch[0]} {scratch[1]} {scratch[1]}")
        tran.writeAction(f"blt {materializing_cache_end} {scratch[1]} cache_kv")
        #   Elif end at limit, reset end to the front of cache space
        lm_reg = self.__get_lm_base(tran, scratch[1])
        tran.writeAction(f"movir {materializing_cache_end} {self.materialize_kv_cache_offset}")
        tran.writeAction(f"add {lm_reg} {materializing_cache_end} {materializing_cache_end}")
        tran.writeAction(f"jmp cache_kv")

        tran.writeAction(f"cache_start_equals_end: beqi {materializing_cache_empty} 0 spin_lock")
        lm_reg = self.__get_lm_base(tran, scratch[1])
        tran.writeAction(f"movir {scratch[0]} {self.materialize_kv_cache_offset + self.materialize_kv_cache_size}")
        tran.writeAction(f"add {lm_reg} {scratch[0]} {scratch[0]}")
        tran.writeAction(f"blt {materializing_cache_end} {scratch[0]} cache_kv")

        # If start and end both at limit, reset them to the front of cache space
        tran.writeAction(f"movir {materializing_cache_start} {self.materialize_kv_cache_offset}")
        tran.writeAction(f"add {lm_reg} {materializing_cache_start} {materializing_cache_start}")
        tran.writeAction(f"movir {materializing_cache_end} {self.materialize_kv_cache_offset}")
        tran.writeAction(f"add {lm_reg} {materializing_cache_end} {materializing_cache_end}")
        tran.writeAction(f"jmp cache_kv")

        tran.writeAction(f"spin_lock: evi X2 {ev_word} 255 4")
        tran.writeAction(f"sendops_wcont {ev_word} X1 OB_0 {self.intermediate_kvpair_size}")
        tran.writeAction(f"yieldt")

        tran.writeAction(f"cache_kv: movrl OB_0 0({materializing_cache_end}) 1 {WORD_SIZE}")
        for i in range(1, self.intermediate_kvpair_size):
            tran.writeAction(f"movrl OB_{i} 0({materializing_cache_end}) 1 {WORD_SIZE}")
        tran.writeAction(f"beqi {materializing_cache_empty} 0 after_cache")
        tran.writeAction(f"movir {materializing_cache_empty} 0")


        # After caching the entry
        # Update the materialize_cache meta data in spd
        tran.writeAction(f"after_cache: movir {scratch[0]} {self.materializing_metadata_offset}")
        lm_reg = self.__get_lm_base(tran, scratch[1])
        tran.writeAction(f"add {lm_reg} {scratch[0]} {lm_reg}")
        tran.writeAction(f"movrl {materializing_cache_start} 0({lm_reg}) 1 {WORD_SIZE}")
        tran.writeAction(f"movrl {materializing_cache_end} 0({lm_reg}) 1 {WORD_SIZE}")
        tran.writeAction(f"movrl {materializing_cache_empty} 0({lm_reg}) 1 {WORD_SIZE}")

        tran.writeAction(f"yieldt")



        # If the materializing pointer is cached, materialize the kv and update stored number in dram
        tran.writeAction(f"store_kv: addi {num} {num} 1")
        tran.writeAction(f"movrl {num} 0({addr}) 1 {WORD_SIZE}")
        tran.writeAction(f"movlr 0({addr}) {scratch[1]} 0 {WORD_SIZE}")
        tran.writeAction(f"evii {ev_word} {ln_helper_worker_matererialize_ret_ev_label} 255 5")
        # tran.writeAction(f"sendops_dmlm {scratch[1]} {ev_word} OB_0 {self.intermediate_kvpair_size}")         # TODO: REPLACE WITH SENDMOPS
        tran.writeAction(f"sendr2_dmlm {scratch[1]} {ev_word} OB_0 OB_1")
        tran.writeAction(f"addi {scratch[1]} {scratch[1]} {WORD_SIZE * self.intermediate_kvpair_size}")
        tran.writeAction(f"movrl {scratch[1]} 0({addr}) 1 {WORD_SIZE}")

        tran.writeAction(f"movir {scratch[0]} {self.intermediate_ptr_offset}")
        lm_reg = self.__get_lm_base(tran, lm_reg)
        tran.writeAction(f"add {scratch[0]} {lm_reg} {lm_reg} ")
        tran.writeAction(f"movlr 0({lm_reg}) {intermediate_ptr} 0 8")
        tran.writeAction(f"muli OB_0 {scratch[0]} {self.intermediate_kvpair_size*8}")
        tran.writeAction(f"add {intermediate_ptr} {scratch[0]} {intermediate_ptr}")
        tran.writeAction(f"sendr_dmlm {intermediate_ptr} {ev_word} {num}")

        tran.writeAction("yieldt")

        return

    def __gen_worker_cache_materializing_kv(self, tran):
        '''
        Event:  returned from worker_receive_kv
                to push the intermediate kv into materialize_kv_cache if there is space
                spin lock otherwise
        Operands:   OB_0      0 indicating first kv pair associated with this key
                              1 indicating a message requesting the materializing ptr is already sent
                    OB_1-n+1  intermediate kv pair

        Cache space:
        materialize_kv_cache: each entry contains self.intermediate_kvpair_size words, kv pairs to be materialized
        '''

        ln_worker_fetched_kv_ptr_for_cache_ev_label = self.get_event_mapping("worker_fetched_kv_ptr_for_cache")

        materializing_cache_start = "UDPR_0"        # UDPR_0                            local reg
        materializing_cache_end = "UDPR_1"          # UDPR_1                            local reg
        materializing_cache_empty = "UDPR_2"        # UDPR_2                            local reg
        dram_req_count = "UDPR_3"                   # UDPR_3                            thread reg

        intermediate_ptr = "UDPR_10"                # UDPR_10                           local reg
        scratch = self.scratch                      # [UDPR_12, UDPR_13]                local reg
        ev_word = self.ev_word                      #                                   local reg

        # Load thread regs from scratchpad

        lm_reg = self.__get_lm_base(tran, scratch[1])
        tran.writeAction(f"movir {scratch[0]} {self.materializing_metadata_offset}")
        tran.writeAction(f"add {lm_reg} {scratch[0]} {scratch[0]}")
        tran.writeAction(f"movlr 0({scratch[0]}) {materializing_cache_start} 0 {WORD_SIZE}")
        tran.writeAction(f"movlr {WORD_SIZE}({scratch[0]}) {materializing_cache_end} 0 {WORD_SIZE}")
        tran.writeAction(f"movlr {WORD_SIZE * 2}({scratch[0]}) {materializing_cache_empty} 0 {WORD_SIZE}")

        #   If cache start equals the end, check if the cache is empty
        tran.writeAction(f"beq {materializing_cache_start} {materializing_cache_end} cache_start_equals_end")
        #   elif cache start larger than the end, meaning there is definitely space
        tran.writeAction(f"bgt {materializing_cache_start} {materializing_cache_end} cache_kv")
        #   elif cache start smaller than the end, check if end - start < cache_size
        tran.writeAction(f"sub {materializing_cache_end} {materializing_cache_start} {scratch[0]}")
        tran.writeAction(f"movir {scratch[1]} {self.materialize_kv_cache_size}")
        #   If end - start == cache_size, spin lock
        tran.writeAction(f"beq {scratch[0]} {scratch[1]} spin_lock")
        lm_reg = self.__get_lm_base(tran, scratch[1])
        tran.writeAction(f"movir {scratch[0]} {self.materialize_kv_cache_offset + self.materialize_kv_cache_size}")
        tran.writeAction(f"add {scratch[0]} {scratch[1]} {scratch[1]}")
        tran.writeAction(f"blt {materializing_cache_end} {scratch[1]} cache_kv")
        #   Elif end at limit, reset end to the front of cache space
        lm_reg = self.__get_lm_base(tran, scratch[1])
        tran.writeAction(f"movir {materializing_cache_end} {self.materialize_kv_cache_offset}")
        tran.writeAction(f"add {lm_reg} {materializing_cache_end} {materializing_cache_end}")
        tran.writeAction(f"jmp cache_kv")

        tran.writeAction(f"cache_start_equals_end: beqi {materializing_cache_empty} 0 spin_lock")
        lm_reg = self.__get_lm_base(tran, scratch[1])
        tran.writeAction(f"movir {scratch[0]} {self.materialize_kv_cache_offset + self.materialize_kv_cache_size}")
        tran.writeAction(f"add {lm_reg} {scratch[0]} {scratch[0]}")
        tran.writeAction(f"blt {materializing_cache_end} {scratch[0]} cache_kv")

        # If start and end both at limit, reset them to the front of cache space
        tran.writeAction(f"movir {materializing_cache_start} {self.materialize_kv_cache_offset}")
        tran.writeAction(f"add {lm_reg} {materializing_cache_start} {materializing_cache_start}")
        tran.writeAction(f"movir {materializing_cache_end} {self.materialize_kv_cache_offset}")
        tran.writeAction(f"add {lm_reg} {materializing_cache_end} {materializing_cache_end}")
        tran.writeAction(f"jmp cache_kv")

        tran.writeAction(f"spin_lock: evi X2 {ev_word} 255 4")
        tran.writeAction(f"sendops_wcont {ev_word} X1 OB_0 {self.intermediate_kvpair_size + 1}")
        tran.writeAction(f"yieldt")

        tran.writeAction(f"cache_kv: movrl OB_1 0({materializing_cache_end}) 1 {WORD_SIZE}")
        for i in range(1, self.intermediate_kvpair_size):
            tran.writeAction(f"movrl OB_{i+1} 0({materializing_cache_end}) 1 {WORD_SIZE}")
        tran.writeAction(f"beqi {materializing_cache_empty} 0 after_cache")
        tran.writeAction(f"movir {materializing_cache_empty} 0")


        # After caching the entry
        # 1. Update the materialize_cache meta data in spd
        tran.writeAction(f"after_cache: movir {scratch[0]} {self.materializing_metadata_offset}")
        lm_reg = self.__get_lm_base(tran, scratch[1])
        tran.writeAction(f"add {lm_reg} {scratch[0]} {lm_reg}")
        tran.writeAction(f"movrl {materializing_cache_start} 0({lm_reg}) 1 {WORD_SIZE}")
        tran.writeAction(f"movrl {materializing_cache_end} 0({lm_reg}) 1 {WORD_SIZE}")
        tran.writeAction(f"movrl {materializing_cache_empty} 0({lm_reg}) 1 {WORD_SIZE}")

        # 2. if OB_0 != 0, terminate the thread
        tran.writeAction(f"bnei OB_0 0 no_dram_request")

        # 3. if OB_0 == 0:
        # send dram request to fecth the stored number (should be 0) and materializing ptr
        tran.writeAction(f"movir {scratch[0]} {self.intermediate_ptr_offset}")
        lm_reg = self.__get_lm_base(tran, scratch[1])
        tran.writeAction(f"add {scratch[0]} {lm_reg} {lm_reg} ")
        tran.writeAction(f"movlr 0({lm_reg}) {intermediate_ptr} 0 8")
        tran.writeAction(f"muli OB_1 {scratch[0]} {self.intermediate_kvpair_size*8}")
        tran.writeAction(f"add {intermediate_ptr} {scratch[0]} {intermediate_ptr}")
        tran.writeAction(f"evii {scratch[1]} {ln_worker_fetched_kv_ptr_for_cache_ev_label} 255 5")
        tran.writeAction(f"send_dmlm_ld {intermediate_ptr} {scratch[1]} 2")

        tran.writeAction(f"no_dram_request: yieldt")

        return

    def __gen_worker_fetched_kv_ptr_for_cache(self, tran):
        '''
        Event:  returned from dram request sent by worker_cache_materializing_kv
                with information to materialize the kv pairs
        Operands:   OB_0: Count of kv pairs
                    OB_1: Pointer to kv array
                    OB_2: Dram address of the entry read in

        2 cache space:
        intermediate_cache: Each entry contains three words, [key*, num_materialized, ptr to materize array]
                            key* here is key shifted left one bit, with lowest bit as is_claimed bit
        materialize_kv_cache: each entry contains self.intermediate_kvpair_size words, kv pairs to be materialized
        '''

        ln_worker_matererialize_ret_ev_label = self.get_event_mapping("worker_materialize_ret")
        ln_helper_worker_materialize_ret_ev_label = self.get_event_mapping("helper_worker_materialize_ret")

        materializing_cache_start = "UDPR_0"        # UDPR_0                            local reg
        materializing_cache_end = "UDPR_1"          # UDPR_1                            local reg
        materializing_cache_empty = "UDPR_2"        # UDPR_2                            local reg
        dram_req_count = "UDPR_3"                   # UDPR_3                            thread reg

        entry_addr = "UDPR_6"                       #
        addr = "UDPR_7"                             # UDPR_7                            local reg
        returned_key = "UDPR_8"                     # UDPR_8                            local reg
        new_end = "UDPR_9"                          # UDPR_9                            local reg
        key = "UDPR_10"                             # UDPR_10                           local reg
        materializing_cache_limit = "UDPR_11"       # UDPR_11                           local reg
        scratch = self.scratch                      # [UDPR_12, UDPR_13]                local reg
        ev_word = self.ev_word                      # UDPR_14                           local reg


        # Load thread regs from scratchpad

        lm_reg = self.__get_lm_base(tran, scratch[1])
        tran.writeAction(f"movir {scratch[0]} {self.materializing_metadata_offset}")
        tran.writeAction(f"add {lm_reg} {scratch[0]} {scratch[0]}")
        tran.writeAction(f"movlr 0({scratch[0]}) {materializing_cache_start} 0 {WORD_SIZE}")
        tran.writeAction(f"movlr {WORD_SIZE}({scratch[0]}) {materializing_cache_end} 0 {WORD_SIZE}")
        tran.writeAction(f"movlr {WORD_SIZE * 2}({scratch[0]}) {materializing_cache_empty} 0 {WORD_SIZE}")
        tran.writeAction(f"movir {dram_req_count} 0")


        # Get the key returned
        lm_reg = self.__get_lm_base(tran, scratch[1])
        tran.writeAction(f"movir {scratch[0]} {self.intermediate_ptr_offset}")
        tran.writeAction(f"add {scratch[0]} {lm_reg} {lm_reg}")
        tran.writeAction(f"movlr 0({lm_reg}) {addr} 0 {WORD_SIZE}")
        tran.writeAction(f"sub OB_2 {addr} {scratch[0]}")
        tran.writeAction(f"divi {scratch[0]} {returned_key} {2*WORD_SIZE}")

        # Locate the entry in intermediate_cache
        lm_reg = self.__get_lm_base(tran, scratch[1])
        tran.writeAction(f"movir {addr} {self.intermediate_cache_offset}")
        tran.writeAction(f"add {lm_reg} {addr} {addr}")
        tran.writeAction(f"addi {addr} {addr} {WORD_SIZE}")

        tran.writeAction(f"find_cached_key: movlr 0({addr}) {key} 1 {WORD_SIZE}")
        tran.writeAction(f"sri {key} {key} 1")
        tran.writeAction(f"beq {key} {returned_key} entry_found")
        tran.writeAction(f"addi {addr} {addr} {2*WORD_SIZE}")
        tran.writeAction(f"jmp find_cached_key")

        # Update the entry in intermediate_cache
        tran.writeAction(f"entry_found: addi {addr} {entry_addr} 0")
        tran.writeAction(f"movrl OB_0 0({addr}) 1 {WORD_SIZE}")
        tran.writeAction(f"movrl OB_1 0({addr}) 1 {WORD_SIZE}")

        # Iterate over the materialize_kv_cache and materialize any entry with the same key
        tran.writeAction(f"addi {materializing_cache_start} {addr} 0")
        tran.writeAction(f"addi {materializing_cache_end} {new_end} 0")

        # Iterate from the beginning
        # First check if materializing_cache_start == materializing_cache_end but materializing_cache_empty == 0, i.e. cache is full
        tran.writeAction(f"bne {addr} {materializing_cache_end} iter_and_update_start")
        tran.writeAction(f"beqi {materializing_cache_empty} 0 iter_do_while")
        # If cache is empty, which is not supposed to happen, yield terminate
        tran.writeAction(f"yieldt")

        tran.writeAction(f"iter_and_update_start: beq {addr} {materializing_cache_end} iter_end")
        tran.writeAction(f"iter_do_while: movlr 0({addr}) {key} 0 {WORD_SIZE}")
        # If key matches, materialize and keep iterating
        # Update materialize count in spd
        tran.writeAction(f"bne {key} {returned_key} front_check_empty_entry")
        tran.writeAction(f"movlr 0({entry_addr}) {scratch[1]} 0 {WORD_SIZE}")
        tran.writeAction(f"addi {scratch[1]} {scratch[1]} 1")
        tran.writeAction(f"movrl {scratch[1]} 0({entry_addr}) 0 {WORD_SIZE}")
        # Update materialize ptr in spd
        tran.writeAction(f"movlr {WORD_SIZE}({entry_addr}) {scratch[1]} 0 {WORD_SIZE}")
        tran.writeAction(f"evii {ev_word} {ln_helper_worker_materialize_ret_ev_label} 255 5")
        tran.writeAction(f"send_dmlm {scratch[1]} {ev_word} {addr} {self.intermediate_kvpair_size}")
        tran.writeAction(f"addi {dram_req_count} {dram_req_count} 1")
        tran.writeAction(f"addi {scratch[1]} {scratch[1]} {WORD_SIZE * self.intermediate_kvpair_size}")
        tran.writeAction(f"movrl {scratch[1]} {WORD_SIZE}({entry_addr}) 0 {WORD_SIZE}")

        tran.writeAction(f"movir {scratch[0]} -1")
        for i in range(self.intermediate_kvpair_size):
            tran.writeAction(f"movrl {scratch[0]} {WORD_SIZE * i}({addr}) 0 {WORD_SIZE}")

        tran.writeAction(f"jmp front_proceed_to_next")
        # If key doesn't match, check if it's already materialized and set to -1 as default
        # If materialized, update materializing_cache_start and keep iterating
        # Else, stop updating materializing_cache_start, and iterate the rest of the cache
        tran.writeAction(f"front_check_empty_entry: bnei {key} -1 iter_rest")
        for i in range(self.intermediate_kvpair_size-1):
            tran.writeAction(f"movlr {8*(i+1)}({addr}) {key} 0 {WORD_SIZE}")
            tran.writeAction(f"bnei {key} -1 iter_rest")

        # Check if updated front of materialize_kv_cache is at limit before procceding to next iteration
        tran.writeAction(f"front_proceed_to_next: addi {addr} {addr} {self.intermediate_kvpair_size*WORD_SIZE}")
        tran.writeAction(f"addi {materializing_cache_start} {materializing_cache_start} {self.intermediate_kvpair_size*WORD_SIZE}")
        tran.writeAction(f"ble {materializing_cache_start} {materializing_cache_end} front_set")
        lm_reg = self.__get_lm_base(tran, scratch[1])
        tran.writeAction(f"movir {scratch[0]} {self.materialize_kv_cache_offset + self.materialize_kv_cache_size}")
        tran.writeAction(f"add {lm_reg} {scratch[0]} {scratch[0]}")
        tran.writeAction(f"blt {addr} {scratch[0]} front_set")
        tran.writeAction(f"movir {addr} {self.materialize_kv_cache_offset}")
        tran.writeAction(f"add {lm_reg} {addr} {addr}")
        tran.writeAction(f"addi {addr} {materializing_cache_start} 0")
        tran.writeAction(f"front_set: jmp iter_and_update_start")


        # Iterate the rest of the cache
        tran.writeAction(f"iter_rest: addi {addr} {addr} {self.intermediate_kvpair_size*WORD_SIZE}")
        tran.writeAction(f"addi {addr} {new_end} 0")
        lm_reg = self.__get_lm_base(tran, scratch[1])
        tran.writeAction(f"movir {scratch[0]} {self.materialize_kv_cache_offset + self.materialize_kv_cache_size}")
        tran.writeAction(f"add {lm_reg} {scratch[0]} {materializing_cache_limit}")

        # If reaches the end of cache, stop iterating
        tran.writeAction(f"iter_and_update_end: beq {addr} {materializing_cache_end} iter_end")
        # Change addr to start of cache space if it reaches limit
        tran.writeAction(f"blt {addr} {materializing_cache_limit} compare_key")
        lm_reg = self.__get_lm_base(tran, scratch[1])
        tran.writeAction(f"movir {scratch[0]} {self.materialize_kv_cache_offset }")
        tran.writeAction(f"add {lm_reg} {scratch[0]} {addr}")
        tran.writeAction(f"compare_key: movlr 0({addr}) {key} 0 {WORD_SIZE}")
        tran.writeAction(f"beq {key} {returned_key} cache_hit")
        # If key doesn't match, check if it's already materialized and set to -1 as default
        # If materialized, don't update potential new_end
        # Else, mark potential new_end
        tran.writeAction(f"bnei {key} -1 update_new_end")
        for i in range(self.intermediate_kvpair_size-1):
            tran.writeAction(f"movlr {8*(i+1)}({addr}) {key} 0 {WORD_SIZE}")
            tran.writeAction(f"bnei {key} -1 update_new_end")
        tran.writeAction(f"jmp end_proceed_to_next")

        tran.writeAction(f"update_new_end: addi {addr} {new_end} {self.intermediate_kvpair_size*WORD_SIZE}")

        tran.writeAction(f"end_proceed_to_next: addi {addr} {addr} {self.intermediate_kvpair_size*WORD_SIZE}")
        tran.writeAction(f"jmp iter_and_update_end")

        # If key matches, materialize, set all entries to -1, and keep iterating
        # Update materialize count in spd
        tran.writeAction(f"cache_hit: movlr 0({entry_addr}) {scratch[1]} 0 {WORD_SIZE}")
        tran.writeAction(f"addi {scratch[1]} {scratch[1]} 1")
        tran.writeAction(f"movrl {scratch[1]} 0({entry_addr}) 0 {WORD_SIZE}")
        # Update materialize ptr in spd
        tran.writeAction(f"movlr {WORD_SIZE}({entry_addr}) {scratch[1]} 0 {WORD_SIZE}")
        tran.writeAction(f"evii {ev_word} {ln_helper_worker_materialize_ret_ev_label} 255 5")
        tran.writeAction(f"send_dmlm {scratch[1]} {ev_word} {addr} {self.intermediate_kvpair_size}")
        tran.writeAction(f"addi {dram_req_count} {dram_req_count} 1")
        tran.writeAction(f"addi {scratch[1]} {scratch[1]} {WORD_SIZE * self.intermediate_kvpair_size}")
        tran.writeAction(f"movrl {scratch[1]} {WORD_SIZE}({entry_addr}) 0 {WORD_SIZE}")

        tran.writeAction(f"movir {scratch[0]} -1")
        for i in range(self.intermediate_kvpair_size):
            tran.writeAction(f"movrl {scratch[0]} {WORD_SIZE * i}({addr}) 0 {WORD_SIZE}")
        tran.writeAction(f"jmp end_proceed_to_next")


        # When reaches the end of cache, stop iterating
        # Update materializing_cache_end
        tran.writeAction(f"iter_end: addi {new_end} {materializing_cache_end} 0")
        tran.writeAction(f"bne {materializing_cache_start} {materializing_cache_end} event_end")
        tran.writeAction(f"movir {materializing_cache_empty} 1")
        # Send updated materialized count to dram
        tran.writeAction(f"event_end: movlr 0({entry_addr}) {scratch[1]} 0 {WORD_SIZE}")
        tran.writeAction(f"evii {ev_word} {ln_helper_worker_materialize_ret_ev_label} 255 5")
        tran.writeAction(f"sendr_dmlm OB_2 {ev_word} {scratch[1]}")
        tran.writeAction(f"addi {dram_req_count} {dram_req_count} 1")

        # Update the materialize_cache meta data in spd
        tran.writeAction(f"movir {scratch[0]} {self.materializing_metadata_offset}")
        lm_reg = self.__get_lm_base(tran, scratch[1])
        tran.writeAction(f"add {lm_reg} {scratch[0]} {lm_reg}")
        tran.writeAction(f"movrl {materializing_cache_start} 0({lm_reg}) 1 {WORD_SIZE}")
        tran.writeAction(f"movrl {materializing_cache_end} 0({lm_reg}) 1 {WORD_SIZE}")
        tran.writeAction(f"movrl {materializing_cache_empty} 0({lm_reg}) 1 {WORD_SIZE}")



        tran.writeAction(f"yieldt")

        return

    def __gen_helper_worker_materialize_ret(self, tran):

        dram_req_count = "UDPR_3"                   # UDPR_3                            thread reg

        # tran.writeAction(f"blei {dram_req_count} 1 all_dram_request_resolved")
        # tran.writeAction(f"subi {dram_req_count} {dram_req_count} 1")
        # tran.writeAction(f"yield")
        # tran.writeAction(f"all_dram_request_resolved: yieldt")

        tran.writeAction(f"yieldt")

        return

    ##############################################################################









    ###     Extra worker thread, assigning shuffled location

    def __gen_assign_shuffle_dest_thread(self):
        assign_shuffle_dest_ev_label = self.get_event_mapping("assign_shufle_dest")
        ln_worker_receive_kv_ev_label = self.get_event_mapping("worker_receive_intermediate_kv_pair")
        tran = self.state.writeTransition("eventCarry", self.state, self.state, assign_shuffle_dest_ev_label)


        '''
        Event: returned from kv_emit, assign a tid in current thread and send the intermediate kv pair to it
        '''

        th_count = "UDPR_0"
        dest_tid = "UDPR_1"
        ev_word = "UDPR_2"
        addr = "UDPR_3"
        
        tran.writeAction(f"movlr {self.local_tid_cache_offset}(X7) {th_count} 0 8")
        tran.writeAction(f"beqi {th_count} 0 no_worker_launched_yet")

        tran.writeAction(f"subi {th_count} {th_count} 1")
        tran.writeAction(f"and OB_0 {th_count} {addr}")
        tran.writeAction(f"addi {addr} {addr} 1")
        tran.writeAction(f"muli {addr} {addr} {WORD_SIZE}")
        tran.writeAction(f"add {addr} X7 {addr}")
        tran.writeAction(f"movlr {self.local_tid_cache_offset}({addr}) {dest_tid} 0 8")

        tran.writeAction(f"addi X2 {ev_word} 0")
        tran.writeAction(f"evlb {ev_word} {ln_worker_receive_kv_ev_label}")
        tran.writeAction(f"ev {ev_word} {ev_word} {dest_tid} {dest_tid} 4")
        tran.writeAction(f"sendops_wcont {ev_word} X1 OB_0 {self.intermediate_kvpair_size}")
        tran.writeAction(f"yieldt")

        tran.writeAction(f"no_worker_launched_yet: sendops_wcont X2 X1 OB_0 {self.intermediate_kvpair_size}")
        tran.writeAction(f"yield")

        return

    def __gen_worker_update_claimed_key_thread(self):

        '''
        Event: return from global claim work event, update a key that was claimed
        Operands:   OB_0    key
        '''

        ln_worker_assert_claimed_key_ev_label = self.get_event_mapping("worker_assert_claimed_key")
        ln_worker_update_claimed_key_ev_label = self.get_event_mapping("worker_update_claimed_key")
        tran = self.state.writeTransition("eventCarry", self.state, self.state, ln_worker_update_claimed_key_ev_label)


        cache_count = "UDPR_6"                      # UDPR_6                            local reg
        addr = "UDPR_7"                             # UDPR_7                            local reg
        is_claimed = "UDPR_9"                       # UDPR_9                            local reg
        key = "UDPR_10"                             # UDPR_10                           local reg
        scratch = self.scratch                      # [UDPR_12, UDPR_13]                local reg
        lm_base_reg = self.scratch[1]               # UDPR_13                           local reg
        ev_word = self.ev_word                      # UDPR_14                           local reg


        # Get number of keys that have been materialized
        lm_base_reg = self.__get_lm_base(tran, lm_base_reg)
        tran.writeAction(f"movir {addr} {self.intermediate_cache_offset}")
        tran.writeAction(f"add {lm_base_reg} {addr} {addr}")
        tran.writeAction(f"movlr 0({addr}) {cache_count} 1 8")

        # Locate returned key in the cached array
        tran.writeAction(f"find_cached_key: movlr 0({addr}) {key} 1 8")
        tran.writeAction(f"sri {key} {key} 1")
        tran.writeAction(f"beq {key} OB_0 cache_hit")
        tran.writeAction(f"addi {addr} {addr} {WORD_SIZE * 2}")
        tran.writeAction(f"subi {cache_count} {cache_count} 1")
        tran.writeAction(f"jmp find_cached_key")

        # Found the key, update the is_claimed bit
        tran.writeAction(f"cache_hit: subi {addr} {addr} {WORD_SIZE}")
        # tran.writeAction(f"movir {is_claimed} 1")
        tran.writeAction(f"slorii {key} {key} 1 1")
        tran.writeAction(f"movrl {key} 0({addr}) 1 8")
        tran.writeAction(f"movrl OB_1 0({addr}) 1 8")

        # Send to dest which claimed the key
        # Annoucing the claiming is asserted
        tran.writeAction(f"sendr_reply {key} {key} {scratch[0]}")
        tran.writeAction(f"yieldt")

        return

    def __gen_worker_assert_claimed_key_thread(self):
        '''
        Event:  returned from worker_update_claimed_key from static hashed lane
                to update the assert_claimed_key bit to 1
        '''
        ln_worker_assert_claimed_key_ev_label = self.get_event_mapping("worker_assert_claimed_key")
        tran = self.state.writeTransition("eventCarry", self.state, self.state, ln_worker_assert_claimed_key_ev_label)

        scratch = self.scratch

        lm_reg = self.__get_lm_base(tran, scratch[1])
        tran.writeAction(f"movir {scratch[0]} 1")
        tran.writeAction(f"movrl {scratch[0]} {self.assert_claimed_key_offset}({lm_reg}) 0 {WORD_SIZE}")
        tran.writeAction(f"yieldt")

        return


    ##############################################################################

    def __gen_global_sync(self):

        self.glb_sync_init_ev_label = self.get_event_mapping(f"init_global_snyc")
        self.node_init_ev_label     = self.get_event_mapping("init_node_sync")
        self.ud_accum_ev_label      = self.get_event_mapping("ud_accumulate")
        self.global_sync_ev_label   = self.get_event_mapping("global_sync")
        self.node_sync_ev_label     = self.get_event_mapping("node_sync")

        global_init_tran    = self.state.writeTransition("eventCarry", self.state, self.state, self.glb_sync_init_ev_label)

        node_init_tran      = self.state.writeTransition("eventCarry", self.state, self.state, self.node_init_ev_label)

        ud_accum_tran       = self.state.writeTransition("eventCarry", self.state, self.state, self.ud_accum_ev_label)

        global_sync_tran    = self.state.writeTransition("eventCarry", self.state, self.state, self.global_sync_ev_label)

        node_sync_tran      = self.state.writeTransition("eventCarry", self.state, self.state, self.node_sync_ev_label)

        self.ev_word        = "UDPR_14"
        global_sync_offsets = [self.reduce_ctr_offset]
        transitions = [global_init_tran, global_sync_tran, node_init_tran, node_sync_tran, ud_accum_tran]
        
        global_sync = GlobalSync(self.task, self.ev_word, global_sync_offsets, self.scratch, self.debug_flag, self.print_level, self.send_temp_reg_flag)
        global_sync.set_labels(self.global_sync_ev_label, self.node_init_ev_label,
                               self.node_sync_ev_label, self.ud_accum_ev_label)

        '''
        Event:      Initialize global synchronization
        Operands:   X8:   Saved continuation
                    X9:   Number of map tasks generated
        '''
        global_sync.global_sync(continuation='X1', sync_value='X9', num_lanes='X8', transitions=transitions)

        return

    # def __gen_global_sync(self):

    #     self.glb_sync_init_ev_label = self.get_event_mapping(f"init_global_snyc")
    #     self.node_init_ev_label     = self.get_event_mapping("init_node_sync")
    #     self.ud_accum_ev_label      = self.get_event_mapping("ud_accumulate")
    #     self.global_sync_ev_label   = self.get_event_mapping("global_sync")
    #     self.node_sync_ev_label     = self.get_event_mapping("node_sync")

    #     global_init_tran    = self.state.writeTransition("eventCarry", self.state, self.state, self.glb_sync_init_ev_label)

    #     node_init_tran      = self.state.writeTransition("eventCarry", self.state, self.state, self.node_init_ev_label)

    #     ud_accum_tran       = self.state.writeTransition("eventCarry", self.state, self.state, self.ud_accum_ev_label)

    #     global_sync_tran    = self.state.writeTransition("eventCarry", self.state, self.state, self.global_sync_ev_label)

    #     node_sync_tran      = self.state.writeTransition("eventCarry", self.state, self.state, self.node_sync_ev_label)

    #     self.ev_word        = "UDPR_11"

    #     global_sync_offsets = [self.reduce_ctr_offset]
    #     global_sync = GlobalSync(self.task, self.ev_word, global_sync_offsets, self.scratch, self.debug_flag, self.print_level, self.send_temp_reg_flag)

    #     global_sync.set_labels(self.global_sync_ev_label, self.node_init_ev_label,
    #                            self.node_sync_ev_label, self.ud_accum_ev_label)

    #     '''
    #     Event:      Initialize global synchronization
    #     Operands:   OB_0:   Saved continuation
    #                 OB_1:   Number of map tasks generated
    #     '''
    #     global_sync.global_sync(global_init_tran, global_sync_tran, continuation='OB_0', \
    #         sync_value='OB_1', num_nodes=self.num_nodes, num_ud_per_nd=self.num_lane_per_ud)

    #     global_sync.node_sync(node_init_tran, node_sync_tran, self.num_ud_per_node, self.num_lane_per_ud)

    #     global_sync.updown_accumulate(ud_accum_tran, self.num_lane_per_ud)

    #     return

    @abstractmethod
    def kv_map(self, tran: Transition, key: str, values: list, map_ret_ev_label: str) -> int:
        '''
        User defined map function. It takes an key-value pair and produce one (or more) key-value pair(s).
        Parameters
            tran:       transition triggered by the map event
            key:        the name of the register/operand buffer entry which contains the input key
            value:      the name of the register/operand buffer entry which contains the input value
        Output
            tran(transition):
                        the last transtion in which the map thread termiantes
            size(int):       the size of the intermediate key-value pair (in words) generated by the mapper
        '''

        pass

    @abstractmethod
    def kv_reduce(self, tran: Transition, key: str, values: list, reduce_ret_ev_label: str, regs = [f"X{i}" for i in range(16, 32)]) -> Transition:
        '''
        User defined reduce function. It takes an key-value pair generated by the mapper and updates the output value mapped to the given key accordingly.
        Parameters
            tran:       transition triggered by the reduce event
            key:        the name of the register/operand buffer entry which contains the intermediate key generated by the mapper
            value:      the name of the register/operand buffer entry which contains the intermediate value generated by the mapper (i.e. the incoming value)
            regs:       the name of registers free to use
        Output
            result_reg: the name of the register containing the reduced value to be stored back
        '''

        pass

    @abstractmethod
    def kv_merge_op(self, tran: Transition, in_key: str, in_values: list, old_values: list, regs: list) -> Transition:
        '''
        User defined merge operation used by the kv_merge() helper function.
        It takes an key-value pair generated by the mapper and updates the output value mapped to the given key accordingly.
        Parameters
            tran:       transition (codelet) triggered by the reduce event
            in_key:     the name of the register/operand buffer entry which contains the intermediate key generated by the mapper
            in_values:  the name of the register/operand buffer entry which contains the intermediate value generated by the mapper (i.e. the incoming value)
            old_values: the name of the register storing the current output kvpair's value corresponding with the incoming intermediate key
        Output
            result_reg: a list of register names containing the merged values to be stored back
        '''

        # user defined merge
        return tran

    def kv_reduce_loc(self, tran: Transition, key: str, dest_id: str):
        '''
        User-defined mapping from a key to a reducer lane (id). Default implementation is a hash.
        Can be overwritten by the user and changed to customized mapping.
        Parameter
            tran:       transition (codelet) triggered by the map event
            key:        name of the register/operand buffer entry containing the key
            result:     name of the register reserved for storing the destination lane id
        '''

        tran.writeAction(f"andi {key} {dest_id} {self.num_workers-1}")


    def kv_emit(self, tran: Transition, key: str, values: list, dest: str, reg1: str, reg2: str):
        '''
        Helper function which sends the intermediate key-value pair generated by the mapper to a reducer lane
        based on the key-lane mapping defined in self.kv_reduce_loc().
        Parameters:
            tran:       transition (codelet) triggered by the map event
            key:        name of the register/operand buffer entry containing the intermediate key to be sent to the reducer
            values:     name of the registers/operand buffer entry containing the intermediate value to be sent to the reducer
            dest:       name of the register reserved for the destination reducer id
            reg1&reg2:  name of scratch registers
        '''

        if self.extension == self.AvailableExtensions.lb_test:
            ln_worker_receive_kv_ev_label = self.get_event_mapping("worker_receive_intermediate_kv_pair")

            self.kv_reduce_loc(tran, key, dest)
            tran.writeAction(f"addi X2 {reg1} 0")
            tran.writeAction(f"evii {reg1} {ln_worker_receive_kv_ev_label} 255 5")
            tran.writeAction(f"ev {reg1}  {reg1}  {dest} {dest} 8")
            tran.writeAction(f"print 'sending key %u value %llu to dest %u' {key} {values[0]} {dest}")
            tran.writeAction(f"sendr_wcont {reg1} EQT {key} {' '.join(values)}")
            lm_base_reg = self.__get_lm_base(tran, reg2)
            tran.writeAction(f"addi {lm_base_reg} {reg2} 0")
            tran.writeAction(f"move {self.map_ctr_offset}({reg2}) {reg1}  0 8")
            tran.writeAction(f"addi {reg1} {reg1} 1")
            tran.writeAction(f"move {reg1} {self.map_ctr_offset}({reg2}) 0 8")
        else:
            ln_reduce_th_ev_label = self.get_event_mapping("init_lane_reduce_thread")

            self.kv_reduce_loc(tran, key, dest)
            tran.writeAction(f"ev_update_2 {reg1} {ln_reduce_th_ev_label} 255 5")
            tran.writeAction(f"ev_update_reg_2 {reg1}  {reg1}  {dest} {dest} 8")
            tran.writeAction(f"sendr_wcont {reg1} EQT {key} {' '.join(values)}")
            lm_base_reg = self.__get_lm_base(tran, reg2)
            tran.writeAction(f"addi {lm_base_reg} {reg2} 0")
            tran.writeAction(f"move {self.map_ctr_offset}({reg2}) {reg1}  0 8")
            tran.writeAction(f"addi {reg1} {reg1} 1")
            tran.writeAction(f"move {reg1} {self.map_ctr_offset}({reg2}) 0 8")
    
    def msr_return(self, tran: Transition, ret_label: str, operands: str = 'EQT EQT', cont_label: str = '', branch_label = '') -> Transition:
        '''
        Helper function for returning to the UDKVMSR library from the user defined map/reduce function.
        Parameter:
            tran:       current transition
            ret_label:  return event label
            operands:   operands to be sent back to the UDKVMSR library (optional)
            cont_label: continuation event label for UDKVMSR (optional)
        '''
        
        tran = set_ev_label(tran, self.ev_word, ret_label, src_ev='X2', label=branch_label)
        if cont_label:
            tran.writeAction(f"sendr_wret {self.ev_word} {cont_label} {operands}")
        else:
            tran.writeAction(f"sendr_wcont {self.ev_word} {'X2'} {operands}")
        return tran
    
    def msr_return_temp(self, tran: Transition, ret_label: str, temp_reg:str, operands: str = 'EQT EQT', cont_label: str = '', branch_label = '') -> Transition:
        '''
        Helper function for returning to the UDKVMSR library from the user defined map/reduce function.
        Parameter:
            tran:       current transition
            ret_label:  return event label
            operands:   operands to be sent back to the UDKVMSR library (optional)
            cont_label: continuation event label for UDKVMSR (optional)
        '''
        
        tran = set_ev_label(tran, self.ev_word, ret_label, src_ev='X2', label=branch_label)
        if cont_label:
            if len(operands) == 2:
                tran.writeAction(format_pseudo(f"sendr_wret {self.ev_word} {cont_label} {operands}", temp_reg, self.send_temp_reg_flag))
            else:
                tran.writeAction(format_pseudo(f"sendr3_wret {self.ev_word} {cont_label} {operands}", temp_reg, self.send_temp_reg_flag))
        else:
            tran.writeAction(f"sendr_wcont {self.ev_word} {'X2'} {operands}")
        return tran

    def kv_merge(self, tran: Transition, key: str, values: list, reduce_ret_ev_label: str, regs: list = [f'UDPR_{i}' for i in range(16)]):
        '''
        Helper function for atomic operation using scratchpad. First check if the newest value is cached or is being read (not coming back yet).
        If either, the update will be merged locally based on the user-defined merge function. When the data is ready, it will apply the accumulated 
        update(s), stores the data back to DRAM, and frees the hash table entry. If there's a hash conflict, the update will be postponed
        (i.e. append to the end of the event queue) until the event is popped up and the entry is freed.
        Parameter:
            key:        name of the operand buffer entries/registers containing the key to the cache entry
            values:     name of the operand buffer entries/registers containing the value to be merged
            reduce_ret_ev_label:    return event label to the udkvmsr library
            regs:       scratch registers, by default is all the 16 general purposed registers
        '''

        if self.extension == self.AvailableExtensions.lb_test:

            merge_ev_label = self.get_event_mapping("merge")
            ev_word = regs[0]
            cont_word = regs[1]
            ob_addr = regs[2]
            tmp = regs[3]

            tran.writeAction(f"evii {ev_word} {merge_ev_label} 255 5")
            tran.writeAction(f"addi X2 {cont_word} 0")
            tran.writeAction(f"evlb {cont_word} {reduce_ret_ev_label}")
            ob_addr = self.__get_lm_base(tran, ob_addr)
            tran.writeAction(f"movir {tmp} {self.ob_cache_offset}")
            tran.writeAction(f"add {tmp} {ob_addr} {ob_addr}")
            tran.writeAction(f"send_any_wcont {ev_word} {cont_word} {ob_addr} {tmp} \
                                        {key} " + " ".join(values))
            tran.writeAction(f"yield")

            merge_tran = self.state.writeTransition("eventCarry", self.state, self.state, merge_ev_label)
            regs = [f'UDPR_{i}' for i in range(16)]

        else:
            merge_tran = tran



        self.ld_merge_ev_label  = self.get_event_mapping("load_merge")
        self.store_ack_ev_label = self.get_event_mapping("store_ack")
        self.store_ack_more_ev_label = self.get_event_mapping("store_ack_more")

        lm_base_reg = regs[0]
        key_lm_offset   = regs[1]
        cached_key  = regs[2]
        pair_addr   = regs[3]
        temp_val    = regs[4]
        masked_key  = regs[5]
        cached_values   = [regs[6+i] for i in range(self.cache_entry_size - 1)]
        result_regs     = [regs[6+i+self.cache_entry_size] for i in range(self.cache_entry_size - 1)]

        tlb_active_hit_label = "tlb_active_hit"
        tlb_hit_label = "tlb_hit"
        tlb_evict_label = "tlb_evict"
        error_label = "error"

        

        '''
        check if the local scratchpad stores a pending update to the same key or a copy of the newest output kvpair with that key.
        '''
        if self.debug_flag and self.print_level > 2:
            merge_tran.writeAction(f"print '[DEBUG][NWID %d] Merge incoming key = %d values = %d' {'X0'} {key} {values[0]}")
        lm_base_reg = self.__get_lm_base(merge_tran, lm_base_reg)
        merge_tran.writeAction(f"lshift_and_imm {key} {key_lm_offset} {int(log2(self.cache_entry_bsize))} \
            {(self.cache_size << int(log2(self.cache_entry_bsize)))-1}")
        print(f"lshift_and_imm {key} {key_lm_offset} {int(log2(self.cache_entry_bsize))} \
            {(self.cache_size << int(log2(self.cache_entry_bsize)))-1}")
        merge_tran.writeAction(f"add {lm_base_reg} {key_lm_offset} {key_lm_offset}")
        merge_tran.writeAction(f"movir {temp_val} {self.cache_offset}")             # New line added by: Jerry
        merge_tran.writeAction(f"add {temp_val} {key_lm_offset} {key_lm_offset}")   # New line added by: Jerry
        merge_tran.writeAction(f"move 0({key_lm_offset}) {cached_key} 0 8")
        if self.debug_flag and self.print_level > 2:
            merge_tran.writeAction(f"print '[DEBUG][NWID %d] Cached key = %d at offset %d' {'X0'} {cached_key} {key_lm_offset}")
        merge_tran.writeAction(f"beq {cached_key} {key} {tlb_active_hit_label}")
        merge_tran.writeAction(f"mov_imm2reg {masked_key} {1}")
        merge_tran.writeAction(f"sli {masked_key} {masked_key} {self.INACTIVE_MASK_SHIFT}")
        merge_tran.writeAction(f"add {masked_key} {key} {masked_key}")
        if self.debug_flag and self.print_level > 2:
            merge_tran.writeAction(f"print '[DEBUG][NWID %d] Masked key = %d' {'X0'} {masked_key}")
        merge_tran.writeAction(f"beq {masked_key} {cached_key} {tlb_hit_label}")
        '''
        If not, check if the data cached has been written back to DRAM.
        If so, evict the current entry.
        '''
        merge_tran.writeAction(f"rshift {cached_key} {temp_val} {self.INACTIVE_MASK_SHIFT}")
        merge_tran.writeAction(f"beqi {temp_val} 1 {tlb_evict_label}")

        '''
        If all conditions failed, the entry is occupied and cannot be evicted for now, push the event back to the queue.
        '''
        if self.debug_flag and self.print_level > 2:
            merge_tran.writeAction(f"print '[DEBUG][NWID %d] Cache entry occupied, push back to queue key = %d values = {' '.join(['%d' for _ in range(self.inter_kvpair_size - 1)])}' \
                {'X0'} {key} {' '.join(values)}")

        # merge_tran.writeAction(f"ev_update_2 {self.ev_word} {self.ln_reduce_th_ev_label} 255 5")
        merge_tran.writeAction(f"evi X2 {self.ev_word} 255 4")              # Lane modified by: Jerry
        merge_tran.writeAction(f"sendops_wcont {self.ev_word} X1 {key} {self.inter_kvpair_size}")
        merge_tran.writeAction(f"move {self.num_reduce_th_offset}({lm_base_reg}) {temp_val} 0 8")
        merge_tran.writeAction(f"subi {temp_val} {temp_val} 1")
        merge_tran.writeAction(f"move {temp_val}  {self.num_reduce_th_offset}({lm_base_reg}) 0 8")
        merge_tran.writeAction("yieldt")

        # Still waiting for the read to the output kv pair on DRAM coming back, merge locally
        merge_tran.writeAction(f"{tlb_active_hit_label}: move {WORD_SIZE}({key_lm_offset}) {cached_values[0]} 1 8") # Line modified by: Jerry
        if self.debug_flag and self.print_level > 2:
            merge_tran.writeAction(f"print '[DEBUG][NWID %d] Cache active hit, cached value[0] = %d' {'X0'} {cached_values[0]}")
        for i in range(len(cached_values) - 1):
            merge_tran.writeAction(f"move {WORD_SIZE * (i+1)}({key_lm_offset}) {cached_values[i+1]} 0 8")   # Line modified by: Jerry
            if self.debug_flag and self.print_level > 2:
                merge_tran.writeAction(f"print '[DEBUG][NWID %d] Cached value[{i+1}] = %d' {'X0'} {cached_values[i+1]}")
        self.kv_merge_op(merge_tran, key, values, cached_values, result_regs)
        for i in range(self.cache_entry_size - 1):
            merge_tran.writeAction(f"move {result_regs[i]} {WORD_SIZE * i}({key_lm_offset}) 0 8")   # Line modified by: Jerry
            if self.debug_flag and self.print_level > 2:
                merge_tran.writeAction(f"print '[DEBUG][NWID %d] Store result value[{i}] = %d' {'X0'} {result_regs[i]}")

        if self.extension == self.AvailableExtensions.lb_test:
            merge_tran.writeAction(f"movir {lm_base_reg} {654321}")
            merge_tran.writeAction(f"sendr_reply {lm_base_reg} {lm_base_reg} {temp_val}")
            merge_tran.writeAction(f"yieldt")
        else:
            if self.send_temp_reg_flag:
                merge_tran = self.msr_return_temp(merge_tran, reduce_ret_ev_label, temp_val, operands=f"EQT {cached_key}")
            else:
                merge_tran = self.msr_return(merge_tran, reduce_ret_ev_label)
            merge_tran.writeAction(f"yield")

        # The output kv pair is cached in the scratchpad, merge and immediate write back the newest value (write through policy)
        merge_tran.writeAction(f"{tlb_hit_label}: move {WORD_SIZE}({key_lm_offset}) {cached_values[0]} 1 8")    # Line modified by: Jerry
        if self.debug_flag and self.print_level > 2:
            merge_tran.writeAction(f"print '[DEBUG][NWID %d] Cache hit, cached value[0] = %d' {'X0'} {cached_values[0]}")
        for i in range(len(cached_values) - 1):
            merge_tran.writeAction(f"move {WORD_SIZE * (i+1)}({key_lm_offset}) {cached_values[i+1]} 0 8")   # Line modified by: Jerry
            if self.debug_flag and self.print_level > 2:
                merge_tran.writeAction(f"print '[DEBUG][NWID %d] Cached value[{i+1}] = %d' {'X0'} {cached_values[i+1]}")
        result_regs = self.kv_merge_op(merge_tran, key, values, cached_values, result_regs)
        # Store back the updated values to DRAM
        merge_tran = self.out_kvset.get_pair(merge_tran, key, pair_addr, cached_values)

        if self.extension == self.AvailableExtensions.lb_test:
            merge_tran.writeAction(f"evii {self.ev_word} {self.store_ack_ev_label} 255 5")
        else:
            merge_tran = set_ev_label(merge_tran, self.ev_word, self.store_ack_ev_label)
        merge_tran.writeAction(f"sendr2_dmlm {pair_addr} {self.ev_word} {key} {result_regs[0]}")

        merge_tran.writeAction(f"print '   MERGE: lane %u writing key %u value %u to addr %lu' X0 {key} {result_regs[0]} {pair_addr}")

        if self.cache_entry_size > 2:
            merge_tran = set_ev_label(merge_tran, self.ev_word, self.store_ack_more_ev_label, src_ev=self.ev_word)
            for i in range(1, len(result_regs), 2):
                merge_tran.writeAction(f"addi {pair_addr} {pair_addr} {WORD_SIZE * 2}")
                merge_tran.writeAction(f"sendr2_dmlm {pair_addr} {self.ev_word} {result_regs[i]} {result_regs[i+1]}")
        for i in range(self.cache_entry_size - 1):
            merge_tran.writeAction(f"move {result_regs[i]} {WORD_SIZE * i}({key_lm_offset}) 0 8")       # Line modified by: Jerry
            if self.debug_flag and self.print_level > 2:
                merge_tran.writeAction(f"print '[DEBUG][NWID %d] Store result value[{i}] = %d' {'X0'} {result_regs[i]}")
        if self.extension == self.AvailableExtensions.lb_test:
            merge_tran.writeAction(f"movir {lm_base_reg} {654321}")
            merge_tran.writeAction(f"sendr_reply {lm_base_reg} {lm_base_reg} {temp_val}")
            merge_tran.writeAction("yieldt")
        else:
            merge_tran.writeAction("yield")

        # Current entry has been written back to DRAM, (i.e., can be evicted). Insert the new entry.
        merge_tran.writeAction(f"{tlb_evict_label}: move {key} {0}({key_lm_offset}) 1 8")               # Line modified by: Jerry
        if self.debug_flag and self.print_level > 2:
            merge_tran.writeAction(f"print '[DEBUG][NWID %d] Cache miss evict old entry %d' {'X0'} {cached_key}")
        # Retrieve the DRAM address of the output kvpair corresponding to {key} based on the user-defined access function
        merge_tran = self.out_kvset.get_pair(merge_tran, key, pair_addr, result_regs)
        merge_tran = set_ev_label(merge_tran, self.ev_word, self.ld_merge_ev_label)
        merge_tran.writeAction(f"send_dmlm_ld {pair_addr} {self.ev_word} {self.out_kvpair_size}")
        if self.debug_flag and self.print_level > 2:
            merge_tran.writeAction(f"print '[DEBUG][NWID %d] Load pair key = %d from DRAM' {'X0'} {key}")
        # Store the new entry to the cache
        for i in range(self.cache_entry_size - 1):
            merge_tran.writeAction(f"move {values[i]} {WORD_SIZE * i}({key_lm_offset}) 0 8")            # Line modified by: Jerry
        merge_tran.writeAction(f"addi {key} {cached_key} 0")
        merge_tran.writeAction(f"yield")






        # Triggered when the old output kvpair is read from DRAM ready for merging with the (accumulated) updates
        load_tran = self.state.writeTransition("eventCarry", self.state, self.state, self.ld_merge_ev_label)
        if self.debug_flag and self.print_level > 2:
            load_tran.writeAction(f"print ' '")
            load_tran.writeAction(f"print '[DEBUG][NWID %d] Event <kvmsr_load_merge> ev_word = %d:' {'X0'} {'EQT'}")
        ld_key = "OB_0"
        ld_values = [f"OB_{1+i}" for i in range(self.cache_entry_size - 1)]

        # counter = lm_base_reg

        # load_tran.writeAction(f"movir {counter} {0}")   # Added by: Jerry

        for i in range(len(cached_values)):
            load_tran.writeAction(f"move {WORD_SIZE * i}({key_lm_offset}) {cached_values[i]} 0 8")      # Line modified by: Jerry
            if self.debug_flag and self.print_level > 2:
                load_tran.writeAction(f"print '[DEBUG][NWID %d] Cached value[{i}] = %d' {'X0'} {cached_values[i]}")

        # Apply the accumulated updates based on user-defined reduce funtion
        result_regs = self.kv_merge_op(load_tran, cached_key, cached_values, ld_values, result_regs)
        # Store back the updated values to DRAM
        load_tran = self.out_kvset.get_pair(load_tran, cached_key, pair_addr, cached_values)

        if self.extension == self.AvailableExtensions.lb_test:
            load_tran.writeAction(f"evii {self.ev_word} {self.store_ack_ev_label} 255 5")
        else:
            load_tran = set_ev_label(load_tran, self.ev_word, self.store_ack_ev_label)
        load_tran.writeAction(f"sendr2_dmlm {pair_addr} {self.ev_word} {cached_key} {result_regs[0]}")      # Modified by: Jerry

        load_tran.writeAction(f"print '   LOAD: lane %u writing key %u value %u to addr %lu' X0 {key} {result_regs[0]} {pair_addr}")

        # load_tran.writeAction(f"addi {counter} {counter} 1")
        if self.debug_flag and self.print_level > 2:
            load_tran.writeAction(f"print '[DEBUG][NWID %d] Store result value[0] = %d to addr = 0x%x' {'X0'} {result_regs[0]} {pair_addr}")
        if self.cache_entry_size > 2:
            if self.extension == self.AvailableExtensions.lb_test:
                load_tran.writeAction(f"evii {self.ev_word} {self.store_ack_more_ev_label} 255 5")
            else:
                load_tran = set_ev_label(load_tran, self.ev_word, self.store_ack_more_ev_label, src_ev=self.ev_word)

            for i in range(1, len(result_regs), 2):
                load_tran.writeAction(f"addi {pair_addr} {pair_addr} {WORD_SIZE * 2}")
                load_tran.writeAction(f"sendr2_dmlm {pair_addr} {self.ev_word} {result_regs[i]} {result_regs[i+1]}")    # Modified by: Jerry
                # load_tran.writeAction(f"addi {counter} {counter} 1")
                if self.debug_flag and self.print_level > 2:
                    load_tran.writeAction(f"print '[DEBUG][NWID %d] Store result value[{i}] = %d result value[{i+1}] = %d to addr = 0x%x' \
                        {'X0'} {result_regs[i]} {result_regs[i+1]} {pair_addr}")
        # Store the updated value back to the cache
        for i in range(self.cache_entry_size - 1):
            load_tran.writeAction(f"move {result_regs[i]} {WORD_SIZE * i}({key_lm_offset}) 0 8")    # Line modified by: Jerry
        # load_tran.writeAction(f"or {cached_key} {cache_key_mask} {cached_key}")
        if self.debug_flag and self.print_level > 2:
            load_tran.writeAction(f"print '[DEBUG][NWID %d] Store masked key = %d to addr = 0x%x' {'X0'} {masked_key} {key_lm_offset}")
        load_tran.writeAction(f"move {masked_key} {- WORD_SIZE}({key_lm_offset}) 0 8")    # flip the highest bit indicating the value is written back   # Line modified by: Jerry
        
        if self.extension == self.AvailableExtensions.lb_test:
            load_tran.writeAction(f"movir {lm_base_reg} {654321}")
            load_tran.writeAction(f"sendr_reply {lm_base_reg} {lm_base_reg} {temp_val}")
            load_tran.writeAction(f"yieldt")
        else:
            load_tran.writeAction(f"yield")

        # load_tran.writeAction(f"{error_label}: print '[DEBUG][NWID %d] ERROR! loaded key=%d is not equal to the cached key=%d' {'X0'} {ld_key} {cached_key}")
        # load_tran.writeAction(f"yield")





        if self.extension == self.AvailableExtensions.lb_test:
            # Triggered when the write comes back from DRAM, finish the merge and store back the updated value
            store_ack_tran = self.state.writeTransition("eventCarry", self.state, self.state, self.store_ack_ev_label)
            if self.debug_flag and self.print_level > 3:
                store_ack_tran.writeAction(f"print ' '")
                store_ack_tran.writeAction(f"print '[DEBUG][NWID %d] Event <store_ack> ev_word = %d addr = 0x%x' {'X0'} {'EQT'} {'OB_0'}")
            
            # store_ack_tran.writeAction(f"movir {cached_key} {654321}")
            # store_ack_tran.writeAction(f"sendr_reply {cached_key} {cached_key} {temp_val}")

            # store_ack_tran.writeAction(f"subi {counter} {counter} 1")
            # store_ack_tran.writeAction(f"beqi {counter} 0 thread_term")
            # store_ack_tran.writeAction("yield")
            # store_ack_tran.writeAction(f"thread_term: yieldt")

            store_ack_tran.writeAction(f"yieldt")

            store_ack_more_tran = self.state.writeTransition("eventCarry", self.state, self.state, self.store_ack_more_ev_label)
            if self.debug_flag and self.print_level > 3:
                store_ack_more_tran.writeAction(f"print ' '")
                store_ack_more_tran.writeAction(f"print '[DEBUG][NWID %d] Event <store_ack_more> ev_word = %d addr = 0x%x' {'X0'} {'EQT'} {'OB_0'}")
           

            # store_ack_more_tran.writeAction(f"subi {counter} {counter} 1")
            # store_ack_more_tran.writeAction(f"beqi {counter} 0 thread_term")
            # store_ack_more_tran.writeAction("yield")
            # store_ack_more_tran.writeAction(f"thread_term: yieldt")
            store_ack_more_tran.writeAction(f"yieldt")

        else:
            # Triggered when the write comes back from DRAM, finish the merge and store back the updated value
            store_ack_tran = self.state.writeTransition("eventCarry", self.state, self.state, self.store_ack_ev_label)
            if self.debug_flag and self.print_level > 3:
                store_ack_tran.writeAction(f"print ' '")
                store_ack_tran.writeAction(f"print '[DEBUG][NWID %d] Event <store_ack> ev_word = %d addr = 0x%x' {'X0'} {'EQT'} {'OB_0'}")
            

            if self.send_temp_reg_flag:
                store_ack_tran = self.msr_return_temp(store_ack_tran, reduce_ret_ev_label, temp_val, operands=f"EQT {cached_key}")
            else:
                store_ack_tran = self.msr_return(store_ack_tran, reduce_ret_ev_label)

            store_ack_tran.writeAction("yield")

            store_ack_more_tran = self.state.writeTransition("eventCarry", self.state, self.state, self.store_ack_more_ev_label)
            if self.debug_flag and self.print_level > 3:
                store_ack_more_tran.writeAction(f"print ' '")
                store_ack_more_tran.writeAction(f"print '[DEBUG][NWID %d] Event <store_ack_more> ev_word = %d addr = 0x%x' {'X0'} {'EQT'} {'OB_0'}")
           
            store_ack_more_tran.writeAction("yield")


        return



'''
Template ends here
-----------------------------------------------------------------------
'''

