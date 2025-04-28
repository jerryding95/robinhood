from linker.EFAProgram import efaProgram

## Global constants

@efaProgram
def EFA_gcn(efa):
  efa.code_level = 'machine'
  state0 = efa.State("udweave_init") #Only one state code 
  efa.add_initId(state0.state_id)
  ## Static declarations
  ## Param "ARRAY" uses Register X8, scope (0->7)
  ## Param "LENGTH" uses Register X9, scope (0->7)
  ## Param "PARTITION_ARRAY" uses Register X10, scope (0->7)
  ## Param "PART_PER_LANE" uses Register X11, scope (0->7)
  ## Param "NUM_WORKER" uses Register X12, scope (0->7)
  ## Param "interSpace" uses Register X13, scope (0->7)
  ## Scoped Variable "TMP_LM_DESC" uses Register X16, scope (0->7)
  ## Scoped Variable "TMP_SP_DESC" uses Register X17, scope (0->7)
  ## Scoped Variable "evword" uses Register X18, scope (0->7)
  ## Scoped Variable "cont_word" uses Register X19, scope (0->7)
  ## Scoped Variable "TMP_LM_DESC" uses Register X16, scope (0->8)
  ## Scoped Variable "COUNTER" uses Register X16, scope (0)
  ## Param "V_SRC" uses Register X8, scope (0->10)
  ## Param "V_DST" uses Register X9, scope (0->10)
  ## Scoped Variable "TMP_LM_DESC" uses Register X17, scope (0->10)
  ## Scoped Variable "TMP_EV_WORD" uses Register X18, scope (0->10)
  ## Param "V_DST" uses Register X8, scope (0->11)
  ## Param "V_SRC" uses Register X9, scope (0->11)
  ## Param "E_ADDR" uses Register X10, scope (0->11)
  ## Scoped Variable "TMP_EV_WORD" uses Register X17, scope (0->11)
  ## Scoped Variable "i" uses Register X17, scope (0->12)
  ## Scoped Variable "iter_times" uses Register X18, scope (0->12)
  ## Scoped Variable "TMP_EV_WORD" uses Register X19, scope (0->12)
  ## Scoped Variable "TMP_EV_WORD" uses Register X17, scope (0->18)
  
  EXTENSION = 'non_load_balancing'
  test_ws = False
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
  from libraries.LMStaticMaps.LMStaticMap import UDKVMSR_0_OFFSET
  
  task_name = 'gnn_vanilla_kvmsr'
  gnnMSR = UDKeyValueMapShuffleReduceTemplate(efa=efa, task_name=task_name, meta_data_offset=UDKVMSR_0_OFFSET, debug_flag=DEBUG_FLAG,
  extension = EXTENSION, load_balancer_type = LB_TYPE, grlb_type = rtype,
  claim_multiple_work = multi, test_map_ws=map_ws, test_reduce_ws=red_ws, random_lb=test_random)
  gnnMSR.set_input_kvset(OneDimKeyValueSet('gnn_input', element_size=2) )
  gnnMSR.set_intermediate_kvset(IntermediateKeyValueSet('gnn_intermediate', key_size=1, value_size=2))
  gnnMSR.set_max_thread_per_lane(max_map_th_per_lane=64, max_reduce_th_per_lane=128, max_reduce_key_to_claim = 1)
  gnnMSR.setup_lb_cache(intermediate_cache_num_bins = 64, intermediate_cache_size = 512, materialize_kv_cache_size = 512)
  print(gnnMSR.heap_offset)
  
  gnnMSR.generate_udkvmsr_task()
  
  
  ########################################################
  ###### Writing code for thread gnn_vanilla_master ######
  ########################################################
  # Writing code for event gnn_vanilla_master::gnn_start
  trangnn_vanilla_master__gnn_start = efa.writeEvent('gnn_vanilla_master::gnn_start')
  trangnn_vanilla_master__gnn_start.writeAction(f"entry: perflog 1 1 'GNN started'") 
  trangnn_vanilla_master__gnn_start.writeAction(f"print 'GNN started'") 
  trangnn_vanilla_master__gnn_start.writeAction(f"addi X7 X16 8") 
  trangnn_vanilla_master__gnn_start.writeAction(f"addi X7 X17 256") 
  trangnn_vanilla_master__gnn_start.writeAction(f"movrl X8 0(X17) 0 8") 
  trangnn_vanilla_master__gnn_start.writeAction(f"movrl X9 8(X17) 0 8") 
  trangnn_vanilla_master__gnn_start.writeAction(f"movrl X13 16(X17) 0 8") 
  trangnn_vanilla_master__gnn_start.writeAction(f"movrl X10 0(X16) 0 8") 
  trangnn_vanilla_master__gnn_start.writeAction(f"movrl X11 8(X16) 0 8") 
  trangnn_vanilla_master__gnn_start.writeAction(f"movrl X12 16(X16) 0 8") 
  trangnn_vanilla_master__gnn_start.writeAction(f"movrl X17 24(X16) 0 8") 
  trangnn_vanilla_master__gnn_start.writeAction(f"addi X17 X19 16") 
  trangnn_vanilla_master__gnn_start.writeAction(f"movrl X19 32(X16) 0 8") 
  trangnn_vanilla_master__gnn_start.writeAction(f"movir X18 0") 
  trangnn_vanilla_master__gnn_start.writeAction(f"evlb X18 gnn_vanilla_kvmsr__map_shuffle_reduce") 
  trangnn_vanilla_master__gnn_start.writeAction(f"evi X18 X18 255 4") 
  trangnn_vanilla_master__gnn_start.writeAction(f"ev X18 X18 X0 X0 8") 
  trangnn_vanilla_master__gnn_start.writeAction(f"evi X2 X19 gnn_vanilla_master::gnn_term 1") 
  trangnn_vanilla_master__gnn_start.writeAction(f"send_wcont X18 X19 X16 5") 
  trangnn_vanilla_master__gnn_start.writeAction(f"yield") 
  
  # Writing code for event gnn_vanilla_master::gnn_term
  trangnn_vanilla_master__gnn_term = efa.writeEvent('gnn_vanilla_master::gnn_term')
  trangnn_vanilla_master__gnn_term.writeAction(f"entry: movir X17 65528") 
  trangnn_vanilla_master__gnn_term.writeAction(f"add X7 X17 X16") 
  trangnn_vanilla_master__gnn_term.writeAction(f"perflog 1 1 'GNN finished'") 
  trangnn_vanilla_master__gnn_term.writeAction(f"print 'GNN finished'") 
  trangnn_vanilla_master__gnn_term.writeAction(f"movir X18 1") 
  trangnn_vanilla_master__gnn_term.writeAction(f"movrl X18 0(X16) 0 8") 
  trangnn_vanilla_master__gnn_term.writeAction(f"yield_terminate") 
  
  
  #######################################################
  ###### Writing code for thread gnn_vanilla_kvmsr ######
  #######################################################
  # Writing code for event gnn_vanilla_kvmsr::kv_map
  trangnn_vanilla_kvmsr__kv_map = efa.writeEvent('gnn_vanilla_kvmsr::kv_map')
  ## print("kv_map_start,%ld,%ld.", V_DST, V_SRC);
  trangnn_vanilla_kvmsr__kv_map.writeAction(f"entry: addi X7 X17 8") 
  trangnn_vanilla_kvmsr__kv_map.writeAction(f"movrl X9 0(X17) 0 8") 
  trangnn_vanilla_kvmsr__kv_map.writeAction(f"movrl X8 8(X17) 0 8") 
  trangnn_vanilla_kvmsr__kv_map.writeAction(f"movir X19 0") 
  trangnn_vanilla_kvmsr__kv_map.writeAction(f"movrl X19 16(X17) 0 8") 
  trangnn_vanilla_kvmsr__kv_map.writeAction(f"movir X18 0") 
  trangnn_vanilla_kvmsr__kv_map.writeAction(f"evlb X18 gnn_vanilla_kvmsr__kv_map_emit") 
  trangnn_vanilla_kvmsr__kv_map.writeAction(f"evi X18 X18 255 4") 
  trangnn_vanilla_kvmsr__kv_map.writeAction(f"ev X18 X18 X0 X0 8") 
  trangnn_vanilla_kvmsr__kv_map.writeAction(f"send_wcont X18 X1 X17 3") 
  trangnn_vanilla_kvmsr__kv_map.writeAction(f"evi X2 X18 gnn_vanilla_kvmsr__kv_map_return 1") 
  trangnn_vanilla_kvmsr__kv_map.writeAction(f"sendr_wcont X18 X1 X8 X9") 
  trangnn_vanilla_kvmsr__kv_map.writeAction(f"yield") 
  
  # Writing code for event gnn_vanilla_kvmsr::kv_reduce
  trangnn_vanilla_kvmsr__kv_reduce = efa.writeEvent('gnn_vanilla_kvmsr::kv_reduce')
  trangnn_vanilla_kvmsr__kv_reduce.writeAction(f"entry: movir X16 2") 
  ## fetch data
  ## print("kv_reduce_start,%ld,%ld.", V_DST, V_SRC);
  trangnn_vanilla_kvmsr__kv_reduce.writeAction(f"evi X2 X17 gnn_vanilla_kvmsr::kv_reduce_compute 1") 
  trangnn_vanilla_kvmsr__kv_reduce.writeAction(f"movir X18 0") 
  trangnn_vanilla_kvmsr__kv_reduce.writeAction(f"sendr_wcont X17 X1 X18 X18") 
  trangnn_vanilla_kvmsr__kv_reduce.writeAction(f"movir X18 0") 
  trangnn_vanilla_kvmsr__kv_reduce.writeAction(f"sendr_wcont X17 X1 X18 X18") 
  trangnn_vanilla_kvmsr__kv_reduce.writeAction(f"yield") 
  
  # Writing code for event gnn_vanilla_kvmsr::kv_reduce_compute
  trangnn_vanilla_kvmsr__kv_reduce_compute = efa.writeEvent('gnn_vanilla_kvmsr::kv_reduce_compute')
  trangnn_vanilla_kvmsr__kv_reduce_compute.writeAction(f"entry: subi X16 X16 1") 
  trangnn_vanilla_kvmsr__kv_reduce_compute.writeAction(f"bleiu X16 0 __if_kv_reduce_compute_2_post") 
  trangnn_vanilla_kvmsr__kv_reduce_compute.writeAction(f"__if_kv_reduce_compute_0_true: yield") 
  trangnn_vanilla_kvmsr__kv_reduce_compute.writeAction(f"__if_kv_reduce_compute_2_post: movir X17 0") 
  trangnn_vanilla_kvmsr__kv_reduce_compute.writeAction(f"movir X18 1024") 
  trangnn_vanilla_kvmsr__kv_reduce_compute.writeAction(f"movir X17 0") 
  trangnn_vanilla_kvmsr__kv_reduce_compute.writeAction(f"__for_kv_reduce_compute_3_condition: bleu X18 X17 __for_kv_reduce_compute_5_post") 
  trangnn_vanilla_kvmsr__kv_reduce_compute.writeAction(f"__for_kv_reduce_compute_4_body: addi X17 X17 0") 
  trangnn_vanilla_kvmsr__kv_reduce_compute.writeAction(f"addi X17 X17 1") 
  trangnn_vanilla_kvmsr__kv_reduce_compute.writeAction(f"jmp __for_kv_reduce_compute_3_condition") 
  ## write data
  trangnn_vanilla_kvmsr__kv_reduce_compute.writeAction(f"__for_kv_reduce_compute_5_post: movir X16 2") 
  trangnn_vanilla_kvmsr__kv_reduce_compute.writeAction(f"evi X2 X19 gnn_vanilla_kvmsr::kv_reduce_write_back 1") 
  trangnn_vanilla_kvmsr__kv_reduce_compute.writeAction(f"movir X20 0") 
  trangnn_vanilla_kvmsr__kv_reduce_compute.writeAction(f"sendr_wcont X19 X1 X20 X20") 
  trangnn_vanilla_kvmsr__kv_reduce_compute.writeAction(f"movir X20 0") 
  trangnn_vanilla_kvmsr__kv_reduce_compute.writeAction(f"sendr_wcont X19 X1 X20 X20") 
  trangnn_vanilla_kvmsr__kv_reduce_compute.writeAction(f"yield") 
  
  # Writing code for event gnn_vanilla_kvmsr::kv_reduce_write_back
  trangnn_vanilla_kvmsr__kv_reduce_write_back = efa.writeEvent('gnn_vanilla_kvmsr::kv_reduce_write_back')
  trangnn_vanilla_kvmsr__kv_reduce_write_back.writeAction(f"entry: subi X16 X16 1") 
  trangnn_vanilla_kvmsr__kv_reduce_write_back.writeAction(f"bleiu X16 0 __if_kv_reduce_write_back_2_post") 
  trangnn_vanilla_kvmsr__kv_reduce_write_back.writeAction(f"__if_kv_reduce_write_back_0_true: yield") 
  ## print("reduce_finish");
  trangnn_vanilla_kvmsr__kv_reduce_write_back.writeAction(f"__if_kv_reduce_write_back_2_post: evi X2 X17 gnn_vanilla_kvmsr__kv_reduce_return 1") 
  trangnn_vanilla_kvmsr__kv_reduce_write_back.writeAction(f"movir X18 0") 
  trangnn_vanilla_kvmsr__kv_reduce_write_back.writeAction(f"sendr_wcont X17 X1 X18 X18") 
  trangnn_vanilla_kvmsr__kv_reduce_write_back.writeAction(f"yield") 
  
