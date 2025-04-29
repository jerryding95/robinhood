#!/bin/bash
install_dir="$UPDOWN_SOURCE_CODE/install/updown/apps"
app_dir="$UPDOWN_SOURCE_CODE/apps/sorting"

# sigma divider from 1 to 37 and step size 3
sigma_dividers=(1 4 7 10 13 16 19 22 25 28 31 34 37)

mode=$1
num_nodes=$2
sortmode=$3
perflog_path="sortingEFA_${mode}_${sortmode}.bin.logs/perflog.tsv"
save_perflog_path="~/sorting_perflog"


for sigma_divider in "${sigma_dividers[@]}"; do
	cd $install_dir;

	echo ./sorting $mode $num_nodes $sortmode $sigma_divider
	
	# num_input_keys=16384
	# num_bins=16384
	if [ "$sortmode" == "insertion" ]; then
		num_input_keys=16777216
		num_bins=131072
	else
		num_input_keys=1073741824
		num_bins=8388608
	fi


	./sorting $mode $num_nodes $sortmode $num_input_keys $num_bins 1000000000 $sigma_divider 1>sorting.out 2>sorting.err

	cd $app_dir;
	if [ "$sortmode" == "insertion" ]; then
		python ../../common/parse_results.py $install_dir/$perflog_path "sorting_${sortmode} ${mode} ${sigma_divider}" "sorting 1" "sorting end"
	else
		python ../../common/parse_results.py $install_dir/$perflog_path "sorting_${sortmode} ${mode} ${sigma_divider}" "sorting phase 2" "sorting end"
	fi
done
