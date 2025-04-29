#include <iostream>
#include <simupdown.h>

void printEvent(UpDown::event_t &ev) {
  printf("Setting the event word = %d, network_id = %d, "
         "thread_id = %d, num_operands = %d, ev_word = 0x%X\n",
         ev.get_EventLabel(), ev.get_NetworkId(), ev.get_ThreadId(),
         ev.get_NumOperands(), ev.get_EventWord());
}

int main() {
  UpDown::SimUDRuntime_t rt;

  rt.dumpMachineConfig();

  // Help operands
  UpDown::word_t ops_data[] = {1, 2, 3, 4};
  UpDown::operands_t ops(4, ops_data);

  // Events with operands
  UpDown::networkid_t nwid(0);
  UpDown::event_t evnt_ops(0 /*Event Label*/,
                           nwid /*Network ID*/,
                           0 /*Thread ID*/,
                           &ops /*Operands*/);

  printEvent(evnt_ops);
  rt.send_event(evnt_ops);
  rt.start_exec(nwid);
  // Events with operands
  UpDown::networkid_t nwid2(16);
  UpDown::event_t evnt_ops2(1 /*Event Label*/,
                           nwid2 /*Network ID*/,
                           UpDown::CREATE_THREAD /*Thread ID*/,
                           &ops /*Operands*/);
  rt.send_event(evnt_ops2);
  rt.start_exec(nwid2);

  return 0;
}