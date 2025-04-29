/*
 * Copyright (c) 2021 University of Chicago and Argonne National Laboratory
 * All rights reserved.
 *
 * Redistribution and use in source and binary forms, with or without
 * modification, are permitted provided that the following conditions are
 * met: redistributions of source code must retain the above copyright
 * notice, this list of conditions and the following disclaimer;
 * redistributions in binary form must reproduce the above copyright
 * notice, this list of conditions and the following disclaimer in the
 * documentation and/or other materials provided with the distribution;
 * neither the name of the copyright holders nor the names of its
 * contributors may be used to endorse or promote products derived from
 * this software without specific prior written permission.
 *
 * THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
 * "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
 * LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
 * A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
 * OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
 * SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
 * LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
 * DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
 * THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
 * (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
 * OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
 *
 * Author - Jose M Monsalve Diaz
 * Author - Andronicus
 *
 */

#ifndef UPDOWNBASIM_H
#define UPDOWNBASIM_H
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <map>
#include <new>
#include <string>
#include <utility>
#include <vector>
#include <filesystem>
#include <chrono>

#include "debug.h"
#include "basim_stats.hh"
#include "udaccelerator.hh"
#include "updown.h"
#include "simupdown.h"
#include "lanetypes.hh"
#include "types.hh"
#define NUMTICKS 100

#ifndef UPDOWN_INSTALL_DIR
#define UPDOWN_INSTALL_DIR "."
#endif

#ifndef UPDOWN_SOURCE_DIR
#define UPDOWN_SOURCE_DIR "."
#endif

namespace UpDown {

/*
  This is a hack as it is possible to have multiple instances of the runtime,
  but only one global logger is allowed. We need to know we are logging from
  which runtime instance.
*/
class BASimUDRuntime_t;
extern BASimUDRuntime_t *curRuntimeInstance;

/**
 * @brief Wrapper class that allows simulation of runtime calls using BASIM 
 *
 * This class inherits from UDRuntime_t, and it overwrites the methods
 * such that they can be simulated using a memory region.
 *
 * This class does not use polymorphism. It just oversubscribes the
 * methods, wrapping the original implementation of the runtime
 *
 * @todo This does not emulate multiple UPDs
 *
 */

class BASimUDRuntime_t : public SimUDRuntime_t {
private:
  // Numticks controls no of ticks a lane will execute before moving on
  uint32_t NumTicks;
  uint64_t globalTick;

  // BAsim's Accelerators
  std::vector<basim::UDAcceleratorPtr> uds;
  std::vector<std::vector<struct BASimStats>> simStats;

  // Num outstanding sends 
  //std::vector<uint32_t> outstanding_sends;
  // Map of EventLabels and Symbols
  std::unordered_map<uint32_t, uint32_t> symbolMap;

  std::chrono::high_resolution_clock::time_point startTime;

  /**
   * @brief Initialize the BASIM accelerators and load program
   * 
   * @param progfile 
   * @param _pgbase 
   * 
   * @todo Add the program binary creation to this function or should
   * it be a separate function?
   */

  void initMachine(std::string progfile, basim::Addr _pgbase);

  /**
   * @brief Initialize the BASIM logging
   * 
   * @param log_folder_path
   * 
   */

  void initLogs(std::filesystem::path log_folder_path);

  /**
   * @brief Initialize OpenMP
   */
  void initOMP();

  /**
   * @brief Post Simulation interface to the Accelerators
   *
   * @todo when increasing the number of lanes to multiple UpDowns, this
   * function must be re-implemented
   */
  void postSimulate(uint32_t udid, uint32_t laneID);

  /**
   * @brief Extract event label symbols from the compiled UpDown binary
   * 
   * @param progfile - .bin file
   */
  void extractSymbols(std::string progfile);

  /**
   * @brief Return the global UD Index for the given network ID
   * 
   * @return uint32_t 
   */
  int getUDIdx(basim::networkid_t, ud_machine_t);
  
  int getUDForAddr(basim::networkid_t, ud_machine_t, basim::Addr);

  /**
   * @brief Send event operands from the sender queues to the receiver lane.
   * @param eops A pointer to the event operands
   * @param sourceUDID ID of the sending UD
   * @param targetLaneID ID of the receiving lane ID
   */
   void sendEventOperands(int sourceUDID, basim::eventoperands_t *eops, uint32_t targetLaneID);

public:
  /**
   * @brief Construct a new BASimUDRuntime_t object
   *
   * This constructor calls initMemoryArrays() to set the simulated memory
   * regions. Python will be disabled. Only simulating memory interactions.
   *
   */
  BASimUDRuntime_t() : SimUDRuntime_t() {
    UPDOWN_INFOMSG("Initializing BASimulated Runtime with default params");
    UPDOWN_WARNING("No python program. Python will be disabled, only "
                   "simulating memory interactions");
    UPDOWN_INFOMSG("Adding stats for %lu UDs", this->MachineConfig.NumUDs);

    for (int i = 0;
         i < this->MachineConfig.NumUDs * this->MachineConfig.NumStacks *
                 this->MachineConfig.NumNodes;
         i++) {
      std::vector<struct BASimStats> v(this->MachineConfig.NumLanes);
      this->simStats.push_back(v);
    }
    python_enabled = false;
    this->startTime = std::chrono::high_resolution_clock::now();
    UpDown::curRuntimeInstance = this;
  }

