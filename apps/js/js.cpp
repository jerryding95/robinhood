#include "simupdown.h"
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cmath>
#include <iterator>
#include <string>

#include "js_udkvmsr_exe_nlb.hpp"
#include "js_udkvmsr_exe_rh_nlbstrm_off.hpp"
#include "js_udkvmsr_exe_rh_nlbstrm_on.hpp"
#include "js_udkvmsr_exe_rh_random.hpp"
#include "js_udkvmsr_exe_ws.hpp"

#if defined(GEM5_MODE)
  #include <gem5/m5ops.h>
#endif

#if defined(BASIM)
  #include <basimupdown.h>
#else
  #include <simupdown.h>
#endif

using namespace std;
#define TEST_TOP_OFFSET 64
#define TEST_TOP_FLAG 273
#define PART_PARM 16

typedef struct vertex_local{
    uint64_t deg;
    uint64_t id;
    uint64_t* neigh;
} vertexl_t;

typedef struct vertex{
    uint64_t id;
    uint64_t deg;
    uint64_t* neigh;
    uint64_t split; // required?
    uint64_t last_deg;
    uint64_t* siblings;  
    uint64_t num_siblings;  //0, -1, >0
    uint64_t reserved;
} vertex_t;


uint64_t* gen_intermediate_kv_do_all(UpDown::UDRuntime_t* rt, uint64_t num_uds, uint64_t arr_size, uint64_t entry_size){

    uint64_t ud_arr_size = arr_size * entry_size;
    printf("ud_arr_size: %lu\n", ud_arr_size);

    uint64_t* interPtrArr = reinterpret_cast<uint64_t*>(rt->mm_malloc(num_uds * sizeof(uint64_t)));
    uint64_t* interUdPtrArr = reinterpret_cast<uint64_t*>(rt->mm_malloc(num_uds * ud_arr_size * sizeof(uint64_t)));

#ifdef DEBUG
    printf("-------------------\ninterPtrArr = %p\n", *interPtrArr);
#endif


    for (int i=0; i<num_uds; i++){
        interPtrArr[i] = (uint64_t) (interUdPtrArr + i * ud_arr_size);
#ifdef DEBUG
        printf("interPtrArr %d, addr %lu, points to %lu\n", i, (uint64_t) (interPtrArr+i), interPtrArr[i]);
#endif
    }

    return interPtrArr;
}

uint64_t* gen_intermediate_kv_do_all_lane(UpDown::UDRuntime_t* rt, uint64_t num_uds, uint64_t arr_size, uint64_t entry_size){

    uint64_t lane_arr_size = (arr_size >> 6) * entry_size;
    uint64_t num_lanes = num_uds * 64;
    printf("%d,%d\n", lane_arr_size, num_lanes);

    uint64_t* interPtrArr = reinterpret_cast<uint64_t*>(rt->mm_malloc(num_lanes * sizeof(uint64_t)));
    uint64_t* interLanePtrArr = reinterpret_cast<uint64_t*>(rt->mm_malloc(num_lanes * lane_arr_size * sizeof(uint64_t)));

#ifdef DEBUG
    printf("-------------------\ninterPtrArr = %p\n", *interPtrArr);
#endif


    for (int i=0; i<num_lanes; i++){
        interPtrArr[i] = (uint64_t) (interLanePtrArr + i * lane_arr_size);
#ifdef DEBUG
        printf("interPtrArr %d, addr %lu, points to %lu\n", i, interPtrArr+i, interPtrArr[i]);
#endif
    }

    return interPtrArr;
}

UpDown::UDRuntime_t* initialize_rt(std::string efa_name, uint64_t num_lanes){
    /* INIT RUNTIME */
    UpDown::ud_machine_t machine;
    machine.LocalMemAddrMode = 1;
    machine.NumLanes = num_lanes > 64 ? 64 : num_lanes;
    machine.NumUDs = std::ceil(num_lanes / 64.0) > 4 ? 4 : std::ceil(num_lanes / 64.0);
    machine.NumStacks = std::ceil(num_lanes / (64.0 * 4)) > 8 ? 8 : std::ceil(num_lanes / (64.0 * 4));
    machine.NumNodes = std::ceil(num_lanes / (64.0 * 4 * 8));
    machine.MapMemSize = 137438953472;

    auto *rt = new UpDown::BASimUDRuntime_t(machine, efa_name+".bin", 0, 100);

    printf("=== Base Addresses ===\n");
    rt->dumpBaseAddrs();
    printf("\n=== Machine Config ===\n");
    rt->dumpMachineConfig();
    printf("\n\n");

    return rt;
}


