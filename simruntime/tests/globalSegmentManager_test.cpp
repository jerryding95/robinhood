#include "globalSegmentManager.hh"
#include "memorySegments.h"

using namespace UpDown;

#define B 10 // 1024 nodes
#define C 10 // 1024 bytes per block
#define P 10 // 10 bits padding (Unchanged upper bits of virtual Addr)
#define F 64 - B - C - P // 34 bits filling

#define VIRTUAL_SIZE (1ULL << (B + C)) * 2 // 2 blocks per node

#define BASE_NODE 0
#define NODE_BASE_OFFSET 0

int main() {

  GSM::global_segment_manager_t *gsm = new GSM::global_segment_manager_t();

  swizzle_mask_t swizzle_mask(P, /*P = Padding*/
                                   F, /*F = Filling*/
                                   B, /*B = 2^B number of nodes*/
                                   C  /*C = 2^C size of block*/
  );
  physical_addr_t physical_addr(BASE_NODE, NODE_BASE_OFFSET);
  // Test creating a new segment
  gsm->createSegment(0,             /*virtual_base*/
                     VIRTUAL_SIZE,  /*virtual_limit*/
                     swizzle_mask,  /*swizzle_mask*/
                     physical_addr, /*pyhisical_base*/
                     0              /*accesss_flags*/
  );

  // Check first address in the virutal address space matches the node base
  UPDOWN_ERROR_IF(gsm->getPhysicalAddr(0) != physical_addr,
                  "Error in getPhysicalAddr for first address 0x0");

  // Check an address within the first block (We use the middle of the block)
  UPDOWN_ERROR_IF(
      gsm->getPhysicalAddr(1ULL << (C - 1)) !=
          physical_addr + physical_addr_t(BASE_NODE, 1ULL << (C - 1)),
      "Error in getPhysicalAddr for first block 0x%llX", 1ULL << (C - 1));

  // Check the address of the second block. First address of the second node
  // Skip the first block, and get the middle of the second block
  UPDOWN_ERROR_IF(
      gsm->getPhysicalAddr((1ULL << C)) !=
          physical_addr + physical_addr_t(BASE_NODE + 1, 0),
      "Error in getPhysicalAddr for first address of second node 0x%llX",
      (1ULL << C));

  // Check an address within the first block of the second node.
  // Skip the first block, and get the middle of the second block
  UPDOWN_ERROR_IF(gsm->getPhysicalAddr((1ULL << C) + (1ULL << (C - 1))) !=
                      physical_addr + physical_addr_t(BASE_NODE + 1,
                                                           (1ULL << (C - 1))),
                  "Error in getPhysicalAddr for address within first block of "
                  "second node 0x%llX",
                  (1ULL << C) + (1ULL << (C - 1)));

  // Check an address within the second block of the first node.
  UPDOWN_ERROR_IF(gsm->getPhysicalAddr(1ULL << (B + C)) !=
                      physical_addr +
                          physical_addr_t(BASE_NODE, 1ULL << C),
                  "Error in getPhysicalAddr for address within second block of "
                  "first node 0x%llX",
                  1ULL << (B + C));

  // Check an address within the second block of the second node.
  UPDOWN_ERROR_IF(gsm->getPhysicalAddr((1ULL << (B + C)) + (1ULL << (C))) !=
                      physical_addr +
                          physical_addr_t(BASE_NODE + 1, 1ULL << C),
                  "Error in getPhysicalAddr for address within second block of "
                  "second node 0x%llX",
                  (1ULL << (B + C)) + (1ULL << (C)));

  return 0;
}