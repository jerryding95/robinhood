#ifndef __tc_udkvmsr_exe_nlb_H__
#define __tc_udkvmsr_exe_nlb_H__

namespace tc_udkvmsr_exe_nlb {

    typedef unsigned int EventSymbol;

    constexpr EventSymbol lm_allocator__spmalloc = 0;
    constexpr EventSymbol lm_allocator__spfree = 1;
    constexpr EventSymbol tc_broadcast__broadcast_global = 2;
    constexpr EventSymbol tc_broadcast__broadcast_node = 3;
    constexpr EventSymbol tc_broadcast__broadcast_ud = 4;
    constexpr EventSymbol tc_broadcast__broadcast_ud_fin = 5;
    constexpr EventSymbol tc_broadcast__broadcast_node_fin = 6;
    constexpr EventSymbol tc_broadcast__broadcast_global_fin = 7;
    constexpr EventSymbol tc_broadcast__broadcast_value_to_scratchpad = 8;
    constexpr EventSymbol tc__map_shuffle_reduce = 9;
    constexpr EventSymbol tc__finish_init_udkvmsr = 10;
    constexpr EventSymbol tc_input__generate_partition_array = 11;
    constexpr EventSymbol tc_input__write_partition_array_return = 12;
    constexpr EventSymbol tc__broadcast_global = 13;
    constexpr EventSymbol tc__broadcast_node = 14;
    constexpr EventSymbol tc__broadcast_ud = 15;
    constexpr EventSymbol tc__broadcast_ud_fin = 16;
    constexpr EventSymbol tc__broadcast_node_fin = 17;
    constexpr EventSymbol tc__broadcast_global_fin = 18;
    constexpr EventSymbol tc__broadcast_value_to_scratchpad = 19;
    constexpr EventSymbol tc__init_input_kvset_on_lane = 20;
    constexpr EventSymbol tc__init_sp_lane = 21;
    constexpr EventSymbol tc__init_global_master = 22;
    constexpr EventSymbol tc__global_master = 23;
    constexpr EventSymbol tc__init_node_master = 24;
    constexpr EventSymbol tc__node_master = 25;
    constexpr EventSymbol tc__termiante_node_master = 26;
    constexpr EventSymbol tc__init_updown_master = 27;
    constexpr EventSymbol tc__updown_master = 28;
    constexpr EventSymbol tc__terminate_updown_master = 29;
    constexpr EventSymbol tc__lane_master_init = 30;
    constexpr EventSymbol tc__lane_master_loop = 31;
    constexpr EventSymbol tc__lane_master_read_partition = 32;
    constexpr EventSymbol tc__lane_master_get_next_return = 33;
    constexpr EventSymbol tc__lane_master_terminate = 34;
    constexpr EventSymbol tc__init_global_snyc = 35;
    constexpr EventSymbol tc__init_node_sync = 36;
    constexpr EventSymbol tc__ud_accumulate = 37;
    constexpr EventSymbol tc__global_sync_return = 38;
    constexpr EventSymbol tc__node_sync_return = 39;
    constexpr EventSymbol tc__kv_map_emit = 40;
    constexpr EventSymbol tc__kv_reduce_emit = 41;
    constexpr EventSymbol tc__kv_map_return = 42;
    constexpr EventSymbol tc__init_reduce_thread = 43;
    constexpr EventSymbol tc__kv_reduce_return = 44;
    constexpr EventSymbol tc_accumulate__init_global_snyc = 45;
    constexpr EventSymbol tc_accumulate__init_node_sync = 46;
    constexpr EventSymbol tc_accumulate__ud_accumulate = 47;
    constexpr EventSymbol tc_accumulate__global_sync_return = 48;
    constexpr EventSymbol tc_accumulate__node_sync_return = 49;
    constexpr EventSymbol tc__kv_map = 50;
    constexpr EventSymbol tc__map_read = 51;
    constexpr EventSymbol tc__map_read_ret = 52;
    constexpr EventSymbol tc__kv_reduce = 53;
    constexpr EventSymbol tc__v2_read_ret = 54;
    constexpr EventSymbol tc__sp_malloc_ret = 55;
    constexpr EventSymbol tc__v1_nblist_read_ret = 56;
    constexpr EventSymbol tc__v2_nblist_read_ret = 57;
    constexpr EventSymbol tc_compute__setup_thread_reg = 58;
    constexpr EventSymbol tc_compute__intersect_ab = 59;
    constexpr EventSymbol tc_compute__v1_nblist_read_ret = 60;
    constexpr EventSymbol tc_compute__v2_nblist_read_ret = 61;
    constexpr EventSymbol tc_compute__sp_free_ret = 62;
    constexpr EventSymbol main__init = 63;
    constexpr EventSymbol main__combine_tc = 64;
    constexpr EventSymbol main__term = 65;
    constexpr EventSymbol main_broadcast_init__setup_spd = 66;
    constexpr EventSymbol Broadcast__broadcast_global = 67;
    constexpr EventSymbol Broadcast__broadcast_node = 68;
    constexpr EventSymbol Broadcast__broadcast_ud = 69;
    constexpr EventSymbol Broadcast__broadcast_ud_fin = 70;
    constexpr EventSymbol Broadcast__broadcast_node_fin = 71;
    constexpr EventSymbol Broadcast__broadcast_global_fin = 72;
    constexpr EventSymbol Broadcast__broadcast_value_to_scratchpad = 73;

} // namespace

#endif