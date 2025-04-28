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
#include "spmv_msr_exe.hpp"
// using namespace std;

#ifdef GEM5_MODE
 #include <gem5/m5ops.h>
#endif

#define USAGE "USAGE: ./spmvMSRPerfFileTest <mat1_height> <mat1_width> <mat2_height> <mat2_width>"

#define NUM_LANE_PER_UD 64
#define NUM_UD_PER_CLUSTER 4
#define NUM_CLUSTER_PER_NODE 8
#define PARTITION_PER_LANE 64 

// #define MAT1_HEIGHT 162
// #define MAT1_WIDTH 162
// #define MAT2_HEIGHT 162
// #define MAT2_WIDTH 162



UpDown::UDRuntime_t* gen_runtime(){
  UpDown::ud_machine_t machine;
  machine.NumNodes = 16;
  machine.NumStacks = 8;
  machine.NumUDs = 4;
  machine.NumLanes = 64;
  machine.MapMemSize = 34359738368;

  machine.LocalMemAddrMode = 1;

  UpDown::UDRuntime_t *rt = 
#ifdef GEM5_MODE
    new UpDown::UDRuntime_t(machine);
    printf("Running Gem5\n");
#elif defined (BASIM)
    new UpDown::BASimUDRuntime_t(machine, "spmv_msr_exe.bin", 0);
    printf("Running BASim\n");
#else
    new UpDown::SimUDRuntime_t(machine, "matMulEFA", "matMulEFA", "./", UpDown::EmulatorLogLevel::FULL_TRACE);
    printf("Running FastSim\n");
#endif

  return rt;
}

int test_exec(UpDown::UDRuntime_t* rt, std::string filename, uint64_t num_workers){

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

#ifdef GEM5_MODE
  uint64_t* mat1_cols = reinterpret_cast<uint64_t*>(rt->mm_malloc_global(nnz * sizeof(uint64_t)));
  double* mat1_vals = reinterpret_cast<double*>(rt->mm_malloc_global(nnz * sizeof(double)));
  uint64_t* mat1_index = reinterpret_cast<uint64_t*>(rt->mm_malloc_global(2 * h * sizeof(uint64_t)));
  uint64_t* part_array = reinterpret_cast<uint64_t*>(rt->mm_malloc_global(2 * num_workers * PARTITION_PER_LANE * sizeof(uint64_t)));
#else
  uint64_t* mat1_cols = reinterpret_cast<uint64_t*>(rt->mm_malloc(nnz * sizeof(uint64_t)));
  double* mat1_vals = reinterpret_cast<double*>(rt->mm_malloc(nnz * sizeof(double)));
  uint64_t* mat1_index = reinterpret_cast<uint64_t*>(rt->mm_malloc(2 * h * sizeof(uint64_t)));
  uint64_t* part_array = reinterpret_cast<uint64_t*>(rt->mm_malloc(2 * num_workers * PARTITION_PER_LANE * sizeof(uint64_t)));
#endif

  uint64_t prev_idx = 0;
  for(int i = 0; i < h; i ++){
      std::getline(mat_file, line);
      mat1_index[i * 2] = prev_idx;
      mat1_index[i * 2 + 1] = std::stol(line);
      prev_idx = mat1_index[i * 2 + 1];
  }
  printf("mat1_index[0] = %ld\n", mat1_index[0]);

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

#ifdef GEM5_MODE
  double* res_mat = reinterpret_cast<double*>(rt->mm_malloc_global(h * sizeof(double)));
#else
  double* res_mat = reinterpret_cast<double*>(rt->mm_malloc(h * sizeof(double)));
#endif

  printf("Results will be stored at address %lx\n", (uint64_t) res_mat);
  printf("Running SpMV on %ld lanes\n", num_workers);
#ifdef GEM5_MODE
  m5_switch_cpu();
#endif

#ifndef GEM5_MODE
  UpDown::BASimUDRuntime_t* simrt = reinterpret_cast<UpDown::BASimUDRuntime_t*> (rt);
  simrt->reset_stats();
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

#ifdef GEM5_MODE
  m5_dump_reset_stats(0,0);
#endif


  UpDown::event_t evnt_ops(spmv_msr_exe::matvecmul_master__mv_init /*Event Label*/,
                            nwid,
                            UpDown::CREATE_THREAD /*Thread ID*/,
                            &ops /*Operands*/);
  rt->send_event(evnt_ops);
  printf("First event sent\n");

  rt->start_exec(nwid);
  printf("Waiting for first loop to terminate\n");

  rt->test_wait_addr(nwid, TOP_FLAG_OFFSET, 1);
  printf("First event terminates.\n");
  
#ifdef GEM5_MODE
  m5_dump_reset_stats(0,0);
#endif

#ifndef GEM5_MODE
  for(int idx = 0; idx < num_workers; idx++){
    simrt->print_stats(idx / 64,idx % 64);
  }
#endif

#ifndef GEM5_MODE
  printf("Printing Output Matrix\n");
  for(int i = 0; i < h; i ++){
    printf("%lf\t", res_mat[i]);
    printf("\n");
  }
#endif

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

    printf("%lf\t", gold_mat[i]);
    printf("\n");
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

#ifdef GEM5_MODE
  m5_dump_reset_stats(0,0);
#endif

  return 0;
  
}

