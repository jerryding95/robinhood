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
#include "sortingEFA_nlb_map.hpp"
#include "sortingEFA_ws_map.hpp"
#include "sortingEFA_rh_nlbstrm_off_map.hpp"
#include "sortingEFA_rh_nlbstrm_on_map.hpp"
#include "sortingEFA_rh_random_map.hpp"
#include "sortingEFA_nlb_reduce.hpp"
#include "sortingEFA_ws_reduce.hpp"
#include "sortingEFA_rh_nlbstrm_off_reduce.hpp"
#include "sortingEFA_rh_nlbstrm_on_reduce.hpp"
#include "sortingEFA_rh_random_reduce.hpp"
#include "sortingEFA_nlb_insertion.hpp"
#include "sortingEFA_ws_insertion.hpp"
#include "sortingEFA_rh_nlbstrm_off_insertion.hpp"
#include "sortingEFA_rh_nlbstrm_on_insertion.hpp"
#include "sortingEFA_rh_random_insertion.hpp"

#include "updown_config.h"
#ifdef BASIM
#include <basimupdown.h>
#endif

#ifdef GEM5_MODE
 #include <gem5/m5ops.h>
#endif

// #define DEBUG

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



uint64_t* gen_intermediate_kv(UpDown::UDRuntime_t* rt, int num_lanes, int num_bin_per_lane, int bin_size){
#ifdef GEM5_MODE
    uint64_t* interPtrArr = reinterpret_cast<uint64_t*>(rt->mm_malloc_global(num_lanes * sizeof(uint64_t)));
    uint64_t* interLanePtrArr = reinterpret_cast<uint64_t*>(rt->mm_malloc_global(num_bin_per_lane * num_lanes * sizeof(uint64_t)));
    uint64_t* p_inter = reinterpret_cast<uint64_t*>(rt->mm_malloc_global(num_bin_per_lane * num_lanes * (bin_size * sizeof(uint64_t))));
#else
    uint64_t* interPtrArr = reinterpret_cast<uint64_t*>(rt->mm_malloc(num_lanes * sizeof(uint64_t)));
    uint64_t* interLanePtrArr = reinterpret_cast<uint64_t*>(rt->mm_malloc(num_bin_per_lane * num_lanes * sizeof(uint64_t)));
    uint64_t* p_inter = reinterpret_cast<uint64_t*>(rt->mm_malloc(num_bin_per_lane * num_lanes * (bin_size * sizeof(uint64_t))));
    // printf("p_inter range: %p to %p\n", p_inter, p_inter + num_bin_per_lane * num_lanes * bin_size);
#endif
// #ifdef DEBUG
//     printf("-------------------\ninterPtrArr = %p\n", *interPtrArr);
// #endif
    for (int i=0; i<num_lanes; i++){
        int lanePtrStart = i*num_bin_per_lane;
        int laneBinStart = i*num_bin_per_lane*bin_size;
        interPtrArr[i] = (uint64_t) (interLanePtrArr + lanePtrStart);
// #ifdef DEBUG
//         printf("Intermediate Hashtable %d: array start=%p, bin start=%p DRAM_addr=%p\n", 
//             i, interLanePtrArr + i*num_bin_per_lane, p_inter + i*num_bin_per_lane*num_bin_per_lane, interPtrArr + i);
// #endif
        for (int j=0; j<num_bin_per_lane; j++){
            interLanePtrArr[lanePtrStart + j] = (uint64_t) (p_inter + laneBinStart + j*bin_size);
// #ifdef DEBUG
//             printf("    interLanePtrArr %d, points to %lx, DRAM address %p\n", j, interLanePtrArr[lanePtrStart + j], interLanePtrArr + lanePtrStart + j);
// #endif
        }
    }
    return interPtrArr;
}


