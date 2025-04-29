import struct


import Weave.WeaveIRenums as WIRinst
from abc import ABC, abstractmethod
from Weave.debug import errorMsg, debugMsg
from Weave.fileLocation import FileLocation
import re
import copy

INDENT = 2


def indent_text(text, indent):
    text = " " * indent + text
    return text


def next_indent(ind):
    return ind + INDENT


class WeaveIRbase(ABC):
    """Base abstract class for an WeaveIR instruction

    Defines a context, this is, the instruction from which this
    IR is generated
    It also contains direct access to the current program, thread,
    and event.

    Args:
        ABC (_type_): _description_
    """

    _inline_code = False

    def __init__(self, ctx=None):
        # Corresponds to the associated type if used as operand.
        self.dataType = WIRinst.WeaveIRtypes.unknown
        self._qualifiers = []
        # Points to parent
        self.ctx = ctx
        if ctx is not None:
            self.extend(ctx)
            # TODO: The context should determine the file location, but this does not seem to be properly
            # implemented in all the cases.
            self.setFileLocation(ctx.getFileLocation())
        else:
            self.ctx_program = None
            self.ctx_thread = None
            self.ctx_event = None
            self.ctx_scope = None
            self.ctx_loop = []
            self.ctx_instruction = None
            self.fileLoc = None

        # Is external
        self._isExternal = False

    def setIsExternal(self, isExternal):
        self._isExternal = isExternal

    def setCtxLoop(self, cond: "WeaveIRbasicBlock", body: "WeaveIRbasicBlock", post: "WeaveIRbasicBlock"):
        self.ctx_loop.append({"cond": cond, "body": body, "post": post})

    def getPostBlock(self) -> "WeaveIRbasicBlock":
        return self.ctx_loop[-1]["post"]

    def getBodyBlock(self) -> "WeaveIRbasicBlock":
        return self.ctx_loop[-1]["body"]

    def getCondBlock(self) -> "WeaveIRbasicBlock":
        return self.ctx_loop[-1]["cond"]

    def inLoop(self) -> bool:
        return len(self.ctx_loop) > 0

    def popCtxLoop(self):
        self.ctx_loop.pop()

    @property
    def isExternal(self):
        return self._isExternal

    @classmethod
    def setInlineCode(cls, inline_code):
        cls._inline_code = inline_code

    @property
    def inlineCode(self):
        return self._inline_code

    def setFileLocation(self, floc: FileLocation):
        self.fileLoc = floc

    def getFileLocation(self):
        return self.fileLoc

    def extend(self, other):
        self.ctx_program = other.ctx_program
        self.ctx_thread = other.ctx_thread
        self.ctx_event = other.ctx_event
        self.ctx_scope = other.ctx_scope
        self.ctx_instruction = other.ctx_instruction
        self.ctx_loop = other.ctx_loop

    def setType(self, dType: WIRinst.WeaveIRtypes):
        """Set a new dataType that this WeaveIR element

        Args:
            dType (WeaveIRTypes): The new Data Type
        """
        self.dataType = dType

    @property
    def dtype(self) -> WIRinst.WeaveIRtypes:
        """Get the data type of the WeaveIR element"""
        return self.dataType

    @property
    def quals(self):
        return self._qualifiers

    def setQuals(self, quals):
        self._qualifiers = quals

    def addQualifier(self, q: WIRinst.WeaveIRqualifiers):
        if q == WIRinst.WeaveIRqualifiers.unsigned:
            try:
                self._qualifiers.remove(WIRinst.WeaveIRqualifiers.signed)
            except ValueError:
                pass  # if it is not there, do not care
        elif q == WIRinst.WeaveIRqualifiers.signed:
            try:
                self._qualifiers.remove(WIRinst.WeaveIRqualifiers.unsigned)
            except ValueError:
                pass  # if it is not there, do not care
        if q not in self._qualifiers:
            self._qualifiers.append(q)

    def isSigned(self) -> bool:
        return WIRinst.WeaveIRqualifiers.signed in self.quals

    def filterScope(self, classSearch: "WeaveIRbase", sections: list) -> list:
        """
        Filter the sections of the program to get only the ones that are of a given class
        @param classSearch: The class to search for
        @type classSearch: WeaveIRbase
        @param sections: Sections of the program
        @type sections: list[WeaveIRBase]
        @return: Found sections that match classSearch
        @rtype: list["WeaveIRbase"]
        """
        res = []
        for section in sections:
            if isinstance(section, WeaveIRscope):
                res.extend(
                    list(
                        filter(
                            lambda s: isinstance(s, classSearch), section.getBodies()
                        )
                    )
                )
            elif isinstance(section, classSearch):
                res.append(section)
        return res

    @abstractmethod
    def to_string(self, indent):
        pass


class WeaveIRmodule(WeaveIRbase):
    def __init__(self, name):
        super().__init__()
        self.name = name
        # List of all the program sections
        self.sections = []
        # Set program
        self.ctx_program = self

        # Contains all the declarations across the program
        # Used to match namespace
        self._symbolDecls = []

        # Contains all the declaration of data types such as structs
        self.dataTypesDecls = []

        from Weave.intrinsics import WeaveIntrinsicFunc, WeaveIntrinsicVar

        self.intrinsicFuncs = WeaveIntrinsicFunc

        self.intrinsicVars = WeaveIntrinsicVar

    def getIntrinsicFuncs(self, name):
        return self.intrinsicFuncs.getIntrinsics(name)

    def getIntrinsicVars(self, name):
        return self.intrinsicVars.getIntrinsics(name)

    def getThreads(self) -> list:
        return self.filterScope(WeaveIRthread, self.sections)

    def getSections(self):
        return self.sections

    def addExternal(self, ext):
        self.sections.append(ext)

    def addThread(self, thread):
        if not thread.isAnonymous and self.threadExists(thread.name):
            errorMsg(
                f"Duplicated thread declaration {thread.name} in program {self.name}",
                thread.getFileLocation(),
            )

        self.sections.append(thread)

    def addDecl(self, decl):
        self.sections.append(decl)

    def addScope(self, scope):
        self.sections.append(scope)

    def findDecl(self, name):
        """Find if a declaration exists in the program"""
        return list(
            filter(
                lambda x: isinstance(x, WeaveIRDecl) and x.name == name, self.sections
            )
        )

    def addAssemblyBlock(self, asm):
        self.sections.append(asm)

    def addComment(self, comment):
        self.sections.append(comment)

    def addSymbolDecl(self, namespace, symbol, isExternal=False):
        debugMsg(9, f"Adding symbol {namespace}::{symbol}")
        self._symbolDecls.append(WeaveIRsymPtr(self, namespace, symbol, isExternal))
        return self._symbolDecls[-1]

    def addSymbolConstDecl(self, namespace, symbol, valueSymbol):
        self._symbolDecls.append(WeaveIRsymConst(self, namespace, symbol, valueSymbol))
        return self._symbolDecls[-1]

    def findSymbolDecl(self, namespace, symbol):
        debugMsg(9, f"Looking for {namespace}::{symbol}")
        result = list(
            filter(
                lambda s: s.namespace == namespace and s.value == symbol,
                self._symbolDecls,
            )
        )
        result.extend(self.ctx_program.findDataTypeDecl(symbol))
        return result

    def getSymbols(self):
        return self._symbolDecls

    def addDataTypeDecl(self, dataType: "WeaveIRdataTypeDecl") -> None:
        self.dataTypesDecls.append(dataType)
        self.sections.append(dataType)

    def findDataTypeDecl(self, dataTypeName: str) -> list:
        return list(filter(lambda s: s.name == dataTypeName, self.dataTypesDecls))

    def getDataTypes(self) -> list:
        return self.dataTypesDecls

    def findThread(self, name: str):
        return list(filter(lambda s: s.name == name, self.getThreads()))

    def threadExists(self, thread_name):
        return len(self.findThread(thread_name)) != 0

    def to_string(self, indent):
        s_string = "".join([s.to_string(next_indent(indent)) for s in self.sections])
        return indent_text(f"Module: {self.name}\n{s_string}", indent)

    def __str__(self):
        return self.to_string(1)


