#ifndef __spmv_lbmsr_exe_nlb_H__
#define __spmv_lbmsr_exe_nlb_H__

namespace spmv_lbmsr_exe_nlb {

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
    constexpr EventSymbol spmv__init_global_snyc = 31;
    constexpr EventSymbol spmv__init_node_sync = 32;
    constexpr EventSymbol spmv__ud_accumulate = 33;
    constexpr EventSymbol spmv__global_sync_return = 34;
    constexpr EventSymbol spmv__node_sync_return = 35;
    constexpr EventSymbol spmv__kv_map_return = 36;
    constexpr EventSymbol matvecmul_master__mv_init = 37;
    constexpr EventSymbol matvecmul_master__cache_metadata_return = 38;
    constexpr EventSymbol matvecmul_master__spmv_term = 39;
    constexpr EventSymbol lane_manager__cache_metadata = 40;
    constexpr EventSymbol spmv__kv_map = 41;
    constexpr EventSymbol spmv__launch_strip = 42;
    constexpr EventSymbol spmv__strip_worker_return = 43;
    constexpr EventSymbol spmv__stream_complete = 44;
    constexpr EventSymbol strip_worker__launch_strip = 45;
    constexpr EventSymbol strip_worker__matval_return = 46;
    constexpr EventSymbol strip_worker__matcol_return = 47;
    constexpr EventSymbol strip_worker__fetch_ele0 = 48;
    constexpr EventSymbol strip_worker__fetch_ele1 = 49;
    constexpr EventSymbol strip_worker__fetch_ele2 = 50;
    constexpr EventSymbol strip_worker__fetch_ele3 = 51;
    constexpr EventSymbol strip_worker__fetch_ele4 = 52;
    constexpr EventSymbol strip_worker__fetch_ele5 = 53;
    constexpr EventSymbol strip_worker__fetch_ele6 = 54;
    constexpr EventSymbol strip_worker__fetch_ele7 = 55;
    constexpr EventSymbol partial_strip_worker__launch_strip = 56;
    constexpr EventSymbol partial_strip_worker__matval_return = 57;
    constexpr EventSymbol partial_strip_worker__matcol_return = 58;
    constexpr EventSymbol partial_strip_worker__fetch_ele0 = 59;
    constexpr EventSymbol partial_strip_worker__fetch_ele1 = 60;
    constexpr EventSymbol partial_strip_worker__fetch_ele2 = 61;
    constexpr EventSymbol partial_strip_worker__fetch_ele3 = 62;
    constexpr EventSymbol partial_strip_worker__fetch_ele4 = 63;
    constexpr EventSymbol partial_strip_worker__fetch_ele5 = 64;
    constexpr EventSymbol partial_strip_worker__fetch_ele6 = 65;

} // namespace

#endif