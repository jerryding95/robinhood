#!/bin/bash

graphs=("com-youtube.ungraph" "cit-Patents" "com-lj.ungraph" "web-Google" "flickrEdges" "mico") #"com-friendster" "com-orkut.ungraph") # "twitter_rv")
#graphs=("web-Google" "flickrEdges" "mico")
install_dir="../../../install/updown/apps"
graph_dir="../../../../graphs"
perflog_path="tc_udkvmsr_exe.bin.logs/perflog.tsv"
num_nodes=$1
num_lanes=$((num_nodes * 2048))

cd $install_dir;
for g in ${graphs[@]}; do
	echo ./tc_udkvmsr ${graph_dir}/${g}.txt_gv.bin ${graph_dir}/${g}.txt_nl.bin ${num_lanes} ${num_lanes} 0
	./tc_udkvmsr ${graph_dir}/${g}.txt_gv.bin ${graph_dir}/${g}.txt_nl.bin ${num_lanes} ${num_lanes} 0 > test.log
	tail -8 test.log
	cat $perflog_path
done
