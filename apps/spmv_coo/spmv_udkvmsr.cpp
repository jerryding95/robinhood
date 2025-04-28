#include "simupdown.h"

#include <cstdio>
#include <cstdlib>
#include <iostream>
#include <fstream>
#include <filesystem>
#include <cmath>
#include <basimupdown.h>
#include "spmvMSR.hpp"

#ifdef GEM5_MODE
 #include <gem5/m5ops.h>
#endif

// #define DEBUG

#define NUM_LANE_PER_UD 64
#define NUM_UD_PER_CLUSTER 4
#define NUM_CLUSTER_PER_NODE 8

#define PART_PARM 4

struct coo_kv_pair{
    uint64_t key;
    double value;
};


UpDown::UDRuntime_t* initialize_rt(std::string efa_name, uint64_t num_nodes, uint64_t num_uds_per_node, uint64_t num_lanes_per_ud){
    // Set up machine parameters
    UpDown::ud_machine_t machine;
    machine.NumLanes = num_lanes_per_ud;
    machine.NumUDs = std::min((int)num_uds_per_node, NUM_UD_PER_CLUSTER);
    machine.NumStacks = std::ceil((double)num_uds_per_node / NUM_UD_PER_CLUSTER);
    machine.NumNodes = num_nodes;
    machine.LocalMemAddrMode = 1;
    machine.MapMemSize = 137438953472; //34359738368;

#ifdef GEM5_MODE
    UpDown::UDRuntime_t *rt = new UpDown::UDRuntime_t(machine);
#else
#ifdef BASIM
    UpDown::BASimUDRuntime_t* rt = new UpDown::BASimUDRuntime_t(machine, efa_name+".bin", 0);
    printf("using basim\n");
#else
    UpDown::SimUDRuntime_t *rt = new UpDown::SimUDRuntime_t(machine, efa_name+".py", efa_name, "./", UpDown::EmulatorLogLevel::FULL_TRACE);
#endif
#endif

// #ifdef DEBUG
    printf("=== Base Addresses ===\n");
    rt->dumpBaseAddrs();
    printf("\n=== Machine Config ===\n");
    rt->dumpMachineConfig();
// #endif

    return rt;
}


coo_kv_pair* gen_input_kv(UpDown::UDRuntime_t* rt, std::string fpath, int* vlength, int* output_length, int* num_input_keys, double** result, int mode){
    int num_row, num_col, num_lines;
    std::string line;
    std::ifstream file(fpath);
    if (!file.is_open()){
        std::cout << "Unable to open file " << fpath; 
        exit(-1);
    }

    // Ignore comments headers
    while (file.peek() == '%') file.ignore(2048, '\n');

    // Read number of rows and columns
    file >> num_row >> num_col >> num_lines;
    *output_length = num_row;
    *vlength = num_col;
    *num_input_keys = num_lines;
#ifdef GEM5_MODE
    *result = (double*) rt->mm_malloc_global(num_row * sizeof(double));
    coo_kv_pair* inKVSet = reinterpret_cast<coo_kv_pair*>(rt->mm_malloc_global(num_lines * sizeof(coo_kv_pair)));
#else
    *result = (double*) rt->mm_malloc(num_row * sizeof(double));
    coo_kv_pair* inKVSet = reinterpret_cast<coo_kv_pair*>(rt->mm_malloc(num_lines * sizeof(coo_kv_pair)));
#endif

#ifdef DEBUG
    printf("-------------------\ninKVSet = %p\n", inKVSet);
    printf("rows: %d, columns: %d, lines: %d\n", num_row, num_col, num_lines);
#endif

    for (int i = 0; i < num_lines; i++){
        double val;
        int row, col;
        if (mode == 0) {
            file >> row >> col >> val;
        }
        else {
            file >> row >> col;
            val = 1.5;
        }
        inKVSet[i].key = row-1;
        inKVSet[i].key <<= 32;
        inKVSet[i].key += col-1;
        inKVSet[i].value = val;
#ifdef DEBUG
        printf("Input pair %d: key=%ld value=%f row=%lu column %lu DRAM_addr=%p\n", i, inKVSet[i].key, inKVSet[i].value, inKVSet[i].key>>32, inKVSet[i].key&0xffffffff, inKVSet + i);
#endif
        (*result)[row-1] += 10*val;
    }

    file.close();
    
    return inKVSet;
}


