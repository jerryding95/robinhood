from linker.EFAProgram import efaProgram, EFAProgram

#from libraries.UDMapShuffleReduce.linkable.LinkableKVMapShuffleReduceTPL import UDKeyValueMapShuffleReduceTemplate
from libraries.UDMapShuffleReduce.linkable.LinkableKVMapShuffleCombineTPL import UDKeyValueMapShuffleReduceTemplate
from spmvConfig import *

EXTENSION = 'non_load_balancing'
test_ws = False
test_random = False
DEBUG_FLAG = False
LB_TYPE = ['mapper']
rtype = 'lane' if test_ws else 'ud'
multi = not test_ws
map_ws = test_ws
red_ws = test_ws

@efaProgram
def GenLinkableMapShuffleReduceEFA(efa: EFAProgram):

    # testMSR = UDKeyValueMapShuffleReduceTemplate(efa=efa, task_name=TASK_NAME, meta_data_offset=METADATA_OFFSET, debug_flag=False, extension='load_balancer', test_map_ws=False)
    testMSR = UDKeyValueMapShuffleReduceTemplate(efa=efa, task_name=TASK_NAME, meta_data_offset=METADATA_OFFSET, debug_flag=DEBUG_FLAG, 
                                                extension = EXTENSION, load_balancer_type = LB_TYPE, grlb_type = rtype, 
                                                claim_multiple_work = multi, test_map_ws=map_ws, test_reduce_ws=red_ws, random_lb=test_random)
    testMSR.set_input_kvset(INPUT_KVSET)
    if ENABLE_REDUCE:
        testMSR.set_intermediate_kvset(INTERMEDIATE_KVSET)
        testMSR.set_output_kvset(OUTPUT_KVSET)
    
    if ENABLE_COMBINE:
        testMSR.setup_cache(cache_offset=CACHE_LM_OFFSET, num_entries=CACHE_NUM_ENTRIES, entry_size=CACHE_ENTRY_SIZE)
    if ENABLE_REDUCE:
        testMSR.set_max_thread_per_lane(max_map_th_per_lane=MAX_MAP_THREAD_PER_LANE, max_reduce_th_per_lane=MAX_REDUCE_THREAD_PER_LANE)
    else:
        testMSR.set_max_thread_per_lane(max_map_th_per_lane=MAX_MAP_THREAD_PER_LANE)

    testMSR.generate_udkvmsr_task()

    
    return efa