#ifndef __tc_udkvmsr_exe_ws_H__
#define __tc_udkvmsr_exe_ws_H__

namespace tc_udkvmsr_exe_ws {

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
    constexpr EventSymbol tc__init_intermediate_kvset_on_lane = 22;
    constexpr EventSymbol tc__init_intermediate_kvset_on_lane_ret = 23;
    constexpr EventSymbol tc__init_global_master = 24;
    constexpr EventSymbol tc__global_master = 25;
    constexpr EventSymbol tc__termiante_global_master = 26;
    constexpr EventSymbol tc__init_node_master = 27;
    constexpr EventSymbol tc__node_master = 28;
    constexpr EventSymbol tc__termiante_node_master = 29;
    constexpr EventSymbol tc__init_updown_master = 30;
    constexpr EventSymbol tc__updown_master = 31;
    constexpr EventSymbol tc__terminate_updown_master = 32;
    constexpr EventSymbol tc__lane_master_init = 33;
    constexpr EventSymbol tc__lane_master_loop = 34;
    constexpr EventSymbol tc__lane_master_read_partition = 35;
    constexpr EventSymbol tc__lane_master_get_next_return = 36;
    constexpr EventSymbol tc__lane_master_terminate = 37;
    constexpr EventSymbol tc__lane_master_launch_worker = 38;
    constexpr EventSymbol tc__init_global_snyc = 39;
    constexpr EventSymbol tc__init_node_sync = 40;
    constexpr EventSymbol tc__ud_accumulate = 41;
    constexpr EventSymbol tc__global_sync_return = 42;
    constexpr EventSymbol tc__node_sync_return = 43;
    constexpr EventSymbol tc__kv_map_emit = 44;
    constexpr EventSymbol tc__kv_reduce_emit = 45;
    constexpr EventSymbol tc__kv_map_return = 46;
    constexpr EventSymbol tc__init_reduce_thread = 47;
    constexpr EventSymbol tc__kv_reduce_return = 48;
    constexpr EventSymbol tc__worker_init = 49;
    constexpr EventSymbol tc__worker_work = 50;
    constexpr EventSymbol tc__worker_claim_local = 51;
    constexpr EventSymbol tc__worker_claim_remote = 52;
    constexpr EventSymbol tc__worker_helper = 53;
    constexpr EventSymbol tc__worker_claimed_map = 54;
    constexpr EventSymbol tc__worker_claimed_reduce_count = 55;
    constexpr EventSymbol tc__worker_claimed_reduce = 56;
    constexpr EventSymbol tc__worker_fetched_kv_ptr = 57;
    constexpr EventSymbol tc__worker_launch_reducer = 58;
    constexpr EventSymbol tc__worker_reducer_ret = 59;
    constexpr EventSymbol tc__worker_early_finish = 60;
    constexpr EventSymbol tc__worker_terminate = 61;
    constexpr EventSymbol tc__receiver_claim_work = 62;
    constexpr EventSymbol tc__receiver_set_terminate_bit = 63;
    constexpr EventSymbol tc__receiver_set_terminate_bit_ret = 64;
    constexpr EventSymbol tc__receiver_receive_intermediate_kv_pair = 65;
    constexpr EventSymbol tc__receiver_fetched_kv_ptr_for_cache = 66;
    constexpr EventSymbol tc__receiver_materialize_ret = 67;
    constexpr EventSymbol tc__receiver_update_unresolved_kv_count = 68;
    constexpr EventSymbol tc__receiver_acknowledge_key_executed = 69;
    constexpr EventSymbol tc__mapper_control_init = 70;
    constexpr EventSymbol tc__mapper_control_read_partition = 71;
    constexpr EventSymbol tc__mapper_control_get_next_return = 72;
    constexpr EventSymbol tc__mapper_control_loop = 73;
    constexpr EventSymbol tc__lane_remote_mapper_finished = 74;
    constexpr EventSymbol tc_accumulate__init_global_snyc = 75;
    constexpr EventSymbol tc_accumulate__init_node_sync = 76;
    constexpr EventSymbol tc_accumulate__ud_accumulate = 77;
    constexpr EventSymbol tc_accumulate__global_sync_return = 78;
    constexpr EventSymbol tc_accumulate__node_sync_return = 79;
    constexpr EventSymbol tc__kv_map = 80;
    constexpr EventSymbol tc__map_read = 81;
    constexpr EventSymbol tc__map_read_ret = 82;
    constexpr EventSymbol tc__kv_reduce = 83;
    constexpr EventSymbol tc__v2_read_ret = 84;
    constexpr EventSymbol tc__sp_malloc_ret = 85;
    constexpr EventSymbol tc__v1_nblist_read_ret = 86;
    constexpr EventSymbol tc__v2_nblist_read_ret = 87;
    constexpr EventSymbol tc_compute__setup_thread_reg = 88;
    constexpr EventSymbol tc_compute__intersect_ab = 89;
    constexpr EventSymbol tc_compute__v1_nblist_read_ret = 90;
    constexpr EventSymbol tc_compute__v2_nblist_read_ret = 91;
    constexpr EventSymbol tc_compute__sp_free_ret = 92;
    constexpr EventSymbol main__init = 93;
    constexpr EventSymbol main__combine_tc = 94;
    constexpr EventSymbol main__term = 95;
    constexpr EventSymbol main_broadcast_init__setup_spd = 96;
    constexpr EventSymbol Broadcast__broadcast_global = 97;
    constexpr EventSymbol Broadcast__broadcast_node = 98;
    constexpr EventSymbol Broadcast__broadcast_ud = 99;
    constexpr EventSymbol Broadcast__broadcast_ud_fin = 100;
    constexpr EventSymbol Broadcast__broadcast_node_fin = 101;
    constexpr EventSymbol Broadcast__broadcast_global_fin = 102;
    constexpr EventSymbol Broadcast__broadcast_value_to_scratchpad = 103;

} // namespace

#endif