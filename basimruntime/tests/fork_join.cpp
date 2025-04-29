

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

    if(argc != 3){
        cout << "Usage: ./fork_join <num_lanes> <num_threads_per_lane>" << endl;
        return 0;
    }

    // read the args
    int num_lanes = atoi(argv[1]);
    int num_threads_per_lane = atoi(argv[2]);
    // int num_elems_per_thread = atoi(argv[3]);
    // updowns
    UpDown::ud_machine_t machine;
    machine.NumLanes = num_lanes;
    machine.NumUDs = 1;
    machine.NumStacks = 1;
    machine.NumNodes = 1;
    machine.LocalMemAddrMode = 1;


    char dir[100] = "efas/";
	strcat(dir,"fork_join");
	printf("%s\n", dir);

#ifdef FASTSIM
#ifdef BASIM 
    cout << "BASIM" << endl;   
    UpDown::BASimUDRuntime_t *rt = new UpDown::BASimUDRuntime_t(machine,
        "fork_join.bin",
        0);
#else
    cout << "FASTSIM" << endl;
    UpDown::SimUDRuntime_t *rt = new UpDown::SimUDRuntime_t(machine,
        "fork_join",
        "fork_join", 
        "./", 
        UpDown::EmulatorLogLevel::NONE); 
#endif
#else
    cout << "GEM5" << endl;
    UpDown::UDRuntime_t *rt = new UpDown::UDRuntime_t();
#endif

    // return 0;
    srand((unsigned)time(NULL));
    // first allocate space for the vars, it is one d array. each thread has a chunk of it
    word_t* data = reinterpret_cast<word_t*>(malloc(sizeof(word_t) * num_lanes * num_threads_per_lane));
    // prepare random data
    for(int i = 0; i < num_lanes * num_threads_per_lane; i++){
        data[i] = rand() % 1000;
    }
    word_t expected_val = 0;
    for(int i = 0; i < num_lanes * num_threads_per_lane; i++){
        word_t temp = data[i];
        word_t temp0 = temp;
        temp += 127;
        temp -= 64;
        temp *= 3;
        temp /= 3;
        temp0 = (word_t)temp;
        temp += temp;
        temp += temp;
        temp += temp;
        temp = temp - temp0;
        // printf("temp[%d]: %lu\n",i, temp);
        expected_val += temp;
    }
    printf("expected val: %lu\n", expected_val);
    // expected value
    // prepare the ops
    word_t offset = 8;
    UpDown::operands_t ops(4);
    ops.set_operand(0, (word_t) offset);
    ops.set_operand(1, (word_t) num_lanes);
    ops.set_operand(2, (word_t) num_threads_per_lane);
    ops.set_operand(3, (word_t) num_lanes * num_threads_per_lane);
    // write the values to their onw SPs
    for(int i = 0; i < num_lanes; i++){
        word_t vzero = 0;
        word_t val = 0;
        rt->t2ud_memcpy(&vzero, sizeof(UpDown::word_t), UpDown::networkid_t(i, 0), 0);
        for(int j = 0; j < num_threads_per_lane; j++){
            // prepare the event
            UpDown::networkid_t nwid(i, 0);
            // write the data 
            // cout << "writing "<< data[i*num_threads_per_lane + j] << endl;
            rt->t2ud_memcpy(&data[i * num_threads_per_lane + j], sizeof(UpDown::word_t), nwid, offset + j * sizeof(UpDown::word_t));
            rt->ud2t_memcpy(&val, sizeof(UpDown::word_t), nwid, offset + j * sizeof(UpDown::word_t));
            // cout << "val: " << val << endl;
            // printf("writing %lu to %lu\n", data[i * num_threads_per_lane + j], offset + j * sizeof(UpDown::word_t));
        }
    }

    // prepare the event
    UpDown::event_t evnt_ops = UpDown::event_t(0,UpDown::networkid_t(0),UpDown::CREATE_THREAD,&ops);
    rt->send_event(evnt_ops);
    rt->start_exec(UpDown::networkid_t(0));
    printf("Expecting results to be = %ld, expect 'Test passed!' after this line. \n", expected_val);
    rt->test_wait_addr(UpDown::networkid_t(0), 0, expected_val);
    rt->test_addr(UpDown::networkid_t(0), 0, expected_val);
    cout << "Test passed!" << endl;
    // cout << "Test done, check the results see if they are correct" << endl;
}
