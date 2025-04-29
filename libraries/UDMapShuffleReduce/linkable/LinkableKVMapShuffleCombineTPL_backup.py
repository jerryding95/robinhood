from linker.EFAProgram import EFAProgram
from math import log2, ceil
from abc import ABCMeta
from LinkableGlobalSync import GlobalSync, Broadcast
from LinkableKeyValueSetTPL import KeyValueSetInterface
from KVMSRMachineConfig import *
from Macro import *
import sys
import random

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
    extensions = {'original', 'load_balancer', 'non_load_balancing'}
    lb_types = {'mapper', 'reducer', 'reducer_local', 'reducer_global'}
    def __init__(self, efa: EFAProgram, task_name: str, meta_data_offset:int, debug_flag: bool = False, 
                    # Added by: Jerry Ding
                    extension: str = 'original', load_balancer_type = ['mapper'], lb_meta_data_offset: int = -1, 
                    claim_multiple_work = False, do_all_reduce = False):
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
        self.lb_type = load_balancer_type
        self.grlb_type = 'ud'

        # Testing flags
        self.intra_map_work_stealing = False
        self.inter_map_work_stealing = False
        self.global_map_work_stealing = False
        if not(self.extension == 'load_balancer' and 'mapper' in self.lb_type):
            self.intra_map_work_stealing = False
            self.inter_map_work_stealing = False
            self.global_map_work_stealing = False

        self.intra_reduce_work_stealing = False
        self.inter_reduce_work_stealing = False
        self.global_reduce_work_stealing = False

        if self.extension == 'load_balancer' and 'reducer' in self.lb_type:
            if self.grlb_type == 'lane' and self.inter_reduce_work_stealing:
                self.inter_reduce_work_stealing = False
            if self.grlb_type == 'ud' and (self.intra_reduce_work_stealing or self.global_reduce_work_stealing):
                self.intra_reduce_work_stealing = False
                self.global_map_work_stealing = False
        else:
            self.intra_reduce_work_stealing = False
            self.inter_reduce_work_stealing = False
            self.global_reduce_work_stealing = False
        self.random_intra_ud = self.intra_map_work_stealing or self.intra_reduce_work_stealing
        self.random_inter_ud = self.inter_map_work_stealing or self.global_map_work_stealing \
                                or self.inter_reduce_work_stealing or self.global_reduce_work_stealing

        self.any_work_stealing = self.intra_map_work_stealing or self.inter_map_work_stealing or self.global_map_work_stealing \
                                or self.intra_reduce_work_stealing or self.inter_reduce_work_stealing or self.global_reduce_work_stealing

        self.enable_mr_barrier = False
        if self.intra_reduce_work_stealing or self.inter_reduce_work_stealing or self.global_reduce_work_stealing:
            self.enable_mr_barrier = True
        if self.any_work_stealing:
            print(f'Work Stealing testing flags:\n    intra_map_work_stealing: {self.intra_map_work_stealing}\n    inter_map_work_stealing: {self.inter_map_work_stealing}\n    global_map_work_stealing: {self.global_map_work_stealing}')
            print(f'    intra_reduce_work_stealing: {self.intra_reduce_work_stealing}\n    inter_reduce_work_stealing: {self.inter_reduce_work_stealing}\n    global_reduce_work_stealing: {self.global_reduce_work_stealing}')
            print(f'enable_mr_barrier: {self.enable_mr_barrier}')

        self.reset_claiming_dest = False
        self.jump_claiming_dest = False             # In progress
        self.claim_multiple_work = claim_multiple_work            # In progress
        self.record_unresolved_kv_count = False 
        self.sync_terminate = True
        self.do_all_reduce = do_all_reduce
        self.do_all_reduce_with_materialize = True

        if self.extension == 'load_balancer' and self.reset_claiming_dest and self.jump_claiming_dest:
            sys.exit()

        self.log_kv_latency = False
        self.log_reduce_latency = False
        self.print_claiming_work = False
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
        
        # Added by: Jerry Ding
        self.metadata_end_offset    = self.send_buffer_offset + self.SEND_BUFFER_SIZE * WORD_SIZE
        self.heap_offset            = self.metadata_end_offset

        print(f"Reduce thread offset: {self.num_reduce_th_offset}")
        print(f"Initialize MapShuffleReduce task {self.task} - bookkeeping_data_offset: {meta_data_offset}, send_buffer_offset: {self.send_buffer_offset}, heap_offset: {self.heap_offset}, debug_flag: {debug_flag}")

        self.launching_worker = self.extension == 'load_balancer' and not (len(self.lb_type) == 1 and 'reducer_local' in self.lb_type)
        if self.extension == 'load_balancer':
            # self.launching_worker = not (len(self.lb_type) == 1 and 'reducer_local' in self.lb_type)
            print(f"Launching workers: {self.launching_worker}")
            # self.launching_worker = 'mapper' in self.lb_type:

        if self.extension == 'load_balancer' and self.launching_worker:
            self.max_reduce_key_to_claim = 1

            self._finish_flag                       = -1
            self._no_work_to_be_claimed_flag        = -2
            self._worker_start_flag                 = -5 #123456
            self._worker_claim_key_flag             = -6 #654321

            self.lb_meta_data_offset                = lb_meta_data_offset if lb_meta_data_offset >= 0 else self.metadata_end_offset

            if self.jump_claiming_dest:
                self.jump_claiming_dest_offset      = self.lb_meta_data_offset
                self.lb_meta_data_offset            = self.jump_claiming_dest_offset + WORD_SIZE

            if self.any_work_stealing:
                self.rand_seed                          = 12345
                self.rand_offset                        = self.lb_meta_data_offset
                self.metadata_end_offset                = self.rand_offset + WORD_SIZE
                self.lb_meta_data_offset                = self.metadata_end_offset

            self.terminate_bit_offset               = self.lb_meta_data_offset 
            self.mapper_lb_meta_data_offset         = self.terminate_bit_offset + WORD_SIZE
            self.reducer_lb_meta_data_offset        = self.mapper_lb_meta_data_offset




            if 'mapper' in self.lb_type:
                self._map_flag                          = -3

                self.ud_mstr_evw_offset                 = self.mapper_lb_meta_data_offset
                self.ln_part_start_offset               = self.ud_mstr_evw_offset + WORD_SIZE
                self.ln_part_end_offset                 = self.ln_part_start_offset + WORD_SIZE
                self.metadata_end_offset                = self.ln_part_end_offset + WORD_SIZE
                self.reducer_lb_meta_data_offset        = self.metadata_end_offset
                self.heap_offset                        = self.metadata_end_offset

                # if self.intra_map_work_stealing or self.inter_map_work_stealing or self.global_map_work_stealing:
                #     self.rand_seed                          = 12345
                #     self.rand_offset                        = self.ln_part_end_offset + WORD_SIZE
                #     print(self.map_ctr_offset, self.rand_offset)
                #     self.metadata_end_offset                = self.rand_offset + WORD_SIZE
                #     self.reducer_lb_meta_data_offset        = self.metadata_end_offset
                #     self.heap_offset                        = self.metadata_end_offset



            if 'reducer' in self.lb_type:
                # if not self.do_all_reduce:
                self.num_init_events += 1
                
                self._reduce_flag                       = -4
                self._worker_start_flag                 = -5 #123456
                self._worker_claim_key_flag             = -6 #654321
                self._claiming_finish_flag              = -7

                self.intermediate_cache_entry_size      = 4
                self.materialize_kv_cache_entry_size    = 2
                self.materializing_metadata_size        = 3
                self.inter_queue_metadata_size          = 2
                self.inter_dict_metadata_size           = 2
                self.inter_dict_entry_size              = 2

                self.intermediate_cache_num_bins        = 16
                self.intermediate_cache_count           = 256
                self.materialize_kv_cache_count         = 512
                self.intermediate_cache_size            = self.intermediate_cache_count * self.intermediate_cache_entry_size * WORD_SIZE 
                print(f"intermediate_cache_size: {self.intermediate_cache_size}")
                self.materialize_kv_cache_size          = self.materialize_kv_cache_count * self.materialize_kv_cache_entry_size * WORD_SIZE

                # New added fixed scratchpad offset
                self.claiming_work_status_offset        = self.reducer_lb_meta_data_offset
                self.unresolved_kv_count_offset         = self.claiming_work_status_offset + WORD_SIZE
                self.intermediate_ptr_offset            = self.unresolved_kv_count_offset + WORD_SIZE
                self.inter_key_received_count_offset    = self.intermediate_ptr_offset + WORD_SIZE
                self.inter_key_resolved_count_offset    = self.inter_key_received_count_offset + WORD_SIZE
                self.inter_key_executed_count_offset    = self.inter_key_resolved_count_offset + WORD_SIZE
                self.claimed_reduce_key_count_offset    = self.inter_key_executed_count_offset + WORD_SIZE
                self.materializing_metadata_offset      = self.claimed_reduce_key_count_offset + WORD_SIZE
                self.metadata_end_offset                = self.materializing_metadata_offset + self.materializing_metadata_size * WORD_SIZE

                if self.do_all_reduce:
                    self.intermediate_cache_entry_size      = 2
                    self.intermediate_cache_size            = self.intermediate_cache_count * self.intermediate_cache_entry_size * WORD_SIZE 
                    self.intermediate_cache_offset          = self.metadata_end_offset
                    self.heap_offset                        = self.intermediate_cache_offset + self.intermediate_cache_size
                else:
                    self.intermediate_cache_bins_offset     = self.metadata_end_offset
                    self.intermediate_cache_offset          = self.intermediate_cache_bins_offset + self.intermediate_cache_num_bins * WORD_SIZE
                    if self.grlb_type == 'ud':
                        # Account for lock for each bin
                        self.intermediate_cache_offset      += self.intermediate_cache_num_bins * WORD_SIZE
                    self.materialize_kv_cache_offset        = self.intermediate_cache_offset + self.intermediate_cache_size
                    self.heap_offset                        = self.materialize_kv_cache_offset + self.materialize_kv_cache_size

            print(self.metadata_end_offset)
            print(f"lb_type: {self.lb_type}")

    def set_max_thread_per_lane(self, max_map_th_per_lane: int, max_reduce_th_per_lane: int = 0, max_worker_th_per_lane: int = 1, max_reduce_key_to_claim = -1):
        self.max_map_th_per_lane    = max_map_th_per_lane
        self.max_reduce_th_per_lane = max_reduce_th_per_lane
        # Added by: Jerry Ding
        if self.extension == 'load_balancer' and self.launching_worker:
            self.max_worker_th_per_lane = max_worker_th_per_lane
            if self.claim_multiple_work:
                self.max_reduce_key_to_claim = max_reduce_key_to_claim if max_reduce_key_to_claim > 0 else 1

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
        if self.extension == 'load_balancer' and 'reducer' in self.lb_type:
            self.intermediate_cache_offset          = self.metadata_end_offset
            self.materialize_kv_cache_offset        = self.intermediate_cache_offset + self.intermediate_cache_size
            self.heap_offset                        = self.materialize_kv_cache_offset + self.materialize_kv_cache_size

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
        if self.extension == 'load_balancer' and 'reducer' in self.lb_type:
            self.intermediate_cache_offset          = self.metadata_end_offset
            self.materialize_kv_cache_offset        = self.intermediate_cache_offset + self.intermediate_cache_size
            self.heap_offset                        = self.materialize_kv_cache_offset + self.materialize_kv_cache_size

    def setup_cache(self, cache_offset: int, num_entries: int, entry_size: int, ival: int = -1, key_size: int = 1,
                    # Added by: Jerry Ding
                    intermediate_cache_bins_offset: int = -1, intermediate_cache_num_bins = 16,
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
        print(self.cache_size, self.cache_entry_bsize, self.cache_entry_size)
        self.INACTIVE_MASK_SHIFT = 63
        self.INACTIVE_MASK = (1 << self.INACTIVE_MASK_SHIFT)
        self.cache_ival = ival | self.INACTIVE_MASK
        self.power_of_two_cache_size = ceil(log2(self.cache_size)) == log2(self.cache_size)
        self.power_of_two_entry_size = ceil(log2(self.cache_entry_size)) == log2(self.cache_entry_size)

        # Added by: Jerry Ding
        self.heap_offset = self.cache_offset + self.cache_entry_size * self.cache_size * WORD_SIZE
        if self.extension == 'load_balancer':
            if 'reducer_local' in self.lb_type:
                self.heap_offset = self.cache_offset + (self.cache_entry_size + 1) * self.cache_size * WORD_SIZE
            if 'reducer' in self.lb_type:
                self.intermediate_cache_count           = intermediate_cache_size
                self.materialize_kv_cache_count         = materialize_kv_cache_size

                if self.do_all_reduce:
                    self.intermediate_cache_entry_size  = self.inter_kvpair_size
                    self.intermediate_cache_size        = intermediate_cache_size * self.intermediate_cache_entry_size * WORD_SIZE
                    self.intermediate_cache_offset      = intermediate_cache_offset if intermediate_cache_offset > 0 \
                                                            else self.heap_offset
                    self.heap_offset                    = self.intermediate_cache_offset + self.intermediate_cache_size
                    print(self.metadata_end_offset, self.cache_offset, self.intermediate_cache_offset)
                else:
                    self.intermediate_cache_bins_offset = intermediate_cache_bins_offset if intermediate_cache_bins_offset > 0 \
                                                            else self.heap_offset
                    self.intermediate_cache_num_bins    = intermediate_cache_num_bins
                    self.intermediate_cache_offset      = intermediate_cache_offset if intermediate_cache_offset > 0 \
                                                            else self.intermediate_cache_bins_offset + self.intermediate_cache_num_bins * WORD_SIZE
                    if self.grlb_type == 'ud':
                        self.intermediate_cache_offset      += self.intermediate_cache_num_bins * WORD_SIZE
                    self.intermediate_cache_size        = intermediate_cache_size * self.intermediate_cache_entry_size * WORD_SIZE
                    self.materialize_kv_cache_offset    = materialize_kv_cache_offset if materialize_kv_cache_offset > 0 \
                                                            else self.intermediate_cache_offset + self.intermediate_cache_size
                    self.materialize_kv_cache_size      = materialize_kv_cache_size * self.materialize_kv_cache_entry_size * WORD_SIZE
                    self.heap_offset                    = self.materialize_kv_cache_offset + self.materialize_kv_cache_size
                    print(self.metadata_end_offset, self.cache_offset, self.intermediate_cache_bins_offset, self.intermediate_cache_offset, self.materialize_kv_cache_offset)
        print(f"Heap Offset: {self.heap_offset}")

        return

    def setup_lb_cache(self, intermediate_cache_bins_offset: int = -1, intermediate_cache_num_bins = 16,
                        intermediate_cache_offset: int = -1, intermediate_cache_size = 256,
                        materialize_kv_cache_offset: int = -1, materialize_kv_cache_size = 512, materialize_kv_dram_size = 65536):
        self.heap_offset = self.metadata_end_offset
        if self.extension == 'load_balancer' and 'reducer' in self.lb_type:
            self.materialize_kv_cache_entry_size    = self.inter_kvpair_size
            self.intermediate_cache_count           = intermediate_cache_size
            self.materialize_kv_cache_count         = materialize_kv_cache_size

            if self.do_all_reduce:
                    self.materialize_kv_dram_size       = materialize_kv_dram_size
                    self.intermediate_cache_entry_size  = self.inter_kvpair_size
                    self.intermediate_cache_size        = intermediate_cache_size * self.intermediate_cache_entry_size * WORD_SIZE
                    self.intermediate_cache_offset      = intermediate_cache_offset if intermediate_cache_offset > 0 \
                                                            else self.heap_offset
                    self.heap_offset                    = self.intermediate_cache_offset + self.intermediate_cache_size

            else:
                self.intermediate_cache_bins_offset = intermediate_cache_bins_offset if intermediate_cache_bins_offset > 0 \
                                                        else self.heap_offset
                self.intermediate_cache_num_bins    = intermediate_cache_num_bins
                self.intermediate_cache_offset      = intermediate_cache_offset if intermediate_cache_offset > 0 \
                                                        else self.intermediate_cache_bins_offset + self.intermediate_cache_num_bins * WORD_SIZE
                if self.grlb_type == 'ud':
                    self.intermediate_cache_offset      += self.intermediate_cache_num_bins * WORD_SIZE
                self.intermediate_cache_num_bins    = intermediate_cache_num_bins
                self.intermediate_cache_size        = intermediate_cache_size * self.intermediate_cache_entry_size * WORD_SIZE
                self.materialize_kv_cache_offset    = materialize_kv_cache_offset if materialize_kv_cache_offset > 0 \
                                                        else self.intermediate_cache_offset + self.intermediate_cache_size
                self.materialize_kv_cache_size      = materialize_kv_cache_size * self.materialize_kv_cache_entry_size * WORD_SIZE
                self.heap_offset                    = self.materialize_kv_cache_offset + self.materialize_kv_cache_size
        print(f"Heap Offset: {self.heap_offset}")

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
        self.kv_combine_ev_label        = self.get_event_mapping("init_reduce_thread")
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
        print(self.extension, self.launching_worker)
        if self.extension == 'load_balancer' and self.launching_worker:
            self.ln_mstr_launch_worker_ev_label                     = self.get_event_mapping(f"lane_master_launch_worker")

            self.ln_worker_init_ev_label                            = self.get_event_mapping("worker_init")    
            self.ln_worker_work_ev_label                            = self.get_event_mapping("worker_work")     
            self.ln_worker_claim_local_ev_label                     = self.get_event_mapping("worker_claim_local")    
            self.ln_worker_claim_remote_ev_label                    = self.get_event_mapping("worker_claim_remote")           
            self.ln_worker_helper_ev_label                          = self.get_event_mapping("worker_helper")

            self.ln_receiver_claim_work_ev_label                    = self.get_event_mapping("receiver_claim_work")
            self.ln_receiver_set_terminate_bit_ev_label             = self.get_event_mapping("receiver_set_terminate_bit")
            self.ln_receiver_set_terminate_bit_ret_ev_label         = self.get_event_mapping("receiver_set_terminate_bit_ret")


            if 'mapper' in self.lb_type:
                self.ln_worker_claimed_map_ev_label                     = self.get_event_mapping("worker_claimed_map")

                self.ln_mapper_control_init_ev_label                    = self.get_event_mapping("mapper_control_init")
                self.ln_mapper_control_loop_ev_label                    = self.get_event_mapping("mapper_control_loop")
                self.ln_mapper_control_rd_part_ev_label                 = self.get_event_mapping("mapper_control_read_partition")
                self.ln_mapper_control_get_ret_ev_label                 = self.get_event_mapping("mapper_control_get_next_return")
                self.ln_remote_mapper_finished_ev_label                 = self.get_event_mapping("lane_remote_mapper_finished")

            if 'reducer' in self.lb_type:

                self.glb_mstr_term_ev_label                             = self.get_event_mapping("termiante_global_master")

                self.lane_init_interkvset_ev_label                      = self.get_event_mapping("init_intermediate_kvset_on_lane")
                self.lane_init_interkvset_ret_ev_label                  = self.get_event_mapping("init_intermediate_kvset_on_lane_ret")

                self.ln_worker_claimed_reduce_count_ev_label                  = self.get_event_mapping("worker_claimed_reduce_count")
                self.ln_worker_claimed_reduce_ev_label                  = self.get_event_mapping("worker_claimed_reduce")
                self.ln_worker_fetched_kv_ptr_ev_label                  = self.get_event_mapping("worker_fetched_kv_ptr")
                self.ln_worker_launch_reducer_ev_label                  = self.get_event_mapping("worker_launch_reducer")
                self.ln_worker_reducer_ret_ev_label                     = self.get_event_mapping("worker_reducer_ret")
                self.ln_worker_early_finish_ev_label                    = self.get_event_mapping("worker_early_finish")
                self.ln_worker_terminate_ev_label                       = self.get_event_mapping("worker_terminate")

                self.ln_receiver_receive_kv_ev_label                    = self.get_event_mapping(f"receiver_receive_intermediate_kv_pair")
                self.ln_receiver_fetched_kv_ptr_for_cache_ev_label      = self.get_event_mapping("receiver_fetched_kv_ptr_for_cache")
                self.ln_receiver_materialize_ret_ev_label               = self.get_event_mapping("receiver_materialize_ret")
                self.ln_receiver_update_unresolved_kv_count_ev_label    = self.get_event_mapping("receiver_update_unresolved_kv_count")
                self.ln_receiver_acknowledge_key_executed_ev_label      = self.get_event_mapping("receiver_acknowledge_key_executed")


                if self.grlb_type == 'ud':
                    self.ln_worker_confirm_local_materialized_count_ev_label            = self.get_event_mapping("worker_confirm_local_materialized_count")
                    self.ln_worker_confirm_materialized_count_ev_label            = self.get_event_mapping("worker_confirm_materialized_count")
                    self.ln_receiver_check_materialized_count_ev_label            = self.get_event_mapping("receiver_check_materialized_count")
            
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
        if self.enable_intermediate and not self.enable_cache: self.__gen_reduce_thread()
        if self.enable_intermediate and self.enable_cache and self.enable_output: self.__gen_kv_combine()

        # Added by: Jerry Ding
        if self.extension == 'load_balancer'  and self.launching_worker:
            self.__gen_worker()
            self.__gen_receiver()
            if 'mapper' in self.lb_type:
                self.__gen_mapper_control()

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
            if self.extension == 'load_balancer' and 'reducer' in self.lb_type:
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
        if self.extension == 'load_balancer' and 'reducer' in self.lb_type:
            inter_meta_data_addr = "X13" if self.enable_output else "X12"

            # Broadcast intermediate kv set meta data to all the lanes
            if self.debug_flag:
                kvmsr_init_tran.writeAction(f"print '[DEBUG][NWID %ld][{self.task}] Broadcast intermediate key-value set metadata size = 1 copy from addr %lu(0x%lx) to %lu(%0xlx)' \
                {'X0'}  {inter_meta_data_addr} {inter_meta_data_addr} {temp_lm_ptr} {temp_lm_ptr}")

            kvmsr_init_tran.writeAction(f"addi {send_buffer_ptr} {temp_lm_ptr} {WORD_SIZE}")
            # Start of send buffer: init interkvset event word
            kvmsr_init_tran.writeAction(f"movir {init_ev_word} 0")
            kvmsr_init_tran.writeAction(f"evlb {init_ev_word} {self.lane_init_interkvset_ev_label}")
            kvmsr_init_tran.writeAction(f"movrl {init_ev_word} 0({temp_lm_ptr}) 1 {WORD_SIZE}")
            # X8: current network id
            kvmsr_init_tran.writeAction(f"addi {'X0'} {self.scratch[1]} {0}")
            kvmsr_init_tran.writeAction(f"movrl {self.scratch[1]} 0({temp_lm_ptr}) 1 {WORD_SIZE}")
            # X9: start pointer of intermediate space
            kvmsr_init_tran.writeAction(f"addi {inter_meta_data_addr} {self.scratch[0]} 0")
            kvmsr_init_tran.writeAction(f"movlr 0({self.scratch[0]}) {self.scratch[1]} 0 {WORD_SIZE}")
            kvmsr_init_tran.writeAction(f"print 'inter_meta_data_addr %lu reads %ld' {inter_meta_data_addr} {self.scratch[1]}")
            kvmsr_init_tran.writeAction(f"movrl {self.scratch[1]} 0({temp_lm_ptr}) 1 {WORD_SIZE}")
            # Broadcast event to read intermediate hashtable pointer from dram
            kvmsr_init_tran.writeAction(f"send_wcont {self.ev_word} {init_ret_ev_word} {send_buffer_ptr} {self.SEND_BUFFER_SIZE} ")

        #######################

        kvmsr_init_tran.writeAction(f"movir {init_counter} 0")
        kvmsr_init_tran.writeAction(f"addi {'X9'} {part_parameter} 0")
        kvmsr_init_tran.writeAction(f"perflog 1 0 'UDKVMSR Initialization setup finished.' ")
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
        kvmsr_init_fin_tran.writeAction(f"perflog 1 0 'UDKVMSR Initialization Finished.' ")
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
            if self.extension == 'load_balancer' and 'reducer_local' in self.lb_type:
                    tran.writeAction(f"muli {num_entries} {cache_bound} {self.cache_entry_bsize + WORD_SIZE}")
                    tran.writeAction(f"add {cache_base} {cache_bound} {cache_bound}")
                    if self.debug_flag:
                        tran.writeAction(f"print 'num_entries %lu cache_base %lu cache_bound %lu' {num_entries} {cache_base} {cache_bound}")
                    tran.writeAction(f"movir {self.scratch[0]} {-1}")
                    tran.writeAction(f"{cache_init_loop_label}: movrl {ival} {0}({cache_base}) 0 8")
                    tran.writeAction(f"movrl {self.scratch[0]} {self.cache_entry_bsize}({cache_base}) 0 {WORD_SIZE}")
                    tran.writeAction(f"addi {cache_base} {cache_base} {self.cache_entry_bsize + WORD_SIZE}")
                    tran.writeAction(f"blt {cache_base} {cache_bound} {cache_init_loop_label}")
            else:
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
        if self.extension == 'load_balancer' and self.launching_worker and self.jump_claiming_dest:
            step = 1 if 'reducer' in self.lb_type and self.grlb_type == 'lane' else LANE_PER_UD
            tran.writeAction(f"sub X0 X9 {self.scratch[0]}")
            tran.writeAction(f"addi {self.scratch[0]} {self.scratch[0]} {step}")
            tran.writeAction(f"mod {self.scratch[0]} X8 {self.scratch[0]}")
            tran.writeAction(f"add {self.scratch[0]} X9 {self.scratch[0]}")
            if step == LANE_PER_UD:
                tran.writeAction(f"sri {self.scratch[0]} {self.scratch[0]} {int(log2(LANE_PER_UD))}")
            tran.writeAction(f"movir {lm_base} {self.jump_claiming_dest_offset}")
            tran.writeAction(f"add {'X7'} {lm_base} {lm_base}")
            tran.writeAction(f"movrl {self.scratch[0]} {0}({lm_base}) 0 {WORD_SIZE}")

        if self.extension == 'load_balancer' and 'reducer' in self.lb_type:
            addr = f"X{GP_REG_BASE+5}"

            if self.grlb_type == 'lane':
                # Initialize the materializing metadata
                if self.do_all_reduce and self.do_all_reduce_with_materialize:
                    tran.writeAction(f"movir {self.scratch[0]} {self.materializing_metadata_offset}")
                    tran.writeAction(f"add {'X7'} {self.scratch[0]} {addr}")
                    tran.writeAction(f"movir {self.scratch[1]} {0}")
                    tran.writeAction(f"movrl {self.scratch[1]} 0({addr}) 1 {WORD_SIZE}")
                    tran.writeAction(f"movrl {self.scratch[1]} 0({addr}) 1 {WORD_SIZE}")
                else:
                    tran.writeAction(f"movir {self.scratch[0]} {self.materializing_metadata_offset}")
                    tran.writeAction(f"add {'X7'} {self.scratch[0]} {addr}")
                    tran.writeAction(f"movir {self.scratch[1]} {self.materialize_kv_cache_offset}")
                    tran.writeAction(f"add {'X7'} {self.scratch[1]} {self.scratch[1]}")
                    tran.writeAction(f"movrl {self.scratch[1]} 0({addr}) 1 {WORD_SIZE}")
                    tran.writeAction(f"movrl {self.scratch[1]} 0({addr}) 1 {WORD_SIZE}")
                    tran.writeAction(f"movir {self.scratch[1]} 1")
                    tran.writeAction(f"movrl {self.scratch[1]} 0({addr}) 1 {WORD_SIZE}")

            elif self.grlb_type == 'ud':
                tran.writeAction(f"andi {'X0'} {'X16'} {63}")
                tran.writeAction(f"bnei {'X16'} {0} init_lane_spd")

                tran.writeAction(f"movir {addr} {self.materializing_metadata_offset}")
                tran.writeAction(f"add {'X7'} {addr} {addr}")
                tran.writeAction(f"movir {self.scratch[1]} 0")
                tran.writeAction(f"movrl {self.scratch[1]} 0({addr}) 1 {WORD_SIZE}")
                tran.writeAction(f"movrl {self.scratch[1]} 0({addr}) 1 {WORD_SIZE}")

            tran.writeAction(f"movir {self.scratch[0]} {self.intermediate_cache_offset}")
            tran.writeAction(f"add {'X7'} {self.scratch[0]} {addr}")
            tran.writeAction(f"movir {self.scratch[1]} {0}")
            tran.writeAction(f"movrl {self.scratch[1]} 0({addr}) 1 {WORD_SIZE}")

            tran.writeAction(f"movir {self.scratch[0]} {0}")
            tran.writeAction(f"movir {addr} {self.lb_meta_data_offset}")
            tran.writeAction(f"add {'X7'} {addr} {addr}")

            tran.writeAction(f"movrl {self.scratch[0]} {self.unresolved_kv_count_offset - self.lb_meta_data_offset}({addr}) 0 {WORD_SIZE}")
            tran.writeAction(f"movrl {self.scratch[0]} {self.inter_key_received_count_offset - self.lb_meta_data_offset}({addr}) 0 {WORD_SIZE}")
            tran.writeAction(f"movrl {self.scratch[0]} {self.inter_key_resolved_count_offset - self.lb_meta_data_offset}({addr}) 0 {WORD_SIZE}")
            tran.writeAction(f"movrl {self.scratch[0]} {self.inter_key_executed_count_offset - self.lb_meta_data_offset}({addr}) 0 {WORD_SIZE}")
            tran.writeAction(f"movrl {self.scratch[0]} {self.claimed_reduce_key_count_offset - self.lb_meta_data_offset}({addr}) 0 {WORD_SIZE}")

            tran.writeAction(f"init_lane_spd: movir {addr} {self.terminate_bit_offset}")
            tran.writeAction(f"add X7 {addr} {addr}")
            tran.writeAction(f"movir {self.scratch[0]} {-1}")
            tran.writeAction(f"movrl {self.scratch[0]} 0({addr}) 0 {WORD_SIZE}")
            if self.debug_flag:
                tran.writeAction(f"print 'Lane %u setting terminate bit to %ld' X0 {self.scratch[0]} ")

            tran.writeAction(f"movir {addr} {self.intermediate_cache_offset}")
            tran.writeAction(f"add {'X7'} {addr} {addr}")
            tran.writeAction(f"movir {self.scratch[0]} {-1}")
            tran.writeAction(f"movir {self.scratch[1]} {self.intermediate_cache_count}")
            tran.writeAction(f"init_intermediate_cache: beqi {self.scratch[1]} {0} end_init_intermediate_cache")
            tran.writeAction(f"movrl {self.scratch[0]} 0({addr}) 0 {WORD_SIZE}")
            tran.writeAction(f"addi {addr} {addr} {self.intermediate_cache_entry_size * WORD_SIZE}")
            tran.writeAction(f"subi {self.scratch[1]} {self.scratch[1]} {1}")
            tran.writeAction(f"jmp init_intermediate_cache")
            if self.do_all_reduce:
                tran.writeAction(f"end_init_intermediate_cache: movir {self.scratch[0]} {0}")
            else:
                tran.writeAction(f"end_init_intermediate_cache: movir {addr} {self.intermediate_cache_bins_offset}")
                tran.writeAction(f"add {'X7'} {addr} {addr}")
                # tran.writeAction(f"movir {self.scratch[0]} {-1}")
                if self.grlb_type == 'ud':
                    tran.writeAction(f"movir {self.scratch[1]} {0}")
                for _ in range(self.intermediate_cache_num_bins):
                    tran.writeAction(f"movrl {self.scratch[0]} 0({addr}) 1 {WORD_SIZE}")
                    if self.grlb_type =='ud':
                        tran.writeAction(f"movrl {self.scratch[1]} 0({addr}) 1 {WORD_SIZE}")



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
        if self.extension == 'load_balancer' and 'reducer' in self.lb_type:
            '''
            Event:      Load intermediate kvset metadata to scratchpad
            Operands:   X8: Global master network id
                        X9: Start pointer of intermediate space
            '''
            init_interkvset_tran = self.state.writeTransition("eventCarry", self.state, self.state, self.lane_init_interkvset_ev_label)

            if self.grlb_type == 'lane':
                init_interkvset_tran.writeAction(f"sub {'X0'} {'X8'} {self.scratch[0]}")
                init_interkvset_tran.writeAction(f"muli {self.scratch[0]} {self.scratch[0]} {WORD_SIZE}")
                init_interkvset_tran.writeAction(f"add {'X9'} {self.scratch[0]} {self.scratch[0]}")
                init_interkvset_tran.writeAction(f"send_dmlm_ld_wret {self.scratch[0]} {self.lane_init_interkvset_ret_ev_label} {1} {self.scratch[1]}")

                init_interkvset_tran.writeAction("yield")

            elif self.grlb_type == 'ud':
                init_interkvset_tran.writeAction(f"andi X0 X16 63")
                init_interkvset_tran.writeAction(f"bnei X16 0 not_lane_0")

                init_interkvset_tran.writeAction(f"sub {'X0'} {'X8'} {self.scratch[0]}")
                init_interkvset_tran.writeAction(f"sri {self.scratch[0]} {self.scratch[0]} {int(log2(64))}")
                init_interkvset_tran.writeAction(f"muli {self.scratch[0]} {self.scratch[0]} {WORD_SIZE}")
                init_interkvset_tran.writeAction(f"add {'X9'} {self.scratch[0]} {self.scratch[0]}")
                if self.debug_flag:
                    init_interkvset_tran.writeAction(f"sri X0 {self.scratch[1]} 6")
                    init_interkvset_tran.writeAction(f"print 'Lane %u ud %u init_interkvset load dram %lu, operand X8 %ld, X9 %ld' X0 {self.scratch[1]} {self.scratch[0]} X8 X9")
                init_interkvset_tran.writeAction(f"send_dmlm_ld_wret {self.scratch[0]} {self.lane_init_interkvset_ret_ev_label} {1} {self.scratch[1]}")

                init_interkvset_tran.writeAction("yield")


                init_interkvset_tran.writeAction(f"not_lane_0: sendr_reply X0 X16 {self.scratch[0]}")
                init_interkvset_tran.writeAction(f"yieldt")

            '''
            Event:      Write intermediate kvset metadata to scratchpad
            Operands:   X8: Pointer to intermediate hashtable assigned to this lane
            '''
            init_interkvset_ret_tran = self.state.writeTransition("eventCarry", self.state, self.state, self.lane_init_interkvset_ret_ev_label)

            init_interkvset_ret_tran.writeAction(f"movir {self.scratch[0]} {self.intermediate_ptr_offset}")
            init_interkvset_ret_tran.writeAction(f"add {'X7'} {self.scratch[0]} {self.scratch[0]}")
            init_interkvset_ret_tran.writeAction(f"movrl {'X8'} 0({self.scratch[0]}) 0 {WORD_SIZE}")
            if self.debug_flag:
                init_interkvset_ret_tran.writeAction(f"sri X0 {self.scratch[1]} 6")
                init_interkvset_ret_tran.writeAction(f"print 'Lane %u ud %u cached intermediate pointer %lu(0x%lx)' X0 {self.scratch[1]} X8 X8")

            init_interkvset_ret_tran.writeAction(f"sendr_reply X0 X16 {self.scratch[0]}")
            init_interkvset_ret_tran.writeAction("yieldt")


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
        if self.extension == 'load_balancer' and 'reducer' in self.lb_type:
            num_node_worker_active  = f"X{GP_REG_BASE+10}"
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
        if self.extension == 'load_balancer' and 'reducer' in self.lb_type:
            glb_mstr_init_tran.writeAction(f"addi {num_node_worker_active} {num_node_worker_active} 1")
        glb_mstr_init_tran.writeAction(f"blt {num_node_active} {self.num_child} {glb_mstr_loop_label}")
        glb_mstr_init_tran.writeAction(f"mul {num_node_active} {part_stride} {self.num_part_issued}")
        # glb_mstr_init_tran.writeAction(f"lshift {num_node_active} {self.num_part_issued} {LOG2_LANE_PER_UD + LOG2_UD_PER_NODE}")
        glb_mstr_init_tran.writeAction(f"mov_imm2reg {self.num_map_gen} 0")    # total number of kv_pair generated by mapper
        if self.debug_flag:
            glb_mstr_init_tran.writeAction(f"print '[DEBUG][NWID %ld][{self.task}] Global master num_partitions = %ld, num_part_issued = %ld' \
                {'X0'} {num_partitions} {self.num_part_issued}")
        if self.extension == 'load_balancer' and 'reducer' in self.lb_type:
            num_node_claim_finished = f"X{GP_REG_BASE+7}"
            glb_mstr_init_tran.writeAction(f"movir {num_node_claim_finished} {0}")
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
        if self.extension == 'load_balancer' and 'reducer' in self.lb_type:
            glb_mstr_loop_tran.writeAction(f"movir {self.scratch[0]} {self._claiming_finish_flag}")
            glb_mstr_loop_tran.writeAction(f"beq X8 {self.scratch[0]} node_claiming_finished")
            if self.sync_terminate:
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
        if not (self.extension == 'load_balancer' and 'reducer' in self.lb_type):
            glb_mstr_loop_tran = set_ev_label(glb_mstr_loop_tran, self.ev_word, self.nd_mstr_term_ev_label, "X1")
            glb_mstr_loop_tran.writeAction(f"sendr_wcont {self.ev_word} X2 {self.part_array_ptr} {self.part_array_ptr}")
            if self.debug_flag:
                glb_mstr_loop_tran.writeAction(f"print '[DEBUG][NWID %ld][{self.task}] Global master num_map_generated = %ld, number of active node = %ld' {'X0'} {self.num_map_gen} {num_node_active}")
            glb_mstr_loop_tran.writeAction(f"beqi {num_node_active} 0 {glb_mstr_fin_map_label}")
            glb_mstr_loop_tran.writeAction(f"yield")

            if self.extension == 'load_balancer' and 'mapper' in self.lb_type and not self.intra_map_work_stealing:
                # All mappers finished, broadcast to set terminate bit
                glb_mstr_loop_tran.writeAction(f"{glb_mstr_fin_map_label}: evii {self.ev_word}, {self.glb_bcst_ev_label} {255} {5}")
                glb_mstr_loop_tran.writeAction(f"movir {self.scratch[1]} {self.send_buffer_offset}")
                glb_mstr_loop_tran.writeAction(f"add {'X7'} {self.scratch[1]} {self.scratch[1]}")
                # Number of lanes in X8
                glb_mstr_loop_tran.writeAction(f"movrl {self.num_lane_reg} 0({self.scratch[1]}) 0 {WORD_SIZE}")
                # Event label in X9
                glb_mstr_loop_tran.writeAction(f"movir {self.scratch[0]} 0")
                glb_mstr_loop_tran.writeAction(f"evlb {self.scratch[0]} {self.ln_receiver_set_terminate_bit_ev_label}")
                glb_mstr_loop_tran.writeAction(f"movrl {self.scratch[0]} {WORD_SIZE}({self.scratch[1]}) 0 {WORD_SIZE}")
                # Terminate bit data in X10
                glb_mstr_loop_tran.writeAction(f"movir {self.scratch[0]} 1")
                glb_mstr_loop_tran.writeAction(f"movrl {self.scratch[0]}  {WORD_SIZE * 2}({self.scratch[1]}) 0 {WORD_SIZE}")
                # Broadcast
                glb_mstr_loop_tran.writeAction(f"evii {self.scratch[0]} {self.ln_receiver_set_terminate_bit_ret_ev_label} {255} {5}")
                glb_mstr_loop_tran.writeAction(f"send_wcont {self.ev_word} {self.scratch[0]} {self.scratch[1]} {self.SEND_BUFFER_SIZE}")
                glb_mstr_loop_tran.writeAction(f"print 'broadcasting terminate bit, num_map_gen %lu' {self.num_map_gen}")

                # All the map master threads are termianted, check if there is any intermediate key-value pairs generated by the map threads
                glb_mstr_loop_tran.writeAction(f"bnei {self.num_map_gen} 0 {glb_mstr_init_sync_label}")

            else:
                # All the map master threads are termianted, check if there is any intermediate key-value pairs generated by the map threads
                glb_mstr_loop_tran.writeAction(f"{glb_mstr_fin_map_label}: bnei {self.num_map_gen} 0 {glb_mstr_init_sync_label}")
            # UDKVMSR finishes, return back to user continuation
            set_ignore_cont(glb_mstr_loop_tran, self.scratch[0])
            glb_mstr_loop_tran.writeAction(f"sendr_wcont {self.saved_cont} {self.scratch[0]} {self.num_lane_reg} {self.num_map_gen}")
            glb_mstr_loop_tran.writeAction(f"print 'returning to user cont %lx' {self.saved_cont}")
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
        if self.extension == 'load_balancer' and 'reducer' in self.lb_type:
            if self.debug_flag:
                glb_mstr_loop_tran.writeAction(f"print '[DEBUG][NWID %ld][{self.task}] Global master num_map_generated = %ld, number of active node = %ld' {'X0'} {self.num_map_gen} {num_node_active}")
            glb_mstr_loop_tran.writeAction(f"beqi {num_node_active} 0 {glb_mstr_fin_map_label}")
            glb_mstr_loop_tran.writeAction(f"yield")

            # All mappers finished, broadcast to set terminate bit
            glb_mstr_loop_tran.writeAction(f"{glb_mstr_fin_map_label}: evii {self.ev_word}, {self.glb_bcst_ev_label} {255} {5}")
            glb_mstr_loop_tran.writeAction(f"movir {self.scratch[1]} {self.send_buffer_offset}")
            glb_mstr_loop_tran.writeAction(f"add {'X7'} {self.scratch[1]} {self.scratch[1]}")
            # Number of lanes in X8
            glb_mstr_loop_tran.writeAction(f"movrl {self.num_lane_reg} 0({self.scratch[1]}) 0 {WORD_SIZE}")
            # Event label in X9
            glb_mstr_loop_tran.writeAction(f"movir {self.scratch[0]} 0")
            glb_mstr_loop_tran.writeAction(f"evlb {self.scratch[0]} {self.ln_receiver_set_terminate_bit_ev_label}")
            glb_mstr_loop_tran.writeAction(f"movrl {self.scratch[0]} {WORD_SIZE}({self.scratch[1]}) 0 {WORD_SIZE}")
            # Terminate bit data in X10
            glb_mstr_loop_tran.writeAction(f"movir {self.scratch[0]} 0")
            glb_mstr_loop_tran.writeAction(f"movrl {self.scratch[0]} {WORD_SIZE * 2}({self.scratch[1]}) 0 {WORD_SIZE}")
            # Broadcast
            glb_mstr_loop_tran.writeAction(f"evii {self.scratch[0]} {self.ln_receiver_set_terminate_bit_ret_ev_label} {255} {5}")
            glb_mstr_loop_tran.writeAction(f"send_wcont {self.ev_word} {self.scratch[0]} {self.scratch[1]} {self.SEND_BUFFER_SIZE}")
            glb_mstr_loop_tran.writeAction(f"yield")



            # If self._claiming_finish_flag is returned, meaning a node's local keys are all claimed
            glb_mstr_loop_tran.writeAction(f"node_claiming_finished: addi {num_node_claim_finished} {num_node_claim_finished} {1}")
            if not self.sync_terminate:
                glb_mstr_loop_tran = set_ev_label(glb_mstr_loop_tran, self.ev_word, self.nd_mstr_term_ev_label, "X1")
                glb_mstr_loop_tran.writeAction(f"sendr_wcont {self.ev_word} X2 {self.part_array_ptr} {self.part_array_ptr}")
            glb_mstr_loop_tran.writeAction(f"beq {num_node_claim_finished} {num_node_worker_active} global_claiming_finished")
            glb_mstr_loop_tran.writeAction(f"yield")

            # If all nodes' local work claimed, broadcast to set the terminate bit
            glb_mstr_loop_tran.writeAction(f"global_claiming_finished: movir {self.scratch[0]} {self._claiming_finish_flag}")

            glb_mstr_loop_tran.writeAction(f"evii {self.ev_word}, {self.glb_bcst_ev_label} {255} {5}")
            # set_ev_label(glb_mstr_loop_tran, self.ev_word, self.glb_bcst_ev_label, new_thread = True)
            glb_mstr_loop_tran.writeAction(f"movir {self.scratch[1]} {self.send_buffer_offset}")
            glb_mstr_loop_tran.writeAction(f"add {'X7'} {self.scratch[1]} {self.scratch[1]}")
            # Number of lanes in X8
            glb_mstr_loop_tran.writeAction(f"movrl {self.num_lane_reg} 0({self.scratch[1]}) 0 {WORD_SIZE}")
            # Event label in X9
            glb_mstr_loop_tran.writeAction(f"movir {self.scratch[0]} 0")
            glb_mstr_loop_tran.writeAction(f"evlb {self.scratch[0]} {self.ln_receiver_set_terminate_bit_ev_label}")
            glb_mstr_loop_tran.writeAction(f"movrl {self.scratch[0]} {WORD_SIZE}({self.scratch[1]}) 0 {WORD_SIZE}")
            # Terminate bit data in X10
            glb_mstr_loop_tran.writeAction(f"movir {self.scratch[0]} 1")
            glb_mstr_loop_tran.writeAction(f"movrl {self.scratch[0]}  {WORD_SIZE * 2}({self.scratch[1]}) 0 {WORD_SIZE}")
            # Broadcast
            if self.sync_terminate or self.enable_cache:
                glb_mstr_loop_tran.writeAction(f"evii {self.scratch[0]} {self.ln_receiver_set_terminate_bit_ret_ev_label} {255} {5}")
            else:
                glb_mstr_loop_tran.writeAction(f"addi X2 {self.scratch[0]} {0}")
                glb_mstr_loop_tran.writeAction(f"evlb {self.scratch[0]} {self.glb_mstr_term_ev_label}")
            glb_mstr_loop_tran.writeAction(f"send_wcont {self.ev_word} {self.scratch[0]} {self.scratch[1]} {self.SEND_BUFFER_SIZE}")
            # glb_mstr_loop_tran.writeAction(f"send_wret {self.ev_word} {self.glb_mstr_term_ev_label} {self.scratch[1]} {self.SEND_BUFFER_SIZE} {self.scratch[0]}")
            


            if self.sync_terminate:

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
                    # glb_mstr_loop_tran.writeAction(f"kvmsr_finished: print 'Load Balancing UDKVMSR finished.' ")
                    # set_ignore_cont(glb_mstr_loop_tran, self.scratch[0])
                    # glb_mstr_loop_tran.writeAction(f"sendr_wcont {self.saved_cont} {self.scratch[0]} {self.scratch[1]} {self.scratch[1]}")
                    # glb_mstr_loop_tran.writeAction(f"yieldt")

                    glb_mstr_loop_tran.writeAction(f"kvmsr_finished: addi X2 {self.ev_word} {0}")
                    glb_mstr_loop_tran.writeAction(f"evlb {self.ev_word} {self.glb_mstr_term_ev_label}")
                    glb_mstr_loop_tran.writeAction(f"sendr_wcont {self.ev_word} {self.saved_cont} {self.scratch[1]} {self.scratch[1]}")
                    glb_mstr_loop_tran.writeAction(f"yield")

            else:
                if self.enable_cache:
                    # Flush the cache
                    set_ev_label(glb_mstr_loop_tran, self.ev_word, self.cache_flush_ev_label)
                    # glb_mstr_loop_tran.writeAction(f"sendr_wcont {self.ev_word} {self.saved_cont} {self.num_lane_reg} {self.num_map_gen}")
                    glb_mstr_loop_tran.writeAction(f"sendr_wret {self.ev_word} {self.glb_mstr_term_ev_label} {self.num_lane_reg} {self.num_map_gen}")
                    glb_mstr_loop_tran.writeAction(f"yield")
                else:
                    glb_mstr_loop_tran.writeAction(f"yield")

  
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
            

        if self.extension == 'load_balancer' and 'reducer' in self.lb_type:
            glb_mstr_term_tran = self.state.writeTransition("eventCarry", self.state, self.state, self.glb_mstr_term_ev_label)

            glb_mstr_term_tran.writeAction(f"print 'Load Balancing UDKVMSR Terminated.'")
            glb_mstr_term_tran.writeAction(f"perflog 1 0 'Load Balancing UDKVMSR Terminated.'")
            set_ignore_cont(glb_mstr_term_tran, self.scratch[0])
            # glb_mstr_term_tran.writeAction(f"sendr_wcont {self.saved_cont} {self.scratch[0]} {self.scratch[1]} {self.scratch[1]}")
            glb_mstr_term_tran = set_ev_label(glb_mstr_term_tran, self.ev_word, self.glb_sync_init_ev_label, src_ev="X2", new_thread=True)
            glb_mstr_term_tran.writeAction(f"sendr_wcont {self.ev_word} {self.saved_cont} {self.num_lane_reg} {self.num_map_gen}")
            glb_mstr_term_tran.writeAction(f"yieldt")


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
        if self.extension == 'load_balancer' and self.launching_worker:
            num_ud_worker_active  = f"X{GP_REG_BASE+10}"
            nd_mstr_init_tran.writeAction(f"movir {num_ud_worker_active} {0}")
            if 'reducer' in self.lb_type:
                num_ud_claim_finished = f"X{GP_REG_BASE+4}"
                nd_mstr_init_tran.writeAction(f"movir {num_ud_claim_finished} {0}")
            

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
        if self.extension == 'load_balancer' and self.launching_worker:
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
        if self.extension == 'load_balancer' and 'reducer' in self.lb_type:
            nd_mstr_loop_tran.writeAction(f"movir {self.scratch[0]} {self._claiming_finish_flag}")
            nd_mstr_loop_tran.writeAction(f"beq X8 {self.scratch[0]} ud_claiming_finished")
            if self.sync_terminate:
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
        # if self.extension == 'original':
        if not (self.extension == 'load_balancer' and 'reducer' in self.lb_type):
            nd_mstr_loop_tran = set_ev_label(nd_mstr_loop_tran, self.ev_word, self.ud_mstr_term_ev_label, "X1")
            nd_mstr_loop_tran.writeAction(f"sendr_wcont {self.ev_word} X2 {self.part_array_ptr} {udid_stride}")
        nd_mstr_loop_tran.writeAction(f"beqi {num_ud_active} 0 {nd_mstr_fin_part_label}")
        nd_mstr_loop_tran.writeAction(f"yield")
        nd_mstr_loop_tran.writeAction(format_pseudo(f"{nd_mstr_fin_part_label}: sendr_wret {self.saved_cont} {self.nd_mstr_init_ev_label} \
            {self.num_map_gen} {self.num_map_gen}", self.scratch[0], self.send_temp_reg_flag))
        nd_mstr_loop_tran.writeAction(f"mov_imm2reg {self.num_map_gen} 0")
        nd_mstr_loop_tran.writeAction(f"yield")

        # Added by: Jerry Ding
        if self.extension == 'load_balancer' and 'reducer' in self.lb_type:
            # If self._claiming_finish_flag is returned, meaning a ud's local keys are all claimed
            nd_mstr_loop_tran.writeAction(f"ud_claiming_finished: addi {num_ud_claim_finished} {num_ud_claim_finished} {1}")
            if not self.sync_terminate:
                nd_mstr_loop_tran = set_ev_label(nd_mstr_loop_tran, self.ev_word, self.ud_mstr_term_ev_label, "X1")
                nd_mstr_loop_tran.writeAction(f"sendr_wcont {self.ev_word} X2 {self.part_array_ptr} {udid_stride}")
            nd_mstr_loop_tran.writeAction(f"beq {num_ud_claim_finished} {num_ud_worker_active} node_claiming_finished")
            nd_mstr_loop_tran.writeAction(f"yield")

            # If all uds' local work claimed, send to node master
            nd_mstr_loop_tran.writeAction(f"node_claiming_finished: movir {self.scratch[0]} {self._claiming_finish_flag}")
            nd_mstr_loop_tran.writeAction(f"sendr_wcont {self.saved_cont} X2 {self.scratch[0]} X0")
            nd_mstr_loop_tran.writeAction(f"yield")

            if self.sync_terminate:
                # If self._finish_flag is returned, meaning a ud's workers all finished, terminate
                nd_mstr_loop_tran.writeAction(f"ud_finished: subi {num_ud_worker_active} {num_ud_worker_active} {1}")
                nd_mstr_loop_tran = set_ev_label(nd_mstr_loop_tran, self.ev_word, self.ud_mstr_term_ev_label, "X1")
                nd_mstr_loop_tran.writeAction(f"sendr_wcont {self.ev_word} X2 {self.part_array_ptr} {udid_stride}")
                nd_mstr_loop_tran.writeAction(f"blei {num_ud_worker_active} {0} node_finished")
                nd_mstr_loop_tran.writeAction(f"yield")

                # If all uds' workers all finished, send to global master
                nd_mstr_loop_tran.writeAction(f"node_finished: movir {self.scratch[0]} {self._finish_flag}")
                # if 'reducer' in self.lb_type:
                nd_mstr_loop_tran.writeAction(f"sendr_wcont {self.saved_cont} X2 {self.scratch[0]} {self.scratch[0]}")
                nd_mstr_loop_tran.writeAction(f"yield")


        if self.debug_flag:
            nd_mstr_term_tran.writeAction(f"print ' '")
            nd_mstr_term_tran.writeAction(f"print '[DEBUG][NWID %ld][{self.task}] Event <{self.nd_mstr_term_ev_label}> ev_word = %lu income_cont = %lu' {'X0'} {'EQT'} {'X1'}")
            nd_mstr_term_tran.writeAction(f"perflog 1 0 'Node master terminate'")
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
        if self.extension == 'load_balancer' and self.launching_worker:
            num_ln_claim_finished = f"X{GP_REG_BASE+4}"
            num_ln_worker_active  = f"X{GP_REG_BASE+10}"
            ud_mstr_init_tran.writeAction(f"movir {num_ln_worker_active} {0}")
            if 'reducer' in self.lb_type:
                ud_mstr_init_tran.writeAction(f"movir {num_ln_claim_finished} {0}")


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

        # Added by: Jerry Ding
        if self.extension == 'non_load_balancing':
            # If non-lb, calculate how many partitions each lane is assigned
            ud_mstr_init_tran.writeAction(f"div {'X9'} {self.num_child} {self.part_array_stride}")
        else:
            ud_mstr_init_tran.writeAction(f"mov_imm2reg {self.part_array_stride} {WORD_SIZE * self.in_kvset_iter_size}")
        if self.debug_flag:
            ud_mstr_init_tran.writeAction(f"print '[DEBUG][NWID %ld][{self.task}] Init updown master part_array_stride = %ld assigned partition array end address = %ld(0x%x)' \
                {'X0'} {self.part_array_stride} {part_array_end} {part_array_end}")

        # Added by: Jerry Ding
        if self.extension == 'load_balancer' and 'mapper' in self.lb_type and not (self.intra_map_work_stealing or self.global_map_work_stealing):
            ud_mstr_init_tran.writeAction(f"movir {self.scratch[1]} {self.ln_part_start_offset}")
            ud_mstr_init_tran.writeAction(f"add {'X7'} {self.scratch[1]} {self.scratch[1]}")
            ud_mstr_init_tran.writeAction(f"mul {self.num_child} {self.part_array_stride} {self.scratch[0]}")
            ud_mstr_init_tran.writeAction(f"add {self.part_array_ptr} {self.scratch[0]} {self.scratch[0]}")
            ud_mstr_init_tran.writeAction(f"movrl {self.scratch[0]} 0({self.scratch[1]}) 0 {WORD_SIZE}") 
            if self.debug_flag:
                ud_mstr_init_tran.writeAction(f"print 'ud master writing partition pointer %lu(0x%lx) to %lu(0x%lx)' {self.scratch[0]} {self.scratch[0]} {self.scratch[1]} {self.scratch[1]}")
            ud_mstr_init_tran.writeAction(f"movir {self.scratch[1]} {self.ln_part_end_offset}")
            ud_mstr_init_tran.writeAction(f"add {'X7'} {self.scratch[1]} {self.scratch[1]}")
            ud_mstr_init_tran.writeAction(f"movrl {part_array_end} 0({self.scratch[1]}) 0 {WORD_SIZE}") 


        ud_mstr_init_tran.writeAction(f"mov_reg2reg X0 {ln_mstr_nwid}")
        ud_mstr_init_tran = set_ev_label(ud_mstr_init_tran, self.ev_word, self.ln_mstr_init_ev_label, new_thread=True)
        # Create the node master on each node and send out a partition of input kv pairs
        if self.debug_flag:
            ud_mstr_init_tran.writeAction(f"print '[DEBUG][NWID %ld][{self.task}] Before ud_mstr_loop, Start lane %u' \
                {'X0'} {ln_mstr_nwid}")

        if self.intra_map_work_stealing or self.global_map_work_stealing:
            stride = f"X{GP_REG_BASE+4}"
            ud_mstr_init_tran.writeAction(f"div {'X9'} {self.num_child} {stride}")
            ud_mstr_init_tran.writeAction(f"{ud_mstr_loop_label}: ev {self.ev_word} {self.ev_word} {ln_mstr_nwid} {ln_mstr_nwid} 8")
            ud_mstr_init_tran.writeAction(format_pseudo(f"sendr3_wret {self.ev_word} {self.ud_mstr_loop_ev_label} \
                {self.part_array_ptr} {stride} {num_ln_active}", self.scratch[0], self.send_temp_reg_flag))
            if self.debug_flag:
                ud_mstr_init_tran.writeAction(f"print '[DEBUG][NWID %ld][{self.task}] Send partition to lane %ld master part_array_ptr = %ld(0x%lx) num_part_assigned = %ld' \
                    {'X0'} {ln_mstr_nwid} {self.part_array_ptr} {self.part_array_ptr} {num_ln_active}")
            ud_mstr_init_tran.writeAction(f"addi {ln_mstr_nwid} {ln_mstr_nwid} {1}")
            ud_mstr_init_tran.writeAction(f"add {stride} {self.part_array_ptr} {self.part_array_ptr} ")
        else:
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
        if self.extension == 'load_balancer' and self.launching_worker:
            ud_mstr_init_tran.writeAction(f"addi {num_ln_worker_active} {num_ln_worker_active} {1}")
        ud_mstr_init_tran.writeAction(f"blt {num_ln_active} {self.num_child} {ud_mstr_loop_label}")

        if self.intra_map_work_stealing or self.global_map_work_stealing:
            ud_mstr_init_tran.writeAction(f"mul {self.part_array_stride} {self.num_child} {self.part_array_ptr}")
            ud_mstr_init_tran.writeAction(f"add X8 {self.part_array_ptr} {self.part_array_ptr}")

        # if (self.intra_map_work_stealing or self.global_map_work_stealing) and self.extension == 'load_balancer' and 'reducer' in self.lb_type:
        if self.extension == 'load_balancer' and 'reducer' in self.lb_type:
            # ud_mstr_init_tran.writeAction(f"movir {num_ln_claim_finished} {0}")
            ud_mstr_init_tran.writeAction(f"addi {num_ln_worker_active} {num_ln_claim_finished} {0}")

        ud_mstr_init_tran.writeAction(f"mov_imm2reg {self.num_map_gen} 0")
        ud_mstr_init_tran.writeAction(f"addi {num_ln_active} {num_part_assigned} 0")
        if self.debug_flag:
            ud_mstr_init_tran.writeAction(f"print 'ud master init finished, %d lanes active' {num_ln_active}")
        
        
        ud_mstr_init_tran.writeAction("yield")

        '''
        Event:      Updown master loop
        Operands:   X8: Number of map tasks generated
                    X9: Return lane master thread loop event word
        '''
        # Added by: Jerry Ding
        if self.extension == 'load_balancer' and 'reducer' in self.lb_type:
            ud_mstr_loop_tran.writeAction(f"movir {self.scratch[0]} {self._claiming_finish_flag}")
            ud_mstr_loop_tran.writeAction(f"beq X8 {self.scratch[0]} lane_claiming_finished")
            if self.sync_terminate:
                ud_mstr_loop_tran.writeAction(f"beqi X8 {self._finish_flag} lane_finished")

        # ud_mstr_loop_tran.writeAction(f"sri X1 {self.scratch[0]} 32")
        # ud_mstr_loop_tran.writeAction(f"sub {self.scratch[0]} X0 {self.scratch[0]}")
        # ud_mstr_loop_tran.writeAction(f"movir {self.scratch[1]} {0xfffff}")
        # ud_mstr_loop_tran.writeAction(f"and X1 {self.scratch[1]} {self.scratch[1]}")
        # ud_mstr_loop_tran.writeAction(f"print 'Coming from lane %u eventlabel %lu, eventword %lx' {self.scratch[0]} {self.scratch[1]} X1")

        if self.debug_flag:
            ud_mstr_loop_tran.writeAction("print ' '")
            ud_mstr_loop_tran.writeAction(f"rshift {'X1'} {self.scratch[0]} {32}")
            ud_mstr_loop_tran.writeAction(f"print '[DEBUG][NWID %ld][{self.task}] Event <{self.ud_mstr_loop_ev_label}> ev_word = %lu income_cont = %lu. Lane %ld master returns. Number of map generated = %ld' \
                {'X0'} {'EQT'} {'X1'}  {self.scratch[0]} {'X8'}")
        ud_mstr_loop_tran.writeAction(f"add X8 {self.num_map_gen} {self.num_map_gen}")
        ud_mstr_loop_tran.writeAction(f"bge {self.part_array_ptr} {part_array_end} {ud_mstr_fin_fetch_label}")

        if not (self.extension == 'load_balancer' and 'mapper' in self.lb_type):
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
            ud_mstr_loop_tran.writeAction(f"print '[DEBUG][NWID %ld][{self.task}] Updown master part_array_ptr = %lu, part_end = %lu' {'X0'} {self.part_array_ptr} {part_array_end}")
            ud_mstr_loop_tran.writeAction(f"print '[DEBUG][NWID %ld][{self.task}] Updown master num_map_generated = %ld' {'X0'} {self.num_map_gen}")
        ud_mstr_loop_tran.writeAction(f"yield")
        # Finish issuing the assigned input kv set, terminate all the lane master threads
        ud_mstr_loop_tran.writeAction(f"{ud_mstr_fin_fetch_label}: subi {num_ln_active} {num_ln_active} 1")
        if self.debug_flag or self.print_level >= 2:
            ud_mstr_loop_tran.writeAction(f"print '[DEBUG][NWID %ld][{self.task}] Updown master assigned all partitions, number of lane master remains active = %ld' {'X0'} {num_ln_active}")
        # Added by: Jerry Ding
        # if self.extension == 'original' or (self.extension=='load_balancer' and 'reducer_local' in self.lb_type):
        if not self.launching_worker:
            ud_mstr_loop_tran = set_ev_label(ud_mstr_loop_tran, self.ev_word, self.ln_mstr_term_ev_label, "X1")
            ud_mstr_loop_tran.writeAction(f"sendr_wcont {self.ev_word} X2 {self.part_array_ptr} {num_part_assigned}")
            if self.debug_flag:
                ud_mstr_loop_tran.writeAction(f"rshift {'X1'} {self.scratch[0]} {32}")
                ud_mstr_loop_tran.writeAction(f"rshift {'X1'} {self.scratch[1]} {24}")
                ud_mstr_loop_tran.writeAction(f"andi {self.scratch[1]} {self.scratch[1]}  {0xFF}")
                ud_mstr_loop_tran.writeAction(f"print '[DEBUG][NWID %ld][{self.task}] Updown master %ld finishes assign all pairs. Terminates lane %ld master tid %ld, remain_active_lane = %ld' \
                    {'X0'} {'X0'} {self.scratch[0]} {self.scratch[1]} {num_ln_active}")
        elif self.extension == 'load_balancer' and len(self.lb_type) == 1 and 'reducer' in self.lb_type:
            ud_mstr_loop_tran = set_ev_label(ud_mstr_loop_tran, self.ev_word, self.ln_mstr_launch_worker_ev_label, "X1")
            ud_mstr_loop_tran.writeAction(f"sendr_wcont {self.ev_word} X2 {self.scratch[0]} {self.scratch[0]}")
            if self.debug_flag:
                ud_mstr_loop_tran.writeAction(f"rshift {'X1'} {self.scratch[0]} {32}")
                ud_mstr_loop_tran.writeAction(f"rshift {'X1'} {self.scratch[1]} {24}")
                ud_mstr_loop_tran.writeAction(f"andi {self.scratch[1]} {self.scratch[1]}  {0xFF}")
                ud_mstr_loop_tran.writeAction(f"print '[DEBUG][NWID %ld][{self.task}] Updown master %ld finishes assign all pairs. Asking lane %ld master tid %ld to launch workers, remain_active_lane = %ld' \
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

        if self.intra_map_work_stealing:
            ud_mstr_loop_tran.writeAction(f"mov_reg2reg X0 {ln_mstr_nwid}")
            ud_mstr_loop_tran.writeAction(f"movir {self.scratch[0]} {1}")
            ud_mstr_loop_tran = set_ev_label(ud_mstr_loop_tran, self.ev_word, self.ln_receiver_set_terminate_bit_ev_label, new_thread=True)
            ud_mstr_loop_tran = set_ev_label(ud_mstr_loop_tran, self.scratch[1], self.ln_receiver_set_terminate_bit_ret_ev_label, new_thread=True)

            ud_mstr_loop_tran.writeAction(f"{ud_mstr_loop_label}: ev {self.ev_word} {self.ev_word} {ln_mstr_nwid} {ln_mstr_nwid} 8")
            ud_mstr_loop_tran.writeAction(f"sendr_wcont {self.ev_word} {self.scratch[1]} {self.scratch[0]} {self.scratch[0]}")
            ud_mstr_loop_tran.writeAction(f"addi {ln_mstr_nwid} {ln_mstr_nwid} {1}")
            ud_mstr_loop_tran.writeAction(f"addi {num_ln_active} {num_ln_active} 1")
            ud_mstr_loop_tran.writeAction(f"blt {num_ln_active} {self.num_child} {ud_mstr_loop_label}")

        ud_mstr_loop_tran.writeAction(f"yield")

        # Added by: Jerry Ding
        if self.extension == 'load_balancer' and 'reducer' in self.lb_type:
            # If self._claiming_finish_flag is returned, meaning a lane's local keys are all claimed
            ud_mstr_loop_tran.writeAction(f"lane_claiming_finished: subi {num_ln_claim_finished} {num_ln_claim_finished} {1}")
            if self.debug_flag:
                ud_mstr_loop_tran.writeAction(f"sri {'X1'} {self.scratch[0]} {32}")
                # ud_mstr_loop_tran.writeAction(f"sub {num_ln_worker_active} {num_ln_claim_finished} {self.scratch[1]}")
                ud_mstr_loop_tran.writeAction(f"print 'Updown master %d confirmed lane %d claiming finished, %d lane remaining' X0 {self.scratch[0]} {num_ln_claim_finished}")

            if not self.sync_terminate:
                ud_mstr_loop_tran = set_ev_label(ud_mstr_loop_tran, self.ev_word, self.ln_mstr_term_ev_label, "X1")
                if self.debug_flag:
                    ud_mstr_loop_tran.writeAction(f"rshift {'X1'} {self.scratch[0]} {32}")
                    ud_mstr_loop_tran.writeAction(f"rshift {'X1'} {self.scratch[1]} {24}")
                    ud_mstr_loop_tran.writeAction(f"andi {self.scratch[1]} {self.scratch[1]}  {0xFF}")
                    ud_mstr_loop_tran.writeAction(f"print '[LB_DEBUG][NWID %ld][{self.task}] LB terminating lane %ld master tid %ld, %d lane terminated' \
                        {'X0'} {self.scratch[0]} {self.scratch[1]} {num_ln_claim_finished}")
                ud_mstr_loop_tran.writeAction(f"sendr_wcont {self.ev_word} X2 {self.part_array_ptr} {num_part_assigned}")

            # ud_mstr_loop_tran.writeAction(f"beq {num_ln_claim_finished} {num_ln_worker_active} ud_claiming_finished")
            ud_mstr_loop_tran.writeAction(f"blei {num_ln_claim_finished} {0} ud_claiming_finished")
            ud_mstr_loop_tran.writeAction(f"yield")

            # If all lanes' local work claimed, send to node master
            ud_mstr_loop_tran.writeAction(f"ud_claiming_finished: movir {self.scratch[0]} {self._claiming_finish_flag}")
            if self.debug_flag:
                ud_mstr_loop_tran.writeAction(f"print 'ud %u claiming finished' X0")
            ud_mstr_loop_tran.writeAction(f"sendr_wcont {self.saved_cont} X2 {self.scratch[0]} X0")
            ud_mstr_loop_tran.writeAction(f"yield")

            if self.sync_terminate:
                # If self._finish_flag is returned, meaning a lane's workers all finished, terminate
                ud_mstr_loop_tran.writeAction(f"lane_finished: subi {num_ln_worker_active} {num_ln_worker_active} {1}")
                ud_mstr_loop_tran = set_ev_label(ud_mstr_loop_tran, self.ev_word, self.ln_mstr_term_ev_label, "X1")
                if self.debug_flag:
                    ud_mstr_loop_tran.writeAction(f"rshift {'X1'} {self.scratch[0]} {32}")
                    ud_mstr_loop_tran.writeAction(f"rshift {'X1'} {self.scratch[1]} {24}")
                    ud_mstr_loop_tran.writeAction(f"andi {self.scratch[1]} {self.scratch[1]}  {0xFF}")
                    ud_mstr_loop_tran.writeAction(f"print '[LB_DEBUG][NWID %ld][{self.task}] LB terminating lane %ld master tid %ld, %d lane remaining' \
                        {'X0'} {self.scratch[0]} {self.scratch[1]} {num_ln_worker_active}")
                ud_mstr_loop_tran.writeAction(f"sendr_wcont {self.ev_word} X2 {self.part_array_ptr} {num_part_assigned}")
                ud_mstr_loop_tran.writeAction(f"blei {num_ln_worker_active} {0} ud_finished")
                ud_mstr_loop_tran.writeAction(f"yield")

                ud_mstr_loop_tran.writeAction(f"ud_finished: movir {self.scratch[0]} {self._finish_flag}")
                ud_mstr_loop_tran.writeAction(f"sendr_wcont {self.saved_cont} X2 {self.scratch[0]} {self.scratch[0]}")
                if self.debug_flag:
                    ud_mstr_loop_tran.writeAction(f"rshift {self.saved_cont} {self.scratch[0]} {32}")
                    ud_mstr_loop_tran.writeAction(f"rshift {self.saved_cont} {self.scratch[1]} {24}")
                    ud_mstr_loop_tran.writeAction(f"print '[LB_DEBUG][NWID %ld][{self.task}] returning to node master lane %ld master tid %ld' \
                        {'X0'} {self.scratch[0]} {self.scratch[1]} ")
                ud_mstr_loop_tran.writeAction(f"yield")

        if self.debug_flag:
            ud_mstr_term_tran.writeAction(f"print ' '")
            ud_mstr_term_tran.writeAction(f"print '[DEBUG][NWID %ld][{self.task}] Event <{self.ud_mstr_term_ev_label}> ev_word = %lu income_cont = %lu' {'X0'} {'EQT'} {'X1'}")
            ud_mstr_term_tran.writeAction(f"perflog 1 0 'Updown master terminate'")
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
        ln_mstr_init_tran.writeAction(f"addi X1 {self.saved_cont} 0")
        ln_mstr_init_tran.writeAction(f"send_dmlm_ld_wret X8 {self.ln_mstr_rd_part_ev_label} {max(2, self.in_kvset_iter_size)} {self.scratch[0]}")
        # Initialize local counter and event words.
        ln_mstr_init_tran.writeAction(f"movir {num_th_active} 0")
        ln_mstr_init_tran.writeAction(f"movir {max_map_th} {self.max_map_th_per_lane}")
        ln_mstr_init_tran.writeAction(f"mov_imm2reg {self.num_map_gen} 0")

        # Added by: Jerry Ding
        if self.extension == 'non_load_balancing':
            part_start = f"X{GP_REG_BASE + self.in_kvset_iter_size + 7}"
            part_end = f"X{GP_REG_BASE + self.in_kvset_iter_size + 8}"
            ln_mstr_init_tran.writeAction(f"addi {'X8'} {part_start} {self.in_kvset_iter_size * WORD_SIZE}")
            ln_mstr_init_tran.writeAction(f"add {'X8'} {'X9'} {part_end}")

        if self.intra_map_work_stealing or self.global_map_work_stealing:
            ln_mstr_init_tran.writeAction(f"movir {self.scratch[1]} {self.ln_part_start_offset}")
            ln_mstr_init_tran.writeAction(f"add {'X7'} {self.scratch[1]} {self.scratch[1]}")
            ln_mstr_init_tran.writeAction(f"addi {'X8'} {self.scratch[0]} {WORD_SIZE * self.in_kvset_iter_size}")
            ln_mstr_init_tran.writeAction(f"movrl {self.scratch[0]} 0({self.scratch[1]}) 0 {WORD_SIZE}") 
            if self.debug_flag:
                ln_mstr_init_tran.writeAction(f"print 'Lane master writing partition pointer %lu(0x%lx) to %lu(0x%lx)' {self.scratch[0]} {self.scratch[0]} {self.scratch[1]} {self.scratch[1]}")
            ln_mstr_init_tran.writeAction(f"movir {self.scratch[1]} {self.ln_part_end_offset}")
            ln_mstr_init_tran.writeAction(f"add {'X7'} {self.scratch[1]} {self.scratch[1]}")
            ln_mstr_init_tran.writeAction(f"add {'X8'} {'X9'} {self.scratch[0]}")
            ln_mstr_init_tran.writeAction(f"movrl {self.scratch[0]} 0({self.scratch[1]}) 0 {WORD_SIZE}") 

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
        if self.extension == 'load_balancer' and self.launching_worker:
            num_worker_alive = f"X{GP_REG_BASE + self.in_kvset_iter_size + 7}"
            ln_mstr_init_tran.writeAction(f"movir {num_worker_alive} 0")
            if 'mapper' in self.lb_type:
                ln_mstr_init_tran.writeAction(f"movir {self.scratch[0]} {self.ud_mstr_evw_offset}")
                ln_mstr_init_tran.writeAction(f"add {'X7'} {self.scratch[0]} {self.scratch[0]}")
                ln_mstr_init_tran.writeAction(f"movrl {'X1'} 0({self.scratch[0]}) 0 {WORD_SIZE}")
            if 'reducer' in self.lb_type:
                num_worker_claim_finished = f"X{GP_REG_BASE+2}"
                ln_mstr_init_tran.writeAction(f"movir {num_worker_claim_finished} 0")


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
        # if self.extension == 'load_balancer' and self.launching_worker:
        if self.extension == 'load_balancer' and 'mapper' in self.lb_type:
            # If the partition is empty, launch workers
            if self.debug_flag:
                ln_mstr_rd_part_tran.writeAction(f"print 'Lane %lu send to launch worker' X0")
            ln_mstr_rd_part_tran = set_ev_label(ln_mstr_rd_part_tran, self.ev_word, self.ln_mstr_launch_worker_ev_label, "X2", label = empty_part_label)
            ln_mstr_rd_part_tran.writeAction(f"sendr_wcont {self.ev_word} X2 {self.scratch[0]} {self.scratch[0]}")
            # return to updown master
            ln_mstr_rd_part_tran.writeAction(f"{'empty_part_ret_to_ud_mstr'}: sendr_wret {self.saved_cont} {self.ln_mstr_init_ev_label} {self.num_map_gen} {self.num_map_gen} {self.scratch[0]}")
        elif self.extension == 'non_load_balancing':
            # If the partition if empty, check if there is more partitions allocated
            ln_mstr_rd_part_tran.writeAction(f"{empty_part_label}: bge {part_start} {part_end} {'all_partitions_finished'}")
            # If there are unread partitions, read next and update part_start
            ln_mstr_rd_part_tran.writeAction(f"send_dmlm_ld_wret {part_start} {self.ln_mstr_rd_part_ev_label} {max(2, self.in_kvset_iter_size)} {self.scratch[0]}")
            ln_mstr_rd_part_tran.writeAction(f"addi {part_start} {part_start} {WORD_SIZE * self.in_kvset_iter_size}")
            ln_mstr_rd_part_tran.writeAction(f"yield")

            # If no more partitions, return to updown master
            ln_mstr_rd_part_tran.writeAction(f"{'all_partitions_finished'}: movlr 0({num_map_gen_addr}) {self.num_map_gen} 0 8")
            ln_mstr_rd_part_tran.writeAction(f"sendr_wret {self.saved_cont} {self.ln_mstr_init_ev_label} {self.num_map_gen} {self.num_map_gen} {self.scratch[0]}")
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


        # Added by: Jerry Ding
        if self.extension == 'non_load_balancing':
            # If the partition if empty, check if there is more partitions allocated
            ln_mstr_get_ret_tran.writeAction(f"bge {part_start} {part_end} {'all_partitions_finished'}")
            # If there are unread partitions, read next and update part_start
            ln_mstr_get_ret_tran.writeAction(f"send_dmlm_ld_wret {part_start} {self.ln_mstr_rd_part_ev_label} {max(2, self.in_kvset_iter_size)} {self.scratch[0]}")
            ln_mstr_get_ret_tran.writeAction(f"addi {part_start} {part_start} {WORD_SIZE * self.in_kvset_iter_size}")
            ln_mstr_get_ret_tran.writeAction(f"yield")

            # If no more partitions, return to updown master
            ln_mstr_get_ret_tran.writeAction(f"{'all_partitions_finished'}: movlr 0({num_map_gen_addr}) {self.num_map_gen} 0 8")
        else:
            ln_mstr_get_ret_tran.writeAction(f"movlr 0({num_map_gen_addr}) {self.num_map_gen} 0 8")

        ln_mstr_get_ret_tran.writeAction(f"sendr_wret {self.saved_cont} {self.ln_mstr_init_ev_label} {self.num_map_gen} {self.num_map_gen} {self.scratch[0]}")
        if self.debug_flag:
            ln_mstr_get_ret_tran.writeAction(f"rshift {self.saved_cont} {self.scratch[0]} {32}")
            ln_mstr_get_ret_tran.writeAction(f"rshift {'X1'} {self.scratch[1]} {24}")
            ln_mstr_get_ret_tran.writeAction(f"andi {self.scratch[1]} {self.scratch[1]} {0xFF}")
            ln_mstr_get_ret_tran.writeAction(f"print '[DEBUG][NWID %ld][{self.ln_mstr_get_ret_ev_label}] Lane %ld master finishes all pairs assigned, return to updown master %ld tid %ld' \
                {'X0'} {'X0'} {self.scratch[0]} {self.scratch[1]}")
        
        # Added by: Jerry
        if self.extension == 'load_balancer' and 'mapper' in self.lb_type:
            # If the partition is empty, launch workers
            if self.debug_flag:
                ln_mstr_get_ret_tran.writeAction(f"print 'Lane %lu send to launch worker' X0")
            ln_mstr_get_ret_tran = set_ev_label(ln_mstr_get_ret_tran, self.ev_word, self.ln_mstr_launch_worker_ev_label, "X2")
            ln_mstr_get_ret_tran.writeAction(f"sendr_wcont {self.ev_word} X2 {self.scratch[0]} {self.scratch[0]}")

        ln_mstr_get_ret_tran.writeAction(f"{ln_mstr_cont_label}: yield")
        
        '''
        Event:      Main lane master loop. When a map thread finishes the assigned key-value pair, it returns to this event.
        Operands:   X8 ~ Xn: Map thread returned values.
        '''

        # Added by: Jerry Ding
        if self.extension == 'load_balancer' and 'reducer' in self.lb_type:
            if self.debug_flag:
                ln_mstr_loop_tran.writeAction(f"print 'Lane %u master loop receives %ld ' X0 X8")
            ln_mstr_loop_tran.writeAction(f"movir {self.scratch[0]} {self._claiming_finish_flag}")
            ln_mstr_loop_tran.writeAction(f"beq X8 {self.scratch[0]} worker_claiming_finished")
            if self.sync_terminate:
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

        # Added by: Jerry Ding
        if self.extension == 'non_load_balancing':
            # Finish issuing all the assigned input kv set, check if there is more partitions allocated
            ln_mstr_loop_tran.writeAction(f"bge {part_start} {part_end} {'all_partitions_finished'}")
            # If there are unread partitions, read next and update part_start
            ln_mstr_loop_tran.writeAction(f"send_dmlm_ld_wret {part_start} {self.ln_mstr_rd_part_ev_label} {max(2, self.in_kvset_iter_size)} {self.scratch[0]}")
            ln_mstr_loop_tran.writeAction(f"addi {part_start} {part_start} {WORD_SIZE * self.in_kvset_iter_size}")
            ln_mstr_loop_tran.writeAction(f"yield")

            # If no more partitions, return to updown master
            ln_mstr_loop_tran.writeAction(f"{'all_partitions_finished'}: movlr 0({num_map_gen_addr}) {self.num_map_gen} 0 8")
        else:
            ln_mstr_loop_tran.writeAction(f"movlr 0({num_map_gen_addr}) {self.num_map_gen} 0 8")

        # Finish issuing all the assigned input kv set, return to the updown master with the number of map tasks generated
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
        if self.extension == 'load_balancer' and 'mapper' in self.lb_type:
            if self.debug_flag:
                ln_mstr_loop_tran.writeAction(f"print 'Lane %lu send to launch worker' X0")
            ln_mstr_loop_tran = set_ev_label(ln_mstr_loop_tran, self.ev_word, self.ln_mstr_launch_worker_ev_label, "X2")
            ln_mstr_loop_tran.writeAction(f"sendr_wcont {self.ev_word} X2 {self.scratch[0]} {self.scratch[0]}")

        ln_mstr_loop_tran.writeAction(f"{ln_mstr_cont_label}: yield")

        # Added by: Jerry Ding
        if self.extension == 'load_balancer' and 'reducer' in self.lb_type:
            # If self._claiming_finish_flag is returned, meaning a worker's local keys are all claimed
            ln_mstr_loop_tran.writeAction(f"worker_claiming_finished: addi {num_worker_claim_finished} {num_worker_claim_finished} {1}")
            if self.debug_flag:
                ln_mstr_loop_tran.writeAction(f"print 'Lane %d master receives _claiming_finish_flag, num_worker_claim_finished: %ld' X0 {num_worker_claim_finished}")
            ln_mstr_loop_tran.writeAction(f"beq {num_worker_claim_finished} {num_worker_alive} lane_claiming_finished")
            ln_mstr_loop_tran.writeAction(f"yield")

            # If all workers' local work claimed, send to ud master
            ln_mstr_loop_tran.writeAction(f"lane_claiming_finished: movir {self.scratch[0]} {self._claiming_finish_flag}")
            ln_mstr_loop_tran.writeAction(f"sendr_wcont {self.saved_cont} X2 {self.scratch[0]} X0")
            if self.debug_flag:
                ln_mstr_loop_tran.writeAction(f"print 'Lane %d workers claiming finished, send to ud master with ev_word %lx' X0 {self.saved_cont}")
            ln_mstr_loop_tran.writeAction(f"yield")

            if self.sync_terminate:
                # If self._finish_flag is returned, meaning a worker has finished
                ln_mstr_loop_tran.writeAction(f"worker_finished: subi {num_worker_alive} {num_worker_alive} {1}")
                ln_mstr_loop_tran.writeAction(f"beqi {num_worker_alive} 0 lane_finished")
                ln_mstr_loop_tran.writeAction(f"yield")

                # If all worker finished, notify ud master
                ln_mstr_loop_tran.writeAction(f"lane_finished: movir {self.scratch[0]} {self._finish_flag}")
                if self.debug_flag:
                    ln_mstr_loop_tran.writeAction(f"print 'Lane %u master receives finish flag' X0")
                ln_mstr_loop_tran.writeAction(f"sendr_wcont {self.saved_cont} X2 {self.scratch[0]} X0")
                ln_mstr_loop_tran.writeAction(f"yield")


        if self.debug_flag:
            ln_mstr_term_tran.writeAction(f"print ' '")
            ln_mstr_term_tran.writeAction(f"print '[DEBUG][NWID %ld][{self.ln_mstr_term_ev_label}] Event <{self.ln_mstr_term_ev_label}> ev_word = %lu income_cont = %lu' {'X0'} {'EQT'} {'X1'}")
            ln_mstr_term_tran.writeAction(f"perflog 1 0 'Lane master terminate'")
        ln_mstr_term_tran.writeAction(f"yield_terminate")



        if self.extension == 'load_balancer' and self.launching_worker:
            ln_mstr_launch_worker_tran   = self.state.writeTransition("eventCarry", self.state, self.state, self.ln_mstr_launch_worker_ev_label)

            if self.enable_mr_barrier and not ('mapper' in self.lb_type):
                # Wait for all mappers finish
                if self.debug_flag:
                    ln_mstr_launch_worker_tran.writeAction(f"print 'Lane %lu launching worker' X0")
                ln_mstr_launch_worker_tran.writeAction(f"movir {self.scratch[1]} {self.terminate_bit_offset}")
                ln_mstr_launch_worker_tran.writeAction(f"add {'X7'} {self.scratch[1]} {self.scratch[1]}")
                ln_mstr_launch_worker_tran.writeAction(f"movlr 0({self.scratch[1]}) {self.scratch[0]} 0 {WORD_SIZE}")
                ln_mstr_launch_worker_tran.writeAction(f"bgei {self.scratch[0]} {0} prepare_launch_workers")
                ln_mstr_launch_worker_tran.writeAction(f"sendr_wcont X2 X1 {self.scratch[0]} {self.scratch[0]}")
                ln_mstr_launch_worker_tran.writeAction(f"yield")


            ln_mstr_launch_worker_tran.writeAction(f"prepare_launch_workers: evii {self.ev_word} {self.ln_worker_init_ev_label} {255} {5}")
            ln_mstr_launch_worker_tran.writeAction(f"movir {self.scratch[0]} {self._worker_start_flag}")
            if self.debug_flag:
                ln_mstr_launch_worker_tran.writeAction(f"print 'Lane %lu launching worker' X0")
            ln_mstr_launch_worker_tran.writeAction(f"launch_workers: bgei {num_worker_alive} {self.max_worker_th_per_lane} {ln_mstr_cont_label}")
            ln_mstr_launch_worker_tran.writeAction(f"sendr_wret {self.ev_word} {self.ln_mstr_loop_ev_label} {self.scratch[0]} {self.scratch[0]} {self.scratch[1]}")
            ln_mstr_launch_worker_tran.writeAction(f"addi {num_worker_alive} {num_worker_alive} {1}")
            ln_mstr_launch_worker_tran.writeAction(f"jmp launch_workers")

            if 'mapper' in self.lb_type and 'reducer' not in self.lb_type:
                ln_mstr_launch_worker_tran.writeAction(f"{ln_mstr_cont_label}: yieldt")
            else:
                ln_mstr_launch_worker_tran.writeAction(f"{ln_mstr_cont_label}: yield")


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

        inter_key       = "X8"
        inter_values    = [f"X{OB_REG_BASE + n + 1}" for n in range((self.inter_kvset.value_size))]
        num_lanes_mask  = f"X{GP_REG_BASE+7}"
        dest_nwid       = f"X{GP_REG_BASE+8}"
        metadata_base   = f"X{GP_REG_BASE+9}"
        base_lane       = f"X{GP_REG_BASE+10}"
        cont_word       = f"X{GP_REG_BASE+11}"
        ev_word         = f"X{GP_REG_BASE+14}"
        
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
                                    f" [{' '.join([ f'%ld' for _ in range(min((self.inter_kvpair_size) - 1,5))])}] to lane %ld' {'X0'} {inter_key} {' '.join(inter_values[:4])} {dest_nwid}")

        # Added by: Jerry Ding
        if self.extension == 'load_balancer' and 'reducer' in self.lb_type:
            set_ev_label(map_emit_tran, ev_word, self.ln_receiver_receive_kv_ev_label, new_thread = True)
            map_emit_tran.writeAction(f"addi {'X2'} {cont_word} {0}")
        else:
            set_ev_label(map_emit_tran, ev_word, self.kv_reduce_init_ev_label, new_thread = True)
            set_ev_label(map_emit_tran, cont_word, self.kv_reduce_ret_ev_label, new_thread = True)

        if self.extension == 'load_balancer':
            if 'reducer_local' in self.lb_type or ('reducer' in self.lb_type and self.grlb_type == 'ud'):
                # Set send_policy to send_to_shortest
                map_emit_tran.writeAction(f"movir {self.scratch[0]} {1}")
                map_emit_tran.writeAction(f"sli {self.scratch[0]} {self.scratch[0]} {27}")
                map_emit_tran.writeAction(f"or {self.scratch[0]} {dest_nwid} {dest_nwid}")

        map_emit_tran.writeAction(f"ev {ev_word}  {ev_word}  {dest_nwid} {dest_nwid} 8")
        map_emit_tran.writeAction(f"sendops_wcont {ev_word} {cont_word} {inter_key} {self.inter_kvpair_size}")
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
        kv_reduce_init_tran.writeAction(f"movlr {self.num_reduce_th_offset - self.metadata_offset}({lm_base_reg}) {temp_value} 0 8")
        kv_reduce_init_tran.writeAction(f"move {self.max_red_th_offset - self.metadata_offset}({lm_base_reg}) {self.scratch[1]} 0 8")
        kv_reduce_init_tran.writeAction(f"bge {temp_value} {self.scratch[1]} {max_th_label}")
        kv_reduce_init_tran.writeAction(f"addi {temp_value} {temp_value} 1")
        kv_reduce_init_tran.writeAction(f"move {temp_value}  {self.num_reduce_th_offset - self.metadata_offset}({lm_base_reg}) 0 8")
        
        # Send the intermediate key-value pair to kv_reduce 
        kv_reduce_init_tran = set_ev_label(kv_reduce_init_tran, self.ev_word, self.kv_reduce_ev_label)
        if self.debug_flag and self.print_level > 2:
            kv_reduce_init_tran.writeAction(f"print '[DEBUG][NWID %ld][{self.task}] Send intermediate key value pair to kv_reduce: key = %ld values = " + 
                                            f"[{' '.join(['%ld' for _ in range(self.inter_kvpair_size - 1)])}]' {'X0'} {inter_key} {' '.join(inter_values)}")
        if self.extension == 'load_balancer' and ('reducer' in self.lb_type or 'reducer_local' in self.lb_type):
            if 'reducer' in self.lb_type:
                kv_reduce_init_tran.writeAction(f"sendops_wcont {self.ev_word} {'X1'} {inter_key} {self.inter_kvpair_size}")
            if 'reducer_local' in self.lb_type:
                kv_reduce_init_tran.writeAction(f"ev {self.ev_word} {self.ev_word} X0 X0 8")
                kv_reduce_init_tran.writeAction(f"ev {self.ev_word} {self.scratch[1]} X0 X0 8")
                kv_reduce_init_tran.writeAction(f"evlb {self.scratch[1]} {self.kv_reduce_ret_ev_label}")
                kv_reduce_init_tran.writeAction(f"sendops_wcont {self.ev_word} {self.scratch[1]} {inter_key} {self.inter_kvpair_size}")
        else:
            kv_reduce_init_tran.writeAction(f"sendops_wret {self.ev_word} {self.kv_reduce_ret_ev_label} {inter_key} {self.inter_kvpair_size} {self.scratch[0]}")
        kv_reduce_init_tran.writeAction(f"yield")

        # Reach maximum parallelism push the intermediate key-value pair to the queue
        kv_reduce_init_tran.writeAction(f"{max_th_label}: ev_update_1 EQT {self.ev_word} {NEW_THREAD_ID} {0b0100}")
        if self.debug_flag and self.print_level > 2:
            kv_reduce_init_tran.writeAction(f"print '[DEBUG][NWID %ld][{self.task}] Lane %ld has %ld reduce thread active, " + 
                                            f"reaches max reduce threads, pushed back to queue.' {'X0'} {'X0'} {temp_value}")
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
        # kv_reduce_ret_tran.writeAction(f"print 'reduced'")

        # Decrement the number of active reduce threads
        kv_reduce_ret_tran.writeAction(f"move {self.num_reduce_th_offset - self.metadata_offset}({lm_base_reg}) {temp_value} 0 8")
        kv_reduce_ret_tran.writeAction(f"subi {temp_value} {temp_value} 1")
        kv_reduce_ret_tran.writeAction(f"move {temp_value}  {self.num_reduce_th_offset - self.metadata_offset}({lm_base_reg}) 0 8")
        if self.debug_flag and self.print_level > 2:
            kv_reduce_ret_tran.writeAction(f"print '[DEBUG][NWID %ld][{self.task}] Lane %ld has %ld reduce thread remain active' {'X0'} {'X0'} {temp_value}")

        # Added by: Jerry Ding
        if self.extension == 'load_balancer' and 'reducer' in self.lb_type:
            # # If Eventword != Contword: reducer launched from worker
            # # return to contral to worker
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
        tran.writeAction(f"and {dest_id} {num_lanes_mask} {dest_id}")
        tran.writeAction(f"add {dest_id} {base_lane} {dest_id}")

        # tran.writeAction(f"and {key} {num_lanes_mask} {dest_id}")

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


    def get_entry_lock(self, tran, lock_offset, scratch):
        # Grab lock for this entry
        tran.writeAction(f"movir {scratch[1]} {-1}")
        tran.writeAction(f"get_lock: cswp {lock_offset} {scratch[0]} {scratch[1]} {'X0'}")
        if self.debug_flag:
            tran.writeAction(f"print 'Lane %u trying to get lock at %lu, reads %lu' X0 {lock_offset} {scratch[0]}")
        tran.writeAction(f"bnei {scratch[0]} {-1} get_lock")
        return

    def get_entry_lock_w_label(self, tran, lock_offset, entry_label, exit_label, scratch):
        entry_label += ":" if entry_label else ""
        tran.writeAction(f"{entry_label} movir {scratch[1]} {-1}")
        tran.writeAction(f"cswp {lock_offset} {scratch[0]} {scratch[1]} {'X0'}")
        if self.debug_flag:
            tran.writeAction(f"print 'Lane %u trying to get lock at %lu, reads %lu' X0 {lock_offset} {scratch[0]}")
        tran.writeAction(f"bnei {scratch[0]} {-1} {exit_label}")
        return

    def release_entry_lock(self, tran, key_offset, scratch, label=''):
        if label:
            tran.writeAction(f"{label}: movir {scratch[0]} {-1}")
        else:
            tran.writeAction(f"movir {scratch[0]} {-1}")
        tran.writeAction(f"movrl {scratch[0]} {self.cache_entry_bsize}({key_offset}) 0 {WORD_SIZE}")
        if self.debug_flag:
            tran.writeAction(f"addi {key_offset} {scratch[0]} {self.cache_entry_bsize}")
            tran.writeAction(f"print 'Lane %u releasing lock at %lu' X0 {scratch[0]} {key_offset}")
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
        # nwid        = regs[8+self.cache_entry_size]
        nwid        = 'X0'

        hit_label   = "cache_hit"
        evict_label = "cache_evict"
        continue_label  = "contiue"
        get_fail_label  = "get_fail"
        skip_flush_label = "skip_flush"
        th_avail_label  = "thread_available"

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
            combine_tran.writeAction(f"perflog 1 0 'Lane %lu, nwid in X2 %lx, Combine key = %ld' X0 X2 X8")
        # check if the local scratchpad stores a pending update to the same key or a copy of the newest output kvpair with that key.
        # combine_tran.writeAction(f"movir {key_offset} 0")
        # combine_tran.writeAction(f"hash {key} {key_offset}")

        if self.extension == 'load_balancer' and 'reducer_local' in self.lb_type:

            # Get start address of the cache lane
            combine_tran.writeAction(f"movir {scratch[1]} {1<<19}")
            combine_tran.writeAction(f"slsubii {scratch[1]} {scratch[1]} {8} {1}")
            combine_tran.writeAction(f"srandi {'X2'} {scratch[1]} {32}")
            combine_tran.writeAction(f"sub {scratch[1]} {'X0'} {scratch[0]}")
            combine_tran.writeAction(f"sli {scratch[0]} {scratch[0]} {int(log2(SPD_BANK_SIZE))}")
            combine_tran.writeAction(f"add {'X7'} {scratch[0]} {scratch[0]}")

            if self.power_of_two_cache_size:
                combine_tran.writeAction(f"andi {key} {key_mask} {self.cache_size - 1}")
            else:
                combine_tran.writeAction(f"movir {key_mask} {self.cache_size}")
                combine_tran.writeAction(f"mod {key} {key_mask} {key_mask}")

            # # Hash key for entry address
            # # combine_tran.writeAction(f"sri {'X2'} {key_mask} {32}")
            # # combine_tran.writeAction(f"addi {key} {key_mask} 0")
            # combine_tran.writeAction(f"movir {key_mask} {self.cache_size << 6}")
            # combine_tran.writeAction(f"hash {key} {key_mask}")
            # combine_tran.writeAction(f"sri {key_mask} {key_mask} {1}")
            # combine_tran.writeAction(f"movir {scratch[0]} {self.cache_size << 6}")
            # combine_tran.writeAction(f"mod {key_mask} {scratch[0]} {key_mask}")

            # # Get ud id on whose spd the key is cached
            # combine_tran.writeAction(f"movir {scratch[0]} {self.cache_size}")
            # combine_tran.writeAction(f"div {key_mask} {scratch[0]} {scratch[1]}")

            # # Get cache entry index on that lane
            # combine_tran.writeAction(f"mod {key_mask} {scratch[0]} {key_mask}")

            # # Get start address of the cache lane
            # combine_tran.writeAction(f"andi {'X0'} {scratch[0]} {63}")
            # combine_tran.writeAction(f"sub {scratch[1]} {scratch[0]} {scratch[0]}")
            # combine_tran.writeAction(f"print 'lane %u, dest %lu, diff %ld' X0 {scratch[1]} {scratch[0]}")
            # combine_tran.writeAction(f"sli {scratch[0]} {scratch[0]} {int(log2(SPD_BANK_SIZE))}")
            # combine_tran.writeAction(f"add {'X7'} {scratch[0]} {scratch[0]}")

            # Get address of cache entry
            combine_tran.writeAction(f"muli {key_mask} {key_offset} {self.cache_entry_bsize + WORD_SIZE}")
            combine_tran.writeAction(f"add {scratch[0]} {key_offset} {key_offset}")

            if self.cache_offset >> 15 > 0:
                combine_tran.writeAction(f"movir {scratch[0]} {self.cache_offset}")
                combine_tran.writeAction(f"add {key_offset} {scratch[0]} {key_offset}")
            else:
                combine_tran.writeAction(f"addi {key_offset} {key_offset} {self.cache_offset}")

            combine_tran.writeAction(f"movir {key_mask} {1}")
            combine_tran.writeAction(f"sli {key_mask} {key_mask} {self.INACTIVE_MASK_SHIFT}")

            combine_tran.writeAction(f"read_key: movlr {0}({key_offset}) {cached_key} 0 8")

        else:
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

        if not (self.extension == 'load_balancer' and 'reducer_local' in self.lb_type):
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
        combine_tran.writeAction(f"evi {'X2'} {scratch[0]} 255 {0b0100}")
        combine_tran.writeAction(f"sendops_wcont {scratch[0]} {'X1'} {key} {self.cache_entry_size}")

        # if self.extension == 'load_balancer' and 'reducer_local' in self.lb_type:
        #     self.release_entry_lock(combine_tran, key_offset, scratch)
        combine_tran.writeAction("yieldt")



        ##### HIT branch
        if self.extension == 'load_balancer' and 'reducer_local' in self.lb_type:
            combine_tran.writeAction(f"{hit_label}: addi {key_offset} {buffer_addr} {self.cache_entry_bsize}")
            # combine_tran.writeAction(f"movlr {0}({key_offset}) {scratch[0]} 0 8")
            # combine_tran.writeAction(f"bne {cached_key} {scratch[0]} read_key")
            self.get_entry_lock_w_label(combine_tran, buffer_addr, '', 'read_key', scratch)

            combine_tran.writeAction(f"move {WORD_SIZE}({key_offset}) {cached_values[0]} 0 8")

        else:
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
        if self.extension == 'load_balancer' and 'reducer_local' in self.lb_type:
            # Release lock after writing
            self.release_entry_lock(combine_tran, key_offset, scratch)
        if self.debug_flag and self.print_level > 2:
            combine_tran.writeAction(f"print '[DEBUG][NWID %ld][{self.kv_combine_ev_label}] Combine key = %ld, result values = " + 
                                     f"[{' '.join(['%ld' for _ in range(self.cache_entry_size - 1)])}]' {'X0'} {key} {' '.join(result_regs)}")
        combine_tran.writeAction(f"sendr_wcont {'X1'} {'X2'} {key} {cached_key} ")

        # Increment the number of reduce tasks processed
        if self.metadata_offset >> 15 > 0:
            combine_tran.writeAction(f"movir {buffer_addr} {self.metadata_offset}")
            combine_tran.writeAction(f"add {'X7'} {buffer_addr} {buffer_addr}")
        else:
            combine_tran.writeAction(f"addi {'X7'} {buffer_addr} {self.metadata_offset}")
        combine_tran.writeAction(f"move {self.reduce_ctr_offset - self.metadata_offset}({buffer_addr}) {scratch[0]} 0 8")
        combine_tran.writeAction(f"addi {scratch[0]} {scratch[0]} 1")
        combine_tran.writeAction(f"move {scratch[0]} {self.reduce_ctr_offset - self.metadata_offset}({buffer_addr}) 0 8")
        if self.debug_flag and self.print_level > 2:
            combine_tran.writeAction(f"print '[DEBUG][NWID %ld][{self.task}] Lane %ld processed %ld reduce tasks' {'X0'} {'X0'} {scratch[0]}")
        # combine_tran.writeAction(f"perflog 1 0 '%u' X0")
        combine_tran.writeAction(f"yieldt")
        

        ##### CACHE MISS branch




        # Cache miss and current entry can be evited. Check if there's thread available. 
        if self.metadata_offset >> 15 > 0:
            combine_tran.writeAction(f"{evict_label}: movir {buffer_addr} {self.metadata_offset}")
            combine_tran.writeAction(f"add {'X7'} {buffer_addr} {buffer_addr}")
        else:
            combine_tran.writeAction(f"{evict_label}: addi {'X7'} {buffer_addr} {self.metadata_offset}")
        combine_tran.writeAction(f"move {self.num_reduce_th_offset - self.metadata_offset}({buffer_addr}) {scratch[0]} 0 8")
        combine_tran.writeAction(f"move {self.max_red_th_offset - self.metadata_offset}({buffer_addr}) {scratch[1]} 0 8")
        combine_tran.writeAction(f"bgt {scratch[1]} {scratch[0]} {th_avail_label}")

        # if self.extension == 'load_balancer' and 'reducer_local' in self.lb_type:
        #     # Release lock if no thread available
        #     self.release_entry_lock(combine_tran, key_offset, scratch)
        
        if self.debug_flag and self.print_level > 2:
            combine_tran.writeAction(f"print '[DEBUG][NWID %ld][{self.kv_combine_ev_label}] Reach max reduce thread %ld, push back to queue key = %ld " +
                                        f"values = [{''.join(['%ld, ' for _ in range(self.cache_entry_size - 1)])}]' {'X0'} {scratch[1]} {key} {' '.join(values)}")
        combine_tran.writeAction(f"evi {'X2'} {scratch[0]} 255 {0b0100}")
        combine_tran.writeAction(f"sendops_wcont {scratch[0]} {'X1'} {key} {self.cache_entry_size}")
        combine_tran.writeAction(f"yieldt")
        
        combine_tran.writeAction(f"{th_avail_label}: addi {scratch[0]} {scratch[0]} 1")

        if self.extension == 'load_balancer' and 'reducer_local' in self.lb_type:
            combine_tran.writeAction(f"movlr {0}({key_offset}) {scratch[0]} 0 8")
            combine_tran.writeAction(f"bne {cached_key} {scratch[0]} read_key")
            combine_tran.writeAction(f"addi {key_offset} {buffer_addr} {self.cache_entry_bsize}")
            self.get_entry_lock_w_label(combine_tran, buffer_addr, '', 'read_key', scratch)
            if self.metadata_offset >> 15 > 0:
                combine_tran.writeAction(f"movir {buffer_addr} {self.metadata_offset}")
                combine_tran.writeAction(f"add {'X7'} {buffer_addr} {buffer_addr}")
            else:
                combine_tran.writeAction(f"addi {'X7'} {buffer_addr} {self.metadata_offset}")
            combine_tran.writeAction(f"move {self.num_reduce_th_offset - self.metadata_offset}({buffer_addr}) {scratch[0]} 0 8")

        combine_tran.writeAction(f"move {scratch[0]}  {self.num_reduce_th_offset - self.metadata_offset}({buffer_addr}) 0 8")

        # Current entry can be evited. Store the dirty entry and insert the new entry.
        combine_tran.writeAction(f"movrl {key} {0}({key_offset}) 1 8")
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

        if self.extension == 'load_balancer' and 'reducer_local' in self.lb_type:
            combine_tran.writeAction(f"ev {temp_evw} {temp_evw} {nwid} {nwid} {0b1000}")
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

        if self.extension == 'load_balancer' and 'reducer_local' in self.lb_type:
            # Store the incoming key-value pair to the cache
            for i in range(self.cache_entry_size - 1):
                combine_tran.writeAction(f"move {values[i]} {WORD_SIZE * i}({key_offset}) 0 8")
            # Release lock after writing
            combine_tran.writeAction(f"subi {key_offset} {scratch[1]} {WORD_SIZE}")
            self.release_entry_lock(combine_tran, scratch[1], scratch)

            combine_tran.writeAction(f"ev {temp_evw} {temp_evw} {nwid} {nwid} {0b1000}")

        self.out_kvset.get_pair(combine_tran, temp_evw, key, scratch)
        if self.debug_flag:
            combine_tran.writeAction(f"print '[DEBUG][NWID %ld][{self.kv_combine_ev_label}] Get pair key = %ld from output key value set' {'X0'} {key}")
        
        if not (self.extension == 'load_balancer' and 'reducer_local' in self.lb_type):
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
        
        if self.extension == 'load_balancer' and 'reducer_local' in self.lb_type:
            # Grab lock for this entry before reading
            combine_get_tran.writeAction(f"addi {key_offset} {key_mask} {self.cache_entry_bsize - WORD_SIZE}")
            self.get_entry_lock(combine_get_tran, key_mask, scratch)

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
        if self.extension == 'load_balancer' and 'reducer_local' in self.lb_type:
            # Release lock after writing
            combine_get_tran.writeAction(f"subi {key_offset} {scratch[1]} {WORD_SIZE}")
            self.release_entry_lock(combine_get_tran, scratch[1], scratch)
        if self.debug_flag and self.print_level > 3:
            combine_get_tran.writeAction(f"sli {cached_key} {scratch[0]} {1}")
            combine_get_tran.writeAction(f"sri {scratch[0]} {scratch[0]} {1}")
            combine_get_tran.writeAction(f"print '[DEBUG][NWID %ld][{self.combine_get_ev_label}] Finish write back store key = %ld (masked = %lu) " + 
                                         f"to lm addr = 0x%lx' {'X0'} {cached_key} {scratch[0]} {key_offset}")
        # combine_get_tran.writeAction(f"movir {temp_evw} {-1}")
        # combine_get_tran.writeAction(f"sri {temp_evw} {temp_evw} {1}")
        combine_get_tran.writeAction(f"sendr_wcont {saved_cont} {'X2'} {'X2'} {cached_key} ")
        if self.metadata_offset >> 15 > 0:
            combine_get_tran.writeAction(f"movir {buffer_addr} {self.metadata_offset}")
            combine_get_tran.writeAction(f"add {'X7'} {buffer_addr} {buffer_addr}")
        else:
            combine_get_tran.writeAction(f"addi {'X7'} {buffer_addr} {self.metadata_offset}")
        combine_get_tran.writeAction(f"move {self.num_reduce_th_offset - self.metadata_offset}({buffer_addr}) {scratch[0]}  0 8")
        combine_get_tran.writeAction(f"subi {scratch[0]} {scratch[0]} 1")
        combine_get_tran.writeAction(f"move {scratch[0]}  {self.num_reduce_th_offset - self.metadata_offset}({buffer_addr}) 0 8")
        # Increment the number of reduce tasks processed
        combine_get_tran.writeAction(f"move {self.reduce_ctr_offset - self.metadata_offset}({buffer_addr}) {scratch[0]} 0 8")
        combine_get_tran.writeAction(f"addi {scratch[0]} {scratch[0]} 1")
        combine_get_tran.writeAction(f"move {scratch[0]} {self.reduce_ctr_offset - self.metadata_offset}({buffer_addr}) 0 8")
        if self.debug_flag and self.print_level > 2:
            combine_get_tran.writeAction(f"print '[DEBUG][NWID %ld][{self.task}] Lane %ld processed %ld reduce tasks' {'X0'} {'X0'} {scratch[0]}")
        # combine_get_tran.writeAction(f"perflog 1 0 '%u' X0")
        combine_get_tran.writeAction(f"yieldt")

        if self.extension == 'load_balancer' and 'reducer_local' in self.lb_type:
            combine_get_tran.writeAction(f"{continue_label}: subi {key_offset} {scratch[1]} {WORD_SIZE}")
            self.release_entry_lock(combine_get_tran, scratch[1], scratch)
            combine_get_tran.writeAction(f"yield")
        else:
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

        # if self.extension == 'load_balancer' and 'reducer_local' in self.lb_type:
        #     # Grab lock for this entry before reading
        #     combine_put_ack_tran.writeAction(f"addi {key_offset} {key_mask} {self.cache_entry_bsize - WORD_SIZE}")
        #     self.get_entry_lock(combine_put_ack_tran, key_mask, scratch)
        combine_put_ack_tran.writeAction(f"movir {key_mask} {1}")
        combine_put_ack_tran.writeAction(f"sli {key_mask} {key_mask} {self.INACTIVE_MASK_SHIFT}")
        combine_put_ack_tran.writeAction(f"or {key_mask} {cached_key} {cached_key}")
        combine_put_ack_tran.writeAction(f"movrl {cached_key} {0 - WORD_SIZE}({key_offset}) 0 8")    # flip the highest bit indicating the value is written back

        # if self.extension == 'load_balancer' and 'reducer_local' in self.lb_type:
        #     # Release lock after writing
        #     combine_put_ack_tran.writeAction(f"subi {key_offset} {scratch[1]} {WORD_SIZE}")
        #     self.release_entry_lock(combine_put_ack_tran, scratch[1], scratch)
        
        if self.debug_flag and self.print_level > 4:
            combine_put_ack_tran.writeAction(f"sli {cached_key} {scratch[0]} {1}")
            combine_put_ack_tran.writeAction(f"sri {scratch[0]} {scratch[0]} {1}")
            combine_put_ack_tran.writeAction(f"print '[DEBUG][NWID %ld][{self.combine_get_ev_label}] Store masked key = %lu (key = %ld) to addr = 0x%lx' {'X0'} {cached_key} {scratch[0]} {key_offset}")
        # combine_put_ack_tran.writeAction(f"movir {temp_evw} {-1}")
        # combine_put_ack_tran.writeAction(f"sri {temp_evw} {temp_evw} {1}")
        combine_put_ack_tran.writeAction(f"sendr_wcont {saved_cont} {'X2'} {'X2'} {cached_key} ")
        # combine_put_ack_tran.writeAction(f"yieldt")
        if self.metadata_offset >> 15 > 0:
            combine_put_ack_tran.writeAction(f"movir {buffer_addr} {self.metadata_offset}")
            combine_put_ack_tran.writeAction(f"add {'X7'} {buffer_addr} {buffer_addr}")
        else:
            combine_put_ack_tran.writeAction(f"addi {'X7'} {buffer_addr} {self.metadata_offset}")
        combine_put_ack_tran.writeAction(f"move {self.num_reduce_th_offset - self.metadata_offset}({buffer_addr}) {scratch[0]}  0 8")
        combine_put_ack_tran.writeAction(f"subi {scratch[0]} {scratch[0]} 1")
        combine_put_ack_tran.writeAction(f"move {scratch[0]}  {self.num_reduce_th_offset - self.metadata_offset}({buffer_addr}) 0 8")
        # Increment the number of reduce tasks processed
        combine_put_ack_tran.writeAction(f"move {self.reduce_ctr_offset - self.metadata_offset}({buffer_addr}) {scratch[0]} 0 8")
        combine_put_ack_tran.writeAction(f"addi {scratch[0]} {scratch[0]} 1")
        combine_put_ack_tran.writeAction(f"move {scratch[0]} {self.reduce_ctr_offset - self.metadata_offset}({buffer_addr}) 0 8")
        if self.debug_flag and self.print_level > 2:
            combine_put_ack_tran.writeAction(f"print '[DEBUG][NWID %ld][{self.task}] Lane %ld processed %ld reduce tasks' {'X0'} {'X0'} {scratch[0]}")
        # combine_put_ack_tran.writeAction(f"perflog 1 0 '%u' X0")
        combine_put_ack_tran.writeAction(f"yieldt")
        combine_put_ack_tran.writeAction(f"{continue_label}: yield")
        
        '''
        Event:      Dummy return event. 
        '''
        kv_reduce_ret_tran  = self.state.writeTransition("eventCarry", self.state, self.state, self.kv_reduce_ret_ev_label)

        if self.extension == 'load_balancer' and 'reducer' in self.lb_type:
            kv_reduce_ret_tran.writeAction(f"sendr_reply {self.scratch[0]} {self.scratch[0]} {self.scratch[0]}")
        kv_reduce_ret_tran.writeAction(f"yieldt")

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
        if self.extension == 'load_balancer' and 'reducer_local' in self.lb_type:
            ln_flush_tran.writeAction(f"muli {cache_bound} {cache_bound} {self.cache_entry_bsize + WORD_SIZE}")
        else:
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
        if self.extension == 'load_balancer' and 'reducer_local' in self.lb_type:
            combine_tran.writeAction(f"ev {temp_evw} {temp_evw} {nwid} {nwid} {0b1000}")
        self.out_kvset.flush_pair(ln_flush_tran, ack_evw, temp_key, cache_offset, buffer_addr, counter, scratch)
        # ln_flush_tran.writeAction(f"addi {counter} {counter} 1")
        if self.extension == 'load_balancer' and 'reducer_local' in self.lb_type:
            ln_flush_tran.writeAction(f"addi {cache_offset} {cache_offset} {WORD_SIZE}")
        ln_flush_tran.writeAction(f"jmp {flush_loop_label}")
        if self.extension == 'load_balancer' and 'reducer_local' in self.lb_type:
            ln_flush_tran.writeAction(f"{continue_label}: addi {cache_offset} {cache_offset} {self.cache_entry_bsize + WORD_SIZE}")
        else:
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
    Worker thread
    '''

    '''
    claiming_work register:
                    # -1: Executing local map
                    # 0:  Local maps finished, claiming local reduces
                    # 1:  Local reduce resolved, claiming remote reduce
                    # 2:  All local reduces have been claimed and executed, claiming remote work

                    -1: Executing local map
                    0:  Local maps finished, claiming local reduces
                    1:  All map finishes, checking local reduce finish
                    2:  Local reduces finished
                    3:  Local reduces have been executed, check terminating condition
        claimed_success register:
                    0:  Last claim is unsuccessful, need to update claim_work_dest_nwid
                    1:  Succeessfully claimed from current claim_work_dest_nwid, no need to update
    '''

    def __gen_worker(self):

        ln_worker_init_tran = self.state.writeTransition("eventCarry", self.state, self.state, self.ln_worker_init_ev_label)
        ln_worker_work_tran = self.state.writeTransition("eventCarry", self.state, self.state, self.ln_worker_work_ev_label)
        ln_worker_claim_local_tran = self.state.writeTransition("eventCarry", self.state, self.state, self.ln_worker_claim_local_ev_label)
        ln_worker_claim_remote_tran = self.state.writeTransition("eventCarry", self.state, self.state, self.ln_worker_claim_remote_ev_label)
        ln_worker_helper_tran = self.state.writeTransition("eventCarry", self.state, self.state, self.ln_worker_helper_ev_label)
        
        self.__gen_worker_init(ln_worker_init_tran)
        self.__gen_worker_work(ln_worker_work_tran)
        self.__gen_worker_claim_local_work(ln_worker_claim_local_tran)
        if self.intra_map_work_stealing:
            self.__gen_worker_claim_remote_work_local_mapper_ws(ln_worker_claim_remote_tran)
        else:
            self.__gen_worker_claim_remote_work(ln_worker_claim_remote_tran)
        self.__gen_worker_helper(ln_worker_helper_tran)
        

        if 'mapper' in self.lb_type:
            ln_worker_claimed_map_tran = self.state.writeTransition("eventCarry", self.state, self.state, self.ln_worker_claimed_map_ev_label)

            self.__gen_worker_claimed_map_task(ln_worker_claimed_map_tran)

        if 'reducer' in self.lb_type:
            ln_worker_claimed_reduce_count_tran = self.state.writeTransition("eventCarry", self.state, self.state, self.ln_worker_claimed_reduce_count_ev_label)
            ln_worker_claimed_reduce_tran = self.state.writeTransition("eventCarry", self.state, self.state, self.ln_worker_claimed_reduce_ev_label)
            ln_worker_fetched_kv_ptr_tran = self.state.writeTransition("eventCarry", self.state, self.state, self.ln_worker_fetched_kv_ptr_ev_label)
            ln_worker_launch_reducer_tran = self.state.writeTransition("eventCarry", self.state, self.state, self.ln_worker_launch_reducer_ev_label)
            ln_worker_reducer_ret_tran = self.state.writeTransition("eventCarry", self.state, self.state, self.ln_worker_reducer_ret_ev_label)
            ln_worker_early_finish_tran = self.state.writeTransition("eventCarry", self.state, self.state, self.ln_worker_early_finish_ev_label)
            ln_worker_terminate_tran = self.state.writeTransition("eventCarry", self.state, self.state, self.ln_worker_terminate_ev_label)

            self.__gen_worker_claimed_reduce_count(ln_worker_claimed_reduce_count_tran)
            self.__gen_worker_claimed_reduce_task(ln_worker_claimed_reduce_tran)
            self.__gen_worker_fetched_kv_ptr(ln_worker_fetched_kv_ptr_tran)
            self.__gen_worker_launch_reducer(ln_worker_launch_reducer_tran)
            self.__gen_worker_reducer_ret(ln_worker_reducer_ret_tran)
            self.__gen_worker_early_finish(ln_worker_early_finish_tran)
            self.__gen_worker_terminate(ln_worker_terminate_tran)

            if self.grlb_type == 'ud':
                ln_worker_confirm_local_materialized_count_tran = self.state.writeTransition("eventCarry", self.state, self.state, self.ln_worker_confirm_local_materialized_count_ev_label)
                ln_worker_confirm_materialized_count_tran = self.state.writeTransition("eventCarry", self.state, self.state, self.ln_worker_confirm_materialized_count_ev_label)
                self.__gen_worker_confirm_local_materialized_count(ln_worker_confirm_local_materialized_count_tran)
                self.__gen_worker_confirm_materialized_count(ln_worker_confirm_materialized_count_tran)

        return

    def __gen_worker_init(self, tran):
        claimed_success = "UDPR_0"                  # UDPR_0                            thread reg
        part_end = "UDPR_2"                         # UDPR_2                            thread reg
        base_addr = "UDPR_3" if 'mapper' in self.lb_type \
                                or ('reducer' in self.lb_type and self.grlb_type == 'ud') \
                                else "X7"
        reduce_left_count = "UDPR_4"                # UDPR_4                            thread reg
        claiming_work = "UDPR_5"                    # UDPR_5                            thread reg
        claim_work_dest_nwid = "UDPR_6"             # UDPR_6                            thread reg
        source_ack_ev_word = "UDPR_9"               # UDPR_9                            thread reg
        saved_cont = self.saved_cont                # UDPR_15                           thread reg

        addr = "UDPR_7"                             # UDPR_7                            local reg
        dest = "UDPR_8"                             # UDPR_8                            local reg
        scratch = self.scratch                      # UDPR_12, UDPR_13                  local reg
        ev_word = self.ev_word                      # UDPR_14                           local reg

        if self.debug_flag:
            tran.writeAction(f"print 'Lane %u initializing worker' X0")
        tran.writeAction(f"addi X1 {saved_cont} 0")
        tran.writeAction(f"movir {claiming_work} -1")
        tran.writeAction(f"movir {claimed_success} 0")
        tran.writeAction(f"addi {'X0'} {claim_work_dest_nwid} 0")

        # Reg cache Lane 0 spd start address
        if 'mapper' in self.lb_type or ('reducer' in self.lb_type and self.grlb_type == 'ud'):    
            tran.writeAction(f"andi {'X0'} {scratch[0]} {63}")
            tran.writeAction(f"sli {scratch[0]} {scratch[0]} {int(log2(SPD_BANK_SIZE))}")
            tran.writeAction(f"sub {'X7'} {scratch[0]} {base_addr}")

        # Read partition end
        if 'mapper' in self.lb_type:
            tran.writeAction(f"movir {addr} {self.ln_part_end_offset}")
            bank_start_addr = "X7" if self.intra_map_work_stealing or self.global_map_work_stealing else base_addr
            tran.writeAction(f"add {addr} {bank_start_addr} {addr}")
            tran.writeAction(f"movlr 0({addr}) {part_end} 0 {WORD_SIZE}")
            if self.debug_flag:
                tran.writeAction(f"print 'Partition arr end reads %ld' {part_end}")

        if 'reducer' in self.lb_type:
            tran.writeAction(f"movir {reduce_left_count} 0")

        tran.writeAction(f"addi {'X2'} {ev_word} {0}")
        tran.writeAction(f"evlb {ev_word} {self.ln_worker_work_ev_label}")
        tran.writeAction(f"movir {scratch[0]} {self._worker_claim_key_flag}")
        tran.writeAction(f"sendr_wcont {ev_word} {'X2'} {scratch[0]} {scratch[0]}")

        tran.writeAction(f"yield")

        return

    def __gen_worker_work(self, tran):

        '''
        Event: worker event after mapper is finished
        Operands:   if first time returned from lane_master_loop
                        X8:   self._worker_start_flag  checking flag for the first time this event is envoked
                        X1:   event word of lane master loop


                    if reached terminating condition and waiting for unresolved kv count
                        X8:   self._finish_flag
                        
                    if returned from fetched_kv_pair
                        X8:   self._worker_claim_key_flag, jump to claim_work

                    if returned from claim work
                        X8:   if == self._no_work_to_be_claimed_flag
                              Jmup to claim_work

                        X8:   if == self._map_flag
                        X9:   ptr to partition
                        X10:  claimed ud event word
                        
                        X8:   if == self._reduce_flag
                        X9:   ptr to kv array
                        X10:  number of kvs materialized
                        X1:   source lane acknowledgement event
        '''

        claimed_success = "UDPR_0"                  # UDPR_0                            thread reg
        part_end = "UDPR_2"                         # UDPR_2                            thread reg
        base_addr = "UDPR_3" if 'mapper' in self.lb_type \
                                or ('reducer' in self.lb_type and self.grlb_type == 'ud') \
                                else "X7"
        reduce_left_count = "UDPR_4"                # UDPR_4                            thread reg
        claiming_work = "UDPR_5"                    # UDPR_5                            thread reg
        claim_work_dest_nwid = "UDPR_6"             # UDPR_6                            thread reg
        source_ack_ev_word = "UDPR_9"               # UDPR_9                            thread reg
        saved_cont = self.saved_cont                # UDPR_15                           thread reg

        # src_nwid = "UDPR_1"                         # UDPR_1                            local reg
        src_nwid = "X9"
        cur_nwid = "UDPR_11" if not ('reducer' in self.lb_type and self.grlb_type == 'lane') else "X0"
        addr = "UDPR_7"                             # UDPR_7                            local reg
        dest = "UDPR_8"                             # UDPR_8                            local reg
        scratch = self.scratch                      # UDPR_12, UDPR_13                  local reg
        ev_word = self.ev_word                      # UDPR_14                           local reg


        if self.jump_claiming_dest:
            tran.writeAction(f"beqi X8 {self._worker_claim_key_flag} claim_work")

            # If X8 != self._worker_claim_key_flag: 
            #   then claim failed, 
            #   Operands: X8    src cached claiming dest
            #             X9    src network id
            # If valid, update local cached claiming dest

            # 1.1 Check if src_nwid == dest: source early finished
            tran.writeAction(f"beq X8 {src_nwid} not_valid")
            # 1.2 Check if cur_nwid == dest: jump to early finish
            if not ('reducer' in self.lb_type and self.grlb_type == 'lane'):
                tran.writeAction(f"sri X0 {cur_nwid} {6}")
            tran.writeAction(f"beq X8 {cur_nwid} not_valid")
            # 1.3 Check if dest is the same as cached
            tran.writeAction(f"movir {addr} {self.jump_claiming_dest_offset}")
            tran.writeAction(f"add {base_addr} {addr} {addr}")
            tran.writeAction(f"movlr 0({addr}) {scratch[0]} 0 {WORD_SIZE}")
            tran.writeAction(f"beq X8 {scratch[0]} claim_work")
            # 1.4 Check if cached dest is the same as cur_nwid: jump to early finish
            tran.writeAction(f"beq {cur_nwid} {scratch[0]} not_valid")

            # 1.3 If src_nwid < cur_nwid
            tran.writeAction(f"bgt {src_nwid} {cur_nwid} source_larger")
            tran.writeAction(f"ble X8 {src_nwid} not_valid")
            tran.writeAction(f"bge X8 {cur_nwid} not_valid")
            tran.writeAction(f"jmp valid")

            # 1.4 If src_nwid < cur_nwid
            tran.writeAction(f"source_larger: blt X8 {cur_nwid} valid")
            tran.writeAction(f"bgt X8 {src_nwid} valid")

            # If not valid, early finish
            tran.writeAction(f"not_valid: addi {'X2'} {ev_word} {0}")
            tran.writeAction(f"evlb {ev_word} {self.ln_worker_early_finish_ev_label}")
            tran.writeAction(f"sendr_wret {ev_word} {self.ln_worker_terminate_ev_label} {scratch[0]} {scratch[0]} {scratch[0]}")
            tran.writeAction(f"yield")

            # If valid, atomically update local cached claiming dest if new dest is farther than cached dest
            # farther condition:
            # 1) cur_nwid < cur_dest:
            #       i)  new_dest > cur_dest
            #       ii) new_dest < cur_nwid
            # 2) cur_dest < cur_nwid:
            #       i) new_dest > cur_dest
            # In short:
            # 1) new_dest > cur_dest
            # 2) cur_nwid < cur_dest && new_dest < cur_nwid
            cur_dest = scratch[0]
            new_dest = "X8"
            tran.writeAction(f"valid: movlr 0({addr}) {cur_dest} 0 {WORD_SIZE}")
            tran.writeAction(f"beq {cur_nwid} {cur_dest} not_valid")
            tran.writeAction(f"beq {new_dest} {cur_dest} claim_work")
            tran.writeAction(f"bgt {new_dest} {cur_dest} update_new_claiming_dest")       # 1) new_dest > cur_dest
            tran.writeAction(f"bgt {cur_nwid} {cur_dest} claim_work")                     # 2) !(cur_nwid < cur_dest)
            tran.writeAction(f"blt {cur_nwid} {new_dest} claim_work")                     # 2) !(new_dest < cur_nwid)
            tran.writeAction(f"update_new_claiming_dest: cswp {addr} {scratch[1]} {cur_dest} {new_dest}")
            tran.writeAction(f"bne {scratch[1]} {cur_dest} valid")


        # Before claiming local work: check if local work is all resolved
        jump_flag = 0 if 'reducer' not in self.lb_type else 2
        tran.writeAction(f"claim_work: bgei {claiming_work} {jump_flag} {'claim_remote_work'}")

        # Send to claim local work
        tran.writeAction(f"addi X2 {ev_word} {0}")
        tran.writeAction(f"evlb {ev_word} {self.ln_worker_claim_local_ev_label}")
        tran.writeAction(f"sendr_wcont {ev_word} X2 X8 X9")
        tran.writeAction(f"yield")

        # Send to claim remote work
        tran.writeAction(f"claim_remote_work: addi X2 {ev_word} {0}")
        tran.writeAction(f"evlb {ev_word} {self.ln_worker_claim_remote_ev_label}")
        tran.writeAction(f"sendr_wcont {ev_word} X2 X8 X9")
        tran.writeAction(f"yield")

        return

    def __gen_worker_claim_local_work(self, tran):
        claimed_success = "UDPR_0"                  # UDPR_0                            thread reg
        part_end = "UDPR_2"                         # UDPR_2                            thread reg
        base_addr = "UDPR_3" if 'mapper' in self.lb_type \
                                or ('reducer' in self.lb_type and self.grlb_type == 'ud') \
                                else "X7"
        reduce_left_count = "UDPR_4"                # UDPR_4                            thread reg
        claiming_work = "UDPR_5"                    # UDPR_5                            thread reg
        claim_work_dest_nwid = "UDPR_6"             # UDPR_6                            thread reg
        source_ack_ev_word = "UDPR_9"               # UDPR_9                            thread reg
        saved_cont = self.saved_cont                # UDPR_15                           thread reg
        addr = "UDPR_7"                             # UDPR_7                            local reg
        dest = "UDPR_8"                             # UDPR_8                            local reg
        scratch = self.scratch                      # UDPR_12, UDPR_13                  local reg
        ev_word = self.ev_word                      # UDPR_14                           local reg

        receive_addr = "UDPR_1"
        entry_ind = "UDPR_11"
        cswp_ret = dest
        claiming_count = reduce_left_count
        materialize_metadata_addr = "UDPR_10"

        
        if self.debug_flag:
            tran.writeAction(f"print 'Start claiming local'")

        if 'reducer' in self.lb_type:
            tran.writeAction(f"bgei {claiming_work} {1} check_unresolved_local_reduce")
            tran.writeAction(f"bgei {claiming_work} {0} check_terminate_bit")

        if 'mapper' in self.lb_type:

            # Calculate spd address of partition start entry
            tran.writeAction(f"movir {addr} {self.ln_part_start_offset}")
            bank_start_addr = "X7" if self.intra_map_work_stealing or self.global_map_work_stealing else base_addr
            tran.writeAction(f"add {bank_start_addr} {addr} {addr}")

            # Try to update start entry atomically
            tran.writeAction(f"claiming_local_maps: movlr 0({addr}) {scratch[0]} 0 {WORD_SIZE}")
            if self.debug_flag:
                tran.writeAction(f"print 'Reading partition start from %lu(0x%lx) as %lu(0x%lx)' {addr} {addr} {scratch[0]} {scratch[0]}")
                tran.writeAction(f"perflog 1 0 'Start claiming local map'")
            tran.writeAction(f"beq {scratch[0]} {part_end} {'local_maps_finished'}")
            tran.writeAction(f"addi {scratch[0]} {scratch[1]} {WORD_SIZE * self.in_kvset_iter_size}")
            tran.writeAction(f"cswp {addr} {dest} {scratch[0]} {scratch[1]}")
            tran.writeAction(f"beq {scratch[0]} {dest} claimed_local_maps")
            tran.writeAction(f"jmp claiming_local_maps")

            # If successfully updated, send partition ptr to mapper
            tran.writeAction(f"claimed_local_maps: evii {ev_word} {self.ln_mapper_control_init_ev_label} {255} {5}")
            tran.writeAction(f"movir {addr} {self.ud_mstr_evw_offset}")
            tran.writeAction(f"add {'X7'} {addr} {addr}")
            tran.writeAction(f"movlr 0({addr}) {scratch[1]} 0 {WORD_SIZE}")
            tran.writeAction(f"sendr_wcont {ev_word} {'X2'} {scratch[0]} {scratch[1]}")

            if self.debug_flag:
                tran.writeAction(f"sri X0 {scratch[1]} {6}")
                tran.writeAction(f"andi {scratch[1]} {scratch[1]} {0b11}")
                tran.writeAction(f"print '[LB_DEBUG][Local] Lane %d claimed ud %d map partition at %lu end %lu' X0 {scratch[1]} {scratch[0]} {part_end}")
            tran.writeAction(f"yield")

            tran.writeAction(f"local_maps_finished: movir {claiming_work} {0}")
            if self.print_claiming_work:
                tran.writeAction(f"print 'setting claiming_work to 0'")

            if self.intra_map_work_stealing or self.inter_map_work_stealing or self.global_map_work_stealing:
                tran.writeAction(f"movir {addr} {self.rand_offset}")
                tran.writeAction(f"add {'X7'} {addr} {addr}")
                tran.writeAction(f"sli {'X0'} {scratch[0]} {16}")
                tran.writeAction(f"ori {scratch[0]} {scratch[0]} {self.rand_seed}")
                tran.writeAction(f"movrl {scratch[0]} 0({addr}) 0 {WORD_SIZE}")


        if 'reducer' in self.lb_type:
            bank_start_addr = "X7" if self.intra_reduce_work_stealing or self.global_reduce_work_stealing else base_addr

            # Before claiming local reduce, check if all mappers finished
            tran.writeAction(f"check_terminate_bit: movir {addr} {self.terminate_bit_offset}")
            tran.writeAction(f"add X7 {addr} {addr}")
            tran.writeAction(f"movlr 0({addr}) {scratch[0]} 0 {WORD_SIZE}")

            next_step_label = 'claim_remote_work' if self.enable_mr_barrier else 'check_unresolved_local_reduce'
            tran.writeAction(f"blti {scratch[0]} {0} {next_step_label}")
            tran.writeAction(f"movir {claiming_work} {1}")
            if self.print_claiming_work:
                tran.writeAction(f"print 'setting claiming_work to 1, terminate bit %u' {scratch[0]}")

            # Before claiming local reduce, check if local reduce all resolved
            tran.writeAction(f"check_unresolved_local_reduce: movir {receive_addr} {self.inter_key_received_count_offset}")
            tran.writeAction(f"add {bank_start_addr} {receive_addr} {receive_addr}")
            tran.writeAction(f"movir {addr} {self.inter_key_resolved_count_offset}")
            tran.writeAction(f"add {bank_start_addr} {addr} {addr}")
            if self.claim_multiple_work:
                tran.writeAction(f"movir {claiming_count} {self.max_reduce_key_to_claim}")

            # Check if local keys are all claimed
            tran.writeAction(f"read_unresolved_reduce_counts: movlr 0({receive_addr}) {scratch[1]} 0 {WORD_SIZE}")
            tran.writeAction(f"movlr 0({addr}) {scratch[0]} 0 {WORD_SIZE}")
            if self.debug_flag:
                tran.writeAction(f"print 'Claiming self work, received_count %lu, resolved_count %lu' {scratch[1]} {scratch[0]}")
            if self.do_all_reduce and self.do_all_reduce_with_materialize:
                # Check if cached keys are all claimed
                tran.writeAction(f"blt {scratch[0]} {scratch[1]} claiming_local_reduces")
                # Check if materialized keys are all claimed
                tran.writeAction(f"movir {materialize_metadata_addr} {self.materializing_metadata_offset}")
                tran.writeAction(f"add {bank_start_addr} {materialize_metadata_addr} {materialize_metadata_addr}")
                tran.writeAction(f"movlr 0({materialize_metadata_addr}) {scratch[0]} 0 {WORD_SIZE}")
                tran.writeAction(f"movlr {WORD_SIZE}({materialize_metadata_addr}) {scratch[1]} 0 {WORD_SIZE}")
                tran.writeAction(f"bge {scratch[0]} {scratch[1]} local_reduces_finished")
                tran.writeAction(f"jmp claiming_local_reduces_from_dram")
            else:
                tran.writeAction(f"bge {scratch[0]} {scratch[1]} local_reduces_finished")


            # Claim next available key
            if self.grlb_type == 'ud': 
                if self.claim_multiple_work:
                    # Atomically Update inter_key_resolved_count in spd
                    tran.writeAction(f"claiming_local_reduces: add {scratch[0]} {claiming_count} {entry_ind}")
                    tran.writeAction(f"ble {entry_ind} {scratch[1]} claim")
                    tran.writeAction(f"addi {scratch[1]} {entry_ind} {0}")
                    tran.writeAction(f"sub {scratch[1]} {scratch[0]} {claiming_count}")
                    tran.writeAction(f"claim: cswp {addr} {cswp_ret} {scratch[0]} {entry_ind}")
                    tran.writeAction(f"bne {cswp_ret} {scratch[0]} read_unresolved_reduce_counts")
                    if self.debug_flag:
                        tran.writeAction(f"sri X0 {cswp_ret} {6}")
                        tran.writeAction(f"print 'Claimed local reduce task count: %lu, starting index %lu, next unclaimed index %lu, ud %u received_count %lu' {claiming_count} {scratch[0]} {entry_ind} {cswp_ret} {scratch[1]}")
                    # Cache the claimed count
                    tran.writeAction(f"movir {addr} {self.claimed_reduce_key_count_offset}")
                    tran.writeAction(f"add X7 {addr} {addr}")
                    tran.writeAction(f"movrl {claiming_count} 0({addr}) 0 {WORD_SIZE}")
                    tran.writeAction(f"addi {scratch[0]} {entry_ind} {0}")
                else:
                    # Atomically Update inter_key_resolved_count in spd
                    tran.writeAction(f"claiming_local_reduces: addi {scratch[0]} {ev_word} {1}")
                    tran.writeAction(f"cswp {addr} {scratch[1]} {scratch[0]} {ev_word}")
                    tran.writeAction(f"bne {scratch[1]} {scratch[0]} check_unresolved_local_reduce")
                    tran.writeAction(f"addi {scratch[0]} {entry_ind} 0")

                # Get the address of next unclaimed key
                tran.writeAction(f"divi {scratch[0]} {dest} {self.intermediate_cache_count}")
                tran.writeAction(f"modi {dest} {dest} {LANE_PER_UD}")
                tran.writeAction(f"modi {scratch[0]} {scratch[1]} {self.intermediate_cache_count}")
                tran.writeAction(f"sli {dest} {dest} {int(log2(SPD_BANK_SIZE))}")
                tran.writeAction(f"muli {scratch[1]} {scratch[1]} {self.intermediate_cache_entry_size * WORD_SIZE}")
                tran.writeAction(f"movir {addr} {self.intermediate_cache_offset}")
                tran.writeAction(f"add {dest} {addr} {addr}")
                tran.writeAction(f"add {base_addr} {addr} {addr}")
                tran.writeAction(f"add {scratch[1]} {addr} {addr}")

                if self.claim_multiple_work:
                    tmp = receive_addr
                    if self.do_all_reduce:
                        # Send out intermediate kv
                        tran.writeAction(f"addi {'X2'} {ev_word} 0")
                        tran.writeAction(f"evlb {ev_word} {self.ln_worker_launch_reducer_ev_label}")
                        tran.writeAction(f"addi {'X2'} {scratch[0]} 0")
                        tran.writeAction(f"evlb {scratch[0]} {self.ln_worker_reducer_ret_ev_label}")
                        tran.writeAction(f"iteration_claim: beqi {claiming_count} 0 iteration_end")
                        if self.debug_flag:
                            tran.writeAction(f"print 'Check index %lu addr %lu if being written...' {entry_ind} {addr}")
                        tran.writeAction(f"check_entry_being_written: movlr 0({addr}) {tmp} 0 {WORD_SIZE}")
                        tran.writeAction(f"beqi {tmp} -1 check_entry_being_written")
                        tran.writeAction(f"send_wcont {ev_word} {scratch[0]} {addr} {self.inter_kvpair_size}")
                        if self.debug_flag:
                            tran.writeAction(f"movlr 0({addr}) {scratch[1]} 0 {WORD_SIZE}")
                            tran.writeAction(f"print 'Send local claimed %lu-th key %lu, entry address %lu' {entry_ind} {scratch[1]} {addr}")
                        tran.writeAction(f"movir {self.scratch[1]} {-1}")
                        tran.writeAction(f"movrl {self.scratch[1]} 0({addr}) 0 {WORD_SIZE}")

                    else:
                        # Prepare event words
                        tran.writeAction(f"addi {'X2'} {ev_word} 0")
                        tran.writeAction(f"evlb {ev_word} {self.ln_worker_fetched_kv_ptr_ev_label}")
                        tran.writeAction(f"addi {'X2'} {scratch[0]} 0")
                        tran.writeAction(f"evlb {scratch[0]} {self.ln_worker_confirm_local_materialized_count_ev_label}")
                        tran.writeAction(f"evi {'X1'} {cswp_ret} {255} {0b0100}")
                        tran.writeAction(f"evii {scratch[1]} {self.kv_reduce_init_ev_label} {255} {0b0101}")

                        # Iterate to send out claimed keys
                        tran.writeAction(f"iteration_claim: beqi {claiming_count} 0 iteration_end")

                        tran.writeAction(f"check_entry_being_written: movlr 0({addr}) {tmp} 0 {WORD_SIZE}")
                        tran.writeAction(f"beqi {tmp} -1 check_entry_being_written")

                        # Update claimed bit in key
                        tran.writeAction(f"ori {tmp} {tmp} {1}")
                        # Update claimed event word
                        tran.writeAction(f"movlr {WORD_SIZE}({addr}) {dest} 0 {WORD_SIZE}")
                        # Write claimed event word
                        tran.writeAction(f"movrl {scratch[1]} {WORD_SIZE}({addr}) 0 {WORD_SIZE}")
                        # Write claimed bit in key
                        tran.writeAction(f"movrl {tmp} 0({addr}) 0 {WORD_SIZE}")

                        # Get the number of kvs materialized for claimed key and kv ptr
                        materialized_count = scratch[1]
                        tran.writeAction(f"movlr {WORD_SIZE * 2}({addr}) {materialized_count} 0 {WORD_SIZE}")
                        tran.writeAction(f"bgei {materialized_count} {0} claim_multiple_work_set_materialized_count")
                        tran.writeAction(f"movir {materialized_count} {0}")
                        tran.writeAction(f"claim_multiple_work_set_materialized_count: sendr3_wcont {ev_word} {scratch[0]} {dest} {materialized_count} {addr}")
                        if self.debug_flag:
                            tran.writeAction(f"print 'Send local claimed key %lu with dest %lu, count %lu, entry address %lu' {tmp} {dest} {materialized_count} {addr}")

                    tran.writeAction(f"subi {claiming_count} {claiming_count} {1}")

                    # Check if entry reaches end of bank
                    tran.writeAction(f"addi {addr} {addr} {self.intermediate_cache_entry_size * WORD_SIZE}")
                    tran.writeAction(f"addi {entry_ind} {entry_ind} {1}")
                    tran.writeAction(f"modi {entry_ind} {tmp} {self.intermediate_cache_count}")
                    tran.writeAction(f"bnei {tmp} {0} iteration_claim")

                    # Check if entry reaches end of last bank
                    tran.writeAction(f"divi {entry_ind} {tmp} {self.intermediate_cache_count}")
                    tran.writeAction(f"modi {tmp} {tmp} {LANE_PER_UD}")
                    tran.writeAction(f"beqi {tmp} {0} return_to_beginning")

                    # If crossing bank, reset entry address correspondingly
                    tran.writeAction(f"movir {tmp} {SPD_BANK_SIZE - self.intermediate_cache_size}")
                    if self.debug_flag:
                        tran.writeAction(f"print 'Crossing bank, adding %lu to spd address %lu, entry index %lu' {tmp} {addr} {entry_ind}")
                    tran.writeAction(f"add {addr} {tmp} {addr}")
                    tran.writeAction(f"jmp iteration_claim")

                    # If reaches end of last bank, reset entry address correspondingly
                    tran.writeAction(f"return_to_beginning: movir {addr} {self.intermediate_cache_offset}")
                    tran.writeAction(f"add {base_addr} {addr} {addr}")
                    if self.debug_flag:
                        tran.writeAction(f"print 'Returning to beginning, setting spd address as %lu, entry index %lu' {addr} {entry_ind}")
                    tran.writeAction(f"jmp iteration_claim")

                    # Iteration finished
                    tran.writeAction(f"iteration_end: movir {claimed_success} {0}")
                    tran.writeAction(f"movir {addr} {self.claimed_reduce_key_count_offset}")
                    tran.writeAction(f"add X7 {addr} {addr}")
                    tran.writeAction(f"movlr 0({addr}) {reduce_left_count} 0 {WORD_SIZE}")
                    tran.writeAction(f"jmp claiming_finished")

                else:
                    if self.do_all_reduce:
                        tran.writeAction(f"addi {reduce_left_count} {reduce_left_count} {1}")
                    tran.writeAction(f"check_entry_being_written: movlr 0({addr}) {scratch[1]} 0 {WORD_SIZE}")
                    tran.writeAction(f"beqi {scratch[1]} -1 check_entry_being_written")

            elif self.grlb_type == 'lane':
                # Update inter_key_resolved_count in spd
                tran.writeAction(f"claiming_local_reduces: addi {scratch[0]} {scratch[1]} {1}")
                tran.writeAction(f"movrl {scratch[1]} 0({addr}) 0 {WORD_SIZE}")
                tran.writeAction(f"modi {scratch[0]} {scratch[1]} {self.intermediate_cache_count}")
                # Get the address of next unclaimed key
                tran.writeAction(f"muli {scratch[1]} {scratch[0]} {self.intermediate_cache_entry_size * WORD_SIZE}")
                tran.writeAction(f"movir {addr} {self.intermediate_cache_offset}")
                tran.writeAction(f"add {'X7'} {addr} {addr}")
                tran.writeAction(f"add {addr} {scratch[0]} {addr}")
                if self.do_all_reduce:
                    tran.writeAction(f"addi {reduce_left_count} {reduce_left_count} {1}")

            if self.do_all_reduce:
                # Send out intermediate kv
                tran.writeAction(f"addi {'X2'} {ev_word} 0")
                tran.writeAction(f"evlb {ev_word} {self.ln_worker_launch_reducer_ev_label}")
                tran.writeAction(f"addi {'X2'} {scratch[0]} 0")
                tran.writeAction(f"evlb {scratch[0]} {self.ln_worker_reducer_ret_ev_label}")
                tran.writeAction(f"send_wcont {ev_word} {scratch[0]} {addr} {self.inter_kvpair_size}")
                if self.debug_flag:
                    tran.writeAction(f"movlr 0({addr}) {scratch[0]} 0 {WORD_SIZE}")
                    tran.writeAction(f"print 'Send local claimed key %lu, entry address %lu' {scratch[0]} {addr}")
                tran.writeAction(f"movir {self.scratch[1]} {-1}")
                tran.writeAction(f"movrl {self.scratch[1]} 0({addr}) 0 {WORD_SIZE}")
            else:
                # Update claimed bit in key
                tran.writeAction(f"movlr 0({addr}) {scratch[0]} 0 {WORD_SIZE}")
                tran.writeAction(f"ori {scratch[0]} {scratch[1]} {1}")
                # Update claimed event word
                tran.writeAction(f"evii {ev_word} {self.kv_reduce_init_ev_label} {255} {0b0101}")
                # Atomic write claimed event word
                tran.writeAction(f"addi {addr} {addr} {WORD_SIZE}")
                tran.writeAction(f"read_dest: movlr 0({addr}) {dest} 0 {WORD_SIZE}")
                tran.writeAction(f"cswp {addr} {scratch[0]} {dest} {ev_word}")
                # tran.writeAction(f"movrl {ev_word} {WORD_SIZE}({addr}) 0 {WORD_SIZE}")
                tran.writeAction(f"bne {scratch[0]} {dest} read_dest")
                tran.writeAction(f"subi {addr} {addr} {WORD_SIZE}")
                # Write claimed bit in key
                tran.writeAction(f"movrl {scratch[1]} 0({addr}) 0 {WORD_SIZE}")

                # Get the number of kvs materialized for claimed key and kv ptr
                materialized_count = "UDPR_10"
                tran.writeAction(f"movlr {WORD_SIZE * 2}({addr}) {materialized_count} 0 {WORD_SIZE}")
                if self.debug_flag:
                    if self.grlb_type == 'lane':
                        tran.writeAction(f"sri {scratch[1]} {scratch[1]} {1}")
                        tran.writeAction(f"sub {addr} {'X7'} {entry_ind}")
                        tran.writeAction(f"subi {entry_ind} {entry_ind} {self.intermediate_cache_offset}")
                        tran.writeAction(f"divi {entry_ind} {entry_ind} {self.intermediate_cache_entry_size * WORD_SIZE}")
                    elif self.grlb_type == 'ud':
                        tran.writeAction(f"sri {scratch[1]} {scratch[1]} {1}")
                    tran.writeAction(f"print 'Lane %d claimed %lu-th local key %lu with materialized_count %ld' X0 {entry_ind} {scratch[1]} {materialized_count}")
                tran.writeAction(f"addi {'X2'} {ev_word} 0")
                tran.writeAction(f"evlb {ev_word} {self.ln_worker_fetched_kv_ptr_ev_label}")
                if self.grlb_type == 'ud':
                    tran.writeAction(f"addi {'X2'} {scratch[0]} 0")
                    tran.writeAction(f"evlb {scratch[0]} {self.ln_worker_confirm_local_materialized_count_ev_label}")
                    # If materialized_count == -1, send 0 instead
                    tran.writeAction(f"bgei {materialized_count} {0} set_materialized_count")
                    tran.writeAction(f"movir {materialized_count} {0}")
                # Send to worker_fetched_kv_ptr
                tran.writeAction(f"set_materialized_count: sendr3_wcont {ev_word} {scratch[0]} {dest} {materialized_count} {addr}")

            tran.writeAction(f"movir {claimed_success} {0}")
            tran.writeAction(f"jmp claiming_finished")

            if self.do_all_reduce and self.do_all_reduce_with_materialize:
                if self.grlb_type == 'lane':
                    tran.writeAction(f"claiming_local_reduces_from_dram: addi {scratch[0]} {entry_ind} {1}")
                    tran.writeAction(f"claim_dram: cswp {materialize_metadata_addr} {cswp_ret} {scratch[0]} {entry_ind}")
                    tran.writeAction(f"bne {cswp_ret} {scratch[0]} read_unresolved_reduce_counts")
                    if self.debug_flag:
                        tran.writeAction(f"print 'Claimed local lane %u dram reduce task count: %lu, starting index %lu, next unclaimed index %lu, received_count %lu' {'X0'} {claiming_count} {scratch[0]} {entry_ind} {scratch[1]}")

                    # Get the address of next unclaimed key
                    if (self.materialize_kv_dram_size & (self.materialize_kv_dram_size-1)) == 0:
                        tran.writeAction(f"movir {cswp_ret} {1}")
                        tran.writeAction(f"sli {cswp_ret} {cswp_ret} {int(log2(self.materialize_kv_dram_size))}")
                    else:
                        tran.writeAction(f"movir {cswp_ret} {self.materialize_kv_dram_size}")
                    tran.writeAction(f"subi {entry_ind} {entry_ind} {1}")
                    tran.writeAction(f"mod {entry_ind} {cswp_ret} {scratch[0]}")
                    tran.writeAction(f"muli {scratch[0]} {scratch[0]} {self.inter_kvpair_size * WORD_SIZE}")
                    tran.writeAction(f"movir {addr} {self.intermediate_ptr_offset}")
                    tran.writeAction(f"add {bank_start_addr} {addr} {addr}")
                    tran.writeAction(f"movlr 0({addr}) {scratch[1]} 0 {WORD_SIZE}")
                    tran.writeAction(f"add {scratch[0]} {scratch[1]} {scratch[1]}")

                    # Send dram request to read intermediate kv
                    tran.writeAction(f"send_dmlm_ld_wret {scratch[1]} {self.ln_worker_launch_reducer_ev_label} {self.inter_kvpair_size} {scratch[0]}")
                    if self.debug_flag:
                        tran.writeAction(f"print 'Send local lane %u %lu-th claimed dram key to lane %lu at dram %lu' {'X0'} {entry_ind} {'X0'} {scratch[1]}")

                    # Iteration finished
                    tran.writeAction(f"iteration_end: movir {claimed_success} {0}")
                    tran.writeAction(f"movir {reduce_left_count} 1")
                    tran.writeAction(f"jmp claiming_finished")

                else:
                    tran.writeAction(f"claiming_local_reduces_from_dram: add {scratch[0]} {claiming_count} {entry_ind}")
                    tran.writeAction(f"ble {entry_ind} {scratch[1]} claim_dram")
                    tran.writeAction(f"addi {scratch[1]} {entry_ind} {0}")
                    tran.writeAction(f"sub {scratch[1]} {scratch[0]} {claiming_count}")
                    tran.writeAction(f"claim_dram: cswp {materialize_metadata_addr} {cswp_ret} {scratch[0]} {entry_ind}")
                    tran.writeAction(f"bne {cswp_ret} {scratch[0]} read_unresolved_reduce_counts")
                    if self.debug_flag:
                        tran.writeAction(f"sri X0 {cswp_ret} {6}")
                        tran.writeAction(f"print 'Claimed local ud %u dram reduce task count: %lu, starting index %lu, next unclaimed index %lu, received_count %lu' {cswp_ret} {claiming_count} {scratch[0]} {entry_ind} {scratch[1]}")
                    # Cache the claimed count
                    tran.writeAction(f"movir {addr} {self.claimed_reduce_key_count_offset}")
                    tran.writeAction(f"add X7 {addr} {addr}")
                    tran.writeAction(f"movrl {claiming_count} 0({addr}) 0 {WORD_SIZE}")
                    tran.writeAction(f"addi {scratch[0]} {entry_ind} {0}")

                    # Get the address of next unclaimed key
                    if (self.materialize_kv_dram_size & (self.materialize_kv_dram_size-1)) == 0:
                        tran.writeAction(f"movir {cswp_ret} {1}")
                        tran.writeAction(f"sli {cswp_ret} {cswp_ret} {int(log2(self.materialize_kv_dram_size))}")
                    else:
                        tran.writeAction(f"movir {cswp_ret} {self.materialize_kv_dram_size}")
                    tran.writeAction(f"mod {entry_ind} {cswp_ret} {scratch[0]}")
                    tran.writeAction(f"muli {scratch[0]} {scratch[0]} {self.inter_kvpair_size * WORD_SIZE}")
                    tran.writeAction(f"movir {addr} {self.intermediate_ptr_offset}")
                    tran.writeAction(f"add {bank_start_addr} {addr} {addr}")
                    tran.writeAction(f"movlr 0({addr}) {scratch[1]} 0 {WORD_SIZE}")
                    tran.writeAction(f"add {scratch[0]} {scratch[1]} {scratch[1]}")
                    
                    # Send dram request to read intermediate kv
                    tran.writeAction(f"dram_iteration_claim: beqi {claiming_count} 0 iteration_end")
                    tran.writeAction(f"send_dmlm_ld_wret {scratch[1]} {self.ln_worker_launch_reducer_ev_label} {self.inter_kvpair_size} {scratch[0]}")
                    if self.debug_flag:
                        tran.writeAction(f"sri X0 X16 6")
                        tran.writeAction(f"print 'Send local ud %u %lu-th claimed dram key to lane %lu at dram %lu' {'X16'} {entry_ind} {'X0'} {scratch[1]}")

                    tran.writeAction(f"subi {claiming_count} {claiming_count} {1}")
                    tran.writeAction(f"addi {scratch[1]} {scratch[1]} {self.inter_kvpair_size * WORD_SIZE}")
                    tran.writeAction(f"addi {entry_ind} {entry_ind} {1}")
                    tran.writeAction(f"mod {entry_ind} {cswp_ret} {scratch[0]}")
                    tran.writeAction(f"bnei {scratch[0]} {0} dram_iteration_claim")
                    tran.writeAction(f"movlr 0({addr}) {scratch[1]} 0 {WORD_SIZE}")
                    tran.writeAction(f"jmp dram_iteration_claim")


            tran.writeAction(f"local_reduces_finished: blti {claiming_work} {1} claim_remote_work")
            tran.writeAction(f"movir {claiming_work} {2}")
            if self.print_claiming_work:
                tran.writeAction(f"print 'setting claiming_work to 2'")


        tran.writeAction(f"claim_remote_work: addi X2 {ev_word} {0}")
        tran.writeAction(f"evlb {ev_word} {self.ln_worker_claim_remote_ev_label}")
        tran.writeAction(f"sendr_wcont {ev_word} {'X2'} {scratch[0]} {scratch[0]}")
        if self.debug_flag:
            tran.writeAction(f"claiming_finished: print 'End claiming local reduce'")
            tran.writeAction(f"yield")
        else:
            tran.writeAction(f"claiming_finished: yield")
        return

    def __gen_worker_claim_remote_work_local_mapper_ws(self, tran):
        claimed_success = "UDPR_0"                  # UDPR_0                            thread reg
        part_end = "UDPR_2"                         # UDPR_2                            thread reg
        base_addr = "UDPR_3" if 'mapper' in self.lb_type \
                                or ('reducer' in self.lb_type and self.grlb_type == 'ud') \
                                else "X7"
        reduce_left_count = "UDPR_4"                # UDPR_4                            thread reg
        claiming_work = "UDPR_5"                    # UDPR_5                            thread reg
        claim_work_dest_nwid = "UDPR_6"             # UDPR_6                            thread reg
        source_ack_ev_word = "UDPR_9"               # UDPR_9                            thread reg
        saved_cont = self.saved_cont                # UDPR_15                           thread reg

        addr = "UDPR_7"                             # UDPR_7                            local reg
        dest = "UDPR_8"                             # UDPR_8                            local reg
        scratch = self.scratch                      # UDPR_12, UDPR_13                  local reg
        ev_word = self.ev_word                      # UDPR_14                           local reg

        base_nwid = "UDPR_11"


        step = 1

        # Claim from other lanes
        # Check if time to terminate
        tran.writeAction(f"claim_work: movir {addr} {self.terminate_bit_offset}")
        tran.writeAction(f"add {'X7'} {addr} {addr}")
        tran.writeAction(f"movlr 0({addr}) {scratch[0]} 0 {WORD_SIZE}")
        tran.writeAction(f"beqi {scratch[0]} {1} worker_finished")

        # Generate a random lane id
        tran.writeAction(f"movir {addr} {self.rand_offset}")
        tran.writeAction(f"add X7 {addr} {addr}")
            # rand_tmp0 = rand_ptr[0];
            # rand_tmp1 = rand_tmp0 << 13;
            # rand_tmp0 = rand_tmp1 ^ rand_tmp0; // x1 <- x ^ (x<<13)
            # rand_tmp1 = rand_tmp0 >> 7; // x1 >> 7
            # rand_tmp0 = rand_tmp0 ^ rand_tmp1; // x2 <- x1 ^ (x1 >> 7)
            # rand_tmp1 = rand_tmp0 << 17; // x2 << 17
            # rand_tmp0 = rand_tmp0 ^ rand_tmp1; // x2 ^ (x2 << 17)
            # rand_ptr[0] = rand_tmp0;
        tran.writeAction(f"gen_rand: movlr 0({addr}) {scratch[0]} 0 {WORD_SIZE}")
        tran.writeAction(f"restart_rand: addi {scratch[0]} {base_nwid} {0}")
        tran.writeAction(f"sli {scratch[0]} {scratch[1]} {13}")
        tran.writeAction(f"xor {scratch[0]} {scratch[1]} {scratch[0]}")
        tran.writeAction(f"sri {scratch[0]} {scratch[1]} {7}")
        tran.writeAction(f"xor {scratch[0]} {scratch[1]} {scratch[0]}")
        tran.writeAction(f"sli {scratch[0]} {scratch[1]} {17}")
        tran.writeAction(f"xor {scratch[0]} {scratch[1]} {scratch[0]}")

        tran.writeAction(f"bne {base_nwid} {scratch[0]} keep_iterating")
        tran.writeAction(f"sli {'X0'} {scratch[0]} {16}")
        tran.writeAction(f"ori {scratch[0]} {scratch[0]} {self.rand_seed}")
        tran.writeAction(f"jmp restart_rand")
        
        tran.writeAction(f"keep_iterating: movir {addr} {self.rand_offset}")
        tran.writeAction(f"add X7 {addr} {addr}")
        tran.writeAction(f"movrl {scratch[0]} 0({addr}) 0 {WORD_SIZE}")

        tran.writeAction(f"andi {scratch[0]} {scratch[1]} {63}")

        # Check if random lane id is current lane
        tran.writeAction(f"andi {'X0'} {scratch[0]} {63}")
        # tran.writeAction(f"beq {scratch[1]} {scratch[0]} gen_rand")

        # Update dest nwid
        tran.writeAction(f"andi {claim_work_dest_nwid} {scratch[0]} {63}")
        tran.writeAction(f"sub {claim_work_dest_nwid} {scratch[0]} {claim_work_dest_nwid}")
        tran.writeAction(f"add {claim_work_dest_nwid} {scratch[1]} {claim_work_dest_nwid}")

        # Prepare to claim remote map
        tran.writeAction(f"prepare_to_claim: movir {claimed_success} {0}")
        if self.debug_flag:
            tran.writeAction(f"print 'Lane %d trying to claim remote work from lane %d' X0 {claim_work_dest_nwid}")
        tran.writeAction(f"andi {claim_work_dest_nwid} {scratch[0]} {63}")
        tran.writeAction(f"sli {scratch[0]} {scratch[0]} {int(log2(SPD_BANK_SIZE))}")
        tran.writeAction(f"add {base_addr} {scratch[0]} {addr}")
        tran.writeAction(f"movir {scratch[0]} {self.ln_part_start_offset}")
        tran.writeAction(f"add {addr} {scratch[0]} {addr}")
        tran.writeAction(f"movlr {self.ln_part_end_offset-self.ln_part_start_offset}({addr}) {part_end} 0 {WORD_SIZE}")

        # Claim remote map
        tran.writeAction(f"claim_remote: movlr 0({addr}) {scratch[0]} 0 {WORD_SIZE}")
        tran.writeAction(f"bge {scratch[0]} {part_end} claim_failed")
        tran.writeAction(f"addi {scratch[0]} {scratch[1]} {WORD_SIZE * self.in_kvset_iter_size}")
        tran.writeAction(f"cswp {addr} {dest} {scratch[0]} {scratch[1]}")
        tran.writeAction(f"beq {scratch[0]} {dest} claimed_remote")
        tran.writeAction(f"jmp claim_remote")

        # If successfully updated, send partition ptr to mapper
        tran.writeAction(f"claimed_remote: evii {ev_word} {self.ln_mapper_control_init_ev_label} {255} {5}")
        tran.writeAction(f"movir {addr} {self.ud_mstr_evw_offset}")
        tran.writeAction(f"add {'X7'} {addr} {addr}")
        tran.writeAction(f"movlr 0({addr}) {scratch[1]} 0 {WORD_SIZE}")
        tran.writeAction(f"sendr_wcont {ev_word} {'X2'} {scratch[0]} {scratch[1]}")
        if self.debug_flag:
            tran.writeAction(f"sri X0 {scratch[1]} {6}")
            tran.writeAction(f"andi {scratch[1]} {scratch[1]} {0b11}")
            tran.writeAction(f"print '[LB_DEBUG][Local] Lane %d claimed ud %d map partition at %lu end %lu' X0 {scratch[1]} {scratch[0]} {part_end}")
        tran.writeAction(f"jmp claim_remote_finished")


        tran.writeAction(f"claim_failed: movir {scratch[0]} {self._no_work_to_be_claimed_flag}")
        if self.debug_flag:
            tran.writeAction(f"perflog 1 0 'End claiming remote'")
        tran.writeAction(f"addi {'X2'} {ev_word} {0}")
        tran.writeAction(f"evlb {ev_word} {self.ln_worker_work_ev_label}")
        tran.writeAction(f"sendr_wcont {ev_word} X2 {scratch[0]} {scratch[1]}")

        tran.writeAction(f"claim_remote_finished: yield")

        tran.writeAction(f"worker_finished: yieldt")

        return
        
    def __gen_worker_claim_remote_work(self, tran):
        claimed_success = "UDPR_0"                  # UDPR_0                            thread reg
        part_end = "UDPR_2"                         # UDPR_2                            thread reg
        base_addr = "UDPR_3" if 'mapper' in self.lb_type \
                                or ('reducer' in self.lb_type and self.grlb_type == 'ud') \
                                else "X7"
        reduce_left_count = "UDPR_4"                # UDPR_4                            thread reg
        claiming_work = "UDPR_5"                    # UDPR_5                            thread reg
        claim_work_dest_nwid = "UDPR_6"             # UDPR_6                            thread reg
        source_ack_ev_word = "UDPR_9"               # UDPR_9                            thread reg
        saved_cont = self.saved_cont                # UDPR_15                           thread reg

        addr = "UDPR_7"                             # UDPR_7                            local reg
        dest = "UDPR_8"                             # UDPR_8                            local reg
        scratch = self.scratch                      # UDPR_12, UDPR_13                  local reg
        ev_word = self.ev_word                      # UDPR_14                           local reg

        base_nwid = "UDPR_11"


        step = 1 if 'reducer' in self.lb_type and self.grlb_type == 'lane' else LANE_PER_UD
        bank_start_addr = "X7" if self.intra_reduce_work_stealing or self.global_reduce_work_stealing else base_addr

        if 'reducer' in self.lb_type:
            if self.debug_flag:
                tran.writeAction(f"print 'Lane %d claim remote, claiming_work %d' X0 {claiming_work}")
            tran.writeAction(f"bnei {claiming_work} {2} claim_work")
            # Check if all resolved keys are executed
            tran.writeAction(f"check_claiming_finish: movir {addr} {self.inter_key_resolved_count_offset}")
            tran.writeAction(f"add {bank_start_addr} {addr} {addr}")
            tran.writeAction(f"movlr 0({addr}) {scratch[0]} 0 {WORD_SIZE}")
            tran.writeAction(f"movir {addr} {self.inter_key_executed_count_offset}")
            tran.writeAction(f"add {bank_start_addr} {addr} {addr}")
            tran.writeAction(f"movlr 0({addr}) {scratch[1]} 0 {WORD_SIZE}")
            # tran.writeAction(f"print 'resolved_count %lu executed_count %lu' {scratch[0]} {scratch[1]}")
            tran.writeAction(f"bgt {scratch[0]} {scratch[1]} claim_work")
            # If so, send to lane_master
            if self.debug_flag:
                tran.writeAction(f"movir {addr} {self.inter_key_received_count_offset}")
                tran.writeAction(f"add {bank_start_addr} {addr} {addr}")
                tran.writeAction(f"movlr 0({addr}) {ev_word} 0 {WORD_SIZE}")
                tran.writeAction(f"print 'received_count %lu resolved_count %lu executed_count %lu ' {ev_word} {scratch[0]} {scratch[1]}")
            tran.writeAction(f"movir {scratch[0]} {self._claiming_finish_flag}")
            tran.writeAction(f"sendr_wcont {saved_cont} {'X2'} {scratch[0]} {scratch[0]}")
            tran.writeAction(f"movir {claiming_work} {3}")
            if self.print_claiming_work:
                tran.writeAction(f"print 'setting claiming_work to 3'")
            if self.debug_flag:
                tran.writeAction(f"print 'Lane %d worker claiming finished, all local keys are executed' X0")


        # Claim from other lanes
        # Check if time to terminate
        tran.writeAction(f"claim_work: movir {addr} {self.terminate_bit_offset}")
        tran.writeAction(f"add {'X7'} {addr} {addr}")
        tran.writeAction(f"movlr 0({addr}) {scratch[0]} 0 {WORD_SIZE}")
        tran.writeAction(f"beqi {scratch[0]} {1} worker_finished")


        if self.jump_claiming_dest:
            tran.writeAction(f"movir {scratch[1]} {self.jump_claiming_dest_offset}")
            tran.writeAction(f"add {base_addr} {scratch[1]} {scratch[1]}")
            tran.writeAction(f"movlr {0}({scratch[1]}) {scratch[0]} 0 {WORD_SIZE}")
            if not ('reducer' in self.lb_type and self.grlb_type == 'lane'):
                tran.writeAction(f"andi {'X0'} {scratch[1]} {LANE_PER_UD-1}")
                tran.writeAction(f"slori {scratch[0]} {scratch[1]} {int(log2(LANE_PER_UD))}")
            else:
                tran.writeAction(f"addi {scratch[0]} {scratch[1]} {0}")
            tran.writeAction(f"beq {claim_work_dest_nwid} {scratch[1]} send_claim_msg")
            tran.writeAction(f"beq {'X0'} {scratch[1]} early_finished")
            tran.writeAction(f"addi {scratch[1]} {claim_work_dest_nwid} {0}")
        else:
            if self.random_intra_ud or self.random_inter_ud:
                # Generate a random lane id
                tran.writeAction(f"gen_rand: movir {addr} {self.rand_offset}")
                tran.writeAction(f"add X7 {addr} {addr}")
                    # rand_tmp0 = rand_ptr[0];
                    # rand_tmp1 = rand_tmp0 << 13;
                    # rand_tmp0 = rand_tmp1 ^ rand_tmp0; // x1 <- x ^ (x<<13)
                    # rand_tmp1 = rand_tmp0 >> 7; // x1 >> 7
                    # rand_tmp0 = rand_tmp0 ^ rand_tmp1; // x2 <- x1 ^ (x1 >> 7)
                    # rand_tmp1 = rand_tmp0 << 17; // x2 << 17
                    # rand_tmp0 = rand_tmp0 ^ rand_tmp1; // x2 ^ (x2 << 17)
                    # rand_ptr[0] = rand_tmp0;
                tran.writeAction(f"movlr 0({addr}) {scratch[0]} 0 {WORD_SIZE}")
                tran.writeAction(f"restart_rand: addi {scratch[0]} {base_nwid} {0}")
                tran.writeAction(f"sli {scratch[0]} {scratch[1]} {13}")
                tran.writeAction(f"sli {scratch[0]} {scratch[1]} {13}")
                tran.writeAction(f"xor {scratch[0]} {scratch[1]} {scratch[0]}")
                tran.writeAction(f"sri {scratch[0]} {scratch[1]} {7}")
                tran.writeAction(f"xor {scratch[0]} {scratch[1]} {scratch[0]}")
                tran.writeAction(f"sli {scratch[0]} {scratch[1]} {17}")
                tran.writeAction(f"xor {scratch[0]} {scratch[1]} {scratch[0]}")
                # Check if generated random number is the same as seed
                tran.writeAction(f"bne {base_nwid} {scratch[0]} keep_iterating")
                tran.writeAction(f"sli {'X0'} {scratch[0]} {16}")
                tran.writeAction(f"ori {scratch[0]} {scratch[0]} {self.rand_seed}")
                tran.writeAction(f"jmp restart_rand")
                tran.writeAction(f"keep_iterating: movir {scratch[1]} {self.map_ctr_offset}")
                tran.writeAction(f"movrl {scratch[0]} 0({addr}) 0 {WORD_SIZE}")

                # Update dest nwid
                if self.random_intra_ud:
                    tran.writeAction(f"andi {scratch[0]} {scratch[1]} {63}")
                    # Check if random lane id is current lane
                    tran.writeAction(f"andi {'X0'} {scratch[0]} {63}")
                    tran.writeAction(f"beq {scratch[1]} {scratch[0]} gen_rand")
                    # Update dest nwid
                    tran.writeAction(f"andi {claim_work_dest_nwid} {scratch[0]} {63}")
                    tran.writeAction(f"sub {claim_work_dest_nwid} {scratch[0]} {claim_work_dest_nwid}")
                    tran.writeAction(f"add {claim_work_dest_nwid} {scratch[1]} {claim_work_dest_nwid}")
                    # tran.writeAction(f"print 'Random dest nwid %lu' {claim_work_dest_nwid}")
                else:
                    tran.writeAction(f"movir {addr} {self.metadata_offset}")
                    tran.writeAction(f"add {'X7'} {addr} {addr}")
                    tran.writeAction(f"movlr {self.base_nwid_offset - self.metadata_offset}({addr}) {base_nwid} 0 8")
                    tran.writeAction(f"movlr {self.nwid_mask_offset - self.metadata_offset}({addr}) {scratch[1]} 0 8")
                    tran.writeAction(f"addi {scratch[1]} {scratch[1]} 1")
                    tran.writeAction(f"sli {scratch[0]} {scratch[0]} 1")
                    tran.writeAction(f"sri {scratch[0]} {scratch[0]} 1")
                    tran.writeAction(f"mod {scratch[0]} {scratch[1]} {claim_work_dest_nwid}")
                    tran.writeAction(f"add {claim_work_dest_nwid} {base_nwid} {claim_work_dest_nwid}")
                    # Check if generated random dest is the same as current lane
                    tran.writeAction(f"beq X0 {claim_work_dest_nwid} {'gen_rand'}")
            else:
                # Check if need to update claim_work_dest_nwid
                tran.writeAction(f"beqi {claimed_success} {1} send_claim_msg")

                # Update dest nwid
                tran.writeAction(f"movir {addr} {self.metadata_offset}")
                tran.writeAction(f"add {'X7'} {addr} {addr}")
                tran.writeAction(f"movlr {self.base_nwid_offset - self.metadata_offset}({addr}) {base_nwid} 0 8")
                tran.writeAction(f"sub {claim_work_dest_nwid} {base_nwid} {claim_work_dest_nwid}")
                tran.writeAction(f"addi {claim_work_dest_nwid} {claim_work_dest_nwid} {step}")
                tran.writeAction(f"movlr {self.nwid_mask_offset - self.metadata_offset}({addr}) {scratch[1]} 0 8")
                tran.writeAction(f"addi {scratch[1]} {scratch[1]} 1")
                tran.writeAction(f"mod {claim_work_dest_nwid} {scratch[1]} {claim_work_dest_nwid}")
                tran.writeAction(f"add {claim_work_dest_nwid} {base_nwid} {claim_work_dest_nwid}")
                # Check if dest is self
                # tran.writeAction(f"beq {'X0'} {claim_work_dest_nwid} early_finished")
                tran.writeAction(f"bne {'X0'} {claim_work_dest_nwid} send_claim_msg")
                tran.writeAction(f"bgei {claiming_work} {3} worker_finished")
                tran.writeAction(f"bgei {claiming_work} {2} early_finished")
                tran.writeAction(f"sub {claim_work_dest_nwid} {base_nwid} {claim_work_dest_nwid}")
                tran.writeAction(f"addi {claim_work_dest_nwid} {claim_work_dest_nwid} {step}")
                tran.writeAction(f"mod {claim_work_dest_nwid} {scratch[1]} {claim_work_dest_nwid}")
                tran.writeAction(f"add {claim_work_dest_nwid} {base_nwid} {claim_work_dest_nwid}")

        # Send claim_work message
        tran.writeAction(f"send_claim_msg: movir {claimed_success} {0}")
        if self.debug_flag:
            tran.writeAction(f"print 'Lane %d trying to claim remote work from lane %d' X0 {claim_work_dest_nwid}")
        tran.writeAction(f"evii {ev_word} {self.ln_receiver_claim_work_ev_label} {255} {5}")
        tran.writeAction(f"ev {ev_word} {ev_word} {claim_work_dest_nwid} {claim_work_dest_nwid} {0b1000}")
        if self.claim_multiple_work:
            tran.writeAction(f"movir {scratch[1]} {self.max_reduce_key_to_claim}")
            tran.writeAction(f"movir {reduce_left_count} {self.max_reduce_key_to_claim}")
        tran.writeAction(f"sendr_wret {ev_word} {self.ln_worker_work_ev_label} {scratch[1]} {scratch[1]} {scratch[0]}")
        tran.writeAction(f"yield")

        if 'reducer' in self.lb_type:
            # All lanes are visited, entering early_finish sequence
            tran.writeAction(f"early_finished: addi {'X2'} {ev_word} {0}")
            tran.writeAction(f"evlb {ev_word} {self.ln_worker_early_finish_ev_label}")
            tran.writeAction(f"sendr_wret {ev_word} {self.ln_worker_terminate_ev_label} {scratch[0]} {scratch[0]} {scratch[0]}")
            tran.writeAction(f"yield")

            # Reach terminating condition
            tran.writeAction(f"worker_finished: addi {'X2'} {ev_word} {0}")
            if self.debug_flag:
                tran.writeAction(f"print 'Lane %d worker finish' X0")
            tran.writeAction(f"evlb {ev_word} {self.ln_worker_terminate_ev_label}")
            tran.writeAction(f"sendr_wcont {ev_word} X2 {scratch[0]} {scratch[0]}")
            tran.writeAction(f"yield")

        else:
            # Reducer load balancer is not enabled, immediately terminate worker
            tran.writeAction(f"early_finished: yieldt")
            tran.writeAction(f"worker_finished: yieldt")

        return

    def __gen_worker_claimed_map_task(self, tran):
        claimed_success = "UDPR_0"                  # UDPR_0                            thread reg
        part_end = "UDPR_2"                         # UDPR_2                            thread reg
        base_addr = "UDPR_3" if 'mapper' in self.lb_type \
                                or ('reducer' in self.lb_type and self.grlb_type == 'ud') \
                                else "X7"
        reduce_left_count = "UDPR_4"                # UDPR_4                            thread reg
        claiming_work = "UDPR_5"                    # UDPR_5                            thread reg
        claim_work_dest_nwid = "UDPR_6"             # UDPR_6                            thread reg
        source_ack_ev_word = "UDPR_9"               # UDPR_9                            thread reg
        saved_cont = self.saved_cont                # UDPR_15                           thread reg

        addr = "UDPR_7"                             # UDPR_7                            local reg
        cswp_ret = "UDPR_8"                         # UDPR_8                            local reg
        scratch = self.scratch                      # UDPR_12, UDPR_13                  local reg
        ev_word = self.ev_word                      # UDPR_14                           local reg

        step = LANE_PER_UD

        tran.writeAction(f"addi {'X1'} {source_ack_ev_word} 0")
        if self.debug_flag:
            tran.writeAction(f"print 'Claimed Map work! source_ack_ev_word: %lu' X1")
        tran.writeAction(f"movir {claimed_success} {1}")

        if self.reset_claiming_dest:
            tran.writeAction(f"movir {scratch[1]} {self.metadata_offset}")
            tran.writeAction(f"add {'X7'} {scratch[1]} {scratch[1]}")
            tran.writeAction(f"movlr {self.base_nwid_offset - self.metadata_offset}({scratch[1]}) {scratch[0]} 0 8")
            tran.writeAction(f"sub {'X0'} {scratch[0]} {claim_work_dest_nwid}")
            tran.writeAction(f"addi {claim_work_dest_nwid} {claim_work_dest_nwid} {step}")
            tran.writeAction(f"movlr {self.nwid_mask_offset - self.metadata_offset}({scratch[1]}) {scratch[0]} 0 8")
            tran.writeAction(f"addi {scratch[0]} {scratch[0]} 1")
            tran.writeAction(f"mod {claim_work_dest_nwid} {scratch[0]} {claim_work_dest_nwid}")
            tran.writeAction(f"movlr {self.base_nwid_offset - self.metadata_offset}({scratch[1]}) {scratch[0]} 0 8")
            tran.writeAction(f"add {claim_work_dest_nwid} {scratch[0]} {claim_work_dest_nwid}")

        # tran.writeAction(f"movir {addr} {self.map_ctr_offset}")
        # tran.writeAction(f"add {'X7'} {addr} {addr}")
        # tran.writeAction(f"movlr 0({addr}) {self.scratch[0]} 0 {WORD_SIZE}")
        # tran.writeAction(f"print 'claimed remote map, num_map %lu.' {self.scratch[0]}")

        tran.writeAction(f"launch_mappers: evii {ev_word} {self.ln_mapper_control_init_ev_label} {255} {5}")
        tran.writeAction(f"sendr_wret {ev_word} {self.ln_worker_work_ev_label} {'X9'} {'X10'} {scratch[0]}")
        tran.writeAction(f"yield")
        return

    def __gen_worker_claimed_reduce_count(self, tran):
        claimed_success = "UDPR_0"                  # UDPR_0                            thread reg
        part_end = "UDPR_2"                         # UDPR_2                            thread reg
        base_addr = "UDPR_3" if 'mapper' in self.lb_type \
                                or ('reducer' in self.lb_type and self.grlb_type == 'ud') \
                                else "X7"
        reduce_left_count = "UDPR_4"                # UDPR_4                            thread reg
        claiming_work = "UDPR_5"                    # UDPR_5                            thread reg
        claim_work_dest_nwid = "UDPR_6"             # UDPR_6                            thread reg
        source_ack_ev_word = "UDPR_9"               # UDPR_9                            thread reg
        saved_cont = self.saved_cont                # UDPR_15                           thread reg

        addr = "UDPR_7"                             # UDPR_7                            local reg
        cswp_ret = "UDPR_8"                         # UDPR_8                            local reg
        scratch = self.scratch                      # UDPR_12, UDPR_13                  local reg
        ev_word = self.ev_word                      # UDPR_14                           local reg

        '''
        Event: reduce task returned from claim work
        Operands:
                    X8:     successfully claimed key count
                    Cont (X1):   source acknowledgement event
                    
        '''

        if self.debug_flag:
            tran.writeAction(f"print 'Claimed remote reduce task count: %lu' X8")
        if self.log_reduce_latency:
            tran.writeAction(f"perflog 1 0 'start %lu' X8")
        tran.writeAction(f"addi {'X1'} {source_ack_ev_word} 0")

        # Cache the claimed count
        tran.writeAction(f"movir {addr} {self.claimed_reduce_key_count_offset}")
        tran.writeAction(f"add X7 {addr} {addr}")
        tran.writeAction(f"movrl X8 0({addr}) 0 {WORD_SIZE}")

        # Correct reduce_left_count if not claimed exactly {self.max_reduce_key_to_claim} keys
        tran.writeAction(f"subi {'X8'} {scratch[0]} {self.max_reduce_key_to_claim}")
        tran.writeAction(f"add {reduce_left_count} {scratch[0]} {reduce_left_count}")

        tran.writeAction(f"yield")

        return

    def __gen_worker_claimed_reduce_task(self, tran):
        claimed_success = "UDPR_0"                  # UDPR_0                            thread reg
        part_end = "UDPR_2"                         # UDPR_2                            thread reg
        base_addr = "UDPR_3" if 'mapper' in self.lb_type \
                                or ('reducer' in self.lb_type and self.grlb_type == 'ud') \
                                else "X7"
        reduce_left_count = "UDPR_4"                # UDPR_4                            thread reg
        claiming_work = "UDPR_5"                    # UDPR_5                            thread reg
        claim_work_dest_nwid = "UDPR_6"             # UDPR_6                            thread reg
        source_ack_ev_word = "UDPR_9"               # UDPR_9                            thread reg
        saved_cont = self.saved_cont                # UDPR_15                           thread reg

        addr = "UDPR_7"                             # UDPR_7                            local reg
        cswp_ret = "UDPR_8"                         # UDPR_8                            local reg
        scratch = self.scratch                      # UDPR_12, UDPR_13                  local reg
        ev_word = self.ev_word                      # UDPR_14                           local reg

        '''
        Event: reduce task returned from claim work
        Operands:
                    X8:     _reduce_flag
                    X9:     dram ptr to kv array
                    X10:    number of kvs materialized
                    X11:    spd ptr to cache entry on source
                    Cont (X1):   source acknowledgement event

                if self.do_all_reduce:
                    X8~Xn:  intermediate kv
                    
        '''

        step = 1 if self.grlb_type == 'lane' else LANE_PER_UD

        tran.writeAction(f"addi {'X1'} {source_ack_ev_word} 0")
        if self.debug_flag:
            if self.do_all_reduce:
                tran.writeAction(f"print 'Claimed Reduce work! intermediate key %lu' X8")
            else:
                if self.grlb_type == 'ud':
                    tran.writeAction(f"print 'Claimed Reduce work! reduce flag %lu dram ptr %lu, number %lu, spd ptr %lu, source_ack_ev_word: %lu' X8 X9 X10 X11 X1")
                elif self.grlb_type == 'lane':
                    tran.writeAction(f"print 'Claimed Reduce work! reduce flag %lu dram ptr %lu, number %lu, source_ack_ev_word: %lu' X8 X9 X10 X1")

        tran.writeAction(f"movir {claimed_success} {1}")
        if self.reset_claiming_dest:
            tran.writeAction(f"movir {scratch[1]} {self.metadata_offset}")
            tran.writeAction(f"add {'X7'} {scratch[1]} {scratch[1]}")
            tran.writeAction(f"movlr {self.base_nwid_offset - self.metadata_offset}({scratch[1]}) {scratch[0]} 0 8")
            tran.writeAction(f"sub {'X0'} {scratch[0]} {claim_work_dest_nwid}")
            tran.writeAction(f"addi {claim_work_dest_nwid} {claim_work_dest_nwid} {step}")
            tran.writeAction(f"movlr {self.nwid_mask_offset - self.metadata_offset}({scratch[1]}) {scratch[0]} 0 8")
            tran.writeAction(f"addi {scratch[0]} {scratch[0]} 1")
            tran.writeAction(f"mod {claim_work_dest_nwid} {scratch[0]} {claim_work_dest_nwid}")
            tran.writeAction(f"movlr {self.base_nwid_offset - self.metadata_offset}({scratch[1]}) {scratch[0]} 0 8")
            tran.writeAction(f"add {claim_work_dest_nwid} {scratch[0]} {claim_work_dest_nwid}")

        # Send ptr and count to worker_fetched_kv_ptr
        tran.writeAction(f"fetch_kv_ptr: addi {'X2'} {ev_word} {0}")
        if self.do_all_reduce:
            tran.writeAction(f"evlb {ev_word} {self.ln_worker_launch_reducer_ev_label}")
            if self.grlb_type == 'ud':
                tran.writeAction(f"sendops_wcont {ev_word} X1 {'X8'} {self.inter_kvpair_size}")
            elif self.grlb_type == 'lane':
                tran.writeAction(f"sendops_wret {ev_word} {self.ln_worker_work_ev_label} {'X8'} {self.inter_kvpair_size} {scratch[0]}")
        else:
            tran.writeAction(f"evlb {ev_word} {self.ln_worker_fetched_kv_ptr_ev_label}")
            if self.grlb_type == 'ud':
                tran.writeAction(f"addi {'X1'} {scratch[0]} 0")
                tran.writeAction(f"evlb {scratch[0]} {self.ln_receiver_check_materialized_count_ev_label}")
                tran.writeAction(f"sendops_wcont {ev_word} {scratch[0]} {'X9'} {3}")
            elif self.grlb_type == 'lane':
                tran.writeAction(f"sendr_wret {ev_word} {self.ln_worker_work_ev_label} {'X9'} {'X10'} {scratch[0]}")
        tran.writeAction(f"yield")
        return

    def __gen_worker_fetched_kv_ptr(self, tran):
        '''
        Event:      Three returned situation
                    1)  returned from dram read request sent by fetched_key / this event
                        X8: Dram Pointer to kv array
                        X9: Count of kv pairs
                        if self.grlb_type == 'ud':
                            X10: Spd pointer to key entry
                            X1: Confirm event word
        '''

        claimed_success = "UDPR_0"                  # UDPR_0                            thread reg
        part_end = "UDPR_2"                         # UDPR_2                            thread reg
        base_addr = "UDPR_3" if 'mapper' in self.lb_type \
                                or ('reducer' in self.lb_type and self.grlb_type == 'ud') \
                                else "X7"
        reduce_left_count = "UDPR_4"                # UDPR_4                            thread reg
        claiming_work = "UDPR_5"                    # UDPR_5                            thread reg
        claim_work_dest_nwid = "UDPR_6"             # UDPR_6                            thread reg
        source_ack_ev_word = "UDPR_9"               # UDPR_9                            thread reg
        claim_work_cont = "UDPR_11"                 # UDPR_11                           thread reg
        saved_cont = self.saved_cont                # UDPR_15                           thread reg

        kv_count = "UDPR_1"                         # UDPR_1                            local reg
        addr = "UDPR_7"                             # UDPR_7                            local reg
        scratch = self.scratch                      # UDPR_12, UDPR_13                  local reg
        ev_word = self.ev_word                      # UDPR_14                           local reg


        if self.debug_flag:
            tran.writeAction(f"print 'intermediate kv pointer fetched with number %u and address %lu(0x%lx)' X9 X8 X8")

        if self.do_all_reduce and self.do_all_reduce_with_materialize:
            tran.writeAction(f"send_dmlm_ld_wret {'X8'} {self.ln_worker_launch_reducer_ev_label} {self.inter_kvpair_size} {scratch[0]}")
            tran.writeAction(f"yield")

        else:
            if self.grlb_type == 'ud':
                # Send to confirm materialized count
                if not self.claim_multiple_work:
                    tran.writeAction(f"addi {reduce_left_count} {reduce_left_count} {1}")
                tran.writeAction(f"sendr3_wret X1 {self.ln_worker_confirm_materialized_count_ev_label} X10 X8 X9 {scratch[0]}")
            tran.writeAction(f"beqi {'X9'} {0} no_kv_to_be_execute")

            tran.writeAction(f"addi X8 {scratch[1]} 0")
            tran.writeAction(f"addi X9 {kv_count} 0")

            tran.writeAction(f"resolving_kv: blei {kv_count} 0 claimed_kv_resolved")
            tran.writeAction(f"send_dmlm_ld_wret {scratch[1]} {self.ln_worker_launch_reducer_ev_label} {self.inter_kvpair_size} {scratch[0]}")
            tran.writeAction(f"addi {scratch[1]} {scratch[1]} {self.inter_kvpair_size * WORD_SIZE}")
            tran.writeAction(f"addi {reduce_left_count} {reduce_left_count} 1")
            tran.writeAction(f"subi {kv_count} {kv_count} 1")
            tran.writeAction(f"jmp resolving_kv")

            tran.writeAction(f"claimed_kv_resolved: yield")

            if self.grlb_type == 'ud':
                # Confirm materialized count hasn't come back, yield
                tran.writeAction(f"no_kv_to_be_execute: yield")

            elif self.grlb_type == 'lane':
                # Claimed a key with no materialized kv: Call worker to claim another work
                tran.writeAction(f"no_kv_to_be_execute: addi X2 {ev_word} 0")
                tran.writeAction(f"evlb {ev_word} {self.ln_worker_work_ev_label}")
                tran.writeAction(f"movir {scratch[0]} {self._worker_claim_key_flag}")
                tran.writeAction(f"sendr_wcont {ev_word} X2 {scratch[0]} {scratch[0]}")
                
                # If last work is local, update inter_key_executed_count
                tran.writeAction(f"beqi {claimed_success} {1} send_ack_to_source")
                tran.writeAction(f"movir {addr} {self.inter_key_executed_count_offset}")
                tran.writeAction(f"add {'X7'} {addr} {addr}")
                tran.writeAction(f"movlr 0({addr}) {scratch[1]} 0 {WORD_SIZE}")
                tran.writeAction(f"addi {scratch[1]} {scratch[1]} {1}")
                tran.writeAction(f"movrl {scratch[1]} 0({addr}) 0 {WORD_SIZE}")
                tran.writeAction(f"yield")

                # If last work is remote, send acknowledgement back
                tran.writeAction(f"send_ack_to_source: sendr_wcont {source_ack_ev_word} {'X2'} {scratch[0]} {scratch[0]}")
                tran.writeAction(f"movir {source_ack_ev_word} -1")
                tran.writeAction(f"yield")

        return

    def __gen_worker_confirm_local_materialized_count(self, tran):
        '''
        Event: confirmed materialized count of local key
        Operands:
                    X8:     Spd ptr to entry                   
                    X9:     Dram Pointer to kv array
                    X10:    Previously claimed count
        '''
        claimed_success = "UDPR_0"                  # UDPR_0                            thread reg
        part_end = "UDPR_2"                         # UDPR_2                            thread reg
        base_addr = "UDPR_3" if 'mapper' in self.lb_type \
                                or ('reducer' in self.lb_type and self.grlb_type == 'ud') \
                                else "X7"
        reduce_left_count = "UDPR_4"                # UDPR_4                            thread reg
        claiming_work = "UDPR_5"                    # UDPR_5                            thread reg
        claim_work_dest_nwid = "UDPR_6"             # UDPR_6                            thread reg
        source_ack_ev_word = "UDPR_9"               # UDPR_9                            thread reg
        saved_cont = self.saved_cont                # UDPR_15                           thread reg

        num = "UDPR_1"
        addr = "UDPR_7"                             # UDPR_7                            local reg
        scratch = self.scratch
        ev_word = self.ev_word                      # UDPR_14                           local reg

        tran.writeAction(f"subi {reduce_left_count} {reduce_left_count} {1}")
        tran.writeAction(f"movlr {WORD_SIZE*2}({'X8'}) {num} 0 {WORD_SIZE}")
        if self.debug_flag:
            tran.writeAction(f"movlr 0({'X8'}) {scratch[0]} 0 {WORD_SIZE}")
            tran.writeAction(f"sri {scratch[0]} {scratch[0]} 1")
            tran.writeAction(f"print 'Lane %u confirm local materialized count of key %u as %ld, previously %ld, entry address %lu, dram ptr %lu' X0 {scratch[0]} {num} {'X10'} X8 X9")
        tran.writeAction(f"after_setting_num: ble {num} {'X10'} claimed_kv_resolved")

        # There are kv pairs not yet read from dram
        tran.writeAction(f"muli {'X10'} {scratch[1]} {self.inter_kvpair_size * WORD_SIZE}")
        tran.writeAction(f"add X9 {scratch[1]} {scratch[1]}")

        tran.writeAction(f"resolving_kv: bge {'X10'} {num} claimed_kv_resolved")
        tran.writeAction(f"send_dmlm_ld_wret {scratch[1]} {self.ln_worker_launch_reducer_ev_label} {self.inter_kvpair_size} {scratch[0]}")
        tran.writeAction(f"addi {scratch[1]} {scratch[1]} {self.inter_kvpair_size * WORD_SIZE}")
        tran.writeAction(f"addi {reduce_left_count} {reduce_left_count} 1")
        tran.writeAction(f"subi {num} {num} 1")
        tran.writeAction(f"jmp resolving_kv")

        tran.writeAction(f"claimed_kv_resolved: bgti {reduce_left_count} {0} wait_for_reduce")

        # If after confirmation, no new kvs received, call worker to claim another work
        tran.writeAction(f"addi X2 {ev_word} 0")
        tran.writeAction(f"evlb {ev_word} {self.ln_worker_work_ev_label}")
        tran.writeAction(f"movir {scratch[0]} {self._worker_claim_key_flag}")
        tran.writeAction(f"sendr_wcont {ev_word} X2 {scratch[0]} {scratch[0]}")

        # Last work is local, update inter_key_executed_count
        if self.claim_multiple_work:
            tran.writeAction(f"movir {addr} {self.claimed_reduce_key_count_offset}")
            tran.writeAction(f"add X7 {addr} {addr}")
            tran.writeAction(f"movlr 0({addr}) {num} 0 {WORD_SIZE}")
        tran.writeAction(f"movir {addr} {self.inter_key_executed_count_offset}")
        if self.grlb_type == 'ud':
            tran.writeAction(f"add {base_addr} {addr} {addr}")
            tran.writeAction(f"update_inter_key_executed_count: movlr 0({addr}) {scratch[1]} 0 {WORD_SIZE}")
            if self.claim_multiple_work:
                tran.writeAction(f"add {scratch[1]} {num} {scratch[0]}")
            else:
                tran.writeAction(f"addi {scratch[1]} {scratch[0]} {1}")
            tran.writeAction(f"cswp {addr} {ev_word} {scratch[1]} {scratch[0]}")
            tran.writeAction(f"bne {ev_word} {scratch[1]} update_inter_key_executed_count")
        else:
            tran.writeAction(f"add {'X7'} {addr} {addr}")
            tran.writeAction(f"movlr 0({addr}) {scratch[1]} 0 {WORD_SIZE}")
            tran.writeAction(f"addi {scratch[1]} {scratch[0]} {1}")
            tran.writeAction(f"movrl {scratch[0]} 0({addr}) 0 {WORD_SIZE}")
        if self.debug_flag:
            tran.writeAction(f"print 'Lane %d acknowledged local key executed, increment from %d to %d' {'X0'} {scratch[1]} {scratch[0]}")

        tran.writeAction(f"wait_for_reduce: yield")
        return

    def __gen_worker_confirm_materialized_count(self, tran):
        '''
        Event: confirmed materialized count from source
        Operands:
                    X8:     Dram Pointer to kv array
                    X9:     Count of kvs materialized
        '''
        claimed_success = "UDPR_0"                  # UDPR_0                            thread reg
        part_end = "UDPR_2"                         # UDPR_2                            thread reg
        base_addr = "UDPR_3" if 'mapper' in self.lb_type \
                                or ('reducer' in self.lb_type and self.grlb_type == 'ud') \
                                else "X7"
        reduce_left_count = "UDPR_4"                # UDPR_4                            thread reg
        claiming_work = "UDPR_5"                    # UDPR_5                            thread reg
        claim_work_dest_nwid = "UDPR_6"             # UDPR_6                            thread reg
        source_ack_ev_word = "UDPR_9"               # UDPR_9                            thread reg
        saved_cont = self.saved_cont                # UDPR_15                           thread reg

        materialized_count = "UDPR_10"              # UDPR_10                           local reg
        scratch = self.scratch
        ev_word = self.ev_word                      # UDPR_14                           local reg

        tran.writeAction(f"subi {reduce_left_count} {reduce_left_count} {1}")
        if self.debug_flag:
            tran.writeAction(f"print 'Lane %u worker confirm_materialized_count has %d reduce left' X0 {reduce_left_count}")
            tran.writeAction(f"print 'Lane %u confirm extra materialized count of key %u with bin address %lu as %ld, previously %ld' X0 X10 X8 X9 {materialized_count}")
        tran.writeAction(f"beqi X9 {0} check_executed_count")

        # There are kv pairs not yet read from dram
        tran.writeAction(f"addi X8 {scratch[1]} {0}")
        tran.writeAction(f"movir {materialized_count} {0}")

        tran.writeAction(f"resolving_kv: bge {materialized_count} {'X9'} check_executed_count")
        tran.writeAction(f"send_dmlm_ld_wret {scratch[1]} {self.ln_worker_launch_reducer_ev_label} {self.inter_kvpair_size} {scratch[0]}")
        tran.writeAction(f"addi {scratch[1]} {scratch[1]} {self.inter_kvpair_size * WORD_SIZE}")
        tran.writeAction(f"addi {reduce_left_count} {reduce_left_count} 1")
        tran.writeAction(f"addi {materialized_count} {materialized_count} 1")
        tran.writeAction(f"jmp resolving_kv")

        # If all kvs are executed, send send acknowledgement back
        tran.writeAction(f"check_executed_count: bnei {reduce_left_count} 0 claimed_kv_resolved")
        if self.claim_multiple_work:
            tran.writeAction(f"movir {scratch[1]} {self.claimed_reduce_key_count_offset}")
            tran.writeAction(f"add X7 {scratch[1]} {scratch[1]}")
            tran.writeAction(f"movlr 0({scratch[1]}) {scratch[0]} 0 {WORD_SIZE}")
        tran.writeAction(f"sendr_wcont {source_ack_ev_word} {'X2'} {scratch[0]} {scratch[0]}")
        if self.debug_flag:
            tran.writeAction(f"sri {source_ack_ev_word} {scratch[0]} {32}")
            tran.writeAction(f"print 'sending event to ack to lane %u' {scratch[0]}")

        # Call worker to claim another work
        tran.writeAction(f"addi X2 {ev_word} 0")
        tran.writeAction(f"evlb {ev_word} {self.ln_worker_work_ev_label}")
        tran.writeAction(f"movir {scratch[0]} {self._worker_claim_key_flag}")
        tran.writeAction(f"sendr_wcont {ev_word} X2 {scratch[0]} {scratch[0]}")
        if self.debug_flag:
            tran.writeAction(f"print 'Return to work'")

        tran.writeAction(f"claimed_kv_resolved: yield")

    def __gen_worker_launch_reducer(self, tran):
        '''
        Event:  returned from dram request sent from worker_fetched_kv_ptr
                to launch reducer 
        Operands:   X8      Key
                    X9~n    Values
        '''
        inter_key       = "X8"
        inter_values    = [f"X{OB_REG_BASE + n + 1}" for n in range((self.inter_kvpair_size) - 1)]

        claimed_success = "UDPR_0"                  # UDPR_0                            thread reg
        part_end = "UDPR_2"                         # UDPR_2                            thread reg
        reduce_left_count = "UDPR_4"                # UDPR_4                            thread reg
        claiming_work = "UDPR_5"                    # UDPR_5                            thread reg
        claim_work_dest_nwid = "UDPR_6"             # UDPR_6                            thread reg
        source_ack_ev_word = "UDPR_9"               # UDPR_9                            thread reg
        claim_work_cont = "UDPR_11"                 #                                   thread reg
        saved_cont = self.saved_cont                # UDPR_15                           thread reg

        lm_base_reg     = f"X{GP_REG_BASE+7}"
        temp_value      = self.scratch[0]

        max_th_label = "push_back_to_queue"

        '''
        Event:      Reduce thread
        Operands:   X8: Key
                    X9 ~ Xn: Values
        '''

        if self.debug_flag:
            tran.writeAction(f"print 'Lane %lu worker_launch_reducer read key %ld value %lx from dram address %lu(0x%lx)' X0 X8 X9 X10 X10")

        if self.enable_intermediate and not self.enable_cache:
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

        else:
            tran = set_ev_label(tran, self.ev_word, self.kv_combine_ev_label, new_thread=True)
            tran.writeAction(f"sendops_wret {self.ev_word} {self.ln_worker_reducer_ret_ev_label} {inter_key} {self.inter_kvpair_size} {self.scratch[0]}")
            tran.writeAction(f"yield")

    def __gen_worker_reducer_ret(self, tran):
        '''
        Event:  returned from kv_reduce_ret
        '''

        claimed_success = "UDPR_0"                  # UDPR_0                            thread reg
        part_end = "UDPR_2"                         # UDPR_2                            thread reg
        base_addr = "UDPR_3" if ('reducer' in self.lb_type and self.grlb_type == 'ud') else "X7"
        reduce_left_count = "UDPR_4"                # UDPR_4                            thread reg
        claiming_work = "UDPR_5"                    # UDPR_5                            thread reg
        claim_work_dest_nwid = "UDPR_6"             # UDPR_6                            thread reg
        source_ack_ev_word = "UDPR_9"               # UDPR_9                            thread reg
        saved_cont = self.saved_cont                # UDPR_15                           thread reg

        addr = "UDPR_7"                             # UDPR_7                            local reg
        tmp = "UDPR_11"
        scratch = self.scratch                      # UDPR_12, UDPR_13                  local reg
        ev_word = self.ev_word                      # UDPR_14                           local reg

        tran.writeAction(f"subi {reduce_left_count} {reduce_left_count} 1")
        if self.debug_flag:
            tran.writeAction(f"print 'Lane %u worker reducer has %d reduce left' X0 {reduce_left_count}")

        # If not all reducer tasks have finished, yield
        tran.writeAction(f"bgti {reduce_left_count} 0 waiting_for_reducers")

        # Call worker to claim another work
        tran.writeAction(f"addi X2 {ev_word} 0")
        tran.writeAction(f"evlb {ev_word} {self.ln_worker_work_ev_label}")
        tran.writeAction(f"movir {scratch[0]} {self._worker_claim_key_flag}")
        tran.writeAction(f"sendr_wcont {ev_word} X2 {scratch[0]} {scratch[0]}")
        if self.debug_flag:
            tran.writeAction(f"print 'Return to work'")
        
        # If last work is local, update inter_key_executed_count
        tran.writeAction(f"beqi {claimed_success} {1} send_ack_to_source")
        tran.writeAction(f"movir {addr} {self.inter_key_executed_count_offset}")
        tran.writeAction(f"add {base_addr} {addr} {addr}")
        if self.grlb_type == 'ud':
            if self.claim_multiple_work:
                tran.writeAction(f"movir {scratch[0]} {self.claimed_reduce_key_count_offset}")
                tran.writeAction(f"add X7 {scratch[0]} {scratch[0]}")
                tran.writeAction(f"movlr 0({scratch[0]}) {tmp} 0 {WORD_SIZE}")
                tran.writeAction(f"update_inter_key_executed_count: movlr 0({addr}) {scratch[1]} 0 {WORD_SIZE}")
                tran.writeAction(f"add {scratch[1]} {tmp} {scratch[0]}")
            else:
                tran.writeAction(f"update_inter_key_executed_count: movlr 0({addr}) {scratch[1]} 0 {WORD_SIZE}")
                tran.writeAction(f"addi {scratch[1]} {scratch[0]} {1}")
            tran.writeAction(f"cswp {addr} {ev_word} {scratch[1]} {scratch[0]}")
            tran.writeAction(f"bne {ev_word} {scratch[1]} update_inter_key_executed_count")

        elif self.grlb_type == 'lane':
            tran.writeAction(f"movlr 0({addr}) {scratch[1]} 0 {WORD_SIZE}")
            tran.writeAction(f"addi {scratch[1]} {scratch[0]} {1}")
            tran.writeAction(f"movrl {scratch[0]} 0({addr}) 0 {WORD_SIZE}")
        if self.debug_flag:
            tran.writeAction(f"print 'Lane %d acknowledged local key executed, increment from %d to %d' {'X0'} {scratch[1]} {scratch[0]}")
        tran.writeAction(f"yield")

        # If last work is remote, send acknowledgement back
        if self.claim_multiple_work:
            tran.writeAction(f"send_ack_to_source: movir {addr} {self.claimed_reduce_key_count_offset}")
            tran.writeAction(f"add X7 {addr} {addr}")
            tran.writeAction(f"movlr 0({addr}) {scratch[0]} 0 {WORD_SIZE}")
            tran.writeAction(f"sendr_wcont {source_ack_ev_word} {'X2'} {scratch[0]} {scratch[0]}")
        else:
            tran.writeAction(f"send_ack_to_source: sendr_wcont {source_ack_ev_word} {'X2'} {scratch[0]} {scratch[0]}")

        if self.debug_flag:
            tran.writeAction(f"sri {source_ack_ev_word} {scratch[0]} {32}")
            tran.writeAction(f"print 'Lane %d acknowledging key executed to lane %d' X0 {scratch[0]}")

        if self.log_reduce_latency:
            tran.writeAction(f"perflog 1 0 'end'")

        tran.writeAction(f"waiting_for_reducers: yield")

        return

    def __gen_worker_early_finish(self, tran):
        '''
        Event:  Evoked when all lanes are visited to claim work yet no return
                Keep checking terminate bit till it's set
        '''

        part_end = "UDPR_2"                         # UDPR_2                            thread reg
        base_addr = "UDPR_3" if ('reducer' in self.lb_type and self.grlb_type == 'ud') else "X7"
        reduce_left_count = "UDPR_4"                # UDPR_4                            thread reg
        claiming_work = "UDPR_5"                    # UDPR_5                            thread reg
        claim_work_dest_nwid = "UDPR_6"             # UDPR_6                            thread reg
        source_ack_ev_word = "UDPR_9"               # UDPR_9                            thread reg
        saved_cont = self.saved_cont                # UDPR_15                           thread reg

        addr = "UDPR_7"                             # UDPR_7                            local reg
        dest = "UDPR_8"                             # UDPR_8                            local reg
        scratch = self.scratch                      # UDPR_12, UDPR_13                  local reg
        ev_word = self.ev_word                      # UDPR_14                           local reg

        if self.debug_flag:
            tran.writeAction(f"print 'Lane %d worker early finish, claiming_work %d ' X0 {claiming_work}")
        tran.writeAction(f"movir {addr} {self.terminate_bit_offset}")
        tran.writeAction(f"add {'X7'} {addr} {addr}")
        tran.writeAction(f"movlr 0({addr}) {scratch[0]} 0 {WORD_SIZE}")
        tran.writeAction(f"beqi {scratch[0]} {1} terminate_bit_set")

        # if self.sync_terminate:
        #     # If terminate bit not set, check if need to check whether all local keys are executed
        #     tran.writeAction(f"bgei {claiming_work} {2} spin_lock")


        # Check whether all local keys are executed
        tran.writeAction(f"movir {addr} {self.inter_key_resolved_count_offset}")
        tran.writeAction(f"add {base_addr} {addr} {addr}")
        tran.writeAction(f"movlr 0({addr}) {scratch[0]} 0 {WORD_SIZE}")
        tran.writeAction(f"movir {addr} {self.inter_key_executed_count_offset}")
        tran.writeAction(f"add {base_addr} {addr} {addr}")
        tran.writeAction(f"movlr 0({addr}) {scratch[1]} 0 {WORD_SIZE}")
        tran.writeAction(f"bgt {scratch[0]} {scratch[1]} spin_lock")
        # If so, send to lane_master
        tran.writeAction(f"movir {scratch[0]} {self._claiming_finish_flag}")
        tran.writeAction(f"sendr_wcont {saved_cont} {'X2'} {scratch[0]} {scratch[0]}")
        tran.writeAction(f"movir {claiming_work} {3}")
        if self.print_claiming_work:
            tran.writeAction(f"print 'setting claiming_work to 3'")
        tran.writeAction(f"jmp terminate_bit_set")

        # If not all received kv resolved, spin lock
        tran.writeAction(f"spin_lock: sendr_wcont {'X2'} {'X1'} {scratch[0]} {scratch[0]}")
        if self.debug_flag:
            if self.record_unresolved_kv_count:
                tran.writeAction(f"movir {addr} {self.unresolved_kv_count_offset}")
                tran.writeAction(f"add {base_addr} {addr} {addr}")
                tran.writeAction(f"movlr 0({addr}) {self.scratch[0]} 0 {WORD_SIZE}")
                tran.writeAction(f"print 'Early Finish: Remaining unresolved_kv_count %d' {scratch[0]}")
            tran.writeAction(f"movir {addr} {self.inter_key_received_count_offset}")
            tran.writeAction(f"add {base_addr} {addr} {addr}")
            tran.writeAction(f"movlr 0({addr}) {self.scratch[1]} 0 {WORD_SIZE}")
            tran.writeAction(f"movir {addr} {self.inter_key_executed_count_offset}")
            tran.writeAction(f"add {base_addr} {addr} {addr}")
            tran.writeAction(f"movlr 0({addr}) {self.scratch[0]} 0 {WORD_SIZE}")
            tran.writeAction(f"movir {addr} {self.inter_key_resolved_count_offset}")
            tran.writeAction(f"add {base_addr} {addr} {addr}")
            tran.writeAction(f"movlr 0({addr}) {ev_word} 0 {WORD_SIZE}")
            tran.writeAction(f"print 'Early Finish: Executed count %lu, Resolved count %lu, Received count %lu' {scratch[0]} {ev_word} {scratch[1]}")
        tran.writeAction(f"yield")

        # Reach terminating condition, send to worker_terminate
        tran.writeAction(f"terminate_bit_set: sendr_reply {scratch[0]} {scratch[0]} {scratch[0]}")
        tran.writeAction(f"yield")

        return

    def __gen_worker_terminate(self, tran):
        claimed_success = "UDPR_0"                  # UDPR_0                            thread reg
        part_end = "UDPR_2"                         # UDPR_2                            thread reg
        base_addr = "UDPR_3" if 'mapper' in self.lb_type \
                                or ('reducer' in self.lb_type and self.grlb_type == 'ud') \
                                else "X7"
        reduce_left_count = "UDPR_4"                # UDPR_4                            thread reg
        claiming_work = "UDPR_5"                    # UDPR_5                            thread reg
        claim_work_dest_nwid = "UDPR_6"             # UDPR_6                            thread reg
        source_ack_ev_word = "UDPR_9"               # UDPR_9                            thread reg
        saved_cont = self.saved_cont                # UDPR_15                           thread reg

        addr = "UDPR_7"                             # UDPR_7                            local reg
        dest = "UDPR_8"                             # UDPR_8                            local reg
        scratch = self.scratch                      # UDPR_12, UDPR_13                  local reg
        ev_word = self.ev_word                      # UDPR_14                           local reg

        if self.sync_terminate:
            # Reach terminating condition
            tran.writeAction(f"movir {scratch[0]} {self._finish_flag}")
            tran.writeAction(f"sendr_wcont {saved_cont} X2 {scratch[0]} {scratch[0]}")
            if self.debug_flag:
                tran.writeAction(f"print 'Lane %u terminates.' X0")
            tran.writeAction(f"yieldt")

        else:
            if self.debug_flag:
                tran.writeAction(f"print 'Lane %u terminates.' X0")
            tran.writeAction(f"yieldt")

        return

    def __gen_worker_helper(self, tran):

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
        ln_remote_mapper_finished_tran   = self.state.writeTransition("eventCarry", self.state, self.state, self.ln_remote_mapper_finished_ev_label)


        self.__gen_mapper_control_init(ln_mapper_control_init_tran)
        self.__gen_mapper_control_rd_part(ln_mapper_control_rd_part_tran)
        self.__gen_mapper_control_get_ret(ln_mapper_control_get_ret_tran)
        self.__gen_mapper_control_loop(ln_mapper_control_loop_tran)
        self.__gen_remote_mapper_finished(ln_remote_mapper_finished_tran)

        return

    def __gen_mapper_control_init(self, tran):
        '''
        Event:  Launched from worker_work as a map partition is claimed 
        Operands:   X8      Partition pointer
                    X9      Ud master evw of which ud this partition is claimed from
        Cont word:  X1      Worker_work event
        '''
        num_th_active   = "X16"
        max_map_th      = "X17"
        ud_mstr_evw     = "X18"
        next_iter_evw   = "X20"
        kv_map_evw      = "X21"
        num_map_gen_addr= "X22"
        iter_flag       = "X23"
        iterator        = [f"X{GP_REG_BASE + k + 7}" for k in range(self.in_kvset_iter_size)]
        
        iterator_ops = [f"X{OB_REG_BASE + k}" for k in range(self.in_kvset_iter_size)]


        if self.debug_flag:
            tran.writeAction(f"print '[DEBUG][NWID %ld] worker_mapper_controller initialized with partition ptr at %lu(0x%lx) ' {'X0'} {'X8'} {'X8'}")
        tran.writeAction(f"addi X1 {self.saved_cont} 0")
        tran.writeAction(f"addi X9 {ud_mstr_evw} 0")
        tran.writeAction(f"send_dmlm_ld_wret X8 {self.ln_mapper_control_rd_part_ev_label} {max(2, self.in_kvset_iter_size)} {self.scratch[0]}")
        # Initialize local counter and event words.
        tran.writeAction(f"movir {num_th_active} 0")
        tran.writeAction(f"movir {max_map_th} {self.max_map_th_per_lane}")
        tran.writeAction(f"movir {self.num_map_gen} 0")
        tran.writeAction(f"movir {num_map_gen_addr} {self.map_ctr_offset}")
        tran.writeAction(f"add {'X7'} {num_map_gen_addr} {num_map_gen_addr}")

        # tran.writeAction(f"movlr 0({num_map_gen_addr}) {self.scratch[0]} 0 {WORD_SIZE}")
        # tran.writeAction(f"print 'mapper_control_init, num_map %lu.' {self.scratch[0]}")

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
        ud_mstr_evw     = "X18"
        next_iter_evw   = "X20"
        kv_map_evw      = "X21"
        num_map_gen_addr= "X22"
        iter_flag       = "X23"
        iterator        = [f"X{GP_REG_BASE + k + 7}" for k in range(self.in_kvset_iter_size)]
        
        iterator_ops = [f"X{OB_REG_BASE + k}" for k in range(self.in_kvset_iter_size)]

        empty_part_label    = "lane_master_empty_partition"

        if self.debug_flag:
            tran.writeAction(f"print ' '")
            tran.writeAction(f"print '[DEBUG][NWID %ld][{self.ln_mapper_control_rd_part_ev_label}] Event <{self.ln_mapper_control_rd_part_ev_label}> ev_word = %lu return from DRAM addr = %lu(0x%lx)' \
                {'X0'} {'EQT'} {f'X{OB_REG_BASE+self.in_kvset_iter_size}'} {f'X{OB_REG_BASE+self.in_kvset_iter_size}'}")
            tran.writeAction(f"print '[DEBUG][NWID %ld][{self.ln_mapper_control_rd_part_ev_label}] Operands: iterator = [{''.join(['%lu(0x%lx), ' for _ in range(self.in_kvset_iter_size)])}]' \
                {'X0'} {' '.join([f'{n} {n} ' for n in iterator_ops])}")

        # Start iterating on the assigned partition and set flag
        self.in_kvset.get_next_pair(tran, next_iter_evw, kv_map_evw, self.kv_map_ev_label, iterator_ops, self.scratch, empty_part_label)
        tran.writeAction(f"addi {num_th_active} {num_th_active} 1")
        tran.writeAction(F"movir {iter_flag} {FLAG}")
        tran.writeAction("yield")
        
        # If the partition is empty, return to worker and terminate
        tran.writeAction(f"{empty_part_label}: movir {self.scratch[1]} {self._worker_claim_key_flag}")
        tran.writeAction(f"sendr_wcont {ud_mstr_evw} {'X2'} {self.num_map_gen} {self.num_map_gen}")
        # tran.writeAction(f"print 'return to ud master, ev_word %lx, num_map_gen %lu' {ud_mstr_evw} {self.num_map_gen}")
        tran.writeAction(f"sendr_wcont {self.saved_cont} {'X2'} {self.scratch[1]} {self.num_map_gen}")
        if self.debug_flag:
            tran.writeAction(f"print '[DEBUG][NWID %ld][{self.ln_mapper_control_rd_part_ev_label}] Empty partition!'")
        tran.writeAction(f"yieldt")

        return

    def __gen_mapper_control_get_ret(self, tran):
        '''
        Event:      Receive the next key-value pair from the assigned partition
        Operands:   X8 ~ Xn: Updated iterator and key-value pair.
        '''

        num_th_active   = "X16"
        max_map_th      = "X17"
        ud_mstr_evw     = "X18"
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
        # tran.writeAction(f"print 'send to map'")
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
        tran.writeAction(f"sendr_wcont {ud_mstr_evw} {'X2'} {self.scratch[1]} {self.num_map_gen}")
        # tran.writeAction(f"print 'return to ud master, ev_word %lx, num_map_gen %lu' {ud_mstr_evw} {self.num_map_gen}")
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
        ud_mstr_evw     = "X18"
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
        tran.writeAction(f"sendr_wcont {ud_mstr_evw} {'X2'} {self.num_map_gen} {self.num_map_gen}")
        # tran.writeAction(f"print 'return to ud master, ev_word %lx, num_map_gen %lu' {ud_mstr_evw} {self.num_map_gen}")
        if self.debug_flag:
            tran.writeAction(f"sri {ud_mstr_evw} {self.scratch[0]} {32 + 6}")
            tran.writeAction(f"andi {self.scratch[0]} {self.scratch[0]} {0b11}")
            tran.writeAction(f"print 'Lane %d mapper controller return to ud %d master' X0 {self.scratch[0]}")
        tran.writeAction(f"sendr_wcont {self.saved_cont} {'X2'} {self.scratch[1]} {self.num_map_gen}")
        tran.writeAction(f"mov_imm2reg {self.num_map_gen} 0")
        tran.writeAction(f"movrl {self.num_map_gen} 0({num_map_gen_addr}) 0 8")
        tran.writeAction(f"yieldt")

        tran.writeAction(f"{mapper_control_cont_label}: yield")

        return

    def __gen_remote_mapper_finished(self, tran):
        tran.writeAction(f"yieldt")
        return



    '''
    Receiver threads are single-event threads, receiving
    1. kvs from kv_emit and materialize them
    2. claim assertion messages from other workers
    3. kvs from static hashed lane to reduce

    2 cache space:
        intermediate_cache: Each entry contains FOUR words, [*key, ptr to materize array / event word at claimed lane, num_dram_req_sent, num_dram_req_ret]
                            *key here is key shifted left one bit, with lowest bit as is_claimed bit
        materialize_kv_cache: each entry contains self.inter_kvpair_size words, kv pairs to be materialized
    '''

    def __gen_receiver(self):
        
        ln_receiver_claim_work_tran = self.state.writeTransition("eventCarry", self.state, self.state, self.ln_receiver_claim_work_ev_label)
        ln_receiver_set_terminate_bit_tran = self.state.writeTransition("eventCarry", self.state, self.state, self.ln_receiver_set_terminate_bit_ev_label)
        ln_receiver_set_terminate_bit_ret_tran = self.state.writeTransition("eventCarry", self.state, self.state, self.ln_receiver_set_terminate_bit_ret_ev_label)

        # self.debug_flag = True
        self.__gen_receiver_claim_work(ln_receiver_claim_work_tran)
        self.__gen_receiver_set_terminate_bit(ln_receiver_set_terminate_bit_tran)
        self.__gen_receiver_set_terminate_bit_ret(ln_receiver_set_terminate_bit_ret_tran)

        if 'reducer' in self.lb_type:
            ln_receiver_receive_kv_tran = self.state.writeTransition("eventCarry", self.state, self.state, self.ln_receiver_receive_kv_ev_label)
            ln_receiver_fetched_kv_ptr_for_cache_tran = self.state.writeTransition("eventCarry", self.state, self.state, self.ln_receiver_fetched_kv_ptr_for_cache_ev_label)
            ln_receiver_materialize_ret_tran = self.state.writeTransition("eventCarry", self.state, self.state, self.ln_receiver_materialize_ret_ev_label)
            ln_receiver_update_unresolved_kv_count_tran = self.state.writeTransition("eventCarry", self.state, self.state, self.ln_receiver_update_unresolved_kv_count_ev_label)
            ln_receiver_acknowledge_key_executed_tran = self.state.writeTransition("eventCarry", self.state, self.state, self.ln_receiver_acknowledge_key_executed_ev_label)

            if self.do_all_reduce:
                self.__gen_receiver_receive_kv_do_all_reduce(ln_receiver_receive_kv_tran)
            else:
                self.__gen_receiver_receive_kv(ln_receiver_receive_kv_tran)
            # self.debug_flag = True
            self.__gen_receiver_fetched_kv_ptr_for_cache(ln_receiver_fetched_kv_ptr_for_cache_tran)
            # self.debug_flag = False
            self.__gen_receiver_materialize_ret(ln_receiver_materialize_ret_tran)
            self.__gen_receiver_update_unresolved_kv_count(ln_receiver_update_unresolved_kv_count_tran)
            self.__gen_receiver_acknowledge_key_executed(ln_receiver_acknowledge_key_executed_tran)
            # self.debug_flag = False

            if self.grlb_type == 'ud':
                ln_receiver_check_materialized_count_tran = self.state.writeTransition("eventCarry", self.state, self.state, self.ln_receiver_check_materialized_count_ev_label)
                self.__gen_receiver_check_materialized_count(ln_receiver_check_materialized_count_tran)
        

        return

    def __gen_receiver_receive_kv(self, tran):

        '''
        Event:  returned from kv_emit, to decide whether materialize the intermediate kv or send to worker that claimed it
        Operands:   X8-n  intermediate kv pair

        
        '''

        bin_lock_addr = "UDPR_0"                    # UDPR_0                            local reg
        cswp_ret = "UDPR_1"                         # UDPR_1                            local reg
        materializing_cache_start = "UDPR_0"        # UDPR_0                            local reg
        materializing_cache_end = "UDPR_1"          # UDPR_1                            local reg
        materializing_cache_empty = "UDPR_2"        # UDPR_2                            local reg
        num = "UDPR_3"                              # UDPR_3                            local reg
        base_addr = "UDPR_4"                        # UDPR_4                            local reg

        cache_count = "UDPR_6"                      # UDPR_6                            local reg
        addr = "UDPR_7"                             # UDPR_7                            local reg
        intermediate_ptr = "UDPR_8"                 # UDPR_8                            local reg
        is_claimed = "UDPR_9"                       # UDPR_9                            local reg
        key = "UDPR_10"                             # UDPR_10                           local reg
        scratch = self.scratch                      # [UDPR_12, UDPR_13]                local reg
        lm_reg = self.scratch[1]                    # UDPR_13                           local reg
        ev_word = self.ev_word                      # UDPR_14                           local reg
        entry_addr = "UDPR_15"                      # UDPR_15                           local reg


        iterate_key_label = "find_cached_key"
        key_hit_label = "cache_hit"
        key_not_hit_label = "cache_all_visited"
        check_kv_ptr_label = "check_materializing_ptr"
        materialize_kv_label = "store_kv"
        init_cache_kv_label = "init_cache_kv"
        update_unresolved_count_label = "update_unresolved_count"



        if self.debug_flag:
            tran.writeAction(f"print '[LB_DEBUG] Lane %u receives key %ld value %lu(0x%lx)' X0 X8 X9 X9")
        if self.log_kv_latency:
            tran.writeAction(f"perflog 1 0 '%lu receive_kv start' X8")

        mask = cache_count

        # Access bin entry
        if self.grlb_type == 'ud':
            # Get Lane 0 spd start address
            tran.writeAction(f"andi {'X0'} {scratch[0]} {63}")
            tran.writeAction(f"sli {scratch[0]} {scratch[0]} {int(log2(SPD_BANK_SIZE))}")
            tran.writeAction(f"sub {'X7'} {scratch[0]} {base_addr}")

            # Hash the key to get bin id
            tran.writeAction(f"movir {mask} {(self.intermediate_cache_num_bins << int(log2(64))) - 1}")
            tran.writeAction(f"addi {base_addr} {key} {0}")
            tran.writeAction(f"hash {'X8'} {key}")
            tran.writeAction(f"and {key} {mask} {key}")

            # Reach bin entry
            tran.writeAction(f"divi {key} {addr} {self.intermediate_cache_num_bins}")
            tran.writeAction(f"modi {key} {key} {self.intermediate_cache_num_bins}")
            tran.writeAction(f"sli {addr} {addr} {int(log2(SPD_BANK_SIZE))}")
            tran.writeAction(f"add {base_addr} {addr} {addr}")
            tran.writeAction(f"movir {scratch[0]} {self.intermediate_cache_bins_offset}")
            tran.writeAction(f"add {scratch[0]} {addr} {addr}")
            tran.writeAction(f"muli {key} {key} {WORD_SIZE * 2}")
            tran.writeAction(f"add {key} {addr} {addr}")
            tran.writeAction(f"addi {addr} {bin_lock_addr} {WORD_SIZE}")
            tran.writeAction(f"subi {addr} {addr} {(self.intermediate_cache_entry_size - 1) * WORD_SIZE}")

            # Locate returned key in the intermediate_cache
            if self.debug_flag:
                tran.writeAction(f"print 'Lane %u start to look for cached key %ld starting from spd address %lu' X0 X8 {addr}")
            tran.writeAction(f"{iterate_key_label}: movlr {(self.intermediate_cache_entry_size - 1) * WORD_SIZE}({addr}) {scratch[0]} 0 {WORD_SIZE}")
            tran.writeAction(f"beqi {scratch[0]} -1 {key_not_hit_label}")
            tran.writeAction(f"addi {scratch[0]} {addr} {0}")
            tran.writeAction(f"movlr 0({addr}) {key} 0 {WORD_SIZE}")
            tran.writeAction(f"sri {key} {scratch[0]} 1")
            tran.writeAction(f"beq {scratch[0]} {'X8'} {key_hit_label}")
            tran.writeAction(f"jmp {iterate_key_label}")

        elif self.grlb_type == 'lane':
            # Hash the key to get bin id
            tran.writeAction(f"movir {mask} {self.intermediate_cache_num_bins -1}")
            tran.writeAction(f"addi {'X0'} {key} {0}")
            tran.writeAction(f"hash {'X8'} {key}")
            tran.writeAction(f"and {key} {mask} {key}")

            # Reach bin entry
            tran.writeAction(f"movir {addr} {self.intermediate_cache_bins_offset}")
            tran.writeAction(f"add {'X7'} {addr} {addr}")
            tran.writeAction(f"muli {key} {key} {WORD_SIZE}")
            tran.writeAction(f"add {key} {addr} {addr}")
            tran.writeAction(f"subi {addr} {addr} {(self.intermediate_cache_entry_size - 1) * WORD_SIZE}")

            # Locate returned key in the intermediate_cache
            if self.debug_flag:
                tran.writeAction(f"print 'Lane %u start to look for cached key %ld starting from spd address %lu' X0 X8 {addr}")
            tran.writeAction(f"{iterate_key_label}: movlr {(self.intermediate_cache_entry_size - 1) * WORD_SIZE}({addr}) {scratch[0]} 0 {WORD_SIZE}")
            tran.writeAction(f"beqi {scratch[0]} -1 {key_not_hit_label}")
            tran.writeAction(f"addi {scratch[0]} {addr} {0}")
            tran.writeAction(f"movlr 0({addr}) {key} 0 {WORD_SIZE}")
            tran.writeAction(f"sri {key} {scratch[0]} 1")
            tran.writeAction(f"beq {scratch[0]} {'X8'} {key_hit_label}")
            tran.writeAction(f"jmp {iterate_key_label}")



        # If found, check if the key is claimed
        # if claimed, send the intermediate kv to cached location
        # if not claimed, check if the materializing pointer is cached
        tran.writeAction(f"{key_hit_label}: addi {addr} {entry_addr} {0}")
        if self.grlb_type == 'ud':
            # First read key again
            tran.writeAction(f"movlr {0}({entry_addr}) {key} 0 {WORD_SIZE}")
            if self.debug_flag:
                tran.writeAction(f"print 'Lane %u key %ld hit' X0 X8")
            # Read num
            tran.writeAction(f"movlr {WORD_SIZE * 2}({entry_addr}) {num} 0 {WORD_SIZE}")
            # Then read dram address / event word
            tran.writeAction(f"movlr {WORD_SIZE}({entry_addr}) {ev_word} 0 {WORD_SIZE}")
            tran.writeAction(f"andi {key} {is_claimed} 1")
            tran.writeAction(f"sri {key} {key} 1")
            tran.writeAction(f"beqi {is_claimed} 0 {check_kv_ptr_label}")

        elif self.grlb_type == 'lane':
            tran.writeAction(f"andi {key} {is_claimed} 1")
            if self.debug_flag:
                tran.writeAction(f"print 'Lane %u key %ld hit' X0 X8")
            tran.writeAction(f"sri {key} {key} 1")
            tran.writeAction(f"beqi {is_claimed} 0 {check_kv_ptr_label}")
            
        
        # If claimed, send to cached event word
        tran.writeAction(f"key_claimed: evii {scratch[0]} {self.ln_receiver_update_unresolved_kv_count_ev_label} {255} {5}")
        tran.writeAction(f"movlr {WORD_SIZE}({entry_addr}) {ev_word} 0 {WORD_SIZE}")
        tran.writeAction(f"sendops_wcont {ev_word} {scratch[0]} X8 {self.inter_kvpair_size}")

        if self.debug_flag:
            tran.writeAction(f"sri {ev_word} {scratch[0]} {32}")
            tran.writeAction(f"print '[LB_DEBUG] Key claimed, receiver_receive_key send key %ld value %lu(0x%lx) to lane %d' X8 X9 X9 {scratch[0]}")
        if self.log_kv_latency:
            tran.writeAction(f"perflog 1 0 '%lu receive_kv end' X8")

        tran.writeAction(f"jmp receive_kv_end")        



        # If found but NOT claimed, check if the materializing pointer is cached
        if self.grlb_type == 'ud':
            # If num >= 0, dram ptr already came back
            if self.debug_flag:
                tran.writeAction(f"{check_kv_ptr_label}: print 'Lane %u key %ld materialized count %ld' X0 X8 {num}")
                tran.writeAction(f"blti {num} 0 {init_cache_kv_label}")
            else:
                tran.writeAction(f"{check_kv_ptr_label}: blti {num} 0 {init_cache_kv_label}")
            

        elif self.grlb_type == 'lane':
            tran.writeAction(f"{check_kv_ptr_label}: movlr {WORD_SIZE * 2}({entry_addr}) {num} 0 {WORD_SIZE}")
            if self.debug_flag:
                tran.writeAction(f"print 'Lane %u key %ld materialized count %ld' X0 X8 {num}")
            # If the materializing pointer is cached, materialize the kv
            tran.writeAction(f"bgti {num} 0 {materialize_kv_label}")
            # If the materializing pointer is NOT cached, push the kv to the end of materializing cache
            tran.writeAction(f"jmp {init_cache_kv_label}")



        # If the materializing pointer is cached, materialize the kv and update stored number in dram
        if self.grlb_type == 'ud':
            # If key is NOT claimed at this point, 
            # meaning the dest read before is dram ptr
            tran.writeAction(f"double_check_key: movlr {0}({entry_addr}) {scratch[0]} 0 {WORD_SIZE}")
            tran.writeAction(f"andi {scratch[0]} {is_claimed} 1")
            tran.writeAction(f"beqi {is_claimed} 0 {materialize_kv_label}")
            tran.writeAction(f"movlr {WORD_SIZE}({entry_addr}) {ev_word} 0 {WORD_SIZE}")
            tran.writeAction(f"jmp key_claimed")

            # Increment num by 1
            tran.writeAction(f"{materialize_kv_label}: addi {entry_addr} {scratch[1]} {2 * WORD_SIZE}")
            tran.writeAction(f"update_materialize_count: movlr {WORD_SIZE * 2}({entry_addr}) {num} 0 {WORD_SIZE}")
            tran.writeAction(f"addi {num} {scratch[0]} 1")
            tran.writeAction(f"cswp {scratch[1]} {cswp_ret} {num} {scratch[0]}")
            tran.writeAction(f"beq {cswp_ret} {num} updated_materialize_count")
            tran.writeAction(f"movlr 0({entry_addr}) {scratch[0]} 0 {WORD_SIZE}")
            tran.writeAction(f"andi {scratch[0]} {scratch[0]} {1}")
            tran.writeAction(f"beqi {scratch[0]} {1} key_claimed")
            tran.writeAction(f"jmp {materialize_kv_label}")

            # Calculate dram address
            tran.writeAction(f"updated_materialize_count: muli {num} {scratch[1]} {self.inter_kvpair_size * WORD_SIZE}")
            tran.writeAction(f"add {ev_word} {scratch[1]} {scratch[0]}")
            if self.debug_flag:
                tran.writeAction(f"print 'Lane %u materializing key %ld, dram bin address %lu(0x%lx) as the %ld-th kv' X0 X8 {ev_word} {ev_word} {num}")

        elif self.grlb_type == 'lane':
            # Calculate dram address
            tran.writeAction(f"{materialize_kv_label}: movlr {WORD_SIZE}({entry_addr}) {scratch[0]} 0 {WORD_SIZE}")
            tran.writeAction(f"muli {num} {scratch[1]} {self.inter_kvpair_size * WORD_SIZE}")
            # Update num_dram_req_sent
            tran.writeAction(f"addi {num} {num} 1")
            tran.writeAction(f"movrl {num} {WORD_SIZE * 2}({addr}) 0 {WORD_SIZE}")
            tran.writeAction(f"add {scratch[0]} {scratch[1]} {scratch[0]}")

        # Set return event word
        tran.writeAction(f"evii {ev_word} {self.ln_receiver_materialize_ret_ev_label} 255 5")
        # Send dram req
        tran.writeAction(f"movir {lm_reg} {self.send_buffer_offset}")
        tran.writeAction(f"add {'X7'} {lm_reg} {lm_reg}")
        for i in range(self.inter_kvpair_size):
            tran.writeAction(f"movrl X{8+i} {WORD_SIZE*i}({lm_reg}) 0 {WORD_SIZE}")
        tran.writeAction(f"send_dmlm {scratch[0]} {ev_word} {lm_reg} {self.inter_kvpair_size}")
        if self.debug_flag:
            tran.writeAction(f"print '[LB_DEBUG] receiver_receive_key materialize key %u value %lu(0x%lx) to Dram %lu(0x%lx)' X8 X9 X9 {scratch[0]} {scratch[0]}")
        if self.log_kv_latency:
            tran.writeAction(f"perflog 1 0 '%lu receive_kv end' X8")

        tran.writeAction(f"jmp receive_kv_end") 



        # If not found, 
        if self.grlb_type == 'ud':
            # 1. ACQUIRE bin lock for adding entry
            tran.writeAction(f"{key_not_hit_label}: cswpi {bin_lock_addr} {scratch[0]} {0} {1}")
            tran.writeAction(f"beqi {scratch[0]} {1} {iterate_key_label}")

            # 2. Find the tail of intermediate_cache
            # 2.1 Get inter_key_received_count
            if self.debug_flag:
                tran.writeAction(f"print 'Lane %d grabbed bin lock for new key %ld' X0 X8")
            tran.writeAction(f"movir {scratch[1]} {self.inter_key_received_count_offset}")
            tran.writeAction(f"add {base_addr} {scratch[1]} {scratch[1]}")
            # 2.2 Occupy tail of intermediate_cache: Atomic update inter_key_received_count
            tran.writeAction(f"update_inter_key_count: movlr 0({scratch[1]}) {num} 0 {WORD_SIZE}")
            tran.writeAction(f"addi {num} {scratch[0]} {1}")
            tran.writeAction(f"cswp {scratch[1]} {cswp_ret} {num} {scratch[0]}")
            tran.writeAction(f"bne {cswp_ret} {num} update_inter_key_count")
            if self.debug_flag:
                tran.writeAction(f"sri X0 {scratch[1]} 6")
                tran.writeAction(f"print '[LB_DEBUG] Lane %u receives new key %ld as ud %lu %lu-th key' X0 X8 {scratch[1]} {num}")

            # 2.3 Reach tail of intermediate_cache
            tran.writeAction(f"divi {num} {scratch[1]} {self.intermediate_cache_count}")
            tran.writeAction(f"sli {scratch[1]} {scratch[1]} {int(log2(SPD_BANK_SIZE))}")
            tran.writeAction(f"add {base_addr} {scratch[1]} {scratch[1]}")
            tran.writeAction(f"movir {scratch[0]} {self.intermediate_cache_offset}")
            tran.writeAction(f"add {scratch[0]} {scratch[1]} {scratch[1]}")
            tran.writeAction(f"modi {num} {scratch[0]} {self.intermediate_cache_count}")
            tran.writeAction(f"muli {scratch[0]} {scratch[0]} {(self.intermediate_cache_entry_size)*WORD_SIZE}")
            tran.writeAction(f"add {scratch[0]} {scratch[1]} {entry_addr}")

            # 3. Write entry
            tran.writeAction(f"movir {scratch[0]} {-1}")
            # 3.0 Set key as -1, indicating writing key entry. LOCK FOR CLAIM_WORK
            tran.writeAction(f"movrl {scratch[0]} {0}({entry_addr}) 0 {WORD_SIZE}")
            # 3.1 Set dest as -1, indicating needing cache. LOCK FOR RECEIVE_KV_PTR
            tran.writeAction(f"movrl {scratch[0]} {WORD_SIZE}({entry_addr}) 0 {WORD_SIZE}")
            # 3.2 Set number materialized as -1 indicating materializing address hasn't returned. LOCK FOR RECEIVE_KEY
            tran.writeAction(f"movrl {scratch[0]} {WORD_SIZE*2}({entry_addr}) 0 {WORD_SIZE}")
            # 3.3 Set entry pointer word as -1, indicating this entry as end of the bin. FOR HASHTABLE
            tran.writeAction(f"movrl {scratch[0]} {WORD_SIZE*3}({entry_addr}) 0 {WORD_SIZE}")
            # 3.4. Cache the key in scratchpad at the end of the intermediate_cache
            tran.writeAction(f"sli X8 {key} 1")
            tran.writeAction(f"movrl {key} 0({entry_addr}) 0 {WORD_SIZE}")
            # 3.5 Write the tail of intermediate_cache to current entry's pointer word
            tran.writeAction(f"movrl {entry_addr} {(self.intermediate_cache_entry_size - 1)*WORD_SIZE}({addr}) 0 {WORD_SIZE}")

            # 4. Release bin lock
            tran.writeAction(f"movir {scratch[0]} {0}")
            tran.writeAction(f"movrl {scratch[0]} 0({bin_lock_addr}) 0 {WORD_SIZE}")

            # 5. Read kv_ptr from dram
            dest_nwid = key
            tran.writeAction(f"movir {addr} {self.intermediate_ptr_offset}")
            tran.writeAction(f"add {base_addr} {addr} {addr}")
            tran.writeAction(f"movlr 0({addr}) {scratch[1]} 0 {WORD_SIZE}")
            tran.writeAction(f"muli {num} {scratch[0]} {WORD_SIZE}")
            tran.writeAction(f"add {scratch[0]} {scratch[1]} {scratch[1]}")
            tran.writeAction(f"evii {ev_word} {self.ln_receiver_fetched_kv_ptr_for_cache_ev_label} {255} {5}")
            tran.writeAction(f"ev {ev_word}  {ev_word}  {'X0'} {'X0'} {8}")
            tran.writeAction(f"send_dmlm_ld {scratch[1]} {ev_word} {1}")
            if self.debug_flag:
                tran.writeAction(f"print '[LB_DEBUG] receiver_receive_key sending dram ptr request to %lu for key %ld' {scratch[1]} X8")

        elif self.grlb_type == 'lane':
            # 1. set is_claim bit to 0
            tran.writeAction(f"{key_not_hit_label}: sli X8 {key} 1")

            # 2. Find the tail of intermediate_cache
            # 2.1 Load inter_key_received_count
            tran.writeAction(f"movir {scratch[1]} {self.inter_key_received_count_offset}")
            tran.writeAction(f"add {'X7'} {scratch[1]} {scratch[1]}")
            tran.writeAction(f"movlr 0({scratch[1]}) {num} 0 {WORD_SIZE}")
            if self.debug_flag:
                tran.writeAction(f"print '[LB_DEBUG] Lane %u receives new key %ld as %lu-th key' X0 X8 {num}")
            # 2.2 Reach tail of intermediate_cache
            tran.writeAction(f"movir {scratch[0]} {self.intermediate_cache_offset}")
            tran.writeAction(f"add {'X7'} {scratch[0]} {scratch[0]}")
            tran.writeAction(f"muli {num} {scratch[1]} {(self.intermediate_cache_entry_size)*WORD_SIZE}")
            tran.writeAction(f"add {scratch[0]} {scratch[1]} {scratch[1]}")

            # 3. Write the tail of intermediate_cache to current entry's pointer word
            tran.writeAction(f"movrl {scratch[1]} {(self.intermediate_cache_entry_size - 1)*WORD_SIZE}({addr}) 0 {WORD_SIZE}")

            # 4. cache the key in scratchpad at the end of the intermediate_cache
            tran.writeAction(f"movrl {key} 0({scratch[1]}) 0 {WORD_SIZE}")
            # Set number materialized as 0 indicating materializing address hasn't returned
            tran.writeAction(f"movir {scratch[0]} {0}")
            tran.writeAction(f"movrl {scratch[0]} {WORD_SIZE*2}({scratch[1]}) 0 {WORD_SIZE}")
            # Set pointer word as -1, indicating this entry as end of the bin
            tran.writeAction(f"movir {scratch[0]} {-1}")
            tran.writeAction(f"movrl {scratch[0]} {WORD_SIZE*3}({scratch[1]}) 0 {WORD_SIZE}")

            # 2.5 Update inter_key_received_count
            tran.writeAction(f"movir {addr} {self.inter_key_received_count_offset}")
            tran.writeAction(f"add {'X7'} {addr} {addr}")
            tran.writeAction(f"addi {num} {scratch[0]} {1}")
            tran.writeAction(f"movrl {scratch[0]} 0({addr}) 0 {WORD_SIZE}")

            # 3. Read kv_ptr from dram
            tran.writeAction(f"movir {addr} {self.intermediate_ptr_offset}")
            tran.writeAction(f"add {'X7'} {addr} {addr}")
            tran.writeAction(f"movlr 0({addr}) {scratch[1]} 0 {WORD_SIZE}")
            tran.writeAction(f"muli {num} {scratch[0]} {WORD_SIZE}")
            tran.writeAction(f"add {scratch[0]} {scratch[1]} {scratch[1]}")
            tran.writeAction(f"evii {ev_word} {self.ln_receiver_fetched_kv_ptr_for_cache_ev_label} {255} {5}")
            if self.debug_flag:
                tran.writeAction(f"print '[LB_DEBUG] receiver_receive_key sending dram ptr request to %lu for key %ld' {scratch[1]} X8")
            tran.writeAction(f"send_dmlm_ld {scratch[1]} {ev_word} {1}")

            # 3.5 Update unresolved kv count
            # Increment 1 to account for dram request
            tran.writeAction(f"movir {addr} {self.unresolved_kv_count_offset}")
            tran.writeAction(f"add {'X7'} {addr} {addr}")
            tran.writeAction(f"movlr 0({addr}) {self.scratch[0]} 0 {WORD_SIZE}")
            if self.debug_flag:
                tran.writeAction(f"print '[LB_DEBUG] receiver_receive_key increment unresolved_kv_count from %d' {scratch[0]}")
            tran.writeAction(f"addi {self.scratch[0]} {self.scratch[0]} {1}")
            tran.writeAction(f"movrl {self.scratch[0]} 0({addr}) 0 {WORD_SIZE}")

        # Push the kv to the end of materializing cache
        # and fetch the materializing ptr (By setting 0 in X8)
        if self.grlb_type == 'ud':
            # Check key if it's claimed
            tran.writeAction(f"{init_cache_kv_label}: addi {entry_addr} {addr} {WORD_SIZE*2}")
            if self.debug_flag:
                tran.writeAction(f"print 'Lane %u start to cache kv of key %ld' X0 X8")
            tran.writeAction(f"final_check_key: movlr 0({entry_addr}) {key} 0 {WORD_SIZE}")
            tran.writeAction(f"andi {key} {scratch[0]} {1}")
            if self.debug_flag:
                tran.writeAction(f"print 'claimed bit %ld' {scratch[0]}")
            tran.writeAction(f"bnei {scratch[0]} {1} update_num")
            tran.writeAction(f"addi {entry_addr} {addr} {0}")
            tran.writeAction(f"jmp key_claimed")

            # Decrement num by 1
            tran.writeAction(f"update_num: movlr {WORD_SIZE*2}({entry_addr}) {num} 0 {WORD_SIZE}")
            if self.debug_flag:
                tran.writeAction(f"print 'materialized count %ld' {num}")
            tran.writeAction(f"blti {num} {0} keep_update_num")
            tran.writeAction(f"movlr {WORD_SIZE}({entry_addr}) {ev_word} 0 {WORD_SIZE}")
            tran.writeAction(f"jmp double_check_key")
            tran.writeAction(f"keep_update_num: subi {num} {scratch[0]} {1}")
            tran.writeAction(f"cswp {addr} {scratch[1]} {num} {scratch[0]}")
            tran.writeAction(f"bne {num} {scratch[1]} final_check_key")

            # Prepare for cache kv
            tran.writeAction(f"movir {addr} {self.materializing_metadata_offset}")
            tran.writeAction(f"add {base_addr} {addr} {addr}")
            tran.writeAction(f"movir {scratch[1]} {self.materialize_kv_cache_count}")
            tran.writeAction(f"sli {scratch[1]} {scratch[1]} {int(log2(64))}")

            # Increase address by a word here to stop at materializing_cache_end
            tran.writeAction(f"update_mcache_end: movlr {0}({addr}) {materializing_cache_start} 1 {WORD_SIZE}")
            tran.writeAction(f"movlr {0}({addr}) {materializing_cache_end} 0 {WORD_SIZE}")
            #   If end - start == cache_size, spin lock
            tran.writeAction(f"sub {materializing_cache_end} {materializing_cache_start} {scratch[0]}")
            tran.writeAction(f"beq {scratch[0]} {scratch[1]} spin_lock")

            #   Try to acquire an entry at end by atomic update materializing_cache_end 
            tran.writeAction(f"addi {materializing_cache_end} {key} {1}")
            tran.writeAction(f"cswp {addr} {scratch[0]} {materializing_cache_end} {key}")
            tran.writeAction(f"beq {scratch[0]} {materializing_cache_end} continue_cache_kv")
            #   If failed, reset addr and read metadata again
            tran.writeAction(f"subi {addr} {addr} {WORD_SIZE}")

            tran.writeAction(f"jmp update_mcache_end")
            # #   Check if claimed
            # tran.writeAction(f"movlr 0({entry_addr}) {key} 0 {WORD_SIZE}")
            # tran.writeAction(f"andi {key} {scratch[0]} {1}")
            # tran.writeAction(f"bnei {scratch[0]} {1} {init_cache_kv_label}")
            # tran.writeAction(f"addi {entry_addr} {addr} {0}")
            # tran.writeAction(f"jmp key_claimed")

            # #   Check if dram ptr came back
            # tran.writeAction(f"check_num: movlr {WORD_SIZE * 2}({entry_addr}) {num} 0 {WORD_SIZE}")
            # tran.writeAction(f"bgei {num} 0 prepare_for_send_kv")
            # tran.writeAction(f"jmp {init_cache_kv_label}")
            # tran.writeAction(f"prepare_for_send_kv: addi {entry_addr} {addr} {0}")
            # tran.writeAction(f"movlr {WORD_SIZE}({addr}) {ev_word} 0 {WORD_SIZE}")
            # tran.writeAction(f"movlr 0({addr}) {key} 0 {WORD_SIZE}")
            # tran.writeAction(f"andi {key} {is_claimed} 1")
            # if self.debug_flag:
            #     tran.writeAction(f"print 'Lane %u key %ld hit' X0 X8")
            # tran.writeAction(f"sri {key} {key} 1")
            # tran.writeAction(f"beqi {is_claimed} 1 key_claimed")
            # tran.writeAction(f"bnei {ev_word} -1 {materialize_kv_label}")
            # tran.writeAction(f"print 'second checking addr: %lu(0x%lx)' {ev_word} {ev_word}")
            # tran.writeAction(f"jmp prepare_for_send_kv")
            # # tran.writeAction(f"jmp {materialize_kv_label}")

            #   After acquiring a tail entry, write kv pair onto cache entry
            tran.writeAction(f"continue_cache_kv: movir {scratch[0]} {self.materialize_kv_cache_count}")
            tran.writeAction(f"div {materializing_cache_end} {scratch[0]} {scratch[1]}")
            tran.writeAction(f"modi {scratch[1]} {scratch[1]} {64}")
            tran.writeAction(f"mod {materializing_cache_end} {scratch[0]} {scratch[0]}")
            if self.debug_flag:
                tran.writeAction(f"print 'Lane %u caching kv of key %ld with start %lu and end %lu, at %d-th lane, %d-th entry' X0 X8 {materializing_cache_start} {materializing_cache_end} {scratch[1]} {scratch[0]}")
            tran.writeAction(f"sli {scratch[1]} {scratch[1]} {int(log2(SPD_BANK_SIZE))}")
            tran.writeAction(f"add {base_addr} {scratch[1]} {addr}")
            tran.writeAction(f"muli {scratch[0]} {scratch[0]} {self.inter_kvpair_size * WORD_SIZE}")
            tran.writeAction(f"add {scratch[0]} {addr} {addr}")
            tran.writeAction(f"movir {scratch[0]} {self.materialize_kv_cache_offset}")
            tran.writeAction(f"add {scratch[0]} {addr} {addr}")
            if self.debug_flag:
                tran.writeAction(f"print 'Lane %u caching %lu-th kv of key %ld at %lu(0x%lx)' X0 {materializing_cache_end} X8 {addr} {addr}")

            tran.writeAction(f"movrl X8 0({addr}) 1 {WORD_SIZE}")
            for i in range(1, self.inter_kvpair_size):
                tran.writeAction(f"movrl X{OB_REG_BASE+i} 0({addr}) 1 {WORD_SIZE}")

        elif self.grlb_type == 'lane':

            tran.writeAction(f"{init_cache_kv_label}: movir {addr} {self.materializing_metadata_offset}")
            tran.writeAction(f"add {'X7'} {addr} {addr}")
            tran.writeAction(f"movlr 0({addr}) {materializing_cache_start} 1 {WORD_SIZE}")
            tran.writeAction(f"movlr 0({addr}) {materializing_cache_end} 1 {WORD_SIZE}")
            tran.writeAction(f"movlr 0({addr}) {materializing_cache_empty} 1 {WORD_SIZE}")

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
            tran.writeAction(f"add {scratch[0]} {'X7'} {addr}")
            tran.writeAction(f"blt {materializing_cache_end} {addr} cache_kv")
            #   Elif end at limit, reset end to the front of cache space
            tran.writeAction(f"movir {materializing_cache_end} {self.materialize_kv_cache_offset}")
            tran.writeAction(f"add {'X7'} {materializing_cache_end} {materializing_cache_end}")
            tran.writeAction(f"jmp cache_kv")

            tran.writeAction(f"cache_start_equals_end: beqi {materializing_cache_empty} 0 spin_lock")
            tran.writeAction(f"movir {addr} {self.materialize_kv_cache_offset + self.materialize_kv_cache_size}")
            tran.writeAction(f"add {'X7'} {addr} {addr}")
            tran.writeAction(f"blt {materializing_cache_end} {addr} cache_kv")

            # If start and end both at limit, reset them to the front of cache space
            tran.writeAction(f"movir {materializing_cache_start} {self.materialize_kv_cache_offset}")
            tran.writeAction(f"add {'X7'} {materializing_cache_start} {materializing_cache_start}")
            tran.writeAction(f"addi {materializing_cache_start} {materializing_cache_end} 0")


            tran.writeAction(f"cache_kv: movrl X8 0({materializing_cache_end}) 1 {WORD_SIZE}")
            for i in range(1, self.inter_kvpair_size):
                tran.writeAction(f"movrl X{OB_REG_BASE+i} 0({materializing_cache_end}) 1 {WORD_SIZE}")
            tran.writeAction(f"beqi {materializing_cache_empty} 0 after_cache")
            tran.writeAction(f"movir {materializing_cache_empty} 0")

            # After caching the entry
            # Update the materialize_cache meta data in spd
            tran.writeAction(f"after_cache: movir {addr} {self.materializing_metadata_offset}")
            tran.writeAction(f"add {'X7'} {addr} {addr}")
            tran.writeAction(f"movrl {materializing_cache_start} 0({addr}) 1 {WORD_SIZE}")
            tran.writeAction(f"movrl {materializing_cache_end} 0({addr}) 1 {WORD_SIZE}")
            tran.writeAction(f"movrl {materializing_cache_empty} 0({addr}) 1 {WORD_SIZE}")

        if self.log_kv_latency:
            tran.writeAction(f"perflog 1 0 '%lu receive_kv end' X8")

        tran.writeAction(f"jmp receive_kv_end")



        tran.writeAction(f"spin_lock: evi X2 {ev_word} 255 4")
        tran.writeAction(f"sendops_wcont {ev_word} X1 X8 {self.inter_kvpair_size}")

        if self.log_kv_latency:
            tran.writeAction(f"receive_kv_end: perflog 1 0 '%lu receive_kv end' X8")
        else:
            tran.writeAction(f"receive_kv_end: yieldt")

        

        

        return

    def __gen_receiver_fetched_kv_ptr_for_cache_original(self, tran):
        '''
        Event:  returned from dram request sent by receiver_receive_kv
                with information to materialize the kv pairs
        Operands:   X8: Pointer to kv array
                    X9: Dram address of the entry read in
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
        tran.writeAction(f"movir {addr} {self.materializing_metadata_offset}")
        tran.writeAction(f"add {'X7'} {addr} {addr}")
        tran.writeAction(f"movlr 0({addr}) {materializing_cache_start} 1 {WORD_SIZE}")
        tran.writeAction(f"movlr 0({addr}) {materializing_cache_end} 1 {WORD_SIZE}")
        tran.writeAction(f"movlr 0({addr}) {materializing_cache_empty} 1 {WORD_SIZE}")
        # Set resolved kv count
        tran.writeAction(f"movir {resolved_kv_count} {0}")


        # Locate the entry in intermediate_cache
        tran.writeAction(f"movir {addr} {self.intermediate_ptr_offset}")
        tran.writeAction(f"add {'X7'} {addr} {addr}")
        tran.writeAction(f"movlr 0({addr}) {scratch[0]} 0 {WORD_SIZE}")
        tran.writeAction(f"sub {'X9'} {scratch[0]} {scratch[0]}")
        tran.writeAction(f"muli {scratch[0]} {scratch[0]} {self.intermediate_cache_entry_size}")
        tran.writeAction(f"movir {entry_addr} {self.intermediate_cache_offset}")
        tran.writeAction(f"add {'X7'} {entry_addr} {entry_addr}")
        tran.writeAction(f"add {scratch[0]} {entry_addr} {entry_addr}")

        # Read the key returned and check if already claimed
        tran.writeAction(f"movlr 0({entry_addr}) {key} 0 {WORD_SIZE}")
        tran.writeAction(f"andi {key} {is_claimed} 1")
        tran.writeAction(f"sri {key} {returned_key} 1")
        tran.writeAction(f"beqi {is_claimed} {1} entry_updated")
        

        # Update the entry in intermediate_cache
        tran.writeAction(f"movrl X9 {WORD_SIZE}({entry_addr}) 0 {WORD_SIZE}")

        # Iterate over the materialize_kv_cache and materialize any entry with the same key
        tran.writeAction(f"entry_updated: addi {materializing_cache_start} {addr} 0")
        tran.writeAction(f"addi {materializing_cache_end} {new_end} 0")

        # Iterate from the beginning
        # First check if materializing_cache_start == materializing_cache_end but materializing_cache_empty == 0, i.e. cache is full
        tran.writeAction(f"bne {addr} {materializing_cache_end} iter_do_while")
        tran.writeAction(f"beqi {materializing_cache_empty} 0 iter_and_update_start")
        # If cache is empty, which is not supposed to happen, yield terminate
        if self.debug_flag:
            tran.writeAction(f"print '[ERROR] Lane %u fetched kv ptr for key %ld but materializing cache empty!' X0 {returned_key}")
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
            tran.writeAction(f"print '[LB_DEBUG] receiveer_receive_kv_ptr send key %ld value %lu(0x%lx) to lane %d' {key} {scratch[1]} {scratch[1]} {scratch[0]}")
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
            tran.writeAction(f"print '[LB_DEBUG] receiveer_receive_kv_ptr materialize key %ld value %lu(0x%lx) to Dram %lu(0x%lx)' {key} {scratch[0]} {scratch[0]} {scratch[1]} {scratch[1]}")
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

        # Update inter_key_received_count
        tran.writeAction(f"movir {lm_reg} {self.inter_key_received_count_offset}")
        tran.writeAction(f"add {'X7'} {lm_reg} {lm_reg}")
        tran.writeAction(f"movlr 0({lm_reg}) {scratch[0]} 0 {WORD_SIZE}")
        tran.writeAction(f"addi {scratch[0]} {scratch[0]} {1}")
        tran.writeAction(f"movrl {scratch[0]} 0({lm_reg}) 0 {WORD_SIZE}")

        tran.writeAction(f"yieldt")

        return

    def __gen_receiver_fetched_kv_ptr_for_cache(self, tran):
        if self.grlb_type == 'lane':
            tranreceiver__fetched_kv_ptr_for_cache = tran

            ## Static declarations
            ## Param "kv_arr_addr" uses Register X8, scope (0->1)
            ## Param "entry_addr" uses Register X9, scope (0->1)
            ## Scoped Variable "ptr" uses Register X16, scope (0->1)
            ## Scoped Variable "base_addr" uses Register X17, scope (0->1)
            ## Scoped Variable "entry_ptr" uses Register X18, scope (0->1)
            ## Scoped Variable "returned_key" uses Register X19, scope (0->1)
            ## Scoped Variable "is_claimed" uses Register X20, scope (0->1)
            ## Scoped Variable "matched_count" uses Register X21, scope (0->1)
            ## Scoped Variable "dest" uses Register X22, scope (0->1)
            ## Scoped Variable "start" uses Register X23, scope (0->1)
            ## Scoped Variable "end" uses Register X24, scope (0->1)
            ## Scoped Variable "is_empty" uses Register X25, scope (0->1)
            ## Scoped Variable "ret_cont_word" uses Register X26, scope (0->1)
            ## Scoped Variable "stop" uses Register X27, scope (0->1)
            ## Scoped Variable "ev_word" uses Register X28, scope (0->1->13->15->20)
            ## Scoped Variable "i" uses Register X28, scope (0->1->13->15->21)
            ## Scoped Variable "ev_word" uses Register X28, scope (0->1->25->27->29->34)
            ## Scoped Variable "i" uses Register X28, scope (0->1->25->27->29->35)
            ## Scoped Variable "new_end" uses Register X28, scope (0->1->39)
            ## Scoped Variable "ev_word" uses Register X29, scope (0->1->39->44->46->48->51)
            ## Scoped Variable "ev_word" uses Register X29, scope (0->1->39->54->56->58->60->63)
            ## Param "dram_addr" uses Register X8, scope (0->71)
            ## Param "tmp" uses Register X8, scope (0->72)

            ##############################################
            ###### Writing code for thread receiver ######
            ##############################################
            ## event receive_intermediate_kv(unsigned long key, unsigned long value){
            ## }
            # Writing code for event receiver::fetched_kv_ptr_for_cache
            ## Decrement unresolved_kv_count by 1
            # tranreceiver__fetched_kv_ptr_for_cache.writeAction(f"print 'Lane %u receive_kv_ptr start' X0")
            # tranreceiver__fetched_kv_ptr_for_cache.writeAction(f"perflog 1 0 'Lane %u receive_kv_ptr start' X0")
            tranreceiver__fetched_kv_ptr_for_cache.writeAction(f"entry: movir X16 {self.unresolved_kv_count_offset}") 
            tranreceiver__fetched_kv_ptr_for_cache.writeAction(f"add X7 X16 X16") 
            tranreceiver__fetched_kv_ptr_for_cache.writeAction(f"movlr 0(X16) X18 0 8") 
            tranreceiver__fetched_kv_ptr_for_cache.writeAction(f"subi X18 X19 1") 
            tranreceiver__fetched_kv_ptr_for_cache.writeAction(f"movrl X19 0(X16) 0 8") 
            ## Locate intermediate_cache entry
            tranreceiver__fetched_kv_ptr_for_cache.writeAction(f"movir X16 {self.intermediate_ptr_offset}") 
            tranreceiver__fetched_kv_ptr_for_cache.writeAction(f"add X7 X16 X16") 
            tranreceiver__fetched_kv_ptr_for_cache.writeAction(f"movlr 0(X16) X17 0 8") 
            tranreceiver__fetched_kv_ptr_for_cache.writeAction(f"movir X18 {self.intermediate_cache_offset}") 
            tranreceiver__fetched_kv_ptr_for_cache.writeAction(f"add X7 X18 X18") 
            tranreceiver__fetched_kv_ptr_for_cache.writeAction(f"sub X9 X17 X19") 
            tranreceiver__fetched_kv_ptr_for_cache.writeAction(f"movir X20 {self.intermediate_cache_entry_size}") 
            tranreceiver__fetched_kv_ptr_for_cache.writeAction(f"mul X19 X20 X20") 
            tranreceiver__fetched_kv_ptr_for_cache.writeAction(f"add X18 X20 X18") 
            ## Read key and check if already claimed
            tranreceiver__fetched_kv_ptr_for_cache.writeAction(f"movlr 0(X18) X19 0 8") 
            tranreceiver__fetched_kv_ptr_for_cache.writeAction(f"andi X19 X20 1") 
            tranreceiver__fetched_kv_ptr_for_cache.writeAction(f"sri X19 X19 1") 
            
            ## Account for the dram request coming back
            tranreceiver__fetched_kv_ptr_for_cache.writeAction(f"movir X21 0") 
            tranreceiver__fetched_kv_ptr_for_cache.writeAction(f"movlr 8(X18) X22 0 8") 
            ## Update kv_ptr if not claimed
            tranreceiver__fetched_kv_ptr_for_cache.writeAction(f"bneiu X20 0 __if_fetched_kv_ptr_for_cache_2_post") 
            tranreceiver__fetched_kv_ptr_for_cache.writeAction(f"__if_fetched_kv_ptr_for_cache_0_true: movrl X8 8(X18) 0 8") 
            tranreceiver__fetched_kv_ptr_for_cache.writeAction(f"addi X8 X22 0") 

            ## Read materialize_kv_cache metadata
            tranreceiver__fetched_kv_ptr_for_cache.writeAction(f"__if_fetched_kv_ptr_for_cache_2_post: movir X16 {self.materializing_metadata_offset}") 
            tranreceiver__fetched_kv_ptr_for_cache.writeAction(f"add X7 X16 X16") 
            tranreceiver__fetched_kv_ptr_for_cache.writeAction(f"movlr 0(X16) X23 0 8") 
            tranreceiver__fetched_kv_ptr_for_cache.writeAction(f"movlr 8(X16) X24 0 8") 
            tranreceiver__fetched_kv_ptr_for_cache.writeAction(f"movlr 16(X16) X25 0 8") 
            tranreceiver__fetched_kv_ptr_for_cache.writeAction(f"bnei X25 1 __if_fetched_kv_ptr_for_cache_5_post") 
            tranreceiver__fetched_kv_ptr_for_cache.writeAction(f"__if_fetched_kv_ptr_for_cache_3_true: print 'Lane %d receiver fetched_kv_ptr_for_cache gets empty cache! Terminate!' X0") 
            tranreceiver__fetched_kv_ptr_for_cache.writeAction(f"__if_fetched_kv_ptr_for_cache_5_post: bneiu X20 1 __if_fetched_kv_ptr_for_cache_7_false") 
            tranreceiver__fetched_kv_ptr_for_cache.writeAction(f"__if_fetched_kv_ptr_for_cache_6_true: evi X2 X26 {self.ln_receiver_update_unresolved_kv_count_ev_label} 1") 
            tranreceiver__fetched_kv_ptr_for_cache.writeAction(f"jmp __if_fetched_kv_ptr_for_cache_8_post") 
            tranreceiver__fetched_kv_ptr_for_cache.writeAction(f"__if_fetched_kv_ptr_for_cache_7_false: evi X2 X26 {self.ln_receiver_materialize_ret_ev_label} 1") 
            tranreceiver__fetched_kv_ptr_for_cache.writeAction(f"__if_fetched_kv_ptr_for_cache_8_post: evi X26 X26 255 4") 
            ## If start >= end, set stop at max limit
            ## Otherwise, set stop at end
            tranreceiver__fetched_kv_ptr_for_cache.writeAction(f"ble X24 X23 __if_fetched_kv_ptr_for_cache_10_false") 
            tranreceiver__fetched_kv_ptr_for_cache.writeAction(f"__if_fetched_kv_ptr_for_cache_9_true: addi X24 X27 0") 
            tranreceiver__fetched_kv_ptr_for_cache.writeAction(f"jmp __while_fetched_kv_ptr_for_cache_12_condition") 
            tranreceiver__fetched_kv_ptr_for_cache.writeAction(f"__if_fetched_kv_ptr_for_cache_10_false: movir X28 {self.materialize_kv_cache_offset}") 
            tranreceiver__fetched_kv_ptr_for_cache.writeAction(f"add X7 X28 X28") 
            tranreceiver__fetched_kv_ptr_for_cache.writeAction(f"movir X27 {self.materialize_kv_cache_size}") 
            tranreceiver__fetched_kv_ptr_for_cache.writeAction(f"add X28 X27 X27") 
            tranreceiver__fetched_kv_ptr_for_cache.writeAction(f"__while_fetched_kv_ptr_for_cache_12_condition: ble X27 X23 __while_fetched_kv_ptr_for_cache_14_post") 
            tranreceiver__fetched_kv_ptr_for_cache.writeAction(f"__while_fetched_kv_ptr_for_cache_13_body: movlr 0(X23) X28 0 8") 
            tranreceiver__fetched_kv_ptr_for_cache.writeAction(f"beqi X28 -1 __if_fetched_kv_ptr_for_cache_17_post") 
            tranreceiver__fetched_kv_ptr_for_cache.writeAction(f"__if_fetched_kv_ptr_for_cache_15_true: movlr 0(X23) X28 0 8") 
            tranreceiver__fetched_kv_ptr_for_cache.writeAction(f"beq X28 X19 __if_fetched_kv_ptr_for_cache_20_post") 
            tranreceiver__fetched_kv_ptr_for_cache.writeAction(f"__if_fetched_kv_ptr_for_cache_18_true: jmp __while_fetched_kv_ptr_for_cache_14_post") 
            tranreceiver__fetched_kv_ptr_for_cache.writeAction(f"__if_fetched_kv_ptr_for_cache_20_post: bneiu X20 0 __if_fetched_kv_ptr_for_cache_22_false") 
            tranreceiver__fetched_kv_ptr_for_cache.writeAction(f"__if_fetched_kv_ptr_for_cache_21_true: send_dmlm X22 X26 X23 {self.inter_kvpair_size}") 
            tranreceiver__fetched_kv_ptr_for_cache.writeAction(f"addi X22 X22 {self.inter_kvpair_size * WORD_SIZE}") 
            tranreceiver__fetched_kv_ptr_for_cache.writeAction(f"jmp __if_fetched_kv_ptr_for_cache_23_post") 
            tranreceiver__fetched_kv_ptr_for_cache.writeAction(f"__if_fetched_kv_ptr_for_cache_22_false: addi X22 X28 0") 
            tranreceiver__fetched_kv_ptr_for_cache.writeAction(f"send_wcont X28 X26 X23 {self.inter_kvpair_size}") 
            tranreceiver__fetched_kv_ptr_for_cache.writeAction(f"__if_fetched_kv_ptr_for_cache_23_post: addi X21 X21 1") 
            tranreceiver__fetched_kv_ptr_for_cache.writeAction(f"movir X28 0") 
            tranreceiver__fetched_kv_ptr_for_cache.writeAction(f"__for_fetched_kv_ptr_for_cache_24_condition: bgei X28 {self.inter_kvpair_size} __if_fetched_kv_ptr_for_cache_17_post") 
            tranreceiver__fetched_kv_ptr_for_cache.writeAction(f"__for_fetched_kv_ptr_for_cache_25_body: movir X30 -1") 
            tranreceiver__fetched_kv_ptr_for_cache.writeAction(f"movwrl X30 X23(X28,0,0)") 
            tranreceiver__fetched_kv_ptr_for_cache.writeAction(f"addi X28 X28 1") 
            tranreceiver__fetched_kv_ptr_for_cache.writeAction(f"jmp __for_fetched_kv_ptr_for_cache_24_condition") 
            tranreceiver__fetched_kv_ptr_for_cache.writeAction(f"__if_fetched_kv_ptr_for_cache_17_post: addi X23 X23 {self.inter_kvpair_size * WORD_SIZE}") 
            tranreceiver__fetched_kv_ptr_for_cache.writeAction(f"jmp __while_fetched_kv_ptr_for_cache_12_condition") 
            ## If start hits either end or maximum limit
            ## If hit maximum limit, reset start to minimum limit and keep iterating start
            tranreceiver__fetched_kv_ptr_for_cache.writeAction(f"__while_fetched_kv_ptr_for_cache_14_post: ceq X23 X27 X28") 
            tranreceiver__fetched_kv_ptr_for_cache.writeAction(f"ceq X27 X24 X29") 
            tranreceiver__fetched_kv_ptr_for_cache.writeAction(f"xori X29 X29 1") 
            tranreceiver__fetched_kv_ptr_for_cache.writeAction(f"and X28 X29 X30") 
            tranreceiver__fetched_kv_ptr_for_cache.writeAction(f"beqi X30 0 __if_fetched_kv_ptr_for_cache_29_post") 
            tranreceiver__fetched_kv_ptr_for_cache.writeAction(f"__if_fetched_kv_ptr_for_cache_27_true: movir X23 {self.materialize_kv_cache_offset}") 
            tranreceiver__fetched_kv_ptr_for_cache.writeAction(f"add X7 X23 X23") 
            tranreceiver__fetched_kv_ptr_for_cache.writeAction(f"__while_fetched_kv_ptr_for_cache_30_condition: ble X24 X23 __if_fetched_kv_ptr_for_cache_29_post") 
            tranreceiver__fetched_kv_ptr_for_cache.writeAction(f"__while_fetched_kv_ptr_for_cache_31_body: movlr 0(X23) X28 0 8") 
            tranreceiver__fetched_kv_ptr_for_cache.writeAction(f"beqi X28 -1 __if_fetched_kv_ptr_for_cache_35_post") 
            tranreceiver__fetched_kv_ptr_for_cache.writeAction(f"__if_fetched_kv_ptr_for_cache_33_true: movlr 0(X23) X28 0 8") 
            tranreceiver__fetched_kv_ptr_for_cache.writeAction(f"beq X28 X19 __if_fetched_kv_ptr_for_cache_38_post") 
            tranreceiver__fetched_kv_ptr_for_cache.writeAction(f"__if_fetched_kv_ptr_for_cache_36_true: jmp __if_fetched_kv_ptr_for_cache_29_post") 
            tranreceiver__fetched_kv_ptr_for_cache.writeAction(f"__if_fetched_kv_ptr_for_cache_38_post: bneiu X20 0 __if_fetched_kv_ptr_for_cache_40_false") 
            tranreceiver__fetched_kv_ptr_for_cache.writeAction(f"__if_fetched_kv_ptr_for_cache_39_true: send_dmlm X22 X26 X23 {self.inter_kvpair_size}") 
            tranreceiver__fetched_kv_ptr_for_cache.writeAction(f"addi X22 X22 {self.inter_kvpair_size * WORD_SIZE}") 
            tranreceiver__fetched_kv_ptr_for_cache.writeAction(f"jmp __if_fetched_kv_ptr_for_cache_41_post") 
            tranreceiver__fetched_kv_ptr_for_cache.writeAction(f"__if_fetched_kv_ptr_for_cache_40_false: addi X22 X28 0") 
            tranreceiver__fetched_kv_ptr_for_cache.writeAction(f"send_wcont X28 X26 X23 {self.inter_kvpair_size}") 
            tranreceiver__fetched_kv_ptr_for_cache.writeAction(f"__if_fetched_kv_ptr_for_cache_41_post: addi X21 X21 1") 
            tranreceiver__fetched_kv_ptr_for_cache.writeAction(f"movir X28 0") 
            tranreceiver__fetched_kv_ptr_for_cache.writeAction(f"__for_fetched_kv_ptr_for_cache_42_condition: bgei X28 {self.inter_kvpair_size} __if_fetched_kv_ptr_for_cache_35_post") 
            tranreceiver__fetched_kv_ptr_for_cache.writeAction(f"__for_fetched_kv_ptr_for_cache_43_body: movir X30 -1") 
            tranreceiver__fetched_kv_ptr_for_cache.writeAction(f"movwrl X30 X23(X28,0,0)") 
            tranreceiver__fetched_kv_ptr_for_cache.writeAction(f"addi X28 X28 1") 
            tranreceiver__fetched_kv_ptr_for_cache.writeAction(f"jmp __for_fetched_kv_ptr_for_cache_42_condition") 
            tranreceiver__fetched_kv_ptr_for_cache.writeAction(f"__if_fetched_kv_ptr_for_cache_35_post: addi X23 X23 {self.inter_kvpair_size * WORD_SIZE}") 
            tranreceiver__fetched_kv_ptr_for_cache.writeAction(f"jmp __while_fetched_kv_ptr_for_cache_30_condition") 
            ## At this point, situation includes
            ## 1. Start hits an unmatch, needs to continue iterating, then start != end
            ## 2. Start == end and the first entry is an unmatch, then matched_count == 0
            ## 3. Start hits end, stop iterating
            ## If in situation 1 and 2, iterating end and update end
            tranreceiver__fetched_kv_ptr_for_cache.writeAction(f"__if_fetched_kv_ptr_for_cache_29_post: ceq X23 X24 X28") 
            tranreceiver__fetched_kv_ptr_for_cache.writeAction(f"xori X28 X28 1") 
            tranreceiver__fetched_kv_ptr_for_cache.writeAction(f"ceqi X21 X29 0") 
            tranreceiver__fetched_kv_ptr_for_cache.writeAction(f"or X28 X29 X30") 
            tranreceiver__fetched_kv_ptr_for_cache.writeAction(f"beqi X30 0 __if_fetched_kv_ptr_for_cache_47_post") 
            tranreceiver__fetched_kv_ptr_for_cache.writeAction(f"__if_fetched_kv_ptr_for_cache_45_true: addi X23 X16 0") 
            tranreceiver__fetched_kv_ptr_for_cache.writeAction(f"addi X23 X28 0") 
            ## If start >= end, set stop at max limit
            ## Otherwise, set stop at end
            tranreceiver__fetched_kv_ptr_for_cache.writeAction(f"ble X24 X23 __if_fetched_kv_ptr_for_cache_49_false") 
            tranreceiver__fetched_kv_ptr_for_cache.writeAction(f"__if_fetched_kv_ptr_for_cache_48_true: addi X24 X27 0") 
            tranreceiver__fetched_kv_ptr_for_cache.writeAction(f"jmp __while_fetched_kv_ptr_for_cache_51_condition") 
            tranreceiver__fetched_kv_ptr_for_cache.writeAction(f"__if_fetched_kv_ptr_for_cache_49_false: movir X29 {self.materialize_kv_cache_offset}") 
            tranreceiver__fetched_kv_ptr_for_cache.writeAction(f"add X7 X29 X29") 
            tranreceiver__fetched_kv_ptr_for_cache.writeAction(f"movir X27 {self.materialize_kv_cache_size}") 
            tranreceiver__fetched_kv_ptr_for_cache.writeAction(f"add X29 X27 X27") 
            tranreceiver__fetched_kv_ptr_for_cache.writeAction(f"__while_fetched_kv_ptr_for_cache_51_condition: bleu X27 X16 __while_fetched_kv_ptr_for_cache_53_post") 
            tranreceiver__fetched_kv_ptr_for_cache.writeAction(f"__while_fetched_kv_ptr_for_cache_52_body: movlr 0(X16) X29 0 8") 
            tranreceiver__fetched_kv_ptr_for_cache.writeAction(f"beqi X29 -1 __if_fetched_kv_ptr_for_cache_56_post") 
            tranreceiver__fetched_kv_ptr_for_cache.writeAction(f"__if_fetched_kv_ptr_for_cache_54_true: movlr 0(X16) X29 0 8") 
            tranreceiver__fetched_kv_ptr_for_cache.writeAction(f"bneu X29 X19 __if_fetched_kv_ptr_for_cache_58_false") 
            tranreceiver__fetched_kv_ptr_for_cache.writeAction(f"__if_fetched_kv_ptr_for_cache_57_true: bneiu X20 0 __if_fetched_kv_ptr_for_cache_61_false") 
            tranreceiver__fetched_kv_ptr_for_cache.writeAction(f"__if_fetched_kv_ptr_for_cache_60_true: send_dmlm X22 X26 X16 {self.inter_kvpair_size}") 
            tranreceiver__fetched_kv_ptr_for_cache.writeAction(f"addi X22 X22 {self.inter_kvpair_size * WORD_SIZE}") 
            tranreceiver__fetched_kv_ptr_for_cache.writeAction(f"jmp __if_fetched_kv_ptr_for_cache_62_post") 
            tranreceiver__fetched_kv_ptr_for_cache.writeAction(f"__if_fetched_kv_ptr_for_cache_61_false: addi X22 X29 0") 
            tranreceiver__fetched_kv_ptr_for_cache.writeAction(f"send_wcont X29 X26 X16 {self.inter_kvpair_size}") 
            tranreceiver__fetched_kv_ptr_for_cache.writeAction(f"__if_fetched_kv_ptr_for_cache_62_post: addi X21 X21 1") 
            tranreceiver__fetched_kv_ptr_for_cache.writeAction(f"jmp __if_fetched_kv_ptr_for_cache_56_post") 
            tranreceiver__fetched_kv_ptr_for_cache.writeAction(f"__if_fetched_kv_ptr_for_cache_58_false: addi X16 X28 {self.inter_kvpair_size * WORD_SIZE}") 
            tranreceiver__fetched_kv_ptr_for_cache.writeAction(f"__if_fetched_kv_ptr_for_cache_56_post: addi X16 X16 {self.inter_kvpair_size * WORD_SIZE}") 
            tranreceiver__fetched_kv_ptr_for_cache.writeAction(f"jmp __while_fetched_kv_ptr_for_cache_51_condition") 
            ## If stop != end, meaning stop == max limit and start >= end
            ## Reset ptr to beginning of cache and iterate till end
            tranreceiver__fetched_kv_ptr_for_cache.writeAction(f"__while_fetched_kv_ptr_for_cache_53_post: beq X27 X24 __if_fetched_kv_ptr_for_cache_65_post") 
            tranreceiver__fetched_kv_ptr_for_cache.writeAction(f"__if_fetched_kv_ptr_for_cache_63_true: movir X16 {self.materialize_kv_cache_offset}") 
            tranreceiver__fetched_kv_ptr_for_cache.writeAction(f"add X7 X16 X16") 
            tranreceiver__fetched_kv_ptr_for_cache.writeAction(f"__while_fetched_kv_ptr_for_cache_66_condition: ble X24 X16 __if_fetched_kv_ptr_for_cache_65_post") 
            tranreceiver__fetched_kv_ptr_for_cache.writeAction(f"__while_fetched_kv_ptr_for_cache_67_body: movlr 0(X16) X29 0 8") 
            tranreceiver__fetched_kv_ptr_for_cache.writeAction(f"beqi X29 -1 __if_fetched_kv_ptr_for_cache_71_post") 
            tranreceiver__fetched_kv_ptr_for_cache.writeAction(f"__if_fetched_kv_ptr_for_cache_69_true: movlr 0(X16) X29 0 8") 
            tranreceiver__fetched_kv_ptr_for_cache.writeAction(f"bneu X29 X19 __if_fetched_kv_ptr_for_cache_73_false") 
            tranreceiver__fetched_kv_ptr_for_cache.writeAction(f"__if_fetched_kv_ptr_for_cache_72_true: bneiu X20 0 __if_fetched_kv_ptr_for_cache_76_false") 
            tranreceiver__fetched_kv_ptr_for_cache.writeAction(f"__if_fetched_kv_ptr_for_cache_75_true: send_dmlm X22 X26 X16 {self.inter_kvpair_size}") 
            tranreceiver__fetched_kv_ptr_for_cache.writeAction(f"addi X22 X22 {self.inter_kvpair_size * WORD_SIZE}") 
            tranreceiver__fetched_kv_ptr_for_cache.writeAction(f"jmp __if_fetched_kv_ptr_for_cache_77_post") 
            tranreceiver__fetched_kv_ptr_for_cache.writeAction(f"__if_fetched_kv_ptr_for_cache_76_false: addi X22 X29 0") 
            tranreceiver__fetched_kv_ptr_for_cache.writeAction(f"send_wcont X29 X26 X16 {self.inter_kvpair_size}") 
            tranreceiver__fetched_kv_ptr_for_cache.writeAction(f"__if_fetched_kv_ptr_for_cache_77_post: addi X21 X21 1") 
            tranreceiver__fetched_kv_ptr_for_cache.writeAction(f"jmp __if_fetched_kv_ptr_for_cache_71_post") 
            tranreceiver__fetched_kv_ptr_for_cache.writeAction(f"__if_fetched_kv_ptr_for_cache_73_false: addi X16 X28 {self.inter_kvpair_size * WORD_SIZE}") 
            tranreceiver__fetched_kv_ptr_for_cache.writeAction(f"__if_fetched_kv_ptr_for_cache_71_post: addi X16 X16 {self.inter_kvpair_size * WORD_SIZE}") 
            tranreceiver__fetched_kv_ptr_for_cache.writeAction(f"jmp __while_fetched_kv_ptr_for_cache_66_condition") 
            tranreceiver__fetched_kv_ptr_for_cache.writeAction(f"__if_fetched_kv_ptr_for_cache_65_post: addi X28 X24 0") 
            tranreceiver__fetched_kv_ptr_for_cache.writeAction(f"__if_fetched_kv_ptr_for_cache_47_post: movir X16 {self.materializing_metadata_offset}") 
            tranreceiver__fetched_kv_ptr_for_cache.writeAction(f"add X7 X16 X16") 
            tranreceiver__fetched_kv_ptr_for_cache.writeAction(f"movrl X23 0(X16) 0 8") 
            tranreceiver__fetched_kv_ptr_for_cache.writeAction(f"movrl X24 8(X16) 0 8") 
            tranreceiver__fetched_kv_ptr_for_cache.writeAction(f"bne X23 X24 __if_fetched_kv_ptr_for_cache_79_false") 
            tranreceiver__fetched_kv_ptr_for_cache.writeAction(f"__if_fetched_kv_ptr_for_cache_78_true: movir X29 1") 
            tranreceiver__fetched_kv_ptr_for_cache.writeAction(f"movrl X29 16(X16) 0 8") 
            tranreceiver__fetched_kv_ptr_for_cache.writeAction(f"jmp __if_fetched_kv_ptr_for_cache_80_post") 
            tranreceiver__fetched_kv_ptr_for_cache.writeAction(f"__if_fetched_kv_ptr_for_cache_79_false: movir X29 0") 
            tranreceiver__fetched_kv_ptr_for_cache.writeAction(f"movrl X29 16(X16) 0 8") 
            tranreceiver__fetched_kv_ptr_for_cache.writeAction(f"__if_fetched_kv_ptr_for_cache_80_post: bneiu X20 1 __if_fetched_kv_ptr_for_cache_82_false") 
            ## If claimed, increment unresolved_kv_count by matched_count
            tranreceiver__fetched_kv_ptr_for_cache.writeAction(f"__if_fetched_kv_ptr_for_cache_81_true: movir X16 {self.unresolved_kv_count_offset}") 
            tranreceiver__fetched_kv_ptr_for_cache.writeAction(f"add X7 X16 X16") 
            tranreceiver__fetched_kv_ptr_for_cache.writeAction(f"movlr 0(X16) X29 0 8") 
            tranreceiver__fetched_kv_ptr_for_cache.writeAction(f"add X29 X21 X30") 
            tranreceiver__fetched_kv_ptr_for_cache.writeAction(f"movrl X30 0(X16) 0 8") 
            tranreceiver__fetched_kv_ptr_for_cache.writeAction(f"jmp __if_fetched_kv_ptr_for_cache_83_post") 
            ## If not claimed, set kv rec number as matched_count
            tranreceiver__fetched_kv_ptr_for_cache.writeAction(f"__if_fetched_kv_ptr_for_cache_82_false: movrl X21 16(X18) 0 8") 
            tranreceiver__fetched_kv_ptr_for_cache.writeAction(f"__if_fetched_kv_ptr_for_cache_83_post: yield_terminate")
            # tranreceiver__fetched_kv_ptr_for_cache.writeAction(f"__if_fetched_kv_ptr_for_cache_83_post: perflog 1 0 'Lane %u receive_kv_ptr end' X0")
            # tranreceiver__fetched_kv_ptr_for_cache.writeAction(f"__if_fetched_kv_ptr_for_cache_83_post: print 'receive_kv_ptr end'")
            tranreceiver__fetched_kv_ptr_for_cache.writeAction(f"yield_terminate")

        elif self.grlb_type == 'ud':
            tranreceiver__ud_fetched_kv_ptr_for_cache = tran

            # if self.log_kv_latency:
            #     tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"perflog 1 0 'receive_kv_ptr start'")

            # ## Get start spd address of this ud
            # tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"entry: andi X0 X22 63") 
            # tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"sli X22 X23 16") 
            # tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"sub X7 X23 X19") 
            # ## Locate intermediate_cache entry
            # tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"movir X26 {self.intermediate_ptr_offset}") 
            # tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"add X19 X26 X20") 
            # ## unsigned long tmp = (entry_addr - ptr[0]) / 8;
            # tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"__if_ud_fetched_kv_ptr_for_cache_0_true: movlr 0(X20) X22 0 8") 
            # tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"sub X9 X22 X23") 
            # tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"sari X23 X22 3") 
            # if self.debug_flag:
            #     tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"print 'Lane %u received kv_ptr for %ld-key, operands %ld, %ld' X0 X22 X8 X9") 
            # ## unsigned long tmp1 = (tmp % intermediate_cache_count) * intermediate_cache_entry_size * 8;
            # ## tmp = (tmp / intermediate_cache_count) << 16;
            # ## entry_ptr = base_ptr + tmp + intermediate_cache_offset + tmp1;
            # tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"movir X24 {self.intermediate_cache_count}") 
            # tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"mod X22 X24 X23") 
            # tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"movir X24 {self.intermediate_cache_entry_size}") 
            # tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"mul X23 X24 X23") 
            # tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"sli X23 X23 3") 
            # tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"movir X24 {self.intermediate_cache_count}") 
            # tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"div X22 X24 X22") 
            # tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"sli X22 X22 16") 
            # tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"add X19 X22 X21") 
            # tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"add X21 X23 X21") 
            # tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"movir X24 {self.intermediate_cache_offset}") 
            # tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"add X21 X24 X21") 
            # ## Read key
            # tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"movlr 0(X21) X22 0 8") 
            # tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"sri X22 X16 1")
            # if self.debug_flag:
            #     tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"print 'Cached key %lu, original key %lu' X22 X16")
            # ## Read dest
            # tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"__if_ud_fetched_kv_ptr_for_cache_3_true: addi X21 X20 8") 
            # tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"movir X24 -1") 
            # tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"movlr 0(X20) X22 0 8") 
            # tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"cswp X20 X23 X24 X8") 
            # tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"bne X23 X24 __if_ud_fetched_kv_ptr_for_cache_7_false") 
            # tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"__if_ud_fetched_kv_ptr_for_cache_6_true: movir X26 0") 
            # tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"movrl X26 16(X21) 0 8") 
            # tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"evi X2 X18 {self.ln_receiver_materialize_ret_ev_label} 1") 
            # tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"movir X17 0") 
            # tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"jmp __if_ud_fetched_kv_ptr_for_cache_8_post") 
            # tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"__if_ud_fetched_kv_ptr_for_cache_7_false: evi X2 X18 {self.ln_receiver_update_unresolved_kv_count_ev_label} 1") 
            # tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"movir X17 1") 
            # tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"__if_ud_fetched_kv_ptr_for_cache_8_post: evi X18 X18 255 4") 
            # ## // Read key and check if already claimed
            # ## returned_key = entry_ptr[0];
            # ## is_claimed = returned_key & 1;
            # ## // Update kv_ptr if not claimed, and generate continuation word for cached kvs
            # ## if (is_claimed == 0) {
            # ##    entry_ptr[1] = kv_arr_addr;
            # ##    entry_ptr[2] = 0;
            # ##    ret_cont_word = evw_update_event(CEVNT, receiver_materialize_kv_ret);
            # ## }
            # ## else {
            # ##    ret_cont_word = evw_update_event(CEVNT, receiver_update_unresolved_kv_count);
            # ## }
            # ## ret_cont_word = evw_update_thread(ret_cont_word, NEWTH);
            # if self.record_unresolved_kv_count:
            #     ## Decrement unresolved_kv_count by 1 to account for this dram read return
            #     tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"__if_ud_fetched_kv_ptr_for_cache_9_true: movir X25 {self.unresolved_kv_count_offset}") 
            #     tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"add X19 X25 X20") 
            #     tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"decrement_unresolved_count: movlr 0(X20) X22 0 8") 
            #     tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"subi X22 X23 1") 
            #     tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"cswp X20 X24 X22 X23") 
            #     tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"bne X24 X22 decrement_unresolved_count") 
            #     tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"print 'Lane %u receive_kv_ptr reduces unresolved_count from %d to %d' X0 X22 X23") 
            # ## // Resume returned key
            # ## returned_key = returned_key >> 1;
            # if self.debug_flag:
            #     tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"print 'Lane %u received kv_ptr for key %ld with bin address %lu(0x%lx), entry address %lu' X0 X16 X8 X8 X21") 
            # ## Read materialize_kv_cache metadata
            # ## Locate start of materialize_kv_cache
            # tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"movir X26 {self.materializing_metadata_offset}") 
            # tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"add X19 X26 X20") 
            # tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"movlr 0(X20) X22 0 8") 
            # ## long end = ptr[1];
            # tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"movir X26 {self.materialize_kv_cache_count}") 
            # tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"div X22 X26 X24") 
            # tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"addi X24 X25 1") 
            # tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"movir X26 {self.materialize_kv_cache_count}") 
            # tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"mul X25 X26 X23") 
            # tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"movir X24 0") 
            # ## long tmp = ((start / materialize_kv_cache_count) % 64) << 16;
            # ## long tmp1 = (start % materialize_kv_cache_count) * inter_kvpair_size * 8;
            # ## tmp = base_ptr + tmp + materialize_kv_cache_offset;
            # ## ptr = tmp + tmp1;
            # tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"__if_ud_fetched_kv_ptr_for_cache_12_true: movir X28 {self.materialize_kv_cache_count}") 
            # tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"div X22 X28 X26") 
            # tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"andi X26 X26 63") 
            # tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"sli X26 X26 16") 
            # tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"movir X28 {self.materialize_kv_cache_offset}") 
            # tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"add X26 X28 X26") 
            # tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"add X26 X19 X26") 
            # tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"movir X28 {self.materialize_kv_cache_count}") 
            # tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"mod X22 X28 X27") 
            # tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"muli X27 X27 {self.inter_kvpair_size}") 
            # tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"sli X27 X27 3") 
            # tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"movlr 8(X20) X25 0 8") 
            # tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"add X26 X27 X20") 
            # tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"bneiu X17 0 __if_ud_fetched_kv_ptr_for_cache_17_post") 
            # ## Move entry_ptr to the materialized count word, for cswp
            # tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"__if_ud_fetched_kv_ptr_for_cache_15_true: addi X21 X21 16") 
            # ## If not claimed, need to account for the first entry found
            # tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"movir X26 0") 
            # ## Iterate and update start until find an unmatch
            # tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"__while_ud_fetched_kv_ptr_for_cache_18_condition: bleu X25 X22 __if_ud_fetched_kv_ptr_for_cache_17_post") 
            # ## First check if entry empty
            # tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"__while_ud_fetched_kv_ptr_for_cache_19_body: movlr 0(X20) X27 0 8") 
            # tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"beqi X27 -1 __if_ud_fetched_kv_ptr_for_cache_23_post") 
            # tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"__if_ud_fetched_kv_ptr_for_cache_21_true: movlr 0(X20) X27 0 8") 
            # ## If not matched for the first time, write new start to spd
            # tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"movlr 0(X20) X28 0 8") 
            # tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"beq X28 X16 __if_ud_fetched_kv_ptr_for_cache_25_false") 
            # # if self.debug_flag:
            # #     tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"__if_ud_fetched_kv_ptr_for_cache_24_true: print 'Not matching: entry %ld reads %ld at %lu' X22 X27 X20") 
            # tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"bneiu X24 0 __if_ud_fetched_kv_ptr_for_cache_29_post") 
            # tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"__if_ud_fetched_kv_ptr_for_cache_27_true: movir X30 {self.materializing_metadata_offset}") 
            # tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"add X19 X30 X24") 
            # tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"update_materializing_start_not_matched: movlr 0(X24) X27 0 8") 
            # tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"bge X27 X22 after_update_materializing_start_not_matched") 
            # tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"cswp X24 X28 X27 X22") 
            # tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"bne X28 X27 update_materializing_start_not_matched") 
            # tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"after_update_materializing_start_not_matched: movir X24 1") 
            # if self.debug_flag:
            #     tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"print 'replace old start %ld with new start %d at %lu' X27 X22 X20")
            # tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"__if_ud_fetched_kv_ptr_for_cache_29_post: jmp __if_ud_fetched_kv_ptr_for_cache_23_post") 
            # if self.debug_flag:
            #     tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"__if_ud_fetched_kv_ptr_for_cache_25_false: print 'Matched: entry %ld reads %ld at %lu' X22 X27 X20") 
            #     ## If matched, first check if key just got claimed
            #     tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"movlr -16(X21) X28 0 8") 
            # else:
            #     tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"__if_ud_fetched_kv_ptr_for_cache_25_false: movlr -16(X21) X28 0 8") 
            # tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"andi X28 X17 1") 
            # tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"beqiu X17 0 __if_ud_fetched_kv_ptr_for_cache_36_true") 
            # ## If just got claimed, wait till claimed dest evword is written
            # tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"__if_ud_fetched_kv_ptr_for_cache_30_true: subi X21 X21 16") 
            # tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"evi X2 X18 {self.ln_receiver_update_unresolved_kv_count_ev_label} 1") 
            # tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"evi X18 X18 255 4") 
            # tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"movlr 8(X21) X27 0 8") 
            # tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"__while_ud_fetched_kv_ptr_for_cache_33_condition: bneu X27 X8 __while_ud_fetched_kv_ptr_for_cache_35_post") 
            # tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"__while_ud_fetched_kv_ptr_for_cache_34_body: movlr 8(X21) X27 0 8") 
            # tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"jmp __while_ud_fetched_kv_ptr_for_cache_33_condition") 
            # tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"__while_ud_fetched_kv_ptr_for_cache_35_post: jmp __if_ud_fetched_kv_ptr_for_cache_17_post") 
            # tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"__if_ud_fetched_kv_ptr_for_cache_36_true: movlr 0(X21) X27 0 8") 
            # tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"addi X27 X30 1") 
            # tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"cswp X21 X29 X27 X30") 
            # tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"bne X29 X27 __if_ud_fetched_kv_ptr_for_cache_36_true") 
            # tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"subi X30 X30 1") 
            # tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"muli X29 X28 {self.inter_kvpair_size}") 
            # tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"sli X28 X28 3") 
            # tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"add X28 X8 X28") 
            # if self.debug_flag:
            #     tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"print 'receive_ptr materialize key %ld to Dram %lu(0x%lx) as the %ld-th kv' X16 X28 X28 X30") 
            # ## Materialize the kv
            # ## long* dest = cswp_ret * inter_kvpair_size * 8 + kv_arr_addr;
            # tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"send_dmlm X28 X18 X20 {self.inter_kvpair_size}") 
            # ## Erase this entry
            # tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"movir X27 0") 
            # tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"__for_ud_fetched_kv_ptr_for_cache_39_condition: bgeiu X27 {self.inter_kvpair_size} __if_ud_fetched_kv_ptr_for_cache_23_post") 
            # tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"__for_ud_fetched_kv_ptr_for_cache_40_body: movir X30 -1") 
            # tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"movwrl X30 X20(X27,0,0)") 
            # tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"addi X27 X27 1") 
            # tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"jmp __for_ud_fetched_kv_ptr_for_cache_39_condition") 
            # ## Step forward one entry
            # tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"__if_ud_fetched_kv_ptr_for_cache_23_post: addi X22 X22 1") 
            # ## If going across lanes, update ptr
            # tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"bneu X22 X23 __if_ud_fetched_kv_ptr_for_cache_43_false") 
            # tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"__if_ud_fetched_kv_ptr_for_cache_42_true: movir X27 {self.materialize_kv_cache_count}") 
            # tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"div X22 X27 X27") 
            # tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"andi X27 X28 63") 
            # tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"sli X28 X29 16") 
            # tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"add X19 X29 X30") 
            # tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"movir X27 {self.materialize_kv_cache_offset}") 
            # tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"add X30 X27 X20") 
            # tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"movir X27 {self.materialize_kv_cache_count}") 
            # tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"add X23 X27 X23") 
            # tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"jmp __if_ud_fetched_kv_ptr_for_cache_44_post") 
            # ## If going inside lane, increment ptr
            # tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"__if_ud_fetched_kv_ptr_for_cache_43_false: addi X20 X20 {self.inter_kvpair_size * WORD_SIZE}") 
            # tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"__if_ud_fetched_kv_ptr_for_cache_44_post: jmp __while_ud_fetched_kv_ptr_for_cache_18_condition") 
            # ## Iteration finished / key is claimed before iteration
            # ## If iteration is interuppted, it means the key is just got claimed

            # tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"__if_ud_fetched_kv_ptr_for_cache_17_post: bleu X25 X22 __if_ud_fetched_kv_ptr_for_cache_47_post") 
            # # tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"__if_ud_fetched_kv_ptr_for_cache_17_post: print 'start %ld end %ld' X22 X25") 
            # # tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"bleu X25 X22 __if_ud_fetched_kv_ptr_for_cache_47_post") 
            # tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"__if_ud_fetched_kv_ptr_for_cache_45_true: movlr 8(X21) X26 0 8") 
            # if self.debug_flag:
            #     tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"print 'Claimed dest event word for claimed key %ld: %lu' X16 X26") 
            # ## If claimed, need to account for number of total cached kvs
            # tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"movir X27 0") 
            # ## Iterate and update start until find an unmatch
            # if self.record_unresolved_kv_count:
            #     tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"__while_ud_fetched_kv_ptr_for_cache_48_condition: bleu X25 X22 __if_ud_fetched_kv_ptr_for_cache_66_true") 
            # else:
            #     tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"__while_ud_fetched_kv_ptr_for_cache_48_condition: bleu X25 X22 __if_ud_fetched_kv_ptr_for_cache_47_post") 
            # ## First check if entry empty
            # tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"__while_ud_fetched_kv_ptr_for_cache_49_body: movlr 0(X20) X28 0 8") 
            # tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"beqi X28 -1 __if_ud_fetched_kv_ptr_for_cache_53_post") 
            # tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"__if_ud_fetched_kv_ptr_for_cache_51_true: movlr 0(X20) X28 0 8") 
            # ## If not matched for the first time, write new start to spd
            # tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"bequ X28 X16 __if_ud_fetched_kv_ptr_for_cache_55_false") 
            # # if self.debug_flag:
            # #     tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"__if_ud_fetched_kv_ptr_for_cache_54_true: print 'Not matching: entry %ld reads %ld at %lu' X22 X28 X20") 
            # tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"bneiu X24 0 __if_ud_fetched_kv_ptr_for_cache_59_post") 
            # tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"__if_ud_fetched_kv_ptr_for_cache_57_true: movir X31 {self.materializing_metadata_offset}") 
            # tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"add X19 X31 X24") 
            # tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"update_materializing_start_not_matched_claimed: movlr 0(X24) X28 0 8") 
            # tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"bge X28 X22 after_update_materializing_start_claimed") 
            # tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"cswp X24 X29 X28 X22") 
            # tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"bne X29 X28 update_materializing_start_not_matched_claimed") 
            # if self.debug_flag:
            #     tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"after_update_materializing_start_claimed: print 'Write start as %ld at %lu' X22 X24") 
            # else:
            #     tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"after_update_materializing_start_claimed: movir X24 1") 
            # tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"__if_ud_fetched_kv_ptr_for_cache_59_post: jmp __if_ud_fetched_kv_ptr_for_cache_53_post") 
            # if self.debug_flag:
            #     tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"__if_ud_fetched_kv_ptr_for_cache_55_false: print 'Matched: entry %ld reads %ld at %lu' X22 X28 X20") 
            #     ## If mached, send it to the claimed destination
            #     tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"send_wcont X26 X18 X20 {self.inter_kvpair_size}") 
            # else:
            #     ## If mached, send it to the claimed destination
            #     tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"__if_ud_fetched_kv_ptr_for_cache_55_false: send_wcont X26 X18 X20 {self.inter_kvpair_size}") 
            # ## Increment matched_count
            # tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"addi X27 X27 1") 
            # ## Erase this entry
            # tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"movir X28 0") 
            # tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"__for_ud_fetched_kv_ptr_for_cache_60_condition: bgeiu X28 {self.inter_kvpair_size} __if_ud_fetched_kv_ptr_for_cache_53_post") 
            # tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"__for_ud_fetched_kv_ptr_for_cache_61_body: movir X30 -1") 
            # tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"movwrl X30 X20(X28,0,0)") 
            # tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"addi X28 X28 1") 
            # tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"jmp __for_ud_fetched_kv_ptr_for_cache_60_condition") 
            # ## Step forward one entry
            # tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"__if_ud_fetched_kv_ptr_for_cache_53_post: addi X22 X22 1") 
            # ## If going across lanes, update ptr
            # tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"bneu X22 X23 __if_ud_fetched_kv_ptr_for_cache_64_false") 
            # tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"__if_ud_fetched_kv_ptr_for_cache_63_true: movir X28 {self.materialize_kv_cache_count}") 
            # tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"div X22 X28 X28") 
            # tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"andi X28 X29 63") 
            # tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"sli X29 X30 16") 
            # tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"add X19 X30 X31") 
            # tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"movir X28 {self.materialize_kv_cache_offset}") 
            # tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"add X31 X28 X20") 
            # tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"movir X28 {self.materialize_kv_cache_count}") 
            # tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"add X23 X28 X23") 
            # tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"jmp __if_ud_fetched_kv_ptr_for_cache_65_post") 
            # ## If going inside lane, increment ptr
            # tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"__if_ud_fetched_kv_ptr_for_cache_64_false: addi X20 X20 {self.inter_kvpair_size * WORD_SIZE}") 
            # tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"__if_ud_fetched_kv_ptr_for_cache_65_post: jmp __while_ud_fetched_kv_ptr_for_cache_48_condition") 
            # if self.record_unresolved_kv_count:
            #     tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"__if_ud_fetched_kv_ptr_for_cache_66_true: movir X31 {self.unresolved_kv_count_offset}") 
            #     tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"add X19 X31 X20") 
            #     tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"update_unresolved_count: movlr 0(X20) X29 0 8") 
            #     tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"add X29 X27 X30") 
            #     tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"cswp X20 X28 X29 X30") 
            #     tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"bne X28 X29 update_unresolved_count") 
            #     tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"print 'Lane %u receive_kv_ptr increment unresolved_count from %d to %d' X0 X29 X30") 
            # ## Write new start to spd if haven't
            # tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"__if_ud_fetched_kv_ptr_for_cache_47_post: bneiu X24 0 __if_ud_fetched_kv_ptr_for_cache_71_post") 
            # tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"__if_ud_fetched_kv_ptr_for_cache_69_true: movir X28 {self.materializing_metadata_offset}") 
            # tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"add X19 X28 X20") 
            # tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"update_materializing_start: movlr 0(X20) X27 0 8") 
            # tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"bge X27 X22 after_update_materializing_start") 
            # tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"cswp X20 X26 X27 X22") 
            # tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"bne X26 X27 update_materializing_start") 
            # if self.debug_flag:
            #     tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"after_update_materializing_start: print 'replace old start %ld with new start %d at %lu' X27 X22 X20") 
            # else:
            #     tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"after_update_materializing_start: movir X24 1") 

            # if self.log_kv_latency:
            #     tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"__if_ud_fetched_kv_ptr_for_cache_71_post: perflog 1 0 'receive_kv_ptr end'")
            #     tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"yield_terminate") 
            # else:
            #     tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"__if_ud_fetched_kv_ptr_for_cache_71_post: yield_terminate") 




            ## Get start spd address of this ud
            tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"entry: andi X0 X22 63") 
            tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"sli X22 X23 16") 
            tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"sub X7 X23 X19") 
            ## Locate intermediate_cache entry
            tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"movir X26 {self.intermediate_ptr_offset}") 
            tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"add X19 X26 X20") 
            ## unsigned long tmp = (entry_addr - ptr[0]) / 8;
            tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"__if_ud_fetched_kv_ptr_for_cache_0_true: movlr 0(X20) X22 0 8") 
            tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"sub X9 X22 X23") 
            tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"sari X23 X22 3") 
            if self.debug_flag:
                tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"print 'Lane %u received kv_ptr for %ld-key, operands %ld, %ld' X0 X22 X8 X9") 
            ## unsigned long tmp1 = (tmp % intermediate_cache_count) * intermediate_cache_entry_size * 8;
            ## tmp = (tmp / intermediate_cache_count) << 16;
            ## entry_ptr = base_ptr + tmp + intermediate_cache_offset + tmp1;
            tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"movir X24 {self.intermediate_cache_count}") 
            tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"mod X22 X24 X23") 
            tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"movir X24 {self.intermediate_cache_entry_size}") 
            tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"mul X23 X24 X23") 
            tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"sli X23 X23 3") 
            tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"movir X24 {self.intermediate_cache_count}") 
            tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"div X22 X24 X22") 
            tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"sli X22 X22 16") 
            tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"add X19 X22 X21") 
            tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"add X21 X23 X21") 
            tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"movir X24 {self.intermediate_cache_offset}") 
            tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"add X21 X24 X21") 
            ## Read key
            tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"movlr 0(X21) X22 0 8") 
            tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"sari X22 X16 1") 
            if self.debug_flag:
                tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"print 'Lane %u received kv_ptr for key %ld with bin address %lu(0x%lx), entry address %lu' X0 X16 X8 X8 X21") 
            ## Read num and dest
            tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"__if_ud_fetched_kv_ptr_for_cache_3_true: movir X24 -1") 
            tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"movir X25 0") 
            tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"addi X21 X20 8") 
            tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"cswp X20 X23 X24 X8") 
            if self.debug_flag:
                tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"print 'cswp dest executed, ptr: %lu, cswp_ret: %ld, before: %ld, after: %lu' X20 X23 X24 X8")

            tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"bne X23 X24 __if_ud_fetched_kv_ptr_for_cache_7_false") 
            ## Set num first
            tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"__if_ud_fetched_kv_ptr_for_cache_6_true: addi X21 X20 16") 
            tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"reset_num: movlr 0(X20) X22 0 8") 
            if self.debug_flag:
                tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"print 'before setting num: %ld' X22")
            tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"movlr -8(X20) X24 0 8") 
            tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"bne X24 X8 key_got_claimed") 
            tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"cswp X20 X23 X22 X25") 
            tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"bne X23 X22 reset_num") 
            if self.debug_flag:
                tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"print 'after setting num: %ld' X25")
            tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"movir X17 0") 
            tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"addi X2 X18 0") 
            tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"evlb X18 {self.ln_receiver_materialize_ret_ev_label}") 
            tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"jmp set_new_thread_imm") 
            tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"key_got_claimed: movlr -16(X20) X24 0 8") 
            tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"andi X24 X24 1") 
            tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"bnei X24 1 key_got_claimed") 
            tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"movlr 0(X20) X22 0 8") 
            tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"movir X17 1") 
            tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"addi X2 X18 0") 
            tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"evlb X18 {self.ln_receiver_update_unresolved_kv_count_ev_label}") 
            tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"set_new_thread_imm: evi X18 X18 255 4") 
            if self.debug_flag:
                tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"print 'not claimed, key %ld materialized count %ld' X16 X22")
            tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"evi X2 X18 {self.ln_receiver_materialize_ret_ev_label} 1") 
            tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"movir X17 0") 
            tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"jmp __if_ud_fetched_kv_ptr_for_cache_8_post") 
            tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"__if_ud_fetched_kv_ptr_for_cache_7_false: evi X2 X18 {self.ln_receiver_update_unresolved_kv_count_ev_label} 1") 
            tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"movir X17 1") 
            tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"movlr 16(X21) X22 0 8")
            if self.debug_flag:
                tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"print 'claimed, key %ld materialized count %ld' X16 X22")
            tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"__if_ud_fetched_kv_ptr_for_cache_8_post: evi X18 X18 255 4") 
            tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"addi X22 X22 1") 
            ## Read materialize_kv_cache metadata
            ## Locate start of materialize_kv_cache
            tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"movir X26 {self.materializing_metadata_offset}") 
            tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"add X19 X26 X20") 
            tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"movlr 0(X20) X23 0 8") 
            tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"movir X26 {self.materialize_kv_cache_count}") 
            tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"div X23 X26 X25") 
            tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"addi X25 X26 1") 
            tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"movir X27 {self.materialize_kv_cache_count}") 
            tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"mul X26 X27 X24") 
            tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"movir X25 0") 
            ## unsigned long end;
            ## long tmp = ((start / materialize_kv_cache_count) % 64) << 16;
            ## long tmp1 = (start % materialize_kv_cache_count) * inter_kvpair_size * 8;
            ## tmp = base_ptr + tmp + materialize_kv_cache_offset;
            ## ptr = tmp + tmp1;
            tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"__if_ud_fetched_kv_ptr_for_cache_9_true: movir X28 {self.materialize_kv_cache_count}") 
            tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"div X23 X28 X26") 
            tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"andi X26 X26 63") 
            tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"sli X26 X26 16") 
            tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"movir X28 {self.materialize_kv_cache_offset}") 
            tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"add X26 X28 X26") 
            tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"add X26 X19 X26") 
            tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"movir X28 {self.materialize_kv_cache_count}") 
            tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"mod X23 X28 X27") 
            tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"muli X27 X27 {self.inter_kvpair_size}") 
            tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"sli X27 X27 3") 
            ## end = ptr[1];
            tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"add X26 X27 X20") 
            tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"bneiu X17 0 __if_ud_fetched_kv_ptr_for_cache_14_post") 
            ## Move entry_ptr to the materialized count word, for cswp
            tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"__if_ud_fetched_kv_ptr_for_cache_12_true: addi X21 X21 16") 
            ## If not claimed, need to account for the first entry found
            tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"movir X26 0") 
            ## Iterate and update start until find an unmatch
            tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"__while_ud_fetched_kv_ptr_for_cache_15_condition: bgei X22 0 __if_ud_fetched_kv_ptr_for_cache_14_post") 
            ## First check if entry empty
            tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"__while_ud_fetched_kv_ptr_for_cache_16_body: movlr 0(X20) X27 0 8") 
            tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"beqi X27 -1 __if_ud_fetched_kv_ptr_for_cache_20_post") 
            tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"__if_ud_fetched_kv_ptr_for_cache_18_true: movlr 0(X20) X27 0 8") 
            ## If not matched for the first time, write new start to spd
            tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"movlr 0(X20) X28 0 8") 
            tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"beq X28 X16 __if_ud_fetched_kv_ptr_for_cache_22_false") 
            if self.debug_flag:
                tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"__if_ud_fetched_kv_ptr_for_cache_21_true: print 'Not matching: entry %ld reads %ld at %lu' X23 X27 X20") 
                tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"bneiu X25 0 __if_ud_fetched_kv_ptr_for_cache_26_post") 
            else:
                tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"__if_ud_fetched_kv_ptr_for_cache_21_true: bneiu X25 0 __if_ud_fetched_kv_ptr_for_cache_26_post") 
            tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"__if_ud_fetched_kv_ptr_for_cache_24_true: movir X30 {self.materializing_metadata_offset}") 
            tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"add X19 X30 X25") 
            tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"update_materializing_start_not_matched: movlr 0(X25) X27 0 8") 
            tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"bge X27 X23 after_update_materializing_start_not_matched") 
            tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"cswp X25 X28 X27 X23") 
            tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"bne X28 X27 update_materializing_start_not_matched") 
            tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"after_update_materializing_start_not_matched: movir X25 1") 
            tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"__if_ud_fetched_kv_ptr_for_cache_26_post: jmp __if_ud_fetched_kv_ptr_for_cache_20_post") 
            if self.debug_flag:
                tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"__if_ud_fetched_kv_ptr_for_cache_22_false: print 'Matched: entry %ld reads %ld at %lu' X23 X27 X20") 
                # tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"addi X22 X22 1") 
                ## If matched, first check if key just got claimed
                ## is_claimed = entry_ptr[-2] & 1;
                tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"movlr -8(X21) X28 0 8")
            else:
                tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"__if_ud_fetched_kv_ptr_for_cache_22_false: movlr -8(X21) X28 0 8")
            tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"ceq X28 X8 X17") 
            tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"xori X17 X17 1") 
            if self.debug_flag:
                tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"print 'cached dest %lu, dram ptr %lu, not equal: %ld' X28 X8 X17") 
            tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"beqiu X17 0 __if_ud_fetched_kv_ptr_for_cache_29_post") 
            ## If just got claimed, wait till claimed dest evword is written
            tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"__if_ud_fetched_kv_ptr_for_cache_27_true: subi X21 X21 16") 
            tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"evi X2 X18 {self.ln_receiver_update_unresolved_kv_count_ev_label} 1") 
            tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"evi X18 X18 255 4") 
            tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"movlr 8(X21) X27 0 8") 
            tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"__while_ud_fetched_kv_ptr_for_cache_30_condition: bneu X27 X8 __while_ud_fetched_kv_ptr_for_cache_32_post") 
            tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"__while_ud_fetched_kv_ptr_for_cache_31_body: movlr 8(X21) X27 0 8") 
            tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"jmp __while_ud_fetched_kv_ptr_for_cache_30_condition") 
            tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"__while_ud_fetched_kv_ptr_for_cache_32_post: jmp __if_ud_fetched_kv_ptr_for_cache_14_post") 
            tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"__if_ud_fetched_kv_ptr_for_cache_29_post: addi X22 X22 1") 


            tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"__if_ud_fetched_kv_ptr_for_cache_33_true: movlr 0(X21) X27 0 8") 
            tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"addi X27 X30 1") 
            tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"cswp X21 X29 X27 X30") 
            tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"bne X29 X27 __if_ud_fetched_kv_ptr_for_cache_33_true") 
            tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"subi X30 X30 1") 
            tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"muli X29 X28 {self.inter_kvpair_size}") 
            tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"sli X28 X28 3") 
            tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"add X28 X8 X28") 
            if self.debug_flag:
                tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"print 'receive_ptr materialize key %ld to Dram %lu(0x%lx) as the %ld-th kv' X16 X28 X28 X30") 
            ## Materialize the kv
            ## long* dest = cswp_ret * inter_kvpair_size * 8 + kv_arr_addr;
            tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"send_dmlm X28 X18 X20 {self.inter_kvpair_size}") 
            ## Erase this entry
            tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"movir X27 0") 
            tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"__for_ud_fetched_kv_ptr_for_cache_36_condition: bgeiu X27 {self.inter_kvpair_size} __if_ud_fetched_kv_ptr_for_cache_20_post") 
            tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"__for_ud_fetched_kv_ptr_for_cache_37_body: movir X30 -1") 
            tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"movwrl X30 X20(X27,0,0)") 
            tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"addi X27 X27 1") 
            tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"jmp __for_ud_fetched_kv_ptr_for_cache_36_condition") 
            ## Step forward one entry
            tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"__if_ud_fetched_kv_ptr_for_cache_20_post: addi X23 X23 1") 
            ## If going across lanes, update ptr
            tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"bneu X23 X24 __if_ud_fetched_kv_ptr_for_cache_40_false") 
            tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"__if_ud_fetched_kv_ptr_for_cache_39_true: movir X27 {self.materialize_kv_cache_count}") 
            tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"div X23 X27 X27") 
            tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"andi X27 X28 63") 
            tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"sli X28 X29 16") 
            tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"add X19 X29 X30") 
            tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"movir X27 {self.materialize_kv_cache_offset}") 
            tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"add X30 X27 X20") 
            tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"movir X27 {self.materialize_kv_cache_count}") 
            tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"add X24 X27 X24") 
            tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"jmp __if_ud_fetched_kv_ptr_for_cache_41_post") 
            ## If going inside lane, increment ptr
            tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"__if_ud_fetched_kv_ptr_for_cache_40_false: addi X20 X20 {self.inter_kvpair_size * WORD_SIZE}") 
            tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"__if_ud_fetched_kv_ptr_for_cache_41_post: jmp __while_ud_fetched_kv_ptr_for_cache_15_condition") 
            ## Iteration finished / key is claimed before iteration
            ## If iteration is interuppted, it means the key is just got claimed
            tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"__if_ud_fetched_kv_ptr_for_cache_14_post: bgei X22 0 __if_ud_fetched_kv_ptr_for_cache_44_post") 
            tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"__if_ud_fetched_kv_ptr_for_cache_42_true: movlr 8(X21) X26 0 8") 
            if self.debug_flag:
                tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"print 'Claimed dest event word for claimed key %ld: %lu' X16 X26") 
            ## // If claimed, need to account for number of total cached kvs
            ## unsigned long matched_count = 0;
            ## Iterate and update start until find an unmatch
            tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"__while_ud_fetched_kv_ptr_for_cache_45_condition: bgei X22 0 __if_ud_fetched_kv_ptr_for_cache_44_post") 
            ## First check if entry empty
            tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"__while_ud_fetched_kv_ptr_for_cache_46_body: movlr 0(X20) X27 0 8") 
            tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"beqi X27 -1 __if_ud_fetched_kv_ptr_for_cache_50_post") 
            tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"__if_ud_fetched_kv_ptr_for_cache_48_true: movlr 0(X20) X27 0 8") 
            ## If not matched for the first time, write new start to spd
            tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"bequ X27 X16 __if_ud_fetched_kv_ptr_for_cache_52_false") 
            if self.debug_flag:
                tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"__if_ud_fetched_kv_ptr_for_cache_51_true: print 'Not matching: entry %ld reads %ld at %lu' X23 X27 X20") 
                tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"bneiu X25 0 __if_ud_fetched_kv_ptr_for_cache_56_post") 
            else:
                tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"__if_ud_fetched_kv_ptr_for_cache_51_true: bneiu X25 0 __if_ud_fetched_kv_ptr_for_cache_56_post") 
            tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"__if_ud_fetched_kv_ptr_for_cache_54_true: movir X30 {self.materializing_metadata_offset}") 
            tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"add X19 X30 X25") 
            tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"update_materializing_start_not_matched_claimed: movlr 0(X25) X27 0 8") 
            tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"bge X27 X23 after_update_materializing_start_claimed") 
            tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"cswp X25 X28 X27 X23") 
            tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"bne X28 X27 update_materializing_start_not_matched_claimed") 
            tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"after_update_materializing_start_claimed: movir X25 1") 
            tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"__if_ud_fetched_kv_ptr_for_cache_56_post: jmp __if_ud_fetched_kv_ptr_for_cache_50_post") 
            if self.debug_flag:
                tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"__if_ud_fetched_kv_ptr_for_cache_52_false: print 'Matched: entry %ld reads %ld at %lu' X23 X27 X20") 
                ## If mached, send it to the claimed destination
                tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"addi X22 X22 1") 
            else:
                tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"__if_ud_fetched_kv_ptr_for_cache_52_false: addi X22 X22 1") 
            tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"send_wcont X26 X18 X20 {self.inter_kvpair_size}") 
            ## // Increment matched_count
            ## matched_count = matched_count + 1;
            ## Erase this entry
            tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"movir X27 0") 
            tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"__for_ud_fetched_kv_ptr_for_cache_57_condition: bgeiu X27 {self.inter_kvpair_size} __if_ud_fetched_kv_ptr_for_cache_50_post") 
            tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"__for_ud_fetched_kv_ptr_for_cache_58_body: movir X29 -1") 
            tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"movwrl X29 X20(X27,0,0)") 
            tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"addi X27 X27 1") 
            tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"jmp __for_ud_fetched_kv_ptr_for_cache_57_condition") 
            ## Step forward one entry
            tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"__if_ud_fetched_kv_ptr_for_cache_50_post: addi X23 X23 1") 
            ## If going across lanes, update ptr
            tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"bneu X23 X24 __if_ud_fetched_kv_ptr_for_cache_61_false") 
            tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"__if_ud_fetched_kv_ptr_for_cache_60_true: movir X27 {self.materialize_kv_cache_count}") 
            tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"div X23 X27 X27") 
            tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"andi X27 X28 63") 
            tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"sli X28 X29 16") 
            tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"add X19 X29 X30") 
            tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"movir X27 {self.materialize_kv_cache_offset}") 
            tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"add X30 X27 X20") 
            tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"movir X27 {self.materialize_kv_cache_count}") 
            tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"add X24 X27 X24") 
            tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"jmp __if_ud_fetched_kv_ptr_for_cache_62_post") 
            ## If going inside lane, increment ptr
            tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"__if_ud_fetched_kv_ptr_for_cache_61_false: addi X20 X20 {self.inter_kvpair_size * WORD_SIZE}") 
            tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"__if_ud_fetched_kv_ptr_for_cache_62_post: jmp __while_ud_fetched_kv_ptr_for_cache_45_condition") 
            ## Write new start to spd if haven't
            tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"__if_ud_fetched_kv_ptr_for_cache_44_post: bneiu X25 0 __if_ud_fetched_kv_ptr_for_cache_65_post") 
            tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"__if_ud_fetched_kv_ptr_for_cache_63_true: movir X28 {self.materializing_metadata_offset}") 
            tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"add X19 X28 X20") 
            tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"update_materializing_start: movlr 0(X20) X27 0 8") 
            tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"bge X27 X23 after_update_materializing_start") 
            tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"cswp X20 X26 X27 X23") 
            tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"bne X26 X27 update_materializing_start") 
            tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"after_update_materializing_start: movir X25 1") 
            tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"__if_ud_fetched_kv_ptr_for_cache_65_post: yield_terminate") 
  


            return

    def __gen_receiver_materialize_ret(self, tran):

        tran.writeAction(f"yieldt")

        return

    def __gen_receiver_update_unresolved_kv_count(self, tran):
        lm_reg = "X16"

        if self.record_unresolved_kv_count:
            if self.grlb_type == 'ud':
                base_addr = "X17"
                cswp_ret = "X18"

                # Get Lane 0 spd start address
                tran.writeAction(f"andi {'X0'} {self.scratch[0]} {63}")
                tran.writeAction(f"sli {self.scratch[0]} {self.scratch[0]} {int(log2(SPD_BANK_SIZE))}")
                tran.writeAction(f"sub {'X7'} {self.scratch[0]} {base_addr}")

                # Get count entry address
                tran.writeAction(f"movir {lm_reg} {self.unresolved_kv_count_offset}")
                tran.writeAction(f"add {base_addr} {lm_reg} {lm_reg}")

                # Atomic update unresolved kv count
                tran.writeAction(f"update_unresolved_count: movlr 0({lm_reg}) {self.scratch[0]} 0 {WORD_SIZE}")
                tran.writeAction(f"subi {self.scratch[0]} {self.scratch[1]} {1}")
                tran.writeAction(f"cswp {lm_reg} {cswp_ret} {self.scratch[0]} {self.scratch[1]}")
                tran.writeAction(f"bne {cswp_ret} {self.scratch[0]} update_unresolved_count")
                if self.debug_flag:
                    tran.writeAction(f"print '[LB_DEBUG] receiver_update_unresolved_kv_count update unresolved_kv_count from %d to %d' {self.scratch[0]} {self.scratch[1]}")

            elif self.grlb_type == 'lane':

                # Update unresolved kv count
                tran.writeAction(f"movir {lm_reg} {self.unresolved_kv_count_offset}")
                tran.writeAction(f"add {'X7'} {lm_reg} {lm_reg}")
                tran.writeAction(f"movlr 0({lm_reg}) {self.scratch[0]} 0 {WORD_SIZE}")
                tran.writeAction(f"subi {self.scratch[0]} {self.scratch[1]} {1}")
                if self.debug_flag:
                    tran.writeAction(f"print '[LB_DEBUG] receiver_update_unresolved_kv_count update unresolved_kv_count from %d to %d' {self.scratch[0]} {self.scratch[1]}")
                tran.writeAction(f"movrl {self.scratch[1]} 0({lm_reg}) 0 {WORD_SIZE}")

        tran.writeAction(f"yieldt")

    def __gen_receiver_claim_work(self, tran):
        '''
        Event: receiver_claim_work
            Called from other lanes' worker
            Return key information if there is any unresolved
            Return self._no_work_to_be_claimed_flag if none
        X1: worker event on claiming resource thread

        If self.claim_multiple_work is True:
        X8: Number of work source lane wants to claim
        '''
        claiming_count = "UDPR_2"
        cswp_ret = "UDPR_3"
        base_addr = "UDPR_4"
        dest = "UDPR_5"
        num = "UDPR_6"
        addr = "UDPR_7" 
        part_end = "UDPR_9"
        entry_ind = "UDPR_10"
        receive_addr = "UDPR_11"
        scratch = self.scratch
        ev_word = self.ev_word 
        cont_word = "UDPR_15"

        materialize_metadata_addr = dest
        intermediate_ptr = num

        if 'mapper' in self.lb_type:
            if 'reducer' in self.lb_type:
                if self.enable_mr_barrier:
                    next_phase_label = 'check_terminate_bit'
                else:
                    next_phase_label = 'claim_reduces'
            else:
                next_phase_label = 'local_work_resolved'
            # next_phase_label = 'claim_reduces' if 'reducer' in self.lb_type else 'local_work_resolved'

            # Get Lane 0 spd start address
            tran.writeAction(f"andi {'X0'} {scratch[0]} {63}")
            tran.writeAction(f"sli {scratch[0]} {scratch[0]} {int(log2(SPD_BANK_SIZE))}")
            tran.writeAction(f"sub {'X7'} {scratch[0]} {base_addr}")
            tran.writeAction(f"movir {addr} {self.ln_part_start_offset}")
            if self.intra_map_work_stealing or self.global_map_work_stealing:
                tran.writeAction(f"add {'X7'} {addr} {addr}")
            else:
                tran.writeAction(f"add {base_addr} {addr} {addr}")

            # Read partition start and end
            tran.writeAction(f"movlr 0({addr}) {scratch[0]} 0 {WORD_SIZE}")
            tran.writeAction(f"movlr {self.ln_part_end_offset - self.ln_part_start_offset}({addr}) {part_end} 0 {WORD_SIZE}")

            # Try to update start entry atomically
            if self.debug_flag:
                tran.writeAction(f"perflog 1 0 'Start claiming remote'")
            tran.writeAction(f"claim_maps: beq {scratch[0]} {part_end} {next_phase_label}")
            tran.writeAction(f"addi {scratch[0]} {scratch[1]} {WORD_SIZE * self.in_kvset_iter_size}")
            tran.writeAction(f"cswp {addr} {dest} {scratch[0]} {scratch[1]}")
            tran.writeAction(f"beq {scratch[0]} {dest} claimed_maps")
            tran.writeAction(f"movlr 0({addr}) {scratch[0]} 0 {WORD_SIZE}")
            tran.writeAction(f"jmp claim_maps")

            # If successfully updated, send partition ptr to mapper
            tran.writeAction(f"claimed_maps: evii {cont_word} {self.ln_receiver_set_terminate_bit_ret_ev_label} {255} {5}")
            if self.debug_flag:
                tran.writeAction(f"perflog 1 0 'End claiming remote'")
            tran.writeAction(f"addi {'X1'} {ev_word} {0}")
            tran.writeAction(f"evlb {ev_word} {self.ln_worker_claimed_map_ev_label}")
            tran.writeAction(f"movir {addr} {self.ud_mstr_evw_offset}")
            tran.writeAction(f"add {'X7'} {addr} {addr}")
            tran.writeAction(f"movlr 0({addr}) {scratch[1]} 0 {WORD_SIZE}")
            tran.writeAction(f"movir {scratch[0]} {self._map_flag}")
            tran.writeAction(f"sendr3_wcont {ev_word} {cont_word} {scratch[0]} {dest} {scratch[1]}")
            if self.debug_flag:
                tran.writeAction(f"sri X0 {scratch[1]} {6}")
                tran.writeAction(f"andi {scratch[1]} {scratch[1]} {0b11}")
                tran.writeAction(f"sri X1 {scratch[0]} {32}")
                tran.writeAction(f"print '[LB_DEBUG][Remote] Lane %d claimed ud %d map partition at %lu end %lu' {scratch[0]} {scratch[1]} {dest} {part_end}")
            tran.writeAction(f"yieldt")


            tran.writeAction(f"check_terminate_bit: movir {addr} {self.terminate_bit_offset}")
            tran.writeAction(f"add X7 {addr} {addr}")
            tran.writeAction(f"movlr 0({addr}) {scratch[0]} 0 {WORD_SIZE}")
            tran.writeAction(f"blti {scratch[0]} {0} local_work_resolved")

        if 'reducer' in self.lb_type:

            if self.grlb_type == 'ud':

                # Get Lane 0 spd start address
                tran.writeAction(f"claim_reduces: andi {'X0'} {scratch[0]} {63}")
                tran.writeAction(f"sli {scratch[0]} {scratch[0]} {int(log2(SPD_BANK_SIZE))}")
                tran.writeAction(f"sub {'X7'} {scratch[0]} {base_addr}")

                if self.claim_multiple_work:
                    tran.writeAction(f"addi X8 {claiming_count} {0}")
                tran.writeAction(f"movir {receive_addr} {self.inter_key_received_count_offset}")
                tran.writeAction(f"add {base_addr} {receive_addr} {receive_addr}")
                tran.writeAction(f"movir {addr} {self.inter_key_resolved_count_offset}")
                tran.writeAction(f"add {base_addr} {addr} {addr}")

                # Read received and resolved key count
                tran.writeAction(f"read_counts: movlr 0({receive_addr}) {scratch[1]} 0 {WORD_SIZE}")
                tran.writeAction(f"movlr 0({addr}) {scratch[0]} 0 {WORD_SIZE}")


                if self.do_all_reduce and self.do_all_reduce_with_materialize:
                    tran.writeAction(f"blt {scratch[0]} {scratch[1]} claim_local_cache")
                    tran.writeAction(f"movir {materialize_metadata_addr} {self.materializing_metadata_offset}")
                    tran.writeAction(f"add {base_addr} {materialize_metadata_addr} {materialize_metadata_addr}")
                    tran.writeAction(f"movlr 0({materialize_metadata_addr}) {scratch[0]} 0 {WORD_SIZE}")
                    tran.writeAction(f"movlr {WORD_SIZE}({materialize_metadata_addr}) {scratch[1]} 0 {WORD_SIZE}")
                    tran.writeAction(f"bge {scratch[0]} {scratch[1]} local_work_resolved")

                    tran.writeAction(f"claiming_local_reduces_from_dram: add {scratch[0]} {claiming_count} {entry_ind}")
                    tran.writeAction(f"ble {entry_ind} {scratch[1]} claim_dram")
                    tran.writeAction(f"addi {scratch[1]} {entry_ind} {0}")
                    tran.writeAction(f"sub {scratch[1]} {scratch[0]} {claiming_count}")
                    tran.writeAction(f"claim_dram: cswp {materialize_metadata_addr} {cswp_ret} {scratch[0]} {entry_ind}")
                    tran.writeAction(f"bne {cswp_ret} {scratch[0]} read_counts")

                    if self.debug_flag:
                        tran.writeAction(f"sri X0 {cswp_ret} {6}")
                        tran.writeAction(f"print 'Remote claimed ud %u dram reduce task count: %lu, starting index %lu, next unclaimed index %lu, received_count %lu' {cswp_ret} {claiming_count} {scratch[0]} {entry_ind} {scratch[1]}")
                    tran.writeAction(f"addi {scratch[0]} {entry_ind} 0")

                    # If successfully claimed, send out claimed count first
                    tran.writeAction(f"addi {'X1'} {ev_word} {0}")
                    tran.writeAction(f"evlb {ev_word} {self.ln_worker_claimed_reduce_count_ev_label}")
                    tran.writeAction(f"evii {cont_word} {self.ln_receiver_acknowledge_key_executed_ev_label} 255 5")
                    tran.writeAction(f"sendr_wcont {ev_word} {cont_word} {claiming_count} {claiming_count}")
                    
                    # Get the address of next unclaimed key
                    if (self.materialize_kv_dram_size & (self.materialize_kv_dram_size-1)) == 0:
                        tran.writeAction(f"movir {cswp_ret} {1}")
                        tran.writeAction(f"sli {cswp_ret} {cswp_ret} {int(log2(self.materialize_kv_dram_size))}")
                    else:
                        tran.writeAction(f"movir {cswp_ret} {self.materialize_kv_dram_size}")
                    tran.writeAction(f"movir {addr} {self.intermediate_ptr_offset}")
                    tran.writeAction(f"add {base_addr} {addr} {addr}")
                    tran.writeAction(f"movlr 0({addr}) {scratch[1]} 0 {WORD_SIZE}")
                    tran.writeAction(f"mod {entry_ind} {cswp_ret} {scratch[0]}")
                    tran.writeAction(f"muli {scratch[0]} {scratch[0]} {self.inter_kvpair_size * WORD_SIZE}")
                    tran.writeAction(f"add {scratch[0]} {scratch[1]} {scratch[1]}")
                    

                    # Prepare event word
                    tran.writeAction(f"addi {'X1'} {ev_word} {0}")
                    tran.writeAction(f"evlb {ev_word} {self.ln_worker_fetched_kv_ptr_ev_label}")

                    # Send dram request to read intermediate kv
                    tran.writeAction(f"dram_iteration_claim: beqi {claiming_count} 0 iteration_end")
                    tran.writeAction(f"sendr_wcont {ev_word} {cont_word} {scratch[1]} {scratch[1]}")
                    if self.debug_flag:
                        tran.writeAction(f"sri X0 X16 6")
                        tran.writeAction(f"sri X1 X17 32")
                        tran.writeAction(f"print 'Send remote ud %u %lu-th claimed dram key to lane %lu at dram %lu' {'X16'} {entry_ind} {'X17'} {scratch[1]}")

                    tran.writeAction(f"subi {claiming_count} {claiming_count} {1}")
                    tran.writeAction(f"addi {scratch[1]} {scratch[1]} {self.intermediate_cache_entry_size * WORD_SIZE}")
                    tran.writeAction(f"addi {entry_ind} {entry_ind} {1}")
                    tran.writeAction(f"mod {entry_ind} {cswp_ret} {scratch[0]}")
                    tran.writeAction(f"bnei {scratch[0]} {0} dram_iteration_claim")
                    tran.writeAction(f"movlr 0({addr}) {scratch[1]} 0 {WORD_SIZE}")
                    tran.writeAction(f"jmp dram_iteration_claim")

                else:
                    tran.writeAction(f"bge {scratch[0]} {scratch[1]} local_work_resolved")

                # If there is work to claim, claim by atomic update resolved count
                if self.claim_multiple_work:
                    tran.writeAction(f"claim_local_cache: add {scratch[0]} {claiming_count} {entry_ind} ")
                    tran.writeAction(f"ble {entry_ind} {scratch[1]} claim")
                    tran.writeAction(f"addi {scratch[1]} {entry_ind} {0}")
                    tran.writeAction(f"sub {scratch[1]} {scratch[0]} {claiming_count}")
                    tran.writeAction(f"claim: cswp {addr} {cswp_ret} {scratch[0]} {entry_ind}")
                else:
                    tran.writeAction(f"claim_local_cache: addi {scratch[0]} {scratch[1]} {1}")
                    tran.writeAction(f"cswp {addr} {cswp_ret} {scratch[0]} {scratch[1]}")
                tran.writeAction(f"bne {cswp_ret} {scratch[0]} read_counts")
                tran.writeAction(f"addi {scratch[0]} {entry_ind} 0")

                if self.claim_multiple_work:
                    if self.debug_flag:
                        tran.writeAction(f"sri X0 {scratch[0]} {6}")
                        tran.writeAction(f"print 'Remote lane claimed %u keys, ud %u received_count %lu resolved_count %lu' {claiming_count} {scratch[1]} {entry_ind}")
                    # If successfully claimed, send out claimed count first
                    tran.writeAction(f"addi {'X1'} {ev_word} {0}")
                    tran.writeAction(f"evlb {ev_word} {self.ln_worker_claimed_reduce_count_ev_label}")
                    tran.writeAction(f"evii {cont_word} {self.ln_receiver_acknowledge_key_executed_ev_label} 255 5")
                    tran.writeAction(f"sendr_wcont {ev_word} {cont_word} {claiming_count} {claiming_count}")

                    # Get the ptr to first entry
                    tran.writeAction(f"divi {cswp_ret} {scratch[1]} {self.intermediate_cache_count}")
                    tran.writeAction(f"modi {scratch[1]} {scratch[1]} {LANE_PER_UD}")
                    tran.writeAction(f"modi {cswp_ret} {cswp_ret} {self.intermediate_cache_count}")
                    tran.writeAction(f"sli {scratch[1]} {scratch[1]} {int(log2(SPD_BANK_SIZE))}")
                    tran.writeAction(f"add {base_addr} {scratch[1]} {addr}")
                    tran.writeAction(f"movir {scratch[0]} {self.intermediate_cache_offset}")
                    tran.writeAction(f"add {scratch[0]} {addr} {addr}")
                    tran.writeAction(f"muli {cswp_ret} {scratch[0]} {(self.intermediate_cache_entry_size)*WORD_SIZE}")
                    tran.writeAction(f"add {scratch[0]} {addr} {addr}")

                    # Prepare event words
                    tran.writeAction(f"addi {'X1'} {ev_word} {0}")
                    tran.writeAction(f"evlb {ev_word} {self.ln_worker_claimed_reduce_ev_label}")
                    tran.writeAction(f"evii {cont_word} {self.ln_receiver_acknowledge_key_executed_ev_label} {255} {5}")

                    if self.do_all_reduce:
                        tran.writeAction(f"iteration_claim: beqi {claiming_count} 0 iteration_end")
                        tran.writeAction(f"check_entry_if_being_written: movlr 0({addr}) {scratch[0]} 0 {WORD_SIZE}")
                        tran.writeAction(f"beqi {scratch[0]} -1 check_entry_if_being_written")
                        tran.writeAction(f"send_wcont {ev_word} {cont_word} {addr} {self.inter_kvpair_size}")
                        if self.debug_flag:
                            tran.writeAction(f"movlr 0({addr}) {part_end} 0 {WORD_SIZE}")
                            tran.writeAction(f"sri {'X1'} {scratch[0]} {32}")
                            tran.writeAction(f"print 'Remote Lane %d claimed %ld-th key %lu from lane %d at %lu' {scratch[0]} {entry_ind} {part_end} X0 {addr}")
                        tran.writeAction(f"movir {self.scratch[1]} {-1}")
                        tran.writeAction(f"movrl {self.scratch[1]} 0({addr}) 0 {WORD_SIZE}")
                    else:
                        tran.writeAction(f"evi {'X1'} {cswp_ret} {255} {0b0100}")
                        tran.writeAction(f"evlb {cswp_ret} {self.kv_reduce_init_ev_label}")

                        # Prepare to iterate
                        tran.writeAction(f"movir {scratch[1]} {self.send_buffer_offset}")
                        tran.writeAction(f"add {'X7'} {scratch[1]} {scratch[1]}")
                        tran.writeAction(f"movir {scratch[0]} {self._reduce_flag}")
                        tran.writeAction(f"movrl {scratch[0]} 0({scratch[1]}) 0 {WORD_SIZE}")

                        # Iterate to send out claimed keys
                        tran.writeAction(f"iteration_claim: beqi {claiming_count} 0 iteration_end")
                        tran.writeAction(f"check_entry_if_being_written: movlr 0({addr}) {scratch[0]} 0 {WORD_SIZE}")
                        tran.writeAction(f"beqi {scratch[0]} -1 check_entry_if_being_written")
                        tran.writeAction(f"movlr {WORD_SIZE}({addr}) {dest} 0 {WORD_SIZE}")
                        tran.writeAction(f"movlr {WORD_SIZE * 2}({addr}) {num} 0 {WORD_SIZE}")
                        tran.writeAction(f"movrl {dest} {WORD_SIZE}({scratch[1]}) 0 {WORD_SIZE}")
                        tran.writeAction(f"bgei {num} {0} buffer_num")
                        tran.writeAction(f"movir {num} {0}")
                        tran.writeAction(f"buffer_num: movrl {num} {WORD_SIZE * 2}({scratch[1]}) 0 {WORD_SIZE}")
                        tran.writeAction(f"movrl {addr} {WORD_SIZE * 3}({scratch[1]}) 0 {WORD_SIZE}")
                        tran.writeAction(f"send_wcont {ev_word} {cont_word} {scratch[1]} {4}")

                        # Update claimed bit in key
                        tran.writeAction(f"movlr 0({addr}) {scratch[0]} 0 {WORD_SIZE}")
                        tran.writeAction(f"ori {scratch[0]} {scratch[0]} {1}")
                        # Update claimed event word
                        tran.writeAction(f"movrl {cswp_ret} {WORD_SIZE}({addr}) 0 {WORD_SIZE}")
                        tran.writeAction(f"movrl {scratch[0]} 0({addr}) 0 {WORD_SIZE}")

                        if self.debug_flag:
                            tran.writeAction(f"sri {scratch[0]} {part_end} {1}")
                            tran.writeAction(f"sri {'X1'} {scratch[0]} {32}")
                            tran.writeAction(f"print 'Remote Lane %d claimed %ld-th key %lu from lane %d with dram address %lu(0x%lx) and number %d' {scratch[0]} {entry_ind} {part_end} X0 {dest} {dest} {num}")

                    tran.writeAction(f"subi {claiming_count} {claiming_count} {1}")
                    tran.writeAction(f"addi {addr} {addr} {self.intermediate_cache_entry_size * WORD_SIZE}")
                    tran.writeAction(f"addi {entry_ind} {entry_ind} {1}")
                    tran.writeAction(f"modi {entry_ind} {scratch[0]} {self.intermediate_cache_count}")
                    tran.writeAction(f"bnei {scratch[0]} {0} iteration_claim")

                    tran.writeAction(f"divi {entry_ind} {scratch[0]} {self.intermediate_cache_count}")
                    tran.writeAction(f"modi {scratch[0]} {scratch[0]} {LANE_PER_UD}")
                    tran.writeAction(f"beqi {scratch[0]} {0} return_to_beginning")

                    tran.writeAction(f"movir {scratch[0]} {SPD_BANK_SIZE - self.intermediate_cache_size}")
                    tran.writeAction(f"add {addr} {scratch[0]} {addr}")
                    tran.writeAction(f"jmp iteration_claim")

                    tran.writeAction(f"return_to_beginning: movir {addr} {self.intermediate_cache_offset}")
                    tran.writeAction(f"add {base_addr} {addr} {addr}")
                    tran.writeAction(f"jmp iteration_claim")

                    tran.writeAction(f"iteration_end: yieldt")
                else:
                    # Get the kv ptr
                    tran.writeAction(f"divi {cswp_ret} {scratch[1]} {self.intermediate_cache_count}")
                    tran.writeAction(f"modi {cswp_ret} {cswp_ret} {self.intermediate_cache_count}")
                    tran.writeAction(f"sli {scratch[1]} {scratch[1]} {int(log2(SPD_BANK_SIZE))}")
                    tran.writeAction(f"add {base_addr} {scratch[1]} {addr}")
                    tran.writeAction(f"movir {scratch[0]} {self.intermediate_cache_offset}")
                    tran.writeAction(f"add {scratch[0]} {addr} {addr}")
                    tran.writeAction(f"muli {cswp_ret} {scratch[0]} {(self.intermediate_cache_entry_size)*WORD_SIZE}")
                    tran.writeAction(f"add {scratch[0]} {addr} {addr}")

                    # Send the entry
                    if self.do_all_reduce:
                        tran.writeAction(f"addi {'X1'} {ev_word} {0}")
                        tran.writeAction(f"evlb {ev_word} {self.ln_worker_claimed_reduce_ev_label}")
                        tran.writeAction(f"evii {cont_word} {self.ln_receiver_acknowledge_key_executed_ev_label} {255} {5}")
                        tran.writeAction(f"send_wcont {ev_word} {cont_word} {addr} {self.inter_kvpair_size}")
                        if self.debug_flag:
                            tran.writeAction(f"movlr 0({addr}) {part_end} 0 {WORD_SIZE}")
                            tran.writeAction(f"sri {'X1'} {scratch[0]} {32}")
                            tran.writeAction(f"print 'Remote Lane %d claimed %ld-th key %lu from lane %d at %lu' {scratch[0]} {entry_ind} {part_end} X0 {addr}")
                        tran.writeAction(f"movir {self.scratch[1]} {-1}")
                        tran.writeAction(f"movrl {self.scratch[1]} 0({addr}) 0 {WORD_SIZE}")
                        tran.writeAction(f"jmp receiver_claim_work_end")
                    else:
                        tran.writeAction(f"movir {scratch[0]} {self._reduce_flag}")
                        tran.writeAction(f"movir {scratch[1]} {self.send_buffer_offset}")
                        tran.writeAction(f"add {'X7'} {scratch[1]} {scratch[1]}")
                        tran.writeAction(f"movrl {scratch[0]} 0({scratch[1]}) 0 {WORD_SIZE}")
                        tran.writeAction(f"check_entry_if_being_written: movlr 0({addr}) {scratch[0]} 0 {WORD_SIZE}")
                        tran.writeAction(f"beqi {scratch[0]} -1 check_entry_if_being_written")

                        # Update claimed event word
                        tran.writeAction(f"evi {'X1'} {ev_word} {255} {0b0100}")
                        tran.writeAction(f"evlb {ev_word} {self.kv_reduce_init_ev_label}")
                        # Update claimed bit in key
                        tran.writeAction(f"movlr 0({addr}) {scratch[0]} 0 {WORD_SIZE}")
                        tran.writeAction(f"ori {scratch[0]} {scratch[0]} {1}")
                        # Atomic update cached dest
                        cswp_addr = "UDPR_0"
                        cswp_ret = "UDPR_1"
                        tran.writeAction(f"addi {addr} {cswp_addr} {WORD_SIZE}")
                        tran.writeAction(f"read_dest: movlr {WORD_SIZE}({addr}) {dest} 0 {WORD_SIZE}")
                        tran.writeAction(f"movlr {WORD_SIZE * 2}({addr}) {num} 0 {WORD_SIZE}")
                        tran.writeAction(f"cswp {cswp_addr} {cswp_ret} {dest} {ev_word}")
                        tran.writeAction(f"bne {cswp_ret} {dest} read_dest")
                        tran.writeAction(f"movrl {scratch[0]} 0({addr}) 0 {WORD_SIZE}")
                        # Write content to sendbuffer
                        tran.writeAction(f"movrl {dest} {WORD_SIZE}({scratch[1]}) 0 {WORD_SIZE}")
                        tran.writeAction(f"bgei {num} {0} buffer_num")
                        tran.writeAction(f"movir {num} {0}")
                        tran.writeAction(f"buffer_num: movrl {num} {WORD_SIZE * 2}({scratch[1]}) 0 {WORD_SIZE}")
                        tran.writeAction(f"movrl {addr} {WORD_SIZE * 3}({scratch[1]}) 0 {WORD_SIZE}")
                        tran.writeAction(f"evii {cont_word} {self.ln_receiver_acknowledge_key_executed_ev_label} {255} {5}")

                        # # Update claimed bit in key
                        # tran.writeAction(f"movlr 0({addr}) {scratch[0]} 0 {WORD_SIZE}")
                        # tran.writeAction(f"ori {scratch[0]} {scratch[0]} {1}")
                        # tran.writeAction(f"movrl {scratch[0]} 0({addr}) 0 {WORD_SIZE}")

                        tran.writeAction(f"addi {'X1'} {ev_word} {0}")
                        tran.writeAction(f"evlb {ev_word} {self.ln_worker_claimed_reduce_ev_label}")
                        tran.writeAction(f"send_wcont {ev_word} {cont_word} {scratch[1]} {4}")

            elif self.grlb_type == 'lane':
                tran.writeAction(f"claim_reduces: movir {addr} {self.inter_key_received_count_offset}")
                tran.writeAction(f"add {'X7'} {addr} {addr}")
                tran.writeAction(f"movlr 0({addr}) {scratch[1]} 0 {WORD_SIZE}")
                tran.writeAction(f"movir {addr} {self.inter_key_resolved_count_offset}")
                tran.writeAction(f"add {'X7'} {addr} {addr}")
                tran.writeAction(f"movlr 0({addr}) {scratch[0]} 0 {WORD_SIZE}")

                if self.do_all_reduce and self.do_all_reduce_with_materialize:
                    tran.writeAction(f"blt {scratch[0]} {scratch[1]} claim_local_cache")
                    tran.writeAction(f"movir {materialize_metadata_addr} {self.materializing_metadata_offset}")
                    tran.writeAction(f"add {'X7'} {materialize_metadata_addr} {materialize_metadata_addr}")
                    tran.writeAction(f"movlr 0({materialize_metadata_addr}) {scratch[0]} 0 {WORD_SIZE}")
                    tran.writeAction(f"movlr {WORD_SIZE}({materialize_metadata_addr}) {scratch[1]} 0 {WORD_SIZE}")
                    tran.writeAction(f"bge {scratch[0]} {scratch[1]} local_work_resolved")

                    tran.writeAction(f"claiming_local_reduces_from_dram: addi {scratch[0]} {entry_ind} {1}")
                    tran.writeAction(f"claim_dram: cswp {materialize_metadata_addr} {cswp_ret} {scratch[0]} {entry_ind}")

                    if self.debug_flag:
                        tran.writeAction(f"sri X0 {cswp_ret} {6}")
                        tran.writeAction(f"print 'Remote claimed ud %u dram reduce task count: %lu, starting index %lu, next unclaimed index %lu, received_count %lu' {cswp_ret} {claiming_count} {scratch[0]} {entry_ind} {scratch[1]}")
                    tran.writeAction(f"addi {scratch[0]} {entry_ind} 0")

                    # If successfully claimed, send out claimed count first
                    tran.writeAction(f"addi {'X1'} {ev_word} {0}")
                    tran.writeAction(f"evlb {ev_word} {self.ln_worker_claimed_reduce_count_ev_label}")
                    tran.writeAction(f"evii {cont_word} {self.ln_receiver_acknowledge_key_executed_ev_label} 255 5")
                    tran.writeAction(f"movir {claiming_count} {1}")
                    tran.writeAction(f"sendr_wcont {ev_word} {cont_word} {claiming_count} {claiming_count}")

                    # Get the address of next unclaimed key
                    if (self.materialize_kv_dram_size & (self.materialize_kv_dram_size-1)) == 0:
                        tran.writeAction(f"movir {cswp_ret} {1}")
                        tran.writeAction(f"sli {cswp_ret} {cswp_ret} {int(log2(self.materialize_kv_dram_size))}")
                    else:
                        tran.writeAction(f"movir {cswp_ret} {self.materialize_kv_dram_size}")
                    tran.writeAction(f"movir {addr} {self.intermediate_ptr_offset}")
                    tran.writeAction(f"add {'X7'} {addr} {addr}")
                    tran.writeAction(f"movlr 0({addr}) {scratch[1]} 0 {WORD_SIZE}")
                    tran.writeAction(f"mod {entry_ind} {cswp_ret} {scratch[0]}")
                    tran.writeAction(f"muli {scratch[0]} {scratch[0]} {self.inter_kvpair_size * WORD_SIZE}")
                    tran.writeAction(f"add {scratch[0]} {scratch[1]} {scratch[1]}")

                    # Prepare event word
                    tran.writeAction(f"addi {'X1'} {ev_word} {0}")
                    tran.writeAction(f"evlb {ev_word} {self.ln_worker_fetched_kv_ptr_ev_label}")

                    # Send dram request to read intermediate kv
                    tran.writeAction(f"sendr_wcont {ev_word} {cont_word} {scratch[1]} {scratch[1]}")
                    if self.debug_flag:
                        tran.writeAction(f"sri X0 X16 6")
                        tran.writeAction(f"sri X1 X17 32")
                        tran.writeAction(f"print 'Send remote ud %u %lu-th claimed dram key to lane %lu at dram %lu' {'X16'} {entry_ind} {'X17'} {scratch[1]}")
                    tran.writeAction(f"jmp receiver_claim_work_end")
                else:
                    tran.writeAction(f"beq {scratch[0]} {scratch[1]} local_work_resolved")

                # Update inter_key_resolved_count
                tran.writeAction(f"claim_local_cache: addi {scratch[0]} {scratch[0]} {1}")
                tran.writeAction(f"movrl {scratch[0]} 0({addr}) 0 {WORD_SIZE}")
                tran.writeAction(f"subi {scratch[0]} {scratch[0]} {1}")

                # Get the kv ptr
                tran.writeAction(f"muli {scratch[0]} {scratch[0]} {WORD_SIZE * self.intermediate_cache_entry_size}")
                tran.writeAction(f"movir {addr} {self.intermediate_cache_offset}")
                tran.writeAction(f"add {'X7'} {addr} {addr}")
                tran.writeAction(f"add {addr} {scratch[0]} {addr}")

                # Send the entry
                if self.do_all_reduce:
                    tran.writeAction(f"addi {'X1'} {ev_word} {0}")
                    tran.writeAction(f"evlb {ev_word} {self.ln_worker_claimed_reduce_ev_label}")
                    tran.writeAction(f"evii {cont_word} {self.ln_receiver_acknowledge_key_executed_ev_label} {255} {5}")
                    tran.writeAction(f"send_wcont {ev_word} {cont_word} {addr} {self.inter_kvpair_size}")
                    if self.debug_flag:
                        tran.writeAction(f"movlr 0({addr}) {part_end} 0 {WORD_SIZE}")
                        tran.writeAction(f"sri {'X1'} {scratch[0]} {32}")
                        tran.writeAction(f"print 'Remote Lane %d claimed %ld-th key %lu from lane %d at %lu' {scratch[0]} {entry_ind} {part_end} X0 {addr}")
                    tran.writeAction(f"movir {self.scratch[1]} {-1}")
                    tran.writeAction(f"movrl {self.scratch[1]} 0({addr}) 0 {WORD_SIZE}")
                    tran.writeAction(f"jmp receiver_claim_work_end")
                else:
                    tran.writeAction(f"movlr {WORD_SIZE}({addr}) {dest} 0 {WORD_SIZE}")
                    tran.writeAction(f"movlr {WORD_SIZE * 2}({addr}) {num} 0 {WORD_SIZE}")
                    tran.writeAction(f"movir {scratch[0]} {self._reduce_flag}")
                    tran.writeAction(f"addi {'X1'} {ev_word} {0}")
                    tran.writeAction(f"evlb {ev_word} {self.ln_worker_claimed_reduce_ev_label}")
                    tran.writeAction(f"evii {cont_word} {self.ln_receiver_acknowledge_key_executed_ev_label} {255} {5}")
                    tran.writeAction(f"sendr3_wcont {ev_word} {cont_word} {scratch[0]} {dest} {num}")


                    # Update claimed bit in key
                    tran.writeAction(f"movlr 0({addr}) {scratch[0]} 0 {WORD_SIZE}")
                    tran.writeAction(f"ori {scratch[0]} {scratch[0]} {1}")
                    # Update claimed event word
                    tran.writeAction(f"evi {'X1'} {ev_word} {255} {0b0100}")
                    tran.writeAction(f"evlb {ev_word} {self.kv_reduce_init_ev_label}")
                    tran.writeAction(f"movrl {ev_word} {WORD_SIZE}({addr}) 0 {WORD_SIZE}")
                    tran.writeAction(f"movrl {scratch[0]} 0({addr}) 0 {WORD_SIZE}")
            if self.debug_flag:
                if self.grlb_type == 'lane':
                    tran.writeAction(f"sri {scratch[0]} {scratch[1]} {1}")
                    tran.writeAction(f"sri {'X1'} {ev_word} {32}")
                    tran.writeAction(f"sub {addr} X7 {scratch[0]}")
                    tran.writeAction(f"subi {scratch[0]} {scratch[0]} {self.intermediate_cache_offset}")
                    tran.writeAction(f"divi {scratch[0]} {scratch[0]} {self.intermediate_cache_entry_size * WORD_SIZE}")
                    tran.writeAction(f"print 'Remote Lane %d claimed %ld-th key %lu from lane %d with dram address %lu(0x%lx) and number %d' {ev_word} {scratch[0]} {scratch[1]} X0 {dest} {dest} {num}")
                elif self.grlb_type == 'ud':
                    tran.writeAction(f"sri {scratch[0]} {scratch[1]} {1}")
                    tran.writeAction(f"sri {'X1'} {ev_word} {32}")
                    tran.writeAction(f"print 'Remote Lane %d claimed %ld-th key %lu from lane %d with dram address %lu(0x%lx) and number %d' {ev_word} {entry_ind} {scratch[1]} X0 {dest} {dest} {num}")
            
            tran.writeAction(f"yieldt")

        tran.writeAction(f"local_work_resolved: movir {scratch[0]} {self._no_work_to_be_claimed_flag}")
        if self.debug_flag:
            tran.writeAction(f"perflog 1 0 'End claiming remote'")

        if self.jump_claiming_dest:
            if 'reducer' in self.lb_type and self.grlb_type == 'lane':
                tran.writeAction(f"movir {addr} {self.jump_claiming_dest_offset}")
                tran.writeAction(f"add {'X7'} {addr} {addr}")
                tran.writeAction(f"movlr 0({addr}) {scratch[0]} 0 {WORD_SIZE}")
                tran.writeAction(f"addi X0 {scratch[1]} 0")
            else:
                tran.writeAction(f"andi {'X0'} {scratch[0]} {63}")
                tran.writeAction(f"sli {scratch[0]} {scratch[0]} {int(log2(SPD_BANK_SIZE))}")
                tran.writeAction(f"sub {'X7'} {scratch[0]} {base_addr}")
                tran.writeAction(f"movir {addr} {self.jump_claiming_dest_offset}")
                tran.writeAction(f"add {base_addr} {addr} {addr}")
                tran.writeAction(f"movlr 0({addr}) {scratch[0]} 0 {WORD_SIZE}")
                tran.writeAction(f"sri X0 {scratch[1]} {6}")

        # tran.writeAction(f"sri X1 {scratch[0]} 32")
        # tran.writeAction(f"print 'no work left, return to Lane %lu claim remote' {scratch[0]}")
        tran.writeAction(f"sendr_wcont X1 X2 {scratch[0]} {scratch[1]}")
        tran.writeAction(f"receiver_claim_work_end: yieldt")

        return

    def __gen_receiver_check_materialized_count(self, tran):
        '''
        Event: returned from claimed dest, check materialized count
        Operands:
                    X8:     Spd ptr to entry                   
                    X9:     Dram Pointer to kv array
                    X10:    Previously claimed count
        '''

        # tran.writeAction(f"movlr {WORD_SIZE}({'X8'}) {self.scratch[0]} 0 {WORD_SIZE}")
        tran.writeAction(f"movlr {WORD_SIZE * 2}({'X8'}) {self.scratch[1]} 0 {WORD_SIZE}")
        tran.writeAction(f"bgei {self.scratch[1]} {0} calibrate_for_extra_kv")
        tran.writeAction(f"movir {self.scratch[1]} {0}")
        tran.writeAction(f"calibrate_for_extra_kv: sub {self.scratch[1]} X10 {self.scratch[1]}")
        tran.writeAction(f"muli X10 {self.scratch[0]} {self.inter_kvpair_size * WORD_SIZE}")
        tran.writeAction(f"add X9 {self.scratch[0]} {self.scratch[0]}")

        if self.debug_flag:
            tran.writeAction(f"movlr 0(X8) X16 0 8")
            tran.writeAction(f"print 'Lane %u check materialized count for key %ld as %ld' X0 X16 {self.scratch[1]}")
            tran.writeAction(f"sendr3_wcont {'X1'} {'X2'} {self.scratch[0]} {self.scratch[1]} {'X16'}")
        else:
            tran.writeAction(f"sendr_wcont {'X1'} {'X2'} {self.scratch[0]} {self.scratch[1]}")
        tran.writeAction(f"yieldt")

        return

    def __gen_receiver_set_terminate_bit(self, tran):
        '''
        Event: Broadcasted from global master, indicating all works been finished
            To set the terminate bit to 1

        Operands:   X8: Terminate bit to be set
        '''


        addr = "UDPR_7"                             # UDPR_7                            local reg
        dest = "UDPR_8"                             # UDPR_8                            local reg
        scratch = self.scratch                      # UDPR_12, UDPR_13                  local reg
        ev_word = self.ev_word                      # UDPR_14                           local reg

        if self.debug_flag:
            tran.writeAction(f"print 'Lane %u setting terminate bit to %ld' X0 X8")
        tran.writeAction(f"movir {addr} {self.terminate_bit_offset}")
        tran.writeAction(f"add {'X7'} {addr} {addr}")
        tran.writeAction(f"movrl {'X8'} 0({addr}) 0 {WORD_SIZE}")
        tran.writeAction(f"bnei {'X8'} 1 terminate")
        tran.writeAction(f"sendr_reply {scratch[0]} {scratch[0]} {scratch[0]}")
        tran.writeAction(f"terminate: yieldt")

        return

    def __gen_receiver_acknowledge_key_executed(self, tran):
        '''
        Event: Sent from lane that once claimed a local key
                indicating all materialized kvs of that key have been executed
                X8: acknowledged key count

               Update inter_key_executed_count
               And return to lane master if all local keys have been executed 

        '''

        addr = "UDPR_7"                             # UDPR_7                            local reg
        dest = "UDPR_8"                             # UDPR_8                            local reg
        scratch = self.scratch                      # UDPR_12, UDPR_13                  local reg
        ev_word = self.ev_word                      # UDPR_14                           local reg

        if self.grlb_type == 'ud':
            base_addr = "X17"
            cswp_ret = "X18"
            tmp = "X19"

            # Get Lane 0 spd start address
            tran.writeAction(f"andi {'X0'} {self.scratch[0]} {63}")
            tran.writeAction(f"sli {self.scratch[0]} {self.scratch[0]} {int(log2(SPD_BANK_SIZE))}")
            tran.writeAction(f"sub {'X7'} {self.scratch[0]} {base_addr}")

            # Get count entry address
            tran.writeAction(f"movir {addr} {self.inter_key_executed_count_offset}")
            tran.writeAction(f"add {base_addr} {addr} {addr}")

            # Atomic update key executed count
            tran.writeAction(f"update_key_exe_count: movlr 0({addr}) {self.scratch[0]} 0 {WORD_SIZE}")
            if self.claim_multiple_work:
                tran.writeAction(f"add {self.scratch[0]} {'X8'} {self.scratch[1]}")
            else:
                tran.writeAction(f"addi {self.scratch[0]} {self.scratch[1]} {1}")
            tran.writeAction(f"cswp {addr} {cswp_ret} {self.scratch[0]} {self.scratch[1]}")
            tran.writeAction(f"bne {cswp_ret} {self.scratch[0]} update_key_exe_count")
            if self.debug_flag:
                tran.writeAction(f"sri {'X1'} {ev_word} {32}")
                tran.writeAction(f"print 'Lane %d acknowledged key executed by remote worker, increment from %d to %d, at %lu' {ev_word} {scratch[0]} {scratch[1]} {addr}")

        elif self.grlb_type == 'lane':

            tran.writeAction(f"movir {addr} {self.inter_key_executed_count_offset}")
            tran.writeAction(f"add {'X7'} {addr} {addr}")
            tran.writeAction(f"movlr 0({addr}) {scratch[1]} 0 {WORD_SIZE}")
            tran.writeAction(f"addi {scratch[1]} {scratch[0]} {1}")
            tran.writeAction(f"movrl {scratch[0]} 0({addr}) 0 {WORD_SIZE}")
            if self.debug_flag:
                tran.writeAction(f"sri {'X1'} {addr} {32}")
                tran.writeAction(f"print 'Lane %d acknowledged key executed by remote worker, increment from %d to %d' {addr} {scratch[1]} {scratch[0]}")

        tran.writeAction(f"yieldt")


        return

    def __gen_receiver_set_terminate_bit_ret(self, tran):
        tran.writeAction(f"yieldt")
        return


    def __gen_receiver_receive_kv_do_all_reduce(self, tran):
        '''
        Event:  returned from kv_emit, cache kv before claiming
        Operands:   X8-n  intermediate kv pair
        '''

        num = "UDPR_0"                    # UDPR_0                            local reg
        cswp_ret = "UDPR_1"                         # UDPR_1                            local reg
        entry_addr = "UDPR_2"
        cache_count = "UDPR_3"                      # UDPR_3                            local reg
        base_addr = "UDPR_4"                        # UDPR_4                            local reg
        receive_addr = "UDPR_5"
        resolved_addr = "UDPR_6"
        addr = "UDPR_7"                             # UDPR_7                            local reg



        scratch = self.scratch                      # [UDPR_12, UDPR_13]                local reg
        ev_word = self.ev_word                      # UDPR_14                           local reg
        tmp = "UDPR_15"


        if self.debug_flag:
            tran.writeAction(f"print '[LB_DEBUG] Lane %u receives key %ld value [%lu,%lu]' X0 X8 X9 X10")
        if self.log_kv_latency:
            tran.writeAction(f"perflog 1 0 '%lu receive_kv start' X8")

        if self.grlb_type == 'lane':
            # Prepare to check if intermediate_cache is full
            tran.writeAction(f"movir {tmp} {self.intermediate_cache_count}")
            tran.writeAction(f"movir {receive_addr} {self.inter_key_received_count_offset}")
            tran.writeAction(f"add {'X7'} {receive_addr} {receive_addr}")
            tran.writeAction(f"movir {resolved_addr} {self.inter_key_resolved_count_offset}")
            tran.writeAction(f"add {'X7'} {resolved_addr} {resolved_addr}")

            # Start cswp routine from reading received and resolved counts
            tran.writeAction(f"update_inter_key_count: movlr 0({receive_addr}) {num} 0 {WORD_SIZE}")
            tran.writeAction(f"movlr 0({resolved_addr}) {scratch[0]} 0 {WORD_SIZE}")
            tran.writeAction(f"sub {num} {scratch[0]} {cache_count}")
            tran.writeAction(f"bge {cache_count} {tmp} intermediate_cache_full")

            # If not full, grab the tail entry
            # Occupy tail of intermediate_cache: Atomic update inter_key_received_count
            tran.writeAction(f"addi {num} {scratch[1]} {1}")
            tran.writeAction(f"cswp {receive_addr} {cswp_ret} {num} {scratch[1]}")
            tran.writeAction(f"bne {cswp_ret} {num} update_inter_key_count")
            if self.debug_flag:
                tran.writeAction(f"print 'receive_kv increase lane %u received_count from %lu to %lu' {'X0'} {num} {scratch[1]}")

            # After occupying the tail, calculate entry address
            tran.writeAction(f"movir {scratch[0]} {self.intermediate_cache_offset}")
            tran.writeAction(f"add {scratch[0]} {'X7'} {scratch[1]}")
            tran.writeAction(f"modi {num} {scratch[0]} {self.intermediate_cache_count}")
            tran.writeAction(f"muli {scratch[0]} {scratch[0]} {(self.intermediate_cache_entry_size)*WORD_SIZE}")
            tran.writeAction(f"add {scratch[0]} {scratch[1]} {entry_addr}")

            # Cache intermediate kv
            if self.debug_flag:
                tran.writeAction(f"print 'Check index %lu addr %lu if being read...' {num} {entry_addr}")
            tran.writeAction(f"check_if_being_read: movlr 0({entry_addr}) {scratch[0]} 0 {WORD_SIZE}")
            tran.writeAction(f"bnei {scratch[0]} {-1} check_if_being_read")

            tran.writeAction(f"addi {entry_addr} {scratch[0]} {WORD_SIZE}")
            tran.writeAction(f"bcpyoli X9 {scratch[0]} {self.inter_kvpair_size-1}")
            tran.writeAction(f"movrl X8 0({entry_addr}) 0 {WORD_SIZE}")
            if self.debug_flag:
                tran.writeAction(f"print 'receives_kv writes lane %u %lu-th key %lu at %lu' {'X0'} {num} X8 {entry_addr}")

            tran.writeAction(f"yieldt")

            if self.do_all_reduce_with_materialize:
                intermediate_ptr = "UDPR_0"
                materializing_start = "UDPR_2"
                materializing_end = "UDPR_3"
                materializing_metadata_addr = "UDPR_5"
                ### If full, materialize the kv

                # Check if intermediate dram full
                tran.writeAction(f"intermediate_cache_full: movir {materializing_metadata_addr} {self.materializing_metadata_offset + WORD_SIZE}")
                if self.debug_flag:
                    tran.writeAction(f"print 'intermediate cache full'")
                tran.writeAction(f"add {'X7'} {materializing_metadata_addr} {materializing_metadata_addr}")
                if (self.materialize_kv_dram_size & (self.materialize_kv_dram_size-1)) == 0:
                    tran.writeAction(f"movir {scratch[1]} {1}")
                    tran.writeAction(f"sli {scratch[1]} {scratch[1]} {int(log2(self.materialize_kv_dram_size))}")
                else:
                    tran.writeAction(f"movir {scratch[1]} {self.materialize_kv_dram_size}")

                tran.writeAction(f"movlr -{WORD_SIZE}({materializing_metadata_addr}) {materializing_start} 0 {WORD_SIZE}")
                tran.writeAction(f"movlr 0({materializing_metadata_addr}) {materializing_end} 0 {WORD_SIZE}")

                tran.writeAction(f"update_materialize_key_count: movlr -{WORD_SIZE}({materializing_metadata_addr}) {materializing_start} 0 {WORD_SIZE}")
                tran.writeAction(f"movlr 0({materializing_metadata_addr}) {materializing_end} 0 {WORD_SIZE}")
                tran.writeAction(f"sub {materializing_end} {materializing_start} {scratch[0]}")
                tran.writeAction(f"bge {scratch[0]} {scratch[1]} intermediate_dram_full")

                # If not full, grab the tail entry
                # Occupy tail of intermediate_cache: Atomic update inter_key_received_count
                tran.writeAction(f"addi {materializing_end} {scratch[0]} {1}")
                tran.writeAction(f"cswp {materializing_metadata_addr} {cswp_ret} {materializing_end} {scratch[0]}")
                tran.writeAction(f"bne {cswp_ret} {materializing_end} update_materialize_key_count")
                

                # Calculate address
                tran.writeAction(f"movir {addr} {self.intermediate_ptr_offset}")
                tran.writeAction(f"add {'X7'} {addr} {addr}")
                tran.writeAction(f"movlr 0({addr}) {intermediate_ptr} 0 {WORD_SIZE}")
                if (self.materialize_kv_dram_size & (self.materialize_kv_dram_size-1)) == 0:
                    tran.writeAction(f"movir {scratch[1]} {1}")
                    tran.writeAction(f"sli {scratch[1]} {scratch[1]} {int(log2(self.materialize_kv_dram_size))}")
                else:
                    tran.writeAction(f"movir {scratch[1]} {self.materialize_kv_dram_size}")
                tran.writeAction(f"mod {materializing_end} {scratch[1]} {scratch[1]}")
                tran.writeAction(f"muli {scratch[1]} {scratch[0]} {self.inter_kvpair_size * WORD_SIZE}")
                tran.writeAction(f"add {intermediate_ptr} {scratch[0]} {intermediate_ptr}")
                tran.writeAction(f"evii {scratch[1]} {self.ln_receiver_materialize_ret_ev_label} 255 5")
                tran.writeAction(f"movir {scratch[0]} {self.send_buffer_offset}")
                tran.writeAction(f"add X7 {scratch[0]} {scratch[0]}")
                for i in range(self.inter_kvpair_size):
                    tran.writeAction(f"movrl X{8+i} {i*WORD_SIZE}({scratch[0]}) 0 {WORD_SIZE}")
                tran.writeAction(f"send_dmlm {intermediate_ptr} {scratch[1]} {scratch[0]} {self.inter_kvpair_size}")
                # tran.writeAction(f"sendmops {intermediate_ptr} {scratch[1]} {'X8'} {self.inter_kvpair_size} {1}")
                if self.debug_flag:
                    tran.writeAction(f"print 'receives_kv sends lane %u %lu-th key %lu to dram %lu' {'X0'} {materializing_end} X8 {intermediate_ptr}")

                tran.writeAction(f"yieldt")

                # If full, spin lock
                tran.writeAction(f"intermediate_dram_full: evi X2 {ev_word} {255} {0b0100}")
                tran.writeAction(f"sendops_wcont {ev_word} X1 X8 {self.inter_kvpair_size}")

            else:
                # If full, spin lock
                tran.writeAction(f"intermediate_cache_full: evi X2 {ev_word} {255} {0b0100}")
                tran.writeAction(f"sendops_wcont {ev_word} X1 X8 {self.inter_kvpair_size}")

            if self.debug_flag:
                tran.writeAction(f"print 'intermediate_dram_full'")
            tran.writeAction(f"yieldt")




        if self.grlb_type == 'ud':
            # Get Lane 0 spd start address
            tran.writeAction(f"andi {'X0'} {scratch[0]} {63}")
            tran.writeAction(f"sli {scratch[0]} {scratch[0]} {int(log2(SPD_BANK_SIZE))}")
            tran.writeAction(f"sub {'X7'} {scratch[0]} {base_addr}")

            # Prepare to check if intermediate_cache is full
            tran.writeAction(f"movir {tmp} {self.intermediate_cache_count * LANE_PER_UD}")
            tran.writeAction(f"movir {receive_addr} {self.inter_key_received_count_offset}")
            tran.writeAction(f"add {base_addr} {receive_addr} {receive_addr}")
            tran.writeAction(f"movir {resolved_addr} {self.inter_key_resolved_count_offset}")
            tran.writeAction(f"add {base_addr} {resolved_addr} {resolved_addr}")

            # Start cswp routine from reading received and resolved counts
            tran.writeAction(f"update_inter_key_count: movlr 0({receive_addr}) {num} 0 {WORD_SIZE}")
            tran.writeAction(f"movlr 0({resolved_addr}) {scratch[0]} 0 {WORD_SIZE}")
            tran.writeAction(f"sub {num} {scratch[0]} {cache_count}")
            tran.writeAction(f"bge {cache_count} {tmp} intermediate_cache_full")

            # If not full, grab the tail entry
            # Occupy tail of intermediate_cache: Atomic update inter_key_received_count
            tran.writeAction(f"addi {num} {scratch[1]} {1}")
            tran.writeAction(f"cswp {receive_addr} {cswp_ret} {num} {scratch[1]}")
            tran.writeAction(f"bne {cswp_ret} {num} update_inter_key_count")
            if self.debug_flag:
                tran.writeAction(f"sri {'X0'} {scratch[0]} {6}")
                tran.writeAction(f"print 'receive_kv increase ud %u received_count from %lu to %lu' {scratch[0]} {num} {scratch[1]}")

            # After occupying the tail, calculate entry address
            tran.writeAction(f"divi {num} {scratch[1]} {self.intermediate_cache_count}")
            tran.writeAction(f"modi {scratch[1]} {scratch[1]} {LANE_PER_UD}")
            tran.writeAction(f"sli {scratch[1]} {scratch[1]} {int(log2(SPD_BANK_SIZE))}")
            tran.writeAction(f"add {base_addr} {scratch[1]} {scratch[1]}")
            tran.writeAction(f"movir {scratch[0]} {self.intermediate_cache_offset}")
            tran.writeAction(f"add {scratch[0]} {scratch[1]} {scratch[1]}")
            tran.writeAction(f"modi {num} {scratch[0]} {self.intermediate_cache_count}")
            tran.writeAction(f"muli {scratch[0]} {scratch[0]} {(self.intermediate_cache_entry_size)*WORD_SIZE}")
            tran.writeAction(f"add {scratch[0]} {scratch[1]} {entry_addr}")

            # Cache intermediate kv
            if self.debug_flag:
                tran.writeAction(f"print 'Check index %lu addr %lu if being read...' {num} {entry_addr}")
            tran.writeAction(f"check_if_being_read: movlr 0({entry_addr}) {scratch[0]} 0 {WORD_SIZE}")
            tran.writeAction(f"bnei {scratch[0]} {-1} check_if_being_read")

            tran.writeAction(f"addi {entry_addr} {scratch[0]} {WORD_SIZE}")
            tran.writeAction(f"bcpyoli X9 {scratch[0]} {self.inter_kvpair_size-1}")
            tran.writeAction(f"movrl X8 0({entry_addr}) 0 {WORD_SIZE}")
            if self.debug_flag:
                tran.writeAction(f"sri X0 {scratch[0]} {6}")
                tran.writeAction(f"print 'receives_kv writes ud %u %lu-th key %lu at %lu' {scratch[0]} {num} X8 {entry_addr}")

            tran.writeAction(f"yieldt")


            if self.do_all_reduce_with_materialize:
                intermediate_ptr = "UDPR_0"
                materializing_start = "UDPR_2"
                materializing_end = "UDPR_3"
                materializing_metadata_addr = "UDPR_5"
                ### If full, materialize the kv

                # Check if intermediate dram full
                tran.writeAction(f"intermediate_cache_full: movir {materializing_metadata_addr} {self.materializing_metadata_offset + WORD_SIZE}")
                if self.debug_flag:
                    tran.writeAction(f"print 'intermediate cache full'")
                tran.writeAction(f"add {base_addr} {materializing_metadata_addr} {materializing_metadata_addr}")
                if (self.materialize_kv_dram_size & (self.materialize_kv_dram_size-1)) == 0:
                    tran.writeAction(f"movir {scratch[1]} {1}")
                    tran.writeAction(f"sli {scratch[1]} {scratch[1]} {int(log2(self.materialize_kv_dram_size))}")
                else:
                    tran.writeAction(f"movir {scratch[1]} {self.materialize_kv_dram_size}")
                tran.writeAction(f"update_materialize_key_count: movlr -{WORD_SIZE}({materializing_metadata_addr}) {materializing_start} 0 {WORD_SIZE}")
                tran.writeAction(f"movlr 0({materializing_metadata_addr}) {materializing_end} 0 {WORD_SIZE}")
                tran.writeAction(f"sub {materializing_end} {materializing_start} {scratch[0]}")
                tran.writeAction(f"bge {scratch[0]} {scratch[1]} intermediate_dram_full")

                # If not full, grab the tail entry
                # Occupy tail of intermediate_cache: Atomic update inter_key_received_count
                tran.writeAction(f"addi {materializing_end} {scratch[0]} {1}")
                tran.writeAction(f"cswp {materializing_metadata_addr} {cswp_ret} {materializing_end} {scratch[0]}")
                tran.writeAction(f"bne {cswp_ret} {materializing_end} update_materialize_key_count")
                

                # Calculate address
                tran.writeAction(f"movir {addr} {self.intermediate_ptr_offset}")
                tran.writeAction(f"add {base_addr} {addr} {addr}")
                tran.writeAction(f"movlr 0({addr}) {intermediate_ptr} 0 {WORD_SIZE}")
                if (self.materialize_kv_dram_size & (self.materialize_kv_dram_size-1)) == 0:
                    tran.writeAction(f"movir {scratch[1]} {1}")
                    tran.writeAction(f"sli {scratch[1]} {scratch[1]} {int(log2(self.materialize_kv_dram_size))}")
                else:
                    tran.writeAction(f"movir {scratch[1]} {self.materialize_kv_dram_size}")
                tran.writeAction(f"mod {materializing_end} {scratch[1]} {scratch[1]}")
                tran.writeAction(f"muli {scratch[1]} {scratch[0]} {self.inter_kvpair_size * WORD_SIZE}")
                tran.writeAction(f"add {intermediate_ptr} {scratch[0]} {intermediate_ptr}")
                tran.writeAction(f"evii {scratch[1]} {self.ln_receiver_materialize_ret_ev_label} 255 5")
                tran.writeAction(f"movir {scratch[0]} {self.send_buffer_offset}")
                tran.writeAction(f"add X7 {scratch[0]} {scratch[0]}")
                for i in range(self.inter_kvpair_size):
                    tran.writeAction(f"movrl X{8+i} {i*WORD_SIZE}({scratch[0]}) 0 {WORD_SIZE}")
                tran.writeAction(f"send_dmlm {intermediate_ptr} {scratch[1]} {scratch[0]} {self.inter_kvpair_size}")
                # tran.writeAction(f"sendmops {intermediate_ptr} {scratch[1]} {'X8'} {self.inter_kvpair_size} {1}")
                if self.debug_flag:
                    tran.writeAction(f"sri X0 {scratch[1]} {6}")
                    tran.writeAction(f"print 'receives_kv sends ud %u %lu-th key %lu to dram %lu' {scratch[1]} {materializing_end} X8 {intermediate_ptr}")

                tran.writeAction(f"yieldt")


                # If full, spin lock
                tran.writeAction(f"intermediate_dram_full: evi X2 {ev_word} {255} {0b0100}")
                tran.writeAction(f"sendops_wcont {ev_word} X1 X8 {self.inter_kvpair_size}")

            else:
                # If full, spin lock
                tran.writeAction(f"intermediate_cache_full: evi X2 {ev_word} {255} {0b0100}")
                tran.writeAction(f"sendops_wcont {ev_word} X1 X8 {self.inter_kvpair_size}")



            tran.writeAction(f"yieldt")


'''
Template ends here
-----------------------------------------------------------------------
'''
