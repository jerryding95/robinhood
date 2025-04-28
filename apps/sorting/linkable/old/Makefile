### The following variables are used in this Makefile:
LINKER_DIR = ../../../linker/
LINKER = $(LINKER_DIR)EFAlinker.py

ASSEMBLER_DIR = ../../../udbasim/assembler/
ASSEMBLER = $(ASSEMBLER_DIR)efa2bin.py

INSTALL_DIR = ../../../install
.DEFAULT_GOAL := all



sorting_exe: sorting.py
	python3 $(LINKER) -L ../../../libraries/UDMapShuffleReduce/linkable/LinkableKVMapShuffleReduceTPL.py -L ../../../libraries/UDMapShuffleReduce/utils/IntermediateKeyValueSet.py  -L ../../../libraries/SingleLaneSort/hybrid_single_lane.py -L ../../../libraries/DistributedSort/distributed_sort.py -o ./$@ $^

all: sorting_exe

clean:
	rm -f *.exe *.out *.o