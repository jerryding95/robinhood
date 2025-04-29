#!/bin/bash
variables=("intermediate_ptr_offset" "intermediate_cache_entry_size" "intermediate_cache_offset" "materializing_metadata_offset" "materialize_kv_cache_offset" "materialize_kv_cache_size" "unresolved_kv_count_offset" "intermediate_cache_count" "materialize_kv_cache_count")
encodings=("111111" "222222" "333333" "444444" "555555" "666666" "888888" "999999" "101010")

for i in ${!variables[@]}; do
	sed -i -e "s/${encodings[$i]}/{self.${variables[$i]}}/g" $1 #load_balancer_events.py
done

echo sed -i -e 's/ 7/ {self.inter_kvpair_size}/g' $1
sed -i -e 's/ 7/ {self.inter_kvpair_size}/g' $1 #load_balancer_events.py
echo sed -i -e 's/ 56/ {self.inter_kvpair_size * WORD_SIZE}/g' $1
sed -i -e 's/ 56/ {self.inter_kvpair_size * WORD_SIZE}/g' $1 #load_balancer_events.py
echo sed -i -e 's/receiver::receiver_materialize_kv_ret/{self.ln_receiver_materialize_ret_ev_label}/g' $1
sed -i -e 's/receiver::receiver_materialize_kv_ret/{self.ln_receiver_materialize_ret_ev_label}/g' $1 #load_balancer_events.py
echo sed -i -e 's/receiver::receiver_update_unresolved_kv_count/{self.ln_receiver_update_unresolved_kv_count_ev_label}/g' $1
sed -i -e 's/receiver::receiver_update_unresolved_kv_count/{self.ln_receiver_update_unresolved_kv_count_ev_label}/g' $1 #load_balancer_events.py