double* gen_output_kv(UpDown::UDRuntime_t* rt, int output_length){
#ifdef GEM5_MODE
    double* outKVSet = (double*)(rt->mm_malloc_global(output_length*sizeof(double)));
#else
    double* outKVSet = (double*)(rt->mm_malloc(output_length*sizeof(double)));
#endif
    for (int i = 0; i < output_length; i++){
        outKVSet[i] = 0;
#ifdef DEBUG
        printf("Output pair %d: key=%d value=%f DRAM_addr=%p\n", i, i, outKVSet[i], outKVSet + i);
#endif
    }

    return outKVSet;
}


// void gen_intermediate_kv(UpDown::UDRuntime_t* rt, int key_space, int bin_size, uint64_t** interKQueue, uint64_t** interKVDict){
// #ifdef GEM5_MODE
//     *interKQueue = reinterpret_cast<uint64_t*>(rt->mm_malloc_global(key_space * sizeof(uint64_t)));
//     *interKVDict = reinterpret_cast<uint64_t*>(rt->mm_malloc_global(key_space * (2 * sizeof(uint64_t))));
//     uint64_t* p_inter = reinterpret_cast<uint64_t*>(rt->mm_malloc_global(key_space * (bin_size * sizeof(uint64_t))));
// #else
//     *interKQueue = reinterpret_cast<uint64_t*>(rt->mm_malloc(key_space * sizeof(uint64_t)));
//     *interKVDict = reinterpret_cast<uint64_t*>(rt->mm_malloc(key_space * (2 * sizeof(uint64_t))));
//     uint64_t* p_inter = reinterpret_cast<uint64_t*>(rt->mm_malloc(key_space * (bin_size * sizeof(uint64_t))));
// #endif

// #ifdef DEBUG
//     printf("-------------------\ninterKQueue = %p\n", *interKQueue);
//     printf("-------------------\ninterKVDict = %p\n", *interKVDict);
// #endif

    
//     for (int i = 0; i < key_space; i++) {
//         (*interKQueue)[i] = 0;
//         (*interKVDict)[i*2] = 0;
//         (*interKVDict)[i*2 + 1] = (uint64_t) (p_inter + bin_size*i);
// #ifdef DEBUG
//         printf("Intermediate key queue %d: key=%d DRAM_addr=%p\n", i, (*interKQueue)[i], (*interKQueue)+i);
//         printf("Intermediate pair %d: num=%llu value=%llu DRAM_addr=%p\n", i, (*interKVDict)[i*2], (*interKVDict)[i*2 + 1], (*interKVDict) + i*2);
// #endif
//     }

//     return;
// }

