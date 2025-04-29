from Weave.WeaveIR import *
from Weave.WeaveIRenums import *


class AllocRegTypes(Enum):
    GPR_ISAV1 = {"prefix": "UDPR_", "min": 0, "max": 15}  # UD registers
    GPR_ISAV2 = {"prefix": "X", "min": 16, "max": 31}     # user registers
    OB_ISAV1 = {"prefix": "OB_", "min": 0, "max": 8}      # operand buffer
    OB_ISAV2 = {"prefix": "X", "min": 8, "max": 15}
    CONTROL_ISAV2_NETID = {"prefix": "X", "val": 0}
    CONTROL_ISAV2_CCONT = {"prefix": "X", "val": 1}
    CONTROL_ISAV2_CEVNT = {"prefix": "X", "val": 2}
    CONTROL_ISAV2_LMBASE = {"prefix": "X", "val": 7}


class AllocRegister:
    def __init__(self, type: AllocRegTypes, number: int = None):
        self.type = type
        self.number = number

    @property
    def name(self) -> str:
        return self.type.value["prefix"] + str(self.number)

    @property
    def prefix(self) -> str:
        return self.type.value["prefix"]

    @property
    def asNumber(self) -> int:
        return self.number

    def setNumberFromStr(self, strName: str) -> None:
        self.number = int(strName.split(AllocRegTypes.GPR_ISAV2.name)[-1])

    def __eq__(self, other) -> bool:
        return self.name == other.name


class weaveRegisterAllocator(ABC):
    """Interface to allow multiple implementations of register allocators
    Abstract class, do not implement
    """

    def __init__(self):
        self.all_regs = [
            AllocRegister(AllocRegTypes.GPR_ISAV2, i)
            for i in range(
                AllocRegTypes.GPR_ISAV2.value["min"],
                AllocRegTypes.GPR_ISAV2.value["max"] + 1,
            )
        ]
        self.all_op_regs = [
            AllocRegister(AllocRegTypes.OB_ISAV2, i)
            for i in range(
                AllocRegTypes.OB_ISAV2.value["min"],
                AllocRegTypes.OB_ISAV2.value["max"] + 1,
            )
        ]
        # There is a special register (X3) that can be used for a 9th operand
        self.all_op_regs.append(AllocRegister(AllocRegTypes.OB_ISAV2, 3))
        self.notUsed = self.all_regs.copy()

    def regExists(self, name: str) -> bool:
        return len(list(filter(lambda a: a.name == name, self.all_regs))) != 0

    def markUsed(self, reg: AllocRegister) -> None:
        if reg in self.notUsed:
            self.notUsed.remove(reg)

    def markUnused(self, reg: AllocRegister) -> None:
        self.notUsed.append(reg)

    def getTempReg(self, num: int) -> AllocRegister:
        if num < len(self.notUsed):
            return self.notUsed[num]
        errorMsg("Not enough registers available to lower to python")

    def changeAvailableRegisters(self, newSet: list) -> None:
        """In case the user wants to restrict the available registers

        Args:
            newSet (list): List of str containing register names
        """
        self.all_regs = newSet

    def getControlReg(self, reg: WeaveIRregister) -> AllocRegister:
        if not reg.isControl:
            errorMsg(
                "Trying to get a control register on a register "
                f"that is of type {reg.regType}"
            )
        if reg.number == WeaveIRcontrolRegs.CCONT:
            return AllocRegister(
                AllocRegTypes.CONTROL_ISAV2_CCONT,
                AllocRegTypes.CONTROL_ISAV2_CCONT.value["val"],
            )
        if reg.number == WeaveIRcontrolRegs.CEVNT:
            return AllocRegister(
                AllocRegTypes.CONTROL_ISAV2_CEVNT,
                AllocRegTypes.CONTROL_ISAV2_CEVNT.value["val"],
            )
        if reg.number == WeaveIRcontrolRegs.NETID:
            return AllocRegister(
                AllocRegTypes.CONTROL_ISAV2_NETID,
                AllocRegTypes.CONTROL_ISAV2_NETID.value["val"],
            )
        if reg.number == WeaveIRcontrolRegs.LMBASE:
            return AllocRegister(
                AllocRegTypes.CONTROL_ISAV2_LMBASE,
                AllocRegTypes.CONTROL_ISAV2_LMBASE.value["val"],
            )
        errorMsg(f"UNREACHABLE: Unknown control register type {reg.number}")

    @abstractmethod
    def allocate(self, th: WeaveIRscope) -> None:
        """
            This is the main function of the register allocator.
        """


