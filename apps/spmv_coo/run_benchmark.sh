#!/bin/bash

matrices=("inline_1" "flickr" "HFE18_96_in" "c8_mat11" "audikw_1" "mycielskian20" "as-Skitter" "Freescale1" "mip1" "torso1" "eu-2005" "NLR")
progs=("spmv_udkvmsr")
dirs=("spmvMSR.bin.logs")
num_lanes=(16384 16384 1024 2048 16384 16384 16384 16384 16384 16384 16384 16384)
modes=(0 1 1 0 0 1 1 0 1 0 1 1)

# matrices=("audikw_1" "mycielskian20" "Freescale1" "mip1" "torso1")
# num_lanes=(16384 16384 16384 16384 16384)
# modes=(0 1 0 1 0)


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
	echo ./spmv_udkvmsr ../../../../matrices/${matrices[i]}/${matrices[i]}.mtx 256 ${modes[i]}; 
	eval ./spmv_udkvmsr ../../../../matrices/${matrices[i]}/${matrices[i]}.mtx 256 ${modes[i]} > ${matrices[i]}.log;
	# eval ./spmvLBMSRPerfFileTest ../../../../matrices/${matrices[i]}/${matrices[i]}_csr.mtx ${num_lanes[i]} > ${matrices[i]}.log;

	cat spmvMSR.bin.logs/perflog.tsv; 
	# python3 parse.py;
done

# for dir in "${dirs[@]}"; do 
# 	cat ${dir}/perflog.tsv; 
# done

eval cd ${cwd}
