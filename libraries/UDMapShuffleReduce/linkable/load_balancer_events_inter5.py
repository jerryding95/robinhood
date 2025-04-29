from linker.EFAProgram import efaProgram

## Global constants

@efaProgram
def EFA_load_balancer_events_inter5(efa):
  efa.code_level = 'machine'
  state0 = efa.State("udweave_init") #Only one state code 
  efa.add_initId(state0.state_id)
  ## Static declarations
  ## Param "kv_arr_addr" uses Register X8, scope (0->1)
  ## Param "entry_addr" uses Register X9, scope (0->1)
  ## Scoped Variable "returned_key" uses Register X16, scope (0->1)
  ## Scoped Variable "is_claimed" uses Register X17, scope (0->1)
  ## Scoped Variable "ret_cont_word" uses Register X18, scope (0->1)
  ## Scoped Variable "base_ptr" uses Register X19, scope (0->1)
  ## Scoped Variable "ptr" uses Register X20, scope (0->1)
  ## Scoped Variable "entry_ptr" uses Register X21, scope (0->1)
  ## Scoped Variable "num" uses Register X22, scope (0->1)
  ## Scoped Variable "ev_word" uses Register X23, scope (0->1)
  ## Scoped Variable "start" uses Register X24, scope (0->1)
  ## Scoped Variable "next_change_stop" uses Register X25, scope (0->1)
  ## Scoped Variable "start_written_flag" uses Register X26, scope (0->1)
  ## Scoped Variable "end" uses Register X27, scope (0->1)
  ## Scoped Variable "tmp" uses Register X22, scope (0->1->3)
  ## Scoped Variable "tmp1" uses Register X23, scope (0->1->3)
  ## Scoped Variable "tmp" uses Register X23, scope (0->1->5)
  ## Scoped Variable "cswp_ret" uses Register X24, scope (0->1->5)
  ## Scoped Variable "tmp" uses Register X28, scope (0->1->13)
  ## Scoped Variable "tmp1" uses Register X29, scope (0->1->13)
  ## Scoped Variable "tmp" uses Register X29, scope (0->1->15->17->19->21)
  ## Scoped Variable "cswp_ret" uses Register X30, scope (0->1->15->17->19->21)
  ## Scoped Variable "tmp" uses Register X29, scope (0->1->15->17->19->33)
  ## Scoped Variable "dest" uses Register X30, scope (0->1->15->17->19->33)
  ## Scoped Variable "cswp_ret" uses Register X30, scope (0->1->15->17->19->33->35)
  ## Scoped Variable "tmp1" uses Register X31, scope (0->1->15->17->19->33->35)
  ## Scoped Variable "tmp" uses Register X29, scope (0->1->15->17->19->39)
  ## Scoped Variable "tmp" uses Register X28, scope (0->1->15->17->42)
  ## Scoped Variable "tmp1" uses Register X29, scope (0->1->15->17->42)
  ## Scoped Variable "cswp_ret" uses Register X30, scope (0->1->15->17->42->44)
  ## Scoped Variable "tmp1" uses Register X28, scope (0->1->54)
  ## Scoped Variable "tmp" uses Register X29, scope (0->1->54)
  ## Scoped Variable "cswp_ret" uses Register X30, scope (0->1->54)
  ## Param "dram_addr" uses Register X8, scope (0->60)
  ## Param "tmp" uses Register X8, scope (0->61)
  
  ##############################################
  ###### Writing code for thread receiver ######
  ##############################################
  ## event receive_intermediate_kv(unsigned long key, unsigned long value){
  ## }
  ## event fetched_kv_ptr_for_cache(unsigned long kv_arr_addr, unsigned long entry_addr){
  ## 	// Decrement unresolved_kv_count by 1
  ## 	unsigned long* local ptr = LMBASE + unresolved_kv_count_offset;
  ## 	ptr[0] = ptr[0] - 1;
  ## 	// Locate intermediate_cache entry
  ## 	ptr = LMBASE + intermediate_ptr_offset;
  ## 	unsigned long base_addr = ptr[0];
  ## 	unsigned long* local entry_ptr = LMBASE + intermediate_cache_offset;
  ## 	entry_ptr = entry_ptr + (entry_addr - base_addr) * intermediate_cache_entry_size;
  ## 	// Read key and check if already claimed
  ## 	unsigned long returned_key = entry_ptr[0];
  ## 	unsigned long is_claimed = returned_key & 1;
  ## 	returned_key = returned_key >> 1;
  ## 	// Account for the dram request coming back
  ## 	unsigned long matched_count = 0;
  ## 	unsigned long* dest = entry_ptr[1];
  ## 	// Update kv_ptr if not claimed
  ## 	if (is_claimed == 0) {
  ## 		entry_ptr[1] = kv_arr_addr;
  ## 		dest = kv_arr_addr;
  ## 	}
  ## 	// Read materialize_kv_cache metadata
  ## 	ptr = LMBASE + materializing_metadata_offset;
  ## 	long* local start = ptr[0];
  ## 	long* local end = ptr[1];
  ## 	long is_empty = ptr[2];
  ## 	if (is_empty == 1){
  ## 		print("Lane %d receiver fetched_kv_ptr_for_cache gets empty cache! Terminate!", NETID);
  ## 	}
  ## 	unsigned long ret_cont_word;
  ## 	if (is_claimed == 1){ ret_cont_word = evw_update_event(CEVNT, receiver_update_unresolved_kv_count); }
  ## 	else{ ret_cont_word = evw_update_event(CEVNT, receiver_materialize_kv_ret); }
  ## 	ret_cont_word = evw_update_thread(ret_cont_word, NEWTH);
  ## 	// If start >= end, set stop at max limit
  ## 	// Otherwise, set stop at end
  ## 	unsigned long* local stop;
  ## 	if (end > start){ stop = end;}
  ## 	else{ stop = LMBASE + materialize_kv_cache_offset + materialize_kv_cache_size; }
  ## 	// Iterate and update start until find an unmatch
  ## 	while (start < stop){
  ## 		if (start[0] != -1){
  ## 			if (start[0] != returned_key){
  ## 				break;
  ## 			}
  ## 			if (is_claimed==0){ 
  ## 				send_dram_write(dest, start, inter_kvpair_size, ret_cont_word); 
  ## 				dest = dest + inter_kvpair_size * 8;
  ## 			}
  ## 			else {
  ## 				unsigned long ev_word = dest;
  ## 				send_event(ev_word, start, inter_kvpair_size, ret_cont_word); 
  ## 			}
  ## 			matched_count = matched_count + 1;
  ## 			for (int i=0; i<inter_kvpair_size; i=i+1) { start[i] = -1; }
  ## 		}
  ## 		start = start + inter_kvpair_size * 8;
  ## 	}
  ## 	// If start hits either end or maximum limit
  ## 	// If hit maximum limit, reset start to minimum limit and keep iterating start
  ## 	if (start == stop && stop != end) {
  ## 		start = LMBASE + materialize_kv_cache_offset;
  ## 		while (start < end){
  ## 			if (start[0] != -1){
  ## 				if (start[0] != returned_key){
  ## 					break;
  ## 				}
  ## 				if (is_claimed==0){ 
  ## 					send_dram_write(dest, start, inter_kvpair_size, ret_cont_word); 
  ## 					dest = dest + inter_kvpair_size * 8;
  ## 				}
  ## 				else {
  ## 					unsigned long ev_word = dest;
  ## 					send_event(ev_word, start, inter_kvpair_size, ret_cont_word); 
  ## 				}
  ## 				matched_count = matched_count + 1;
  ## 				for (int i=0; i<inter_kvpair_size; i=i+1) { start[i] = -1; }
  ## 			}
  ## 			start = start + inter_kvpair_size * 8;
  ## 		}
  ## 	}
  ## 	// At this point, situation includes
  ## 	// 1. Start hits an unmatch, needs to continue iterating, then start != end
  ## 	// 2. Start == end and the first entry is an unmatch, then matched_count == 0
  ## 	// 3. Start hits end, stop iterating
  ## 	// If in situation 1 and 2, iterating end and update end
  ## 	if (start != end || matched_count == 0){
  ## 		ptr = start;
  ## 		unsigned long new_end = start;
  ## 		// If start >= end, set stop at max limit
  ## 		// Otherwise, set stop at end
  ## 		if (end > start){ stop = end;}
  ## 		else{ stop = LMBASE + materialize_kv_cache_offset + materialize_kv_cache_size; }
  ## 		// Iterate till stop
  ## 		while (ptr < stop) {
  ## 			if (ptr[0] != -1){
  ## 				if (ptr[0] == returned_key){
  ## 					if (is_claimed==0){ 
  ## 						send_dram_write(dest, ptr, inter_kvpair_size, ret_cont_word); 
  ## 						dest = dest + inter_kvpair_size * 8;
  ## 					}
  ## 					else {
  ## 						unsigned long ev_word = dest;
  ## 						send_event(ev_word, ptr, inter_kvpair_size, ret_cont_word); 
  ## 					}
  ## 					matched_count = matched_count + 1;
  ## 				}
  ## 				else{ new_end = ptr + inter_kvpair_size * 8; }
  ## 			}
  ## 			ptr = ptr + inter_kvpair_size * 8;
  ## 		}
  ## 		// If stop != end, meaning stop == max limit and start >= end
  ## 		// Reset ptr to beginning of cache and iterate till end
  ## 		if (stop != end) {
  ## 			ptr = LMBASE + materialize_kv_cache_offset;
  ## 			while (ptr < end) {
  ## 				if (ptr[0] != -1){
  ## 					if (ptr[0] == returned_key){
  ## 						if (is_claimed==0){ 
  ## 							send_dram_write(dest, ptr, inter_kvpair_size, ret_cont_word); 
  ## 							dest = dest + inter_kvpair_size * 8;
  ## 						}
  ## 						else {
  ## 							unsigned long ev_word = dest;
  ## 							send_event(ev_word, ptr, inter_kvpair_size, ret_cont_word); 
  ## 						}
  ## 						matched_count = matched_count + 1;
  ## 					}
  ## 					else{ new_end = ptr + inter_kvpair_size * 8; }
  ## 				}
  ## 				ptr = ptr + inter_kvpair_size * 8;
  ## 			}
  ## 		}
  ## 		end = new_end;
  ## 	}
  ## 	ptr = LMBASE + materializing_metadata_offset;
  ## 	ptr[0] = start;
  ## 	ptr[1] = end;
  ## 	if (start == end){ ptr[2] = 1; }
  ## 	else{ ptr[2] = 0; }
  ## 	if (is_claimed == 1){
  ## 		// If claimed, increment unresolved_kv_count by matched_count
  ## 		ptr = LMBASE + unresolved_kv_count_offset;
  ## 		ptr[0] = ptr[0] + matched_count;
  ## 	}
  ## 	else{
  ## 		// If not claimed, set kv rec number as matched_count
  ## 		entry_ptr[2] = matched_count;
  ## 	}
  ## 	yield_terminate;
  ## }
  # Writing code for event receiver::ud_fetched_kv_ptr_for_cache
  tranreceiver__ud_fetched_kv_ptr_for_cache = efa.writeEvent('receiver::ud_fetched_kv_ptr_for_cache')
  ## Get start spd address of this ud
  tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"entry: andi X0 X22 63") 
  tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"sli X22 X23 16") 
  tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"sub X7 X23 X19") 
  ## Locate intermediate_cache entry
  tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"movir X28 {self.intermediate_ptr_offset}") 
  tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"add X19 X28 X20") 
  ## unsigned long tmp = (entry_addr - ptr[0]) / 8;
  tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"__if_ud_fetched_kv_ptr_for_cache_0_true: movlr 0(X20) X22 0 8") 
  tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"sub X9 X22 X23") 
  tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"sari X23 X22 3") 
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
  tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"movlr 0(X21) X16 0 8") 
  tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"andi X16 X17 1") 
  tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"sri X16 X16 1") 
  tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"print 'Lane %u received kv_ptr for key %ld with bin address %lu(0x%lx), entry address %lu' X0 X16 X8 X8 X9") 
  ## Read cache start and num
  ## unsigned long* local start;
  ## unsigned long num;
  ## asm {
  ## 	"movlr 13(%[entry_ptr]) %[start] 0 3
  ## 	movlr 16(%[entry_ptr]) %[num] 0 4"
  ## } : [entry_ptr] "r" (entry_ptr), [start] "r" (start), [num] "r" (num);
  tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"addi X21 X20 16") 
  tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"__if_ud_fetched_kv_ptr_for_cache_3_true: addi X22 X24 1") 
  tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"__while_ud_fetched_kv_ptr_for_cache_6_condition: bequ X22 X24 __while_ud_fetched_kv_ptr_for_cache_8_post") 
  tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"__while_ud_fetched_kv_ptr_for_cache_7_body: movlr 0(X20) X22 0 8") 
  tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"movlr 0(X20) X23 0 4") 
  tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"cswp X20 X24 X22 X23") 
  tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"jmp __while_ud_fetched_kv_ptr_for_cache_6_condition") 
  tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"__while_ud_fetched_kv_ptr_for_cache_8_post: sri X22 X22 32") 
  tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"movlr 24(X21) X23 0 8") 
  tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"print 'Key %ld: %ld values cached, claimed: %ld, event word %lx' X16 X22 X17 X23") 
  tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"movrl X8 8(X21) 0 8") 
  tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"bneiu X17 1 __if_ud_fetched_kv_ptr_for_cache_10_false") 
  tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"__if_ud_fetched_kv_ptr_for_cache_9_true: evi X2 X18 {self.ln_receiver_update_unresolved_kv_count_ev_label} 1") 
  tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"jmp __if_ud_fetched_kv_ptr_for_cache_11_post") 
  tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"__if_ud_fetched_kv_ptr_for_cache_10_false: evi X2 X18 {self.ln_receiver_materialize_ret_ev_label} 1") 
  tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"__if_ud_fetched_kv_ptr_for_cache_11_post: evi X18 X18 255 4") 
  ## Read materialize_kv_cache metadata
  ## Locate start of materialize_kv_cache
  tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"movir X28 {self.materializing_metadata_offset}") 
  tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"add X19 X28 X20") 
  tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"movlr 0(X20) X24 0 8") 
  tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"movir X28 {self.materialize_kv_cache_count}") 
  tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"div X24 X28 X26") 
  tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"addi X26 X27 1") 
  tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"movir X28 {self.materialize_kv_cache_count}") 
  tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"mul X27 X28 X25") 
  tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"movir X26 0") 
  ## long tmp = ((start / materialize_kv_cache_count) % 64) << 16;
  ## long tmp1 = (start % materialize_kv_cache_count) * inter_kvpair_size * 8;
  ## tmp = base_ptr + tmp + materialize_kv_cache_offset;
  ## ptr = tmp + tmp1;
  ## long tmp = ((start / materialize_kv_cache_count) % 64) << 16;
  ## long tmp1 = (start % materialize_kv_cache_count) * inter_kvpair_size * 8;
  ## tmp = base_ptr + tmp + materialize_kv_cache_offset;
  ## ptr = tmp + tmp1;
  tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"__if_ud_fetched_kv_ptr_for_cache_12_true: movir X30 {self.materialize_kv_cache_count}") 
  tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"div X24 X30 X28") 
  tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"andi X28 X28 63") 
  tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"sli X28 X28 16") 
  tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"movir X30 {self.materialize_kv_cache_offset}") 
  tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"add X28 X30 X28") 
  tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"add X28 X19 X28") 
  tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"movir X30 {self.materialize_kv_cache_count}") 
  tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"mod X24 X30 X29") 
  tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"muli X29 X29 {self.inter_kvpair_size}") 
  tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"sli X29 X29 3") 
  tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"movlr 8(X20) X27 0 8") 
  tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"add X28 X29 X20") 
  tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"addi X21 X21 16") 
  tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"__while_ud_fetched_kv_ptr_for_cache_15_condition: bleiu X22 0 __while_ud_fetched_kv_ptr_for_cache_17_post") 
  tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"__while_ud_fetched_kv_ptr_for_cache_16_body: movlr 0(X20) X28 0 8") 
  tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"beqi X28 -1 __if_ud_fetched_kv_ptr_for_cache_20_post") 
  ## unsigned long tmp = ptr[0];
  tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"__if_ud_fetched_kv_ptr_for_cache_18_true: movlr 0(X20) X28 0 8") 
  tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"bne X28 X16 __if_ud_fetched_kv_ptr_for_cache_22_false") 
  tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"__if_ud_fetched_kv_ptr_for_cache_21_true: movlr 0(X20) X28 0 8") 
  tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"print 'Matched: entry %ld reads %ld at %lu' X24 X28 X20") 
  tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"subi X22 X22 1") 
  tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"bneiu X22 0 __if_ud_fetched_kv_ptr_for_cache_26_post") 
  tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"__if_ud_fetched_kv_ptr_for_cache_24_true: addi X22 X30 1") 
  tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"__while_ud_fetched_kv_ptr_for_cache_27_condition: bequ X22 X30 __while_ud_fetched_kv_ptr_for_cache_29_post") 
  tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"__while_ud_fetched_kv_ptr_for_cache_28_body: movlr 0(X21) X22 0 8") 
  tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"movlr 0(X21) X29 0 4") 
  tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"cswp X21 X30 X22 X29") 
  tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"jmp __while_ud_fetched_kv_ptr_for_cache_27_condition") 
  tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"__while_ud_fetched_kv_ptr_for_cache_29_post: sri X22 X22 32") 
  ## If matched, first double check if key just got claimed
  tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"__if_ud_fetched_kv_ptr_for_cache_26_post: bneiu X17 0 __if_ud_fetched_kv_ptr_for_cache_32_post") 
  tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"__if_ud_fetched_kv_ptr_for_cache_30_true: movlr -16(X21) X29 0 8") 
  tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"andi X29 X17 1") 
  tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"beqiu X17 0 __if_ud_fetched_kv_ptr_for_cache_32_post") 
  ## If just got claimed, wait till claimed dest evword is written
  tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"__if_ud_fetched_kv_ptr_for_cache_33_true: evlb X18 {self.ln_receiver_update_unresolved_kv_count_ev_label}") 
  tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"movlr 8(X21) X23 0 8") 
  tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"print 'Key %ld just got claimed, event word %lx' X16 X23") 
  tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"__while_ud_fetched_kv_ptr_for_cache_36_condition: movlr 8(X21) X29 0 8") 
  tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"bnei X29 -1 __if_ud_fetched_kv_ptr_for_cache_32_post") 
  tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"__while_ud_fetched_kv_ptr_for_cache_37_body: movlr 8(X21) X23 0 8") 
  tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"jmp __while_ud_fetched_kv_ptr_for_cache_36_condition") 
  tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"__if_ud_fetched_kv_ptr_for_cache_32_post: beqiu X17 0 __if_ud_fetched_kv_ptr_for_cache_42_true") 
  tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"__if_ud_fetched_kv_ptr_for_cache_39_true: send_wcont X23 X18 X20 {self.inter_kvpair_size}") 
  tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"jmp __if_ud_fetched_kv_ptr_for_cache_41_post") 
  tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"__if_ud_fetched_kv_ptr_for_cache_42_true: addi X30 X29 1") 
  tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"__while_ud_fetched_kv_ptr_for_cache_45_condition: beq X30 X29 __while_ud_fetched_kv_ptr_for_cache_47_post") 
  tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"__while_ud_fetched_kv_ptr_for_cache_46_body: movlr 0(X21) X29 0 8") 
  tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"addi X29 X31 1") 
  tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"cswp X21 X30 X29 X31") 
  tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"jmp __while_ud_fetched_kv_ptr_for_cache_45_condition") 
  tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"__while_ud_fetched_kv_ptr_for_cache_47_post: sli X29 X29 32") 
  tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"sri X29 X29 32") 
  tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"muli X29 X30 {self.inter_kvpair_size}") 
  tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"sli X30 X31 3") 
  tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"add X8 X31 X23") 
  tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"addi X23 X30 0") 
  tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"print 'receive_ptr materialize key %ld to Dram %lu(0x%lx) as the %ld-th kv' X16 X30 X30 X29") 
  tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"send_dmlm X30 X18 X20 {self.inter_kvpair_size}") 
  ## Erase this entry
  tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"__if_ud_fetched_kv_ptr_for_cache_41_post: movir X29 0") 
  tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"__for_ud_fetched_kv_ptr_for_cache_48_condition: bgei X29 {self.inter_kvpair_size} __for_ud_fetched_kv_ptr_for_cache_50_post") 
  tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"__for_ud_fetched_kv_ptr_for_cache_49_body: movir X31 -1") 
  tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"movwrl X31 X20(X29,0,0)") 
  tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"addi X29 X29 1") 
  tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"jmp __for_ud_fetched_kv_ptr_for_cache_48_condition") 
  tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"__for_ud_fetched_kv_ptr_for_cache_50_post: jmp __if_ud_fetched_kv_ptr_for_cache_20_post") 
  tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"__if_ud_fetched_kv_ptr_for_cache_22_false: movlr 0(X20) X28 0 8") 
  ## print("Not matching: entry %ld reads %ld at %lu", start, tmp, ptr);
  ## If not matched for the first time, write new start to spd
  tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"bneiu X26 0 __if_ud_fetched_kv_ptr_for_cache_20_post") 
  tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"__if_ud_fetched_kv_ptr_for_cache_51_true: movir X31 {self.materializing_metadata_offset}") 
  tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"add X19 X31 X29") 
  ## long tmp;
  tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"addi X28 X30 1") 
  tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"__while_ud_fetched_kv_ptr_for_cache_54_condition: beq X30 X28 __while_ud_fetched_kv_ptr_for_cache_56_post") 
  tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"__while_ud_fetched_kv_ptr_for_cache_55_body: movlr 0(X29) X28 0 8") 
  tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"bgt X24 X28 __if_ud_fetched_kv_ptr_for_cache_59_post") 
  tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"__if_ud_fetched_kv_ptr_for_cache_57_true: jmp __while_ud_fetched_kv_ptr_for_cache_56_post") 
  tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"__if_ud_fetched_kv_ptr_for_cache_59_post: cswp X29 X30 X28 X24") 
  tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"jmp __while_ud_fetched_kv_ptr_for_cache_54_condition") 
  tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"__while_ud_fetched_kv_ptr_for_cache_56_post: movir X26 1") 
  ## Step forward one entry
  tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"__if_ud_fetched_kv_ptr_for_cache_20_post: addi X24 X24 1") 
  tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"bneu X24 X25 __if_ud_fetched_kv_ptr_for_cache_61_false") 
  ## If going across lanes, update ptr
  tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"__if_ud_fetched_kv_ptr_for_cache_60_true: movir X28 {self.materialize_kv_cache_count}") 
  tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"div X24 X28 X28") 
  tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"andi X28 X29 63") 
  tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"sli X29 X30 16") 
  tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"add X19 X30 X31") 
  tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"movir X28 {self.materialize_kv_cache_offset}") 
  tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"add X31 X28 X20") 
  tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"movir X28 {self.materialize_kv_cache_count}") 
  tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"add X25 X28 X25") 
  tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"jmp __if_ud_fetched_kv_ptr_for_cache_62_post") 
  tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"__if_ud_fetched_kv_ptr_for_cache_61_false: addi X20 X20 {self.inter_kvpair_size * WORD_SIZE}") 
  ## If going inside lane, increment ptr
  tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"__if_ud_fetched_kv_ptr_for_cache_62_post: jmp __while_ud_fetched_kv_ptr_for_cache_15_condition") 
  ## Write new start to spd if haven't
  tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"__while_ud_fetched_kv_ptr_for_cache_17_post: bneiu X26 0 __if_ud_fetched_kv_ptr_for_cache_65_post") 
  tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"__if_ud_fetched_kv_ptr_for_cache_63_true: movir X31 {self.materializing_metadata_offset}") 
  tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"add X19 X31 X28") 
  tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"addi X29 X30 1") 
  tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"__while_ud_fetched_kv_ptr_for_cache_66_condition: beq X30 X29 __while_ud_fetched_kv_ptr_for_cache_68_post") 
  tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"__while_ud_fetched_kv_ptr_for_cache_67_body: movlr 0(X28) X29 0 8") 
  tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"bgt X24 X29 __if_ud_fetched_kv_ptr_for_cache_71_post") 
  tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"__if_ud_fetched_kv_ptr_for_cache_69_true: jmp __while_ud_fetched_kv_ptr_for_cache_68_post") 
  tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"__if_ud_fetched_kv_ptr_for_cache_71_post: cswp X28 X30 X29 X24") 
  tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"jmp __while_ud_fetched_kv_ptr_for_cache_66_condition") 
  tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"__while_ud_fetched_kv_ptr_for_cache_68_post: movir X26 1") 
  tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"__if_ud_fetched_kv_ptr_for_cache_65_post: yield_terminate") 
  
  # Writing code for event {self.ln_receiver_materialize_ret_ev_label}
  tranreceiver__receiver_materialize_kv_ret = efa.writeEvent('{self.ln_receiver_materialize_ret_ev_label}')
  tranreceiver__receiver_materialize_kv_ret.writeAction(f"entry: yield_terminate") 
  
  # Writing code for event {self.ln_receiver_update_unresolved_kv_count_ev_label}
  tranreceiver__receiver_update_unresolved_kv_count = efa.writeEvent('{self.ln_receiver_update_unresolved_kv_count_ev_label}')
  tranreceiver__receiver_update_unresolved_kv_count.writeAction(f"entry: yield_terminate") 
  
