from linker.EFAProgram import efaProgram, EFAProgram
# from libraries.UDMapShuffleReduce.linkable.LinkableKVMapShuffleReduceTPL import UDKeyValueMapShuffleReduceTemplate
from libraries.UDMapShuffleReduce.linkable.LinkableKVMapShuffleCombineTPL import UDKeyValueMapShuffleReduceTemplate


"""================ START CONFIGURATION ================"""

from libraries.UDMapShuffleReduce.utils.OneDimArrayKeyValueSet import OneDimKeyValueSet
from libraries.UDMapShuffleReduce.utils.IntermediateKeyValueSet import IntermediateKeyValueSet
# from libraries.UDMapShuffleReduce.utils.SHTKeyValueSet import SHTKeyValueSet
from libraries.UDMapShuffleReduce.linkable.LinkableLMCache import LMCache

import LMStaticMap as Defs

'''
UDKVMSR program configuration. The following parameters are required:
    task_name:      unique identifier for each UDKVMSR program.
    metadata_offset:   offset of the metadata in bytes. Reserve 32 words on each lane, starting from the offset.
    debug_flag:     enable debug print (optional), default is False
'''
TASK_NAME       = "DistributedSortPhase1Insertion"
METADATA_OFFSET = Defs.UDKVMSR_0_OFFSET
DEBUG_FLAG      = False
DEBUG_FLAG_CACHE      = False

MAX_MAP_THREAD_PER_LANE     = 1
MAX_REDUCE_THREAD_PER_LANE  = 1


SORT_OFFSET = 20000
COUNTERS_OFFSET = 256

# The usage of kv_combine is optional. If not enabled, set ENABLE_COMBINE to False.
ENABLE_COMBINE      = False
'''
Cache configuration. Required if kv_combine is used in reduce.
    cache_offset:   scratchpad bank offset (Bytes) for the cache. 
    num_entries:    number of entries per lane
    entry_size:     size of each entry (in words)
'''
# CACHE_LM_OFFSET     = Defs.CACHE_0_OFFSET
# CACHE_NUM_ENTRIES   = 128
# CACHE_ENTRY_SIZE    = 2

'''
Define the input, intermediate and output key value set.
Available key value set types:
    OneDimKeyValueSet:          One dimensional array in DRAM, key is implicitly the index of the array, value is the element in the array.
                                Init parameters:
                                    name         - name of the key value set
                                    element_size - size of each element in the array (in words)
    IntermediateKeyValueSet:    Dummy set for intermediate key-value pair emitted by map task.
                                Init parameters:
                                    name        - name of the key value set
                                    key_size    - size of the key (in words)
                                    value_size  - size of the value (in words)
    SHTKeyValueSet:             Multi-word scalable hash table.
                                Init parameters:
                                    name        - name of the key value set
                                    value_size  - size of the value (in words)
    SingleWordSHTKeyValueSet:   Single-word scalable hash table.
                                Init parameters:
                                    name        - name of the key value set
'''
# Input array configuration
# INPUT_KVSET = SHTKeyValueSet(name=f"{TASK_NAME}_input", value_size=2)

# # Reduce is optional. If not enabled, set ENABLE_REDUCE to False.
ENABLE_REDUCE = False
# # Intermediate key value pair configuration
# INTERMEDIATE_KEY_SIZE = 1
# INTERMEDIATE_VALUE_SIZE = 1
# INTERMEDIATE_KVSET = IntermediateKeyValueSet(name=f"{TASK_NAME}_intermediate", key_size=INTERMEDIATE_KEY_SIZE, value_size=INTERMEDIATE_VALUE_SIZE)

# Output array configuration
# OUTPUT_ARRAY_ELEMENT_SIZE = 1
# OUTPUT_KVSET = OneDimKeyValueSet(name=f"{TASK_NAME}_output", element_size=OUTPUT_ARRAY_ELEMENT_SIZE, argument_size=1)


INPUT_KVSET = OneDimKeyValueSet("Dsort_phase1_insertion_input", element_size=1, metadata_size=4)
# INTERMEDIATE_KVSET = OneDimKeyValueSet("Dsort_intermediate", element_size=2, metadata_size=4)
INTERMEDIATE_KVSET =IntermediateKeyValueSet("Dsort_phase1_insertion_intermediate", key_size=1, value_size=1)


