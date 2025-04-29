#ifndef __spmvMSR_rh_nlbstrm_on_H__
#define __spmvMSR_rh_nlbstrm_on_H__

namespace spmvMSR_rh_nlbstrm_on {

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
    constexpr EventSymbol spmv__lane_master_launch_worker = 36;
    constexpr EventSymbol spmv__init_global_snyc = 37;
    constexpr EventSymbol spmv__init_node_sync = 38;
    constexpr EventSymbol spmv__ud_accumulate = 39;
    constexpr EventSymbol spmv__global_sync_return = 40;
    constexpr EventSymbol spmv__node_sync_return = 41;
    constexpr EventSymbol spmv__kv_map_emit = 42;
    constexpr EventSymbol spmv__kv_reduce_emit = 43;
    constexpr EventSymbol spmv__kv_map_return = 44;
    constexpr EventSymbol spmv__init_reduce_thread = 45;
    constexpr EventSymbol spmv__combine_get_pair = 46;
    constexpr EventSymbol spmv__combine_put_pair_ack = 47;
    constexpr EventSymbol spmv__kv_reduce_return = 48;
    constexpr EventSymbol spmv__combine_flush_lane = 49;
    constexpr EventSymbol spmv__combine_flush_ack = 50;
    constexpr EventSymbol spmv__worker_init = 51;
    constexpr EventSymbol spmv__worker_work = 52;
    constexpr EventSymbol spmv__worker_claim_local = 53;
    constexpr EventSymbol spmv__worker_claim_remote = 54;
    constexpr EventSymbol spmv__worker_helper = 55;
    constexpr EventSymbol spmv__worker_claimed_map = 56;
    constexpr EventSymbol spmv__receiver_claim_work = 57;
    constexpr EventSymbol spmv__receiver_set_terminate_bit = 58;
    constexpr EventSymbol spmv__receiver_set_terminate_bit_ret = 59;
    constexpr EventSymbol spmv__mapper_control_init = 60;
    constexpr EventSymbol spmv__mapper_control_read_partition = 61;
    constexpr EventSymbol spmv__mapper_control_get_next_return = 62;
    constexpr EventSymbol spmv__mapper_control_loop = 63;
    constexpr EventSymbol spmv__lane_remote_mapper_finished = 64;
    constexpr EventSymbol updown_init = 65;
    constexpr EventSymbol set_vector_ptr = 66;
    constexpr EventSymbol msr_init = 67;
    constexpr EventSymbol spmv__kv_map = 68;
    constexpr EventSymbol kv_map_calc = 69;
    constexpr EventSymbol updown_terminate = 70;

} // namespace

#endif