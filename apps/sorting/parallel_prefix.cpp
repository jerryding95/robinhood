#include "simupdown.h"

#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <iostream>
#include <cmath>
#include <random>
#include <algorithm>
#include <vector>
#include <chrono>
#include <cstddef>
#include <iomanip>
#include <numeric>
typedef std::chrono::system_clock timer;

#include <sys/types.h>
#include "sorting_exe.hpp"
#include "updown_config.h"
#ifdef BASIM
#include <basimupdown.h>
#endif

#ifdef GEM5_MODE
 #include <gem5/m5ops.h>
#endif

#define DEBUG

#define USAGE "USAGE: ./testLinkableMapShuffleReduce <num_nodes> <num_ud_per_node> <num_lane_per_ud> (<num_pair_per_partition> <num_partition_per_lane>)\n\
  num_nodes: \tnumber of nodes, minimum is 1.\n\
  num_ud_per_node: \tnumber of UDs per node, default = 32 if greater than 1 node is used.\n\
  num_lane_per_ud: \tnumber of lanes per UD, default = 64 if greater than 1 updown is used.\n\
  num_pair_per_partition: number of key-value pairs per partition, default = 20.\n\
  num_partition_per_lane: number of partitions per lane, default = 1.\n"

#define NUM_LANE_PER_UD 64
#define NUM_UD_PER_CLUSTER 4
#define NUM_CLUSTER_PER_NODE 8

struct testKVpair{
  uint64_t key;
  uint64_t value;
};

std::mt19937_64 rng(0);

