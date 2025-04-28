//#include "stdafx.h"
#include "Snap.h"
#include <cstdio>
#include <cstdlib>
#include <algorithm>
#include <cmath>
#include <iostream>
#include <vector>
#include <map>
#include <omp.h>
#include <string>
//#define DEBUG
#define GAMMA 3
#define USAGE "USAGE: ./preprocess_pagerank <graph_file>"

typedef uint64_t* ptr;

/**
 * Simple graph vertex
*/
typedef struct vertex{
  uint64_t deg;
  uint64_t id;
  ptr neigh;
} vertex_t;

/**
 * Insert into an array at the right postiion
*/
void array_insert(uint64_t *narray, int pos, int sz, uint64_t val){
  int inserted=0;
  if(pos>(sz-1)){
    narray[pos]=val;
  }else{
    uint64_t temp = narray[pos];
    narray[pos]=val;
    for(int i=sz; i > pos+1; i--){
      narray[i]=narray[i-1];
    }
    narray[pos+1]=temp;
  }
}

/**
 * Sort an array of size arr_sz
*/
void sort_narray(uint64_t *narray, uint64_t arr_sz){
  for(int i=0; i<arr_sz; i++){
    for(int j=i; j<arr_sz;j++){
      if(narray[i]>narray[j]){
        uint64_t temp=narray[i];
        narray[i]=narray[j];
        narray[j]=temp;
      }
    }
  }
}

/**
 * Print two arrays in tandem
*/
void print_arrays(uint64_t* ordered_vertices, uint64_t* ordered_vertex_degrees, int num_nodes){
  printf("Nodes\n[ ");
  for(int i=0; i<num_nodes;i++){
    printf("%ld ", ordered_vertices[i]);
  }
  printf("]\nDegrees\n[ ");
  for(int i=0; i<num_nodes;i++){
    printf("%ld ", ordered_vertex_degrees[i]);
  }
  printf("]\n");
}


/**
 * Print 1D array
*/
void print_array_1D(uint64_t* arr, int sz){
  printf("\n[ ");
  for(int i=0; i<sz;i++){
    printf("%ld ", arr[i]);
  }
  printf("]\n");
}


