from SpMalloc import *
from linker.EFAProgram import efaProgram, EFAProgram
#class RegFile:
#	def __init__(self, registers=None, prefix="X"):
#		self.available = registers
#		if self.available is None:
#			self.available = list(range(16))
#		self.reg_mapping = {}
#		self.name_prefix = prefix
#		logging.info(f"Initialized {len(self.available)} general-purpose registers.")
#
#	def __getitem__(self, name):
#		if name not in self.reg_mapping:
#			self.reg_mapping[name] = self.available.pop()
#			reg_name = f"{self.name_prefix}{self.reg_mapping[name]}"
#			logging.info(f"Allocated {reg_name} for {name} (remaining: {len(self.available)})")
#		reg_name = f"{self.name_prefix}{self.reg_mapping[name]}"
#		return reg_name
#
#	def assign(self, name, i):
#		if name in self.reg_mapping:
#			logging.error(f"{name} already allocated. Exiting...")
#			exit(1)
#		self.reg_mapping[name] = i
#		if i not in self.reg_mapping:
#			logging.error(
#				f"{name} cannot be assigned to {self.name_prefix}{i} because {i} is already in use. Exiting...")
#			exit(1)
#		self.available.remove(i)
#		reg_name = f"{self.name_prefix}{self.reg_mapping[name]}"
#		logging.info(f"Explicit allocation of {reg_name} for {name}")
#		return reg_name
#
#	def free(self, name):
#		reg_name = f"{self.name_prefix}{self.reg_mapping[name]}"
#		register = self.reg_mapping[name]
#		del self.reg_mapping[name]
#		self.available.append(register)
#		logging.info(f"Freed {reg_name} for {name} (remaining: {len(self.available)})")
#
#class ThreadRegFile:
#	def __init__(self, registers=None, prefix="X"):
#		self.usable = registers
#		self.prefix = prefix
#		self.current_context = None
#		self.register_files = {}
#
#	def init_context(self, name, change_context=True):
#		if name in self.register_files:
#			logging.error(f"Context {name} already exists.")
#			exit(1)
#		self.register_files[name] = RegFile(self.usable, self.prefix, name)
#		if change_context:
#			self.current_context = name
#			logging.info(f"Initialized context {name} and changed to it.")
#		else:
#			logging.info(
#				f"Initialized context {name} but retained current context to {self.current_context}")
#
#	def change_context(self, name):
#		if name not in self.register_files:
#			logging.warn(f"Context {name} not initialized. Initializing context...")
#			self.init_context(self, name)
#		else:
#			self.current_context = name
#			logging.info(f"Changed context to {name}")
#
#	def check_context(self):
#		if self.current_context is None:
#			logging.error("No context set for the thread.")
#			exit(1)
#
#	def assign(self, name, i):
#		self.check_context()
#		return self.register_files[self.current_context].assign(name, i)
#
#	def __getitem__(self, name):
#		self.check_context()
#		return self.register_files[self.current_context][name]
#
#	def free(self, name):
#		self.check_context()
#		self.register_files[self.current_context].free(name)




@efaProgram
def testSpMallocEFA(efa: EFAProgram):
	spMalloc = SpMalloc(0, iter(range(3,1000)), word_width = 8)

	efa = efa
	efa.code_level = "machine"
	state0 = efa.State()
	efa.add_initId(state0.state_id)
	efa.add_state(state0)
 
	#events['spMalloc'] = spMalloc.sp_malloc(state0)
	#events['spFree'] = spMalloc.sp_free(state0)
	tran0 = state0.writeTransition("eventCarry", state0, state0, "start_event")
	tran1 = state0.writeTransition("eventCarry", state0, state0, "write_crap")
	tran2 = state0.writeTransition("eventCarry", state0, state0, "terminate_event")

	tran0.writeAction(f"movir X16 0")
	tran0.writeAction(f"addi X7 X17 0")
	tran0.writeAction(f"move X16 0(X17) 0 8")
	tran0.writeAction(f"addi X8 X16 0")
	tran0.writeAction(f"evii X17 {'lm_allocator::spmalloc'} 255 5")
	tran0.writeAction(f"sendr_wret X17 {tran1.getLabel()} X16 X18 X19 X20")
	tran0.writeAction(f"yield")

	tran1.writeAction(f"beqiu X9 1 success_malloc")
	tran1.writeAction(f"yieldt")
	tran1.writeAction(f"success_malloc: addi X8 X17 0")
	tran1.writeAction(f"print 'SP MALLOC succeeded %lu %lu' X8 X9 ")
	tran1.writeAction(f"movir X19 999")
	tran1.writeAction(f"move X19 0(X17) 0 8")
	tran1.writeAction(f"add X16 X17 X17")
	tran1.writeAction(f"move X19 -8(X17) 0 8")
	tran1.writeAction(f"evii X17 {'lm_allocator::spfree'} 255 5")
	tran1.writeAction(f"sendr_wret X17 {tran2.getLabel()} X8 X16 X17 X18")
	tran1.writeAction(f"yield")

	tran2.writeAction(f"movir X16 100")
	tran2.writeAction(f"print 'SP FREE done will quit' ")
	tran2.writeAction(f"addi X7 X17 0")
	tran2.writeAction(f"move X16 0(X17) 0 8")
	tran2.writeAction(f"yieldt") 

	#events['spMalloc'] = spMalloc.sp_malloc(state0)
	#events['spFree'] = spMalloc.sp_free(state0)

	#tran0 = state0.writeTransition("eventCarry", state0, state0, events['start_event'])
	#tran0.writeAction(f"addi X8 X16 0")
	#tran0.writeAction(f"evii X17 {events['spMalloc']} 255 5")
	#tran0.writeAction(f"sendr_wret X17 {events['write_craps']} X16 X18 X19 X20")
	#tran0.writeAction(f"yield")

	#tran1 = state0.writeTransition("eventCarry", state0, state0, events['write_craps'])
	#tran1.writeAction(f"beqiu X9 1 success_malloc")
	#tran1.writeAction(f"yieldt")
	#tran1.writeAction(f"success_malloc: addi X8 X17 0")
	#tran1.writeAction(f"movir X19 999")
	#tran1.writeAction(f"move X19 0(X17) 0 8")
	#tran1.writeAction(f"add X16 X17 X17")
	#tran1.writeAction(f"move X19 -8(X17) 0 8")
	#tran1.writeAction(f"evii X17 {events['spFree']} 255 5")
	#tran1.writeAction(f"sendr_wret X17 {events['terminate_event']} X8 X16 X17 X18")
	#tran1.writeAction(f"yield")

	#tran2 = state0.writeTransition("eventCarry", state0, state0, events['terminate_event'])
	#tran2.writeAction(f"movir X16 100")
	#tran2.writeAction(f"addi X7 X17 0")
	#tran2.writeAction(f"move X16 0(X17) 0 8")
	#tran2.writeAction(f"yieldt")

	return efa