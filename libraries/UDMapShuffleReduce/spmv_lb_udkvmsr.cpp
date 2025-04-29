#include "simupdown.h"

#include <cstdio>
#include <cstdlib>
#include <iostream>
#include <fstream>
#include <filesystem>
#include <cmath>
#include <basimupdown.h>

#ifdef GEM5_MODE
 #include <gem5/m5ops.h>
#endif

// #define DEBUG

#define NUM_LANE_PER_UD 64
#define NUM_UD_PER_CLUSTER 4
#define NUM_CLUSTER_PER_NODE 8

#define PART_PARM 1

struct coo_kv_pair{
    uint64_t key;
    double value;
};


UpDown::UDRuntime_t* initialize_rt(uint64_t num_nodes, uint64_t num_uds_per_node, uint64_t num_lanes_per_ud){
    // Set up machine parameters
    UpDown::ud_machine_t machine;
    machine.NumLanes = num_lanes_per_ud;
    machine.NumUDs = std::min((int)num_uds_per_node, NUM_UD_PER_CLUSTER);
    machine.NumStacks = std::ceil((double)num_uds_per_node / NUM_UD_PER_CLUSTER);
    machine.NumNodes = num_nodes;
    machine.LocalMemAddrMode = 1;

#ifdef GEM5_MODE
    UpDown::UDRuntime_t *rt = new UpDown::UDRuntime_t(machine);
#else
#ifdef BASIM
    UpDown::BASimUDRuntime_t* rt = new UpDown::BASimUDRuntime_t(machine, "spmvLBTestEFA.bin", 0);
    printf("using basim\n");
#else
    UpDown::SimUDRuntime_t *rt = new UpDown::SimUDRuntime_t(machine, "spmvLBTestEFA.py", "spmvLBTestEFA", "./", UpDown::EmulatorLogLevel::FULL_TRACE);
#endif
#endif

#ifdef DEBUG
    printf("=== Base Addresses ===\n");
    rt->dumpBaseAddrs();
    printf("\n=== Machine Config ===\n");
    rt->dumpMachineConfig();
#endif

    return rt;
}


coo_kv_pair* gen_input_kv(UpDown::UDRuntime_t* rt, std::string fpath, int* vlength, int* output_length, int* num_input_keys, double** result){
    int num_row, num_col, num_lines;
    std::string line;
    std::ifstream file(fpath);
    if (!file.is_open()){
        std::cout << "Unable to open file"; 
        exit(-1);
    }

    // Ignore comments headers
    while (file.peek() == '%') file.ignore(2048, '\n');

    // Read number of rows and columns
    file >> num_row >> num_col >> num_lines;
    *output_length = num_row;
    *vlength = num_col;
    *num_input_keys = num_lines;
    *result = (double*) rt->mm_malloc(num_row * sizeof(double));
    coo_kv_pair* inKVSet = reinterpret_cast<coo_kv_pair*>(rt->mm_malloc(num_lines * sizeof(coo_kv_pair)));
    

#ifdef DEBUG
    printf("-------------------\ninKVSet = %p\n", inKVSet);
    printf("rows: %d, columns: %d, lines: %d\n", num_row, num_col, num_lines);
#endif

    for (int i = 0; i < num_lines; i++){
        double val;
        int row, col;
        file >> row >> col >> val;
        inKVSet[i].key = row-1;
        inKVSet[i].key <<= 32;
        inKVSet[i].key += col-1;
        inKVSet[i].value = val;
#ifdef DEBUG
        printf("Input pair %d: key=%ld value=%f row=%d column %d DRAM_addr=%p\n", i, inKVSet[i].key, inKVSet[i].value, inKVSet[i].key>>32, inKVSet[i].key&0xffffffff, inKVSet + i);
#endif
        (*result)[row-1] += 10*val;
    }

    file.close();
    
    return inKVSet;
}


