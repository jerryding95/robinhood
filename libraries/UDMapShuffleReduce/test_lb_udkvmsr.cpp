#include "simupdown.h"

#include <cstdio>
#include <cstdlib>
#include <iostream>
#include <cmath>
#include <basimupdown.h>

#ifdef GEM5_MODE
 #include <gem5/m5ops.h>
#endif

#define DEBUG

#define NUM_LANE_PER_UD 64
#define NUM_UD_PER_CLUSTER 4
#define NUM_CLUSTER_PER_NODE 8

#define PART_PARM 1

struct naiveKVpair{
  uint64_t key;
  uint64_t value;
};


UpDown::UDRuntime_t* initialize_rt(uint64_t num_nodes, uint64_t num_uds_per_node, uint64_t num_lanes_per_ud)
{
  // Set up machine parameters
  UpDown::ud_machine_t machine;
  machine.NumLanes = num_lanes_per_ud;
  machine.NumUDs = std::min((int)num_uds_per_node, NUM_UD_PER_CLUSTER);
  machine.NumStacks = std::ceil((double)num_uds_per_node / NUM_UD_PER_CLUSTER);
  machine.NumNodes = num_nodes;
  machine.LocalMemAddrMode = 1;

#ifdef GEM5_MODE
  UpDown::UDRuntime_t *rt = new UpDown::UDRuntime_t(machine);
#else
#ifdef BASIM
  UpDown::BASimUDRuntime_t* rt = new UpDown::BASimUDRuntime_t(machine, "lbTestEFA.bin", 0);
  printf("using basim\n");
#else
  UpDown::SimUDRuntime_t *rt = new UpDown::SimUDRuntime_t(machine, "lbTestEFA.py", "lbTestEFA", "./", UpDown::EmulatorLogLevel::FULL_TRACE);
#endif
#endif

#ifdef DEBUG
  printf("=== Base Addresses ===\n");
  rt->dumpBaseAddrs();
  printf("\n=== Machine Config ===\n");
  rt->dumpMachineConfig();
#endif

  return rt;
}


naiveKVpair* gen_input_kv(UpDown::UDRuntime_t* rt, uint64_t num_input_keys)
{
  naiveKVpair* inKVSet = reinterpret_cast<naiveKVpair*>(rt->mm_malloc(num_input_keys * sizeof(naiveKVpair)));

#ifdef DEBUG
  printf("-------------------\ninKVSet = %p\n", inKVSet);
#endif

  for (int i = 0; i < num_input_keys; i++) {
    inKVSet[i].key = i;
    inKVSet[i].value = 1;

#ifdef DEBUG
    printf("Input pair %d: key=%ld value=%ld DRAM_addr=%p\n", i, inKVSet[i].key, inKVSet[i].value, inKVSet + i);
#endif
  }

  return inKVSet;
}

naiveKVpair* gen_skewed_input_kv(UpDown::UDRuntime_t* rt, uint64_t num_workers, uint64_t* num_input_keys)
{
  uint64_t key_per_worker = 4;
  uint64_t num_vals_max = 1024;
  uint64_t num_vals_min = 8;
  uint64_t num_workers_got_max = 1;

  *num_input_keys = key_per_worker * ( (num_workers - num_workers_got_max) * num_vals_min + num_workers_got_max * num_vals_max );

  naiveKVpair* inKVSet = reinterpret_cast<naiveKVpair*>(rt->mm_malloc(*num_input_keys * sizeof(naiveKVpair)));

#ifdef DEBUG
  printf("-------------------\ninKVSet = %p\n", inKVSet);
#endif

  int ind = 0;

  for (int i = 0; i < key_per_worker; i++) {
    for (int j=0; j < num_workers_got_max; j++){
      for (int k=0; k<num_vals_max; k++){
        inKVSet[ind].key = i*num_workers + j;
        inKVSet[ind].value = 1;
#ifdef DEBUG
        printf("Input pair %d: key=%ld value=%ld DRAM_addr=%p\n", ind, inKVSet[ind].key, inKVSet[ind].value, inKVSet + ind);
#endif
        ind ++;
      }
    }

    for (int j=num_workers_got_max; j<num_workers; j++){
      for (int k=0; k<num_vals_min; k++){
        inKVSet[ind].key = i*num_workers + j;
        inKVSet[ind].value = 1;
#ifdef DEBUG
        printf("Input pair %d: key=%ld value=%ld DRAM_addr=%p\n", ind, inKVSet[ind].key, inKVSet[ind].value, inKVSet + ind);
#endif
        ind ++;
      }
    }


  }

  return inKVSet;
}


