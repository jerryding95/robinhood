#include <iostream>
#include <simupdown.h>

#define N 15

int main() {
  // Default configurations runtime
  UpDown::SimUDRuntime_t *test_rt = new UpDown::SimUDRuntime_t("memcpyEFA", "memcpyEFA", "./");

  printf("=== Base Addresses ===\n");
  test_rt->dumpBaseAddrs();
  printf("\n=== Machine Config ===\n");
  test_rt->dumpMachineConfig();

  long * mmArray = reinterpret_cast<long*>(test_rt->mm_malloc(sizeof(long)*N));
  long * mmArray2 = reinterpret_cast<long*>(test_rt->mm_malloc(sizeof(long)*N));

  for (int i = 0; i < N; i++)
    mmArray[i] = i;

  // 1 element at a time
  UpDown::word_t ops[5];
  uint64_t *ptr = reinterpret_cast<uint64_t*>(ops);
  *ptr = reinterpret_cast<uint64_t>(mmArray);
  ptr ++ ;
  *ptr = reinterpret_cast<uint64_t>(mmArray2);
  ops[4] = N*sizeof(long);

  UpDown::operands_t op(5, ops);

  UpDown::networkid_t nwid(0);
  UpDown::event_t ev(0,nwid,UpDown::CREATE_THREAD, &op);

  test_rt->send_event(ev);

  test_rt->start_exec(nwid);

  test_rt->test_wait_addr(nwid,0,1);

  for (int i = 0; i < N; i++)
    printf("AnArray2[%d] = %d\n", i, mmArray2[i]);

  delete test_rt;
  return 0;
}