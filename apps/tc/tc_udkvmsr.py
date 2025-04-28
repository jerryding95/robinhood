from linker.EFAProgram import efaProgram

## Global constants

@efaProgram
def EFA_tc(efa):
  efa.code_level = 'machine'
  state0 = efa.State("udweave_init") #Only one state code 
  efa.add_initId(state0.state_id)
  ## Static declarations
  ## Scoped Variable "v1" uses Register X16, scope (0)
  ## Scoped Variable "v1_deg" uses Register X17, scope (0)
  ## Scoped Variable "v1_nb_list" uses Register X18, scope (0)
  ## Scoped Variable "v2_deg" uses Register X19, scope (0)
  ## Scoped Variable "v2_nb_list" uses Register X20, scope (0)
  ## Scoped Variable "threashold" uses Register X21, scope (0)
  ## Scoped Variable "read_count" uses Register X22, scope (0)
  ## Scoped Variable "cached_nb" uses Register X23, scope (0)
  ## Scoped Variable "saved_cont" uses Register X24, scope (0)
  ## Param "id" uses Register X8, scope (0->10)
  ## Param "degree" uses Register X9, scope (0->10)
  ## Param "nb_list" uses Register X10, scope (0->10)
  ## Scoped Variable "nb_list_cur" uses Register X24, scope (0->10->12)
  ## Scoped Variable "ev_word" uses Register X25, scope (0->10->12)
  ## Scoped Variable "ev_word" uses Register X24, scope (0->10->13)
  ## Scoped Variable "nb_list_cur" uses Register X24, scope (0->14)
  ## Scoped Variable "cur_read_count" uses Register X25, scope (0->14)
  ## Param "op0" uses Register X8, scope (0->32)
  ## Param "op1" uses Register X9, scope (0->32)
  ## Param "op2" uses Register X10, scope (0->32)
  ## Param "op3" uses Register X11, scope (0->32)
  ## Param "op4" uses Register X12, scope (0->32)
  ## Param "op5" uses Register X13, scope (0->32)
  ## Param "op6" uses Register X14, scope (0->32)
  ## Param "op7" uses Register X15, scope (0->32)
  ## Scoped Variable "num_ops" uses Register X24, scope (0->32)
  ## Scoped Variable "ev_word" uses Register X25, scope (0->32)
  ## Scoped Variable "key" uses Register X26, scope (0->32->34)
  ## Scoped Variable "key" uses Register X26, scope (0->32->38)
  ## Scoped Variable "key" uses Register X26, scope (0->32->42)
  ## Scoped Variable "key" uses Register X26, scope (0->32->46)
  ## Scoped Variable "key" uses Register X26, scope (0->32->50)
  ## Scoped Variable "key" uses Register X26, scope (0->32->54)
  ## Scoped Variable "key" uses Register X26, scope (0->32->58)
  ## Scoped Variable "key" uses Register X26, scope (0->32->62)
  ## Param "v2_v1" uses Register X8, scope (0->68)
  ## Param "degree" uses Register X9, scope (0->68)
  ## Param "nb_list" uses Register X10, scope (0->68)
  ## Scoped Variable "ptr" uses Register X25, scope (0->68)
  ## Scoped Variable "graph" uses Register X26, scope (0->68)
  ## Scoped Variable "v2" uses Register X27, scope (0->68)
  ## Param "v2" uses Register X8, scope (0->69)
  ## Param "degree" uses Register X9, scope (0->69)
  ## Param "nb_list" uses Register X10, scope (0->69)
  ## Scoped Variable "ev_word" uses Register X25, scope (0->69)
  ## Scoped Variable "ev_word" uses Register X25, scope (0->69->71)
  ## Param "addr" uses Register X8, scope (0->72)
  ## Param "status" uses Register X9, scope (0->72)
  ## Param "op0" uses Register X8, scope (0->73)
  ## Param "op1" uses Register X9, scope (0->73)
  ## Param "op2" uses Register X10, scope (0->73)
  ## Param "op3" uses Register X11, scope (0->73)
  ## Param "op4" uses Register X12, scope (0->73)
  ## Param "op5" uses Register X13, scope (0->73)
  ## Param "op6" uses Register X14, scope (0->73)
  ## Param "op7" uses Register X15, scope (0->73)
  ## Scoped Variable "ptr" uses Register X25, scope (0->73)
  ## Scoped Variable "ev_word" uses Register X26, scope (0->73->77)
  ## Param "op0" uses Register X8, scope (0->78)
  ## Param "op1" uses Register X9, scope (0->78)
  ## Param "op2" uses Register X10, scope (0->78)
  ## Param "op3" uses Register X11, scope (0->78)
  ## Param "op4" uses Register X12, scope (0->78)
  ## Param "op5" uses Register X13, scope (0->78)
  ## Param "op6" uses Register X14, scope (0->78)
  ## Param "op7" uses Register X15, scope (0->78)
  ## Scoped Variable "ptr" uses Register X25, scope (0->78)
  ## Scoped Variable "ev_word" uses Register X26, scope (0->78->82)
  ## Scoped Variable "v1_id" uses Register X16, scope (0)
  ## Scoped Variable "loc_tc" uses Register X17, scope (0)
  ## Scoped Variable "threashold" uses Register X18, scope (0)
  ## Scoped Variable "read_count" uses Register X19, scope (0)
  ## Scoped Variable "cached_nb" uses Register X20, scope (0)
  ## Param "v1" uses Register X8, scope (0->84)
  ## Param "v2" uses Register X9, scope (0->84)
  ## Param "spmalloc_ptr" uses Register X10, scope (0->84)
  ## Scoped Variable "ev_word" uses Register X21, scope (0->84)
  ## Scoped Variable "offs_a" uses Register X21, scope (0->85)
  ## Scoped Variable "offs_b" uses Register X22, scope (0->85)
  ## Scoped Variable "loc_size_a" uses Register X23, scope (0->85)
  ## Scoped Variable "loc_size_b" uses Register X24, scope (0->85)
  ## Scoped Variable "iter_a" uses Register X25, scope (0->85)
  ## Scoped Variable "iter_b" uses Register X26, scope (0->85)
  ## Scoped Variable "rem" uses Register X25, scope (0->85->87)
  ## Scoped Variable "reached_end" uses Register X25, scope (0->85->95)
  ## Scoped Variable "ptr" uses Register X26, scope (0->85->95)
  ## Scoped Variable "elem_a" uses Register X27, scope (0->85->95->97->99)
  ## Scoped Variable "elem_b" uses Register X28, scope (0->85->95->97->99)
  ## Scoped Variable "ev_word" uses Register X27, scope (0->85->95->110)
  ## Scoped Variable "cont_word" uses Register X28, scope (0->85->95->110)
  ## Scoped Variable "ptr" uses Register X26, scope (0->85->112->114)
  ## Scoped Variable "ev_word" uses Register X26, scope (0->85->112->114->116)
  ## Scoped Variable "cont_word" uses Register X27, scope (0->85->112->114->116)
  ## Scoped Variable "ptr" uses Register X27, scope (0->85->118->120)
  ## Scoped Variable "ev_word" uses Register X27, scope (0->85->118->120->122)
  ## Scoped Variable "cont_word" uses Register X28, scope (0->85->118->120->122)
  ## Scoped Variable "addr" uses Register X27, scope (0->85->124)
  ## Scoped Variable "addr" uses Register X27, scope (0->85->126)
  ## Param "op0" uses Register X8, scope (0->127)
  ## Param "op1" uses Register X9, scope (0->127)
  ## Param "op2" uses Register X10, scope (0->127)
  ## Param "op3" uses Register X11, scope (0->127)
  ## Param "op4" uses Register X12, scope (0->127)
  ## Param "op5" uses Register X13, scope (0->127)
  ## Param "op6" uses Register X14, scope (0->127)
  ## Param "op7" uses Register X15, scope (0->127)
  ## Scoped Variable "ptr" uses Register X21, scope (0->127)
  ## Scoped Variable "ev_word" uses Register X22, scope (0->127->129)
  ## Param "op0" uses Register X8, scope (0->130)
  ## Param "op1" uses Register X9, scope (0->130)
  ## Param "op2" uses Register X10, scope (0->130)
  ## Param "op3" uses Register X11, scope (0->130)
  ## Param "op4" uses Register X12, scope (0->130)
  ## Param "op5" uses Register X13, scope (0->130)
  ## Param "op6" uses Register X14, scope (0->130)
  ## Param "op7" uses Register X15, scope (0->130)
  ## Scoped Variable "ptr" uses Register X21, scope (0->130)
  ## Scoped Variable "ev_word" uses Register X22, scope (0->130->132)
  ## Scoped Variable "cached_num_lanes" uses Register X16, scope (0)
  ## Param "partitions" uses Register X8, scope (0->135)
  ## Param "partition_per_lane" uses Register X9, scope (0->135)
  ## Param "num_lanes" uses Register X10, scope (0->135)
  ## Param "input" uses Register X11, scope (0->135)
  ## Param "input_size" uses Register X12, scope (0->135)
  ## Param "intermediate_hashmap" uses Register X13, scope (0->135)
  ## Scoped Variable "send_buffer" uses Register X17, scope (0->135)
  ## Scoped Variable "heap" uses Register X18, scope (0->135)
  ## Scoped Variable "ev_word" uses Register X19, scope (0->135)
  ## Scoped Variable "tmp_ev_word" uses Register X20, scope (0->135)
  ## Scoped Variable "ptr" uses Register X21, scope (0->135)
  ## Scoped Variable "tc_count" uses Register X22, scope (0->135)
  ## Param "num_reduce" uses Register X8, scope (0->136)
  ## Scoped Variable "tmp" uses Register X17, scope (0->136)
  ## Scoped Variable "ev_word" uses Register X18, scope (0->136)
  ## Param "tc_count" uses Register X8, scope (0->138)
  ## Scoped Variable "ptr" uses Register X17, scope (0->138)
  ## Param "graph" uses Register X8, scope (0->141)
  ## Scoped Variable "ptr" uses Register X16, scope (0->141)
  ## #include "LMStaticMap.udwh"
  ## #define SEND_ALL_MAP_READ
  ## #define PRINT_EDGE_RESULT
  
  EXTENSION = 'load_balancer'
  test_ws = True
  test_random = False
  DEBUG_FLAG = False
  LB_TYPE = ['mapper','reducer']
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
  
  spmalloc = SpMallocEFA(efa, state0 = state0, init_offset = 29864)
  broadcast = Broadcast(state = state0, identifier='tc_broadcast')
  
  task_name = 'tc'
  tcMSR = UDKeyValueMapShuffleReduceTemplate(efa=efa, task_name=task_name, meta_data_offset=UDKVMSR_0_OFFSET, debug_flag=DEBUG_FLAG,
  extension = EXTENSION, load_balancer_type = LB_TYPE, grlb_type = rtype,
  claim_multiple_work = multi, test_map_ws=map_ws, test_reduce_ws=red_ws, random_lb=test_random, do_all_reduce = True)
  tcMSR.set_input_kvset(OneDimKeyValueSet('tc_input', element_size=8) )
  tcMSR.set_intermediate_kvset(IntermediateKeyValueSet('tc_intermediate', key_size=1, value_size=2))
  tcMSR.set_max_thread_per_lane(max_map_th_per_lane=64, max_reduce_th_per_lane=128, max_reduce_key_to_claim = 128)
  tcMSR.setup_lb_cache(intermediate_cache_num_bins = 16, intermediate_cache_size = 1024, materialize_kv_cache_size = 512, materialize_kv_dram_size = 1<<16)
  print(tcMSR.heap_offset)
  
  tcMSR.generate_udkvmsr_task()
  
  tc_accumulate_global_sync = GlobalSync(tcMSR.state, 'tc_accumulate', 'X28', [29856], ['X29','X30'], debug_flag = DEBUG_FLAG)
  tc_accumulate_global_sync.global_sync(continuation='X1', sync_value='X9', num_lanes='X8')
  
  
  ########################################
  ###### Writing code for thread tc ######
  ########################################
  ## unsigned long iter_a;
  ## unsigned long offs_a;
  ## unsigned long iter_b;
  ## unsigned long offs_b;
  # Writing code for event tc::kv_map
  trantc__kv_map = efa.writeEvent('tc::kv_map')
  ## print("start map, v1 %lu degree %lu nb_list %lu", id, degree, nb_list);
  ## if (1) {
  ##     print("start map");
  ##     unsigned long ev_word = evw_update_event(CEVNT, tc__kv_map_return);
  ##     send_event(ev_word, id, degree, IGNRCONT);
  ##     yield;
  ## }
  trantc__kv_map.writeAction(f"entry: bleiu X9 0 __if_kv_map_1_false") 
  trantc__kv_map.writeAction(f"__if_kv_map_0_true: addi X8 X16 0") 
  trantc__kv_map.writeAction(f"addi X9 X17 0") 
  trantc__kv_map.writeAction(f"addi X10 X18 0") 
  trantc__kv_map.writeAction(f"addi X10 X24 0") 
  trantc__kv_map.writeAction(f"movir X22 0") 
  trantc__kv_map.writeAction(f"evi X2 X25 tc::map_read 1") 
  trantc__kv_map.writeAction(f"movir X26 3") 
  trantc__kv_map.writeAction(f"movir X27 -1") 
  trantc__kv_map.writeAction(f"sri X27 X27 1") 
  trantc__kv_map.writeAction(f"sendr_wcont X25 X27 X8 X26") 
  trantc__kv_map.writeAction(f"jmp __if_kv_map_2_post") 
  trantc__kv_map.writeAction(f"__if_kv_map_1_false: evi X2 X24 tc__kv_map_return 1") 
  trantc__kv_map.writeAction(f"movir X25 3") 
  trantc__kv_map.writeAction(f"movir X26 -1") 
  trantc__kv_map.writeAction(f"sri X26 X26 1") 
  trantc__kv_map.writeAction(f"sendr_wcont X24 X26 X8 X25") 
  trantc__kv_map.writeAction(f"__if_kv_map_2_post: yield") 
  
  # Writing code for event tc::map_read
  trantc__map_read = efa.writeEvent('tc::map_read')
  trantc__map_read.writeAction(f"entry: sli X22 X25 3") 
  trantc__map_read.writeAction(f"add X18 X25 X24") 
  trantc__map_read.writeAction(f"sub X17 X22 X25") 
  trantc__map_read.writeAction(f"bltiu X25 8 __if_map_read_2_post") 
  trantc__map_read.writeAction(f"__if_map_read_0_true: movir X25 8") 
  trantc__map_read.writeAction(f"__if_map_read_2_post: add X22 X25 X22") 
  trantc__map_read.writeAction(f"bneiu X25 8 __if_map_read_4_false") 
  trantc__map_read.writeAction(f"__if_map_read_3_true: send_dmlm_ld_wret X24 tc::map_read_ret 8 X26") 
  trantc__map_read.writeAction(f"jmp __if_map_read_5_post") 
  trantc__map_read.writeAction(f"__if_map_read_4_false: bneiu X25 1 __if_map_read_7_false") 
  trantc__map_read.writeAction(f"__if_map_read_6_true: send_dmlm_ld_wret X24 tc::map_read_ret 1 X26") 
  trantc__map_read.writeAction(f"jmp __if_map_read_5_post") 
  trantc__map_read.writeAction(f"__if_map_read_7_false: bneiu X25 2 __if_map_read_10_false") 
  trantc__map_read.writeAction(f"__if_map_read_9_true: send_dmlm_ld_wret X24 tc::map_read_ret 2 X26") 
  trantc__map_read.writeAction(f"jmp __if_map_read_5_post") 
  trantc__map_read.writeAction(f"__if_map_read_10_false: bneiu X25 3 __if_map_read_13_false") 
  trantc__map_read.writeAction(f"__if_map_read_12_true: send_dmlm_ld_wret X24 tc::map_read_ret 3 X26") 
  trantc__map_read.writeAction(f"jmp __if_map_read_5_post") 
  trantc__map_read.writeAction(f"__if_map_read_13_false: bneiu X25 4 __if_map_read_16_false") 
  trantc__map_read.writeAction(f"__if_map_read_15_true: send_dmlm_ld_wret X24 tc::map_read_ret 4 X26") 
  trantc__map_read.writeAction(f"jmp __if_map_read_5_post") 
  trantc__map_read.writeAction(f"__if_map_read_16_false: bneiu X25 5 __if_map_read_19_false") 
  trantc__map_read.writeAction(f"__if_map_read_18_true: send_dmlm_ld_wret X24 tc::map_read_ret 5 X26") 
  trantc__map_read.writeAction(f"jmp __if_map_read_5_post") 
  trantc__map_read.writeAction(f"__if_map_read_19_false: bneiu X25 6 __if_map_read_22_false") 
  trantc__map_read.writeAction(f"__if_map_read_21_true: send_dmlm_ld_wret X24 tc::map_read_ret 6 X26") 
  trantc__map_read.writeAction(f"jmp __if_map_read_5_post") 
  trantc__map_read.writeAction(f"__if_map_read_22_false: send_dmlm_ld_wret X24 tc::map_read_ret 7 X26") 
  ## print("map read count %lu", read_count);
  trantc__map_read.writeAction(f"__if_map_read_5_post: yield") 
  
  # Writing code for event tc::map_read_ret
  trantc__map_read_ret = efa.writeEvent('tc::map_read_ret')
  trantc__map_read_ret.writeAction(f"entry: sri X2 X25 20") 
  trantc__map_read_ret.writeAction(f"andi X25 X26 7") 
  trantc__map_read_ret.writeAction(f"addi X26 X24 1") 
  trantc__map_read_ret.writeAction(f"movir X25 0") 
  trantc__map_read_ret.writeAction(f"evlb X25 tc__kv_map_emit") 
  trantc__map_read_ret.writeAction(f"evi X25 X25 255 4") 
  trantc__map_read_ret.writeAction(f"ev X25 X25 X0 X0 8") 
  ## print("map read return");
  trantc__map_read_ret.writeAction(f"bleiu X24 0 __if_map_read_ret_2_post") 
  trantc__map_read_ret.writeAction(f"__if_map_read_ret_0_true: bgt X16 X8 __if_map_read_ret_5_post") 
  trantc__map_read_ret.writeAction(f"__if_map_read_ret_3_true: evi X2 X25 tc__kv_map_return 1") 
  trantc__map_read_ret.writeAction(f"movir X26 -1") 
  trantc__map_read_ret.writeAction(f"sri X26 X26 1") 
  trantc__map_read_ret.writeAction(f"sendr_wcont X25 X26 X16 X16") 
  ## print("map return");
  trantc__map_read_ret.writeAction(f"yield") 
  trantc__map_read_ret.writeAction(f"__if_map_read_ret_5_post: sli X8 X27 32") 
  trantc__map_read_ret.writeAction(f"or X27 X16 X26") 
  trantc__map_read_ret.writeAction(f"movir X27 -1") 
  trantc__map_read_ret.writeAction(f"sri X27 X27 1") 
  trantc__map_read_ret.writeAction(f"sendr3_wcont X25 X27 X26 X17 X18") 
  trantc__map_read_ret.writeAction(f"__if_map_read_ret_2_post: bleiu X24 1 __if_map_read_ret_8_post") 
  trantc__map_read_ret.writeAction(f"__if_map_read_ret_6_true: bgt X16 X9 __if_map_read_ret_11_post") 
  trantc__map_read_ret.writeAction(f"__if_map_read_ret_9_true: evi X2 X25 tc__kv_map_return 1") 
  trantc__map_read_ret.writeAction(f"movir X26 -1") 
  trantc__map_read_ret.writeAction(f"sri X26 X26 1") 
  trantc__map_read_ret.writeAction(f"sendr_wcont X25 X26 X16 X16") 
  ## print("map return");
  trantc__map_read_ret.writeAction(f"yield") 
  trantc__map_read_ret.writeAction(f"__if_map_read_ret_11_post: sli X9 X27 32") 
  trantc__map_read_ret.writeAction(f"or X27 X16 X26") 
  trantc__map_read_ret.writeAction(f"movir X27 -1") 
  trantc__map_read_ret.writeAction(f"sri X27 X27 1") 
  trantc__map_read_ret.writeAction(f"sendr3_wcont X25 X27 X26 X17 X18") 
  trantc__map_read_ret.writeAction(f"__if_map_read_ret_8_post: bleiu X24 2 __if_map_read_ret_14_post") 
  trantc__map_read_ret.writeAction(f"__if_map_read_ret_12_true: bgt X16 X10 __if_map_read_ret_17_post") 
  trantc__map_read_ret.writeAction(f"__if_map_read_ret_15_true: evi X2 X25 tc__kv_map_return 1") 
  trantc__map_read_ret.writeAction(f"movir X26 -1") 
  trantc__map_read_ret.writeAction(f"sri X26 X26 1") 
  trantc__map_read_ret.writeAction(f"sendr_wcont X25 X26 X16 X16") 
  ## print("map return");
  trantc__map_read_ret.writeAction(f"yield") 
  trantc__map_read_ret.writeAction(f"__if_map_read_ret_17_post: sli X10 X27 32") 
  trantc__map_read_ret.writeAction(f"or X27 X16 X26") 
  trantc__map_read_ret.writeAction(f"movir X27 -1") 
  trantc__map_read_ret.writeAction(f"sri X27 X27 1") 
  trantc__map_read_ret.writeAction(f"sendr3_wcont X25 X27 X26 X17 X18") 
  trantc__map_read_ret.writeAction(f"__if_map_read_ret_14_post: bleiu X24 3 __if_map_read_ret_20_post") 
  trantc__map_read_ret.writeAction(f"__if_map_read_ret_18_true: bgt X16 X11 __if_map_read_ret_23_post") 
  trantc__map_read_ret.writeAction(f"__if_map_read_ret_21_true: evi X2 X25 tc__kv_map_return 1") 
  trantc__map_read_ret.writeAction(f"movir X26 -1") 
  trantc__map_read_ret.writeAction(f"sri X26 X26 1") 
  trantc__map_read_ret.writeAction(f"sendr_wcont X25 X26 X16 X16") 
  ## print("map return");
  trantc__map_read_ret.writeAction(f"yield") 
  trantc__map_read_ret.writeAction(f"__if_map_read_ret_23_post: sli X11 X27 32") 
  trantc__map_read_ret.writeAction(f"or X27 X16 X26") 
  trantc__map_read_ret.writeAction(f"movir X27 -1") 
  trantc__map_read_ret.writeAction(f"sri X27 X27 1") 
  trantc__map_read_ret.writeAction(f"sendr3_wcont X25 X27 X26 X17 X18") 
  trantc__map_read_ret.writeAction(f"__if_map_read_ret_20_post: bleiu X24 4 __if_map_read_ret_26_post") 
  trantc__map_read_ret.writeAction(f"__if_map_read_ret_24_true: bgt X16 X12 __if_map_read_ret_29_post") 
  trantc__map_read_ret.writeAction(f"__if_map_read_ret_27_true: evi X2 X25 tc__kv_map_return 1") 
  trantc__map_read_ret.writeAction(f"movir X26 -1") 
  trantc__map_read_ret.writeAction(f"sri X26 X26 1") 
  trantc__map_read_ret.writeAction(f"sendr_wcont X25 X26 X16 X16") 
  ## print("map return");
  trantc__map_read_ret.writeAction(f"yield") 
  trantc__map_read_ret.writeAction(f"__if_map_read_ret_29_post: sli X12 X27 32") 
  trantc__map_read_ret.writeAction(f"or X27 X16 X26") 
  trantc__map_read_ret.writeAction(f"movir X27 -1") 
  trantc__map_read_ret.writeAction(f"sri X27 X27 1") 
  trantc__map_read_ret.writeAction(f"sendr3_wcont X25 X27 X26 X17 X18") 
  trantc__map_read_ret.writeAction(f"__if_map_read_ret_26_post: bleiu X24 5 __if_map_read_ret_32_post") 
  trantc__map_read_ret.writeAction(f"__if_map_read_ret_30_true: bgt X16 X13 __if_map_read_ret_35_post") 
  trantc__map_read_ret.writeAction(f"__if_map_read_ret_33_true: evi X2 X25 tc__kv_map_return 1") 
  trantc__map_read_ret.writeAction(f"movir X26 -1") 
  trantc__map_read_ret.writeAction(f"sri X26 X26 1") 
  trantc__map_read_ret.writeAction(f"sendr_wcont X25 X26 X16 X16") 
  ## print("map return");
  trantc__map_read_ret.writeAction(f"yield") 
  trantc__map_read_ret.writeAction(f"__if_map_read_ret_35_post: sli X13 X27 32") 
  trantc__map_read_ret.writeAction(f"or X27 X16 X26") 
  trantc__map_read_ret.writeAction(f"movir X27 -1") 
  trantc__map_read_ret.writeAction(f"sri X27 X27 1") 
  trantc__map_read_ret.writeAction(f"sendr3_wcont X25 X27 X26 X17 X18") 
  trantc__map_read_ret.writeAction(f"__if_map_read_ret_32_post: bleiu X24 6 __if_map_read_ret_38_post") 
  trantc__map_read_ret.writeAction(f"__if_map_read_ret_36_true: bgt X16 X14 __if_map_read_ret_41_post") 
  trantc__map_read_ret.writeAction(f"__if_map_read_ret_39_true: evi X2 X25 tc__kv_map_return 1") 
  trantc__map_read_ret.writeAction(f"movir X26 -1") 
  trantc__map_read_ret.writeAction(f"sri X26 X26 1") 
  trantc__map_read_ret.writeAction(f"sendr_wcont X25 X26 X16 X16") 
  ## print("map return");
  trantc__map_read_ret.writeAction(f"yield") 
  trantc__map_read_ret.writeAction(f"__if_map_read_ret_41_post: sli X14 X27 32") 
  trantc__map_read_ret.writeAction(f"or X27 X16 X26") 
  trantc__map_read_ret.writeAction(f"movir X27 -1") 
  trantc__map_read_ret.writeAction(f"sri X27 X27 1") 
  trantc__map_read_ret.writeAction(f"sendr3_wcont X25 X27 X26 X17 X18") 
  trantc__map_read_ret.writeAction(f"__if_map_read_ret_38_post: bleiu X24 7 __if_map_read_ret_44_post") 
  trantc__map_read_ret.writeAction(f"__if_map_read_ret_42_true: bgt X16 X15 __if_map_read_ret_47_post") 
  trantc__map_read_ret.writeAction(f"__if_map_read_ret_45_true: evi X2 X25 tc__kv_map_return 1") 
  trantc__map_read_ret.writeAction(f"movir X26 -1") 
  trantc__map_read_ret.writeAction(f"sri X26 X26 1") 
  trantc__map_read_ret.writeAction(f"sendr_wcont X25 X26 X16 X16") 
  ## print("map return");
  trantc__map_read_ret.writeAction(f"yield") 
  trantc__map_read_ret.writeAction(f"__if_map_read_ret_47_post: sli X15 X27 32") 
  trantc__map_read_ret.writeAction(f"or X27 X16 X26") 
  trantc__map_read_ret.writeAction(f"movir X27 -1") 
  trantc__map_read_ret.writeAction(f"sri X27 X27 1") 
  trantc__map_read_ret.writeAction(f"sendr3_wcont X25 X27 X26 X17 X18") 
  trantc__map_read_ret.writeAction(f"__if_map_read_ret_44_post: bneu X22 X17 __if_map_read_ret_49_false") 
  trantc__map_read_ret.writeAction(f"__if_map_read_ret_48_true: evi X2 X25 tc__kv_map_return 1") 
  trantc__map_read_ret.writeAction(f"movir X26 -1") 
  trantc__map_read_ret.writeAction(f"sri X26 X26 1") 
  trantc__map_read_ret.writeAction(f"sendr_wcont X25 X26 X16 X17") 
  ## print("map return");
  trantc__map_read_ret.writeAction(f"jmp __if_map_read_ret_50_post") 
  trantc__map_read_ret.writeAction(f"__if_map_read_ret_49_false: evi X2 X25 tc::map_read 1") 
  trantc__map_read_ret.writeAction(f"movir X26 -1") 
  trantc__map_read_ret.writeAction(f"sri X26 X26 1") 
  trantc__map_read_ret.writeAction(f"sendr_wcont X25 X26 X16 X17") 
  trantc__map_read_ret.writeAction(f"__if_map_read_ret_50_post: yield") 
  
  # Writing code for event tc::kv_reduce
  trantc__kv_reduce = efa.writeEvent('tc::kv_reduce')
  ## unsigned long* local ptr = LMBASE + TC_COUNT_OFFSET;
  ## unsigned long tc_count = ptr[0];
  ## print("Current triangle count: %lu", tc_count);
  ## print("Reduce start.");
  trantc__kv_reduce.writeAction(f"entry: addi X1 X24 0") 
  trantc__kv_reduce.writeAction(f"sli X8 X25 32") 
  trantc__kv_reduce.writeAction(f"sri X25 X16 32") 
  trantc__kv_reduce.writeAction(f"addi X9 X17 0") 
  trantc__kv_reduce.writeAction(f"addi X10 X18 0") 
  ## print("Received v1_nb_list: %lu", v1_nb_list);
  ## if (v1 ==0) {
  ##     print("v1: %lu, v1_deg: %lu, v1_nb_list: %lu", v1, v1_deg, v1_nb_list);
  ## }
  trantc__kv_reduce.writeAction(f"addi X7 X25 29848") 
  trantc__kv_reduce.writeAction(f"movlr 0(X25) X26 0 8") 
  trantc__kv_reduce.writeAction(f"sri X8 X27 32") 
  trantc__kv_reduce.writeAction(f"sli X27 X28 6") 
  trantc__kv_reduce.writeAction(f"add X26 X28 X26") 
  trantc__kv_reduce.writeAction(f"send_dmlm_ld_wret X26 tc::v2_read_ret 3 X28") 
  trantc__kv_reduce.writeAction(f"yield") 
  
  # Writing code for event tc::v2_read_ret
  trantc__v2_read_ret = efa.writeEvent('tc::v2_read_ret')
  trantc__v2_read_ret.writeAction(f"entry: bneiu X9 0 __if_v2_read_ret_2_post") 
  trantc__v2_read_ret.writeAction(f"__if_v2_read_ret_0_true: evi X2 X25 tc__kv_reduce_return 1") 
  trantc__v2_read_ret.writeAction(f"sendr_wcont X25 X1 X21 X21") 
  trantc__v2_read_ret.writeAction(f"yield") 
  trantc__v2_read_ret.writeAction(f"__if_v2_read_ret_2_post: movir X25 0") 
  trantc__v2_read_ret.writeAction(f"evlb X25 lm_allocator__spmalloc") 
  trantc__v2_read_ret.writeAction(f"evi X25 X25 255 4") 
  trantc__v2_read_ret.writeAction(f"ev X25 X25 X0 X0 8") 
  trantc__v2_read_ret.writeAction(f"movir X26 24") 
  trantc__v2_read_ret.writeAction(f"sendr_wret X25 tc::sp_malloc_ret X26 X26 X27") 
  trantc__v2_read_ret.writeAction(f"addi X8 X21 0") 
  trantc__v2_read_ret.writeAction(f"addi X9 X19 0") 
  trantc__v2_read_ret.writeAction(f"addi X10 X20 0") 
  ## print("v2: %lu, v2_deg: %lu, v1_nb_list: %lu, v2_nb_list: %lu", v2, degree, v1_nb_list, nb_list);
  trantc__v2_read_ret.writeAction(f"yield") 
  
  # Writing code for event tc::sp_malloc_ret
  trantc__sp_malloc_ret = efa.writeEvent('tc::sp_malloc_ret')
  trantc__sp_malloc_ret.writeAction(f"entry: addi X8 X23 0") 
  trantc__sp_malloc_ret.writeAction(f"movrl X17 0(X23) 0 8") 
  trantc__sp_malloc_ret.writeAction(f"movrl X18 8(X23) 0 8") 
  trantc__sp_malloc_ret.writeAction(f"movir X26 0") 
  trantc__sp_malloc_ret.writeAction(f"movrl X26 16(X23) 0 8") 
  trantc__sp_malloc_ret.writeAction(f"movir X26 0") 
  trantc__sp_malloc_ret.writeAction(f"movrl X26 24(X23) 0 8") 
  trantc__sp_malloc_ret.writeAction(f"movrl X19 32(X23) 0 8") 
  trantc__sp_malloc_ret.writeAction(f"movrl X20 40(X23) 0 8") 
  trantc__sp_malloc_ret.writeAction(f"movir X26 0") 
  trantc__sp_malloc_ret.writeAction(f"movrl X26 48(X23) 0 8") 
  trantc__sp_malloc_ret.writeAction(f"movir X26 0") 
  trantc__sp_malloc_ret.writeAction(f"movrl X26 56(X23) 0 8") 
  trantc__sp_malloc_ret.writeAction(f"send_dmlm_ld_wret X18 tc::v1_nblist_read_ret 8 X25") 
  trantc__sp_malloc_ret.writeAction(f"send_dmlm_ld_wret X20 tc::v2_nblist_read_ret 8 X25") 
  trantc__sp_malloc_ret.writeAction(f"movir X22 2") 
  trantc__sp_malloc_ret.writeAction(f"yield") 
  
  # Writing code for event tc::v1_nblist_read_ret
  trantc__v1_nblist_read_ret = efa.writeEvent('tc::v1_nblist_read_ret')
  trantc__v1_nblist_read_ret.writeAction(f"entry: subi X22 X22 1") 
  trantc__v1_nblist_read_ret.writeAction(f"bneiu X23 0 __if_v1_nblist_read_ret_2_post") 
  trantc__v1_nblist_read_ret.writeAction(f"__if_v1_nblist_read_ret_0_true: sendops_wcont X2 X1 X8 8") 
  trantc__v1_nblist_read_ret.writeAction(f"yield") 
  trantc__v1_nblist_read_ret.writeAction(f"__if_v1_nblist_read_ret_2_post: addi X23 X25 64") 
  trantc__v1_nblist_read_ret.writeAction(f"bcpyoli X8 X25 8") 
  trantc__v1_nblist_read_ret.writeAction(f"bneiu X22 0 __if_v1_nblist_read_ret_5_post") 
  trantc__v1_nblist_read_ret.writeAction(f"__if_v1_nblist_read_ret_3_true: evi X2 X26 tc_compute::setup_thread_reg 1") 
  trantc__v1_nblist_read_ret.writeAction(f"sendr3_wcont X26 X24 X16 X21 X23") 
  trantc__v1_nblist_read_ret.writeAction(f"__if_v1_nblist_read_ret_5_post: yield") 
  
  # Writing code for event tc::v2_nblist_read_ret
  trantc__v2_nblist_read_ret = efa.writeEvent('tc::v2_nblist_read_ret')
  trantc__v2_nblist_read_ret.writeAction(f"entry: subi X22 X22 1") 
  trantc__v2_nblist_read_ret.writeAction(f"bneiu X23 0 __if_v2_nblist_read_ret_2_post") 
  trantc__v2_nblist_read_ret.writeAction(f"__if_v2_nblist_read_ret_0_true: sendops_wcont X2 X1 X8 8") 
  trantc__v2_nblist_read_ret.writeAction(f"yield") 
  trantc__v2_nblist_read_ret.writeAction(f"__if_v2_nblist_read_ret_2_post: addi X23 X25 128") 
  trantc__v2_nblist_read_ret.writeAction(f"bcpyoli X8 X25 8") 
  trantc__v2_nblist_read_ret.writeAction(f"bneiu X22 0 __if_v2_nblist_read_ret_5_post") 
  trantc__v2_nblist_read_ret.writeAction(f"__if_v2_nblist_read_ret_3_true: evi X2 X26 tc_compute::setup_thread_reg 1") 
  trantc__v2_nblist_read_ret.writeAction(f"sendr3_wcont X26 X24 X16 X21 X23") 
  trantc__v2_nblist_read_ret.writeAction(f"__if_v2_nblist_read_ret_5_post: yield") 
  
  
  ################################################
  ###### Writing code for thread tc_compute ######
  ################################################
  ## cache_nb = || v1_deg || v1_nb_list || iter_a || offs_a || v2_deg || v2_nb_list || iter_b || offs_b ||
  ## index      || 0      || 1          || 2      || 3      || 4      || 5          || 6      || 7      ||
  # Writing code for event tc_compute::setup_thread_reg
  trantc_compute__setup_thread_reg = efa.writeEvent('tc_compute::setup_thread_reg')
  trantc_compute__setup_thread_reg.writeAction(f"entry: addi X8 X16 0") 
  trantc_compute__setup_thread_reg.writeAction(f"movir X17 0") 
  trantc_compute__setup_thread_reg.writeAction(f"movir X19 0") 
  trantc_compute__setup_thread_reg.writeAction(f"addi X9 X18 0") 
  trantc_compute__setup_thread_reg.writeAction(f"addi X10 X20 0") 
  ## if (v1_id == 15661 && threashold == 15662) {
  ##     unsigned long v1_deg = cached_nb[0];
  ##     unsigned long v1_nb_list = cached_nb[1];
  ##     unsigned long v2_deg = cached_nb[4];
  ##     unsigned long v2_nb_list = cached_nb[5];
  ##     print("Edge %lu-%lu: v1_deg: %lu, v1_nb_list: 0x%lx, v2_deg: %lu, v2_nb_list: 0x%lx", v1_id, threashold, v1_deg, v1_nb_list, v2_deg, v2_nb_list);
  ## }
  trantc_compute__setup_thread_reg.writeAction(f"evi X2 X21 tc_compute::intersect_ab 1") 
  trantc_compute__setup_thread_reg.writeAction(f"sendops_wcont X21 X1 X9 2") 
  trantc_compute__setup_thread_reg.writeAction(f"yield") 
  
  # Writing code for event tc_compute::intersect_ab
  trantc_compute__intersect_ab = efa.writeEvent('tc_compute::intersect_ab')
  ## if (v1_id == 1394 && threashold == 1380) {
  ##     print("V1 neighbors:");
  ##     for (int i=0; i<8; i=i+1){
  ##         unsigned long tmp = cached_nb[i+8];
  ##         print("neighbor_%d: %lu", i, tmp);
  ##     }
  ##     print("V2 neighbors:");
  ##     for (int i=0; i<8; i=i+1){
  ##         unsigned long tmp = cached_nb[i+16];
  ##         print("neighbor_%d: %lu", i, tmp);
  ##     }
  ## }
  ## print("Start intersect");
  trantc_compute__intersect_ab.writeAction(f"entry: movlr 24(X20) X21 0 8") 
  trantc_compute__intersect_ab.writeAction(f"movlr 56(X20) X22 0 8") 
  trantc_compute__intersect_ab.writeAction(f"__if_intersect_ab_0_true: movlr 0(X20) X26 0 8") 
  trantc_compute__intersect_ab.writeAction(f"movlr 16(X20) X27 0 8") 
  trantc_compute__intersect_ab.writeAction(f"sub X26 X27 X25") 
  trantc_compute__intersect_ab.writeAction(f"bleiu X25 8 __if_intersect_ab_4_false") 
  trantc_compute__intersect_ab.writeAction(f"__if_intersect_ab_3_true: movir X23 8") 
  trantc_compute__intersect_ab.writeAction(f"jmp __if_intersect_ab_5_post") 
  trantc_compute__intersect_ab.writeAction(f"__if_intersect_ab_4_false: addi X25 X23 0") 
  trantc_compute__intersect_ab.writeAction(f"__if_intersect_ab_5_post: movlr 32(X20) X26 0 8") 
  trantc_compute__intersect_ab.writeAction(f"movlr 48(X20) X27 0 8") 
  trantc_compute__intersect_ab.writeAction(f"sub X26 X27 X25") 
  trantc_compute__intersect_ab.writeAction(f"bleiu X25 8 __if_intersect_ab_7_false") 
  trantc_compute__intersect_ab.writeAction(f"__if_intersect_ab_6_true: movir X24 8") 
  trantc_compute__intersect_ab.writeAction(f"jmp __if_intersect_ab_9_true") 
  trantc_compute__intersect_ab.writeAction(f"__if_intersect_ab_7_false: addi X25 X24 0") 
  trantc_compute__intersect_ab.writeAction(f"__if_intersect_ab_9_true: movir X25 0") 
  trantc_compute__intersect_ab.writeAction(f"addi X20 X26 64") 
  trantc_compute__intersect_ab.writeAction(f"__while_intersect_ab_15_condition: clt X21 X23 X27") 
  trantc_compute__intersect_ab.writeAction(f"clt X22 X24 X28") 
  trantc_compute__intersect_ab.writeAction(f"and X27 X28 X29") 
  trantc_compute__intersect_ab.writeAction(f"beqiu X29 0 __while_intersect_ab_17_post") 
  trantc_compute__intersect_ab.writeAction(f"__while_intersect_ab_16_body: movwlr X26(X21,0,0) X27") 
  trantc_compute__intersect_ab.writeAction(f"addi X22 X29 8") 
  trantc_compute__intersect_ab.writeAction(f"movwlr X26(X29,0,0) X28") 
  trantc_compute__intersect_ab.writeAction(f"bgt X18 X27 __if_intersect_ab_19_false") 
  trantc_compute__intersect_ab.writeAction(f"__if_intersect_ab_18_true: movir X25 1") 
  trantc_compute__intersect_ab.writeAction(f"addi X23 X21 0") 
  trantc_compute__intersect_ab.writeAction(f"addi X27 X19 0") 
  trantc_compute__intersect_ab.writeAction(f"jmp __if_intersect_ab_20_post") 
  trantc_compute__intersect_ab.writeAction(f"__if_intersect_ab_19_false: bgt X18 X28 __if_intersect_ab_22_false") 
  trantc_compute__intersect_ab.writeAction(f"__if_intersect_ab_21_true: movir X25 1") 
  trantc_compute__intersect_ab.writeAction(f"addi X24 X22 0") 
  trantc_compute__intersect_ab.writeAction(f"addi X28 X19 0") 
  trantc_compute__intersect_ab.writeAction(f"jmp __if_intersect_ab_20_post") 
  trantc_compute__intersect_ab.writeAction(f"__if_intersect_ab_22_false: ble X28 X27 __if_intersect_ab_25_false") 
  trantc_compute__intersect_ab.writeAction(f"__if_intersect_ab_24_true: addi X21 X21 1") 
  trantc_compute__intersect_ab.writeAction(f"jmp __if_intersect_ab_20_post") 
  trantc_compute__intersect_ab.writeAction(f"__if_intersect_ab_25_false: ble X27 X28 __if_intersect_ab_28_false") 
  trantc_compute__intersect_ab.writeAction(f"__if_intersect_ab_27_true: addi X22 X22 1") 
  trantc_compute__intersect_ab.writeAction(f"jmp __if_intersect_ab_20_post") 
  trantc_compute__intersect_ab.writeAction(f"__if_intersect_ab_28_false: addi X17 X17 1") 
  trantc_compute__intersect_ab.writeAction(f"addi X21 X21 1") 
  trantc_compute__intersect_ab.writeAction(f"addi X22 X22 1") 
  trantc_compute__intersect_ab.writeAction(f"__if_intersect_ab_20_post: jmp __while_intersect_ab_15_condition") 
  ## if intersect result > v0, end
  trantc_compute__intersect_ab.writeAction(f"__while_intersect_ab_17_post: bneiu X25 1 __if_intersect_ab_32_post") 
  trantc_compute__intersect_ab.writeAction(f"__if_intersect_ab_30_true: movir X27 0") 
  trantc_compute__intersect_ab.writeAction(f"evlb X27 lm_allocator__spfree") 
  trantc_compute__intersect_ab.writeAction(f"evi X27 X27 255 4") 
  trantc_compute__intersect_ab.writeAction(f"ev X27 X27 X0 X0 8") 
  trantc_compute__intersect_ab.writeAction(f"movir X28 0") 
  trantc_compute__intersect_ab.writeAction(f"evlb X28 tc_compute::sp_free_ret") 
  trantc_compute__intersect_ab.writeAction(f"evi X28 X28 255 4") 
  trantc_compute__intersect_ab.writeAction(f"ev X28 X28 X0 X0 8") 
  trantc_compute__intersect_ab.writeAction(f"sendr_wcont X27 X28 X20 X20") 
  trantc_compute__intersect_ab.writeAction(f"evi X2 X27 tc__kv_reduce_return 1") 
  trantc_compute__intersect_ab.writeAction(f"sendr_wcont X27 X1 X18 X18") 
  ## update the loc tc
  trantc_compute__intersect_ab.writeAction(f"addi X7 X26 29856") 
  trantc_compute__intersect_ab.writeAction(f"movlr 0(X26) X30 0 8") 
  trantc_compute__intersect_ab.writeAction(f"add X30 X17 X31") 
  trantc_compute__intersect_ab.writeAction(f"movrl X31 0(X26) 0 8") 
  ## if (v1_id < threashold) {
  ##     print("Reach end. element: %lu, threashold: %lu", read_count, threashold);
  ##     print("Edge %u-%u intersect finished, tc count: %lu", v1_id, threashold, loc_tc);
  ## }
  ## if (loc_tc > 0){
  ##     double js = loc_tc/(v1_deg + v2_deg - loc_tc);
  ##     ptr = next(dram);
  ##     send (ptr, js);
  ##     dram += size(entry);
  ##     local_count += 1;
  ## }
  trantc_compute__intersect_ab.writeAction(f"yield") 
  ## one or both the lists exited --> whichever did fetch that
  ## update iter by how much ever was processed 
  ## check for bounds and fetch
  ## retain offs of the other one 
  trantc_compute__intersect_ab.writeAction(f"__if_intersect_ab_32_post: movlr 16(X20) X25 0 8") 
  trantc_compute__intersect_ab.writeAction(f"bneu X21 X23 __if_intersect_ab_35_post") 
  trantc_compute__intersect_ab.writeAction(f"__if_intersect_ab_33_true: add X25 X23 X25") 
  trantc_compute__intersect_ab.writeAction(f"movlr 0(X20) X26 0 8") 
  trantc_compute__intersect_ab.writeAction(f"bgtu X26 X25 __if_intersect_ab_35_post") 
  trantc_compute__intersect_ab.writeAction(f"__if_intersect_ab_39_true: movir X26 0") 
  trantc_compute__intersect_ab.writeAction(f"evlb X26 lm_allocator__spfree") 
  trantc_compute__intersect_ab.writeAction(f"evi X26 X26 255 4") 
  trantc_compute__intersect_ab.writeAction(f"ev X26 X26 X0 X0 8") 
  trantc_compute__intersect_ab.writeAction(f"movir X27 0") 
  trantc_compute__intersect_ab.writeAction(f"evlb X27 tc_compute::sp_free_ret") 
  trantc_compute__intersect_ab.writeAction(f"evi X27 X27 255 4") 
  trantc_compute__intersect_ab.writeAction(f"ev X27 X27 X0 X0 8") 
  trantc_compute__intersect_ab.writeAction(f"sendr_wcont X26 X27 X20 X20") 
  trantc_compute__intersect_ab.writeAction(f"evi X2 X26 tc__kv_reduce_return 1") 
  trantc_compute__intersect_ab.writeAction(f"sendr_wcont X26 X1 X18 X18") 
  ## update the loc tc
  trantc_compute__intersect_ab.writeAction(f"addi X7 X26 29856") 
  trantc_compute__intersect_ab.writeAction(f"movlr 0(X26) X28 0 8") 
  trantc_compute__intersect_ab.writeAction(f"add X28 X17 X29") 
  trantc_compute__intersect_ab.writeAction(f"movrl X29 0(X26) 0 8") 
  ## if (v1_id < threashold) {
  ##     unsigned long v1_deg = cached_nb[0];
  ##     print("V1 iteration ends. iter_a: %lu, v1_deg: %lu", iter_a, v1_deg);
  ##     print("Edge %u-%u intersect finished, tc count: %lu", v1_id, threashold, loc_tc);
  ## }
  trantc_compute__intersect_ab.writeAction(f"yield") 
  trantc_compute__intersect_ab.writeAction(f"__if_intersect_ab_35_post: movlr 48(X20) X26 0 8") 
  trantc_compute__intersect_ab.writeAction(f"bneu X22 X24 __if_intersect_ab_44_post") 
  trantc_compute__intersect_ab.writeAction(f"__if_intersect_ab_42_true: add X26 X24 X26") 
  trantc_compute__intersect_ab.writeAction(f"movlr 32(X20) X27 0 8") 
  trantc_compute__intersect_ab.writeAction(f"bgtu X27 X26 __if_intersect_ab_44_post") 
  trantc_compute__intersect_ab.writeAction(f"__if_intersect_ab_48_true: movir X27 0") 
  trantc_compute__intersect_ab.writeAction(f"evlb X27 lm_allocator__spfree") 
  trantc_compute__intersect_ab.writeAction(f"evi X27 X27 255 4") 
  trantc_compute__intersect_ab.writeAction(f"ev X27 X27 X0 X0 8") 
  trantc_compute__intersect_ab.writeAction(f"movir X28 0") 
  trantc_compute__intersect_ab.writeAction(f"evlb X28 tc_compute::sp_free_ret") 
  trantc_compute__intersect_ab.writeAction(f"evi X28 X28 255 4") 
  trantc_compute__intersect_ab.writeAction(f"ev X28 X28 X0 X0 8") 
  trantc_compute__intersect_ab.writeAction(f"sendr_wcont X27 X28 X20 X20") 
  trantc_compute__intersect_ab.writeAction(f"evi X2 X27 tc__kv_reduce_return 1") 
  trantc_compute__intersect_ab.writeAction(f"sendr_wcont X27 X1 X18 X18") 
  ## update the loc tc
  trantc_compute__intersect_ab.writeAction(f"addi X7 X27 29856") 
  trantc_compute__intersect_ab.writeAction(f"movlr 0(X27) X29 0 8") 
  trantc_compute__intersect_ab.writeAction(f"add X29 X17 X30") 
  trantc_compute__intersect_ab.writeAction(f"movrl X30 0(X27) 0 8") 
  ## if (v1_id < threashold) {
  ##     unsigned long v2_deg = cached_nb[4];
  ##     print("V2 iteration ends. iter_b: %lu, v2_deg: %lu", iter_b, v2_deg);
  ##     print("Edge %u-%u intersect finished, tc count: %lu", v1_id, threashold, loc_tc);
  ## }
  trantc_compute__intersect_ab.writeAction(f"yield") 
  trantc_compute__intersect_ab.writeAction(f"__if_intersect_ab_44_post: bneu X21 X23 __if_intersect_ab_53_post") 
  trantc_compute__intersect_ab.writeAction(f"__if_intersect_ab_51_true: movlr 8(X20) X28 0 8") 
  trantc_compute__intersect_ab.writeAction(f"sli X25 X29 3") 
  trantc_compute__intersect_ab.writeAction(f"add X28 X29 X27") 
  trantc_compute__intersect_ab.writeAction(f"send_dmlm_ld_wret X27 tc_compute::v1_nblist_read_ret 8 X28") 
  trantc_compute__intersect_ab.writeAction(f"movir X21 0") 
  trantc_compute__intersect_ab.writeAction(f"addi X19 X19 1") 
  trantc_compute__intersect_ab.writeAction(f"__if_intersect_ab_53_post: bneu X22 X24 __if_intersect_ab_56_post") 
  trantc_compute__intersect_ab.writeAction(f"__if_intersect_ab_54_true: movlr 40(X20) X28 0 8") 
  trantc_compute__intersect_ab.writeAction(f"sli X26 X29 3") 
  trantc_compute__intersect_ab.writeAction(f"add X28 X29 X27") 
  trantc_compute__intersect_ab.writeAction(f"send_dmlm_ld_wret X27 tc_compute::v2_nblist_read_ret 8 X28") 
  trantc_compute__intersect_ab.writeAction(f"movir X22 0") 
  trantc_compute__intersect_ab.writeAction(f"addi X19 X19 1") 
  trantc_compute__intersect_ab.writeAction(f"__if_intersect_ab_56_post: movrl X25 16(X20) 0 8") 
  trantc_compute__intersect_ab.writeAction(f"movrl X21 24(X20) 0 8") 
  trantc_compute__intersect_ab.writeAction(f"movrl X26 48(X20) 0 8") 
  trantc_compute__intersect_ab.writeAction(f"movrl X22 56(X20) 0 8") 
  trantc_compute__intersect_ab.writeAction(f"yield") 
  
  # Writing code for event tc_compute::v1_nblist_read_ret
  trantc_compute__v1_nblist_read_ret = efa.writeEvent('tc_compute::v1_nblist_read_ret')
  trantc_compute__v1_nblist_read_ret.writeAction(f"entry: subi X19 X19 1") 
  trantc_compute__v1_nblist_read_ret.writeAction(f"addi X20 X21 64") 
  trantc_compute__v1_nblist_read_ret.writeAction(f"bcpyoli X8 X21 8") 
  trantc_compute__v1_nblist_read_ret.writeAction(f"bneiu X19 0 __if_v1_nblist_read_ret_2_post") 
  trantc_compute__v1_nblist_read_ret.writeAction(f"__if_v1_nblist_read_ret_0_true: evi X2 X22 tc_compute::intersect_ab 1") 
  trantc_compute__v1_nblist_read_ret.writeAction(f"sendr_wcont X22 X1 X18 X20") 
  trantc_compute__v1_nblist_read_ret.writeAction(f"__if_v1_nblist_read_ret_2_post: yield") 
  
  # Writing code for event tc_compute::v2_nblist_read_ret
  trantc_compute__v2_nblist_read_ret = efa.writeEvent('tc_compute::v2_nblist_read_ret')
  trantc_compute__v2_nblist_read_ret.writeAction(f"entry: subi X19 X19 1") 
  trantc_compute__v2_nblist_read_ret.writeAction(f"addi X20 X21 128") 
  trantc_compute__v2_nblist_read_ret.writeAction(f"bcpyoli X8 X21 8") 
  trantc_compute__v2_nblist_read_ret.writeAction(f"bneiu X19 0 __if_v2_nblist_read_ret_2_post") 
  trantc_compute__v2_nblist_read_ret.writeAction(f"__if_v2_nblist_read_ret_0_true: evi X2 X22 tc_compute::intersect_ab 1") 
  trantc_compute__v2_nblist_read_ret.writeAction(f"sendr_wcont X22 X1 X18 X20") 
  trantc_compute__v2_nblist_read_ret.writeAction(f"__if_v2_nblist_read_ret_2_post: yield") 
  
  # Writing code for event tc_compute::sp_free_ret
  trantc_compute__sp_free_ret = efa.writeEvent('tc_compute::sp_free_ret')
  trantc_compute__sp_free_ret.writeAction(f"entry: yield_terminate") 
  
  
  ##########################################
  ###### Writing code for thread main ######
  ##########################################
  # Writing code for event main::init
  tranmain__init = efa.writeEvent('main::init')
  tranmain__init.writeAction(f"entry: addi X7 X17 704") 
  tranmain__init.writeAction(f"addi X7 X18 29872") 
  tranmain__init.writeAction(f"movir X19 0") 
  tranmain__init.writeAction(f"evlb X19 tc_broadcast__broadcast_global") 
  tranmain__init.writeAction(f"evi X19 X19 255 4") 
  tranmain__init.writeAction(f"ev X19 X19 X0 X0 8") 
  tranmain__init.writeAction(f"movir X20 0") 
  tranmain__init.writeAction(f"evlb X20 main_broadcast_init::setup_spd") 
  tranmain__init.writeAction(f"evi X20 X20 255 4") 
  tranmain__init.writeAction(f"ev X20 X20 X0 X0 8") 
  tranmain__init.writeAction(f"movrl X10 0(X17) 0 8") 
  tranmain__init.writeAction(f"movrl X20 8(X17) 0 8") 
  tranmain__init.writeAction(f"movrl X11 16(X17) 0 8") 
  tranmain__init.writeAction(f"send_wcont X19 X2 X17 8") 
  tranmain__init.writeAction(f"movrl X8 0(X17) 0 8") 
  tranmain__init.writeAction(f"movrl X9 8(X17) 0 8") 
  tranmain__init.writeAction(f"movrl X10 16(X17) 0 8") 
  tranmain__init.writeAction(f"movrl X11 0(X18) 0 8") 
  tranmain__init.writeAction(f"movrl X12 8(X18) 0 8") 
  tranmain__init.writeAction(f"movrl X18 24(X17) 0 8") 
  tranmain__init.writeAction(f"addi X18 X18 16") 
  tranmain__init.writeAction(f"movrl X13 0(X18) 0 8") 
  tranmain__init.writeAction(f"movrl X18 32(X17) 0 8") 
  tranmain__init.writeAction(f"movir X19 0") 
  tranmain__init.writeAction(f"evlb X19 tc__map_shuffle_reduce") 
  tranmain__init.writeAction(f"evi X19 X19 255 4") 
  tranmain__init.writeAction(f"ev X19 X19 X0 X0 8") 
  tranmain__init.writeAction(f"send_wret X19 main::combine_tc X17 8 X23") 
  tranmain__init.writeAction(f"addi X10 X16 0") 
  tranmain__init.writeAction(f"addi X7 X21 29856") 
  tranmain__init.writeAction(f"movlr 0(X21) X22 0 8") 
  tranmain__init.writeAction(f"print 'Initial triangle count: %lu' X22") 
  tranmain__init.writeAction(f"yield") 
  
  # Writing code for event main::combine_tc
  tranmain__combine_tc = efa.writeEvent('main::combine_tc')
  tranmain__combine_tc.writeAction(f"entry: print 'UDKVMSR finished, executed %lu reduce tasks.' X8") 
  tranmain__combine_tc.writeAction(f"perflog 1 0 'UDKVMSR finished'") 
  tranmain__combine_tc.writeAction(f"movir X17 0") 
  tranmain__combine_tc.writeAction(f"movir X18 0") 
  tranmain__combine_tc.writeAction(f"evlb X18 tc_accumulate__init_global_snyc") 
  tranmain__combine_tc.writeAction(f"evi X18 X18 255 4") 
  tranmain__combine_tc.writeAction(f"ev X18 X18 X0 X0 8") 
  tranmain__combine_tc.writeAction(f"sendr_wret X18 main::term X16 X17 X19") 
  tranmain__combine_tc.writeAction(f"yield") 
  
  # Writing code for event main::term
  tranmain__term = efa.writeEvent('main::term')
  tranmain__term.writeAction(f"entry: print 'Total triangle count: %lu' X8") 
  tranmain__term.writeAction(f"perflog 1 0 'TC finished'") 
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
  tranmain_broadcast_init__setup_spd.writeAction(f"entry: addi X7 X16 29864") 
  tranmain_broadcast_init__setup_spd.writeAction(f"movir X18 29872") 
  tranmain_broadcast_init__setup_spd.writeAction(f"movrl X18 0(X16) 0 8") 
  tranmain_broadcast_init__setup_spd.writeAction(f"addi X7 X16 29856") 
  tranmain_broadcast_init__setup_spd.writeAction(f"movir X18 0") 
  tranmain_broadcast_init__setup_spd.writeAction(f"movrl X18 0(X16) 0 8") 
  tranmain_broadcast_init__setup_spd.writeAction(f"addi X7 X16 29848") 
  tranmain_broadcast_init__setup_spd.writeAction(f"movrl X8 0(X16) 0 8") 
  tranmain_broadcast_init__setup_spd.writeAction(f"yield_terminate") 
  
