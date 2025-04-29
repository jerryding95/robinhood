### The following variables are used in this Makefile:
LINKER_DIR = $(UPDOWN_SOURCE_CODE)/linker/
LINKER = $(LINKER_DIR)EFAlinker.py

UDWEAVE_DIR = $(UPDOWN_SOURCE_CODE)/udweave
UDWEAVE = $(UDWEAVE_DIR)/UDweave.py

INSTALL_DIR = $(UPDOWN_SOURCE_CODE)/install
.DEFAULT_GOAL := all

spmvMSR_${mode}.py: spmvMSREFA.py
	python3 $(LINKER) -L $(UPDOWN_SOURCE_CODE)/libraries/UDMapShuffleReduce/linkable/ \
		-L $(UPDOWN_SOURCE_CODE)/libraries/LMStaticMaps/LMStaticMap.py \
		-o $@ $^
	cd $(UPDOWN_SOURCE_CODE)/udbasim/assembler; \
	python3 efa2bin.py \
		--efa $(UPDOWN_SOURCE_CODE)/apps/spmv_coo/spmvMSR_${mode}.py \
		--outpath $(UPDOWN_SOURCE_CODE)/install/updown/apps/ \
		--toplinker 

all: spmvMSR_${mode}.py

clean:
	@rm -f spmvMSR.py