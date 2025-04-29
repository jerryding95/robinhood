modes=(
    "nlb"
    "ws"
    "rh_nlbstrm_off"
    "rh_nlbstrm_on"
    "rh_random"
)

sortmodes=(
    "map"
    "reduce"
    "insertion"
)

num_nodes=8


for sortmode in "${sortmodes[@]}"; do
    for mode in "${modes[@]}"; do
        $UPDOWN_SOURCE_CODE/apps/sorting/run_one_set.sh "$mode" "$num_nodes" "$sortmode"
    done
done