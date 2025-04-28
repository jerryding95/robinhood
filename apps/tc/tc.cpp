#include "simupdown.h"

#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <iostream>
#include <cmath>
#include <sys/types.h>
#include "tc_udkvmsr_exe_nlb.hpp"
#include "tc_udkvmsr_exe_ws.hpp"
#include "tc_udkvmsr_exe_rh_nlbstrm_off.hpp"
#include "tc_udkvmsr_exe_rh_nlbstrm_on.hpp"
#include "tc_udkvmsr_exe_rh_random.hpp"

#define CPU_CMP
#ifdef BASIM
#include <basimupdown.h>
#endif

//#define DEBUG


#define USAGE "USAGE: ./tc_udkvmsr <gv_bin> <nl_bin> <num_lanes> <num_master_lanes> <mode> <start> <stop>"
#define NUM_LANE_PER_UD 64
#define NUM_UD_PER_CLUSTER 4
#define NUM_CLUSTER_PER_NODE 8
#define PART_PARM 16
#define TEST_TOP_OFFSET 64
#define TEST_TOP_FLAG 273

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

void print_array(uint64_t* a1, int a1_sz){
    printf("[ ");
    for(int i = 0; i < a1_sz; i++){
        printf("%d ", a1[i]);
    }
    printf("]\n");
}

int isPowerOf2(int number) {
    if (number <= 0) {
        return 0;  // Negative numbers and zero are not powers of 2
    }
    return (number & (number - 1)) == 0;
}

UpDown::word_t intersection(vertexl_t* u0, vertexl_t* u1, uint64_t* u0u1){
    UpDown::word_t size = 0;
    if(u0->deg == 0 || u1->deg == 0)
    return 0;
    if(!(u0->neigh[u0->deg - 1] < u1->neigh[0]) && !(u0->neigh[0] > u1->neigh[u1->deg - 1])) {
        // At least some overlap
        UpDown::word_t pos0 = 0, pos1 = 0;
        while(pos0 != u0->deg && pos1 != u1->deg)
        {
            if(u0->neigh[pos0] < u1->neigh[pos1])
                pos0++;
            else if(u0->neigh[pos0] > u1->neigh[pos1])
                pos1++;
            else {
                u0u1[size++] = u0->neigh[pos0];
                pos0++;
                pos1++;
            }
        }
    }
    return size;
}

long three_clique_count_cpu(uint64_t svert, uint64_t evert, vertexl_t* g_v_bin) {
    long count = 0, intersection_count = 0;
    long i1 = 0;
    for(i1=svert; i1<evert; i1++) {
        long count2 = 0;
        long v1 = i1;
        uint64_t deg1 = g_v_bin[v1].deg;

        if (deg1 == 0)
            continue;

        int i2;
        for(i2=0; i2<deg1; i2++) {
            long count3 = 0;
            long v2 = g_v_bin[v1].neigh[i2];

            if(v2 >= v1)
                break;

            intersection_count += 1;
            uint64_t deg2 = g_v_bin[v2].deg;
            if (deg2 == 0)
                continue;
            
            uint64_t* list3 = reinterpret_cast<uint64_t*>(malloc(deg2 * sizeof(uint64_t)));
            uint64_t len3 = intersection(&g_v_bin[v1], &g_v_bin[v2], list3);

            
            int i3;
            for(i3=0; i3<len3; i3++) {
                long v3 = list3[i3];
                
                if(v3 >= v2)
                    break;
                count3++;
            }
            free(list3);
            list3 = NULL;
            count2 += count3;
            // if (count3 > 0) {
                // printf("Edge %ld-%ld: %d\n", v1, v2, count3);
            // }
            // if (v1 == 1394 && v2 == 1380) {
            //     printf("Edge 1394-1380: v1_deg: %lu, v1_nb_list: %p, v2_deg: %lu, v2_nb_list: %p\n", deg1, g_v_bin[v1].neigh, deg2, g_v_bin[v2].neigh);
            // }
        }
        count += count2;
        // printf("CPU[%d] v[%ld] count num = %ld\n",gl_ud_id,v1,count2);
    }
    printf("Total intersection count: %ld", intersection_count);
    return count;
}

