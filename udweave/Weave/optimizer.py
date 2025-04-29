from Weave.intrinsics import *
from Weave.helper import isPowerOfTwo, log2


class WeaveIRopt:
    @classmethod
    @abstractmethod
    def apply(cls, program: WeaveIRmodule):
        """Apply the optimization"""
        pass

    @classmethod
    @abstractmethod
    def getOptName(cls):
        """Given name of the optimization"""
        pass

    @classmethod
    def getAllOpts(cls):
        return list(cls.__subclasses__())

    @classmethod
    def getOpt(cls, name):
        return list(filter(lambda i: i.getOptName() == name, cls.getAllOpts()))


class inlineIntrinsicsOpt(WeaveIRopt):
    @classmethod
    def apply(cls, program: WeaveIRmodule):
        for thr in program.getThreads():
            for evnt in thr.getEvents():
                for bb in evnt.getBasicBlocks():
                    originalInsts = bb.getInstructions()
                    for inum, inst in enumerate(originalInsts):
                        if isinstance(inst, WeaveIRcall):
                            defi = inst.getDefinition()
                            if defi and isinstance(defi, WeaveIntrinsicFunc):
                                newInsts = defi.generateWeaveIR()
                                if newInsts:
                                    originalInsts.pop(inum)
                                    originalInsts[inum:inum] = newInsts

    @classmethod
    def getOptName(cls):
        return "inlineIntrinsic"


class emptyBasicBlockMergingOpt(WeaveIRopt):
    @classmethod
    def apply(cls, program: WeaveIRmodule):
        debugMsg(10, "OPT: Starting empty basic block merging")
        for thr in program.getThreads():
            for event in thr.getEvents():
                to_remove = []
                bb_to_merge = None
                for bb in event.getBasicBlocks():
                    if bb_to_merge is not None:
                        # Merge all references to current block
                        for ref in bb_to_merge.references:
                            debugMsg(
                                10,
                                f"Changing reference from BB {ref}, instruction \"{ref.to_string(0)}\" "
                                f"to {bb.name}"
                            )
                            # Change the references of the instructions in the previous BB (bb_to_merge) that point to
                            # the current BB (bb).
                            ref.changeDestBlock(bb)
                            # Add those instructions to the reference list of the current BB.
                            bb.addRef(ref)
                        # Merge all incoming edges to current block
                        for inb in bb_to_merge.in_edges:
                            debugMsg(
                                10,
                                f"Changing outgoing edge {inb.name}->{bb_to_merge.name} to {inb.name}->{bb.name}",
                            )
                            inb.removeOutEdge(bb_to_merge)
                            inb.addOutEdge(bb)
                            bb.addInEdge(inb)
                        bb.removeInEdge(bb_to_merge)
                        bb_to_merge = None

                    if len(bb.getInstructions(withComments=False)) == 0:
                        debugMsg(5, f"Marking empty basic block {bb.name} to remove")
                        to_remove.append(bb)
                        bb_to_merge = bb
                for bb in to_remove:
                    event.removeBasicBlock(bb)

                # if the first block was empty, it has been removed.
                if event.getBasicBlocks()[0].name == "":
                    event.getBasicBlocks()[0].setName("entry")

    @classmethod
    def getOptName(cls):
        return "emptyBasicBlockMerging"


class ifCmpBranchMerging(WeaveIRopt):
    @classmethod
    def getOptName(cls):
        return "ifCmpBranchMerging"

    @classmethod
    def apply(cls, program: WeaveIRmodule):
        debugMsg(10, "OPT: Starting compare and branch instruction merging")
        for thr in program.getThreads():
            for event in thr.getEvents():
                for bb in event.getBasicBlocks():
                    originalInsts = bb.getInstructions()
                    for inum, inst in enumerate(originalInsts):
                        if isinstance(inst, WeaveIRcompare) and inst.getBranchInstr() is not None:
                            debugMsg(10, f"Found compare instruction {inst.to_string(0)}")
                            branchInstr = inst.getBranchInstr()

                            # Translate the compare instruction into the appropriate compare/branch instruction
                            if inst.instType == WeaveIRcompareTypes.EQUAL:
                                branchInstr.setOpType(WeaveIRBranchTypes.CONDITIONALNEQ)
                            elif inst.instType == WeaveIRcompareTypes.NOTEQUAL:
                                branchInstr.setOpType(WeaveIRBranchTypes.CONDITIONALEQ)
                            elif (inst.instType == WeaveIRcompareTypes.UGREAT
                                  or inst.instType == WeaveIRcompareTypes.SGREAT):
                                branchInstr.setOpType(WeaveIRBranchTypes.CONDITIONALLE)
                            elif (inst.instType == WeaveIRcompareTypes.ULESS
                                  or inst.instType == WeaveIRcompareTypes.SLESS):
                                branchInstr.setOpType(WeaveIRBranchTypes.CONDITIONALGE)
                            elif (inst.instType == WeaveIRcompareTypes.UGREATEQ
                                  or inst.instType == WeaveIRcompareTypes.SGREATEQ):
                                branchInstr.setOpType(WeaveIRBranchTypes.CONDITIONALLT)
                            elif (inst.instType == WeaveIRcompareTypes.ULESSEQ
                                  or inst.instType == WeaveIRcompareTypes.SLESSEQ):
                                branchInstr.setOpType(WeaveIRBranchTypes.CONDITIONALGT)

                            branchInstr.setLeft(inst.left)
                            branchInstr.setRight(inst.right)
                            debugMsg(10, f"Replacing {inst.to_string(0)} with {branchInstr.to_string(0)}")
                            originalInsts[inum] = branchInstr


