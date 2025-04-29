modes=(
    "nlb"
    "ws"
    "rh_nlbstrm_off"
    "rh_nlbstrm_on"
    "rh_random"
)

num_nodes=8

for mode in "${modes[@]}"; do
    $UPDOWN_SOURCE_CODE/apps/spmv_coo/run_one_set.sh "$mode" "$num_nodes"
done