"""================  END CONFIGURATION  ================"""

class TestMapShuffleReduce(UDKeyValueMapShuffleReduceTemplate):
    pass
    def kv_reduce_loc(self, tran: EFAProgram.Transition, key: str, num_lanes_mask:str, base_lane: str, dest_id: str):
        '''
        User-defined mapping from a key to a reducer lane (id). Default implementation is a hash.
        Can be overwritten by the user and changed to customized mapping.
        Parameter
            tran:       EFAProgram.Transition (codelet) triggered by the map event
            key:        name of the register/operand buffer entry containing the key
            result:     name of the register reserved for storing the destination lane id
        '''
        hash_seed = 41
        tran.writeAction(f"movir {dest_id} {hash_seed}")
        tran.writeAction(f"hash {key} {dest_id}")
        tran.writeAction(f"sri {dest_id} {dest_id} {1}")
        # if self.extension == 'load_balancer':
        #     tran.writeAction(f"subi {num_lanes_mask} {num_lanes_mask} {1}")
        tran.writeAction(f"and {dest_id} {num_lanes_mask} {dest_id}")
        tran.writeAction(f"add {dest_id} {base_lane} {dest_id}")
        # tran.writeAction(f"add {base_lane} {key} {dest_id}")
        # tran.writeAction(f"print 'base_lane %d key %d dest_id %d' {base_lane} {key} {dest_id}")

# def cache_combine_func(tran: EFAProgram.Transition, key: str, values: list, cached_values: list, result_regs: list, scratch: list, combine_fail_label: str, label_prefix: str):
#     '''
#     Default combine function.
#     Parameters:
#         tran:               EFAProgram.Transition
#         key:                Register name of the key to be updated
#         values:             list of Register names of the values to be updated. List length equals to value_size.
#         cached_values:      list of Register names of the cached values. List length equals to value_size.
#         result_regs:        list of Register names for storing the combined results. List length equals to value_size.
#         combine_fail_label: Branch label for failure.
#         label_prefix:       Prefix for the branch labels. 
#     '''
    
#     for i in range(len(values)):
#         tran.writeAction(f"add {values[i]} {cached_values[i]} {result_regs[i]}")
#         # if selfdebug_flag:
#         if DEBUG_FLAG_CACHE:
#             tran.writeAction(f"print '[DEBUG][NWID %ld][combing_func] key %ld combine result value %ld' {'X0'} {key} {result_regs[i]}")

@efaProgram
def GenKMerCntMSREFA(efa: EFAProgram):

    testMSR = TestMapShuffleReduce(efa=efa, task_name=TASK_NAME, meta_data_offset=METADATA_OFFSET, debug_flag=DEBUG_FLAG)
    testMSR.set_input_kvset(INPUT_KVSET)
    testMSR.set_intermediate_kvset(INTERMEDIATE_KVSET)
    if ENABLE_REDUCE:
        testMSR.set_output_kvset(OUTPUT_KVSET)

    if ENABLE_COMBINE:
        testMSR.setup_cache(cache_offset=CACHE_LM_OFFSET, num_entries=CACHE_NUM_ENTRIES, entry_size=CACHE_ENTRY_SIZE)
    # if ENABLE_REDUCE:
    testMSR.set_max_thread_per_lane(max_map_th_per_lane=MAX_MAP_THREAD_PER_LANE, max_reduce_th_per_lane=MAX_REDUCE_THREAD_PER_LANE)
    # else:
    #     testMSR.set_max_thread_per_lane(max_map_th_per_lane=MAX_MAP_THREAD_PER_LANE)

    testMSR.generate_udkvmsr_task()


    # cache_data_store = OneDimKeyValueSet(f"phase1_cache_data_store", element_size=1)
    # cache = LMCache(state=testMSR.state, identifier="phase1_bin_size_cache", cache_offset = SORT_OFFSET + COUNTERS_OFFSET, num_entries = 2048, policy=LMCache.Policy.WRITE_BACK, 
    #         entry_size = 2, data_store = cache_data_store, metadata_offset = Defs.CACHE_0_OFFSET, debug_flag = DEBUG_FLAG_CACHE, combine_func=cache_combine_func)

    return efa
