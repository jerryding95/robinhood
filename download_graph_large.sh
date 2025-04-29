#!/bin/bash

# List of graph files to download (base names, without extensions)
graphs=(
    "ca-AstroPh"
    "com-youtube.ungraph"
    "cit-Patents"
    "com-lj.ungraph"
    "web-Google"
    "flickrEdges"
    # "mico"
    "com-orkut.ungraph"
)

# Corresponding download links (relative SNAP paths or full URLs)
links=(
    "ca-AstroPh.txt.gz"
    "bigdata/communities/com-youtube.ungraph.txt.gz"
    "cit-Patents.txt.gz"
    "bigdata/communities/com-lj.ungraph.txt.gz"
    "web-Google.txt.gz"
    "flickrEdges.txt.gz"
    # "https://www.dropbox.com/scl/fo/vzgbdupimwncae24891mi/ACHGAeFPgvNR_xIMOrYbIDE/mico?dl=1"
    "bigdata/communities/com-orkut.ungraph.txt.gz"
)

base_url="https://snap.stanford.edu/data"
output_dir="$UPDOWN_DATA_DIR"
mkdir -p "$output_dir"

for idx in "${!graphs[@]}"; do
    name="${graphs[$idx]}"
    link="${links[$idx]}"

    echo "Downloading $name..."
    if [[ "$link" =~ ^https?:// ]]; then
        url="$link"
        outpath="$output_dir/$name"
    else
        url="$base_url/$link"
        outpath="$output_dir/$name.txt.gz"
    fi

    wget -q -O "$outpath" "$url"
    if [[ $? -eq 0 ]]; then
        if [[ "$outpath" == *.gz ]]; then
            echo "  -> $name downloaded, unzipping..."
            gunzip -c "$outpath" > "$output_dir/$name.txt"
            echo "  -> $name unzipped successfully."
            rm -f "$outpath"     # <-- remove archive after unzip
        else
            echo "  -> $name downloaded successfully."
        fi
    else
        echo "  !! Warning: failed to download $name from $url"
    fi
done

echo "All done. Files are in '$output_dir'."