class WeaveIRthread(WeaveIRbase):
    def __init__(self, program):
        super().__init__(program)
        self.ctx_thread = self

        self.name = None
        # List of all the sections, including declarations
        self.sections = []
        self._isAnonymous = False

    def setAnonymous(self, val: bool):
        self._isAnonymous = val

    @property
    def isAnonymous(self) -> bool:
        return self._isAnonymous

    def getEvents(self):
        return self.filterScope(WeaveIRevent, self.sections)

    def addEvent(self, e):
        if self.ctx_scope.declExists(e.name):
            errorMsg(
                f"Event {e.name} "
                f"has the same name of an already existing thread or"
                f"local variable in thread {self.ctx_thread.name}",
                e.getFileLocation(),
            )
        if self.eventExists(e.name):
            errorMsg(
                f"Duplicated event declaration {e.name} in thread {self.name}",
                e.getFileLocation(),
            )
        sym = self.ctx_program.findSymbolDecl(self.name, e.name)
        if len(sym) == 0:
            errorMsg(
                f"UNREACHABLE: Symbol not found for {self.name}::{e.name} in thread {self.name}.",
                e.getFileLocation(),
            )
        e.setSymbol(sym[0])

        self.sections.append(e)
        self.ctx_scope.addBody(e)

    def findEvent(self, name):
        return list(filter(lambda s: s.name == name, self.getEvents()))

    def eventExists(self, name):
        return len(self.findEvent(name)) != 0

    def addThreadDecl(self, decl: "WeaveIRthreadDecl"):
        self.ctx_scope.addDeclaration(decl)
        self.sections.append(decl)

    def addAssemblyBlock(self, asm):
        self.sections.append(asm)

    def addComment(self, comment):
        self.sections.append(comment)

    def getSections(self):
        return self.sections

    def to_string(self, indent):
        name = self.name if not self.isAnonymous else "<anonymous>"
        t_string = "".join([t.to_string(next_indent(indent)) for t in self.sections])
        return indent_text(f"thread: {name}\n{t_string}\n", indent)

    def getUses(self, searchFor: "WeaveIRregister") -> list:
        """Get all the instructions that use a given register
        @param searchFor: The register to search for
        @type searchFor: WeaveIRregister
        @return: List of instructions that use the register
        @rtype: list[WeaveIRinstruction]
        """
        instrs = []
        for b in self.sections:
            if isinstance(b, WeaveIRevent):
                instrs.extend(b.getUses(searchFor))
        return instrs


class WeaveIRscope(WeaveIRbase):
    maxDepth = 0

    def __init__(self, ctx, depth: int, parent: "WeaveIRscope"):
        super().__init__(ctx)
        ctx.ctx_scope = self
        self.ctx_scope = self
        self.depth = depth
        # parent of the scope
        self._parent = parent

        # Everything such as instructions, events, threads, inside this scope
        self._bodies = []

        # children scopes
        self._children = []
        if parent:
            self.name = parent.name + f"->{WeaveIRscope.maxDepth}"
            self.cur_reg_number = parent.cur_reg_number
            self.max_reg_number = parent.max_reg_number
            self._parent.addChild(self)
        else:
            self.name = str(depth)
            self.cur_reg_number = -1
            self.max_reg_number = -1

        self._oldRegNumber = []
        WeaveIRscope.maxDepth += 1

        # Declarations inside the current scope
        self._declarations = []

    def addBody(self, scope):
        self._bodies.append(scope)

    def getBodies(self):
        return self._bodies

    def addChild(self, scope):
        self._children.append(scope)

    def getChildren(self):
        return self._children

    def getNextRegister(self) -> int:
        self.cur_reg_number = self.cur_reg_number + 1
        if self.cur_reg_number > self.max_reg_number:
            self.max_reg_number = self.cur_reg_number
        return self.cur_reg_number

    def getNextRegisterInScope(self) -> int:
        """Get a register that is guaranteed to be unique in the thread. It
        keeps track of the max register that has already been allocated, and uses
        it to give a new register number."""
        self.max_reg_number = self.max_reg_number + 1
        return self.max_reg_number

    def startScope(self) -> None:
        self._oldRegNumber.append(self.cur_reg_number)

    def endScope(self) -> None:
        self.cur_reg_number = self._oldRegNumber.pop(0)

    def to_string(self, indent):
        # d_string = ", ".join(
        #     [d.to_string(next_indent(indent)).strip() for d in self.__declarations]
        # )
        d_string = "".join(
            [d.to_string(next_indent(indent)).strip() for d in self.getBodies()]
        )
        return indent_text(d_string, indent)

    def addDeclaration(self, val):
        """Add a declaration to the current scope"""
        debugMsg(5, f"Adding declaration {val.name} to scope {self.name}")

        if self.ctx_thread and self.ctx_thread.eventExists(val.name):
            errorMsg(
                f"Local variable of event {self.ctx_event.name} with name {val.name} "
                f"has the same name of an already existing event in thread {self.ctx_thread.name}",
                val.getFileLocation(),
            )
        if self.declExists(val.name):
            # TODO: Add location to the previous declaration
            errorMsg(
                f"Redefinition of variable {val.name} within the same scope.",
                val.getFileLocation(),
            )
        self._declarations.append(val)

    def removeDeclaration(self, val: "WeaveIRDecl"):
        pass
        """Remove a declaration from the current scope"""
        # delete the instruction that belongs to this declaration
        references = val.references
        for reference in references:
            if not isinstance(reference, WeaveIRDecl):
                bb: WeaveIRbasicBlock = reference.curBB
                if bb is not None and reference in bb.instructions:
                    bb.instructions.remove(reference)
        self._declarations.remove(val)

    def findDecl(self, name):
        """Find if a declaration exists in the event or the thread"""
        check_local = list(filter(lambda x: x.name == name, self._declarations))
        # search recursively through all the parent scopes
        if len(check_local) == 0 and self._parent:
            check_local = self._parent.findDecl(name)
        # check the parameters of the current event
        if len(check_local) == 0 and self.ctx_event:
            check_local = self.ctx_event.findParameter(name)
        if len(check_local) == 0:
            check_local = self.ctx_program.findDecl(name)
        return check_local

    def declExists(self, name):
        return len(self.findDecl(name)) != 0

    def getDeclarations(self):
        return self._declarations

    def getUses(self, searchFor: "WeaveIRregister") -> list:
        """
        Get all the instructions that use a given register
        @param searchFor: Search for instruction that uses the register
        @type searchFor: WeaveIRregister
        @return: List of instructions that use the register
        @rtype: list["WeaveIRinstruction"]
        """
        instrs = []
        for b in self._bodies:
            if isinstance(b, WeaveIRevent):
                instrs.extend(b.getUses(searchFor))
            elif isinstance(b, WeaveIRthread):
                instrs.extend(b.getUses(searchFor))
            elif isinstance(b, WeaveIRinstruction):
                for op in b.getInOps():
                    # Do not use `==` instead of `is`. We do not want to execute the method __eq__ of WeaveIRregister,
                    # but actually compare the pointer values.
                    if isinstance(op, WeaveIRregister) and op is searchFor:
                        instrs.append(b)

        for child in self._children:
            instrs.extend(child.getUses(searchFor))
        return instrs


