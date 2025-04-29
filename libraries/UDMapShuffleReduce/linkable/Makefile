### The following variables are used in this Makefile:
LINKER_DIR = ../../../linker
LINKER = $(LINKER_DIR)/EFAlinker.py

UDWEAVE_DIR = ../../../../udweave
UDWEAVE = $(UDWEAVE_DIR)/UDweave.py

INSTALL_DIR = ../../../install
.DEFAULT_GOAL := all

LMCache: LinkableLMCache.py
	mkdir -p modules
	python3 $(LINKER) -f linkable-module -L./ -L ../ -L../../../ -o ./modules/$@ $^

Broadcast: LinkableGlobalSync.py
	mkdir -p modules
	python3 $(LINKER) -f linkable-module -L./ -L ../ -L../../../ -o ./modules/$@ $^

load_balancer_events.py: load_balancer_events.udw 
	$(UDWEAVE) -i $< -o $@
	./convert_lb_events.sh $@

load_balancer_events_inter5.py: load_balancer_events_inter5.udw
	$(UDWEAVE) -i $< -o $@
	./convert_lb_events.sh $@

all: LMCache Broadcast

clean:
	rm -f *.exe *.out *.o LMCache.py Broadcast.hpp
