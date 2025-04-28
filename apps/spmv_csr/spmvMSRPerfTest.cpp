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

#define USAGE "USAGE: ./spmvMSRPerfTest <mat1_height> <mat1_width> <nonzeros_per_row> <num_workers>"

#define NUM_LANE_PER_UD 64
#define NUM_UD_PER_CLUSTER 4
#define NUM_CLUSTER_PER_NODE 8
#define PARTITION_PER_LANE 4 



UpDown::UDRuntime_t* gen_runtime(){
  UpDown::ud_machine_t machine;
  machine.NumNodes = 1;
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

int test_exec(UpDown::UDRuntime_t* rt, uint64_t MAT1_HEIGHT, uint64_t MAT1_WIDTH, uint64_t nnz, uint64_t num_workers){

  printf("=== Base Addresses ===\n");
  rt->dumpBaseAddrs();
  printf("\n=== Machine Config ===\n");
  rt->dumpMachineConfig();




  double lower_bound = - 1.0;
  double upper_bound = 1.0;
  std::uniform_real_distribution<double> unif(lower_bound,upper_bound);
  std::default_random_engine re;

  printf("Building Matrix 1\n");
#ifdef GEM5_MODE
  uint64_t* mat1_cols = reinterpret_cast<uint64_t*>(rt->mm_malloc_global(MAT1_HEIGHT * MAT1_WIDTH * sizeof(double)));
  double* mat1_vals = reinterpret_cast<double*>(rt->mm_malloc_global(MAT1_HEIGHT * MAT1_WIDTH * sizeof(double)));
  uint64_t* mat1_index = reinterpret_cast<uint64_t*>(rt->mm_malloc_global((MAT1_HEIGHT) * 2 * sizeof(double)));
  uint64_t* part_array = reinterpret_cast<uint64_t*>(rt->mm_malloc_global(2 * num_workers * PARTITION_PER_LANE * sizeof(uint64_t)));
#else
  uint64_t* mat1_cols = reinterpret_cast<uint64_t*>(rt->mm_malloc(MAT1_HEIGHT * MAT1_WIDTH * sizeof(double)));
  double* mat1_vals = reinterpret_cast<double*>(rt->mm_malloc(MAT1_HEIGHT * MAT1_WIDTH * sizeof(double)));
  uint64_t* mat1_index = reinterpret_cast<uint64_t*>(rt->mm_malloc((MAT1_HEIGHT) * 2 * sizeof(double)));
  uint64_t* part_array = reinterpret_cast<uint64_t*>(rt->mm_malloc(2 * num_workers * PARTITION_PER_LANE * sizeof(uint64_t)));
#endif

  for(int i = 0; i < MAT1_HEIGHT; i ++){
    for(int j = 0; j < nnz; j ++){
      mat1_vals[i * nnz + j] = unif(re);
      mat1_cols[i * nnz + j] = rand() % MAT1_WIDTH;
#ifndef GEM5_MODE
      printf("(%lf, %ld)\t", mat1_vals[i * nnz + j], mat1_cols[i * nnz + j]);
#endif
    }
    mat1_index[i * 2] = nnz * i * 8;
    mat1_index[i * 2 + 1] = nnz * (i + 1) * 8;
#ifndef GEM5_MODE
    printf("\n");
#endif
  }
  printf("Address of Matrix 1: %lx\n", (uint64_t) mat1_vals);

  printf("Building Matrix 2\n");

#ifdef GEM5_MODE
  double* mat2 = reinterpret_cast<double*>(rt->mm_malloc_global(MAT1_WIDTH * sizeof(double)));
#else
  double* mat2 = reinterpret_cast<double*>(rt->mm_malloc(MAT1_WIDTH * sizeof(double)));
#endif

  for(int i = 0; i < MAT1_WIDTH; i ++){
    mat2[i] = unif(re);
#ifndef GEM5_MODE
    printf("%lf\t", mat2[i]);
    printf("\n");
#endif
  }
  printf("Address of Matrix 2: %lx\n", (uint64_t) mat2);

#ifdef GEM5_MODE
  double* res_mat = reinterpret_cast<double*>(rt->mm_malloc_global(MAT1_HEIGHT * sizeof(double)));
#else
  double* res_mat = reinterpret_cast<double*>(rt->mm_malloc(MAT1_HEIGHT * sizeof(double)));
#endif

  printf("Results will be stored at address %lx\n", (uint64_t) res_mat);
  printf("Running SpMV on %ld lanes\n", num_workers);

#ifdef GEM5_MODE
  m5_switch_cpu();
#endif
  
  UpDown::word_t ops_data[8];
  UpDown::operands_t ops(8, ops_data);
  ops.set_operand(0, (uint64_t) mat1_index);
  ops.set_operand(1, (uint64_t) MAT1_HEIGHT);
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
  for(int i = 0; i < MAT1_HEIGHT; i ++){
    printf("%lf\t", res_mat[i]);
    printf("\n");
  }
#endif

  double* gold_mat = (double*) malloc(MAT1_HEIGHT * sizeof(double));

  printf("Printing Gold Matrix\n");
  for(int i = 0; i < MAT1_HEIGHT; i++){
    double val = 0.0;
    for(int k = 0; k < (mat1_index[i * 2 + 1] - mat1_index[i * 2]) / 8; k++){
      uint64_t curr_idx = k + mat1_index[i * 2] / 8;
      val += mat1_vals[curr_idx] * mat2[mat1_cols[curr_idx]];
    }
    gold_mat[i] = val;

#ifndef GEM5_MODE
    printf("%lf\t", gold_mat[i]);
    printf("\n");
#endif
  }

  for(int i = 0; i < MAT1_HEIGHT; i++){
    int idx = i;
    if(gold_mat[idx] - res_mat[idx] > 0.001 || gold_mat[idx] - res_mat[idx] < -0.001){
      printf("TEST FAILED AT POS %d\n", idx);
      return 1;
    }
  }
  printf("TEST PASSED\n");
  
  

#ifdef GEM5_MODE
  m5_dump_reset_stats(0,0);
#endif

  return 0;
  
}

int main(int argc, char* argv[]) {
  
  UpDown::UDRuntime_t* rt = gen_runtime();

  uint64_t MAT1_HEIGHT = atoll(argv[1]);
  uint64_t MAT1_WIDTH = atoll(argv[2]);
  uint64_t nnz = atoll(argv[3]);
  uint64_t num_workers = atoll(argv[4]);

  return test_exec(rt, MAT1_HEIGHT, MAT1_WIDTH, nnz, num_workers);

}
