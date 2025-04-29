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

#define NUM_LANE_PER_UD 64
#define NUM_UD_PER_CLUSTER 4
#define NUM_CLUSTER_PER_NODE 8

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

int main(int argc, char* argv[]) {

    std::string fpath = std::filesystem::current_path();
    fpath = fpath + "/" + argv[1];
    std::cout << fpath <<"\n";
    uint64_t num_nodes = 1;
    uint64_t num_uds_per_node = 1;
    uint64_t num_lanes_per_ud = 64;
    uint64_t num_workers = num_nodes * num_uds_per_node * num_lanes_per_ud;


    UpDown::UDRuntime_t* rt = initialize_rt(num_nodes, num_uds_per_node, num_lanes_per_ud);


    printf("before test\n");
    

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
    ops.set_operand(0, 0);
    ops.set_operand(1, 0);

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



    delete rt;
    printf("Test UDKVMSR program finishes.\n");

    return 0;
}