from linker.EFAProgram import efaProgram, EFAProgram
from libraries.UDMapShuffleReduce.linkable.LinkableKVMapShuffleReduceTPL import UDKeyValueMapShuffleReduceTemplate


"""================ START CONFIGURATION ================"""

from libraries.UDMapShuffleReduce.utils.OneDimArrayKeyValueSet import OneDimKeyValueSet
from libraries.UDMapShuffleReduce.utils.IntermediateKeyValueSet import IntermediateKeyValueSet
# from libraries.UDMapShuffleReduce.utils.SHTKeyValueSet import SHTKeyValueSet
from libraries.SingleLaneSort.hybrid_single_lane import SingleLaneSort

import LMStaticMap as Defs

'''
UDKVMSR program configuration. The following parameters are required:
    task_name:      unique identifier for each UDKVMSR program.
    metadata_offset:   offset of the metadata in bytes. Reserve 32 words on each lane, starting from the offset.
    debug_flag:     enable debug print (optional), default is False
'''
TASK_NAME       = "DistributedSortPhase3"
METADATA_OFFSET = Defs.UDKVMSR_0_OFFSET
DEBUG_FLAG      = False
MAX_MAP_THREAD_PER_LANE     = 10
MAX_REDUCE_THREAD_PER_LANE  = 10

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


INPUT_KVSET = OneDimKeyValueSet("Dsort_input3", element_size=1, metadata_size=2)
# INTERMEDIATE_KVSET = OneDimKeyValueSet("Dsort_intermediate", element_size=2, metadata_size=4)
INTERMEDIATE_KVSET =IntermediateKeyValueSet("Dsort_intermediate3", key_size=1, value_size=2)


"""================  END CONFIGURATION  ================"""

# class TestMapShuffleReduce(UDKeyValueMapShuffleReduceTemplate):


@efaProgram
def GenKMerCntMSREFA(efa: EFAProgram):

    testMSR = UDKeyValueMapShuffleReduceTemplate(efa=efa, task_name=TASK_NAME, meta_data_offset=METADATA_OFFSET, debug_flag=DEBUG_FLAG)
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

    # test_sort_sp = SingleLaneSort(testMSR.efa, 'DistributedSortPhase3LocalSort', 0, 'X31', False)

    return efa