class WeaveIRevent(WeaveIRbase):
    def __init__(self, thread, name, is_external=False):
        super().__init__(thread)
        self.ctx_event = self

        # Name
        self.name = name
        # Symbol (full name with namespace)
        self.symbol = None
        # Declarations inside an event
        self.params = []
        # For reference when generating code
        self.curBB = WeaveIRbasicBlock(self, "entry")
        # List of all the basic blocks
        self.basic_blocks = [self.curBB]
        # Label counts
        self.nr_blocks = 0

        self._isExternal = is_external

        # Tracing op number
        self._cur_param_number = -1

    def setSymbol(self, sym):
        self.symbol = sym

    @property
    def fullName(self):
        return self.symbol.name

    def getNextParamRegister(self):
        self._cur_param_number = self._cur_param_number + 1
        return self._cur_param_number

    def addParameter(self, param):
        if not self.isExternal:
            if self.ctx_thread.eventExists(param.name):
                errorMsg(
                    f"Parameter of event {self.name} with name {param.name} "
                    f"has the same name of an already existing event in thread {self.ctx_thread.name}",
                    param.getFileLocation(),
                )
            if self.ctx_scope.declExists(param.name):
                errorMsg(
                    f"Parameter of event {self.name} with name {param.name} "
                    f"has the same name of an already existing variable in the scope (thread {self.ctx_thread.name}).",
                    param.getFileLocation(),
                )
        if self.paramExists(param.name):
            errorMsg(
                f"Duplicated parameter declaration. {param.name} "
                f"has been already declared for event {self.name}",
                param.getFileLocation(),
            )
        self.params.append(param)

        # Add the parameters to the current scope
        self.ctx_scope.addDeclaration(param)

    def numParams(self):
        return len(self.params)

    def addImplicitYield(self):
        """Check if yield_terminate is the last instruction"""
        lastInst = (
            self.basic_blocks[-1].instructions[-1]
            if len(self.basic_blocks[-1].instructions) > 0
            else None
        )
        if not lastInst or not isinstance(lastInst, WeaveIRyield):
            self.basic_blocks[-1].addInstruction(
                WeaveIRyield(self, WIRinst.WeaveIRyieldTypes.YIELD, self.numParams())
            )

    def findParameter(self, name):
        return list(filter(lambda x: x.name == name, self.params))

    def paramExists(self, name):
        return len(self.findParameter(name)) != 0

    def getParams(self):
        return self.params

    def removeLastInst(self):
        """ Remove the last instruction from the current basic block """
        return self.curBB.removeLastInst()

    def addInstruction(self, inst):
        """ Adds instruction to current basic block """
        self.curBB.addInstruction(inst)

    def addOrMoveLastInstruction(self, inst):
        """ Adds the instruction to the current basic block. In case the same instruction already exists in the BB,
        this instruction is moved to the end of the BB. """
        if inst in self.curBB.instructions:
            self.curBB.instructions.remove(inst)
        self.curBB.addInstruction(inst)

    def addAssemblyBlock(self, asm):
        self.curBB.addInstruction(asm)

    def addComment(self, comment):
        self.curBB.addInstruction(comment)

    def getBasicBlocks(self):
        return self.filterScope(WeaveIRbasicBlock, self.basic_blocks)

    def getUses(self, searchFor: "WeaveIRregister") -> list:
        """
        Get all the instructions that use a given register
        @param searchFor: Search for the instructions that use this register
        @type searchFor: WeaveIRregister
        @return: List of instructions that use the register
        @rtype: list["WeaveIRinstruction"]
        """
        result = []
        for b in self.basic_blocks:
            for instr in b.getInstructions():
                if isinstance(instr, WeaveIRinstruction):
                    for op in instr.getInOps():
                        if isinstance(op, WeaveIRregister) and op is searchFor:
                            result.append(instr)
        return result

    def addBasicBlock(self, new_block):
        self.basic_blocks.append(new_block)
        self.curBB = new_block

    def removeBasicBlock(self, block):
        self.basic_blocks.remove(block)

    def getLabel(self, pre, post):
        label = f"__{pre}_{self.name}_{self.nr_blocks}_{post}"
        self.nr_blocks += 1
        return label

    def to_string(self, indent):
        p_string = ", ".join(p.to_string(next_indent(indent)) for p in self.params)
        b_string = "".join(
            [b.to_string(next_indent(indent)) for b in self.basic_blocks]
        )
        if self.isExternal:
            return indent_text(f"Extern event: {self.name} ({p_string})\n", indent)
        return indent_text(f"event: {self.name} ({p_string}):\n{b_string}\n", indent)


class WeaveIRbasicBlock(WeaveIRbase):
    def __init__(self, ctx, name):
        super().__init__(ctx)
        self._name = name
        # List of instructions
        self.instructions = []
        # List of all the out edges
        self._out_edges = []
        # List of all the out edges
        self._in_edges = []

        # List of instructions that reference this basic block.
        self._references = []

    @property
    def name(self):
        return self._name

    @property
    def out_edges(self):
        return self._out_edges

    @property
    def in_edges(self):
        return self._in_edges

    def removeOutEdge(self, edge):
        self._out_edges.remove(edge)

    def removeInEdge(self, edge):
        self._in_edges.remove(edge) if edge in self._in_edges else None

    def addOutEdge(self, edge):
        self._out_edges.append(edge)

    def addInEdge(self, edge):
        self._in_edges.append(edge)

    def resetOutEdges(self):
        self.out_edges.clear()

    @property
    def references(self):
        return self._references

    def addRef(self, ref_inst: "WeaveIRbranch"):
        self._references.append(ref_inst)

    def setName(self, name):
        self._name = name

    def getInstructions(self, withComments: bool = True):
        if withComments:
            return self.instructions
        else:
            return list(filter(lambda i: not isinstance(i, WeaveIRcomment), self.instructions))

    def addInstruction(self, inst):
        self.instructions.append(inst)

    def removeLastInst(self):
        return self.instructions.pop()

    def to_string(self, indent):
        body_string = ""
        prevFileLocation = None
        for inst in self.instructions:
            if (
                    inst.getFileLocation() is not None
                    and not inst.getFileLocation().sameLine(prevFileLocation)
            ):
                prevFileLocation = inst.getFileLocation()
                if self.inlineCode:
                    body_string += indent_text(
                        ";; " + inst.getFileLocation().getLine() + "\n",
                        next_indent(indent),
                    )
            body_string += inst.to_string(next_indent(indent)) + "\n"

        in_edges_string = ", ".join([e.name for e in self.in_edges])
        out_edges_string = ", ".join([e.name for e in self.out_edges])
        in_edges_string = f"in: [{in_edges_string}]"
        out_edges_string = f"out: [{out_edges_string}]"
        return indent_text(
            f"{self.name}:  {in_edges_string}, {out_edges_string}\n{body_string}",
            indent,
        )


class WeaveIRinstruction(WeaveIRbase, ABC):
    """Base class for Instructions in the WeaveIR
    Instructions are things that can be added to a basic block. They must
    always have a dataType associated to it. This is for type checking.
    Qualifiers are also important for constants, sign or unsigned behavior.
    Some instructions return. The return operand is a register that is stored
    in ret_op. If the instruction does not return, then this is None
    """

    def __init__(self, ctx):
        super().__init__(ctx)
        self._in_ops = []
        self._ret_op = None

    def setRetOp(self, ret_op):
        self._ret_op = ret_op

    @abstractmethod
    def getAsOperand(self):
        """Used during WeaveIR generation to obtain the value to be used as
        operand for another instruction"""
        pass

    def isRegRead(self, reg):
        """Check if a register is used as a read operand of the instruction

        Args:
            reg (WeaveIRregister): Register to search
        """
        fil = filter(
            lambda i: isinstance(i, WeaveIRregister) and i.number == reg, self.getInOps()
        )
        return len(list(fil)) > 0

    def isRegWritten(self, reg):
        """Check if a register is used as a write operand of the instruction

        Args:
            reg (WeaveIRregister): Register to search
        """
        return reg == self._ret_op.number

    def getInOps(self):
        """Get the input operands for this instruction

        Returns:
            list: input operands
        """
        return self._in_ops

    def getReturnReg(self):
        """Get the return register of the instruction

        Returns:
            WeaveIRregister: Return register
        """
        return self._ret_op

    @property
    def curBB(self) -> WeaveIRbasicBlock:
        """Get the current basic block
            Current basic block is an event property. But if we are generating a
            weaveIR instruction, and we need to get the current BB, we can use this
            as a proxy to get the current BB from the event.

        Returns:
            WeaveIRbasicBlock: Current basic block
        """
        return self.ctx_event.curBB


class WeaveIRpadding(WeaveIRbase):
    """This class represents a padding inside the struct

    This is used for alignment purposes of the data structure

    """

    def __init__(self, ctx, size):
        super().__init__(ctx)
        self._size = size

    def getSize(self, loc: FileLocation = None) -> int:
        return self._size

    @property
    def name(self):
        return f"___anon_padding_{self._size}"

    def to_string(self, indent):
        return indent_text(f"padding: {self._size}\n", indent)


