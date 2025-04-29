modes=(
    "nlb"
    "ws"
    "rh_nlbstrm_off"
    "rh_nlbstrm_on"
    "rh_random"
)

num_nodes=1

for mode in "${modes[@]}"; do
    $UPDOWN_SOURCE_CODE/apps/gcn_vanilla/run_one_set.sh "$mode" "$num_nodes"
done