uint64_t read_and_load_nlistbin(const char* binfilename, const char* binfilename2 , vertexl_t *g_v_bin, uint64_t* nlist_beg){
    printf("Binfile:%s\n", binfilename);
    fflush(stdout);
    FILE* in_file_gv = fopen(binfilename, "rb");
    if (!in_file_gv) {
        exit(EXIT_FAILURE);
    }
    FILE* in_file_nl = fopen(binfilename2, "rb");
    if (!in_file_nl) {
        exit(EXIT_FAILURE);
    }
    uint64_t num_nodes, nlist_size = 0;

    fseek(in_file_gv, 0, SEEK_SET);
    fseek(in_file_nl, 0, SEEK_SET);
    fread(&num_nodes, sizeof(num_nodes),1, in_file_gv);
    fread(&nlist_size, sizeof(nlist_size), 1, in_file_nl);

    fread(g_v_bin, sizeof(vertexl_t), num_nodes, in_file_gv); // read in all vertices 
    uint64_t num_edges = 0, max_deg = 0;
    uint64_t curr_base = 0;
    for(int i=0; i<num_nodes; i++) {
        uint64_t * loc_nlist = reinterpret_cast<uint64_t *>(((uint64_t)nlist_beg) + curr_base);
        uint64_t deg = g_v_bin[i].deg;
        fread(loc_nlist, sizeof(uint64_t), deg, in_file_nl); // read in all vertices
        g_v_bin[i].neigh = loc_nlist;

        num_edges += deg;
        if (max_deg < deg) {
            max_deg = deg;
        }

        curr_base += deg * sizeof(uint64_t);
        curr_base = curr_base + (64 - (curr_base % 64));

#ifdef TESTBIN
        print_array(g_v_bin[i].neigh, g_v_bin[i].deg);
        printf("Input pair %lu: key=%lu deg=%lu nlist_ptr=%lu\n", i, g_v_bin[i].id, g_v_bin[i].deg, g_v_bin[i].neigh);
#endif
    }

    printf("# vertices: %lu , # edges:%lu , avg deg: %lf, max deg: %lu\n", num_nodes, num_edges, ((double)num_edges)/num_nodes, max_deg);
    fflush(stdout);
    return max_deg;
}

void convert_to_new_struct(int num_nodes, vertexl_t *g_v_bin, vertex_t* g_v_bin_new){
    for(int i = 0; i < num_nodes; i++){
        g_v_bin_new[i].id = g_v_bin[i].id;
        g_v_bin_new[i].deg = g_v_bin[i].deg;
        g_v_bin_new[i].neigh = g_v_bin[i].neigh;
        g_v_bin_new[i].split = 0;
        g_v_bin_new[i].last_deg = g_v_bin_new[i].deg;
        g_v_bin_new[i].siblings = 0;
        g_v_bin_new[i].num_siblings = 0;
        g_v_bin_new[i].reserved = 0;
#ifdef DEBUG
        printf("g_v_bin_new:%lu, i:%lu v:%lu, deg:%lu, neigh:%lu\n", g_v_bin_new, i, g_v_bin_new[i].id, g_v_bin_new[i].deg, g_v_bin_new[i].neigh);
#endif
    }
}

UpDown::UDRuntime_t* initialize_rt(std::string efa_name, uint64_t num_nodes, uint64_t num_uds_per_node, uint64_t num_lanes_per_ud){
    // Set up machine parameters
    UpDown::ud_machine_t machine;
    machine.NumLanes = num_lanes_per_ud;
    machine.NumUDs = std::min((int)num_uds_per_node, NUM_UD_PER_CLUSTER);
    machine.NumStacks = std::ceil((double)num_uds_per_node / NUM_UD_PER_CLUSTER);
    machine.NumNodes = num_nodes;
    machine.LocalMemAddrMode = 1;
    machine.MapMemSize = 34359738368;

    UpDown::BASimUDRuntime_t* rt = new UpDown::BASimUDRuntime_t(machine, efa_name+".bin", 0, 100);
    printf("using basim\n");

#ifdef DEBUG
    printf("Nodes: %lu, UDs per node: %lu, Lanes per UD: %lu", num_nodes, num_uds_per_node, num_lanes_per_ud);
    printf("=== Base Addresses ===\n");
    rt->dumpBaseAddrs();
    printf("\n=== Machine Config ===\n");
    rt->dumpMachineConfig();
#endif

    return rt;
}

uint64_t* gen_partitions(UpDown::UDRuntime_t* rt, uint64_t num_lanes, uint64_t num_partition_per_lane){

    uint64_t* partitions = reinterpret_cast<uint64_t*>(rt->mm_malloc((num_lanes * num_partition_per_lane * 2) * sizeof(uint64_t)));

    return partitions;
}