uint64_t* gen_intermediate_kv(UpDown::UDRuntime_t* rt, int num_lanes, int num_bin_per_lane, int bin_size){
#ifdef GEM5_MODE
    uint64_t* interPtrArr = reinterpret_cast<uint64_t*>(rt->mm_malloc_global(num_lanes * sizeof(uint64_t)));
    uint64_t* interLanePtrArr = reinterpret_cast<uint64_t*>(rt->mm_malloc_global(num_bin_per_lane * num_lanes * sizeof(uint64_t)));
    uint64_t* p_inter = reinterpret_cast<uint64_t*>(rt->mm_malloc_global(num_bin_per_lane * num_lanes * (bin_size * sizeof(uint64_t))));
#else
    uint64_t* interPtrArr = reinterpret_cast<uint64_t*>(rt->mm_malloc(num_lanes * sizeof(uint64_t)));
    uint64_t* interLanePtrArr = reinterpret_cast<uint64_t*>(rt->mm_malloc(num_bin_per_lane * num_lanes * sizeof(uint64_t)));
    uint64_t* p_inter = reinterpret_cast<uint64_t*>(rt->mm_malloc(num_bin_per_lane * num_lanes * (bin_size * sizeof(uint64_t))));
#endif

#ifdef DEBUG
    printf("-------------------\ninterPtrArr = %p\n", *interPtrArr);
#endif

    for (int i=0; i<num_lanes; i++){
        int lanePtrStart = i*num_bin_per_lane;
        int laneBinStart = i*num_bin_per_lane*bin_size;
        interPtrArr[i] = (uint64_t) (interLanePtrArr + lanePtrStart);
#ifdef DEBUG
        printf("Intermediate Hashtable %d: array start=%p, bin start=%p DRAM_addr=%p\n", 
            i, interLanePtrArr + i*num_bin_per_lane, p_inter + i*num_bin_per_lane*bin_size, interPtrArr + i);
#endif
        for (int j=0; j<num_bin_per_lane; j++){
            interLanePtrArr[lanePtrStart + j] = (uint64_t) (p_inter + laneBinStart + j*bin_size);
#ifdef DEBUG
            printf("    interLanePtrArr %d, points to %lx, DRAM address %p\n", j, interLanePtrArr[lanePtrStart + j], interLanePtrArr + lanePtrStart + j);
#endif
        }

    }

    return interPtrArr;
}

uint64_t* gen_intermediate_kv_ud(UpDown::UDRuntime_t* rt, int num_uds, int num_bin_per_ud, int bin_size){
#ifdef GEM5_MODE
    uint64_t* interPtrArr = reinterpret_cast<uint64_t*>(rt->mm_malloc_global(num_uds * sizeof(uint64_t)));
    uint64_t* interUdPtrArr = reinterpret_cast<uint64_t*>(rt->mm_malloc_global(num_bin_per_ud * num_uds * sizeof(uint64_t)));
    uint64_t* p_inter = reinterpret_cast<uint64_t*>(rt->mm_malloc_global(num_bin_per_ud * num_uds * (bin_size * sizeof(uint64_t))));
#else
    uint64_t* interPtrArr = reinterpret_cast<uint64_t*>(rt->mm_malloc(num_uds * sizeof(uint64_t)));
    uint64_t* interUdPtrArr = reinterpret_cast<uint64_t*>(rt->mm_malloc(num_bin_per_ud * num_uds * sizeof(uint64_t)));
    uint64_t* p_inter = reinterpret_cast<uint64_t*>(rt->mm_malloc(num_bin_per_ud * num_uds * (bin_size * sizeof(uint64_t))));
#endif

#ifdef DEBUG
    printf("-------------------\ninterPtrArr = %p\n", *interPtrArr);
#endif

    for (int i=0; i<num_uds; i++){
        int udPtrStart = i*num_bin_per_ud;
        int udBinStart = i*num_bin_per_ud*bin_size;
        interPtrArr[i] = (uint64_t) (interUdPtrArr + udPtrStart);
#ifdef DEBUG
        printf("Intermediate Hashtable %d: array start=%p, bin start=%p DRAM_addr=%p\n", 
            i, interUdPtrArr + i*num_bin_per_ud, p_inter + i*num_bin_per_ud*bin_size, interPtrArr + i);
#endif
        for (int j=0; j<num_bin_per_ud; j++){
            interUdPtrArr[udPtrStart + j] = (uint64_t) (p_inter + udBinStart + j*bin_size);
#ifdef DEBUG
            printf("    interUdPtrArr %d, points to %lx, DRAM address %p\n", j, interUdPtrArr[udPtrStart + j], interUdPtrArr + udPtrStart + j);
#endif
        }

    }

    return interPtrArr;
}


// coo_kv_pair** gen_partitions(UpDown::UDRuntime_t* rt, uint64_t num_workers, uint64_t num_input_keys, coo_kv_pair* inKVSet){
//     uint64_t num_partitions = num_workers;
//     uint64_t num_pairs_per_part = num_input_keys/num_workers;
//     int extra_pairs = num_input_keys - (num_partitions*num_pairs_per_part);
//     printf("generating partition: num_input_keys %lu, num_partitions %lu, num_pairs_per_part %lu, extra_pairs %d\n", 
//         num_input_keys, num_partitions, num_pairs_per_part, extra_pairs);

