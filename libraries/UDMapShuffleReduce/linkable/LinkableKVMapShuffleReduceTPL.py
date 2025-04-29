from linker.EFAProgram import EFAProgram
from math import log2, ceil
from abc import ABCMeta
from LinkableGlobalSync import GlobalSync, Broadcast
from LinkableKeyValueSetTPL import KeyValueSetInterface
from KVMSRMachineConfig import *
from Macro import *
import sys

class UDKeyValueMapShuffleReduceTemplate(metaclass=ABCMeta):
    """
    UpDown KeyValue MapShuffleReduce Library

    Usage:
    1. Import the module into UpDown source code file.
        from LinkableKVMapShuffleReduceTPL import UDKeyValueMapShuffleReduceTemplate
    2. Extend the UDKeyValueMapShuffleReduceTemplate class.
       (Optionally, overwrite key binding functions for e.g. customized work distribution.)
    3. Implement map and reduce code, using the following event labels as the entry point:
        <task_name>::kv_map:     Event label for map function
        <task_name>::kv_reduce:  Event label for reduce function
    4. Use the following events to emit intermediate key-value pairs to reduce and output key-value pairs to output kvset:
        <task_name>::kv_map_emit:       Event label for emitting intermediate key-value pairs
        <task_name>::kv_reduce_emit:    Event label for emitting output key-value pairs
    5. At the end of map and reduce, use the fllowing events to return to the UDKVMSR library:
        <task_name>::kv_map_return:     Event label for returning from map function
        <task_name>::kv_reduce_return:  Event label for returning from reduce function
    If Load Balancer is enabled, 
        At the end of reduce
        Keep the continuation word as the same as at the start of reduce!

    6. Instantiate the UDMapShuffleReduce class and wrap in customized GenerateEFA() function to generate UpDown assembly code.

    Example linkable UDKVMSR programs can be find in updown/apps/msr_examples/.
    """
    FLAG    = 1
    extensions = {'original', 'load_balancer'}

    def __init__(self, efa: EFAProgram, task_name: str, meta_data_offset:int, debug_flag: bool = False, 
                    # Added by: Jerry Ding
                    extension: str = 'original', lb_meta_data_offset: int = -1):
        '''
        Parameters
            efa:                Instance of EFAProgram.
            task_name:          unique identifier for each UDKVMSR program.
            meta_data_offset:   offset of the metadata in bytes. Reserve 32 words on each lane, starting from the offset.
            debug_flag:         enable debug print (optional), default is False
        '''

        self.task = task_name
        self.efa = efa
        self.efa.code_level = 'machine'

        self.state = efa.State()
        self.efa.add_initId(self.state.state_id)

        # Added by: Jerry Ding
        self.extension = extension
        if self.extension not in UDKeyValueMapShuffleReduceTemplate.extensions:
            sys.exit()
        ######################
        
        self.enable_intermediate = False
        self.enable_output = False
        self.num_init_ops = 2
        self.num_init_events = 3
        
        self.metadata_offset        = meta_data_offset
        self.map_ctr_offset         = self.metadata_offset
        self.reduce_ctr_offset      = self.map_ctr_offset + WORD_SIZE
        self.ln_mstr_evw_offset     = self.reduce_ctr_offset + WORD_SIZE
        self.num_reduce_th_offset   = self.ln_mstr_evw_offset + WORD_SIZE
        self.max_red_th_offset      = self.num_reduce_th_offset + WORD_SIZE
        self.nwid_mask_offset       = self.max_red_th_offset + WORD_SIZE
        self.user_cont_offset       = self.nwid_mask_offset + WORD_SIZE
        self.base_nwid_offset       = self.user_cont_offset + WORD_SIZE

        self.send_buffer_offset     = self.base_nwid_offset + WORD_SIZE
        self.SEND_BUFFER_SIZE       = 8
        
        self.enable_cache   = False
        self.debug_flag     = debug_flag
        self.print_level    = 3 if self.debug_flag else 0
        self.send_temp_reg_flag     = True
        
        self.max_map_th_per_lane    = 10
        self.max_reduce_th_per_lane = 10
        
        self.event_map = []
        print(f"Initialize MapShuffleReduce task {self.task} - bookkeeping_data_offset: {meta_data_offset}, send_buffer_offset: {self.send_buffer_offset}, debug_flag: {debug_flag}")

        
        # Added by: Jerry Ding
        self.metadata_end_offset    = self.send_buffer_offset + self.SEND_BUFFER_SIZE * WORD_SIZE
        self.heap_offset            = self.metadata_end_offset
        if self.extension == 'load_balancer':
            self.num_init_events += 1
            self._finish_flag                       = -1
            self._map_finish_flag                   = -2
            self._map_flag                          = -3
            self._reduce_flag                       = -4
            self._worker_start_flag                 = -5 #123456
            self._worker_claim_key_flag             = -6 #654321
            self._worker_spin_lock_flag             = -7
            self.intermediate_cache_entry_size      = 4
            self.materialize_kv_cache_entry_size    = 2
            self.materializing_metadata_size        = 3
            self.inter_queue_metadata_size          = 2
            self.inter_dict_metadata_size           = 2
            self.inter_dict_entry_size              = 2

            self.intermediate_cache_size            = 256 * self.intermediate_cache_entry_size * WORD_SIZE + WORD_SIZE
            self.materialize_kv_cache_size          = 512 * self.materialize_kv_cache_entry_size * WORD_SIZE

            # New added fixed scratchpad offset
            self.lb_meta_data_offset                = lb_meta_data_offset if lb_meta_data_offset >= 0 \
                                                        else self.send_buffer_offset + self.SEND_BUFFER_SIZE * WORD_SIZE

            self.unresolved_kv_count_offset         = self.lb_meta_data_offset
            self.push_key_cont_offset               = self.unresolved_kv_count_offset + WORD_SIZE
            self.claim_work_cont_offset             = self.push_key_cont_offset + WORD_SIZE
            self.assert_claimed_key_offset          = self.claim_work_cont_offset + WORD_SIZE
            self.claimed_key_ptr_offset             = self.assert_claimed_key_offset + WORD_SIZE
            self.materializing_metadata_offset      = self.claimed_key_ptr_offset + WORD_SIZE
            self.inter_queue_metadata_offset        = self.materializing_metadata_offset + self.materializing_metadata_size * WORD_SIZE
            self.inter_dict_metadata_offset           = self.inter_queue_metadata_offset + self.inter_queue_metadata_size * WORD_SIZE
            self.metadata_end_offset                = self.inter_dict_metadata_offset + self.inter_dict_metadata_size * WORD_SIZE

            self.intermediate_cache_offset          = self.metadata_end_offset
            self.materialize_kv_cache_offset        = self.intermediate_cache_offset + self.intermediate_cache_size
            self.heap_offset                        = self.materialize_kv_cache_offset + self.materialize_kv_cache_size
                        

    def set_max_thread_per_lane(self, max_map_th_per_lane: int, max_reduce_th_per_lane: int = 0, max_worker_th_per_lane: int = 1):
        self.max_map_th_per_lane    = max_map_th_per_lane
        self.max_reduce_th_per_lane = max_reduce_th_per_lane
        # Added by: Jerry Ding
        if self.extension == 'load_balancer':
            self.max_worker_th_per_lane = max_worker_th_per_lane

    def set_input_kvset(self, kvset: KeyValueSetInterface):
        '''
        Set up the input key-value set's metadata, the kvset is stored in DRAM.
        Parameters
            kvset:  Instance of key-value set. Input to UDKVMSR.
        '''

        self.in_kvset = kvset
        self.in_kvset_offset = self.metadata_end_offset     # self.metadata_offset + 16 * WORD_SIZE   Modified by: Jerry Ding
        self.in_kvpair_size = kvset.pair_size
        self.in_kvset_iter_size = kvset.iter_size
        self.log2_in_kvset_iter_size = int(log2(self.in_kvset_iter_size))
        self.in_kvset.setup_kvset(self.state, self.in_kvset_offset, self.send_buffer_offset, self.debug_flag if self.print_level > 3 else False)
        # Added by: Jerry Ding
        self.metadata_end_offset = self.in_kvset_offset + 8 * WORD_SIZE
        if self.extension == 'load_balancer':
            self.intermediate_cache_offset          = self.metadata_end_offset
            self.materialize_kv_cache_offset        = self.intermediate_cache_offset + self.intermediate_cache_size

    def set_intermediate_kvset(self, kvset: KeyValueSetInterface):
        '''
        Set up the intermediate key-value set's metadata.
        Parameters
            kvset:  Instance of key-value set. Intermediate output of UDKVMSR kv_map.
        '''

        self.enable_intermediate = True
        self.inter_kvset = kvset
        self.inter_kvpair_size = kvset.pair_size
        
    def set_output_kvset(self, kvset: KeyValueSetInterface):
        '''
        Set up the output key-value set's metadata, the kvset is stored in DRAM.
        Parameters
            kvset:  Instance of key-value set. Output of UDKVMSR.
        '''

        self.enable_output = True
        self.num_init_events += 1
        self.out_kvset = kvset
        self.out_kvset_offset = self.metadata_end_offset    # self.in_kvset_offset + 8 * WORD_SIZE   Modified by: Jerry Ding
        self.out_kvpair_size = kvset.pair_size
        self.out_kvset.setup_kvset(self.state, self.out_kvset_offset, self.send_buffer_offset, self.debug_flag if self.print_level > 3 else False)
        # Added by: Jerry Ding
        self.metadata_end_offset = self.out_kvset_offset + 8 * WORD_SIZE
        if self.extension == 'load_balancer':
            self.intermediate_cache_offset          = self.metadata_end_offset
            self.materialize_kv_cache_offset        = self.intermediate_cache_offset + self.intermediate_cache_size

    def setup_cache(self, cache_offset: int, num_entries: int, entry_size: int, ival: int = -1, key_size: int = 1,
                    # Added by: Jerry Ding
                    intermediate_cache_offset: int = -1, intermediate_cache_size = 256, 
                    materialize_kv_cache_offset: int = -1, materialize_kv_cache_size = 512):
        '''
        If the reduce function involves read-modify-write to a DRAM location, initiates a per-lane-private software write through
        cache to combine updates to the same location (i.e. intermediate kvpair with the same key)
        Parameters
            cache_offset:   per lane local cache base (Bytes offset relative to the local bank, limited to the 64KB bank size)
            num_entries:    number of entries for each of lane-private cache segment
            entry_size:     the size of a cache entry in words, default equals to the output kv pair size.
            ival:           invalid value for invalid cache entry, default is 0xffffffffffffffff (-1)

            If load balancer is enabled:
            intermediate_cache_offset:      Cache base to cache intermediate keys statically hashed to itself
            intermediate_cache_size:        Number of entries in intermediate_cache
            materialize_kv_cache_offset:    Cache base to cache intermediate kv pairs sent to itself before fetching materializing pointer
            materialize_kv_cache_size:      Number of entries in materialize_kv_cache
        '''

        self.enable_cache = True
        self.cache_offset = cache_offset
        self.cache_size = num_entries
        if not entry_size: entry_size = self.out_kvpair_size
        self.cache_entry_bsize = entry_size << LOG2_WORD_SIZE
        self.cache_entry_size = entry_size
        self.INACTIVE_MASK_SHIFT = 63
        self.INACTIVE_MASK = (1 << self.INACTIVE_MASK_SHIFT)
        self.cache_ival = ival | self.INACTIVE_MASK
        self.power_of_two_cache_size = ceil(log2(self.cache_size)) == log2(self.cache_size)
        self.power_of_two_entry_size = ceil(log2(self.cache_entry_size)) == log2(self.cache_entry_size)

        # Added by: Jerry Ding
        self.heap_offset = self.cache_offset + self.cache_entry_size * self.cache_size * WORD_SIZE
        if self.extension == 'load_balancer':
            self.intermediate_cache_offset      = intermediate_cache_offset if intermediate_cache_offset > 0 \
                                                    else self.heap_offset
            self.intermediate_cache_size        = intermediate_cache_size * self.intermediate_cache_entry_size * WORD_SIZE + WORD_SIZE
            self.materialize_kv_cache_offset    = materialize_kv_cache_offset if materialize_kv_cache_offset > 0 \
                                                    else self.intermediate_cache_offset + self.intermediate_cache_size
            self.materialize_kv_cache_size      = materialize_kv_cache_size * self.materialize_kv_cache_entry_size * WORD_SIZE
            self.heap_offset                    = self.materialize_kv_cache_offset + self.materialize_kv_cache_size

        return

    def setup_lb_cache(self, intermediate_cache_offset: int = -1, intermediate_cache_size = 256, 
                        materialize_kv_cache_offset: int = -1, materialize_kv_cache_size = 512):
        if self.extension == 'load_balancer':
            self.intermediate_cache_offset      = intermediate_cache_offset if intermediate_cache_offset > 0 \
                                                    else self.heap_offset
            self.intermediate_cache_size        = intermediate_cache_size * self.intermediate_cache_entry_size * WORD_SIZE + WORD_SIZE
            self.materialize_kv_cache_offset    = materialize_kv_cache_offset if materialize_kv_cache_offset > 0 \
                                                    else self.intermediate_cache_offset + self.intermediate_cache_size
            self.materialize_kv_cache_size      = materialize_kv_cache_size * self.materialize_kv_cache_entry_size * WORD_SIZE
            self.heap_offset                    = self.materialize_kv_cache_offset + self.materialize_kv_cache_size

        return

    def get_event_mapping(self, label):
        '''
        Overwritten, linker will resolve the event label mapping.
        Parameter
            label:          string label
        Ouput
            event label with prefix of task name
        '''

        label = f"{self.task}::{label}"
        if label not in self.event_map: self.event_map.append(label)
        return label
        
    def __gen_event_labels(self):
        
        self.init_kvmsr_ev_label    = self.get_event_mapping("map_shuffle_reduce")
        self.kv_map_ev_label        = self.get_event_mapping("kv_map")
        self.kv_map_emit_ev_label   = self.get_event_mapping("kv_map_emit")
        self.kv_map_ret_ev_label    = self.get_event_mapping("kv_map_return")
        self.kv_reduce_ev_label     = self.get_event_mapping("kv_reduce")
        self.kv_reduce_emit_ev_label    = self.get_event_mapping("kv_reduce_emit")
        self.kv_reduce_ret_ev_label     = self.get_event_mapping("kv_reduce_return")
        self.kv_combine_ev_label        = self.get_event_mapping("kv_combine")
        self.glb_bcst_ev_label          = self.get_event_mapping("broadcast_global")
        
        self.combine_get_ev_label       = self.get_event_mapping("combine_get_pair")
        self.combine_put_ack_ev_label   = self.get_event_mapping("combine_put_pair_ack")
        self.cache_flush_ev_label   = self.get_event_mapping("cache_flush")
        self.flush_lane_ev_label    = self.get_event_mapping("combine_flush_lane")
        self.flush_ack_ev_label     = self.get_event_mapping("combine_flush_ack")
        self.cache_flush_ret_ev_label   = self.get_event_mapping("cache_flush_return")
        
        self.glb_mstr_init_ev_label = self.get_event_mapping("init_global_master")
        self.glb_mstr_loop_ev_label = self.get_event_mapping("global_master")

        self.nd_mstr_init_ev_label  = self.get_event_mapping("init_node_master")
        self.nd_mstr_loop_ev_label  = self.get_event_mapping("node_master")
        self.nd_mstr_term_ev_label  = self.get_event_mapping("termiante_node_master")

        self.ud_mstr_init_ev_label  = self.get_event_mapping("init_updown_master")
        self.ud_mstr_loop_ev_label  = self.get_event_mapping("updown_master")
        self.ud_mstr_term_ev_label  = self.get_event_mapping("terminate_updown_master")

        self.ln_mstr_init_ev_label  = self.get_event_mapping("lane_master_init")
        self.ln_mstr_loop_ev_label  = self.get_event_mapping("lane_master_loop")
        self.ln_mstr_term_ev_label  = self.get_event_mapping("lane_master_terminate")
        self.ln_mstr_rd_part_ev_label   = self.get_event_mapping("lane_master_read_partition")
        self.ln_mstr_get_ret_ev_label   = self.get_event_mapping("lane_master_get_next_return")
        
        self.kv_reduce_init_ev_label    = self.get_event_mapping("init_reduce_thread")

        self.glb_sync_init_ev_label     = self.get_event_mapping("init_global_snyc")
        
        self.kvmsr_init_fin_ev_label    = self.get_event_mapping("finish_init_udkvmsr")
        
        self.lane_init_inkvset_ev_label = self.get_event_mapping("init_input_kvset_on_lane")
        self.lane_init_outkvset_ev_label= self.get_event_mapping("init_output_kvset_on_lane")
        self.lane_init_sp_ev_label      = self.get_event_mapping("init_sp_lane")

        # Added by: Jerry Ding
        if self.extension == 'load_balancer':
            self.lane_init_interkvset_ev_label                      = self.get_event_mapping("init_intermediate_kvset_on_lane")

            self.glb_mstr_claim_work_ev_label                       = self.get_event_mapping(f"master_global_claim_work")
            self.glb_mstr_push_key_ev_label                         = self.get_event_mapping(f"master_global_push_key")
            self.glb_mstr_push_key_ret_ev_label                     = self.get_event_mapping(f"master_global_push_key_ret")

            self.ln_worker_work_ev_label                            = self.get_event_mapping(f"worker_work")
            self.ln_worker_fetched_key_ev_label                     = self.get_event_mapping("worker_fetched_key")
            self.ln_worker_fetched_kv_ptr_ev_label                  = self.get_event_mapping("worker_fetched_kv_ptr")
            self.ln_worker_launch_reducer_ev_label                  = self.get_event_mapping("worker_launch_reducer")
            self.ln_worker_reducer_ret_ev_label                     = self.get_event_mapping("worker_reducer_ret")

            self.ln_receiver_receive_kv_ev_label                    = self.get_event_mapping(f"receiver_receive_intermediate_kv_pair")
            self.ln_receiver_fetched_inter_dict_entry_ptr_ev_label  = self.get_event_mapping(f"receiver_fetched_inter_dict_entry_ptr")
            self.ln_receiver_fetched_kv_ptr_for_cache_ev_label      = self.get_event_mapping("receiver_fetched_kv_ptr_for_cache")
            self.ln_receiver_materialize_ret_ev_label               = self.get_event_mapping("receiver_materialize_ret")
            self.ln_receiver_update_claimed_key_ev_label            = self.get_event_mapping("receiver_update_claimed_key")
            self.ln_receiver_assert_claimed_key_ev_label            = self.get_event_mapping("receiver_assert_claimed_key")
            self.ln_receiver_update_unresolved_kv_count_ev_label    = self.get_event_mapping("receiver_update_unresolved_kv_count")

            self.ln_worker_helper_ev_label                          = self.get_event_mapping("worker_helper")

            self.ln_mapper_control_init_ev_label  = self.get_event_mapping("mapper_control_init")
            self.ln_mapper_control_loop_ev_label  = self.get_event_mapping("mapper_control_loop")
            self.ln_mapper_control_rd_part_ev_label   = self.get_event_mapping("mapper_control_read_partition")
            self.ln_mapper_control_get_ret_ev_label   = self.get_event_mapping("mapper_control_get_next_return")
            

        
        print(self.event_map)

    def generate_udkvmsr_task(self):
        '''
        Entry point to generate all the assembly code for UDKVMSR.
        '''
        self.__gen_event_labels()
        self.__gen_initialization()
        self.__gen_masters()
        self.__gen_global_sync()
        if self.enable_intermediate or self.enable_output: self.__gen_kv_emit()
        self.__gen_map_thread()
        if self.enable_intermediate: self.__gen_reduce_thread()
        if self.enable_intermediate and self.enable_cache and self.enable_output: self.__gen_kv_combine()

        # Added by: Jerry Ding
        if self.extension == 'load_balancer':
            self.__gen_worker()
            self.__gen_mapper_control()
            self.__gen_receiver()

        return

    def __gen_initialization(self):
        '''
        Generate the initialization code for UDKVMSR (partitions, scratchpad, input and output kvset)
        '''
        self.__gen_init_kvmsr()
        self.__gen_broadcast_init()
        
    def __gen_masters(self):
        '''
        Generate the master thread code for each level of hierarchy.
        '''
        self.__gen_global_master()
        self.__gen_node_master()
        self.__gen_updown_master()
        self.__gen_lane_master()

        # Added by: Jerry Ding
        if self.extension == 'load_balancer':
            self.__gen_global_master_lb_events()

    def __gen_init_kvmsr(self):
        '''
        Generate the initialization code for UDKVMSR (partitions, scratchpad, input and output kvset)
        '''
        
        self.scratch = [f"X{GP_REG_BASE+12}", f"X{GP_REG_BASE+13}"]

        self.part_array_ptr = f"X{GP_REG_BASE+0}"
        send_buffer_ptr     = f"X{GP_REG_BASE+1}"
        init_ev_word        = f"X{GP_REG_BASE+2}"
        part_parameter      = f"X{GP_REG_BASE+3}"
        temp_lm_ptr         = f"X{GP_REG_BASE+4}"
        init_ret_ev_word    = f"X{GP_REG_BASE+5}"
        self.num_child      = f"X{GP_REG_BASE+9}"
        init_counter        = f"X{GP_REG_BASE+10}"
        self.num_lane_reg   = f"X{GP_REG_BASE+11}"
        self.ev_word        = f"X{GP_REG_BASE+14}"
        self.saved_cont     = f"X{GP_REG_BASE+15}"


        
        self.mod_zero_label = "modular_eq_zero"
        
        kvmsr_init_tran   = self.state.writeTransition("eventCarry", self.state, self.state, self.init_kvmsr_ev_label)
                
        kvmsr_init_fin_tran   = self.state.writeTransition("eventCarry", self.state, self.state, self.kvmsr_init_fin_ev_label)
        
        '''
        Event:      Initialize UDKVMSR.
        Operands:   X8:   Pointer to the partition array (64-bit DRAM address)
                    X9:   Number of partitions per lane
                    X10:  Number of lanes
                    X11:  Scratchapd addr storing the input kvset metadata
                    X12:  Scratchapd addr storing the output kvset metadata (Optionally, only required when output kvset is enabled)
                    (If load balancer enabled) 
                    If output NOT enabled, X12: Scratchapd addr storing the intermediate kvset metadata
                    If output enabled, X13: Scratchapd addr storing the intermediate kvset metadata
        '''
        if self.debug_flag:
            kvmsr_init_tran.writeAction(f"print '[DEBUG][NWID %ld][{self.task}] here2 Initialize UDKVMSR' {'X0'}")

            # assert False

            kvmsr_init_tran.writeAction(f"print ' '")
            kvmsr_init_tran.writeAction(f"print '[DEBUG][NWID %ld][{self.task}] Event <{self.init_kvmsr_ev_label}> ev_word=%ld' {'X0'} {'EQT'}")
            kvmsr_init_tran.writeAction(f"print '[DEBUG][NWID %ld][{self.task}] Operands: partition_arr = %ld(0x%lx)' {'X0'} {'X8'} {'X8'}")
            kvmsr_init_tran.writeAction(f"print '[DEBUG][NWID %ld][{self.task}] Operands: part_per_lane = %ld(0x%lx)' {'X0'} {'X9'} {'X9'}")
            kvmsr_init_tran.writeAction(f"print '[DEBUG][NWID %ld][{self.task}] Operands: num_lanes    = %ld(0x%lx)' {'X0'} {'X10'} {'X10'}")
            kvmsr_init_tran.writeAction(f"print '[DEBUG][NWID %ld][{self.task}] Operands: input_kvset  = %ld(0x%lx)' {'X0'} {'X11'} {'X11'}")
            if self.enable_output: 
                kvmsr_init_tran.writeAction(f"print '[DEBUG][NWID %ld][{self.task}] Operands: out_kvset  = %ld(0x%lx)' {'X0'} {'X12'} {'X12'}")
            if self.extension == 'load_balancer':
                kvmsr_init_tran.writeAction(f"print '[DEBUG][NWID %ld][{self.task}] Operands: inter_kvset  = %ld(0x%lx)' {'X0'} {'X13' if self.enable_output else 'X12'} {'X13' if self.enable_output else 'X12'}")
        if self.user_cont_offset >> 15 > 0:
            kvmsr_init_tran.writeAction(f"movir {temp_lm_ptr} {self.user_cont_offset}")
            kvmsr_init_tran.writeAction(f"add {'X7'} {temp_lm_ptr} {temp_lm_ptr}")
        else:
            kvmsr_init_tran.writeAction(f"addi {'X7'} {temp_lm_ptr} {self.user_cont_offset}")
        # Save the continuation event word
        kvmsr_init_tran.writeAction(f"addi {'X1'} {self.saved_cont} 0")
        kvmsr_init_tran.writeAction(f"move {self.saved_cont} {0}({temp_lm_ptr}) 0 8")
        kvmsr_init_tran.writeAction(f"addi {'X8'} {self.part_array_ptr} 0")
        kvmsr_init_tran.writeAction(f"addi {'X10'} {self.num_lane_reg} 0")
        kvmsr_init_tran.writeAction(f"mul {'X9'} {self.num_lane_reg} {part_parameter}")
        # Generate the partition array
        kvmsr_init_tran.writeAction(f"addi {'X2'} {init_ret_ev_word} 0")
        kvmsr_init_tran.writeAction(f"evlb {init_ret_ev_word} {self.kvmsr_init_fin_ev_label}")
        # Copy the metadata of the input kvset to the expected offset in scratchpad
        if self.in_kvset_offset >> 15 > 0:
            kvmsr_init_tran.writeAction(f"movir {temp_lm_ptr} {self.in_kvset_offset}")
            kvmsr_init_tran.writeAction(f"add {'X7'} {temp_lm_ptr} {temp_lm_ptr}")
        else:
            kvmsr_init_tran.writeAction(f"addi {'X7'} {temp_lm_ptr} {self.in_kvset_offset}")
        kvmsr_init_tran.writeAction(f"addi {'X11'} {self.scratch[1]} 0")
        kvmsr_init_tran.writeAction(f"bcpylli {self.scratch[1]} {temp_lm_ptr} {self.in_kvset.meta_data_size << LOG2_WORD_SIZE}")
        self.in_kvset.generate_partitions(kvmsr_init_tran, init_ret_ev_word, self.part_array_ptr, part_parameter, [init_counter, self.scratch[0], self.scratch[1]])
        # Initialize the scratchpad memory
        set_ev_label(kvmsr_init_tran, self.ev_word, self.glb_bcst_ev_label, new_thread = True)
        kvmsr_init_tran.writeAction(f"movir {send_buffer_ptr} {self.send_buffer_offset}")
        kvmsr_init_tran.writeAction(f"add {'X7'} {send_buffer_ptr} {send_buffer_ptr}")
        kvmsr_init_tran.writeAction(f"movrl {self.num_lane_reg} 0({send_buffer_ptr}) 0 8")
        kvmsr_init_tran.writeAction(f"movir {init_ev_word} 0")
        kvmsr_init_tran.writeAction(f"evlb {init_ev_word} {self.lane_init_sp_ev_label}")
        kvmsr_init_tran.writeAction(f"movrl {init_ev_word} {WORD_SIZE}({send_buffer_ptr}) 0 8")
        kvmsr_init_tran.writeAction(f"movrl {self.num_lane_reg}  {WORD_SIZE * 2}({send_buffer_ptr}) 0 8")
        kvmsr_init_tran.writeAction(f"movrl {'X0'} {WORD_SIZE * 3}({send_buffer_ptr}) 0 8")
        kvmsr_init_tran.writeAction(f"send_wcont {self.ev_word} {init_ret_ev_word} {send_buffer_ptr} {self.SEND_BUFFER_SIZE}")
        if self.debug_flag:
            kvmsr_init_tran.writeAction(f"print '[DEBUG][NWID %ld][{self.task}] Scratchpad initialization broadcast operands: [%ld, %lu]' {'X0'} {self.num_lane_reg} {init_ev_word}")
        # Broadcast input kv set meta data to all the lanes
        kvmsr_init_tran.writeAction(f"addi {send_buffer_ptr} {temp_lm_ptr} {WORD_SIZE}")
        kvmsr_init_tran.writeAction(f"movir {init_ev_word} 0")
        kvmsr_init_tran.writeAction(f"evlb {init_ev_word} {self.lane_init_inkvset_ev_label}")
        kvmsr_init_tran.writeAction(f"movrl {init_ev_word} 0({temp_lm_ptr}) 1 8")
        if self.debug_flag:
            kvmsr_init_tran.writeAction(f"print '[DEBUG][NWID %ld][{self.task}] Input initialization broadcast operands: [%ld, %lu]' {'X0'} {self.num_lane_reg} {init_ev_word}")
            kvmsr_init_tran.writeAction(f"print '[DEBUG][NWID %ld][{self.task}] Broadcast input key-value set metadata size = {self.in_kvset.meta_data_size} copy from addr %lu(0x%lx) to %lu(%0xlx)' \
                {'X0'} {'X11'} {'X11'} {temp_lm_ptr} {temp_lm_ptr}")
        kvmsr_init_tran.writeAction(f"addi {'X11'} {self.scratch[1]} 0")
        kvmsr_init_tran.writeAction(f"bcpylli {self.scratch[1]} {temp_lm_ptr} {self.in_kvset.meta_data_size << LOG2_WORD_SIZE}")
        if self.debug_flag:
            for i in range(self.in_kvset.meta_data_size):
                kvmsr_init_tran.writeAction(f"movlr {16 + i * WORD_SIZE}({send_buffer_ptr}) {self.scratch[0]} 0 8")
                kvmsr_init_tran.writeAction(f"print '[DEBUG][NWID %ld][{self.task}] Input broadcast send operands[{i+2}] = %ld' {'X0'} {self.scratch[0]}")
        kvmsr_init_tran.writeAction(f"send_wcont {self.ev_word} {init_ret_ev_word} {send_buffer_ptr} {self.SEND_BUFFER_SIZE}")
        if self.enable_output:
            # Broadcast output kv set meta data to all the lanes
            if self.debug_flag:
                kvmsr_init_tran.writeAction(f"print '[DEBUG][NWID %ld][{self.task}] Broadcast output key-value set metadata size = {self.out_kvset.meta_data_size} copy from addr %lu(0x%lx) to %lu(%0xlx)' \
                {'X0'}  {'X11'} {'X11'} {temp_lm_ptr} {temp_lm_ptr}")
            kvmsr_init_tran.writeAction(f"addi {send_buffer_ptr} {temp_lm_ptr} {WORD_SIZE}")
            kvmsr_init_tran.writeAction(f"movir {init_ev_word} 0")
            kvmsr_init_tran.writeAction(f"evlb {init_ev_word} {self.lane_init_outkvset_ev_label}")
            kvmsr_init_tran.writeAction(f"movrl {init_ev_word} 0({temp_lm_ptr}) 1 8")
            kvmsr_init_tran.writeAction(f"addi {'X12'} {self.scratch[1]} 0")
            kvmsr_init_tran.writeAction(f"bcpylli {self.scratch[1]} {temp_lm_ptr} {self.out_kvset.meta_data_size << LOG2_WORD_SIZE}")
            if self.debug_flag:
                kvmsr_init_tran.writeAction(f"print '[DEBUG][NWID %ld][{self.task}] Output initialization broadcast operands: [%ld, %lu]' {'X0'} {self.num_lane_reg} {init_ev_word}")
                for i in range(self.out_kvset.meta_data_size):
                    kvmsr_init_tran.writeAction(f"movlr {16 + i * WORD_SIZE}({send_buffer_ptr}) {self.scratch[0]} 0 8")
                    kvmsr_init_tran.writeAction(f"print '[DEBUG][NWID %ld][{self.task}] Output broadcast send operands[{i+2}] = %ld' {'X0'} {self.scratch[0]}")
            kvmsr_init_tran.writeAction(f"send_wcont {self.ev_word} {init_ret_ev_word} {send_buffer_ptr} {self.SEND_BUFFER_SIZE} ")

        # Added by: Jerry Ding
        if self.extension == 'load_balancer':
            inter_meta_data_addr = "X13" if self.enable_output else "X12"
            inter_queue_start  = f"X{GP_REG_BASE+6}"

            # Broadcast intermediate kv set meta data to all the lanes
            if self.debug_flag:
                kvmsr_init_tran.writeAction(f"print '[DEBUG][NWID %ld][{self.task}] Broadcast intermediate key-value set metadata size = 1 copy from addr %lu(0x%lx) to %lu(%0xlx)' \
                {'X0'}  {'X13'} {'X13'} {temp_lm_ptr} {temp_lm_ptr}")
            # Set intermediate key queue start and end
            kvmsr_init_tran.writeAction(f"addi {inter_meta_data_addr} {temp_lm_ptr} 0")
            kvmsr_init_tran.writeAction(f"movlr 0({temp_lm_ptr}) {inter_queue_start} 0 {WORD_SIZE}")
            kvmsr_init_tran.writeAction(f"movir {temp_lm_ptr} {self.inter_queue_metadata_offset}")
            kvmsr_init_tran.writeAction(f"add {'X7'} {temp_lm_ptr} {temp_lm_ptr}")
            kvmsr_init_tran.writeAction(f"movrl {inter_queue_start} 0({temp_lm_ptr}) 1 {WORD_SIZE}")
            kvmsr_init_tran.writeAction(f"movrl {inter_queue_start} 0({temp_lm_ptr}) 0 {WORD_SIZE}")

            # Set intermediate key value dictionary start and end
            kvmsr_init_tran.writeAction(f"addi {inter_meta_data_addr} {temp_lm_ptr} 0")
            kvmsr_init_tran.writeAction(f"movlr {WORD_SIZE}({temp_lm_ptr}) {inter_queue_start} 0 {WORD_SIZE}")
            kvmsr_init_tran.writeAction(f"movir {temp_lm_ptr} {self.inter_dict_metadata_offset}")
            kvmsr_init_tran.writeAction(f"add {'X7'} {temp_lm_ptr} {temp_lm_ptr}")
            kvmsr_init_tran.writeAction(f"movrl {inter_queue_start} 0({temp_lm_ptr}) 1 {WORD_SIZE}")
            kvmsr_init_tran.writeAction(f"movrl {inter_queue_start} 0({temp_lm_ptr}) 0 {WORD_SIZE}")

            kvmsr_init_tran.writeAction(f"addi {send_buffer_ptr} {temp_lm_ptr} {WORD_SIZE}")
            # Start of send buffer: init interkvset event word
            kvmsr_init_tran.writeAction(f"movir {init_ev_word} 0")
            kvmsr_init_tran.writeAction(f"evlb {init_ev_word} {self.lane_init_interkvset_ev_label}")
            kvmsr_init_tran.writeAction(f"movrl {init_ev_word} 0({temp_lm_ptr}) 1 {WORD_SIZE}")
            # X8: intermediate kvset pointer
            kvmsr_init_tran.writeAction(f"addi {inter_meta_data_addr} {self.scratch[0]} 0")
            kvmsr_init_tran.writeAction(f"movlr {WORD_SIZE}({self.scratch[0]}) {self.scratch[1]} 0 {WORD_SIZE}")
            kvmsr_init_tran.writeAction(f"movrl {self.scratch[1]} 0({temp_lm_ptr}) 1 {WORD_SIZE}")
            # X9: global push key event word
            kvmsr_init_tran.writeAction(f"addi {'X2'} {self.scratch[1]} 0")
            kvmsr_init_tran.writeAction(f"evlb {self.scratch[1]} {self.glb_mstr_push_key_ev_label}")
            # kvmsr_init_tran.writeAction(f"evlb {self.scratch[1]} {self.lane_init_interkvset_ev_label}")
            kvmsr_init_tran.writeAction(f"movrl {self.scratch[1]} 0({temp_lm_ptr}) 1 {WORD_SIZE}")
            # X10: global claim work event word
            kvmsr_init_tran.writeAction(f"addi {'X2'} {self.scratch[1]} 0")
            kvmsr_init_tran.writeAction(f"evlb {self.scratch[1]} {self.glb_mstr_claim_work_ev_label}")
            kvmsr_init_tran.writeAction(f"movrl {self.scratch[1]} 0({temp_lm_ptr}) 1 {WORD_SIZE}")
            kvmsr_init_tran.writeAction(f"send_wcont {self.ev_word} {init_ret_ev_word} {send_buffer_ptr} {self.SEND_BUFFER_SIZE} ")

        #######################

        kvmsr_init_tran.writeAction(f"movir {init_counter} 0")
        kvmsr_init_tran.writeAction(f"addi {'X9'} {part_parameter} 0")
        kvmsr_init_tran.writeAction(f"yield")
                
        fin_kvmsr_init_label = "finish_initialize_udkvmsr"
        if self.debug_flag:
            kvmsr_init_fin_tran.writeAction(f"print ' '")
            kvmsr_init_fin_tran.writeAction(f"print '[DEBUG][NWID %ld][{self.task}] Event <{self.kvmsr_init_fin_ev_label}> ev_word=%ld continuation=%ld' {'X0'} {'EQT'} {'X1'}")
        kvmsr_init_fin_tran.writeAction(f"addi {init_counter} {init_counter} 1")
        kvmsr_init_fin_tran.writeAction(f"bgei {init_counter} {self.num_init_events} {fin_kvmsr_init_label}")
        kvmsr_init_fin_tran.writeAction(f"yield")
        # Finish initialization, start the main loop for UDKVMSR program
        set_ev_label(kvmsr_init_fin_tran, self.ev_word, self.glb_mstr_init_ev_label, label =fin_kvmsr_init_label)
        kvmsr_init_fin_tran.writeAction(f"sendr_wcont {self.ev_word} {self.saved_cont} {self.part_array_ptr} {part_parameter}")
        kvmsr_init_fin_tran.writeAction(f"yield")

    def __init_lane_scratchpad(self, tran: EFAProgram.Transition) -> EFAProgram.Transition:

        lm_base     = f"X{GP_REG_BASE+4}"
        tran.writeAction("mov_imm2reg UDPR_0 0")
        # Initialize termination counters (private per worker lane)
        if self.map_ctr_offset >> 15 > 0:
            tran.writeAction(f"movir {lm_base} {self.map_ctr_offset}")
            tran.writeAction(f"add {lm_base} {'X7'} {lm_base}")
        else:
            tran.writeAction(f"addi X7 {lm_base} {self.map_ctr_offset}")
        tran.writeAction(f"move UDPR_0 {0}({lm_base}) 0 8")
        tran.writeAction(f"move UDPR_0 {self.reduce_ctr_offset - self.map_ctr_offset}({lm_base}) 0 8")
        tran.writeAction(f"move UDPR_0 {self.num_reduce_th_offset - self.map_ctr_offset}({lm_base}) 0 8")
        tran.writeAction(f"movir {self.scratch[0]} {self.max_reduce_th_per_lane}")
        tran.writeAction(f"move {self.scratch[0]} {self.max_red_th_offset - self.map_ctr_offset}({lm_base}) 0 8")
        tran.writeAction(f"subi {'X8'} {self.scratch[0]} 1")
        tran.writeAction(f"move {self.scratch[0]} {self.nwid_mask_offset - self.map_ctr_offset}({lm_base}) 0 8")
        tran.writeAction(f"move {'X9'} {self.base_nwid_offset - self.map_ctr_offset}({lm_base}) 0 8")

        # Initialize the per lane private cache in scratchpad to merge Read-Modify-Write updates and ensure TSO
        if self.enable_cache:
            cache_init_loop_label = "init_cache_loop"
            ival        = f"X{GP_REG_BASE+0}"
            cache_base  = f"X{GP_REG_BASE+1}"
            init_ctr    = f"X{GP_REG_BASE+2}"
            num_entries = f"X{GP_REG_BASE+3}"
            cache_bound = f"X{GP_REG_BASE+4}"
            # tran.writeAction(f"mov_imm2reg {ival} {(1<<21)-1}")
            # tran.writeAction(f"sli {ival} {ival} {self.INACTIVE_MASK_SHIFT-20}")
            tran.writeAction(f"movir {ival} {self.cache_ival}")
            tran.writeAction(f"movir {num_entries} {self.cache_size}")
            tran.writeAction(f"movir {cache_base} {self.cache_offset}")
            tran.writeAction(f"add {'X7'} {cache_base} {cache_base}")
            if self.debug_flag and self.print_level > 3:
                tran.writeAction(f"print '[DEBUG][NWID %ld][{self.task}] Initialize scratchpad cache base addr = %lu(0x%lx) " + 
                                 f"initial value = %lu(0x%lx)' {'X0'} {cache_base} {cache_base} {ival} {ival}")
            if self.power_of_two_entry_size:
                tran.writeAction(f"mov_imm2reg {init_ctr} 0")
                tran.writeAction(f"{cache_init_loop_label}: movwrl {ival} {cache_base}({init_ctr},1,{int(log2(self.cache_entry_size))})")
                tran.writeAction(f"blt {init_ctr} {num_entries} {cache_init_loop_label}")
            else:
                tran.writeAction(f"muli {num_entries} {cache_bound} {self.cache_entry_bsize}")
                tran.writeAction(f"add {cache_base} {cache_bound} {cache_bound}")
                tran.writeAction(f"{cache_init_loop_label}: movrl {ival} {0}({cache_base}) 0 8")
                tran.writeAction(f"addi {cache_base} {cache_base} {self.cache_entry_bsize}")
                tran.writeAction(f"blt {cache_base} {cache_bound} {cache_init_loop_label}")

        # Added by: Jerry Ding
        if self.extension == 'load_balancer':
            addr = f"X{GP_REG_BASE+5}"

            # Initialize the materializing metadata
            tran.writeAction(f"movir {self.scratch[0]} {self.materializing_metadata_offset}")
            tran.writeAction(f"add {'X7'} {self.scratch[0]} {addr}")
            tran.writeAction(f"movir {self.scratch[1]} {self.materialize_kv_cache_offset}")
            tran.writeAction(f"add {'X7'} {self.scratch[1]} {self.scratch[1]}")
            tran.writeAction(f"movrl {self.scratch[1]} 0({addr}) 1 {WORD_SIZE}")
            tran.writeAction(f"movrl {self.scratch[1]} 0({addr}) 1 {WORD_SIZE}")
            tran.writeAction(f"movir {self.scratch[1]} 1")
            tran.writeAction(f"movrl {self.scratch[1]} 0({addr}) 1 {WORD_SIZE}")

            tran.writeAction(f"movir {self.scratch[0]} {self.intermediate_cache_offset}")
            tran.writeAction(f"add {'X7'} {self.scratch[0]} {addr}")
            tran.writeAction(f"movir {self.scratch[1]} {0}")
            tran.writeAction(f"movrl {self.scratch[1]} 0({addr}) 1 {WORD_SIZE}")

            # tran.writeAction(f"movir {addr} {self.unresolved_kv_count_offset}")
            # tran.writeAction(f"add {'X7'} {addr} {addr}")
            # tran.writeAction(f"movir {self.scratch[0]} {0}")
            # tran.writeAction(f"movrl {self.scratch[0]} 0({addr}) 0 {WORD_SIZE}")

            # tran.writeAction(f"movir {addr} {self.push_key_cont_offset}")
            # tran.writeAction(f"add {'X7'} {addr} {addr}")
            # tran.writeAction(f"movrl {'X9'} 0({addr}) 0 {WORD_SIZE}")

            # tran.writeAction(f"movir {addr} {self.claim_work_cont_offset}")
            # tran.writeAction(f"add {'X7'} {addr} {addr}")
            # tran.writeAction(f"movrl {'X10'} 0({addr}) 0 {WORD_SIZE}")



        ######################

        return tran
            
    def __gen_broadcast_init(self):
        
        init_kvmsr_broadcast = Broadcast(self.state, self.task, self.debug_flag)
        
        init_kvmsr_broadcast.gen_broadcast()
        
        init_inkvset_tran = self.state.writeTransition("eventCarry", self.state, self.state, self.lane_init_inkvset_ev_label)
        
        '''
        Event:      Store input kvset metadata to scratchpad
        Operands:   X8 ~ X[8+in_kvset.meta_data_size]: input kvset metadata 
        '''
        metadata_addr = f"X{GP_REG_BASE+0}"
        if self.debug_flag and self.print_level > 5:
            init_inkvset_tran.writeAction(f"print ' '")
            init_inkvset_tran.writeAction(f"print '[DEBUG][NWID %ld][{self.task}] Event <{self.lane_init_inkvset_ev_label}> ev_word=%ld' {'X0'} {'EQT'}")
        init_inkvset_tran.writeAction(f"movir {metadata_addr} {self.in_kvset_offset}")
        init_inkvset_tran.writeAction(f"add {'X7'} {metadata_addr} {metadata_addr}")
        init_inkvset_tran.writeAction(f"bcpyoli {'X8'} {metadata_addr} {self.in_kvset.meta_data_size}")
        init_inkvset_tran.writeAction(f"sendr_reply X0 X16 {self.scratch[0]}")
        init_inkvset_tran.writeAction("yield_terminate")
        
        if self.enable_output:
            init_outkvset_tran = self.state.writeTransition("eventCarry", self.state, self.state, self.lane_init_outkvset_ev_label)
            
            '''
            Event:      Store output kvset metadata to scratchpad
            Operands:   X8 ~ X[8+out_kvset.meta_data_size]: input kvset metadata 
            '''
            metadata_addr = f"X{GP_REG_BASE+0}"
            if self.debug_flag and self.print_level > 5:
                init_outkvset_tran.writeAction(f"print ' '")
                init_outkvset_tran.writeAction(f"print '[DEBUG][NWID %ld][{self.task}] Event <{self.lane_init_outkvset_ev_label}> ev_word=%ld' {'X0'} {'EQT'}")
            init_outkvset_tran.writeAction(f"movir {metadata_addr} {self.out_kvset_offset}")
            init_outkvset_tran.writeAction(f"add {'X7'} {metadata_addr} {metadata_addr}")
            init_outkvset_tran.writeAction(f"bcpyoli {'X8'} {metadata_addr}  {self.out_kvset.meta_data_size}")
            init_outkvset_tran.writeAction(f"sendr_reply X0 X16 {self.scratch[0]}")
            init_outkvset_tran.writeAction("yield_terminate")
            
        lane_init_sp_tran   = self.state.writeTransition("eventCarry", self.state, self.state, self.lane_init_sp_ev_label)

        '''
        Event:      Initialize lane scratchpad
        Operands:   X8: number of workers
        '''
        if self.debug_flag and self.print_level > 5:
            lane_init_sp_tran.writeAction(f"print ' '")
            lane_init_sp_tran.writeAction(f"print '[DEBUG][NWID %ld][{self.task}] Event <kvmsr_lane_sp_init> ev_word=%ld' {'X0'} {'EQT'}")
        lane_init_sp_tran = self.__init_lane_scratchpad(lane_init_sp_tran)
        lane_init_sp_tran.writeAction(f"sendr_reply X0 X16 {self.scratch[0]}")
        lane_init_sp_tran.writeAction("yield_terminate")

        # Added by: Jerry Ding
        if self.extension == 'load_balancer':
            '''
            Event:      Store intermediate kvset metadata to scratchpad
            Operands:   X8: pointer to intermediate kv set
                        X9: Event word to global push key event
                        X10: Event word to global claim work event
            '''
            init_interkvset_tran = self.state.writeTransition("eventCarry", self.state, self.state, self.lane_init_interkvset_ev_label)

            metadata_addr = f"X{GP_REG_BASE+0}"
            init_interkvset_tran.writeAction(f"movir {metadata_addr} {self.unresolved_kv_count_offset}")
            init_interkvset_tran.writeAction(f"add {'X7'} {metadata_addr} {metadata_addr}")
            init_interkvset_tran.writeAction(f"movir {self.scratch[0]} {0}")
            init_interkvset_tran.writeAction(f"movrl {self.scratch[0]} 0({metadata_addr}) 0 {WORD_SIZE}")

            init_interkvset_tran.writeAction(f"movir {metadata_addr} {self.push_key_cont_offset}")
            init_interkvset_tran.writeAction(f"add {'X7'} {metadata_addr} {metadata_addr}")
            init_interkvset_tran.writeAction(f"movrl {'X9'} 0({metadata_addr}) 0 {WORD_SIZE}")

            init_interkvset_tran.writeAction(f"movir {metadata_addr} {self.claim_work_cont_offset}")
            init_interkvset_tran.writeAction(f"add {'X7'} {metadata_addr} {metadata_addr}")
            init_interkvset_tran.writeAction(f"movrl {'X10'} 0({metadata_addr}) 0 {WORD_SIZE}")

            init_interkvset_tran.writeAction(f"sendr_reply X0 X16 {self.scratch[0]}")
            init_interkvset_tran.writeAction("yieldt")
        ######################



    def __gen_global_master(self):
        
        glb_mstr_init_tran  = self.state.writeTransition("eventCarry", self.state, self.state, self.glb_mstr_init_ev_label)

        glb_mstr_loop_tran  = self.state.writeTransition("eventCarry", self.state, self.state, self.glb_mstr_loop_ev_label)

        self.num_part_issued    = f"X{GP_REG_BASE+1}"
        self.part_array_stride  = f"X{GP_REG_BASE+2}"
        self.num_map_gen    = f"X{GP_REG_BASE+3}"
        part_stride     = f"X{GP_REG_BASE+4}"
        num_node_active = f"X{GP_REG_BASE+5}"
        ndid_stride     = f"X{GP_REG_BASE+6}"
        nd_mstr_nwid    = f"X{GP_REG_BASE+7}"
        num_partitions  = f"X{GP_REG_BASE+8}"
        part_parameter  = "X9"

        # Added by: Jerry Ding
        if self.extension == 'load_balancer':
            num_node_worker_active  = f"X{GP_REG_BASE+10}"


        glb_mstr_loop_label     = "glb_master_loop"
        glb_mstr_fin_map_label  =  "global_master_fin_map"
        glb_mstr_full_label     = "global_master_full_child"
        glb_mstr_fin_fetch_label = "global_master_fin_fetch"
        glb_mstr_init_sync_label = "global_master_init_sync"
        
        if self.debug_flag:
            glb_mstr_init_tran.writeAction(f"print ' '")
            glb_mstr_init_tran.writeAction(f"print '[DEBUG][NWID %ld][{self.task}] Event <{self.glb_mstr_init_ev_label}> ev_word=%ld partition_array=%ld(0x%lx) Number of partitions per lane = %ld' \
                {'X0'} {'EQT'} {'X8'} {'X8'} {'X9'}")
        # Added by: Jerry Ding
        if self.extension == 'load_balancer':
            glb_mstr_init_tran.writeAction(f"movir {num_node_worker_active} {0}")
        glb_mstr_init_tran.writeAction(f"mul {self.num_lane_reg} {part_parameter} {num_partitions}")
        get_num_node(glb_mstr_init_tran, self.num_lane_reg, self.num_child, self.mod_zero_label, self.scratch[0])
        glb_mstr_init_tran.writeAction(f"{self.mod_zero_label}: mov_imm2reg {ndid_stride} {UD_PER_NODE * LANE_PER_UD}")
        glb_mstr_init_tran.writeAction(f"bge {self.num_lane_reg} {ndid_stride} {glb_mstr_full_label}")
        glb_mstr_init_tran.writeAction(f"addi {self.num_lane_reg} {ndid_stride} 0")    # Adjust nwid stride if not all the lanes in a node is used.
        glb_mstr_init_tran.writeAction(f"{glb_mstr_full_label}: mul {ndid_stride} {part_parameter} {part_stride}")
        glb_mstr_init_tran.writeAction(f"lshift {part_stride} {self.part_array_stride} {LOG2_WORD_SIZE + self.log2_in_kvset_iter_size}")
        if self.debug_flag:
            glb_mstr_init_tran.writeAction(f"print '[DEBUG][NWID %ld][{self.task}] Init global master ndid_stride = %ld part_stride = %ld part_array_stride = %ld' {'X0'} {ndid_stride} {part_stride} {self.part_array_stride}")
        glb_mstr_init_tran.writeAction(f"mov_reg2reg X0 {nd_mstr_nwid}")
        glb_mstr_init_tran.writeAction(f"movir {num_node_active} 0") 
        glb_mstr_init_tran = set_ev_label(glb_mstr_init_tran, self.ev_word,
            self.nd_mstr_init_ev_label, new_thread=True)
        # Create the node master on each node and send out a partition of input kv pairs
        glb_mstr_init_tran.writeAction(f"{glb_mstr_loop_label}: ev_update_reg_2 \
            {self.ev_word} {self.ev_word} {nd_mstr_nwid} {nd_mstr_nwid} 8")
        glb_mstr_init_tran.writeAction(format_pseudo(f"sendr3_wret {self.ev_word} {self.glb_mstr_loop_ev_label} \
            {self.part_array_ptr} {self.part_array_stride} {self.num_lane_reg}", self.scratch[0], self.send_temp_reg_flag))
        glb_mstr_init_tran.writeAction(f"add {ndid_stride} {nd_mstr_nwid} {nd_mstr_nwid}")
        glb_mstr_init_tran.writeAction(f"add {self.part_array_stride} {self.part_array_ptr} {self.part_array_ptr} ")
        glb_mstr_init_tran.writeAction(f"addi {num_node_active} {num_node_active} 1")
        # Added by: Jerry Ding
        if self.extension == 'load_balancer':
            glb_mstr_init_tran.writeAction(f"addi {num_node_worker_active} {num_node_worker_active} 1")
        glb_mstr_init_tran.writeAction(f"blt {num_node_active} {self.num_child} {glb_mstr_loop_label}")
        glb_mstr_init_tran.writeAction(f"mul {num_node_active} {part_stride} {self.num_part_issued}")
        # glb_mstr_init_tran.writeAction(f"lshift {num_node_active} {self.num_part_issued} {LOG2_LANE_PER_UD + LOG2_UD_PER_NODE}")
        glb_mstr_init_tran.writeAction(f"mov_imm2reg {self.num_map_gen} 0")    # total number of kv_pair generated by mapper
        if self.debug_flag:
            glb_mstr_init_tran.writeAction(f"print '[DEBUG][NWID %ld][{self.task}] Global master num_partitions = %ld, num_part_issued = %ld' \
                {'X0'} {num_partitions} {self.num_part_issued}")
        glb_mstr_init_tran.writeAction("yield")

        '''
        Event:      Global master loop
        Operands:   X8: Number of map tasks generated
                    X9: Return node master thread loop event word
        If load balancer is enabled:
        Operands:   X8: if == self._finish_flag: node terminate
                        else:                    node all mappers finished
        '''

        # Added by: Jerry Ding
        if self.extension == 'load_balancer':
            glb_mstr_loop_tran.writeAction(f"beqi X8 {self._finish_flag} node_finished")

        if self.debug_flag:
            glb_mstr_loop_tran.writeAction(f"print ' '")
            glb_mstr_loop_tran.writeAction(f"print '[DEBUG][NWID %ld][{self.task}] Event <kvmsr_global_master_loop> ev_word=%ld income_cont = %lu' {'X0'} {'EQT'} {'X1'}")
        glb_mstr_loop_tran.writeAction(f"add X8 {self.num_map_gen} {self.num_map_gen}")
        glb_mstr_loop_tran.writeAction(f"bge {self.num_part_issued} {num_partitions} {glb_mstr_fin_fetch_label}")

        # Send next non-assigned partitions to the node
        glb_mstr_loop_tran.writeAction(format_pseudo(f"sendr3_wret X1 {self.glb_mstr_loop_ev_label} \
            {self.part_array_ptr} {self.part_array_stride} {self.num_lane_reg}", self.scratch[0], self.send_temp_reg_flag))
        glb_mstr_loop_tran.writeAction(f"add {part_stride} {self.num_part_issued} {self.num_part_issued}")
        glb_mstr_loop_tran.writeAction(f"add {self.part_array_stride} {self.part_array_ptr} {self.part_array_ptr} ")
        if self.debug_flag:
            glb_mstr_loop_tran.writeAction(f"print '[DEBUG][NWID %ld][{self.task}] Global master num_partitions = %ld, num_part_issued = %ld num_map_generated = %ld' {'X0'} {num_partitions} {self.num_part_issued} {self.num_map_gen}")
        glb_mstr_loop_tran.writeAction(f"yield")

        # Finish issuing all the partitions of input kv set, terminate the node master thread
        glb_mstr_loop_tran.writeAction(f"{glb_mstr_fin_fetch_label}: subi {num_node_active} {num_node_active} 1")
        # Added by: Jerry Ding
        if self.extension == 'original':
            glb_mstr_loop_tran = set_ev_label(glb_mstr_loop_tran, self.ev_word, self.nd_mstr_term_ev_label, "X1")
            glb_mstr_loop_tran.writeAction(f"sendr_wcont {self.ev_word} X2 {self.part_array_ptr} {self.part_array_ptr}")
            if self.debug_flag:
                glb_mstr_loop_tran.writeAction(f"print '[DEBUG][NWID %ld][{self.task}] Global master num_map_generated = %ld, number of active node = %ld' {'X0'} {self.num_map_gen} {num_node_active}")
            glb_mstr_loop_tran.writeAction(f"beqi {num_node_active} 0 {glb_mstr_fin_map_label}")
            glb_mstr_loop_tran.writeAction(f"yield")

            # All the map master threads are termianted, check if there is any intermediate key-value pairs generated by the map threads
            glb_mstr_loop_tran.writeAction(f"{glb_mstr_fin_map_label}: bnei {self.num_map_gen} 0 {glb_mstr_init_sync_label}")
            # UDKVMSR finishes, return back to user continuation
            set_ignore_cont(glb_mstr_loop_tran, self.scratch[0])
            glb_mstr_loop_tran.writeAction(f"sendr_wcont {self.saved_cont} {self.scratch[0]} {self.num_lane_reg} {self.num_map_gen}")
            glb_mstr_loop_tran.writeAction(f"yieldt")
            # Map emits intermediate pairs, start the global synchronization
            glb_mstr_loop_tran = set_ev_label(glb_mstr_loop_tran, self.ev_word, self.glb_sync_init_ev_label, src_ev="X2", new_thread=True, label=glb_mstr_init_sync_label)
            if self.enable_cache:
                set_ev_label(glb_mstr_loop_tran, self.scratch[0], self.cache_flush_ev_label)
                glb_mstr_loop_tran.writeAction(f"sendr_wcont {self.ev_word} {self.scratch[0]} {self.num_lane_reg} {self.num_map_gen}")
                if self.debug_flag or self.print_level >= 1:
                    glb_mstr_loop_tran.writeAction(f"print '[DEBUG][NWID %ld][{self.task}] Finish dispatch all the map tasks. Start the global synchronization, ev_word = %lu' {'X0'} {self.ev_word}")
                glb_mstr_loop_tran.writeAction(f"yield")
            else:
                glb_mstr_loop_tran.writeAction(f"sendr_wcont {self.ev_word} {self.saved_cont} {self.num_lane_reg} {self.num_map_gen}")
                if self.debug_flag or self.print_level >= 1:
                    glb_mstr_loop_tran.writeAction(f"print '[DEBUG][NWID %ld][{self.task}] Finish dispatch all the map tasks. Start the global synchronization, ev_word = %lu' {'X0'} {self.ev_word}")
                glb_mstr_loop_tran.writeAction(f"yield_terminate")

        # Added by: Jerry Ding
        if self.extension == 'load_balancer':
            glb_mstr_loop_tran.writeAction(f"yield")

            # If self._finish_flag is returned, meaning a ud's workers all finished, terminate
            glb_mstr_loop_tran.writeAction(f"node_finished: subi {num_node_worker_active} {num_node_worker_active} {1}")
            glb_mstr_loop_tran = set_ev_label(glb_mstr_loop_tran, self.ev_word, self.nd_mstr_term_ev_label, "X1")
            glb_mstr_loop_tran.writeAction(f"sendr_wcont {self.ev_word} X2 {self.part_array_ptr} {self.part_array_ptr}")
            glb_mstr_loop_tran.writeAction(f"blei {num_node_worker_active} {0} kvmsr_finished")
            glb_mstr_loop_tran.writeAction(f"yield")
            # All nodes' workers finished
            if self.enable_cache:
                # Flush the cache
                set_ev_label(glb_mstr_loop_tran, self.ev_word, self.cache_flush_ev_label, label = "kvmsr_finished")
                glb_mstr_loop_tran.writeAction(f"sendr_wcont {self.ev_word} {self.saved_cont} {self.num_lane_reg} {self.num_map_gen}")
                glb_mstr_loop_tran.writeAction(f"yield")
            else:
                # send to saved continuation word
                # glb_mstr_loop_tran.writeAction(f"kvmsr_finished: movir {self.scratch[0]} -1")
                # glb_mstr_loop_tran.writeAction(f"sri {self.scratch[0]} {self.scratch[0]} 1")
                glb_mstr_loop_tran.writeAction(f"kvmsr_finished: print 'Load Balancing UDKVMSR finished.' ")
                set_ignore_cont(glb_mstr_loop_tran, self.scratch[0])
                glb_mstr_loop_tran.writeAction(f"sendr_wcont {self.saved_cont} {self.scratch[0]} {self.scratch[1]} {self.scratch[1]}")
                glb_mstr_loop_tran.writeAction(f"yieldt")

        
        if self.enable_cache:
            buffer_addr = f"X{GP_REG_BASE+4}"
            '''
            Event:      Finish UDKVMSR, start flushing the cache.
            X1:         Continuation
            '''
            flush_tran = self.state.writeTransition("eventCarry", self.state, self.state, self.cache_flush_ev_label)
            flush_tran.writeAction(f"movir {buffer_addr} {self.send_buffer_offset}")
            flush_tran.writeAction(f"add {buffer_addr} {'X7'} {buffer_addr}")
            flush_tran.writeAction(f"movrl {self.num_lane_reg} 0({buffer_addr}) 0 8")
            flush_tran.writeAction(f"movir {self.scratch[0]} 0")
            flush_tran.writeAction(f"evlb {self.scratch[0]} {self.flush_lane_ev_label}")
            flush_tran.writeAction(f"movrl {self.scratch[0]} {WORD_SIZE}({buffer_addr}) 0 8")
            set_ev_label(flush_tran, self.ev_word, self.glb_bcst_ev_label, new_thread = True)
            flush_tran.writeAction(f"send_wret {self.ev_word} {self.cache_flush_ret_ev_label} {buffer_addr} {self.SEND_BUFFER_SIZE} {self.scratch[0]}")
            flush_tran.writeAction(f"yield")

            '''
            Finish flushing the cache, return to user continuation
            '''
            flush_ret_tran = self.state.writeTransition("eventCarry", self.state, self.state, self.cache_flush_ret_ev_label)
            flush_ret_tran.writeAction(f"print ' '")
            flush_ret_tran.writeAction(f"print '[DEBUG][NWID %ld][{self.cache_flush_ret_ev_label}] Finish flushing the cache. UDKVMSR program {self.task} terminates, " + 
                                        f"number of reduce task process = %ld. Return to user continuation %lu' {'X0'} {self.num_map_gen} {self.saved_cont}")
            set_ignore_cont(flush_ret_tran, self.scratch[0])
            flush_ret_tran.writeAction(f"sendr_wcont {self.saved_cont} {self.scratch[0]} {self.num_map_gen} {self.num_map_gen}")
            flush_ret_tran.writeAction(f"yieldt")
            
        return

    def __gen_node_master(self):

        nd_mstr_init_tran   = self.state.writeTransition("eventCarry", self.state, self.state, self.nd_mstr_init_ev_label)

        nd_mstr_loop_tran   = self.state.writeTransition("eventCarry", self.state, self.state, self.nd_mstr_loop_ev_label)

        nd_mstr_term_tran   = self.state.writeTransition("eventCarry", self.state, self.state, self.nd_mstr_term_ev_label)

        num_ud_active   = f"X{GP_REG_BASE+5}"
        udid_stride     = f"X{GP_REG_BASE+6}"
        ud_mstr_nwid    = f"X{GP_REG_BASE+7}"
        part_array_end  = f"X{GP_REG_BASE+8}"

        nd_mstr_loop_label  = "node_master_loop"
        nd_mstr_fin_fetch_label = "node_master_fin_fetch"
        nd_mstr_fin_part_label  = "node_master_fin_partition"
        nd_mstr_full_label  = "node_master_full_child"

        '''
        Event:      Initialize node master
        Operands:   X8: Pointer to the base address of the initial partition
                    X9: Length of partition array assigned to this node in Bytes
                    X10: Number of lanes in total
        '''

        # Added by: Jerry Ding
        if self.extension == 'load_balancer':
            num_ud_worker_active  = f"X{GP_REG_BASE+10}"
            nd_mstr_init_tran.writeAction(f"movir {num_ud_worker_active} {0}")

        if self.debug_flag:
            nd_mstr_init_tran.writeAction(f"print ' '")
            nd_mstr_init_tran.writeAction(f"rshift {'X9'} {self.scratch[0]} {LOG2_WORD_SIZE + self.log2_in_kvset_iter_size}")
            nd_mstr_init_tran.writeAction(f"print '[DEBUG][NWID %ld][{self.task}] Event <{self.nd_mstr_init_ev_label}> ev_word = %lu income_cont = %lu Operands: partition_base = %ld(0x%lx) assigned partition array length = %ld num_part_assigned = %ld num_lanes = %ld' \
                {'X0'} {'EQT'} {'X1'} {'X8'} {'X8'} {'X9'} {self.scratch[0]} {'X10'}")
        nd_mstr_init_tran.writeAction(f"mov_reg2reg X1 {self.saved_cont}")
        nd_mstr_init_tran.writeAction(f"mov_reg2reg X8 {self.part_array_ptr}")
        nd_mstr_init_tran.writeAction(f"mov_reg2reg X10 {self.num_lane_reg}")
        get_num_ud_per_node(nd_mstr_init_tran, self.num_lane_reg, self.num_child, self.mod_zero_label, self.scratch[0])
        nd_mstr_init_tran.writeAction(f"{self.mod_zero_label}: add X9 {self.part_array_ptr} {part_array_end}")
        nd_mstr_init_tran.writeAction(f"mov_imm2reg {num_ud_active} 0")
        nd_mstr_init_tran.writeAction(f"mov_imm2reg {udid_stride} {LANE_PER_UD}")
        nd_mstr_init_tran.writeAction(f"bge {self.num_lane_reg} {udid_stride} {nd_mstr_full_label}")
        nd_mstr_init_tran.writeAction(f"addi {self.num_lane_reg} {udid_stride} 0")  # Adjust nwid stride if not all the lanes in a updown is used.
        nd_mstr_init_tran.writeAction(f"{nd_mstr_full_label}: div {'X9'} {self.num_child} {self.part_array_stride}")
        if self.debug_flag:
            nd_mstr_init_tran.writeAction(f"rshift {self.part_array_stride} {self.scratch[1]} {LOG2_WORD_SIZE + self.log2_in_kvset_iter_size}")
            nd_mstr_init_tran.writeAction(f"print '[DEBUG][NWID %ld][{self.task}] Init node master udid_stride = %ld part_stride = %ld part_array_stride = %ld assigned partition array end address = %ld(0x%x)' \
                {'X0'} {udid_stride} {self.scratch[1]} {self.part_array_stride} {part_array_end} {part_array_end}")
        nd_mstr_init_tran.writeAction(f"addi X0 {ud_mstr_nwid} 0")
        nd_mstr_init_tran = set_ev_label(nd_mstr_init_tran, self.ev_word, self.ud_mstr_init_ev_label, new_thread=True)

        # Create the node master on each node and send out a partition of input kv pairs
        nd_mstr_init_tran.writeAction(f"{nd_mstr_loop_label}: ev {self.ev_word} {self.ev_word} {ud_mstr_nwid} {ud_mstr_nwid} 8")
        nd_mstr_init_tran.writeAction(f"sendr3_wret {self.ev_word} {self.nd_mstr_loop_ev_label} \
            {self.part_array_ptr} {self.part_array_stride} {self.num_lane_reg} {self.scratch[0]}")
        if self.debug_flag or self.print_level >= 2:
            nd_mstr_init_tran.writeAction(f"print '[DEBUG][NWID %ld][{self.task}] Node master sends partition to ud %ld master part_array_ptr = %ld(0x%lx)' \
                {'X0'} {ud_mstr_nwid} {self.part_array_ptr} {self.part_array_ptr}")
        nd_mstr_init_tran.writeAction(f"add {udid_stride} {ud_mstr_nwid} {ud_mstr_nwid}")
        nd_mstr_init_tran.writeAction(f"add {self.part_array_stride} {self.part_array_ptr} {self.part_array_ptr} ")
        nd_mstr_init_tran.writeAction(f"addi {num_ud_active} {num_ud_active} 1")
        # Added by: Jerry Ding
        if self.extension == 'load_balancer':
            nd_mstr_init_tran.writeAction(f"addi {num_ud_worker_active} {num_ud_worker_active} 1")
        nd_mstr_init_tran.writeAction(f"blt {num_ud_active} {self.num_child} {nd_mstr_loop_label}")
        nd_mstr_init_tran.writeAction(f"mov_imm2reg {self.num_map_gen} 0")
        nd_mstr_init_tran.writeAction("yield")


        '''
        Event:      Node master loop
        Operands:   X8: Number of map tasks generated
                    X9: Return updown master thread loop event word
        '''

        # Added by: Jerry Ding
        if self.extension == 'load_balancer':
            nd_mstr_loop_tran.writeAction(f"beqi X8 {self._finish_flag} ud_finished")

        if self.debug_flag:
            nd_mstr_loop_tran.writeAction(f"print ' '")
            nd_mstr_loop_tran.writeAction(f"rshift {'X1'} {self.scratch[0]} {32 + 6}")
            nd_mstr_loop_tran.writeAction(f"print '[DEBUG][NWID %ld][{self.task}] Event <{self.nd_mstr_loop_ev_label}> ev_word = %lu income_cont = %lu. Updown %ld master returns. Number of map generated = %ld' \
                {'X0'} {'EQT'} {'X1'} {self.scratch[0]} {'X8'}")
        nd_mstr_loop_tran.writeAction(f"add X8 {self.num_map_gen} {self.num_map_gen}")
        nd_mstr_loop_tran.writeAction(f"bge {self.part_array_ptr} {part_array_end} {nd_mstr_fin_fetch_label}")
        # Send next non-assigned partition to the updown
        nd_mstr_loop_tran.writeAction(format_pseudo(f"sendr3_wret X1 {self.nd_mstr_loop_ev_label} \
            {self.part_array_ptr} {self.part_array_stride} {self.num_lane_reg}", self.scratch[0], self.send_temp_reg_flag))
        if self.debug_flag:
            nd_mstr_loop_tran.writeAction(f"rshift {'X1'} {self.scratch[0]} {32}")
            nd_mstr_loop_tran.writeAction(f"rshift {'X1'} {self.scratch[1]} {24}")
            nd_mstr_loop_tran.writeAction(f"andi {self.scratch[1]} {self.scratch[1]}  {0xFF}")
            nd_mstr_loop_tran.writeAction(f"print '[DEBUG][NWID %ld][{self.task}] Node master sends part to ud %ld master tid = %ld ev_word=%ld part_array_ptr = %ld(0x%lx) node_part_end = %ld(0x%lx)' \
                {'X0'} {self.scratch[0]} {self.scratch[1]} {'X1'} {self.part_array_ptr} {self.part_array_ptr} {part_array_end} {part_array_end}")
            nd_mstr_loop_tran.writeAction(f"print '[DEBUG][NWID %ld][{self.task}] Node master num_map_generated = %ld' {'X0'} {self.num_map_gen}")
        nd_mstr_loop_tran.writeAction(f"add {self.part_array_stride} {self.part_array_ptr} {self.part_array_ptr} ")
        nd_mstr_loop_tran.writeAction(f"yield")
        # Finish issuing all the partitions of input kv set, terminate all the updown master threads
        nd_mstr_loop_tran.writeAction(f"{nd_mstr_fin_fetch_label}: subi {num_ud_active} {num_ud_active} 1")
        # Added by: Jerry Ding
        if self.extension == 'original':
            nd_mstr_loop_tran = set_ev_label(nd_mstr_loop_tran, self.ev_word, self.ud_mstr_term_ev_label, "X1")
            nd_mstr_loop_tran.writeAction(f"sendr_wcont {self.ev_word} X2 {self.part_array_ptr} {udid_stride}")
        nd_mstr_loop_tran.writeAction(f"beqi {num_ud_active} 0 {nd_mstr_fin_part_label}")
        nd_mstr_loop_tran.writeAction(f"yield")
        nd_mstr_loop_tran.writeAction(format_pseudo(f"{nd_mstr_fin_part_label}: sendr_wret {self.saved_cont} {self.nd_mstr_init_ev_label} \
            {self.num_map_gen} {self.num_map_gen}", self.scratch[0], self.send_temp_reg_flag))
        nd_mstr_loop_tran.writeAction(f"mov_imm2reg {self.num_map_gen} 0")
        nd_mstr_loop_tran.writeAction(f"yield")

        # Added by: Jerry Ding
        if self.extension == 'load_balancer':
            # If self._finish_flag is returned, meaning a ud's workers all finished, terminate
            nd_mstr_loop_tran.writeAction(f"ud_finished: subi {num_ud_worker_active} {num_ud_worker_active} {1}")
            nd_mstr_loop_tran = set_ev_label(nd_mstr_loop_tran, self.ev_word, self.ud_mstr_term_ev_label, "X1")
            nd_mstr_loop_tran.writeAction(f"sendr_wcont {self.ev_word} X2 {self.part_array_ptr} {udid_stride}")
            nd_mstr_loop_tran.writeAction(f"blei {num_ud_worker_active} {0} node_finished")
            nd_mstr_loop_tran.writeAction(f"yield")
            # If all uds' workers all finished, send to global master
            nd_mstr_loop_tran.writeAction(f"node_finished: movir {self.scratch[0]} {self._finish_flag}")
            nd_mstr_loop_tran.writeAction(f"sendr_wcont {self.saved_cont} X2 {self.scratch[0]} {self.scratch[0]}")
            nd_mstr_loop_tran.writeAction(f"yield")


        if self.debug_flag:
            nd_mstr_term_tran.writeAction(f"print ' '")
            nd_mstr_term_tran.writeAction(f"print '[DEBUG][NWID %ld][{self.task}] Event <{self.nd_mstr_term_ev_label}> ev_word = %lu income_cont = %lu' {'X0'} {'EQT'} {'X1'}")
        nd_mstr_term_tran.writeAction(f"yield_terminate")

        return

    def __gen_updown_master(self):

        ud_mstr_init_tran   = self.state.writeTransition("eventCarry", self.state, self.state, self.ud_mstr_init_ev_label)

        ud_mstr_loop_tran   = self.state.writeTransition("eventCarry", self.state, self.state, self.ud_mstr_loop_ev_label)

        ud_mstr_term_tran   = self.state.writeTransition("eventCarry", self.state, self.state, self.ud_mstr_term_ev_label)

        num_ln_active       = f"X{GP_REG_BASE+5}"
        num_part_assigned   = f"X{GP_REG_BASE+6}"
        ln_mstr_nwid        = f"X{GP_REG_BASE+7}"
        part_array_end      = f"X{GP_REG_BASE+8}"

        ud_mstr_loop_label = "updown_master_loop"
        ud_mstr_fin_fetch_label = "updown_master_fin_fetch"
        ud_mstr_fin_part_label = "updown_master_fin_partition"

        '''
        Event:      Initialize updown master
        Operands:   X8: Pointer to the base address of the initial partition
                    X9: Length of partition array assigned to this updown in Bytes
                    X10: Number of lanes in total
        '''
        # Added by: Jerry Ding
        if self.extension == 'load_balancer':
            num_ln_worker_active  = f"X{GP_REG_BASE+10}"
            ud_mstr_init_tran.writeAction(f"movir {num_ln_worker_active} {0}")

        if self.debug_flag:
            ud_mstr_init_tran.writeAction("print ' '")
            ud_mstr_init_tran.writeAction(f"rshift {'X9'} {self.scratch[0]} {LOG2_WORD_SIZE + self.log2_in_kvset_iter_size}")
            ud_mstr_init_tran.writeAction(f"print '[DEBUG][NWID %ld][{self.task}] Event <{self.ud_mstr_init_ev_label}> ev_word = %lu income_cont = %lu Operands: partition_base = %ld(0x%lx) assigned partition array length = %ld num_part = %ld num_lanes = %ld' \
                {'X0'} {'EQT'} {'X1'} {'X8'} {'X8'} {'X9'} {self.scratch[0]} {'X10'}")
        ud_mstr_init_tran.writeAction(f"mov_reg2reg X1 {self.saved_cont}")
        ud_mstr_init_tran.writeAction(f"mov_reg2reg X8 {self.part_array_ptr}")
        ud_mstr_init_tran.writeAction(f"mov_reg2reg X10 {self.num_lane_reg}")
        get_num_lane_per_ud(ud_mstr_init_tran, self.num_lane_reg, self.num_child, self.mod_zero_label)
        ud_mstr_init_tran.writeAction(f"{self.mod_zero_label}: add X9 {self.part_array_ptr} {part_array_end}")
        ud_mstr_init_tran.writeAction(f"mov_imm2reg {num_ln_active} {0}")
        ud_mstr_init_tran.writeAction(f"mov_imm2reg {self.part_array_stride} {WORD_SIZE * self.in_kvset_iter_size}")
        if self.debug_flag:
            ud_mstr_init_tran.writeAction(f"print '[DEBUG][NWID %ld][{self.task}] Init updown master part_array_stride = %ld assigned partition array end address = %ld(0x%x)' \
                {'X0'} {self.part_array_stride} {part_array_end} {part_array_end}")

        # Added by Jerry
        if self.extension == 'load_balancer':
            # Get global master network id from global_push_key event word
            ud_mstr_init_tran.writeAction(f"movir {self.scratch[0]} {self.push_key_cont_offset}")
            ud_mstr_init_tran.writeAction(f"add {'X7'} {self.scratch[0]} {self.scratch[0]}")
            ud_mstr_init_tran.writeAction(f"movlr 0({self.scratch[0]}) {self.scratch[1]} 0 {WORD_SIZE}")
            ud_mstr_init_tran.writeAction(f"sri {self.scratch[1]} {self.scratch[1]} {32}")
            # If not the same as global master network id, skip following
            if self.debug_flag:
                ud_mstr_init_tran.writeAction(f"print '[DEBUG][NWID %ld][{self.task}] Current lane %u, global master lane %u' \
                    {'X0'} {'X0'} {self.scratch[1]}")
            ud_mstr_init_tran.writeAction(f"bne {'X0'} {self.scratch[1]} not_glb_mstr_ln")
            # Not launching lane master on global master lane
            ud_mstr_init_tran.writeAction(f"addi {'X0'} {ln_mstr_nwid} {1}")
            # If num_child smaller than 64, skip following
            ud_mstr_init_tran.writeAction(f"movir {self.scratch[0]} {LANE_PER_UD}")
            ud_mstr_init_tran.writeAction(f"blt {self.num_child} {self.scratch[0]} not_glb_mstr_ln")
            # Skip first partition
            ud_mstr_init_tran.writeAction(f"add {self.part_array_stride} {self.part_array_ptr} {self.part_array_ptr} ")
            # Reduce num_child by 1
            ud_mstr_init_tran.writeAction(f"subi {self.num_child} {self.num_child} {1}")
            ud_mstr_init_tran.writeAction(f"jmp continue_ud_mstr_init")

            ud_mstr_init_tran.writeAction(f"not_glb_mstr_ln: addi X0 {ln_mstr_nwid} {0}")
        else:
            ud_mstr_init_tran.writeAction(f"mov_reg2reg X0 {ln_mstr_nwid}")

        ud_mstr_init_tran = set_ev_label(ud_mstr_init_tran, self.ev_word, self.ln_mstr_init_ev_label, new_thread=True, 
            label="continue_ud_mstr_init" if self.extension=='load_balancer' else "")
        # Create the node master on each node and send out a partition of input kv pairs
        if self.debug_flag:
            ud_mstr_init_tran.writeAction(f"print '[DEBUG][NWID %ld][{self.task}] Before ud_mstr_loop, Start lane %u' \
                {'X0'} {ln_mstr_nwid}")
        ud_mstr_init_tran.writeAction(f"{ud_mstr_loop_label}: ev {self.ev_word} {self.ev_word} {ln_mstr_nwid} {ln_mstr_nwid} 8")
        ud_mstr_init_tran.writeAction(format_pseudo(f"sendr3_wret {self.ev_word} {self.ud_mstr_loop_ev_label} \
            {self.part_array_ptr} {self.part_array_stride} {num_ln_active}", self.scratch[0], self.send_temp_reg_flag))
        if self.debug_flag:
            ud_mstr_init_tran.writeAction(f"print '[DEBUG][NWID %ld][{self.task}] Send partition to lane %ld master part_array_ptr = %ld(0x%lx) num_part_assigned = %ld' \
                {'X0'} {ln_mstr_nwid} {self.part_array_ptr} {self.part_array_ptr} {num_ln_active}")
        ud_mstr_init_tran.writeAction(f"addi {ln_mstr_nwid} {ln_mstr_nwid} {1}")
        ud_mstr_init_tran.writeAction(f"add {self.part_array_stride} {self.part_array_ptr} {self.part_array_ptr} ")
        ud_mstr_init_tran.writeAction(f"addi {num_ln_active} {num_ln_active} 1")
        # Added by: Jerry Ding
        if self.extension == 'load_balancer':
            ud_mstr_init_tran.writeAction(f"addi {num_ln_worker_active} {num_ln_worker_active} {1}")
        ud_mstr_init_tran.writeAction(f"blt {num_ln_active} {self.num_child} {ud_mstr_loop_label}")
        ud_mstr_init_tran.writeAction(f"mov_imm2reg {self.num_map_gen} 0")
        ud_mstr_init_tran.writeAction(f"addi {num_ln_active} {num_part_assigned} 0")
        ud_mstr_init_tran.writeAction("yield")

        '''
        Event:      Updown master loop
        Operands:   X8: Number of map tasks generated
                    X9: Return lane master thread loop event word
        '''
        # Added by: Jerry Ding
        if self.extension == 'load_balancer':
            ud_mstr_loop_tran.writeAction(f"beqi X8 {self._finish_flag} lane_finished")

        if self.debug_flag:
            ud_mstr_loop_tran.writeAction("print ' '")
            ud_mstr_loop_tran.writeAction(f"rshift {'X1'} {self.scratch[0]} {32}")
            ud_mstr_loop_tran.writeAction(f"print '[DEBUG][NWID %ld][{self.task}] Event <{self.ud_mstr_loop_ev_label}> ev_word = %lu income_cont = %lu. Lane %ld master returns. Number of map generated = %ld' \
                {'X0'} {'EQT'} {'X1'}  {self.scratch[0]} {'X8'}")
        ud_mstr_loop_tran.writeAction(f"add X8 {self.num_map_gen} {self.num_map_gen}")
        ud_mstr_loop_tran.writeAction(f"bge {self.part_array_ptr} {part_array_end} {ud_mstr_fin_fetch_label}")
        # Send next non-assigned partition to the lane
        ud_mstr_loop_tran.writeAction(format_pseudo(f"sendr3_wret X1 {self.ud_mstr_loop_ev_label} \
            {self.part_array_ptr} {self.part_array_stride} {num_part_assigned}", self.scratch[0], self.send_temp_reg_flag))
        if self.debug_flag:
            ud_mstr_loop_tran.writeAction(f"rshift {'X1'} {self.scratch[0]} {32}")
            ud_mstr_loop_tran.writeAction(f"rshift {'X1'} {self.scratch[1]} {24}")
            ud_mstr_loop_tran.writeAction(f"andi {self.scratch[1]} {self.scratch[1]}  {0xFF}")
            ud_mstr_loop_tran.writeAction(f"print '[DEBUG][NWID %ld][{self.task}] Send partition to lane %ld master tid %ld part_array_ptr = %ld(0x%lx) num_part_assigned = %ld' \
                {'X0'} {self.scratch[0]} {self.scratch[1]} {self.part_array_ptr} {self.part_array_ptr} {num_part_assigned}")
        if self.debug_flag or self.print_level >= 2:
            ud_mstr_loop_tran.writeAction(f"print '[DEBUG][NWID %ld][{self.task}] Updown master assignes %ld partition.' {'X0'} {num_part_assigned}")
        ud_mstr_loop_tran.writeAction(f"addi {num_part_assigned} {num_part_assigned} 1")
        ud_mstr_loop_tran.writeAction(f"add {self.part_array_stride} {self.part_array_ptr} {self.part_array_ptr} ")
        if self.debug_flag:
            ud_mstr_loop_tran.writeAction(f"print '[DEBUG][NWID %ld][{self.task}] Updown master num_map_generated = %ld' {'X0'} {self.num_map_gen}")
        ud_mstr_loop_tran.writeAction(f"yield")
        # Finish issuing the assigned input kv set, terminate all the lane master threads
        ud_mstr_loop_tran.writeAction(f"{ud_mstr_fin_fetch_label}: subi {num_ln_active} {num_ln_active} 1")
        if self.debug_flag or self.print_level >= 2:
            ud_mstr_loop_tran.writeAction(f"print '[DEBUG][NWID %ld][{self.task}] Updown master assigned all partitions, number of lane master remains active = %ld' {'X0'} {num_ln_active}")
        # Added by: Jerry Ding
        if self.extension == 'original':
            ud_mstr_loop_tran = set_ev_label(ud_mstr_loop_tran, self.ev_word, self.ln_mstr_term_ev_label, "X1")
            ud_mstr_loop_tran.writeAction(f"sendr_wcont {self.ev_word} X2 {self.part_array_ptr} {num_part_assigned}")
        if self.debug_flag:
            ud_mstr_loop_tran.writeAction(f"rshift {'X1'} {self.scratch[0]} {32}")
            ud_mstr_loop_tran.writeAction(f"rshift {'X1'} {self.scratch[1]} {24}")
            ud_mstr_loop_tran.writeAction(f"andi {self.scratch[1]} {self.scratch[1]}  {0xFF}")
            ud_mstr_loop_tran.writeAction(f"print '[DEBUG][NWID %ld][{self.task}] Updown master %ld finishes assign all pairs. Terminates lane %ld master tid %ld, remain_active_lane = %ld' \
                {'X0'} {'X0'} {self.scratch[0]} {self.scratch[1]} {num_ln_active}")
        ud_mstr_loop_tran.writeAction(f"blei {num_ln_active} 0 {ud_mstr_fin_part_label}")
        ud_mstr_loop_tran.writeAction(f"yield")
        ud_mstr_loop_tran.writeAction(format_pseudo(f"{ud_mstr_fin_part_label}: sendr_wret {self.saved_cont} \
            {self.ud_mstr_init_ev_label} {self.num_map_gen} {self.num_map_gen}", self.scratch[0], self.send_temp_reg_flag))
        if self.debug_flag:
            ud_mstr_loop_tran.writeAction(f"rshift {'X2'} {self.scratch[0]} {32}")
            ud_mstr_loop_tran.writeAction(f"rshift {'X1'} {self.scratch[1]} {24}")
            ud_mstr_loop_tran.writeAction(f"andi {self.scratch[1]} {self.scratch[1]}  {0xFF}")
            ud_mstr_loop_tran.writeAction(f"print '[DEBUG][NWID %ld][{self.task}] Updown master %ld tid %ld finishes issue num_map_generated = %ld' \
                {'X0'} {self.scratch[0]} {self.scratch[1]} {self.num_map_gen}")
            ud_mstr_loop_tran.writeAction(f"rshift {self.saved_cont} {self.scratch[0]} {32}")
            ud_mstr_loop_tran.writeAction(f"rshift {self.saved_cont} {self.scratch[1]} {24}")
            ud_mstr_loop_tran.writeAction(f"andi {self.scratch[1]} {self.scratch[1]}  {0xFF}")
            ud_mstr_loop_tran.writeAction(f"print '[DEBUG][NWID %ld][{self.task}] Return to node master %ld tid %ld' \
                {'X0'} {self.scratch[0]} {self.scratch[1]}")
        ud_mstr_loop_tran.writeAction(f"mov_imm2reg {self.num_map_gen} 0")
        ud_mstr_loop_tran.writeAction(f"yield")

        # Added by: Jerry Ding
        if self.extension == 'load_balancer':
            # If self._finish_flag is returned, meaning a lane's workers all finished, terminate
            ud_mstr_loop_tran.writeAction(f"lane_finished: subi {num_ln_worker_active} {num_ln_worker_active} {1}")
            ud_mstr_loop_tran = set_ev_label(ud_mstr_loop_tran, self.ev_word, self.ln_mstr_term_ev_label, "X1")
            ud_mstr_loop_tran.writeAction(f"sendr_wcont {self.ev_word} X2 {self.part_array_ptr} {num_part_assigned}")
            ud_mstr_loop_tran.writeAction(f"blei {num_ln_worker_active} {0} ud_finished")
            ud_mstr_loop_tran.writeAction(f"yield")
            # If all lanes' workers all finished, send to node master
            ud_mstr_loop_tran.writeAction(f"ud_finished: movir {self.scratch[0]} {self._finish_flag}")
            ud_mstr_loop_tran.writeAction(f"sendr_wcont {self.saved_cont} X2 {self.scratch[0]} {self.scratch[0]}")
            ud_mstr_loop_tran.writeAction(f"yield")

        if self.debug_flag:
            ud_mstr_term_tran.writeAction(f"print ' '")
            ud_mstr_term_tran.writeAction(f"print '[DEBUG][NWID %ld][{self.task}] Event <{self.ud_mstr_term_ev_label}> ev_word = %lu income_cont = %lu' {'X0'} {'EQT'} {'X1'}")
        ud_mstr_term_tran.writeAction(f"yield_terminate")

        return
    
    def __gen_lane_master(self):

        ln_mstr_init_tran   = self.state.writeTransition("eventCarry", self.state, self.state, self.ln_mstr_init_ev_label)

        ln_mstr_loop_tran   = self.state.writeTransition("eventCarry", self.state, self.state, self.ln_mstr_loop_ev_label)

        ln_mstr_rd_part_tran    = self.state.writeTransition("eventCarry", self.state, self.state, self.ln_mstr_rd_part_ev_label)
        
        ln_mstr_get_ret_tran    = self.state.writeTransition("eventCarry", self.state, self.state, self.ln_mstr_get_ret_ev_label)

        ln_mstr_term_tran   = self.state.writeTransition("eventCarry", self.state, self.state, self.ln_mstr_term_ev_label)

        num_th_active   = "X16"
        max_map_th      = "X17"
        next_iter_evw   = "X20"
        kv_map_evw      = "X21"
        num_map_gen_addr= "X22"
        iter_flag       = "X23"
        iterator        = [f"X{GP_REG_BASE + k + 7}" for k in range(self.in_kvset_iter_size)]
        
        iterator_ops = [f"X{OB_REG_BASE + k}" for k in range(self.in_kvset_iter_size)]

        empty_part_label    = "lane_master_empty_partition"
        pass_end_label      = "lane_master_iterator_pass_end"
        ln_mstr_reach_end_label = "lane_master_reach_end"
        ln_mstr_cont_label      = "lane_master_loop_continue"
        ln_mstr_break_iter_label= "lane_master_break_iterate_loop"

        '''
        Event:      Initialize lane master
        Operands:   X8: Pointer to the base address of the initial partition
                    X9: Number of partitions assigned to this lane x WORD_SIZE
                    X10: nth partition assigned to the lane
        '''
        if self.debug_flag:
            ln_mstr_init_tran.writeAction(f"print ' '")
            ln_mstr_init_tran.writeAction(f"print '[DEBUG][NWID %ld][{self.ln_mstr_init_ev_label}] Event <{self.ln_mstr_init_ev_label}> ev_word = %lu income_cont = %lu' {'X0'} {'EQT'} {'X1'}")
            ln_mstr_init_tran.writeAction(f"print '[DEBUG][NWID %ld][{self.ln_mstr_init_ev_label}] Operands: lane master %ld is assigned with %ld th partition." + 
                                          f" partition_base = %lu(0x%lx) partition_stride = %lu Bytes' {'X0'} {'X0'} {'X10'} {'X8'} {'X8'} {'X9'}")
        ln_mstr_init_tran.writeAction(f"perflog 1 {818} 'Lane master %ld is assigned with %ld th partition. Partition_base = %lu(0x%lx) partition_stride = %lu Bytes' {'X0'} {'X10'} {'X8'} {'X8'} {'X9'}")
        ln_mstr_init_tran.writeAction(f"addi X1 {self.saved_cont} 0")
        ln_mstr_init_tran.writeAction(f"send_dmlm_ld_wret X8 {self.ln_mstr_rd_part_ev_label} {max(2, self.in_kvset_iter_size)} {self.scratch[0]}")
        # Initialize local counter and event words.
        ln_mstr_init_tran.writeAction(f"movir {num_th_active} 0")
        ln_mstr_init_tran.writeAction(f"movir {max_map_th} {self.max_map_th_per_lane}")
        ln_mstr_init_tran.writeAction(f"mov_imm2reg {self.num_map_gen} 0")
        if self.map_ctr_offset >> 15 > 0:
            ln_mstr_init_tran.writeAction(f"movir {num_map_gen_addr} {self.map_ctr_offset}")
            ln_mstr_init_tran.writeAction(f"add {'X7'} {num_map_gen_addr} {num_map_gen_addr}")
        else:
            ln_mstr_init_tran.writeAction(f"addi {'X7'} {num_map_gen_addr} {self.map_ctr_offset}")
        ln_mstr_init_tran.writeAction(f"move {self.num_map_gen} 0({num_map_gen_addr}) 0 8")
        # Save map thread return event word to scratchpad
        set_ev_label(ln_mstr_init_tran, self.scratch[0], self.ln_mstr_loop_ev_label)
        if self.ln_mstr_evw_offset >> 15 > 0:
            ln_mstr_init_tran.writeAction(f"movir {self.scratch[1]} {self.ln_mstr_evw_offset}")
            ln_mstr_init_tran.writeAction(f"add {'X7'} {self.scratch[1]} {self.scratch[1]}")
        else:
            ln_mstr_init_tran.writeAction(f"addi {'X7'} {self.scratch[1]} {self.ln_mstr_evw_offset}")
        ln_mstr_init_tran.writeAction(f"move {self.scratch[0]} {0}({self.scratch[1]}) 0 8")
        set_ev_label(ln_mstr_init_tran, next_iter_evw, self.ln_mstr_get_ret_ev_label)
        set_ev_label(ln_mstr_init_tran, kv_map_evw, self.kv_map_ev_label, new_thread=True)

        # Added by: Jerry Ding
        if self.extension == 'load_balancer':
            num_worker_alive = f"X{GP_REG_BASE + self.in_kvset_iter_size + 7}"
            ln_mstr_init_tran.writeAction(f"movir {num_worker_alive} 0")

        ln_mstr_init_tran.writeAction(f"yield")
        
        '''
        Event:      Read the assigned partition and start iterating on the partition
        Operands:   X8 ~ Xn: Iterator
        '''
        if self.debug_flag:
            ln_mstr_rd_part_tran.writeAction(f"print ' '")
            ln_mstr_rd_part_tran.writeAction(f"print '[DEBUG][NWID %ld][{self.ln_mstr_rd_part_ev_label}] Event <{self.ln_mstr_rd_part_ev_label}> ev_word = %lu return from DRAM addr = %lu(0x%lx)' \
                {'X0'} {'EQT'} {f'X{OB_REG_BASE+self.in_kvset_iter_size}'} {f'X{OB_REG_BASE+self.in_kvset_iter_size}'}")
            ln_mstr_rd_part_tran.writeAction(f"print '[DEBUG][NWID %ld][{self.ln_mstr_rd_part_ev_label}] Operands: iterator = [{''.join(['%lu(0x%lx), ' for _ in range(self.in_kvset_iter_size)])}]' \
                {'X0'} {' '.join([f'{n} {n} ' for n in iterator_ops])}")
        # Start iterating on the assigned partition and set flag
        self.in_kvset.get_next_pair(ln_mstr_rd_part_tran, next_iter_evw, kv_map_evw, self.kv_map_ev_label, iterator_ops, self.scratch, empty_part_label)
        ln_mstr_rd_part_tran.writeAction(f"addi {num_th_active} {num_th_active} 1")
        ln_mstr_rd_part_tran.writeAction(F"movir {iter_flag} {FLAG}")
        # Initialize local counter.
        if self.debug_flag:
            ln_mstr_rd_part_tran.writeAction(f"print '[DEBUG][NWID %ld][{self.ln_mstr_rd_part_ev_label}] Save lane master map return event word = %ld to scratchpad' {'X0'} {self.scratch[0]}")
        ln_mstr_rd_part_tran.writeAction("yield")
        
        # Added by: Jerry Ding
        if self.extension == 'load_balancer':
            loop_ev_word = f"X{GP_REG_BASE + self.in_kvset_iter_size + 8}"
            # If the partition is empty, launch workers
            set_ev_label(ln_mstr_rd_part_tran, self.ev_word, self.ln_worker_work_ev_label, new_thread=True, label = empty_part_label)
            ln_mstr_rd_part_tran.writeAction(f"movir {self.scratch[0]} {self.claim_work_cont_offset}")
            ln_mstr_rd_part_tran.writeAction(f"add {'X7'} {self.scratch[0]} {self.scratch[0]}")
            ln_mstr_rd_part_tran.writeAction(f"movlr 0({self.scratch[0]}) {self.scratch[1]} 0 {WORD_SIZE}")
            ln_mstr_rd_part_tran.writeAction(f"movir {self.scratch[0]} {self._worker_start_flag}")
            ln_mstr_rd_part_tran.writeAction(f"addi X2 {loop_ev_word} {0}")
            ln_mstr_rd_part_tran.writeAction(f"evlb {loop_ev_word} {self.ln_mstr_loop_ev_label}")
            ln_mstr_rd_part_tran.writeAction(f"launch_workers: bgei {num_worker_alive} {self.max_worker_th_per_lane} {'empty_part_ret_to_ud_mstr'}")
            ln_mstr_rd_part_tran.writeAction(f"sendr3_wcont {self.ev_word} X2 {self.scratch[0]} {self.scratch[1]} {loop_ev_word}")
            ln_mstr_rd_part_tran.writeAction(f"addi {num_worker_alive} {num_worker_alive} {1}")
            ln_mstr_rd_part_tran.writeAction(f"jmp launch_workers")

            # return to updown master
            ln_mstr_rd_part_tran.writeAction(f"{'empty_part_ret_to_ud_mstr'}: sendr_wret {self.saved_cont} {self.ln_mstr_init_ev_label} {self.num_map_gen} {self.num_map_gen} {self.scratch[0]}")
        else:
            # If the partition is empty, return to updown master.
            ln_mstr_rd_part_tran.writeAction(f"{empty_part_label}: sendr_wret {self.saved_cont} {self.ln_mstr_init_ev_label} {self.num_map_gen} {self.num_map_gen} {self.scratch[0]}")
        

        if self.debug_flag:
            ln_mstr_rd_part_tran.writeAction(f"rshift {self.saved_cont} {self.scratch[0]} {32}")
            ln_mstr_rd_part_tran.writeAction(f"rshift {'X1'} {self.scratch[1]} {24}")
            ln_mstr_rd_part_tran.writeAction(f"andi {self.scratch[1]} {self.scratch[1]}  {0xFF}")
            ln_mstr_rd_part_tran.writeAction(f"print '[DEBUG][NWID %ld][{self.ln_mstr_rd_part_ev_label}] Lane %ld master receives empty partition, iterator[0] = %lu(0x%lx) iteratior[1] = %lu(0x%lx)." + 
                                             f" Return to updown master %ld tid %ld' {'X0'} {'X0'} {'X8'} {'X8'} {'X9'} {'X9'}  {self.scratch[0]} {self.scratch[1]}")
        ln_mstr_rd_part_tran.writeAction(f"yield")
        
        '''
        Event:      Receive the next key-value pair from the assigned partition
        Operands:   X8 ~ Xn: Updated iterator and key-value pair.
        '''
        if self.debug_flag:
            ln_mstr_get_ret_tran.writeAction(f"print ' '")
            ln_mstr_get_ret_tran.writeAction(f"print '[DEBUG][NWID %ld][{self.ln_mstr_get_ret_ev_label}] Event <{self.ln_mstr_get_ret_ev_label}> ev_word = %lu" + 
                                             f" income_cont = %lu num_thread_active = %ld' {'X0'} {'EQT'} {'X1'} {num_th_active}")
            ln_mstr_get_ret_tran.writeAction(f"print '[DEBUG][NWID %ld][{self.ln_mstr_get_ret_ev_label}] Operands: iterator = [{''.join(['%lu(0x%lx), ' for _ in range(self.in_kvset_iter_size)])}]' \
                {'X0'} {' '.join([f'{n} {n} ' for n in iterator_ops])}")
        # Check if the iterator pass the end of the assigned partition
        self.in_kvset.check_iter(ln_mstr_get_ret_tran, iterator_ops, self.scratch, pass_end_label)
        # Pause iterating if the number of active map threads is greater than the maximum number of map threads
        ln_mstr_get_ret_tran.writeAction(f"bge {num_th_active} {max_map_th} {ln_mstr_break_iter_label}")
        # Get the next key-value pair from the assigned partition
        self.in_kvset.get_next_pair(ln_mstr_get_ret_tran, next_iter_evw, kv_map_evw, self.kv_map_ev_label, iterator_ops, self.scratch, ln_mstr_break_iter_label)
        if self.debug_flag:
            ln_mstr_get_ret_tran.writeAction(f"print '[DEBUG][NWID %ld][{self.ln_mstr_get_ret_ev_label}] Lane %ld master gets next pair, iterator = [{''.join(['%lu(0x%lx), ' for _ in range(self.in_kvset_iter_size)])}]" +
                                                f" %ld map thread remains active.' {'X0'} {'X0'} {' '.join([f'{n} {n} ' for n in iterator_ops])} {num_th_active}")
        ln_mstr_get_ret_tran.writeAction(f"addi {num_th_active} {num_th_active} 1")
        ln_mstr_get_ret_tran.writeAction(f"yield")
        
        # Pause/stop iterating 
        ln_mstr_get_ret_tran.writeAction(f"{ln_mstr_break_iter_label}: movir {iter_flag} 0")
        # Save current position of the iterator
        for k in range(self.in_kvset_iter_size):
            ln_mstr_get_ret_tran.writeAction(f"addi {f'X{OB_REG_BASE+k}'} {iterator[k]} 0")
        if self.debug_flag:
            ln_mstr_get_ret_tran.writeAction(f"print '[DEBUG][NWID %ld][{self.ln_mstr_get_ret_ev_label}] Lane %ld master pause iterate loop, iterator = [{''.join(['%lu(0x%lx), ' for _ in range(self.in_kvset_iter_size)])}]" + 
                                             f" %ld map thread remains active.' {'X0'} {'X0'} {' '.join([f'{n} {n} ' for n in iterator_ops])} {num_th_active}")
        ln_mstr_get_ret_tran.writeAction(f"yield")
        
        # Finish iterate the assigned partition
        ln_mstr_get_ret_tran.writeAction(f"{pass_end_label}: subi {num_th_active} {num_th_active} 1")
        # ln_mstr_get_ret_tran.writeAction(f"movir {iter_flag} 0")
        for k in range(self.in_kvset_iter_size):
            ln_mstr_get_ret_tran.writeAction(f"addi {f'X{OB_REG_BASE+k}'} {iterator[k]} 0")

        if self.debug_flag:
            ln_mstr_get_ret_tran.writeAction(f"print '[DEBUG][NWID %ld][{self.ln_mstr_get_ret_ev_label}] Lane %ld master iterator pass end, iterator = [{''.join(['%lu(0x%lx), ' for _ in range(self.in_kvset_iter_size)])}]," + 
                                             f" %ld map thread remains active, iter_flag=%ld. ' {'X0'} {'X0'} {' '.join([f'{n} {n} ' for n in iterator_ops])} {num_th_active} {iter_flag}")
        ln_mstr_get_ret_tran.writeAction(f"bgti {num_th_active} 0 {ln_mstr_cont_label}")
        ln_mstr_get_ret_tran.writeAction(f"movlr 0({num_map_gen_addr}) {self.num_map_gen} 0 8")
        ln_mstr_get_ret_tran.writeAction(f"sendr_wret {self.saved_cont} {self.ln_mstr_init_ev_label} {self.num_map_gen} {self.num_map_gen} {self.scratch[0]}")
        if self.debug_flag:
            ln_mstr_get_ret_tran.writeAction(f"rshift {self.saved_cont} {self.scratch[0]} {32}")
            ln_mstr_get_ret_tran.writeAction(f"rshift {'X1'} {self.scratch[1]} {24}")
            ln_mstr_get_ret_tran.writeAction(f"andi {self.scratch[1]} {self.scratch[1]} {0xFF}")
            ln_mstr_get_ret_tran.writeAction(f"print '[DEBUG][NWID %ld][{self.ln_mstr_get_ret_ev_label}] Lane %ld master finishes all pairs assigned, return to updown master %ld tid %ld' \
                {'X0'} {'X0'} {self.scratch[0]} {self.scratch[1]}")
        ln_mstr_get_ret_tran.writeAction(f"{ln_mstr_cont_label}: yield")
        
        '''
        Event:      Main lane master loop. When a map thread finishes the assigned key-value pair, it returns to this event.
        Operands:   X8 ~ Xn: Map thread returned values.
        '''
        # Added by: Jerry Ding
        if self.extension == 'load_balancer':
            ln_mstr_loop_tran.writeAction(f"beqi X8 {self._finish_flag} worker_finished")

        if self.debug_flag:
            ln_mstr_loop_tran.writeAction(f"print ' '")
            ln_mstr_loop_tran.writeAction(f"rshift {'X1'} {self.scratch[0]} {24}")
            ln_mstr_loop_tran.writeAction(f"andi {self.scratch[0]} {self.scratch[0]}  {0xFF}")
            ln_mstr_loop_tran.writeAction(f"print '[DEBUG][NWID %ld][{self.ln_mstr_loop_ev_label}] Event <{self.ln_mstr_loop_ev_label}> ev_word = %lu income_cont = %lu num_thread_active = %ld' {'X0'} {'EQT'} {'X1'} {num_th_active}")
            ln_mstr_loop_tran.writeAction(f"print '[DEBUG][NWID %ld][{self.ln_mstr_loop_ev_label}] Lane %ld map thread tid = %ld return ops: X8 = %ld X9 = %ld' \
                {'X0'} {'X0'} {self.scratch[0]} {'X8'} {'X9'}")
        ln_mstr_loop_tran.writeAction(f"subi {num_th_active} {num_th_active} 1")
        # Check if lane master is iterating on the assigned partition
        ln_mstr_loop_tran.writeAction(f"beqi {iter_flag} {FLAG} {ln_mstr_cont_label}")
        # Check if the iterator pass the end of the assigned partition, if not, continue iterating
        self.in_kvset.get_next_pair(ln_mstr_loop_tran, next_iter_evw, kv_map_evw, self.kv_map_ev_label, iterator, self.scratch, ln_mstr_reach_end_label)
        ln_mstr_loop_tran.writeAction(f"addi {num_th_active} {num_th_active} 1")
        ln_mstr_loop_tran.writeAction(f"movir {iter_flag} {FLAG}")
        if self.debug_flag:
            ln_mstr_loop_tran.writeAction(f"print '[DEBUG][NWID %ld][{self.ln_mstr_loop_ev_label}] Lane %ld master restart iterating the assigned partition, iterator = " +
                                            f"[{''.join(['%lu(0x%lx), ' for _ in range(self.in_kvset_iter_size)])}] num_thread_active = %ld' {'X0'} {'X0'} {' '.join([f'{n} {n} ' for n in iterator_ops])} {num_th_active}")
        ln_mstr_loop_tran.writeAction(f"yield")
        if self.debug_flag:
            ln_mstr_loop_tran.writeAction(f"{ln_mstr_reach_end_label}: print '[DEBUG][NWID %ld][{self.ln_mstr_loop_ev_label}] Lane %ld master finishes all pairs assigned. num_thread_active = %ld' {'X0'} {'X0'} {num_th_active}")
            ln_mstr_loop_tran.writeAction(f"bgti {num_th_active} 0 {ln_mstr_cont_label}")
        else:
            ln_mstr_loop_tran.writeAction(f"{ln_mstr_reach_end_label}: bgti {num_th_active} 0 {ln_mstr_cont_label}")
        # Finish issuing all the assigned input kv set, return to the updown master with the number of map tasks generated
        ln_mstr_loop_tran.writeAction(f"movlr 0({num_map_gen_addr}) {self.num_map_gen} 0 8")
        ln_mstr_loop_tran.writeAction(f"sendr_wret {self.saved_cont} {self.ln_mstr_init_ev_label} {self.num_map_gen} {self.num_map_gen} {self.scratch[0]}")
        if self.debug_flag:
            ln_mstr_loop_tran.writeAction(f"rshift {self.saved_cont} {self.scratch[0]} {32}")
            ln_mstr_loop_tran.writeAction(f"rshift {'X1'} {self.scratch[1]} {24}")
            ln_mstr_loop_tran.writeAction(f"andi {self.scratch[1]} {self.scratch[1]}  {0xFF}")
            ln_mstr_loop_tran.writeAction(f"print '[DEBUG][NWID %ld][{self.ln_mstr_loop_ev_label}] Lane %ld master no thread active, return to updown master %ld tid %ld: num_map_generated = %ld. " + 
                                          f"Iterator={''.join(['%lu, ' for _ in range(self.in_kvset_iter_size)])}' {'X0'} {'X0'} {self.scratch[0]} {self.scratch[1]} {self.num_map_gen} {' '.join(iterator)}")
        ln_mstr_loop_tran.writeAction(f"mov_imm2reg {self.num_map_gen} 0")
        ln_mstr_loop_tran.writeAction(f"movrl {self.num_map_gen} 0({num_map_gen_addr}) 0 8")

        # Added by: Jerry Ding
        # If all mappers finished, launch workers if haven't
        if self.extension == 'load_balancer':
            set_ev_label(ln_mstr_loop_tran, self.ev_word, self.ln_worker_work_ev_label, new_thread=True)
            ln_mstr_loop_tran.writeAction(f"movir {self.scratch[0]} {self.claim_work_cont_offset}")
            ln_mstr_loop_tran.writeAction(f"add {'X7'} {self.scratch[0]} {self.scratch[0]}")
            ln_mstr_loop_tran.writeAction(f"movlr 0({self.scratch[0]}) {self.scratch[1]} 0 {WORD_SIZE}")
            ln_mstr_loop_tran.writeAction(f"movir {self.scratch[0]} {self._worker_start_flag}")
            ln_mstr_loop_tran.writeAction(f"launch_workers: bgei {num_worker_alive} {self.max_worker_th_per_lane} {ln_mstr_cont_label}")
            ln_mstr_loop_tran.writeAction(f"sendr3_wcont {self.ev_word} X2 {self.scratch[0]} {self.scratch[1]} X2")
            ln_mstr_loop_tran.writeAction(f"addi {num_worker_alive} {num_worker_alive} {1}")
            ln_mstr_loop_tran.writeAction(f"jmp launch_workers")

        ln_mstr_loop_tran.writeAction(f"{ln_mstr_cont_label}: yield")

        # Added by: Jerry Ding
        if self.extension == 'load_balancer':
            # If self._finish_flag is returned, meaning a worker has finished
            ln_mstr_loop_tran.writeAction(f"worker_finished: subi {num_worker_alive} {num_worker_alive} 1")
            ln_mstr_loop_tran.writeAction(f"beqi {num_worker_alive} 0 lane_finished")
            ln_mstr_loop_tran.writeAction(f"yield")

            # If all worker finished, notify node master
            ln_mstr_loop_tran.writeAction(f"lane_finished: movir {self.scratch[0]} {self._finish_flag}")
            ln_mstr_loop_tran.writeAction(f"sendr_wcont {self.saved_cont} X2 {self.scratch[0]} X0")
            ln_mstr_loop_tran.writeAction(f"yield")

        if self.debug_flag:
            ln_mstr_term_tran.writeAction(f"print ' '")
            ln_mstr_term_tran.writeAction(f"print '[DEBUG][NWID %ld][{self.ln_mstr_term_ev_label}] Event <{self.ln_mstr_term_ev_label}> ev_word = %lu income_cont = %lu' {'X0'} {'EQT'} {'X1'}")
        ln_mstr_term_tran.writeAction(f"perflog 1 {818} 'Lane master %ld finishes all assigned partitions, terminates.' {'X0'}")
        ln_mstr_term_tran.writeAction(f"yield_terminate")

        return
        
    def __gen_map_thread(self):
        
        kv_map_ret_tran = self.state.writeTransition("eventCarry", self.state, self.state, self.kv_map_ret_ev_label)
        
        lm_addr     = 'X16'

        '''
        Event:      Map thread return event
        Operands:
        '''
        # Return to lane master
        if self.debug_flag:
            kv_map_ret_tran.writeAction(f"print ' '")
            kv_map_ret_tran.writeAction(f"rshift {'X2'} {self.scratch[1]} {24}")
            kv_map_ret_tran.writeAction(f"andi {self.scratch[1]} {self.scratch[1]}  {0xFF}")
            kv_map_ret_tran.writeAction(f"print '[DEBUG][NWID %ld][{self.task}] Event <{self.kv_map_ret_ev_label}> ev_word = %lu income_cont = %lu' {'X0'} {'EQT'} {'X1'}")
            kv_map_ret_tran.writeAction(f"print '[DEBUG][NWID %ld][{self.task}] Map thread %ld finishes pair %ld(0x%lx)' {'X0'} {self.scratch[1]} {self.saved_cont} {self.saved_cont}")
        if self.ln_mstr_evw_offset >> 15 > 0:
            kv_map_ret_tran.writeAction(f"movir {lm_addr} {self.ln_mstr_evw_offset}")
            kv_map_ret_tran.writeAction(f"add {'X7'} {lm_addr} {lm_addr}")
        else:
            kv_map_ret_tran.writeAction(f"addi {'X7'} {lm_addr} {self.ln_mstr_evw_offset}")
        kv_map_ret_tran.writeAction(f"move {0}({lm_addr}) {self.scratch[1]} 0 8")
        kv_map_ret_tran.writeAction(f"sendops_wcont {self.scratch[1]} {'X2'} X8 2")
        if self.debug_flag:
            kv_map_ret_tran.writeAction(f"rshift {self.scratch[1]} {self.scratch[1]} {24}")
            kv_map_ret_tran.writeAction(f"andi {self.scratch[1]} {self.scratch[1]}  {0xFF}")
            kv_map_ret_tran.writeAction(f"print '[DEBUG][NWID %ld][{self.task}] Map thread returns operands: X8 = %ld X9 = %ld to lane master tid %ld' \
                {'X0'} {'X8'} {'X9'} {self.scratch[1]}")
        kv_map_ret_tran.writeAction("yieldt")

        return

    def __gen_kv_emit(self):
        
        map_emit_tran    = self.state.writeTransition("eventCarry", self.state, self.state, self.kv_map_emit_ev_label)
        
        reduce_emit_tran = self.state.writeTransition("eventCarry", self.state, self.state, self.kv_reduce_emit_ev_label)
        
        '''
        Event:      Emit intermediate key-value pair from kv_map and shuffle to kv_reduce.
        Operands:   Intermediate key-value pair generated from the kv_map function.
        '''
        if self.enable_intermediate:
            inter_key       = "X8"
            inter_values    = [f"X{OB_REG_BASE + n + 1}" for n in range((self.inter_kvset.value_size))]
            num_lanes_mask  = f"X{GP_REG_BASE+7}"
            dest_nwid       = f"X{GP_REG_BASE+8}"
            metadata_base   = f"X{GP_REG_BASE+9}"
            base_lane       = f"X{GP_REG_BASE+10}"
            
            if self.debug_flag:
                map_emit_tran.writeAction(f"print ' '")
                map_emit_tran.writeAction(f"print '[DEBUG][NWID %ld][{self.task}] Event <{self.kv_map_emit_ev_label}> ev_word = %lu income_cont = %lu' {'X0'} {'EQT'} {'X1'}")
            if self.metadata_offset >> 15 > 0:
                map_emit_tran.writeAction(f"movir {metadata_base} {self.metadata_offset}")
                map_emit_tran.writeAction(f"add {'X7'} {metadata_base} {metadata_base}")
            else:
                map_emit_tran.writeAction(f"addi {'X7'} {metadata_base} {self.metadata_offset}")
            map_emit_tran.writeAction(f"movlr {self.nwid_mask_offset - self.metadata_offset}({metadata_base}) {num_lanes_mask} 0 8")
            map_emit_tran.writeAction(f"movlr {self.base_nwid_offset - self.metadata_offset}({metadata_base}) {base_lane} 0 8")
            self.kv_reduce_loc(map_emit_tran, inter_key, num_lanes_mask, base_lane, dest_nwid)
            if self.debug_flag:
                map_emit_tran.writeAction(f"print '[DEBUG][NWID %ld][{self.task}] map emit intermediate key = %ld values =" + 
                                        f" [{' '.join([ f'%ld' for _ in range((self.inter_kvpair_size) - 1)])}] to lane %ld' {'X0'} {inter_key} {' '.join(inter_values)} {dest_nwid}")

            # Added by: Jerry Ding
            if self.extension == 'load_balancer':
                set_ev_label(map_emit_tran, self.ev_word, self.ln_receiver_receive_kv_ev_label, new_thread = True)
            else:
                set_ev_label(map_emit_tran, self.ev_word, self.kv_reduce_init_ev_label, new_thread = True)
            map_emit_tran.writeAction(f"ev_update_reg_2 {self.ev_word}  {self.ev_word}  {dest_nwid} {dest_nwid} 8")
            map_emit_tran.writeAction(f"sendops_wcont {self.ev_word} EQT {inter_key} {self.inter_kvpair_size}")
            map_emit_tran.writeAction(f"move {self.map_ctr_offset - self.metadata_offset}({metadata_base}) {self.scratch[1]}  0 8")
            map_emit_tran.writeAction(f"addi {self.scratch[1]} {self.scratch[1]} 1")
            map_emit_tran.writeAction(f"move {self.scratch[1]} {self.map_ctr_offset - self.metadata_offset}({metadata_base}) 0 8")
            map_emit_tran.writeAction(f"yield_terminate")
        
        '''
        Event:      Emit output key-value pair from kv_reduce and store to the output key-value set.
        Operands:   Output key-value pair generated from the kv_reduce function.
        '''
        if self.enable_output:
            output_key       = "X8"
            output_values    = [f"X{OB_REG_BASE + n + 1}" for n in range((self.out_kvpair_size) - 1)]
            buffer_addr      = f"X{GP_REG_BASE+0}"
            reduce_emit_tran.writeAction(f"movir {buffer_addr} {self.send_buffer_offset}")
            reduce_emit_tran.writeAction(f"add {buffer_addr} {'X7'} {buffer_addr}")
            self.out_kvset.put_pair(reduce_emit_tran, 'X1', output_key, output_values, buffer_addr, self.scratch)
            reduce_emit_tran.writeAction(f'yieldt')

    def __gen_reduce_thread(self):

        inter_key       = "X8"
        inter_values    = [f"X{OB_REG_BASE + n + 1}" for n in range((self.inter_kvpair_size) - 1)]
        lm_base_reg     = f"X{GP_REG_BASE+4}"
        temp_value      = self.scratch[0]

        kv_reduce_init_tran = self.state.writeTransition("eventCarry", self.state, self.state, self.kv_reduce_init_ev_label)

        kv_reduce_ret_tran  = self.state.writeTransition("eventCarry", self.state, self.state, self.kv_reduce_ret_ev_label)

        max_th_label = "push_back_to_queue"

        '''
        Event:      Reduce thread
        Operands:   X8: Key
                    X9 ~ Xn: Values
        '''
        # Check the thread name space usage
        if self.debug_flag and self.print_level > 2:
            kv_reduce_init_tran.writeAction(f"print ' '")
            kv_reduce_init_tran.writeAction(f"print '[DEBUG][NWID %ld][{self.task}] Event <{self.kv_reduce_init_ev_label}> ev_word = %lu income_cont = %lu' {'X0'} {'EQT'} {'X1'}")
        if self.metadata_offset >> 15 > 0:
            kv_reduce_init_tran.writeAction(f"movir {lm_base_reg} {self.metadata_offset}")
            kv_reduce_init_tran.writeAction(f"add {'X7'} {lm_base_reg} {lm_base_reg}")
        else:
            kv_reduce_init_tran.writeAction(f"addi {'X7'} {lm_base_reg} {self.metadata_offset}")
        kv_reduce_init_tran.writeAction(f"move {self.num_reduce_th_offset - self.metadata_offset}({lm_base_reg}) {temp_value} 0 8")
        kv_reduce_init_tran.writeAction(f"move {self.max_red_th_offset - self.metadata_offset}({lm_base_reg}) {self.scratch[1]} 0 8")
        kv_reduce_init_tran.writeAction(f"bge {temp_value} {self.scratch[1]} {max_th_label}")
        kv_reduce_init_tran.writeAction(f"addi {temp_value} {temp_value} 1")
        kv_reduce_init_tran.writeAction(f"move {temp_value}  {self.num_reduce_th_offset - self.metadata_offset}({lm_base_reg}) 0 8")
        
        # Send the intermediate key-value pair to kv_reduce 
        kv_reduce_init_tran = set_ev_label(kv_reduce_init_tran, self.ev_word, self.kv_reduce_ev_label)
        if self.debug_flag and self.print_level > 2:
            kv_reduce_init_tran.writeAction(f"print '[DEBUG][NWID %ld][{self.task}] Send intermediate key value pair to kv_reduce: key = %ld values = " + 
                                            f"[{' '.join(['%ld' for _ in range(self.inter_kvpair_size - 1)])}]' {'X0'} {inter_key} {' '.join(inter_values)}")
        if self.extension == 'load_balancer':
            kv_reduce_init_tran.writeAction(f"sendops_wcont {self.ev_word} {'X1'} {inter_key} {self.inter_kvpair_size}")
        else:
            kv_reduce_init_tran.writeAction(format_pseudo(f"sendops_wret {self.ev_word} {self.kv_reduce_ret_ev_label} {inter_key} {self.inter_kvpair_size}", \
                self.scratch[0], self.send_temp_reg_flag))
        kv_reduce_init_tran.writeAction(f"yield")

        # Reach maximum parallelism push the intermediate key-value pair to the queue
        kv_reduce_init_tran.writeAction(f"{max_th_label}: ev_update_1 EQT {self.ev_word} {NEW_THREAD_ID} {0b0100}")
        if self.debug_flag and self.print_level > 2:
            kv_reduce_init_tran.writeAction(f"print '[DEBUG][NWID %ld][{self.task}] Lane %ld has %ld reduce thread active, reaches max reduce threads, pushed back to queue.' {'X0'} {'X0'} {temp_value}")
        kv_reduce_init_tran.writeAction(f"sendops_wcont {self.ev_word} X1 {'X8'} {self.inter_kvpair_size}")
        kv_reduce_init_tran.writeAction(f"yield_terminate")

        '''
        Event:      Reduce thread return, update the number of reduce tasks processed and the number of active reduce threads
        Operands:   
        '''
        if self.debug_flag and self.print_level > 2:
            kv_reduce_ret_tran.writeAction(f"print ' '")
            kv_reduce_ret_tran.writeAction(f"print '[DEBUG][NWID %ld][{self.task}] Event <{self.kv_reduce_ret_ev_label}> ev_word = %lu income_cont = %lu' {'X0'} {'EQT'} {'X1'}")
        if self.metadata_offset >> 15 > 0:
            kv_reduce_ret_tran.writeAction(f"movir {lm_base_reg} {self.metadata_offset}")
            kv_reduce_ret_tran.writeAction(f"add {'X7'} {lm_base_reg} {lm_base_reg}")
        else:
            kv_reduce_ret_tran.writeAction(f"addi {'X7'} {lm_base_reg} {self.metadata_offset}")
        # Increment the number of reduce tasks processed
        kv_reduce_ret_tran.writeAction(f"move {self.reduce_ctr_offset - self.metadata_offset}({lm_base_reg}) {temp_value} 0 8")
        kv_reduce_ret_tran.writeAction(f"addi {temp_value} {temp_value} 1")
        kv_reduce_ret_tran.writeAction(f"move {temp_value} {self.reduce_ctr_offset - self.metadata_offset}({lm_base_reg}) 0 8")
        if self.debug_flag and self.print_level > 2:
            kv_reduce_ret_tran.writeAction(f"print '[DEBUG][NWID %ld][{self.task}] Lane %ld processed %ld reduce tasks' {'X0'} {'X0'} {temp_value}")

        # Decrement the number of active reduce threads
        kv_reduce_ret_tran.writeAction(f"move {self.num_reduce_th_offset - self.metadata_offset}({lm_base_reg}) {temp_value} 0 8")
        kv_reduce_ret_tran.writeAction(f"subi {temp_value} {temp_value} 1")
        kv_reduce_ret_tran.writeAction(f"move {temp_value}  {self.num_reduce_th_offset - self.metadata_offset}({lm_base_reg}) 0 8")
        if self.debug_flag and self.print_level > 2:
            kv_reduce_ret_tran.writeAction(f"print '[DEBUG][NWID %ld][{self.task}] Lane %ld has %ld reduce thread remain active' {'X0'} {'X0'} {temp_value}")

        # Added by: Jerry Ding
        if self.extension == 'load_balancer':
            # # If Eventword != Contword: reducer launched from worker
            # # return to contral to worker
            # kv_reduce_ret_tran.writeAction(f"bne X1 X2 return_to_worker")
            kv_reduce_ret_tran.writeAction(f"sendr_reply {self.scratch[0]} {self.scratch[0]} {self.scratch[0]}")

        kv_reduce_ret_tran.writeAction("yield_terminate")

        # # Added by: Jerry Ding
        # if self.extension == 'load_balancer':
        #     kv_reduce_ret_tran.writeAction(f"return_to_worker: sendr_reply {self.scratch[0]} {self.scratch[0]} {self.scratch[0]}")
        #     kv_reduce_ret_tran.writeAction(f"yieldt")

        return

    def __gen_global_sync(self):

        self.ev_word        = f"X{GP_REG_BASE+14}"
        global_sync_offsets = [self.reduce_ctr_offset]
        
        global_sync = GlobalSync(self.state, self.task, self.ev_word, global_sync_offsets, self.scratch, self.debug_flag, self.print_level, self.send_temp_reg_flag)

        '''
        Event:      Initialize global synchronization
        Operands:   X8:   Saved continuation
                    X9:   Number of map tasks generated
        '''
        global_sync.global_sync(continuation='X1', sync_value='X9', num_lanes='X8')

        return
    
    def msr_return(self, tran: EFAProgram.Transition, ret_label: str, temp_reg:str, operands: str = 'EQT EQT', cont_label: str = '', branch_label = '') -> EFAProgram.Transition:
        '''
        Helper function for returning to the UDKVMSR library from the user defined map/reduce function.
        Parameter:
            tran:       current transition
            ret_label:  return event label
            operands:   operands to be sent back to the UDKVMSR library (optional)
            cont_label: continuation event label for UDKVMSR (optional)
        '''
        
        tran = set_ev_label(tran, self.ev_word, ret_label, src_ev='X2', label=branch_label)
        suffix = ""
        if len(operands.split()) == 3:
            suffix = "3"
        elif len(operands.split()) != 2:
            exit("Error: invalid number of operands for msr_return")
        if cont_label:
            tran.writeAction(f"sendr{suffix}_wret {self.ev_word} {cont_label} {operands} {temp_reg}")
        else:
            tran.writeAction(f"sendr{suffix}_wcont {self.ev_word} {'X2'} {operands}")
        return tran

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
        for in_val, old_val, result in zip(in_values, old_values, results):
            tran.writeAction(f"add {in_val} {old_val} {result}")
        if self.debug_flag and self.print_level > 2:
            tran.writeAction(f"print '[DEBUG][NWID %ld][{self.task}] Combine intermediate key = %ld values = " + 
                             f"[{' '.join(['%ld' for _ in range(len(in_values))])}] with values = " + 
                             f"[{' '.join(['%ld' for _ in range(len(old_values))])}]' {'X0'} {key} {' '.join(in_values)} {' '.join(old_values)}")
        return tran

    def kv_reduce_loc(self, tran: EFAProgram.Transition, key: str, num_lanes_mask: str, base_lane: str, dest_id: str):
        '''
        User-defined mapping from a key to a reducer lane (id). Default implementation is a hash.
        Can be overwritten by the user and changed to customized mapping.
        Parameter
            tran:       EFAProgram.Transition (codelet) triggered by the map event
            key:        name of the register/operand buffer entry containing the key
            num_lanes_mask: name of the register reserved for storing the mask to get destination nwid (= num_lanes - 1)
            base_lane:  name of the register reserved for storing the base lane id (i.e. the lane nwid of the first lane for this UDKVMSR instance)
            result:     name of the register reserved for storing the destination lane nwid
        '''
        
        hash_seed = 0
        tran.writeAction(f"movir {dest_id} {hash_seed}")
        tran.writeAction(f"hash {key} {dest_id}")
        if self.extension == 'load_balancer':
            tran.writeAction(f"subi {num_lanes_mask} {num_lanes_mask} {1}")
        tran.writeAction(f"and {dest_id} {num_lanes_mask} {dest_id}")
        tran.writeAction(f"add {dest_id} {base_lane} {dest_id}")
        if self.extension == 'load_balancer':
            tran.writeAction(f"addi {num_lanes_mask} {num_lanes_mask} {1}")
            tran.writeAction(f"addi {dest_id} {dest_id} {1}")

    def __gen_kv_combine_write_through(self):
        '''
        Helper function for atomic operation using scratchpad. First check if the newest value is cached or is being read (not coming back yet).
        If either, the update will be merged locally based on the user-defined merge function. When the data is ready, it will apply the accumulated 
        update(s), stores the data back to DRAM, and frees the hash table entry. If there's a hash conflict, the update will be postponed
        (i.e. append to the end of the event queue) until the event is popped up and the entry is freed.
        '''
        
        combine_tran        = self.state.writeTransition("eventCarry", self.state, self.state, self.kv_combine_ev_label)
        
        combine_get_tran    = self.state.writeTransition("eventCarry", self.state, self.state, self.combine_get_ev_label)
        
        combine_put_ack_tran    = self.state.writeTransition("eventCarry", self.state, self.state, self.combine_put_ack_ev_label)

        key     = 'X8'
        values  = [f'X{n+9}' for n in range(self.cache_entry_size - 1)]

        regs: list  = [f'X{GP_REG_BASE + i}' for i in range(16)]
        key_lm_offset   = regs[0]
        cached_key  = regs[1]
        buffer_addr = regs[2]
        masked_key  = regs[3]
        saved_cont  = regs[4]
        temp_evw    = regs[5]
        cached_values   = [regs[6+i] for i in range(self.cache_entry_size - 1)]
        result_regs     = [regs[6+i+self.cache_entry_size] for i in range(self.cache_entry_size - 1)]
        scratch = [regs[6+i+2*self.cache_entry_size] for i in range(2)]

        tlb_active_hit_label = "tlb_active_hit"
        tlb_hit_label   = "tlb_hit"
        tlb_evict_label = "tlb_evict"
        get_fail_label  = "error"

        '''
        Event:      Check if the scratchpad caches the key-value pair. If so, combine the incoming values with the cached values. If not, retrieve the pair from output key-value set.
        Operands:   X8: Key
                    X9 ~ Xn: Values
        '''
        if self.debug_flag:
            combine_tran.writeAction(f"print ' '")
            combine_tran.writeAction(f"print '[DEBUG][NWID %ld][{self.task}] Event <{self.kv_combine_ev_label}> key = %ld, values =" + 
                                     f" {' '.join(['%ld' for _ in range(self.cache_entry_size - 1)])}' {'X0'} {key} {' '.join(values)}")
        # check if the local scratchpad stores a pending update to the same key or a copy of the newest output kvpair with that key.
        if self.power_of_two_cache_size:
            combine_tran.writeAction(f"andi {key} {masked_key} {self.cache_size - 1}")
        else:
            combine_tran.writeAction(f"movir {scratch[0]} {self.cache_size}")
            combine_tran.writeAction(f"mod {key} {scratch[0]} {masked_key}")
        if self.power_of_two_entry_size:
            combine_tran.writeAction(f"sli {masked_key} {key_lm_offset} {int(log2(self.cache_entry_bsize))}")
        else:
            combine_tran.writeAction(f"muli {masked_key} {key_lm_offset} {self.cache_entry_bsize}")
        combine_tran.writeAction(f"add {'X7'} {key_lm_offset} {key_lm_offset}")
        if self.cache_offset >> 15 > 0:
            combine_tran.writeAction(f"movir {scratch[0]} {self.cache_offset}")
            combine_tran.writeAction(f"add {key_lm_offset} {scratch[0]} {key_lm_offset}")
        else:
            combine_tran.writeAction(f"addi {key_lm_offset} {key_lm_offset} {self.cache_offset}")
        combine_tran.writeAction(f"move {0}({key_lm_offset}) {cached_key} 0 8")
        if self.debug_flag and self.print_level > 2:
            combine_tran.writeAction(f"print '[DEBUG][NWID %ld][{self.task}] Merge incoming key = %ld Cached key = %lu at cache index %ld' {'X0'} {key} {cached_key} {masked_key}")
        combine_tran.writeAction(f"beq {cached_key} {key} {tlb_active_hit_label}")
        combine_tran.writeAction(f"movir {masked_key} {1}")
        combine_tran.writeAction(f"sli {masked_key} {masked_key} {self.INACTIVE_MASK_SHIFT}")
        combine_tran.writeAction(f"add {masked_key} {key} {masked_key}")
        if self.debug_flag and self.print_level > 2:
            combine_tran.writeAction(f"print '[DEBUG][NWID %ld][{self.task}] Masked key = %lu(0x%lx)' {'X0'} {masked_key} {masked_key}")
        combine_tran.writeAction(f"beq {masked_key} {cached_key} {tlb_hit_label}")
        # If not, check if the data cached has been written back. If so, evict the current entry.
        combine_tran.writeAction(f"rshift {cached_key} {scratch[0]} {self.INACTIVE_MASK_SHIFT}")
        combine_tran.writeAction(f"beqi {scratch[0]} 1 {tlb_evict_label}")

        # If all conditions failed, the entry is occupied and cannot be evicted for now, push the event back to the queue.
        if self.debug_flag and self.print_level > 2:
            combine_tran.writeAction(f"sli {cached_key} {scratch[1]} {1}")
            combine_tran.writeAction(f"sri {scratch[1]} {scratch[1]} {1}")
            combine_tran.writeAction(f"print '[DEBUG][NWID %ld][{self.task}] Cache entry occupied by key = %lu, push back to queue key = %ld " + 
                                     f"values = [{' '.join(['%ld' for _ in range(self.cache_entry_size - 1)])}]' {'X0'} {scratch[1]} {key} {' '.join(values)}")
        # combine_tran.writeAction(f"sendops_wcont {'X2'} {'X1'} {key} {self.cache_entry_size}")
        # combine_tran.writeAction(f"yield")
        if self.extension == 'load_balancer':
            set_ev_label(combine_tran, temp_evw, self.kv_combine_ev_label, new_thread=True)
            combine_tran.writeAction(f"sendops_wcont {temp_evw} X1 {key} {self.inter_kvpair_size}")
        else:
            set_ev_label(combine_tran, temp_evw, self.kv_reduce_init_ev_label, new_thread=True)
            combine_tran.writeAction(f"sendops_wcont {temp_evw} X1 {key} {self.inter_kvpair_size}")
            if self.num_reduce_th_offset >> 15 > 0:
                combine_tran.writeAction(f"movir {scratch[1]} {self.num_reduce_th_offset}")
                combine_tran.writeAction(f"add {'X7'} {scratch[1]} {scratch[1]}")
            else:
                combine_tran.writeAction(f"addi {'X7'} {scratch[1]} {self.num_reduce_th_offset}")
            combine_tran.writeAction(f"move {0}({scratch[1]}) {scratch[0]} 0 8")
            combine_tran.writeAction(f"subi {scratch[0]} {scratch[0]} 1")
            combine_tran.writeAction(f"move {scratch[0]}  {0}({scratch[1]}) 0 8")
        combine_tran.writeAction("yield_terminate")

        # Still waiting for the read to the output kv pair on DRAM coming back, merge locally
        combine_tran.writeAction(f"{tlb_active_hit_label}: move {WORD_SIZE}({key_lm_offset}) {cached_values[0]} 1 8")
        for i in range(len(cached_values) - 1):
            combine_tran.writeAction(f"move {WORD_SIZE * (i+1)}({key_lm_offset}) {cached_values[i+1]} 0 8")
        if self.debug_flag and self.print_level > 2:
            combine_tran.writeAction(f"print '[DEBUG][NWID %ld][{self.task}] Cache active hit key = %ld, cached values = [{' '.join(['%ld' for _ in range(self.cache_entry_size - 1)])}]' \
                {'X0'} {key} {' '.join(cached_values)}")
        self.kv_combine_op(combine_tran, key, values, cached_values, result_regs)
        for i in range(self.cache_entry_size - 1):
            combine_tran.writeAction(f"move {result_regs[i]} {WORD_SIZE * i}({key_lm_offset}) 0 8")
            if self.debug_flag and self.print_level > 2:
                combine_tran.writeAction(f"print '[DEBUG][NWID %ld][{self.task}] Store result value[{i}] = %ld' {'X0'} {result_regs[i]}")
        combine_tran.writeAction(f"sendr_wcont {'X1'} {'X2'} {cached_key} {cached_key} ")
        combine_tran.writeAction(f"yield")

        # The output kv pair is cached in the scratchpad, merge and immediate write back the newest value (write through policy)
        combine_tran.writeAction(f"{tlb_hit_label}: move {WORD_SIZE}({key_lm_offset}) {cached_values[0]} 1 8")
        for i in range(len(cached_values) - 1):
            combine_tran.writeAction(f"move {WORD_SIZE * (i+1)}({key_lm_offset}) {cached_values[i+1]} 0 8")
        if self.debug_flag and self.print_level > 2:
            combine_tran.writeAction(f"print '[DEBUG][NWID %ld][{self.task}] Cache hit key = %ld, cached values = [{' '.join(['%ld' for _ in range(self.cache_entry_size - 1)])}]' \
                {'X0'} {key} {' '.join(cached_values)}")
        self.kv_combine_op(combine_tran, key, values, cached_values, result_regs)
        # Store back the updated values to output key value set
        combine_tran = set_ev_label(combine_tran, temp_evw, self.combine_put_ack_ev_label)
        combine_tran.writeAction(f"movir {buffer_addr} {self.send_buffer_offset}")
        combine_tran.writeAction(f"add {buffer_addr} {'X7'} {buffer_addr}")
        if self.debug_flag:
            combine_tran.writeAction(f"print '[DEBUG][NWID %ld][{self.task}] Put output key value pair: key = %ld values = [{' '.join(['%ld' for _ in range(self.cache_entry_size - 1)])}]' \
                {'X0'} {key} {' '.join(result_regs)}")
        self.out_kvset.put_pair(combine_tran, temp_evw, key, result_regs, buffer_addr, scratch)
        for i in range(self.cache_entry_size - 1):
            combine_tran.writeAction(f"move {result_regs[i]} {WORD_SIZE * i}({key_lm_offset}) 0 8")
        combine_tran.writeAction(f"addi {key} {cached_key} 0")
        combine_tran.writeAction(f"addi {'X1'} {saved_cont} 0")
        combine_tran.writeAction("yield")

        # Current entry has been written back, (i.e., can be evicted). Insert the new entry.
        combine_tran.writeAction(f"{tlb_evict_label}: move {key} {0}({key_lm_offset}) 1 8")
        if self.debug_flag and self.print_level > 2:
            combine_tran.writeAction(f"print '[DEBUG][NWID %ld][{self.task}] Cache miss evict old entry %lu. Get pair key = %ld from output key value set' {'X0'} {cached_key} {key}")
        # Retrieve the current value.
        combine_tran = set_ev_label(combine_tran, temp_evw, self.combine_get_ev_label)
        combine_tran = self.out_kvset.get_pair(combine_tran, temp_evw, key, scratch)
        # Store the incoming key-value pair to the cache
        for i in range(self.cache_entry_size - 1):
            combine_tran.writeAction(f"move {values[i]} {WORD_SIZE * i}({key_lm_offset}) 0 8")
        combine_tran.writeAction(f"addi {key} {cached_key} 0")
        combine_tran.writeAction(f"addi {'X1'} {saved_cont} 0")
        combine_tran.writeAction(f"yield")

        '''
        Event:      Get pair returns, merge with cached values.
        Operands:   X8: Key
                    X9 ~ Xn: Values in output kv set
        '''
        # Value is retrieved and ready for merging with the (accumulated) updates
        get_pair_ops = self.out_kvset.get_pair_ops()
        combine_get_tran = self.state.writeTransition("eventCarry", self.state, self.state, self.combine_get_ev_label)
        if self.debug_flag and self.print_level > 2:
            combine_get_tran.writeAction(f"print ' '")
            combine_get_tran.writeAction(f"print '[DEBUG][{self.combine_get_ev_label}] Cached key = %ld return ops = " + 
                                         f"[{' '.join(['%ld, ' for _ in range(len(get_pair_ops))])}]' {cached_key} {' '.join(get_pair_ops)}")
        # Read the accumulated cached value 
        for i in range(len(cached_values)):
            combine_get_tran.writeAction(f"move {WORD_SIZE * i}({key_lm_offset}) {cached_values[i]} 0 8")
        if self.debug_flag and self.print_level > 2:
            combine_get_tran.writeAction(f"print '[DEBUG][{self.combine_get_ev_label}] Cached key = %ld values = [{''.join(['%ld, ' for _ in range(len(cached_values))])}]' \
                {cached_key} {' '.join(cached_values)} ")

        # Check if the get is successful
        self.out_kvset.check_get_pair(combine_get_tran, cached_key, get_pair_ops, get_fail_label)
        
        # Load the cached value
        ld_values = self.out_kvset.get_pair_value_ops()
        if self.debug_flag and self.print_level > 2:
            combine_get_tran.writeAction(f"print '[DEBUG][NWID %ld][{self.combine_get_ev_label}] Get pair success, return values = [{''.join(['%ld, ' for _ in range(len(ld_values))])}]' \
                {'X0'} {' '.join(ld_values)}")
        # Apply the accumulated updates based on user-defined reduce funtion
        self.kv_combine_op(combine_get_tran, cached_key, cached_values, ld_values, result_regs)
        # Store back the updated values to output key value set
        set_ev_label(combine_get_tran, temp_evw, self.combine_put_ack_ev_label)
        combine_get_tran.writeAction(f"movir {buffer_addr} {self.send_buffer_offset}")
        combine_get_tran.writeAction(f"add {buffer_addr} {'X7'} {buffer_addr}")
        if self.debug_flag:
            combine_get_tran.writeAction(f"print '[DEBUG][{self.combine_get_ev_label}] Put output key value pair: key = %ld " + 
                                         f"values = [{' '.join(['%ld, ' for _ in range(self.cache_entry_size - 1)])}]' {cached_key} {' '.join(result_regs)}")
        self.out_kvset.put_pair(combine_get_tran, temp_evw, cached_key, result_regs, buffer_addr, scratch)
        # Store the updated value back to the cache
        for i in range(self.cache_entry_size - 1):
            combine_get_tran.writeAction(f"move {result_regs[i]} {WORD_SIZE * i}({key_lm_offset}) 0 8")
        if self.debug_flag and self.print_level > 2:
            combine_get_tran.writeAction(f"print '[DEBUG][NWID %ld][{self.combine_get_ev_label}] Store masked key = %lu(0x%lx) to addr = 0x%lx' {'X0'} {masked_key} {masked_key} {key_lm_offset}")
        combine_get_tran.writeAction(f"move {masked_key} {0 - WORD_SIZE}({key_lm_offset}) 0 8")    # flip the highest bit indicating the value is written back
        combine_get_tran.writeAction(f"yield")
        
        # Key not exist in output kv set, store the incoming value.
        set_ev_label(combine_get_tran, temp_evw, self.combine_put_ack_ev_label, label=get_fail_label)
        if self.debug_flag:
            combine_get_tran.writeAction(f"print '[DEBUG][NWID %ld][{self.combine_get_ev_label}] Key not exist in output kv set, " + 
                                         f"store the incoming value: key = %ld values = {' '.join(['%ld' for _ in range(len(cached_values))])}' " + 
                                         f"{'X0'} {cached_key} {' '.join(cached_values)}")
        combine_get_tran.writeAction(f"movir {buffer_addr} {self.send_buffer_offset}")
        combine_get_tran.writeAction(f"add {buffer_addr} {'X7'} {buffer_addr}")
        self.out_kvset.put_pair(combine_get_tran, temp_evw, cached_key, cached_values, buffer_addr, scratch)
        if self.debug_flag:
            combine_get_tran.writeAction(f"print '[DEBUG][NWID %ld][{self.combine_get_ev_label}] Put output key value pair: key = %ld values = " + 
                                         f"[{' '.join(['%ld, ' for _ in range(len(cached_values))])}]' {'X0'} {cached_key} {' '.join(cached_values)}")
        if self.debug_flag and self.print_level > 2:
            combine_get_tran.writeAction(f"print '[DEBUG][NWID %ld][{self.combine_get_ev_label}] Store masked key = %lu(0x%lx) to addr = 0x%lx' {'X0'} {masked_key} {masked_key} {key_lm_offset}")
        combine_get_tran.writeAction(f"move {masked_key} {0 - WORD_SIZE}({key_lm_offset}) 0 8")    # flip the highest bit indicating the value is written back
        combine_get_tran.writeAction(f"yield")
        
        '''
        Event:      Put pair ack, return to user passed in continuation.
        Operands:   X8: status
        '''
        put_pair_ops = self.out_kvset.put_pair_ops()
        combine_put_ack_tran = self.state.writeTransition("eventCarry", self.state, self.state, self.combine_put_ack_ev_label)
        if self.debug_flag and self.print_level > 3:
            combine_put_ack_tran.writeAction(f"print ' '")
            combine_put_ack_tran.writeAction(f"print '[DEBUG][NWID %ld][{self.combine_put_ack_ev_label}] Event word = %lu put pair key = %ld return operands = " + 
                                             f"[{''.join(['%lu, ' for _ in range(len(put_pair_ops))])}]' {'X0'} {'EQT'} {cached_key} {' '.join(put_pair_ops)}")
        combine_put_ack_tran.writeAction(f"sendr_wcont {saved_cont} {'X2'} {cached_key} {cached_key} ")
        combine_put_ack_tran.writeAction("yield")

        return

    def __gen_kv_combine(self):
        '''
        Helper function for atomic operation using scratchpad. First check if the newest value is cached or is being read (not coming back yet).
        If either, the update will be merged locally based on the user-defined merge function. When the data is ready, it will apply the accumulated 
        update(s), stores the data back to DRAM, and frees the hash table entry. If there's a hash conflict, the update will be postponed
        (i.e. append to the end of the event queue) until the event is popped up and the entry is freed.
        '''
        
        combine_tran        = self.state.writeTransition("eventCarry", self.state, self.state, self.kv_combine_ev_label)
        
        combine_get_tran    = self.state.writeTransition("eventCarry", self.state, self.state, self.combine_get_ev_label)
        
        combine_put_ack_tran    = self.state.writeTransition("eventCarry", self.state, self.state, self.combine_put_ack_ev_label)
                

        key     = 'X8'
        values  = [f'X{n+9}' for n in range(self.cache_entry_size - 1)]

        regs: list  = [f'X{GP_REG_BASE + i}' for i in range(16)]
        key_offset  = regs[0]
        cached_key  = regs[1]
        buffer_addr = regs[2]
        pending_ack = regs[3]
        saved_cont  = regs[4]
        temp_evw    = regs[5]
        key_mask    = regs[5]
        cached_values   = [regs[6+i] for i in range(self.cache_entry_size - 1)]
        result_regs = [regs[6+i] for i in range(self.cache_entry_size - 1)]
        scratch     = [regs[6+i+self.cache_entry_size] for i in range(2)]

        hit_label   = "cache_hit"
        evict_label = "cache_evict"
        continue_label  = "contiue"
        get_fail_label  = "get_fail"
        skip_flush_label = "skip_flush"

        '''
        Event:      Check if the scratchpad caches the key-value pair. If so, combine the incoming values with the cached values. 
                    If not, evict the entry and retrieve the value from output key-value set .
        Operands:   X8: Key
                    X9 ~ Xn: Values
        '''
        if self.debug_flag:
            combine_tran.writeAction(f"print ' '")
            combine_tran.writeAction(f"print '[DEBUG][NWID %ld][{self.task}] Event <{self.kv_combine_ev_label}> key = %ld, values =" + 
                                     f" {' '.join(['%ld' for _ in range(self.cache_entry_size - 1)])}' {'X0'} {key} {' '.join(values)}")
        # check if the local scratchpad stores a pending update to the same key or a copy of the newest output kvpair with that key.
        # combine_tran.writeAction(f"movir {key_offset} 0")
        # combine_tran.writeAction(f"hash {key} {key_offset}")
        if self.power_of_two_cache_size:
            combine_tran.writeAction(f"andi {key} {key_mask} {self.cache_size - 1}")
        else:
            combine_tran.writeAction(f"movir {key_mask} {self.cache_size}")
            combine_tran.writeAction(f"mod {key} {key_mask} {key_mask}")
        if self.power_of_two_entry_size:
            combine_tran.writeAction(f"sli {key_mask} {key_offset} {int(log2(self.cache_entry_bsize))}")
        else:
            combine_tran.writeAction(f"muli {key_mask} {key_offset} {self.cache_entry_bsize}")
        combine_tran.writeAction(f"add {'X7'} {key_offset} {key_offset}")
        if self.cache_offset >> 15 > 0:
            combine_tran.writeAction(f"movir {scratch[0]} {self.cache_offset}")
            combine_tran.writeAction(f"add {key_offset} {scratch[0]} {key_offset}")
        else:
            combine_tran.writeAction(f"addi {key_offset} {key_offset} {self.cache_offset}")
        combine_tran.writeAction(f"movlr {0}({key_offset}) {cached_key} 0 8")
        if self.debug_flag and self.print_level > 2:
            combine_tran.writeAction(f"print '[DEBUG][NWID %ld][{self.kv_combine_ev_label}] Merge incoming key = %ld Cached key = %lu(0x%lx) at " + 
                                     f"cache addr %lu(0x%lx) offset %ld' {'X0'} {key} {cached_key} {cached_key} {key_offset} {key_offset} {key_mask}")
        combine_tran.writeAction(f"beq {cached_key} {key} {hit_label}")
        combine_tran.writeAction(f"movir {key_mask} {1}")
        combine_tran.writeAction(f"sli {key_mask} {key_mask} {self.INACTIVE_MASK_SHIFT}")
        combine_tran.writeAction(f"or {key_mask} {key} {scratch[1]}")
        if self.debug_flag and self.print_level > 3:
            combine_tran.writeAction(f"print '[DEBUG][NWID %ld][{self.kv_combine_ev_label}] key = %ld masked key = %lu(0x%lx) cached key = %lu(0x%lx)' " + 
                                     f"{'X0'} {key} {scratch[1]} {scratch[1]} {cached_key} {cached_key}")
        combine_tran.writeAction(f"beq {scratch[1]} {cached_key} {hit_label}")
        # If not, check if the data cached has been written back. If so, evict the current entry.
        combine_tran.writeAction(f"rshift {cached_key} {scratch[0]} {self.INACTIVE_MASK_SHIFT}")
        combine_tran.writeAction(f"beqi {scratch[0]} 1 {evict_label}")
        combine_tran.writeAction(f"beqi {cached_key} {-1} {evict_label}")

        # If all conditions failed, the entry is occupied and cannot be evicted for now, push the event back to the queue.
        if self.debug_flag and self.print_level > 2:
            combine_tran.writeAction(f"print '[DEBUG][NWID %ld][{self.kv_combine_ev_label}] Cache entry occupied by key = %lu, push back to queue key = %ld " + 
                                     f"values = [{''.join(['%ld, ' for _ in range(self.cache_entry_size - 1)])}]' {'X0'} {cached_key} {key} {' '.join(values)}")
        # combine_tran.writeAction(f"sendops_wcont {'X2'} {'X1'} {key} {self.cache_entry_size}")
        # combine_tran.writeAction(f"yield")
        if self.extension == 'load_balancer':
            set_ev_label(combine_tran, temp_evw, self.kv_combine_ev_label, new_thread=True)
            combine_tran.writeAction(f"sendops_wcont {temp_evw} X1 {key} {self.inter_kvpair_size}")
        else:
            set_ev_label(combine_tran, temp_evw, self.kv_reduce_init_ev_label, new_thread=True)
            combine_tran.writeAction(f"sendops_wcont {temp_evw} X1 {key} {self.inter_kvpair_size}")
            if self.num_reduce_th_offset >> 15 > 0:
                combine_tran.writeAction(f"movir {scratch[1]} {self.num_reduce_th_offset}")
                combine_tran.writeAction(f"add {'X7'} {scratch[1]} {scratch[1]}")
            else:
                combine_tran.writeAction(f"addi {'X7'} {scratch[1]} {self.num_reduce_th_offset}")
            combine_tran.writeAction(f"move {0}({scratch[1]}) {scratch[0]} 0 8")
            combine_tran.writeAction(f"subi {scratch[0]} {scratch[0]} 1")
            combine_tran.writeAction(f"move {scratch[0]}  {0}({scratch[1]}) 0 8")
        combine_tran.writeAction("yieldt")

        # Still waiting for the read to the output kv pair on DRAM coming back, merge locally
        combine_tran.writeAction(f"{hit_label}: move {WORD_SIZE}({key_offset}) {cached_values[0]} 0 8")
        for i in range(self.cache_entry_size - 2):
            combine_tran.writeAction(f"move {WORD_SIZE * (i+2)}({key_offset}) {cached_values[i+1]} 0 8")
        if self.debug_flag and self.print_level > 2:
            combine_tran.writeAction(f"print '[DEBUG][NWID %ld][{self.kv_combine_ev_label}] Cache hit key = %ld, cached values = " + 
                                     f"[{' '.join(['%ld' for _ in range(self.cache_entry_size - 1)])}]' {'X0'} {key} {' '.join(cached_values)}")
        self.kv_combine_op(combine_tran, key, values, cached_values, result_regs)
        if self.debug_flag and self.print_level > 2:
            combine_tran.writeAction(f"print '[DEBUG][NWID %ld][{self.kv_combine_ev_label}] Store key = %ld combine result values = " + 
                                         f"[{''.join(['%ld, ' for _ in range(len(result_regs))])}] at addr %lu(0x%lx)' {'X0'} {key} {' '.join(result_regs)} {key_offset} {key_offset}")
        for i in range(self.cache_entry_size - 1):
            combine_tran.writeAction(f"movrl {result_regs[i]} {WORD_SIZE * (i+1)}({key_offset}) 0 8")
        if self.debug_flag and self.print_level > 2:
            combine_tran.writeAction(f"print '[DEBUG][NWID %ld][{self.kv_combine_ev_label}] Combine key = %ld, result values = " + 
                                     f"[{' '.join(['%ld' for _ in range(self.cache_entry_size - 1)])}]' {'X0'} {key} {' '.join(result_regs)}")
        combine_tran.writeAction(f"sendr_wcont {'X1'} {'X2'} {key} {cached_key} ")
        combine_tran.writeAction(f"yieldt")  # LB NEEDS MODIFICATION
        
        # Current entry can be evited. Store the dirty entry and insert the new entry.
        combine_tran.writeAction(f"{evict_label}: movrl {key} {0}({key_offset}) 1 8")
        if self.debug_flag and self.print_level > 2:
            combine_tran.writeAction(f"print '[DEBUG][NWID %ld][{self.kv_combine_ev_label}] Cache miss evict old key %lu. Get value for " + 
                                     f"key = %ld from output key value set' {'X0'} {cached_key} {key}")
        combine_tran.writeAction(f"movir {pending_ack} {0}")
        combine_tran.writeAction(f"beqi {cached_key} {self.cache_ival} {skip_flush_label}")
        combine_tran.writeAction(f"sub {cached_key} {key_mask} {cached_key}")
        # Store the evicted key-value pair to output key value set
        if self.debug_flag:
            for i in range(self.cache_entry_size - 1):
                combine_tran.writeAction(f"movlr {WORD_SIZE * i}({key_offset}) {cached_values[i]} 0 8")
            combine_tran.writeAction(f"print '[DEBUG][NWID %ld][{self.kv_combine_ev_label}] Evict cached key = %ld, values = " + 
                                     f"[{' '.join(['%ld' for _ in range(self.cache_entry_size - 1)])}]' {'X0'} {cached_key} {' '.join(cached_values)}")
        combine_tran.writeAction(f"addi {key_offset} {cached_values[0]} 0")
        if (self.send_buffer_offset >> 15) > 0:
            combine_tran.writeAction(f"movir {buffer_addr} {self.send_buffer_offset}")
            combine_tran.writeAction(f"add {'X7'} {buffer_addr} {buffer_addr}")
        else:
            combine_tran.writeAction(f"addi {'X7'} {buffer_addr} {self.send_buffer_offset}")
        set_ev_label(combine_tran, temp_evw, self.combine_put_ack_ev_label)
        self.out_kvset.flush_pair(combine_tran, temp_evw, cached_key, cached_values[0], buffer_addr, pending_ack, scratch)
        # combine_tran.writeAction(f"addi {pending_ack} {pending_ack} 1")
        # Retrieve the current value.
        if self.debug_flag:
            combine_tran.writeAction(f"jmp {continue_label}")
            combine_tran.writeAction(f"{skip_flush_label}: print '[DEBUG][NWID %ld][{self.kv_combine_ev_label}] Invalid cached_key = %ld(0x%lx) skip put pair' {'X0'} {cached_key} {cached_key}")
            set_ev_label(combine_tran, temp_evw, self.combine_get_ev_label, label=continue_label)
        else:
            set_ev_label(combine_tran, temp_evw, self.combine_get_ev_label, label=skip_flush_label)
        # combine_tran.writeAction(f"{skip_flush_label}: evlb {temp_evw} {self.combine_get_ev_label}")
        self.out_kvset.get_pair(combine_tran, temp_evw, key, scratch)
        if self.debug_flag:
            combine_tran.writeAction(f"print '[DEBUG][NWID %ld][{self.kv_combine_ev_label}] Get pair key = %ld from output key value set' {'X0'} {key}")
        # Store the incoming key-value pair to the cache
        for i in range(self.cache_entry_size - 1):
            combine_tran.writeAction(f"move {values[i]} {WORD_SIZE * i}({key_offset}) 0 8")
        combine_tran.writeAction(f"addi {key} {cached_key} 0")
        combine_tran.writeAction(f"addi {'X1'} {saved_cont} 0")
        combine_tran.writeAction(f"addi {pending_ack} {pending_ack} 1")
        combine_tran.writeAction(f"yield")

        '''
        Event:      Get pair returns, merge with cached values.
        Operands:   X8: Key
                    X9 ~ Xn: Values in output kv set
        '''
        # Value is retrieved and ready for merging with the (accumulated) updates
        get_pair_ops = self.out_kvset.get_pair_ops()
        combine_get_tran = self.state.writeTransition("eventCarry", self.state, self.state, self.combine_get_ev_label)
        if self.debug_flag and self.print_level > 3:
            combine_get_tran.writeAction(f"print ' '")
            combine_get_tran.writeAction(f"print '[DEBUG][NWID %ld][{self.combine_get_ev_label}] Event word = %lu Get key = %ld return ops = " + 
                                         f"[{''.join(['%ld, ' for _ in range(len(get_pair_ops))])}]' {'X0'} {'EQT'} {cached_key} {' '.join(get_pair_ops)}")
            
        # Check if the get is successful
        self.out_kvset.check_get_pair(combine_get_tran, cached_key, get_pair_ops, get_fail_label)
        
        # Read the accumulated cached value 
        for i in range(len(cached_values)):
            combine_get_tran.writeAction(f"move {WORD_SIZE * i}({key_offset}) {cached_values[i]} 0 8")
        if self.debug_flag and self.print_level > 2:
            combine_get_tran.writeAction(f"print '[DEBUG][NWID %ld][{self.combine_get_ev_label}] Cached key = %ld values = " + 
                                         f"[{''.join(['%ld, ' for _ in range(len(cached_values))])}]' {'X0'} {cached_key} {' '.join(cached_values)} ")

        # Load the cached value
        ld_values = self.out_kvset.get_pair_value_ops()
        if self.debug_flag and self.print_level > 3:
            combine_get_tran.writeAction(f"print '[DEBUG][NWID %ld][{self.combine_get_ev_label}] Get pair success, return values = " + 
                                         f"[{''.join(['%ld, ' for _ in range(len(ld_values))])}]' {'X0'} {' '.join(ld_values)}")
        # Apply the accumulated updates based on user-defined reduce funtion
        self.kv_combine_op(combine_get_tran, cached_key, cached_values, ld_values, result_regs)
        if self.debug_flag and self.print_level > 2:
            combine_get_tran.writeAction(f"print '[DEBUG][NWID %ld][{self.combine_get_ev_label}] Store key = %ld combine result values = " + 
                                         f"[{''.join(['%ld, ' for _ in range(len(result_regs))])}] at addr %lu(0x%lx)' {'X0'} {cached_key} {' '.join(result_regs)} {key_offset} {key_offset}")
        # Store the updated value back to the cache
        for i in range(self.cache_entry_size - 1):
            combine_get_tran.writeAction(f"move {result_regs[i]} {WORD_SIZE * i}({key_offset}) 0 8")
        # Merged with the loaded value, check for synchronization
        combine_get_tran.writeAction(f"{get_fail_label}: subi {pending_ack} {pending_ack} 1")
        combine_get_tran.writeAction(f"bnei {pending_ack} 0 {continue_label}")
        # Finish combine, return to user passed in continuation.
        combine_get_tran.writeAction(f"movir {key_mask} {1}")
        combine_get_tran.writeAction(f"sli {key_mask} {key_mask} {self.INACTIVE_MASK_SHIFT}")
        combine_get_tran.writeAction(f"or {key_mask} {cached_key} {cached_key}")
        combine_get_tran.writeAction(f"movrl {cached_key} {0 - WORD_SIZE}({key_offset}) 0 8")    # flip the highest bit indicating the value is written back
        if self.debug_flag and self.print_level > 3:
            combine_get_tran.writeAction(f"sli {cached_key} {scratch[0]} {1}")
            combine_get_tran.writeAction(f"sri {scratch[0]} {scratch[0]} {1}")
            combine_get_tran.writeAction(f"print '[DEBUG][NWID %ld][{self.combine_get_ev_label}] Finish write back store key = %ld (masked = %lu) " + 
                                         f"to lm addr = 0x%lx' {'X0'} {cached_key} {scratch[0]} {key_offset}")
        # combine_get_tran.writeAction(f"movir {temp_evw} {-1}")
        # combine_get_tran.writeAction(f"sri {temp_evw} {temp_evw} {1}")
        combine_get_tran.writeAction(f"sendr_wcont {saved_cont} {'X2'} {'X2'} {cached_key} ")
        combine_get_tran.writeAction(f"yieldt")
        combine_get_tran.writeAction(f"{continue_label}: yield")   # LB NEEDS MODIFICATION
        
        '''
        Event:      Put pair ack, return to user passed in continuation.
        Operands:   X8: status
        '''
        put_pair_ops = self.out_kvset.put_pair_ops()
        combine_put_ack_tran = self.state.writeTransition("eventCarry", self.state, self.state, self.combine_put_ack_ev_label)
        if self.debug_flag and self.print_level > 3:
            combine_put_ack_tran.writeAction(f"print ' '")
            combine_put_ack_tran.writeAction(f"print '[DEBUG][NWID %ld][{self.combine_put_ack_ev_label}] Event word = %lu put pair return operands = " + 
                                             f"[{''.join(['%lu, ' for _ in range(len(put_pair_ops))])}]' {'X0'} {'EQT'} {' '.join(put_pair_ops)}")
        combine_put_ack_tran.writeAction(f"subi {pending_ack} {pending_ack} 1")
        combine_put_ack_tran.writeAction(f"bnei {pending_ack} 0 {continue_label}")
        combine_put_ack_tran.writeAction(f"movir {key_mask} {1}")
        combine_put_ack_tran.writeAction(f"sli {key_mask} {key_mask} {self.INACTIVE_MASK_SHIFT}")
        combine_put_ack_tran.writeAction(f"or {key_mask} {cached_key} {cached_key}")
        combine_put_ack_tran.writeAction(f"movrl {cached_key} {0 - WORD_SIZE}({key_offset}) 0 8")    # flip the highest bit indicating the value is written back
        if self.debug_flag and self.print_level > 4:
            combine_put_ack_tran.writeAction(f"sli {cached_key} {scratch[0]} {1}")
            combine_put_ack_tran.writeAction(f"sri {scratch[0]} {scratch[0]} {1}")
            combine_put_ack_tran.writeAction(f"print '[DEBUG][NWID %ld][{self.combine_get_ev_label}] Store masked key = %lu (key = %ld) to addr = 0x%lx' {'X0'} {cached_key} {scratch[0]} {key_offset}")
        # combine_put_ack_tran.writeAction(f"movir {temp_evw} {-1}")
        # combine_put_ack_tran.writeAction(f"sri {temp_evw} {temp_evw} {1}")
        combine_put_ack_tran.writeAction(f"sendr_wcont {saved_cont} {'X2'} {'X2'} {cached_key} ")
        combine_put_ack_tran.writeAction(f"yieldt")
        combine_put_ack_tran.writeAction(f"{continue_label}: yield")

        '''
        ----------------------- Flush the cache to DRAM -----------------------
        '''
        
        ln_flush_tran = self.state.writeTransition("eventCarry", self.state, self.state, self.flush_lane_ev_label)

        flush_ack_tran = self.state.writeTransition("eventCarry", self.state, self.state, self.flush_ack_ev_label)

        cache_bound = regs[0]
        saved_cont  = regs[1] 
        buffer_addr = regs[2]
        counter     = regs[3]
        cache_offset= regs[4]
        temp_key    = regs[5]
        invalid_key = regs[6]
        ack_evw     = regs[7]
        key_mask    = regs[8]
        cached_values   = [regs[9+i] for i in range(self.cache_entry_size - 1)]

        flush_loop_label    = "flush_loop"
        break_label = "break_flush_loop"
        continue_label  = "continue_flush_loop"
        empty_cache_label   = "empty_cache"
        
        '''
        Event:      Flush the lane-private cache to DRAM.
        '''
        if self.debug_flag and self.print_level > 3:
            ln_flush_tran.writeAction(f"print ' '")
            ln_flush_tran.writeAction(f"print '[DEBUG][NWID %ld][{self.flush_lane_ev_label}] Flush the cache at offset {self.cache_offset} to DRAM' {'X0'}")
        ln_flush_tran.writeAction(f"addi {'X1'} {saved_cont} 0")
        if self.cache_offset >> 15 > 0:
            ln_flush_tran.writeAction(f"movir {cache_offset} {self.cache_offset}")
            ln_flush_tran.writeAction(f"add {'X7'} {cache_offset} {cache_offset}")
        else:
            ln_flush_tran.writeAction(f"addi {'X7'} {cache_offset} {self.cache_offset}")
        ln_flush_tran.writeAction(f"movir {cache_bound} {self.cache_size}")
        if self.power_of_two_entry_size:
            ln_flush_tran.writeAction(f"sli {cache_bound} {cache_bound} {int(log2(self.cache_entry_bsize))}")
        else:
            ln_flush_tran.writeAction(f"muli {cache_bound} {cache_bound} {self.cache_entry_bsize}")
        ln_flush_tran.writeAction(f"add {cache_bound} {cache_offset} {cache_bound}")
        if self.debug_flag and self.print_level > 3:
            ln_flush_tran.writeAction(f"print '[DEBUG][NWID %ld][{self.flush_lane_ev_label}] Flush cache from offset = %lu(0x%lx) to offset = %lu(0x%lx) " + 
                                      f"(X7 = %lu(0x%lx))' {'X0'} {cache_offset} {cache_offset} {cache_bound} {cache_bound} {'X7'}")
        # ln_flush_tran.writeAction(f"movir {key_mask} {1}")
        # ln_flush_tran.writeAction(f"sli {key_mask} {key_mask} {self.INACTIVE_MASK_SHIFT}")
        # ln_flush_tran.writeAction(f"subi {key_mask} {key_mask} 1")
        # if self.debug_flag and self.print_level > 2:
        #     ln_flush_tran.writeAction(f"print '[DEBUG][NWID %ld][{self.flush_lane_ev_label}] key mask = %lu(0x%lx)' {'X0'} {key_mask} {key_mask}")
        ln_flush_tran.writeAction(f"movir {counter} {0}")
        ln_flush_tran.writeAction(f"movir {invalid_key} {self.cache_ival}")
        set_ev_label(ln_flush_tran, ack_evw, self.flush_ack_ev_label)
        if (self.send_buffer_offset >> 15) > 0:
            ln_flush_tran.writeAction(f"movir {buffer_addr} {self.send_buffer_offset}")
            ln_flush_tran.writeAction(f"add {'X7'} {buffer_addr} {buffer_addr}")
        else:
            ln_flush_tran.writeAction(f"addi {'X7'} {buffer_addr} {self.send_buffer_offset}")
        ln_flush_tran.writeAction(f"{flush_loop_label}: bge {cache_offset} {cache_bound} {break_label}")
        ln_flush_tran.writeAction(f"movlr {0}({cache_offset}) {temp_key} 0 8")
        ln_flush_tran.writeAction(f"beq {temp_key} {invalid_key} {continue_label}")
        if self.debug_flag:
            ln_flush_tran.writeAction(f"print '[DEBUG][NWID %ld][{self.flush_lane_ev_label}] Flush key = %ld at lm_addr = %lu(0x%lx)' {'X0'} {temp_key} {cache_offset} {cache_offset}")
        ln_flush_tran.writeAction(f"sli {temp_key} {temp_key} 1")
        ln_flush_tran.writeAction(f"sri {temp_key} {temp_key} 1")
        if self.debug_flag and self.print_level > 2:
            for i in range(self.cache_entry_size - 1):
                ln_flush_tran.writeAction(f"movlr {WORD_SIZE * (i+1)}({cache_offset}) {cached_values[i]} 0 8")
            ln_flush_tran.writeAction(f"print '[DEBUG][NWID %ld][{self.flush_lane_ev_label}] Flush key = %lu at lm_addr = %lu(0x%lx), values = " + 
                                     f"[{' '.join(['%ld' for _ in range(self.cache_entry_size - 1)])}]' {'X0'} {temp_key} {cache_offset} {cache_offset} {' '.join(cached_values)}")
        ln_flush_tran.writeAction(f"addi {cache_offset} {cache_offset} {WORD_SIZE}")
        self.out_kvset.flush_pair(ln_flush_tran, ack_evw, temp_key, cache_offset, buffer_addr, counter, scratch)
        # ln_flush_tran.writeAction(f"addi {counter} {counter} 1")
        ln_flush_tran.writeAction(f"jmp {flush_loop_label}")
        ln_flush_tran.writeAction(f"{continue_label}: addi {cache_offset} {cache_offset} {self.cache_entry_bsize}")
        if self.debug_flag and self.print_level > 3:
            ln_flush_tran.writeAction(f"print '[DEBUG][NWID %ld][{self.flush_lane_ev_label}] Invalid key %ld, skip flush' {'X0'} {temp_key}")
        ln_flush_tran.writeAction(f"jmp {flush_loop_label}")
        # Finish sending all the cached key-value pairs.
        ln_flush_tran.writeAction(f"{break_label}: beqi {counter} {0} {empty_cache_label}")
        ln_flush_tran.writeAction(f"yield")
        ln_flush_tran.writeAction(f"{empty_cache_label}: movir {temp_evw} {-1}")
        ln_flush_tran.writeAction(f"sri {temp_evw} {temp_evw} {1}")
        ln_flush_tran.writeAction(f"sendr_wcont {saved_cont} {temp_evw} {'X2'} {cache_bound} ")
        if self.debug_flag and self.print_level > 5:
            ln_flush_tran.writeAction(f"print '[DEBUG][NWID %ld][{self.flush_ack_ev_label}] Flush complete, empty cache, return to continuation %lu' {'X0'} {saved_cont}")
        ln_flush_tran.writeAction(f"yieldt")
        
        '''
        Event:      Flush ack, return to user passed in continuation.
        '''
        flush_ack_tran.writeAction(f"subi {counter} {counter} 1")
        flush_ack_tran.writeAction(f"bnei {counter} 0 {continue_label}")
        flush_ack_tran.writeAction(f"movir {temp_evw} {-1}")
        flush_ack_tran.writeAction(f"sri {temp_evw} {temp_evw} {1}")
        flush_ack_tran.writeAction(f"sendr_wcont {saved_cont} {temp_evw} {'X2'} {cache_bound} ")
        if self.debug_flag and self.print_level > 3:
            flush_ack_tran.writeAction(f"print '[DEBUG][NWID %ld][{self.flush_ack_ev_label}] Flush complete, return to global master %lu' {'X0'} {saved_cont}")
        flush_ack_tran.writeAction(f"yieldt")
        flush_ack_tran.writeAction(f"{continue_label}: yield")
        
        return


    ##############################################################################
    # Following Added by: Jerry Ding

    '''
    Extra global master events for load balancer
    '''
    def __gen_global_master_lb_events(self):
        
        glb_mstr_claim_work_tran = self.state.writeTransition("eventCarry", self.state, self.state, self.glb_mstr_claim_work_ev_label)
        push_key_tran = self.state.writeTransition("eventCarry", self.state, self.state, self.glb_mstr_push_key_ev_label)
        push_key_ret_tran = self.state.writeTransition("eventCarry", self.state, self.state, self.glb_mstr_push_key_ret_ev_label)

        self.__gen_global_master_claim_work(glb_mstr_claim_work_tran)
        self.__gen_blobal_master_push_key(push_key_tran)
        self.__gen_global_master_push_key_ret(push_key_ret_tran)

    def __gen_global_master_claim_work(self, tran):
        '''
        Event: master_global_claim_work
            Returning from map thread. Call get_n_pair and return a kv_pair
            If input kv_pairs left, return to map thread, map event; else return to reduce event
        X1: worker event on the map thread
        '''
        temp_lm_ptr         = f"X{GP_REG_BASE+4}"
        num_node_active     = f"X{GP_REG_BASE+5}"
        num_partitions  = f"X{GP_REG_BASE+8}"

        # Check if map partition is claimed
        tran.writeAction(f"bgt {self.num_part_issued} {num_partitions} {'claim_reduce_task'}")
        # Calculate pointer to first partition
        # Send back to worker
        # X8  in    self.scratch[1]:    self._map_flag
        # X9  in    self.scratch[0]:    partition pointer
        # tran.writeAction(f"mul {self.part_array_stride} {self.num_part_issued} {self.scratch[0]}")
        tran.writeAction(f"sli {self.num_part_issued} {self.scratch[0]} {LOG2_WORD_SIZE + self.log2_in_kvset_iter_size}")
        tran.writeAction(f"sub {self.part_array_ptr} {self.scratch[0]} {self.scratch[0]}")
        tran.writeAction(f"movir {self.scratch[1]} {self._map_flag}")
        tran.writeAction(f"sendr_wcont X1 X2 {self.scratch[1]} {self.scratch[0]}")
        tran.writeAction(f"addi {self.num_part_issued} {self.num_part_issued} {1}")
        tran.writeAction(f"yield")

        # claim key for reducer
        tran.writeAction(f"claim_reduce_task: movir {temp_lm_ptr} {self.inter_queue_metadata_offset}")
        tran.writeAction(f"add {'X7'} {temp_lm_ptr} {temp_lm_ptr}")
        tran.writeAction(f"movlr 0({temp_lm_ptr}) {self.scratch[0]} 0 {WORD_SIZE}")
        tran.writeAction(f"movlr {WORD_SIZE}({temp_lm_ptr}) {self.scratch[1]} 0 {WORD_SIZE}")
        tran.writeAction(f"beq {self.scratch[0]} {self.scratch[1]} queue_empty") # check intermediate key-value count

        # Send back to worker
        # X8  in    self.scratch[1]:    self._reduce_flag
        # X9  in    self.scratch[0]:    intermediate key queue start
        # X10 in    self.ev_word:       intermediate kv dict start
        tran.writeAction(f"movir {self.scratch[1]} {self._reduce_flag}")
        tran.writeAction(f"movir {temp_lm_ptr} {self.inter_dict_metadata_offset}")
        tran.writeAction(f"add {'X7'} {temp_lm_ptr} {temp_lm_ptr}")
        tran.writeAction(f"movlr 0({temp_lm_ptr}) {self.ev_word} 0 {WORD_SIZE}")

        tran.writeAction(f"sendr3_wcont X1 X2 {self.scratch[1]} {self.scratch[0]} {self.ev_word}")
        # Update inter_dict start
        tran.writeAction(f"addi {self.ev_word} {self.ev_word} {self.inter_dict_entry_size*WORD_SIZE}")
        tran.writeAction(f"movrl {self.ev_word} 0({temp_lm_ptr}) 0 {WORD_SIZE}")
        # Update intermediate key queue start
        tran.writeAction(f"movir {temp_lm_ptr} {self.inter_queue_metadata_offset}")
        tran.writeAction(f"add {'X7'} {temp_lm_ptr} {temp_lm_ptr}")
        tran.writeAction(f"addi {self.scratch[0]} {self.scratch[0]} {WORD_SIZE}")
        tran.writeAction(f"movrl {self.scratch[0]} 0({temp_lm_ptr}) 0 {WORD_SIZE}")
        

        # # Read intermediate kv entry from inter_dict start and return to worker
        # tran.writeAction(f"movir {temp_lm_ptr} {self.inter_dict_metadata_offset}")
        # tran.writeAction(f"add {'X7'} {temp_lm_ptr} {temp_lm_ptr}")
        # tran.writeAction(f"movlr 0({temp_lm_ptr}) {self.scratch[0]} 0 {WORD_SIZE}")
        # tran.writeAction(f"evi {'X1'} {self.ev_word} {self.ln_worker_fetched_kv_ptr_ev_label} {1}")
        # tran.writeAction(f"send_dmlm_ld {self.scratch[0]} {self.ev_word} {self.inter_dict_entry_size}")
        # # Update inter_dict start
        # tran.writeAction(f"addi {self.scratch[0]} {self.scratch[0]} {self.inter_dict_entry_size*WORD_SIZE}")
        # tran.writeAction(f"movrl {self.scratch[0]} 0({temp_lm_ptr}) 0 {WORD_SIZE}")

        tran.writeAction(f"yield")

        # If queue is empty but not all map tasks finished yet
        # Spin lock
        tran.writeAction(f"queue_empty: blei {num_node_active} {0} reduce_finished")
        tran.writeAction(f"sendr_wcont X2 X1 X8 X9")
        tran.writeAction(f"yield")

        # All intermediate kv pairs claimed, sending finish flag back
        tran.writeAction(f"reduce_finished: movir {self.scratch[0]} {self._finish_flag}")
        tran.writeAction(f"sendr_reply {self.scratch[0]} {self.scratch[0]} {self.scratch[1]}")
        tran.writeAction(f"yield")

        return

    def __gen_blobal_master_push_key(self, tran):
        '''
        Event:      returned from worker_receive_kv, push returned key into global queue
        Operands:   X8: key
        '''

        temp_lm_ptr         = f"X{GP_REG_BASE+4}"

        # tran.writeAction(f"print '        key %u pushed' X8")

        # Write key to intermediate key queue end
        tran.writeAction(f"movir {temp_lm_ptr} {self.inter_queue_metadata_offset}")
        tran.writeAction(f"add {'X7'} {temp_lm_ptr} {temp_lm_ptr}")
        tran.writeAction(f"movlr {WORD_SIZE}({temp_lm_ptr}) {self.scratch[0]} 0 {WORD_SIZE}")
        tran.writeAction(f"evii {self.ev_word} {self.glb_mstr_push_key_ret_ev_label} 255 5")
        tran.writeAction(f"movir {self.scratch[1]} {self.send_buffer_offset}")
        tran.writeAction(f"add {'X7'} {self.scratch[1]} {self.scratch[1]}")
        tran.writeAction(f"movrl X8 0({self.scratch[1]}) 0 {WORD_SIZE}")
        tran.writeAction(f"send_dmlm {self.scratch[0]} {self.ev_word} {self.scratch[1]} 1")

        # Update intermediate key queue end
        tran.writeAction(f"addi {self.scratch[0]} {self.scratch[0]} {WORD_SIZE}")
        tran.writeAction(f"movrl {self.scratch[0]} {WORD_SIZE}({temp_lm_ptr}) 0 {WORD_SIZE}")

        # Send intermediate key value dict end back to lane pushing key
        tran.writeAction(f"movir {temp_lm_ptr} {self.inter_dict_metadata_offset}")
        tran.writeAction(f"add {'X7'} {temp_lm_ptr} {temp_lm_ptr}")
        tran.writeAction(f"movlr {WORD_SIZE}({temp_lm_ptr}) {self.scratch[0]} 0 {WORD_SIZE}")
        tran.writeAction(f"sendr_reply {'X8'} {self.scratch[0]} {self.scratch[1]}")

        if self.debug_flag:
            tran.writeAction(f"print '[LB_DEBUG] GM sending key %d and inter_dict entry at %lu to Lane %d receiver' X8 {self.scratch[0]} X0")

        # Update intermediate key value dict end
        tran.writeAction(f"addi {self.scratch[0]} {self.scratch[0]} {self.inter_dict_entry_size*WORD_SIZE}")
        tran.writeAction(f"movrl {self.scratch[0]} {WORD_SIZE}({temp_lm_ptr}) 0 {WORD_SIZE}")

        tran.writeAction(f"yield")



        return

    def __gen_global_master_push_key_ret(self,tran):
        tran.writeAction(f"yieldt")
        return


    '''
    Worker thread
    '''
    def __gen_worker(self):

        ln_worker_work_tran = self.state.writeTransition("eventCarry", self.state, self.state, self.ln_worker_work_ev_label)
        ln_worker_fetched_key_tran = self.state.writeTransition("eventCarry", self.state, self.state, self.ln_worker_fetched_key_ev_label)
        ln_worker_fetched_kv_ptr_tran = self.state.writeTransition("eventCarry", self.state, self.state, self.ln_worker_fetched_kv_ptr_ev_label)
        ln_worker_launch_reducer_tran = self.state.writeTransition("eventCarry", self.state, self.state, self.ln_worker_launch_reducer_ev_label)
        ln_worker_reducer_ret_tran = self.state.writeTransition("eventCarry", self.state, self.state, self.ln_worker_reducer_ret_ev_label)
        ln_worker_helper_tran = self.state.writeTransition("eventCarry", self.state, self.state, self.ln_worker_helper_ev_label)

        self.__gen_worker_work(ln_worker_work_tran)
        self.__gen_worker_fetched_key(ln_worker_fetched_key_tran)
        self.__gen_worker_fetched_kv_ptr(ln_worker_fetched_kv_ptr_tran)
        self.__gen_worker_launch_reducer(ln_worker_launch_reducer_tran)
        self.__gen_worker_reducer_ret(ln_worker_reducer_ret_tran)
        self.__gen_worker_helper(ln_worker_helper_tran)

        return

    def __gen_worker_work(self, tran):

        '''
        Event: worker event after mapper is finished
        Operands:   if returned from lane_master_loop
                        X8:   self._worker_start_flag  checking flag for the first time this event is envoked
                        X9:   event word of the claim work event
                        X10:   event word of lane master loop

                    if returned from claim work
                        X8:   if == self._finish_flag, no keys left in the dram
                                else, self._reduce_flag
                        X9:   ptr to key in dram
                        X10:  ptr to kv_dict entry in dram

                        X8:   if == self._map_flag
                        X9:   ptr to partition

                    if returned from fetched_kv_pair
                        X8:   self._worker_claim_key_flag, jump to claim_work
        '''

        kv_count = "UDPR_1"                         # UDPR_1                            thread reg
        cur_kv_count = "UDPR_2"                     # UDPR_2                            thread reg
        intermediate_ptr = "UDPR_3"                 # UDPR_3                            thread reg
        reduce_left_count = "UDPR_4"                # UDPR_4                            thread reg
        claiming_work = "UDPR_5"                    # UDPR_5                            thread reg
        kv_received_count = "UDPR_10"               # UDPR_10                           thread reg
        claim_work_cont = "UDPR_11"                 # UDPR_11                           thread reg
        saved_cont = self.saved_cont                # UDPR_15                           thread reg

        scratch = self.scratch                      # UDPR_12, UDPR_13                  local reg
        ev_word = self.ev_word                      # UDPR_14                           local reg


        # If X8 == self._worker_start_flag
        # First time this event is launched
        tran.writeAction(f"movir {scratch[0]} {self._worker_start_flag}")
        tran.writeAction(f"bne X8 {scratch[0]} after_set_claim_work_cont")
        tran.writeAction(f"addi X10 {saved_cont} 0")
        tran.writeAction(f"addi X9 {claim_work_cont} 0")
        tran.writeAction(f"movir {reduce_left_count} 0")
        tran.writeAction(f"movir {claiming_work} 0")
        tran.writeAction(f"jmp claim_work")

        # If not the first time, keep checking X8
        tran.writeAction(f"after_set_claim_work_cont: beqi X8 {self._finish_flag} reduce_finished")
        tran.writeAction(f"movir {scratch[0]} {self._worker_claim_key_flag} ")
        tran.writeAction(f"beq X8 {scratch[0]} claim_work")
        # If X8 == either self._map_flag or self._reduce_flag
        # Event returned from global claimed work
        # Set claiming_work bit to 0
        tran.writeAction(f"movir {claiming_work} 0")
        tran.writeAction(f"beqi X8 {self._map_flag} claimed_map_task")
        tran.writeAction(f"beqi X8 {self._reduce_flag} claimed_reduce_task")
        # If X8 not in [self._worker_start_flag, self._worker_claim_key_flag, self._finish_flag, self._map_flag, self._reduce_flag]
        # Something's wrong, yieldt
        tran.writeAction(f"print '[LB_ERROR] Wrong flag %llu sent to worker at lane %d, Cont Word %llu, terminating' {'X8'} {'X0'} {'X1'}")
        tran.writeAction(f"yieldt")

        # If X8 == self._map_flag
        # X9 = pointer to claimed partition
        # Launch mapper control
        tran.writeAction(f"claimed_map_task: evii {ev_word} {self.ln_mapper_control_init_ev_label} {255} {5}")
        tran.writeAction(f"sendr_wcont {ev_word} {'X2'} {'X9'} {scratch[0]}")
        tran.writeAction(f"yield")

        # If X8 = self._reduce_flag
        # X9 = ptr to key in dram
        # X10= ptr to kv_dict entry in dram
        # Fetch the key and send it to worker_fetched_key

        tran.writeAction(f"claimed_reduce_task: addi {'X7'} {scratch[1]} {0}")
        tran.writeAction(f"movrl X9 {self.claimed_key_ptr_offset}({scratch[1]}) 0 {WORD_SIZE}")
        tran.writeAction(f"send_dmlm_ld_wret X9 {self.ln_worker_fetched_key_ev_label} {1} {scratch[0]}")
        # Fetch the kv entry and send it to worker_fetched_kv_ptr
        tran.writeAction(f"send_dmlm_ld_wret X10 {self.ln_worker_fetched_kv_ptr_ev_label} {self.inter_dict_entry_size} {scratch[0]}")
        
        tran.writeAction(f"yield")


        # If X8 == self._worker_start_flag or self._worker_claim_key_flag
        # Either first time or returned from global claim work
        # If not currently claiming work, call claim work, set assert_claimed_key_flag = 0 and claiming_work = 1
        tran.writeAction(f"claim_work: beqi {claiming_work} 1 claiming_work")
        tran.writeAction(f"sendr_wcont {claim_work_cont} X2 {scratch[0]} {scratch[0]}")
        tran.writeAction(f"movir {claiming_work} 1")
        tran.writeAction(f"movir {scratch[0]} 0")
        tran.writeAction(f"addi {'X7'} {scratch[1]} {0}")
        tran.writeAction(f"movrl {scratch[0]} {self.assert_claimed_key_offset}({scratch[1]}) 0 {WORD_SIZE}")

        tran.writeAction(f"movir {cur_kv_count} 0")
        tran.writeAction(f"movir {kv_received_count} {0}")

        tran.writeAction(f"claiming_work: yield")

        # If X8 == self._finished_flag
        # Returned from global claim work but all intermediate kv are resolved
        # Entering terminating sequence
        # Check if all left reduce tasks have finished
        # If not, spin lock
        tran.writeAction(f"reduce_finished: bgti {reduce_left_count} 0 reduce_not_all_finished")
        # If not all received kv resolved, spin lock
        tran.writeAction(f"movir {scratch[1]} {self.unresolved_kv_count_offset}")
        tran.writeAction(f"add {'X7'} {scratch[1]} {scratch[1]}")
        tran.writeAction(f"movlr 0({scratch[1]}) {scratch[0]} 0 {WORD_SIZE}")
        tran.writeAction(f"bgti {scratch[0]} 0 kv_not_all_resolved")
        tran.writeAction(f"sendr_wcont {saved_cont} X2 X8 X8")
        tran.writeAction(f"yieldt")

        tran.writeAction(f"reduce_not_all_finished: sendr_wcont X2 X1 X8 X9")
        tran.writeAction(f"yield")

        tran.writeAction(f"kv_not_all_resolved: sendr_wcont X2 X1 X8 X9")
        if self.debug_flag:
            tran.writeAction(f"print 'Remaining unresolved_kv_count %d' {scratch[0]}")
        tran.writeAction(f"yield")

        return

    def __gen_worker_fetched_key(self, tran):
        '''
        Event:      return from dram request sent by worker_work
        Operands:   X8:   claimed key
        '''
    
        kv_count = "UDPR_1"                         # UDPR_1                            thread reg
        cur_kv_count = "UDPR_2"                     # UDPR_2                            thread reg
        intermediate_ptr = "UDPR_3"                 # UDPR_3                            thread reg
        reduce_left_count = "UDPR_4"                # UDPR_4                            thread reg
        claiming_work = "UDPR_5"                    # UDPR_5                            thread reg
        kv_received_count = "UDPR_10"               # UDPR_10                           thread reg
        claim_work_cont = "UDPR_11"                 # UDPR_11                           thread reg
        saved_cont = self.saved_cont                # UDPR_15                           thread reg

        metadata_offset = "UDPR_6"                  # UDPR_6                            local reg
        dest_nwid = "UDPR_7"                        # UDPR_7                            local reg
        metadata_base = "UDPR_8"                    # UDPR_8                            local reg
        cont_word = "UDPR_9"                        # UDPR_9                            local reg
        scratch = self.scratch                      # UDPR_12, UDPR_13                  local reg
        ev_word = self.ev_word                      # UDPR_14                           local reg

        if self.debug_flag:
            tran.writeAction(f"print '        key %u claimed by lane %u' X8 X0")

        # # Send dram request to read intermediate kv
        # tran.writeAction(f"movir {scratch[0]} {self.intermediate_ptr_offset}")
        # tran.writeAction(f"add {'X7'} {scratch[0]} {scratch[1]}")
        # tran.writeAction(f"movlr 0({scratch[1]}) {intermediate_ptr} 0 {WORD_SIZE}")

        # tran.writeAction(f"muli X8 {scratch[0]} {2*WORD_SIZE}")
        # tran.writeAction(f"add {intermediate_ptr} {scratch[0]} {intermediate_ptr}")
        # tran.writeAction(f"send_dmlm_ld_wret {intermediate_ptr} {self.ln_worker_fetched_kv_ptr_ev_label} {2} {scratch[0]}")

        # Send message to static hashed lane indicating this thread has claimed the key
        tran.writeAction(f"movir {metadata_base} {self.metadata_offset}")
        tran.writeAction(f"add {'X7'} {metadata_base} {metadata_base}")
        tran.writeAction(f"movlr {self.nwid_mask_offset - self.metadata_offset}({metadata_base}) {scratch[0]} 0 8")
        tran.writeAction(f"movlr {self.base_nwid_offset - self.metadata_offset}({metadata_base}) {scratch[1]} 0 8")
        self.kv_reduce_loc(tran, "X8", scratch[0], scratch[1], dest_nwid)
        tran.writeAction(f"evii {ev_word} {self.ln_receiver_update_claimed_key_ev_label} 255 5")
        tran.writeAction(f"ev {ev_word}  {ev_word} {dest_nwid} {dest_nwid} 8")
        tran.writeAction(f"evii {cont_word} {self.ln_receiver_assert_claimed_key_ev_label} 255 5")
        tran.writeAction(f"evi X2 {scratch[0]} {self.kv_reduce_init_ev_label} 1")
        tran.writeAction(f"sendr_wcont {ev_word} {cont_word} X8 {scratch[0]}")

        tran.writeAction(f"yield")

        return

    def __gen_worker_fetched_kv_ptr(self, tran):
        '''
        Event:      Three returned situation
                    1)  returned from dram read request sent by fetched_key / this event
                        X8: Count of kv pairs
                        X9: Dram Pointer to kv array
                        X10: Dram Pointer to the entry [X8, X9]
                    2)  returned from spin lock of this event, 
                        waiting for asserting claimed_key from static hashed lane
                        X8: self._worker_claim_key_flag
        '''

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
        tran.writeAction(f"movir {scratch[0]} {self._worker_spin_lock_flag}")
        tran.writeAction(f"beq X8 {scratch[0]} claimed_kv_resolved")

        # If return from dram read request
        # Update the materialized count and cache pointer to the entry
        if self.debug_flag:
            tran.writeAction(f"print 'intermediate kv pointer fetched with number %u and address %lu(0x%lx)' X8 X9 X9")
        tran.writeAction(f"addi X8 {kv_count} 0")
        tran.writeAction(f"addi X10 {intermediate_ptr} 0")

        # cur_kv_count == number of dram request has been sent to read kvs
        # kv_count == updated count of materialized kvs
        # If cur_kv_count != kv_count, then there are materialized kvs need to be read, start resolving
        # Else, the materialized count read from dram is all resolved
        # check assert_claimed_key bit
        tran.writeAction(f"resolving_kv: beq {cur_kv_count} {kv_count} claimed_kv_resolved")
        tran.writeAction(f"muli {cur_kv_count} {scratch[1]} {self.inter_kvpair_size * WORD_SIZE}")
        tran.writeAction(f"add X9 {scratch[1]} {scratch[1]}")
        tran.writeAction(f"send_dmlm_ld_wret {scratch[1]} {self.ln_worker_launch_reducer_ev_label} {self.inter_kvpair_size} {scratch[0]}")
        # tran.writeAction(f"send_dmlm_ld_wret {scratch[1]} {self.ln_worker_helper_ev_label} {self.inter_kvpair_size} {scratch[0]}")
        tran.writeAction(f"addi {scratch[1]} {scratch[1]} {self.inter_kvpair_size * WORD_SIZE}")
        tran.writeAction(f"addi {reduce_left_count} {reduce_left_count} 1")
        tran.writeAction(f"addi {cur_kv_count} {cur_kv_count} 1")
        tran.writeAction(f"jmp resolving_kv")

        # The materialized count read from dram is all resolved
        # Check assert_claimed_key bit
        tran.writeAction(f"claimed_kv_resolved: movir {scratch[1]} {self.assert_claimed_key_offset}")
        tran.writeAction(f"add {'X7'} {scratch[1]} {scratch[1]}")
        tran.writeAction(f"movlr 0({scratch[1]}) {scratch[0]} 0 {WORD_SIZE}")
        tran.writeAction(f"beqi {scratch[0]} 1 asserted_claimed_key")
        tran.writeAction(f"beqi {scratch[0]} 2 updated_kv_count")
        tran.writeAction(f"movir {scratch[0]} {self._worker_spin_lock_flag}")
        tran.writeAction(f"sendr_wcont X2 X1 {scratch[0]} {scratch[0]}")
        tran.writeAction(f"yield")

        # If assert_claimed_key bit == 1
        # Meaning the assertation message from static hashed lane has come back
        # Read the most current materialized count from dram
        # And set assert_claimed_key bit to 2
        tran.writeAction(f"asserted_claimed_key: send_dmlm_ld {intermediate_ptr} X2 {2}")
        tran.writeAction(f"movir {scratch[0]} 2")
        tran.writeAction(f"movir {scratch[1]} {self.assert_claimed_key_offset}")
        tran.writeAction(f"add {'X7'} {scratch[1]} {scratch[1]}")
        tran.writeAction(f"movrl {scratch[0]} 0({scratch[1]}) 0 {WORD_SIZE}")
        tran.writeAction(f"yield")

        # If assert_claimed_key bit == 2
        # Meaning all materialized kvs are resolved
        # If all reducers finished, Send message to worker_work to claim work
        
        tran.writeAction(f"updated_kv_count: movir {scratch[0]} 3")
        tran.writeAction(f"movir {scratch[1]} {self.assert_claimed_key_offset}")
        tran.writeAction(f"add {'X7'} {scratch[1]} {scratch[1]}")
        tran.writeAction(f"movrl {scratch[0]} 0({scratch[1]}) 0 {WORD_SIZE}")

        tran.writeAction(f"bgti {reduce_left_count} 0 waiting_for_reducers")
        tran.writeAction(f"addi X2 {ev_word} 0")
        tran.writeAction(f"evlb {ev_word} {self.ln_worker_work_ev_label}")
        tran.writeAction(f"movir {scratch[0]} {self._worker_claim_key_flag}")
        tran.writeAction(f"sendr_wcont {ev_word} X2 {scratch[0]} {scratch[0]}")

        tran.writeAction(f"waiting_for_reducers: yield")

    def __gen_worker_launch_reducer(self, tran):
        '''
        Event:  returned from dram request sent from worker_fetched_kv_ptr
                to launch reducer 
        Operands:   X8      Key
                    X9~n    Values
        '''
        inter_key       = "X8"
        inter_values    = [f"X{OB_REG_BASE + n + 1}" for n in range((self.inter_kvpair_size) - 1)]

        kv_count = "UDPR_1"                         # UDPR_1                            thread reg
        cur_kv_count = "UDPR_2"                     # UDPR_2                            thread reg
        intermediate_ptr = "UDPR_3"                 # UDPR_3                            thread reg
        reduce_left_count = "UDPR_4"                # UDPR_4                            thread reg
        claiming_work = "UDPR_5"                    # UDPR_5                            thread reg
        claim_work_cont = "UDPR_11"                 #                                   thread reg
        saved_cont = self.saved_cont                # UDPR_15                           thread reg

        lm_base_reg     = f"X{GP_REG_BASE+6}"
        temp_value      = self.scratch[0]

        max_th_label = "push_back_to_queue"

        '''
        Event:      Reduce thread
        Operands:   X8: Key
                    X9 ~ Xn: Values
        '''
        # Check the thread name space usage
        if self.debug_flag and self.print_level > 2:
            tran.writeAction(f"print ' '")
            tran.writeAction(f"print '[DEBUG][NWID %ld][{self.task}] Event <{self.ln_worker_launch_reducer_ev_label}> ev_word = %lu income_cont = %lu' {'X0'} {'EQT'} {'X1'}")
        if self.metadata_offset >> 15 > 0:
            tran.writeAction(f"movir {lm_base_reg} {self.metadata_offset}")
            tran.writeAction(f"add {'X7'} {lm_base_reg} {lm_base_reg}")
        else:
            tran.writeAction(f"addi {'X7'} {lm_base_reg} {self.metadata_offset}")
        tran.writeAction(f"move {self.num_reduce_th_offset - self.metadata_offset}({lm_base_reg}) {temp_value} 0 8")
        tran.writeAction(f"move {self.max_red_th_offset - self.metadata_offset}({lm_base_reg}) {self.scratch[1]} 0 8")
        tran.writeAction(f"bge {temp_value} {self.scratch[1]} {max_th_label}")
        tran.writeAction(f"addi {temp_value} {temp_value} 1")
        tran.writeAction(f"move {temp_value}  {self.num_reduce_th_offset - self.metadata_offset}({lm_base_reg}) 0 8")
        
        # Send the intermediate key-value pair to kv_reduce 
        tran = set_ev_label(tran, self.ev_word, self.kv_reduce_ev_label, new_thread=True)
        if self.debug_flag and self.print_level > 2:
            tran.writeAction(f"print '[DEBUG][NWID %ld][{self.task}] Send intermediate key value pair to kv_reduce: key = %ld values = " + 
                                            f"[{' '.join(['%ld' for _ in range(self.inter_kvpair_size - 1)])}]' {'X0'} {inter_key} {' '.join(inter_values)}")
        tran.writeAction(format_pseudo(f"sendops_wret {self.ev_word} {self.ln_worker_reducer_ret_ev_label} {inter_key} {self.inter_kvpair_size}", \
            self.scratch[0], self.send_temp_reg_flag))
        tran.writeAction(f"yield")

        # Reach maximum parallelism push the intermediate key-value pair to the queue
        tran.writeAction(f"{max_th_label}: ev_update_1 EQT {self.ev_word} {NEW_THREAD_ID} {0b0100}")
        if self.debug_flag and self.print_level > 2:
            tran.writeAction(f"print '[DEBUG][NWID %ld][{self.task}] Lane %ld has %ld reduce thread active, reaches max reduce threads, pushed back to queue.' {'X0'} {'X0'} {temp_value}")
        tran.writeAction(f"sendops_wcont X2 X1 {'X8'} {self.inter_kvpair_size}")
        tran.writeAction(f"yield")

    def __gen_worker_reducer_ret(self, tran):
        '''
        Event:  returned from kv_reduce_ret
        '''

        reduce_left_count = "UDPR_4"                # UDPR_4                            thread reg

        scratch = self.scratch                      # UDPR_12, UDPR_13                  local reg
        ev_word = self.ev_word

        tran.writeAction(f"subi {reduce_left_count} {reduce_left_count} 1")

        # If not all reducer tasks have finished, yield
        tran.writeAction(f"bgti {reduce_left_count} 0 waiting_for_reducers")

        # If the number of intermediate kvs hasn't updated, yield
        tran.writeAction(f"movir {scratch[1]} {self.assert_claimed_key_offset}")
        tran.writeAction(f"add {'X7'} {scratch[1]} {scratch[1]}")
        tran.writeAction(f"movlr 0({scratch[1]}) {scratch[0]} 0 {WORD_SIZE}")
        tran.writeAction(f"bnei {scratch[0]} 3 waiting_for_reducers")

        tran.writeAction(f"addi X2 {ev_word} 0")
        tran.writeAction(f"evlb {ev_word} {self.ln_worker_work_ev_label}")
        tran.writeAction(f"movir {scratch[0]} {self._worker_claim_key_flag}")
        tran.writeAction(f"sendr_wcont {ev_word} X2 {scratch[0]} {scratch[0]}")
        tran.writeAction(f"waiting_for_reducers: yield")

        return

    def __gen_worker_helper(self, tran):
        kv_count = "UDPR_1"                         # UDPR_1                            thread reg
        cur_kv_count = "UDPR_2"                     # UDPR_2                            thread reg
        intermediate_ptr = "UDPR_3"                 # UDPR_3                            thread reg
        reduce_left_count = "UDPR_4"                # UDPR_4                            thread reg
        claiming_work = "UDPR_5"                    # UDPR_5                            thread reg
        claim_work_cont = "UDPR_11"                 # UDPR_11                           thread reg
        saved_cont = self.saved_cont                # UDPR_15                           thread reg

        kv_received_count = "UDPR_10"               # UDPR_10                           thread reg

        tran.writeAction(f"addi {kv_received_count} {kv_received_count} {1}")
        if self.debug_flag:
            tran.writeAction(f"print '[NWID %u][WORKER_DEBUG] kv received count %d' X0 {kv_received_count}")
        tran.writeAction(f"addi X2 {self.scratch[0]} 0")
        tran.writeAction(f"evlb {self.scratch[0]} {self.ln_worker_launch_reducer_ev_label}")
        tran.writeAction(f"sendops_wcont {self.scratch[0]} X1 {'X8'} {self.inter_kvpair_size}")
        tran.writeAction(f"yield")

        return



    '''
    Mapper controller thread
    '''
    def __gen_mapper_control(self):
        ln_mapper_control_init_tran = self.state.writeTransition("eventCarry", self.state, self.state, self.ln_mapper_control_init_ev_label)
        ln_mapper_control_rd_part_tran = self.state.writeTransition("eventCarry", self.state, self.state, self.ln_mapper_control_rd_part_ev_label)
        ln_mapper_control_get_ret_tran = self.state.writeTransition("eventCarry", self.state, self.state, self.ln_mapper_control_get_ret_ev_label)
        ln_mapper_control_loop_tran = self.state.writeTransition("eventCarry", self.state, self.state, self.ln_mapper_control_loop_ev_label)

        self.__gen_mapper_control_init(ln_mapper_control_init_tran)
        self.__gen_mapper_control_rd_part(ln_mapper_control_rd_part_tran)
        self.__gen_mapper_control_get_ret(ln_mapper_control_get_ret_tran)
        self.__gen_mapper_control_loop(ln_mapper_control_loop_tran)

    def __gen_mapper_control_init(self, tran):
        '''
        Event:  Launched from worker_work as a map partition is claimed 
        Operands:   X8      Partition pointer
        Cont word:  X1      Worker_work event
        '''
        num_th_active   = "X16"
        max_map_th      = "X17"
        next_iter_evw   = "X20"
        kv_map_evw      = "X21"
        num_map_gen_addr= "X22"
        iter_flag       = "X23"
        iterator        = [f"X{GP_REG_BASE + k + 7}" for k in range(self.in_kvset_iter_size)]
        
        iterator_ops = [f"X{OB_REG_BASE + k}" for k in range(self.in_kvset_iter_size)]


        if self.debug_flag:
            tran.writeAction(f"print '[DEBUG][NWID %ld] worker_mapper_controller initialized with partition ptr at %lu(0x%lx) ' {'X0'} {'X8'} {'X8'}")
        tran.writeAction(f"addi X1 {self.saved_cont} 0")
        tran.writeAction(f"send_dmlm_ld_wret X8 {self.ln_mapper_control_rd_part_ev_label} {max(2, self.in_kvset_iter_size)} {self.scratch[0]}")
        # Initialize local counter and event words.
        tran.writeAction(f"movir {num_th_active} 0")
        tran.writeAction(f"movir {max_map_th} {self.max_map_th_per_lane}")
        tran.writeAction(f"movir {self.num_map_gen} 0")
        tran.writeAction(f"movir {num_map_gen_addr} {self.map_ctr_offset}")
        tran.writeAction(f"add {'X7'} {num_map_gen_addr} {num_map_gen_addr}")

        # Save map thread return event word to scratchpad
        set_ev_label(tran, self.scratch[0], self.ln_mapper_control_loop_ev_label)
        tran.writeAction(f"movir {self.scratch[1]} {self.ln_mstr_evw_offset}")
        tran.writeAction(f"add {'X7'} {self.scratch[1]} {self.scratch[1]}")
        tran.writeAction(f"move {self.scratch[0]} {0}({self.scratch[1]}) 0 8")
        set_ev_label(tran, next_iter_evw, self.ln_mapper_control_get_ret_ev_label)
        set_ev_label(tran, kv_map_evw, self.kv_map_ev_label, new_thread=True)

        tran.writeAction(f"yield")

        return

    def __gen_mapper_control_rd_part(self, tran):
        '''
        Event:      Read the assigned partition and start iterating on the partition
        Operands:   X8 ~ Xn: Iterator
        '''

        num_th_active   = "X16"
        max_map_th      = "X17"
        next_iter_evw   = "X20"
        kv_map_evw      = "X21"
        num_map_gen_addr= "X22"
        iter_flag       = "X23"
        iterator        = [f"X{GP_REG_BASE + k + 7}" for k in range(self.in_kvset_iter_size)]
        
        iterator_ops = [f"X{OB_REG_BASE + k}" for k in range(self.in_kvset_iter_size)]

        empty_part_label    = "lane_master_empty_partition"

        # Start iterating on the assigned partition and set flag
        self.in_kvset.get_next_pair(tran, next_iter_evw, kv_map_evw, self.kv_map_ev_label, iterator_ops, self.scratch, empty_part_label)
        tran.writeAction(f"addi {num_th_active} {num_th_active} 1")
        tran.writeAction(F"movir {iter_flag} {FLAG}")
        tran.writeAction("yield")
        
        # If the partition is empty, return to worker and terminate
        tran.writeAction(f"{empty_part_label}: movir {self.scratch[1]} {self._worker_claim_key_flag}")
        tran.writeAction(f"sendr_wcont {self.saved_cont} {'X2'} {self.scratch[1]} {self.num_map_gen}")
        tran.writeAction(f"yieldt")

        return

    def __gen_mapper_control_get_ret(self, tran):
        '''
        Event:      Receive the next key-value pair from the assigned partition
        Operands:   X8 ~ Xn: Updated iterator and key-value pair.
        '''

        num_th_active   = "X16"
        max_map_th      = "X17"
        next_iter_evw   = "X20"
        kv_map_evw      = "X21"
        num_map_gen_addr= "X22"
        iter_flag       = "X23"
        iterator        = [f"X{GP_REG_BASE + k + 7}" for k in range(self.in_kvset_iter_size)]
        
        iterator_ops = [f"X{OB_REG_BASE + k}" for k in range(self.in_kvset_iter_size)]

        pass_end_label      = "mapper_control_iterator_pass_end"
        mapper_control_cont_label      = "lane_master_loop_continue"
        mapper_control_break_iter_label= "mapper_control_break_iterate_loop"          

        # Check if the iterator pass the end of the assigned partition
        self.in_kvset.check_iter(tran, iterator_ops, self.scratch, pass_end_label)
        # Pause iterating if the number of active map threads is greater than the maximum number of map threads
        tran.writeAction(f"bge {num_th_active} {max_map_th} {mapper_control_break_iter_label}")
        # Get the next key-value pair from the assigned partition
        self.in_kvset.get_next_pair(tran, next_iter_evw, kv_map_evw, self.kv_map_ev_label, iterator_ops, self.scratch, mapper_control_break_iter_label)
        tran.writeAction(f"addi {num_th_active} {num_th_active} 1")
        tran.writeAction(f"yield")
        
        # Pause/stop iterating 
        tran.writeAction(f"{mapper_control_break_iter_label}: movir {iter_flag} 0")
        # Save current position of the iterator
        for k in range(self.in_kvset_iter_size):
            tran.writeAction(f"addi {f'X{OB_REG_BASE+k}'} {iterator[k]} 0")
        tran.writeAction(f"yield")
        
        # Finish iterate the assigned partition
        tran.writeAction(f"{pass_end_label}: subi {num_th_active} {num_th_active} 1")
        for k in range(self.in_kvset_iter_size):
            tran.writeAction(f"addi {f'X{OB_REG_BASE+k}'} {iterator[k]} 0")
        tran.writeAction(f"bgti {num_th_active} 0 {mapper_control_cont_label}")

        tran.writeAction(f"movlr 0({num_map_gen_addr}) {self.num_map_gen} 0 8")
        tran.writeAction(f"movir {self.scratch[1]} {self._worker_claim_key_flag}")
        tran.writeAction(f"sendr_wcont {self.saved_cont} {'X2'} {self.scratch[1]} {self.num_map_gen}")
        tran.writeAction(f"yieldt")

        tran.writeAction(f"{mapper_control_cont_label}: yield")

        return

    def __gen_mapper_control_loop(self, tran):
        '''
        Event:      Main worker mapper controller loop. When a map thread finishes the assigned key-value pair, it returns to this event.
        Operands:   X8 ~ Xn: Map thread returned values.
        '''

        num_th_active   = "X16"
        max_map_th      = "X17"
        next_iter_evw   = "X20"
        kv_map_evw      = "X21"
        num_map_gen_addr= "X22"
        iter_flag       = "X23"
        iterator        = [f"X{GP_REG_BASE + k + 7}" for k in range(self.in_kvset_iter_size)]
        
        iterator_ops = [f"X{OB_REG_BASE + k}" for k in range(self.in_kvset_iter_size)]

        mapper_control_reach_end_label = "mapper_control_reach_end"
        mapper_control_cont_label      = "mapper_control_loop_continue"

        tran.writeAction(f"subi {num_th_active} {num_th_active} 1")
        # Check if lane master is iterating on the assigned partition
        tran.writeAction(f"beqi {iter_flag} {FLAG} {mapper_control_cont_label}")
        # Check if the iterator pass the end of the assigned partition, if not, continue iterating
        self.in_kvset.get_next_pair(tran, next_iter_evw, kv_map_evw, self.kv_map_ev_label, iterator, self.scratch, mapper_control_reach_end_label)
        tran.writeAction(f"addi {num_th_active} {num_th_active} 1")
        tran.writeAction(f"movir {iter_flag} {FLAG}")
        tran.writeAction(f"yield")

        tran.writeAction(f"{mapper_control_reach_end_label}: bgti {num_th_active} 0 {mapper_control_cont_label}")

        # Finish issuing all the assigned input kv set, return to worker and terminate
        tran.writeAction(f"movlr 0({num_map_gen_addr}) {self.num_map_gen} 0 8")
        tran.writeAction(f"movir {self.scratch[1]} {self._worker_claim_key_flag}")
        tran.writeAction(f"sendr_wcont {self.saved_cont} {'X2'} {self.scratch[1]} {self.num_map_gen}")
        tran.writeAction(f"mov_imm2reg {self.num_map_gen} 0")
        tran.writeAction(f"movrl {self.num_map_gen} 0({num_map_gen_addr}) 0 8")
        tran.writeAction(f"yieldt")

        tran.writeAction(f"{mapper_control_cont_label}: yield")

        return





    '''
    Receiver threads that receive 
    1. kvs from kv_emit and materialize them
    2. claim assertion messages from other workers
    3. kvs from static hashed lane to reduce
    '''

    def __gen_receiver(self):
        

        ln_receiver_receive_kv_tran = self.state.writeTransition("eventCarry", self.state, self.state, self.ln_receiver_receive_kv_ev_label)
        ln_receiver_fetched_kv_ptr_for_cache_tran = self.state.writeTransition("eventCarry", self.state, self.state, self.ln_receiver_fetched_kv_ptr_for_cache_ev_label)
        ln_receiver_materialize_ret_tran = self.state.writeTransition("eventCarry", self.state, self.state, self.ln_receiver_materialize_ret_ev_label)
        ln_receiver_update_claimed_key_tran = self.state.writeTransition("eventCarry", self.state, self.state, self.ln_receiver_update_claimed_key_ev_label)
        ln_receiver_assert_claimed_key_tran = self.state.writeTransition("eventCarry", self.state, self.state, self.ln_receiver_assert_claimed_key_ev_label)
        ln_receiver_fetched_inter_dict_entry_ptr_tran = self.state.writeTransition("eventCarry", self.state, self.state, self.ln_receiver_fetched_inter_dict_entry_ptr_ev_label)
        ln_receiver_update_unresolved_kv_count_tran = self.state.writeTransition("eventCarry", self.state, self.state, self.ln_receiver_update_unresolved_kv_count_ev_label)

        self.__gen_receiver_receive_kv(ln_receiver_receive_kv_tran)
        self.__gen_receiver_fetched_inter_dict_entry_ptr(ln_receiver_fetched_inter_dict_entry_ptr_tran)
        self.__gen_receiver_fetched_kv_ptr_for_cache(ln_receiver_fetched_kv_ptr_for_cache_tran)
        self.__gen_receiver_materialize_ret(ln_receiver_materialize_ret_tran)
        self.__gen_receiver_update_claimed_key_thread(ln_receiver_update_claimed_key_tran)
        self.__gen_receiver_assert_claimed_key_thread(ln_receiver_assert_claimed_key_tran)
        self.__gen_receiver_update_unresolved_kv_count(ln_receiver_update_unresolved_kv_count_tran)

        return

    def __gen_receiver_receive_kv(self, tran):

        '''
        Event:  returned from kv_emit, to decide whether materialize the intermediate kv or send to worker that claimed it
        Operands:   X8-n  intermediate kv pair

        2 cache space:
        intermediate_cache: Each entry contains FOUR words, [key*, num_materialized, ptr to materize array, ptr to intermediate_kv_dict entry]
                            key* here is key shifted left one bit, with lowest bit as is_claimed bit
        materialize_kv_cache: each entry contains self.inter_kvpair_size words, kv pairs to be materialized
        '''

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

        if self.debug_flag:
            tran.writeAction(f"print '[LB_DEBUG] Lane %u receives key %u value %lu(0x%lx)' X0 X8 X9 X9")

        # Get number of keys that have been materialized
        tran.writeAction(f"movir {addr} {self.intermediate_cache_offset}")
        tran.writeAction(f"add {'X7'} {addr} {addr}")
        tran.writeAction(f"movlr 0({addr}) {cache_count} 1 8")

        # Locate returned key in the intermediate_cache
        tran.writeAction(f"find_cached_key: blei {cache_count} 0 cache_all_visited")
        tran.writeAction(f"movlr 0({addr}) {key} 1 {WORD_SIZE}")
        tran.writeAction(f"andi {key} {is_claimed} 1")
        tran.writeAction(f"sri {key} {key} 1")
        tran.writeAction(f"beq {key} X8 cache_hit")
        tran.writeAction(f"addi {addr} {addr} {(self.intermediate_cache_entry_size-1)*WORD_SIZE}")
        tran.writeAction(f"subi {cache_count} {cache_count} 1")
        tran.writeAction(f"jmp find_cached_key")

        # If found, check if the key is claimed
        # if claimed, send the intermediate kv to cached location
        # if not claimed, check if the materializing pointer is cached
        tran.writeAction(f"cache_hit: beqi {is_claimed} 0 check_materializing_ptr")
        # if claimed, send to cached event word
        tran.writeAction(f"movlr 0({addr}) {ev_word} 1 {WORD_SIZE}")
        tran.writeAction(f"evi {ev_word} {ev_word} 255 4")
        tran.writeAction(f"evii {scratch[0]} {self.ln_receiver_update_unresolved_kv_count_ev_label} {255} {5}")
        tran.writeAction(f"sendops_wcont {ev_word} {scratch[0]} X8 {self.inter_kvpair_size}")
        if self.debug_flag:
            tran.writeAction(f"sri {ev_word} {scratch[0]} {32}")
            tran.writeAction(f"print '[LB_DEBUG] receiveer_receive_key send key %u value %lu(0x%lx) to lane %d' X8 X9 X9 {scratch[0]}")

        # Update unresolved kv count
        tran.writeAction(f"movir {lm_reg} {self.unresolved_kv_count_offset}")
        tran.writeAction(f"add {'X7'} {lm_reg} {lm_reg}")
        tran.writeAction(f"movlr 0({lm_reg}) {self.scratch[0]} 0 {WORD_SIZE}")
        tran.writeAction(f"addi {self.scratch[0]} {self.scratch[0]} {1}")
        tran.writeAction(f"movrl {self.scratch[0]} 0({lm_reg}) 0 {WORD_SIZE}")
        tran.writeAction(f"yieldt")

        # If found but not claimed, check if the materializing pointer is cached
        num = key                       # UDPR_10                           local reg
        tran.writeAction(f"check_materializing_ptr: movlr 0({addr}) {num} 0 {WORD_SIZE}")
        # If the materializing pointer is cached, materialize the kv
        tran.writeAction(f"bgti {num} 0 store_kv")
        # If the materializing pointer is NOT cached, push the kv to the end of materializing cache
        tran.writeAction(f"jmp init_cache_kv")

        # If not found, 
        # # 1. send dram request to fecth the stored number (should be 0) and materializing ptr
        # tran.writeAction(f"cache_all_visited: movir {lm_reg} {self.intermediate_ptr_offset}")
        # tran.writeAction(f"add {'X7'} {lm_reg} {lm_reg}")
        # tran.writeAction(f"movlr 0({lm_reg}) {intermediate_ptr} 0 {WORD_SIZE}")
        # tran.writeAction(f"muli X8 {scratch[0]} {2*WORD_SIZE}")
        # tran.writeAction(f"add {intermediate_ptr} {scratch[0]} {intermediate_ptr}")
        # tran.writeAction(f"evii {ev_word} {self.ln_receiver_fetched_kv_ptr_for_cache_ev_label} 255 5")
        # tran.writeAction(f"send_dmlm_ld {intermediate_ptr} {ev_word} {2}")

        # 2. send the key to global master to push it into queue
        tran.writeAction(f"cache_all_visited: movir {lm_reg} {self.push_key_cont_offset}")
        tran.writeAction(f"add {'X7'} {lm_reg} {lm_reg}")
        tran.writeAction(f"movlr 0({lm_reg}) {ev_word} 0 {WORD_SIZE}")
        tran.writeAction(f"evii {self.scratch[0]} {self.ln_receiver_fetched_inter_dict_entry_ptr_ev_label} {255} {5}")
        tran.writeAction(f"sendr_wcont {ev_word} {self.scratch[0]} X8 X8")

        # 3. set is_claim bit to 0
        tran.writeAction(f"sli X8 {key} 1")

        # 4. cache the key in scratchpad at the end of the intermediate_cache
        tran.writeAction(f"movir {lm_reg} {self.intermediate_cache_offset}")
        tran.writeAction(f"add {'X7'} {lm_reg} {lm_reg}")
        # Update cached key count
        tran.writeAction(f"movlr 0({lm_reg}) {scratch[0]} 0 {WORD_SIZE}")
        tran.writeAction(f"addi {scratch[0]} {scratch[0]} {1}")
        tran.writeAction(f"movrl {scratch[0]} 0({lm_reg}) 1 {WORD_SIZE}")
        # Cache new key
        tran.writeAction(f"subi {scratch[0]} {scratch[0]} {1}")
        tran.writeAction(f"muli {scratch[0]} {scratch[0]} {self.intermediate_cache_entry_size * WORD_SIZE}")
        tran.writeAction(f"add {scratch[0]} {lm_reg} {lm_reg}")
        tran.writeAction(f"movrl {key} 0({lm_reg}) 1 {WORD_SIZE}")
        # Set number materialized as 0 indicating materializing address hasn't returned
        tran.writeAction(f"movir {scratch[0]} {0}")
        tran.writeAction(f"movrl {scratch[0]} 0({lm_reg}) 1 {WORD_SIZE}")

        # 5. push the kv to the end of materializing cache
        #    and fetch the stored number (should be 0) and materializing ptr (By setting 0 in X8)
        tran.writeAction(f"init_cache_kv: movir {lm_reg} {self.materializing_metadata_offset}")
        tran.writeAction(f"add {'X7'} {lm_reg} {lm_reg}")
        tran.writeAction(f"movlr 0({lm_reg}) {materializing_cache_start} 1 {WORD_SIZE}")
        tran.writeAction(f"movlr 0({lm_reg}) {materializing_cache_end} 1 {WORD_SIZE}")
        tran.writeAction(f"movlr 0({lm_reg}) {materializing_cache_empty} 1 {WORD_SIZE}")

        #   If cache start equals the end, check if the cache is empty
        tran.writeAction(f"beq {materializing_cache_start} {materializing_cache_end} cache_start_equals_end")
        #   elif cache start larger than the end, meaning there is definitely space
        tran.writeAction(f"bgt {materializing_cache_start} {materializing_cache_end} cache_kv")
        #   elif cache start smaller than the end, check if end - start < cache_size
        tran.writeAction(f"sub {materializing_cache_end} {materializing_cache_start} {scratch[0]}")
        tran.writeAction(f"movir {scratch[1]} {self.materialize_kv_cache_size}")
        #   If end - start == cache_size, spin lock
        tran.writeAction(f"beq {scratch[0]} {scratch[1]} spin_lock")
        #   otherwise, if end < limit, cache kv
        tran.writeAction(f"movir {scratch[0]} {self.materialize_kv_cache_offset + self.materialize_kv_cache_size}")
        tran.writeAction(f"add {scratch[0]} {'X7'} {lm_reg}")
        tran.writeAction(f"blt {materializing_cache_end} {lm_reg} cache_kv")
        #   Elif end at limit, reset end to the front of cache space
        tran.writeAction(f"movir {materializing_cache_end} {self.materialize_kv_cache_offset}")
        tran.writeAction(f"add {'X7'} {materializing_cache_end} {materializing_cache_end}")
        tran.writeAction(f"jmp cache_kv")

        tran.writeAction(f"cache_start_equals_end: beqi {materializing_cache_empty} 0 spin_lock")
        tran.writeAction(f"movir {lm_reg} {self.materialize_kv_cache_offset + self.materialize_kv_cache_size}")
        tran.writeAction(f"add {'X7'} {lm_reg} {lm_reg}")
        tran.writeAction(f"blt {materializing_cache_end} {lm_reg} cache_kv")

        # If start and end both at limit, reset them to the front of cache space
        tran.writeAction(f"movir {materializing_cache_start} {self.materialize_kv_cache_offset}")
        tran.writeAction(f"add {'X7'} {materializing_cache_start} {materializing_cache_start}")
        tran.writeAction(f"movir {materializing_cache_end} {self.materialize_kv_cache_offset}")
        tran.writeAction(f"add {'X7'} {materializing_cache_end} {materializing_cache_end}")

        tran.writeAction(f"cache_kv: movrl X8 0({materializing_cache_end}) 1 {WORD_SIZE}")
        for i in range(1, self.inter_kvpair_size):
            tran.writeAction(f"movrl X{OB_REG_BASE+i} 0({materializing_cache_end}) 1 {WORD_SIZE}")
        tran.writeAction(f"beqi {materializing_cache_empty} 0 after_cache")
        tran.writeAction(f"movir {materializing_cache_empty} 0")

        # After caching the entry
        # Update the materialize_cache meta data in spd
        tran.writeAction(f"after_cache: movir {lm_reg} {self.materializing_metadata_offset}")
        tran.writeAction(f"add {'X7'} {lm_reg} {lm_reg}")
        tran.writeAction(f"movrl {materializing_cache_start} 0({lm_reg}) 1 {WORD_SIZE}")
        tran.writeAction(f"movrl {materializing_cache_end} 0({lm_reg}) 1 {WORD_SIZE}")
        tran.writeAction(f"movrl {materializing_cache_empty} 0({lm_reg}) 1 {WORD_SIZE}")
        # Update unresolved kv count
        tran.writeAction(f"movir {lm_reg} {self.unresolved_kv_count_offset}")
        tran.writeAction(f"add {'X7'} {lm_reg} {lm_reg}")
        tran.writeAction(f"movlr 0({lm_reg}) {self.scratch[0]} 0 {WORD_SIZE}")
        tran.writeAction(f"addi {self.scratch[0]} {self.scratch[0]} {1}")
        tran.writeAction(f"movrl {self.scratch[0]} 0({lm_reg}) 0 {WORD_SIZE}")
        tran.writeAction(f"yieldt")

        tran.writeAction(f"spin_lock: evi X2 {ev_word} 255 4")
        tran.writeAction(f"sendops_wcont {ev_word} X1 X8 {self.inter_kvpair_size}")
        tran.writeAction(f"yieldt")



        # If the materializing pointer is cached, materialize the kv and update stored number in dram
        tran.writeAction(f"store_kv: addi {num} {num} 1")
        tran.writeAction(f"movrl {num} 0({addr}) 1 {WORD_SIZE}")
        tran.writeAction(f"movlr 0({addr}) {scratch[1]} 0 {WORD_SIZE}")
        tran.writeAction(f"evii {ev_word} {self.ln_receiver_materialize_ret_ev_label} 255 5")
        # tran.writeAction(f"sendops_dmlm {scratch[1]} {ev_word} X8 {self.inter_kvpair_size}")         # TODO: REPLACE WITH SENDMOPS
        tran.writeAction(f"sendr2_dmlm {scratch[1]} {ev_word} X8 X9")
        if self.debug_flag:
            tran.writeAction(f"print '[LB_DEBUG] receiveer_receive_key materialize key %u value %lu(0x%lx) to Dram %lu(0x%lx)' X8 X9 X9 {scratch[1]} {scratch[1]}")
        tran.writeAction(f"addi {scratch[1]} {scratch[1]} {WORD_SIZE * self.inter_kvpair_size}")
        tran.writeAction(f"movrl {scratch[1]} 0({addr}) 0 {WORD_SIZE}")


        # tran.writeAction(f"movir {addr} {self.intermediate_ptr_offset}")
        # tran.writeAction(f"add {'X7'} {addr} {addr}")
        # tran.writeAction(f"movlr 0({addr}) {intermediate_ptr} 0 {WORD_SIZE}")
        # tran.writeAction(f"muli X8 {scratch[0]} {2*WORD_SIZE}")
        # tran.writeAction(f"add {intermediate_ptr} {scratch[0]} {intermediate_ptr}")
        tran.writeAction(f"movlr {WORD_SIZE}({addr}) {intermediate_ptr} 0 {WORD_SIZE}")
        tran.writeAction(f"sendr_dmlm {intermediate_ptr} {ev_word} {num}")

        tran.writeAction("yieldt")

        return

    def __gen_receiver_fetched_inter_dict_entry_ptr(self, tran):
        '''
        Event:  returned from kv_emit, to decide whether materialize the intermediate kv or send to worker that claimed it
        Operands:   X8  pushed key
                    X9  dram pointer to the inter_dict entry

        2 cache space:
        intermediate_cache: Each entry contains FOUR words, [key*, num_materialized, ptr to materize array, ptr to intermediate_kv_dict entry]
                            key* here is key shifted left one bit, with lowest bit as is_claimed bit
        materialize_kv_cache: each entry contains self.inter_kvpair_size words, kv pairs to be materialized
        '''

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

        if self.debug_flag:
            tran.writeAction(f"print '[LB_DEBUG] Lane %d receiver fetched key %d and inter_dict entry at %lu' X0 X8 X9")

        # Get number of keys that have been materialized
        tran.writeAction(f"movir {addr} {self.intermediate_cache_offset + WORD_SIZE}")
        tran.writeAction(f"add {'X7'} {addr} {addr}")

        # Locate returned key in the intermediate_cache
        tran.writeAction(f"find_cached_key: movlr 0({addr}) {key} 0 {WORD_SIZE}")
        tran.writeAction(f"andi {key} {is_claimed} 1")
        tran.writeAction(f"sri {key} {key} 1")
        tran.writeAction(f"beq {key} X8 cache_hit")
        tran.writeAction(f"addi {addr} {addr} {(self.intermediate_cache_entry_size)*WORD_SIZE}")
        tran.writeAction(f"jmp find_cached_key")

        # Update ptr to intermediate_kv_dict
        tran.writeAction(f"cache_hit: movrl {'X9'} {(self.intermediate_cache_entry_size-1)*WORD_SIZE}({addr}) 0 {WORD_SIZE}")

        # Read kv pointer for cache
        tran.writeAction(f"addi {'X9'} {intermediate_ptr} 0")
        tran.writeAction(f"evii {ev_word} {self.ln_receiver_fetched_kv_ptr_for_cache_ev_label} 255 5")
        tran.writeAction(f"send_dmlm_ld {intermediate_ptr} {ev_word} {2}")

        tran.writeAction(f"yieldt")

        return

    def __gen_receiver_fetched_kv_ptr_for_cache(self, tran):
        '''
        Event:  returned from dram request sent by receiver_receive_kv
                with information to materialize the kv pairs
        Operands:   X8: Count of kv pairs
                    X9: Pointer to kv array
                    X10: Dram address of the entry read in

        2 cache space:
        intermediate_cache: Each entry contains FOUR words, [key*, num_materialized, ptr to materize array, ptr to intermediate_kv_dict entry]
                            key* here is key shifted left one bit, with lowest bit as is_claimed bit
        materialize_kv_cache: each entry contains self.inter_kvpair_size words, kv pairs to be materialized
        '''

        materializing_cache_start = "UDPR_0"        # UDPR_0                            local reg
        materializing_cache_end = "UDPR_1"          # UDPR_1                            local reg
        materializing_cache_empty = "UDPR_2"        # UDPR_2                            local reg

        resolved_kv_count = "UDPR_4"                # UDPR_4                            local reg
        is_claimed = "UDPR_5"                       # UDPR_5                            local reg
        entry_addr = "UDPR_6"                       # UDPR_6                            local reg
        addr = "UDPR_7"                             # UDPR_7                            local reg
        returned_key = "UDPR_8"                     # UDPR_8                            local reg
        new_end = "UDPR_9"                          # UDPR_9                            local reg
        key = "UDPR_10"                             # UDPR_10                           local reg
        materializing_cache_limit = "UDPR_11"       # UDPR_11                           local reg
        scratch = self.scratch                      # [UDPR_12, UDPR_13]                local reg
        ev_word = self.ev_word                      # UDPR_14                           local reg
        lm_reg = scratch[1]

        # Load thread regs from scratchpad
        tran.writeAction(f"movir {lm_reg} {self.materializing_metadata_offset}")
        tran.writeAction(f"add {'X7'} {lm_reg} {lm_reg}")
        tran.writeAction(f"movlr 0({lm_reg}) {materializing_cache_start} 1 {WORD_SIZE}")
        tran.writeAction(f"movlr 0({lm_reg}) {materializing_cache_end} 1 {WORD_SIZE}")
        tran.writeAction(f"movlr 0({lm_reg}) {materializing_cache_empty} 1 {WORD_SIZE}")
        # Set resolved kv count
        tran.writeAction(f"movir {resolved_kv_count} {0}")

        # # Get the key returned
        # tran.writeAction(f"movir {lm_reg} {self.intermediate_ptr_offset}")
        # tran.writeAction(f"add {'X7'} {lm_reg} {lm_reg}")
        # tran.writeAction(f"movlr 0({lm_reg}) {addr} 0 {WORD_SIZE}")
        # tran.writeAction(f"sub X10 {addr} {scratch[0]}")
        # tran.writeAction(f"divi {scratch[0]} {returned_key} {2*WORD_SIZE}")

        # Locate the entry in intermediate_cache
        # And get the key returned
        tran.writeAction(f"movir {addr} {self.intermediate_cache_offset}")
        tran.writeAction(f"add {'X7'} {addr} {addr}")
        tran.writeAction(f"addi {addr} {addr} {WORD_SIZE}")

        tran.writeAction(f"find_cached_key: movlr 0({addr}) {key} 0 {WORD_SIZE}")
        tran.writeAction(f"andi {key} {is_claimed} 1")
        tran.writeAction(f"sri {key} {returned_key} 1")
        tran.writeAction(f"movlr {(self.intermediate_cache_entry_size-1)*WORD_SIZE}({addr}) {scratch[0]} 0 {WORD_SIZE}")
        tran.writeAction(f"beq {scratch[0]} {'X10'} entry_found")
        tran.writeAction(f"addi {addr} {addr} {self.intermediate_cache_entry_size*WORD_SIZE}")
        tran.writeAction(f"jmp find_cached_key")

        # Update the entry in intermediate_cache
        tran.writeAction(f"entry_found: addi {addr} {entry_addr} {WORD_SIZE}")
        tran.writeAction(f"beqi {is_claimed} {1} entry_updated")
        tran.writeAction(f"movrl X8 {WORD_SIZE}({addr}) 1 {WORD_SIZE}")
        tran.writeAction(f"movrl X9 {WORD_SIZE}({addr}) 1 {WORD_SIZE}")

        # Iterate over the materialize_kv_cache and materialize any entry with the same key
        tran.writeAction(f"entry_updated: addi {materializing_cache_start} {addr} 0")
        tran.writeAction(f"addi {materializing_cache_end} {new_end} 0")

        # Iterate from the beginning
        # First check if materializing_cache_start == materializing_cache_end but materializing_cache_empty == 0, i.e. cache is full
        tran.writeAction(f"bne {addr} {materializing_cache_end} iter_do_while")
        tran.writeAction(f"beqi {materializing_cache_empty} 0 iter_and_update_start")
        # If cache is empty, which is not supposed to happen, yield terminate
        if self.debug_flag:
            tran.writeAction(f"print '[ERROR] Lane %u fetched kv ptr for key %u but materializing cache empty!' X0 {returned_key}")
        tran.writeAction(f"yieldt")

        tran.writeAction(f"iter_and_update_start: beq {addr} {materializing_cache_end} iter_end")
        tran.writeAction(f"iter_do_while: movlr 0({addr}) {key} 0 {WORD_SIZE}")
        tran.writeAction(f"bne {key} {returned_key} front_check_empty_entry")
        # If key matches, check if it's claimed
        # If claimed, send it to destination
        tran.writeAction(f"beqi {is_claimed} {0} front_materialize_kv")
        tran.writeAction(f"movlr 0({entry_addr}) {ev_word} 0 {WORD_SIZE}")
        tran.writeAction(f"evi {ev_word} {ev_word} 255 4")
        tran.writeAction(f"evii {scratch[0]} {self.ln_receiver_update_unresolved_kv_count_ev_label} {255} {5}")
        tran.writeAction(f"send_wcont {ev_word} {scratch[0]} {addr} {self.inter_kvpair_size}")
        if self.debug_flag:
            tran.writeAction(f"movlr {WORD_SIZE}({addr}) {scratch[1]} 0 {WORD_SIZE}")
            tran.writeAction(f"sri {ev_word} {scratch[0]} {32}")
            tran.writeAction(f"print '[LB_DEBUG] receiveer_receive_kv_ptr send key %u value %lu(0x%lx) to lane %d' {key} {scratch[1]} {scratch[1]} {scratch[0]}")
        tran.writeAction(f"addi {resolved_kv_count} {resolved_kv_count} {1}")
        tran.writeAction(f"jmp front_reset_kv")
        # Otherwise, materialize and keep iterating,
        # and update materialize count in spd
        tran.writeAction(f"front_materialize_kv: movlr 0({entry_addr}) {scratch[1]} 0 {WORD_SIZE}")
        tran.writeAction(f"addi {scratch[1]} {scratch[1]} 1")
        tran.writeAction(f"movrl {scratch[1]} 0({entry_addr}) 0 {WORD_SIZE}")
        # Update materialize ptr in spd
        tran.writeAction(f"movlr {WORD_SIZE}({entry_addr}) {scratch[1]} 0 {WORD_SIZE}")
        tran.writeAction(f"evii {ev_word} {self.ln_receiver_materialize_ret_ev_label} 255 5")
        tran.writeAction(f"send_dmlm {scratch[1]} {ev_word} {addr} {self.inter_kvpair_size}")
        if self.debug_flag:
            tran.writeAction(f"movlr {WORD_SIZE}({addr}) {scratch[0]} 0 {WORD_SIZE}")
            tran.writeAction(f"print '[LB_DEBUG] receiveer_receive_kv_ptr materialize key %u value %lu(0x%lx) to Dram %lu(0x%lx)' {key} {scratch[0]} {scratch[0]} {scratch[1]} {scratch[1]}")
        tran.writeAction(f"addi {scratch[1]} {scratch[1]} {WORD_SIZE * self.inter_kvpair_size}")
        tran.writeAction(f"movrl {scratch[1]} {WORD_SIZE}({entry_addr}) 0 {WORD_SIZE}")
        tran.writeAction(f"addi {resolved_kv_count} {resolved_kv_count} {1}")

        tran.writeAction(f"front_reset_kv: movir {scratch[0]} -1")
        for i in range(self.inter_kvpair_size):
            tran.writeAction(f"movrl {scratch[0]} {WORD_SIZE * i}({addr}) 0 {WORD_SIZE}")

        tran.writeAction(f"jmp front_proceed_to_next")
        # If key doesn't match, check if it's already materialized and set to -1 as default
        # If materialized, update materializing_cache_start and keep iterating
        # Else, stop updating materializing_cache_start, and iterate the rest of the cache
        tran.writeAction(f"front_check_empty_entry: bnei {key} -1 iter_rest")
        for i in range(self.inter_kvpair_size-1):
            tran.writeAction(f"movlr {8*(i+1)}({addr}) {key} 0 {WORD_SIZE}")
            tran.writeAction(f"bnei {key} -1 iter_rest")

        # Check if updated front of materialize_kv_cache is at limit before procceding to next iteration
        tran.writeAction(f"front_proceed_to_next: addi {addr} {addr} {self.inter_kvpair_size*WORD_SIZE}")
        tran.writeAction(f"addi {materializing_cache_start} {materializing_cache_start} {self.inter_kvpair_size*WORD_SIZE}")
        tran.writeAction(f"ble {materializing_cache_start} {materializing_cache_end} front_set")
        tran.writeAction(f"movir {lm_reg} {self.materialize_kv_cache_offset + self.materialize_kv_cache_size}")
        tran.writeAction(f"add {'X7'} {lm_reg} {lm_reg}")
        tran.writeAction(f"blt {addr} {lm_reg} front_set")
        tran.writeAction(f"movir {addr} {self.materialize_kv_cache_offset}")
        tran.writeAction(f"add {'X7'} {addr} {addr}")
        tran.writeAction(f"addi {addr} {materializing_cache_start} 0")
        tran.writeAction(f"front_set: jmp iter_and_update_start")


        # Iterate the rest of the cache
        tran.writeAction(f"iter_rest: addi {addr} {addr} {self.inter_kvpair_size*WORD_SIZE}")
        tran.writeAction(f"addi {addr} {new_end} 0")
        tran.writeAction(f"movir {scratch[0]} {self.materialize_kv_cache_offset + self.materialize_kv_cache_size}")
        tran.writeAction(f"add {'X7'} {scratch[0]} {materializing_cache_limit}")

        # If reaches the end of cache, stop iterating
        tran.writeAction(f"iter_and_update_end: beq {addr} {materializing_cache_end} iter_end")
        # Change addr to start of cache space if it reaches limit
        tran.writeAction(f"blt {addr} {materializing_cache_limit} compare_key")
        tran.writeAction(f"movir {scratch[0]} {self.materialize_kv_cache_offset }")
        tran.writeAction(f"add {'X7'} {scratch[0]} {addr}")
        tran.writeAction(f"compare_key: movlr 0({addr}) {key} 0 {WORD_SIZE}")
        tran.writeAction(f"beq {key} {returned_key} cache_hit")
        # If key doesn't match, check if it's already materialized and set to -1 as default
        # If materialized, don't update potential new_end
        # Else, mark potential new_end
        tran.writeAction(f"bnei {key} -1 update_new_end")
        for i in range(self.inter_kvpair_size-1):
            tran.writeAction(f"movlr {8*(i+1)}({addr}) {key} 0 {WORD_SIZE}")
            tran.writeAction(f"bnei {key} -1 update_new_end")
        tran.writeAction(f"jmp end_proceed_to_next")

        tran.writeAction(f"update_new_end: addi {addr} {new_end} {self.inter_kvpair_size*WORD_SIZE}")

        tran.writeAction(f"end_proceed_to_next: addi {addr} {addr} {self.inter_kvpair_size*WORD_SIZE}")
        tran.writeAction(f"jmp iter_and_update_end")


        # If key matches, check if it's claimed
        # If claimed, send it to destination
        tran.writeAction(f"cache_hit: beqi {is_claimed} {0} end_materialize_kv")
        tran.writeAction(f"movlr 0({entry_addr}) {ev_word} 0 {WORD_SIZE}")
        tran.writeAction(f"evi {ev_word} {ev_word} 255 4")
        tran.writeAction(f"evii {scratch[0]} {self.ln_receiver_update_unresolved_kv_count_ev_label} {255} {5}")
        tran.writeAction(f"send_wcont {ev_word} {scratch[0]} {addr} {self.inter_kvpair_size}")
        if self.debug_flag:
            tran.writeAction(f"movlr {WORD_SIZE}({addr}) {scratch[1]} 0 {WORD_SIZE}")
            tran.writeAction(f"sri {ev_word} {scratch[0]} {32}")
            tran.writeAction(f"print '[LB_DEBUG] receiveer_receive_kv_ptr send key %u value %lu(0x%lx) to lane %d' {key} {scratch[1]} {scratch[1]} {scratch[0]}")
        tran.writeAction(f"addi {resolved_kv_count} {resolved_kv_count} {1}")
        tran.writeAction(f"jmp end_reset_kv")
        # Otherwise, materialize and keep iterating,
        # and update materialize count in spd
        tran.writeAction(f"end_materialize_kv: movlr 0({entry_addr}) {scratch[1]} 0 {WORD_SIZE}")
        tran.writeAction(f"addi {scratch[1]} {scratch[1]} 1")
        tran.writeAction(f"movrl {scratch[1]} 0({entry_addr}) 0 {WORD_SIZE}")
        # Update materialize ptr in spd
        tran.writeAction(f"movlr {WORD_SIZE}({entry_addr}) {scratch[1]} 0 {WORD_SIZE}")
        tran.writeAction(f"evii {ev_word} {self.ln_receiver_materialize_ret_ev_label} 255 5")
        tran.writeAction(f"send_dmlm {scratch[1]} {ev_word} {addr} {self.inter_kvpair_size}")
        if self.debug_flag:
            tran.writeAction(f"movlr {WORD_SIZE}({addr}) {scratch[0]} 0 {WORD_SIZE}")
            tran.writeAction(f"print '[LB_DEBUG] receiveer_receive_kv_ptr materialize key %u value %lu(0x%lx) to Dram %lu(0x%lx)' {key} {scratch[0]} {scratch[0]} {scratch[1]} {scratch[1]}")
        tran.writeAction(f"addi {scratch[1]} {scratch[1]} {WORD_SIZE * self.inter_kvpair_size}")
        tran.writeAction(f"movrl {scratch[1]} {WORD_SIZE}({entry_addr}) 0 {WORD_SIZE}")
        tran.writeAction(f"addi {resolved_kv_count} {resolved_kv_count} {1}")

        tran.writeAction(f"end_reset_kv: movir {scratch[0]} -1")
        for i in range(self.inter_kvpair_size):
            tran.writeAction(f"movrl {scratch[0]} {WORD_SIZE * i}({addr}) 0 {WORD_SIZE}")
        tran.writeAction(f"jmp end_proceed_to_next")


        # When reaches the end of cache, stop iterating
        # Update materializing_cache_end
        tran.writeAction(f"iter_end: addi {new_end} {materializing_cache_end} 0")
        tran.writeAction(f"bne {materializing_cache_start} {materializing_cache_end} event_end")
        tran.writeAction(f"movir {materializing_cache_empty} 1")
        # If not claimed, Send updated materialized count to dram
        tran.writeAction(f"event_end: beqi {is_claimed} {1} update_meta_data")
        tran.writeAction(f"movlr 0({entry_addr}) {scratch[1]} 0 {WORD_SIZE}")
        tran.writeAction(f"evii {ev_word} {self.ln_receiver_materialize_ret_ev_label} 255 5")
        tran.writeAction(f"sendr_dmlm X10 {ev_word} {scratch[1]}")

        # Update the materialize_cache meta data in spd
        tran.writeAction(f"update_meta_data: movir {scratch[0]} {self.materializing_metadata_offset}")
        tran.writeAction(f"add {'X7'} {scratch[0]} {lm_reg}")
        tran.writeAction(f"movrl {materializing_cache_start} 0({lm_reg}) 1 {WORD_SIZE}")
        tran.writeAction(f"movrl {materializing_cache_end} 0({lm_reg}) 1 {WORD_SIZE}")
        tran.writeAction(f"movrl {materializing_cache_empty} 0({lm_reg}) 1 {WORD_SIZE}")

        # Update unresolved kv count
        tran.writeAction(f"movir {lm_reg} {self.unresolved_kv_count_offset}")
        tran.writeAction(f"add {'X7'} {lm_reg} {lm_reg}")
        tran.writeAction(f"movlr 0({lm_reg}) {self.scratch[0]} 0 {WORD_SIZE}")
        tran.writeAction(f"sub {self.scratch[0]} {resolved_kv_count} {self.scratch[0]}")
        tran.writeAction(f"movrl {self.scratch[0]} 0({lm_reg}) 0 {WORD_SIZE}")


        tran.writeAction(f"yieldt")

        return

    def __gen_receiver_materialize_ret(self, tran):

        tran.writeAction(f"yieldt")

        return

    def __gen_receiver_update_claimed_key_thread(self, tran):

        '''
        Event: return from worker_fetched_key event, update a key that was claimed
        Operands:   X8    key
                    X9    reducer event word
        Cont word:  X1      receiver_assert_claimed_key event at source lane
        '''

        cache_count = "UDPR_6"                      # UDPR_6                            local reg
        addr = "UDPR_7"                             # UDPR_7                            local reg
        is_claimed = "UDPR_9"                       # UDPR_9                            local reg
        key = "UDPR_10"                             # UDPR_10                           local reg
        scratch = self.scratch                      # [UDPR_12, UDPR_13]                local reg
        lm_base_reg = self.scratch[1]               # UDPR_13                           local reg
        ev_word = self.ev_word                      # UDPR_14                           local reg


        # Get number of keys that have been materialized
        tran.writeAction(f"movir {addr} {self.intermediate_cache_offset}")
        tran.writeAction(f"add {'X7'} {addr} {addr}")
        tran.writeAction(f"movlr 0({addr}) {cache_count} 1 8")

        # Locate returned key in the cached array
        tran.writeAction(f"find_cached_key: movlr 0({addr}) {key} 0 {WORD_SIZE}")
        tran.writeAction(f"sri {key} {key} 1")
        tran.writeAction(f"beq {key} X8 cache_hit")
        tran.writeAction(f"addi {addr} {addr} {WORD_SIZE * self.intermediate_cache_entry_size}")
        tran.writeAction(f"subi {cache_count} {cache_count} 1")
        tran.writeAction(f"jmp find_cached_key")

        # Found the key, update the is_claimed bit
        tran.writeAction(f"cache_hit: slorii {key} {key} {1} {1}")
        tran.writeAction(f"movrl {key} 0({addr}) 1 {WORD_SIZE}")
        tran.writeAction(f"movrl X9 0({addr}) 1 {WORD_SIZE}")

        # Send to dest which claimed the key
        # Annoucing the claiming is asserted
        tran.writeAction(f"sendr_reply {key} {key} {scratch[0]}")
        tran.writeAction(f"yieldt")

        return

    def __gen_receiver_assert_claimed_key_thread(self, tran):
        '''
        Event:  returned from worker_update_claimed_key from static hashed lane
                to update the assert_claimed_key bit to 1
        '''

        scratch = self.scratch

        tran.writeAction(f"movir {scratch[1]} {self.assert_claimed_key_offset}")
        tran.writeAction(f"add {'X7'} {scratch[1]} {scratch[1]}")
        tran.writeAction(f"movir {scratch[0]} 1")
        tran.writeAction(f"movrl {scratch[0]} 0({scratch[1]}) 0 {WORD_SIZE}")
        tran.writeAction(f"yieldt")

        return

    def __gen_receiver_update_unresolved_kv_count(self, tran):
        lm_reg = "X16"

        # Update unresolved kv count
        tran.writeAction(f"movir {lm_reg} {self.unresolved_kv_count_offset}")
        tran.writeAction(f"add {'X7'} {lm_reg} {lm_reg}")
        tran.writeAction(f"movlr 0({lm_reg}) {self.scratch[0]} 0 {WORD_SIZE}")
        tran.writeAction(f"subi {self.scratch[0]} {self.scratch[0]} {1}")
        tran.writeAction(f"movrl {self.scratch[0]} 0({lm_reg}) 0 {WORD_SIZE}")
        tran.writeAction(f"yieldt")

'''
Template ends here
-----------------------------------------------------------------------
'''
