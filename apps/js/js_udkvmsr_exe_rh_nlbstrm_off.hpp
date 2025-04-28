#ifndef __js_udkvmsr_exe_rh_nlbstrm_off_H__
#define __js_udkvmsr_exe_rh_nlbstrm_off_H__

namespace js_udkvmsr_exe_rh_nlbstrm_off {

    typedef unsigned int EventSymbol;

    constexpr EventSymbol lm_allocator__spmalloc = 0;
    constexpr EventSymbol lm_allocator__spfree = 1;
    constexpr EventSymbol js_broadcast__broadcast_global = 2;
    constexpr EventSymbol js_broadcast__broadcast_node = 3;
    constexpr EventSymbol js_broadcast__broadcast_ud = 4;
    constexpr EventSymbol js_broadcast__broadcast_ud_fin = 5;
    constexpr EventSymbol js_broadcast__broadcast_node_fin = 6;
    constexpr EventSymbol js_broadcast__broadcast_global_fin = 7;
    constexpr EventSymbol js_broadcast__broadcast_value_to_scratchpad = 8;
    constexpr EventSymbol js__map_shuffle_reduce = 9;
    constexpr EventSymbol js__finish_init_udkvmsr = 10;
    constexpr EventSymbol js__broadcast_global = 11;
    constexpr EventSymbol js__broadcast_node = 12;
    constexpr EventSymbol js__broadcast_ud = 13;
    constexpr EventSymbol js__broadcast_ud_fin = 14;
    constexpr EventSymbol js__broadcast_node_fin = 15;
    constexpr EventSymbol js__broadcast_global_fin = 16;
    constexpr EventSymbol js__broadcast_value_to_scratchpad = 17;
    constexpr EventSymbol js__init_input_kvset_on_lane = 18;
    constexpr EventSymbol js__init_sp_lane = 19;
    constexpr EventSymbol js__init_intermediate_kvset_on_lane = 20;
    constexpr EventSymbol js__init_intermediate_kvset_on_lane_ret = 21;
    constexpr EventSymbol js__init_global_master = 22;
    constexpr EventSymbol js__global_master = 23;
    constexpr EventSymbol js__termiante_global_master = 24;
    constexpr EventSymbol js__init_node_master = 25;
    constexpr EventSymbol js__node_master = 26;
    constexpr EventSymbol js__termiante_node_master = 27;
    constexpr EventSymbol js__init_updown_master = 28;
    constexpr EventSymbol js__updown_master = 29;
    constexpr EventSymbol js__terminate_updown_master = 30;
    constexpr EventSymbol js__lane_master_init = 31;
    constexpr EventSymbol js__lane_master_loop = 32;
    constexpr EventSymbol js__lane_master_read_partition = 33;
    constexpr EventSymbol js__lane_master_get_next_return = 34;
    constexpr EventSymbol js__lane_master_terminate = 35;
    constexpr EventSymbol js__lane_master_launch_worker = 36;
    constexpr EventSymbol js__init_global_snyc = 37;
    constexpr EventSymbol js__init_node_sync = 38;
    constexpr EventSymbol js__ud_accumulate = 39;
    constexpr EventSymbol js__global_sync_return = 40;
    constexpr EventSymbol js__node_sync_return = 41;
    constexpr EventSymbol js__kv_map_emit = 42;
    constexpr EventSymbol js__kv_reduce_emit = 43;
    constexpr EventSymbol js__kv_map_return = 44;
    constexpr EventSymbol js__init_reduce_thread = 45;
    constexpr EventSymbol js__kv_reduce_return = 46;
    constexpr EventSymbol js__worker_init = 47;
    constexpr EventSymbol js__worker_work = 48;
    constexpr EventSymbol js__worker_claim_local = 49;
    constexpr EventSymbol js__worker_claim_remote = 50;
    constexpr EventSymbol js__worker_helper = 51;
    constexpr EventSymbol js__worker_claimed_map = 52;
    constexpr EventSymbol js__worker_claimed_reduce_count = 53;
    constexpr EventSymbol js__worker_claimed_reduce = 54;
    constexpr EventSymbol js__worker_fetched_kv_ptr = 55;
    constexpr EventSymbol js__worker_launch_reducer = 56;
    constexpr EventSymbol js__worker_reducer_ret = 57;
    constexpr EventSymbol js__worker_early_finish = 58;
    constexpr EventSymbol js__worker_terminate = 59;
    constexpr EventSymbol js__worker_confirm_local_materialized_count = 60;
    constexpr EventSymbol js__worker_confirm_materialized_count = 61;
    constexpr EventSymbol js__receiver_claim_work = 62;
    constexpr EventSymbol js__receiver_set_terminate_bit = 63;
    constexpr EventSymbol js__receiver_set_terminate_bit_ret = 64;
    constexpr EventSymbol js__receiver_receive_intermediate_kv_pair = 65;
    constexpr EventSymbol js__receiver_fetched_kv_ptr_for_cache = 66;
    constexpr EventSymbol js__receiver_materialize_ret = 67;
    constexpr EventSymbol js__receiver_update_unresolved_kv_count = 68;
    constexpr EventSymbol js__receiver_acknowledge_key_executed = 69;
    constexpr EventSymbol js__receiver_check_materialized_count = 70;
    constexpr EventSymbol js__mapper_control_init = 71;
    constexpr EventSymbol js__mapper_control_read_partition = 72;
    constexpr EventSymbol js__mapper_control_get_next_return = 73;
    constexpr EventSymbol js__mapper_control_loop = 74;
    constexpr EventSymbol js__lane_remote_mapper_finished = 75;
    constexpr EventSymbol js__kv_map = 76;
    constexpr EventSymbol js__map_v1_read_ret = 77;
    constexpr EventSymbol js__map_v2_read_ret = 78;
    constexpr EventSymbol js__kv_reduce = 79;
    constexpr EventSymbol js__sp_malloc_ret = 80;
    constexpr EventSymbol js_compute__setup_thread_reg = 81;
    constexpr EventSymbol js_compute__v1_nblist_read_ret = 82;
    constexpr EventSymbol js_compute__v2_nblist_read_ret = 83;
    constexpr EventSymbol js_compute__intersect_ab = 84;
    constexpr EventSymbol js_compute__intersect_term = 85;
    constexpr EventSymbol js_compute__sp_free_ret = 86;
    constexpr EventSymbol main__init = 87;
    constexpr EventSymbol main__combine_js = 88;
    constexpr EventSymbol main__term = 89;
    constexpr EventSymbol main_broadcast_init__setup_spd = 90;
    constexpr EventSymbol Broadcast__broadcast_global = 91;
    constexpr EventSymbol Broadcast__broadcast_node = 92;
    constexpr EventSymbol Broadcast__broadcast_ud = 93;
    constexpr EventSymbol Broadcast__broadcast_ud_fin = 94;
    constexpr EventSymbol Broadcast__broadcast_node_fin = 95;
    constexpr EventSymbol Broadcast__broadcast_global_fin = 96;
    constexpr EventSymbol Broadcast__broadcast_value_to_scratchpad = 97;

} // namespace

#endif