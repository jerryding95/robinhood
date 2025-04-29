#include <iostream>
#include <simupdown.h>

void printEvent(UpDown::event_t &ev) {
  printf("Setting the event word = %d, network_id = %d, "
         "thread_id = %d, num_operands = %d, ev_word = 0x%X\n",
         ev.get_EventLabel(), ev.get_NetworkId(), ev.get_ThreadId(),
         ev.get_NumOperands(), ev.get_EventWord());
}

int main() {
  // Default configurations runtime
  UpDown::SimUDRuntime_t *test_rt = new UpDown::SimUDRuntime_t("simpleEFA", "simpleEFA", "./");

  printf("=== Base Addresses ===\n");
  test_rt->dumpBaseAddrs();
  printf("\n=== Machine Config ===\n");
  test_rt->dumpMachineConfig();

  // Help operands
  UpDown::word_t ops_data[] = {99};
  UpDown::operands_t ops(1, ops_data);

  // Events with operands
  UpDown::networkid_t nwid(0);
  UpDown::event_t evnt_ops(0 /*Event Label*/,
                           nwid /*Network ID*/,
                           UpDown::CREATE_THREAD /*Thread ID*/,
                           &ops /*Operands*/);

  printEvent(evnt_ops);
  test_rt->send_event(evnt_ops);
  test_rt->start_exec(nwid);

  test_rt->test_wait_addr(nwid,0,100);

  delete test_rt;
  return 0;
}