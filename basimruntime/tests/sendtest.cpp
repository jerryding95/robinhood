#include "basimupdown.h"
#include <iostream>
#ifdef GEM5_MODE
    #include "gem5/m5ops.h"
#endif
using namespace std;

int main() {
  // Set up machine parameters
  UpDown::ud_machine_t machine;
  machine.NumLanes = 64;
  machine.NumNodes = 1;
  machine.NumStacks = 1;
  machine.NumUDs = 1;

  // Default configurations runtime
#if defined GEM5_MODE
  UpDown::UDRuntime_t *rt = new UpDown::UDRuntime_t(machine);

#else
  UpDown::BASimUDRuntime_t *rt = new UpDown::BASimUDRuntime_t(machine, "sendtest.bin", 0);
#endif

  printf("=== Base Addresses ===\n");
  rt->dumpBaseAddrs();
  printf("\n=== Machine Config ===\n");
  rt->dumpMachineConfig();
#ifdef GEM5_MODE
  m5_switch_cpu();
#endif
  
  UpDown::word_t data = 1;
  UpDown::word_t mem_data;
  UpDown::word_t ops_data[2];
  UpDown::operands_t ops(2, ops_data);
  printf("Starting launch of events\n");
  ops.set_operand(0, 0);
  ops.set_operand(1, 0);
  UpDown::networkid_t nwid(0);
  UpDown::event_t evnt_ops(
        0 /*Event Label*/, nwid /*Lane ID*/,
        UpDown::CREATE_THREAD /*Thread ID*/, &ops /*Operands*/);
  rt->send_event(evnt_ops);
  rt->start_exec(nwid);
  printf("Check for termination now\n");
  rt->test_wait_addr(nwid, 0 /*Offset*/,
                      1 /*Expected value*/);
  rt->ud2t_memcpy(&data /*top_ptr*/, 8, nwid,
                8 /*offset in spmem*/);
  printf("Data Read :%d\n", data);
#if not defined GEM5_MODE
  printf("Total Sim Cycles :%ld\n", rt->getCurTick());
#endif
  printf("Test Success\n");
  delete rt;
  return 0;
}