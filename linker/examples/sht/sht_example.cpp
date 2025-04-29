#include <algorithm>
#include <cmath>
#include <cstdio>
#include <cstdlib>
#include <iostream>
#include <map>
#include <pthread.h>
#include "simupdown.h"
#include <vector>
#include <unistd.h>
#include <getopt.h>

#ifdef GEM5_MODE
#include <gem5/m5ops.h>
#endif

#include "sht_test_out.hpp"

using namespace std;

void sht_example(int num_lanes, int num_buckets_per_lane)
{
  UpDown::ud_machine_t machine;
  machine.LocalMemAddrMode = 1;
  machine.NumLanes = num_lanes > 64 ? 64 : num_lanes;
  machine.NumUDs = std::ceil(num_lanes / 64.0) > 4 ? 4 : std::ceil(num_lanes / 64.0);
  machine.NumStacks = std::ceil(num_lanes / (64.0 * 4)) > 8 ? 8 : std::ceil(num_lanes / (64.0 * 4));
  machine.NumNodes = std::ceil(num_lanes / (64.0 * 4 * 8));

#ifdef GEM5_MODE
  auto *rt = new UpDown::UDRuntime_t();
#else
  auto *rt = new UpDown::SimUDRuntime_t(machine, "sht_test_out", "main", "./", UpDown::EmulatorLogLevel::FULL_TRACE);
  // auto *rt = new UpDown::SimUDRuntime_t(machine, "sht_test", "SHTExampleEFA", "./", UpDown::EmulatorLogLevel::FULL_TRACE);
#endif

  UpDown::word_t lm_start_off = 8;
  UpDown::word_t sht_desc_size = 40;
  UpDown::word_t bucket_desc_lm_start_off = lm_start_off + sht_desc_size + 64;
  UpDown::word_t entry_size = 16;
  UpDown::word_t alloc_entries_per_bucket = 64;

  UpDown::networkid_t nwid(0, false, 0);

  UpDown::word_t flag = 0;
  rt->t2ud_memcpy(&flag, 8, nwid, 0); // set signal flag to 0

  uint32_t size = num_lanes * num_buckets_per_lane * entry_size * alloc_entries_per_bucket;
  void *dram_alloc = rt->mm_malloc(size);

  UpDown::operands_t ops(8);
  ops.set_operand(0, lm_start_off);                 // sht desc lm addr
  ops.set_operand(1, lm_start_off + sht_desc_size); // LM buf addr
  ops.set_operand(2, 0);                            // X10 - START_NWID
  ops.set_operand(3, num_lanes);                    // X11 - NUM_ALLOC_LANES
  ops.set_operand(4, bucket_desc_lm_start_off);     // X12 - BUCKET_DESC_LM_OFFSET
  ops.set_operand(5, (UpDown::word_t)dram_alloc);   // X13 - DRAM_ALLOC_ADDR
  ops.set_operand(6, num_buckets_per_lane);         // X14 - BUCKETS_PER_LANE
  ops.set_operand(7, alloc_entries_per_bucket);     // X15 - ENTRIES_PER_BUCKET

  UpDown::event_t evnt_ops(
      sht_test_out::entry_init, /*Event Label*/
      nwid,                     /* Network ID*/
      UpDown::CREATE_THREAD,    /*Thread ID*/
      &ops                      /*Operands*/
  );

#ifdef GEM5_MODE
  m5_dump_reset_stats(0, 0);
  m5_perf_log_write(0, 0, 0, "TOP START");
#endif

  rt->send_event(evnt_ops);
  rt->start_exec(nwid);
  rt->test_wait_addr(nwid, 0, 1);

#ifdef GEM5_MODE
  m5_perf_log_write(0, 0, 0, "TOP DONE");
  m5_dump_reset_stats(0, 0);
#endif

  rt->mm_free(dram_alloc);
  delete rt;
  return;
}

int main(int argc, char *argv[])
{
  int num_lanes = atoi(argv[1]);
  int num_buckets_per_lane = atoi(argv[2]);

#ifdef GEM5_MODE
  m5_switch_cpu();
#endif
  sht_example(num_lanes, num_buckets_per_lane);

  printf("TOP DONE.\n");
}
