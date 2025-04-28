#ifndef __gcn_udkvmsr_exe_nlb_H__
#define __gcn_udkvmsr_exe_nlb_H__

namespace gcn_udkvmsr_exe_nlb {

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
    constexpr EventSymbol gnn_vanilla_kvmsr__init_global_master = 13;
    constexpr EventSymbol gnn_vanilla_kvmsr__global_master = 14;
    constexpr EventSymbol gnn_vanilla_kvmsr__init_node_master = 15;
    constexpr EventSymbol gnn_vanilla_kvmsr__node_master = 16;
    constexpr EventSymbol gnn_vanilla_kvmsr__termiante_node_master = 17;
    constexpr EventSymbol gnn_vanilla_kvmsr__init_updown_master = 18;
    constexpr EventSymbol gnn_vanilla_kvmsr__updown_master = 19;
    constexpr EventSymbol gnn_vanilla_kvmsr__terminate_updown_master = 20;
    constexpr EventSymbol gnn_vanilla_kvmsr__lane_master_init = 21;
    constexpr EventSymbol gnn_vanilla_kvmsr__lane_master_loop = 22;
    constexpr EventSymbol gnn_vanilla_kvmsr__lane_master_read_partition = 23;
    constexpr EventSymbol gnn_vanilla_kvmsr__lane_master_get_next_return = 24;
    constexpr EventSymbol gnn_vanilla_kvmsr__lane_master_terminate = 25;
    constexpr EventSymbol gnn_vanilla_kvmsr__init_global_snyc = 26;
    constexpr EventSymbol gnn_vanilla_kvmsr__init_node_sync = 27;
    constexpr EventSymbol gnn_vanilla_kvmsr__ud_accumulate = 28;
    constexpr EventSymbol gnn_vanilla_kvmsr__global_sync_return = 29;
    constexpr EventSymbol gnn_vanilla_kvmsr__node_sync_return = 30;
    constexpr EventSymbol gnn_vanilla_kvmsr__kv_map_emit = 31;
    constexpr EventSymbol gnn_vanilla_kvmsr__kv_reduce_emit = 32;
    constexpr EventSymbol gnn_vanilla_kvmsr__kv_map_return = 33;
    constexpr EventSymbol gnn_vanilla_kvmsr__init_reduce_thread = 34;
    constexpr EventSymbol gnn_vanilla_kvmsr__kv_reduce_return = 35;
    constexpr EventSymbol gnn_vanilla_master__gnn_start = 36;
    constexpr EventSymbol gnn_vanilla_master__gnn_term = 37;
    constexpr EventSymbol gnn_vanilla_kvmsr__kv_map = 38;
    constexpr EventSymbol gnn_vanilla_kvmsr__kv_reduce = 39;
    constexpr EventSymbol gnn_vanilla_kvmsr__kv_reduce_compute = 40;
    constexpr EventSymbol gnn_vanilla_kvmsr__kv_reduce_write_back = 41;
    constexpr EventSymbol Broadcast__broadcast_global = 42;
    constexpr EventSymbol Broadcast__broadcast_node = 43;
    constexpr EventSymbol Broadcast__broadcast_ud = 44;
    constexpr EventSymbol Broadcast__broadcast_ud_fin = 45;
    constexpr EventSymbol Broadcast__broadcast_node_fin = 46;
    constexpr EventSymbol Broadcast__broadcast_global_fin = 47;
    constexpr EventSymbol Broadcast__broadcast_value_to_scratchpad = 48;

} // namespace

#endif