class WeaveIRstructDecl(WeaveIRbase):
    def __init__(self, ctx: WeaveIRbase, name: str, fields: list = None):
        super().__init__(ctx)
        self._name = name
        self.regs = {}  # Map of element name, register number

        self.dataType = WIRinst.WeaveIRuserDefinedType(0, WIRinst.WeaveIRtypes.struct)
        self._fields = []
        if fields is None:
            fields = []
        self.setFields(fields)

    def setFields(self, fields: list):
        self._fields = fields
        size = sum([f.getSize() for f in self._fields])
        self.dataType.setSize(size)

    def getFields(self) -> list:
        return self._fields

    def getField(self, name: str):
        """
        Get field of struct by name
        @param name: The name of the field
        @type name: str
        @return: The field or None, if not found
        @rtype: WeaveIRbase | None
        """
        for f in self._fields:
            if f.name == name:
                return f
        return None

    def getFieldOffset(self, name: str) -> int:
        offset = 0
        for f in self._fields:
            if f.name == name:
                return offset
            offset += f.getSize()
        return -1

    def assignRegisters(self, ctx: WeaveIRbase, fileLocation: FileLocation):
        """Assign registers to the fields of the type declaration"""
        for f in self._fields:
            if isinstance(f, WeaveIRstructDecl):
                f.assignRegisters(ctx, fileLocation)
            elif not isinstance(f, WeaveIRpadding):
                regNum = ctx.ctx_scope.getNextRegister()
                debugMsg(
                    5, f"Assigning register {regNum} to field {f.name} in {self._name}"
                )
                f.addReg(WeaveIRregister(ctx, regNum, WIRinst.WeaveIRregTypes.gpr, f.dtype))
                f.setFileLocation(fileLocation)

    @property
    def name(self) -> str:
        return self._name

    def getSize(self, fileLocation: FileLocation = None) -> int:
        return self.dataType.getSize(fileLocation)

    def getScale(self, fileLocation: FileLocation = None) -> int:
        return 0

    def getAsOperand(self) -> None:
        errorMsg("Type declaration cannot be used as operand", self.getFileLocation())

    def to_string(self, indent) -> str:
        fields_string = "".join(
            [f.to_string(next_indent(indent)) for f in self._fields]
        )
        return indent_text(f"typeDecl {self.name}:\n{fields_string}", indent)


class WeaveIRunionDecl(WeaveIRbase):
    def __init__(self, ctx: WeaveIRbase, name: str, fields: list = None):
        super().__init__(ctx)
        self._name = name
        self.dataType = WIRinst.WeaveIRuserDefinedType(0, WIRinst.WeaveIRtypes.union)
        self._fields = fields
        self.setFields(fields)

    def setFields(self, fields: list):
        if fields is None:
            fields = []
            self._fields = []
        if len(fields) == 0:
            return
        self._fields = fields

        size = max([f.getSize() for f in self._fields])
        self.dataType.setSize(size)

    def getFields(self) -> list:
        return self._fields

    def getField(self, name: str):
        """
        Get field of union by name
        @param name: The name of the field
        @type name: str
        @return: The field or None, if not found
        @rtype: WeaveIRbase | None
        """
        for f in self._fields:
            if f.name == name:
                return f
        return None

    def assignRegisters(self, ctx: WeaveIRbase, fileLocation: FileLocation):
        """Assign registers to the fields of the type declaration"""
        regNum = ctx.ctx_scope.getNextRegister()
        debugMsg(
            5, f"Assigning register {regNum} to the fields in {self._name}"
        )
        for f in self._fields:
            f.addReg(WeaveIRregister(ctx, regNum, WIRinst.WeaveIRregTypes.gpr, f.dtype, f.quals))
            f.setFileLocation(fileLocation)

    @property
    def name(self) -> str:
        return self._name

    def getSize(self, fileLocation: FileLocation = None) -> int:
        return self.dataType.getSize(fileLocation)

    def getScale(self, fileLocation: FileLocation = None) -> int:
        return 0

    def getAsOperand(self) -> None:
        errorMsg("Type declaration cannot be used as operand", self.getFileLocation())

    def to_string(self, indent) -> str:
        fields_string = "".join(
            [f.to_string(next_indent(indent)) for f in self._fields]
        )
        return indent_text(f"typeDecl {self.name}:\n{fields_string}", indent)


class WeaveIRGlobalDecl(WeaveIRbase):
    def __init__(self, ctx, var_name, typ, quals=None, var_data=None):
        super().__init__(ctx)

        if quals is None:
            quals = []
        self._qualifiers = quals
        self.dataType = typ
        self.data = var_data
        self.name = var_name
        self._size = typ.getSize(self.getFileLocation())

    def setSize(self, size):
        self._size = size

    @property
    def size(self):
        return self._size

    def getType(self):
        return self.dataType

    @property
    def value(self):
        return self.data.value

    @property
    def fullName(self):
        name = self.name
        if self.ctx_event:
            name = self.ctx_event.name + "::" + name
        if self.ctx_thread:
            name = self.ctx_thread.name + "::" + name
        return name

    def to_string(self, indent):
        return indent_text(
            f"constexp {self.dataType.name} {self.fullName} = {self.value};\n",
            indent,
        )


class WeaveIRDecl(WeaveIRinstruction):
    def __init__(self, ctx, var_name, typ, typ_point=None, quals=None, reg_num=None):
        super().__init__(ctx)

        # To generate SSA form, we use a list
        if quals is None:
            quals = []

        if len(quals) == 0:
            quals = [WIRinst.WeaveIRqualifiers.signed]

        self.regs = (
            [WeaveIRregister(self, reg_num, WIRinst.WeaveIRregTypes.gpr, typ, quals)]
            if reg_num is not None
            else []
        )

        self._qualifiers = quals
        self.dataType = typ
        self.pointeeType = typ_point
        self._name = var_name
        self._isStatic = False
        self._isExternal = False
        self._isPrivate = False
        self._assignment = None
        self._size = typ.getSize(self.getFileLocation())
        self._isRead = False
        self._isWritten = False
        # List of instructions that reference this variable.
        self.references = []

    def addNewReg(self, num):
        """Creates a register based on a number and add it to the list

        Args:
            num (int): new register value
        """
        if not self.regs[-1].isGPR:
            errorMsg(
                "Adding a new SSA value to a non general purpose register is illegal"
            ), self.getFileLocation()
        self.regs.append(
            WeaveIRregister(num, WIRinst.WeaveIRregTypes.gpr, self.dtype, self._qualifiers)
        )

    def addReg(self, reg):
        """Add an already existing register

        Args:
            reg (WeaveIRregister): The register to add
        """
        self.regs.append(reg)

    @property
    def name(self):
        return self._name

    def setSize(self, size):
        self._size = size

    @property
    def size(self):
        return self._size

    @property
    def curReg(self):
        return self.regs[-1] if len(self.regs) > 0 else None

    @property
    def isPointer(self):
        return self.dataType == WIRinst.WeaveIRtypes.ptr and self.pointeeType

    @property
    def isLocalPointer(self):
        return self.isPointer and WIRinst.WeaveIRqualifiers.spmem in self._qualifiers

    @property
    def isStatic(self):
        return self._isStatic

    def setStatic(self, val: bool):
        self._isStatic = val

    @property
    def isExternal(self):
        return self._isExternal

    def setExternal(self, val: bool):
        self._isExternal = val

    @property
    def isPrivate(self):
        return self._isPrivate

    def setPrivate(self, val: bool):
        self._isPrivate = val

    @property
    def isConstant(self) -> bool:
        return WIRinst.WeaveIRqualifiers.const in self._qualifiers

    @property
    def isAssigned(self) -> bool:
        return self._assignment is not None

    def setAssigned(self, val) -> None:
        self._assignment = val

    def getAssigned(self):
        return self._assignment

    @property
    def isStruct(self):
        return isinstance(self.dataType, WeaveIRstructDecl)

    @property
    def isUnion(self):
        return isinstance(self.dataType, WeaveIRunionDecl)

    def getPointeeType(self):
        return self.pointeeType

    def getAsOperand(self):
        self.setIsRead()
        if self.isConstant:
            return self._assignment
        if not self.curReg:
            errorMsg(
                "Returning an operand with no registers on it", self.getFileLocation()
            )
        return self.curReg

    @property
    def fullName(self):
        name = self.name
        if self.ctx_event:
            name = self.ctx_event.name + "::" + name
        if self.ctx_thread:
            name = self.ctx_thread.name + "::" + name
        return name

    @property
    def getRegs(self):
        return self.regs

    def getSize(self, fileLocation: FileLocation = None) -> int:
        """Get the size in bytes of the declaration

        If the data type is a struct, then this will recursively
        get the size. If it is a base datatype WeaveIRdataTypes, then
        it uses the getSize method of the data type

        Returns:
            int: size in bytes
        """
        if not fileLocation:
            fileLocation = self.getFileLocation()
        return self.dataType.getSize(fileLocation)

    @property
    def isRead(self) -> bool:
        return self._isRead

    @property
    def isWritten(self) -> bool:
        return self._isWritten

    def setIsRead(self) -> None:
        self._isRead = True

    def setIsWritten(self) -> None:
        self._isWritten = True

    def to_string(self, indent):
        if len(self.regs) > 0:
            priv = "private " if self.isPrivate else ""
            if self.isStatic:
                return indent_text(
                    f"static {priv}{self.dataType.name} {self.fullName};\n", indent
                )
            if self.isExternal:
                return indent_text(
                    f"extern {priv}{self.dataType.name} {self.fullName};\n", indent
                )
            if self.isPrivate:
                return indent_text(
                    f"private {priv}{self.dataType.name} {self.fullName};\n", indent
                )
            return indent_text(
                f"alloca {priv}{self.regs[0].name} {self.dataType.name} {self.fullName};\n",
                indent,
            )
        else:
            return indent_text(f"{self.dataType.name} {self.name};\n", indent)

    def addRef(self, ref_inst):
        if not isinstance(ref_inst, WeaveIRinstruction):
            errorMsg(
                "Trying to add a reference to a declaration that is not an instruction",
                self.getFileLocation(),
            )
        self.references.append(ref_inst)


