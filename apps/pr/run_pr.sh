#!/bin/bash

graphs=("ca-AstroPh" "com-youtube.ungraph" "cit-Patents" "com-lj.ungraph" "web-Google" "flickrEdges" "mico" "com-orkut.ungraph") #"com-friendster" ) # "twitter_rv")
#graphs=("web-Google" "flickrEdges" "mico")
install_dir="../../install/updown/apps"
graph_dir="../../../../prgraphs"
perflog_path="PagerankMsrEFA.bin.logs/perflog.tsv"
num_nodes=$1
num_lanes=$((num_nodes * 2048))

# cd $install_dir;
# for g in ${graphs[@]}; do
# 	echo ./preprocess_pagerank ${graph_dir}/${g}.txt
# 	./preprocess_pagerank ${graph_dir}/${g}.txt
# done


cd $install_dir;
for g in ${graphs[@]}; do
	echo ./pagerankMapShuffleReduce ${graph_dir}/${g}.txt  ${num_nodes} 32 16
	./pagerankMapShuffleReduce ${graph_dir}/${g}.txt ${num_nodes} 32 16 > test.log
	tail -8 test.log
	cat $perflog_path
done