uint64_t* gen_intermediate_kv_do_all(UpDown::UDRuntime_t* rt, int num_uds, int arr_size, int entry_size){

    int ud_arr_size = arr_size * entry_size;

    uint64_t* interPtrArr = reinterpret_cast<uint64_t*>(rt->mm_malloc(num_uds * sizeof(uint64_t)));
    uint64_t* interUdPtrArr = reinterpret_cast<uint64_t*>(rt->mm_malloc(num_uds * ud_arr_size * sizeof(uint64_t)));

#ifdef DEBUG
    printf("-------------------\ninterPtrArr = %p\n", *interPtrArr);
#endif


    for (int i=0; i<num_uds; i++){
        interPtrArr[i] = (uint64_t) (interUdPtrArr + i * ud_arr_size);
#ifdef DEBUG
        printf("interPtrArr %d, addr %lu, points to %lu\n", i, interPtrArr+i, interPtrArr[i]);
#endif
    }

    return interPtrArr;
}

uint64_t* gen_intermediate_kv_do_all_lane(UpDown::UDRuntime_t* rt, int num_uds, int arr_size, int entry_size){

    int lane_arr_size = (arr_size >> 6) * entry_size;
    int num_lanes = num_uds * 64;
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

int main(int argc, char* argv[]) {

    if (argc < 2) {
        printf("Insufficient Input Params\n");
        printf("%s\n", USAGE);
        exit(1);
    }

    std::string lb_mode = argv[1];
    if (lb_mode == "rh") {
        lb_mode = "rh_nlbstrm_off";
    }
    uint64_t num_nodes = atoi(argv[2]);
    uint64_t updown_count = num_nodes * 32;
    uint64_t num_lanes = num_nodes * 2048;

    std::string fname = argv[3];
    std::string filename = fname + "_gv.bin";
    std::string filename2 = fname + "_nl.bin";

    int mode = 0;
    uint64_t svert = 0, evert;

    printf("File Name:%s , ", filename);
    printf("Num Lanes:%ld\n", num_lanes);
    fflush(stdout);

    UpDown::UDRuntime_t* rt = initialize_rt("tc_udkvmsr_exe_"+lb_mode, std::ceil(num_lanes / (64.0 * 4 * 8)), std::ceil(num_lanes / 64.0) > 32 ? 32 : std::ceil(num_lanes / 64.0), 64);

    /* Use KVMSR to create the EdgeStore */
    /* Partition the input binary edges based on number of lanes and buckets per lane */
    uint64_t num_edges=0, num_verts=0, nlist_size = 0;
    printf("Binfile:%s\n", filename);
    fflush(stdout);

    FILE* in_file_gv = fopen(filename.c_str(), "rb");
    if (!in_file_gv) {
        exit(EXIT_FAILURE);
    }
    FILE* in_file_nl = fopen(filename2.c_str(), "rb");
    if (!in_file_nl) {
        exit(EXIT_FAILURE);
    }

    fseek(in_file_gv, 0, SEEK_SET);
    fseek(in_file_nl, 0, SEEK_SET);
    fread(&num_verts, sizeof(num_verts),1, in_file_gv);
    fread(&nlist_size, sizeof(nlist_size), 1, in_file_nl);

    fclose(in_file_gv);
    fclose(in_file_nl);
    printf("num_verts = %lu, nlist_size = %lu\n",num_verts,nlist_size);
    fflush(stdout);


    vertexl_t *g_v_bin_initial = reinterpret_cast<vertexl_t *>(rt->mm_malloc(num_verts * sizeof(vertexl_t) + 8 * sizeof(uint64_t)));
    uint64_t* nlist_beg_initial = reinterpret_cast<uint64_t*>(rt->mm_malloc((nlist_size + num_verts * 8 + 8) * sizeof(uint64_t)));
    vertex_t *g_v_bin_new_initial = reinterpret_cast<vertex_t *>(rt->mm_malloc(num_verts * sizeof(vertex_t) + 8 * sizeof(uint64_t)));

    vertexl_t *g_v_bin = reinterpret_cast<vertexl_t *>((uint64_t)g_v_bin_initial + (64 - ((uint64_t)g_v_bin_initial % 64)));
    uint64_t* nlist_beg = reinterpret_cast<uint64_t*>((uint64_t)nlist_beg_initial + (64 - ((uint64_t)nlist_beg_initial % 64)));
    vertex_t *g_v_bin_new = reinterpret_cast<vertex_t *>((uint64_t)g_v_bin_new_initial + (64 - ((uint64_t)g_v_bin_new_initial % 64)));


    // Load all the neighborlists
    read_and_load_nlistbin(filename.c_str(), filename2.c_str(),  g_v_bin, nlist_beg);

    // Convert to different vertex data struct and launch TC
    convert_to_new_struct(num_verts, g_v_bin, g_v_bin_new);

    if(mode == 0 || evert > num_verts){
        evert = num_verts;
    }
    

    uint64_t* partitions = gen_partitions(rt, num_lanes, PART_PARM);
    // uint64_t* interSpace = gen_intermediate_kv_ud(rt, updown_count, 256*64, 8);
    uint64_t* interSpace;
    if (lb_mode == "ws") {
        interSpace = gen_intermediate_kv_do_all_lane(rt, updown_count, 1<<22, 3);
    }
    else if (lb_mode != "nlb") {
        interSpace = gen_intermediate_kv_do_all(rt, updown_count, 1<<22, 3);
    }
    
    UpDown::networkid_t nwid(0, false, 0);
    uint64_t flag = 0, cpu_count = 0;

#ifdef CPU_CMP
    cpu_count = three_clique_count_cpu(svert, evert, g_v_bin);
    printf("Three Clique Count: Reference:%lu\n", cpu_count);
    fflush(stdout);
#endif
    printf("Starting UD now\n");
    fflush(stdout);

    rt->t2ud_memcpy(&flag, 8, nwid, TEST_TOP_OFFSET); // set signal flag to 0

    UpDown::word_t ops_data[8];
    UpDown::operands_t ops(8, ops_data);

    ops.set_operand(0, (uint64_t) partitions);
    ops.set_operand(1, (uint64_t) PART_PARM);
    ops.set_operand(2, (uint64_t) num_lanes);
    ops.set_operand(3, (uint64_t) g_v_bin_new);
    ops.set_operand(4, (uint64_t) num_verts);
    ops.set_operand(5, (uint64_t) interSpace);

    // UpDown::event_t evnt_ops(tc_udkvmsr_exe::main__init,                     /*Event Label*/
    //                          nwid,
    //                          UpDown::CREATE_THREAD, /*Thread ID*/
    //                          &ops                   /*Operands*/);

    UpDown::event_t *event_ops;
    std::cout << "lb_mode: " << lb_mode << std::endl;
    if(lb_mode == "rh_nlbstrm_off"){
        event_ops = new UpDown::event_t(tc_udkvmsr_exe_rh_nlbstrm_off::main__init /*Event Label*/,
                                nwid,
                                UpDown::CREATE_THREAD /*Thread ID*/,
                                &ops /*Operands*/);
        printf("Running Jaccard with NLBSTRM Off\n");
    }
    else if (lb_mode == "rh_nlbstrm_on"){
        event_ops = new UpDown::event_t(tc_udkvmsr_exe_rh_nlbstrm_on::main__init /*Event Label*/,
                                nwid,
                                UpDown::CREATE_THREAD /*Thread ID*/,
                                &ops /*Operands*/);
        printf("Running Jaccard with NLBSTRM On\n");
    }
    else if (lb_mode == "rh_random"){
        event_ops = new UpDown::event_t(tc_udkvmsr_exe_rh_random::main__init /*Event Label*/,
                                nwid,
                                UpDown::CREATE_THREAD /*Thread ID*/,
                                &ops /*Operands*/);
        printf("Running Jaccard with RobinHood Random\n");
    }
    else if (lb_mode == "ws"){
        event_ops = new UpDown::event_t(tc_udkvmsr_exe_ws::main__init /*Event Label*/,
                                nwid,
                                UpDown::CREATE_THREAD /*Thread ID*/,
                                &ops /*Operands*/);
        printf("Running Jaccard with WS\n");
    }
    else if (lb_mode == "nlb"){
        event_ops = new UpDown::event_t(tc_udkvmsr_exe_nlb::main__init /*Event Label*/,
                                nwid,
                                UpDown::CREATE_THREAD /*Thread ID*/,
                                &ops /*Operands*/);
        printf("Running Jaccard with NLB\n");
    }
    else{
        printf("Invalid mode selected!\n");
        return 0;
    }


    printf("set event word\n");
    rt->send_event(*event_ops);
    printf("Event sent to updown lane %d.\n", 0);

    rt->start_exec(nwid);
    rt->test_wait_addr(nwid, TEST_TOP_OFFSET, TEST_TOP_FLAG);

    printf("TOP: Intersection test done.\n");
    fflush(stdout);


    printf("Three Clique Count UD: %lu\n", updown_count);
#ifdef CPU_CMP
    printf("Three Clique Count CPU: %lu\n", cpu_count);
#endif
    fflush(stdout);



    printf("Three Clique Count UD: %lu\n", updown_count);
#ifdef CPU_CMP
    printf("Three Clique Count CPU: %lu\n", cpu_count);
#endif

  
    delete rt;
    return 0;
}