class WeaveIRParamDecl(WeaveIRDecl):
    # This class extends normal declarations for parameters, such that the
    # event parameters property can be determined
    def __init__(self, ctx, var_name, typ, typ_point, quals, reg_num):
        super().__init__(ctx, var_name, typ, typ_point, quals, reg_num)
        self.regs[0].regType = WIRinst.WeaveIRregTypes.opbuff

    def to_string(self, indent):
        return f"{self.regs[0].name} {self.dataType.name}"


class WeaveIRthreadDecl(WeaveIRDecl):
    # This class extends normal declarations for threads, such that the
    # thread_local property can be determined, and there is a differentiation
    # with event local variables
    def __init__(self, ctx, var_name, typ, typ_point, quals, reg_num=None):
        super().__init__(ctx, var_name, typ, typ_point, quals, reg_num)

    def to_string(self, indent):
        priv = "private " if self.isPrivate else ""
        if self.isStatic:
            return indent_text(
                f"static {priv}{self.dataType.name} {self.ctx_thread.name}::{self.name};\n",
                indent,
            )
        if self.isExternal:
            errorMsg(
                "External thread local variable not supported", self.getFileLocation()
            )

        return indent_text(
            f"thread_local {self.regs[0].name} {self.dataType.name} {self.name};\n",
            indent,
        )


class WeaveIRregister(WeaveIRbase):
    def __init__(
            self, ctx, num, ty: WIRinst.WeaveIRregTypes, dtype=WIRinst.WeaveIRtypes.unknown, quals=None
    ):
        super().__init__(ctx)
        if quals is None:
            quals = []
        self.reg_num = num
        self.regType = ty
        self.dataType = dtype
        self.allocated = None
        self.setQuals(quals)

    @property
    def name(self):
        if self.regType == WIRinst.WeaveIRregTypes.opbuff:
            return "%ob_" + str(self.number)
        return "%" + str(self.number)

    @property
    def number(self):
        return self.reg_num

    @property
    def isGPR(self):
        return self.regType == WIRinst.WeaveIRregTypes.gpr

    @property
    def isOBuff(self):
        return self.regType == WIRinst.WeaveIRregTypes.opbuff

    @property
    def isControl(self):
        return self.regType == WIRinst.WeaveIRregTypes.control

    def allocate(self, val):
        """Set the equivalent string for the operand

        Args:
            val (str): String of the register name
        """
        self.allocated = val

    @property
    def alreadyAllocated(self):
        """Check if register has already been allocated

        Returns:
            bool: True if register was allocated
        """
        return self.allocated is not None

    def __eq__(self, __value: "WeaveIRregister") -> bool:
        return self.number == __value.number and self.regType == __value.regType

    def getAllocation(self):
        """Get the current register allocation

        Returns:
            str: Register allocation
        """
        return self.allocated

    def to_string(self, indent):
        pass


class WeaveIRimmediate(WeaveIRinstruction):
    def __init__(self, ctx, val=None, dataType=None, quals=None, inLoop=False):
        super().__init__(ctx)

        self._originalValue = val
        self._value = None
        self._inLoop = inLoop

        if quals:
            if isinstance(quals, list):
                self._qualifiers = quals.copy()
            else:
                self.addQualifier(quals)
        else:
            self._inferQuals()

        # if the data type has not been set or the data type is a type declaration, infer the data type based on the
        # value. The latter condition is true, if in a conditional statement, the field of a struct is compared against
        # a literal. In this case, the data type is from the struct, which is unknown.
        if dataType is None or isinstance(dataType, WeaveIRstructDecl) or isinstance(dataType, WeaveIRunionDecl):
            self._inferType()
        else:
            self.dataType = dataType

        # set the value based on the type and qualifiers
        self.setValue(val)

    def setValue(self, v):
        # If the value is an FP, convert it to an integer bit representation
        self._originalValue = v
        if self.dtype.isFloatingPoint:
            if self.dtype == WIRinst.WeaveIRtypes.float:
                self._value = struct.pack("f", v)
            elif self.dtype == WIRinst.WeaveIRtypes.double:
                self._value = struct.pack("d", v)
            else:
                errorMsg(
                    f"Unsupported floating point type {self.dtype.name}",
                    self.getFileLocation(),
                )
        else:
            try:
                if self.dtype == WIRinst.WeaveIRtypes.i32:
                    if self.isSigned():
                        self._value = struct.pack("i", v)
                    elif not self.isSigned():
                        # special -1 integer
                        if v == -1:
                            v = 0xffff_ffff
                        self._value = struct.pack("I", v)
                elif self.dtype == WIRinst.WeaveIRtypes.i64:
                    if self.isSigned():
                        self._value = struct.pack("q", v)
                    elif not self.isSigned():
                        # special -1 integer
                        if v < 0:
                            # compute the 2's complement
                            v = (0x1_0000_0000_0000_0000 + v)
                        self._value = struct.pack("Q", v)
                else:
                    self._value = v
            except struct.error:
                errorMsg(
                    f"Unsupported integer (type: {self.dtype.name}): {v}",
                    self.getFileLocation(),
                )

    def _inferType(self):
        # If the current statement is a declaration with an assignment as in
        #   double var0 = 304830948;
        # the literal which is an integer in this case, will be a double no matter what.
        if self.ctx_instruction and isinstance(self.ctx_instruction, WeaveIRDecl):
            self.dataType = self.ctx_instruction.dataType
        elif isinstance(self._originalValue, int):
            self.dataType = WIRinst.WeaveIRtypes.i64
        elif isinstance(self._originalValue, float):
            self.dataType = WIRinst.WeaveIRtypes.double
        elif isinstance(self._originalValue, str):
            self.dataType = WIRinst.WeaveIRtypes.void

    def _inferQuals(self):
        # If the current statement is a declaration with an assignment as in
        #   double var0 = 304830948;
        # the literal which is an integer in this case, will be a double no matter what.
        if self.ctx_instruction and isinstance(self.ctx_instruction, WeaveIRDecl):
            self.setQuals(self.ctx_instruction.quals.copy())
        elif not isinstance(self._originalValue, str):
            self.addQualifier(WIRinst.WeaveIRqualifiers.signed if self._originalValue < 0
                              else WIRinst.WeaveIRqualifiers.unsigned)

    def getValue(self):
        if isinstance(self._value, (bytes, bytearray)):
            integer = int.from_bytes(self._value, byteorder="little",
                                     signed=WIRinst.WeaveIRqualifiers.signed in self.quals)
            # if self.dtype.isFloatingPoint:
            #     return abs(integer)
            return integer
        return self._value

    @property
    def isInLoop(self) -> bool:
        return self._inLoop

    def getOriginalValue(self):
        return self._originalValue

    def getAsOperand(self):
        return self

    @property
    def name(self) -> str:
        return str(self.getValue())

    def to_string(self, indent):
        pass


