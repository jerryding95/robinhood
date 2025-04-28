#ifndef __gcn_udkvmsr_exe_ws_H__
#define __gcn_udkvmsr_exe_ws_H__

namespace gcn_udkvmsr_exe_ws {

    typedef unsigned int EventSymbol;

    constexpr EventSymbol gnn_vanilla_kvmsr__map_shuffle_reduce = 0;
    constexpr EventSymbol gnn_vanilla_kvmsr__finish_init_udkvmsr = 1;
    constexpr EventSymbol gnn_input__generate_partition_array = 2;
    constexpr EventSymbol gnn_input__write_partition_array_return = 3;
    constexpr EventSymbol gnn_vanilla_kvmsr__broadcast_global = 4;
    constexpr EventSymbol gnn_vanilla_kvmsr__broadcast_node = 5;
    constexpr EventSymbol gnn_vanilla_kvmsr__broadcast_ud = 6;
    constexpr EventSymbol gnn_vanilla_kvmsr__broadcast_ud_fin = 7;
    constexpr EventSymbol gnn_vanilla_kvmsr__broadcast_node_fin = 8;
    constexpr EventSymbol gnn_vanilla_kvmsr__broadcast_global_fin = 9;
    constexpr EventSymbol gnn_vanilla_kvmsr__broadcast_value_to_scratchpad = 10;
    constexpr EventSymbol gnn_vanilla_kvmsr__init_input_kvset_on_lane = 11;
    constexpr EventSymbol gnn_vanilla_kvmsr__init_sp_lane = 12;
    constexpr EventSymbol gnn_vanilla_kvmsr__init_intermediate_kvset_on_lane = 13;
    constexpr EventSymbol gnn_vanilla_kvmsr__init_intermediate_kvset_on_lane_ret = 14;
    constexpr EventSymbol gnn_vanilla_kvmsr__init_global_master = 15;
    constexpr EventSymbol gnn_vanilla_kvmsr__global_master = 16;
    constexpr EventSymbol gnn_vanilla_kvmsr__termiante_global_master = 17;
    constexpr EventSymbol gnn_vanilla_kvmsr__init_node_master = 18;
    constexpr EventSymbol gnn_vanilla_kvmsr__node_master = 19;
    constexpr EventSymbol gnn_vanilla_kvmsr__termiante_node_master = 20;
    constexpr EventSymbol gnn_vanilla_kvmsr__init_updown_master = 21;
    constexpr EventSymbol gnn_vanilla_kvmsr__updown_master = 22;
    constexpr EventSymbol gnn_vanilla_kvmsr__terminate_updown_master = 23;
    constexpr EventSymbol gnn_vanilla_kvmsr__lane_master_init = 24;
    constexpr EventSymbol gnn_vanilla_kvmsr__lane_master_loop = 25;
    constexpr EventSymbol gnn_vanilla_kvmsr__lane_master_read_partition = 26;
    constexpr EventSymbol gnn_vanilla_kvmsr__lane_master_get_next_return = 27;
    constexpr EventSymbol gnn_vanilla_kvmsr__lane_master_terminate = 28;
    constexpr EventSymbol gnn_vanilla_kvmsr__lane_master_launch_worker = 29;
    constexpr EventSymbol gnn_vanilla_kvmsr__init_global_snyc = 30;
    constexpr EventSymbol gnn_vanilla_kvmsr__init_node_sync = 31;
    constexpr EventSymbol gnn_vanilla_kvmsr__ud_accumulate = 32;
    constexpr EventSymbol gnn_vanilla_kvmsr__global_sync_return = 33;
    constexpr EventSymbol gnn_vanilla_kvmsr__node_sync_return = 34;
    constexpr EventSymbol gnn_vanilla_kvmsr__kv_map_emit = 35;
    constexpr EventSymbol gnn_vanilla_kvmsr__kv_reduce_emit = 36;
    constexpr EventSymbol gnn_vanilla_kvmsr__kv_map_return = 37;
    constexpr EventSymbol gnn_vanilla_kvmsr__init_reduce_thread = 38;
    constexpr EventSymbol gnn_vanilla_kvmsr__kv_reduce_return = 39;
    constexpr EventSymbol gnn_vanilla_kvmsr__worker_init = 40;
    constexpr EventSymbol gnn_vanilla_kvmsr__worker_work = 41;
    constexpr EventSymbol gnn_vanilla_kvmsr__worker_claim_local = 42;
    constexpr EventSymbol gnn_vanilla_kvmsr__worker_claim_remote = 43;
    constexpr EventSymbol gnn_vanilla_kvmsr__worker_helper = 44;
    constexpr EventSymbol gnn_vanilla_kvmsr__worker_claimed_map = 45;
    constexpr EventSymbol gnn_vanilla_kvmsr__worker_claimed_reduce_count = 46;
    constexpr EventSymbol gnn_vanilla_kvmsr__worker_claimed_reduce = 47;
    constexpr EventSymbol gnn_vanilla_kvmsr__worker_fetched_kv_ptr = 48;
    constexpr EventSymbol gnn_vanilla_kvmsr__worker_launch_reducer = 49;
    constexpr EventSymbol gnn_vanilla_kvmsr__worker_reducer_ret = 50;
    constexpr EventSymbol gnn_vanilla_kvmsr__worker_early_finish = 51;
    constexpr EventSymbol gnn_vanilla_kvmsr__worker_terminate = 52;
    constexpr EventSymbol gnn_vanilla_kvmsr__receiver_claim_work = 53;
    constexpr EventSymbol gnn_vanilla_kvmsr__receiver_set_terminate_bit = 54;
    constexpr EventSymbol gnn_vanilla_kvmsr__receiver_set_terminate_bit_ret = 55;
    constexpr EventSymbol gnn_vanilla_kvmsr__receiver_receive_intermediate_kv_pair = 56;
    constexpr EventSymbol gnn_vanilla_kvmsr__receiver_fetched_kv_ptr_for_cache = 57;
    constexpr EventSymbol gnn_vanilla_kvmsr__receiver_materialize_ret = 58;
    constexpr EventSymbol gnn_vanilla_kvmsr__receiver_update_unresolved_kv_count = 59;
    constexpr EventSymbol gnn_vanilla_kvmsr__receiver_acknowledge_key_executed = 60;
    constexpr EventSymbol gnn_vanilla_kvmsr__mapper_control_init = 61;
    constexpr EventSymbol gnn_vanilla_kvmsr__mapper_control_read_partition = 62;
    constexpr EventSymbol gnn_vanilla_kvmsr__mapper_control_get_next_return = 63;
    constexpr EventSymbol gnn_vanilla_kvmsr__mapper_control_loop = 64;
    constexpr EventSymbol gnn_vanilla_kvmsr__lane_remote_mapper_finished = 65;
    constexpr EventSymbol gnn_vanilla_master__gnn_start = 66;
    constexpr EventSymbol gnn_vanilla_master__gnn_term = 67;
    constexpr EventSymbol gnn_vanilla_kvmsr__kv_map = 68;
    constexpr EventSymbol gnn_vanilla_kvmsr__kv_reduce = 69;
    constexpr EventSymbol gnn_vanilla_kvmsr__kv_reduce_compute = 70;
    constexpr EventSymbol gnn_vanilla_kvmsr__kv_reduce_write_back = 71;
    constexpr EventSymbol Broadcast__broadcast_global = 72;
    constexpr EventSymbol Broadcast__broadcast_node = 73;
    constexpr EventSymbol Broadcast__broadcast_ud = 74;
    constexpr EventSymbol Broadcast__broadcast_ud_fin = 75;
    constexpr EventSymbol Broadcast__broadcast_node_fin = 76;
    constexpr EventSymbol Broadcast__broadcast_global_fin = 77;
    constexpr EventSymbol Broadcast__broadcast_value_to_scratchpad = 78;

} // namespace

#endif