  /**
   * @brief Construct a new BASimUDRuntime_t object
   *
   * This constructor calls initMemoryArrays() to set the simulated memory
   * regions. The pointers of ud_machine_t.MappedMemBase, ud_machine_t.UDbase
   * ud_machine_t.SPMemBase and ud_machine_t.ControlBase will be ignored and
   * overwritten in order to simulate the runtime.
   *
   * @param machineConfig Machine configuration
   */
  BASimUDRuntime_t(ud_machine_t machineConfig)
      : SimUDRuntime_t(machineConfig){
    UPDOWN_INFOMSG("Initializing runtime with custom machineConfig");
    UPDOWN_WARNING("No python program. Python will be disabled, only "
                   "simulating memory interactions");
    UPDOWN_INFOMSG("Adding stats for %lu UDs", this->MachineConfig.NumUDs);
    for (int i = 0;
         i < this->MachineConfig.NumUDs * this->MachineConfig.NumStacks *
                 this->MachineConfig.NumNodes;
         i++) {
      std::vector<struct BASimStats> v(this->MachineConfig.NumLanes);
      this->simStats.push_back(v);
    }
    python_enabled = false;
    init_stats();
    this->startTime = std::chrono::high_resolution_clock::now();
    UpDown::curRuntimeInstance = this;
    initOMP();
  }

  /**
   * @brief Construct a new BASimUDRuntime_t object
   *
   * This constructor calls initMemoryArrays() to set the simulated memory
   * regions. The pointers of ud_machine_t.MappedMemBase, ud_machine_t.UDbase
   * ud_machine_t.SPMemBase and ud_machine_t.ControlBase will be ignored and
   * overwritten.
   *
   * @param machineConfig Machine configuration
   */
  BASimUDRuntime_t(ud_machine_t machineConfig, std::string programFile,
                 std::string programName, basim::Addr pgbase, uint32_t numTicks=NUMTICKS)
      : SimUDRuntime_t(machineConfig ,programFile, programName), NumTicks(numTicks)
        {
    UPDOWN_INFOMSG("Initializing runtime with custom machineConfig");
    UPDOWN_INFOMSG("Adding stats for %lu UDs", this->MachineConfig.NumUDs);
    for (int i = 0;
         i < this->MachineConfig.NumUDs * this->MachineConfig.NumStacks *
                 this->MachineConfig.NumNodes;
         i++) {
      std::vector<struct BASimStats> v(this->MachineConfig.NumLanes);
      this->simStats.push_back(v);
    }
    UPDOWN_INFOMSG("Running file %s Program %s", programFile.c_str(),
                   programName.c_str());
    // Recalculate address map
    python_enabled = false;
    initMachine(programFile, pgbase);
    calc_addrmap();
    init_stats();
    this->startTime = std::chrono::high_resolution_clock::now();
    UpDown::curRuntimeInstance = this;
    initLogs(std::filesystem::path(programFile + ".logs").filename());
    initOMP();
  }


  
  BASimUDRuntime_t(ud_machine_t machineConfig, std::string programFile, basim::Addr pgbase, 
                  uint32_t numTicks=NUMTICKS)
      : SimUDRuntime_t(machineConfig ,programFile), NumTicks(numTicks)
        {
    UPDOWN_INFOMSG("Initializing runtime with custom machineConfig");
    UPDOWN_INFOMSG("Adding stats for %lu UDs", this->MachineConfig.NumUDs);
    for (int i = 0;
         i < this->MachineConfig.NumUDs * this->MachineConfig.NumStacks *
                 this->MachineConfig.NumNodes;
         i++) {
      std::vector<struct BASimStats> v(this->MachineConfig.NumLanes);
      this->simStats.push_back(v);
    }
    UPDOWN_INFOMSG("Running file %s Program %s", programFile.c_str(),
                   programName.c_str());
    // Recalculate address map
    python_enabled = false;
    initMachine(programFile, pgbase);
    calc_addrmap();
    init_stats();
    this->startTime = std::chrono::high_resolution_clock::now();
    UpDown::curRuntimeInstance = this;
    initLogs(std::filesystem::path(programFile + ".logs").filename());
    initOMP();
  }

  /**
   * @brief Wrapper function for send_event
   *
   * Calls the emulator and calls the UDRuntime_t::send_event() function
   */
  void send_event(event_t ev) override;