class WeaveIRsymConst(WeaveIRbase):
    def __init__(self, ctx, namespace, nameSymbol, valueSymbol):
        super().__init__(ctx)
        self.namespace = namespace
        self._value = nameSymbol
        self.dataType = valueSymbol.data.dataType
        self._operand = valueSymbol
        self.dataType = WIRinst.WeaveIRtypes.unknown

    @property
    def value(self):
        return self._value

    def setValue(self, v):
        self._value = v

    def getAsOperand(self):
        return self._operand

    @property
    def name(self):
        if len(self.namespace) > 0:
            return f"{self.namespace}::{str(self._value)}"
        return str(self._value)

    def to_string(self, indent):
        pass


class WeaveIRsymPtr(WeaveIRbase):
    def __init__(self, ctx, namespace, nameSymbol, isExternal=False):
        super().__init__(ctx)
        self.namespace = namespace
        # Name of the symbol
        self._value = nameSymbol
        self.dataType = WIRinst.WeaveIRtypes.ptr
        self.address = None
        self._isExternal = isExternal

    @property
    def isExternal(self):
        return self._isExternal

    def setExternal(self, isExternal):
        self._isExternal = isExternal

    @property
    def value(self):
        return self._value

    def setValue(self, v):
        self._value = v

    def getAsOperand(self):
        return self

    @property
    def name(self):
        if len(self.namespace) > 0:
            return f"{self.namespace}::{str(self._value)}"
        return str(self._value)

    def to_string(self, indent):
        pass


class WeaveIRbinaryOps(WeaveIRinstruction):
    """Class to support operations in the form 'B op C'

    This is the base class to be used for the different three
    address operations supported in WeaveIR
    """

    def to_string(self, indent):
        pass

    def __init__(self, ctx=None):
        super().__init__(ctx)
        ctx.ctx_instruction = self
        self.instType = WIRinst.WeaveIRarithTypes.UNKNOWN
        self._in_ops = [None, None]

    @property
    def left(self):
        return self._in_ops[0]

    @property
    def right(self):
        return self._in_ops[1]

    def setOpType(self, op):
        self.instType = op

    def setLeft(self, left):
        self._in_ops[0] = left
        self._setQualifierBasedOnOperands()

    def setRight(self, right):
        self._in_ops[1] = right
        self._setQualifierBasedOnOperands()

    def _setQualifierBasedOnOperands(self):
        if self.right and self.left:
            qualifierLeft = WIRinst.WeaveIRqualifiers.signed if self.left.isSigned() \
                else WIRinst.WeaveIRqualifiers.unsigned
            qualifierRight = WIRinst.WeaveIRqualifiers.signed if self.right.isSigned() \
                else WIRinst.WeaveIRqualifiers.unsigned

            if qualifierLeft == WIRinst.WeaveIRqualifiers.signed or qualifierRight == WIRinst.WeaveIRqualifiers.signed:
                self.addQualifier(WIRinst.WeaveIRqualifiers.signed)
            else:
                self.addQualifier(WIRinst.WeaveIRqualifiers.unsigned)
        elif self.right:
            qualifier = WIRinst.WeaveIRqualifiers.signed if self.right.isSigned() \
                else WIRinst.WeaveIRqualifiers.unsigned
            self.addQualifier(qualifier)
        elif self.left:
            qualifier = WIRinst.WeaveIRqualifiers.signed if self.left.isSigned() \
                else WIRinst.WeaveIRqualifiers.unsigned
            self.addQualifier(qualifier)
        else:
            qualifiers = self.quals
            try:
                qualifiers.remove(WIRinst.WeaveIRqualifiers.signed)
            except ValueError:
                pass
            try:
                qualifiers.remove(WIRinst.WeaveIRqualifiers.unsigned)
            except ValueError:
                pass
            self.setQuals(qualifiers)

    def getAsOperand(self):
        return self._ret_op


class WeaveIRarith(WeaveIRbinaryOps):
    def __init__(self, ctx, dataType, opType, left, right):
        super().__init__(ctx)
        self.dataType = dataType
        self.instType = opType
        self.setLeft(left)
        self.setRight(right)

    def to_string(self, indent):
        if not (self.getReturnReg().isGPR or self.getReturnReg().isControl):
            errorMsg(
                "Result of binary operations must be stored in a general purpose register. "
                f"received {self.getReturnReg().name}",
                self.getFileLocation(),
            )

        if not self.instType or self.instType is WIRinst.WeaveIRarithTypes.UNKNOWN:
            errorMsg("Unknown arithmetic operation", self.getFileLocation())

        qual = "sig" if self.isSigned() else "unsig"
        return indent_text(
            f"{self.getReturnReg().name} = {self.instType.value} {qual} {self.dataType.name}, {self.left.name}, "
            f"{self.right.name}",
            indent,
        )


class WeaveIRbitwise(WeaveIRbinaryOps):
    def __init__(self, ctx, dataType, opType, left, right):
        super().__init__(ctx)
        self.dataType = dataType
        self.instType = opType
        self.setLeft(left)
        self.setRight(right)

    def to_string(self, indent):
        if self.getReturnReg() is None:
            errorMsg(
                "Result of binary operations must be stored in a register."
                "This is an internal bug, please report",
                self.getFileLocation(),
            )
        if not (self.getReturnReg().isGPR or self.getReturnReg().isControl):
            errorMsg(
                "Result of binary operations must be stored in a general purpose register. "
                f"Received {self.getReturnReg().name}",
                self.getFileLocation(),
            )

        if not self.instType or self.instType is WIRinst.WeaveIRbitwiseTypes.UNKNOWN:
            errorMsg("Unknown bitwise operation", self.getFileLocation())

        qual = "sig" if WIRinst.WeaveIRqualifiers.signed in self._qualifiers else "unsig"
        return indent_text(
            f"{self.getReturnReg().name} = {self.instType.value} {qual} {self.dataType}, "
            f"{self.left.name}, {self.right.name}",
            indent,
        )


class WeaveIRcompare(WeaveIRbinaryOps):
    def __init__(self, ctx, dataType, opType, left, right):
        super().__init__(ctx)
        self.dataType = dataType
        self.instType = opType
        self.setLeft(left)
        self.setRight(right)
        self._branchInstr = None
        ctx.ctx_instruction = self

    def setBranchInstr(self, branch: "WeaveIRBranch"):
        self._branchInstr = branch

    def getBranchInstr(self):
        return self._branchInstr

    def to_string(self, indent):
        if not (self.getReturnReg().isGPR or self.getReturnReg().isControl):
            errorMsg(
                f"Result of binary operations must be stored in a general purpose register. "
                f"Received {self.getReturnReg().name}",
                self.getFileLocation(),
            )

        if not self.instType or self.instType is WIRinst.WeaveIRcompareTypes.UNKNOWN:
            errorMsg("Unknown bitwise operation", self.getFileLocation())

        op = "icomp" if self.dataType.isInteger else "fcomp"

        return indent_text(
            f"{self.getReturnReg().name} = {op} {self.instType.value} {self.dataType}, "
            f"{self.left.name}, {self.right.name}",
            indent,
        )


