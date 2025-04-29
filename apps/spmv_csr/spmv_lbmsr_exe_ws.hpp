#ifndef __spmv_lbmsr_exe_ws_H__
#define __spmv_lbmsr_exe_ws_H__

namespace spmv_lbmsr_exe_ws {

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
    constexpr EventSymbol spmv__broadcast_global = 9;
    constexpr EventSymbol spmv__broadcast_node = 10;
    constexpr EventSymbol spmv__broadcast_ud = 11;
    constexpr EventSymbol spmv__broadcast_ud_fin = 12;
    constexpr EventSymbol spmv__broadcast_node_fin = 13;
    constexpr EventSymbol spmv__broadcast_global_fin = 14;
    constexpr EventSymbol spmv__broadcast_value_to_scratchpad = 15;
    constexpr EventSymbol spmv__init_input_kvset_on_lane = 16;
    constexpr EventSymbol spmv__init_sp_lane = 17;
    constexpr EventSymbol spmv__init_global_master = 18;
    constexpr EventSymbol spmv__global_master = 19;
    constexpr EventSymbol spmv__init_node_master = 20;
    constexpr EventSymbol spmv__node_master = 21;
    constexpr EventSymbol spmv__termiante_node_master = 22;
    constexpr EventSymbol spmv__init_updown_master = 23;
    constexpr EventSymbol spmv__updown_master = 24;
    constexpr EventSymbol spmv__terminate_updown_master = 25;
    constexpr EventSymbol spmv__lane_master_init = 26;
    constexpr EventSymbol spmv__lane_master_loop = 27;
    constexpr EventSymbol spmv__lane_master_read_partition = 28;
    constexpr EventSymbol spmv__lane_master_get_next_return = 29;
    constexpr EventSymbol spmv__lane_master_terminate = 30;
    constexpr EventSymbol spmv__lane_master_launch_worker = 31;
    constexpr EventSymbol spmv__init_global_snyc = 32;
    constexpr EventSymbol spmv__init_node_sync = 33;
    constexpr EventSymbol spmv__ud_accumulate = 34;
    constexpr EventSymbol spmv__global_sync_return = 35;
    constexpr EventSymbol spmv__node_sync_return = 36;
    constexpr EventSymbol spmv__kv_map_return = 37;
    constexpr EventSymbol spmv__worker_init = 38;
    constexpr EventSymbol spmv__worker_work = 39;
    constexpr EventSymbol spmv__worker_claim_local = 40;
    constexpr EventSymbol spmv__worker_claim_remote = 41;
    constexpr EventSymbol spmv__worker_helper = 42;
    constexpr EventSymbol spmv__worker_claimed_map = 43;
    constexpr EventSymbol spmv__receiver_claim_work = 44;
    constexpr EventSymbol spmv__receiver_set_terminate_bit = 45;
    constexpr EventSymbol spmv__receiver_set_terminate_bit_ret = 46;
    constexpr EventSymbol spmv__mapper_control_init = 47;
    constexpr EventSymbol spmv__mapper_control_read_partition = 48;
    constexpr EventSymbol spmv__mapper_control_get_next_return = 49;
    constexpr EventSymbol spmv__mapper_control_loop = 50;
    constexpr EventSymbol spmv__lane_remote_mapper_finished = 51;
    constexpr EventSymbol matvecmul_master__mv_init = 52;
    constexpr EventSymbol matvecmul_master__cache_metadata_return = 53;
    constexpr EventSymbol matvecmul_master__spmv_term = 54;
    constexpr EventSymbol lane_manager__cache_metadata = 55;
    constexpr EventSymbol spmv__kv_map = 56;
    constexpr EventSymbol spmv__launch_strip = 57;
    constexpr EventSymbol spmv__strip_worker_return = 58;
    constexpr EventSymbol spmv__stream_complete = 59;
    constexpr EventSymbol strip_worker__launch_strip = 60;
    constexpr EventSymbol strip_worker__matval_return = 61;
    constexpr EventSymbol strip_worker__matcol_return = 62;
    constexpr EventSymbol strip_worker__fetch_ele0 = 63;
    constexpr EventSymbol strip_worker__fetch_ele1 = 64;
    constexpr EventSymbol strip_worker__fetch_ele2 = 65;
    constexpr EventSymbol strip_worker__fetch_ele3 = 66;
    constexpr EventSymbol strip_worker__fetch_ele4 = 67;
    constexpr EventSymbol strip_worker__fetch_ele5 = 68;
    constexpr EventSymbol strip_worker__fetch_ele6 = 69;
    constexpr EventSymbol strip_worker__fetch_ele7 = 70;
    constexpr EventSymbol partial_strip_worker__launch_strip = 71;
    constexpr EventSymbol partial_strip_worker__matval_return = 72;
    constexpr EventSymbol partial_strip_worker__matcol_return = 73;
    constexpr EventSymbol partial_strip_worker__fetch_ele0 = 74;
    constexpr EventSymbol partial_strip_worker__fetch_ele1 = 75;
    constexpr EventSymbol partial_strip_worker__fetch_ele2 = 76;
    constexpr EventSymbol partial_strip_worker__fetch_ele3 = 77;
    constexpr EventSymbol partial_strip_worker__fetch_ele4 = 78;
    constexpr EventSymbol partial_strip_worker__fetch_ele5 = 79;
    constexpr EventSymbol partial_strip_worker__fetch_ele6 = 80;

} // namespace

#endif