### The following variables are used in this Makefile:
LINKER_DIR = $(UPDOWN_SOURCE_CODE)/linker/
LINKER = $(LINKER_DIR)EFAlinker.py

UDWEAVE_DIR = $(UPDOWN_SOURCE_CODE)/udweave
UDWEAVE = $(UDWEAVE_DIR)/UDweave.py

INSTALL_DIR = $(UPDOWN_SOURCE_CODE)/install
.DEFAULT_GOAL := all


genSpMV: 
	python3 $(UDWEAVE) -i spmv.udw -o ./out/spmvEFA.py

spmv_lbudkmvsr_${mode}: spmvLBMSRModule.py
	python3 $(LINKER) -f linkable-module -L./ -L $(UPDOWN_SOURCE_CODE)/libraries/UDMapShuffleReduce/linkable -L $(UPDOWN_SOURCE_CODE)/libraries/UDMapShuffleReduce/ -o ./out/$@ $^

spmv_lbmsr_exe_${mode}: ./out/spmv_lbudkmvsr_${mode}.py ./out/spmvEFA.py
	python3 $(LINKER)  -o ./$@ $^;
	cd $(UPDOWN_SOURCE_CODE)/udbasim/assembler; \
	python3 efa2bin.py --efa $(UPDOWN_SOURCE_CODE)/apps/spmv_csr/spmv_lbmsr_exe_${mode}.py --outpath $(UPDOWN_SOURCE_CODE)/install/updown/apps

all: genSpMV spmv_lbudkmvsr_${mode} spmv_lbmsr_exe_${mode}

clean:
	rm -f *.exe *.out *.o
