#include "simupdown.h"

#include <cstdio>
#include <cstdlib>
#include <iostream>
#include <cmath>

#ifdef GEM5_MODE
 #include <gem5/m5ops.h>
#endif

// #define DEBUG
// #define DEBUG_GRAPH

#define USAGE "USAGE: ./pagerankMapShuffleReduce <graph_file_path> <num_nodes> <num_uds> <parition_parm>\n\
  graph_file_path: \tpath to the graph file.\n\
  num_nodes: \tnumber of nodes, minimum is 1.\n\
  num_uds: \tnumber of UDs per node, default = 32 if greater than 1 node is used.\n\
  partition_parm: \tthe partition parameter, default = 1.\n"

#define NUM_LANE_PER_UD 64
#define NUM_UD_PER_CLUSTER 4
#define NUM_CLUSTER_PER_NODE 8
#define TOP_FLAG_OFFSET 16

// #define PART_PARM 1

struct Vertex{
  uint64_t id;
  uint64_t deg;
  uint64_t* neigh;
  double val;
};

struct Value{
  uint64_t id;
  double val;
};

int main(int argc, char* argv[]) {

  if (argc < 4) {
    printf("Insufficient Input Params\n");
    printf("%s\n", USAGE);
    exit(1);
  }
  
  char* filename = argv[1];
  uint64_t num_nodes = atoi(argv[2]);
  uint64_t num_uds_per_node = NUM_UD_PER_CLUSTER * NUM_CLUSTER_PER_NODE;
  uint64_t num_lanes_per_ud = NUM_LANE_PER_UD;
  int PART_PARM = 1;

  if (num_nodes < 2) {
    num_nodes = 1;
    num_uds_per_node = atoi(argv[3]);
  } 

  PART_PARM = atoi(argv[4]);
  printf("argv[1] = %s argv[2] = %s argv[3] = %s argv[4] = %s\n", argv[1], argv[2], argv[3], argv[4]);

  printf("Test configurations: \n\tnum_nodes = %ld, \n\tnum_uds_per_node = %ld, \n\tnum_lanes_per_ud = %ld, ", num_nodes, num_uds_per_node, num_lanes_per_ud);

  uint64_t num_lanes = num_nodes * num_uds_per_node * num_lanes_per_ud;

  printf("\ttotal_num_lanes = %ld\n", num_lanes);

  // Set up machine parameters
  UpDown::ud_machine_t machine;
  machine.NumLanes = num_lanes_per_ud;
  machine.NumUDs = std::min((int)num_uds_per_node, NUM_UD_PER_CLUSTER);
  machine.NumStacks = std::ceil((double)num_uds_per_node / NUM_UD_PER_CLUSTER);
  machine.NumNodes = num_nodes;
  machine.LocalMemAddrMode = 1;


#ifdef GEM5_MODE
  UpDown::UDRuntime_t *pagerank_rt = new UpDown::UDRuntime_t(machine);
#else
  std::string program_name = "GeneratePageRankMapShuffleReduceEFA_" + std::to_string(PART_PARM) + "p";
  // Init runtime
  UpDown::SimUDRuntime_t *pagerank_rt = new UpDown::SimUDRuntime_t(machine,
  "GenMSRBalancedPagerankEFA", 
  program_name.c_str(),
  "./", 
  UpDown::EmulatorLogLevel::NONE);
#endif

#ifdef DEBUG
  printf("=== Base Addresses ===\n");
  pagerank_rt->dumpBaseAddrs();
  printf("\n=== Machine Config ===\n");
  pagerank_rt->dumpMachineConfig();
#endif

  
  FILE* in_file = fopen(filename, "rb");
  if (!in_file) {
        printf("Error when openning file, exiting.\n");
        exit(EXIT_FAILURE);
  }
  uint64_t num_vertices, num_edges;

  fseek(in_file, 0, SEEK_SET);
  fread(&num_vertices, sizeof(num_vertices), 1, in_file);
  fread(&num_edges, sizeof(num_edges), 1, in_file);
  printf("Input graph: Number of Vertices = %ld\t Number of edges = %ld\n", num_vertices, num_edges);

  // Allocate the array where the top and updown can see it:
  Vertex* g_v_bin = reinterpret_cast<Vertex *>(pagerank_rt->mm_malloc(num_vertices * sizeof(Vertex)));
  Value* g_v_val  = reinterpret_cast<Value *>(pagerank_rt->mm_malloc(num_vertices * sizeof(Value)));
  
  // UpDown::word_t INPUT_KVMAP_SIZE = 1 << 14;
  int num_partitions = num_lanes * PART_PARM;
  uint64_t num_pairs_per_part = ceil((num_vertices + 0.0) / num_partitions);
  printf("Number of lanes = %ld\t Number of partitions = %d\t Number of vertices per partition = %ld\n", num_lanes, num_partitions, num_pairs_per_part);

  Vertex** partitions = reinterpret_cast<Vertex**>(pagerank_rt->mm_malloc((num_partitions + 1) * sizeof(Vertex*)));

  uint64_t* nlist_bin = reinterpret_cast<uint64_t *>(pagerank_rt->mm_malloc(num_edges * sizeof(uint64_t)));

#ifdef DEBUG
  printf("Vertax array = %p\n", g_v_bin);
  printf("Value array = %p\n", g_v_val);
  printf("Edge array = %p\n", nlist_bin);
#endif

  // calculate size of neighbour list and assign values to each member value
  printf("Build the graph now\n");

  uint64_t curr_base = 0;
  for(int i = 0; i < num_vertices; i++) {
    uint64_t deg, srcid;
    fread(&deg, sizeof(deg),1, in_file);
    fread(&srcid, sizeof(srcid),1, in_file);
    g_v_bin[srcid].deg   = deg;
    g_v_bin[srcid].id    = srcid;
    g_v_bin[srcid].val   = 1.0 / deg;
    g_v_bin[srcid].neigh = (nlist_bin + curr_base);

    g_v_val[srcid].id    = srcid;
    g_v_val[srcid].val   = 0.0;

#ifdef DEBUG_GRAPH
    printf("Vertex %ld (addr %p) - deg %ld, neigh_list %p\n", srcid, (g_v_bin + srcid), deg, (nlist_bin + curr_base));
#endif

    for(int j = 0; j < deg; j++){
      uint64_t dstid;
      fread(&dstid, sizeof(dstid), 1, in_file);
      nlist_bin[curr_base+j] = dstid;
    }

    curr_base += deg;
  }

#ifdef DEBUG_GRAPH
  printf("-------------------\nparitions = %p\n", partitions);
#endif
  // Initialize partitions
  for (int i = 0; i < num_partitions; i++) {
    int offset = std::min(i * num_pairs_per_part, num_vertices);
    partitions[i] = g_v_bin + offset;
#ifdef DEBUG
    printf("Partition %d: pair_id=%d, key=%ld neighbors=%p base_pair_addr=%p, part_entry_addr=%p\n",
      i, offset, partitions[i]->id, partitions[i]->neigh, partitions[i], partitions + i);
#endif
  }
  partitions[num_partitions] = g_v_bin + num_vertices;
#ifdef DEBUG_GRAPH
  printf("Partition %d: pair_id=%ld base_pair_addr=%p, part_entry_addr=%p\n",
      num_partitions, num_partitions * num_pairs_per_part, partitions[num_partitions], partitions + num_partitions);
#endif
  printf("Finish building the graph, start running PageRank.\n");
  fflush(stdout);

#ifdef GEM5_MODE
  m5_switch_cpu();
  /* operands
    OB_0: Pointer to partitions (64-bit DRAM address)
    OB_1: Number of lanes
    OB_2: Pointer to inKVSet (64-bit DRAM address)
    OB_3: Pointer to outKVSet (64-bit DRAM address)
    OB_4: Top flag offset in the scratchpad (in Bytes)
  */
  UpDown::word_t ops_data[5];
  UpDown::operands_t ops(5, ops_data);
  ops.set_operand(0, (uint64_t) partitions);
  ops.set_operand(1, num_lanes);
  ops.set_operand(2, (uint64_t) g_v_bin);
  ops.set_operand(3, (uint64_t) g_v_val);
  ops.set_operand(4, TOP_FLAG_OFFSET);

  UpDown::networkid_t nwid(0, false, 0);

  UpDown::event_t evnt_ops(0 /*Event Label*/,
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

#ifdef DEBUG
  printf("Event sent to updown lane %d.\n", 0);
  fflush(stdout);
#endif

  m5_reset_stats(0,0);
  pagerank_rt->start_exec(nwid);
  printf("Waiting for terminate\n");

  pagerank_rt->test_wait_addr(nwid, TOP_FLAG_OFFSET, 1);

  m5_dump_reset_stats(0,0);

  printf("UpDown checking terminates.\n");

#else

  /* operands
    OB_0: Pointer to partitions (64-bit DRAM address)
    OB_1: Number of lanes
    OB_2: Pointer to inKVSet (64-bit DRAM address)
    OB_3: Pointer to outKVSet (64-bit DRAM address)
    OB_4: Top flag offset in the scratchpad (in Bytes)
  */
  UpDown::word_t ops_data[5];
  UpDown::operands_t ops(5, ops_data);
  ops.set_operand(0, (uint64_t) partitions);
  ops.set_operand(1, num_lanes);
  ops.set_operand(2, (uint64_t) g_v_bin);
  ops.set_operand(3, (uint64_t) g_v_val);
  ops.set_operand(4, TOP_FLAG_OFFSET);

  UpDown::networkid_t nwid(0, false, 0);

  UpDown::event_t evnt_ops(0 /*Event Label*/,
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

#ifdef DEBUG_PROC
  int ctr = 0; // Max pulling iteration, only used for debug
  uint64_t tmp;
  do {
    pagerank_rt->ud2t_memcpy(&tmp,
                    sizeof(uint64_t),
                    nwid,
                    TOP_FLAG_OFFSET /*Offset*/);
    ctr++;
  } while (tmp != 1 && ctr < 5);

#else
  pagerank_rt->test_wait_addr(nwid, TOP_FLAG_OFFSET, 1);
#endif

#endif

#ifdef DEBUG
  printf("-------------------\nUpDown program termiantes. Verify the result output kv set.\n");
  for (int i = 0; i < num_vertices; i++) {
    printf("Output pagerank value array %d: key=%ld value=%f DRAM_addr=%p\n", i, g_v_val[i].id, g_v_val[i].val, g_v_val + i);
  }
#endif

  delete pagerank_rt;
  printf("UDKVMSR PageRank program finishes.\n");

  return 0;
}
