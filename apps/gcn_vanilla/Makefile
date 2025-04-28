### The following variables are used in this Makefile:
LINKER_DIR = $(UPDOWN_SOURCE_CODE)/linker/
LINKER = $(LINKER_DIR)EFAlinker.py

UDWEAVE_DIR = $(UPDOWN_SOURCE_CODE)/udweave
UDWEAVE = $(UDWEAVE_DIR)/UDweave.py

INSTALL_DIR = ../../install
.DEFAULT_GOAL := all

gcn_udkvmsr.py: gcn.udw
	python3 $(UDWEAVE) -i $^ -o $@

gcn_udkvmsr_exe_nlb.py: gcn_udkvmsr.py #gnnMSR.py
	python3 $(LINKER) -L $(UPDOWN_SOURCE_CODE)/libraries/UDMapShuffleReduce/linkable/ \
		-L $(UPDOWN_SOURCE_CODE)/libraries/LMStaticMaps/LMStaticMap.py \
		-L $(UPDOWN_SOURCE_CODE)/libraries/SpMalloc/SpMalloc.py \
		-o $@ $^

gcn_udkvmsr_exe_nlb.bin: gcn_udkvmsr_exe_nlb.py
	cd $(UPDOWN_SOURCE_CODE)/udbasim/assembler; \
	python3 efa2bin.py \
		--efa $(UPDOWN_SOURCE_CODE)/apps/gcn_vanilla/$^ \
		--outpath $(UPDOWN_SOURCE_CODE)/install/updown/apps/ \
		--toplinker
# 	python3 ../../../udbasim/assembler/efa2bin.py \
		--efa $^ \
		--outpath $(INSTALL_DIR)/updown/apps/ \
		--toplinker --debug-messages

all: gcn_udkvmsr.py gcn_udkvmsr_exe_nlb.py gcn_udkvmsr_exe_nlb.bin

clean:
	@rm -f gcn_udkvmsr.py gcn_udkvmsr_exe_nlb.py gcn_udkvmsr_exe_nlb.hpp
