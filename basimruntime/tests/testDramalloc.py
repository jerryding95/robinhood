from EFA_v2 import *
import sys, os
enable_debug = False
sys.path.insert(1, os.getcwd() +'/../../libraries/dramalloc')
from dramalloc import TranslationEntryInstaller
def testDramalloc():
    def printu(tran, msg):
        if enable_debug:
            return tran.writeAction(f"print {msg}")
        else:
            return None
    efa = EFA([])
    efa.code_level = 'machine'

    
    state0 = State() #Initial State
    efa.add_initId(state0.state_id)
    efa.add_state(state0)
    
    event_map = {
        'tei_installer_request_sender': 500,
        'tei_installer': 501,
        'tei_terminate': 502,
        'tei_argument_ptr_getter': 503,
        'init': 0,
        'allocate_B': 1,
        'after_allocation': 2,
        'shmem_get': 3,
        'terminate': 4,
        'after_term': 5,
        'bogus': 6,
    }

    
    tei = TranslationEntryInstaller(1, 1, 1, enable_debug) # 1 node, 8 clusters, 4 uds
    ttran0 = state0.writeTransition("eventCarry", state0, state0, event_map['tei_installer_request_sender'])
    tei.implement_installer_request_sender(ttran0)
    ttran1 = state0.writeTransition("eventCarry", state0, state0, event_map['tei_installer'])
    tei.implement_installer_event(ttran1)
    ttran2 = state0.writeTransition("eventCarry", state0, state0, event_map['tei_terminate'])
    tei.implement_termination_event(ttran2)
    ttran3 = state0.writeTransition("eventCarry", state0, state0, event_map['tei_argument_ptr_getter'])
    tei.implement_argument_ptr_getter_event(ttran3)
    

    # drammalloc uses SMP [0-7]
    # for safety, we can use [16:] for your application
    INIT_OFFSET = 128 # 0-128 bytes reserved for the installer
    REQ_OFFSET = 256 # 128-256 reserved for incoming obs,
    B_OFFSET = 1024 # 256-1024 bytes reserved for the request parameters
    # 1024 store the B array pointer
    
    # event<init> 0: read OBs, get: nelemsB, startnodeB, blocksizeB, nnodesB, nelemsA, arrayA
    # write those OBs to the SPM, then send a argument_ptr_getter_event to get the gseg ptr
    # allocate B, writing the parameters to the DRAM, so it can be read by the installer
    tran0 = state0.writeTransition("eventCarry", state0, state0, event_map['init'])
    NELEMS_B = 'X16'
    STARTNODE_B = 'X17'
    BLOCKSIZE_B = 'X18'
    NNODES_B = 'X19'
    NELEMS_A = 'X20'
    ARRAY_A = 'X21'
    SPPTR = 'X22'
    EVW = 'X23'
    
    EVW_TEMP0 = 'X31'
    EVW_TEMP1 = 'X30'
    # read the obs
    tran0.writeAction(f"addi X8 {NELEMS_B} 0")
    tran0.writeAction(f"addi X9 {STARTNODE_B} 0")
    tran0.writeAction(f"addi X10 {BLOCKSIZE_B} 0")
    tran0.writeAction(f"addi X11 {NNODES_B} 0")
    tran0.writeAction(f"addi X12 {NELEMS_A} 0")
    tran0.writeAction(f"addi X13 {ARRAY_A} 0")
    
    # move the obs to the SPM
    tran0.writeAction(f"addi X7 {SPPTR} {INIT_OFFSET}")
    tran0.writeAction(f"movrl {NELEMS_B} 0({SPPTR}) 1 8")
    tran0.writeAction(f"movrl {STARTNODE_B} 0({SPPTR}) 1 8")
    tran0.writeAction(f"movrl {BLOCKSIZE_B} 0({SPPTR}) 1 8")
    tran0.writeAction(f"movrl {NNODES_B} 0({SPPTR}) 1 8")
    tran0.writeAction(f"movrl {NELEMS_A} 0({SPPTR}) 1 8")
    tran0.writeAction(f"movrl {ARRAY_A} 0({SPPTR}) 1 8")
    
    # send the argument_ptr_getter_event
    tran0.writeAction(f"evii {EVW} 503 255 {0b0101}")
    tran0.writeAction(f"evi {EVW} {EVW} 0 {0b1000}") # dramalloc is using lane 0
    
    # reset ptr to the INIT_OFFSET, get the argument_ptr_getter_event
    tran0.writeAction(f"addi X7 {SPPTR} {INIT_OFFSET}")
    tran0.writeAction(f"sendr3_wret {EVW} {event_map['allocate_B']} X16 X17 X18 {EVW_TEMP0} {EVW_TEMP1}")
    tran0.writeAction(f"yield")
    
    
    # event<allocate_B> 1: first OB will be the gseg ptr, then you know where to write the OBs
    # write the following to SPM, get from reading the SPM
    # reqType: 1; networkID: 0, still on the same lane; returnEvent: <after_allocation>
    # blockSize: the size of the blocks (should be the same as the one in the installer, and 8*gsegSize)
    # size: the size of the array, has to be a multiple of blockSize
    # nrNodes: the number of nodes in the array
    # startNode: the nodeID of the first node in the array
    tran1 = state0.writeTransition("eventCarry", state0, state0, event_map['allocate_B'])
    # read the gseg ptr
    NELEMS_B = 'X16'
    STARTNODE_B = 'X17' # offset=8
    BLOCKSIZE_B = 'X18' # offset=16
    NNODES_B = 'X19' # offset=24
    NELEMS_A = 'X20'
    ARRAY_A = 'X21'
    SPPTR = 'X22'
    EVW = 'X23'
    
    ADDR = 'X24'
    VAL = 'X25'
    RSPPTR = 'X26'
    NBYTES_B = 'X27'
    
    TEMP0 = "X31"
    # tran1.writeAction(f"print 'Allocating B'")
    printu(tran1, "'Allocating B'")
    tran1.writeAction(f"addi X8 {ADDR} 0")
    
    # construct a request
    tran1.writeAction(f"addi X7 {SPPTR} {REQ_OFFSET}")
    tran1.writeAction(f"movrl {ADDR} 0({SPPTR}) 1 8")
    # reqType == 1; ALLOCATE_MEMORY
    tran1.writeAction(f"movir {VAL} 1") 
    tran1.writeAction(f"movrl {VAL} 0({SPPTR}) 1 8")
    
    # networkID == 0
    tran1.writeAction(f"movir {VAL} 0")
    tran1.writeAction(f"movrl {VAL} 0({SPPTR}) 1 8")
    
    # returnEvent == <after_allocation>
    # tran1.writeAction(f"movir {VAL} {event_map['after_allocation']}")
    tran1.writeAction(f"movir {VAL} {event_map['terminate']}")
    tran1.writeAction(f"movrl {VAL} 0({SPPTR}) 1 8")
    
    # blockSize = blockSizeB
    tran1.writeAction(f"addi X7 {RSPPTR} {INIT_OFFSET}") # find the buffered value
    tran1.writeAction(f"movlr 16({RSPPTR}) {BLOCKSIZE_B} 0 8")
    tran1.writeAction(f"movrl {BLOCKSIZE_B} 0({SPPTR}) 1 8")
    
    # size = nelemsB*8
    tran1.writeAction(f"movlr 0({RSPPTR}) {NELEMS_B} 0 8")
    tran1.writeAction(f"sli {NELEMS_B} {NBYTES_B} 3")
    tran1.writeAction(f"movrl {NBYTES_B} 0({SPPTR}) 1 8")
    
    # nrNodes = nnodesB
    tran1.writeAction(f"movlr 24({RSPPTR}) {NNODES_B} 0 8")
    tran1.writeAction(f"movrl {NNODES_B} 0({SPPTR}) 1 8")
    
    # startNode = startNodeB
    tran1.writeAction(f"movlr 8({RSPPTR}) {STARTNODE_B} 0 8")
    tran1.writeAction(f"movrl {STARTNODE_B} 0({SPPTR}) 1 8")
    
    # write the request to the DRAM, but first we need to write those to the SPM
    tran1.writeAction(f"addi X7 {SPPTR} {REQ_OFFSET}")
    tran1.writeAction(f"addi {SPPTR} {SPPTR} 8") # first value is the gseg base ptr
    # tran1.writeAction(f"send_dmlm_wret {ADDR} {event_map['after_allocation']} {SPPTR} 7")
    # tran1.writeAction(f"send_dmlm_wret {ADDR} {event_map['bogus']} {SPPTR} 7")
    # tran1.writeAction(f"print 'Sending allocate request to: %ld' {ADDR}")
    printu(tran1, f"'Sending allocate request to: %ld' {ADDR}")
    tran1.writeAction(f"send_dmlm_wret {ADDR} {event_map['bogus']} {SPPTR} 7 {TEMP0}")
    
    tran1.writeAction(f"yield")
    
    # event<after_allocation> 2: trigger the next event, depending on if shmem is used
    # if not shmem, write the allocated B to the SPM or print the SPM.
    tran2 = state0.writeTransition("eventCarry", state0, state0, event_map['after_allocation'])
    # part 1, not using shmem, just yield and print the address
    # tran2.writeAction(f"print 'Allocation Done. Address: %ld' {ADDR}")
    printu(tran2, f"'Allocation Done. Address: %ld' {ADDR}")
    # tran2.writeAction("yieldt")
    
    # part2, using shmem, then writing numbers to the SPM and then write the address to the SPM
    tran2.writeAction(f"addi X7 {SPPTR} {B_OFFSET}")
    tran2.writeAction(f"movrl {ADDR} 0({SPPTR}) 0 8")
    # tran2.writeAction(f"print 'Address is in SPM, at: %ld' {SPPTR}")
    printu(tran2, f"'Address is in SPM, at: %ld' {SPPTR}")
    tran2.writeAction("yieldt")
    
    
    # event<shmem_get> 3: this will trigger shmem routine. moving data from B to A or A to B is the same
    tran3 = state0.writeTransition("eventCarry", state0, state0, event_map['shmem_get'])
    tran3.writeAction(f"yieldt")
    
    tran4 = state0.writeTransition("eventCarry", state0, state0, event_map['terminate'])
    # tran4.writeAction(f"print 'Terminating'")
    printu(tran4, "'Terminating'")
    
    # construct a request
    tran4.writeAction(f"addi X7 {SPPTR} {REQ_OFFSET}")
    tran4.writeAction(f"movlr 0({SPPTR}) {ADDR} 0 8")
    # tran4.writeAction(f"print 'address: %ld' {ADDR}")
    printu(tran4, f"'address: %ld' {ADDR}")
    tran4.writeAction(f"addi {SPPTR} {SPPTR} 8") # first is the address
    tran4.writeAction(f"movir {VAL} 3") # reqType == 0; TERMINATE
    tran4.writeAction(f"movrl {VAL} 0({SPPTR}) 1 8")
    
    # networkID == 0
    tran4.writeAction(f"movir {VAL} 0")
    tran4.writeAction(f"movrl {VAL} 0({SPPTR}) 1 8")
    
    # returnEvent == <after_allocation>
    tran4.writeAction(f"movir {VAL} {event_map['after_term']}")
    tran4.writeAction(f"movrl {VAL} 0({SPPTR}) 1 8")
    
    # write the request to the DRAM, but first we need to write those to the SPM
    tran4.writeAction(f"addi X7 {SPPTR} {REQ_OFFSET}")
    tran4.writeAction(f"addi {SPPTR} {SPPTR} 8") # first value is the gseg base ptr
    # tran4.writeAction(f"print 'Term request sent to: %ld' {ADDR}")
    printu(tran4, f"'Term request sent to: %ld' {ADDR}")

    tran4.writeAction(f"send_dmlm_wret {ADDR} {event_map['bogus']} {SPPTR} 7 {TEMP0}")
    tran4.writeAction(f"yield")
    
    tran5 = state0.writeTransition("eventCarry", state0, state0, event_map['after_term'])
    # tran5.writeAction(f"print 'After term'")
    printu(tran5, "'After term'")

    tran5.writeAction(f"yieldt")
    
    tran6 = state0.writeTransition("eventCarry", state0, state0, event_map['bogus'])
    # tran6.writeAction(f"print 'Bogus, just waiting for top to process the request.'")
    printu(tran6, "'Bogus, just waiting for top to process the request.'")
    tran6.writeAction(f"yieldt")
    return efa

