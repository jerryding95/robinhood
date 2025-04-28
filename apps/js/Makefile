### The following variables are used in this Makefile:
LINKER_DIR = $(UPDOWN_SOURCE_CODE)/linker/
LINKER = $(LINKER_DIR)EFAlinker.py

UDWEAVE_DIR = $(UPDOWN_SOURCE_CODE)/udweave
UDWEAVE = $(UDWEAVE_DIR)/UDweave.py

INSTALL_DIR = $(UPDOWN_SOURCE_CODE)/install
.DEFAULT_GOAL := all

js_udkvmsr.py: js.udw
	python3 $(UDWEAVE) -i $^ -o $@

js_udkvmsr_exe_${mode}.py: js_udkvmsr.py #jsMSR.py
	python3 $(LINKER) -L $(UPDOWN_SOURCE_CODE)/libraries/UDMapShuffleReduce/linkable/ \
		-L $(UPDOWN_SOURCE_CODE)/libraries/LMStaticMaps/LMStaticMap.py \
		-L $(UPDOWN_SOURCE_CODE)/libraries/SpMalloc/SpMalloc.py \
		-o $@ $^

js_udkvmsr_exe_${mode}.bin: js_udkvmsr_exe_${mode}.py
	cd $(UPDOWN_SOURCE_CODE)/udbasim/assembler; \
	python3 efa2bin.py \
		--efa $(UPDOWN_SOURCE_CODE)/apps/js/$^ \
		--outpath $(UPDOWN_SOURCE_CODE)/install/updown/apps/ \
		--toplinker
# 	python3 ../../../udbasim/assembler/efa2bin.py \
		--efa $^ \
		--outpath $(INSTALL_DIR)/updown/apps/ \
		--toplinker # --debug-messages

all: js_udkvmsr.py js_udkvmsr_exe_${mode}.py js_udkvmsr_exe_${mode}.bin

clean:
	@rm -f js_udkvmsr.py js_udkvmsr_exe_${mode}.py js_udkvmsr_exe_${mode}.hpp