coo_kv_pair* gen_output_kv(UpDown::UDRuntime_t* rt, int output_length){
    coo_kv_pair* outKVSet = reinterpret_cast<coo_kv_pair*>(rt->mm_malloc(output_length * sizeof(coo_kv_pair)));

#ifdef DEBUG
    printf("-------------------\noutKVSet = %p\n", outKVSet);
#endif

    for (int i = 0; i < output_length; i++) {
        outKVSet[i].key = i;
        outKVSet[i].value = 0;

#ifdef DEBUG
        printf("Output pair %d: key=%ld value=%f DRAM_addr=%p\n", i, outKVSet[i].key, outKVSet[i].value, outKVSet + i);
#endif
    }

    return outKVSet;
}


uint64_t* gen_intermediate_kv(UpDown::UDRuntime_t* rt, int vlength, int output_length){
    uint64_t* interKVSpace = reinterpret_cast<uint64_t*>(rt->mm_malloc(output_length * (3 * sizeof(uint64_t))));

#ifdef DEBUG
    printf("-------------------\ninterKVSet = %p\n", interKVSpace);
#endif

//     for (int i = 0; i < output_length; i++) {
//         interKVSpace[output_length + i*2] = 0;
//         // interKVSpace[output_length + i*2 + 1] = (uint64_t) reinterpret_cast<uint64_t*>(rt->mm_malloc(vlength * sizeof(uint64_t)));
//         interKVSpace[output_length + i*2 + 1] = (uint64_t) reinterpret_cast<uint64_t*>(rt->mm_malloc(10 * sizeof(uint64_t)));

// // #ifdef DEBUG
//         printf("Intermediate kv entry %d: num=%ld pointer=%ld DRAM_addr=%p\n", i, interKVSpace[output_length + i*2], interKVSpace[output_length + i*2 + 1], interKVSpace + output_length + i*2);
// // #endif
    // }

    int bin_size = 20;
    uint64_t* p_inter = reinterpret_cast<uint64_t*>(rt->mm_malloc(output_length * (bin_size * sizeof(uint64_t))));
    for (int i = 0; i < output_length; i++) {
        interKVSpace[output_length + i*2] = 0;
        interKVSpace[output_length + i*2 + 1] = (uint64_t) (p_inter + bin_size*i);

        // printf("Intermediate kv entry %d: num=%ld pointer=%lx DRAM_addr=%p\n", i, interKVSpace[output_length + i*2], interKVSpace[output_length + i*2 + 1], interKVSpace + output_length + i*2);
    }

    return interKVSpace;
}


coo_kv_pair** gen_partitions(UpDown::UDRuntime_t* rt, uint64_t num_workers, uint64_t num_input_keys, coo_kv_pair* inKVSet){
    uint64_t num_partitions = num_workers;
    uint64_t num_pairs_per_part = num_input_keys/num_workers;
    int extra_pairs = num_input_keys - (num_partitions*num_pairs_per_part);
    printf("generating partition: num_input_keys %lu, num_partitions %lu, num_pairs_per_part %lu, extra_pairs %d\n", 
        num_input_keys, num_partitions, num_pairs_per_part, extra_pairs);

    coo_kv_pair** partitions = reinterpret_cast<coo_kv_pair**>(rt->mm_malloc((num_partitions + 1) * sizeof(coo_kv_pair*)));
    int ind = 0;
#ifdef DEBUG
    printf("-------------------\nparitions = %p\n", partitions);
#endif

    for (int i = 0; i < num_partitions+1; i++) {
        partitions[i] = inKVSet + ind;

#ifdef DEBUG
        printf("Partition %d: pair_id=%ld, key=%ld value=%f base_pair_addr=%p, part_entry_addr=%p\n",
            i, ind, partitions[i]->key, partitions[i]->value, partitions[i], partitions + i);
#endif
        ind += extra_pairs-- <= 0 ? num_pairs_per_part : num_pairs_per_part+1;
    }

    return partitions;
}


