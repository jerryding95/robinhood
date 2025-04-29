#!/bin/bash
pushd /media/data/andronicus/updown-develop/updown
source setup_env.sh
export PYTHONPATH=$PYTHONPATH:$(pwd)
pushd linker
./EFAlinker.py  ../libraries/SpMalloc/SpMalloc.py ../libraries/SpMalloc/testSpMallocEFA.py -o ../libraries/SpMalloc/spmalloc_test_exe

popd
pushd udbasim/assembler
python3 ./efa2bin.py --efa ../../libraries/SpMalloc/spmalloc_test_exe.py --outpath ../../install/updown/libraries --toplinker
# --debug-messages