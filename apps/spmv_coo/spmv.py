from EFA_v2 import *

def EFA_spmv():
  efa = EFA([])
  efa.code_level = 'machine'
  state0 = State() #Only one state code 
  efa.add_initId(state0.state_id)
  efa.add_state(state0)


  event_map = {
    "spmv::init" : 0,
    "spmv::finish_emit" : 1,
    "accumulator::init" : 2,
    "accumulator::receive" : 3,
    "accumulator::terminate" : 4,
    "emitter::init" : 5,
    "emitter::startemit" : 6,
    "emitter::got_nonzero_info" : 7,
    "emitter::got_vector_info" : 8
  }

  ## UDWeave sparse matrix vector product.
  ## David Gleich (based on the Jose's initial programs)
  ## and hopefully future contributions from others.
  ## input:
  ## - a pointer to sparse matrix data as a long list of packed
  ##     long, long, double
  ##   entries. so if there are nnz entries, the data has length 24*nnz bytes
  ## - a pointer to a right hand side vector x
  ## - a pointer to an output vector y
  ## - the length of y
  ## - the number of nonzeros
  ## - a blocksize to use in mapping to threads. (currently hardcoded as 0x00200)
  ## on termination:
  ## - y will be overwritten by the entries of A*x
  ##
  ## Recall:
  ## y_i = sum_j A_{ij} x_j
  ## so for each non-zero entry (i,j,Aij), we will
  ## emit an increment Aij*xj to send to yi.
  ##
  ## Method:
  ## - for each yi we create an accumulator thread that has an "accumulate" event
  ## - for blocks of non-zeros, we create an emitter thread that reads from DRAM
  ##   and sends events to the accumulator threads
  ## Limitations:
  ## notes: this may slow down a lot for highly skewed distributions...
  ## notes: meant to be simple to get something working initially :)
  ## notes: the thread creation seems like the it needs more scalability
  ##         so we aren't creating everything from one starting thread.
  ## notes: lots of places to probably improve stuff
  ## key note: if you see // ?? that means I currently don't know exactly what to do here yet.
  ## but I think we have some idea that something can go there to make it work.
  ##
  ## this is the controller thread, it inits itself and
  ## 1. creates accumulator threads that will do the local accumulation for each entry of y
  ## 2. creates the emitter threads that will read from DRAM and send Aij*xj to y
  ## 3. sends the terminate command to the accumulators which instructs them to
  ##    write to DRAM and end.
  ## BLOCKSIZE=0x00200
  
  ##########################################
  ###### Writing code for thread spmv ######
  ##########################################
  ## Thread variable number_of_emits using Register X16
  ## Thread variable ysize using Register X17
  # Writing code for event spmv::init
  tran0 = state0.writeTransition("eventCarry", state0, state0, event_map['spmv::init'])
  ## Param nonzeros using Register X8
  ## Param x using Register X9
  ## Param y using Register X10
  ## Param nnz using Register X11
  ## Param _ysize using Register X12
  ## Param blocksize using Register X13
  ## Local Variable evw_reducer using Register X18
  ## Local Variable i using Register X19
  ## Local Variable dest using Register X23
  ## Local Variable evw_emit using Register X19
  ## compute the number of emits based on the blocksize
  ## and handle the case where we don’t easily divide 
  tran0.writeAction(f"div X11 X13 X18") 
  tran0.writeAction(f"mov_reg2reg X18 X16") # This is for casting. May be used later on
  tran0.writeAction(f"muli X16 X18 512") 
  tran0.writeAction(f"mov_reg2reg X18 X19") # This is for casting. May be used later on
  tran0.writeAction(f"compreg_gt X18 X19 X20") 
  tran0.writeAction(f"beqc X20 0 __if_init_2_post") 
  tran0.writeAction(f"__if_init_0_true: addi X16 X16 1") 
  ## save the value of ysize 
  tran0.writeAction(f"mov_reg2reg X12 X17") # This is for casting. May be used later on
  ## create a new event 
  ## - NID this is the current node id, what if I want this to go to a separate node?
  ## - emitter::init this is the UDweave routine to start the event
  ## - 3 this is the number of arguments it takes 
  tran0.writeAction(f"rshift X0 X19 11") 
  tran0.writeAction(f"andi X19 X19 65535") 
  tran0.writeAction(f"mov_imm2reg X18 0") 
  tran0.writeAction(f"ew_update_reg_2 X18 X18 X19 X19 8") 
  tran0.writeAction(f"ew_update_1 X18 X18 {event_map['accumulator::init']} 1") 
  tran0.writeAction(f"ew_update_1 X18 X18 1 2") 
  ## update the event to indicate it should create a new thread
  tran0.writeAction(f"ew_update_1 X18 X18 255 4") 
  ## TODO - use a tree creation strategy.
  ## TODO - how to make this handle more than just one node? 
  tran0.writeAction(f"mov_imm2reg X19 0") 
  tran0.writeAction(f"__for_init_3_condition: mov_reg2reg X19 X20") # This is for casting. May be used later on
  tran0.writeAction(f"compreg_gt X19 X20 X21") 
  tran0.writeAction(f"mov_reg2reg X21 X22") # This is for casting. May be used later on
  tran0.writeAction(f"beqc X22 0 __for_init_5_post") 
  ## copied almost verbatim from the broadcast example
  ## I’m not sure this dest is correct. 
  ## Create a destination ID
  tran0.writeAction(f"rshift X0 X24 11") 
  tran0.writeAction(f"andi X24 X24 65535") 
  tran0.writeAction(f"andi X24 X25 4294901760") 
  tran0.writeAction(f"andi X19 X26 63") 
  tran0.writeAction(f"add X25 X26 X23") 
  ## currently only one UD
  tran0.writeAction(f"") # This is for casting. May be used later on
  tran0.writeAction(f"add X10 X24 X25") 
  tran0.writeAction(f"send4 X18 X23 X1 X25 4") 
  ## do I need CCONT here? 
  tran0.writeAction(f"addi X19 X19 1") 
  tran0.writeAction(f"jmp __for_init_3_condition") 
  tran0.writeAction(f"__for_init_5_post: rshift X0 X20 11") 
  tran0.writeAction(f"andi X20 X20 65535") 
  tran0.writeAction(f"mov_imm2reg X19 0") 
  tran0.writeAction(f"ew_update_reg_2 X19 X19 X20 X20 8") 
  tran0.writeAction(f"ew_update_1 X19 X19 {event_map['emitter::init']} 1") 
  tran0.writeAction(f"ew_update_1 X19 X19 2 2") 
  tran0.writeAction(f"ew_update_1 X19 X19 255 4") 
  tran0.writeAction(f"mov_imm2reg X19 0") 
  tran0.writeAction(f"__for_init_6_condition: compreg_gt X19 X11 X20") 
  tran0.writeAction(f"mov_reg2reg X20 X21") # This is for casting. May be used later on
  tran0.writeAction(f"beqc X21 0 __for_init_8_post") 
  ## these will self-terminate.
  tran0.writeAction(f"rshift X0 X22 11") 
  tran0.writeAction(f"andi X22 X22 65535") 
  tran0.writeAction(f"andi X22 X23 4294901760") 
  tran0.writeAction(f"andi X19 X24 63") 
  tran0.writeAction(f"add X23 X24 X23") 
  ## currently only one UD
  tran0.writeAction(f"muli X19 X22 3") 
  tran0.writeAction(f"muli X22 X23 512") 
  tran0.writeAction(f"") # This is for casting. May be used later on
  tran0.writeAction(f"add X8 X24 X25") 
  tran0.writeAction(f"send4 X19 X23 X1 X9 X25 4") 
  tran0.writeAction(f"addi X19 X19 512") 
  tran0.writeAction(f"jmp __for_init_6_condition") 
  tran0.writeAction(f"__for_init_8_post: yield") 
  
  # Writing code for event spmv::finish_emit
  tran1 = state0.writeTransition("eventCarry", state0, state0, event_map['spmv::finish_emit'])
  ## Local Variable evw_reducer using Register X19
  ## Local Variable i using Register X20
  ## Local Variable dest using Register X24
  ## Local Variable term using Register X20
  tran1.writeAction(f"entry: subi X16 X16 1") 
  tran1.writeAction(f"comp_eq X16 X18 0") 
  tran1.writeAction(f"beqc X18 0 __if_finish_emit_1_false") 
  tran1.writeAction(f"__if_finish_emit_0_true: rshift X0 X20 11") 
  tran1.writeAction(f"andi X20 X20 65535") 
  tran1.writeAction(f"mov_imm2reg X19 0") 
  tran1.writeAction(f"ew_update_reg_2 X19 X19 X20 X20 8") 
  tran1.writeAction(f"ew_update_1 X19 X19 {event_map['accumulator::terminate']} 1") 
  tran1.writeAction(f"ew_update_1 X19 X19 1 2") 
  ## update the event to indicate it should create a new thread
  tran1.writeAction(f"mov_imm2reg X20 0") 
  tran1.writeAction(f"jmp __if_finish_emit_2_post") 
  tran1.writeAction(f"__for_finish_emit_3_condition: mov_reg2reg X20 X21") # This is for casting. May be used later on
  tran1.writeAction(f"compreg_gt X20 X21 X22") 
  tran1.writeAction(f"mov_reg2reg X22 X23") # This is for casting. May be used later on
  tran1.writeAction(f"beqc X23 0 __for_finish_emit_5_post") 
  ## send the terminate command to accumulators
  tran1.writeAction(f"rshift X0 X25 11") 
  tran1.writeAction(f"andi X25 X25 65535") 
  tran1.writeAction(f"andi X25 X26 4294901760") 
  tran1.writeAction(f"andi X20 X27 63") 
  tran1.writeAction(f"add X26 X27 X24") 
  ## currently only one UD
  tran1.writeAction(f"send4 X19 X24 X1 1 4") 
  tran1.writeAction(f"addi X20 X20 1") 
  tran1.writeAction(f"jmp __for_finish_emit_3_condition") 
  tran1.writeAction(f"__for_finish_emit_5_post: mov_reg2reg X7 X20") 
  tran1.writeAction(f"mov_imm2reg X22 1") 
  tran1.writeAction(f"mov_reg2lm X20 X22 8") 
  tran1.writeAction(f"yield_terminate") 
  tran1.writeAction(f"__if_finish_emit_1_false: yield") 
  tran1.writeAction(f"__if_finish_emit_2_post: yield") 
  
  ## this is the accumulator thread
  ## notes: in general, you'd want this for a basket of entries.
  ## and you may want more than one accumulator for each
  ## this keeps one local variable a.
  
  #################################################
  ###### Writing code for thread accumulator ######
  #################################################
  ## Thread variable a using Register X16
  ## Thread variable final using Register X17
  # Writing code for event accumulator::init
  tran2 = state0.writeTransition("eventCarry", state0, state0, event_map['accumulator::init'])
  ## Param result using Register X8
  tran2.writeAction(f"entry: mov_imm2reg X16 0.0") 
  tran2.writeAction(f"mov_reg2reg X8 X17") 
  tran2.writeAction(f"yield") 
  
  # Writing code for event accumulator::receive
  tran3 = state0.writeTransition("eventCarry", state0, state0, event_map['accumulator::receive'])
  ## Param val using Register X8
  tran3.writeAction(f"entry: fadd X16 X8 X16") 
  tran3.writeAction(f"yield") 
  
  # Writing code for event accumulator::terminate
  tran4 = state0.writeTransition("eventCarry", state0, state0, event_map['accumulator::terminate'])
  ## Param _ using Register X8
  tran4.writeAction(f"entry: send4 0 X17 X1 X16 8 2") 
  tran4.writeAction(f"yield_terminate") 
  
  ## emitter threads read a block of entries from the
  ## sparse matrix and emit products aij*xj
  ## to the accumulators
  
  #############################################
  ###### Writing code for thread emitter ######
  #############################################
  ## Thread variable x using Register X16
  ## Thread variable rowi using Register X17
  ## Thread variable valij using Register X18
  ## Thread variable nextblock using Register X19
  ## Thread variable blocksleft using Register X20
  ## Thread variable nextiterevent using Register X21
  # Writing code for event emitter::init
  tran5 = state0.writeTransition("eventCarry", state0, state0, event_map['emitter::init'])
  ## Param _x using Register X8
  ## Param blockstart using Register X9
  tran5.writeAction(f"entry: mov_reg2reg X8 X16") 
  tran5.writeAction(f"mov_reg2reg X9 X19") 
  tran5.writeAction(f"mov_imm2reg X20 512") 
  tran5.writeAction(f"rshift X2 X22 24") 
  tran5.writeAction(f"andi X22 X22 255") 
  tran5.writeAction(f"mov_imm2reg X21 0") 
  tran5.writeAction(f"ew_update_reg_2 X21 X21 X22 X22 8") 
  tran5.writeAction(f"ew_update_1 X21 X21 {event_map['emitter::startemit']} 1") 
  tran5.writeAction(f"ew_update_1 X21 X21 1 2") 
  tran5.writeAction(f"rshift X2 X22 24") 
  tran5.writeAction(f"andi X22 X22 255") 
  tran5.writeAction(f"send4 X21 X22 X1 1 4") 
  tran5.writeAction(f"yield") 
  
  # Writing code for event emitter::startemit
  tran6 = state0.writeTransition("eventCarry", state0, state0, event_map['emitter::startemit'])
  ## Param _ using Register X8
  ## Local Variable curblock using Register X24
  tran6.writeAction(f"entry: comp_eq X20 X22 0") 
  tran6.writeAction(f"mov_reg2reg X22 X23") # This is for casting. May be used later on
  tran6.writeAction(f"beqc X23 0 __if_startemit_1_false") 
  tran6.writeAction(f"__if_startemit_0_true: yield_terminate") 
  tran6.writeAction(f"jmp __if_startemit_2_post") 
  tran6.writeAction(f"__if_startemit_1_false: mov_reg2reg X19 X24") 
  tran6.writeAction(f"addi X24 X19 24") 
  tran6.writeAction(f"subi X20 X20 1") 
  tran6.writeAction(f"mov_imm2reg X29 {event_map['emitter::got_nonzero_info']}") 
  tran6.writeAction(f"send 0 X24 X29 0 24 2") 
  tran6.writeAction(f"__if_startemit_2_post: yield") 
  
  # Writing code for event emitter::got_nonzero_info
  tran7 = state0.writeTransition("eventCarry", state0, state0, event_map['emitter::got_nonzero_info'])
  ## Param localdata_from_dram using Register X8
  ## Local Variable colj using Register X22
  ## Local Variable valij_long using Register X23
  ## extract
  tran7.writeAction(f"mov_lm2reg X8 X17 8") 
  tran7.writeAction(f"mov_imm2reg X29 8") 
  tran7.writeAction(f"add X29 X8 X29") 
  tran7.writeAction(f"mov_lm2reg X29 X22 8") 
  tran7.writeAction(f"mov_imm2reg X29 16") 
  tran7.writeAction(f"add X29 X8 X29") 
  tran7.writeAction(f"mov_lm2reg X29 X23 8") 
  ## valij = (double) valij_int; // typecast, tbd… 
  tran7.writeAction(f"mov_imm2reg X18 1.0") 
  ## now read from dram to get the right value of x, and send along the
  ## local data.
  ## ?? okay, I guess this works slightly differently than I thought. 
  ## I was hoping we could forward local data to the destination as well, sort 
  ## of like the send_event. But that doesn’t seem to be the case. 
  tran7.writeAction(f"") # This is for casting. May be used later on
  tran7.writeAction(f"add X16 X24 X25") 
  tran7.writeAction(f"mov_imm2reg X29 {event_map['emitter::got_vector_info']}") 
  tran7.writeAction(f"send 0 X25 X29 0 8 2") 
  tran7.writeAction(f"yield") 
  
  # Writing code for event emitter::got_vector_info
  tran8 = state0.writeTransition("eventCarry", state0, state0, event_map['emitter::got_vector_info'])
  ## Param pxj using Register X8
  ## Local Variable xj using Register X22
  ## Local Variable val using Register X23
  ## Local Variable dest using Register X24
  ## Local Variable evw_emit using Register X25
  tran8.writeAction(f"entry: mov_lm2reg X8 X22 8") 
  tran8.writeAction(f"fmul X22 X18 X23") 
  ## build the destination ID for yi 
  tran8.writeAction(f"rshift X0 X25 11") 
  tran8.writeAction(f"andi X25 X25 65535") 
  tran8.writeAction(f"andi X25 X26 4294901760") 
  tran8.writeAction(f"andi X17 X27 63") 
  tran8.writeAction(f"mov_reg2reg X26 X28") # This is for casting. May be used later on
  tran8.writeAction(f"add X26 X28 X24") 
  tran8.writeAction(f"mov_imm2reg X25 0") 
  tran8.writeAction(f"ew_update_reg_2 X25 X25 X24 X24 8") 
  tran8.writeAction(f"ew_update_1 X25 X25 {event_map['accumulator::receive']} 1") 
  tran8.writeAction(f"ew_update_1 X25 X25 1 2") 
  tran8.writeAction(f"send4 X25 X24 X1 X23 4") 
  tran8.writeAction(f"rshift X2 X26 24") 
  tran8.writeAction(f"andi X26 X26 255") 
  tran8.writeAction(f"send4 X21 X26 X1 1 4") 
  tran8.writeAction(f"yield") 
  
  return efa