// #ifdef GEM5_MODE
//     coo_kv_pair** partitions = reinterpret_cast<coo_kv_pair**>(rt->mm_malloc_global((num_partitions + 1) * sizeof(coo_kv_pair*)));
// #else
//     coo_kv_pair** partitions = reinterpret_cast<coo_kv_pair**>(rt->mm_malloc((num_partitions + 1) * sizeof(coo_kv_pair*)));
// #endif

//     int ind = 0;
// #ifdef DEBUG
//     printf("-------------------\nparitions = %p\n", partitions);
// #endif

//     for (int i = 0; i < num_partitions+1; i++) {
//         partitions[i] = inKVSet + ind;

// #ifdef DEBUG
//         printf("Partition %d: pair_id=%d, key=%ld value=%f base_pair_addr=%p, part_entry_addr=%p\n",
//             i, ind, partitions[i]->key, partitions[i]->value, partitions[i], partitions + i);
// #endif
//         ind += extra_pairs-- <= 0 ? num_pairs_per_part : num_pairs_per_part+1;
//     }

//     return partitions;
// }

uint64_t* gen_partitions(UpDown::UDRuntime_t* rt, uint64_t num_lanes, uint64_t num_partition_per_lane){

#ifdef GEM5_MODE
    uint64_t* partitions = reinterpret_cast<uint64_t*>(rt->mm_malloc_global((num_lanes * num_partition_per_lane * 2) * sizeof(uint64_t)));
#else
    uint64_t* partitions = reinterpret_cast<uint64_t*>(rt->mm_malloc((num_lanes * num_partition_per_lane * 2) * sizeof(uint64_t)));
#endif

    return partitions;
}


void test_lb(UpDown::UDRuntime_t* rt, uint64_t* args, int arglen){
    // printf("%lu, %lu, %lu, %lu, %lu, %lu\n", arg0, arg1, arg2, arg3, arg4, arg5);
    UpDown::word_t TOP_FLAG_OFFSET = 0;

    // Init top flag to 0
    uint64_t val = 0;
    UpDown::networkid_t nwid(0, false, 0);
    rt->t2ud_memcpy(&val,
                          sizeof(uint64_t),
                          nwid,
                          TOP_FLAG_OFFSET /*Offset*/);
    printf("set flag\n");

#ifdef GEM5_MODE
    m5_switch_cpu();
#endif
    
    UpDown::word_t* ops_data = new UpDown::word_t[arglen];
    UpDown::operands_t ops(arglen);
    // UpDown::operands_t* ops = new UpDown::operands_t[arglen];
    for(int i=0; i<arglen; i++){
        ops.set_operand(i, args[i]);
    }
    printf("ops set\n");

    UpDown::event_t evnt_ops(spmvMSR::updown_init,                     /*Event Label*/
                             nwid,
                             UpDown::CREATE_THREAD, /*Thread ID*/
                             &ops                   /*Operands*/);
    printf("set event word\n");
    rt->send_event(evnt_ops);
    printf("Event sent to updown lane %d.\n", 0);

#ifdef GEM5_MODE
    m5_reset_stats(0,0);
#else
    UpDown::BASimUDRuntime_t* simrt = reinterpret_cast<UpDown::BASimUDRuntime_t*> (rt);
    simrt->reset_stats();
#endif

    rt->start_exec(nwid);
    printf("Waiting for terminate\n");

    // UpDown::networkid_t nwidd(8, false, 0);

    rt->test_wait_addr(nwid, TOP_FLAG_OFFSET, 1);

#ifdef GEM5_MODE
    m5_dump_reset_stats(0,0);
#else
    simrt->print_stats(0,0);
#endif

    printf("UpDown checking terminates.\n");

}

void set_arg_buffer(UpDown::UDRuntime_t* rt, int offset, uint64_t* args, int arglen){
    
    UpDown::networkid_t nwid(0, false, 0);
    UpDown::word_t val;
    for(int i=0; i < arglen; i++){
        rt->t2ud_memcpy(args+i, sizeof(UpDown::word_t), nwid, offset+i*8);
    }
    return;
}

