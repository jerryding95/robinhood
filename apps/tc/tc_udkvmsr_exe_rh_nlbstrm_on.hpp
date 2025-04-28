#ifndef __tc_udkvmsr_exe_rh_nlbstrm_on_H__
#define __tc_udkvmsr_exe_rh_nlbstrm_on_H__

namespace tc_udkvmsr_exe_rh_nlbstrm_on {

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
    constexpr EventSymbol tc__lane_master_launch_worker = 35;
    constexpr EventSymbol tc__init_global_snyc = 36;
    constexpr EventSymbol tc__init_node_sync = 37;
    constexpr EventSymbol tc__ud_accumulate = 38;
    constexpr EventSymbol tc__global_sync_return = 39;
    constexpr EventSymbol tc__node_sync_return = 40;
    constexpr EventSymbol tc__kv_map_emit = 41;
    constexpr EventSymbol tc__kv_reduce_emit = 42;
    constexpr EventSymbol tc__kv_map_return = 43;
    constexpr EventSymbol tc__init_reduce_thread = 44;
    constexpr EventSymbol tc__kv_reduce_return = 45;
    constexpr EventSymbol tc__worker_init = 46;
    constexpr EventSymbol tc__worker_work = 47;
    constexpr EventSymbol tc__worker_claim_local = 48;
    constexpr EventSymbol tc__worker_claim_remote = 49;
    constexpr EventSymbol tc__worker_helper = 50;
    constexpr EventSymbol tc__worker_claimed_map = 51;
    constexpr EventSymbol tc__receiver_claim_work = 52;
    constexpr EventSymbol tc__receiver_set_terminate_bit = 53;
    constexpr EventSymbol tc__receiver_set_terminate_bit_ret = 54;
    constexpr EventSymbol tc__mapper_control_init = 55;
    constexpr EventSymbol tc__mapper_control_read_partition = 56;
    constexpr EventSymbol tc__mapper_control_get_next_return = 57;
    constexpr EventSymbol tc__mapper_control_loop = 58;
    constexpr EventSymbol tc__lane_remote_mapper_finished = 59;
    constexpr EventSymbol tc_accumulate__init_global_snyc = 60;
    constexpr EventSymbol tc_accumulate__init_node_sync = 61;
    constexpr EventSymbol tc_accumulate__ud_accumulate = 62;
    constexpr EventSymbol tc_accumulate__global_sync_return = 63;
    constexpr EventSymbol tc_accumulate__node_sync_return = 64;
    constexpr EventSymbol tc__kv_map = 65;
    constexpr EventSymbol tc__map_read = 66;
    constexpr EventSymbol tc__map_read_ret = 67;
    constexpr EventSymbol tc__kv_reduce = 68;
    constexpr EventSymbol tc__v2_read_ret = 69;
    constexpr EventSymbol tc__sp_malloc_ret = 70;
    constexpr EventSymbol tc__v1_nblist_read_ret = 71;
    constexpr EventSymbol tc__v2_nblist_read_ret = 72;
    constexpr EventSymbol tc_compute__setup_thread_reg = 73;
    constexpr EventSymbol tc_compute__intersect_ab = 74;
    constexpr EventSymbol tc_compute__v1_nblist_read_ret = 75;
    constexpr EventSymbol tc_compute__v2_nblist_read_ret = 76;
    constexpr EventSymbol tc_compute__sp_free_ret = 77;
    constexpr EventSymbol main__init = 78;
    constexpr EventSymbol main__combine_tc = 79;
    constexpr EventSymbol main__term = 80;
    constexpr EventSymbol main_broadcast_init__setup_spd = 81;
    constexpr EventSymbol Broadcast__broadcast_global = 82;
    constexpr EventSymbol Broadcast__broadcast_node = 83;
    constexpr EventSymbol Broadcast__broadcast_ud = 84;
    constexpr EventSymbol Broadcast__broadcast_ud_fin = 85;
    constexpr EventSymbol Broadcast__broadcast_node_fin = 86;
    constexpr EventSymbol Broadcast__broadcast_global_fin = 87;
    constexpr EventSymbol Broadcast__broadcast_value_to_scratchpad = 88;

} // namespace

#endif