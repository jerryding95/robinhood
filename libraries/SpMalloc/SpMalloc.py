import logging
from math import log2
from libraries.LMStaticMaps import LMStaticMap
from linker.EFAProgram import efaProgram, EFAProgram


def SpMallocEFA(efa: EFAProgram, state0, init_offset=LMStaticMap.HEAP_OFFSET, debug=False):
    efa.code_level = 'machine'

    spmalloc_inst = SpMalloc(init_offset, "lm_allocator", debug=debug)
    spmalloc_inst.sp_malloc(state0)
    spmalloc_inst.sp_free(state0)
    #def __init__(self, init_offset, taskname, bank_size=65536, word_width=8, registers=None):

    return efa


class RegFile:
    def __init__(self, registers=None, prefix="UDPR_"):
        self.available = registers
        if self.available is None:
            self.available = list(range(16))
        self.reg_mapping = {}
        self.name_prefix = prefix

    def __getitem__(self, name):
        if name not in self.reg_mapping:
            self.reg_mapping[name] = self.available.pop()
            reg_name = f"{self.name_prefix}{self.reg_mapping[name]}"
            #logging.info(f"Allocated {reg_name} for {name}")
        reg_name = f"{self.name_prefix}{self.reg_mapping[name]}"
        return reg_name

    def assign(self, name, i):
        self.reg_mapping[name] = i
        self.available.remove(i)
        reg_name = f"{self.name_prefix}{self.reg_mapping[name]}"
        #logging.info(f"Explicit allocation of {reg_name} for {name}")
        return reg_name

    def free(self, name):
        reg_name = f"{self.name_prefix}{self.reg_mapping[name]}"
        register = self.reg_mapping[name]
        del self.reg_mapping[name]
        self.available.append(register)
        #logging.info(f"Freed {reg_name} for {name}")

class SpMallocImpl:
    def __init__(self, init_offset, bank_size=65536, word_width=8, registers=None, debug=False):
        self.init_offset = init_offset
        self.bank_size = bank_size
        self.shift_size = int(log2(bank_size))
        self.word_width = word_width
        self.debug = debug

        self.block_break_threshold = 2 * self.word_width # Remaining space must be atleast two blocks to break current block
        self.dealloc_mask = ((2 ** 32) - 1) ^ 1

        logging.basicConfig(format="%(levelname)s:%(name)s:%(message)s", level=logging.INFO)

        self.registers = RegFile(registers)


    def read_initial_addresses(self, tran):
        bank_start_address = self.registers["bank_start_address"]  # Pre-allocated
        bank_first_heap_address = self.registers["bank_first_heap_address"]  # Pre-allocated
        bank_end_address = self.registers["bank_end_address"] # Pre-allocated
        bank_offset = self.registers["bank_offset"]
        tmp = self.registers["tmp"]

        lane_id = self.registers["lane_id"]
        lane_id_mask = 0x3f

