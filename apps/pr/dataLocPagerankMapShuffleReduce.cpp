#include "PagerankMsrEFA.hpp"
// #include "simupdown.h"

#include <cmath>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cmath>
#include <string>

#ifdef BASIM
#include <basimupdown.h>
#endif

#ifdef GEM5_MODE
 #include <gem5/m5ops.h>
#endif

#define DEBUG
// #define DEBUG_GRAPH

#define USAGE "USAGE: ./pagerankFastLoadMapShuffleReduce <graph_file_path> <num_nodes> <num_uds> <partition_per_lane> (<output_file_path>)\n\
  graph_file_path: \tpath to the graph file.\n\
  num_nodes: \tnumber of nodes, minimum is 1.\n\
  num_uds: \tnumber of UDs per node, default = 32 if greater than 1 node is used.\n\
  partition_per_lane: \tnumber of partitions per lane.\n"

#define NUM_LANE_PER_UD 64
#define NUM_UD_PER_CLUSTER 4
#define NUM_CLUSTER_PER_NODE 8
#define TOP_FLAG_OFFSET 0

#ifdef GEM5_MODE
#define FLAG_ADDR 0x7FFF0000
volatile uint64_t *flags = (uint64_t *)FLAG_ADDR;
#endif

// #define PART_PARM 1

struct Vertex {
  uint64_t id;
  uint64_t deg;
  uint64_t *neigh;
  double val;
};

struct Value{
  // uint64_t id;
  double val;
};

struct Iterator {
  Vertex* begin;
  Vertex* end;
};

#ifdef GEM5_MODE
void switch_cpu_barrier(uint64_t core, uint64_t num_cpus, uint64_t init_offset) {

  printf("GEM5_MODE, core:%ld swithing cpus\n", core);
  printf("flags[%ld] = %ld\n", core + init_offset, flags[core + init_offset]);
  flags[core + init_offset] = 1;
  while (true) {
    bool all_ready = true;
    for (uint64_t i = init_offset; i < num_cpus + init_offset; i++) {
      // if(flags[i]==0){
      //     all_ready = false;
      //     break;
      // }
      all_ready &= (flags[i] == 1);
    }
    if (all_ready)
      break;
  }
  printf("All cores are ready\n");
  for (uint64_t i = init_offset; i < num_cpus + init_offset; i++) {
    printf("flags[%ld] = %ld\n", i, flags[i]);
  }
}
#endif

