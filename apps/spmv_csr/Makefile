### The following variables are used in this Makefile:
LINKER_DIR = ../../linker/
LINKER = $(LINKER_DIR)EFAlinker.py

UDWEAVE_DIR = ../../../udweave
UDWEAVE = $(UDWEAVE_DIR)/UDweave.py

INSTALL_DIR = ../../../install
.DEFAULT_GOAL := all


genSpMV: 
	python3 $(UDWEAVE) -i spmv.udw -o ./out/spmvEFA.py

spmv_udkmvsr: spmvMSRModule.py
	python3 $(LINKER) -f linkable-module -L./ -L../../libraries/UDMapShuffleReduce/linkable -L../../libraries/UDMapShuffleReduce -L../../../  -o ./out/$@ $^

spmv_msr_exe: ./out/spmv_udkmvsr.py ./out/spmvEFA.py
	python3 $(LINKER)  -o ./$@ $^

spmv_lbudkmvsr: spmvLBMSRModule.py
	python3 $(LINKER) -f linkable-module -L./ -L../../libraries/UDMapShuffleReduce/linkable -L../../libraries/UDMapShuffleReduce -L../../../  -o ./out/$@ $^

spmv_lbmsr_exe: ./out/spmv_lbudkmvsr.py ./out/spmvEFA.py
	python3 $(LINKER)  -o ./$@ $^;
	cd ../../udbasim/assembler; \
	python3 efa2bin.py --efa ../../apps/spmv_udkvmsr/spmv_lbmsr_exe.py --outpath ../../install/updown/apps --debug-messages

all: genSpMV spmv_udkmvsr spmv_msr_exe spmv_lbudkmvsr spmv_lbmsr_exe

clean:
	rm -f *.exe *.out *.o
