from linker.EFAProgram import efaProgram

## Global constants

@efaProgram
def EFA_load_balancer_events(efa):
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
  ## Scoped Variable "start" uses Register X23, scope (0->1)
  ## Scoped Variable "next_change_stop" uses Register X24, scope (0->1)
  ## Scoped Variable "start_written_flag" uses Register X25, scope (0->1)
  ## Scoped Variable "end" uses Register X26, scope (0->1)
  ## Scoped Variable "tmp" uses Register X22, scope (0->1->3)
  ## Scoped Variable "tmp1" uses Register X23, scope (0->1->3)
  ## Scoped Variable "cswp_ret" uses Register X23, scope (0->1->6)
  ## Scoped Variable "tmp" uses Register X24, scope (0->1->6)
  ## Scoped Variable "tmp1" uses Register X25, scope (0->1->6)
  ## Scoped Variable "tmp" uses Register X27, scope (0->1->14)
  ## Scoped Variable "tmp1" uses Register X28, scope (0->1->14)
  ## Scoped Variable "first_entry_sent" uses Register X27, scope (0->1->16)
  ## Scoped Variable "tmp" uses Register X28, scope (0->1->16->18->20)
  ## Scoped Variable "cswp_ret" uses Register X29, scope (0->1->16->18->20->22->25)
  ## Scoped Variable "tmp1" uses Register X30, scope (0->1->16->18->20->22->25)
  ## Scoped Variable "dest" uses Register X29, scope (0->1->16->18->20->27)
  ## Scoped Variable "cswp_ret" uses Register X30, scope (0->1->16->18->20->27->34)
  ## Scoped Variable "tmp1" uses Register X31, scope (0->1->16->18->20->27->34)
  ## Scoped Variable "dest" uses Register X27, scope (0->1->43)
  ## Scoped Variable "tmp" uses Register X28, scope (0->1->43->46->48)
  ## Scoped Variable "cswp_ret" uses Register X29, scope (0->1->43->46->48->50->53)
  ## Scoped Variable "tmp1" uses Register X30, scope (0->1->43->46->48->50->53)
  ## Scoped Variable "cswp_ret" uses Register X27, scope (0->1->65)
  ## Scoped Variable "tmp" uses Register X28, scope (0->1->65)
  ## Param "dram_addr" uses Register X8, scope (0->67)
  ## Param "tmp" uses Register X8, scope (0->68)
  
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
  tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"movir X27 {self.intermediate_ptr_offset}") 
  tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"add X19 X27 X20") 
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
  tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"movlr 0(X21) X22 0 8") 
  tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"sari X22 X16 1") 
  ## Read num and dest
  tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"__if_ud_fetched_kv_ptr_for_cache_3_true: movir X24 -1") 
  tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"movir X25 0") 
  tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"addi X21 X20 8") 
  tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"cswp X20 X23 X24 X8") 
  tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"bne X23 X24 __if_ud_fetched_kv_ptr_for_cache_7_false") 
  ## Set num first
  tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"__if_ud_fetched_kv_ptr_for_cache_6_true: addi X21 X20 16") 
  tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"reset_num: movlr 0(X20) X22 0 8") 
  tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"movlr -8(X20) X24 0 8") 
  tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"bne X24 X8 key_got_claimed") 
  tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"cswp X20 X23 X22 X25") 
  tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"bne X23 X22 reset_num") 
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
  # tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"") 
  # tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"evi X2 X18 {self.ln_receiver_materialize_ret_ev_label} 1") 
  # tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"movir X17 0") 
  tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"jmp __if_ud_fetched_kv_ptr_for_cache_8_post") 
  tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"__if_ud_fetched_kv_ptr_for_cache_7_false: evi X2 X18 {self.ln_receiver_update_unresolved_kv_count_ev_label} 1") 
  tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"movir X17 1") 
  tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"__if_ud_fetched_kv_ptr_for_cache_8_post: evi X18 X18 255 4") 
  ## // Resume returned key
  ## returned_key = returned_key >> 1;
  tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"print 'Lane %u received kv_ptr for key %ld with bin address %lu(0x%lx), entry address %lu' X0 X16 X8 X8 X21") 
  ## Read materialize_kv_cache metadata
  ## Locate start of materialize_kv_cache
  tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"movir X27 {self.materializing_metadata_offset}") 
  tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"add X19 X27 X20") 
  tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"movlr 0(X20) X23 0 8") 
  tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"movir X27 {self.materialize_kv_cache_count}") 
  tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"div X23 X27 X25") 
  tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"addi X25 X26 1") 
  tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"movir X27 {self.materialize_kv_cache_count}") 
  tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"mul X26 X27 X24") 
  tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"movir X25 0") 
  ## long tmp = ((start / materialize_kv_cache_count) % 64) << 16;
  ## long tmp1 = (start % materialize_kv_cache_count) * inter_kvpair_size * 8;
  ## tmp = base_ptr + tmp + materialize_kv_cache_offset;
  ## ptr = tmp + tmp1;
  tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"__if_ud_fetched_kv_ptr_for_cache_9_true: movir X29 {self.materialize_kv_cache_count}") 
  tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"div X23 X29 X27") 
  tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"andi X27 X27 63") 
  tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"sli X27 X27 16") 
  tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"movir X29 {self.materialize_kv_cache_offset}") 
  tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"add X27 X29 X27") 
  tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"add X27 X19 X27") 
  tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"movir X29 {self.materialize_kv_cache_count}") 
  tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"mod X23 X29 X28") 
  tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"muli X28 X28 {self.inter_kvpair_size}") 
  tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"sli X28 X28 3") 
  tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"movlr 8(X20) X26 0 8") 
  tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"add X27 X28 X20") 
  tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"bneiu X17 0 __if_ud_fetched_kv_ptr_for_cache_14_post") 
  ## Move entry_ptr to the materialized count word, for cswp
  tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"__if_ud_fetched_kv_ptr_for_cache_12_true: addi X21 X21 16") 
  ## If not claimed, need to account for the first entry found
  tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"movir X27 0") 
  ## Iterate and update start until find an unmatch
  tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"__while_ud_fetched_kv_ptr_for_cache_15_condition: clt X23 X26 X28") 
  tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"clti X22 X29 0") 
  tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"and X28 X29 X30") 
  tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"beqi X30 0 __if_ud_fetched_kv_ptr_for_cache_14_post") 
  ## First check if entry empty
  tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"__while_ud_fetched_kv_ptr_for_cache_16_body: movlr 0(X20) X28 0 8") 
  tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"beqi X28 -1 __if_ud_fetched_kv_ptr_for_cache_20_post") 
  tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"__if_ud_fetched_kv_ptr_for_cache_18_true: movlr 0(X20) X28 0 8") 
  ## If not matched for the first time, write new start to spd
  tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"movlr 0(X20) X29 0 8") 
  tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"beq X29 X16 __if_ud_fetched_kv_ptr_for_cache_22_false") 
  tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"__if_ud_fetched_kv_ptr_for_cache_21_true: print 'Not matching: entry %ld reads %ld at %lu' X23 X28 X20") 
  tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"bneiu X25 0 __if_ud_fetched_kv_ptr_for_cache_26_post") 
  tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"__if_ud_fetched_kv_ptr_for_cache_24_true: movir X31 {self.materializing_metadata_offset}") 
  tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"add X19 X31 X25") 
  tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"update_materializing_start_not_matched: movlr 0(X25) X28 0 8") 
  tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"bge X28 X23 after_update_materializing_start_not_matched") 
  tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"cswp X25 X29 X28 X23") 
  tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"bne X29 X28 update_materializing_start_not_matched") 
  tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"after_update_materializing_start_not_matched: movir X25 1") 
  tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"__if_ud_fetched_kv_ptr_for_cache_26_post: jmp __if_ud_fetched_kv_ptr_for_cache_20_post") 
  tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"__if_ud_fetched_kv_ptr_for_cache_22_false: print 'Matched: entry %ld reads %ld at %lu' X23 X28 X20") 
  tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"addi X22 X22 1") 
  ## If matched, first check if key just got claimed
  ## is_claimed = entry_ptr[-2] & 1;
  tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"movlr -8(X21) X29 0 8") 
  tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"ceq X29 X8 X17") 
  tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"xori X17 X17 1") 
  tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"beqiu X17 0 __if_ud_fetched_kv_ptr_for_cache_33_true") 
  ## If just got claimed, wait till claimed dest evword is written
  tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"__if_ud_fetched_kv_ptr_for_cache_27_true: subi X21 X21 16") 
  tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"evi X2 X18 {self.ln_receiver_update_unresolved_kv_count_ev_label} 1") 
  tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"evi X18 X18 255 4") 
  tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"movlr 8(X21) X28 0 8") 
  tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"__while_ud_fetched_kv_ptr_for_cache_30_condition: bneu X28 X8 __while_ud_fetched_kv_ptr_for_cache_32_post") 
  tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"__while_ud_fetched_kv_ptr_for_cache_31_body: movlr 8(X21) X28 0 8") 
  tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"jmp __while_ud_fetched_kv_ptr_for_cache_30_condition") 
  tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"__while_ud_fetched_kv_ptr_for_cache_32_post: jmp __if_ud_fetched_kv_ptr_for_cache_14_post") 
  tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"__if_ud_fetched_kv_ptr_for_cache_33_true: update_materialized_count: movlr 0(X21) X28 0 8") 
  tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"addi X28 X31 1") 
  tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"cswp X21 X30 X28 X31") 
  tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"bne X30 X28 update_materialized_count") 
  tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"subi X31 X31 1") 
  tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"muli X30 X29 {self.inter_kvpair_size}") 
  tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"sli X29 X29 3") 
  tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"add X29 X8 X29") 
  tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"print 'receive_ptr materialize key %ld to Dram %lu(0x%lx) as the %ld-th kv' X16 X29 X29 X31") 
  ## Materialize the kv
  ## long* dest = cswp_ret * inter_kvpair_size * 8 + kv_arr_addr;
  tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"send_dmlm X29 X18 X20 {self.inter_kvpair_size}") 
  ## Erase this entry
  tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"movir X28 0") 
  tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"__for_ud_fetched_kv_ptr_for_cache_36_condition: bgeiu X28 {self.inter_kvpair_size} __if_ud_fetched_kv_ptr_for_cache_20_post") 
  tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"__for_ud_fetched_kv_ptr_for_cache_37_body: movir X31 -1") 
  tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"movwrl X31 X20(X28,0,0)") 
  tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"addi X28 X28 1") 
  tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"jmp __for_ud_fetched_kv_ptr_for_cache_36_condition") 
  ## Step forward one entry
  tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"__if_ud_fetched_kv_ptr_for_cache_20_post: addi X23 X23 1") 
  ## If going across lanes, update ptr
  tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"bneu X23 X24 __if_ud_fetched_kv_ptr_for_cache_40_false") 
  tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"__if_ud_fetched_kv_ptr_for_cache_39_true: movir X28 {self.materialize_kv_cache_count}") 
  tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"div X23 X28 X28") 
  tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"andi X28 X29 63") 
  tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"sli X29 X30 16") 
  tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"add X19 X30 X31") 
  tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"movir X28 {self.materialize_kv_cache_offset}") 
  tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"add X31 X28 X20") 
  tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"movir X28 {self.materialize_kv_cache_count}") 
  tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"add X24 X28 X24") 
  tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"jmp __if_ud_fetched_kv_ptr_for_cache_41_post") 
  ## If going inside lane, increment ptr
  tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"__if_ud_fetched_kv_ptr_for_cache_40_false: addi X20 X20 {self.inter_kvpair_size * WORD_SIZE}") 
  tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"__if_ud_fetched_kv_ptr_for_cache_41_post: jmp __while_ud_fetched_kv_ptr_for_cache_15_condition") 
  ## Iteration finished / key is claimed before iteration
  ## If iteration is interuppted, it means the key is just got claimed
  tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"__if_ud_fetched_kv_ptr_for_cache_14_post: clt X23 X26 X27") 
  tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"clti X22 X28 0") 
  tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"and X27 X28 X29") 
  tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"beqi X29 0 __if_ud_fetched_kv_ptr_for_cache_44_post") 
  tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"__if_ud_fetched_kv_ptr_for_cache_42_true: movlr 8(X21) X27 0 8") 
  tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"print 'Claimed dest event word for claimed key %ld: %lu' X16 X27") 
  ## // If claimed, need to account for number of total cached kvs
  ## unsigned long matched_count = 0;
  ## Iterate and update start until find an unmatch
  tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"__while_ud_fetched_kv_ptr_for_cache_45_condition: clt X23 X26 X28") 
  tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"clti X22 X29 0") 
  tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"and X28 X29 X30") 
  tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"beqi X30 0 __if_ud_fetched_kv_ptr_for_cache_44_post") 
  ## First check if entry empty
  tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"__while_ud_fetched_kv_ptr_for_cache_46_body: movlr 0(X20) X28 0 8") 
  tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"beqi X28 -1 __if_ud_fetched_kv_ptr_for_cache_50_post") 
  tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"__if_ud_fetched_kv_ptr_for_cache_48_true: movlr 0(X20) X28 0 8") 
  ## If not matched for the first time, write new start to spd
  tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"bequ X28 X16 __if_ud_fetched_kv_ptr_for_cache_52_false") 
  tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"__if_ud_fetched_kv_ptr_for_cache_51_true: print 'Not matching: entry %ld reads %ld at %lu' X23 X28 X20") 
  tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"bneiu X25 0 __if_ud_fetched_kv_ptr_for_cache_56_post") 
  tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"__if_ud_fetched_kv_ptr_for_cache_54_true: movir X31 {self.materializing_metadata_offset}") 
  tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"add X19 X31 X25") 
  tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"update_materializing_start_not_matched_claimed: movlr 0(X25) X28 0 8") 
  tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"bge X28 X23 after_update_materializing_start_claimed") 
  tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"cswp X25 X29 X28 X23") 
  tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"bne X29 X28 update_materializing_start_not_matched_claimed") 
  tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"after_update_materializing_start_claimed: movir X25 1") 
  tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"__if_ud_fetched_kv_ptr_for_cache_56_post: jmp __if_ud_fetched_kv_ptr_for_cache_50_post") 
  tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"__if_ud_fetched_kv_ptr_for_cache_52_false: print 'Matched: entry %ld reads %ld at %lu' X23 X28 X20") 
  ## If mached, send it to the claimed destination
  tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"addi X22 X22 1") 
  tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"send_wcont X27 X18 X20 {self.inter_kvpair_size}") 
  ## // Increment matched_count
  ## matched_count = matched_count + 1;
  ## Erase this entry
  tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"movir X28 0") 
  tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"__for_ud_fetched_kv_ptr_for_cache_57_condition: bgeiu X28 {self.inter_kvpair_size} __if_ud_fetched_kv_ptr_for_cache_50_post") 
  tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"__for_ud_fetched_kv_ptr_for_cache_58_body: movir X30 -1") 
  tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"movwrl X30 X20(X28,0,0)") 
  tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"addi X28 X28 1") 
  tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"jmp __for_ud_fetched_kv_ptr_for_cache_57_condition") 
  ## Step forward one entry
  tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"__if_ud_fetched_kv_ptr_for_cache_50_post: addi X23 X23 1") 
  ## If going across lanes, update ptr
  tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"bneu X23 X24 __if_ud_fetched_kv_ptr_for_cache_61_false") 
  tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"__if_ud_fetched_kv_ptr_for_cache_60_true: movir X28 {self.materialize_kv_cache_count}") 
  tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"div X23 X28 X28") 
  tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"andi X28 X29 63") 
  tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"sli X29 X30 16") 
  tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"add X19 X30 X31") 
  tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"movir X28 {self.materialize_kv_cache_offset}") 
  tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"add X31 X28 X20") 
  tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"movir X28 {self.materialize_kv_cache_count}") 
  tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"add X24 X28 X24") 
  tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"jmp __if_ud_fetched_kv_ptr_for_cache_62_post") 
  ## If going inside lane, increment ptr
  tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"__if_ud_fetched_kv_ptr_for_cache_61_false: addi X20 X20 {self.inter_kvpair_size * WORD_SIZE}") 
  tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"__if_ud_fetched_kv_ptr_for_cache_62_post: jmp __while_ud_fetched_kv_ptr_for_cache_45_condition") 
  ## Write new start to spd if haven't
  tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"__if_ud_fetched_kv_ptr_for_cache_44_post: bneiu X25 0 __if_ud_fetched_kv_ptr_for_cache_65_post") 
  tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"__if_ud_fetched_kv_ptr_for_cache_63_true: movir X29 {self.materializing_metadata_offset}") 
  tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"add X19 X29 X20") 
  tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"update_materializing_start: movlr 0(X20) X28 0 8") 
  tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"bge X28 X23 after_update_materializing_start") 
  tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"cswp X20 X27 X28 X23") 
  tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"bne X27 X28 update_materializing_start") 
  tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"after_update_materializing_start: movir X25 1") 
  tranreceiver__ud_fetched_kv_ptr_for_cache.writeAction(f"__if_ud_fetched_kv_ptr_for_cache_65_post: yield_terminate") 
  
  # Writing code for event {self.ln_receiver_materialize_ret_ev_label}
  tranreceiver__receiver_materialize_kv_ret = efa.writeEvent('{self.ln_receiver_materialize_ret_ev_label}')
  tranreceiver__receiver_materialize_kv_ret.writeAction(f"entry: yield_terminate") 
  
  # Writing code for event {self.ln_receiver_update_unresolved_kv_count_ev_label}
  tranreceiver__receiver_update_unresolved_kv_count = efa.writeEvent('{self.ln_receiver_update_unresolved_kv_count_ev_label}')
  tranreceiver__receiver_update_unresolved_kv_count.writeAction(f"entry: yield_terminate") 
  
