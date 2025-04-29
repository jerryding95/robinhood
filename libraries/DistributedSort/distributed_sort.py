from linker.EFAProgram import EFAProgram

from libraries.UDMapShuffleReduce.linkable.LinkableKVMapShuffleReduceTPL import UDKeyValueMapShuffleReduceTemplate
from libraries.UDMapShuffleReduce.utils.OneDimArrayKeyValueSet import OneDimKeyValueSet
from libraries.UDMapShuffleReduce.utils.IntermediateKeyValueSet import IntermediateKeyValueSet
from libraries.UDMapShuffleReduce.linkable.LinkableGlobalSync import Broadcast
from libraries.SingleLaneSort.hybrid_single_lane import SingleLaneSort
from Macro import *

'''
Distributed Sort for uniform distribution

Step 1: Initialize the class with:
	1. EFA
	2. Task name

Step 2: Call the '<Task name>::distributed_sort' event with operands and a continuation word to return to:
	1. No. of elements
	2. DRAM address of the elements
	3. number of lanes
	4. Temporary DRAM address for the bins & prefix sums
	5. whether to delete duplicates from the list
	6. max possible value in the list

Step 3: Returns to the continuation word. Operands:
	1. No. of elements (after deduplicating)
	2. DRAM address of the elements (the same as input address)
'''





class TestMapShuffleReduce(UDKeyValueMapShuffleReduceTemplate):
    
    def kv_reduce_loc(self, tran: EFAProgram.Transition, key: str, num_lanes_mask:str, base_lane: str, dest_id: str):
        '''
        User-defined mapping from a key to a reducer lane (id). Default implementation is a hash.
        Can be overwritten by the user and changed to customized mapping.
        Parameter
            tran:       EFAProgram.Transition (codelet) triggered by the map event
            key:        name of the register/operand buffer entry containing the key
            result:     name of the register reserved for storing the destination lane id
        '''
        tran.writeAction(f"add {base_lane} {key} {dest_id}")
    


