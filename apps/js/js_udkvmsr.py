from linker.EFAProgram import efaProgram

## Global constants

@efaProgram
def EFA_js(efa):
  efa.code_level = 'machine'
  state0 = efa.State("udweave_init") #Only one state code 
  efa.add_initId(state0.state_id)
  ## Static declarations
  ## Scoped Variable "v1" uses Register X16, scope (0)
  ## Scoped Variable "v1_deg" uses Register X17, scope (0)
  ## Scoped Variable "v1_nl" uses Register X18, scope (0)
  ## Scoped Variable "v2" uses Register X19, scope (0)
  ## Scoped Variable "v2_deg" uses Register X20, scope (0)
  ## Scoped Variable "v2_nl" uses Register X21, scope (0)
  ## Scoped Variable "threashold" uses Register X22, scope (0)
  ## Scoped Variable "read_count" uses Register X23, scope (0)
  ## Scoped Variable "cached_nb" uses Register X24, scope (0)
  ## Scoped Variable "saved_cont" uses Register X25, scope (0)
  ## Param "v1_id" uses Register X8, scope (0->9)
  ## Param "v2_id" uses Register X9, scope (0->9)
  ## Param "intersect_count" uses Register X10, scope (0->9)
  ## Scoped Variable "ptr" uses Register X25, scope (0->9)
  ## Scoped Variable "graph" uses Register X26, scope (0->9)
  ## Param "id" uses Register X8, scope (0->10)
  ## Param "degree" uses Register X9, scope (0->10)
  ## Param "nb_list" uses Register X10, scope (0->10)
  ## Scoped Variable "ptr" uses Register X25, scope (0->10)
  ## Scoped Variable "graph" uses Register X26, scope (0->10)
  ## Scoped Variable "graph_size" uses Register X27, scope (0->10)
  ## Scoped Variable "v1_pair_count" uses Register X28, scope (0->10)
  ## Scoped Variable "ev_word" uses Register X29, scope (0->10->18->20)
  ## Param "id" uses Register X8, scope (0->22)
  ## Param "degree" uses Register X9, scope (0->22)
  ## Param "nb_list" uses Register X10, scope (0->22)
  ## Param "v2_addr" uses Register X11, scope (0->22)
  ## Scoped Variable "ev_word" uses Register X25, scope (0->22->24)
  ## Scoped Variable "key" uses Register X26, scope (0->22->24)
  ## Scoped Variable "send_buffer" uses Register X27, scope (0->22->24)
  ## Scoped Variable "ev_word" uses Register X25, scope (0->22->26->28)
  ## Scoped Variable "ptr" uses Register X25, scope (0->22->26->29)
  ## Scoped Variable "graph" uses Register X26, scope (0->22->26->29)
  ## Param "v2_v1" uses Register X8, scope (0->30)
  ## Param "v1_degree" uses Register X9, scope (0->30)
  ## Param "v1_nb_list" uses Register X10, scope (0->30)
  ## Param "v2_degree" uses Register X11, scope (0->30)
  ## Param "v2_nb_list" uses Register X12, scope (0->30)
  ## Scoped Variable "ev_word" uses Register X26, scope (0->30)
  ## Scoped Variable "ptr" uses Register X27, scope (0->30)
  ## Scoped Variable "tmp" uses Register X28, scope (0->30)
  ## Param "addr" uses Register X8, scope (0->31)
  ## Param "status" uses Register X9, scope (0->31)
  ## Scoped Variable "ev_word" uses Register X26, scope (0->31)
  ## Scoped Variable "v1" uses Register X16, scope (0)
  ## Scoped Variable "v2" uses Register X17, scope (0)
  ## Scoped Variable "loc_js" uses Register X18, scope (0)
  ## Scoped Variable "read_count" uses Register X19, scope (0)
  ## Scoped Variable "cached_nb" uses Register X20, scope (0)
  ## Param "v1_id" uses Register X8, scope (0->33)
  ## Param "v2_id" uses Register X9, scope (0->33)
  ## Param "spmalloc_ptr" uses Register X10, scope (0->33)
  ## Scoped Variable "v1_nl" uses Register X21, scope (0->33)
  ## Scoped Variable "v2_nl" uses Register X22, scope (0->33)
  ## Param "op0" uses Register X8, scope (0->34)
  ## Param "op1" uses Register X9, scope (0->34)
  ## Param "op2" uses Register X10, scope (0->34)
  ## Param "op3" uses Register X11, scope (0->34)
  ## Param "op4" uses Register X12, scope (0->34)
  ## Param "op5" uses Register X13, scope (0->34)
  ## Param "op6" uses Register X14, scope (0->34)
  ## Param "op7" uses Register X15, scope (0->34)
  ## Scoped Variable "ptr" uses Register X21, scope (0->34)
  ## Scoped Variable "ev_word" uses Register X22, scope (0->34->36)
  ## Param "op0" uses Register X8, scope (0->37)
  ## Param "op1" uses Register X9, scope (0->37)
  ## Param "op2" uses Register X10, scope (0->37)
  ## Param "op3" uses Register X11, scope (0->37)
  ## Param "op4" uses Register X12, scope (0->37)
  ## Param "op5" uses Register X13, scope (0->37)
  ## Param "op6" uses Register X14, scope (0->37)
  ## Param "op7" uses Register X15, scope (0->37)
  ## Scoped Variable "ptr" uses Register X21, scope (0->37)
  ## Scoped Variable "ev_word" uses Register X22, scope (0->37->39)
  ## Scoped Variable "offs_a" uses Register X21, scope (0->40)
  ## Scoped Variable "offs_b" uses Register X22, scope (0->40)
  ## Scoped Variable "loc_size_a" uses Register X23, scope (0->40)
  ## Scoped Variable "loc_size_b" uses Register X24, scope (0->40)
  ## Scoped Variable "iter_a" uses Register X25, scope (0->40)
  ## Scoped Variable "iter_b" uses Register X26, scope (0->40)
  ## Scoped Variable "rem" uses Register X25, scope (0->40->42)
  ## Scoped Variable "ptr" uses Register X25, scope (0->40->50)
  ## Scoped Variable "elem_a" uses Register X26, scope (0->40->50->52)
  ## Scoped Variable "elem_b" uses Register X27, scope (0->40->50->52)
  ## Scoped Variable "ev_word" uses Register X26, scope (0->40->59->61)
  ## Scoped Variable "ev_word" uses Register X27, scope (0->40->63->65)
  ## Scoped Variable "addr" uses Register X27, scope (0->40->67)
  ## Scoped Variable "addr" uses Register X27, scope (0->40->69)
  ## Scoped Variable "ev_word" uses Register X21, scope (0->70)
  ## Scoped Variable "cont_word" uses Register X22, scope (0->70)
  ## Scoped Variable "v1_deg" uses Register X21, scope (0->70->72)
  ## Scoped Variable "v2_deg" uses Register X22, scope (0->70->72)
  ## Scoped Variable "tmp0" uses Register X23, scope (0->70->72)
  ## Scoped Variable "tmp1" uses Register X24, scope (0->70->72)
  ## Scoped Variable "js_entry" uses Register X25, scope (0->70->72)
  ## Scoped Variable "ptr" uses Register X26, scope (0->70->72)
  ## Scoped Variable "cached_num_lanes" uses Register X16, scope (0)
  ## Param "partitions" uses Register X8, scope (0->75)
  ## Param "partition_per_lane" uses Register X9, scope (0->75)
  ## Param "num_lanes" uses Register X10, scope (0->75)
  ## Param "input" uses Register X11, scope (0->75)
  ## Param "input_size" uses Register X12, scope (0->75)
  ## Param "graph" uses Register X13, scope (0->75)
  ## Param "v_count" uses Register X14, scope (0->75)
  ## Param "intermediate_hashmap" uses Register X15, scope (0->75)
  ## Scoped Variable "send_buffer" uses Register X17, scope (0->75)
  ## Scoped Variable "heap" uses Register X18, scope (0->75)
  ## Scoped Variable "ev_word" uses Register X19, scope (0->75)
  ## Scoped Variable "tmp_ev_word" uses Register X20, scope (0->75)
  ## Param "num_reduce" uses Register X8, scope (0->76)
  ## Scoped Variable "ptr" uses Register X17, scope (0->76)
  ## Param "js_count" uses Register X8, scope (0->78)
  ## Scoped Variable "ptr" uses Register X17, scope (0->78)
  ## Param "graph" uses Register X8, scope (0->81)
  ## Param "v_count" uses Register X9, scope (0->81)
  ## Scoped Variable "ptr" uses Register X16, scope (0->81)
  ## #include "LMStaticMap.udwh"
  ## #define SEND_ALL_MAP_READ
  ## #define PRINT_EDGE_RESULT
  
  EXTENSION = 'load_balancer'
  DEBUG_FLAG = False
  LB_TYPE = ['mapper','reducer']
  test_ws = False
  test_random = True
  rtype = 'lane' if test_ws else 'ud'
  multi = not test_ws
  map_ws = test_ws
  red_ws = test_ws
  
  from libraries.UDMapShuffleReduce.linkable.LinkableKVMapShuffleCombineTPL import UDKeyValueMapShuffleReduceTemplate
  from libraries.UDMapShuffleReduce.utils.OneDimArrayKeyValueSet import OneDimKeyValueSet
  from libraries.UDMapShuffleReduce.utils.IntermediateKeyValueSet import IntermediateKeyValueSet
  from LinkableGlobalSync import Broadcast, GlobalSync
  from SpMalloc import SpMallocEFA
  from libraries.LMStaticMaps.LMStaticMap import UDKVMSR_0_OFFSET
  
  spmalloc = SpMallocEFA(efa, state0 = state0, init_offset = 21464, debug=False)
  broadcast = Broadcast(state = state0, identifier='js_broadcast')
  
  task_name = 'js'
  jsMSR = UDKeyValueMapShuffleReduceTemplate(efa=efa, task_name=task_name, meta_data_offset=UDKVMSR_0_OFFSET, debug_flag=DEBUG_FLAG,
  extension = EXTENSION, load_balancer_type = LB_TYPE, grlb_type = rtype,
  claim_multiple_work = multi, test_map_ws=map_ws, test_reduce_ws=red_ws, random_lb=test_random, do_all_reduce = True)
  jsMSR.set_input_kvset(OneDimKeyValueSet('js_input', element_size=3, bypass_gen_partition=True) )
  jsMSR.set_intermediate_kvset(IntermediateKeyValueSet('js_intermediate', key_size=1, value_size=4))
  jsMSR.set_max_thread_per_lane(max_map_th_per_lane=64, max_reduce_th_per_lane=128, max_reduce_key_to_claim = 256)
  jsMSR.setup_lb_cache(intermediate_cache_num_bins = 16, intermediate_cache_size = 512, materialize_kv_cache_size = 512, materialize_kv_dram_size = 1<<24)
  print(jsMSR.heap_offset)
  
  jsMSR.generate_udkvmsr_task()
  
  
  
  ########################################
  ###### Writing code for thread js ######
  ########################################
  # Writing code for event js::kv_map
  tranjs__kv_map = efa.writeEvent('js::kv_map')
  ## Cache info
  tranjs__kv_map.writeAction(f"entry: addi X8 X16 0") 
  tranjs__kv_map.writeAction(f"addi X9 X19 0") 
  tranjs__kv_map.writeAction(f"addi X10 X22 0") 
  ## Read cached graph info
  tranjs__kv_map.writeAction(f"addi X7 X25 21440") 
  tranjs__kv_map.writeAction(f"movlr 0(X25) X26 0 8") 
  ## print("v1: %lu, v2: %lu, intersect_count: %lu, graph address: %lu, from spd %lu", v1_id, v2_id, intersect_count, graph, ptr);
  ## Init read counts
  tranjs__kv_map.writeAction(f"movir X23 0") 
  ## Read first v1 assigned
  tranjs__kv_map.writeAction(f"sli X8 X27 6") 
  tranjs__kv_map.writeAction(f"add X26 X27 X26") 
  tranjs__kv_map.writeAction(f"send_dmlm_ld_wret X26 js::map_v1_read_ret 3 X27") 
  tranjs__kv_map.writeAction(f"yield") 
  
  # Writing code for event js::map_v1_read_ret
  tranjs__map_v1_read_ret = efa.writeEvent('js::map_v1_read_ret')
  ## Read cached graph info
  tranjs__map_v1_read_ret.writeAction(f"entry: addi X7 X25 21440") 
  tranjs__map_v1_read_ret.writeAction(f"movlr 0(X25) X26 0 8") 
  tranjs__map_v1_read_ret.writeAction(f"addi X7 X25 21448") 
  tranjs__map_v1_read_ret.writeAction(f"movlr 0(X25) X27 0 8") 
  ## Calculate the number of v2 to read
  tranjs__map_v1_read_ret.writeAction(f"sub X27 X19 X28") 
  tranjs__map_v1_read_ret.writeAction(f"bgtu X22 X28 __if_map_v1_read_ret_2_post") 
  tranjs__map_v1_read_ret.writeAction(f"__if_map_v1_read_ret_0_true: addi X22 X28 0") 
  ## print("Map v1 %lu, v2 %lu, read_count %lu, v1_pair_count %lu, start v2 %lu, graph %lu, graph_size %lu", v1, v2, read_count, v1_pair_count, v2, graph, graph_size);
  ## If v1 degree > 0, read all asigned v2
  tranjs__map_v1_read_ret.writeAction(f"__if_map_v1_read_ret_2_post: bleiu X9 0 __if_map_v1_read_ret_5_post") 
  tranjs__map_v1_read_ret.writeAction(f"__if_map_v1_read_ret_3_true: addi X9 X17 0") 
  tranjs__map_v1_read_ret.writeAction(f"addi X10 X18 0") 
  tranjs__map_v1_read_ret.writeAction(f"sli X19 X29 6") 
  tranjs__map_v1_read_ret.writeAction(f"add X26 X29 X26") 
  tranjs__map_v1_read_ret.writeAction(f"__while_map_v1_read_ret_6_condition: bleu X28 X23 __if_map_v1_read_ret_5_post") 
  ## if (1) {
  ##     unsigned long tmp = v2 + read_count;
  ##     print("Send dram read v2 %lu from %lu, v1 %lu, read_count %lu, v1_pair_count %lu, start v2 %lu, graph_size %lu", tmp, graph, v1, read_count, v1_pair_count, v2, graph_size);
  ## }
  tranjs__map_v1_read_ret.writeAction(f"__while_map_v1_read_ret_7_body: send_dmlm_ld_wret X26 js::map_v2_read_ret 3 X29") 
  tranjs__map_v1_read_ret.writeAction(f"addi X26 X26 64") 
  tranjs__map_v1_read_ret.writeAction(f"addi X23 X23 1") 
  tranjs__map_v1_read_ret.writeAction(f"jmp __while_map_v1_read_ret_6_condition") 
  ## Update counter
  tranjs__map_v1_read_ret.writeAction(f"__if_map_v1_read_ret_5_post: sub X22 X28 X22") 
  ## If degree == 0, check if cheaching end
  tranjs__map_v1_read_ret.writeAction(f"bneiu X23 0 __if_map_v1_read_ret_11_post") 
  tranjs__map_v1_read_ret.writeAction(f"__if_map_v1_read_ret_9_true: bneiu X22 0 __if_map_v1_read_ret_13_false") 
  ## If reach end, return to  tc__kv_map_return
  tranjs__map_v1_read_ret.writeAction(f"__if_map_v1_read_ret_12_true: evi X2 X29 js__kv_map_return 1") 
  tranjs__map_v1_read_ret.writeAction(f"movir X30 -1") 
  tranjs__map_v1_read_ret.writeAction(f"sri X30 X30 1") 
  tranjs__map_v1_read_ret.writeAction(f"sendr_wcont X29 X30 X16 X19") 
  tranjs__map_v1_read_ret.writeAction(f"jmp __if_map_v1_read_ret_11_post") 
  ## Otherwise, read another v1
  tranjs__map_v1_read_ret.writeAction(f"__if_map_v1_read_ret_13_false: addi X16 X16 1") 
  tranjs__map_v1_read_ret.writeAction(f"addi X16 X19 1") 
  tranjs__map_v1_read_ret.writeAction(f"sli X16 X29 6") 
  tranjs__map_v1_read_ret.writeAction(f"add X26 X29 X26") 
  tranjs__map_v1_read_ret.writeAction(f"send_dmlm_ld_wret X26 js::map_v1_read_ret 3 X29") 
  tranjs__map_v1_read_ret.writeAction(f"__if_map_v1_read_ret_11_post: yield") 
  
  # Writing code for event js::map_v2_read_ret
  tranjs__map_v2_read_ret = efa.writeEvent('js::map_v2_read_ret')
  tranjs__map_v2_read_ret.writeAction(f"entry: subi X23 X23 1") 
  ## If v2 degree > 0, send to reduce
  tranjs__map_v2_read_ret.writeAction(f"bleiu X9 0 __if_map_v2_read_ret_2_post") 
  ## print("Dram read v2 %lu, v2_deg %lu, v2_nl %lu, dram addr %lu", id, degree, nb_list, v2_addr);
  tranjs__map_v2_read_ret.writeAction(f"__if_map_v2_read_ret_0_true: movir X25 0") 
  tranjs__map_v2_read_ret.writeAction(f"evlb X25 js__kv_map_emit") 
  tranjs__map_v2_read_ret.writeAction(f"evi X25 X25 255 4") 
  tranjs__map_v2_read_ret.writeAction(f"ev X25 X25 X0 X0 8") 
  tranjs__map_v2_read_ret.writeAction(f"sli X8 X27 32") 
  tranjs__map_v2_read_ret.writeAction(f"or X27 X16 X26") 
  tranjs__map_v2_read_ret.writeAction(f"addi X7 X27 704") 
  tranjs__map_v2_read_ret.writeAction(f"movrl X26 0(X27) 0 8") 
  tranjs__map_v2_read_ret.writeAction(f"movrl X17 8(X27) 0 8") 
  tranjs__map_v2_read_ret.writeAction(f"movrl X18 16(X27) 0 8") 
  tranjs__map_v2_read_ret.writeAction(f"movrl X9 24(X27) 0 8") 
  tranjs__map_v2_read_ret.writeAction(f"movrl X10 32(X27) 0 8") 
  tranjs__map_v2_read_ret.writeAction(f"movir X28 -1") 
  tranjs__map_v2_read_ret.writeAction(f"sri X28 X28 1") 
  tranjs__map_v2_read_ret.writeAction(f"send_wcont X25 X28 X27 5") 
  ## If all v2 read returns, check if reaching end
  tranjs__map_v2_read_ret.writeAction(f"__if_map_v2_read_ret_2_post: bneiu X23 0 __if_map_v2_read_ret_5_post") 
  tranjs__map_v2_read_ret.writeAction(f"__if_map_v2_read_ret_3_true: bneiu X22 0 __if_map_v2_read_ret_7_false") 
  ## If reach end, return to  tc__kv_map_return
  tranjs__map_v2_read_ret.writeAction(f"__if_map_v2_read_ret_6_true: evi X2 X25 js__kv_map_return 1") 
  tranjs__map_v2_read_ret.writeAction(f"movir X26 -1") 
  tranjs__map_v2_read_ret.writeAction(f"sri X26 X26 1") 
  tranjs__map_v2_read_ret.writeAction(f"sendr_wcont X25 X26 X16 X19") 
  tranjs__map_v2_read_ret.writeAction(f"jmp __if_map_v2_read_ret_5_post") 
  ## Otherwise, read another v1
  tranjs__map_v2_read_ret.writeAction(f"__if_map_v2_read_ret_7_false: addi X16 X16 1") 
  tranjs__map_v2_read_ret.writeAction(f"addi X16 X19 1") 
  ## Read cached graph info
  tranjs__map_v2_read_ret.writeAction(f"addi X7 X25 21440") 
  tranjs__map_v2_read_ret.writeAction(f"movlr 0(X25) X26 0 8") 
  tranjs__map_v2_read_ret.writeAction(f"sli X16 X27 6") 
  tranjs__map_v2_read_ret.writeAction(f"add X26 X27 X26") 
  tranjs__map_v2_read_ret.writeAction(f"send_dmlm_ld_wret X26 js::map_v1_read_ret 3 X27") 
  tranjs__map_v2_read_ret.writeAction(f"__if_map_v2_read_ret_5_post: yield") 
  
  # Writing code for event js::kv_reduce
  tranjs__kv_reduce = efa.writeEvent('js::kv_reduce')
  ## print("start reduce");
  tranjs__kv_reduce.writeAction(f"entry: addi X1 X25 0") 
  tranjs__kv_reduce.writeAction(f"sli X8 X26 32") 
  tranjs__kv_reduce.writeAction(f"sri X26 X16 32") 
  tranjs__kv_reduce.writeAction(f"addi X9 X17 0") 
  tranjs__kv_reduce.writeAction(f"addi X10 X18 0") 
  tranjs__kv_reduce.writeAction(f"sri X8 X19 32") 
  tranjs__kv_reduce.writeAction(f"addi X11 X20 0") 
  tranjs__kv_reduce.writeAction(f"addi X12 X21 0") 
  tranjs__kv_reduce.writeAction(f"movir X26 0") 
  tranjs__kv_reduce.writeAction(f"evlb X26 lm_allocator__spmalloc") 
  tranjs__kv_reduce.writeAction(f"evi X26 X26 255 4") 
  tranjs__kv_reduce.writeAction(f"ev X26 X26 X0 X0 8") 
  tranjs__kv_reduce.writeAction(f"movir X29 24") 
  tranjs__kv_reduce.writeAction(f"sendr_wret X26 js::sp_malloc_ret X29 X29 X30") 
  tranjs__kv_reduce.writeAction(f"addi X7 X27 21464") 
  tranjs__kv_reduce.writeAction(f"movlr 0(X27) X28 0 8") 
  ## print("Reduce v1 %lu, v1_deg %lu, v1_nl %lu, v2 %lu, v2_deg %lu, v2_nl %lu, cont_word 0x%lx, metadata %lu, X7 %lu", v1, v1_deg, v1_nl, v2, v2_deg, v2_nl, saved_cont, tmp, LMBASE);
  tranjs__kv_reduce.writeAction(f"yield") 
  
  # Writing code for event js::sp_malloc_ret
  tranjs__sp_malloc_ret = efa.writeEvent('js::sp_malloc_ret')
  tranjs__sp_malloc_ret.writeAction(f"entry: addi X8 X24 0") 
  tranjs__sp_malloc_ret.writeAction(f"movrl X17 0(X24) 0 8") 
  tranjs__sp_malloc_ret.writeAction(f"movrl X18 8(X24) 0 8") 
  tranjs__sp_malloc_ret.writeAction(f"movir X27 0") 
  tranjs__sp_malloc_ret.writeAction(f"movrl X27 16(X24) 0 8") 
  tranjs__sp_malloc_ret.writeAction(f"movir X27 0") 
  tranjs__sp_malloc_ret.writeAction(f"movrl X27 24(X24) 0 8") 
  tranjs__sp_malloc_ret.writeAction(f"movrl X20 32(X24) 0 8") 
  tranjs__sp_malloc_ret.writeAction(f"movrl X21 40(X24) 0 8") 
  tranjs__sp_malloc_ret.writeAction(f"movir X27 0") 
  tranjs__sp_malloc_ret.writeAction(f"movrl X27 48(X24) 0 8") 
  tranjs__sp_malloc_ret.writeAction(f"movir X27 0") 
  tranjs__sp_malloc_ret.writeAction(f"movrl X27 56(X24) 0 8") 
  ## print("Write v1_nl %lu, v2_nl %lu at %lu", v1_nl, v2_nl, addr);
  tranjs__sp_malloc_ret.writeAction(f"evi X2 X26 js_compute::setup_thread_reg 1") 
  tranjs__sp_malloc_ret.writeAction(f"sendr3_wcont X26 X25 X16 X19 X24") 
  tranjs__sp_malloc_ret.writeAction(f"yield") 
  
  
  ################################################
  ###### Writing code for thread js_compute ######
  ################################################
  ## cache_nb = || v1_deg || v1_nb_list || iter_a || offs_a || v2_deg || v2_nb_list || iter_b || offs_b ||
  ## index      || 0      || 1          || 2      || 3      || 4      || 5          || 6      || 7      ||
  # Writing code for event js_compute::setup_thread_reg
  tranjs_compute__setup_thread_reg = efa.writeEvent('js_compute::setup_thread_reg')
  tranjs_compute__setup_thread_reg.writeAction(f"entry: addi X8 X16 0") 
  tranjs_compute__setup_thread_reg.writeAction(f"addi X9 X17 0") 
  tranjs_compute__setup_thread_reg.writeAction(f"movir X18 0") 
  tranjs_compute__setup_thread_reg.writeAction(f"movir X19 0") 
  tranjs_compute__setup_thread_reg.writeAction(f"addi X10 X20 0") 
  tranjs_compute__setup_thread_reg.writeAction(f"movlr 8(X20) X21 0 8") 
  tranjs_compute__setup_thread_reg.writeAction(f"movlr 40(X20) X22 0 8") 
  ## print("Read v1_nl %lu, v2_nl %lu from %lu", v1_nl, v2_nl, cached_nb);
  tranjs_compute__setup_thread_reg.writeAction(f"send_dmlm_ld_wret X21 js_compute::v1_nblist_read_ret 8 X23") 
  tranjs_compute__setup_thread_reg.writeAction(f"send_dmlm_ld_wret X22 js_compute::v2_nblist_read_ret 8 X23") 
  tranjs_compute__setup_thread_reg.writeAction(f"movir X19 2") 
  tranjs_compute__setup_thread_reg.writeAction(f"yield") 
  
  # Writing code for event js_compute::v1_nblist_read_ret
  tranjs_compute__v1_nblist_read_ret = efa.writeEvent('js_compute::v1_nblist_read_ret')
  ## print("v1_nblist_read_ret op0 %lu, op1 %lu, op2 %lu, op3 %lu, op4 %lu, op5 %lu, op6 %lu, op7 %lu", op0, op1, op2, op3, op4, op5, op6, op7);
  tranjs_compute__v1_nblist_read_ret.writeAction(f"entry: subi X19 X19 1") 
  tranjs_compute__v1_nblist_read_ret.writeAction(f"addi X20 X21 64") 
  tranjs_compute__v1_nblist_read_ret.writeAction(f"bcpyoli X8 X21 8") 
  tranjs_compute__v1_nblist_read_ret.writeAction(f"bneiu X19 0 __if_v1_nblist_read_ret_2_post") 
  tranjs_compute__v1_nblist_read_ret.writeAction(f"__if_v1_nblist_read_ret_0_true: evi X2 X22 js_compute::intersect_ab 1") 
  tranjs_compute__v1_nblist_read_ret.writeAction(f"sendr_wcont X22 X1 X16 X17") 
  tranjs_compute__v1_nblist_read_ret.writeAction(f"__if_v1_nblist_read_ret_2_post: yield") 
  
  # Writing code for event js_compute::v2_nblist_read_ret
  tranjs_compute__v2_nblist_read_ret = efa.writeEvent('js_compute::v2_nblist_read_ret')
  ## print("v2_nblist_read_ret op0 %lu, op1 %lu, op2 %lu, op3 %lu, op4 %lu, op5 %lu, op6 %lu, op7 %lu", op0, op1, op2, op3, op4, op5, op6, op7);
  tranjs_compute__v2_nblist_read_ret.writeAction(f"entry: subi X19 X19 1") 
  tranjs_compute__v2_nblist_read_ret.writeAction(f"addi X20 X21 128") 
  tranjs_compute__v2_nblist_read_ret.writeAction(f"bcpyoli X8 X21 8") 
  tranjs_compute__v2_nblist_read_ret.writeAction(f"bneiu X19 0 __if_v2_nblist_read_ret_2_post") 
  tranjs_compute__v2_nblist_read_ret.writeAction(f"__if_v2_nblist_read_ret_0_true: evi X2 X22 js_compute::intersect_ab 1") 
  tranjs_compute__v2_nblist_read_ret.writeAction(f"sendr_wcont X22 X1 X16 X17") 
  tranjs_compute__v2_nblist_read_ret.writeAction(f"__if_v2_nblist_read_ret_2_post: yield") 
  
  # Writing code for event js_compute::intersect_ab
  tranjs_compute__intersect_ab = efa.writeEvent('js_compute::intersect_ab')
  ## print("intersect_ab v1 %lu, v2 %lu, loc_js %lu", v1, v2, loc_js);
  tranjs_compute__intersect_ab.writeAction(f"entry: movlr 24(X20) X21 0 8") 
  tranjs_compute__intersect_ab.writeAction(f"movlr 56(X20) X22 0 8") 
  tranjs_compute__intersect_ab.writeAction(f"__if_intersect_ab_0_true: movlr 0(X20) X26 0 8") 
  tranjs_compute__intersect_ab.writeAction(f"movlr 16(X20) X27 0 8") 
  tranjs_compute__intersect_ab.writeAction(f"sub X26 X27 X25") 
  tranjs_compute__intersect_ab.writeAction(f"bleiu X25 8 __if_intersect_ab_4_false") 
  tranjs_compute__intersect_ab.writeAction(f"__if_intersect_ab_3_true: movir X23 8") 
  tranjs_compute__intersect_ab.writeAction(f"jmp __if_intersect_ab_5_post") 
  tranjs_compute__intersect_ab.writeAction(f"__if_intersect_ab_4_false: addi X25 X23 0") 
  tranjs_compute__intersect_ab.writeAction(f"__if_intersect_ab_5_post: movlr 32(X20) X26 0 8") 
  tranjs_compute__intersect_ab.writeAction(f"movlr 48(X20) X27 0 8") 
  tranjs_compute__intersect_ab.writeAction(f"sub X26 X27 X25") 
  tranjs_compute__intersect_ab.writeAction(f"bleiu X25 8 __if_intersect_ab_7_false") 
  tranjs_compute__intersect_ab.writeAction(f"__if_intersect_ab_6_true: movir X24 8") 
  tranjs_compute__intersect_ab.writeAction(f"jmp __if_intersect_ab_9_true") 
  tranjs_compute__intersect_ab.writeAction(f"__if_intersect_ab_7_false: addi X25 X24 0") 
  tranjs_compute__intersect_ab.writeAction(f"__if_intersect_ab_9_true: addi X20 X25 64") 
  ## Walk through the two lists simultaeously
  tranjs_compute__intersect_ab.writeAction(f"__while_intersect_ab_12_condition: clt X21 X23 X26") 
  tranjs_compute__intersect_ab.writeAction(f"clt X22 X24 X27") 
  tranjs_compute__intersect_ab.writeAction(f"and X26 X27 X28") 
  tranjs_compute__intersect_ab.writeAction(f"beqiu X28 0 __while_intersect_ab_14_post") 
  tranjs_compute__intersect_ab.writeAction(f"__while_intersect_ab_13_body: movwlr X25(X21,0,0) X26") 
  tranjs_compute__intersect_ab.writeAction(f"addi X22 X28 8") 
  tranjs_compute__intersect_ab.writeAction(f"movwlr X25(X28,0,0) X27") 
  tranjs_compute__intersect_ab.writeAction(f"ble X27 X26 __if_intersect_ab_16_false") 
  tranjs_compute__intersect_ab.writeAction(f"__if_intersect_ab_15_true: addi X21 X21 1") 
  tranjs_compute__intersect_ab.writeAction(f"jmp __if_intersect_ab_17_post") 
  tranjs_compute__intersect_ab.writeAction(f"__if_intersect_ab_16_false: ble X26 X27 __if_intersect_ab_19_false") 
  tranjs_compute__intersect_ab.writeAction(f"__if_intersect_ab_18_true: addi X22 X22 1") 
  tranjs_compute__intersect_ab.writeAction(f"jmp __if_intersect_ab_17_post") 
  tranjs_compute__intersect_ab.writeAction(f"__if_intersect_ab_19_false: addi X18 X18 1") 
  tranjs_compute__intersect_ab.writeAction(f"addi X21 X21 1") 
  tranjs_compute__intersect_ab.writeAction(f"addi X22 X22 1") 
  tranjs_compute__intersect_ab.writeAction(f"__if_intersect_ab_17_post: jmp __while_intersect_ab_12_condition") 
  ## print("checkpoint 2");
  ## one or both the lists exited --> whichever did fejsh that
  ## update iter by how much ever was processed 
  ## check for bounds and fejsh
  ## retain offs of the other one 
  tranjs_compute__intersect_ab.writeAction(f"__while_intersect_ab_14_post: movlr 16(X20) X25 0 8") 
  tranjs_compute__intersect_ab.writeAction(f"bneu X21 X23 __if_intersect_ab_23_post") 
  tranjs_compute__intersect_ab.writeAction(f"__if_intersect_ab_21_true: add X25 X23 X25") 
  tranjs_compute__intersect_ab.writeAction(f"movlr 0(X20) X26 0 8") 
  tranjs_compute__intersect_ab.writeAction(f"bgtu X26 X25 __if_intersect_ab_23_post") 
  tranjs_compute__intersect_ab.writeAction(f"__if_intersect_ab_24_true: evi X2 X26 js_compute::intersect_term 1") 
  tranjs_compute__intersect_ab.writeAction(f"sendr_wcont X26 X1 X16 X17") 
  ## print("yield 1");
  tranjs_compute__intersect_ab.writeAction(f"yield") 
  tranjs_compute__intersect_ab.writeAction(f"__if_intersect_ab_23_post: movlr 48(X20) X26 0 8") 
  tranjs_compute__intersect_ab.writeAction(f"bneu X22 X24 __if_intersect_ab_29_post") 
  tranjs_compute__intersect_ab.writeAction(f"__if_intersect_ab_27_true: add X26 X24 X26") 
  tranjs_compute__intersect_ab.writeAction(f"movlr 32(X20) X27 0 8") 
  tranjs_compute__intersect_ab.writeAction(f"bgtu X27 X26 __if_intersect_ab_29_post") 
  tranjs_compute__intersect_ab.writeAction(f"__if_intersect_ab_30_true: evi X2 X27 js_compute::intersect_term 1") 
  tranjs_compute__intersect_ab.writeAction(f"sendr_wcont X27 X1 X16 X17") 
  ## print("yield 2");
  tranjs_compute__intersect_ab.writeAction(f"yield") 
  ## print("checkpoint 3");
  ## If neither lists end yet, read the list that exited
  tranjs_compute__intersect_ab.writeAction(f"__if_intersect_ab_29_post: bneu X21 X23 __if_intersect_ab_35_post") 
  tranjs_compute__intersect_ab.writeAction(f"__if_intersect_ab_33_true: movlr 8(X20) X28 0 8") 
  tranjs_compute__intersect_ab.writeAction(f"sli X25 X29 3") 
  tranjs_compute__intersect_ab.writeAction(f"add X28 X29 X27") 
  tranjs_compute__intersect_ab.writeAction(f"send_dmlm_ld_wret X27 js_compute::v1_nblist_read_ret 8 X28") 
  tranjs_compute__intersect_ab.writeAction(f"movir X21 0") 
  tranjs_compute__intersect_ab.writeAction(f"addi X19 X19 1") 
  tranjs_compute__intersect_ab.writeAction(f"__if_intersect_ab_35_post: bneu X22 X24 __if_intersect_ab_38_post") 
  tranjs_compute__intersect_ab.writeAction(f"__if_intersect_ab_36_true: movlr 40(X20) X28 0 8") 
  tranjs_compute__intersect_ab.writeAction(f"sli X26 X29 3") 
  tranjs_compute__intersect_ab.writeAction(f"add X28 X29 X27") 
  tranjs_compute__intersect_ab.writeAction(f"send_dmlm_ld_wret X27 js_compute::v2_nblist_read_ret 8 X28") 
  tranjs_compute__intersect_ab.writeAction(f"movir X22 0") 
  tranjs_compute__intersect_ab.writeAction(f"addi X19 X19 1") 
  ## Cache iterators
  tranjs_compute__intersect_ab.writeAction(f"__if_intersect_ab_38_post: movrl X25 16(X20) 0 8") 
  tranjs_compute__intersect_ab.writeAction(f"movrl X21 24(X20) 0 8") 
  tranjs_compute__intersect_ab.writeAction(f"movrl X26 48(X20) 0 8") 
  tranjs_compute__intersect_ab.writeAction(f"movrl X22 56(X20) 0 8") 
  tranjs_compute__intersect_ab.writeAction(f"yield") 
  
  # Writing code for event js_compute::intersect_term
  tranjs_compute__intersect_term = efa.writeEvent('js_compute::intersect_term')
  ## If intersection count > 0, calculate js entry
  ## print("intersect_term v1 %lu, v2 %lu, loc_js %lu", v1, v2, loc_js);
  tranjs_compute__intersect_term.writeAction(f"entry: bleiu X18 0 __if_intersect_term_2_post") 
  tranjs_compute__intersect_term.writeAction(f"__if_intersect_term_0_true: movlr 0(X20) X21 0 8") 
  tranjs_compute__intersect_term.writeAction(f"movlr 32(X20) X22 0 8") 
  tranjs_compute__intersect_term.writeAction(f"fcnvt.i64.64 X18 X23")  # This is for casting. May be used later on
  tranjs_compute__intersect_term.writeAction(f"add X21 X22 X25") 
  tranjs_compute__intersect_term.writeAction(f"sub X25 X18 X26") 
  tranjs_compute__intersect_term.writeAction(f"fcnvt.i64.64 X26 X24")  # This is for casting. May be used later on
  tranjs_compute__intersect_term.writeAction(f"fdiv.64 X23 X24 X25") 
  tranjs_compute__intersect_term.writeAction(f"addi X7 X26 21456") 
  tranjs_compute__intersect_term.writeAction(f"movlr 0(X26) X28 0 8") 
  tranjs_compute__intersect_term.writeAction(f"addi X28 X29 1") 
  tranjs_compute__intersect_term.writeAction(f"movrl X29 0(X26) 0 8") 
  ## Spfree
  tranjs_compute__intersect_term.writeAction(f"__if_intersect_term_2_post: movir X21 0") 
  tranjs_compute__intersect_term.writeAction(f"evlb X21 lm_allocator__spfree") 
  tranjs_compute__intersect_term.writeAction(f"evi X21 X21 255 4") 
  tranjs_compute__intersect_term.writeAction(f"ev X21 X21 X0 X0 8") 
  tranjs_compute__intersect_term.writeAction(f"movir X22 0") 
  tranjs_compute__intersect_term.writeAction(f"evlb X22 js_compute::sp_free_ret") 
  tranjs_compute__intersect_term.writeAction(f"evi X22 X22 255 4") 
  tranjs_compute__intersect_term.writeAction(f"ev X22 X22 X0 X0 8") 
  tranjs_compute__intersect_term.writeAction(f"sendr_wcont X21 X22 X20 X20") 
  ## print("Reduce term: send spfree to 0x%lx, cont 0x%lx", ev_word, cont_word);
  ## Return to js__kv_reduce_return
  tranjs_compute__intersect_term.writeAction(f"evi X2 X21 js__kv_reduce_return 1") 
  tranjs_compute__intersect_term.writeAction(f"sendr_wcont X21 X1 X16 X17") 
  ## print("Reduce term: send js__kv_reduce_return to 0x%lx, cont 0x%lx", ev_word, CCONT);
  tranjs_compute__intersect_term.writeAction(f"yield") 
  
  # Writing code for event js_compute::sp_free_ret
  tranjs_compute__sp_free_ret = efa.writeEvent('js_compute::sp_free_ret')
  tranjs_compute__sp_free_ret.writeAction(f"entry: yield_terminate") 
  
  
  ##########################################
  ###### Writing code for thread main ######
  ##########################################
  # Writing code for event main::init
  tranmain__init = efa.writeEvent('main::init')
  tranmain__init.writeAction(f"entry: addi X7 X17 704") 
  tranmain__init.writeAction(f"addi X7 X18 21472") 
  tranmain__init.writeAction(f"movir X19 0") 
  tranmain__init.writeAction(f"evlb X19 js_broadcast__broadcast_global") 
  tranmain__init.writeAction(f"evi X19 X19 255 4") 
  tranmain__init.writeAction(f"ev X19 X19 X0 X0 8") 
  tranmain__init.writeAction(f"movir X20 0") 
  tranmain__init.writeAction(f"evlb X20 main_broadcast_init::setup_spd") 
  tranmain__init.writeAction(f"evi X20 X20 255 4") 
  tranmain__init.writeAction(f"ev X20 X20 X0 X0 8") 
  tranmain__init.writeAction(f"movrl X10 0(X17) 0 8") 
  tranmain__init.writeAction(f"movrl X20 8(X17) 0 8") 
  tranmain__init.writeAction(f"movrl X13 16(X17) 0 8") 
  tranmain__init.writeAction(f"movrl X14 24(X17) 0 8") 
  ## print("broadcast v_count %lu", v_count);
  tranmain__init.writeAction(f"send_wcont X19 X2 X17 8") 
  tranmain__init.writeAction(f"movrl X8 0(X17) 0 8") 
  tranmain__init.writeAction(f"movrl X9 8(X17) 0 8") 
  tranmain__init.writeAction(f"movrl X10 16(X17) 0 8") 
  tranmain__init.writeAction(f"movrl X11 0(X18) 0 8") 
  tranmain__init.writeAction(f"movrl X12 8(X18) 0 8") 
  tranmain__init.writeAction(f"movrl X18 24(X17) 0 8") 
  tranmain__init.writeAction(f"addi X18 X18 16") 
  tranmain__init.writeAction(f"movrl X15 0(X18) 0 8") 
  tranmain__init.writeAction(f"movrl X18 32(X17) 0 8") 
  tranmain__init.writeAction(f"movir X19 0") 
  tranmain__init.writeAction(f"evlb X19 js__map_shuffle_reduce") 
  tranmain__init.writeAction(f"evi X19 X19 255 4") 
  tranmain__init.writeAction(f"ev X19 X19 X0 X0 8") 
  tranmain__init.writeAction(f"send_wret X19 main::combine_js X17 8 X21") 
  tranmain__init.writeAction(f"addi X10 X16 0") 
  tranmain__init.writeAction(f"yield") 
  
  # Writing code for event main::combine_js
  tranmain__combine_js = efa.writeEvent('main::combine_js')
  tranmain__combine_js.writeAction(f"entry: print 'UDKVMSR finished, executed %lu reduce tasks.' X8") 
  tranmain__combine_js.writeAction(f"perflog 1 0 'UDKVMSR finished'") 
  ## unsigned long tmp = 0;
  ## unsigned long ev_word = evw_new(NETID, js_accumulate__init_global_snyc);
  ## send_event(ev_word, cached_num_lanes, tmp, term);
  tranmain__combine_js.writeAction(f"addi X7 X17 64") 
  tranmain__combine_js.writeAction(f"movir X19 273") 
  tranmain__combine_js.writeAction(f"movrl X19 0(X17) 0 8") 
  tranmain__combine_js.writeAction(f"yield_terminate") 
  
  # Writing code for event main::term
  tranmain__term = efa.writeEvent('main::term')
  tranmain__term.writeAction(f"entry: print 'Total js nonzero count: %lu' X8") 
  tranmain__term.writeAction(f"perflog 1 0 'JS finished'") 
  tranmain__term.writeAction(f"addi X7 X17 64") 
  tranmain__term.writeAction(f"movir X19 273") 
  tranmain__term.writeAction(f"movrl X19 0(X17) 0 8") 
  tranmain__term.writeAction(f"print 'Set test flag TEST_TOP_FLAG at offset TEST_TOP_OFFSET.'") 
  tranmain__term.writeAction(f"yield_terminate") 
  
  
  #########################################################
  ###### Writing code for thread main_broadcast_init ######
  #########################################################
  # Writing code for event main_broadcast_init::setup_spd
  tranmain_broadcast_init__setup_spd = efa.writeEvent('main_broadcast_init::setup_spd')
  tranmain_broadcast_init__setup_spd.writeAction(f"entry: addi X7 X16 21464") 
  tranmain_broadcast_init__setup_spd.writeAction(f"movir X18 21472") 
  tranmain_broadcast_init__setup_spd.writeAction(f"movrl X18 0(X16) 0 8") 
  tranmain_broadcast_init__setup_spd.writeAction(f"addi X7 X16 21440") 
  tranmain_broadcast_init__setup_spd.writeAction(f"movrl X8 0(X16) 0 8") 
  tranmain_broadcast_init__setup_spd.writeAction(f"addi X7 X16 21448") 
  tranmain_broadcast_init__setup_spd.writeAction(f"movrl X9 0(X16) 0 8") 
  ## print("write graph_size %lu at %lu", v_count, ptr);
  tranmain_broadcast_init__setup_spd.writeAction(f"yield_terminate") 
  
