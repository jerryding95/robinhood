#include "simupdown.h"

#define N 100
#define CHUNK 10

struct myStruct {
  int a;
  int b;
  int c;
  int d;
};

int main() {
  // Set up machine parameters
  UpDown::ud_machine_t machine;
  machine.NumLanes = 64;

  // Default configurations runtime
  UpDown::SimUDRuntime_t *test_rt = new UpDown::SimUDRuntime_t(machine, "gatherEFA", "structArray", "./", UpDown::EmulatorLogLevel::FULL_TRACE);

  printf("=== Base Addresses ===\n");
  test_rt->dumpBaseAddrs();
  printf("\n=== Machine Config ===\n");
  test_rt->dumpMachineConfig();

  // Allocate the array where the top and updown can see it:
  myStruct* str = reinterpret_cast<myStruct*>(test_rt->mm_malloc(N*sizeof(myStruct)));

  // Populate the array of structs
  for (int i = 0; i < N; i++)
    str[i].c = i+1;

  // Initialize Scratchpad memory
  // The first location of each lane will be used to check completion of code
  for (int i = 0; i < N/CHUNK; i++) {
    UpDown::word_t value = 0;
    UpDown::networkid_t nwid((uint8_t)i, 0);
    test_rt->t2ud_memcpy(&value /*Pointer to top data*/, 
                         sizeof(UpDown::word_t) /*Size in bytes*/,
                         nwid,
                         0 /*Offset*/);
  }

  // operands
  // 0 and 1: Pointer to DRAM (operands are 32 bits, pointers are 64 bits)
  // 2: Initial Offset to memory
  // 3: Distance between elements
  // 4: Number of elements to fetch
  UpDown::word_t ops_data[5];
  UpDown::operands_t ops(5, ops_data);
  ops.set_operands(0,2,&str);
  ops.set_operand(3, sizeof(myStruct)); // Assume N divisible by CHUNK
  ops.set_operand(4, CHUNK);

  for (int i = 0; i < N/CHUNK; i++) {
    // We will fetch c, which is offset by a, and b. Pointer arithmetic may be better here
    ops.set_operand(2, sizeof(myStruct)*i*CHUNK + sizeof(int)*2);
    // Events with operands
    UpDown::networkid_t nwid(i);

    UpDown::event_t evnt_ops(0 /*Event Label*/,
                             nwid /*Lane ID*/,
                             UpDown::CREATE_THREAD /*Thread ID*/,
                             &ops /*Operands*/);
    test_rt->send_event(evnt_ops);
    test_rt->start_exec(nwid);
  }

  for (int i = 0; i < N/CHUNK; i++) {
    UpDown::networkid_t nwid(i);
    test_rt->test_wait_addr(nwid,0,1);
    for (int j = 0; j < CHUNK; j++) {
      int val;
      UpDown::networkid_t nwid((uint8_t)i, 0);
      // Skip the first element since it is our termination signal
      // Access the other elements one by one
      uint32_t offset = sizeof(UpDown::word_t) + j*sizeof(int);
      test_rt->ud2t_memcpy(&val, sizeof(int), nwid, offset);
      printf("str[%d].c = %d\n", i*CHUNK + j, val);
    }
  }

  delete test_rt;

  return 0;
}