void read_preprocess_input(UpDown::UDRuntime_t* rt, std::string file_name, uint64_t* v_count, uint64_t* e_count, vertex_t** graph){

    /* open file */
    FILE* in_file_gv = fopen((file_name+"_gv.bin").c_str(), "rb");
    if (!in_file_gv)
        exit(EXIT_FAILURE);
    FILE* in_file_nl = fopen((file_name+"_nl.bin").c_str(), "rb");
    if (!in_file_nl)
        exit(EXIT_FAILURE);

    /* read graph size */
    fseek(in_file_gv, 0, SEEK_SET);
    fseek(in_file_nl, 0, SEEK_SET);
    fread(v_count, sizeof(uint64_t), 1, in_file_gv);
    fread(e_count, sizeof(uint64_t), 1, in_file_nl);
    printf("v_count = %lu, e_count = %lu\n",(*v_count), (*e_count));

    /* malloc space */
    vertexl_t *g_v_bin_initial = reinterpret_cast<vertexl_t *>(rt->mm_malloc((*v_count) * sizeof(vertexl_t) + 8 * sizeof(uint64_t)));
    uint64_t* nlist_beg_initial = reinterpret_cast<uint64_t*>(rt->mm_malloc(((*e_count) + (*v_count) * 8 + 8) * sizeof(uint64_t)));
    vertex_t *g_v_bin_new_initial = reinterpret_cast<vertex_t *>(rt->mm_malloc((*v_count) * sizeof(vertex_t) + 8 * sizeof(uint64_t)));

    vertexl_t *g_v_bin = reinterpret_cast<vertexl_t *>((uint64_t)g_v_bin_initial + (64 - ((uint64_t)g_v_bin_initial % 64)));
    uint64_t* nlist_beg = reinterpret_cast<uint64_t*>((uint64_t)nlist_beg_initial + (64 - ((uint64_t)nlist_beg_initial % 64)));
    *graph = reinterpret_cast<vertex_t *>((uint64_t)g_v_bin_new_initial + (64 - ((uint64_t)g_v_bin_new_initial % 64)));

    /* read all vertices */
    fread(g_v_bin, sizeof(vertexl_t), *v_count, in_file_gv); // read in all vertices 

    /* read neighbor lists */
    uint64_t num_edges = 0, max_deg = 0, curr_base = 0;
    for(int i=0; i < *v_count; i++) {
        uint64_t* loc_nlist = reinterpret_cast<uint64_t *>(((uint64_t)(nlist_beg)) + curr_base);
        g_v_bin[i].neigh = loc_nlist;

        uint64_t deg = g_v_bin[i].deg;
        fread(loc_nlist, sizeof(uint64_t), deg, in_file_nl);        

        /* Allign nl to 8 words */
        curr_base += deg * sizeof(uint64_t);
        curr_base += 64 - (curr_base % 64);

        /* track #edges read and max degree */
        num_edges += deg;
        if (max_deg < deg)
            max_deg = deg;
    }

    printf("# vertices: %lu , # edges:%lu , avg deg: %lf, max deg: %lu\n", *v_count, num_edges, ((double)num_edges)/(*v_count), max_deg);
    fflush(stdout);

    /* Allign graph to 64 bytes */
    for(int i = 0; i < *v_count; i++){
        (*graph)[i].id = g_v_bin[i].id;
        (*graph)[i].deg = g_v_bin[i].deg;
        (*graph)[i].neigh = g_v_bin[i].neigh;
        (*graph)[i].split = 0;
        (*graph)[i].last_deg = g_v_bin[i].deg;
        (*graph)[i].siblings = 0;
        (*graph)[i].num_siblings = 0;
        (*graph)[i].reserved = 0;
#ifdef DEBUG
        printf("(*graph):%lu, i:%lu v:%lu, deg:%lu, neigh:%lu\n", (*graph), i, (*graph)[i].id, (*graph)[i].deg, (*graph)[i].neigh);
#endif
    }

    rt->mm_free(g_v_bin_initial);
    return;
}