int main(int argc, char* argv[]) {

  if (argc < 2) {
    printf("Insufficient Input Params\n");
    printf("%s\n", USAGE);
    exit(1);
  }

  uint64_t num_nodes = atoi(argv[1]);
  uint64_t num_uds_per_node = NUM_UD_PER_CLUSTER * NUM_CLUSTER_PER_NODE;
  uint64_t num_lanes_per_ud = NUM_LANE_PER_UD;

  if (num_nodes < 2) {
    num_nodes = 1;
    num_uds_per_node = atoi(argv[2]);
    if (num_uds_per_node < 2) {
      num_uds_per_node = 1;
      num_lanes_per_ud = atoi(argv[3]);
    }  
  } 
  uint64_t num_input_keys = atoi(argv[4]);
  uint64_t pblock_size = atoi(argv[5]);
  // uint64_t bin_extra_factor = 100;
  // uint64_t num_input_keys = atoi(argv[4]);
  // uint64_t num_bins = atoi(argv[5]);
  // uint64_t num_partition_per_lane = 1;
  // uint64_t using_unique = atoi(argv[6]);
  // uint64_t max_value = atoll(argv[7]);
  uint64_t start_lane_offset = 0;
  // if(argc >= 9) {
  //   start_lane_offset = atoi(argv[8]);
  // }
  // if (argc > 4) {
  //   num_pairs_per_part = atoi(argv[4]);
  //   if (argc > 5) {
  //     num_partition_per_lane = atoi(argv[5]);
  //   }
  // }

  printf("Test configurations: \n\tnum_nodes = %ld, \n\tnum_uds_per_node = %ld, \n\tnum_lanes_per_ud = %ld, \n", num_nodes, num_uds_per_node, num_lanes_per_ud);
  assert(num_nodes * num_uds_per_node * num_lanes_per_ud > start_lane_offset);
  uint64_t num_lanes = num_nodes * num_uds_per_node * num_lanes_per_ud - start_lane_offset;
  printf("\tnum_lanes = %ld\n", num_lanes);

  // Set up machine parameters
  UpDown::ud_machine_t machine;
  machine.NumLanes = num_lanes_per_ud;
  machine.NumUDs = std::min((int)num_uds_per_node, NUM_UD_PER_CLUSTER);
  machine.NumStacks = std::ceil((double)num_uds_per_node / NUM_UD_PER_CLUSTER);
  machine.NumNodes = num_nodes;
  machine.LocalMemAddrMode = 1;

#ifdef GEM5_MODE
  UpDown::UDRuntime_t *testKVMSR_rt = new UpDown::UDRuntime_t(machine);
#elif BASIM
  UpDown::BASimUDRuntime_t* testKVMSR_rt = new UpDown::BASimUDRuntime_t(machine, "sorting_exe.bin", 0);
#else
  // Init runtime
  UpDown::SimUDRuntime_t *testKVMSR_rt = new UpDown::SimUDRuntime_t(machine, "sorting_exe", "sorting_exe", "./", UpDown::EmulatorLogLevel::FULL_TRACE);
#endif

#ifdef DEBUG
  printf("=== Base Addresses ===\n");
  testKVMSR_rt->dumpBaseAddrs();
  printf("\n=== Machine Config ===\n");
  testKVMSR_rt->dumpMachineConfig();
#endif

  // uint64_t num_partitions = num_lanes * num_partition_per_lane;
  ;
  // uint64_t max_value = 1000000;
  printf("num_input_keys = %ld\n", num_input_keys);

  // uint64_t BLOCK_SIZE = 256;
  uint64_t BLOCK_SIZE = 5;
  // Allocate the array where the top and updown can see it:
  // testKVpair* inKVSet = reinterpret_cast<testKVpair*>(testKVMSR_rt->mm_malloc(num_input_keys * sizeof(testKVpair)));
  UpDown::word_t* input_addr = reinterpret_cast<UpDown::word_t*>(testKVMSR_rt->mm_malloc(num_input_keys * 2 * sizeof(UpDown::word_t)));
  for (int i = 0; i < num_input_keys; i++) {
    input_addr[i] = rng() % 10;
  }
  std::vector<UpDown::word_t> input_keys(input_addr, input_addr + num_input_keys), inputVec(input_addr, input_addr + num_input_keys);
  uint64_t sum = 0;
  for (int i = 0; i < num_input_keys; i++) {
    uint64_t cur = inputVec[i];
    inputVec[i] = sum;
    sum += cur;
  }
  
  /* operands
      OB_0: Pointer to the partition array (64-bit DRAM address)
      OB_1: Number of partitions per lane
      OB_2: Number of lanes
      OB_3: Pointer to input kvset (64-bit DRAM address)
      OB_4: Number of elements in the input kvset (1D array)
      OB_5: Pointer to outKVMap (64-bit DRAM address)
      OB_6: Number of elements in the output kvset (1D array)
  */
  UpDown::word_t ops_data[3];
  UpDown::operands_t ops(3, ops_data);
  ops.set_operand(0, (uint64_t) input_addr);
  ops.set_operand(1, (uint64_t) num_input_keys);
  ops.set_operand(2, (uint64_t) num_lanes);
  // ops.set_operand(3, (uint64_t) num_lanes);
  // ops.set_operand(4, (uint64_t) outputTempSet);
  // ops.set_operand(5, (uint64_t) num_bins);
  // ops.set_operand(6, (uint64_t) using_unique);
  // ops.set_operand(7, (uint64_t) max_value);
  // ops.set_operand(7, (uint64_t) 0);

  printf("Prepare operands done.\n");
  
  UpDown::networkid_t nwid(start_lane_offset, false, 0);
  UpDown::word_t TOP_FLAG_OFFSET = 0;
  const auto time_start = timer::now();

  for (int iter = 0; iter < 1; iter++) {
    UpDown::event_t evnt_ops(sorting_exe::SortingTest__test_parallel_prefix /*Event Label*/,
                                nwid,
                                UpDown::CREATE_THREAD /*Thread ID*/,
                                &ops /*Operands*/);

      // Init top flag to 0
      uint64_t val = 0;
      testKVMSR_rt->t2ud_memcpy(&val,
                      sizeof(uint64_t),
                      nwid,
                      TOP_FLAG_OFFSET /*Offset*/);

      printf("Clear top flag.\n");
      testKVMSR_rt->send_event(evnt_ops);

      testKVMSR_rt->start_exec(nwid);

      testKVMSR_rt->test_wait_addr(nwid, TOP_FLAG_OFFSET, 1);


      const auto time_end = timer::now();

      auto elapsed_time = std::chrono::duration_cast<std::chrono::milliseconds>(time_end - time_start);

      std::cout << "Time to sort: " << elapsed_time.count() << " ms" << '\n';
  }
  // UpDown::event_t evnt_ops(sorting_exe::test_sort__distributed_sort /*Event Label*/,
  printf("input: ");
  for (int i = 0; i < num_input_keys; i++) {
    std::cout << input_keys[i] << " ";
  }
  std::cout << std::endl;
  printf("expected result: ");
  for (int i = 0; i < num_input_keys; i++) {
    std::cout << inputVec[i] << " ";
  }
  std::cout << std::endl;
  bool good = true;
  printf("actual result: ");
  for (int i = 0; i < num_input_keys; i++) {
    std::cout << input_addr[i] << " ";
    good &= (input_addr[i] == inputVec[i]);
  }
  std::cout << std::endl;
  
  printf("hierarchical result:\n");
  uint64_t cur_size = num_input_keys;
  uint64_t cur_offset = 0;
  while(cur_size > 1) {
    for (int i = cur_offset; i < cur_offset + cur_size; i++) {
      std::cout << input_addr[i] << " ";
    }
    std::cout << std::endl;
    cur_offset += cur_size;
    cur_size = (cur_size + pblock_size - 1) / pblock_size;
  }

  printf("Test %s\n", good ? "PASSED" : "FAILED");
   
  delete testKVMSR_rt;
  printf("Test UDKVMSR program finishes.\n");

  return 0;
}