int test_exec_bin(UpDown::UDRuntime_t* rt, std::string filename, uint64_t num_workers){

  printf("=== Base Addresses ===\n");
  rt->dumpBaseAddrs();
  printf("\n=== Machine Config ===\n");
  rt->dumpMachineConfig();

  std::ifstream mat_file(filename, std::ios::in | std::ios::binary);
  if(!mat_file.is_open()){
    printf("Failed to open matrix file!\n");
    exit(1);
  }
  
  uint64_t h, w, nnz;
  mat_file.read(reinterpret_cast<char*>(&h), sizeof(uint64_t));
  mat_file.read(reinterpret_cast<char*>(&w), sizeof(uint64_t));
  mat_file.read(reinterpret_cast<char*>(&nnz), sizeof(uint64_t));


  printf("Parsing Matrix (Height: %ld  Width: %ld  Nonzeros: %ld)\n", h, w, nnz);

#ifdef GEM5_MODE
  uint64_t* mat1_cols = reinterpret_cast<uint64_t*>(rt->mm_malloc_global(nnz * sizeof(uint64_t)));
  double* mat1_vals = reinterpret_cast<double*>(rt->mm_malloc_global(nnz * sizeof(double)));
  uint64_t* mat1_index = reinterpret_cast<uint64_t*>(rt->mm_malloc_global(2 * h * sizeof(uint64_t)));
  uint64_t* part_array = reinterpret_cast<uint64_t*>(rt->mm_malloc_global(2 * num_workers * PARTITION_PER_LANE * sizeof(uint64_t)));
#else
  uint64_t* mat1_cols = reinterpret_cast<uint64_t*>(rt->mm_malloc(nnz * sizeof(uint64_t)));
  double* mat1_vals = reinterpret_cast<double*>(rt->mm_malloc(nnz * sizeof(double)));
  uint64_t* mat1_index = reinterpret_cast<uint64_t*>(rt->mm_malloc(2 * h * sizeof(uint64_t)));
  uint64_t* part_array = reinterpret_cast<uint64_t*>(rt->mm_malloc(2 * num_workers * PARTITION_PER_LANE * sizeof(uint64_t)));
#endif

  mat_file.read(reinterpret_cast<char*>(mat1_index), 2 * h * sizeof(uint64_t));
  printf("mat1_index[0] = %ld\n", mat1_index[0]);

  mat_file.read(reinterpret_cast<char*>(mat1_cols), nnz * sizeof(uint64_t));
  printf("mat1_cols[0] = %ld\n", mat1_cols[0]);

  mat_file.read(reinterpret_cast<char*>(mat1_vals), nnz * sizeof(double));
  printf("mat1_vals[0] = %lf\n", mat1_vals[0]);

  printf("Address of Matrix 1: %lx\n", (uint64_t) mat1_vals);

  printf("Building Matrix 2\n");

#ifdef GEM5_MODE
  double* mat2 = reinterpret_cast<double*>(rt->mm_malloc_global(w * sizeof(double)));
#else
  double* mat2 = reinterpret_cast<double*>(rt->mm_malloc(w * sizeof(double)));
#endif

#ifndef GEM5_MODE
  for(int i = 0; i < w; i ++){
    mat2[i] = 1.0;
  }
#endif
  printf("Address of Matrix 2: %lx\n", (uint64_t) mat2);

#ifdef GEM5_MODE
  double* res_mat = reinterpret_cast<double*>(rt->mm_malloc_global(h * sizeof(double)));
#else
  double* res_mat = reinterpret_cast<double*>(rt->mm_malloc(h * sizeof(double)));
#endif

  printf("Results will be stored at address %lx\n", (uint64_t) res_mat);
  printf("Running SpMV on %ld lanes\n", num_workers);
#ifdef GEM5_MODE
  m5_switch_cpu();
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

#ifdef GEM5_MODE
  m5_dump_reset_stats(0,0);
#endif


  UpDown::event_t evnt_ops(spmv_msr_exe::matvecmul_master__mv_init /*Event Label*/,
                            nwid,
                            UpDown::CREATE_THREAD /*Thread ID*/,
                            &ops /*Operands*/);
  rt->send_event(evnt_ops);
  printf("First event sent\n");

  rt->start_exec(nwid);
  printf("Waiting for first loop to terminate\n");

  rt->test_wait_addr(nwid, TOP_FLAG_OFFSET, 1);
  printf("First event terminates.\n");
  
#ifdef GEM5_MODE
  m5_dump_reset_stats(0,0);
#endif

#ifndef GEM5_MODE
  printf("Printing Output Matrix\n");
  for(int i = 0; i < h; i ++){
    printf("%lf\t", res_mat[i]);
    printf("\n");
  }
  double* gold_mat = (double*) malloc(h * sizeof(double));

  printf("Printing Gold Matrix\n");
  for(int i = 0; i < h; i++){
    double val = 0.0;
    for(int k = 0; k < (mat1_index[i * 2 + 1] - mat1_index[i * 2]) / 8; k++){
      uint64_t prev_idx = mat1_index[i * 2] / 8;
      val += mat1_vals[k + prev_idx] * mat2[mat1_cols[k + prev_idx]];
    }
    gold_mat[i] = val;

    printf("%lf\t", gold_mat[i]);
    printf("\n");
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
  

#ifdef GEM5_MODE
  m5_dump_reset_stats(0,0);
#endif

  return 0;
  
}

int main(int argc, char* argv[]) {
  
  UpDown::UDRuntime_t* rt = gen_runtime();

  std::string path = argv[1];
  uint64_t num_workers = std::stol(argv[2]);

  return test_exec_bin(rt, path, num_workers);

}