class operandSubstitution(WeaveIRopt):
    """
    This class implements the operand folding optimization. The following operations are currently supported:
    n * 2^m -> n << m
    n / 2^m -> n >> m
    n % 2^m -> n & (2^m - 1)
    n << m with m >= dataType -> 0
    n >> m with m >= dataType -> 0
    """

    @classmethod
    def getOptName(cls):
        return "operandSubstitution"

    @classmethod
    def __replaceInstr(cls, index: int, remove: int, newInsts, originalInsts: list) -> None:
        """
        Replaces the instruction at index with the new instructions.
        @param index: Current index
        @type index: int
        @param remove: How many instructions shall be removed from index?
        @type remove: int
        @param newInsts: List of the instructions to be inserted at index or None, if instructions should just be
        deleted.
        @type newInsts: list[WeaveIRinstruction] | None
        @param originalInsts: Instructions in the entire BB
        @type originalInsts: list[WeaveIRinstruction]
        """
        if newInsts is None:
            originalInsts[index:index + remove] = []  # delete the instruction(s)
        else:
            originalInsts[index:index + remove] = newInsts

    @classmethod
    def __checkNegShift(cls, shiftInstr: WeaveIRinstruction) -> bool:
        """
        If the immediate of a shift instruction is negative, the shift is turned around and the immediate
        becomes positive:

        sli Xs, Xe, -$shift -> sri Xs, Xe, $shift
        sri Xs, Xe, -$shift -> sli Xs, Xe, $shift
        """

        if not isinstance(shiftInstr, WeaveIRbitwise):
            return False

        if not isinstance(shiftInstr.right, WeaveIRimmediate):
            return False

        if not (shiftInstr.instType == WeaveIRbitwiseTypes.SHFTLFT or
                shiftInstr.instType == WeaveIRbitwiseTypes.LSHFTRGT or
                shiftInstr.instType == WeaveIRbitwiseTypes.ASHFTRGT):
            return False

        immediate = shiftInstr.right
        if immediate.getOriginalValue() >= 0:
            return False

        immediate.setValue(abs(immediate.getOriginalValue()))
        if shiftInstr.instType == WeaveIRbitwiseTypes.SHFTLFT:
            shiftInstr.instType = WeaveIRbitwiseTypes.LSHFTRGT
        elif shiftInstr.instType == WeaveIRbitwiseTypes.LSHFTRGT:
            shiftInstr.instType = WeaveIRbitwiseTypes.SHFTLFT
        else:  # arithmetic right shift
            errorMsg(
                f"Cannot handle arithmetic right shift with a negative immediate (immediate: "
                f"{immediate.getOriginalValue()}",
                shiftInstr.getFileLocation(),
            )
        return False

    @classmethod
    def __optimizeShiftAndArith(cls, shiftInstr: WeaveIRinstruction, arithInstr: WeaveIRinstruction, index: int,
                                originalInsts: list) -> bool:
        """
        -------------------------------------------------------------------------------------
            sli Xs, Xe, $shift
            addi Xe, Xd, $imm0
        ->
            sladdii Xs, Xd, $shift, $imm0
        -------------------------------------------------------------------------------------
            sli Xs, Xe, $shift                  |    sli Xs, Xe, $shift
            ori Xe, Xd, $imm0                   |    or Xe, Xt, Xd
        ->                                      | ->
            slorii Xs, Xd, $shift, $imm0        |    slori Xs, Xd, $shift, Xt
                                                |
                                                | Since or is commutative:
                                                |    sli Xs, Xe, $shift
                                                |    or Xt, Xe, Xd
                                                | ->
                                                |    slori Xs, Xd, $shift, Xt
        @param shiftInstr: The shift instruction to be optimized
        @type shiftInstr: WeaveIRinstruction
        @param arithInstr: The following add instruction
        @type arithInstr: WeaveIRinstruction
        @param index: Current index in the BB
        @type index: int
        @param originalInsts: all instructions in the BB
        @type originalInsts: list[WeaveIRinstruction]
        @return: True, if shift and arithmetic instruction could be combined, false otherwise
        @rtype: bool
        """
        if not (isinstance(shiftInstr, WeaveIRbitwise) and
                (isinstance(arithInstr, WeaveIRarith) or isinstance(arithInstr, WeaveIRbitwise))):
            return False

        if not (shiftInstr.instType == WeaveIRbitwiseTypes.SHFTLFT or
                shiftInstr.instType == WeaveIRbitwiseTypes.LSHFTRGT):
            return False

        if not (arithInstr.instType == WeaveIRarithTypes.IADDITION or
                arithInstr.instType == WeaveIRarithTypes.ISUBTRACTION or
                arithInstr.instType == WeaveIRbitwiseTypes.BWOR or
                arithInstr.instType == WeaveIRbitwiseTypes.BWAND):
            return False

        if shiftInstr.dataType != arithInstr.dataType:
            return False

        shiftImmediate = None
        if isinstance(shiftInstr.right, WeaveIRimmediate):
            shiftImmediate = shiftInstr.right
        else:
            # The shift needs to have an immediate value on the right. If the immediate is on the left, this is not
            # a combined instruction, since a version which takes a register for the shift is not part of the ISA.
            return False

        # If the return register of the first instruction is not the source register of the second instruction,
        # we cannot combine them as both instructions belong to different operations.
        # The arithInstr is commutative, if it is an addition.
        if isinstance(arithInstr.left, WeaveIRregister) and shiftInstr.getReturnReg() is arithInstr.left:
            arithImmediate = arithInstr.right
        elif (
                isinstance(arithInstr.right, WeaveIRregister) and
                shiftInstr.getReturnReg() is arithInstr.right and
                arithInstr.instType.isCommutative()
        ):
            arithImmediate = arithInstr.left
        else:
            # The instructions do not belong to each other
            return False

        if not isinstance(arithImmediate, WeaveIRimmediate):
            return False

        if (
                arithImmediate.getValue() < 0 or shiftImmediate.getValue() < 0 or
                arithImmediate.getValue() >= (1 << splitImmediates.ImmediateType.ShortI.value) or
                shiftImmediate.getValue() >= (1 << splitImmediates.ImmediateType.TiniestI.value)
        ):
            return False

        # If the return register of the shift instruction is anywhere else used, except the following arithmetic
        # instruction. In this case, we cannot merge the instructions.
        uses = shiftInstr.ctx_scope.getUses(shiftInstr.getReturnReg())
        if len(uses) != 1 or uses[0] is not arithInstr:
            return False

        combineSLandArith = WeaveIRShiftArith(
            ctx=shiftInstr.ctx,
            shiftInstr=shiftInstr,
            logicInstr=arithInstr,
            ops=[
                shiftInstr.left,  # the original source register
                shiftImmediate,  # the shift immediate
                arithImmediate,  # the operand for the BW operation
            ]
        )
        combineSLandArith.setRetOp(arithInstr.getReturnReg())
        combineSLandArith.setFileLocation(shiftInstr.getFileLocation())
        cls.__replaceInstr(index, 2, [combineSLandArith], originalInsts)
        return True

    @classmethod
    def __getRemainder(cls, valReg: WeaveIRregister, curInst: WeaveIRarith, immediate: WeaveIRimmediate) -> list:
        """
        Returns the instructions to calculate the remainder of a division by a power of two.
        inspired by https://godbolt.org/z/qh76cvszG
        @param valReg: The register that should hold the final value
        @type valReg: WeaveIRregister
        @param curInst: Current modulo instruction
        @type curInst: WeaveIRarith
        @param immediate: The immediate value to check if it is a power of two
        @type immediate: WeaveIRimmediate
        @return: List of new instructions to compute the remainder
        @rtype: list[WeaveIRinstruction]
        """
        bitSize = curInst.dataType.getSize(curInst.getFileLocation()) * 8
        # get the sign bit
        instrs = []
        getSign = WeaveIRbitwise(
            ctx=curInst.ctx,
            opType=WeaveIRbitwiseTypes.ASHFTRGT,
            dataType=curInst.dataType,
            left=curInst.left,
            right=WeaveIRimmediate(curInst.ctx, bitSize - 1),
        )
        getSign.setRetOp(valReg)
        getSign.setFileLocation(curInst.getFileLocation())
        instrs.append(getSign)

        # construct the remainder
        mask = WeaveIRbitwise(
            ctx=curInst.ctx,
            opType=WeaveIRbitwiseTypes.LSHFTRGT,
            dataType=curInst.dataType,
            left=getSign.getReturnReg(),
            right=WeaveIRimmediate(curInst.ctx, bitSize - log2(immediate.getValue())),
        )
        mask.setRetOp(valReg)
        mask.setFileLocation(curInst.getFileLocation())
        instrs.append(mask)

        # add the mask to the dividend
        addMaskDividend = WeaveIRarith(
            ctx=curInst.ctx,
            opType=WeaveIRarithTypes.IADDITION,
            dataType=curInst.dataType,
            left=mask.getReturnReg(),
            right=curInst.left,
        )
        addMaskDividend.setRetOp(curInst.getReturnReg())
        addMaskDividend.setFileLocation(curInst.getFileLocation())
        instrs.append(addMaskDividend)
        return instrs

    @classmethod
    def __optimizeModI(cls, curInst: WeaveIRinstruction, index: int, originalInsts: list) -> bool:
        """
        n % 2^m -> n & (2^m - 1) only for unsigned

        For signed it n:
            n % 2^m -> n & (2^m - 1) if n >= 0
            n % 2^m -> n | ~(2^m - 1) if n < 0
            However, at this point, we do not know the value of n
        @param curInst: Current instruction
        @type curInst: WeaveIRinstruction
        @param index: Index of the instruction in the BB
        @type index: int
        @param originalInsts: All instructions in the current BB
        @type originalInsts: list[WeaveIRinstruction]
        @return: True, if the instruction could be optimized, False otherwise
        @rtype: bool
        """

        if not (
                isinstance(curInst, WeaveIRarith) and
                curInst.instType == WeaveIRarithTypes.MODULO and
                isinstance(curInst.right, WeaveIRimmediate)
        ):
            return False

        immediate = curInst.right
        if immediate.getValue() == 0:
            errorMsg("Division by zero", curInst.getFileLocation())

        if abs(immediate.getValue()) == 1:
            newInstr = WeaveIRmemory(
                ctx=curInst.ctx,
                dataType=curInst.dataType,
                opType=WeaveIRmemoryTypes.LOAD,
                ops=[WeaveIRimmediate(curInst.ctx, 0)],
            )
            newInstr.setFileLocation(curInst.getFileLocation())
            newInstr.setRetOp(curInst.getReturnReg())
            cls.__replaceInstr(index, 1, [newInstr], originalInsts)
            return True

        if isPowerOfTwo(abs(immediate.getValue())):
            if not curInst.isSigned() and immediate.getValue() > 0:
                mod = WeaveIRbitwise(
                    ctx=curInst.ctx,
                    opType=WeaveIRbitwiseTypes.BWAND,
                    dataType=curInst.dataType,
                    left=curInst.left,
                    right=WeaveIRimmediate(curInst.ctx, immediate.getValue() - 1),
                )
                mod.setRetOp(curInst.getReturnReg())
                mod.setFileLocation(curInst.getFileLocation())
                cls.__replaceInstr(index, 1, [mod], originalInsts)
                return True
            else:
                curInst.ctx_scope.startScope()
                valReg = WeaveIRregister(
                    curInst.ctx,
                    curInst.ctx_scope.getNextRegister(),
                    WeaveIRregTypes.gpr,
                    curInst.dtype,
                    curInst.quals,
                )
                valReg.setFileLocation(curInst.getFileLocation())

                instrs = cls.__getRemainder(valReg, curInst, immediate)

                # Divide by shifting right
                modulo = WeaveIRbitwise(
                    ctx=curInst.ctx,
                    opType=WeaveIRbitwiseTypes.BWAND,
                    dataType=curInst.dataType,
                    left=valReg,
                    right=WeaveIRimmediate(curInst.ctx, -immediate.getValue()),
                )
                modulo.setRetOp(valReg)
                modulo.setFileLocation(curInst.getFileLocation())
                instrs.append(modulo)

                sub = WeaveIRarith(
                    ctx=curInst.ctx,
                    opType=WeaveIRarithTypes.ISUBTRACTION,
                    dataType=curInst.dataType,
                    left=curInst.left,
                    right=modulo.getReturnReg(),
                )
                sub.setRetOp(curInst.getReturnReg())
                sub.setFileLocation(curInst.getFileLocation())
                instrs.append(sub)

                cls.__replaceInstr(index, 1, instrs, originalInsts)
                curInst.ctx_scope.endScope()
                return True
        return False

    @classmethod
    def __optimizeDivI(cls, curInst: WeaveIRinstruction, index: int, originalInsts: list) -> bool:
        """
        Optimizing the division
            n / 2^m -> n >> m
            n / -2^m -> 0 - (n >> m)
            n / 1   -> n
            n / 0   -> error
            n / -1  -> 0-n
            0 / n   -> 0
        @param curInst: Current instruction
        @type curInst: WeaveIRinstruction
        @param index: Index of the instruction in the BB
        @type index: int
        @param originalInsts: All instructions in the current BB
        @type originalInsts: list[WeaveIRinstruction]
        @return: True, if the instruction could be optimized, False otherwise
        @rtype: bool
        """
        if not (isinstance(curInst, WeaveIRarith) and curInst.instType == WeaveIRarithTypes.IDIVIDE):
            return False

        if isinstance(curInst.left, WeaveIRimmediate) and curInst.left.getOriginalValue() == 0:
            newInstr = WeaveIRmemory(
                ctx=curInst.ctx,
                dataType=curInst.dataType,
                opType=WeaveIRmemoryTypes.LOAD,
                ops=[WeaveIRimmediate(curInst.ctx, 0)],
            )
            newInstr.setFileLocation(curInst.getFileLocation())
            newInstr.setRetOp(curInst.getReturnReg())
            cls.__replaceInstr(index, 1, [newInstr], originalInsts)
            return True

        if not isinstance(curInst.right, WeaveIRimmediate):
            return False

        immediate = curInst.right
        if immediate.getValue() == 0:
            errorMsg("Division by zero", curInst.getFileLocation())

        if immediate.getValue() == 1:
            # If we have something like a = a / 1
            if curInst.left == curInst.getReturnReg():
                cls.__replaceInstr(index, 1, None, originalInsts)  # delete this instruction
                return True
            # If we have something like b = a / 1, we have to copy a into b
            else:
                newInstr = WeaveIRmemory(
                    ctx=curInst.ctx,
                    dataType=curInst.dataType,
                    opType=WeaveIRmemoryTypes.LOAD,
                    ops=[curInst.left],
                )
                newInstr.setFileLocation(curInst.getFileLocation())
                newInstr.setRetOp(curInst.getReturnReg())
                cls.__replaceInstr(index, 1, [newInstr], originalInsts)
                return True

        if immediate.getValue() == -1:
            newLoad = WeaveIRmemory(
                ctx=curInst.ctx,
                dataType=curInst.dataType,
                opType=WeaveIRmemoryTypes.LOAD,
                ops=[WeaveIRimmediate(curInst.ctx, 0)],
            )
            newLoad.setFileLocation(curInst.getFileLocation())
            newLoad.setRetOp(curInst.getReturnReg())
            newSub = WeaveIRarith(
                ctx=curInst.ctx,
                opType=WeaveIRarithTypes.ISUBTRACTION,
                dataType=curInst.dataType,
                left=newLoad.getReturnReg(),
                right=curInst.left,
            )
            newSub.setFileLocation(curInst.getFileLocation())
            newSub.setRetOp(curInst.getReturnReg())
            cls.__replaceInstr(index, 1, [newLoad, newSub], originalInsts)
            return True

        if isPowerOfTwo(abs(immediate.getValue())):
            if not curInst.isSigned():
                divide = WeaveIRbitwise(
                    ctx=curInst.ctx,
                    opType=WeaveIRbitwiseTypes.ASHFTRGT,
                    dataType=curInst.dataType,
                    left=curInst.left,
                    right=WeaveIRimmediate(curInst.ctx, log2(immediate.getValue())),
                )
                divide.setRetOp(curInst.getReturnReg())
                divide.setFileLocation(curInst.getFileLocation())
                cls.__replaceInstr(index, 1, [divide], originalInsts)
                return True
            else:
                # inspired by https://godbolt.org/z/qh76cvszG
                curInst.ctx_scope.startScope()
                valReg = WeaveIRregister(
                    curInst.ctx,
                    curInst.ctx_scope.getNextRegister(),
                    WeaveIRregTypes.gpr,
                    curInst.dtype,
                    curInst.quals,
                )
                valReg.setFileLocation(curInst.getFileLocation())

                instrs = cls.__getRemainder(valReg, curInst, immediate)

                # Divide by shifting right
                divide = WeaveIRbitwise(
                    ctx=curInst.ctx,
                    opType=WeaveIRbitwiseTypes.ASHFTRGT,
                    dataType=curInst.dataType,
                    left=curInst.getReturnReg(),
                    right=WeaveIRimmediate(curInst.ctx, log2(immediate.getValue())),
                )
                divide.setRetOp(curInst.getReturnReg())
                divide.setFileLocation(curInst.getFileLocation())
                instrs.append(divide)

                if immediate.getValue() < 0:
                    newLoad = WeaveIRmemory(
                        ctx=curInst.ctx,
                        dataType=curInst.dataType,
                        opType=WeaveIRmemoryTypes.LOAD,
                        ops=[WeaveIRimmediate(curInst.ctx, 0)],
                    )
                    newLoad.setFileLocation(curInst.getFileLocation())
                    newLoad.setRetOp(valReg)
                    instrs.append(newLoad)

                    newSub = WeaveIRarith(
                        ctx=curInst.ctx,
                        opType=WeaveIRarithTypes.ISUBTRACTION,
                        dataType=curInst.dataType,
                        left=newLoad.getReturnReg(),
                        right=divide.getReturnReg(),
                    )
                    newSub.setFileLocation(curInst.getFileLocation())
                    newSub.setRetOp(curInst.getReturnReg())
                    instrs.append(newSub)

                cls.__replaceInstr(index, 1, instrs, originalInsts)
                curInst.ctx_scope.endScope()
                return True
        return False

    @classmethod
    def __optimizeMulI(cls, curInst: WeaveIRinstruction, index: int, originalInsts: list) -> bool:
        """
        Optimizing the multiplication
            n * 2^m -> n << m
            n * 1   -> n
            n * 0   -> 0
            n * -1  -> 0-n
        @param curInst: Current instruction
        @type curInst: WeaveIRinstruction
        @param index: Index of the instruction in the BB
        @type index: int
        @param originalInsts: All instructions in the current BB
        @type originalInsts: list[WeaveIRinstruction]
        @return: True, if the instruction could be optimized, False otherwise
        @rtype: bool
        """
        if not (isinstance(curInst, WeaveIRarith) and curInst.instType == WeaveIRarithTypes.IMULT):
            return False

        # Multiplication is commutative, so we check both operands for the immediates
        if isinstance(curInst.left, WeaveIRimmediate):
            immediate = curInst.left
        elif isinstance(curInst.right, WeaveIRimmediate):
            immediate = curInst.right
        else:
            return False

        if immediate.getValue() == 0:
            newInstr = WeaveIRmemory(
                ctx=curInst.ctx,
                dataType=curInst.dataType,
                opType=WeaveIRmemoryTypes.LOAD,
                ops=[WeaveIRimmediate(curInst.ctx, 0)],
            )
            newInstr.setFileLocation(curInst.getFileLocation())
            newInstr.setRetOp(curInst.getReturnReg())
            cls.__replaceInstr(index, 1, [newInstr], originalInsts)
            return True
        if immediate.getValue() == 1:
            nonImmediateInput = curInst.left if not isinstance(curInst.left, WeaveIRimmediate) else curInst.right

            # If we have something like a = a * 1
            if nonImmediateInput == curInst.getReturnReg():
                cls.__replaceInstr(index, 1, None, originalInsts)
                return True
            # If we have something like b = a * 1, we have to copy a into b
            else:
                newInstr = WeaveIRmemory(
                    ctx=curInst.ctx,
                    dataType=curInst.dataType,
                    opType=WeaveIRmemoryTypes.LOAD,
                    ops=[nonImmediateInput],
                )
                newInstr.setFileLocation(curInst.getFileLocation())
                newInstr.setRetOp(curInst.getReturnReg())
                cls.__replaceInstr(index, 1, [newInstr], originalInsts)
                return True

        if immediate.getValue() == -1:
            newLoad = WeaveIRmemory(
                ctx=curInst.ctx,
                dataType=curInst.dataType,
                opType=WeaveIRmemoryTypes.LOAD,
                ops=[WeaveIRimmediate(curInst.ctx, 0)],
            )
            newLoad.setFileLocation(curInst.getFileLocation())
            newLoad.setRetOp(curInst.getReturnReg())
            newSub = WeaveIRarith(
                ctx=curInst.ctx,
                opType=WeaveIRarithTypes.ISUBTRACTION,
                dataType=curInst.dataType,
                left=newLoad.getReturnReg(),
                right=curInst.left if not isinstance(curInst.left, WeaveIRimmediate) else curInst.right,
            )
            newSub.setFileLocation(curInst.getFileLocation())
            newSub.setRetOp(curInst.getReturnReg())
            cls.__replaceInstr(index, 1, [newLoad, newSub], originalInsts)
            return True
        elif isPowerOfTwo(abs(immediate.getValue())):
            newInstrs = []
            newShift = WeaveIRbitwise(
                ctx=curInst.ctx,
                opType=WeaveIRbitwiseTypes.SHFTLFT,
                dataType=curInst.dataType,
                left=curInst.left if not isinstance(curInst.left, WeaveIRimmediate) else curInst.right,
                right=WeaveIRimmediate(curInst.ctx, log2(immediate.getValue())),
            )
            newShift.setRetOp(curInst.getReturnReg())
            newShift.setFileLocation(curInst.getFileLocation())
            newInstrs.append(newShift)

            # m = i * -8 -> m = 0 - (i << 3)
            if immediate.getValue() < 0:
                curInst.ctx_scope.startScope()
                valReg = WeaveIRregister(
                    curInst.ctx,
                    curInst.ctx_scope.getNextRegister(),
                    WeaveIRregTypes.gpr,
                    curInst.dtype,
                    curInst.quals,
                )
                valReg.setFileLocation(curInst.getFileLocation())
                newLoad = WeaveIRmemory(
                    ctx=curInst.ctx,
                    dataType=curInst.dataType,
                    opType=WeaveIRmemoryTypes.LOAD,
                    ops=[WeaveIRimmediate(curInst.ctx, 0)],
                )
                newLoad.setFileLocation(curInst.getFileLocation())
                newLoad.setRetOp(valReg)
                newInstrs.append(newLoad)
                newSub = WeaveIRarith(
                    ctx=curInst.ctx,
                    opType=WeaveIRarithTypes.ISUBTRACTION,
                    dataType=curInst.dataType,
                    left=newLoad.getReturnReg(),
                    right=newShift.getReturnReg(),
                )
                newSub.setFileLocation(curInst.getFileLocation())
                newSub.setRetOp(curInst.getReturnReg())
                newInstrs.append(newSub)
                curInst.ctx_scope.endScope()
            cls.__replaceInstr(index, 1, newInstrs, originalInsts)
            return True
        return False

    @classmethod
    def __optimizeShift(cls, curInst: WeaveIRinstruction, index: int, originalInsts: list) -> bool:
        """
        Optimizing the shift:
            n << m with m >= dataType -> 0
            n >> m with m >= dataType -> 0
        @param curInst: Current instruction
        @type curInst: WeaveIRinstruction
        @param index: Index of the instruction in the BB
        @type index: int
        @param originalInsts: All instructions in the current BB
        @type originalInsts: list[WeaveIRinstruction]
        @return: True, if the instruction could be optimized, False otherwise
        @rtype: bool
        """
        if (
                isinstance(curInst, WeaveIRbitwise) and isinstance(curInst.right, WeaveIRimmediate) and
                curInst.right.getValue() >= curInst.dataType.getSize(curInst.getFileLocation()) * 8
        ):

            if curInst.instType == WeaveIRbitwiseTypes.SHFTLFT or curInst.instType == WeaveIRbitwiseTypes.LSHFTRGT:
                newInstr = WeaveIRmemory(
                    ctx=curInst.ctx,
                    dataType=curInst.dataType,
                    opType=WeaveIRmemoryTypes.LOAD,
                    ops=[WeaveIRimmediate(curInst.ctx, 0)],
                )
                newInstr.setRetOp(curInst.getReturnReg())
                newInstr.setFileLocation(curInst.getFileLocation())
                cls.__replaceInstr(index, 1, [newInstr], originalInsts)
                return True
            elif curInst.instType == WeaveIRbitwiseTypes.ASHFTRGT:
                newInstr = WeaveIRmemory(
                    ctx=curInst.ctx,
                    dataType=curInst.dataType,
                    opType=WeaveIRmemoryTypes.LOAD,
                    ops=[WeaveIRimmediate(curInst.ctx, 0 if curInst.right.getOriginalValue() >= 0 else -1)],
                )
                newInstr.setRetOp(curInst.getReturnReg())
                newInstr.setFileLocation(curInst.getFileLocation())
                cls.__replaceInstr(index, 1, [newInstr], originalInsts)
                return True
        return False

    @classmethod
    def apply(cls, program: WeaveIRmodule):
        debugMsg(10, "OPT: Starting operand substitution")

        while True:
            # execute this pass until no operands have been substituted anymore
            somethingChanged = False
            for thr in program.getThreads():
                for event in thr.getEvents():
                    for bb in event.getBasicBlocks():
                        originalInsts = bb.getInstructions()
                        nextInst = None

                        # Go through the list from bottom up since we might insert instructions and do not want to mess
                        # up the indices.
                        for index, inst in reversed(list(enumerate(originalInsts))):
                            if nextInst:
                                somethingChanged |= cls.__optimizeShift(inst, index, originalInsts)
                                somethingChanged |= cls.__optimizeMulI(inst, index, originalInsts)
                                somethingChanged |= cls.__optimizeDivI(inst, index, originalInsts)
                                somethingChanged |= cls.__optimizeModI(inst, index, originalInsts)
                                somethingChanged |= cls.__checkNegShift(inst)
                                somethingChanged |= cls.__optimizeShiftAndArith(inst, nextInst, index, originalInsts)
                                inst = originalInsts[index]
                            nextInst = inst
            if not somethingChanged:
                break