class WeaveSimpleRegAlloc(weaveRegisterAllocator):
    """A simple dumb register allocator for nonSSA form"""

    def __init__(self):
        debugMsg(6, "Creating simple register allocator")
        super().__init__()

    def recursiveTypeReg(self, ty: AllocRegTypes, thread: bool) -> None:
        for field in ty.getFields():
            if isinstance(field, WeaveIRstructDecl):
                self.recursiveTypeReg(field, thread)
            elif not isinstance(field, WeaveIRpadding):
                val = self.getReg(field.getRegs[0])
                field.getRegs[0].allocate(val.name)
                self.markUsed(val)
                debugMsg(
                    6, f"Allocating {'thread' if thread else 'local'} {val.name} for {field.getRegs[0].name}"
                )

    def getReg(self, reg: WeaveIRregister, inst: WeaveIRinstruction = None) -> AllocRegister:
        if reg.isControl:
            return self.getControlReg(reg)
        if reg.isOBuff:
            return self.getParamReg(reg)
        if reg.number >= len(self.all_regs):
            if inst:
                errorMsg(
                    f"Not enough registers to allocate register {reg.number} for {inst.to_string(0)}",
                    inst.getFileLocation()
                )
            else:
                errorMsg(f"Not enough registers to allocate register {reg.number}")
        return self.all_regs[reg.number]

    def getParamReg(self, reg: WeaveIRregister) -> AllocRegister:
        if reg.isControl:
            return self.getControlReg(reg)
        if reg.number >= len(self.all_op_regs):
            errorMsg(f"Not enough registers to allocate register {reg.number} for parameter")
        return self.all_op_regs[reg.number]

    def allocate(self, scope: WeaveIRscope) -> None:
        # This assumes nonSSA form. It just uses the same
        # register number, however, it fails if there are no more registers.
        # Register allocation occurs during code gen.

        # Thread local variables are kept across events
        # single allocation and propagate to all instructions
        for decl in scope.getDeclarations():
            if decl.isStatic or decl.isConstant:
                continue
            if decl.isStruct or decl.isUnion:
                self.recursiveTypeReg(decl.dataType, scope.depth == 1)
            elif isinstance(decl, WeaveIRParamDecl):
                val = self.getParamReg(decl.getRegs[0])
                decl.getRegs[0].allocate(val.name)
                self.markUsed(val)
                debugMsg(
                    6, f"Allocating register {val.name} for parameter {decl.name} in scope {scope.name}"
                )
            else:
                val = self.getReg(decl.getRegs[0])
                decl.getRegs[0].allocate(val.name)
                self.markUsed(val)
                debugMsg(
                    6, f"Allocating register {val.name} for {decl.name} in scope {scope.name}"
                )
        self.allocateReturnRegs(scope)

    def allocateReturnRegs(self, scope: WeaveIRscope) -> None:
        for s in scope.getBodies():
            if isinstance(s, WeaveIRthread):
                for section in s.sections:
                    if isinstance(section, WeaveIRscope):
                        self.allocateReturnRegs(section)
                    elif isinstance(section, WeaveIRevent):
                        self.allocateRegsForEvents(section)
            if isinstance(s, WeaveIRevent):
                self.allocateRegsForEvents(s)

    def allocateRegsForEvents(self, event: WeaveIRevent):
        for bb in event.basic_blocks:
            for inst in bb.instructions:
                if isinstance(inst, WeaveIRinstruction):
                    if (
                        inst.getReturnReg()
                        and not inst.getReturnReg().alreadyAllocated
                    ):
                        val = self.getReg(inst.getReturnReg(), inst)
                        inst.getReturnReg().allocate(val.name)

                        debugMsg(
                            6,
                            f"Allocating {val.name} for {inst.getReturnReg().name}",
                        )
                    readOps = inst.getInOps()
                    for op in readOps:
                        if (
                            isinstance(op, WeaveIRregister)
                            and not op.alreadyAllocated
                        ):
                            val = self.getReg(op, inst)
                            op.allocate(val.name)
                            debugMsg(6, f"Allocating {val.name} for {op.name}")