int main(int argc, char *argv[]) {

  if (argc < 5) {
    printf("Insufficient Input Params\n");
    printf("%s\n", USAGE);
    exit(1);
  }
  
  std::string filename (argv[1]);
  uint64_t num_nodes = atoi(argv[2]);
  uint64_t num_uds_per_node = NUM_UD_PER_CLUSTER * NUM_CLUSTER_PER_NODE;
  uint64_t num_lanes_per_ud = NUM_LANE_PER_UD;
  int PART_PARM = atoi(argv[4]);

  if (num_nodes < 2) {
    num_nodes = 1;
    num_uds_per_node = atoi(argv[3]);
  } 

  int core_id = atoi(argv[5]);

  printf("Test configurations: \n\tnum_nodes = %ld, \n\tnum_uds_per_node = "
         "%ld, \n\tnum_lanes_per_ud = %ld, ",
         num_nodes, num_uds_per_node, num_lanes_per_ud);

  uint64_t num_lanes = num_nodes * num_uds_per_node * num_lanes_per_ud;

  printf("\ttotal_num_lanes = %ld\n", num_lanes);

#ifdef GEM5_MODE
  if (core_id != 0) {
    m5_switch_cpu();
    switch_cpu_barrier(core_id, num_nodes, 0);
    return 0;
  } else {
#endif

    // Set up machine parameters
    UpDown::ud_machine_t machine;
    machine.NumLanes = num_lanes_per_ud;
    machine.NumUDs = std::min((int)num_uds_per_node, NUM_UD_PER_CLUSTER);
    machine.NumStacks =
        std::ceil((double)num_uds_per_node / NUM_UD_PER_CLUSTER);
    machine.NumNodes = num_nodes;
    machine.LocalMemAddrMode = 1;

#ifdef GEM5_MODE
  UpDown::UDRuntime_t *pagerank_rt = new UpDown::UDRuntime_t(machine);
#elif BASIM
  UpDown::BASimUDRuntime_t* pagerank_rt = new UpDown::BASimUDRuntime_t(machine, "PagerankMsrEFA.bin", 0, 1);
#else
  // Init runtime
  UpDown::SimUDRuntime_t *pagerank_rt =
      new UpDown::SimUDRuntime_t(machine, "GenDataLocMSRPagerankEFA",
                                 "GeneratePageRankMapShuffleReduceEFA", "./",
                                 UpDown::EmulatorLogLevel::NONE);
#endif

#ifdef DEBUG
    printf("=== Base Addresses ===\n");
    pagerank_rt->dumpBaseAddrs();
    printf("\n=== Machine Config ===\n");
    pagerank_rt->dumpMachineConfig();
#endif

  
  FILE* in_file_gv = fopen((filename + "_gv.bin").c_str(), "rb");
  if (!in_file_gv) {
    printf("Error when openning file %s, exiting.\n", (filename + "_gv.bin").c_str());
    exit(EXIT_FAILURE);
  }

  FILE* in_file_nl = fopen((filename + "_nl.bin").c_str(), "rb");
  if (!in_file_nl) {
    printf("Error when openning file %s, exiting.\n", (filename + "_nl.bin").c_str());
    exit(EXIT_FAILURE);
  }

  uint64_t num_vertices, num_edges;
  std::size_t n;

  fseek(in_file_gv, 0, SEEK_SET);
  n = fread(&num_vertices, sizeof(num_vertices), 1, in_file_gv);
  n = fread(&num_edges, sizeof(num_edges), 1, in_file_nl);
  printf("Input graph: Number of Vertices = %ld\t Number of edges = %ld\n", num_vertices, num_edges);
  fflush(stdout);

    // Allocate the array where the top and updown can see it:
    Vertex *g_v_bin = reinterpret_cast<Vertex *>(
        pagerank_rt->mm_malloc_global(num_vertices * sizeof(Vertex)));
    Value *g_v_val = reinterpret_cast<Value *>(
        pagerank_rt->mm_malloc_global(num_vertices * sizeof(Value)));

  uint64_t* nlist_bin = reinterpret_cast<uint64_t *>(pagerank_rt->mm_malloc_global(num_edges * sizeof(uint64_t)));

  n = fread(g_v_bin, sizeof(Vertex), num_vertices, in_file_gv); // read in all vertices 
  n = fread(nlist_bin, sizeof(uint64_t), num_edges, in_file_nl); // read in all vertices
  
  // UpDown::word_t INPUT_KVMAP_SIZE = 1 << 14;
  uint64_t num_partitions = num_lanes * PART_PARM;
  uint64_t num_pairs_per_part = ceil((num_vertices + 0.0) / num_partitions);
  printf("Number of partitions per lane = %d\t Number of partitions = %ld\t Number of vertices per partition = %ld\n", PART_PARM, num_partitions, num_pairs_per_part);

  Iterator *partitions = reinterpret_cast<Iterator *>(
        pagerank_rt->mm_malloc_global((num_partitions) * sizeof(Iterator)));

#ifdef DEBUG
    printf("Vertax array = %p\n", g_v_bin);
    printf("Value array = %p\n", g_v_val);
    printf("Edge array = %p\n", nlist_bin);
#endif

    // calculate size of neighbour list and assign values to each member value
    printf("Build the graph now\n");

  uint64_t curr_base = 0;
  for(int i = 0; i < num_vertices; i++) {
    g_v_bin[i].neigh = (uint64_t *) ((uint64_t) nlist_bin + curr_base * sizeof(uint64_t));

    g_v_val[i].val  = 0.0;

#ifdef DEBUG_GRAPH
    printf("Vertex %d (addr %p) - deg %ld, neigh_list %p\n", i, (g_v_bin + i), g_v_bin[i].deg, (nlist_bin + curr_base));
#endif
    curr_base += g_v_bin[i].deg;
  }

#ifdef DEBUG_GRAPH
    printf("-------------------\nparitions = %p\n", partitions);
#endif
    // Initialize partitions
    int offset = 0;
    for (int i = 0; i < num_partitions; i++) {
      partitions[i].begin = g_v_bin + offset;
      offset = std::min((i+1) * num_pairs_per_part, num_vertices);
      partitions[i].end = g_v_bin + offset;
#ifdef DEBUG_GRAPH
      printf("Partition %d: pair_id=%d, key=%ld neighbors=%p "
             "base_pair_addr=%p, part_entry_addr=%p\n",
             i, offset, partitions[i].begin->id, partitions[i].begin->neigh, partitions[i],
             partitions + i);
#endif
    }
    
#ifdef DEBUG_GRAPH
    printf("Partition %ld: pair_id=%ld base_pair_addr=%p, part_entry_addr=%p\n",
           num_partitions, num_partitions * num_pairs_per_part,
           partitions[num_partitions], partitions + num_partitions);
#endif
    printf("Finish building the graph, cpu id = %d.\n", core_id);
    fflush(stdout);

#ifdef GEM5_MODE
  m5_switch_cpu();
  /* operands
    X8: Pointer to partitions (64-bit DRAM address)
    X9: Number of lanes
    X10: Number of partitions per lane
    X11: Pointer to inKVSet (64-bit DRAM address)
    X12: Input KVSet length
    X13: Pointer to outKVSet (64-bit DRAM address)
    X14: Output KVSet length
    X15: Top flag offset in the scratchpad (in Bytes)
  */
  UpDown::operands_t ops(7);
  ops.set_operand(0, (uint64_t) partitions);
  ops.set_operand(1, (uint64_t) PART_PARM);
  ops.set_operand(2, (uint64_t) num_lanes);
  ops.set_operand(3, (uint64_t) g_v_bin);
  ops.set_operand(4, (uint64_t) num_vertices);
  ops.set_operand(5, (uint64_t) g_v_val);
  ops.set_operand(6, (uint64_t) num_vertices);

    UpDown::networkid_t nwid(0, false, 0);

  UpDown::event_t evnt_ops( PagerankMsrEFA::updown_init/*Event Label*/,
                            nwid,
                            UpDown::CREATE_THREAD /*Thread ID*/,
                            &ops /*Operands*/);

  // Init top flag to 0
  uint64_t val = 0;
  pagerank_rt->t2ud_memcpy(&val,
                  sizeof(uint64_t),
                  nwid,
                  TOP_FLAG_OFFSET /*Offset*/);

  pagerank_rt->send_event(evnt_ops);

#ifdef DEBUG
  printf("Event sent to updown lane %d.\n", 0);
  fflush(stdout);
#endif

  m5_reset_stats(0,0);
  pagerank_rt->start_exec(nwid);
  printf("Waiting for terminate\n");

  pagerank_rt->test_wait_addr(nwid, TOP_FLAG_OFFSET, 1);

    m5_dump_reset_stats(0, 0);

    printf("UpDown checking terminates.\n");

#ifdef GEM5_MODE
    switch_cpu_barrier(core_id, num_nodes, 0);
#endif
  delete pagerank_rt;

  }

#else

  /* operands
    X8: Pointer to partitions (64-bit DRAM address)
    X9: Number of lanes
    X10: Number of partitions per lane
    X11: Pointer to inKVSet (64-bit DRAM address)
    X12: Input KVSet length
    X13: Pointer to outKVSet (64-bit DRAM address)
    X14: Output KVSet length
    X15: Top flag offset in the scratchpad (in Bytes)
  */
  UpDown::operands_t ops(7);
  ops.set_operand(0, (uint64_t) partitions);
  ops.set_operand(1, (uint64_t) PART_PARM);
  ops.set_operand(2, (uint64_t) num_lanes);
  ops.set_operand(3, (uint64_t) g_v_bin);
  ops.set_operand(4, (uint64_t) num_vertices);
  ops.set_operand(5, (uint64_t) g_v_val);
  ops.set_operand(6, (uint64_t) num_vertices);

  UpDown::networkid_t nwid(0, false, 0);

  UpDown::event_t evnt_ops( PagerankMsrEFA::updown_init/*Event Label*/,
                            nwid,
                            UpDown::CREATE_THREAD /*Thread ID*/,
                            &ops /*Operands*/);

  // Init top flag to 0
  uint64_t val = 0;
  pagerank_rt->ud2t_memcpy(&val,
                  sizeof(uint64_t),
                  nwid,
                  TOP_FLAG_OFFSET /*Offset*/);

  pagerank_rt->send_event(evnt_ops);

  pagerank_rt->start_exec(nwid);

  pagerank_rt->test_wait_addr(nwid, TOP_FLAG_OFFSET, 1);

  delete pagerank_rt;
#endif
  
#ifdef VALIDATE_RESULT
  const char* output_file;
  if (argc < 6) {
    output_file = "output/pagerank_output.txt";
  } else {
    output_file = argv[5];
  }
  std::ofstream output(output_file);
#ifdef DEBUG
  printf("-------------------\nUpDown program termiantes. Verify the result output kv set.\n");
#endif
  for (int i = 0; i < num_vertices; i++) {
#ifdef DEBUG
    printf("Output pagerank value array %d: key=%ld value=%f DRAM_addr=%p\n", i, g_v_val[i].id, g_v_val[i].val, g_v_val + i);
#endif
    output << i << " " << g_v_val[i].val << std::endl;
  }
#endif

  printf("UDKVMSR PageRank program finishes.\n");

  return 0;
}