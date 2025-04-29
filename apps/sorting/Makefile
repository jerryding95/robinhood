### The following variables are used in this Makefile:
LINKER_DIR = ../../linker/
LINKER = $(LINKER_DIR)EFAlinker.py

UDWEAVE_DIR = ../../../udweave
UDWEAVE = $(UDWEAVE_DIR)/UDweave.py
UDW_HEADER_FILES = $(wildcard *.udwh)

INSTALL_DIR = ../../../install
.DEFAULT_GOAL := all

# Default values for mode and sortmode if not provided
mode ?= default
sortmode ?= default

# Target filename with parameters
TARGET = sortingEFA_$(mode)_$(sortmode).py

phase1_kvmsr_module.py: phase1_kvmsr.py
	python3 $(LINKER) -f linkable-module -L./ -L../../libraries/UDMapShuffleReduce/linkable -L../../libraries/UDMapShuffleReduce -L../../ -L../../libraries/LMStaticMaps/ -L ../../libraries/SingleLaneSort/hybrid_single_lane.py -o $@ $^

phase1_insertion_kvmsr_module.py: phase1_insertion_kvmsr.py
	python3 $(LINKER) -f linkable-module -L./ -L../../libraries/UDMapShuffleReduce/linkable -L../../libraries/UDMapShuffleReduce -L../../ -L../../libraries/LMStaticMaps/ -L ../../libraries/SingleLaneSort/hybrid_single_lane.py -o $@ $^

phase1_insertion_lb_kvmsr_module.py: phase1_insertion_lb_kvmsr.py
	python3 $(LINKER) -f linkable-module -L./ -L../../libraries/UDMapShuffleReduce/linkable -L../../libraries/UDMapShuffleReduce -L../../ -L../../libraries/LMStaticMaps/ -L ../../libraries/SingleLaneSort/hybrid_single_lane.py -o $@ $^

phase2_kvmsr_module.py: phase2_kvmsr.py
	python3 $(LINKER) -f linkable-module -L./ -L../../libraries/UDMapShuffleReduce/linkable -L../../libraries/UDMapShuffleReduce -L../../ -L../../libraries/LMStaticMaps/  -o $@ $^

phase2_lb_kvmsr_module.py: phase2_lb_kvmsr.py
	python3 $(LINKER) -f linkable-module -L./ -L../../libraries/UDMapShuffleReduce/linkable -L../../libraries/UDMapShuffleReduce -L../../ -L../../libraries/LMStaticMaps/  -o $@ $^

phase2_mapper_kvmsr_module.py: phase2_mapper_kvmsr.py
	python3 $(LINKER) -f linkable-module -L./ -L../../libraries/UDMapShuffleReduce/linkable -L../../libraries/UDMapShuffleReduce -L../../ -L../../libraries/LMStaticMaps/  -o $@ $^

phase2_mapper_lb_kvmsr_module.py: phase2_mapper_lb_kvmsr.py
	python3 $(LINKER) -f linkable-module -L./ -L../../libraries/UDMapShuffleReduce/linkable -L../../libraries/UDMapShuffleReduce -L../../ -L../../libraries/LMStaticMaps/  -o $@ $^

phase3_kvmsr_module.py: phase3_kvmsr.py
	python3 $(LINKER) -f linkable-module -L./ -L../../libraries/UDMapShuffleReduce/linkable -L../../libraries/UDMapShuffleReduce -L../../ -L../../libraries/LMStaticMaps/  -o $@ $^


# sorting_exe.py: sorting.py \
# 			phase1_kvmsr_module.py \
# 			phase1_insertion_kvmsr_module.py \
# 			phase1_insertion_lb_kvmsr_module.py \
# 			phase2_kvmsr_module.py \
# 			phase2_mapper_kvmsr_module.py \
# 			phase2_lb_kvmsr_module.py \
# 			phase2_mapper_lb_kvmsr_module.py \
# 			phase3_kvmsr_module.py
# 	python3 $(LINKER) -L./ \
# 		-L../ \
# 		-L../../ \
# 		-L../../libraries/UDMapShuffleReduce/linkable/ \
# 		-L../../libraries/UDMapShuffleReduce/ \
# 		-L../../libraries/UDMapShuffleReduce/linkable/LinkableKVMapShuffleReduceTPL.py \
# 		-L../../libraries/UDMapShuffleReduce/linkable/LinkableKVMapShuffleCombineTPL.py \
# 		-L../../libraries/UDMapShuffleReduce/linkable/LinkableGlobalSync.py \
# 		-o ./$@ $^ \
# 		../../libraries/DistributedSort/distributed_sort.py
# 	cd ../../udbasim/assembler; \
# 	python3 efa2bin.py \
# 		--efa ../../apps/sorting/$@  \
# 		--outpath ../../install/updown/apps/ \
# 		--toplinker

$(TARGET): sorting.py \
			phase1_kvmsr_module.py \
			phase1_insertion_kvmsr_module.py \
			phase1_insertion_lb_kvmsr_module.py \
			phase2_kvmsr_module.py \
			phase2_mapper_kvmsr_module.py \
			phase2_lb_kvmsr_module.py \
			phase2_mapper_lb_kvmsr_module.py \
			phase3_kvmsr_module.py
	python3 $(LINKER) -L./ \
		-L../ \
		-L../../ \
		-L../../libraries/UDMapShuffleReduce/linkable/ \
		-L../../libraries/UDMapShuffleReduce/ \
		-L../../libraries/UDMapShuffleReduce/linkable/LinkableKVMapShuffleReduceTPL.py \
		-L../../libraries/UDMapShuffleReduce/linkable/LinkableKVMapShuffleCombineTPL.py \
		-L../../libraries/UDMapShuffleReduce/linkable/LinkableGlobalSync.py \
		-o ./$@ $^ \
		../../libraries/DistributedSort/distributed_sort.py
	cd ../../udbasim/assembler; \
	python3 efa2bin.py \
		--efa ../../apps/sorting/$@  \
		--outpath ../../install/updown/apps/ \
		--toplinker

# --outpath ../../build/apps/ \

%.py: %.udw $(UDW_HEADER_FILES) 
	$(UDWEAVE) -i $< -I ../../libraries/DistributedSort/ \
					 -I ../../libraries/LMStaticMaps/ \
					 -I ../../libraries/UDMapShuffleReduce/linkable/ \
					 -o $@

all: $(TARGET)

clean:
	@rm -f sorting.py sorting_exe.py sortingEFA_${mode}_${sortmode}.py sortingEFA_${mode}_${sortmode}.hpp phase1_kvmsr_module.py phase2_kvmsr_module.py phase2_lb_kvmsr_module.py phase3_kvmsr_module.py phase2_mapper_kvmsr_module.py phase2_mapper_lb_kvmsr_module.py phase1_insertion_kvmsr_module.py phase1_insertion_lb_kvmsr_module.py

