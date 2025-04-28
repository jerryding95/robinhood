#ifndef __js_udkvmsr_exe_rh_nlbstrm_on_H__
#define __js_udkvmsr_exe_rh_nlbstrm_on_H__

namespace js_udkvmsr_exe_rh_nlbstrm_on {

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
    constexpr EventSymbol js__init_global_master = 20;
    constexpr EventSymbol js__global_master = 21;
    constexpr EventSymbol js__init_node_master = 22;
    constexpr EventSymbol js__node_master = 23;
    constexpr EventSymbol js__termiante_node_master = 24;
    constexpr EventSymbol js__init_updown_master = 25;
    constexpr EventSymbol js__updown_master = 26;
    constexpr EventSymbol js__terminate_updown_master = 27;
    constexpr EventSymbol js__lane_master_init = 28;
    constexpr EventSymbol js__lane_master_loop = 29;
    constexpr EventSymbol js__lane_master_read_partition = 30;
    constexpr EventSymbol js__lane_master_get_next_return = 31;
    constexpr EventSymbol js__lane_master_terminate = 32;
    constexpr EventSymbol js__lane_master_launch_worker = 33;
    constexpr EventSymbol js__init_global_snyc = 34;
    constexpr EventSymbol js__init_node_sync = 35;
    constexpr EventSymbol js__ud_accumulate = 36;
    constexpr EventSymbol js__global_sync_return = 37;
    constexpr EventSymbol js__node_sync_return = 38;
    constexpr EventSymbol js__kv_map_emit = 39;
    constexpr EventSymbol js__kv_reduce_emit = 40;
    constexpr EventSymbol js__kv_map_return = 41;
    constexpr EventSymbol js__init_reduce_thread = 42;
    constexpr EventSymbol js__kv_reduce_return = 43;
    constexpr EventSymbol js__worker_init = 44;
    constexpr EventSymbol js__worker_work = 45;
    constexpr EventSymbol js__worker_claim_local = 46;
    constexpr EventSymbol js__worker_claim_remote = 47;
    constexpr EventSymbol js__worker_helper = 48;
    constexpr EventSymbol js__worker_claimed_map = 49;
    constexpr EventSymbol js__receiver_claim_work = 50;
    constexpr EventSymbol js__receiver_set_terminate_bit = 51;
    constexpr EventSymbol js__receiver_set_terminate_bit_ret = 52;
    constexpr EventSymbol js__mapper_control_init = 53;
    constexpr EventSymbol js__mapper_control_read_partition = 54;
    constexpr EventSymbol js__mapper_control_get_next_return = 55;
    constexpr EventSymbol js__mapper_control_loop = 56;
    constexpr EventSymbol js__lane_remote_mapper_finished = 57;
    constexpr EventSymbol js__kv_map = 58;
    constexpr EventSymbol js__map_v1_read_ret = 59;
    constexpr EventSymbol js__map_v2_read_ret = 60;
    constexpr EventSymbol js__kv_reduce = 61;
    constexpr EventSymbol js__sp_malloc_ret = 62;
    constexpr EventSymbol js_compute__setup_thread_reg = 63;
    constexpr EventSymbol js_compute__v1_nblist_read_ret = 64;
    constexpr EventSymbol js_compute__v2_nblist_read_ret = 65;
    constexpr EventSymbol js_compute__intersect_ab = 66;
    constexpr EventSymbol js_compute__intersect_term = 67;
    constexpr EventSymbol js_compute__sp_free_ret = 68;
    constexpr EventSymbol main__init = 69;
    constexpr EventSymbol main__combine_js = 70;
    constexpr EventSymbol main__term = 71;
    constexpr EventSymbol main_broadcast_init__setup_spd = 72;
    constexpr EventSymbol Broadcast__broadcast_global = 73;
    constexpr EventSymbol Broadcast__broadcast_node = 74;
    constexpr EventSymbol Broadcast__broadcast_ud = 75;
    constexpr EventSymbol Broadcast__broadcast_ud_fin = 76;
    constexpr EventSymbol Broadcast__broadcast_node_fin = 77;
    constexpr EventSymbol Broadcast__broadcast_global_fin = 78;
    constexpr EventSymbol Broadcast__broadcast_value_to_scratchpad = 79;

} // namespace

#endif