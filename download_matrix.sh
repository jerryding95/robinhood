#!/bin/bash
set -euo pipefail

# target directory (ensure UPDOWN_DATA_DIR is set in your env)
output_dir="$UPDOWN_DATA_DIR"
mkdir -p "$output_dir"

# list of datasets (base names)
tamu_graphs=(
  inline_1
  flickr
  HFE18_96_in
  c8_mat11
  audikw_1
  mycielskian20
  as-Skitter
  Freescale1
  mip1
  torso1
  eu-2005
  NLR
)

# SuiteSparse Matrix Market overrides: <matrix>.tar.gz URLs under the SS web site
declare -A overrides=(
  [inline_1]="MM/GHS_psdef/inline_1.tar.gz"
  [flickr]="MM/Gleich/flickr.tar.gz"
  [HFE18_96_in]="MM/JGD_Groebner/HFE18_96_in.tar.gz"
  [c8_mat11]="MM/JGD_Groebner/c8_mat11.tar.gz"
  [audikw_1]="MM/GHS_psdef/audikw_1.tar.gz"
  [mycielskian20]="MM/Mycielski/mycielskian20.tar.gz"
  [as-Skitter]="MM/SNAP/as-Skitter.tar.gz"
  [Freescale1]="MM/Freescale/Freescale1.tar.gz"
  [mip1]="MM/Andrianov/mip1.tar.gz"
  [torso1]="MM/Norris/torso1.tar.gz"
  [eu-2005]="MM/LAW/eu-2005.tar.gz"
  [NLR]="MM/DIMACS10/NLR.tar.gz"
)

SS_BASE="https://suitesparse-collection-website.herokuapp.com"

# TAMU fallback (Matrix Market .mtx.gz)
TAMU_BASE="https://sparse.tamu.edu/mat"

download_and_unpack() {
  local url=$1 out=$2 mode=$3 base name
  echo "  → fetching [$mode] $url"

  if wget -q -O "$out" "$url"; then
    echo "    • downloaded $(basename "$out")"
    case "$out" in
      *.tar.gz)
        # strip one leading directory, extract only the .mtx, write to $output_dir/<base>.mtx
        base=$(basename "$out" .tar.gz)
        tar -xOzf "$out" --strip-components=1 --wildcards '*.mtx' > "$output_dir/$base.mtx"
        ;;
      *.mtx.gz)
        # write directly to $output_dir/<name>.mtx
        name=$(basename "$out" .gz)   # yields e.g. "inline_1.mtx"
        gunzip -c "$out" > "$output_dir/$name"
        ;;
    esac
    echo "    • unpacked into '$output_dir'"
    rm -f "$out"
  else
    echo "    !! failed to fetch $url"
    return 1
  fi
}

for g in "${tamu_graphs[@]}"; do
  echo "Processing $g …"

  # 1) Try SuiteSparse override if present
  if [[ -n "${overrides[$g]:-}" ]]; then
    url="$SS_BASE/${overrides[$g]}"
    out="$output_dir/$g.tar.gz"
    if download_and_unpack "$url" "$out" "SuiteSparse"; then
      continue
    fi
  fi

  # 2) Fallback to TAMU (.mtx.gz)
  url="$TAMU_BASE/$g.mtx.gz"
  out="$output_dir/$g.mtx.gz"
  if download_and_unpack "$url" "$out" "TAMU"; then
    continue
  fi

  echo " !! ERROR: Could not download '$g' from either SuiteSparse or TAMU."
done

echo "All done. Files are in '$output_dir'."