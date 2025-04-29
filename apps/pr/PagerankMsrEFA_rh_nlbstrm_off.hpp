#ifndef __PagerankMsrEFA_rh_nlbstrm_off_H__
#define __PagerankMsrEFA_rh_nlbstrm_off_H__

namespace PagerankMsrEFA_rh_nlbstrm_off {

    typedef unsigned int EventSymbol;

    constexpr EventSymbol Broadcast__broadcast_global = 0;
    constexpr EventSymbol Broadcast__broadcast_node = 1;
    constexpr EventSymbol Broadcast__broadcast_ud = 2;
    constexpr EventSymbol Broadcast__broadcast_ud_fin = 3;
    constexpr EventSymbol Broadcast__broadcast_node_fin = 4;
    constexpr EventSymbol Broadcast__broadcast_global_fin = 5;
    constexpr EventSymbol Broadcast__broadcast_value_to_scratchpad = 6;
    constexpr EventSymbol pr__map_shuffle_reduce = 7;
    constexpr EventSymbol pr__finish_init_udkvmsr = 8;
    constexpr EventSymbol pr__broadcast_global = 9;
    constexpr EventSymbol pr__broadcast_node = 10;
    constexpr EventSymbol pr__broadcast_ud = 11;
    constexpr EventSymbol pr__broadcast_ud_fin = 12;
    constexpr EventSymbol pr__broadcast_node_fin = 13;
    constexpr EventSymbol pr__broadcast_global_fin = 14;
    constexpr EventSymbol pr__broadcast_value_to_scratchpad = 15;
    constexpr EventSymbol pr__init_input_kvset_on_lane = 16;
    constexpr EventSymbol pr__init_output_kvset_on_lane = 17;
    constexpr EventSymbol pr__init_sp_lane = 18;
    constexpr EventSymbol pr__init_intermediate_kvset_on_lane = 19;
    constexpr EventSymbol pr__init_intermediate_kvset_on_lane_ret = 20;
    constexpr EventSymbol pr__init_global_master = 21;
    constexpr EventSymbol pr__global_master = 22;
    constexpr EventSymbol pr__cache_flush = 23;
    constexpr EventSymbol pr__cache_flush_return = 24;
    constexpr EventSymbol pr__termiante_global_master = 25;
    constexpr EventSymbol pr__init_node_master = 26;
    constexpr EventSymbol pr__node_master = 27;
    constexpr EventSymbol pr__termiante_node_master = 28;
    constexpr EventSymbol pr__init_updown_master = 29;
    constexpr EventSymbol pr__updown_master = 30;
    constexpr EventSymbol pr__terminate_updown_master = 31;
    constexpr EventSymbol pr__lane_master_init = 32;
    constexpr EventSymbol pr__lane_master_loop = 33;
    constexpr EventSymbol pr__lane_master_read_partition = 34;
    constexpr EventSymbol pr__lane_master_get_next_return = 35;
    constexpr EventSymbol pr__lane_master_terminate = 36;
    constexpr EventSymbol pr__lane_master_launch_worker = 37;
    constexpr EventSymbol pr__init_global_snyc = 38;
    constexpr EventSymbol pr__init_node_sync = 39;
    constexpr EventSymbol pr__ud_accumulate = 40;
    constexpr EventSymbol pr__global_sync_return = 41;
    constexpr EventSymbol pr__node_sync_return = 42;
    constexpr EventSymbol pr__kv_map_emit = 43;
    constexpr EventSymbol pr__kv_reduce_emit = 44;
    constexpr EventSymbol pr__kv_map_return = 45;
    constexpr EventSymbol pr__init_reduce_thread = 46;
    constexpr EventSymbol pr__combine_get_pair = 47;
    constexpr EventSymbol pr__combine_put_pair_ack = 48;
    constexpr EventSymbol pr__kv_reduce_return = 49;
    constexpr EventSymbol pr__combine_flush_lane = 50;
    constexpr EventSymbol pr__combine_flush_ack = 51;
    constexpr EventSymbol pr__worker_init = 52;
    constexpr EventSymbol pr__worker_work = 53;
    constexpr EventSymbol pr__worker_claim_local = 54;
    constexpr EventSymbol pr__worker_claim_remote = 55;
    constexpr EventSymbol pr__worker_helper = 56;
    constexpr EventSymbol pr__worker_claimed_map = 57;
    constexpr EventSymbol pr__worker_claimed_reduce_count = 58;
    constexpr EventSymbol pr__worker_claimed_reduce = 59;
    constexpr EventSymbol pr__worker_fetched_kv_ptr = 60;
    constexpr EventSymbol pr__worker_launch_reducer = 61;
    constexpr EventSymbol pr__worker_reducer_ret = 62;
    constexpr EventSymbol pr__worker_early_finish = 63;
    constexpr EventSymbol pr__worker_terminate = 64;
    constexpr EventSymbol pr__worker_confirm_local_materialized_count = 65;
    constexpr EventSymbol pr__worker_confirm_materialized_count = 66;
    constexpr EventSymbol pr__receiver_claim_work = 67;
    constexpr EventSymbol pr__receiver_set_terminate_bit = 68;
    constexpr EventSymbol pr__receiver_set_terminate_bit_ret = 69;
    constexpr EventSymbol pr__receiver_receive_intermediate_kv_pair = 70;
    constexpr EventSymbol pr__receiver_fetched_kv_ptr_for_cache = 71;
    constexpr EventSymbol pr__receiver_materialize_ret = 72;
    constexpr EventSymbol pr__receiver_update_unresolved_kv_count = 73;
    constexpr EventSymbol pr__receiver_acknowledge_key_executed = 74;
    constexpr EventSymbol pr__receiver_check_materialized_count = 75;
    constexpr EventSymbol pr__mapper_control_init = 76;
    constexpr EventSymbol pr__mapper_control_read_partition = 77;
    constexpr EventSymbol pr__mapper_control_get_next_return = 78;
    constexpr EventSymbol pr__mapper_control_loop = 79;
    constexpr EventSymbol pr__lane_remote_mapper_finished = 80;
    constexpr EventSymbol updown_init = 81;
    constexpr EventSymbol updown_terminate = 82;
    constexpr EventSymbol pr__kv_map = 83;
    constexpr EventSymbol pr__map_load_return = 84;

} // namespace

#endif