#!/bin/bash

# Define the array of graph names
graphs=(ca-AstroPh soc-Epinions1 musae_facebook deezer_europe email-Enron cit-HepPh ca-CondMat ca-HepPh)
num_vertex=(18772	75879	22470	28281	36692	34546	23133	12008)

# Directories
input_dir="$UPDOWN_DATA_DIR"
output_dir="$UPDOWN_DATA_DIR/js"
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