uint64_t* gen_input_arr(UpDown::UDRuntime_t* rt, uint64_t v_count, uint64_t num_maps) {
    uint64_t* input_arr = (uint64_t *) rt->mm_malloc(num_maps * 3 * sizeof(UpDown::word_t)); 
    uint64_t pairs_per_map = ((v_count - 1) * v_count / 2) / num_maps;
    int extra_pairs = ((v_count - 1) * v_count / 2) % num_maps;
    uint64_t cur_ind = 0, cur_count = 0;
    for (int i=0; i<num_maps; i++) {
        input_arr[3*i] = cur_ind;
        input_arr[3*i+1] = cur_count + cur_ind + 1;
        input_arr[3*i+2] = pairs_per_map;
        input_arr[3*i+2] += extra_pairs > 0 ? 1 : 0;
        extra_pairs -= 1;
        cur_count += input_arr[3*i+2];
        while (cur_count >= v_count - cur_ind - 1 && cur_ind < v_count) {
            cur_count -= v_count - cur_ind - 1;
            cur_ind += 1;
        }
    }

    // for (int i=0; i<num_maps; i++) {
    //     printf("intput arr %d: v1: %lu, v2: %lu, intersect_count: %lu, dram addr: %lu\n", i, input_arr[3*i], input_arr[3*i+1], input_arr[3*i+2], (uint64_t)(input_arr+3*i));
    // }
    return input_arr;
}

uint64_t* gen_output_arr(UpDown::UDRuntime_t* rt, uint64_t v_count) {
    uint64_t num_jc = v_count * (v_count - 1) / 2;
    uint64_t size = sizeof(UpDown::word_t) * num_jc * 3;

    uint64_t *output_arr = reinterpret_cast<uint64_t *>(rt->mm_malloc(size * sizeof(uint64_t)));

    return output_arr;
}

uint64_t* gen_partitions(UpDown::UDRuntime_t* rt, uint64_t num_lanes, uint64_t num_partition_per_lane, uint64_t* input_arr, uint64_t input_size, uint64_t input_entry_size){

    uint64_t* partitions = reinterpret_cast<uint64_t*>(rt->mm_malloc((num_lanes * num_partition_per_lane * 2) * sizeof(uint64_t)));

    uint64_t num_pairs_per_part = input_size / (num_lanes * num_partition_per_lane);

    // Initialize partitions
    uint64_t num_partitions = num_lanes * num_partition_per_lane;
    int offset = 0;
    for (int i = 0; i < num_partitions; i++) {
        partitions[2*i] = (uint64_t)(input_arr + input_entry_size*offset);
        offset = std::min((i+1) * num_pairs_per_part, input_size);
        partitions[2*i+1] = (uint64_t)(input_arr + input_entry_size*offset);

    }

    return partitions;
}

