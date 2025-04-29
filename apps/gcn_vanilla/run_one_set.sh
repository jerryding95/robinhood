#!/bin/bash
install_dir="$UPDOWN_SOURCE_CODE/install/updown/apps"
graph_dir="$UPDOWN_DATA_DIR"
parser_path="$UPDOWN_SOURCE_CODE/common/parse_results.py"

graphs=(ca-AstroPh	soc-Epinions1	musae_facebook	deezer_europe	email-Enron	cit-HepPh	ca-CondMat	ca-HepPh)
vertices=(18772	75879	22470	28281	36692	34546	23133	12008)
edges=(396160	508837	342004	185504	367662	843156	186994	237042)

mode=$1
num_nodes=$2
perflog_path="${install_dir}/gcn_udkvmsr_exe_${mode}.bin.logs/perflog.tsv"
save_perflog_path="~/gcn_perflog"

cd $install_dir;

for i in "${!graphs[@]}"; do
	echo ./gcn_vanilla $mode $num_nodes ${graph_dir}/${graphs[$i]}.txt ${vertices[$i]} ${edges[$i]}
	./gcn_vanilla $mode $num_nodes ${graph_dir}/${graphs[$i]}.txt ${vertices[$i]} ${edges[$i]}
	python3 $parser_path $perflog_path "Summary: GCN ${mode} ${graphs[$i]}" "UDKVMSR Initialization Finished." "GNN finished"
done
