// #include "simupdown.h"
#include "basimupdown.h"
#include "updown.h"


uint64_t fibonacci(uint64_t n){
	if(n==0)
		return 0;
	if(n==1)
		return 1;
	return (fibonacci(n-1) + fibonacci(n-2));
}



int main(int argc, char *argv[]){
    if (argc != 2){
        printf("Input: ./fibonacci <n>\n");
        return 1;
    }

    int n = atoi(argv[1]);

	UpDown::ud_machine_t machine;
	machine.NumLanes = 1;
	machine.NumUDs = 1;
	machine.NumStacks = 1;
	machine.NumNodes = 1;
	machine.LocalMemAddrMode = 1;

#ifdef GEM5_MODE
	UpDown::UDRuntime_t *rt = new UpDown::UDRuntime_t(machine);
#else
	UpDown::BASimUDRuntime_t *rt = new UpDown::BASimUDRuntime_t(machine, "fibonacci_recursion.bin", 0);
	// UpDown::SimUDRuntime_t *rt = new UpDown::SimUDRuntime_t(machine,
	// 	"fibonacci_recursion",
	// 	"fibonacci_recursion", 
	// 	"./",
	// 	UpDown::EmulatorLogLevel::FULL_TRACE);
#endif
	UpDown::networkid_t nwid = UpDown::networkid_t(0,0,0,0);
	UpDown::word_t ops_data[4];
	UpDown::operands_t ops(4, ops_data);
	ops.set_operand(0, n);
	ops.set_operand(1, 1);
	ops.set_operand(2, 1);
	ops.set_operand(3, 0);
	uint64_t init_zero = 0;
	rt->t2ud_memcpy(&init_zero, 8, nwid, 0);
    rt->t2ud_memcpy(&init_zero, 8, nwid, 8);
	UpDown::event_t event_ops(  0 /*Event Label*/,
                            	nwid,
                                UpDown::CREATE_THREAD /*Thread ID*/,
                                &ops /*Operands*/);
    rt->send_event(event_ops);
    rt->start_exec(nwid);
	
	uint64_t updown_result = 0;
	uint64_t cpu_result = fibonacci(n);

	rt->test_wait_addr(nwid, 0, 1);
	rt->ud2t_memcpy(&updown_result,
                    sizeof(uint64_t),
                    nwid,
                    8);
	if(updown_result == cpu_result)
		printf("TEST PASSED\n fibonacci(%ld) = %ld\n",n,updown_result);
	else
		printf("TEST FAILED\n fibonacci(%ld) in cpu = %ld, fibonacci(%ld) in updown = %ld\n", n, cpu_result, n, updown_result);

	return 0;
}