class splitImmediates(WeaveIRopt):
    """
    Split immediate values into multiple instructions, if the bit field for
    the immediate in the instruction field does not fit.
    In that case, we split the immediate into a `movir` instruction and
    shift in the value, in case the immediate is too large even for the `movir`.
    """

    @classmethod
    def getOptName(cls):
        return "splitImmediates"

    class ImmediateType(Enum):
        """
        Enum for the type of instruction.
        The immediate sizes are different for each instruction type.
        """
        LongI = 21
        I = 16
        ShortI = 12
        SmallI = 6
        TinyI = 5
        TiniestI = 4

    @classmethod
    def __tryShiftingIn(cls, immediate: WeaveIRimmediate, originalInstr: WeaveIRinstruction) -> list:
        """ check, if the immediate can be built by shifting zeroes in from the left to the right. For instance,
        the IGNRCONT word is -1 >> 1. This method checks if the immediate can be build using this method.
        """

        def checkEquality(index: int, immediateIn: WeaveIRimmediate, shiftType: WeaveIRbitwiseTypes):
            # insert movir -1
            newImmediate = WeaveIRimmediate(
                ctx=immediateIn.ctx,
                val=-1,
                dataType=WeaveIRtypes.i64,
                quals=[WeaveIRqualifiers.signed],
            )
            newInstr = [(cls.__createLoadImmediate(newImmediate, originalInstr, retReg, WeaveIRtypes.i64))]

            # shift by index positions
            if index != 0:
                shiftInstr = WeaveIRbitwise(
                    ctx=immediateIn.ctx,
                    opType=shiftType,
                    dataType=WeaveIRtypes.i64,
                    left=newInstr[-1].getReturnReg(),
                    right=WeaveIRimmediate(originalInstr.ctx, index, WeaveIRtypes.i64, [WeaveIRqualifiers.unsigned]),
                )
                shiftInstr.setFileLocation(originalInstr.getFileLocation())
                shiftInstr.setRetOp(newInstr[-1].getReturnReg())
                newInstr.append(shiftInstr)
            return newInstr

        retReg = None if originalInstr.getReturnReg() is None else originalInstr.getReturnReg().reg_num

        searchValue = 0xffff_ffff_ffff_ffff
        immValue = immediate.getValue()
        # We check all positions from 64 down to 44 shifts to the right. If we have to shift for more than 44 places
        # to the right, we could use a normal movir to load the value.
        for i in range(44):
            if searchValue >> i == immValue:
                return checkEquality(i, immediate, WeaveIRbitwiseTypes.LSHFTRGT)

        # maybe from the right to the left?
        for i in range(64):
            if ((searchValue << i) & 0xffff_ffff_ffff_ffff) == immValue:
                return checkEquality(i, immediate, WeaveIRbitwiseTypes.SHFTLFT)

        return []

    @classmethod
    def __getImmediateFieldSize(cls, instr: WeaveIRinstruction) -> int:
        if isinstance(instr, WeaveIRarith):
            return splitImmediates.ImmediateType.I.value - 1  # immediate is always signed!
        if isinstance(instr, WeaveIRbitwise):
            if (
                    instr.instType == WeaveIRbitwiseTypes.SHFTLFT or
                    instr.instType == WeaveIRbitwiseTypes.LSHFTRGT or
                    instr.instType == WeaveIRbitwiseTypes.ASHFTRGT
            ):
                return splitImmediates.ImmediateType.SmallI.value
            return splitImmediates.ImmediateType.I.value
        if isinstance(instr, WeaveIRcompare):
            return splitImmediates.ImmediateType.I.value - 1  # immediate is always signed!
        if isinstance(instr, WeaveIRbranch):
            # There are 2 different branch instructions: signed and unsigned. Depending on that, the bit field size
            # of the immediate has an addition bit for the immediate in case the operation is unsigned.
            if instr.isSigned():
                return splitImmediates.ImmediateType.TinyI.value - 1
            else:
                return splitImmediates.ImmediateType.TinyI.value
        if isinstance(instr, WeaveIRmemory):
            return splitImmediates.ImmediateType.LongI.value - 1  # immediate is always signed!
        if isinstance(instr, WeaveIRShiftArith):
            return splitImmediates.ImmediateType.ShortI.value
        # if isinstance(instr, WeaveIRupdate):
        #     return splitImmediates.ImmediateType.ShortI.value

        errorMsg(f"Unknown immediate field bit size for instruction: {instr.to_string(0)}")

    @classmethod
    def __createLoadImmediate(cls, immediate: WeaveIRimmediate, originalInstr: WeaveIRinstruction, retReg,
                              dataType: WeaveIRtypes, shiftInValue=None) -> WeaveIRmemory:
        """
        Creates a load immediate instruction.
        @param immediate: The immediate value to be loaded
        @type immediate: WeaveIRimmediate
        @param originalInstr: The original instruction for context
        @type originalInstr: WeaveIRinstruction
        @param retReg: Is a return register available? If not, create one
        @type retReg:  int | None
        @param dataType: Data type of the immediate to be loaded
        @type dataType: WeaveIRtypes
        @param shiftInValue: If the shiftInValue is None, load the immediate, otherwise create a new immediate for the
        load.
        @type shiftInValue: int | None
        @return: The load instruction
        @rtype: WeaveIRmemory
        """
        valReg = WeaveIRregister(
            originalInstr.ctx,
            originalInstr.ctx_scope.getNextRegister() if retReg is None else retReg,
            WeaveIRregTypes.gpr,
            dataType,
            immediate.quals,
        )
        valReg.setFileLocation(originalInstr.getFileLocation())

        loadImmediate = WeaveIRmemory(
            ctx=originalInstr.ctx,
            dataType=dataType,
            opType=WeaveIRmemoryTypes.LOAD,
            ops=[immediate if shiftInValue is None else WeaveIRimmediate(
                ctx=originalInstr.ctx,
                val=shiftInValue,
                dataType=dataType,
                quals=immediate.quals
            )],
        )
        loadImmediate.setRetOp(valReg)
        loadImmediate.setFileLocation(originalInstr.ctx.getFileLocation())
        return loadImmediate

    @classmethod
    def __splitImmediate(cls, immediate: WeaveIRimmediate, originalInstr: WeaveIRinstruction, instrBB: list, inum: int)\
            -> tuple:
        """Splits an immediate value into multiple instructions
        depending on the length of the immediate value encoded in
        the instruction.

        Args:
            immediate (WeaveIRimmediate): The immediate that needs to be split (eventually)
            originalInstr (WeaveIRinstruction): The current instruction that the optimization is applied to
            inum (int): The index of the instruction in the basic block
        @param immediate: The immediate that needs to be split (eventually)
        @type immediate: WeaveIRimmediate
        @param originalInstr: The current instruction
        @type originalInstr: WeaveIRinstruction
        @param instrBB: The instructions in the BB
        @type instrBB: list[WeaveIRinstruction]
        @param inum: Index of the current instruction in the BB
        @type inum: int
        @return: A tuple containing the last instruction of the split, and the number of instructions that were
        inserted.
        @rtype: tuple[WeaveIRimmediate, int]
        """

        # TODO Some instructions (such as movir) handle negative numbers correctly, but others might not. We should
        #  check, if the immediate is negative and handle it accordingly. For instance, a `movir Xd -3` does not
        #  need to be converted. However, what is the smallest negative number that movir can handle using 21 bits?
        #  What about other instructions?
        value = immediate.getValue()
        size = immediate.dataType.getSize(immediate.getFileLocation()) * 8
        intDataType = WeaveIRtypes.i32 if size == 32 else WeaveIRtypes.i64

        retReg = None if originalInstr.getReturnReg() is None or isinstance(originalInstr, WeaveIRarith) \
            else originalInstr.getReturnReg().reg_num

        # Hold the resulting instructions. It allows us to check and update the previous instructions (i.e. the
        # shift operands).
        instructions = []

        if abs(value) >= (1 << size):
            errorMsg(
                f"The immediate ({value}) is out of range to fit into the data type {immediate.dataType.name}.",
                immediate.getFileLocation(),
            )

        if abs(value) >= (1 << cls.__getImmediateFieldSize(originalInstr)):
            # The very first instruction needs to be a movir as this one will reset the register
            currentValueIsZero = True

            originalInstr.ctx_scope.startScope()

            if immediate.isInLoop:
                warningMsg(
                    f"Immediate value {value} is larger than {cls.__getImmediateFieldSize(originalInstr)} bit values "
                    f"and is used in a loop. Check, if the immediate is split due to the size of the bit field of the "
                    f"associated instruction. Consider to improve the performance by defining the immediate in a "
                    f"variable outside of the loop to prevent it from being regenerated in every iteration. "
                    f"{originalInstr.getFileLocation()}",
                )

            # If the value fits into the 20 bit movir immediate field (+1 sign bit), we just need 1 movir. Otherwise,
            # we need to split the movir instruction into multiple 16 bit long segments as the OR instruction has only
            # 16 bits.
            if abs(value) < (1 << splitImmediates.ImmediateType.LongI.value - 1):
                instructions.append(cls.__createLoadImmediate(immediate, originalInstr, retReg, intDataType))
            else:
                # Try to optimize the immediate value by checking, if it can be created by shifting -1 by n positions
                # to the right. That is useful for, e.g., the IGNRCONT word, which is -1 >> 1. If we are successful in
                # doing this, we are already done and just need a movir Xd, -1 and a right shift operation.
                instructions = cls.__tryShiftingIn(immediate, originalInstr)

                if len(instructions) == 0:
                    # This loop goes through chunks of 16 bit and builds the register. Although the movir immediate
                    # can hold 20 bits, the immediates for `ori` cannot. Therefore, we cannot shift-in more than 16
                    # bits.
                    for part in range(
                            size - splitImmediates.ImmediateType.I.value,
                            -1,
                            -splitImmediates.ImmediateType.I.value,
                    ):
                        shiftInValue = (value >> part)

                        # Only insert a value into the target register, if there is anything to insert.
                        if shiftInValue & 0xFFFF != 0:
                            if currentValueIsZero:
                                instructions.append(cls.__createLoadImmediate(immediate, originalInstr, retReg,
                                                                              intDataType, shiftInValue))
                                currentValueIsZero = False
                            else:
                                newOR = WeaveIRbitwise(
                                    ctx=originalInstr.ctx,
                                    opType=WeaveIRbitwiseTypes.BWOR,
                                    dataType=intDataType,
                                    left=instructions[-1].getReturnReg(),
                                    right=WeaveIRimmediate(
                                        ctx=originalInstr.ctx,
                                        val=shiftInValue & 0xFFFF,  # automatic conversion into 2's complement, if <0
                                        dataType=intDataType,
                                    )
                                )
                                newOR.setFileLocation(originalInstr.getFileLocation())
                                newOR.setRetOp(instructions[-1].getReturnReg())
                                instructions.append(newOR)

                        # Shift the result register, only if there is data in the register
                        if not currentValueIsZero and part:
                            # check, if the previous instruction is a shift. If that is the case, just increment that
                            # shift by 16 bits, so that we can save a sli instruction.
                            if (
                                    isinstance(instructions[-1], WeaveIRbitwise) and
                                    instructions[-1].instType == WeaveIRbitwiseTypes.SHFTLFT
                            ):
                                instructions[-1].right.setValue(instructions[-1].right.getOriginalValue() +
                                                                splitImmediates.ImmediateType.I.value)
                            else:
                                newShift = WeaveIRbitwise(
                                    ctx=originalInstr.ctx,
                                    opType=WeaveIRbitwiseTypes.SHFTLFT,
                                    dataType=intDataType,
                                    left=instructions[-1].getReturnReg(),
                                    right=WeaveIRimmediate(
                                        ctx=originalInstr.ctx,
                                        val=splitImmediates.ImmediateType.I.value,
                                        dataType=intDataType,
                                    )
                                )
                                newShift.setFileLocation(originalInstr.getFileLocation())
                                newShift.setRetOp(instructions[-1].getReturnReg())
                                instructions.append(newShift)

            # We are done, print the instructions
            for inst in reversed(instructions):
                instrBB.insert(inum, inst)
            immediate = instructions[-1].getReturnReg()
            originalInstr.ctx_scope.endScope()

        return immediate, len(instructions)

    @classmethod
    def apply(cls, program: WeaveIRmodule):
        debugMsg(10, "OPT: Starting immediate splitting")
        for thr in program.getThreads():
            for event in thr.getEvents():
                for bb in event.getBasicBlocks():
                    originalInsts = bb.getInstructions()

                    # Go through the list from bottom up since we might insert instructions and do not want to mess
                    # up the indices.
                    for index, inst in reversed(list(enumerate(originalInsts))):
                        if isinstance(inst, WeaveIRbinaryOps):
                            if isinstance(inst.left, WeaveIRimmediate):
                                debugMsg(10, f"Found immediate {inst.to_string(0)}")
                                newInst = inst
                                immediate, insertedInstructions = cls.__splitImmediate(newInst.left, newInst,
                                                                                       originalInsts, index)
                                inst.setLeft(immediate)

                            if isinstance(inst.right, WeaveIRimmediate):
                                debugMsg(10, f"Found immediate {inst.to_string(0)}")
                                immediate, insertedInstructions = cls.__splitImmediate(inst.right, inst,
                                                                                       originalInsts, index)
                                inst.setRight(immediate)
                        # split the movir
                        elif isinstance(inst, WeaveIRmemory):
                            if inst.instType == WeaveIRmemoryTypes.LOAD:
                                if isinstance(inst.getInOps()[0], WeaveIRimmediate):
                                    debugMsg(10, f"Found immediate {inst.to_string(0)}")

                                    tmp, insertedInstructions = cls.__splitImmediate(inst.getInOps()[0], inst,
                                                                                     originalInsts, index)

                                    # remove the movir instruction as it has been replaced by the instructions in
                                    # __splitImmediate
                                    if insertedInstructions != 0:
                                        originalInsts.pop(index + insertedInstructions)
                        # TODO split the evi and evii (does not work at the moment due to register allocator, done in
                        # ASTweave.py instead)
                        # elif isinstance(inst, WeaveIRupdate):
                        #     for opIndex, op in enumerate(inst.getInOps()):
                        #         if isinstance(op, WeaveIRimmediate):
                        #             debugMsg(10, f"Found immediate {inst.to_string(0)}")
                        #             immediate, insertedInstructions = cls.__splitImmediate(op, inst, originalInsts,
                        #                                                                    index)
                        #             inst.getInOps()[opIndex] = immediate


