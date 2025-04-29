#include <iostream>
#include <updown.h>

void printEvent(UpDown::event_t &ev) {
  printf("Setting the event word = %d, lane_id = %d, "
         "thread_id = %d, num_operands = %d, ev_word = 0x%lX\n",
         ev.get_EventLabel(), (ev.get_NetworkId()).get_LaneId(),
         ev.get_ThreadId(), ev.get_NumOperands(), ev.get_EventWord());
}

int main() {

  // Create an empty event_
  UpDown::event_t empty_evnt;
  printEvent(empty_evnt);
  UpDown::event_t def_envt(10, UpDown::networkid_t(11));
  printEvent(def_envt);
  UpDown::event_t def_envt2(12, UpDown::networkid_t(13, 14));
  printEvent(def_envt2);
  UpDown::event_t def_envt3(15, UpDown::networkid_t(16, 17), 18);
  printEvent(def_envt3);

  // Help operands
  UpDown::word_t ops_data[] = {1, 2, 3, 4};
  UpDown::operands_t ops(4, ops_data);

  // Events with operands
  UpDown::event_t evnt_ops(15, UpDown::networkid_t(16, 17), 18, &ops);
  printEvent(evnt_ops);

  def_envt.set_event(1, UpDown::networkid_t(2));
  printEvent(def_envt);
  def_envt.set_event(3, UpDown::networkid_t(4, 5));
  printEvent(def_envt);
  def_envt.set_event(3, UpDown::networkid_t(4, 5), 6);
  printEvent(def_envt);
  def_envt.set_event(3, UpDown::networkid_t(4, 5), 6, &ops);
  printEvent(def_envt);
  return 0;
}