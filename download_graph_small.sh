#!/bin/bash

# List of graph files to download
graphs=(
    "ca-AstroPh"
    "soc-Epinions1"
    # "musae_facebook"
    # "deezer_europe"
    "email-Enron"
    "cit-HepPh"
    "ca-CondMat"
    "ca-HepPh"
)

zip_graphs=(
    "facebook_large.zip"
    "deezer_europe.zip"
)
zip_graph_files=(
    "musae_facebook"
    "deezer_europe"
)

# Base URL for downloading the graphs
base_url="https://snap.stanford.edu/data"

# Create a directory to store the downloaded files
output_dir=$UPDOWN_DATA_DIR
mkdir -p "$output_dir"

# Download and unzip the zip files
for i in "${!zip_graphs[@]}"; do
    zip_file="${zip_graphs[$i]}"
    csv_file="${zip_graph_files[$i]}_edges.csv"
    echo "Downloading $zip_file..."
    wget -q -P "$output_dir" "$base_url/$zip_file"
    if [[ $? -eq 0 ]]; then
        echo "$zip_file downloaded successfully."
        unzip -o "$output_dir/$zip_file" -d "$output_dir"
        rm -f "$output_dir/$zip_file"
        if [[ -f "$output_dir/${zip_file%.zip}/$csv_file" ]]; then
            echo "Moving $csv_file to $output_dir and cleaning up..."
            mv "$output_dir/${zip_file%.zip}/$csv_file" "$output_dir/"
            rm -rf "$output_dir/${zip_file%.zip}"
        else
            echo "$csv_file not found in the unzipped directory."
        fi
    else
        echo "Failed to download $zip_file."
    fi
done

# Convert CSV files to TXT files
for csv_file in "${zip_graph_files[@]}"; do
    input_csv="$output_dir/${csv_file}_edges.csv"
    output_txt="$output_dir/${csv_file}.txt"
    if [[ -f "$input_csv" ]]; then
        echo "Converting $input_csv to $output_txt..."
        awk -F, 'NR > 1 {print $1, $2}' "$input_csv" > "$output_txt"
        if [[ $? -eq 0 ]]; then
            echo "Conversion successful: $output_txt"
            rm -f "$input_csv"
            echo "Deleted CSV file: $input_csv"
        else
            echo "Failed to convert $input_csv to TXT."
        fi
    else
        echo "CSV file $input_csv not found. Skipping conversion."
    fi
done

# Download each graph file
for graph in "${graphs[@]}"; do
    echo "Downloading $graph..."
    wget -q -P "$output_dir" "$base_url/$graph.txt.gz"
    if [[ $? -eq 0 ]]; then
        echo "$graph downloaded successfully."
    else
        echo "Failed to download $graph."
    fi
    gunzip -f "$output_dir/$graph.txt.gz"
done

echo "All downloads completed. Files are saved in the '$output_dir' directory."