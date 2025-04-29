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
#include "spmv_lbmsr_exe_nlb.hpp"
#include "spmv_lbmsr_exe_ws.hpp"
#include "spmv_lbmsr_exe_rh_nlbstrm_on.hpp"
#include "spmv_lbmsr_exe_rh_random.hpp"
// using namespace std;

#ifdef GEM5_MODE
 #include <gem5/m5ops.h>
#endif

#define USAGE "USAGE: ./spmvMSRPerfFileTest <mat1_height> <mat1_width> <mat2_height> <mat2_width>"

#define NUM_LANE_PER_UD 64
#define NUM_UD_PER_CLUSTER 4
#define NUM_CLUSTER_PER_NODE 8
#define PARTITION_PER_LANE 32 

// #define MAT1_HEIGHT 162
// #define MAT1_WIDTH 162
// #define MAT2_HEIGHT 162
// #define MAT2_WIDTH 162



UpDown::UDRuntime_t* gen_runtime(uint64_t num_workers, std::string mode){
  UpDown::ud_machine_t machine;
  machine.NumNodes = std::max((uint64_t)1, num_workers/2048);
  machine.NumStacks = 8;
  machine.NumUDs = 4;
  machine.NumLanes = 64;
  machine.MapMemSize = 34359738368;

  machine.LocalMemAddrMode = 1;

  UpDown::UDRuntime_t *rt = new UpDown::BASimUDRuntime_t(machine, "spmv_lbmsr_exe_"+mode+".bin", 0);
  printf("Running BASim\n");

  return rt;
}

int test_exec(UpDown::UDRuntime_t* rt, std::string mode, std::string filename, uint64_t num_workers){

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
  std::istringstream iss(line);
  std::string result;
  std::string token;
  std::getline( iss, token, ' ' );
  int h = std::stol(token);
  std::getline( iss, token, ' ' );
  int w = std::stol(token);
  std::getline( iss, token, ' ' );
  int nnz = std::stol(token);


  printf("Parsing Matrix (Height: %ld  Width: %ld  Nonzeros: %ld)\n", h, w, nnz);

  uint64_t* mat1_cols = reinterpret_cast<uint64_t*>(rt->mm_malloc(nnz * sizeof(uint64_t)));
  double* mat1_vals = reinterpret_cast<double*>(rt->mm_malloc(nnz * sizeof(double)));
  uint64_t* mat1_index = reinterpret_cast<uint64_t*>(rt->mm_malloc(2 * h * sizeof(uint64_t)));
  uint64_t* part_array = reinterpret_cast<uint64_t*>(rt->mm_malloc(2 * num_workers * PARTITION_PER_LANE * sizeof(uint64_t)));


  uint64_t prev_idx = 0;
  for(int i = 0; i < h; i ++){
      std::getline(mat_file, line);
      mat1_index[i * 2] = prev_idx;
      mat1_index[i * 2 + 1] = std::stol(line);
      prev_idx = mat1_index[i * 2 + 1];
  }
  printf("mat1_index = %p, mat1_index[0] = %ld\n", mat1_index, mat1_index[0]);

  for(int i = 0; i < nnz; i ++){
      std::getline(mat_file, line);
      mat1_cols[i] = std::stol(line);
  }
  printf("mat1_cols[0] = %ld\n", mat1_cols[0]);

  for(int i = 0; i < nnz; i ++){
      std::getline(mat_file, line);
      mat1_vals[i] = std::stod(line);
  }
  printf("mat1_vals[0] = %lf\n", mat1_vals[0]);

  printf("Address of Matrix 1: %lx\n", (uint64_t) mat1_vals);

  printf("Building Matrix 2\n");

#ifdef GEM5_MODE
  double* mat2 = reinterpret_cast<double*>(rt->mm_malloc_global(w * sizeof(double)));
#else
  double* mat2 = reinterpret_cast<double*>(rt->mm_malloc(w * sizeof(double)));
#endif

  for(int i = 0; i < w; i ++){
    mat2[i] = 1.0;
  }
  printf("Address of Matrix 2: %lx\n", (uint64_t) mat2);

  double* res_mat = reinterpret_cast<double*>(rt->mm_malloc(h * sizeof(double)));

  printf("Results will be stored at address %lx\n", (uint64_t) res_mat);
  printf("Running SpMV on %ld lanes\n", num_workers);


  // Generate partitions
  uint64_t input_size = h, num_lanes=num_workers, input_entry_size=2, num_partition_per_lane=PARTITION_PER_LANE;
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
      uint64_t *input_arr = mat1_index + i * input_entry_size * num_pairs_per_part;
      input_arr += i < extra_pairs ? (input_entry_size * i) : (input_entry_size * extra_pairs);
      part_array[2*i] = (uint64_t) input_arr;
      input_arr += input_entry_size * num_pairs_per_part;
      input_arr += i < extra_pairs ? input_entry_size : 0;
      part_array[2*i+1] = (uint64_t) input_arr;
      // std::cout << i << std::endl;
  }
  std::cout << "Finished generating partitions." << std::endl;
  ////////////////////////

