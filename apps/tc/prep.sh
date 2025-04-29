#!/bin/bash

# Define the array of graph names
graphs=(ca-AstroPh com-youtube cit-Patents live-Journal web-Google flickrEdges mico com-orkut)
num_vertex=(18772 1134890 3774768 4847571 875713 105938 96638 3072441)

# Directories
input_dir="$UPDOWN_DATA_DIR"
output_dir="$UPDOWN_DATA_DIR/tc"
reorder_tool="$UPDOWN_SOURCE_CODE/apps/preprocess/reorder/MtxReorder"

# Ensure the output directory exists
mkdir -p "$output_dir"

# Loop through each graph and preprocess it
for i in "${!graphs[@]}"; do
    graph="${graphs[$i]}"
    num_vertices="${num_vertex[$i]}"
    input_file="$input_dir/$graph.txt"
    output_file="$output_dir/$graph.txt"
    
    if [[ -f "$input_file" ]]; then
        echo "Processing $graph with $num_vertices vertices..."
        "$reorder_tool" "$input_file" "$output_file" "$num_vertices"
    else
        echo "Input file $input_file not found. Skipping $graph."
    fi
done

echo "Preprocessing completed."