naiveKVpair* gen_output_kv(UpDown::UDRuntime_t* rt, uint64_t num_workers)
{
  naiveKVpair* outKVSet = reinterpret_cast<naiveKVpair*>(rt->mm_malloc(num_workers * sizeof(naiveKVpair)));

#ifdef DEBUG
  printf("-------------------\noutKVSet = %p\n", outKVSet);
#endif

  for (int i = 0; i < num_workers; i++) {
    outKVSet[i].key = i;

#ifdef DEBUG
    printf("Output pair %d: key=%ld value=%ld DRAM_addr=%p\n", i, outKVSet[i].key, outKVSet[i].value, outKVSet + i);
#endif
  }

  return outKVSet;
}


uint64_t* gen_intermediate_kv(UpDown::UDRuntime_t* rt, uint64_t num_intermediate_keys, uint64_t vsize)
{
  uint64_t* interKVSpace = reinterpret_cast<uint64_t*>(rt->mm_malloc(num_intermediate_keys * (3 * sizeof(uint64_t))));

#ifdef DEBUG
  printf("-------------------\ninterKVSet = %p\n", interKVSpace);
#endif

  for (int i = 0; i < num_intermediate_keys; i++) {
    interKVSpace[num_intermediate_keys + i*2] = 0;
    interKVSpace[num_intermediate_keys + i*2 + 1] = (uint64_t) reinterpret_cast<uint64_t*>(rt->mm_malloc(vsize * sizeof(uint64_t)));

#ifdef DEBUG
    printf("Intermediate kv entry %d: num=%ld pointer=%ld DRAM_addr=%p\n", i, interKVSpace[num_intermediate_keys + i*2], interKVSpace[num_intermediate_keys + i*2 + 1], interKVSpace + num_intermediate_keys + i*2);
#endif
  }

  return interKVSpace;
}


naiveKVpair** gen_partitions(UpDown::UDRuntime_t* rt, uint64_t num_workers, uint64_t num_input_keys, naiveKVpair* inKVSet)
{
  uint64_t num_partitions = num_workers;
  uint64_t num_pairs_per_part = num_input_keys/num_workers;

  naiveKVpair** partitions = reinterpret_cast<naiveKVpair**>(rt->mm_malloc((num_partitions + 1) * sizeof(naiveKVpair*)));

#ifdef DEBUG
  printf("-------------------\nparitions = %p\n", partitions);
#endif

  for (int i = 0; i < num_partitions + 1; i++) {
    partitions[i] = inKVSet + (i * num_pairs_per_part);

#ifdef DEBUG
    printf("Partition %d: pair_id=%ld, key=%ld value=%ld base_pair_addr=%p, part_entry_addr=%p\n",
      i, i * num_pairs_per_part, partitions[i]->key, partitions[i]->value, partitions[i], partitions + i);
#endif
  }

  partitions[num_partitions] = inKVSet + num_input_keys;

  return partitions;
}


