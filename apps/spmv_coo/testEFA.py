from EFA_v2 import EFA, State, Transition
from linker.EFAProgram import efaProgram, EFAProgram

from libraries.UDMapShuffleReduce.linkable.LinkableKVMapShuffleReduceTPL import UDKeyValueMapShuffleReduceTemplate
from libraries.UDMapShuffleReduce.utils.OneDimArrayKeyValueSet import OneDimKeyValueSet
from libraries.UDMapShuffleReduce.utils.IntermediateKeyValueSet import IntermediateKeyValueSet
from libraries.LMStaticMaps.LMStaticMap import *
from libraries.UDMapShuffleReduce.KVMSRMachineConfig import *

def testEFA():
	efa = EFA([])
	return efa