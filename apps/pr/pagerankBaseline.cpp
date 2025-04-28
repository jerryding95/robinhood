#include <cstdio>
#include <cstdlib>
#include <fstream>
#include <iostream>
#include <string>
#include <cstdint>

#ifdef GEM5_MODE
 #include <gem5/m5ops.h>
#endif

#define VALIDATE_RESULT
// #define DEBUG
// #define DEBUG_GRAPH
// #define DEBUG_PROC

#define USAGE "USAGE: ./pagerankBaseline <graph_file_path> (<output_file_path>)\n\
  graph_file_path: \tpath to the graph file.\n"

struct Vertex{
  uint64_t id;
  uint64_t deg;
  uint64_t* neigh;
  double val;
};

struct Value{
  uint64_t id;
  double val = 0;
};

void pagerank_top(Vertex *g_v, Value *val_array, int num_vertices){
#ifdef GEM5_MODE
  m5_switch_cpu();
  m5_reset_stats(0,0);
#endif

  int vid = 0;
  uint64_t deg, uid;
  double old_val, new_val;
  uint64_t* edge_list;
  while (vid < num_vertices) {
    deg = g_v[vid].deg;
    old_val = g_v[vid].val;

    if (deg == 0) {
      vid ++;
      continue;
    }
    // printf("vid: %d deg: %d, value: %d\n", vid, deg, g_v[vid].ival);
    edge_list = g_v[vid].neigh;
    new_val = old_val / deg;
    for (int j = 0; j < deg; j++) {
      uid = edge_list[j];
      val_array[uid].val += new_val;
      // printf("uid: %d new_value: %d", vid, g_v[uid].nval);
    }
    vid ++;
  }
  
#ifdef GEM5_MODE
  m5_dump_reset_stats(0,0);
#endif
}

int main(int argc, char* argv[]) {

  if (argc < 2) {
    printf("Insufficient Input Params\n");
    printf("%s\n", USAGE);
    exit(1);
  }
  
  std::string filename (argv[1]);
#ifdef VALIDATE_RESULT
  char *output_file (argv[2]);
#endif
  
  FILE* in_file_gv = fopen((filename + "_gv.bin").c_str(), "rb");
  if (!in_file_gv) {
    printf("Error when openning file %s, exiting.\n", (filename + "nl.bin").c_str());
    exit(EXIT_FAILURE);
  }

  FILE* in_file_nl = fopen((filename + "_nl.bin").c_str(), "rb");
  if (!in_file_nl) {
    printf("Error when openning file %s, exiting.\n", (filename + "nl.bin").c_str());
    exit(EXIT_FAILURE);
  }

  uint64_t num_vertices, num_edges;

  fseek(in_file_gv, 0, SEEK_SET);
  fread(&num_vertices, sizeof(num_vertices), 1, in_file_gv);
  fread(&num_edges, sizeof(num_edges), 1, in_file_nl);
  printf("Input graph: Number of Vertices = %ld\t Number of edges = %ld\n", num_vertices, num_edges);

  // Allocate the array where the top and updown can see it:
  Vertex* g_v_bin = reinterpret_cast<Vertex *>(malloc(num_vertices * sizeof(Vertex)));
  Value* g_v_val  = reinterpret_cast<Value *>(malloc(num_vertices * sizeof(Value)));

  uint64_t* nlist_bin = reinterpret_cast<uint64_t *>(malloc(num_edges * sizeof(uint64_t)));

  fread(g_v_bin, sizeof(Vertex), num_vertices, in_file_gv); // read in all vertices 
  fread(nlist_bin, sizeof(uint64_t), num_edges, in_file_nl); // read in all vertices
  
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

  printf("Finish building the graph, start running PageRank.\n");
  fflush(stdout);

  pagerank_top(g_v_bin, g_v_val, num_vertices);

#ifdef VALIDATE_RESULT
  std::ofstream output(output_file);
#ifdef DEBUG
  printf("-------------------\nCPU baseline program termiantes. Verify the result output kv set.\n");
#endif
  for (int i = 0; i < num_vertices; i++) {
#ifdef DEBUG
    printf("Output pagerank value array %d: key=%ld value=%f DRAM_addr=%p\n", i, g_v_val[i].id, g_v_val[i].val, g_v_val + i);
#endif
    output << i << " " << g_v_val[i].val << std::endl;
  }
#endif

  printf("PageRank baseline program finishes.\n");

  return 0;
}
