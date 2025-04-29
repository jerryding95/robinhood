#!/bin/bash
install_dir="$UPDOWN_SOURCE_CODE/install/updown/apps"
matrix_dir="$UPDOWN_DATA_DIR"
parser_path="$UPDOWN_SOURCE_CODE/common/parse_results.py"

matrices=("inline_1" "flickr" "HFE18_96_in" "c8_mat11" "audikw_1" "mycielskian20" "as-Skitter" "Freescale1" "mip1" "torso1" "eu-2005" "NLR")
mtx_modes=(0 1 1 0 0 1 1 0 1 0 1 1)

mode=$1
num_nodes=$2
perflog_path="${install_dir}/spmvMSR_${mode}.bin.logs/perflog.tsv"
save_perflog_path="~/spmv_coo_perflog"

cd $install_dir;

for i in "${!matrices[@]}"; do
	echo ./spmv_coo $mode $num_nodes ${matrix_dir}/${matrices[$i]}.txt ${mtx_modes[$i]}
	./spmv_coo $mode $num_nodes ${matrix_dir}/${matrices[$i]}.txt ${mtx_modes[$i]}
	python3 $parser_path $perflog_path "Summary: SPMV_COO ${mode} ${graphs[$i]}" "UDKVMSR Initialization Finished." "MSR terminate"
done
