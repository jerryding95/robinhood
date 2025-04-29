#include <iostream>
#include "updown.h"
#include <vector>
#include <thread>
#include <mutex>
#include <chrono>
#include <updown.h>
#include <simupdown.h>
#ifdef BASIM
#include <basimupdown.h>
#endif

using namespace UpDown;
using namespace std;

void test_read_write(
#ifdef BASIM  
    UpDown::BASimUDRuntime_t *,
#else
#ifdef FASTSIM
    UpDown::SimUDRuntime_t *,
#else
    UpDown::UDRuntime_t *,
#endif
#endif  
word_t* , word_t* , word_t* , int , int , int);

int main(int argc, char* argv[], char* envp[]){
    if(argc != 5 && argc != 4){
        cout << "Usage: ./dram_tests <numlanes> <numthreadsperlane> <nelemsperthread> <optional:chunk>" << endl;
        return 0;
    }
    // the args
    // 1. num lanes
    // 2. num threads per lane
    // 3. nelems per thread
    // 4. test type: read, write_sendm, write_sendmr, write_sendmops, read_and_write(sendm, sendmr, sendmops)
    //  0: read
    //  1: write_sendm
    //  2: write_sendmr
    //  3: write_sendmops
    //  4: read_and_write_sendm
    //  5: read_and_write_sendmr
    //  6: read_and_write_sendmops
    int numlanes = atoi(argv[1]);
    int numthreadsperlane = atoi(argv[2]);
    int nelemsperthread = atoi(argv[3]);
    int chunk = 0;
    if(argc == 5){
        chunk = atoi(argv[4]);
    }

    ud_machine_t machine;
    machine.NumLanes = numlanes;
    machine.NumUDs = 1;
    machine.NumStacks = 1;
    machine.NumNodes = 1;
    machine.LocalMemAddrMode = 0;

for(int i = 1; i < 9; i++){
    if(chunk != 0 && chunk != i)
        continue;
        std::string testname = "dram_tests_CHUNK" + std::to_string(i) + ".bin";
        cout << "Running test: " << testname << endl;
#ifdef BASIM
        cout << "BASIM" << endl;
        UpDown::BASimUDRuntime_t *rt = new UpDown::BASimUDRuntime_t(machine,
            testname.c_str(),
            // "dram_tests.bin",
            0);
#else
#ifdef FASTSIM
        SimUDRuntime_t *rt = new SimUDRuntime_t(machine,
            "dram_tests",
            testname.c_str(), 
            "./", 
            EmulatorLogLevel::NONE);
#else
        UDRuntime_t *rt = new UDRuntime_t();
#endif
#endif
        srand((unsigned)time(NULL));
        int total_size = numlanes * numthreadsperlane * nelemsperthread * sizeof(word_t);
        word_t* data = reinterpret_cast<word_t*>(malloc(total_size));
        word_t* dram_src = reinterpret_cast<word_t*>(rt->mm_malloc(total_size));
        word_t* dram_dst = reinterpret_cast<word_t*>(rt->mm_malloc(total_size));
        // give source some random data
        for(int i = 0; i < numlanes * numthreadsperlane * nelemsperthread; i++){
            data[i] = rand() % 10000;
            dram_src[i] = data[i];
            dram_dst[i] = 0;
        }
        // if read tests, then the data will be written to spm, starting from the second word (offset 8)
        // write the same data to spm if write test and using sendm
        // just test read then write

        test_read_write(rt, data, dram_dst, dram_src, numlanes, numthreadsperlane, nelemsperthread);
}
    // prepare the ops
    return 0;
}

void test_read_write(
#ifdef BASIM
    UpDown::BASimUDRuntime_t *rt,
#else
#ifdef FASTSIM
    UpDown::SimUDRuntime_t *rt,
#else
    UpDown::UDRuntime_t *rt,
#endif
#endif    
word_t* data, word_t* dram_dst, word_t* dram_src, int numlanes, int numthreadsperlane, int nelemsperthread){
    // ops/obs

    // 0: src
    // 1: dest - offset 8
    // 2: num lanes
    // 3: num threads per lane
    // 4: nelems per thread
    // 5: total threads/workers, lazy to compute on updown
    
    // init/entry event will always be 0, which is work distributor
    // spm first 9 elements are reserved for storeing these ops/obs
    operands_t ops(8);
    ops.set_operand(0, (word_t) dram_src);
    ops.set_operand(1, (word_t) dram_dst); // for dram_dest, for read it is bogus
    ops.set_operand(2, (word_t) numlanes);
    ops.set_operand(3, (word_t) numthreadsperlane);
    ops.set_operand(4, (word_t) nelemsperthread);
    ops.set_operand(5, (word_t) numlanes * numthreadsperlane);
    // placeholders
    ops.set_operand(6, (word_t) 0);
    ops.set_operand(7, (word_t) 0);
    event_t event_ops = event_t(0, networkid_t(0), CREATE_THREAD, &ops);
    rt->send_event(event_ops);
    rt->start_exec(networkid_t(0));
    rt->test_wait_addr(networkid_t(0), 0, 1);

    // make sure src is not changed
    for(int i = 0; i < numlanes * numthreadsperlane * nelemsperthread; i++){
        assert(dram_src[i] == data[i]);
    }
    for(int i = 0; i < numlanes * numthreadsperlane * nelemsperthread; i++){
        // cout << "dram_dst[" << i << "]: " << dram_dst[i] << ", expected: " << dram_src[i] << endl;
        assert(dram_dst[i] == dram_src[i]);
    }
    cout << "Read/Write Test passed!" << endl;

    // assertion, check the spm data
    // for(int i = 0; i < numlanes * numthreadsperlane * nelemsperthread; i++){
    //     uint64_t val;
    //     // rt->ud2t_memcpy(&val, sizeof(word_t), networkid_t(0), 8 + i);
    //     // cout << "val: " << val << ", expected: " << data[i] << endl;
    //     // assert(val == data[i]);
    // }

}

void test_read_same_address(){

}

void test_write_same_address(){

}