class unusedInstrRemoval(WeaveIRopt):
    @classmethod
    def getOptName(cls):
        return "unusedInstrRemoval"

    @classmethod
    def apply(cls, program: WeaveIRmodule):
        debugMsg(10, "OPT: Starting unused declaration removal")
        for thr in program.getThreads():
            for event in thr.getEvents():
                for bb in event.getBasicBlocks():
                    originalInsts = bb.getInstructions()
                    # Go through the list from bottom up since we might insert instructions and do not want to mess
                    # up the indices.
                    for index, inst in reversed(list(enumerate(originalInsts))):
                        if isinstance(inst, WeaveIRbinaryOps) or isinstance(inst, WeaveIRmemory):
                            returnReg = inst.getReturnReg()

                            if returnReg is None:
                                continue

                            # Get all instruction in the current scope and check, if the return register is an input
                            # operand for any of the instructions.
                            uses = inst.ctx_scope.getUses(returnReg)

                            if len(uses) == 0:
                                debugMsg(10, f"Removing unused operation {inst.to_string(0)}")
                                originalInsts.pop(index)


class faddFmulMerging(WeaveIRopt):
    @classmethod
    def getOptName(cls):
        return "faddFmulMerging"

    @classmethod
    def apply(cls, program: WeaveIRmodule):
        debugMsg(10, "OPT: Starting fadd and fmul merging")
        for thr in program.getThreads():
            for event in thr.getEvents():
                for bb in event.getBasicBlocks():
                    originalInsts = bb.getInstructions()
                    previousInstruction = None
                    for inum, inst in enumerate(reversed(originalInsts)):
                        if isinstance(inst, WeaveIRarith):
                            if previousInstruction is None:
                                # The fmadd instruction computes Xd = Xs * Xt + Xd. Therefore, we can only merge
                                # instructions, if the summand is already in Xd, which also serves as the destination
                                # register. Therefore, the fadd needs to be Xd = Xs + Xd or double0 = double1 + double0.
                                if (
                                        inst.instType == WeaveIRarithTypes.FADDITION and
                                        isinstance(inst.left, WeaveIRregister) and
                                        isinstance(inst.right, WeaveIRregister) and
                                        (inst.getReturnReg() == inst.left or inst.getReturnReg() == inst.right
                                )):
                                    previousInstruction = inst
                            elif inst.instType == WeaveIRarithTypes.FMULT:
                                # We have an add and a mul instruction. Check, if the one of the inputs for the fmul is
                                # the sum of the previous fadd. Otherwise, we have to unrelated instructions and hence
                                # cannot merge.
                                if (
                                        inst.getReturnReg() == previousInstruction.left or
                                        inst.getReturnReg() == previousInstruction.right
                                ):
                                    debugMsg(10, f"Merging {previousInstruction.to_string(0)} and "
                                                 f"{inst.to_string(0)}")
                                    inst.setOpType(WeaveIRarithTypes.FMULTADD)
                                    inst.setRetOp(previousInstruction.getReturnReg())
                                    originalInsts.remove(previousInstruction)
                                    previousInstruction = None
                            else:
                                previousInstruction = None
                        else:
                            previousInstruction = None


