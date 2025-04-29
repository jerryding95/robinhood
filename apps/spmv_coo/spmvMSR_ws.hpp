#ifndef __spmvMSR_ws_H__
#define __spmvMSR_ws_H__

namespace spmvMSR_ws {

    typedef unsigned int EventSymbol;

    constexpr EventSymbol Broadcast__broadcast_global = 0;
    constexpr EventSymbol Broadcast__broadcast_node = 1;
    constexpr EventSymbol Broadcast__broadcast_ud = 2;
    constexpr EventSymbol Broadcast__broadcast_ud_fin = 3;
    constexpr EventSymbol Broadcast__broadcast_node_fin = 4;
    constexpr EventSymbol Broadcast__broadcast_global_fin = 5;
    constexpr EventSymbol Broadcast__broadcast_value_to_scratchpad = 6;
    constexpr EventSymbol spmv__map_shuffle_reduce = 7;
    constexpr EventSymbol spmv__finish_init_udkvmsr = 8;
    constexpr EventSymbol Test_input__generate_partition_array = 9;
    constexpr EventSymbol Test_input__write_partition_array_return = 10;
    constexpr EventSymbol spmv__broadcast_global = 11;
    constexpr EventSymbol spmv__broadcast_node = 12;
    constexpr EventSymbol spmv__broadcast_ud = 13;
    constexpr EventSymbol spmv__broadcast_ud_fin = 14;
    constexpr EventSymbol spmv__broadcast_node_fin = 15;
    constexpr EventSymbol spmv__broadcast_global_fin = 16;
    constexpr EventSymbol spmv__broadcast_value_to_scratchpad = 17;
    constexpr EventSymbol spmv__init_input_kvset_on_lane = 18;
    constexpr EventSymbol spmv__init_output_kvset_on_lane = 19;
    constexpr EventSymbol spmv__init_sp_lane = 20;
    constexpr EventSymbol spmv__init_intermediate_kvset_on_lane = 21;
    constexpr EventSymbol spmv__init_intermediate_kvset_on_lane_ret = 22;
    constexpr EventSymbol spmv__init_global_master = 23;
    constexpr EventSymbol spmv__global_master = 24;
    constexpr EventSymbol spmv__cache_flush = 25;
    constexpr EventSymbol spmv__cache_flush_return = 26;
    constexpr EventSymbol spmv__termiante_global_master = 27;
    constexpr EventSymbol spmv__init_node_master = 28;
    constexpr EventSymbol spmv__node_master = 29;
    constexpr EventSymbol spmv__termiante_node_master = 30;
    constexpr EventSymbol spmv__init_updown_master = 31;
    constexpr EventSymbol spmv__updown_master = 32;
    constexpr EventSymbol spmv__terminate_updown_master = 33;
    constexpr EventSymbol spmv__lane_master_init = 34;
    constexpr EventSymbol spmv__lane_master_loop = 35;
    constexpr EventSymbol spmv__lane_master_read_partition = 36;
    constexpr EventSymbol spmv__lane_master_get_next_return = 37;
    constexpr EventSymbol spmv__lane_master_terminate = 38;
    constexpr EventSymbol spmv__lane_master_launch_worker = 39;
    constexpr EventSymbol spmv__init_global_snyc = 40;
    constexpr EventSymbol spmv__init_node_sync = 41;
    constexpr EventSymbol spmv__ud_accumulate = 42;
    constexpr EventSymbol spmv__global_sync_return = 43;
    constexpr EventSymbol spmv__node_sync_return = 44;
    constexpr EventSymbol spmv__kv_map_emit = 45;
    constexpr EventSymbol spmv__kv_reduce_emit = 46;
    constexpr EventSymbol spmv__kv_map_return = 47;
    constexpr EventSymbol spmv__init_reduce_thread = 48;
    constexpr EventSymbol spmv__combine_get_pair = 49;
    constexpr EventSymbol spmv__combine_put_pair_ack = 50;
    constexpr EventSymbol spmv__kv_reduce_return = 51;
    constexpr EventSymbol spmv__combine_flush_lane = 52;
    constexpr EventSymbol spmv__combine_flush_ack = 53;
    constexpr EventSymbol spmv__worker_init = 54;
    constexpr EventSymbol spmv__worker_work = 55;
    constexpr EventSymbol spmv__worker_claim_local = 56;
    constexpr EventSymbol spmv__worker_claim_remote = 57;
    constexpr EventSymbol spmv__worker_helper = 58;
    constexpr EventSymbol spmv__worker_claimed_map = 59;
    constexpr EventSymbol spmv__worker_claimed_reduce_count = 60;
    constexpr EventSymbol spmv__worker_claimed_reduce = 61;
    constexpr EventSymbol spmv__worker_fetched_kv_ptr = 62;
    constexpr EventSymbol spmv__worker_launch_reducer = 63;
    constexpr EventSymbol spmv__worker_reducer_ret = 64;
    constexpr EventSymbol spmv__worker_early_finish = 65;
    constexpr EventSymbol spmv__worker_terminate = 66;
    constexpr EventSymbol spmv__receiver_claim_work = 67;
    constexpr EventSymbol spmv__receiver_set_terminate_bit = 68;
    constexpr EventSymbol spmv__receiver_set_terminate_bit_ret = 69;
    constexpr EventSymbol spmv__receiver_receive_intermediate_kv_pair = 70;
    constexpr EventSymbol spmv__receiver_fetched_kv_ptr_for_cache = 71;
    constexpr EventSymbol spmv__receiver_materialize_ret = 72;
    constexpr EventSymbol spmv__receiver_update_unresolved_kv_count = 73;
    constexpr EventSymbol spmv__receiver_acknowledge_key_executed = 74;
    constexpr EventSymbol spmv__mapper_control_init = 75;
    constexpr EventSymbol spmv__mapper_control_read_partition = 76;
    constexpr EventSymbol spmv__mapper_control_get_next_return = 77;
    constexpr EventSymbol spmv__mapper_control_loop = 78;
    constexpr EventSymbol spmv__lane_remote_mapper_finished = 79;
    constexpr EventSymbol updown_init = 80;
    constexpr EventSymbol set_vector_ptr = 81;
    constexpr EventSymbol msr_init = 82;
    constexpr EventSymbol spmv__kv_map = 83;
    constexpr EventSymbol kv_map_calc = 84;
    constexpr EventSymbol updown_terminate = 85;

} // namespace

#endif