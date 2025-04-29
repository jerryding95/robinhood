#include "simupdown.h"
#include "updown.h"
#include "basimupdown.h"
#include "spmalloc_test_exe.hpp"
#ifdef GEM5_MODE
#include <gem5/m5ops.h>
#endif

int main(int argc, char *argv[]){

	printf("\nSpMalloc Test Started.\n\n");
	int num_lanes = 1;
	UpDown::ud_machine_t machine;
	machine.NumLanes = num_lanes > 64 ? 64 : num_lanes;
	machine.NumUDs = std::ceil(num_lanes / 64.0) > 4 ? 4 : std::ceil(num_lanes / 64.0);
	machine.NumStacks = std::ceil(num_lanes / (64.0 * 4)) > 8 ? 8 : std::ceil(num_lanes / (64.0 * 4));
	machine.NumNodes = std::ceil(num_lanes / (64.0 * 4 * 8));
	machine.LocalMemAddrMode = 1;
	printf("\n Checkpoint 0.\n\n");

#ifdef GEM5_MODE
	UpDown::UDRuntime_t *rt = new UpDown::UDRuntime_t(machine);
#elif BASIM && FASTSIM
	UpDown::BASimUDRuntime_t *rt = new UpDown::BASimUDRuntime_t(machine,
        "spmalloc_test_exe.bin",
        0);
#else 
	UpDown::SimUDRuntime_t *rt = new UpDown::SimUDRuntime_t(machine,
		"testSpMallocEFA",
		"testSpMallocEFA", 
		"./", 
		UpDown::EmulatorLogLevel::FULL_TRACE);
#endif
printf("\n Checkpoint 1.\n\n");

#ifdef GEM5_MODE
	m5_switch_cpu();
#endif

	UpDown::word_t ops_data[2], size;
	size = 512;
	UpDown::operands_t ops(3, ops_data);
	ops.set_operand(0, size);
	ops.set_operand(1, 0);

	UpDown::networkid_t nwid(0);
	UpDown::event_t evnt_ops = UpDown::event_t(spmalloc_test_exe::start_event,nwid,UpDown::CREATE_THREAD,&ops);
	rt->send_event(evnt_ops);
	rt->start_exec(nwid);

	rt->test_wait_addr(nwid,0,100);
printf("\n Checkpoint 2.\n\n");
	
	return 0;
}