class branchJumpMerging(WeaveIRopt):
    """
    Merges a conditional jump instruction, if the BB that the instruction skips, contains only an uncoditional jump
    instruction. This is the case, if e.g. in a loop an if body only contains "break" or "continue". For instance,

    ```c
    for (int i = 0; i < 10; i++) {
        if (i == 5) {
            break;
        }
    }
    ```
    In this case, the branch instruction skipping the if branch if i != 5 can be merged with the branch instruction
    created by the break statement.
    """
    @classmethod
    def getOptName(cls):
        return "branchJumpMerging"

    @classmethod
    def apply(cls, program: WeaveIRmodule):
        debugMsg(10, "OPT: Starting branch and jump instruction merging")
        for thr in program.getThreads():
            for event in thr.getEvents():
                for bnum, bb in enumerate(event.getBasicBlocks()):
                    originalInsts = bb.getInstructions()
                    for inum, inst in enumerate(reversed(originalInsts)):
                        if isinstance(inst, WeaveIRbranch):
                            for outEdge in bb.out_edges:
                                if (
                                        outEdge != inst.getDestBlock() and
                                        len(outEdge.getInstructions()) == 1 and
                                        isinstance(outEdge.getInstructions()[0], WeaveIRbranch) and
                                        outEdge.getInstructions()[0].instType == WeaveIRBranchTypes.UNCONDITIONAL
                                ):
                                    unCondJumpInstruction = outEdge.getInstructions()[0]

                                    # Remove the incoming edge from the BB holding the unconditional jump instruction
                                    # from the BB that the jump wants to jump to
                                    unCondJumpTargetBB = unCondJumpInstruction.getDestBlock()
                                    unCondJumpTargetBB.removeInEdge(outEdge)
                                    outEdge.resetOutEdges()

                                    # remove the unconditional jump instruction
                                    outEdge.instructions.clear()

                                    # replace the unconditional jump target with the current branch instruction target
                                    inst.changeDestBlock(unCondJumpTargetBB)

                                    # negate the condition of the conditional branch
                                    inst.instType = inst.instType.negateCondition()
                                    break