#ifndef GEM5_MODE
  UpDown::BASimUDRuntime_t* simrt = reinterpret_cast<UpDown::BASimUDRuntime_t*> (rt);
  simrt->reset_stats();
  std::cout << "Finished reseting stats in fastim." << std::endl;
#endif
  
  UpDown::word_t ops_data[8];
  UpDown::operands_t ops(8, ops_data);
  ops.set_operand(0, (uint64_t) mat1_index);
  ops.set_operand(1, (uint64_t) h);
  ops.set_operand(2, (uint64_t) mat1_vals);
  ops.set_operand(3, (uint64_t) mat1_cols);
  ops.set_operand(4, (uint64_t) mat2);
  ops.set_operand(5, (uint64_t) res_mat);
  ops.set_operand(6, (uint64_t) part_array);
  ops.set_operand(7, (uint64_t) num_workers);

  UpDown::networkid_t nwid(0, false, 0);
  UpDown::word_t TOP_FLAG_OFFSET = 65528;


  // UpDown::event_t evnt_ops(spmv_lbmsr_exe::matvecmul_master__mv_init /*Event Label*/,
  //                           nwid,
  //                           UpDown::CREATE_THREAD /*Thread ID*/,
  //                           &ops /*Operands*/);
  // rt->send_event(evnt_ops);
  UpDown::event_t *event_ops;
  if (mode == "rh_nlbstrm_on" || mode == "rh_nlbstrm_off"){
      event_ops = new UpDown::event_t(spmv_lbmsr_exe_rh_nlbstrm_on::matvecmul_master__mv_init /*Event Label*/,
                              nwid,
                              UpDown::CREATE_THREAD /*Thread ID*/,
                              &ops /*Operands*/);
      printf("Running CSR SPMV with NLBSTRM On\n");
  }
  else if (mode == "rh_random"){
      event_ops = new UpDown::event_t(spmv_lbmsr_exe_rh_random::matvecmul_master__mv_init /*Event Label*/,
                              nwid,
                              UpDown::CREATE_THREAD /*Thread ID*/,
                              &ops /*Operands*/);
      printf("Running CSR SPMV with RobinHood Random\n");
  }
  else if (mode == "ws"){
      event_ops = new UpDown::event_t(spmv_lbmsr_exe_ws::matvecmul_master__mv_init /*Event Label*/,
                              nwid,
                              UpDown::CREATE_THREAD /*Thread ID*/,
                              &ops /*Operands*/);
      printf("Running CSR SPMV with WS\n");
  }
  else if (mode == "nlb"){
      event_ops = new UpDown::event_t(spmv_lbmsr_exe_nlb::matvecmul_master__mv_init /*Event Label*/,
                              nwid,
                              UpDown::CREATE_THREAD /*Thread ID*/,
                              &ops /*Operands*/);
      printf("Running CSR SPMV with NLB\n");
  }
  else{
      printf("Invalid mode selected!\n");
      return 0;
  }


  printf("set event word\n");
  rt->send_event(*event_ops);


  printf("First event sent\n");

  std::cout << "Starting execution" << std::endl;
  rt->start_exec(nwid);
  printf("Waiting for first loop to terminate\n");

  rt->test_wait_addr(nwid, TOP_FLAG_OFFSET, 1);
  printf("First event terminates.\n");
  

#ifndef GEM5_MODE
  double* gold_mat = (double*) malloc(h * sizeof(double));

  printf("Printing Gold Matrix\n");
  for(int i = 0; i < h; i++){
    double val = 0.0;
    for(int k = 0; k < (mat1_index[i * 2 + 1] - mat1_index[i * 2]) / 8; k++){
      uint64_t prev_idx = mat1_index[i * 2] / 8;
      val += mat1_vals[k + prev_idx] * mat2[mat1_cols[k + prev_idx]];
    }
    gold_mat[i] = val;

    // printf("%lf\t", gold_mat[i]);
    // printf("\n");
  }

  for(int i = 0; i < h; i++){
    int idx = i;
    if(gold_mat[idx] - res_mat[idx] > 0.001 || gold_mat[idx] - res_mat[idx] < -0.001){
      printf("TEST FAILED AT POS %ld\n", idx);
      return 1;
    }
  }
  printf("TEST PASSED\n");
  
#endif

  return 0;
  
}

int main(int argc, char* argv[]) {
  
  std::string mode = argv[1];
  if (mode == "rh" || mode == "rh_nlbstrm_off") {
    mode = "rh_nlbstrm_on";
  }
  uint64_t num_workers = std::stol(argv[2]) * 2048;
  std::string path = argv[3];
  UpDown::UDRuntime_t* rt = gen_runtime(num_workers, mode);

  return test_exec(rt, mode, path, num_workers);

}
