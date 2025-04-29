#ifndef __spmvMSR_nlb_H__
#define __spmvMSR_nlb_H__

namespace spmvMSR_nlb {

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
    constexpr EventSymbol spmv__init_global_master = 21;
    constexpr EventSymbol spmv__global_master = 22;
    constexpr EventSymbol spmv__cache_flush = 23;
    constexpr EventSymbol spmv__cache_flush_return = 24;
    constexpr EventSymbol spmv__init_node_master = 25;
    constexpr EventSymbol spmv__node_master = 26;
    constexpr EventSymbol spmv__termiante_node_master = 27;
    constexpr EventSymbol spmv__init_updown_master = 28;
    constexpr EventSymbol spmv__updown_master = 29;
    constexpr EventSymbol spmv__terminate_updown_master = 30;
    constexpr EventSymbol spmv__lane_master_init = 31;
    constexpr EventSymbol spmv__lane_master_loop = 32;
    constexpr EventSymbol spmv__lane_master_read_partition = 33;
    constexpr EventSymbol spmv__lane_master_get_next_return = 34;
    constexpr EventSymbol spmv__lane_master_terminate = 35;
    constexpr EventSymbol spmv__init_global_snyc = 36;
    constexpr EventSymbol spmv__init_node_sync = 37;
    constexpr EventSymbol spmv__ud_accumulate = 38;
    constexpr EventSymbol spmv__global_sync_return = 39;
    constexpr EventSymbol spmv__node_sync_return = 40;
    constexpr EventSymbol spmv__kv_map_emit = 41;
    constexpr EventSymbol spmv__kv_reduce_emit = 42;
    constexpr EventSymbol spmv__kv_map_return = 43;
    constexpr EventSymbol spmv__init_reduce_thread = 44;
    constexpr EventSymbol spmv__combine_get_pair = 45;
    constexpr EventSymbol spmv__combine_put_pair_ack = 46;
    constexpr EventSymbol spmv__kv_reduce_return = 47;
    constexpr EventSymbol spmv__combine_flush_lane = 48;
    constexpr EventSymbol spmv__combine_flush_ack = 49;
    constexpr EventSymbol updown_init = 50;
    constexpr EventSymbol set_vector_ptr = 51;
    constexpr EventSymbol msr_init = 52;
    constexpr EventSymbol spmv__kv_map = 53;
    constexpr EventSymbol kv_map_calc = 54;
    constexpr EventSymbol updown_terminate = 55;

} // namespace

#endif