#        # Extract lane id from NWID
#        tran.writeAction(f"andi NWID {lane_id} {lane_id_mask}")
#        # Get the first memory address of the lane
#        tran.writeAction(
#            f"lshift {lane_id} {bank_start_address} {self.shift_size}")
#        # Get the next to last address of the lane
#        tran.writeAction(
#            f"init: lshift_add_imm {lane_id} {bank_end_address} {self.shift_size} {self.bank_size}")

        if self.debug:
            tran.writeAction(
            f"print '[SpMalloc] Received request to allocate %ld words' X8")
        tran.writeAction(
            f"addi X7 {bank_start_address} 0")
        tran.writeAction(f"movir {tmp} {self.bank_size}")
        tran.writeAction(f"init: add X7 {tmp} {bank_end_address}")

        # Increment the memory address to point to the usable offset
        tran.writeAction(
            f"movir {bank_first_heap_address} {self.init_offset}")
        tran.writeAction(
            f"add {bank_start_address} {bank_first_heap_address} {bank_first_heap_address}")
        # Read the number of bytes to skip to point to the first usable address
        tran.writeAction(
            f"move 0({bank_first_heap_address}) {bank_offset} 0 {self.word_width}")
        # Add the bytes to skip to the first memory address and store in UPDR_21
        if self.debug:
            tran.writeAction(
                f"print '[SpMalloc] Start allocating from offset %ld' {bank_offset}")
        tran.writeAction(
            f"add {bank_offset} {bank_start_address} {bank_first_heap_address}")
        

        self.registers.free("lane_id")
        self.registers.free("bank_offset")
        self.registers.free("tmp")

    def init_allocator(self, tran):
        # The following registers will already be initialized by the allocate function
        bank_end_address = self.registers["bank_end_address"] # Pre-allocated
        bank_first_heap_address = self.registers["bank_first_heap_address"] # Pre-allocated
        block_header = self.registers["block_header"] # Temporary

        # Initialize the first block
        tran.writeAction(
            f"sub {bank_end_address} {bank_first_heap_address} {block_header}")
        tran.writeAction(f"lshift {block_header} {block_header} 1") # Jerry: Why left shift 1 bit?
        tran.writeAction(f"move {block_header} 0({bank_first_heap_address}) 0 {self.word_width}")

        self.registers.free("block_header")

        # Ideally we would want to jump to allocate block again
        # but we're not doing that because this code will be inlined

    def perform_initialization_on_first_call(self, tran):
        bank_first_heap_address = self.registers["bank_first_heap_address"]  # Pre-initialized
        block_data = self.registers["block_data"]

        tran.writeAction(
            f"move 0({bank_first_heap_address}) {block_data} 0 {self.word_width}")
        tran.writeAction(f"bnei {block_data} 0 allocate_block")
        self.init_allocator(tran)

        self.registers.free("block_data")

    def allocate_block(self, tran):
        free_block_address = self.registers["free_block_address"]
        required_size = self.registers["required_size"]
        block_size = self.registers["block_size"]

        remaining = self.registers["remaining"] # Temporary

        # Store remaining size
        tran.writeAction(f"found_free_block: sub {block_size} {required_size} {remaining}")
        tran.writeAction(f"bltiu {remaining} {self.block_break_threshold} post_allocation_header_assignment")

        # Compute the address of the next block's header to save the next header
        next_block_header_address = self.registers["next_block_header_address"] # Temporary

        # Change the current block size to the required size
        tran.writeAction(f"mov_reg2reg {required_size} {block_size}")
        tran.writeAction(f"lshift {remaining} {remaining} 1")
        tran.writeAction(f"add {free_block_address} {block_size} {next_block_header_address}")
        tran.writeAction(f"move {remaining} 0({next_block_header_address}) 0 {self.word_width}")
        if self.debug:
            tran.writeAction(f"print '[SpMalloc] Split block and updated remaining size to %ld at addr %lx' {remaining} {next_block_header_address}")

        self.registers.free("next_block_header_address")
        self.registers.free("remaining")

        # Left shift and add 1 to mark as allocated
        tran.writeAction(f"post_allocation_header_assignment: lshift_add_imm {block_size} {block_size} 1 1")
        tran.writeAction(f"move {block_size} 0({free_block_address}) 0 {self.word_width}")

        # Increment free_block_address to point to first byte of the payload
        tran.writeAction(f"addi {free_block_address} {free_block_address} {self.word_width}")

    def handle_failure(self, tran):
        free_block_address = self.registers["free_block_address"]
        tran.writeAction(f"no_block_available: mov_imm2reg {free_block_address} 0")

    def coalesce(self, tran):
        free_block_address = self.registers["free_block_address"] # reserved by find_and_allocate_block
        next_block_address = self.registers["next_block_address"] # reserved by find_and_allocate_block
        block_data = self.registers["block_data"] # reserved by find_and_allocate_block
        block_size = self.registers["block_size"] # reserved by find_and_allocate_block
        is_allocated = self.registers["is_allocated"] # reserved by find_and_allocate_block

        next_block_header_data = self.registers["next_block_header_data"]

        # If block is allocated then we can't coalesce
        tran.writeAction(f"beqi {is_allocated} 1 do_not_coalesce")
        # Perform the same check for next header
        tran.writeAction(f"move 0({next_block_address}) {next_block_header_data} 0 {self.word_width}")
        tran.writeAction(f"andi {next_block_header_data} {is_allocated} 1")
        tran.writeAction(f"beqi {is_allocated} 1 do_not_coalesce")

        # Coalesce blocks because both are allocated
        tran.writeAction(f"rshift {next_block_header_data} {next_block_header_data} 1") # Just store next block size in next_block_header_data register
        tran.writeAction(f"add {next_block_header_data} {block_size} {block_size}")
        tran.writeAction(f"lshift {block_size} {block_size} 1")
        tran.writeAction(f"move {block_size} 0({free_block_address}) 0 {self.word_width}")
        tran.writeAction(f"jmp find_free_block")

        tran.writeAction(f"do_not_coalesce: mov_reg2reg {next_block_address} {free_block_address}")

        self.registers.free("next_block_header_data")

    def find_and_allocate_block(self, tran):
        bank_first_heap_address = self.registers["bank_first_heap_address"]
        free_block_address = self.registers["free_block_address"]
        required_size = self.registers["required_size"]
        bank_end_address = self.registers["bank_end_address"]

        block_data = self.registers["block_data"]
        block_size = self.registers["block_size"]
        is_allocated = self.registers["is_allocated"]
        next_block_address = self.registers["next_block_address"]

        # Fetch the required size from the operand buffer
        tran.writeAction(f"allocate_block: addi X8 {required_size} 0")
        # Return error if 0 words are requested
        tran.writeAction(f"beqi {required_size} 0 no_block_available")
        tran.writeAction(f"addi {required_size} {required_size} 1")
        tran.writeAction(f"lshift {required_size} {required_size} {int(log2(self.word_width))}")
        # Convert required size to bytes

        tran.writeAction(f"mov_reg2reg {bank_first_heap_address} {free_block_address}")

        # Read block data and transform size and allocation flag
        tran.writeAction(f"find_free_block: move 0({free_block_address}) {block_data} 0 {self.word_width}")
        if self.debug:
            tran.writeAction(f"print '[SpMalloc] Read header = %lx from %lx' {block_data} {free_block_address}")
        tran.writeAction(f"rshift {block_data} {block_size} 1")
        tran.writeAction(f"andi {block_data} {is_allocated} 1")

        # Break from loop if current block is greater than or equal to the required size
        tran.writeAction(f"blt {block_size} {required_size} continue_find_block_loop")
        tran.writeAction(f"beqi {is_allocated} 0 found_free_block")

        # Move to next block
        tran.writeAction(f"continue_find_block_loop: add {block_size} {free_block_address} {next_block_address}")
        # Jump to the failure if address is out of bounds of the local bank
        if self.debug:
            tran.writeAction(f"print '[SpMalloc] Checking addr %lx' {next_block_address}")
        tran.writeAction(f"bge {next_block_address} {bank_end_address} no_block_available")
        # Perform coalescing if possible and continue iteration with the same block, otherwise continue with next block
        #   moving to next block is done with in the coalesce function
        self.coalesce(tran)
        tran.writeAction(f"jmp find_free_block")

        self.registers.free("block_data")
        self.registers.free("is_allocated")
        self.registers.free("next_block_address")

        self.allocate_block(tran) # Contains the found_free_block label
        tran.writeAction("jmp write_results")  # In sp_malloc

        self.handle_failure(tran) # Contains the no_block_available label

        self.registers.free("block_size")

    def sp_malloc(self, tran):
        self.registers.assign("required_size", 0)
        self.registers.assign("bank_first_heap_address", 1)
        self.registers.assign("bank_end_address", 2)
        free_block_address = self.registers.assign("free_block_address", 3)
        ret_cont = self.registers.assign("ret_cont", 4)

        tran.writeAction(f"mov_reg2reg X1 {ret_cont}")
        self.read_initial_addresses(tran)

        self.perform_initialization_on_first_call(tran)
        self.find_and_allocate_block(tran) # Contains the allocate_block label

        success_code = self.registers["success_code"]
        tran.writeAction(f"write_results: mov_imm2reg {success_code} 0")
        tran.writeAction(f"beqi {free_block_address} 0 reply")
        tran.writeAction(f"mov_imm2reg {success_code} 1")

        tran.writeAction(
            f"reply: sendr_wcont {ret_cont} {ret_cont} {free_block_address} {success_code} {success_code}")
        tran.writeAction("yield_terminate")

        self.registers.free("required_size")
        self.registers.free("bank_first_heap_address")
        self.registers.free("bank_end_address")
        self.registers.free("free_block_address")
        self.registers.free("ret_cont")

    def sp_free(self, tran):
        header_address = self.registers["header_address"]
        header = self.registers["header"]
        ret_cont = self.registers["ret_cont"]
        tmp_register = self.registers["tmp_register"]

        if self.debug:
            tran.writeAction(f"print '[SpMalloc] Received request to free addr %lx' X8")
        tran.writeAction(f"mov_reg2reg X1 {ret_cont}")

        tran.writeAction(f"addi X8 {header_address} 0")
        tran.writeAction(f"subi {header_address} {header_address} {self.word_width}")
        tran.writeAction(f"move 0({header_address}) {header} 0 {self.word_width}")


        tran.writeAction(f"movir {tmp_register} {self.dealloc_mask >> 16}")
        tran.writeAction(f"sli {tmp_register} {tmp_register} 16")
        tran.writeAction(f"ori {tmp_register} {tmp_register} {self.dealloc_mask & 0xffff}")
        tran.writeAction(f"and {header} {tmp_register} {header}")

        # tran.writeAction(f"andi {header} {header} {self.dealloc_mask}")
        tran.writeAction(f"move {header} 0({header_address}) 0 {self.word_width}")
        if self.debug:
            tran.writeAction(f"print '[SpMalloc] Updated the header at addr %lx to %lx' {header_address} {header}")

        
        tran.writeAction(f"mov_imm2reg {tmp_register} 1")
        tran.writeAction(
            f"sendr_wcont {ret_cont} {ret_cont} {tmp_register} {tmp_register} {tmp_register}")
        tran.writeAction("yield_terminate")
        self.registers.free("tmp_register")

        self.registers.free("header_address")
        self.registers.free("header")
        self.registers.free("ret_cont")


