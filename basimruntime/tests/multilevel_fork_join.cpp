#include "simupdown.h"
#include "updown.h"
#include <stdlib.h>
#include <time.h>
#include <stdio.h>
#include <cstdlib>
#include <iostream>
#include <algorithm>
#include <cmath>
#include <cstdio>
#include <map>
#include <pthread.h>
#include <vector>
#include <basimupdown.h>
#ifdef GEM5_MODE
#include <gem5/m5ops.h>
#endif

using namespace UpDown;
using namespace std;
int main(int argc, char* argv[], char* envp[]){
    // read the args
     if(argc != 4){
        cout << "Usage: ./multilevel_fork_join <log2_num_forks> <level> <num_lanes>" << endl;
        return 0;
    }

    int log2_num_forks = atoi(argv[1]);
    int level = atoi(argv[2]);
    int num_lanes = atoi(argv[3]);

    if(num_lanes > 64){
        printf("num lanes cannot be greater than 64, setting it to 64.\n");
        num_lanes = 64;
    }

    cout << "multi level fork join test" << endl;
    cout << "log2_num_forks: " << log2_num_forks << endl;
    cout << "level: " << level << endl;
    cout << "num_lanes: " << num_lanes << endl;

        
    // updowns
    UpDown::ud_machine_t machine;
    machine.NumLanes = num_lanes;
    machine.NumUDs = 1;
    machine.NumStacks = 1;
    machine.NumNodes = 1;
    machine.LocalMemAddrMode = 1;

#ifdef FASTSIM  
#ifdef BASIM
    cout << "BASIM" << endl;
    UpDown::BASimUDRuntime_t *rt = new UpDown::BASimUDRuntime_t(machine,
        "multilevel_fork_join.bin",
        0);
#else

    cout << "FASTSIM" << endl;
    UpDown::SimUDRuntime_t *rt = new UpDown::SimUDRuntime_t(machine,
        "multilevel_fork_join",
        "multilevel_fork_join", 
        "./", 
        UpDown::EmulatorLogLevel::NONE);
#endif
#else
// GEM5_MODE
    cout << "GEM5, not implemented.." << endl;
    UpDown::UDRuntime_t *rt = new UpDown::UDRuntime_t();
    // UpDown::GEM5UDRuntime_t *rt = new UpDown::GEM5UDRuntime_t(machine,
    //     "multilevel_fork_join.bin",
    //     0);
#endif
    // return 0;
    srand((unsigned)time(NULL));
    // first allocate space for the vars, it is one d array. each thread has a chunk of it
   
    // word_t input_val = rand() % 1000;
    uint64_t input_val = 111;
    word_t expected_val = 0;
    // expected value
    word_t v, v0;
    v = input_val;
    v += 127;
    v -= 64;
    v *= 3;
    v /= 3;
    v0 = (word_t)v;
    v += v;
    v += v;
    v += v;
    v = v - v0;
    expected_val += v;
    expected_val *= (1 << (log2_num_forks * level));

    printf("expected val: %lu\n", expected_val);
    // expected value
    // prepare the ops
   
    UpDown::operands_t ops(5);
    ops.set_operand(0, (word_t) log2_num_forks);
    ops.set_operand(1, (word_t) level);
    ops.set_operand(2, (word_t) num_lanes);
    ops.set_operand(3, (word_t) input_val);
    ops.set_operand(4, (word_t) level);
    // write the values to their onw SPs

    // prepare the event
    UpDown::event_t evnt_ops = UpDown::event_t(0,UpDown::networkid_t(0),UpDown::CREATE_THREAD,&ops);
    rt->send_event(evnt_ops);
    rt->start_exec(UpDown::networkid_t(0));
    printf("Expecting results to be = %ld\n", expected_val);
    rt->test_wait_addr(UpDown::networkid_t(0), 0, expected_val);
    cout << "Test passed" << endl;

}
