#include <iostream>
#include <simupdown.h>

#define N 15

int main() {
  // Default configurations runtime
  UpDown::SimUDRuntime_t *test_rt = new UpDown::SimUDRuntime_t();

  printf("=== Base Addresses ===\n");
  test_rt->dumpBaseAddrs();
  printf("\n=== Machine Config ===\n");
  test_rt->dumpMachineConfig();

  uint32_t data[N];
  UpDown::networkid_t nwid1(0, 0);
  UpDown::networkid_t nwid2(16, 0);

  // Copy element to [0,0,0]
  test_rt->t2ud_memcpy(data /*ptr*/, 
                       N*sizeof(uint32_t) /*size*/, 
                       nwid1,
                       0 /*offset*/);

  // Copy element to [0,16,16]
  test_rt->t2ud_memcpy(data /*ptr*/, 
                       N*sizeof(uint32_t) /*size*/, 
                       nwid2,
                       16 /*offset*/);
  
  // Copy element from [0,0,0]
  test_rt->ud2t_memcpy(data /*ptr*/, 
                       N*sizeof(uint32_t) /*size*/, 
                       nwid1,
                       0 /*offset*/);

  // Copy element from [0,16,16]
  test_rt->ud2t_memcpy(data /*ptr*/, 
                       N*sizeof(uint32_t) /*size*/, 
                       nwid2,
                       16 /*offset*/);

  for (int i = 0; i < N; i++)
    data[i] = i;

  // Copy element to [0,16,16]
  test_rt->t2ud_memcpy(data /*ptr*/,
                       N*sizeof(UpDown::word_t) /*size*/,
                       nwid2,
                       16 /*offset*/);

  // Testing 
  for (int i = 0; i < N; i++){
    test_rt->test_addr(nwid2,16+i*sizeof(UpDown::word_t),i);
  }
  // Testing. This should never be blocking 
  // because we don't have UD side in this test
  // Just memory copy
  for (int i = 0; i < N; i++)
    test_rt->test_wait_addr(nwid2,16+i*sizeof(UpDown::word_t),i);

  delete test_rt;

  return 0;
}