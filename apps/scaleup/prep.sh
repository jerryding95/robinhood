#!/bin/bash

# Freescale*64
# live-Journal*32

mkdir -p $UPDOWN_DATA_DIR/scaleup

LINE="4847571 4847571 68993773"
# Source to COO
sed "1,4d" \
  "$UPDOWN_DATA_DIR/com-lj.ungraph.txt" \
> "$UPDOWN_DATA_DIR/scaleup/com-lj.ungraph.txt_coo"
sed -i "1i ${LINE}" "$UPDOWN_DATA_DIR/scaleup/com-lj.ungraph.txt_coo"
# COO to CSR
python3 $UPDOWN_SOURCE_CODE/apps/scaleup/coo2csr.py $UPDOWN_DATA_DIR/scaleup/com-lj.ungraph.txt_coo 
# Duplicate
./duplicate_coo 32 $UPDOWN_DATA_DIR/scaleup/com-ljungraph_csr.txt_coo $UPDOWN_DATA_DIR/scaleup/com-lj.ungraph.txt 4847571 4847571 68993773 1
# Remove temp files
rm -f $UPDOWN_DATA_DIR/scaleup/com-lj.ungraph.txt_coo
rm -f $UPDOWN_DATA_DIR/scaleup/com-ljungraph_csr.txt_coo

graphs=(com-lj.ungraph)
num_vertex=(155122272)

# Directories
input_dir="$UPDOWN_DATA_DIR/scaleup"
output_dir="$UPDOWN_DATA_DIR/scaleup"
reorder_tool="$UPDOWN_SOURCE_CODE/apps/preprocess/reorder/MtxReorder"

# Ensure the output directory exists
mkdir -p "$output_dir"

# Loop through each graph and preprocess it
for i in "${!graphs[@]}"; do
    graph="${graphs[$i]}"
    num_vertices="${num_vertex[$i]}"
    input_file="$input_dir/$graph.txt_raw"
    output_file="$output_dir/$graph.txt"
    
    if [[ -f "$input_file" ]]; then
        echo "Processing $graph with $num_vertices vertices..."
        "$reorder_tool" "$input_file" "$output_file" "$num_vertices"
    else
        echo "Input file $input_file not found. Skipping $graph."
    fi
done
rm -f $UPDOWN_DATA_DIR/scaleup/com-lj.ungraph.txt_raw


cp $UPDOWN_DATA_DIR/Freescale1.mtx $UPDOWN_DATA_DIR/scaleup/Freescale1.mtx
# COO to CSR
python3 $UPDOWN_SOURCE_CODE/apps/spmv_csr/coo2csr.py $UPDOWN_DATA_DIR/scaleup/Freescale1.mtx
rm -f $UPDOWN_DATA_DIR/scaleup/Freescale1.mtx
# Duplicate
./duplicate_csr 64 $UPDOWN_DATA_DIR/scaleup/Freescale1_csr.mtx $UPDOWN_DATA_DIR/scaleup/Freescale1.mtx 3428755 3428755 18920347 1
# Remove temp files
rm -f $UPDOWN_DATA_DIR/scaleup/Freescale1_csr.mtx

echo "Preprocessing completed."