#!/bin/bash

matrices=("inline_1" "flickr" "HFE18_96_in" "c8_mat11" "audikw_1" "mycielskian20" "as-Skitter" "Freescale1" "mip1" "torso1" "eu-2005" "NLR")
progs=("spmvLBMSRPerfFileTest")
dirs=("spmv_lbmsr_exe.bin.logs")
num_lanes=(16384 16384 1024 2048 16384 16384 16384 16384 16384 16384 16384 16384)

# matrices=("audikw_1" "mycielskian20" "as-Skitter" "Freescale1" "mip1" "torso1" "eu-2005" "NLR")
# num_lanes=(16384 16384 16384 16384 16384 16384 16384 16384)


cwd=$(pwd)

echo 111;
# cd ~/matrices/csr
# echo python3 ~/lb/updown/apps/spmv_perf/coo2csr.py ../${mat}/${mat}.mtx
# eval python3 ~/lb/updown/apps/spmv_perf/coo2csr.py ../${mat}/${mat}.mtx

# cd ~/updown/install/updown/apps
for i in ${!matrices[@]}; do
	# cd ~/updown/apps/spmv_perf/
	# echo python3 coo2csr.py ~/matrices/${matrices[i]}/${matrices[i]}.mtx
	# eval python3 coo2csr.py ~/matrices/${matrices[i]}/${matrices[i]}.mtx

	cd ~/updown/install/updown/apps
	echo ./spmvLBMSRPerfFileTest ../../../../matrices/${matrices[i]}/${matrices[i]}_csr.mtx ${num_lanes[i]}; 
	# eval ./spmvLBMSRPerfFileTest ../../../../matrices/${matrices[i]}/${matrices[i]}_csr.mtx ${num_lanes[i]} > ${matrices[i]}.log;

	# cat spmv_lbmsr_exe.bin.logs/perflog.tsv; 
	# python3 parse.py;
done

# for dir in "${dirs[@]}"; do 
# 	cat ${dir}/perflog.tsv; 
# done

eval cd ${cwd}