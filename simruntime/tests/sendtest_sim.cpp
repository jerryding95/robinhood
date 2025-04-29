#include "simupdown.h"
#include <iostream>
using namespace std;

int main() {
  // Set up machine parameters
  UpDown::ud_machine_t machine;
  machine.NumLanes = 4;
  machine.NumNodes = 1;
  machine.NumStacks = 1;
  machine.NumUDs = 1;

  // Default configurations runtime
  UpDown::SimUDRuntime_t *rt = new UpDown::SimUDRuntime_t(machine, "sendtest", "sendtest", "./", UpDown::EmulatorLogLevel::NONE);

  printf("=== Base Addresses ===\n");
  rt->dumpBaseAddrs();
  printf("\n=== Machine Config ===\n");
  rt->dumpMachineConfig();
  
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
  rt->ud2t_memcpy(&data /*top_ptr*/, 1 /*size in words*/, nwid,
                8 /*offset in spmem*/);
  printf("Data Read :%d\n", data);

  printf("Test Success\n");
  delete rt;
  return 0;
}