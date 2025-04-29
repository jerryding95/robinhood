#!/bin/bash

# Directory containing the matrices in CSR format
matrix_dir="$UPDOWN_DATA_DIR"
output_dir="$UPDOWN_DATA_DIR/csr"
app_dir="$UPDOWN_SOURCE_CODE/apps/spmv_csr"

# List of matrices to preprocess
matrices=("inline_1" "flickr" "HFE18_96_in" "c8_mat11" "audikw_1" "mycielskian20" "as-Skitter" "Freescale1" "mip1" "torso1" "eu-2005" "NLR")

# Iterate over each matrix and preprocess it using coo2csr.py
for matrix in "${matrices[@]}"; do
    input_file="$UPDOWN_DATA_DIR/${matrix}.mtx"
    output_file="$UPDOWN_DATA_DIR/${matrix}_csr.mtx"
    
    # Create output directory if it doesn't exist
    mkdir -p "$output_dir"
    
    # Call coo2csr.py to preprocess the matrix
    python3 "$app_dir/coo2csr.py" "$input_file"
    
    if [ $? -eq 0 ]; then
        # Move the output file to the output directory
        mv "$output_file" "$output_dir/"
        if [ $? -eq 0 ]; then
            echo "Successfully processed and moved $matrix"
        else
            echo "Failed to move $matrix" >&2
        fi
    else
        echo "Failed to process $matrix" >&2
    fi
done