/**
**********************************************************************************************************************************************************************************************************************************
* @file:	udaccelerator.hh
* @author:	Andronicus
* @date:
* @brief:   Accelerator Definition
**********************************************************************************************************************************************************************************************************************************
**/
#ifndef __UDACCELERATOR__H__
#define __UDACCELERATOR__H__
#include "lanetypes.hh"
#include "logging.hh"
#include "stats.hh"
#include "translationmemory.hh"
#include "types.hh"
#include "udlane.hh"
#include <cstdint>
#include <iostream>

namespace basim {

class UDAccelerator : public TickObject {
private:
  /* NetworkID down to UDID (laneIDs are masked)*/
  uint32_t udid;

  /* Num of Lanes */
  int numLanes;

  /* ScratchPad Base and size */
  Addr scratchpadBase;
  uint64_t scratchpadSize;
  int lmMode;

  /* Full scratchpad Interface*/
  ScratchPadPtr spd;

  /* lanes */
  std::vector<UDLanePtr> udLanes;

  /* Stats */
  UDStats *udstats;

  // Translation table
  TranslationMemoryPtr transmem;


  // Instruction memory
  InstructionMemoryPtr instmem;

  // Simulation stuff
  uint64_t curTimeStamp;

public:
  /* Null Constructor */
  UDAccelerator() : udid(0), numLanes(0), scratchpadBase(0), scratchpadSize(0), lmMode(0){};

  /* Accelerator Constructor with lanes, addresses */
  UDAccelerator(int numlanes, uint32_t udid, int lmMode = 1);

  /* Initialize Accelerator  */
  void initSetup(Addr _pgbase, std::string progfile, Addr _lmbase);

  /* Initialize Accelerator  */
  void initSetup(Addr _pgbase, std::string progfile, Addr _lmbase, int _num_uds);

  /* get Accelerator Size */
  size_t getEventQSize(int laneid);

  /* Idle Check */
  bool isIdle();

  /* Idle Check */
  bool isIdle(uint32_t laneID);

  /* push Event + Operands */
  bool pushEventOperands(eventoperands_t eop, uint32_t laneid);

  /* Write Scratch Pad */
  void writeScratchPad(int size, Addr addr, uint8_t *data);

  /* read data from the scratchpad */
  // word_t readScratchPad(Addr addr);
  void readScratchPad(int size, Addr addr, uint8_t *data);

  ///* Pointer to all scratchpad data */
  void readScratchPadBank(uint8_t laneid, uint8_t* data);
  void readAllScratchPad(uint8_t* data);

  ///* Pointer to all scratchpad data */
  void writeScratchPadBank(uint8_t laneid, const uint8_t* data);
  void writeAllScratchPad(const uint8_t* data);

  // Check if send message is available
  bool sendReady(uint32_t laneid);

  // Read the SendMessage from buffer
  // MMessagePtr getSendMessage(int laneid);
  std::unique_ptr<MMessage> getSendMessage(int laneid);

  // Remove the message
  void removeSendMessage(int laneid);

  /* Tick for Accelerator */
  void tick(uint64_t timestamp) override;

  /* simulate API for accelerator runs through all lanes */
  void simulate(uint64_t numTicks, uint64_t timestamp = 0);

  /* Simulate API to call per lane */
  void simulate(uint32_t laneID, uint64_t numTicks, uint64_t timestamp = 0);

  /* testing api returns value from register of whatever thread is currently active */
  bool testReg(int laneID, RegId raddr, word_t val) { return (udLanes[laneID]->testReg(raddr, val)); }

  /* testing api returns value from scratchpad memory */
  bool testMem(Addr memaddr, word_t val) { return (spd->readWord(memaddr) == val); }

  const LaneStats *getLaneStats(int laneid) { return udLanes[laneid]->getLaneStats(); }
  
  void resetStats(int laneid) { udLanes[laneid]->resetStats(); }
  
  void resetStats(void);

  const UDStats *getUDStats() { return udstats; }

  ScratchPadPtr getspd() { return spd; }
  word_t readReg(int laneid, RegId raddr) {
    word_t val = udLanes[laneid]->readReg(raddr);
    return val;
  }
  void insertLocalTrans(private_segment_t ps) { transmem->insertLocalTrans(ps); }

  int getLanebyPolicy(int laneid, uint8_t policy);

  void insertLocalTrans(uint64_t virtual_base, uint64_t physical_base, uint64_t size, uint8_t permission) {
    transmem->insertLocalTrans(virtual_base, physical_base, size, permission);
  }

  void insertGlobalTrans(global_segment_t gs) { transmem->insertGlobalTrans(gs); }

  void insertGlobalTrans(uint64_t virtual_base, uint64_t physical_base, uint64_t size, uint64_t block_size, uint8_t permission) {
    uint64_t nrC = log2(block_size);
    uint64_t nrB = log2(size/block_size);
    uint64_t nrF = 37 - nrC;
    uint64_t mask = 0 | (uint64_t(pow(2, nrF)) - 1) << (nrC + nrB) |
                    (uint64_t(pow(2, nrC)) - 1);
    transmem->insertGlobalTrans(virtual_base, physical_base, size, mask, permission);
  }

  // Destructor
  ~UDAccelerator();
};

typedef UDAccelerator *UDAcceleratorPtr;

} // namespace basim
#endif //!__EVENTQ__H__