class DistributedSort:
	def __init__(self, efa: EFAProgram, offset: int = 0, taskname = "distributed_sort_test", debug_flag = False):
		self.efa = efa
		self.taskname = taskname
		self.debug_flag = debug_flag
		
		# offset = 56
		self.BK_SIZE = 256
		self.FACTOR = 100


		self.offset = offset



		# propagated by udkvmsr, but useful across whole program
		self.LIST_COUNTER = self.offset
		self.enable_unique = self.offset + 8
		self.saved_return = self.offset + 16
		self.minus_base_lane = self.offset + 24
		self.mx_value = self.offset + 32


	
		self.SEND_BUFFER_OFFSET = self.offset + 32 + 8
		self.SEND_BUFFER_OFFSET2 = self.SEND_BUFFER_OFFSET + 8 * 8



		# print("BUUFFEFS", self.SEND_BUFFER_OFFSET2)
		# reserve 16 words for msr metadata
		# not useful after udkvmsr

		self.kvmsr_meta_data_offset = self.SEND_BUFFER_OFFSET2 + 8 * 8


		self.input_kv_meta_data_offset = self.kvmsr_meta_data_offset + 16 * 8


		self.SIZE_OFF = self.input_kv_meta_data_offset + 8
		self.BIN_OFF = self.input_kv_meta_data_offset + 16
		self.NUM_LANES_OFFSET = self.input_kv_meta_data_offset + 24


		cur_off = self.kvmsr_meta_data_offset + 32 * 8
		

		# we will only use those after UDKVMSR
		self.NEW_LENGTH = cur_off
		self.SAVE_CONT = cur_off + 8
		self.SAVE_CONT2 = cur_off + 16
		self.LANE_PREFIX_ADDR = cur_off + 24
		self.LIST_POS = cur_off + 32
		self.BK_COUNT = cur_off + 40
		self.BK_PREFIX_ADDR = cur_off + 48
		self.INPUT_ADDR = cur_off + 56

		self.PREFIX_SUM =  cur_off + 64
		self.LIST_ADDR = self.PREFIX_SUM
		self.BK_SUM = cur_off + self.BK_SIZE * 8 + 48

		# print("PREFIX_SUM", self.PREFIX_SUM)
		# print("LIST_ADDR", self.LIST_ADDR)
		# print("BK_PREFIX_ADDR", self.BK_SUM)



	def generate_sort(self):

		udkvsmr_task_name = f"{self.taskname}::sort_udkvmsr"
		# self.taskname = f"{self.taskname}"

		'''
		Initialize the map reduce task. The following parameters are required:
			task_name:      unique identifier for each UDKVMSR program.
			meta_data_offset:   offset of the metadata in bytes. Reserve 16 words on each lane, starting from the offset.
			debug_flag:     enable debug print (optional), default is False
		'''
		testMSR = TestMapShuffleReduce(efa=self.efa, task_name=udkvsmr_task_name, meta_data_offset=self.kvmsr_meta_data_offset, debug_flag=False)
		self.state = testMSR.state
		'''
		Define the input, intermediate and output key value set. 
		Available key value set types:
			OneDimKeyValueSet:          One dimensional array in DRAM, key is implicitly the index of the array, value is the element in the array.
										Init parameters: 
											element_size - size of each element in the array (in words)
											lm_offset    - scratchpad offset (Bytes) storing the base address and size of the array (metadata of the key value set)
			IntermediateKeyValueSet:    Dummy set for intermediate key-value pair emitted by map task.
										Init parameters:
											key_size    - size of the key (in words)
											value_size  - size of the value (in words)
			SHTKeyValueSet:             Scalable hash table. (See example GenSHTMapShuffleReduceEFA.py)
		'''
		#testMSR.set_input_kvset(OneDimKeyValueSet("Test input", element_size=1, lm_offset=self.input_kv_meta_data_offset, metadata_size=4) )
		testMSR.set_input_kvset(OneDimKeyValueSet("Dsort_input", element_size=1, metadata_size=4) )
		testMSR.set_intermediate_kvset(IntermediateKeyValueSet("Dsort_intermediate", key_size=1, value_size=1))
		# testMSR.set_output_kvset(OneDimKeyValueSet("Test input", element_size=1, lm_offset=24, metadata_size=3) )
		

		testMSR.set_max_thread_per_lane(max_map_th_per_lane=10, max_reduce_th_per_lane=20)
		testMSR.generate_udkvmsr_task()
		
		init_kvmsr_broadcast = Broadcast(testMSR.state, f"{self.taskname}::sort_udkvmsr_broadcast", False)
		init_kvmsr_broadcast.gen_broadcast()

		test_sort_sp = SingleLaneSort(testMSR.efa, f'{self.taskname}::distributed_sort_sp', 0, 'X31', False)


		temp_reg    = "UDPR_0"
		lm_base_reg = "UDPR_1"
		send_buffer = "UDPR_2"
		input_meta_data = "UDPR_3"
		send_buffer2 = "UDPR_4"
		tmp_addr = "UDPR_5"
		ev_word_reg = "UDPR_9"
		lane_mask = "UDPR_10"
		cnt = "UDPR_12"
		len_bins = "UDPR_13"
		pre_start = "UDPR_15"
		
		'''
		Entry event transition to be triggered by the top program. Updown program starts from here.
		operands

		X8:  Number of elements in the input kvset (1D array)
		X9:  Pointer to input kvset (64-bit DRAM address)
		X10: Number of lanes
		X11: Temporary DRAM address for the bins & prefix sums
		X12: Whether to delete duplicates from the list
		X13: The maximum possible value in the list (asumming smallest value is 0) 
		'''
		init_tran = testMSR.state.writeTransition("eventCarry", testMSR.state, testMSR.state, f'{self.taskname}::distributed_sort')
		init_tran.writeAction(f"perflog 1 0 'entry of sorting'")
		# init_tran.writeAction(f"print 'extra paremeters: %ld %ld %ld %ld %ld %ld %ld %ld' {'X8'} {'X9'} {'X10'} {'X11'} {'X12'} {'X13'} {'X14'} {'X15'}")
		# Move the UDKVMSR call parameters to scratchpad.
		if self.debug_flag:
			init_tran.writeAction(f"print '[DEBUG][NWID %d] Event <init_tran> ' {'X0'} ")
		init_tran.writeAction(f"movir {send_buffer} {self.SEND_BUFFER_OFFSET}")
		init_tran.writeAction(f"add {'X7'} {send_buffer} {send_buffer}")



		# init_tran.writeAction(f"movrl {'X13'} 0({send_buffer}) 0 8")
		init_tran.writeAction(f"muli {'X8'} {len_bins} {8 * self.FACTOR}")
		
		init_tran.writeAction(f"add {len_bins} {'X11'} {pre_start}")
		init_tran.writeAction(f"movrl {pre_start} 0({send_buffer}) 0 8")
		init_tran.writeAction(f"mov_imm2reg {cnt} 1")
		init_tran.writeAction(f"movrl {cnt} 8({send_buffer}) 0 8")
		init_tran.writeAction(f"movrl {'X10'} 16({send_buffer}) 0 8")
		init_tran.writeAction(f"addi {'X7'} {lm_base_reg} 0")
		init_tran.writeAction(f"addi {lm_base_reg} {tmp_addr} {self.INPUT_ADDR}")
		init_tran.writeAction(f"movrl {'X9'} 0({tmp_addr}) 0 8")
		init_tran.writeAction(f"addi {'X7'} {input_meta_data} {self.input_kv_meta_data_offset}")


		init_tran.writeAction(f"movrl {input_meta_data} 24({send_buffer}) 0 8")
		# init_tran.writeAction(f"print '[DEBUG][NWID %d] Save input key value set base pointer %ld(0x%lx) and size %ld to scratchpad addr %ld(0x%lx)' {'X0'} {'X11'} {'X11'} {'X12'} {lm_base_reg} {lm_base_reg}")
		init_tran.writeAction(f"movrl {'X9'} 0({input_meta_data}) 1 8")
		init_tran.writeAction(f"movrl {'X8'} 0({input_meta_data}) 1 8")
		init_tran.writeAction(f"movrl {'X11'} 0({input_meta_data}) 1 8")
		init_tran.writeAction(f"subi {'X10'} {lane_mask} {1}")
		init_tran.writeAction(f"movrl {lane_mask} 0({input_meta_data}) 1 8")
		# init_tran.writeAction(f"print 'putting num_lanes = %ld' {'X10'}")
		


		ev_word_reg = "UDPR_9"
		temp_reg = "UDPR_0"
		lm_base_reg = "UDPR_1"
		tmp_reg = "UDPR_2"
		tran_per_lane_reg = "UDPR_3"
		send_buffer2 = "UDPR_4"
		tmp_addr = "UDPR_12"
		cnt_perlane = "UDPR_13"
		mbaselane = "UDPR_14"
		pre_start = "UDPR_15"

		# nlanes = "UDPR_5"

		# tran_init_step2 = testMSR.state.writeTransition("eventCarry", testMSR.state, testMSR.state, f"{self.taskname}::updown_init_step2")


		if self.debug_flag:
			init_tran.writeAction(f"print '[DEBUG][NWID %d] Event <init_tran2> ' {'X0'} ")

		init_tran.writeAction(f"addi {'X7'} {lm_base_reg} 0")
		init_tran.writeAction(f"addi {'X7'} {send_buffer2} {self.SEND_BUFFER_OFFSET2}")
		init_tran.writeAction(f"addi {'X7'} {tmp_addr} {self.saved_return}")
		init_tran.writeAction(f"movrl {'X1'} 0({tmp_addr}) 0 8")

		# Prepare for global_broadcast event


		init_tran.writeAction(f"mov_imm2reg {ev_word_reg} 0")
		init_tran = set_ev_label(init_tran, ev_word_reg, f'{self.taskname}::sort_udkvmsr_broadcast::broadcast_global', new_thread = True, label="")
		# tran_init_local_sort = set_ev_label(tran_init_local_sort, ev_word_reg, f'{self.taskname}::updown_terminate', new_thread = True, label="")
		# tran_init_local_sort.writeAction(f"addi {tmp_reg} {lm_base_reg} 0")

		# Prepare for per lane arguemnts
		init_tran.writeAction(f"mov_imm2reg {tran_per_lane_reg} 0")
		init_tran.writeAction(f"evlb {tran_per_lane_reg}  {f'{self.taskname}::updown_init_step2_per_lane'} ")
		# tran_init_step2.writeAction(f"movlr {self.NUM_LANES_OFFSET}({lm_base_reg}) {tmp_reg} 0 8")
		init_tran.writeAction(f"addi {'X10'} {tmp_reg} 0")
		# tran_init_step2.writeAction(f"addi {tmp_reg} {tmp_reg} 1")
		init_tran.writeAction(f"movrl {tmp_reg} 0({send_buffer2}) 0 8")
		init_tran.writeAction(f"movrl {tran_per_lane_reg} 8({send_buffer2}) 0 8")
		init_tran.writeAction(f"addi {lm_base_reg} {tmp_addr} {self.INPUT_ADDR}")
		init_tran.writeAction(f"movlr 0({tmp_addr}) {tmp_reg} 0 8")
		init_tran.writeAction(f"movrl {pre_start} 16({send_buffer2}) 0 8")

		# init_tran.writeAction(f"movrl {'X11'} 16({send_buffer2}) 0 8")
		init_tran.writeAction(f"div {'X8'} {'X10'} {cnt_perlane}")
		init_tran.writeAction(f"movrl {cnt_perlane} 24({send_buffer2}) 0 8")
		init_tran.writeAction(f"movrl {'X9'} 32({send_buffer2}) 0 8")
		init_tran.writeAction(f"movrl {'X12'} 40({send_buffer2}) 0 8")
		init_tran.writeAction(f"mov_imm2reg {mbaselane} 0")
		init_tran.writeAction(f"sub {mbaselane} {'X0'} {mbaselane}")
		init_tran.writeAction(f"movrl {mbaselane} 48({send_buffer2}) 0 8")
		init_tran.writeAction(f"movrl {'X13'} 56({send_buffer2}) 0 8")
		


		# Prepare for return event
		# init_tran.writeAction(f"mov_imm2reg {temp_reg} 0")
		init_tran.writeAction(f"addi {'X2'} {temp_reg} 0")

		init_tran.writeAction(f"evlb {temp_reg} {f'{self.taskname}::updown_init_udkvmsr'}")

		# Send out the event
		init_tran.writeAction(f"send_wcont {ev_word_reg} {temp_reg} {send_buffer2} {8} {tmp_reg}")
		init_tran.writeAction(f"yield")



		tmp = "UDPR_0"
		lm_base_reg = "UDPR_1"
		to_addr = "UDPR_2"
		to_val = "UDPR_3"
		lane_idx = "UDPR_4"
		tmp_addr = "UDPR_5"
		

		tran_init_step2_per_lane = testMSR.state.writeTransition("eventCarry", testMSR.state, testMSR.state, f"{self.taskname}::updown_init_step2_per_lane")
		# tran_init_step2_per_lane.writeAction(f"print '[DEBUG][NWID %d] Event <init_tran2> ' {'X0'} ")
		if self.debug_flag:
			tran_init_step2_per_lane.writeAction(f"print '[DEBUG][NWID %d] Event <updown_init_step2_per_lane> ' {'X0'} ")
		tran_init_step2_per_lane.writeAction(f"addi {'X7'} {lm_base_reg} 0")
		tran_init_step2_per_lane.writeAction(f"mov_imm2reg {tmp} 0")
		tran_init_step2_per_lane.writeAction(f"addi {lm_base_reg} {tmp_addr} {self.LIST_COUNTER}")
		tran_init_step2_per_lane.writeAction(f"movrl {tmp} 0({tmp_addr}) 0 8")
		tran_init_step2_per_lane.writeAction(f"addi {lm_base_reg} {tmp_addr} {self.enable_unique}")
		tran_init_step2_per_lane.writeAction(f"movrl {'X11'} 0({tmp_addr}) 0 8")
		tran_init_step2_per_lane.writeAction(f"addi {lm_base_reg} {tmp_addr} {self.minus_base_lane}")
		tran_init_step2_per_lane.writeAction(f"movrl {'X12'} 0({tmp_addr}) 0 8")
		tran_init_step2_per_lane.writeAction(f"addi {lm_base_reg} {tmp_addr} {self.mx_value}")
		tran_init_step2_per_lane.writeAction(f"movrl {'X13'} 0({tmp_addr}) 0 8")

		# tran_init_step2_per_lane.writeAction(f"print 'getting start and cnt: %ld %ld' {'X8'} {'X9'}")
		tran_init_step2_per_lane.writeAction(f"muli {'X9'} {to_val} {8}")
		tran_init_step2_per_lane = self.get_lane_idx(tran_init_step2_per_lane, lane_idx, tmp_addr)
		# tran_init_step2_per_lane.writeAction(f"print 'lane idx: %ld' {lane_idx}")
		tran_init_step2_per_lane.writeAction(f"mul {to_val} {lane_idx} {to_val}")
		tran_init_step2_per_lane.writeAction(f"add {to_val} {'X10'} {to_val}")
		tran_init_step2_per_lane.writeAction(f"muli {lane_idx} {to_addr} {8}")
		tran_init_step2_per_lane.writeAction(f"add {to_addr} {'X8'} {to_addr}")
		tran_init_step2_per_lane.writeAction(f"sendr_dmlm {to_addr} {'X1'} {to_val}")
		tran_init_step2_per_lane.writeAction(f"yield_terminate")
		# tran_init_step2_per_lane.writeAction(f"sendr_reply UDPR_0 UDPR_1 UDPR_2")



		'''
		Send the parameter to UDKVMSR library to start the UDKVMSR program. 
			Operands:
			OB_0: Pointer to the partition array (64-bit DRAM address)
			OB_1: Number of partitions per lane
			OB_2: Number of lanes
			OB_3: Scratchapd addr storing the input kvset metadata (base address and size)
			OB_4: Scratchapd addr storing the output kvset metadata (base address and size)
		'''
		init_tran_udkvmsr = testMSR.state.writeTransition("eventCarry", testMSR.state, testMSR.state, f'{self.taskname}::updown_init_udkvmsr')
		if self.debug_flag:
			init_tran_udkvmsr.writeAction(f"print '[DEBUG][NWID %d] Event <updown_init_udkvmsr> ' {'X0'} ")
		ev_word_reg = "UDPR_9"
		lm_base_reg = "UDPR_1"
		send_buffer = "UDPR_2"
		temp_reg = "UDPR_0"
		
		init_tran_udkvmsr.writeAction(f"addi {'X7'} {lm_base_reg} 0")
		init_tran_udkvmsr.writeAction(f"addi {'X7'} {send_buffer} {self.SEND_BUFFER_OFFSET}")

		init_tran_udkvmsr.writeAction(f"mov_imm2reg {ev_word_reg} 0")
		init_tran_udkvmsr.writeAction(f"ev_update_2 {ev_word_reg} {f'{udkvsmr_task_name}::map_shuffle_reduce'} 255 5")
		init_tran_udkvmsr.writeAction(f"send_wret {ev_word_reg} {f'{self.taskname}::updown_local_sorting'} {send_buffer} 4 {temp_reg}")

		# init_tran_udkvmsr.writeAction(f"mov_imm2reg {temp_reg} 0")
		# init_tran_udkvmsr.writeAction(f"addi {'X7'} {lm_base_reg} 0")
		# init_tran_udkvmsr.writeAction(f"move {temp_reg} {TERM_FLAG_ADDR}({lm_base_reg}) 0 8")
		init_tran_udkvmsr.writeAction("yield")


		# local sort

		ev_word_reg = "UDPR_9"
		temp_reg = "UDPR_0"
		lm_base_reg = "UDPR_1"
		tmp_reg = "UDPR_2"
		tran_per_lane_reg = "UDPR_3"
		send_buffer2 = "UDPR_4"
		tmp_addr = "UDPR_5"
		# nlanes = "UDPR_5"
		
		tran_local_sorting = testMSR.state.writeTransition("eventCarry", testMSR.state, testMSR.state, f"{self.taskname}::updown_local_sorting")
		tran_local_sorting.writeAction(f"perflog 1 0 'finish UDKVMSR, start local sorting'")

		if self.debug_flag:
			tran_local_sorting.writeAction(f"print '[DEBUG][NWID %d] Event <updown_local_sorting> ' {'X0'} ")

		tran_local_sorting.writeAction(f"addi {'X7'} {lm_base_reg} 0")
		tran_local_sorting.writeAction(f"addi {'X7'} {send_buffer2} {self.SEND_BUFFER_OFFSET}")
		
		# Prepare for global_broadcast event

		
		tran_local_sorting.writeAction(f"mov_imm2reg {ev_word_reg} 0")
		tran_local_sorting = set_ev_label(tran_local_sorting, ev_word_reg, f'{self.taskname}::sort_udkvmsr_broadcast::broadcast_global', new_thread = True, label="")
		# tran_init_local_sort = set_ev_label(tran_init_local_sort, ev_word_reg, f'{self.taskname}::updown_terminate', new_thread = True, label="")
		# tran_init_local_sort.writeAction(f"addi {tmp_reg} {lm_base_reg} 0")

		# Prepare for per lane arguemnts
		tran_local_sorting.writeAction(f"mov_imm2reg {tran_per_lane_reg} 0")
		tran_local_sorting.writeAction(f"evlb {tran_per_lane_reg}  {f'{self.taskname}::updown_local_sorting_per_lane'} ")
		tran_local_sorting.writeAction(f"addi {lm_base_reg} {tmp_addr} {self.NUM_LANES_OFFSET}")
		tran_local_sorting.writeAction(f"movlr 0({tmp_addr}) {tmp_reg} 0 8")
		tran_local_sorting.writeAction(f"addi {tmp_reg} {tmp_reg} 1")
		tran_local_sorting.writeAction(f"movrl {tmp_reg} 0({send_buffer2}) 0 8")
		tran_local_sorting.writeAction(f"movrl {tran_per_lane_reg} 8({send_buffer2}) 0 8")
		tran_local_sorting.writeAction(f"addi {lm_base_reg} {tmp_addr} {self.INPUT_ADDR}")
		tran_local_sorting.writeAction(f"movlr 0({tmp_addr}) {tmp_reg} 0 8")
		tran_local_sorting.writeAction(f"movrl {tmp_reg} 16({send_buffer2}) 0 8")

		# tran_local_sorting.writeAction(f"print '[DEBUG][NWID %d] Event <updown_local_sorting> ' {'X0'} ")
		# Prepare for return event
		# tran_local_sorting.writeAction(f"mov_imm2reg {temp_reg} 0")
		tran_local_sorting.writeAction(f"addi {'X2'} {temp_reg} 0")

		tran_local_sorting.writeAction(f"evlb {temp_reg} {f'{self.taskname}::updown_parallel_prefix_sum_step1'}")

		# Send out the event
		tran_local_sorting.writeAction(f"send_wcont {ev_word_reg} {temp_reg} {send_buffer2} {8} {tmp_reg}")
		tran_local_sorting.writeAction(f"yield")

		# local sort per lane
		cur_addr = "UDPR_0"
		cur_sp_addr = "UDPR_1"
		last_num = "UDPR_2"
		lm_base_reg = "UDPR_3"
		nxt_reg = "UDPR_4"
		bin_start_reg = "UDPR_5"

		bin_start = "UDPR_6"
		counter = "UDPR_7"
		len = "UDPR_8"
		nlanes = "UDPR_9"
		has = "UDPR_10"
		tmp_addr = send_buffer2 = "UDPR_11"
		off_addr = "UDPR_12"
		ev_word_reg = "UDPR_13"
		temp_reg = "UDPR_14"
		tmp_reg = "UDPR_15"
		
		tran_local_sorting_per_lane = testMSR.state.writeTransition("eventCarry", testMSR.state, testMSR.state, f"{self.taskname}::updown_local_sorting_per_lane")
		# tran_local_sorting_per_lane.writeAction(f"print '[DEBUG][NWID %d] Event <updown_local_sorting_per_lane> ' {'X0'} ")
		# tran_local_sorting_per_lane = set_ev_label(tran_local_sorting_per_lane, nxt_reg, f'{self.taskname}::updown_local_sort_per_lane_mid', new_thread = False, label="")
		# tran_local_sorting_per_lane = set_ev_label(tran_local_sorting_per_lane, nxt_reg, f'sort::setup', new_thread = False, label="")
		# tran_local_sorting_per_lane.writeAction(f"print 'cont_word now = %lu' {'X1'}")
		# tran_local_sorting_per_lane.writeAction(f"ev {nxt_reg} {nxt_reg} {'X0'} {'X0'} {0b1100}") 
		tran_local_sorting_per_lane.writeAction(f"addi {'X7'} {lm_base_reg} 0")
		tran_local_sorting_per_lane.writeAction(f"addi {lm_base_reg} {tmp_addr} {self.SAVE_CONT2}")
		tran_local_sorting_per_lane.writeAction(f"movrl {'X1'} 0({tmp_addr}) 0 8")
		tran_local_sorting_per_lane.writeAction(f"movir {bin_start_reg} {0}")
		tran_local_sorting_per_lane.writeAction(f"add {'X7'} {bin_start_reg} {bin_start_reg}")
		tran_local_sorting_per_lane.writeAction(f"addi {bin_start_reg} {tmp_addr} {self.BIN_OFF}")
		tran_local_sorting_per_lane.writeAction(f"movlr 0({tmp_addr}) {bin_start} 0 8")
		tran_local_sorting_per_lane.writeAction(f"addi {lm_base_reg} {tmp_addr} {self.LIST_COUNTER}")
		tran_local_sorting_per_lane.writeAction(f"movlr 0({tmp_addr}) {counter} 0 8")
		tran_local_sorting_per_lane.writeAction(f"addi {lm_base_reg} {tmp_addr} {self.SIZE_OFF}")
		tran_local_sorting_per_lane.writeAction(f"movlr 0({tmp_addr}) {len} 0 8")
		tran_local_sorting_per_lane.writeAction(f"addi {lm_base_reg} {tmp_addr} {self.NUM_LANES_OFFSET}")
		tran_local_sorting_per_lane.writeAction(f"movlr 0({tmp_addr}) {nlanes} 0 8")
		tran_local_sorting_per_lane.writeAction(f"addi {nlanes} {nlanes} 1")
		

	
		tran_local_sorting_per_lane.writeAction(f"div {len} {nlanes} {len}")
		
		tran_local_sorting_per_lane = self.get_lane_idx(tran_local_sorting_per_lane, cur_addr, tmp_addr)
		tran_local_sorting_per_lane.writeAction(f"mul {len} {cur_addr} {len}")
		tran_local_sorting_per_lane.writeAction(f"muli {len} {len} {8 * self.FACTOR}")
		tran_local_sorting_per_lane.writeAction(f"add {len} {bin_start} {bin_start}")
		tran_local_sorting_per_lane.writeAction(f"addi {'X7'} {off_addr} {self.LIST_ADDR}")
		tran_local_sorting_per_lane.writeAction(f"sub {off_addr} {bin_start} {off_addr}")
		
		tran_local_sorting_per_lane.writeAction(f"divi {counter} {counter} 8")
		tran_local_sorting_per_lane.writeAction(f"bnei {counter} {0} general_case")
		tran_local_sorting_per_lane.writeAction(f"sendr_reply UDPR_0 UDPR_1 UDPR_2")
		tran_local_sorting_per_lane.writeAction(f"yield")
		tran_local_sorting_per_lane = set_ev_label(tran_local_sorting_per_lane, ev_word_reg, f'{self.taskname}::updown_local_sorting_per_lane_step2', new_thread = False, label="general_case")
		tran_local_sorting_per_lane.writeAction(f"mov_imm2reg {has} 0")
		tran_local_sorting_per_lane.writeAction(f"addi {bin_start} {cur_addr} 0")
		tran_local_sorting_per_lane.writeAction(f"loop_start: beq {has} {counter} loop_end")
		tran_local_sorting_per_lane.writeAction(f"send_dmlm_ld {cur_addr} {ev_word_reg} 1")
		tran_local_sorting_per_lane.writeAction(f"addi {cur_addr} {cur_addr} 8")
		tran_local_sorting_per_lane.writeAction(f"addi {has} {has} 1")
		tran_local_sorting_per_lane.writeAction(f"jmp loop_start")
		# tran_local_sorting_per_lane.writeAction(f"loop_end: print 'yes'")

		# tran_local_sorting_per_lane.writeAction(f"sendr_reply {tmp1} {tmp2} {tmp3}")
		tran_local_sorting_per_lane.writeAction(f"loop_end: yield")


		tran_local_sorting_per_lane_step2 = testMSR.state.writeTransition("eventCarry", testMSR.state, testMSR.state, f"{self.taskname}::updown_local_sorting_per_lane_step2")
		tran_local_sorting_per_lane_step2.writeAction(f"subi {has} {has} 1")
		tran_local_sorting_per_lane_step2.writeAction(f"add {'X9'} {off_addr} {cur_sp_addr}")
		tran_local_sorting_per_lane_step2.writeAction(f"movrl {'X8'} {0}({cur_sp_addr}) 0 8")
		# tran_local_sorting_per_lane_step2.writeAction(f"print 'before sort: arr element at %ld = %ld' {cur_sp_addr} { 'X8'}")
		tran_local_sorting_per_lane_step2.writeAction(f"bnei {has} {0} continue")
		# tran_local_sorting_per_lane_step2.writeAction(f"print 'lane %d, getting all local' {'X0'}")
		
		# tran_local_sorting_per_lane_step2.writeAction(f"mov_imm2reg {tmp3} -42")
		# tran_local_sorting_per_lane_step2.writeAction(f"movrl {tmp3} {self.LIST_ADDR + 8}({lm_base_reg}) 0 8")
		# tran_local_sorting_per_lane_step2.writeAction(f"mov")


		
		tran_local_sorting_per_lane_step2.writeAction(f"addi {'X7'} {lm_base_reg} 0")
		
		# Prepare for global_broadcast event

		
		tran_local_sorting_per_lane_step2.writeAction(f"mov_imm2reg {ev_word_reg} 0")
		tran_local_sorting_per_lane_step2 = set_ev_label(tran_local_sorting_per_lane_step2, ev_word_reg, f'{self.taskname}::distributed_sort_sp::init', new_thread = False, label="")
		# tran_local_sorting_per_lane_step2 = set_ev_label(tran_local_sorting_per_lane_step2, ev_word_reg, f'{self.taskname}::updown_local_sorting_per_lane_step2_pre', new_thread = True, label="")

		tran_local_sorting_per_lane_step2.writeAction(f"mov_imm2reg {temp_reg} 0")
		tran_local_sorting_per_lane_step2 = set_ev_label(tran_local_sorting_per_lane_step2, temp_reg, f'{self.taskname}::updown_local_sorting_per_lane_step3', new_thread = False, label="")
		tran_local_sorting_per_lane_step2.writeAction(f"addi {lm_base_reg} {tmp_addr} {self.SAVE_CONT}")

		tran_local_sorting_per_lane_step2.writeAction(f"movrl {temp_reg} 0({tmp_addr}) 0 8")

		tran_local_sorting_per_lane_step2.writeAction(f"mov_imm2reg {temp_reg} 0")
		tran_local_sorting_per_lane_step2 = set_ev_label(tran_local_sorting_per_lane_step2, temp_reg, f'{self.taskname}::updown_local_sorting_per_lane_step2_pre', new_thread = True, label="")

		# Prepare for per lane arguemnts
		tran_local_sorting_per_lane_step2.writeAction(f"addi {lm_base_reg} {tmp_addr} {self.LIST_COUNTER}")

		tran_local_sorting_per_lane_step2.writeAction(f"movlr 0({tmp_addr}) {tmp_reg} 0 8")
		tran_local_sorting_per_lane_step2.writeAction(f"divi {tmp_reg} {tmp_reg} 8")
		# tran_local_sorting_per_lane_step2.writeAction(f"print 'trying to sort length %ld' {tmp_reg}")
		tran_local_sorting_per_lane_step2.writeAction(f"addi {'X7'} {send_buffer2} {self.SEND_BUFFER_OFFSET}")

		tran_local_sorting_per_lane_step2.writeAction(f"movrl {tmp_reg} 0({send_buffer2}) 0 8")
		tran_local_sorting_per_lane_step2.writeAction(f"addi {'X7'} {tmp_reg} {self.LIST_ADDR}")
		tran_local_sorting_per_lane_step2.writeAction(f"movrl {tmp_reg} 8({send_buffer2}) 0 8")
		# tran_local_sorting_per_lane_step2.writeAction(f"print '[DEBUG][NWID %d] Event <updown_local_sorting_per_lane_step2> ' {'X0'} ")
		# Prepare for return event
		# tran_local_sorting_per_lane_step2.writeAction(f"mov_imm2reg {temp_reg} 0")
		# tran_local_sorting_per_lane_step2.writeAction(f"addi {'X1'} {temp_reg} 0")
		

		# Send out the event
		# tran_local_sorting_per_lane_step2.writeAction(f"sendr_reply {counter} {cur_sp_addr} {tran_per_lane_reg}")

		# tran_local_sorting_per_lane_step2.writeAction(f"mov")
		tran_local_sorting_per_lane_step2.writeAction(f"send_wcont {ev_word_reg} {temp_reg} {send_buffer2} {3} {tmp_reg}")
		tran_local_sorting_per_lane_step2.writeAction(f"movir {temp_reg} 0")
		tran_local_sorting_per_lane_step2.writeAction(f"sri {'X2'} {tmp_reg} 24")
		tran_local_sorting_per_lane_step2.writeAction(f"andi {tmp_reg} {tmp_reg} 255")
		# tran_local_sorting_per_lane_step2.writeAction(f"print 'lane %d, launching local sort, TID: %d' {'X0'} {tmp_reg}")

		tran_local_sorting_per_lane_step2.writeAction(f"yield")

		tran_local_sorting_per_lane_step2.writeAction(f"continue: yield")



		# tran_local_sorting_per_lane_step2_rs = testMSR.state.writeTransition("eventCarry", testMSR.state, testMSR.state, f"{self.taskname}::updown_local_sorting_per_lane_step2_r111s")
		# tran_local_sorting_per_lane_step2_rs.writeAction(f"print 'lane %d, asda return local sort' {'X0'}")

		# tran_local_sorting_per_lane_step2_rs.writeAction(f"print '[DEBUG][NWID %d] Event <updown_local_sorting_per_lane_step2_rs> ' {'X0'} ")
		# tran_local_sorting_per_lane_step2_rs.writeAction(f"sendr_reply UDPR_0 UDPR_1 UDPR_2")
		# tran_local_sorting_per_lane_step2_rs.writeAction(f"yield_terminate")


		tran_local_sorting_per_lane_step2_pre = testMSR.state.writeTransition("eventCarry", testMSR.state, testMSR.state, f"{self.taskname}::updown_local_sorting_per_lane_step2_pre")
		tran_local_sorting_per_lane_step2_pre.writeAction(f"sri {'X2'} {tmp_reg} 24")
		tran_local_sorting_per_lane_step2_pre.writeAction(f"andi {tmp_reg} {tmp_reg} 255")
		# tran_local_sorting_per_lane_step2_pre.writeAction(f"print 'lane %d, getting local sort, TID: %d' {'X0'} {tmp_reg}")

		tran_local_sorting_per_lane_step2_pre = set_ev_label(tran_local_sorting_per_lane_step2_pre, ev_word_reg, f'{self.taskname}::updown_local_sorting_per_lane_step2_dummy', new_thread = True, label="")

		# tran_local_sorting_per_lane_step2_pre.writeAction(f"print '[DEBUG][NWID %d] Event <updown_local_sorting_per_lane_step2_pre> ' {'X0'} ")
		tran_local_sorting_per_lane_step2_pre.writeAction(f"addi {'X7'} {tmp_addr} {self.SAVE_CONT}")
		tran_local_sorting_per_lane_step2_pre.writeAction(f"movlr 0({tmp_addr}) {tmp_reg} 0 8")
		tran_local_sorting_per_lane_step2_pre.writeAction(f"sendr_wcont {ev_word_reg} {tmp_reg} UDPR_0 UDPR_1 UDPR_2")
		tran_local_sorting_per_lane_step2_pre.writeAction(f"yield_terminate")


		tran_local_sorting_per_lane_step2_dummy = testMSR.state.writeTransition("eventCarry", testMSR.state, testMSR.state, f"{self.taskname}::updown_local_sorting_per_lane_step2_dummy")
		# tran_local_sorting_per_lane_step2_dummy.writeAction(f"print '[DEBUG][NWID %d] Event <updown_local_sorting_per_lane_step2_dummy> ' {'X0'} ")
		# tran_local_sorting_per_lane_step2_dummy.writeAction(f"sendr_reply UDPR_0 UDPR_1 UDPR_2")
	# 
		tran_local_sorting_per_lane_step2_dummy.writeAction(f"sendr_reply UDPR_0 UDPR_1 UDPR_2")
		tran_local_sorting_per_lane_step2_dummy.writeAction(f"yield_terminate")


		# plugin sort
		tran_local_sorting_per_lane_step3 = testMSR.state.writeTransition("eventCarry", testMSR.state, testMSR.state, f"{self.taskname}::updown_local_sorting_per_lane_step3")
		tran_local_sorting_per_lane_step3.writeAction(f"sri {'X2'} {tmp_reg} 24")
		tran_local_sorting_per_lane_step3.writeAction(f"andi {tmp_reg} {tmp_reg} 255")
		# tran_local_sorting_per_lane_step3.writeAction(f"print 'lane %d, ending local sort, TID: %d' {'X0'} {tmp_reg}")

		tran_local_sorting_per_lane_step3.writeAction(f"addi {bin_start} {cur_addr} 0")

		tran_local_sorting_per_lane_step3 = set_ev_label(tran_local_sorting_per_lane_step3, ev_word_reg, f'{self.taskname}::updown_local_sorting_per_lane_step4', new_thread = False, label="")
		# tran_local_sorting_per_lane_step3.writeAction(f"print ' [DEBUG][NWID %d]  in tran_local_sorting_per_lane_step3' {'X0'}")

		cur_val = temp_reg
		addr2 = tmp_reg
		tran_local_sorting_per_lane_step3.writeAction(f"addi {lm_base_reg} {tmp_addr} {self.enable_unique}")

		tran_local_sorting_per_lane_step3.writeAction(f"movlr 0({tmp_addr}) {cur_val} 0 8")
		tran_local_sorting_per_lane_step3.writeAction(f"beqi {cur_val} {0} skip_unique")
		
		tran_local_sorting_per_lane_step3.writeAction(f"addi {'X7'} {tmp_addr} {self.LIST_ADDR}")
		tran_local_sorting_per_lane_step3.writeAction(f"movlr 0({tmp_addr}) {last_num} 0 8")
		# tran_local_sorting_per_lane_step3.writeAction(f"print 'adding unique number = %d' {last_num}")

		tran_local_sorting_per_lane_step3.writeAction(f"mov_imm2reg {has} 1")
		tran_local_sorting_per_lane_step3.writeAction(f"addi {'X7'} {addr2} {self.LIST_ADDR + 8}")
		tran_local_sorting_per_lane_step3.writeAction(f"addi {'X7'} {cur_sp_addr} {self.LIST_ADDR + 8}")

		
		tran_local_sorting_per_lane_step3.writeAction(f"clean_start: beq {has} {counter} clean_end")
		tran_local_sorting_per_lane_step3.writeAction(f"movlr {0}({cur_sp_addr}) {cur_val} 0 8")
		tran_local_sorting_per_lane_step3.writeAction(f"beq {last_num} {cur_val} skip_add")
		tran_local_sorting_per_lane_step3.writeAction(f"movrl {cur_val} {0}({addr2}) 1 8")
		tran_local_sorting_per_lane_step3.writeAction(f"addi {cur_val} {last_num} 0")
		# tran_local_sorting_per_lane_step3.writeAction(f"print 'adding unique number = %d' {last_num}")
		tran_local_sorting_per_lane_step3.writeAction(f"skip_add: addi {cur_sp_addr} {cur_sp_addr} 8")
		tran_local_sorting_per_lane_step3.writeAction(f"addi {has} {has} 1")
		tran_local_sorting_per_lane_step3.writeAction(f"jmp clean_start")
		# tran_local_sorting_per_lane_step3.writeAction(f"clean_end: print 'yes'")
		
		tran_local_sorting_per_lane_step3.writeAction(f"clean_end: sub {addr2} {'X7'} {addr2}")
		tran_local_sorting_per_lane_step3.writeAction(f"subi {addr2} {addr2} {self.LIST_ADDR}")
		tran_local_sorting_per_lane_step3.writeAction(f"addi {lm_base_reg} {tmp_addr} {self.LIST_COUNTER}")

		tran_local_sorting_per_lane_step3.writeAction(f"movrl {addr2} 0({tmp_addr}) 0 8")
		# tran_local_sorting_per_lane_step3.writeAction(f"sub {addr2} {'X7'} {addr2}")

		tran_local_sorting_per_lane_step3.writeAction(f"skip_unique: mov_imm2reg {has} 0")
		tran_local_sorting_per_lane_step3.writeAction(f"addi {'X7'} {cur_sp_addr} {self.LIST_ADDR}")
			# tran_local_sorting_per_lane_step4.writeAction(f"print 'lane: %d, current has = %d' {'X0'} {has}")

		tran_local_sorting_per_lane_step3.writeAction(f"loop_start: beq {has} {counter} loop_end")
		# tran_local_sorting_per_lane_step3.writeAction(f"movlr {0}({cur_sp_addr}) {tmp3} 0 8")
		# tran_local_sorting_per_lane_step3.writeAction(f"print 'lane %d, local sort sending %ld to %ld' {'X0'} {tmp3} {cur_addr}")
		tran_local_sorting_per_lane_step3.writeAction(f"send_dmlm {cur_addr} {ev_word_reg} {cur_sp_addr} 1")
		tran_local_sorting_per_lane_step3.writeAction(f"addi {cur_addr} {cur_addr} 8")
		tran_local_sorting_per_lane_step3.writeAction(f"movlr {0}({cur_sp_addr}) {tmp_reg} 0 8")
		# tran_local_sorting_per_lane_step3.writeAction(f"print 'lane %d, local sort sending %ld to %ld' {'X0'} {tmp_reg} {cur_addr}")
		# tran_local_sorting_per_lane_step3.writeAction(f"print 'after sort: arr element at %ld = %ld' {cur_sp_addr} {tmp_reg}")

		tran_local_sorting_per_lane_step3.writeAction(f"addi {cur_sp_addr} {cur_sp_addr} 8")
		tran_local_sorting_per_lane_step3.writeAction(f"addi {has} {has} 1")
		tran_local_sorting_per_lane_step3.writeAction(f"jmp loop_start")
		# tran_local_sorting_per_lane_step3.writeAction(f"loop_end: print 'yes'")
		tran_local_sorting_per_lane_step3.writeAction(f"loop_end: yield")

		tran_local_sorting_per_lane_step4 = testMSR.state.writeTransition("eventCarry", testMSR.state, testMSR.state, f"{self.taskname}::updown_local_sorting_per_lane_step4")
		tran_local_sorting_per_lane_step4.writeAction(f"subi {has} {has} 1")
		tran_local_sorting_per_lane_step4.writeAction(f"add {'X9'} {off_addr} {cur_addr}")
		# tran_local_sorting_per_lane_step4.writeAction(f"print 'lane: %d, current has = %d' {'X0'} {has}")
		tran_local_sorting_per_lane_step4.writeAction(f"bnei {has} {0} continue")
		# tran_local_sorting_per_lane_step4.writeAction(f"print 'lane %d, sending all local' {'X0'}")
		# tran_local_sorting_per_lane_step4.writeAction(f"sendr_reply {counter} {cur_sp_addr} {tran_per_lane_reg}")
		tran_local_sorting_per_lane_step4.writeAction(f"addi {'X7'} {lm_base_reg} 0")
		tran_local_sorting_per_lane_step4.writeAction(f"addi {lm_base_reg} {tmp_addr} {self.SAVE_CONT2}")
		tran_local_sorting_per_lane_step4.writeAction(f"movlr 0({tmp_addr}) {ev_word_reg} 0 8")
		# tran_local_sorting_per_lane_step4.writeAction(f"print 'cont_word now = %lu' {ev_word_reg}")

		tran_local_sorting_per_lane_step4.writeAction(f"movir {tmp_reg} 1")
		tran_local_sorting_per_lane_step4.writeAction(f"sli {tmp_reg} {tmp_reg} 63")
		tran_local_sorting_per_lane_step4.writeAction(f"subi {tmp_reg} {tmp_reg} 1")
		tran_local_sorting_per_lane_step4.writeAction(f"sendr_wcont {ev_word_reg} {tmp_reg} UDPR_0 UDPR_1 UDPR_2")


		tran_local_sorting_per_lane_step4.writeAction(f"yield_terminate")
		# tran_local_sorting_per_lane_step4.writeAction(f"yield")
		# tran_local_sorting_per_lane_step4.writeAction(f"sendr_wret {'X1'} {f'{self.taskname}::updown_dummy'} UDPR_0 UDPR_1 UDPR_2")
		tran_local_sorting_per_lane_step4.writeAction(f"continue: yield")

		
		# Parallel prefix sum

		# Step 1: put the list counter back to dram


		ev_word_reg = "UDPR_9"
		temp_reg = "UDPR_0"
		lm_base_reg = "UDPR_1"
		tmp_reg = "UDPR_2"
		tran_per_lane_reg = "UDPR_3"
		send_buffer2 = "UDPR_4"
		tmp_addr = "UDPR_5"
		# nlanes = "UDPR_5"

		tran_parallel_prefix_sum_step1 = testMSR.state.writeTransition("eventCarry", testMSR.state, testMSR.state, f"{self.taskname}::updown_parallel_prefix_sum_step1")
		if self.debug_flag:
			tran_parallel_prefix_sum_step1.writeAction(f"print '[DEBUG][NWID %d] Event <updown_parallel_prefix_sum> ' {'X0'} ")
		tran_parallel_prefix_sum_step1.writeAction(f"perflog 1 0 'finish local_sorting, start parallel prefix sum'")

		tran_parallel_prefix_sum_step1.writeAction(f"addi {'X7'} {lm_base_reg} 0")
		tran_parallel_prefix_sum_step1.writeAction(f"addi {'X7'} {send_buffer2} {self.SEND_BUFFER_OFFSET}")
		
		# Prepare for global_broadcast event

		
		tran_parallel_prefix_sum_step1.writeAction(f"mov_imm2reg {ev_word_reg} 0")
		tran_parallel_prefix_sum_step1 = set_ev_label(tran_parallel_prefix_sum_step1, ev_word_reg, f'{self.taskname}::sort_udkvmsr_broadcast::broadcast_global', new_thread = True, label="")
		# tran_init_local_sort = set_ev_label(tran_init_local_sort, ev_word_reg, f'{self.taskname}::updown_terminate', new_thread = True, label="")
		# tran_init_local_sort.writeAction(f"addi {tmp_reg} {lm_base_reg} 0")

		# Prepare for per lane arguemnts
		tran_parallel_prefix_sum_step1.writeAction(f"mov_imm2reg {tran_per_lane_reg} 0")
		tran_parallel_prefix_sum_step1.writeAction(f"evlb {tran_per_lane_reg}  {f'{self.taskname}::updown_parallel_prefix_sum_step1_per_lane'} ")
		tran_parallel_prefix_sum_step1.writeAction(f"addi {lm_base_reg} {tmp_addr} {self.NUM_LANES_OFFSET}")
		tran_parallel_prefix_sum_step1.writeAction(f"movlr 0({tmp_addr}) {tmp_reg} 0 8")
		tran_parallel_prefix_sum_step1.writeAction(f"addi {tmp_reg} {tmp_reg} 1")
		tran_parallel_prefix_sum_step1.writeAction(f"movrl {tmp_reg} 0({send_buffer2}) 0 8")
		tran_parallel_prefix_sum_step1.writeAction(f"movrl {tran_per_lane_reg} 8({send_buffer2}) 0 8")
		tran_parallel_prefix_sum_step1.writeAction(f"addi {lm_base_reg} {tmp_addr} {self.INPUT_ADDR}")
		tran_parallel_prefix_sum_step1.writeAction(f"movlr 0({tmp_addr}) {tmp_reg} 0 8")
		# tran_parallel_prefix_sum_step1.writeAction(f"print 'getting input addr = %ld' {tmp_reg}")

		tran_parallel_prefix_sum_step1.writeAction(f"movrl {tmp_reg} 16({send_buffer2}) 0 8")

		if self.debug_flag:
			tran_parallel_prefix_sum_step1.writeAction(f"print '[DEBUG][NWID %d] Event <updown_parallel_prefix_sum_step1> ' {'X0'} ")
		# Prepare for return event
		tran_parallel_prefix_sum_step1.writeAction(f"addi {'X2'} {temp_reg} 0")
		# tran_parallel_prefix_sum_step1.writeAction(f"mov_imm2reg {temp_reg} 0")
		tran_parallel_prefix_sum_step1.writeAction(f"evlb {temp_reg} {f'{self.taskname}::updown_parallel_prefix_sum_step2'}")

		# Send out the event
		tran_parallel_prefix_sum_step1.writeAction(f"send_wcont {ev_word_reg} {temp_reg} {send_buffer2} {8} {tmp_reg}")
		tran_parallel_prefix_sum_step1.writeAction(f"yield")
		# AL_OFF = 40



		tmp1 = "UDPR_0"
		tmp2 = "UDPR_1"
		tmp3 = "UDPR_2"
		bin_start_reg = "UDPR_3"
		len = "UDPR_4"
		bin_start = "UDPR_5"
		to_addr = "UDPR_6"
		counter = "UDPR_7"
		lane_idx = "UDPR_8"
		counter_ptr = "UDPR_9"
		tmp_addr = "UDPR_10"

		tran_parallel_prefix_sum_step1_per_lane = testMSR.state.writeTransition("eventCarry", testMSR.state, testMSR.state, f"{self.taskname}::updown_parallel_prefix_sum_step1_per_lane")
		if self.debug_flag:
			tran_parallel_prefix_sum_step1_per_lane.writeAction(f"print '[DEBUG][NWID %d] Event <updown_parallel_prefix_sum_step1_per_lane> ' {'X0'} ")
		# tran_parallel_prefix_sum_step1_per_lane.writeAction(f"addi {'X7'} {lm_base_reg} 0")
		# tran_parallel_prefix_sum_step1_per_lane.writeAction(f"")
		tran_parallel_prefix_sum_step1_per_lane.writeAction(f"addi {'X7'} {lm_base_reg} 0")

		tran_parallel_prefix_sum_step1_per_lane.writeAction(f"addi {lm_base_reg} {tmp_addr} {self.INPUT_ADDR}")
		tran_parallel_prefix_sum_step1_per_lane.writeAction(f"movrl {'X8'} 0({tmp_addr}) 0 8")
		# tran_parallel_prefix_sum_step1_per_lane.writeAction(f"print 'getting input addr = %ld' {'X8'}")

		# tran_parallel_prefix_sum_step1_per_lane.writeAction(f"movir {bin_start_reg} {0}")
		# tran_parallel_prefix_sum_step1_per_lane.writeAction(f"add {'X7'} {bin_start_reg} {bin_start_reg}")
		tran_parallel_prefix_sum_step1_per_lane.writeAction(f"addi X7 {tmp_addr} {self.BIN_OFF}")

		tran_parallel_prefix_sum_step1_per_lane.writeAction(f"movlr 0({tmp_addr}) {bin_start} 0 8")
		tran_parallel_prefix_sum_step1_per_lane.writeAction(f"addi X7 {tmp_addr} {self.SIZE_OFF}")

		# tran_parallel_prefix_sum_step1_per_lane.writeAction(f"print 'bin_start = %ld' {bin_start}")
		tran_parallel_prefix_sum_step1_per_lane.writeAction(f"movlr 0({tmp_addr}) {len} 0 8")
		# tran_parallel_prefix_sum_step1_per_lane.writeAction(f"print 'csize = %ld' {len}")
		tran_parallel_prefix_sum_step1_per_lane.writeAction(f"muli {len} {len} {8 * self.FACTOR}")
		tran_parallel_prefix_sum_step1_per_lane.writeAction(f"add {len} {bin_start} {bin_start}")
		tran_parallel_prefix_sum_step1_per_lane.writeAction(f"addi {lm_base_reg} {tmp_addr} {self.LANE_PREFIX_ADDR}")
		tran_parallel_prefix_sum_step1_per_lane.writeAction(f"movrl {bin_start} 0({tmp_addr}) 0 8")
		# tran_parallel_prefix_sum_step1_per_lane.writeAction(f"print 'setting self.LANE_PREFIX_ADDR = %ld at lane %d' {bin_start} {'X0'}")
		# tran_parallel_prefix_sum_step1_per_lane.writeAction(f"addi {bin_start} {bin_start} 8")
		tran_parallel_prefix_sum_step1_per_lane = self.get_lane_idx(tran_parallel_prefix_sum_step1_per_lane, lane_idx, tmp_addr)
		tran_parallel_prefix_sum_step1_per_lane.writeAction(f"muli {lane_idx} {lane_idx} 8")
		tran_parallel_prefix_sum_step1_per_lane.writeAction(f"add {bin_start} {lane_idx} {bin_start}")


		tran_parallel_prefix_sum_step1_per_lane.writeAction(f"addi X7 {tmp_addr} {self.LIST_COUNTER}")

		tran_parallel_prefix_sum_step1_per_lane.writeAction(f"movlr 0({tmp_addr}) {counter} 0 8")
		# tran_parallel_prefix_sum_step1_per_lane.writeAction(f"divi {counter} {counter} 8")
		# tran_parallel_prefix_sum_step1_per_lane.writeAction(f"print 'listsize = %ld' {counter}")
		tran_parallel_prefix_sum_step1_per_lane.writeAction(f"addi {'X7'} {counter_ptr} {self.LIST_COUNTER}")
		# tran_parallel_prefix_sum_step1_per_lane.writeAction(f"print 'lane %d sending to bin_start = %ld with %d' {'X0'} {bin_start} {counter}")

		tran_parallel_prefix_sum_step1_per_lane.writeAction(f"send_dmlm {bin_start} {'X1'} {counter_ptr} 1")
		# tran_parallel_prefix_sum_step1_per_lane.writeAction(f"sendr_reply {tmp1} {tmp2} {tmp3}")
		tran_parallel_prefix_sum_step1_per_lane.writeAction(f"yield_terminate")


		# Step 2: each lane load 256 words from DRAM, do prefix sum. 

		ev_word_reg = "UDPR_9"
		temp_reg = "UDPR_0"
		lm_base_reg = "UDPR_1"
		tmp_reg = "UDPR_2"
		tran_per_lane_reg = "UDPR_3"
		send_buffer2 = "UDPR_4"
		tmp_addr = "UDPR_5"
		# nlanes = "UDPR_5"
		

		tran_parallel_prefix_sum_step2 = testMSR.state.writeTransition("eventCarry", testMSR.state, testMSR.state, f"{self.taskname}::updown_parallel_prefix_sum_step2")
		if self.debug_flag:
			tran_parallel_prefix_sum_step2.writeAction(f"print '[DEBUG][NWID %d] Event <updown_parallel_prefix_sum_step2> ' {'X0'} ")

		tran_parallel_prefix_sum_step2.writeAction(f"addi {'X7'} {lm_base_reg} 0")
		tran_parallel_prefix_sum_step2.writeAction(f"addi {'X7'} {send_buffer2} {self.SEND_BUFFER_OFFSET}")
		
		# Prepare for global_broadcast event

		
		tran_parallel_prefix_sum_step2.writeAction(f"mov_imm2reg {ev_word_reg} 0")
		tran_parallel_prefix_sum_step2 = set_ev_label(tran_parallel_prefix_sum_step2, ev_word_reg, f'{self.taskname}::sort_udkvmsr_broadcast::broadcast_global', new_thread = True, label="")
		# tran_init_local_sort = set_ev_label(tran_init_local_sort, ev_word_reg, f'{self.taskname}::updown_terminate', new_thread = True, label="")
		# tran_init_local_sort.writeAction(f"addi {tmp_reg} {lm_base_reg} 0")

		# Prepare for per lane arguemnts
		tran_parallel_prefix_sum_step2.writeAction(f"mov_imm2reg {tran_per_lane_reg} 0")
		tran_parallel_prefix_sum_step2.writeAction(f"evlb {tran_per_lane_reg}  {f'{self.taskname}::updown_parallel_prefix_sum_step2_per_lane'} ")
		tran_parallel_prefix_sum_step2.writeAction(f"addi {lm_base_reg} {tmp_addr} {self.NUM_LANES_OFFSET}")
		tran_parallel_prefix_sum_step2.writeAction(f"movlr 0({tmp_addr}) {tmp_reg} 0 8")
		tran_parallel_prefix_sum_step2.writeAction(f"addi {tmp_reg} {tmp_reg} 1")
		tran_parallel_prefix_sum_step2.writeAction(f"addi {tmp_reg} {tmp_reg} {self.BK_SIZE - 1}")
		tran_parallel_prefix_sum_step2.writeAction(f"divi {tmp_reg} {tmp_reg} {self.BK_SIZE}")
		tran_parallel_prefix_sum_step2.writeAction(f"addi {lm_base_reg} {tmp_addr} {self.BK_COUNT}")

		tran_parallel_prefix_sum_step2.writeAction(f"movrl {tmp_reg} 0({tmp_addr}) 0 8")
		tran_parallel_prefix_sum_step2.writeAction(f"movrl {tmp_reg} 0({send_buffer2}) 0 8")
		tran_parallel_prefix_sum_step2.writeAction(f"movrl {tran_per_lane_reg} 8({send_buffer2}) 0 8")
		tran_parallel_prefix_sum_step2.writeAction(f"movrl {tmp_reg} 16({send_buffer2}) 0 8")
		if self.debug_flag:
			tran_parallel_prefix_sum_step2.writeAction(f"print '[DEBUG][NWID %d] Event <updown_parallel_prefix_sum_step2> ' {'X0'} ")
		# Prepare for return event
		tran_parallel_prefix_sum_step2.writeAction(f"addi {'X2'} {temp_reg} 0")
		# tran_parallel_prefix_sum_step2.writeAction(f"mov_imm2reg {temp_reg} 0")
		
		tran_parallel_prefix_sum_step2.writeAction(f"evlb {temp_reg} {f'{self.taskname}::updown_parallel_prefix_sum_step3'}")

		# Send out the event
		tran_parallel_prefix_sum_step2.writeAction(f"send_wcont {ev_word_reg} {temp_reg} {send_buffer2} {8} {tmp_reg}")
		tran_parallel_prefix_sum_step2.writeAction(f"yield")


		prefix_addr = "UDPR_0"
		cur_val = "UDPR_1"
		off = "UDPR_2"
		bin_start_reg = "UDPR_3"
		len = "UDPR_4"
		bin_start = "UDPR_5"
		ev_word_reg = "UDPR_6"
		counter = "UDPR_7"
		lane_idx = "UDPR_8"
		# counter_ptr = "UDPR_9"
		num_in = "UDPR_10"
		tot = "UDPR_11"
		label = "continue"

		curidx = "UDPR_12"
		
		cursum = "UDPR_13"
		off_addr = "UDPR_14"
		tmp_addr = saved_bin_start = "UDPR_15"

		tran_parallel_prefix_sum_step2_per_lane = testMSR.state.writeTransition("eventCarry", testMSR.state, testMSR.state, f"{self.taskname}::updown_parallel_prefix_sum_step2_per_lane")
		if self.debug_flag:
			tran_parallel_prefix_sum_step2_per_lane.writeAction(f"print '[DEBUG][NWID %d] Event <updown_parallel_prefix_sum_step2_per_lane> ' {'X0'} ")


		# l_bound = "UDPR_10"
		# tran_parallel_prefix_sum_step2_per_lane.writeAction(f"print 'getting perlane arguments %d' {'X8'}")


		tran_parallel_prefix_sum_step2_per_lane.writeAction(f"addi {'X7'} {lm_base_reg} 0")
		# tran_parallel_prefix_sum_step2_per_lane.writeAction(f"addi {'X7'} {lm_base_reg} 0")
		# tran_parallel_prefix_sum_step2_per_lane.writeAction(f"")

		# tran_parallel_prefix_sum_step2_per_lane.writeAction(f"addi {'X7'} {lm_base_reg} 0")
		# tran_parallel_prefix_sum_step2_per_lane.writeAction(f"movir {bin_start_reg} {0}")
		# tran_parallel_prefix_sum_step2_per_lane.writeAction(f"add {'X7'} {bin_start_reg} {bin_start_reg}")

		tran_parallel_prefix_sum_step2_per_lane.writeAction(f"addi {'X7'} {tmp_addr} {self.BIN_OFF}")
		tran_parallel_prefix_sum_step2_per_lane.writeAction(f"movlr 0({tmp_addr}) {bin_start} 0 8")
		tran_parallel_prefix_sum_step2_per_lane.writeAction(f"addi {'X7'} {tmp_addr} {self.SIZE_OFF}")

		tran_parallel_prefix_sum_step2_per_lane.writeAction(f"movlr 0({tmp_addr}) {len} 0 8")

		tran_parallel_prefix_sum_step2_per_lane.writeAction(f"muli {len} {len} {8 * self.FACTOR}")
		tran_parallel_prefix_sum_step2_per_lane.writeAction(f"add {len} {bin_start} {bin_start}")

		tran_parallel_prefix_sum_step2_per_lane.writeAction(f"addi {'X7'} {tmp_addr} {self.NUM_LANES_OFFSET}")

		tran_parallel_prefix_sum_step2_per_lane.writeAction(f"movlr 0({tmp_addr}) {prefix_addr} 0 8")
		tran_parallel_prefix_sum_step2_per_lane.writeAction(f"addi {prefix_addr} {prefix_addr} 1")

		tran_parallel_prefix_sum_step2_per_lane.writeAction(f"muli {prefix_addr} {prefix_addr} {8}")
		tran_parallel_prefix_sum_step2_per_lane.writeAction(f"add {prefix_addr} {bin_start} {prefix_addr}")
		tran_parallel_prefix_sum_step2_per_lane.writeAction(f"addi {lm_base_reg} {tmp_addr} {self.BK_PREFIX_ADDR}")

		tran_parallel_prefix_sum_step2_per_lane.writeAction(f"movrl {prefix_addr} 0({tmp_addr}) 0 8")
		# tran_parallel_prefix_sum_step2_per_lane.writeAction(f"print 'setting prefix_addr = %ld at lane %d' {prefix_addr} {'X0'}")
		
		# tran_parallel_prefix_sum_step2_per_lane.writeAction(f"addi {bin_start} {bin_start} 8")
		tran_parallel_prefix_sum_step2_per_lane = self.get_lane_idx(tran_parallel_prefix_sum_step2_per_lane, lane_idx, tmp_addr)
		tran_parallel_prefix_sum_step2_per_lane.writeAction(f"muli {lane_idx} {lane_idx} {8 * self.BK_SIZE}")
		tran_parallel_prefix_sum_step2_per_lane.writeAction(f"add {bin_start} {lane_idx} {bin_start}")
		tran_parallel_prefix_sum_step2_per_lane.writeAction(f"addi {bin_start} {saved_bin_start} 0")
		tran_parallel_prefix_sum_step2_per_lane = set_ev_label(tran_parallel_prefix_sum_step2_per_lane, ev_word_reg, f'{self.taskname}::updown_parallel_prefix_sum_step2_per_lane_step2', new_thread = False, label="")


		tran_parallel_prefix_sum_step2_per_lane.writeAction(f"addi {'X7'} {off_addr} {self.PREFIX_SUM}")
		tran_parallel_prefix_sum_step2_per_lane.writeAction(f"sub {off_addr} {bin_start} {off_addr}")
		tran_parallel_prefix_sum_step2_per_lane.writeAction(f"mov_imm2reg {tot} {self.BK_SIZE}")

		
		tran_parallel_prefix_sum_step2_per_lane.writeAction(f"mov_imm2reg {num_in} 0")
		tran_parallel_prefix_sum_step2_per_lane.writeAction(f"loop_start: beq {num_in} {tot} loop_end")
		tran_parallel_prefix_sum_step2_per_lane.writeAction(f"addi {num_in} {num_in} 1")
		# tran_parallel_prefix_sum_step2_per_lane.writeAction(f"print 'sending num_in = %ld' {num_in}")
		tran_parallel_prefix_sum_step2_per_lane.writeAction(f"send_dmlm_ld {bin_start} {ev_word_reg} 1")
		tran_parallel_prefix_sum_step2_per_lane.writeAction(f"addi {bin_start} {bin_start} 8")
		tran_parallel_prefix_sum_step2_per_lane.writeAction(f"jmp loop_start")
		tran_parallel_prefix_sum_step2_per_lane.writeAction(f"loop_end: addi {'X7'} {curidx} {self.PREFIX_SUM}")
		# tran_parallel_prefix_sum_step2_per_lane.writeAction(f"yield_terminate")
		tran_parallel_prefix_sum_step2_per_lane.writeAction(f"yield")

		# tran_parallel_prefix_sum_step2_per_lane.writeAction(f"movlr {self.LIST_COUNTER}(X7) {counter} 0 8")
		# # tran_parallel_prefix_sum_step2_per_lane.writeAction(f"divi {counter} {counter} 8")
		# tran_parallel_prefix_sum_step2_per_lane.writeAction(f"print 'listsize = %ld' {counter}")
		# tran_parallel_prefix_sum_step2_per_lane.writeAction(f"addi {'X7'} {counter_ptr} {self.LIST_COUNTER}")
		# tran_parallel_prefix_sum_step2_per_lane.writeAction(f"print 'lane %d sending to bin_start = %ld with %d' {'X0'} {bin_start} {counter}")

		# tran_parallel_prefix_sum_step2_per_lane.writeAction(f"send_dmlm {bin_start} {'X1'} {counter_ptr} 1")
		# tran_parallel_prefix_sum_step2_per_lane.writeAction(f"sendr_reply {tmp1} {tmp2} {tmp3}")
		# tran_parallel_prefix_sum_step2_per_lane.writeAction(f"yield")

		
		tran_parallel_prefix_sum_step2_per_lane_step2 = testMSR.state.writeTransition("eventCarry", testMSR.state, testMSR.state, f"{self.taskname}::updown_parallel_prefix_sum_step2_per_lane_step2")
		tran_parallel_prefix_sum_step2_per_lane_step2 = set_ev_label(tran_parallel_prefix_sum_step2_per_lane_step2, ev_word_reg, f'{self.taskname}::updown_parallel_prefix_sum_step2_per_lane_step3', new_thread = False, label="")


		tran_parallel_prefix_sum_step2_per_lane_step2.writeAction(f"subi {num_in} {num_in} 1")
		tran_parallel_prefix_sum_step2_per_lane_step2.writeAction(f"add {'X9'} {off_addr} {curidx}")
		tran_parallel_prefix_sum_step2_per_lane_step2.writeAction(f"movrl {'X8'} 0({curidx}) 0 8")
		# tran_parallel_prefix_sum_step2_per_lane_step2.writeAction(f"print 'getting value = %d' {'X8'}")
		

		# tran_parallel_prefix_sum_step2_per_lane_step2.writeAction(f"print '[DEBUG][NWID %d] Event <updown_parallel_prefix_sum_step2_per_lane_step2> expecting %d more ' {'X0'} {num_in}")
		tmp_addr = len
		tran_parallel_prefix_sum_step2_per_lane_step2.writeAction(f"addi X7 {tmp_addr} {self.BK_PREFIX_ADDR}")
		tran_parallel_prefix_sum_step2_per_lane_step2.writeAction(f"movlr 0({tmp_addr}) {prefix_addr} 0 8")

		# tran_parallel_prefix_sum_step2_per_lane_step2.writeAction(f"print 'lane %d, here having num_in = %ld' {'X0'} {num_in}")
		tran_parallel_prefix_sum_step2_per_lane_step2.writeAction(f"bgti {num_in} 0 {'continue'}")


		
		tran_parallel_prefix_sum_step2_per_lane_step2.writeAction(f"addi {'X7'} {curidx} {self.PREFIX_SUM}")
		tran_parallel_prefix_sum_step2_per_lane_step2.writeAction(f"mov_imm2reg {cursum} 0")
		tran_parallel_prefix_sum_step2_per_lane_step2.writeAction(f"loop_start: beq {num_in} {tot} loop_end")
		tran_parallel_prefix_sum_step2_per_lane_step2.writeAction(f"movlr 0({curidx}) {cur_val} 0 8")
		tran_parallel_prefix_sum_step2_per_lane_step2.writeAction(f"movrl {cursum} 0({curidx}) 0 8")
		tran_parallel_prefix_sum_step2_per_lane_step2.writeAction(f"send_dmlm {saved_bin_start} {ev_word_reg} {curidx} 1")
		tran_parallel_prefix_sum_step2_per_lane_step2.writeAction(f"addi {saved_bin_start} {saved_bin_start} 8")
		tran_parallel_prefix_sum_step2_per_lane_step2.writeAction(f"addi {curidx} {curidx} 8")
		tran_parallel_prefix_sum_step2_per_lane_step2.writeAction(f"add {cur_val} {cursum} {cursum}")
		tran_parallel_prefix_sum_step2_per_lane_step2.writeAction(f"addi {num_in} {num_in} 1")

		tran_parallel_prefix_sum_step2_per_lane_step2.writeAction(f"beq {saved_bin_start} {prefix_addr} loop_end")

		# tran_parallel_prefix_sum_step2_per_lane_step2.writeAction(f"send_dmlm_ld {bin_start} {ev_word_reg} 1")
		# tran_parallel_prefix_sum_step2_per_lane_step2.writeAction(f"add {cursum} {ev_word_reg} {cursum}")
		tran_parallel_prefix_sum_step2_per_lane_step2.writeAction(f"jmp loop_start")
		# tran_parallel_prefix_sum_step2_per_lane_step2.writeAction(f"loop_end: print 'yes'")

		# tran_parallel_prefix_sum_step2_per_lane_step2.writeAction(f"print 'lane %d, getting psum = %ld' {'X0'} {cursum}")


		# tran_parallel_prefix_sum_step2_per_lane_step2.writeAction(f"")
		tran_parallel_prefix_sum_step2_per_lane_step2.writeAction(f"loop_end: addi X7 {tmp_addr} {self.BK_PREFIX_ADDR}")

		tran_parallel_prefix_sum_step2_per_lane_step2.writeAction(f"movlr 0({tmp_addr}) {prefix_addr} 0 8")
		tran_parallel_prefix_sum_step2_per_lane_step2 = self.get_lane_idx(tran_parallel_prefix_sum_step2_per_lane_step2, off, tmp_addr)
		tran_parallel_prefix_sum_step2_per_lane_step2.writeAction(f"muli {off} {off} 8")
		tran_parallel_prefix_sum_step2_per_lane_step2.writeAction(f"add {prefix_addr} {off} {prefix_addr}")
		# tran_parallel_prefix_sum_step2_per_lane_step2.writeAction(f"print 'lane %d, sending value = %d back to %ld' {'X0'} {cursum} {prefix_addr}")


		tran_parallel_prefix_sum_step2_per_lane_step2.writeAction(f"sendr_dmlm {prefix_addr} {ev_word_reg} {cursum}")
		tran_parallel_prefix_sum_step2_per_lane_step2.writeAction(f"addi {num_in} {num_in} 1")
		# tran_parallel_prefix_sum_step2_per_lane_step2.writeAction(f"print 'lane %d, adding num_in = %ld' {'X0'} {num_in}")

		# tran_parallel_prefix_sum_step2_per_lane_step2.writeAction(f"i")
		tran_parallel_prefix_sum_step2_per_lane_step2.writeAction(f"continue: yield")


		tran_parallel_prefix_sum_step2_per_lane_step3 = testMSR.state.writeTransition("eventCarry", testMSR.state, testMSR.state, f"{self.taskname}::updown_parallel_prefix_sum_step2_per_lane_step3")
		# tran_parallel_prefix_sum_step2_per_lane_step3.writeAction(f"print '[DEBUG][NWID %d] Event <updown_parallel_prefix_sum_step2_per_lane_step3> ' {'X0'} ")
		tran_parallel_prefix_sum_step2_per_lane_step3.writeAction(f"subi {num_in} {num_in} 1")
		# tran_parallel_prefix_sum_step2_per_lane_step3.writeAction(f"print 'lane %d, getting num_in = %ld' {'X0'} {num_in}")

		tran_parallel_prefix_sum_step2_per_lane_step3.writeAction(f"beqi {num_in} 0 end_evet")
		tran_parallel_prefix_sum_step2_per_lane_step3.writeAction(f"yield")


		tran_parallel_prefix_sum_step2_per_lane_step3.writeAction(f"end_evet: sendr_reply UDPR_1 UDPR_2 UDPR_3")
		tran_parallel_prefix_sum_step2_per_lane_step3.writeAction(f"yield_terminate")
		# tran_parallel_prefix_sum_step2_per_lane_step3.writeAction(f"continue: yield")




		# Step 3: load block sum from DRAM, do prefix sum and store them back
		nxt_reg = "UDPR_0"
		tmp = "UDPR_1"
		len = "UDPR_2"
		has = "UDPR_3"
		prefix_addr = "UDPR_4"
		ev_word_reg = "UDPR_5"
		cur_addr = "UDPR_6"
		lm_base_reg = "UDPR_7"
		cursum = "UDPR_8"
		a = "UDPR_9"
		b = "UDPR_10"
		cur_val = "UDPR_11"
		tmp_addr = "UDPR_12"

		tran_parallel_prefix_sum_step3 = testMSR.state.writeTransition("eventCarry", testMSR.state, testMSR.state, f"{self.taskname}::updown_parallel_prefix_sum_step3")
		if self.debug_flag:
			tran_parallel_prefix_sum_step3.writeAction(f"print '[DEBUG][NWID %d] Event <updown_parallel_prefix_sum_step3> ' {'X0'} ")

		tran_parallel_prefix_sum_step3.writeAction(f"mov_imm2reg {ev_word_reg} 0")  
		tran_parallel_prefix_sum_step3 = set_ev_label(tran_parallel_prefix_sum_step3, ev_word_reg, f'{self.taskname}::updown_parallel_prefix_sum_step3_step2', new_thread = False, label="")

		tran_parallel_prefix_sum_step3.writeAction(f"addi {'X7'} {lm_base_reg} 0")
		tran_parallel_prefix_sum_step3.writeAction(f"mov_imm2reg {has} 0")
		tran_parallel_prefix_sum_step3.writeAction(f"addi {lm_base_reg} {tmp_addr} {self.BK_COUNT}")
		tran_parallel_prefix_sum_step3.writeAction(f"movlr 0({tmp_addr}) {len} 0 8")
		tran_parallel_prefix_sum_step3.writeAction(f"addi {lm_base_reg} {tmp_addr} {self.BK_PREFIX_ADDR}")
		tran_parallel_prefix_sum_step3.writeAction(f"movlr 0({tmp_addr}) {prefix_addr} 0 8")
		tran_parallel_prefix_sum_step3.writeAction(f"loop_start: beq {has} {len} loop_end")
		tran_parallel_prefix_sum_step3.writeAction(f"addi {has} {has} 1")
		tran_parallel_prefix_sum_step3.writeAction(f"send_dmlm_ld {prefix_addr} {ev_word_reg} 1")
		tran_parallel_prefix_sum_step3.writeAction(f"addi {prefix_addr} {prefix_addr} 8")
		tran_parallel_prefix_sum_step3.writeAction(f"jmp loop_start")
		# tran_parallel_prefix_sum_step3.writeAction(f"loop_end: print 'yes'")
		tran_parallel_prefix_sum_step3.writeAction(f"loop_end: addi {'X7'} {cur_addr} {self.BK_SUM}")
		tran_parallel_prefix_sum_step3.writeAction(f"mov_imm2reg {cursum} 0")
		tran_parallel_prefix_sum_step3.writeAction(f"addi {lm_base_reg} {tmp_addr} {self.BK_PREFIX_ADDR}")
		tran_parallel_prefix_sum_step3.writeAction(f"movlr 0({tmp_addr}) {prefix_addr} 0 8")
		tran_parallel_prefix_sum_step3.writeAction(f"yield")

		# tran_parallel_prefix_sum_step3.writeAction(f"movlr {self.BK_SUM}({lm_base_reg}) {cur_addr} 0 8")
		# tran_parallel_prefix_sum_step3.writeAction(f"movlr {self.BK_SUM}({lm_base_reg}) {prefix_addr} 0 8")

		# tran_parallel_prefix_sum_step3.writeAction(f"mov_imm2reg {has} 0")



		tran_parallel_prefix_sum_step3_step2 = testMSR.state.writeTransition("eventCarry", testMSR.state, testMSR.state, f"{self.taskname}::updown_parallel_prefix_sum_step3_step2")
		tran_parallel_prefix_sum_step3_step2.writeAction(f"subi {has} {has} 1")
		tran_parallel_prefix_sum_step3_step2.writeAction(f"sub {'X9'} {prefix_addr} {cur_addr}")

		# tran_parallel_prefix_sum_step3_step2.writeAction(f"print 'bksum getting %d from address %ld' {cursum} {'X9'}")
		tran_parallel_prefix_sum_step3_step2.writeAction(f"add {'X7'} {cur_addr} {cur_addr}")
		tran_parallel_prefix_sum_step3_step2.writeAction(f"addi {cur_addr} {cur_addr} {self.BK_SUM}")
		tran_parallel_prefix_sum_step3_step2.writeAction(f"movrl {'X8'} {0}({cur_addr}) 0 8")

		tran_parallel_prefix_sum_step3_step2.writeAction(f"mov_imm2reg {ev_word_reg} 0")  

		# tran_parallel_prefix_sum_step3.writeAction(f"movlr {self.BK_PREFIX_ADDR}({lm_base_reg}) {prefix_addr} 0 8")

		# tran_parallel_prefix_sum_step3_step2.writeAction(f"addi {'X7'} {cur_addr} {cur_addr}")

		# tran_parallel_prefix_sum_step3_step2.writeAction(f"add {cursum} {'X8'} {cursum}")
		tran_parallel_prefix_sum_step3_step2.writeAction(f"bnei {has} {0} continue")

		tran_parallel_prefix_sum_step3_step2 = set_ev_label(tran_parallel_prefix_sum_step3_step2, ev_word_reg, f'{self.taskname}::updown_parallel_prefix_sum_step3_step3', new_thread = False, label="")

		tran_parallel_prefix_sum_step3_step2.writeAction(f"mov_imm2reg {cursum} 0")
		tran_parallel_prefix_sum_step3_step2.writeAction(f"addi {'X7'} {cur_addr} {self.BK_SUM}")
		tran_parallel_prefix_sum_step3_step2.writeAction(f"loop_start: beq {has} {len} loop_end")
		tran_parallel_prefix_sum_step3_step2.writeAction(f"addi {has} {has} 1")
		tran_parallel_prefix_sum_step3_step2.writeAction(f"movlr 0({cur_addr}) {cur_val} 0 8")
		tran_parallel_prefix_sum_step3_step2.writeAction(f"movrl {cursum} 0({cur_addr}) 0 8")

		tran_parallel_prefix_sum_step3_step2.writeAction(f"send_dmlm {prefix_addr} {ev_word_reg} {cur_addr} 1")

		tran_parallel_prefix_sum_step3_step2.writeAction(f"addi {prefix_addr} {prefix_addr} 8")
		tran_parallel_prefix_sum_step3_step2.writeAction(f"addi {cur_addr} {cur_addr} 8")
		tran_parallel_prefix_sum_step3_step2.writeAction(f"add {cur_val} {cursum} {cursum}")
		tran_parallel_prefix_sum_step3_step2.writeAction(f"jmp loop_start")
		# tran_parallel_prefix_sum_step3_step2.writeAction(f"loop_end: print 'yes'")
		# tran_parallel_prefix_sum_step3_step2.writeAction(f"print 'getting psum tot %ld' {cursum}")
		tran_parallel_prefix_sum_step3_step2.writeAction(f"loop_end: divi {cursum} {cursum} {8}")
		tran_parallel_prefix_sum_step3_step2.writeAction(f"addi {lm_base_reg} {tmp_addr} {self.NEW_LENGTH}")
		tran_parallel_prefix_sum_step3_step2.writeAction(f"movrl {cursum} 0({tmp_addr}) 0 8")
		# tran_parallel_prefix_sum_step3_step2.writeAction(f"print 'getting psum tot %ld' {cursum}")





		# tran_parallel_prefix_sum_step3_step2.writeAction(f"yield_termin)
		tran_parallel_prefix_sum_step3_step2.writeAction(f"continue: yield")


		tran_parallel_prefix_sum_step3_step3 = testMSR.state.writeTransition("eventCarry", testMSR.state, testMSR.state, f"{self.taskname}::updown_parallel_prefix_sum_step3_step3")
		# tran_parallel_prefix_sum_step3_step3.writeAction(f"print f'{self.taskname}::updown_parallel_prefix_sum_step3_step3'")



		tran_parallel_prefix_sum_step3_step3.writeAction(f"subi {has} {has} 1")
		tran_parallel_prefix_sum_step3_step3.writeAction(f"bnei {has} {0} continue")



		tran_parallel_prefix_sum_step3_step3.writeAction(f"mov_imm2reg {nxt_reg} 0")  
		tran_parallel_prefix_sum_step3_step3 = set_ev_label(tran_parallel_prefix_sum_step3_step3, nxt_reg, f'{self.taskname}::updown_parallel_prefix_sum_step4', new_thread = True, label="")
		tran_parallel_prefix_sum_step3_step3.writeAction(f"send_wret {nxt_reg} {f'{self.taskname}::updown_dummy'} {'X7'} 1 {tmp}")
		tran_parallel_prefix_sum_step3_step3.writeAction(f"yield_terminate")

		tran_parallel_prefix_sum_step3_step3.writeAction(f"continue: yield")


		# Step 4: in each lane, load prefix offset, and add it to the prefix offset of each list, send the bins from bins to input list
		ev_word_reg = "UDPR_9"
		temp_reg = "UDPR_0"
		lm_base_reg = "UDPR_1"
		tmp_reg = "UDPR_2"
		tran_per_lane_reg = "UDPR_3"
		send_buffer2 = "UDPR_4"
		prefix_addr = "UDPR_5"
		tmp_addr = "UDPR_6"
		# nlanes = "UDPR_5"
		

		tran_parallel_prefix_sum_step4 = testMSR.state.writeTransition("eventCarry", testMSR.state, testMSR.state, f"{self.taskname}::updown_parallel_prefix_sum_step4")
		if self.debug_flag:
			tran_parallel_prefix_sum_step4.writeAction(f"print '[DEBUG][NWID %d] Event <updown_parallel_prefix_sum_step4> ' {'X0'} ")

		tran_parallel_prefix_sum_step4.writeAction(f"addi {'X7'} {lm_base_reg} 0")
		tran_parallel_prefix_sum_step4.writeAction(f"addi {'X7'} {send_buffer2} {self.SEND_BUFFER_OFFSET}")
		
		# Prepare for global_broadcast event

		
		tran_parallel_prefix_sum_step4.writeAction(f"mov_imm2reg {ev_word_reg} 0")
		tran_parallel_prefix_sum_step4 = set_ev_label(tran_parallel_prefix_sum_step4, ev_word_reg, f'{self.taskname}::sort_udkvmsr_broadcast::broadcast_global', new_thread = True, label="")
		# tran_init_local_sort = set_ev_label(tran_init_local_sort, ev_word_reg, f'{self.taskname}::updown_terminate', new_thread = True, label="")
		# tran_init_local_sort.writeAction(f"addi {tmp_reg} {lm_base_reg} 0")

		# Prepare for per lane arguemnts
		tran_parallel_prefix_sum_step4.writeAction(f"mov_imm2reg {tran_per_lane_reg} 0")
		tran_parallel_prefix_sum_step4.writeAction(f"evlb {tran_per_lane_reg}  {f'{self.taskname}::updown_parallel_prefix_sum_step4_per_lane'} ")
		tran_parallel_prefix_sum_step4.writeAction(f"addi {lm_base_reg} {tmp_addr} {self.NUM_LANES_OFFSET}")
		tran_parallel_prefix_sum_step4.writeAction(f"movlr 0({tmp_addr}) {tmp_reg} 0 8")
		tran_parallel_prefix_sum_step4.writeAction(f"addi {tmp_reg} {tmp_reg} 1")
		tran_parallel_prefix_sum_step4.writeAction(f"movrl {tmp_reg} 0({send_buffer2}) 0 8")
		tran_parallel_prefix_sum_step4.writeAction(f"movrl {tran_per_lane_reg} 8({send_buffer2}) 0 8")
		tran_parallel_prefix_sum_step4.writeAction(f"addi {'X7'} {tmp_addr} {self.BK_PREFIX_ADDR}")

		tran_parallel_prefix_sum_step4.writeAction(f"movlr 0({tmp_addr}) {prefix_addr} 0 8")
		tran_parallel_prefix_sum_step4.writeAction(f"movrl {prefix_addr} 16({send_buffer2}) 0 8")


		if self.debug_flag:
			tran_parallel_prefix_sum_step4.writeAction(f"print '[DEBUG][NWID %d] Event <updown_parallel_prefix_sum_step4> ' {'X0'} ")

		# Prepare for return event
		# tran_parallel_prefix_sum_step4.writeAction(f"movlr {self.saved_return}({lm_base_reg}) {temp_reg} 0 8")
		# tran_parallel_prefix_sum_step4.writeAction(f"mov_imm2reg {temp_reg} 0")
		tran_parallel_prefix_sum_step4.writeAction(f"addi {'X2'} {temp_reg} 0")
		tran_parallel_prefix_sum_step4.writeAction(f"evlb {temp_reg} {f'{self.taskname}::updown_final'}")
		# tran_parallel_prefix_sum_step4.writeAction(f"evlb {temp_reg} {f'updown_terminate'}")

		# Send out the event
		tran_parallel_prefix_sum_step4.writeAction(f"send_wcont {ev_word_reg} {temp_reg} {send_buffer2} {8} {tmp_reg}")
		tran_parallel_prefix_sum_step4.writeAction(f"yield")







		lane_addr = "UDPR_0"
		tot_off = "UDPR_1"
		nlanes = "UDPR_2"
		prefix_addr = "UDPR_3"
		off_addr = "UDPR_4"
		tmp_addr = ev_word_reg = "UDPR_5"
		cur_dram_addr = "UDPR_6"
		len = "UDPR_7"
		tot = "UDPR_8"
		curidx = "UDPR_9"
		lm_base_reg = "UDPR_10"
		dram_addr_off = "UDPR_11" 
		out = "UDPR_12"
		ev_word_reg2 = "UDPR_13"
		list_size = "UDPR_14"
		lane_idx = "UDPR_15"
		
		tran_parallel_prefix_sum_step4_per_lane = testMSR.state.writeTransition("eventCarry", testMSR.state, testMSR.state, f"{self.taskname}::updown_parallel_prefix_sum_step4_per_lane")
		if self.debug_flag:
			tran_parallel_prefix_sum_step4_per_lane.writeAction(f"print '[DEBUG][NWID %d] Event <updown_parallel_prefix_sum_step4_per_lane> ' {'X0'} ")
		# tran_parallel_prefix_sum_step4_per_lane.writeAction(f"movlr {self.BK_PREFIX_ADDR}(X7) {prefix_addr} 0 8")

		tran_parallel_prefix_sum_step4_per_lane = self.get_lane_idx(tran_parallel_prefix_sum_step4_per_lane, off_addr, tmp_addr)
		tran_parallel_prefix_sum_step4_per_lane.writeAction(f"divi {off_addr} {off_addr} {self.BK_SIZE}")
		tran_parallel_prefix_sum_step4_per_lane.writeAction(f"muli {off_addr} {off_addr} {8}")
		
		tran_parallel_prefix_sum_step4_per_lane.writeAction(f"add {'X8'} {off_addr} {off_addr}")
		# tran_parallel_prefix_sum_step4_per_lane.writeAction(f"print 'want to get offset from %ld, %ld, %d' {prefix_addr} {off_addr} {'X0'}")

		tran_parallel_prefix_sum_step4_per_lane.writeAction(f"mov_imm2reg {ev_word_reg} 0")
		tran_parallel_prefix_sum_step4_per_lane = set_ev_label(tran_parallel_prefix_sum_step4_per_lane, ev_word_reg, f'{self.taskname}::updown_parallel_prefix_sum_step4_per_lane_step2', new_thread = False, label="")
		tran_parallel_prefix_sum_step4_per_lane.writeAction(f"send_dmlm_ld {off_addr} {ev_word_reg} 1")
		tran_parallel_prefix_sum_step4_per_lane.writeAction(f"yield")

		tran_parallel_prefix_sum_step4_per_lane_step2 = testMSR.state.writeTransition("eventCarry", testMSR.state, testMSR.state, f"{self.taskname}::updown_parallel_prefix_sum_step4_per_lane_step2")
		tran_parallel_prefix_sum_step4_per_lane_step2.writeAction(f"addi {'X8'} {tot_off} 0")
		tran_parallel_prefix_sum_step4_per_lane_step2.writeAction(f"addi {'X7'} {tmp_addr} {self.INPUT_ADDR}")
		tran_parallel_prefix_sum_step4_per_lane_step2.writeAction(f"movlr 0({tmp_addr}) {cur_dram_addr} 0 8")
		tran_parallel_prefix_sum_step4_per_lane_step2.writeAction(f"add {cur_dram_addr} {'X8'} {cur_dram_addr}")
		tran_parallel_prefix_sum_step4_per_lane_step2.writeAction(f"addi {'X7'} {tmp_addr} {self.LANE_PREFIX_ADDR}")

		tran_parallel_prefix_sum_step4_per_lane_step2.writeAction(f"movlr 0({tmp_addr}) {lane_addr} 0 8")
		tran_parallel_prefix_sum_step4_per_lane_step2 = self.get_lane_idx(tran_parallel_prefix_sum_step4_per_lane_step2, off_addr, tmp_addr)
		tran_parallel_prefix_sum_step4_per_lane_step2.writeAction(f"muli {off_addr} {off_addr} {8}")
		tran_parallel_prefix_sum_step4_per_lane_step2.writeAction(f"add {lane_addr} {off_addr} {off_addr}")

		tran_parallel_prefix_sum_step4_per_lane_step2 = set_ev_label(tran_parallel_prefix_sum_step4_per_lane_step2, ev_word_reg, f'{self.taskname}::updown_parallel_prefix_sum_step4_per_lane_step3', new_thread = False, label="")
		tran_parallel_prefix_sum_step4_per_lane_step2.writeAction(f"send_dmlm_ld {off_addr} {ev_word_reg} 1")
		tran_parallel_prefix_sum_step4_per_lane_step2.writeAction(f"yield")
		# tran_parallel_prefix_sum_step4_per_lane_step2.writeAction(f"")
		# tran_parallel_prefix_sum_step4_per_lane_step2.writeAction(f"addi {cur_sp_addr} 0 8")
		# tran_parallel_prefix_sum_step4_per_lane_step2.writeAction(f"addi {'X8
		# '} {cur_dram_addr}")


	


		tran_parallel_prefix_sum_step4_per_lane_step3 = testMSR.state.writeTransition("eventCarry", testMSR.state, testMSR.state, f"{self.taskname}::updown_parallel_prefix_sum_step4_per_lane_step3")
		

		tran_parallel_prefix_sum_step4_per_lane_step3 = set_ev_label(tran_parallel_prefix_sum_step4_per_lane_step3, ev_word_reg2, f'{self.taskname}::updown_parallel_prefix_sum_step4_per_lane_step5', new_thread = False, label="")

		tran_parallel_prefix_sum_step4_per_lane_step3.writeAction(f"addi {'X7'} {lm_base_reg} {self.BIN_OFF}")
		tran_parallel_prefix_sum_step4_per_lane_step3.writeAction(f"movlr {0}({lm_base_reg}) {cur_dram_addr} 0 8")
		tran_parallel_prefix_sum_step4_per_lane_step3.writeAction(f"addi {'X7'} {lm_base_reg} {self.SIZE_OFF}")
		tran_parallel_prefix_sum_step4_per_lane_step3.writeAction(f"movlr {0}({lm_base_reg}) {len} 0 8")
		tran_parallel_prefix_sum_step4_per_lane_step3.writeAction(f"addi {'X7'} {lm_base_reg} {self.NUM_LANES_OFFSET}")

		tran_parallel_prefix_sum_step4_per_lane_step3.writeAction(f"movlr {0}({lm_base_reg}) {nlanes} 0 8")
		tran_parallel_prefix_sum_step4_per_lane_step3.writeAction(f"addi {nlanes} {nlanes} 1")
		# tran_parallel_prefix_sum_step4_per_lane_step3.writeAction(f"print 'num_lanes = %ld' {nlanes}")


		tran_parallel_prefix_sum_step4_per_lane_step3.writeAction(f"div {len} {nlanes} {len}")
		
		tran_parallel_prefix_sum_step4_per_lane_step3 = self.get_lane_idx(tran_parallel_prefix_sum_step4_per_lane_step3, lane_idx, lm_base_reg)
		tran_parallel_prefix_sum_step4_per_lane_step3.writeAction(f"mul {len} {lane_idx} {len}")
		tran_parallel_prefix_sum_step4_per_lane_step3.writeAction(f"muli {len} {len} {8 * self.FACTOR}")
		tran_parallel_prefix_sum_step4_per_lane_step3.writeAction(f"add {len} {cur_dram_addr} {cur_dram_addr}")


		tran_parallel_prefix_sum_step4_per_lane_step3.writeAction(f"add {tot_off} {'X8'} {tot_off}")
		
		tran_parallel_prefix_sum_step4_per_lane_step3.writeAction(f"addi {'X7'} {tmp_addr} {self.LIST_COUNTER}")
		tran_parallel_prefix_sum_step4_per_lane_step3.writeAction(f"movlr 0({tmp_addr}) {list_size} 0 8")
		# tran_parallel_prefix_sum_step4_per_lane_step3.writeAction(f"print 'lane %d getting sum subprefix = %d, sum = %ld, %ld' {'X0'} {'X8'} {tot_off} {list_size}")
		
		tran_parallel_prefix_sum_step4_per_lane_step3.writeAction(f"divi {list_size} {list_size} 8")



		tran_parallel_prefix_sum_step4_per_lane_step3.writeAction(f"addi {'X7'} {tmp_addr} {self.INPUT_ADDR}")
		tran_parallel_prefix_sum_step4_per_lane_step3.writeAction(f"movlr 0({tmp_addr}) {dram_addr_off} 0 8")
		tran_parallel_prefix_sum_step4_per_lane_step3.writeAction(f"add {dram_addr_off} {tot_off} {dram_addr_off}")
		
		tran_parallel_prefix_sum_step4_per_lane_step3.writeAction(f"sub {dram_addr_off} {cur_dram_addr} {dram_addr_off}")

		tran_parallel_prefix_sum_step4_per_lane_step3.writeAction(f"bgti {list_size} 0 start_sending")
		tran_parallel_prefix_sum_step4_per_lane_step3.writeAction(f"sendr_reply {tmp1} {tmp2} {tmp3}")

		tran_parallel_prefix_sum_step4_per_lane_step3.writeAction(f"start_sending: mov_imm2reg {out} 0")
		tran_parallel_prefix_sum_step4_per_lane_step3.writeAction(f"loop_start: beq {out} {list_size} loop_end")
		tran_parallel_prefix_sum_step4_per_lane_step3.writeAction(f"addi {out} {out} 1")
		tran_parallel_prefix_sum_step4_per_lane_step3 = set_ev_label(tran_parallel_prefix_sum_step4_per_lane_step3, ev_word_reg, f'{self.taskname}::updown_parallel_prefix_sum_step4_per_lane_step4', new_thread = False, label="")

		tran_parallel_prefix_sum_step4_per_lane_step3.writeAction(f"send_dmlm_ld {cur_dram_addr} {ev_word_reg} 1")
		# tran_parallel_prefix_sum_step4_per_lane_step4.writeAction(f"print 'sending out value = %d from %ld, want to send to %ld' {'X8'} {'X9'} {cur_dram_addr} ")
		tran_parallel_prefix_sum_step4_per_lane_step3.writeAction(f"addi {cur_dram_addr} {cur_dram_addr} 8")

		tran_parallel_prefix_sum_step4_per_lane_step3.writeAction(f"jmp loop_start")

		# tran_parallel_prefix_sum_step4_per_lane_step3.writeAction(f"movlr {}(X7) {cur_dram_addr} 0 8")
		# tran_parallel_prefix_sum_step4_per_lane_step3.writeAction(f"sendr_reply {tmp1} {tmp2} {tmp3}")
		tran_parallel_prefix_sum_step4_per_lane_step3.writeAction(f"loop_end: yield")



		tran_parallel_prefix_sum_step4_per_lane_step4 = testMSR.state.writeTransition("eventCarry", testMSR.state, testMSR.state, f"{self.taskname}::updown_parallel_prefix_sum_step4_per_lane_step4")


		tran_parallel_prefix_sum_step4_per_lane_step4.writeAction(f"add {'X9'} {dram_addr_off} {cur_dram_addr}")
		tran_parallel_prefix_sum_step4_per_lane_step4.writeAction(f"sendr_dmlm {cur_dram_addr} {ev_word_reg2} {'X8'}")
		tran_parallel_prefix_sum_step4_per_lane_step4.writeAction(f"yield")

		tran_parallel_prefix_sum_step4_per_lane_step5 = testMSR.state.writeTransition("eventCarry", testMSR.state, testMSR.state, f"{self.taskname}::updown_parallel_prefix_sum_step4_per_lane_step5")


		tran_parallel_prefix_sum_step4_per_lane_step5.writeAction(f"subi {out} {out} 1")

		tran_parallel_prefix_sum_step4_per_lane_step5.writeAction(f"bnei {out} {0} continue")
		
		tran_parallel_prefix_sum_step4_per_lane_step5.writeAction(f"sendr_reply {tmp1} {tmp2} {tmp3}")
		tran_parallel_prefix_sum_step4_per_lane_step5.writeAction(f"yield_terminate")
		
		tran_parallel_prefix_sum_step4_per_lane_step5.writeAction(f"continue: yield")




		lm_base_reg = "UDPR_0"
		ev_word_reg = "UDPR_1"
		temp_reg = "UDPR_2"
		len = "UDPR_3"
		addr = "UDPR_4"

		tran_final = testMSR.state.writeTransition("eventCarry", testMSR.state, testMSR.state, f"{self.taskname}::updown_final")
		if self.debug_flag:
			tran_final.writeAction(f"print '[DEBUG][NWID %d] Event <updown_final> ' {'X0'} ")
		tran_final.writeAction(f"perflog 1 0 'ending parallel prefix sum, ending sorting'")
		tran_final.writeAction(f"addi {'X7'} {lm_base_reg} {self.saved_return}")
		tran_final.writeAction(f"movlr {0}({lm_base_reg}) {ev_word_reg} 0 8")
		tran_final.writeAction(f"addi {'X7'} {lm_base_reg} {self.NEW_LENGTH}")
		tran_final.writeAction(f"movlr {0}({lm_base_reg}) {len} 0 8")
		tran_final.writeAction(f"addi {'X7'} {lm_base_reg} {self.INPUT_ADDR}")
		tran_final.writeAction(f"movlr {0}({lm_base_reg}) {addr} 0 8")

		tran_final.writeAction(f"movir {temp_reg} 1")
		tran_final.writeAction(f"sli {temp_reg} {temp_reg} 63")
		tran_final.writeAction(f"subi {temp_reg} {temp_reg} 1")

		tran_final.writeAction(f"sendr3_wcont {ev_word_reg} {temp_reg} {len} {addr} X0")
		tran_final.writeAction(f"yield_terminate")

		self.kv_map(testMSR.state, udkvsmr_task_name)
		self.kv_reduce(testMSR.state, udkvsmr_task_name)


		tran_dummy = testMSR.state.writeTransition("eventCarry", testMSR.state, testMSR.state, f"{self.taskname}::updown_dummy")
		if self.debug_flag:
			tran_dummy.writeAction(f"print '[DEBUG][NWID %d] Event <updown_dummy> ' {'X0'} ")

		# tran_dummy.writeAction(f"print 'In updown dummy %d' {'X0'}")
		tran_dummy.writeAction(f"yield_terminate")
		
	def get_lane_idx(self, tran: EFAProgram.Transition, reg: str, reg2 = ""):
		if reg2 == "":
		# tran.writeAction(f"addi {reg} {reg} {self.LANE_IDX_OFFSET}")
			assert False
			tran.writeAction(f"movlr {self.minus_base_lane}(X7) {reg} 0 8")
		else:
			tran.writeAction(f"addi {'X7'} {reg2} {self.minus_base_lane}")
			tran.writeAction(f"movlr 0({reg2}) {reg} 0 8")
		tran.writeAction(f"add {reg} {'X0'} {reg}")
		return tran
		



	def kv_map(self, state: EFAProgram.State, task: str):
		
		map_tran: EFAProgram.Transition = state.writeTransition("eventCarry", state, state, f"{task}::kv_map")
		'''
		Event:      Map task
		Operands:   Input key-value pair
		'''
		ev_word_reg = "UDPR_9"
		tmp_addr = "UDPR_14"

		# map_tran.writeAction(f"print ' '")
		if self.debug_flag:
			map_tran.writeAction(f"print '[DEBUG][NWID %d] Event <{task}::kv_map> ' {'X0'} ")
		map_tran.writeAction(f"addi {'X7'} {tmp_addr} {self.NUM_LANES_OFFSET}")

		map_tran.writeAction(f"movlr 0({tmp_addr}) {'X16'} 0 8")
		map_tran.writeAction(f"addi {'X16'} {'X16'} 1")
		# map_tran.writeAction(f"print 'getting num_lanes = %ld' {'X16'}")
		# map_tran.writeAction(f"mod {'X8'} {'X16'} {'X17'}")


		size = "UDPR_15"
	
		map_tran.writeAction(f"addi {'X7'} {tmp_addr} {self.mx_value}")
		map_tran.writeAction(f"movlr 0({tmp_addr}) {size} 0 8")
		# map_tran.writeAction(f"print 'size = %ld' {size}")
		map_tran.writeAction(f"div {size} {'X16'} {size}")
		map_tran.writeAction(f"addi {size} {size} 1")

		# map_tran.writeAction(f"print 'size = %ld' {size}")
		map_tran.writeAction(f"div {'X8'} {size} {'X17'}")
		
		# map_tran.writeAction(f"print 'size = %ld' {size}")
		# map_tran.writeAction(f"print 'mapping key %d to %d' {'X8'} {'X17'}")

		map_tran.writeAction(f"evi {'X2'} {ev_word_reg} 255 {0b0100}")
		# Emit the intermediate key-value pair to reduce task
		map_tran.writeAction(f"evlb {ev_word_reg} {f'{task}::kv_map_emit'}")
		map_tran.writeAction(f"sendr_wcont {ev_word_reg} {'X2'} {'X17'} {'X8'}")
		map_tran.writeAction(f"addi {'X2'} {ev_word_reg} 0")
		# Return to UDKVMSR library
		map_tran.writeAction(f"evlb {ev_word_reg} {f'{task}::kv_map_return'}")
		map_tran.writeAction(f"sendr_wcont {ev_word_reg} {'X2'} {'X16'} {'X16'}")
		map_tran.writeAction("yield")
		return 




	def kv_reduce(self, state: EFAProgram.State, task: str):
		# user defined reduce code
		reduce_tran: EFAProgram.Transition = state.writeTransition("eventCarry", state, state, f"{task}::kv_reduce")
		
		'''
		Event:      Reduce task 
		Operands:   Intermediate key-value pair
		'''
		bin_start_reg = "UDPR_0"
		bin_start = "UDPR_1"
		counter = "UDPR_2"
		lm_base_reg = "UDPR_3"
		len = "UDPR_4"
		nlanes = "UDPR_5"
		key = "UDPR_6"
		value = "UDPR_7"
		lane_idx = "UDPR_8"
		tmp_addr = "UDPR_9"

		if self.debug_flag:
			reduce_tran.writeAction(f"print '[DEBUG][NWID %d] Event <{task}::kv_reduce> for key = %d, value = %d' {'X0'} {'X8'} {'X9'}")
		reduce_tran.writeAction(f"addi {'X7'} {lm_base_reg} 0")
		reduce_tran.writeAction(f"movir {bin_start_reg} {0}")
		reduce_tran.writeAction(f"add {'X7'} {bin_start_reg} {bin_start_reg}")
		reduce_tran.writeAction(f"addi {bin_start_reg} {tmp_addr} {self.BIN_OFF}")
		reduce_tran.writeAction(f"movlr 0({tmp_addr}) {bin_start} 0 8")
		reduce_tran.writeAction(f"addi {lm_base_reg} {tmp_addr} {self.LIST_COUNTER}")
		reduce_tran.writeAction(f"movlr 0({tmp_addr}) {counter} 0 8")
		reduce_tran.writeAction(f"addi {lm_base_reg} {tmp_addr} {self.SIZE_OFF}")
		reduce_tran.writeAction(f"movlr 0({tmp_addr}) {len} 0 8")
		reduce_tran.writeAction(f"addi {lm_base_reg} {tmp_addr} {self.NUM_LANES_OFFSET}")
		reduce_tran.writeAction(f"movlr 0({tmp_addr}) {nlanes} 0 8")
		reduce_tran.writeAction(f"addi {nlanes} {nlanes} 1")


		reduce_tran.writeAction(f"div {len} {nlanes} {len}")
		
		reduce_tran = self.get_lane_idx(reduce_tran, lane_idx, tmp_addr)
		reduce_tran.writeAction(f"mul {len} {lane_idx} {len}")
		reduce_tran.writeAction(f"muli {len} {len} {8 * self.FACTOR}")
		reduce_tran.writeAction(f"add {len} {bin_start} {bin_start}")
		reduce_tran.writeAction(f"add {bin_start} {counter} {bin_start}")

		
		reduce_tran.writeAction(f"addi {'X8'} {key} 0")
		reduce_tran.writeAction(f"addi {'X9'} {value} 0")
		reduce_tran.writeAction(f"sendr_dmlm_wret {bin_start} {f'{task}::kv_reduce_return'} {value} {key}")

		reduce_tran.writeAction(f"addi {counter} {counter} 8")
		reduce_tran.writeAction(f"addi {lm_base_reg} {tmp_addr} {self.LIST_COUNTER}")

		reduce_tran.writeAction(f"movrl {counter} 0({tmp_addr}) 0 8")

		reduce_tran.writeAction("yield")
		
		return 
