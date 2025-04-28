### The following variables are used in this Makefile:
LINKER_DIR = ../../linker/
LINKER = $(LINKER_DIR)EFAlinker.py

UDWEAVE_DIR = ../../../udweave
UDWEAVE = $(UDWEAVE_DIR)/UDweave.py

INSTALL_DIR = ../../../install
.DEFAULT_GOAL := all

spmvMSR.py: spmvMSREFA.py
	python3 $(LINKER) -L ../../libraries/UDMapShuffleReduce/linkable/ \
		-L ../../libraries/LMStaticMaps/LMStaticMap.py \
		-o $@ $^
	cd ../../udbasim/assembler; \
	python3 efa2bin.py \
		--efa ../../apps/spmv/spmvMSR.py \
		--outpath ../../install/updown/apps/ \
		--toplinker --debug-messages

all: spmvMSR.py

clean:
	@rm -f spmvMSR.py