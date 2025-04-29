#!/bin/bash

modes=(
    "nlb"
    "ws"
    "rh_nlbstrm_off"
    "rh_nlbstrm_on"
    "rh_random"
)

install_dir="$UPDOWN_SOURCE_CODE/install/updown/apps"
matrix_dir="$UPDOWN_DATA_DIR/scaleup/Freescale1.mtx"
matrix="Freescale1_scaleup"
graph_dir="$UPDOWN_DATA_DIR/scaleup/com-lj.ungraph.txt"
graph="com-lj.ungraph_scaleup"
parser_path="$UPDOWN_SOURCE_CODE/common/parse_results.py"

num_nodes=(8) # 16 32 64 128 256 512)
for mode in "${modes[@]}"; do
    perflog_path_spmv="${install_dir}/spmv_lbmsr_exe_${mode}.bin.logs/perflog.tsv"
    perflog_path_tc="${install_dir}/tc_udkvmsr_exe_${mode}.bin.logs/perflog.tsv"

    cd $install_dir;
    for num_node in "${num_nodes[@]}"; do
        echo ./spmv_csr $mode $num_node ${matrix_dir}
        ./spmv_csr $mode $num_node ${matrix_dir}
        python3 $parser_path $perflog_path_spmv "Summary: SPMV_CSR ${mode} ${matrix} ${num_node}" "UDKVMSR Initialization Finished." "KVMSR Return"
        
        echo ./tc $mode $num_nodes ${graph_dir}
        ./tc $mode $num_nodes ${graph_dir}
        python3 $parser_path $perflog_path_tc "Summary: TC ${mode} ${graph} ${num_node}" "UDKVMSR Initialization Finished." "TC finished"
    done
done