class WeaveIRmemory(WeaveIRinstruction):
    def __init__(self, ctx, dataType: WIRinst.WeaveIRtypes, opType: WIRinst.WeaveIRmemoryTypes, ops: list = None):
        super().__init__(ctx)
        self.dataType: WIRinst.WeaveIRtypes = dataType
        self.instType: WIRinst.WeaveIRmemoryTypes = opType
        self._in_ops = ops if ops else [None, None, None]

    def getAsOperand(self):
        return self.getReturnReg()

    def getOffset(self):
        return self.getInOps()[1] if self.isLocal() else None

    def getElementOffset(self):
        return self.getInOps()[2] if self.isLocal() else None

    def isLocal(self):
        return self.instType.isLocal

    def setInstType(self, ty: WIRinst.WeaveIRmemoryTypes):
        self.instType = ty

    def addOperand(self, op):
        self._in_ops.append(op)

    @property
    def dtype(self) -> WIRinst.WeaveIRtypes:
        """ Get the data type of the instruction. If the memory instruction is for dereferencing a struct, return the
        type of the accessed field, if it is set. Otherwise, return that this type is a struct. If it is not a struct,
        just return the type of the scalar value."""
        if isinstance(self.dataType, WeaveIRstructDecl):
            if len(self._in_ops) == 3:
                return self._in_ops[2].dtype
            else:
                return WIRinst.WeaveIRtypes.struct
        elif isinstance(self.dataType, WeaveIRunionDecl):
            if len(self._in_ops) == 3:
                return self._in_ops[2].dtype
            else:
                return WIRinst.WeaveIRtypes.union

        return self.dataType

    @property
    def quals(self):
        if ((isinstance(self.dataType, WeaveIRstructDecl) or isinstance(self.dataType, WeaveIRunionDecl))
                and len(self._in_ops) == 3):
            return self._in_ops[2].quals
        return self._qualifiers

    def to_string(self, indent) -> str:
        if self.getReturnReg() and not self.getReturnReg().isGPR:
            errorMsg(
                f"Result of binary operations must be stored in a general purpose register. "
                f"Received {self.getReturnReg().name}",
                self.getFileLocation(),
            )
        operands = ", ".join([i.name for i in self.getInOps()])
        if self.getReturnReg():
            return indent_text(
                f"{self.getReturnReg().name} = {self.instType.value} {self.dataType.name}, {operands}",
                indent,
            )
        else:
            return indent_text(
                f"{self.instType.value} {self.dataType.name}, {operands}",
                indent,
            )


class WeaveIRbranch(WeaveIRbinaryOps):
    def __init__(
            self, ctx, instType: WIRinst.WeaveIRBranchTypes, dst_block: WeaveIRbasicBlock, left=None, right=None
    ):
        super().__init__(ctx)
        self.dataType = None
        self.instType = instType
        self.setLeft(left)
        self.setRight(right)
        self.setRetOp(None)
        self._dst_block = dst_block
        self._dst_block.addRef(self)
        if left is not None and left.isSigned() or right is not None and right.isSigned():
            self.addQualifier(WIRinst.WeaveIRqualifiers.signed)

    @property
    def label(self):
        return self._dst_block.name

    def changeDestBlock(self, new_block):
        self._dst_block = new_block

    def getDestBlock(self):
        return self._dst_block

    def to_string(self, indent):
        if self.instType == WIRinst.WeaveIRBranchTypes.UNCONDITIONAL:
            return indent_text(f"{self.instType.value} {self.label}", indent)
        else:
            return indent_text(
                f"{self.instType.value} {self.left.name}, {self.right.name}, {self.label}",
                indent,
            )


class WeaveIRcombinedInst(WeaveIRbinaryOps):
    def __init__(self, ctx, combinedInstr: list, ops: list = None):
        """
        @param ctx: Context
        @type ctx: WeaveIRbase
        @param combinedInstr: Which instructions are combined?
        @type combinedInstr: list[WeaveIRbinaryOps]
        @param ops: List of operands
        @type ops: list[WeaveIRbase]
        """
        super().__init__(ctx)
        assert len(combinedInstr) > 0
        self.inst = combinedInstr
        self.dataType = combinedInstr[0].dataType
        self._in_ops = ops if ops else [None, None, None]

    @property
    def dataType(self):
        return self.inst[0].dataType

    @dataType.setter
    def dataType(self, value: "WeaveIRtypes"):
        try:
            for i in self.inst:
                i.dataType = value
        except AttributeError:
            # The parent class calls the setter. However, the attributes do not exist yet as the super().__init__() is
            # called first. In this case, ignore the setting.
            pass


class WeaveIRShiftArith(WeaveIRcombinedInst):
    """
    An instruction that can hold a shift instruction and a bitwise arithmetic instruction.
    Updown can combine both instructions.
    """

    def __init__(self, ctx, shiftInstr: WeaveIRbitwise, logicInstr: WeaveIRbinaryOps, ops: list = None):
        super().__init__(ctx, [shiftInstr, logicInstr], ops)

    @property
    def shift_inst(self):
        return self.inst[0]

    @property
    def arith_inst(self):
        return self.inst[1]

    def to_string(self, indent):
        returnString = (f"SHBW: sh: {self.shift_inst.instType} {self.dataType.name}, "
                        f"arith: {self.arith_inst.instType} {self.dataType.name} ")
        returnString += ", ".join([f"{i.name}" for i in self.getInOps()])
        return indent_text(returnString, indent)


class WeaveIRcall(WeaveIRinstruction):
    def __init__(self, ctx, name, ops: list = None):
        super().__init__(ctx)
        self.name = name
        self.dataType = WIRinst.WeaveIRtypes.void
        self._in_ops = ops if ops else []
        self.definition = None

    def getAsOperand(self):
        return self.getReturnReg()

    def addInOperand(self, op):
        """Receive the instruction that produced this operand

        We use the instruction instead of the register because we want to
        get the dtype later on for checking call

        Args:
            op (_type_): _description_
        """
        if not (
                isinstance(op, WeaveIRimmediate)
                or isinstance(op, WeaveIRregister)
                or isinstance(op, WeaveIRsymPtr)
        ):
            errorMsg(
                f"Adding incorrect value of type {type(op)} to operands of call {self.name}",
                self.getFileLocation(),
            )
        self._in_ops.append(op)

    def getInOpTypes(self):
        return [i.dtype for i in self.getInOps()]

    def getDefinition(self):
        return self.definition

    def setDefinition(self, func_def, input_types_def):
        """Set pointer to definition of this function

        In the case of an intrinsic this points to the WeaveIntrinsic
        object that knows how to do code generation during inlining.

        @todo: There is currently no support for other type of functions
        so I am not sure how to change this in the future to support function
        definition yet.

        Args:
            func_def: Definition of the function.
            input_types_def: List of input types of the function
        """
        self.definition = func_def(self)
        self.definition.selectedInputTypes = input_types_def

    def to_string(self, indent):
        if self.getReturnReg() and not (self.getReturnReg().isGPR or self.getReturnReg().isControl):
            errorMsg(
                "Result of call operations should be stored in a general purpose register. "
                f"Received {self.getReturnReg().name}",
                self.getFileLocation(),
            )

        # TODO: Add to this print the input data type
        operands = ", ".join([f"{i.name}" for i in self.getInOps()])
        if self.getReturnReg():
            return indent_text(
                f"{self.getReturnReg().name} = call {self.name}, {operands}",
                indent,
            )
        else:
            return indent_text(
                f"call {self.name}, {operands}",
                indent,
            )


class WeaveIRyield(WeaveIRinstruction):
    def __init__(self, ctx, ty: WIRinst.WeaveIRyieldTypes, num_ops: int = 0):
        super().__init__(ctx)
        self.dataType = WIRinst.WeaveIRtypes.void
        self._in_ops = [num_ops]
        self.instType = ty

    def getAsOperand(self):
        return None

    def to_string(self, indent):
        return indent_text(
            f"{self.instType.value} {self._in_ops[0]}",
            indent,
        )


class WeaveIRcast(WeaveIRinstruction):
    def __init__(self, ctx, out_type, inReg):
        super().__init__(ctx)
        self.dataType = out_type
        self._in_ops = [inReg]

    def getAsOperand(self):
        return self.getReturnReg()

    @property
    def originOp(self):
        return self._in_ops[0]

    def to_string(self, indent):
        return indent_text(
            f"{self.getReturnReg().name} = cast {self.dataType.name} from {self.originOp.dtype.name} "
            f"{self.originOp.name}",
            indent,
        )


class WeaveIRsend(WeaveIRinstruction):
    def __init__(self, ctx, ty: WIRinst.WeaveIRsendTypes, ops: list = None):
        super().__init__(ctx)
        self.dataType = WIRinst.WeaveIRtypes.void
        self._in_ops = ops if ops else []
        self.instType = ty

    def getAsOperand(self):
        return None

    def to_string(self, indent):
        operands = ", ".join([f"{i.name}" for i in self.getInOps()])
        return indent_text(
            f"{self.instType.value} {operands}",
            indent,
        )


