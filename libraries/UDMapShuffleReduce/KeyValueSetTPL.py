from typing import Tuple
from EFA_v2 import *
from abc import ABCMeta
from abc import abstractmethod
from enum import Enum

class KeyValueSetTemplate(metaclass=ABCMeta):

    class AvailableExtensions(Enum):
        original = 0
        load_balancer = 1
        lb_test = 2
    
    def __init__(self, name: str, key_size: int, value_size: int, extension = AvailableExtensions.original):

        self.extension = extension

        self.name = name
        self.key_size = key_size
        self.value_size = value_size
        self.pair_size = key_size + value_size
        self.meta_data_size = 0
        print(f"{self.name} kvset: key size = {key_size}, value size = {value_size}, pair size = {self.pair_size}")

        
    
    '''
    size: size of the metadata in words
    offset: offset of the metadata in bytes
    '''
    def set_meta_data(self, size: int, offset: int):
        self.meta_data_size = size
        self.meta_data_offset = offset
        print(f"{self.name} kvset: metadata size = {size}, offset = {offset}")
    
    def store(self, tran: Transition, lm_reg: str, kv_regs: list, kv_set_ptr: str, temp_regs: list, ob_offset: int, ret_lable: str):
        tran.writeAction(f"muli {kv_regs[0]} {temp_regs[0]} {self.pair_size*8}")
        tran.writeAction(f"add {lm_reg} {temp_regs[0]} {temp_regs[0]}")
        tran.writeAction(f"addi {lm_reg} {temp_regs[1]} {ob_offset}")
        for i in range(self.pair_size):
            tran.writeAction(f"movrl {kv_regs[i]} {i*8}({temp_regs[1]}) 0 8")
        tran.writeAction(f"send_dmlm_wret {kv_set_ptr} {ret_lable} {temp_regs[1]} {self.pair_size}")

        return

    # For load balancer
    # Called by the global master thread
    def get_n_pairs(self, tran: Transition, n: int, curr_pair: str, regs: list):
        pass


    @abstractmethod
    def get_next_pair(self, tran: Transition, curr_pair: str, regs: list) -> Tuple[Transition, str]:
        pass
    
    @abstractmethod
    def get_pair(self, tran: Transition, key: str, addr_reg: str, regs: list) -> Transition:
        pass
    
    @abstractmethod
    def generate_partitions(self, tran: Transition, num_partitions: int, part_arry_base: str):
        pass