int main(int argc, char* argv[]) {

  char* filename;
  int mode = 0; // 1 - TC adjlist_plus
  if(argc < 2){
        printf("Insufficient Input Params\n");
        printf("%s\n", USAGE);
        exit(1);
  }else{
        filename = argv[1];
  }

  std::cout << "Start the graph building\n" << std::endl;
  PUNGraph G = TSnap::LoadEdgeList<PUNGraph>(filename, 0, 1);
  uint64_t **adjlists; // Adjacency lists
  uint64_t* vertices;
  uint64_t* degrees;
  std::map<long,uint64_t> nodemap;
  printf("Graph Nodes added for size %d\n", G->GetNodes());
  uint64_t num_nodes=G->GetNodes();
  int k=0;
  for(TUNGraph::TNodeI NI = G->BegNI(); NI < G->EndNI(); NI++){
    nodemap[NI.GetId()]=k++;
  }
  adjlists = (uint64_t**)malloc(num_nodes*sizeof(uint64_t*));
  vertices = (uint64_t*)malloc(num_nodes*sizeof(uint64_t));
  degrees = (uint64_t*)malloc(num_nodes*sizeof(uint64_t));

  printf("Build the graph now\n");
  int data;
  struct vertex *g_v_bin = (struct vertex*)malloc(num_nodes*sizeof(struct vertex));
  int ranked=0;
  uint64_t neighbor_array_size=0;
  
  omp_lock_t adj_lock;
  omp_init_lock(&adj_lock);
  int i = 0;
  //#pragma omp parallel for
  for(TUNGraph::TNodeI NI = G->BegNI(); NI < G->EndNI(); NI++, ranked++, i++){
    vertices[ranked] = nodemap[NI.GetId()]; 
    degrees[ranked] = NI.GetDeg(); 
    uint64_t* adjlist_local = new uint64_t[NI.GetDeg()];
    neighbor_array_size += NI.GetDeg();
    for (int e = 0; e < NI.GetDeg(); e++) {
      uint64_t v2 = nodemap[NI.GetOutNId(e)];
      adjlist_local[e] = v2;
    }
    // sort_narray(adjlist_local, NI.GetDeg());
#ifdef DEBUG
    print_array_1D(adjlist_local, NI.GetDeg());
#endif 
    //omp_set_lock(&adj_lock);
    adjlists[i] = adjlist_local;
    //omp_unset_lock(&adj_lock);
  }
  printf("Adjacency Lists created\n");
  
  std::string binfile = std::string(filename) + ".bin";
  std::string binfile_gv = std::string(filename) + "_gv" + ".bin";
  std::string binfile_nl = std::string(filename) + "_nl" + ".bin";
  char* binfilename = const_cast<char*>(binfile.c_str()); 
  
  printf("Binfile:%s\n", binfilename);
  FILE* out_file = fopen(binfilename, "wb");
  if (!out_file) {
        exit(EXIT_FAILURE);
  }
  fseek(out_file, 0, SEEK_SET);
  
  printf("Size of uint64_t:%ld, writing num_nodes:%ld\n", sizeof(uint64_t), num_nodes);
  fwrite(&num_nodes, sizeof(uint64_t), 1, out_file);
  fwrite(&neighbor_array_size, sizeof(uint64_t), 1, out_file);
  for(int i = 0; i < num_nodes; i++){
    fwrite(&vertices[i], sizeof(vertices[i]), 1, out_file);
    fwrite(&degrees[i], sizeof(degrees[i]), 1, out_file);
    fwrite(adjlists[i], sizeof(uint64_t), degrees[i], out_file);
  }
  fclose(out_file);

  binfilename = const_cast<char*>(binfile_gv.c_str()); 
  printf("Binfile:%s\n", binfilename);
  out_file = fopen(binfilename, "wb");
  if (!out_file) {
        exit(EXIT_FAILURE);
  }
  fseek(out_file, 0, SEEK_SET);
  printf("Size of uint64_t:%ld, writing num_nodes:%ld in new file\n", sizeof(uint64_t), num_nodes);
  fwrite(&num_nodes,sizeof(uint64_t),1,out_file);
  double value = 1.0;
  for(int i=0; i< num_nodes;i++){
    fwrite(&vertices[i], sizeof(vertices[i]), 1, out_file);
    fwrite(&degrees[i], sizeof(degrees[i]), 1, out_file);
    fwrite(&adjlists[i], sizeof(adjlists[i]), 1, out_file);
    fwrite(&value, sizeof(double), 1, out_file);
  }
  fclose(out_file);
  
  binfilename = const_cast<char*>(binfile_nl.c_str()); 
  printf("Binfile:%s\n", binfilename);
  out_file = fopen(binfilename, "wb");
  if (!out_file) {
        exit(EXIT_FAILURE);
  }
  fseek(out_file, 0, SEEK_SET);
  printf("Size of uint64_t:%ld, writing nlarray:%ld in NL\n", sizeof(uint64_t), neighbor_array_size);
  fwrite(&neighbor_array_size,sizeof(uint64_t), 1, out_file);
  for(int i=0; i< num_nodes;i++)
  {
    // sort_narray(adjlists[i], degrees[i]); 
  #ifdef DEBUG
    print_array_1D(adjlists[i], degrees[i]);
  #endif
    fwrite(adjlists[i], sizeof(uint64_t), degrees[i], out_file);
  }
  fclose(out_file);
  // Try to read file back?  
  #ifdef DEBUG
  binfilename = const_cast<char*>(binfile_gv.c_str()); 
  printf("Binfile:%s\n", binfilename);
  out_file = fopen(binfilename, "rb");

  uint64_t num_verts, nlist_size, deg;
  fseek(out_file, 0, SEEK_SET);
  fread(&num_verts, sizeof(num_verts),1, out_file);
  g_v_bin = reinterpret_cast<vertex_t *>(malloc(num_verts * sizeof(vertex_t)));
  fread(g_v_bin, sizeof(vertex_t), num_verts, out_file); // read in all vertices
  fclose(out_file);
  
  binfilename = const_cast<char*>(binfile_nl.c_str()); 
  printf("Binfile:%s\n", binfilename);
  out_file = fopen(binfilename, "rb"); 
  fseek(out_file, 0, SEEK_SET);
  fread(&nlist_size, sizeof(nlist_size), 1, out_file);
  uint64_t* nlist_beg = reinterpret_cast<uint64_t*>(malloc(nlist_size * sizeof(uint64_t)));
  fread(nlist_beg, sizeof(uint64_t), nlist_size, out_file); // read in all vertices
  fclose(out_file);
  k = 0;

  for(int i=0; i< num_nodes;i++){
    printf("g_v[%lu]:%lu:[", g_v_bin[i].id, g_v_bin[i].deg);
    for(int j=0; j < g_v_bin[i].deg; j++, k++){
      printf(" %lu ", nlist_beg[k]);
    }
    printf("]\n");
  }
  #endif



}


