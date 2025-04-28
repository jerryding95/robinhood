#include "simupdown.h"

#include <cstdio>
#include <cstdlib>
#include <iostream>
#include <cmath>
#include <fstream>
#include <string>
#include <sstream>
#include <random>
#include "basimupdown.h"
#include "gcn_udkvmsr_exe_rh_random.hpp"
#include "gcn_udkvmsr_exe_rh_nlbstrm_off.hpp"
#include "gcn_udkvmsr_exe_rh_nlbstrm_on.hpp"
#include "gcn_udkvmsr_exe_ws.hpp"
#include "gcn_udkvmsr_exe_nlb.hpp"
// using namespace std;

#ifdef GEM5_MODE
 #include <gem5/m5ops.h>
#endif

#define USAGE "USAGE: ./gcn_vanilla <input_file> <num_node> <num_vertex> <num_edges>\n"

#define NUM_LANE_PER_UD 64
#define NUM_UD_PER_CLUSTER 4
#define NUM_CLUSTER_PER_NODE 8
#define PARTITION_PER_LANE 32

uint64_t* gen_intermediate_kv(UpDown::UDRuntime_t* rt, int num_lanes, int num_bin_per_lane, int bin_size){
#ifdef GEM5_MODE
    uint64_t* interPtrArr = reinterpret_cast<uint64_t*>(rt->mm_malloc_global(num_lanes * sizeof(uint64_t)));
    uint64_t* interLanePtrArr = reinterpret_cast<uint64_t*>(rt->mm_malloc_global(num_bin_per_lane * num_lanes * sizeof(uint64_t)));
    uint64_t* p_inter = reinterpret_cast<uint64_t*>(rt->mm_malloc_global(num_bin_per_lane * num_lanes * (bin_size * sizeof(uint64_t))));
#else
    uint64_t* interPtrArr = reinterpret_cast<uint64_t*>(rt->mm_malloc(num_lanes * sizeof(uint64_t)));
    uint64_t* interLanePtrArr = reinterpret_cast<uint64_t*>(rt->mm_malloc(num_bin_per_lane * num_lanes * sizeof(uint64_t)));
    uint64_t* p_inter = reinterpret_cast<uint64_t*>(rt->mm_malloc(num_bin_per_lane * num_lanes * (bin_size * sizeof(uint64_t))));
#endif

#ifdef DEBUG
    printf("-------------------\ninterPtrArr = %p\n", *interPtrArr);
#endif

    for (int i=0; i<num_lanes; i++){
        int lanePtrStart = i*num_bin_per_lane;
        int laneBinStart = i*num_bin_per_lane*bin_size;
        interPtrArr[i] = (uint64_t) (interLanePtrArr + lanePtrStart);
#ifdef DEBUG
        printf("Intermediate Hashtable %d: array start=%p, bin start=%p DRAM_addr=%p\n", 
            i, interLanePtrArr + i*num_bin_per_lane, p_inter + i*num_bin_per_lane*bin_size, interPtrArr + i);
#endif
        for (int j=0; j<num_bin_per_lane; j++){
            interLanePtrArr[lanePtrStart + j] = (uint64_t) (p_inter + laneBinStart + j*bin_size);
#ifdef DEBUG
            printf("    interLanePtrArr %d, points to %lx, DRAM address %p\n", j, interLanePtrArr[lanePtrStart + j], interLanePtrArr + lanePtrStart + j);
#endif
        }

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

#ifdef DEBUG_GRAPH
    printf("-------------------\ninterPtrArr = %p\n", *interPtrArr);
#endif

    for (int i=0; i<num_uds; i++){
        int udPtrStart = i*num_bin_per_ud;
        int udBinStart = i*num_bin_per_ud*bin_size;
        interPtrArr[i] = (uint64_t) (interUdPtrArr + udPtrStart);
#ifdef DEBUG_GRAPH
        printf("Intermediate Hashtable %d: array start=%p, bin start=%p DRAM_addr=%p\n", 
            i, interUdPtrArr + i*num_bin_per_ud, p_inter + i*num_bin_per_ud*bin_size, interPtrArr + i);
#endif
        for (int j=0; j<num_bin_per_ud; j++){
            interUdPtrArr[udPtrStart + j] = (uint64_t) (p_inter + udBinStart + j*bin_size);
#ifdef DEBUG_GRAPH
            printf("    interUdPtrArr %d, points to %lx, DRAM address %p\n", j, interUdPtrArr[udPtrStart + j], interUdPtrArr + udPtrStart + j);
#endif
        }

    }

    return interPtrArr;
}

UpDown::UDRuntime_t* gen_runtime(uint64_t num_workers, std::string filename) {
  UpDown::ud_machine_t machine;
  machine.NumNodes = std::max((uint64_t)1, num_workers/2048);
  machine.NumStacks = 8;
  machine.NumUDs = 4;
  machine.NumLanes = 64;
  machine.MapMemSize = 1ULL<<37;

  machine.LocalMemAddrMode = 1;

  UpDown::UDRuntime_t *rt = 
#ifdef GEM5_MODE
    new UpDown::UDRuntime_t(machine);
    printf("Running Gem5\n");
#elif defined (BASIM)
    new UpDown::BASimUDRuntime_t(machine, filename, 0);
    printf("Running BASim\n");
#else
    new UpDown::SimUDRuntime_t(machine, "matMulEFA", "matMulEFA", "./", UpDown::EmulatorLogLevel::FULL_TRACE);
    printf("Running FastSim\n");
#endif

  return rt;
}

int test_exec(UpDown::UDRuntime_t* rt, std::string mode, std::string filename, uint64_t num_workers, uint64_t h, uint64_t w, uint64_t nnz){

  printf("=== Base Addresses ===\n");
  rt->dumpBaseAddrs();
  printf("\n=== Machine Config ===\n");
  rt->dumpMachineConfig();

  std::ifstream mat_file(filename);
  if(!mat_file.is_open()){
    printf("Failed to open matrix file!\n");
    exit(1);
  }
  
  std::string line;
  std::getline(mat_file, line);
  while (line[0] == '%' || line[0] == '#') {
    std::getline(mat_file, line);
  }
  std::istringstream iss(line);
  std::string result;
  std::string token;
  // std::getline( iss, token, ' ' );
  // int h = std::stol(token);
  // std::getline( iss, token, ' ' );
  // int w = std::stol(token);
  // std::getline( iss, token, ' ' );
  // int nnz = std::stol(token);


  printf("Parsing Matrix (Height: %ld  Width: %ld  Nonzeros: %ld)\n", h, w, nnz);

#ifdef GEM5_MODE
  uint64_t* mat1 = reinterpret_cast<uint64_t*>(rt->mm_malloc_global(2 * nnz * sizeof(uint64_t)));
  uint64_t* part_array = reinterpret_cast<uint64_t*>(rt->mm_malloc_global(2 * num_workers * PARTITION_PER_LANE * sizeof(uint64_t)));
#else
  uint64_t* mat1 = reinterpret_cast<uint64_t*>(rt->mm_malloc(2 * nnz * sizeof(uint64_t)));
  uint64_t* part_array = reinterpret_cast<uint64_t*>(rt->mm_malloc(2 * num_workers * PARTITION_PER_LANE * sizeof(uint64_t)));
#endif

  uint64_t prev_idx = 0;
  for(int i = 0; i < nnz; i ++){
      uint64_t r, c;
      mat_file >> r >> c;
      mat1[i * 2] = r;
      mat1[i * 2 + 1] = c;
      // std::getline(mat_file, line);
      // std::cout << "line " << line << std::endl;
      // iss.clear();
      // iss.str(line);
      // std::getline(iss, token, ' ');
      // std::cout << "token0 " << token << std::endl;
      // mat1[i * 2] = std::stol(token);
      // std::getline(iss, token, ' ');
      // std::cout << "token1 " << token << std::endl;
      // mat1[i * 2 + 1] = std::stol(token);
      // std::getline(mat_file, line);
      // std::cout << "src:  " << mat1[i*2] << ", dest: " << mat1[i*2+1] << std::endl;
  }
  printf("mat1 = %p\n", mat1);

#ifdef GEM5_MODE
  m5_switch_cpu();
#endif


  // Generate partitions
  uint64_t input_size = nnz, num_lanes=num_workers, input_entry_size=2, num_partition_per_lane=PARTITION_PER_LANE;
  // uint64_t num_pairs_per_part = std::max((uint64_t)(std::ceil(input_size / (num_lanes * num_partition_per_lane * 1.0))), (uint64_t)1);
  uint64_t num_pairs_per_part = input_size / (num_lanes * num_partition_per_lane);
  uint64_t extra_pairs = input_size - num_lanes * num_partition_per_lane * num_pairs_per_part;

  std::cout << "Generating partitions, num_pairs_per_part: " << num_pairs_per_part << std::endl;

  // Initialize partitions
  uint64_t num_partitions = num_lanes * num_partition_per_lane;
  int offset = 0;

  #pragma omp parallel for
  for (int i = 0; i < num_partitions; i++) {
      // part_array[2*i] = (uint64_t)(input_arr + input_entry_size*std::min((i) * num_pairs_per_part, input_size));
      // part_array[2*i+1] = (uint64_t)(input_arr + input_entry_size*std::min((i+1) * num_pairs_per_part, input_size));
      // printf("Partition %d: start 0x%lx, end 0x%lx, address %p\n", i, part_array[2*i], part_array[2*i+1], part_array+2*i);
      uint64_t *input_arr = mat1 + i * input_entry_size * num_pairs_per_part;
      input_arr += i < extra_pairs ? input_entry_size * i : input_entry_size * extra_pairs;
      part_array[2*i] = (uint64_t) input_arr;
      input_arr += input_entry_size * num_pairs_per_part;
      input_arr += i < extra_pairs ? input_entry_size : 0;
      part_array[2*i+1] = (uint64_t) input_arr;
  }
  
  uint64_t* interSpace;
  if (mode == "ws")
    interSpace = gen_intermediate_kv(rt, num_workers, 512, 512*3);
  else if(mode != "nlb")
    interSpace = gen_intermediate_kv_ud(rt, num_workers / 64, 512*64, 512*3);
    

// #ifndef GEM5_MODE
//   UpDown::BASimUDRuntime_t* simrt = reinterpret_cast<UpDown::BASimUDRuntime_t*> (rt);
//   simrt->reset_stats();
// #endif
#ifdef GEM5_MODE
  m5_switch_cpu();
#endif
  
  UpDown::word_t ops_data[6];
  UpDown::operands_t ops(6, ops_data);
  ops.set_operand(0, (uint64_t) mat1);
  ops.set_operand(1, (uint64_t) nnz);
  ops.set_operand(2, (uint64_t) part_array);
  ops.set_operand(3, (uint64_t) PARTITION_PER_LANE);
  ops.set_operand(4, (uint64_t) num_workers);
  ops.set_operand(5, (uint64_t) interSpace);
  UpDown::networkid_t nwid(0, false, 0);
  UpDown::word_t TOP_FLAG_OFFSET = 65528;

#ifdef GEM5_MODE
  m5_dump_reset_stats(0,0);
#endif

  UpDown::event_t *event_ops;
  if(mode == "rh_nlbstrm_off"){
    event_ops = new UpDown::event_t(gcn_udkvmsr_exe_rh_nlbstrm_off::gnn_vanilla_master__gnn_start /*Event Label*/,
                          nwid,
                          UpDown::CREATE_THREAD /*Thread ID*/,
                          &ops /*Operands*/);
    printf("Running GCN Vanilla with NLBSTRM Off\n");
  }
  else if (mode == "rh_nlbstrm_on"){
    event_ops = new UpDown::event_t(gcn_udkvmsr_exe_rh_nlbstrm_on::gnn_vanilla_master__gnn_start /*Event Label*/,
                          nwid,
                          UpDown::CREATE_THREAD /*Thread ID*/,
                          &ops /*Operands*/);
    printf("Running GCN Vanilla with NLBSTRM On\n");
  }
  else if (mode == "rh_random"){
    event_ops = new UpDown::event_t(gcn_udkvmsr_exe_rh_random::gnn_vanilla_master__gnn_start /*Event Label*/,
                          nwid,
                          UpDown::CREATE_THREAD /*Thread ID*/,
                          &ops /*Operands*/);
    printf("Running GCN Vanilla with RobinHood Random\n");
  }
  else if (mode == "ws"){
    event_ops = new UpDown::event_t(gcn_udkvmsr_exe_ws::gnn_vanilla_master__gnn_start /*Event Label*/,
                          nwid,
                          UpDown::CREATE_THREAD /*Thread ID*/,
                          &ops /*Operands*/);
    printf("Running GCN Vanilla with WS\n");
  }
  else if (mode == "nlb"){
    event_ops = new UpDown::event_t(gcn_udkvmsr_exe_nlb::gnn_vanilla_master__gnn_start /*Event Label*/,
                          nwid,
                          UpDown::CREATE_THREAD /*Thread ID*/,
                          &ops /*Operands*/);
    printf("Running GCN Vanilla with NLB\n");
  }
  else{
    printf("Invalid mode selected!\n");
    return 1;
  }
  
  // UpDown::event_t evnt_ops(gcn_udkvmsr_exe_rh_random::gnn_vanilla_master__gnn_start /*Event Label*/,
  //                           nwid,
  //                           UpDown::CREATE_THREAD /*Thread ID*/,
  //                           &ops /*Operands*/);
  rt->send_event(*event_ops);
  printf("First event sent\n");

  rt->start_exec(nwid);
  printf("Waiting for first loop to terminate\n");

  rt->test_wait_addr(nwid, TOP_FLAG_OFFSET, 1);
  printf("First event terminates.\n");
  
  delete event_ops;
  return 0;
  
}

int main(int argc, char* argv[]) {
  if (argc != 6) {
    std::cerr << USAGE;
    return 1;
  }
  std::string mode = argv[1];
  std::string filename = "gcn_udkvmsr_exe_"+mode+".bin";
  uint64_t num_workers = std::stol(argv[2]);
  std::string path = argv[3];
  uint64_t h = std::stol(argv[4]);
  uint64_t nnz = std::stol(argv[5]);
  UpDown::UDRuntime_t* rt = gen_runtime(num_workers*2048, filename);

  return test_exec(rt, mode, path, num_workers*2048, h, h, nnz);

}
