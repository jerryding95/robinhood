#include "dramalloc.hpp"
#include <iostream>
#include "updown.h"
#include <vector>
#include <thread>
#include <mutex>
#include <chrono>
#include <updown.h>
#ifdef GEM5_MODE
#include <gem5/m5ops.h>
#endif
#include <simupdown.h>
#ifdef BASIM
#include <basimupdown.h>
#endif
#define DRAMALLOC_NWID 0
using namespace std;
using namespace UpDown;
std::mutex rt_lock;
std::mutex dram_lock;


void runAllocator(
#ifdef FASTSIM
UpDown::SimUDRuntime_t *rt,
#else
UpDown::UDRuntime_t *rt,
#endif
dramalloc::Allocator *allocator, ud_machine_t machine, mutex* rt_lock, int nrNode, int blockSize, int sharedSegSize);

void runDRAMallocTests(
#ifdef FASTSIM
UpDown::SimUDRuntime_t *rt,
#else
UpDown::UDRuntime_t *rt,
#endif
mutex* rt_lock, int nelemsA, int startnodeA, int blocksizeA, int nnodesA, int nelemsB, int startnodeB, int blocksizeB, int nnodesB);
int main(int argc, char** argv){
    if(argc != 9){
        cout << "argc = " << argc << endl;
        cout << "Usage: ./testDramalloc <nelemsA> <startnodeA> <blocksizeA> <nnodesA> <nelemsB> <startnodeB> <blocksizeB> <nnodesB>" << endl;
        return -1;
    }
    dram_lock.lock();
    // allocate array A
    int nelemsA = atoi(argv[1]);
    int startnodeA = atoi(argv[2]);
    int blocksizeA = atoi(argv[3]);
    int nnodesA = atoi(argv[4]);
    // allocate array B
    int nelemsB = atoi(argv[5]);
    int startnodeB = atoi(argv[6]);
    int blocksizeB = atoi(argv[7]);
    int nnodesB = atoi(argv[8]);

    UpDown::ud_machine_t machine;
    machine.NumLanes=64;   
    machine.NumUDs=2;
    machine.NumStacks=1;
    machine.NumNodes=1;
#ifdef FASTSIM
#ifdef BASIM
    cout << "BASIM MODE" << endl;
    UpDown::BASimUDRuntime_t *rt = new UpDown::BASimUDRuntime_t(machine,
        "testDramalloc.bin",
        0);
#else 
    cout << "FASTSIM MODE" << endl;
    UpDown::SimUDRuntime_t *rt = new UpDown::SimUDRuntime_t(
        machine,
        "testDramalloc",
        "testDramalloc",
        "./",
        UpDown::EmulatorLogLevel::NONE
    );

#endif
#else
    cout << "GEM5 MODE" << endl;
    UpDown::UDRuntime_t *rt = new UpDown::UDRuntime_t();
#endif
    vector<thread> threads;
    dramalloc::Allocator *allocator;
    threads.push_back(std::thread(runAllocator, rt, allocator, machine, &rt_lock, nnodesB, blocksizeB, nelemsB*8*16));
    threads.push_back(std::thread(runDRAMallocTests, rt, &rt_lock, nelemsA, startnodeA, blocksizeA, nnodesA, nelemsB, startnodeB, blocksizeB, nnodesB));
    for (auto& th : threads) th.join();
    cout << "TOP DONE!" << endl;
    return 0;
}
void runAllocator(
#ifdef FASTSIM
UpDown::SimUDRuntime_t *rt,
#else
UpDown::UDRuntime_t *rt,
#endif

dramalloc::Allocator *allocator, ud_machine_t machine, mutex* rt_lock, int nrNode, int blockSize, int sharedSegSize){
    cout << "Start Allocator:" << "nrNode = " << nrNode << ", blockSize = " << blockSize << ", sharedSegSize = " << sharedSegSize << endl;
    allocator = new dramalloc::Allocator(nrNode /*nrNode*/, blockSize /*minSize*/, sharedSegSize/*sharedSegSize*/, 
    machine /*machineConfig*/, networkid_t(0, DRAMALLOC_NWID) /*nwid-cl0ud1*/, rt /*runtime*/, rt_lock /*runtime lock*/);
    
    // cout << "Running allocator" << endl;
    // flag = 1;
    cout << "Flag set to 1" << endl;
    dram_lock.unlock();
    allocator->run();
}

void runDRAMallocTests(
#ifdef FASTSIM
UpDown::SimUDRuntime_t *rt,
#else
UpDown::UDRuntime_t *rt,
#endif
mutex* rt_lock, int nelemsA, int startnodeA, int blocksizeA, int nnodesA, int nelemsB, int startnodeB, int blocksizeB, int nnodesB){
    dram_lock.lock();
    cout << "Running UDSHMEM" << endl;

    // allocate 1-D array A
    rt_lock->lock();
    UpDown:: word_t *arrayA = reinterpret_cast<UpDown::word_t*>(rt->mm_malloc(nelemsA * sizeof(UpDown::word_t)));
    UpDown:: word_t ops_data[6];
    UpDown:: operands_t ops(6, ops_data);

    ops.set_operand(0, (UpDown::word_t) nelemsB);
    ops.set_operand(1, (UpDown::word_t) startnodeB);
    ops.set_operand(2, (UpDown::word_t) blocksizeB);
    ops.set_operand(3, (UpDown::word_t) nnodesB);
    ops.set_operand(4, (UpDown::word_t) nelemsA);
    ops.set_operand(5, (UpDown::word_t) arrayA);


    UpDown::networkid_t nwid(0);
    UpDown::event_t evnt_ops(
        0, nwid, 
        UpDown::CREATE_THREAD, &ops
    );
    
    cout << "Sending event" << endl;
    rt->send_event(evnt_ops);
    rt->start_exec(nwid);
    rt_lock->unlock();

    uint64_t val;
    UpDown::networkid_t dnwid(0, DRAMALLOC_NWID);


    while(1){
        // no need for locks
        rt_lock->lock();
        rt->ud2t_memcpy(&val, sizeof(uint64_t), dnwid, 0);
        rt_lock->unlock();
        if(val){
            // cout << "DRAMALLOC: " << val << endl;
            break;
        }
           

    }
    uint64_t p;
    rt_lock->lock();
    rt->ud2t_memcpy(&p, sizeof(uint64_t), dnwid, 256);
    rt_lock->unlock();
    cout << "DRAMALLOC: " << p << endl;
    for(int i = 0; i < 8; i++){
        cout << "DRAMALLOC values: " <<((uint64_t *)p + i) << " = " << *((uint64_t *)p + i) << endl;
    }
    for(int i = 0; i < 32; i++){
        rt_lock->lock();
        rt->ud2t_memcpy(&val, sizeof(uint64_t), networkid_t(0,0), 8 * i);
        rt_lock->unlock();
        cout<< "val = " << val << endl;
        // if(i==2)
        //     for(int j = 0; j < 32; j++){
                
        //         cout<< "dram = " << *((uint64_t *)val + j)  << endl;
        //     }
    }
    cout << "DRAMALLOC terminated successfully." << endl;
}