class WeaveIRupdate(WeaveIRinstruction):
    # The last operand is the mask. The mask determines what fields of the
    # event word are to be updated. We use the mask during lowering to determine
    # How many instructions we need to generate. The remaining operands are seen
    # From LSB to MSB: event word, number of operands, thread id, network id.
    def __init__(self, ctx, ops: list):
        super().__init__(ctx)
        self.dataType = WIRinst.WeaveIRtypes.i64
        # Operand order is :
        # Input Event Word, [event label, number of operands, thread id, network id], mask
        # where the number in [] is optional, but must match the number of ones in the mask
        self._in_ops = ops if ops else []

    def getAsOperand(self):
        return self.getReturnReg()

    def to_string(self, indent):
        if not isinstance(self._in_ops[-1], WeaveIRimmediate):
            errorMsg(
                "Last operand 'mask' of update instruction must be an immediate",
            )
        operands = ", ".join([f"{i.name}" for i in self.getInOps()[:-1]])
        # change mask to binary
        mask = bin(int(self.getInOps()[-1].name))
        operands += f", {mask}"
        return indent_text(
            f"{self.getReturnReg().name} = ew_update {operands}",
            indent,
        )


class WeaveIRcomment(WeaveIRbase):
    def __init__(self, ctx, comment):
        super().__init__(ctx)
        self.comment = comment

    def getAsOperand(self):
        errorMsg(
            "Comments cannot be operands. This should never be reached",
            self.getFileLocation(),
        )
        return None

    def getValue(self):
        return self.comment

    def to_string(self, indent):
        comment = self.comment
        if comment[-1] != "\n":
            comment += "\n"
        return indent_text(f";; {comment}", indent)


class WeaveIRasmOperand(WeaveIRbase):
    def __init__(self, ctx: WeaveIRbase, symName, constraints, opName):
        super().__init__(ctx)
        self.symbolName = symName
        self.constraints = constraints
        self.varName = opName
        self.wirValue = None

    def resolveOperand(self):
        # Resolve constraints
        if WIRinst.WeaveIRasmConstraints.REGISTER in self.constraints:
            # Sanity checks
            debugMsg(
                6,
                f"Found register constraint for operand {self.symbolName} attached to {self.varName}",
            )
            if WIRinst.WeaveIRasmConstraints.LABEL in self.constraints:
                errorMsg(
                    "Found conflicting constraints: Register and Label",
                    self.getFileLocation(),
                )

            if self.ctx.ctx_scope:
                self.wirValue = self.varName

                # Since we do not know, what instructions the developer uses in the assembly block, we assume that the
                # register is both read and written. This is important in case, UDW removes unused registers later.
                if isinstance(self.varName.ctx, WeaveIRDecl):
                    decl: WeaveIRDecl = self.varName.ctx
                    decl.setIsRead()
                    decl.setIsWritten()
            else:
                errorMsg(
                    f"Trying to reference {self.varName} in context with no declarations (outside a thread or event?)",
                    self.getFileLocation(),
                )
        if WIRinst.WeaveIRasmConstraints.LABEL in self.constraints:
            debugMsg(
                6,
                f"Found label constraint for operand {self.symbolName} attached to {self.varName.getAsOperand()}",
            )
            self.wirValue = self.varName.getAsOperand()
        if WIRinst.WeaveIRasmConstraints.LITERAL in self.constraints:
            debugMsg(
                6,
                f"Found literal constraint for operand {self.symbolName} attached to {self.varName.getAsOperand()}",
            )
            self.wirValue = self.varName.getAsOperand()
        if WIRinst.WeaveIRasmConstraints.OUTPUT in self.constraints:
            debugMsg(
                6,
                f"Found output constraint for operand {self.symbolName}attached to {self.varName}",
            )
            if isinstance(self.varName.ctx, WeaveIRDecl):
                decl: WeaveIRDecl = self.varName.ctx
                decl.setIsWritten()

    def getValue(self):
        return self.wirValue

    def applyOperand(self, line: str):
        newVal = None
        if WIRinst.WeaveIRasmConstraints.REGISTER in self.constraints:
            if isinstance(self.wirValue, WeaveIRregister):
                newVal = self.wirValue.getAllocation()
            else:
                errorMsg('Trying to apply an immediate as a register operand', self.getFileLocation())
        if (
                WIRinst.WeaveIRasmConstraints.LABEL in self.constraints
                or WIRinst.WeaveIRasmConstraints.LITERAL in self.constraints
        ):
            newVal = self.wirValue.name

        if newVal:
            debugMsg(9, f"Replacing %{self.symbolName} for {newVal} in {line}")
            return re.sub(re.escape(f"%{self.symbolName}"), re.escape(newVal), line)
        return line

    def to_string(self, indent):
        out = f"'{''.join([c.value for c in self.constraints])}' {self.varName} mapped to %{self.symbolName}"
        if self.wirValue:
            return indent_text(
                out
                + f" => {self.getValue().__class__.__name__}:{self.getValue().name}\n",
                indent,
            )
        else:
            return indent_text(
                out + "\n",
                indent,
            )


class WeaveIRcopyOperands(WeaveIRbase):
    def __init__(self, ctx: WeaveIRbase, operands: list):
        super().__init__(ctx)
        self._in_ops = operands

    def getAsOperand(self):
        return None

    def getInOps(self):
        return self._in_ops

    def to_string(self, indent):
        operands = ", ".join([f"{i.name}" for i in self.getInOps()])
        return indent_text(
            f"copy_operands {operands}",
            indent,
        )


class WeaveIRassembly(WeaveIRinstruction):
    def __init__(self, ctx, lines):
        super().__init__(ctx)
        self.lines = lines[0].split('\n')
        self.lines = [s.strip() for s in self.lines]
        self.operands = []  # Operands are dictionaries
        self._nativeInline = False

    def setNativeInline(self, val):
        self._nativeInline = val

    @property
    def isNativeInline(self):
        return self._nativeInline

    def getLines(self):
        return self.lines

    def addOperand(self, op: dict):
        self.operands.append(op)

    def applyOperands(self):
        for num, line in enumerate(self.lines):
            for op in self.operands:
                line = op.applyOperand(line)
            self.lines[num] = line

    def getAsOperand(self):
        errorMsg(
            "Assembly blocks cannot be operands. This should never be reached",
            self.getFileLocation(),
        )
        return None

    def resolveOperands(self):
        debugMsg(6, f"resolving {len(self.operands)} operands for assembly block")
        for op in self.operands:
            op.resolveOperand()

    def getValue(self):
        return

    def to_string(self, indent):
        name = "asm " if not self.isNativeInline else "asm native "
        out = (
            indent_text(name + "{\n", indent)
            if len(self.lines) > 0
            else indent_text(name + "{ }\n", indent)
        )
        for line in self.lines:
            out += indent_text(
                f"{line}\n",
                next_indent(indent),
            )
        if len(self.lines) > 0:
            out += indent_text("}, \n", indent)
        for op in self.operands:
            out += op.to_string(next_indent(indent))
        return out


class WeaveIRprint(WeaveIRinstruction):
    """Print Instruction has been previously used for
    debugging in the simulator. However, given the importance for
    this in applications, it is best if we add as a stand-alone
    instruction rather than some extension of WeaveIRcall"""

    def __init__(self, ctx, ops: list):
        super().__init__(ctx)
        self._in_ops = ops if ops else []

    def getAsOperand(self):
        return None

    def to_string(self, indent):
        operands = ", ".join([f"{i.name}" for i in self.getInOps()])
        return indent_text(f"print {operands} \n", indent)


class WeaveIRhash(WeaveIRinstruction):
    """hash intrinsics are used to generate hash values for the
    input operands. The hash function is determined by the hashType
    attribute."""

    def __init__(self, ctx, ops: list, hashType: WIRinst.WeaveIRhashTypes):
        super().__init__(ctx)
        self._in_ops = ops if ops else []
        self.hashType = hashType

    def getAsOperand(self):
        return self.getReturnReg()

    def to_string(self, indent):
        operands = ", ".join([f"{i.name}" for i in self.getInOps()])
        return indent_text(f"hash {operands} \n", indent)


class WeaveIRperflog(WeaveIRinstruction):
    """Perflog to store timing information"""

    def __init__(self, ctx, ops: list):
        super().__init__(ctx)
        self._in_ops = ops if ops else []

    def getAsOperand(self):
        return None

    def to_string(self, indent):
        operands = ", ".join([f"{i.name}" for i in self.getInOps()])
        return indent_text(f"perflog {operands} \n", indent)