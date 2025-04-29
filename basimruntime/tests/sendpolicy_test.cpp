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
  machine.LocalMemAddrMode = 1;

  // Default configurations runtime
#if defined GEM5_MODE
  UpDown::UDRuntime_t *rt = new UpDown::UDRuntime_t(machine);

#else
  UpDown::BASimUDRuntime_t *rt = new UpDown::BASimUDRuntime_t(machine, "sendpolicy_test.bin", 0);
#endif

  printf("=== Base Addresses ===\n");
  rt->dumpBaseAddrs();
  printf("\n=== Machine Config ===\n");
  rt->dumpMachineConfig();
#ifdef GEM5_MODE
  m5_switch_cpu();
#endif
  
  UpDown::word_t flag = 0;
  UpDown::word_t mem_data;
  UpDown::word_t ops_data[2];
  UpDown::operands_t ops(2, ops_data);
  printf("Starting Policy 1 testing\n");
  ops.set_operand(0, 20);
  ops.set_operand(1, 1);
  UpDown::networkid_t nwid(0);
  UpDown::event_t evnt_ops(
        0 /*Event Label*/, nwid /*Lane ID*/,
        UpDown::CREATE_THREAD /*Thread ID*/, &ops /*Operands*/);
  rt->send_event(evnt_ops);
  rt->start_exec(nwid);
  rt->t2ud_memcpy(&flag /*top_ptr*/, 8 /*size in words*/, nwid,
                0/*offset in spmem*/);
  printf("Check for termination now\n");
  rt->test_wait_addr(nwid, 0 /*Offset*/,
                      1 /*Expected value*/);

  printf("Starting Policy 2 testing\n");
  ops.set_operand(0, 20);
  ops.set_operand(1, 2);
  UpDown::event_t evnt_ops1(
        0 /*Event Label*/, nwid /*Lane ID*/,
        UpDown::CREATE_THREAD /*Thread ID*/, &ops /*Operands*/);
  rt->t2ud_memcpy(&flag /*top_ptr*/, 8 /*size in words*/, nwid,
                0/*offset in spmem*/);
  printf("Check for termination now\n");
  rt->send_event(evnt_ops1);
  rt->start_exec(nwid);
  printf("Check for termination now\n");
  rt->test_wait_addr(nwid, 0 /*Offset*/,
                      1 /*Expected value*/);
  
  printf("Starting Policy 3 testing\n");
  ops.set_operand(0, 20);
  ops.set_operand(1, 3);
  UpDown::event_t evnt_ops2(
        0 /*Event Label*/, nwid /*Lane ID*/,
        UpDown::CREATE_THREAD /*Thread ID*/, &ops /*Operands*/);
  rt->t2ud_memcpy(&flag /*top_ptr*/, 8 /*size in words*/, nwid,
                0/*offset in spmem*/);
  printf("Check for termination now\n");
  rt->send_event(evnt_ops2);
  rt->start_exec(nwid);
  rt->test_wait_addr(nwid, 0 /*Offset*/,
                      1 /*Expected value*/);
  
  printf("Starting Policy 4 testing\n");
  ops.set_operand(0, 20);
  ops.set_operand(1, 4);
  UpDown::event_t evnt_ops3(
        0 /*Event Label*/, nwid /*Lane ID*/,
        UpDown::CREATE_THREAD /*Thread ID*/, &ops /*Operands*/);
  rt->t2ud_memcpy(&flag /*top_ptr*/, 8/*size in words*/, nwid,
                0/*offset in spmem*/);
  printf("Check for termination now\n");
  rt->send_event(evnt_ops3);
  rt->start_exec(nwid);
  rt->test_wait_addr(nwid, 0 /*Offset*/,
                      1 /*Expected value*/);

  printf("Starting Policy 5 testing\n");
  ops.set_operand(0, 20);
  ops.set_operand(1, 5);
  UpDown::event_t evnt_ops4(
        0 /*Event Label*/, nwid /*Lane ID*/,
        UpDown::CREATE_THREAD /*Thread ID*/, &ops /*Operands*/);
  rt->t2ud_memcpy(&flag /*top_ptr*/, 8 /*size in words*/, nwid,
                0/*offset in spmem*/);
  rt->send_event(evnt_ops4);
  rt->start_exec(nwid);
  printf("Check for termination now\n");
  rt->test_wait_addr(nwid, 0 /*Offset*/,
                      1 /*Expected value*/);

  printf("Starting Policy 6 testing\n");
  ops.set_operand(0, 20);
  ops.set_operand(1, 6);
  UpDown::event_t evnt_ops5(
        0 /*Event Label*/, nwid /*Lane ID*/,
        UpDown::CREATE_THREAD /*Thread ID*/, &ops /*Operands*/);
  rt->t2ud_memcpy(&flag /*top_ptr*/, 8 /*size in words*/, nwid,
                0/*offset in spmem*/);
  rt->send_event(evnt_ops5);
  rt->start_exec(nwid);
  printf("Check for termination now\n");
  rt->test_wait_addr(nwid, 0 /*Offset*/,
                      1 /*Expected value*/);

  printf("Starting Policy 7 testing\n");
  ops.set_operand(0, 20);
  ops.set_operand(1, 7);
  UpDown::event_t evnt_ops6(
        0 /*Event Label*/, nwid /*Lane ID*/,
        UpDown::CREATE_THREAD /*Thread ID*/, &ops /*Operands*/);
  rt->t2ud_memcpy(&flag /*top_ptr*/, 8 /*size in words*/, nwid,
                0/*offset in spmem*/);
  rt->send_event(evnt_ops6);
  rt->start_exec(nwid);
  printf("Check for termination now\n");
  rt->test_wait_addr(nwid, 0 /*Offset*/,
                      1 /*Expected value*/);

#if not defined GEM5_MODE
  printf("Total Sim Cycles :%ld\n", rt->getCurTick());
#endif
  printf("Test Success\n");
  delete rt;
  return 0;
}