void test_lb(UpDown::UDRuntime_t* rt, uint64_t arg0, uint64_t arg1, uint64_t arg2, uint64_t arg3, uint64_t arg4, uint64_t arg5)
{
  printf("%lu, %lu, %lu, %lu, %lu, %lu\n", arg0, arg1, arg2, arg3, arg4, arg5);
  UpDown::word_t TOP_FLAG_OFFSET = 512;

  // Init top flag to 0
  uint64_t val = 0;
  UpDown::networkid_t nwid(0, false, 0);
  rt->t2ud_memcpy(&val,
                          sizeof(uint64_t),
                          nwid,
                          TOP_FLAG_OFFSET /*Offset*/);
  printf("set flag\n");

  #ifdef GEM5_MODE
    m5_switch_cpu();
  #endif

  /* operands
    OB_0: Pointer to partitions (64-bit DRAM address)
    OB_1: Pointer to inKVSet (64-bit DRAM address)
    OB_2: Input kvset length
    OB_3: Pointer to outKVSet (64-bit DRAM address)
    OB_4: Output kvset length
  */
  UpDown::word_t ops_data[6];
  UpDown::operands_t ops(6);
  ops.set_operand(0, arg0);
  ops.set_operand(1, arg1);
  ops.set_operand(2, arg2);
  ops.set_operand(3, arg3);
  ops.set_operand(4, arg4);
  ops.set_operand(5, arg5);

  printf("ops set\n");

  UpDown::event_t evnt_ops(1,                     /*Event Label*/
                           nwid,
                           UpDown::CREATE_THREAD, /*Thread ID*/
                           &ops                   /*Operands*/);
  printf("set event word\n");
  rt->send_event(evnt_ops);
  printf("Event sent to updown lane %d.\n", 0);

#ifdef GEM5_MODE
  m5_reset_stats(0,0);
#endif

  rt->start_exec(nwid);
  printf("Waiting for terminate\n");

  // UpDown::networkid_t nwidd(8, false, 0);

  rt->test_wait_addr(nwid, TOP_FLAG_OFFSET, 1);

#ifdef GEM5_MODE
  m5_dump_reset_stats(0,0);
#endif

  printf("UpDown checking terminates.\n");

}


int main(int argc, char* argv[]) {


  uint64_t num_nodes = 1;
  uint64_t num_uds_per_node = 1;
  uint64_t num_lanes_per_ud = 64;

  uint64_t num_workers = num_nodes * num_uds_per_node * num_lanes_per_ud;
  printf("\tnum_workers = %ld\n", num_workers);

  uint64_t num_partitions = num_workers;
  // uint64_t num_pairs_per_part = 4;
  // uint64_t num_input_keys = num_partitions * num_pairs_per_part;
  // printf("num_input_keys = %ld\n", num_input_keys);
  uint64_t num_input_keys;

  UpDown::UDRuntime_t* rt = initialize_rt(num_nodes, num_uds_per_node, num_lanes_per_ud);

  // uint64_t* interKVSpace = reinterpret_cast<uint64_t*>(rt->mm_malloc(num_input_keys * (sizeof(uint64_t) + sizeof(naiveKVpair))));
  uint64_t* interKVSpace = gen_intermediate_kv(rt, num_workers*4, 4096);
  // naiveKVpair* inKVSet = gen_input_kv(rt, num_input_keys);
  naiveKVpair* inKVSet = gen_skewed_input_kv(rt, num_workers, &num_input_keys);
  naiveKVpair** partitions = gen_partitions(rt, num_workers, num_input_keys, inKVSet);
  naiveKVpair* outKVSet = gen_output_kv(rt, num_workers*4);
    
  fflush(stdout);

  printf("before test\n");
  test_lb(rt, (uint64_t) partitions, (uint64_t) inKVSet, num_input_keys, (uint64_t) outKVSet, num_workers*4, (uint64_t) interKVSpace);

  delete rt;
  printf("Test UDKVMSR program finishes.\n");

  for (int i = 0; i < num_workers*4; i++) {

#ifdef DEBUG
    printf("Output pair %d: key=%ld value=%ld DRAM_addr=%p\n", i, outKVSet[i].key, outKVSet[i].value, outKVSet + i);
#endif
  }

//   for (int i = 0; i < num_workers*4; i++) {

// #ifdef DEBUG
//     printf("Intermediate kv entry %d: num=%ld pointer=%ld DRAM_addr=%p\n", i, interKVSpace[num_workers*4 + i*2], interKVSpace[num_workers*4 + i*2 + 1], interKVSpace + num_workers*4 + i*2);
// #endif
//     uint64_t *ptr = (uint64_t*) interKVSpace[num_workers*4 + i*2 + 1];
//     for (int j=0; j<interKVSpace[num_workers*4 + i*2]; j++){
//       printf("  key %d, value %d\n", ptr[2*j], ptr[2*j + 1]);
//     }
//   }

  return 0;
}