uint64_t* gen_intermediate_kv_do_all(UpDown::UDRuntime_t* rt, int num_uds, int arr_size, int entry_size){

    int ud_arr_size = arr_size * entry_size;
#ifdef GEM5_MODE
    uint64_t* interPtrArr = reinterpret_cast<uint64_t*>(rt->mm_malloc_global(num_uds * sizeof(uint64_t)));
    uint64_t* interUdPtrArr = reinterpret_cast<uint64_t*>(rt->mm_malloc_global(num_uds * ud_arr_size * sizeof(uint64_t)));
#else
    uint64_t* interPtrArr = reinterpret_cast<uint64_t*>(rt->mm_malloc(num_uds * sizeof(uint64_t)));
    uint64_t* interUdPtrArr = reinterpret_cast<uint64_t*>(rt->mm_malloc(num_uds * ud_arr_size * sizeof(uint64_t)));
#endif

#ifdef DEBUG
    printf("-------------------\ninterPtrArr = %p\n", *interPtrArr);
#endif


    for (int i=0; i<num_uds; i++){
        interPtrArr[i] = (uint64_t) (interUdPtrArr + i * ud_arr_size);
// #ifdef DEBUG
        printf("interPtrArr %d, addr %lu, points to %lu\n", i, interPtrArr+i, interPtrArr[i]);
// #endif
    }

    return interPtrArr;
}


uint64_t* gen_intermediate_kv_do_all_lane(UpDown::UDRuntime_t* rt, int num_uds, int arr_size, int entry_size){

    int lane_arr_size = (arr_size >> 6) * entry_size;
    int num_lanes = num_uds * 64;
    printf("%d,%d\n", lane_arr_size, num_lanes);
#ifdef GEM5_MODE
    uint64_t* interPtrArr = reinterpret_cast<uint64_t*>(rt->mm_malloc_global(num_lanes * sizeof(uint64_t)));
    uint64_t* interLanePtrArr = reinterpret_cast<uint64_t*>(rt->mm_malloc_global(num_lanes * lane_arr_size * sizeof(uint64_t)));
#else
    uint64_t* interPtrArr = reinterpret_cast<uint64_t*>(rt->mm_malloc(num_lanes * sizeof(uint64_t)));
    uint64_t* interLanePtrArr = reinterpret_cast<uint64_t*>(rt->mm_malloc(num_lanes * lane_arr_size * sizeof(uint64_t)));
#endif

#ifdef DEBUG
    printf("-------------------\ninterPtrArr = %p\n", *interPtrArr);
#endif


    for (int i=0; i<num_lanes; i++){
        interPtrArr[i] = (uint64_t) (interLanePtrArr + i * lane_arr_size);
// #ifdef DEBUG
        printf("interPtrArr %d, addr %lu, points to %lu\n", i, interPtrArr+i, interPtrArr[i]);
// #endif
    }

    return interPtrArr;
}

