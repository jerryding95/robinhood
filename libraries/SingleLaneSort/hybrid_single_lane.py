from linker.EFAProgram import EFAProgram

'''
Hybrid sort for single lane
1. Quick for no. of elements >= 18
2. Insertion for no. of elements < 18

Step 1: Initialize the class with:
	1. EFA
	2. Task name
	3. '1' or '0' indicating if elements are in DRAM or SP
	4. A temporary register for the library to use
	5. Debug flag

Step 2: Call the '<Task name>::init' event with operands and a continuation word to return to:
	1. No. of elements
	2. SP address
	3 (Optional). DRAM address (if the elements are in DRAM)

Step 3: Returns to the continuation word. Operands:
	1. No. of elements
	2. SP address
	3 (Optional). DRAM address (if the elements are in DRAM)

Examples are in apps/sort/{sp/dram}
'''

class SingleLaneSort:
	def __init__(self, efa: EFAProgram, task_name: str, in_dram: int, tmp_reg: str, debug_flag: bool = False):
		self.efa = efa
		self.task_name = task_name
		self.debug = debug_flag

		tran_init = self.efa.writeEvent(f"{self.task_name}::init")

		if in_dram == 1:
			if self.debug:
				tran_init.writeAction(f"print 'SingleLaneSort: Initializing DRAM sort num:%lu SP_addr:%lu DRAM_addr:%lu' X8 X9 X10")
			tran_init.writeAction(f"evi X2 {tmp_reg} {self.task_name}::dram_setup 1")
			tran_init.writeAction(f"evi {tmp_reg} {tmp_reg} 3 2")
			tran_init.writeAction(f"evi {tmp_reg} {tmp_reg} 255 4")
			tran_init.writeAction(f"sendr3_wcont {tmp_reg} X1 X8 X9 X10")
		else:
			if self.debug:
				tran_init.writeAction(f"print 'SingleLaneSort: Initializing SP sort' num:%lu SP_addr:%lu' X8 X9")
			tran_init.writeAction(f"evi X2 {tmp_reg} {self.task_name}::sp_setup 1")
			tran_init.writeAction(f"evi {tmp_reg} {tmp_reg} 2 2")
			tran_init.writeAction(f"evi {tmp_reg} {tmp_reg} 255 4")
			tran_init.writeAction(f"sendr_wcont {tmp_reg} X1 X8 X9")

		tran_init.writeAction(f"yield")

		# Writing code for event {self.task_name}::sp_setup
		tran_sp_setup = self.efa.writeEvent(f"{self.task_name}::sp_setup")
		if self.debug:
			tran_sp_setup.writeAction(f"print 'SingleLaneSort: Setting up parameters for SP sort'")
		tran_sp_setup.writeAction(f"entry: bnei X8 1 __if_setup_2_post") 
		tran_sp_setup.writeAction(f"__if_setup_0_true: sendr_wcont X1 X1 X8 X9") 
		if self.debug:
			tran_sp_setup.writeAction(f"print 'SingleLaneSort: Terminating early, user-defined event:%lu' X1")
		tran_sp_setup.writeAction(f"yield_terminate") 
		tran_sp_setup.writeAction(f"__if_setup_2_post: movir X16 0") 
		tran_sp_setup.writeAction(f"movir X18 0") 
		tran_sp_setup.writeAction(f"addi X9 X20 0") 
		tran_sp_setup.writeAction(f"movir X21 1") 
		tran_sp_setup.writeAction(f"movir X22 18") 
		tran_sp_setup.writeAction(f"addi X8 X17 0") 
		tran_sp_setup.writeAction(f"addi X1 X23 0") 
		tran_sp_setup.writeAction(f"movir X25 0") 
		tran_sp_setup.writeAction(f"subi X8 X26 1") 
		tran_sp_setup.writeAction(f"ble X22 X17 __if_setup_4_false") 
		tran_sp_setup.writeAction(f"__if_setup_3_true: evi X2 X24 {self.task_name}::insertion_sort 1") 
		if self.debug:
			tran_sp_setup.writeAction(f"print 'SingleLaneSort: Shifting to insertion, no. of elements currently:%lu' X8")
		tran_sp_setup.writeAction(f"evi X24 X24 2 2") 
		tran_sp_setup.writeAction(f"jmp __if_setup_5_post") 
		tran_sp_setup.writeAction(f"__if_setup_4_false: evi X2 X24 {self.task_name}::setup_pivot_partition 1") 
		if self.debug:
			tran_sp_setup.writeAction(f"print 'SingleLaneSort: Quick sort, no. of elements currently:%lu' X8")
		tran_sp_setup.writeAction(f"evi X24 X24 2 2") 
		tran_sp_setup.writeAction(f"__if_setup_5_post: sendr_wcont X24 X24 X25 X26") 
		tran_sp_setup.writeAction(f"yield") 

		# Writing code for event {self.task_name}::dram_setup
		tran_dram_setup = self.efa.writeEvent(f"{self.task_name}::dram_setup")
		tran_dram_setup.writeAction(f"entry: bnei X8 1 __if_dram_setup_2_post") 
		tran_dram_setup.writeAction(f"__if_dram_setup_0_true: sendr3_wcont X1 X1 X8 X9 X10") 
		if self.debug:
			tran_dram_setup.writeAction(f"print 'SingleLaneSort: Terminating early, user-defined event:%lu' X1")
		tran_dram_setup.writeAction(f"yield_terminate") 
		tran_dram_setup.writeAction(f"__if_dram_setup_2_post: evi X2 X24 {self.task_name}::dram_load 1") 
		tran_dram_setup.writeAction(f"evi X24 X24 1 2") 
		tran_dram_setup.writeAction(f"addi X10 X16 0") 
		tran_dram_setup.writeAction(f"addi X8 X17 0") 
		tran_dram_setup.writeAction(f"addi X8 X19 0") 
		tran_dram_setup.writeAction(f"addi X10 X18 0") 
		tran_dram_setup.writeAction(f"addi X9 X20 0") 
		tran_dram_setup.writeAction(f"movir X21 1") 
		tran_dram_setup.writeAction(f"movir X22 18") 
		tran_dram_setup.writeAction(f"addi X1 X23 0") 
		tran_dram_setup.writeAction(f"sendr_wcont X24 X24 X17 X17") 
		tran_dram_setup.writeAction(f"yield") 

		# Writing code for event {self.task_name}::dram_store
		tran_dram_store = self.efa.writeEvent(f"{self.task_name}::dram_store")
		tran_dram_store.writeAction(f"entry: addi X20 X25 0") 
		tran_dram_store.writeAction(f"addi X17 X19 0") 
		tran_dram_store.writeAction(f"addi X17 X30 0")  # store it in X30 for accounting
		tran_dram_store.writeAction(f"addi X16 X18 0") 
		if self.debug:
			tran_dram_store.writeAction(f"print 'SingleLaneSort: Storing back to DRAM'")
		tran_dram_store.writeAction(f"__while_dram_store_0_condition: blei X19 0 __while_dram_store_2_post") 
		if self.debug:
			tran_dram_store.writeAction(f"print 'SingleLaneSort: Remaining values to store back:%lu' X19")
		tran_dram_store.writeAction(f"__while_dram_store_1_body: blei X19 7 __if_dram_store_4_false") 
		tran_dram_store.writeAction(f"__if_dram_store_3_true: send_dmlm_wret X18 {self.task_name}::dram_store_ret X20 8 X26") 
		tran_dram_store.writeAction(f"subi X19 X19 8") 
		tran_dram_store.writeAction(f"addi X18 X18 64") 
		tran_dram_store.writeAction(f"addi X20 X20 64") 
		tran_dram_store.writeAction(f"jmp __if_dram_store_5_post") 
		tran_dram_store.writeAction(f"__if_dram_store_4_false: bnei X19 7 __if_dram_store_7_false") 
		tran_dram_store.writeAction(f"__if_dram_store_6_true: send_dmlm_wret X18 {self.task_name}::dram_store_ret X20 7 X26") 
		tran_dram_store.writeAction(f"movir X19 0") 
		tran_dram_store.writeAction(f"jmp __if_dram_store_5_post") 
		tran_dram_store.writeAction(f"__if_dram_store_7_false: bnei X19 6 __if_dram_store_10_false") 
		tran_dram_store.writeAction(f"__if_dram_store_9_true: send_dmlm_wret X18 {self.task_name}::dram_store_ret X20 6 X26") 
		tran_dram_store.writeAction(f"movir X19 0") 
		tran_dram_store.writeAction(f"jmp __if_dram_store_5_post") 
		tran_dram_store.writeAction(f"__if_dram_store_10_false: bnei X19 5 __if_dram_store_13_false") 
		tran_dram_store.writeAction(f"__if_dram_store_12_true: send_dmlm_wret X18 {self.task_name}::dram_store_ret X20 5 X26") 
		tran_dram_store.writeAction(f"movir X19 0") 
		tran_dram_store.writeAction(f"jmp __if_dram_store_5_post") 
		tran_dram_store.writeAction(f"__if_dram_store_13_false: bnei X19 4 __if_dram_store_16_false") 
		tran_dram_store.writeAction(f"__if_dram_store_15_true: send_dmlm_wret X18 {self.task_name}::dram_store_ret X20 4 X26") 
		tran_dram_store.writeAction(f"movir X19 0") 
		tran_dram_store.writeAction(f"jmp __if_dram_store_5_post") 
		tran_dram_store.writeAction(f"__if_dram_store_16_false: bnei X19 3 __if_dram_store_19_false") 
		tran_dram_store.writeAction(f"__if_dram_store_18_true: send_dmlm_wret X18 {self.task_name}::dram_store_ret X20 3 X26") 
		tran_dram_store.writeAction(f"movir X19 0") 
		tran_dram_store.writeAction(f"jmp __if_dram_store_5_post") 
		tran_dram_store.writeAction(f"__if_dram_store_19_false: bnei X19 2 __if_dram_store_22_false") 
		tran_dram_store.writeAction(f"__if_dram_store_21_true: send_dmlm_wret X18 {self.task_name}::dram_store_ret X20 2 X26") 
		tran_dram_store.writeAction(f"movir X19 0") 
		tran_dram_store.writeAction(f"jmp __if_dram_store_5_post") 
		tran_dram_store.writeAction(f"__if_dram_store_22_false: bnei X19 1 __if_dram_store_5_post") 
		tran_dram_store.writeAction(f"__if_dram_store_24_true: send_dmlm_wret X18 {self.task_name}::dram_store_ret X20 1 X26") 
		tran_dram_store.writeAction(f"movir X19 0") 
		tran_dram_store.writeAction(f"__if_dram_store_5_post: jmp __while_dram_store_0_condition") 
		tran_dram_store.writeAction(f"__while_dram_store_2_post: addi X25 X20 0") 
		#tran_dram_store.writeAction(f"evi X2 X24 {self.task_name}::__dram_store_ret 1") 
		#tran_dram_store.writeAction(f"evi X24 X24 1 2") 
		#tran_dram_store.writeAction(f"sendr_wcont X24 X24 X17 X17") 
		tran_dram_store.writeAction(f"yield") 

		# Writing code for event {self.task_name}::__dram_store_ret
		tran___dram_store_ret = self.efa.writeEvent(f"{self.task_name}::__dram_store_ret")
		if self.debug:
			tran___dram_store_ret.writeAction(f"print 'DRAM store completed, exiting to user-defined continuation %lu' X23")
		tran___dram_store_ret.writeAction(f"entry: sendr3_wcont X23 X23 X17 X20 X16") 
		tran___dram_store_ret.writeAction(f"yield_terminate") 

		# Writing code for event {self.task_name}::dram_store_ret
		tran_dram_store_ret = self.efa.writeEvent(f"{self.task_name}::dram_store_ret")
		tran_dram_store_ret.writeAction(f"entry: subi X30 X30 8") 
		tran_dram_store_ret.writeAction(f"bgti X30 0 only_yield") 
		if self.debug:
			tran_dram_store_ret.writeAction(f"print 'DRAM store completed, exiting to user-defined continuation %lu' X23")
		tran_dram_store_ret.writeAction(f"sendr3_wcont X23 X23 X17 X20 X16") 
		tran_dram_store_ret.writeAction(f"yield_terminate") 
  
		tran_dram_store_ret.writeAction(f"only_yield: yield") 

		# Writing code for event {self.task_name}::dram_load
		tran_dram_load = self.efa.writeEvent(f"{self.task_name}::dram_load")
		if self.debug:
			tran_dram_load.writeAction(f"print 'SingleLaneSort: remaining values to load:%lu' X19")
		tran_dram_load.writeAction(f"entry: blei X19 7 __if_dram_load_1_false") 
		tran_dram_load.writeAction(f"__if_dram_load_0_true: send_dmlm_ld_wret X18 {self.task_name}::dram_load_ret_8 8 X25") 
		tran_dram_load.writeAction(f"jmp __if_dram_load_2_post") 
		tran_dram_load.writeAction(f"__if_dram_load_1_false: bnei X19 7 __if_dram_load_4_false") 
		tran_dram_load.writeAction(f"__if_dram_load_3_true: send_dmlm_ld_wret X18 {self.task_name}::dram_load_ret_7 7 X25") 
		tran_dram_load.writeAction(f"jmp __if_dram_load_2_post") 
		tran_dram_load.writeAction(f"__if_dram_load_4_false: bnei X19 6 __if_dram_load_7_false") 
		tran_dram_load.writeAction(f"__if_dram_load_6_true: send_dmlm_ld_wret X18 {self.task_name}::dram_load_ret_6 6 X25") 
		tran_dram_load.writeAction(f"jmp __if_dram_load_2_post") 
		tran_dram_load.writeAction(f"__if_dram_load_7_false: bnei X19 5 __if_dram_load_10_false") 
		tran_dram_load.writeAction(f"__if_dram_load_9_true: send_dmlm_ld_wret X18 {self.task_name}::dram_load_ret_5 5 X25") 
		tran_dram_load.writeAction(f"jmp __if_dram_load_2_post") 
		tran_dram_load.writeAction(f"__if_dram_load_10_false: bnei X19 4 __if_dram_load_13_false") 
		tran_dram_load.writeAction(f"__if_dram_load_12_true: send_dmlm_ld_wret X18 {self.task_name}::dram_load_ret_4 4 X25") 
		tran_dram_load.writeAction(f"jmp __if_dram_load_2_post") 
		tran_dram_load.writeAction(f"__if_dram_load_13_false: bnei X19 3 __if_dram_load_16_false") 
		tran_dram_load.writeAction(f"__if_dram_load_15_true: send_dmlm_ld_wret X18 {self.task_name}::dram_load_ret_3 3 X25") 
		tran_dram_load.writeAction(f"jmp __if_dram_load_2_post") 
		tran_dram_load.writeAction(f"__if_dram_load_16_false: bnei X19 2 __if_dram_load_19_false") 
		tran_dram_load.writeAction(f"__if_dram_load_18_true: send_dmlm_ld_wret X18 {self.task_name}::dram_load_ret_2 2 X25") 
		tran_dram_load.writeAction(f"jmp __if_dram_load_2_post") 
		tran_dram_load.writeAction(f"__if_dram_load_19_false: bnei X19 1 __if_dram_load_22_false") 
		tran_dram_load.writeAction(f"__if_dram_load_21_true: send_dmlm_ld_wret X18 {self.task_name}::dram_load_ret_1 1 X25") 
		tran_dram_load.writeAction(f"jmp __if_dram_load_2_post") 
		tran_dram_load.writeAction(f"__if_dram_load_22_false: movir X25 0") 
		tran_dram_load.writeAction(f"subi X17 X26 1") 
		tran_dram_load.writeAction(f"muli X17 X27 8") 
		tran_dram_load.writeAction(f"sub X20 X27 X20") 
		tran_dram_load.writeAction(f"ble X22 X17 __if_dram_load_25_false") 
		tran_dram_load.writeAction(f"__if_dram_load_24_true: evi X2 X24 {self.task_name}::insertion_sort 1") 
		if self.debug:
			tran_dram_load.writeAction(f"print 'SingleLaneSort: Shifting to insertion num_elements:%lu' X17")
		tran_dram_load.writeAction(f"evi X24 X24 2 2") 
		tran_dram_load.writeAction(f"jmp __if_dram_load_26_post") 
		tran_dram_load.writeAction(f"__if_dram_load_25_false: evi X2 X24 {self.task_name}::setup_pivot_partition 1") 
		if self.debug:
			tran_dram_load.writeAction(f"print 'SingleLaneSort: Quick sort num_elements:%lu' X17")
		tran_dram_load.writeAction(f"evi X24 X24 2 2") 
		tran_dram_load.writeAction(f"__if_dram_load_26_post: sendr_wcont X24 X24 X25 X26") 
		tran_dram_load.writeAction(f"__if_dram_load_2_post: yield") 

		# Writing code for event {self.task_name}::pivot_partition
		tran_pivot_partition = self.efa.writeEvent(f"{self.task_name}::pivot_partition")
		if self.debug:
			tran_pivot_partition.writeAction(f"print 'SingleLaneSort: Ongoing quick left and right indices:%lu %lu' X8 X9")
		tran_pivot_partition.writeAction(f"entry: subi X8 X25 1") 
		tran_pivot_partition.writeAction(f"addi X9 X29 1") 
		tran_pivot_partition.writeAction(f"subi X21 X21 1") 
		tran_pivot_partition.writeAction(f"movwlr X20(X9,0,0) X24") 
		tran_pivot_partition.writeAction(f"addi X8 X26 0") 
		tran_pivot_partition.writeAction(f"__for_pivot_partition_0_condition: ble X29 X26 __for_pivot_partition_2_post") 
		tran_pivot_partition.writeAction(f"__for_pivot_partition_1_body: movwlr X20(X26,0,0) X27") 
		tran_pivot_partition.writeAction(f"ble X24 X27 __if_pivot_partition_5_post") 
		tran_pivot_partition.writeAction(f"__if_pivot_partition_3_true: addi X25 X25 1") 
		tran_pivot_partition.writeAction(f"movwlr X20(X25,0,0) X30") 
		tran_pivot_partition.writeAction(f"movwrl X30 X20(X26,0,0)") 
		tran_pivot_partition.writeAction(f"movwrl X27 X20(X25,0,0)") 
		tran_pivot_partition.writeAction(f"__if_pivot_partition_5_post: addi X26 X26 1") 
		tran_pivot_partition.writeAction(f"jmp __for_pivot_partition_0_condition") 
		tran_pivot_partition.writeAction(f"__for_pivot_partition_2_post: addi X25 X26 1") 
		tran_pivot_partition.writeAction(f"movwlr X20(X26,0,0) X27") 
		tran_pivot_partition.writeAction(f"movwlr X20(X9,0,0) X30") 
		tran_pivot_partition.writeAction(f"movwrl X30 X20(X26,0,0)") 
		tran_pivot_partition.writeAction(f"movwrl X27 X20(X9,0,0)") 
		tran_pivot_partition.writeAction(f"sub X25 X8 X30") 
		tran_pivot_partition.writeAction(f"addi X30 X27 1") 
		tran_pivot_partition.writeAction(f"ble X26 X8 __if_pivot_partition_8_post") 
		tran_pivot_partition.writeAction(f"__if_pivot_partition_6_true: addi X21 X21 1") 
		tran_pivot_partition.writeAction(f"ble X22 X27 __if_pivot_partition_10_false") 
		tran_pivot_partition.writeAction(f"__if_pivot_partition_9_true: evi X2 X28 {self.task_name}::insertion_sort 1")
		if self.debug:
			tran_pivot_partition.writeAction(f"print 'SingleLaneSort: Shifting to insertion left and right indices:%lu %lu' X8 X25") 
		tran_pivot_partition.writeAction(f"evi X28 X28 2 2") 
		tran_pivot_partition.writeAction(f"sendr_wcont X28 X28 X8 X25") 
		tran_pivot_partition.writeAction(f"jmp __if_pivot_partition_8_post") 
		tran_pivot_partition.writeAction(f"__if_pivot_partition_10_false: sendr_wcont X1 X1 X8 X25") 
		tran_pivot_partition.writeAction(f"__if_pivot_partition_8_post: addi X26 X26 1") 
		tran_pivot_partition.writeAction(f"sub X9 X26 X30") 
		tran_pivot_partition.writeAction(f"addi X30 X27 1") 
		tran_pivot_partition.writeAction(f"ble X29 X26 __if_pivot_partition_14_post") 
		tran_pivot_partition.writeAction(f"__if_pivot_partition_12_true: addi X21 X21 1") 
		tran_pivot_partition.writeAction(f"ble X22 X27 __if_pivot_partition_16_false") 
		tran_pivot_partition.writeAction(f"__if_pivot_partition_15_true: evi X2 X28 {self.task_name}::insertion_sort 1") 
		if self.debug:
			tran_pivot_partition.writeAction(f"print 'SingleLaneSort: Shifting to insertion left and right indices:%lu %lu' X26 X9")
		tran_pivot_partition.writeAction(f"evi X28 X28 2 2") 
		tran_pivot_partition.writeAction(f"sendr_wcont X28 X28 X26 X9") 
		tran_pivot_partition.writeAction(f"jmp __if_pivot_partition_14_post") 
		tran_pivot_partition.writeAction(f"__if_pivot_partition_16_false: sendr_wcont X1 X1 X26 X9") 
		tran_pivot_partition.writeAction(f"__if_pivot_partition_14_post: yield") 

		# Writing code for event {self.task_name}::setup_pivot_partition
		tran_setup_pivot_partition = self.efa.writeEvent(f"{self.task_name}::setup_pivot_partition")
		if self.debug:
			tran_setup_pivot_partition.writeAction(f"print 'SingleLaneSort: Sampling for quick sort left and right indices:%lu %lu' X8 X9")
		tran_setup_pivot_partition.writeAction(f"entry: add X8 X9 X25") 
		tran_setup_pivot_partition.writeAction(f"sri X25 X24 1") 
		tran_setup_pivot_partition.writeAction(f"evi X2 X31 {self.task_name}::pivot_partition 1") 
		tran_setup_pivot_partition.writeAction(f"evi X31 X31 2 2") 
		tran_setup_pivot_partition.writeAction(f"movwlr X20(X8,0,0) X25") 
		tran_setup_pivot_partition.writeAction(f"movwlr X20(X24,0,0) X26") 
		tran_setup_pivot_partition.writeAction(f"movwlr X20(X9,0,0) X27") 
		tran_setup_pivot_partition.writeAction(f"ble X26 X25 __if_setup_pivot_partition_1_false") 
		tran_setup_pivot_partition.writeAction(f"__if_setup_pivot_partition_0_true: bgt X27 X25 __if_setup_pivot_partition_4_false") 
		tran_setup_pivot_partition.writeAction(f"__if_setup_pivot_partition_3_true: movwrl X25 X20(X9,0,0)") 
		tran_setup_pivot_partition.writeAction(f"movwrl X27 X20(X8,0,0)") 
		tran_setup_pivot_partition.writeAction(f"jmp __if_setup_pivot_partition_5_post") 
		tran_setup_pivot_partition.writeAction(f"__if_setup_pivot_partition_4_false: ble X27 X26 __if_setup_pivot_partition_5_post") 
		tran_setup_pivot_partition.writeAction(f"__if_setup_pivot_partition_6_true: movwrl X26 X20(X9,0,0)") 
		tran_setup_pivot_partition.writeAction(f"movwrl X27 X20(X24,0,0)") 
		tran_setup_pivot_partition.writeAction(f"__if_setup_pivot_partition_5_post: jmp __if_setup_pivot_partition_2_post") 
		tran_setup_pivot_partition.writeAction(f"__if_setup_pivot_partition_1_false: ble X27 X25 __if_setup_pivot_partition_10_false") 
		tran_setup_pivot_partition.writeAction(f"__if_setup_pivot_partition_9_true: movwrl X25 X20(X9,0,0)") 
		tran_setup_pivot_partition.writeAction(f"movwrl X27 X20(X8,0,0)") 
		tran_setup_pivot_partition.writeAction(f"jmp __if_setup_pivot_partition_2_post") 
		tran_setup_pivot_partition.writeAction(f"__if_setup_pivot_partition_10_false: bgt X27 X26 __if_setup_pivot_partition_2_post") 
		tran_setup_pivot_partition.writeAction(f"__if_setup_pivot_partition_12_true: movwrl X26 X20(X9,0,0)") 
		tran_setup_pivot_partition.writeAction(f"movwrl X27 X20(X24,0,0)") 
		tran_setup_pivot_partition.writeAction(f"__if_setup_pivot_partition_2_post: sendr_wcont X31 X2 X8 X9") 
		tran_setup_pivot_partition.writeAction(f"yield") 

		# Writing code for event {self.task_name}::insertion_sort
		tran_insertion_sort = self.efa.writeEvent(f"{self.task_name}::insertion_sort")
		tran_insertion_sort.writeAction(f"entry: addi X9 X29 1") 
		tran_insertion_sort.writeAction(f"addi X8 X24 1") 
		tran_insertion_sort.writeAction(f"__for_insertion_sort_0_condition: ble X29 X24 __for_insertion_sort_2_post") 
		tran_insertion_sort.writeAction(f"__for_insertion_sort_1_body: movwlr X20(X24,0,0) X27") 
		tran_insertion_sort.writeAction(f"addi X24 X26 0") 
		tran_insertion_sort.writeAction(f"addi X8 X25 0") 
		tran_insertion_sort.writeAction(f"__for_insertion_sort_3_condition: ble X24 X25 __while_insertion_sort_9_condition") 
		tran_insertion_sort.writeAction(f"__for_insertion_sort_4_body: movwlr X20(X25,0,0) X19") 
		tran_insertion_sort.writeAction(f"ble X19 X27 __if_insertion_sort_8_post") 
		tran_insertion_sort.writeAction(f"__if_insertion_sort_6_true: movwrl X27 X20(X25,0,0)") 
		tran_insertion_sort.writeAction(f"addi X19 X27 0") 
		tran_insertion_sort.writeAction(f"addi X25 X26 1") 
		tran_insertion_sort.writeAction(f"addi X24 X25 0") 
		tran_insertion_sort.writeAction(f"__if_insertion_sort_8_post: addi X25 X25 1") 
		tran_insertion_sort.writeAction(f"jmp __for_insertion_sort_3_condition") 
		tran_insertion_sort.writeAction(f"__while_insertion_sort_9_condition: ble X24 X26 __while_insertion_sort_11_post") 
		tran_insertion_sort.writeAction(f"__while_insertion_sort_10_body: movwlr X20(X26,0,0) X19") 
		tran_insertion_sort.writeAction(f"movwrl X27 X20(X26,0,0)") 
		tran_insertion_sort.writeAction(f"addi X19 X27 0") 
		tran_insertion_sort.writeAction(f"addi X26 X26 1") 
		tran_insertion_sort.writeAction(f"jmp __while_insertion_sort_9_condition") 
		tran_insertion_sort.writeAction(f"__while_insertion_sort_11_post: movwrl X27 X20(X24,0,0)") 
		tran_insertion_sort.writeAction(f"addi X24 X24 1") 
		tran_insertion_sort.writeAction(f"jmp __for_insertion_sort_0_condition") 
		tran_insertion_sort.writeAction(f"__for_insertion_sort_2_post: subi X21 X21 1") 
		if self.debug:
			tran_insertion_sort.writeAction(f"print 'SingleLaneSort: Partitions remaining:%lu' X21")
		tran_insertion_sort.writeAction(f"bnei X21 0 __if_insertion_sort_14_post") 
		tran_insertion_sort.writeAction(f"__if_insertion_sort_12_true: beq X16 X18 __if_insertion_sort_16_false") 
		tran_insertion_sort.writeAction(f"__if_insertion_sort_15_true: evi X2 X28 {self.task_name}::dram_store 1") 
		tran_insertion_sort.writeAction(f"evi X28 X28 1 2") 
		tran_insertion_sort.writeAction(f"sendr_wcont X28 X28 X17 X17") 
		tran_insertion_sort.writeAction(f"jmp __if_insertion_sort_14_post") 
		tran_insertion_sort.writeAction(f"__if_insertion_sort_16_false: sendr_wcont X23 X23 X17 X20") 
		if self.debug:
			tran_insertion_sort.writeAction(f"print 'SingleLaneSort: Terminating, return to user-defined event %lu' X23")
		tran_insertion_sort.writeAction(f"yield_terminate") 
		tran_insertion_sort.writeAction(f"__if_insertion_sort_14_post: yield") 

		# Writing code for event {self.task_name}::dram_load_ret_8
		tran_dram_load_ret_8 = self.efa.writeEvent(f"{self.task_name}::dram_load_ret_8")
		tran_dram_load_ret_8.writeAction(f"entry: evi X2 X24 {self.task_name}::dram_load 1") 
		tran_dram_load_ret_8.writeAction(f"evi X24 X24 1 2") 
		tran_dram_load_ret_8.writeAction(f"bcpyoli X8 X20 8") 
		tran_dram_load_ret_8.writeAction(f"addi X18 X18 64") 
		tran_dram_load_ret_8.writeAction(f"addi X20 X20 64") 
		tran_dram_load_ret_8.writeAction(f"subi X19 X19 8") 
		tran_dram_load_ret_8.writeAction(f"sendr_wcont X24 X24 X17 X17") 
		tran_dram_load_ret_8.writeAction(f"yield") 

		# Writing code for event {self.task_name}::dram_load_ret_7
		tran_dram_load_ret_7 = self.efa.writeEvent(f"{self.task_name}::dram_load_ret_7")
		tran_dram_load_ret_7.writeAction(f"entry: evi X2 X24 {self.task_name}::dram_load 1") 
		tran_dram_load_ret_7.writeAction(f"evi X24 X24 1 2") 
		tran_dram_load_ret_7.writeAction(f"bcpyoli X8 X20 7") 
		tran_dram_load_ret_7.writeAction(f"addi X18 X18 56") 
		tran_dram_load_ret_7.writeAction(f"addi X20 X20 56") 
		tran_dram_load_ret_7.writeAction(f"movir X19 0") 
		tran_dram_load_ret_7.writeAction(f"sendr_wcont X24 X24 X17 X17") 
		tran_dram_load_ret_7.writeAction(f"yield") 

		# Writing code for event {self.task_name}::dram_load_ret_6
		tran_dram_load_ret_6 = self.efa.writeEvent(f"{self.task_name}::dram_load_ret_6")
		tran_dram_load_ret_6.writeAction(f"entry: evi X2 X24 {self.task_name}::dram_load 1") 
		tran_dram_load_ret_6.writeAction(f"evi X24 X24 1 2") 
		tran_dram_load_ret_6.writeAction(f"bcpyoli X8 X20 6") 
		tran_dram_load_ret_6.writeAction(f"addi X18 X18 48") 
		tran_dram_load_ret_6.writeAction(f"addi X20 X20 48") 
		tran_dram_load_ret_6.writeAction(f"movir X19 0") 
		tran_dram_load_ret_6.writeAction(f"sendr_wcont X24 X24 X17 X17") 
		tran_dram_load_ret_6.writeAction(f"yield") 

		# Writing code for event {self.task_name}::dram_load_ret_5
		tran_dram_load_ret_5 = self.efa.writeEvent(f"{self.task_name}::dram_load_ret_5")
		tran_dram_load_ret_5.writeAction(f"entry: evi X2 X24 {self.task_name}::dram_load 1") 
		tran_dram_load_ret_5.writeAction(f"evi X24 X24 1 2") 
		tran_dram_load_ret_5.writeAction(f"bcpyoli X8 X20 5") 
		tran_dram_load_ret_5.writeAction(f"addi X18 X18 40") 
		tran_dram_load_ret_5.writeAction(f"addi X20 X20 40") 
		tran_dram_load_ret_5.writeAction(f"movir X19 0") 
		tran_dram_load_ret_5.writeAction(f"sendr_wcont X24 X24 X17 X17") 
		tran_dram_load_ret_5.writeAction(f"yield") 

		# Writing code for event {self.task_name}::dram_load_ret_4
		tran_dram_load_ret_4 = self.efa.writeEvent(f"{self.task_name}::dram_load_ret_4")
		tran_dram_load_ret_4.writeAction(f"entry: evi X2 X24 {self.task_name}::dram_load 1") 
		tran_dram_load_ret_4.writeAction(f"evi X24 X24 1 2") 
		tran_dram_load_ret_4.writeAction(f"bcpyoli X8 X20 4") 
		tran_dram_load_ret_4.writeAction(f"addi X18 X18 32") 
		tran_dram_load_ret_4.writeAction(f"addi X20 X20 32") 
		tran_dram_load_ret_4.writeAction(f"movir X19 0") 
		tran_dram_load_ret_4.writeAction(f"sendr_wcont X24 X24 X17 X17") 
		tran_dram_load_ret_4.writeAction(f"yield") 

		# Writing code for event {self.task_name}::dram_load_ret_3
		tran_dram_load_ret_3 = self.efa.writeEvent(f"{self.task_name}::dram_load_ret_3")
		tran_dram_load_ret_3.writeAction(f"entry: evi X2 X24 {self.task_name}::dram_load 1") 
		tran_dram_load_ret_3.writeAction(f"evi X24 X24 1 2") 
		tran_dram_load_ret_3.writeAction(f"bcpyoli X8 X20 3") 
		tran_dram_load_ret_3.writeAction(f"addi X18 X18 24") 
		tran_dram_load_ret_3.writeAction(f"addi X20 X20 24") 
		tran_dram_load_ret_3.writeAction(f"movir X19 0") 
		tran_dram_load_ret_3.writeAction(f"sendr_wcont X24 X24 X17 X17") 
		tran_dram_load_ret_3.writeAction(f"yield") 

		# Writing code for event {self.task_name}::dram_load_ret_2
		tran_dram_load_ret_2 = self.efa.writeEvent(f"{self.task_name}::dram_load_ret_2")
		tran_dram_load_ret_2.writeAction(f"entry: evi X2 X24 {self.task_name}::dram_load 1") 
		tran_dram_load_ret_2.writeAction(f"evi X24 X24 1 2") 
		tran_dram_load_ret_2.writeAction(f"bcpyoli X8 X20 2") 
		tran_dram_load_ret_2.writeAction(f"addi X18 X18 16") 
		tran_dram_load_ret_2.writeAction(f"addi X20 X20 16") 
		tran_dram_load_ret_2.writeAction(f"movir X19 0") 
		tran_dram_load_ret_2.writeAction(f"sendr_wcont X24 X24 X17 X17") 
		tran_dram_load_ret_2.writeAction(f"yield") 

		# Writing code for event {self.task_name}::dram_load_ret_1
		tran_dram_load_ret_1 = self.efa.writeEvent(f"{self.task_name}::dram_load_ret_1")
		tran_dram_load_ret_1.writeAction(f"entry: evi X2 X24 {self.task_name}::dram_load 1") 
		tran_dram_load_ret_1.writeAction(f"evi X24 X24 1 2") 
		tran_dram_load_ret_1.writeAction(f"bcpyoli X8 X20 1") 
		tran_dram_load_ret_1.writeAction(f"addi X18 X18 8") 
		tran_dram_load_ret_1.writeAction(f"addi X20 X20 8") 
		tran_dram_load_ret_1.writeAction(f"movir X19 0") 
		tran_dram_load_ret_1.writeAction(f"sendr_wcont X24 X24 X17 X17") 
		tran_dram_load_ret_1.writeAction(f"yield") 