void test_lb(UpDown::UDRuntime_t* rt, uint64_t arg0, uint64_t arg1, uint64_t arg2, uint64_t arg3, uint64_t arg4, uint64_t arg5){
    printf("%lu, %lu, %lu, %lu, %lu, %lu\n", arg0, arg1, arg2, arg3, arg4, arg5);
    UpDown::word_t TOP_FLAG_OFFSET = 512;

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
    
    /* operands
    OB_0: Pointer to partitions (64-bit DRAM address)
    OB_1: Pointer to inKVSet (64-bit DRAM address)
    OB_2: Input kvset length
    OB_3: Pointer to outKVSet (64-bit DRAM address)
    OB_4: Output kvset length
    */
    UpDown::word_t ops_data[6];
    UpDown::operands_t ops(6);
    ops.set_operand(0, arg0);
    ops.set_operand(1, arg1);
    ops.set_operand(2, arg2);
    ops.set_operand(3, arg3);
    ops.set_operand(4, arg4);
    ops.set_operand(5, arg5);

    printf("ops set\n");

    UpDown::event_t evnt_ops(1,                     /*Event Label*/
                             nwid,
                             UpDown::CREATE_THREAD, /*Thread ID*/
                             &ops                   /*Operands*/);
    printf("set event word\n");
    rt->send_event(evnt_ops);
    printf("Event sent to updown lane %d.\n", 0);

#ifdef GEM5_MODE
    m5_reset_stats(0,0);
#endif

    rt->start_exec(nwid);
    printf("Waiting for terminate\n");

    // UpDown::networkid_t nwidd(8, false, 0);

    rt->test_wait_addr(nwid, TOP_FLAG_OFFSET, 1);

#ifdef GEM5_MODE
    m5_dump_reset_stats(0,0);
#endif

    printf("UpDown checking terminates.\n");

}


int main(int argc, char* argv[]) {

    std::string fpath = std::filesystem::current_path();
    fpath = fpath + "/" + argv[1];
    std::cout << fpath <<"\n";
    uint64_t num_nodes = 1;
    uint64_t num_uds_per_node = 1;
    uint64_t num_lanes_per_ud = 64;
    uint64_t num_workers = num_nodes * num_uds_per_node * num_lanes_per_ud;

    int vlength, output_length, num_input_keys;

    UpDown::UDRuntime_t* rt = initialize_rt(num_nodes, num_uds_per_node, num_lanes_per_ud);

    // double* result = (double*) malloc(1200 * sizeof(double));
    // for (int i = 0; i < 1200; i++){
    //     result[i] = 0;
    // }
    double* result = NULL;
    coo_kv_pair* inKVSet = gen_input_kv(rt, fpath, &vlength, &output_length, &num_input_keys, &result);
    coo_kv_pair** partitions = gen_partitions(rt, num_workers, num_input_keys, inKVSet);
    coo_kv_pair* outKVSet = gen_output_kv(rt, output_length);
    uint64_t* interKVSpace = gen_intermediate_kv(rt, vlength, output_length);

    fflush(stdout);

    printf("before test\n");
    test_lb(rt, (uint64_t) partitions, (uint64_t) inKVSet, num_input_keys, (uint64_t) outKVSet, output_length, (uint64_t) interKVSpace);

    delete rt;
    printf("Test UDKVMSR program finishes.\n");


//     int tcount = 0, fcount= 0;
//     for (int i = 0; i < output_length; i++) {
// #ifdef DEBUG
//         printf("Output pair %d: key=%ld value=%f DRAM_addr=%p\n", i, outKVSet[i].key, outKVSet[i].value, outKVSet + i);
//         printf("Result %f\n", result[i]);
// #endif
//         if (outKVSet[i].value - result[i] < 0.001){
//             tcount += 1;
//         }
//         else{
//             fcount += 1;
//         }
//     }

//     printf("True count %d, false count %d\n", tcount, fcount);


    return 0;
}
