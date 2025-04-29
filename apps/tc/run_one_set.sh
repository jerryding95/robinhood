#!/bin/bash
install_dir="$UPDOWN_SOURCE_CODE/install/updown/apps"
graph_dir="$UPDOWN_DATA_DIR/preprocessed"
parser_path="$UPDOWN_SOURCE_CODE/common/parse_results.py"

graphs=("ca-AstroPh" "com-youtube.ungraph" "cit-Patents" "com-lj.ungraph" "web-Google" "flickrEdges" "mico" "com-orkut.ungraph")

mode=$1
num_nodes=$2
perflog_path="tc_udkvmsr_exe_${mode}.bin.logs/perflog.tsv"
save_perflog_path="~/tc_perflog"

cd $install_dir;

for i in "${!graphs[@]}"; do
	echo ./tc $mode $num_nodes ${graph_dir}/${graphs[$i]}.txt
	./tc $mode $num_nodes ${graph_dir}/${graphs[$i]}.txt
	python3 $parser_path $perflog_path "Summary: TC ${mode} ${graphs[$i]}" "UDKVMSR Initialization Finished." "TC finished"
done
