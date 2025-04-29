### This is an example Makefile for linking and building the
### complete application.


### The following variables are used in this Makefile:
LINKER_DIR = ../../
LINKER = $(LINKER_DIR)EFAlinker.py


INSTALL_DIR = ../../../install

CXX=g++

#/usr/bin/g++  -std=c++11 -fopenmp -ggdb CMakeFiles/udshmemtest.dir/shmem/udshmemtest.cpp.o ../../apps/common/snap-core/Snap.o -o udshmemtest  libudshmem.a ../simruntime/libUpDownSimRuntimeStatic.a -lm ../runtime/libUpDownRuntimeStatic.a /usr/lib/x86_64-linux-gnu/libpython3.8.so 

CXX_FLAGS=-std=c++11 -fopenmp -ggdb  -I$(INSTALL_DIR)/updown/include -DDEBUG_MODE=1
CXX_LINK_FLAGS=-L$(INSTALL_DIR)/updown/lib  -lUpDownRuntime -lm -lUpDownSimRuntime -lpython3.8

%.exe: %.cpp
	$(CXX) $(CXX_FLAGS) -o $@ $^ $(CXX_LINK_FLAGS)


sht_test_out: sht_test.py
	$(LINKER) -L../../../libraries/ScalableHashTable/ -o $@ $^

all: sht_test_out sht_example.exe

clean:
	rm -f *.exe *.out *.o sht_test_out.py