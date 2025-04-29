/**
**********************************************************************************************************************************************************************************************************************************
* @file:	translation_memory.hh
* @author:	
* @date:	
* @brief:   Translation Memory for UpDown
**********************************************************************************************************************************************************************************************************************************
**/
#ifndef __TRANSLATION_MEMORY__H__
#define __TRANSLATION_MEMORY__H__
#include <cmath>
#include <cstdint>
#include <iostream>
#include <unordered_map>
#include "../../../common/include/memorySegments.h"
#include "lanetypes.hh"

namespace basim
{

class TranslationMemory
{
private:
    /* Translation tables for private and global segments */
    std::vector<private_segment_t> private_segments;
    std::vector<global_segment_t> global_segments;

    // Private UD details
    uint32_t udid;
    int num_uds;
    uint64_t nwid_range;
    bool enable_translation;
    Addr scratchpad_base;

public:
    // Empty constructor useful for single UD experiments
    TranslationMemory(): udid(0), num_uds(1), scratchpad_base(0), enable_translation(false) {};
    
    TranslationMemory(uint32_t _udid, int _num_uds, Addr _spbase): udid(_udid), num_uds(_num_uds), nwid_range(_num_uds*64), scratchpad_base(_spbase), enable_translation(false) {};

    /**
     * @brief Insert a local translation
     * 
     */
    void insertLocalTrans(private_segment_t ps){
        enable_translation = true;
        private_segments.push_back(ps);
    }

    /**
     * @brief Construct and insert a local translation entry
     * 
     */
    void insertLocalTrans(uint64_t virtual_base, uint64_t physical_base, uint64_t size, uint8_t permission);

    /**
     * @brief Insert a global translation
     * 
     */
    
    void insertGlobalTrans(global_segment_t gs){
        enable_translation = true;
        global_segments.emplace_back(gs);
    }

    /**
     * @brief Construct and insert a global translation entry
     * 
     */
    
    void insertGlobalTrans(uint64_t virtual_base, uint64_t physical_base, uint64_t size, uint64_t swizzle_mask, uint8_t permission);

    /**
     * @brief Validate and translate DRAM Address 
     * 
     */
    Addr translate(Addr addr, int num_words);
    
    /**
     * @brief Validate Scratchpad Address
     * 
     */
    bool validate_sp_addr(Addr addr, int num_bytes);

    /**
     * @brief Validate network id
     * 
     */
    bool validate_nwid(networkid_t nwid);
};


typedef TranslationMemory* TranslationMemoryPtr;
    
}//basim

#endif  //!__TRANSLATION_MEMORY__H__

