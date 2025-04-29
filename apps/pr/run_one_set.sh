#!/bin/bash
install_dir="$UPDOWN_SOURCE_CODE/install/updown/apps"
graph_dir="$UPDOWN_DATA_DIR/pr"
parser_path="$UPDOWN_SOURCE_CODE/common/parse_results.py"

graphs=("ca-AstroPh" "com-youtube.ungraph" "cit-Patents" "com-lj.ungraph" "web-Google" "flickrEdges" "mico" "com-orkut.ungraph")

mode=$1
num_nodes=$2
perflog_path="${install_dir}/PagerankMsrEFA_${mode}.bin.logs/perflog.tsv"
save_perflog_path="~/pr_perflog"

cd $install_dir;

for i in "${!graphs[@]}"; do
	echo ./pr $mode $num_nodes ${graph_dir}/${graphs[$i]}.txt
	./pr $mode $num_nodes ${graph_dir}/${graphs[$i]}.txt
	python3 $parser_path $perflog_path "Summary: PR ${mode} ${graphs[$i]}" "UDKVMSR Initialization Finished." "Finish PageRank"
done