void run_js(UpDown::UDRuntime_t* rt, std::string mode, uint64_t partitions, uint64_t num_lanes, uint64_t input_arr, uint64_t input_size, uint64_t graph, uint64_t graph_size, uint64_t interSpace) {
    UpDown::networkid_t nwid(0, false, 0);
    uint64_t flag = 0;
    rt->t2ud_memcpy(&flag, 8, nwid, TEST_TOP_OFFSET); // set signal flag to 0

    UpDown::word_t ops_data[8];
    UpDown::operands_t ops(8, ops_data);

    ops.set_operand(0, partitions);
    ops.set_operand(1, PART_PARM);
    ops.set_operand(2, num_lanes);
    ops.set_operand(3, input_arr);
    ops.set_operand(4, input_size);
    ops.set_operand(5, graph);
    ops.set_operand(6, graph_size);
    ops.set_operand(7, interSpace);

    // UpDown::event_t evnt_ops(js_udkvmsr_exe::main__init,                     /*Event Label*/
    //                          nwid,
    //                          UpDown::CREATE_THREAD, /*Thread ID*/
    //                          &ops                   /*Operands*/);

    UpDown::event_t *event_ops;
    if(mode == "rh_nlbstrm_off"){
        event_ops = new UpDown::event_t(js_udkvmsr_exe_rh_nlbstrm_off::main__init /*Event Label*/,
                                nwid,
                                UpDown::CREATE_THREAD /*Thread ID*/,
                                &ops /*Operands*/);
        printf("Running Jaccard with NLBSTRM Off\n");
    }
    else if (mode == "rh_nlbstrm_on"){
        event_ops = new UpDown::event_t(js_udkvmsr_exe_rh_nlbstrm_on::main__init /*Event Label*/,
                                nwid,
                                UpDown::CREATE_THREAD /*Thread ID*/,
                                &ops /*Operands*/);
        printf("Running Jaccard with NLBSTRM On\n");
    }
    else if (mode == "rh_random"){
        event_ops = new UpDown::event_t(js_udkvmsr_exe_rh_random::main__init /*Event Label*/,
                                nwid,
                                UpDown::CREATE_THREAD /*Thread ID*/,
                                &ops /*Operands*/);
        printf("Running Jaccard with RobinHood Random\n");
    }
    else if (mode == "ws"){
        event_ops = new UpDown::event_t(js_udkvmsr_exe_ws::main__init /*Event Label*/,
                                nwid,
                                UpDown::CREATE_THREAD /*Thread ID*/,
                                &ops /*Operands*/);
        printf("Running Jaccard with WS\n");
    }
    else if (mode == "nlb"){
        event_ops = new UpDown::event_t(js_udkvmsr_exe_nlb::main__init /*Event Label*/,
                                nwid,
                                UpDown::CREATE_THREAD /*Thread ID*/,
                                &ops /*Operands*/);
        printf("Running Jaccard with NLB\n");
    }
    else{
        printf("Invalid mode selected!\n");
        return;
    }

    printf("set event word\n");
    rt->send_event(*event_ops);
    printf("Event sent to updown lane %d.\n", 0);

    rt->start_exec(nwid);
    rt->test_wait_addr(nwid, TEST_TOP_OFFSET, TEST_TOP_FLAG);

    delete event_ops;
    return;
}



int main(int argc, char *argv[]) {

    std::string mode = argv[1];
    int num_nodes = atoi(argv[2]);
    std::string file_name = argv[3];
    int num_ud = num_nodes * 32;
    int num_lanes = num_ud * 64;
    
    /* INIT RUNTIME */
    printf("Start initializing runtime\n");
    UpDown::UDRuntime_t* rt = initialize_rt("js_udkvmsr_exe_"+mode, num_lanes);


    /* READ AND PREPROCESS INPUT*/
    uint64_t v_count, e_count;
    vertex_t* graph;
    printf("Start reading input graph\n");
    read_preprocess_input(rt, file_name, &v_count, &e_count, &graph);

    /* GENERATE INPUT ARRAY, RESULT SPACE, PARTITIONS and INTERMEDIATE SPACE*/
    printf("Start assigning input array\n");
    uint64_t* input_arr = gen_input_arr(rt, v_count, num_lanes * PART_PARM);
    // uint64_t* result_arr = gen_output_arr(v_count);
    printf("Start assigning partition array\n");
    uint64_t* partitions = gen_partitions(rt, num_lanes, PART_PARM, input_arr, num_lanes * PART_PARM, 3);
    printf("Start assigning intermediate space\n");
    uint64_t* interSpace;
    if (mode == "ws")
        interSpace = gen_intermediate_kv_do_all_lane(rt, num_ud, 1<<24, 5);
    else if(mode != "nlb")
        interSpace = gen_intermediate_kv_do_all(rt, num_ud, 1<<24, 5);
    // uint64_t* interSpace = gen_intermediate_kv_do_all(rt, num_ud, 1<<24, 5);

    /* Send init event to UD */
    run_js(rt, 
        mode,
        (uint64_t) partitions, 
        (uint64_t) num_lanes, 
        (uint64_t) input_arr, 
        (uint64_t) (num_lanes * PART_PARM), 
        (uint64_t) graph, 
        (uint64_t) v_count, 
        (uint64_t) interSpace);
    
    /* JS Finished */
    delete rt;
    printf("TOP DONE.\n");

    return 0;
}

