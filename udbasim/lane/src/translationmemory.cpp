#include "translationmemory.hh"
#include "../../../common/include/memorySegments.h"
#include "types.hh"
#include <cstdio>
#include "debug.hh"
#include <cstdlib>
#include "lanetypes.hh"

namespace basim 
{
    void TranslationMemory::insertLocalTrans(Addr virtual_base, Addr physical_base, uint64_t size, uint8_t permission) {
        BASIM_INFOMSG("Updown %d (nwid between %d and %d) inserts private translation entry {virtual base = %ld(0x%lx), physical base = %ld(0x%lx), size = %ld (%fGB), access permission = %d}", 
                udid, udid << 6, ((udid + 1) << 6) - 1, virtual_base,  virtual_base, 
                physical_base, physical_base, size, size / std::pow(1024, 3), permission);

        enable_translation = true;
        private_segment_t ps = private_segment_t(virtual_base, virtual_base + size, 
            (int64_t) (physical_base - virtual_base), permission);
        private_segments.emplace_back(ps);
        ps.print_info();
        return;
    }

    void TranslationMemory::insertGlobalTrans(Addr virtual_base, Addr physical_base, uint64_t size, uint64_t swizzle_mask, uint8_t permission) {
        BASIM_INFOMSG("Updown %d (nwid between %d and %d) inserts global translation entry {virtual base = %ld(0x%lx), physical base = %ld(0x%lx), size = %ld (%fGB), swizzle mask = %ld, access permission = %d}", 
                udid, udid << 6, ((udid + 1) << 6) - 1, virtual_base,  virtual_base, 
                physical_base, physical_base, size, size / std::pow(1024, 3), swizzle_mask, permission);
                
        enable_translation = true;
        global_segment_t gs = global_segment_t(virtual_base, virtual_base + size, swizzle_mask_t(swizzle_mask),
            physical_addr_t(physical_base), permission);
        global_segments.emplace_back(gs);
        gs.print_info();
        return;
    }

    Addr TranslationMemory::translate(Addr addr, int num_words) {
        BASIM_INFOMSG("Validating DRAM address on updown %d: %lu(0x%lx) length: %d", udid, addr, addr, num_words);
        // Direct mapping if no translation entry is added
        if (!enable_translation) return addr;

        for (auto seg : private_segments) {
            if (seg.contains(addr) && seg.contains(addr + num_words * 8)) {
                seg.print_info();
                Addr pa = seg.getPhysicalAddr(addr);
                BASIM_INFOMSG("Translate DRAM address %lu(0x%lx) -> %lu(0x%lx)", addr, addr, pa, pa);
                // return pa;
                return addr; // Translation on UpDown is disabled, use top's translation for now.
            } 
        }

        for (auto seg : global_segments) {
            if (seg.contains(addr) && seg.contains(addr + num_words * 8)) {
                seg.print_info();
                Addr pa = seg.getPhysicalAddr(addr).getPhysicalAddress();
                BASIM_INFOMSG("Translate DRAM address %lu(0x%lx) -> %lu(0x%lx)", addr, addr, pa, pa);
                // return pa;
                return addr; // Translation on UpDown is disabled, use top's translation for now.
            }
        }
        // BASIM_ERROR("Could not translate address: %lu(0x%lx)\n", addr, addr);
        // BASIM_ERROR("Translation entry is not found in updown %d", udid);
        return 0;
        // exit(1);
    }

    bool TranslationMemory::validate_sp_addr(Addr addr, int num_bytes) {
        BASIM_INFOMSG("Validating scratchpad address on updown %d: addr = %lu(0x%lx), num_bytes = %d", udid, addr, addr, num_bytes);
        // BASIM_PRINT("Validating scratchpad address on updown %d: addr = %lu(0x%lx), num_bytes = %d", udid, addr, addr, num_bytes);
        if ((addr >= scratchpad_base) && ((addr + num_bytes) <= scratchpad_base + SCRATCHPAD_SIZE)) {
            return true;
        }
        // BASIM_ERROR("Address: %lu(0x%lx) is not in the updown %d's scratchpad (base = %lu(0x%lx)\n", addr, addr, udid, scratchpad_base, scratchpad_base);
        return false;
    }

    bool TranslationMemory::validate_nwid(networkid_t nwid) {
        BASIM_INFOMSG("Validating message network id %u  on updown %d, nwid range=[0:%d]", (nwid.networkid & 0x7FFFFFF), udid, (num_uds * 64) - 1);
        uint32_t netid = (nwid.networkid & 0x7FFFFFF);
        if((netid < nwid_range) && (netid >= 0)){
            return true;
        }
        // BASIM_ERROR("NWID:%u is invalid message destination.", nwid.networkid);
        // BASIM_ERROR("Only support %d updown accelerators, nwid [0:%d]", num_uds, (num_uds * 64) - 1);
        return false;
    }
}