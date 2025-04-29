#!/bin/bash
install_dir="$UPDOWN_SOURCE_CODE/install/updown/apps"
matrix_dir="$UPDOWN_DATA_DIR/csr"
parser_path="$UPDOWN_SOURCE_CODE/common/parse_results.py"

matrices=("inline_1" "flickr" "HFE18_96_in" "c8_mat11" "audikw_1" "mycielskian20" "as-Skitter" "Freescale1" "mip1" "torso1" "eu-2005" "NLR")

mode=$1
num_nodes=$2
perflog_path="spmv_lbmsr_exe_${mode}.bin.logs/perflog.tsv"
save_perflog_path="~/spmv_csr_perflog"

cd $install_dir;

for i in "${!matrices[@]}"; do
	echo ./spmv_csr $mode $num_nodes ${matrix_dir}/${matrices[$i]}_csr.mtx
	./spmv_csr $mode $num_nodes ${matrix_dir}/${matrices[$i]}_csr.mtx
	python3 $parser_path $perflog_path "Summary: SPMV_CSR ${mode} ${graphs[$i]}" "UDKVMSR Initialization Finished." "KVMSR Return"
done