double* gen_vector(UpDown::UDRuntime_t* rt, int length){
#ifdef GEM5_MODE
    double* v = (double*)(rt->mm_malloc_global(length*sizeof(double)));
#else
    double* v = (double*)(rt->mm_malloc(length*sizeof(double)));
#endif

#ifdef DEBUG
    printf("-------------------\nVector = %p, length = %d\n", v, length);
#endif
    for(int i=0; i < length; i++){
        v[i] = 10;
#ifdef DEBUG
        printf("Vector entry %d: value=%f\n DRAM_addr=%p\n", i, v[i], v+i);
#endif
    }
    return v;
}

int main(int argc, char* argv[]) {

    std::string fpath = std::filesystem::current_path();
    fpath = fpath + "/" + argv[1];
    std::cout << fpath <<"\n";

    int mtx_mode = std::stoi(argv[3]);

    uint64_t num_uds = strtol(argv[2], nullptr, 0);
    uint64_t num_nodes = num_uds < 32 ? 1 : num_uds/32;
    uint64_t num_uds_per_node = num_uds < 32 ? num_uds : 32;
    uint64_t num_lanes_per_ud = 64;
    uint64_t num_workers = num_nodes * num_uds_per_node * num_lanes_per_ud;

    int vlength, output_length, num_input_keys;
    double* result = NULL;

    UpDown::UDRuntime_t* rt = initialize_rt("spmvMSR", num_nodes, num_uds_per_node, num_lanes_per_ud);
    printf("Reading input kv space...\n");
    coo_kv_pair* inKVSet = gen_input_kv(rt, fpath, &vlength, &output_length, &num_input_keys, &result, mtx_mode);
    printf("Generating partition array...\n");
    uint64_t* partitions = gen_partitions(rt, num_workers, PART_PARM);
    printf("Generating output kv space...\n");
    double* outKVSet = gen_output_kv(rt, output_length);
    printf("Generating intermediate kv space...\n");
    // uint64_t* interSpace = gen_intermediate_kv(rt, num_workers, 256, 256*2);
    uint64_t* interSpace = gen_intermediate_kv_ud(rt, num_uds, 512*64, 512*2);
    // uint64_t* interSpace = NULL;
    double* vector = gen_vector(rt, vlength);

    // Write metadata to scratchpad
    UpDown::word_t BUFFER_OFFSET = 8;
    uint64_t buffer_args[5] = {(uint64_t) inKVSet, (uint64_t) num_input_keys, (uint64_t) outKVSet, 
                        (uint64_t) output_length, (uint64_t) interSpace};
    set_arg_buffer(rt, BUFFER_OFFSET, buffer_args, 5);

    /* operands
      OB_0: Pointer to the partition array (64-bit DRAM address)
      OB_1: Number of partitions per lane
      OB_2: Number of lanes
      OB_3: Pointer to vector
      OB_4:  Local offset to input metadata
      OB_5:  Local offset to output metadata
      OB_6:  Local offset to intermediate metadata
    */
    uint64_t args[7] = {(uint64_t) partitions, PART_PARM, num_workers, (uint64_t) vector, BUFFER_OFFSET, BUFFER_OFFSET+2*sizeof(uint64_t), BUFFER_OFFSET+4*sizeof(uint64_t)}; 
    test_lb(rt, args, 7);

    int tcount = 0, fcount= 0;

    delete rt;
    printf("Test UDKVMSR program finishes.\n");

// #ifdef DEBUG
    tcount = 0;
    fcount= 0;
    for (int i = 0; i < output_length; i++) {

        if (std::abs(outKVSet[i] - result[i]) < 0.001){
            tcount += 1;
        }
        else{
            printf("Output pair %d: value=%f DRAM_addr=%p\n", i, outKVSet[i], outKVSet + i);
            printf("Result %f\n", result[i]);
            fcount += 1;
        }
    }
    printf("True count %d, false count %d\n", tcount, fcount);
// #endif

    return 0;
}