class SpMalloc:
    """
    SpMalloc library for dynamic scratchpad memory management in UpDown nodes.

    Usage:
    1. import the module into your UpDown source code file (you can do it any way that you like to work with python modules)
    2. Initialize the SpMalloc library using the the SpMalloc constructor (see __init__ docstring for more details)
    3. Write out events for sp_malloc and sp_free using the corresponding functions and save the event ids for use in your code.
    """

    def __init__(self, init_offset, thread_name, bank_size=65536, word_width=8, registers=None, debug=False):
        """
        Parameters
            init_offset: This parameter contains the memory offset from the starting address of each memory bank that holds
                the offset to the first memory address of the heap from the begging of the memory bank.
            event_id_allocator: And iterator that can be used to get event ids, this will be used to generate ids for the sp_malloc and sp_free
                events when the sp_malloc and sp_free functions are called.
            bank_size: (default: 65536) The size in bytes of each lane's memory bank.
            word_width: (default: 4) The width in bytes of a word of memory in the architecture.
            registers: Any registers that the user of the library would like the sp_malloc and sp_free functions not to use.
        """
        #self.event_id_allocator = event_id_allocator
        self.thread_name = thread_name
        self.sp_malloc_writer = SpMallocImpl(
            init_offset, bank_size, word_width, registers, debug=debug)

    def sp_malloc(self, state):
        """
        Parameters
            state: The updown state in which a new transition will be allocated. The code for the sp_malloc
                event will be written in a transition on this state.

        Returns
            event_id: This is the id for the sp_malloc event that can be used to call into this event in your code.
        """
        malloc_event = f"{self.thread_name}::spmalloc"
        transaction = state.writeTransition(
            "eventCarry", state, state, malloc_event)
        self.sp_malloc_writer.sp_malloc(transaction)
        return malloc_event

    def sp_free(self, state):
        """
        Parameters
            state: The updown state in which a new transition will be allocated. The code for the sp_free
                event will be written in a transition on this state.

        Returns
            event_id: This is the id for the sp_free event that can be used to call into this event in your code.
        """
        free_event = f"{self.thread_name}::spfree"
        transaction = state.writeTransition(
            "eventCarry", state, state, free_event)
        self.sp_malloc_writer.sp_free(transaction)
        return free_event