uint64_t* gen_intermediate_kv_ud(UpDown::UDRuntime_t* rt, int num_uds, int num_bin_per_ud, int bin_size){
#ifdef GEM5_MODE
    uint64_t* interPtrArr = reinterpret_cast<uint64_t*>(rt->mm_malloc_global(num_uds * sizeof(uint64_t)));
    uint64_t* interUdPtrArr = reinterpret_cast<uint64_t*>(rt->mm_malloc_global(num_bin_per_ud * num_uds * sizeof(uint64_t)));
    uint64_t* p_inter = reinterpret_cast<uint64_t*>(rt->mm_malloc_global(num_bin_per_ud * num_uds * (bin_size * sizeof(uint64_t))));
#else
    uint64_t* interPtrArr = reinterpret_cast<uint64_t*>(rt->mm_malloc(num_uds * sizeof(uint64_t)));
    uint64_t* interUdPtrArr = reinterpret_cast<uint64_t*>(rt->mm_malloc(num_bin_per_ud * num_uds * sizeof(uint64_t)));
    uint64_t* p_inter = reinterpret_cast<uint64_t*>(rt->mm_malloc(num_bin_per_ud * num_uds * (bin_size * sizeof(uint64_t))));
#endif

#ifdef DEBUG
    printf("-------------------\ninterPtrArr = %p\n", *interPtrArr);
#endif

    for (int i=0; i<num_uds; i++){
        int udPtrStart = i*num_bin_per_ud;
        int udBinStart = i*num_bin_per_ud*bin_size;
        interPtrArr[i] = (uint64_t) (interUdPtrArr + udPtrStart);
#ifdef DEBUG
        printf("Intermediate Hashtable %d: array start=%p, bin start=%p DRAM_addr=%p\n", 
            i, interUdPtrArr + i*num_bin_per_ud, p_inter + i*num_bin_per_ud*bin_size, interPtrArr + i);
#endif
        for (int j=0; j<num_bin_per_ud; j++){
            interUdPtrArr[udPtrStart + j] = (uint64_t) (p_inter + udBinStart + j*bin_size);
#ifdef DEBUG
            printf("    interUdPtrArr %d, points to %lx, DRAM address %p\n", j, interUdPtrArr[udPtrStart + j], interUdPtrArr + udPtrStart + j);
#endif
        }

    }

    return interPtrArr;
}