class removeUnusedVariables(WeaveIRopt):
    """
    Removes variables that have been declared but never been used.
    """
    @classmethod
    def getOptName(cls):
        return "removeUnusedVariables"

    @classmethod
    def _checkDeclarations(cls, scope: WeaveIRscope):
        """
        Walks through all declarations and checks, if they are used anywhere within the scope.
        """
        decls = scope.getDeclarations()
        for decl in decls:
            if isinstance(decl, WeaveIRParamDecl):
                # WeaveIRParamDecl are read-only.
                if not decl.isRead:
                    warningMsg(f"Detected unused event parameter declaration {decl.name} ({decl.getFileLocation()})")
                    scope.removeDeclaration(decl)
            elif isinstance(decl, WeaveIRDecl):
                if not decl.isRead and not decl.isWritten:
                    warningMsg(f"Detected unused declaration {decl.name} ({decl.getFileLocation()})")
                    scope.removeDeclaration(decl)
                elif not decl.isRead and decl.isWritten:
                    warningMsg(f"Declaration {decl.name} ({decl.getFileLocation()}) is written but never read. "
                               f"Consider to remove the declaration")
                    scope.removeDeclaration(decl)
                elif decl.isRead and not decl.isWritten:
                    warningMsg(f"Declaration {decl.name} ({decl.getFileLocation()}) is read but never written, may "
                               f"be uninitialized")

    @classmethod
    def _findScope(cls, scope: WeaveIRscope):
        cls._checkDeclarations(scope)
        for child in scope.getChildren():
            cls._findScope(child)

    @classmethod
    def apply(cls, program: WeaveIRmodule):
        debugMsg(10, "OPT: Starting unused variables removal")
        for section in program.getSections():
            if isinstance(section, WeaveIRscope):
                cls._findScope(section)



