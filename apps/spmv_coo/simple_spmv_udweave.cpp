#include "simupdown.h"
#include "Snap.h"

#include <cstdio>
#include <cstdlib>
#include <iostream>
#include <chrono>
#include <vector>

// #define DEBUG
#define GEM5
#ifdef GEM5_MODE
 #include <gem5/m5ops.h>
#endif

//#define USAGE "USAGE: ./simple_spmv_udweave <sample_file> <numlanes> <numthreadsperlane> "
#define USAGE "USAGE: ./simple_spmv_udweave <sample_file>"


// we are going to call this event
// spmv::init
// which is eventid 0 
// long* nonzeros, double* x, double* y, int nnz, int _ysize, int blocksize
// 
void spmv_upstream(
  UpDown:: UDRuntime_t *rt, void* spdata, void* outdata, void* vdata, uint64_t num_rows, uint64_t num_cols, uint64_t num_entries
) { 

  UpDown::word_t ops_data[5];
  UpDown::operands_t ops(5, ops_data);
  UpDown::networkid_t nwid(0, 0);

  // setup the termination condition on top before calling to avoid a race condition
  // TOP will check that this location becomes one when things are done. 
  uint64_t tmp=0;
  rt->t2ud_memcpy(&tmp, // pointer on top 
    sizeof(uint64_t), // sizeof transfer in bytes
   nwid, // where it's going 
   0 // offset into local scratchpad
  ); 
    
  // Operand 0 : address of vertices list g_v
  // Operand 1    : number of lanes
  // Operand 2    : number of vertices/nodes
  // Operand 3    : worker id
  // Operand 4    : number of threads
  ops.set_operand(0, (UpDown::word_t)spdata);
  ops.set_operand(1, (UpDown::word_t)outdata);
  ops.set_operand(2, (UpDown::word_t)vdata);
  ops.set_operand(3, (uint64_t) num_entries);
  ops.set_operand(4, (uint64_t) num_cols);
  ops.set_operand(5, 0x200);

  UpDown::event_t event_ops(0 /*Event Label*/,
                            nwid,
                            UpDown::CREATE_THREAD /*Thread ID*/,
                            &ops /*Operands*/);
  rt->send_event(event_ops);

  rt->start_exec(nwid);

  // keep testing the locations 
  rt->test_wait_addr(nwid, // network id
    0,  // offset into scrttchpad 
    1  // value to wait for! - the default is one, but David likes being explicit. 
  ); 

  // need to improve this output...
  double* result =  (double*)outdata; 
  for (uint64_t i=0; i<num_rows; ++i) {
    printf("%lf\n", result[i]);
  }
  
}


int main(int argc, char* argv[]) {
  // Set up machine parameters
  UpDown::ud_machine_t machine;
  machine.NumLanes = 64;

#ifdef GEM5_MODE
  UpDown::UDRuntime_t *spmv_rt = new UpDown::UDRuntime_t(machine);
#else
  // Default configurations runtime
  UpDown::SimUDRuntime_t *spmv_rt = new UpDown::SimUDRuntime_t(machine,
  "spmv",  // program file (without pythone extension)
  "EFA_spmv", // program function (the function with the code in the python file)
  "./", // simulation dir
  UpDown::EmulatorLogLevel::NONE // we don't see output with ::NONE, 
  // other options are ::FULL_TRACE, ::STAGE_TRACE, ::PROGRESS_TRACE
  );
#endif

  printf("=== Base Addresses ===\n");
  spmv_rt->dumpBaseAddrs();
  printf("\n=== Machine Config ===\n");
  spmv_rt->dumpMachineConfig();

  char* filename;
  uint32_t num_iterations = 1;
  if (argc < 4) {
    printf("Insufficient Input Params\n");
    printf("%s\n", USAGE);
    exit(1);
  }
  filename = argv[1];
  //uint64_t num_lanes = atoi(argv[2]);
  uint64_t num_lanes = 64;
  // uint64_t num_threads = atoi(argv[3]) * num_lanes;
  uint64_t num_threads = 1; 

  printf("Num Lanes:%d\n", num_lanes);
  printf("Num Threads:%d\n", num_threads);
  printf("Num Iterations:%d\n", num_iterations);
  FILE* in_file = fopen(filename, "rb");
  if (!in_file) {
        printf("Error when openning file, exiting.\n");
        exit(EXIT_FAILURE);
  }
  uint64_t num_rows=0, num_cols=0, num_entries=0;
  fseek(in_file, 0, SEEK_SET);
  fread(&num_rows, sizeof(num_rows), 1, in_file);
  fread(&num_cols, sizeof(num_cols), 1, in_file);
  fread(&num_entries, sizeof(num_entries), 1, in_file);

  printf("Graph of Matrix :%d %d %d\n", num_rows, num_cols, num_entries);

  printf("Allocating memory for spmv...\n");

  // This allocates memory that we can use both from C++ and on the UpDown. 
  // Allocate the array where the top and updown can see it:
  
  void* sparsematrix_data = (spmv_rt->mm_malloc(num_entries * (sizeof(uint64_t)*2 + sizeof(double))));
  void* vector_data = (spmv_rt->mm_malloc(num_cols*(sizeof(double))));
  void* result_data = (spmv_rt->mm_malloc(num_rows*(sizeof(double))));

  fread(sparsematrix_data,  (sizeof(uint64_t)*2 + sizeof(double)), num_entries, in_file);
  fread(vector_data,  (sizeof(double)), num_cols, in_file);

  printf("Data allocation done! Will do SPMV now\n");


#ifdef GEM5_MODE
  m5_switch_cpu();

  // Dumps a set of statistics per iteration of Page Rank
  printf("Run spmv updown.\n");
  m5_dump_reset_stats(0,0);

  spmv_upstream(spmv_rt, sparsematrix_data, result_data, vector_data, num_rows, num_cols, num_entries); 
  
#else
  spmv_upstream(spmv_rt, sparsematrix_data, result_data, vector_data, num_rows, num_cols, num_entries); 
#endif

  printf("Pagerank done.\n");
}