int main(int argc, char* argv[]) {

  if (argc < 2) {
    printf("Insufficient Input Params\n");
    printf("%s\n", USAGE);
    exit(1);
  }
  std::string mode = argv[1];

  uint64_t num_nodes = atoi(argv[2]);

  std::string sortmode = argv[3];
  uint64_t num_uds_per_node = NUM_UD_PER_CLUSTER * NUM_CLUSTER_PER_NODE;
  uint64_t num_lanes_per_ud = NUM_LANE_PER_UD;

  uint64_t updown_count = num_nodes * num_uds_per_node;

  // if (num_nodes < 2) {
  //   num_nodes = 1;
  //   num_uds_per_node = atoi(argv[2]);
  //   if (num_uds_per_node < 2) {
  //     num_uds_per_node = 1;
  //     num_lanes_per_ud = atoi(argv[3]);
  //   }  
  // } 
  std::unordered_map<std::string, int> event_labels = {
    {"nlb_map", sortingEFA_nlb_map::SortingTest__test},
    {"ws_map", sortingEFA_ws_map::SortingTest__test},
    {"rh_nlbstrm_off_map", sortingEFA_rh_nlbstrm_off_map::SortingTest__test},
    {"rh_nlbstrm_on_map", sortingEFA_rh_nlbstrm_on_map::SortingTest__test},
    {"rh_random_map", sortingEFA_rh_random_map::SortingTest__test},
    {"nlb_reduce", sortingEFA_nlb_reduce::SortingTest__test},
    {"ws_reduce", sortingEFA_ws_reduce::SortingTest__test},
    {"rh_nlbstrm_off_reduce", sortingEFA_rh_nlbstrm_off_reduce::SortingTest__test},
    {"rh_nlbstrm_on_reduce", sortingEFA_rh_nlbstrm_on_reduce::SortingTest__test},
    {"rh_random_reduce", sortingEFA_rh_random_reduce::SortingTest__test},
    {"nlb_insertion", sortingEFA_nlb_insertion::SortingTest__test},
    {"ws_insertion", sortingEFA_ws_insertion::SortingTest__test},
    {"rh_nlbstrm_off_insertion", sortingEFA_rh_nlbstrm_off_insertion::SortingTest__test},
    {"rh_nlbstrm_on_insertion", sortingEFA_rh_nlbstrm_on_insertion::SortingTest__test},
    {"rh_random_insertion", sortingEFA_rh_random_insertion::SortingTest__test}
  };
  assert(event_labels.find(mode + "_" + sortmode) != event_labels.end());
  std::cout << "Executing mode: " << mode << std::endl;
  std::cout << "Sort mode: " << sortmode << std::endl;
  std::cout << "Label: " << event_labels[mode + "_" + sortmode] << std::endl;
  
  uint64_t bin_extra_factor = 10;
  uint64_t num_input_keys = atoi(argv[4]);
  uint64_t num_bins = atoi(argv[5]);
  uint64_t num_partition_per_lane = 1;
  // uint64_t using_lb = atoi(argv[6]);
  // 0 is reducer/normal, 
  // uint64_t sorting_version = atoi(argv[6]);
  
  uint64_t max_value = atoll(argv[6]);
  // uint64_t add_size = atoi(argv[8]);
  uint64_t sigma_divider = atoi(argv[7]);
  uint64_t start_lane_offset = 0;
  assert(num_input_keys % num_bins == 0);
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
  // machine.MapMemSize = (1UL << 37) + (1UL << 36); // 128GB
  machine.MapMemSize = (1UL << 37); // 128GB
  // machine.MapMemSize = (1UL << 36); // 128GB
  machine.NumLanes = num_lanes_per_ud;
  machine.NumUDs = std::min((int)num_uds_per_node, NUM_UD_PER_CLUSTER);
  machine.NumStacks = std::ceil((double)num_uds_per_node / NUM_UD_PER_CLUSTER);
  machine.NumNodes = num_nodes;
  machine.LocalMemAddrMode = 1;

#ifdef GEM5_MODE
  UpDown::UDRuntime_t *testKVMSR_rt = new UpDown::UDRuntime_t(machine);
#elif BASIM
  printf("Using BASim\n");
  std::string logFolder = "sorting_exe.bin_";
  logFolder += std::to_string(sigma_divider);
  logFolder +=  ".logs";

  // UpDown::BASimUDRuntime_t* testKVMSR_rt = new UpDown::BASimUDRuntime_t(machine, "sorting_exe.bin", 0, logFolder);
  UpDown::BASimUDRuntime_t* testKVMSR_rt = new UpDown::BASimUDRuntime_t(machine, "sortingEFA_" + mode + "_" + sortmode + ".bin", 0, 1);
  // testKVMSR_rt->initLogs(std::filesystem::path(programFile + ".logs").filename());

  printf("here-2\n");
  fflush(stdout);

#else
  // Init runtime
  UpDown::SimUDRuntime_t *testKVMSR_rt = new UpDown::SimUDRuntime_t(machine, "sortingEFA", "sortingEFA", "./", UpDown::EmulatorLogLevel::FULL_TRACE);
#endif
  uint64_t* lb_tmp_addr = 0;
  printf("here-1\n");
  fflush(stdout);

  if (sortmode == "reduce")  {
    if (mode == "ws") {
      lb_tmp_addr = gen_intermediate_kv_do_all_lane(testKVMSR_rt, updown_count, 1<<20, 3);
    }
    else {
      lb_tmp_addr = gen_intermediate_kv_do_all(testKVMSR_rt, updown_count, 1<<20, 3);
    }
  } else {
    if (mode == "ws") {
      lb_tmp_addr = gen_intermediate_kv(testKVMSR_rt, num_lanes, 64, 2048 * 3);
    }
    else {
      lb_tmp_addr = gen_intermediate_kv_ud(testKVMSR_rt, updown_count, 64 * 64, 2048 * 3);
    }
  }
  // if(using_lb) {

  //   // if reduce bin sort
  //   // work_stealing 
  //   // lb_tmp_addr = gen_intermediate_kv_do_all_lane(testKVMSR_rt, updown_count, 1<<20, 3);

  //   // not work_stealing
  //   // lb_tmp_addr = gen_intermediate_kv_do_all(testKVMSR_rt, updown_count, 1<<20, 3);



  //   // if map bin sort or insertion sort
  //   // work stealing
  //   // lb_tmp_addr = gen_intermediate_kv(testKVMSR_rt, num_lanes, 16, 2048 * 3);
  //   // lb_tmp_addr = gen_intermediate_kv(testKVMSR_rt, num_lanes, 64, 2048 * 3);

  //   // not work_stealing
  //   // lb_tmp_addr = gen_intermediate_kv_ud(testKVMSR_rt, updown_count, 64 * 16, 2048 * 3);
  //   // lb_tmp_addr = gen_intermediate_kv_ud(testKVMSR_rt, updown_count, 64 * 64, 2048 * 3);




  //   // printf("using lb, addr = %lu", lb_tmp_addr);
  // }

#ifdef DEBUG
  printf("=== Base Addresses ===\n");
  testKVMSR_rt->dumpBaseAddrs();
  printf("\n=== Machine Config ===\n");
  testKVMSR_rt->dumpMachineConfig();
#endif

  

  // assert(num_bins % 4 == 0);
  // std::vector<UpDown::word_t> bin_sizes(num_bins);

  // if(add_size < num_input_keys / num_bins) {
  //   for (int i = 0; i < num_bins; i++) {
  //     int d = std::min(abs(i - (int)num_bins / 2), abs((int)num_bins / 2 - 1 - i));
  //     bin_sizes[i] = std::max(0LL, (long long)num_input_keys / (long long)num_bins + (long long)add_size - (long long)add_size * 4 * d / (long long)num_bins); 
  //   }
  // } else {
  //   for (int i = 0; i < num_bins; i++) {
  //     int d = std::min(abs(i - (int)num_bins / 2), abs((int)num_bins / 2 - 1 - i));
  //     int len = (int)num_input_keys / (add_size + num_input_keys / num_bins);
  //     printf("len = %d\n", len);
  //     // int slope = (add_size + num_input_keys / num_bins) / len;
  //       // printf("slope: %d\n", slope);
  //     // slope = (add_size + num_input_keys / num_bins) / len
  //     bin_sizes[i] = std::max(0LL, (long long)num_input_keys / (long long)num_bins + (long long)add_size - (long long)d * ((long long)add_size + (long long)num_input_keys / (long long)num_bins) / len);
  //     printf("bin %d size: %ld\n", i, bin_sizes[i]);
  //   }
  // }

  // // std::shuffle(bin_sizes.begin(), bin_sizes.end(), rng);
  // // printf("tot num_of_keys %ld\n",);
  // // printf("add_size = %ld\n", add_size);
  // // printf("bin sizes: ");
  // // for (int i = 0; i < num_bins; i++) printf("%lu ", bin_sizes[i]);
  // // printf("\n");

  // num_input_keys =  std::accumulate(bin_sizes.begin(), bin_sizes.end(), 0LL);
  printf("here0\n");

  std::vector<UpDown::word_t> inputOri(num_input_keys);

  // uint64_t num_partitions = num_lanes * num_partition_per_lane;
  ;
  // uint64_t max_value = 1000000;
  printf("num_input_keys = %ld\n", num_input_keys);

  // uint64_t BLOCK_SIZE = 256;
  // uint64_t BLOCK_SIZE = 5;
  // Allocate the array where the top and updown can see it:
  // testKVpair* inKVSet = reinterpret_cast<testKVpair*>(testKVMSR_rt->mm_malloc(num_input_keys * sizeof(testKVpair)));
  printf("here1\n");
  UpDown::word_t* inKVSet = reinterpret_cast<UpDown::word_t*>(testKVMSR_rt->mm_malloc(num_input_keys * sizeof(UpDown::word_t)));
  printf("here2\n");

  UpDown::word_t* outKVSet = reinterpret_cast<UpDown::word_t*>(testKVMSR_rt->mm_malloc(num_lanes * sizeof(UpDown::word_t)));
  
  printf("here3\n");

  uint64_t dramBlockSize = num_input_keys / num_bins * bin_extra_factor * sizeof(UpDown::word_t);
  uint64_t binBlockSize = dramBlockSize * num_bins;
  printf("dramBlockSize: %ld, binBlockSize: %ld\n", dramBlockSize, binBlockSize);
  UpDown::word_t* outputTempSet = reinterpret_cast<UpDown::word_t*>(testKVMSR_rt->mm_malloc(binBlockSize + num_bins * 3 * sizeof(UpDown::word_t)));
  printf("inKVSet = %p, outKVSet = %p, outputTempSet = %p\n", inKVSet, outKVSet, outputTempSet);

  printf("input segment: %lu to %lu", inKVSet, inKVSet + num_input_keys);
  // printf("output segment: %lu to %lu", outKVSet, outKVSet + num_lanes);
  printf("outputTempSet segment: %lu to %lu", outputTempSet, outputTempSet + binBlockSize / 8 + num_bins * 3);
  // UpDown::word_t* outputArray = reinterpret_cast<UpDown::word_t*>(testKVMSR_rt->mm_malloc(num_input_keys * sizeof(UpDown::word_t)));

#ifdef DEBUG
  printf("-------------------\ninKVSet = %p\n", inKVSet);
#endif
  // Initialize input key-value set in DRAM

  // int cur = 0;
  // UpDown::word_t value_block_size = (max_value + num_bins) / num_bins;
  // for (int i = 0; i < num_bins; i++) {
  //   for (int j = 0; j < bin_sizes[i]; j++) {
  //     inKVSet[cur] = value_block_size * i + rng() % value_block_size;
  //     inputOri[cur] = inKVSet[cur];
  //     cur++;
  //   }
  // }
  // std::shuffle(inKVSet, inKVSet + num_input_keys, rng);

  // printf("here4");
  // initialize integer normal distribution with mean=max_value / 2 and a fixed seed 233
  std::default_random_engine generator(233);
  // normal distribution
  std::normal_distribution<double> distribution(max_value / 3 * 2, max_value / sigma_divider);
  std::normal_distribution<double> distribution2(max_value / 3, max_value / sigma_divider);
  // std::uniform_int_distribution<int> distribution(1, max_value);

  auto sample_next = [&](std::normal_distribution<double>& distribution) {
    while(true) {
      double value = distribution(generator);
      if (value < 0 || value > max_value) {
        continue;
      }
      return (int64_t)value;
    }
  };
  
  std::vector<int> cnt(num_bins, 0);
  for (int i = 0; i < num_input_keys; i++) {
    // inKVSet[i].key = i;
    inKVSet[i] = sample_next(i < num_input_keys / 2 ? distribution : distribution2);
    // inKVSet[i] = std::max(std::min((int64_t)max_value, (int64_t)distribution(generator)), (int64_t)1);
    cnt[inKVSet[i] / ((max_value + num_bins) / num_bins)]++;
    // inKVSet[i] = std::max((uint64_t)1, rng() % (max_value + 1));
    // inputOri[i] = inKVSet[i];
    // inKVSet[i].value = 1;
#ifdef DEBUG_INPUT
    printf("Input pair %d: key=%ld value=%ld DRAM_addr=%p\n", i, inKVSet[i].key, inKVSet[i].value, inKVSet + i);
#endif
  }
  std::shuffle(inKVSet, inKVSet + num_input_keys, rng);
  std::vector<std::pair<int,int>> ps(num_bins);
  for (int i = 0; i < num_bins; i++) {
    ps[i] = std::make_pair(cnt[i], i);
  }
  std::sort(ps.begin(), ps.end());
  std::reverse(ps.begin(), ps.end());
  for (int i = 0; i < 10; i++) {
    std::cout << ps[i].first << ", " << ps[i].second << '\n';
  }
  for (int i = num_bins - 10; i < num_bins; i++) {
      std::cout << ps[i].first << ", " << ps[i].second << '\n';
  }
  std::cout << std::endl;
  // std::cout << "input keys: "; 
  // for (int i = 0; i < num_input_keys; i++) {
  //   printf("%ld ", inKVSet[i]);
  // }
  // printf("\n");
  std::vector<UpDown::word_t> inputVec(inKVSet, inKVSet + num_input_keys);

#ifdef DEBUG
  printf("-------------------\noutKVSet = %p\n", outKVSet);
#endif

  // UpDown::word_t** partitions = reinterpret_cast<UpDown::word_t**>(testKVMSR_rt->mm_malloc((num_partitions) * sizeof(UpDown::word_t*)));
  UpDown::word_t** partitions = reinterpret_cast<UpDown::word_t**>(outputTempSet);
  printf("size of word_t: %ld, word_t*: %d\n", sizeof(UpDown::word_t), sizeof(UpDown::word_t*));

#ifdef DEBUG
  printf("-------------------\nparitions = %p\n", partitions);
#endif

  fflush(stdout);

  //   printf("-------------------\n input kv set.\n");
  // for (int i = 0; i < num_input_keys; i++) {
  //   // printf("%ld ", inKVSet[i]);
  //   printf("%ld %ld\n", &inKVSet[i], inKVSet[i]);
  // }
  // printf("\n");

  // printf("-------------------\nPrefix sum array\n");
  // uint64_t start = bin_extra_factor * num_input_keys;
  // for (int i = 0; i < num_lanes; i++) {
  //   printf("%d ",outputTempSet[start + i]);
  // }
  // printf("\n");
  // printf("-------------------\n Block sum array\n");
  // start = bin_extra_factor * num_input_keys + num_lanes;
  // for (int i = 0; i < num_lanes / 2; i++) {
  //   printf("%ld %d \n", &outputTempSet[start + i], outputTempSet[start + i]);
  // }
  // printf("\n");
  // fflush(stdout);

  UpDown::word_t TOP_FLAG_OFFSET = 0;
  const auto time_start = timer::now();
  // uint64_t start_lane_offset = 5;
#if defined(GEM5_MODE)
  m5_switch_cpu();
  m5_dump_reset_stats(0, 0);
  m5_perf_log_write(0, 0, 0, "start sort");
#endif
// #if defined(GEM5_MODE)
//   m5_dump_reset_stats(0, 0);
//   m5_perf_log_write(0, 0, 0, "start sort");
// #endif

  /* operands
      OB_0: Pointer to the partition array (64-bit DRAM address)
      OB_1: Number of partitions per lane
      OB_2: Number of lanes
      OB_3: Pointer to input kvset (64-bit DRAM address)
      OB_4: Number of elements in the input kvset (1D array)
      OB_5: Pointer to outKVMap (64-bit DRAM address)
      OB_6: Number of elements in the output kvset (1D array)
  */
  UpDown::word_t ops_data[8];
  UpDown::operands_t ops(8, ops_data);
  ops.set_operand(0, (uint64_t) 1600);
  ops.set_operand(1, (uint64_t) num_input_keys);
  ops.set_operand(2, (uint64_t) inKVSet);
  ops.set_operand(3, (uint64_t) num_lanes);
  ops.set_operand(4, (uint64_t) outputTempSet);
  ops.set_operand(5, (uint64_t) num_bins);
  ops.set_operand(6, (uint64_t) lb_tmp_addr);
  ops.set_operand(7, (uint64_t) max_value);
  // ops.set_operand(7, (uint64_t) 0);

  printf("Prepare operands done.\n");
  
  UpDown::networkid_t nwid(start_lane_offset, false, 0);

  for (int iter = 0; iter < 1; iter++) {
    UpDown::event_t evnt_ops(event_labels[mode + "_" + sortmode] /*Event Label*/,
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
  

#ifdef DEBUG
  printf("-------------------\nUpDown program termiantes. Verify the result input kv set.\n");

#if defined(GEM5_MODE)
  m5_dump_reset_stats(0, 0);
  m5_perf_log_write(0, 0, 0, "end sort");
#endif

#endif



  delete testKVMSR_rt;
  printf("Test UDKVMSR program finishes.\n");

  return 0;
}