  /**
   * @brief Wrapper function for start_exec
   *
   * Calls the emulator and calls the UDRuntime_t::start_exec() function
   */
  void start_exec(networkid_t nwid) override;

  /**
   * @brief Wrapper function for t2ud_memcpy
   *
   * Calls the emulator and calls the UDRuntime_t::t2ud_memcpy() function
   *
   * @todo The physical memory is contiguous, therefore the calculation of this
   * offset is different to the address space in the virtual memory. Is there
   * a way to express this? The runtime is doing some heavy lifting here that
   * is translating things to physical memory
   */
  void t2ud_memcpy(void *data, uint64_t size, networkid_t nwid,
                   uint32_t offset) override;

  /**
   * @brief Wrapper function for ud2t_memcpy
   *
   * Calls the emulator and calls the UDRuntime_t::ud2t_memcpy() function
   *
   * This function copies from the emulator directly into the scratchpad memory
   * and then calls the real runtime function. This allows to keep the logic of
   * the real runtime even though we are simulating the hardware
   *
   * @todo The physical memory is contiguous, therefore the calculation of this
   * offset is different to the address space in the virtual memory. Is there
   * a way to express this? The runtime is doing some heavy lifting here that
   * is translating things to physical memory
   */
  void ud2t_memcpy(void *data, uint64_t size, networkid_t nwid,
                   uint32_t offset) override;

  /**
   * @brief Wrapper function for test_addr
   *
   * Calls the emulator and calls the UDRuntime_t::test_addr() function
   *
   * @todo The physical memory is contiguous, therefore the calculation of this
   * offset is different to the address space in the virtual memory. Is there
   * a way to express this? The runtime is doing some heavy lifting here that
   * is translating things to physical memory
   */
  bool test_addr(networkid_t nwid, uint32_t offset,
                 word_t expected = 1) override;

  /**
   * @brief Wrapper function for test_wait_addr
   *
   * Calls the emulator and calls the UDRuntime_t::test_wait_addr() function
   *
   * @todo The physical memory is contiguous, therefore the calculation of this
   * offset is different to the address space in the virtual memory. Is there
   * a way to express this? The runtime is doing some heavy lifting here that
   * is translating things to physical memory
   */
  void test_wait_addr(networkid_t nwid, uint32_t offset,
                      word_t expected = 1) override;

  /**
   * @brief Function to dump the memory into a file
   * @param filename file to be dumped into
   * @param vaddr Start vaddr
   * @param size size of memory to be dumped
  */
  void dumpMemory(const char* filename, void *vaddr, uint64_t size) override;

  /**
   * @brief Function to load memory from a file
   * @param filename file to be dumped into
   * @param vaddr Start vaddr
   * @param size size of memory to be dumped
   * @return std::pair<void *, uint64_t> pointer to the memory and size
  */
  std::pair<void *, uint64_t> loadMemory(const char* filename, void *vaddr = nullptr, uint64_t size = 0) override;

    /**
   * @brief Function to dump the memory into a file
   * @param vaddr Start vaddr
   * @param size size of memory to be dumped
   * @param filename file to be dumped into
  */
  void dumpLocalMemory(const char* filename, networkid_t start_nwid = networkid_t(), uint64_t num_lanes = 0) override;

  /**
   * @brief Function to load memory from a file
   * @param vaddr Start vaddr
   * @param size size of memory to be dumped
   * @param filename file to be dumped into
   * @return std::pair<networkid_t, uint64_t> load networkid and number of lanes
  */
  std::pair<networkid_t, uint64_t> loadLocalMemory(const char* filename, networkid_t start_nwid = networkid_t(), uint64_t num_lanes = 0) override;


  uint64_t getCurTick(){
    return globalTick;
  }

  std::chrono::high_resolution_clock::time_point getStartTime(){
    return startTime;
  }

  ~BASimUDRuntime_t();

  // Reset stats for all UDs
  void reset_stats();
  // Reset stats for a specific UDs
  void reset_stats(uint32_t lane_num);
  // Reset stats for a specific lane
  void reset_stats(uint32_t ud_id, uint8_t lane_num);

  // Update stats (copy from basim into runtime) for a specific lane
  void update_stats(uint32_t lane_num);
  void update_stats(uint32_t ud_id,
                    uint8_t lane_num);
  
  // Get stats for a specific lane
  struct BASimStats& get_stats(uint32_t lane_num);
  struct BASimStats& get_stats(uint32_t ud_id, uint8_t lane_num);

#ifdef DETAIL_STATS
  void print_histograms(uint32_t ud_id, uint8_t lane_num);
  void print_histograms(uint32_t nwid);
#endif

  void print_stats(uint32_t ud_id, uint8_t lane_num);
  void print_stats(uint32_t lane_num);
};

} // namespace UpDown

#endif
