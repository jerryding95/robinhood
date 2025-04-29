#include "basimupdown.h"
#include "debug.h"
#include "memorySegments.h"
#include "networkid.h"
#include "basim_stats.hh"
#include <cstddef>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <fcntl.h>
#include <ios>
#include <string>
#include <sys/mman.h>
#include <utility>
#include <vector>
#include <omp.h>
#include "types.hh"
#include "lanetypes.hh"
#include "fstream"
#include "logging.hh"
#include "updown_config.h"
#include "util.hh"

namespace UpDown {

/*
  This is a hack as it is possible to have multiple instances of the runtime,
  but only one global logger is allowed. We need to know we are logging from
  which runtime instance.
*/
BASimUDRuntime_t *curRuntimeInstance = nullptr;

void BASimUDRuntime_t::extractSymbols(std::string progfile){
  std::ifstream instream(progfile.c_str(), std::ifstream::binary);
  uint64_t startofEventSymbols;
  uint32_t numEventSymbols, label, labelAddr;
  if(instream){
    instream.seekg(0, instream.end); 
    int length = instream.tellg();
    UPDOWN_INFOMSG("Program Size: %d Bytes", length);
    instream.seekg(0, instream.beg);
    instream.read(reinterpret_cast<char *>(&startofEventSymbols), sizeof(startofEventSymbols));
    instream.seekg(startofEventSymbols, instream.beg);
    instream.read(reinterpret_cast<char *>(&numEventSymbols), sizeof(numEventSymbols));
    UPDOWN_INFOMSG("Extracting %d EventLabels:Addresses from %s", numEventSymbols, progfile.c_str());
    for(auto i = 0; i < numEventSymbols; i++){
      instream.read(reinterpret_cast<char *>(&label), sizeof(label));
      instream.read(reinterpret_cast<char *>(&labelAddr), sizeof(labelAddr));
      symbolMap[label] = labelAddr; 
      UPDOWN_INFOMSG("%d:%d", label, labelAddr);
    }
    instream.seekg(0, instream.beg);
  }else
    UPDOWN_ERROR("Could not load the binary: %s\n", progfile.c_str());
}

void BASimUDRuntime_t::initMachine(std::string progfile, basim::Addr _pgbase){
  globalTick = 0;
  total_uds = this->MachineConfig.NumNodes * this->MachineConfig.NumStacks * this->MachineConfig.NumUDs;
  uds.reserve(total_uds);

  // Create the default private segment, i.e., the entire memory mapped region
  private_segment_t default_segment(this->MachineConfig.MapMemBase, 
    this->MachineConfig.MapMemBase + this->MachineConfig.MapMemSize, 0, 0b11);

  for (uint32_t node = 0; node < this->MachineConfig.NumNodes; node++) {
    for (uint32_t stack = 0; stack < this->MachineConfig.NumStacks; stack++) {
      for (uint32_t udid = 0; udid < this->MachineConfig.NumUDs; udid++) {
        uint32_t ud_idx = (node * this->MachineConfig.NumStacks + stack) *
                              this->MachineConfig.NumUDs +
                          udid;
        uint32_t nwid = ((node << 11) & 0x07FFF800) | ((stack << 8) & 0x00000700) |
                  ((udid << 6) & 0x000000C0);
        
        basim::UDAcceleratorPtr udptr = new basim::UDAccelerator(MachineConfig.NumLanes, nwid, MachineConfig.LocalMemAddrMode);

        uds.push_back(udptr);

        basim::Addr spBase = this->MachineConfig.SPMemBase + ((node * this->MachineConfig.NumStacks + stack) * this->MachineConfig.NumUDs + udid) * this->MachineConfig.NumLanes * this->MachineConfig.SPBankSize;
        
        //uds[ud_idx]->initSetup(_pgbase, progfile, spBase);
        //basim::TranslationMemoryPtr tm = new basim::TranslationMemory(nwid, total_uds, spBase);
        extractSymbols(progfile);
        uds[ud_idx]->initSetup(_pgbase, progfile, spBase, total_uds);
        // Add the translation for the default private local segment to the UpDown's translation memory
        uds[ud_idx]->insertLocalTrans(default_segment);

        UPDOWN_INFOMSG("Creating UpDown: Node: %d, Stack: %d, UD: %d, nwid: %d ud_idx = %d SPBase: %lx\n", 
        node, stack, udid, nwid, ud_idx, spBase);
      }
    }
  }
  
  // Get UPDOWN_SIM_ITERATIONS from env variable
  if (char *EnvStr = getenv("UPDOWN_SIM_ITERATIONS"))
    max_sim_iterations = std::stoi(EnvStr);
  UPDOWN_INFOMSG("Running with UPDOWN_SIM_ITERATIONS = %ld",
                 max_sim_iterations);

}

void BASimUDRuntime_t::initOMP() {
  #ifndef GEM5_MODE
    // A set environment variable always takes precedence
    if(getenv("OMP_NUM_THREADS"))
      return;

    uint64_t hardwareThreads = omp_get_max_threads();
    int threads = int(hardwareThreads < total_uds ? hardwareThreads : total_uds);
    omp_set_num_threads(threads);

    UPDOWN_INFOMSG("Available hardware threads: %lu, running %d threads in parallel for %u UDs",
                    hardwareThreads, threads, total_uds);
  #endif
}

static void writeUpdownBasimPerflog(uint32_t network_id, uint32_t thread_id, // IDs
                             uint32_t event_label,     // event
                             uint32_t inc_exec_cycles, // incremental exec cycles
                             uint64_t total_exec_cycles, // total exec cycles
                             uint32_t msg_id, std::string &msg_str // message
) {
  // uint64_t final_tick = this->getCurTick() + updown_period * inc_exec_cycles;
  uint64_t final_tick = UpDown::curRuntimeInstance->getCurTick();
  uint64_t sim_ticks = final_tick;
  double sim_sec = 0.0;
  double host_sec = std::chrono::duration<double>(std::chrono::high_resolution_clock::now() - UpDown::curRuntimeInstance->getStartTime()).count();
  // uint64_t lane_exec_ticks = updown_period * total_exec_cycles;
  uint64_t lane_exec_ticks = total_exec_cycles;

  basim::globalLogs.perflog.writeUpdown(host_sec, final_tick, sim_ticks, sim_sec, network_id, thread_id, event_label,
               lane_exec_ticks, msg_id, msg_str);
}

static void writeBasimTracelog(uint32_t inc_exec_cycles,  // incremental exec cycles
                               std::string &msg_type_str, // type of message
                               std::string &msg_str       // message
) {
  // uint64_t final_tick = this->getCurTick() + updown_period * inc_exec_cycles;
  uint64_t final_tick = UpDown::curRuntimeInstance->getCurTick();
  uint64_t sim_ticks = final_tick;

  basim::globalLogs.tracelog.write(sim_ticks, msg_type_str, msg_str);
}

void BASimUDRuntime_t::initLogs(std::filesystem::path log_folder_path) {
  if (!std::filesystem::exists(log_folder_path)) {
    if (std::filesystem::create_directory(log_folder_path)) {
      UPDOWN_INFOMSG("CREATED LOG FOLDER: %s\n", log_folder_path.c_str());
    } else {
      UPDOWN_ERROR("COULD NOT CREATE LOG FOLDER: %s\n", log_folder_path.c_str());
    }
  } else {
    UPDOWN_INFOMSG("EXSISTING LOG FOLDER: %s\n", log_folder_path.c_str());
  }

  // open perflog
  basim::globalLogs.perflog.open(log_folder_path / "perflog.tsv");
  basim::globalLogs.perflog.registerPerflogCallback(writeUpdownBasimPerflog);
  // open tracelog
  basim::globalLogs.tracelog.open(log_folder_path / "tracelog.log");
  basim::globalLogs.tracelog.registerTracelogCallback(writeBasimTracelog);
}

void BASimUDRuntime_t::send_event(event_t ev) {
  // Perform the regular access. This will have no effect
  UDRuntime_t::send_event(ev);
  auto netid = ev.get_NetworkId();
  uint32_t udid = this->get_globalUDNum((netid));

  // Update the label with the actual event label resolved address
  ev.set_EventLabel(symbolMap[ev.get_EventLabel()]);

  basim::eventword_t basimev = basim::EventWord(ev.get_EventWord());
  basim::operands_t op(ev.get_NumOperands(), basim::EventWord(ev.get_OperandsData()[0]));  // num opernads + cont
  op.setData(&ev.get_OperandsData()[1]);
  basim::eventoperands_t eops(&basimev, &op);
  sendEventOperands(udid, &eops, (ev.get_NetworkId()).get_LaneId());
}

int BASimUDRuntime_t::getUDIdx(basim::networkid_t nid, ud_machine_t m){
  return nid.getNodeID() *
             (this->MachineConfig.NumStacks * this->MachineConfig.NumUDs) +
         nid.getStackID() * (this->MachineConfig.NumUDs) + nid.getUDID();
}
int BASimUDRuntime_t::getUDForAddr(basim::networkid_t nid, ud_machine_t m, basim::Addr addr){
  // This needs to be modified when node level DRAM view is available on fastsim
  return nid.getNodeID() *
             (this->MachineConfig.NumStacks * this->MachineConfig.NumUDs) +
         nid.getStackID() * (this->MachineConfig.NumUDs) + nid.getUDID();
}

void BASimUDRuntime_t::postSimulate(uint32_t udid, uint32_t laneID) {
  // Cycle through the send buffers of each lane in the UDs
  while(uds[udid]->sendReady(laneID)){
      //printf("postSimulate: ud:%d, ln: %d\n", udid, laneID);
      std::unique_ptr<basim::MMessage> m = uds[udid]->getSendMessage(laneID);
      switch(m->getType()){
          case basim::MType::M1Type:{
              // Send Message to another lane
              basim::eventword_t ev = m->getXe();
              basim::operands_t op0(m->getLen(), m->getXc());  // num operands + cont
              //op0.setData((m->getpayload()).get());
              op0.setData((m->getpayload()));
              basim::eventoperands_t eops(&ev, &op0);
              int ud = getUDIdx(ev.getNWID(), this->MachineConfig);
            #ifndef SENDPOLICY
              sendEventOperands(ud, &eops, (ev.getNWID()).getLaneID());
            #else
              int policy = (ev.getNWID()).getSendPolicy();
              if(policy == 7){
                basim::Addr addr = op0[1];
                ud = getUDForAddr(ev.getNWID(), this->MachineConfig, addr);
                sendEventOperands(ud, &eops, (ev.getNWID()).getLaneID());
              }else{
                int laneid = uds[ud]->getLanebyPolicy(ev.getNWID().getLaneID(), policy);
                sendEventOperands(ud, &eops, laneid);
              }
            #endif
              #if defined(FASTSIM_TRACE_MSG)
              basim::globalLogs.tracelog.write(UpDown::curRuntimeInstance->getCurTick(), "MSG",
                "<LANE2LANE, " +
                std::to_string(m->getSrcEventWord().getNWID().getUDName()) + ":" +
                std::to_string(m->getSrcEventWord().getThreadID()) +" -> " +
                std::to_string(m->getXe().getNWID().getUDName()) + ":" +
                std::to_string(m->getXe().getThreadID()) +", " +
                std::to_string(m->getMsgSize()) + ">"
                );
              #endif
              break;
          }
          case basim::MType::M2Type:{
              // Send to Memory
              basim::eventword_t* cont = new basim::EventWord();
              *cont = m->getXc();
              if(m->isStore()){
                  // Writes to memory
                  word_t* dataptr = (m->getpayload()); // get the data and store it in memory
                  //word_t* dataptr = (m->getpayload()).get(); // get the data and store it in memory
                  word_t* dst = reinterpret_cast<word_t*>(m->getdestaddr());
                  std::memcpy(dst, dataptr, m->getLen()*WORDSIZE);
                  // Post store event push
                  uint64_t noupdate_cont = 0x7fffffffffffffff;
                  basim::operands_t op0(2, basim::EventWord(noupdate_cont));  // num opernads + cont
                  op0.setDataWord(0, m->getdestaddr());
                  op0.setDataWord(1, m->getdestaddr());
                  basim::eventoperands_t eops(cont, &op0);
                  int ud = getUDIdx(cont->getNWID(), this->MachineConfig);
                  sendEventOperands(ud, &eops, (cont->getNWID()).getLaneID());
                  #if defined(FASTSIM_TRACE_MSG)
                  basim::globalLogs.tracelog.write(UpDown::curRuntimeInstance->getCurTick(), "MSG",
                    "<LANE2MEM_ST, " +
                    std::to_string(m->getSrcEventWord().getNWID().getUDName()) + " -> " +
                    basim::addr2HexString(reinterpret_cast<void *>(m->getdestaddr())) + ", " +
                    std::to_string(m->getMsgSize()) + ">"
                    );
                  basim::globalLogs.tracelog.write(UpDown::curRuntimeInstance->getCurTick(), "MSG",
                    "<MEM2LANE_ST, " +
                    basim::addr2HexString(reinterpret_cast<void *>(m->getdestaddr())) + " -> " +
                    std::to_string(m->getXc().getNWID().getUDName()) + ", " +
                    std::to_string((2 /* DRAM Address */ + 1 /* Dst Event Word */ + 1 /* Continuation Word */) * WORDSIZE) + ">"
                    );
                  #endif
              }else{
                  // Reads from memory
                  word_t* dataptr = reinterpret_cast<word_t*>(m->getdestaddr());
                  word_t* dst = new word_t[m->getLen()];
                  std::memcpy(dst, dataptr, m->getLen()*WORDSIZE);
                  uint64_t noupdate_cont = 0x7fffffffffffffff;
                  basim::operands_t op0(m->getLen() + 1, basim::EventWord(noupdate_cont));  // num opernads + dram addr (cont added by constructor)
                  for (int im = 0; im < m->getLen(); im++) {
                    op0.setDataWord(im, dst[im]);
                  }
                  op0.setDataWord(m->getLen(), m->getdestaddr());
                  basim::eventoperands_t eops(cont, &op0);
                  int ud = getUDIdx(cont->getNWID(), this->MachineConfig);
                  sendEventOperands(ud, &eops, (cont->getNWID()).getLaneID());
                  delete[] dst;
                  #if defined(FASTSIM_TRACE_MSG)
                  basim::globalLogs.tracelog.write(UpDown::curRuntimeInstance->getCurTick(), "MSG",
                    "<LANE2MEM_LD, " +
                    std::to_string(m->getSrcEventWord().getNWID().getUDName()) + " -> " +
                    basim::addr2HexString(reinterpret_cast<void *>(m->getdestaddr())) + ", " +
                    std::to_string(m->getMsgSize()) + ">"
                    );
                  basim::globalLogs.tracelog.write(UpDown::curRuntimeInstance->getCurTick(), "MSG",
                    "<MEM2LANE_LD, " +
                    basim::addr2HexString(reinterpret_cast<void *>(m->getdestaddr())) + " -> " +
                    std::to_string(m->getXc().getNWID().getUDName()) + ", " +
                    std::to_string((m->getLen() + 1 /* DRAM Address */ + 1 /* Dst Event Word */ + 1 /* Continuation Word */) * WORDSIZE) + ">"
                    );
                  #endif
              }
              delete cont;
              break;
          }
          case basim::MType::M3Type:{
              // Send Message to another lane
              basim::eventword_t ev = m->getXe();
              basim::operands_t op0(m->getLen(), m->getXc());  // num opernads + cont
              //op0.setData((m->getpayload()).get());
              op0.setData((m->getpayload()));
              basim::eventoperands_t eops(&ev, &op0);
              int ud = getUDIdx(ev.getNWID(), this->MachineConfig);
            #ifndef SENDPOLICY
              sendEventOperands(ud, &eops, (ev.getNWID()).getLaneID());
            #else
              int policy = (ev.getNWID()).getSendPolicy();
              if(policy == 7){
                basim::Addr addr = op0[1];
                ud = getUDForAddr(ev.getNWID(), this->MachineConfig, addr);
                sendEventOperands(ud, &eops, (ev.getNWID()).getLaneID());
              }else{
                int laneid = uds[ud]->getLanebyPolicy(ev.getNWID().getLaneID(), (ev.getNWID()).getSendPolicy());
                sendEventOperands(ud, &eops, laneid);
              }
            #endif
            #if defined(FASTSIM_TRACE_MSG)
            basim::globalLogs.tracelog.write(UpDown::curRuntimeInstance->getCurTick(), "MSG",
              "<LANE2LANE, " +
              std::to_string(m->getSrcEventWord().getNWID().getUDName()) + ":" +
              std::to_string(m->getSrcEventWord().getThreadID()) +" -> " +
              std::to_string(m->getXe().getNWID().getUDName()) + ":" +
              std::to_string(m->getXe().getThreadID()) +", " +
              std::to_string(m->getMsgSize()) + ">"
              );
            #endif
            break;
          }
          case basim::MType::M3Type_M:{
              // Always a store (2 words)
              basim::eventword_t cont = m->getXc();
              // Writes to memory
              //word_t* dataptr = (m->getpayload()).get(); // get the data and store it in memory
              word_t* dataptr = (m->getpayload()); // get the data and store it in memory
              word_t* dst = reinterpret_cast<word_t*>(m->getdestaddr());
              std::memcpy(dst, dataptr, m->getLen()*WORDSIZE);
              // Post store event push
              uint64_t noupdate_cont = 0x7fffffffffffffff;
              basim::operands_t op0(2, basim::EventWord(noupdate_cont));  // num opernads + cont
              op0.setDataWord(0, m->getdestaddr());
              op0.setDataWord(1, m->getdestaddr());
              basim::eventoperands_t eops(&cont, &op0);
              int ud = getUDIdx(cont.getNWID(), this->MachineConfig);
              sendEventOperands(ud, &eops, (cont.getNWID()).getLaneID());
              #if defined(FASTSIM_TRACE_MSG)
              basim::globalLogs.tracelog.write(UpDown::curRuntimeInstance->getCurTick(), "MSG",
                "<LANE2MEM_ST, " +
                std::to_string(m->getSrcEventWord().getNWID().getUDName()) + " -> " +
                basim::addr2HexString(reinterpret_cast<void *>(m->getdestaddr())) + ", " +
                std::to_string(m->getMsgSize()) + ">"
                );
              basim::globalLogs.tracelog.write(UpDown::curRuntimeInstance->getCurTick(), "MSG",
                "<MEM2LANE_ST, " +
                basim::addr2HexString(reinterpret_cast<void *>(m->getdestaddr())) + " -> " +
                std::to_string(m->getXc().getNWID().getUDName()) + ", " +
                std::to_string((2 /* DRAM Address */ + 1 /* Dst Event Word */ + 1 /* Continuation Word */) * WORDSIZE) + ">"
                );
              #endif
              break;
          }
          case basim::MType::M4Type:{
              // Send Message to another lane
              // Merge this with M3Type
              basim::eventword_t ev = m->getXe();
              basim::operands_t op0(m->getLen(), m->getXc());  // num opernads + cont
              //op0.setData((m->getpayload()).get());
              op0.setData((m->getpayload()));
              basim::eventoperands_t eops(&ev, &op0);
              int ud = getUDIdx(ev.getNWID(), this->MachineConfig);
            #ifndef SENDPOLICY
                sendEventOperands(ud, &eops, (ev.getNWID()).getLaneID());
            #else
              int policy = (ev.getNWID()).getSendPolicy();
              if(policy == 7){
                basim::Addr addr = op0[1];
                ud = getUDForAddr(ev.getNWID(), this->MachineConfig, addr);
                sendEventOperands(ud, &eops, (ev.getNWID()).getLaneID());
              }else{
                int laneid = uds[ud]->getLanebyPolicy(ev.getNWID().getLaneID(), (ev.getNWID()).getSendPolicy());
                sendEventOperands(ud, &eops, laneid);
              }
            #endif
              #if defined(FASTSIM_TRACE_MSG)
              basim::globalLogs.tracelog.write(UpDown::curRuntimeInstance->getCurTick(), "MSG",
                "<LANE2LANE, " +
                std::to_string(m->getSrcEventWord().getNWID().getUDName()) + ":" +
                std::to_string(m->getSrcEventWord().getThreadID()) +" -> " +
                std::to_string(m->getXe().getNWID().getUDName()) + ":" +
                std::to_string(m->getXe().getThreadID()) +", " +
                std::to_string(m->getMsgSize()) + ">"
                );
              #endif
              break;
          }
          case basim::MType::M4Type_M:{
              // Always a store (2 words)
              // Merge this with M3Type_M
              basim::eventword_t cont = m->getXc();
              // Writes to memory
              //word_t* dataptr = (m->getpayload()).get(); // get the data and store it in memory
              word_t* dataptr = (m->getpayload()); // get the data and store it in memory
              word_t* dst = reinterpret_cast<word_t*>(m->getdestaddr());
              std::memcpy(dst, dataptr, m->getLen()*WORDSIZE);
              // Post store event push
              uint64_t noupdate_cont = 0x7fffffffffffffff;
              basim::operands_t op0(2, basim::EventWord(noupdate_cont));  // num opernads + cont
              op0.setDataWord(0, m->getdestaddr());
              op0.setDataWord(1, m->getdestaddr());
              basim::eventoperands_t eops(&cont, &op0);
              int ud = getUDIdx(cont.getNWID(), this->MachineConfig);
              sendEventOperands(ud, &eops, (cont.getNWID()).getLaneID());
              #if defined(FASTSIM_TRACE_MSG)
              basim::globalLogs.tracelog.write(UpDown::curRuntimeInstance->getCurTick(), "MSG",
                "<LANE2MEM_ST, " +
                std::to_string(m->getSrcEventWord().getNWID().getUDName()) + " -> " +
                basim::addr2HexString(reinterpret_cast<void *>(m->getdestaddr())) + ", " +
                std::to_string(m->getMsgSize()) + ">"
                );
              basim::globalLogs.tracelog.write(UpDown::curRuntimeInstance->getCurTick(), "MSG",
                "<MEM2LANE_ST, " +
                basim::addr2HexString(reinterpret_cast<void *>(m->getdestaddr())) + " -> " +
                std::to_string(m->getXc().getNWID().getUDName()) + ", " +
                std::to_string((2 /* DRAM Address */ + 1 /* Dst Event Word */ + 1 /* Continuation Word */) * WORDSIZE) + ">"
                );
              #endif
              break;
          }
          default:{
              BASIM_ERROR("Undefined Message type in Send Buffer");
              break;
          }
      }
      //uds[udid]->removeSendMessage(i);
  }
}

void BASimUDRuntime_t::sendEventOperands(int sourceUDID, basim::eventoperands_t *eops, uint32_t targetLaneID) {
    uds[sourceUDID]->pushEventOperands(*eops, targetLaneID);
}

void BASimUDRuntime_t::start_exec(networkid_t nwid) {
  // Perform the regular access. This will have no effect
  UDRuntime_t::start_exec(nwid);
  // Then we do a round-robin execution of all the lanes while
  // there is something executing
  bool something_exec;
  uint64_t num_iterations = 0;
  do {
        something_exec = false;

        #ifndef GEM5_MODE
            //#pragma omp parallel for collapse(2) schedule(dynamic, 1) reduction(|| : something_exec) // lane level parallelism
            #pragma omp parallel for schedule(static, 1) reduction(|| : something_exec) // ud level parallelism
            for (uint32_t ud = 0; ud < total_uds; ud++) {
                for (uint32_t ln = 0; ln < this->MachineConfig.NumLanes; ln++) {
                    if (!uds[ud]->isIdle(ln)) {
                      something_exec = true;
                      uds[ud]->simulate(ln, NumTicks, globalTick);
                    }
                }
            }
            // OMP: implicit barrier

            if(something_exec) {
                #pragma omp parallel for collapse(2)
                for (uint32_t ud = 0; ud < total_uds; ud++) {
                    for (uint32_t ln = 0; ln < this->MachineConfig.NumLanes; ln++) {
                        postSimulate(ud, ln);
                    }
                }
                // OMP: implicit barrier
            }
        #else
            for (uint32_t ud = 0; ud < total_uds; ud++) {
                for (uint32_t ln = 0; ln < this->MachineConfig.NumLanes; ln++) {
                    if (!uds[ud]->isIdle(ln)) {
                      something_exec = true;
                      uds[ud]->simulate(ln, NumTicks, globalTick);
                      postSimulate(ud, ln);
                    }
                }
            }
        #endif
        globalTick+=NumTicks;
  } while (something_exec &&
           (!max_sim_iterations || ++num_iterations < max_sim_iterations));
}

void BASimUDRuntime_t::t2ud_memcpy(void *data, uint64_t size, networkid_t nwid,
                                 uint32_t offset) {
  UDRuntime_t::t2ud_memcpy(data, size, nwid, offset);
  uint32_t ud_num = this->get_globalUDNum(nwid);
  uint64_t addr = UDRuntime_t::get_lane_physical_memory(nwid, offset); 
                  // UDRuntime_t::get_ud_physical_memory(nwid);
  uint8_t* data_ptr = reinterpret_cast<uint8_t *>(data);
  for (int i = 0; i < size / sizeof(word_t); i++) {
    // Address is local
    uds[ud_num]->writeScratchPad(sizeof(word_t), addr, reinterpret_cast<uint8_t *>(data_ptr));
    addr += sizeof(word_t);
    data_ptr += sizeof(word_t);
  }
}

void BASimUDRuntime_t::ud2t_memcpy(void *data, uint64_t size, networkid_t nwid,
                                 uint32_t offset) {
  uint32_t ud_num = this->get_globalUDNum(nwid);
  uint64_t addr = UDRuntime_t::get_lane_physical_memory(nwid, offset); //
                  //UDRuntime_t::get_ud_physical_memory(nwid);
  uint64_t apply_offset = UDRuntime_t::get_lane_aligned_offset(nwid, offset);
  apply_offset /= sizeof(word_t);
  ptr_t base = BaseAddrs.spaddr + apply_offset;
  UPDOWN_INFOMSG("Actual addr: 0x%lX , base: 0x%lX", addr, (unsigned long)base);
  UPDOWN_ASSERT(
      base + size / sizeof(word_t) <
          BaseAddrs.spaddr + MachineConfig.SPSize() / sizeof(word_t),
      "ud2t_memcpy: memory access to 0x%lX out of scratchpad memory bounds "
      "with offset %lu bytes and size %lu bytes. Scratchpad memory Base "
      "Address 0x%lX scratchpad memory size %lu bytes",
      (unsigned long)(base), (unsigned long)(apply_offset * sizeof(word_t)),
      (unsigned long)size, (unsigned long)BaseAddrs.spaddr,
      (unsigned long)MachineConfig.SPSize());
  //if (python_enabled)
  //  upstream_pyintf[ud_num]->read_scratch(
  //      addr, reinterpret_cast<uint8_t *>(base), size);
  uds[ud_num]->readScratchPad(sizeof(word_t), addr, reinterpret_cast<uint8_t*>(base));
  UDRuntime_t::ud2t_memcpy(data, size, nwid, offset);
}

bool BASimUDRuntime_t::test_addr(networkid_t nwid, uint32_t offset,
                               word_t expected) {
  uint32_t ud_num = this->get_globalUDNum(nwid);
  uint64_t addr = UDRuntime_t::get_lane_physical_memory(nwid, offset);
                  //UDRuntime_t::get_ud_physical_memory(nwid);
  uint64_t apply_offset = UDRuntime_t::get_lane_aligned_offset(nwid, offset);
  apply_offset /= sizeof(word_t);
  ptr_t base = BaseAddrs.spaddr + apply_offset;
  UPDOWN_ASSERT(
      base < BaseAddrs.spaddr + MachineConfig.SPSize() / sizeof(word_t),
      "test_addr: memory access to 0x%lX out of scratchpad memory bounds "
      "with offset %lu bytes and size 4 bytes. Scratchpad memory Base Address "
      "0x%lX scratchpad memory size %lu bytes",
      (unsigned long)(base), (unsigned long)(apply_offset * sizeof(word_t)),
      (unsigned long)BaseAddrs.spaddr, (unsigned long)MachineConfig.SPSize());
  start_exec(nwid);
  uds[ud_num]->readScratchPad(sizeof(word_t), addr, reinterpret_cast<uint8_t*>(base));
  return UDRuntime_t::test_addr(nwid, offset, expected);
}

void BASimUDRuntime_t::test_wait_addr(networkid_t nwid, uint32_t offset,
                                    word_t expected) {

  while (!test_addr(nwid, offset, expected))
    ;
  // The bottom call will never hold since we're holding here
  UDRuntime_t::test_wait_addr(nwid, offset, expected);
}

void BASimUDRuntime_t::dumpMemory(const char* filename, void* vaddr, uint64_t size){
  FILE* mem_file = fopen(filename, "wb");
  if (!mem_file) {
    printf("Could not open %s\n", filename);
    exit(1);
  }

  // Use API to access mm_malloced area
  uint64_t offset = reinterpret_cast<uint64_t>(vaddr) - reinterpret_cast<uint64_t>(BaseAddrs.mmaddr);
  uint8_t *data = (uint8_t*)malloc(size * sizeof(uint8_t));
  this->mm2t_memcpy(offset, data, size);

  fseek(mem_file, 0, SEEK_SET);
  // Write 'F' to indicate dump by Fastsim
  fwrite("F", sizeof(char), 1, mem_file);
  // Write 'D' to indicate DRAM dump
  fwrite("D", sizeof(char), 1, mem_file);
  // Write dump start file offset
  uint64_t dump_start_file_offset = 1 + 1 + 8 + 8 + 8;
  fwrite(&dump_start_file_offset, sizeof(uint64_t), 1, mem_file);
  BASIM_INFOMSG("DRAM Dump start file offset: %lu", dump_start_file_offset);
  // Write dump vaddr
  fwrite(&vaddr, sizeof(uint64_t), 1, mem_file);
  BASIM_INFOMSG("DRAM Dump vaddr: %p", vaddr);
  // Write dump size
  fwrite(&size, sizeof(uint64_t), 1, mem_file);
  BASIM_INFOMSG("DRAM Dump size: %lu", size);
  // Write size bytes into mem_file
  fwrite(data, sizeof(uint8_t), size, mem_file);

  fclose(mem_file);
  free(data);
}

std::pair<void *, uint64_t> BASimUDRuntime_t::loadMemory(const char* filename, void* vaddr, uint64_t size){
  FILE* mem_file = fopen(filename, "rb");
  if (!mem_file) {
    printf("Could not open %s\n", filename);
    exit(1);
  }

  fseek(mem_file, 0, SEEK_SET);
  // Read 'F' to indicate dump by Fastsim
  char dump_type;
  fread(&dump_type, sizeof(char), 1, mem_file);
  UPDOWN_ERROR_IF(dump_type != 'F', "DRAM dump load failed! Not a FastSim dump file!\n");
  // Read 'D' to indicate DRAM dump
  fread(&dump_type, sizeof(char), 1, mem_file);
  UPDOWN_ERROR_IF(dump_type != 'D', "DRAM dump load failed! Not a DRAM dump file!\n");
  // Read dump start file offset
  uint64_t dump_start_file_offset;
  fread(&dump_start_file_offset, sizeof(uint64_t), 1, mem_file);
  BASIM_INFOMSG("DRAM Dump start file offset: %lu", dump_start_file_offset);
  // Read dump vaddr
  uint64_t dump_vaddr;
  fread(&dump_vaddr, sizeof(uint64_t), 1, mem_file);
  if (vaddr == nullptr) {
    vaddr = reinterpret_cast<void *>(dump_vaddr);
    BASIM_INFOMSG("DRAM Dump vaddr (from dump file): %p", vaddr);
  } else {
    BASIM_INFOMSG("DRAM Dump vaddr (user specified): %p", vaddr);
  }
  // Read dump size
  uint64_t dump_size;
  fread(&dump_size, sizeof(uint64_t), 1, mem_file);
  if (vaddr == nullptr || size == 0) {
    size = dump_size;
    BASIM_INFOMSG("DRAM Dump size (from dump file): %lu", size);
  } else {
    BASIM_INFOMSG("DRAM Dump size (user specified): %lu", size);
  }
  // Read size bytes into mem_file
  fseek(mem_file, dump_start_file_offset, SEEK_SET);
  uint8_t *data = (uint8_t*)malloc(size * sizeof(uint8_t));
  fread(data, sizeof(uint8_t), size, mem_file);

  // Use API to access mm_malloced area
  if (this->mm_malloc_at_addr(vaddr, size) == nullptr) { // allocate memory
    BASIM_ERROR("DRAM dump load failed! Cannot allocate memory at (%p, %lu)", vaddr, size);
  }
  uint64_t offset = reinterpret_cast<uint64_t>(vaddr) - reinterpret_cast<uint64_t>(BaseAddrs.mmaddr);
  this->t2mm_memcpy(offset, data, size);

  fclose(mem_file);
  free(data);

  return std::make_pair(vaddr, size);
}

void BASimUDRuntime_t::dumpLocalMemory(const char* filename, networkid_t start_nwid, uint64_t num_lanes) {
  FILE* spd_file = fopen(filename, "wb");
  if (!spd_file) {
    printf("Could not open %s\n", filename);
    exit(1);
  }

  uint64_t lane_lm_size = DEF_SPMEM_BANK_SIZE;
  uint64_t total_lm_size;
  if (start_nwid.get_NetworkId_UdName() == 0 && num_lanes == 0) {
    // all LMs
    total_lm_size = lane_lm_size * this->MachineConfig.NumLanes * this->MachineConfig.NumUDs * this->MachineConfig.NumStacks * this->MachineConfig.NumNodes;
    num_lanes = this->MachineConfig.NumLanes * this->MachineConfig.NumUDs * this->MachineConfig.NumStacks * this->MachineConfig.NumNodes;
  } else {
    // selected LMs
    total_lm_size = lane_lm_size * num_lanes;
  }
  uint8_t *data = (uint8_t*)malloc(total_lm_size * sizeof(uint8_t));
  basim::Addr start_addr = (uint64_t)BaseAddrs.spaddr;
  uint64_t lm_offset = 0;

  for (uint32_t i = start_nwid.get_NetworkId_UdName(); i < start_nwid.get_NetworkId_UdName() + num_lanes; i++) {
    uds[i / DEF_NUM_LANES]->readScratchPadBank(i % DEF_NUM_LANES, &data[lm_offset]);
    lm_offset += DEF_SPMEM_BANK_SIZE;
  }

  fseek(spd_file, 0, SEEK_SET);
  // Write 'F' to indicate dump by Fastsim
  fwrite("F", sizeof(char), 1, spd_file);
  // Write 'L' to indicate LM dump
  fwrite("L", sizeof(char), 1, spd_file);
  // Write dump start file offset
  uint64_t dump_start_file_offset = 1 + 1 + 8 + 8 + 8 + 8;
  fwrite(&dump_start_file_offset, sizeof(uint64_t), 1, spd_file);
  BASIM_INFOMSG("LM Dump start file offset: %lu", dump_start_file_offset);
  // Write dump start nwid (ud_name only)
  uint64_t dump_nwid = start_nwid.get_NetworkId_UdName();
  fwrite(&dump_nwid, sizeof(uint64_t), 1, spd_file);
  BASIM_INFOMSG("LM Dump start nwid: %lu", dump_nwid);
  // Write num lanes dumped
  if (start_nwid.get_NetworkId_UdName() == 0 && num_lanes == 0) {
    num_lanes = this->MachineConfig.NumLanes * this->MachineConfig.NumUDs * this->MachineConfig.NumStacks * this->MachineConfig.NumNodes;
  }
  fwrite(&num_lanes, sizeof(uint64_t), 1, spd_file);
  BASIM_INFOMSG("LM Dump num lanes: %lu", num_lanes);
  // Write LM size per lane
  fwrite(&lane_lm_size, sizeof(uint64_t), 1, spd_file);
  BASIM_INFOMSG("LM Dump size per lane: %lu", lane_lm_size);
  // Write size bytes into mem_file
  fwrite(data, sizeof(uint8_t), total_lm_size, spd_file);
  fclose(spd_file);

  free(data);
}

std::pair<networkid_t, uint64_t> BASimUDRuntime_t::loadLocalMemory(const char* filename, networkid_t start_nwid, uint64_t num_lanes){
  FILE* spd_file = fopen(filename, "rb");
  if (!spd_file) {
    printf("Could not open %s\n", filename);
    exit(1);
  }

  fseek(spd_file, 0, SEEK_SET);
  // Read 'F' to indicate dump by Fastsim
  char dump_type;
  fread(&dump_type, sizeof(char), 1, spd_file);
  UPDOWN_ERROR_IF(dump_type != 'F', "DRAM dump load failed! Not a FastSim dump file!\n");
  // Read 'L' to indicate LM dump
  fread(&dump_type, sizeof(char), 1, spd_file);
  UPDOWN_ERROR_IF(dump_type != 'L', "DRAM dump load failed! Not a LM dump file!\n");
  // Read dump start file offset
  uint64_t dump_start_file_offset;
  fread(&dump_start_file_offset, sizeof(uint64_t), 1, spd_file);
  BASIM_INFOMSG("LM Dump start file offset: %lu", dump_start_file_offset);
  // Read dump start nwid (ud_name only)
  uint64_t dump_start_nwid_raw;
  fread(&dump_start_nwid_raw, sizeof(uint64_t), 1, spd_file);
  networkid_t dump_start_nwid(dump_start_nwid_raw, false, 0);
  BASIM_INFOMSG("LM Dump start nwid (from dump file): %lu", dump_start_nwid_raw);
  // Read num lanes dumped
  uint64_t dump_num_lanes;
  fread(&dump_num_lanes, sizeof(uint64_t), 1, spd_file);
  BASIM_INFOMSG("LM Dump num lanes (from dump file): %lu", dump_num_lanes);
  // Read LM size per lane
  uint64_t lane_lm_size;
  fread(&lane_lm_size, sizeof(uint64_t), 1, spd_file);
  BASIM_INFOMSG("LM Dump size per lane (from dump file): %lu", lane_lm_size);

  // Copy it lm by lm
  fseek(spd_file, dump_start_file_offset, SEEK_SET);
  uint8_t *data = nullptr;
  if (start_nwid.get_NetworkId_UdName() == 0 && num_lanes == 0) {
    // LM specified from the dump
    uint64_t total_lm_size = dump_num_lanes * lane_lm_size;
    data = (uint8_t*)malloc(total_lm_size * sizeof(uint8_t));
    fread(data, sizeof(uint8_t), total_lm_size, spd_file);
    uint64_t lm_offset = 0;
    for (uint32_t i = dump_start_nwid.get_NetworkId_UdName(); i < dump_start_nwid.get_NetworkId_UdName() + dump_num_lanes; i++) {
      uds[i / DEF_NUM_LANES]->writeScratchPadBank(i % DEF_NUM_LANES, &data[lm_offset]);
      lm_offset += DEF_SPMEM_BANK_SIZE;
    }
  } else {
    // all LMs
    uint64_t total_lm_size = num_lanes * DEF_SPMEM_BANK_SIZE;
    data = (uint8_t*)malloc(total_lm_size * sizeof(uint8_t));
    fread(data, sizeof(uint8_t), total_lm_size, spd_file);
    uint64_t lm_offset = 0;
    for (uint32_t i = start_nwid.get_NetworkId_UdName(); i < start_nwid.get_NetworkId_UdName() + num_lanes; i++) {
      uds[i / DEF_NUM_LANES]->writeScratchPadBank(i % DEF_NUM_LANES, &data[lm_offset]);
      lm_offset += DEF_SPMEM_BANK_SIZE;
    }
  }

  fclose(spd_file);
  free(data);

  if (start_nwid.get_NetworkId_UdName() == 0 && num_lanes == 0) {
    return std::make_pair(dump_start_nwid, dump_num_lanes);
  } else {
    return std::make_pair(start_nwid, num_lanes);
  }
}

void BASimUDRuntime_t::reset_stats(uint32_t ud_id, uint8_t lane_id){
  this->uds[ud_id]->resetStats(lane_id);
}

void BASimUDRuntime_t::reset_stats(uint32_t ud_id){
  this->uds[ud_id]->resetStats();
}

void BASimUDRuntime_t::reset_stats(){
  for (int ud = 0; ud < total_uds; ud++)
    this->uds[ud]->resetStats();
}

void BASimUDRuntime_t::update_stats(uint32_t lane_num) {
  uint8_t lane_id = lane_num % 64;
  uint32_t ud_id = lane_num / 64;
  this->update_stats(ud_id, lane_id);
}

void BASimUDRuntime_t::update_stats(uint32_t ud_id, uint8_t lane_num) {

  const basim::LaneStats* loc_stats = uds[ud_id]->getLaneStats(lane_num);
  uint32_t lane_id = lane_num; 
  this->simStats[ud_id][lane_id].cycle_count = loc_stats->cycle_count;
  this->simStats[ud_id][lane_id].inst_count = loc_stats->inst_count;  
  this->simStats[ud_id][lane_id].tran_count = loc_stats->tran_count;
  this->simStats[ud_id][lane_id].thread_count = loc_stats->thread_count;
  this->simStats[ud_id][lane_id].inst_count_atomic = loc_stats->inst_count_atomic;
  this->simStats[ud_id][lane_id].inst_count_bitwise = loc_stats->inst_count_bitwise;
  this->simStats[ud_id][lane_id].inst_count_ctrlflow = loc_stats->inst_count_ctrlflow;
  this->simStats[ud_id][lane_id].inst_count_datmov = loc_stats->inst_count_datmov; 
  this->simStats[ud_id][lane_id].inst_count_ev = loc_stats->inst_count_ev;
  this->simStats[ud_id][lane_id].inst_count_fparith = loc_stats->inst_count_fparith;
  this->simStats[ud_id][lane_id].inst_count_hash = loc_stats->inst_count_hash;
  this->simStats[ud_id][lane_id].inst_count_intarith = loc_stats->inst_count_intarith;
  this->simStats[ud_id][lane_id].inst_count_intcmp = loc_stats->inst_count_intcmp;
  this->simStats[ud_id][lane_id].inst_count_msg = loc_stats->inst_count_msg;
  this->simStats[ud_id][lane_id].inst_count_threadctrl = loc_stats->inst_count_threadctrl;
  this->simStats[ud_id][lane_id].inst_count_tranctrl = loc_stats->inst_count_tranctrl;
  this->simStats[ud_id][lane_id].inst_count_vec = loc_stats->inst_count_vec;
  this->simStats[ud_id][lane_id].tran_count_basic = loc_stats->tran_count_basic;
  this->simStats[ud_id][lane_id].tran_count_majority = loc_stats->tran_count_majority;
  this->simStats[ud_id][lane_id].tran_count_default = loc_stats->tran_count_default;
  this->simStats[ud_id][lane_id].tran_count_epsilon = loc_stats->tran_count_epsilon;
  this->simStats[ud_id][lane_id].tran_count_common = loc_stats->tran_count_common;
  this->simStats[ud_id][lane_id].tran_count_flagged = loc_stats->tran_count_flagged;
  this->simStats[ud_id][lane_id].tran_count_refill = loc_stats->tran_count_refill;
  this->simStats[ud_id][lane_id].tran_count_event = loc_stats->tran_count_event;
#ifdef DETAIL_STATS
  this->simStats[ud_id][lane_id].max_inst_count_per_event = loc_stats->max_inst_per_event;
  this->simStats[ud_id][lane_id].max_inst_count_per_tx = loc_stats->max_inst_per_tx;
#endif
  this->simStats[ud_id][lane_id].lm_load_bytes = loc_stats->lm_load_bytes;
  this->simStats[ud_id][lane_id].lm_store_bytes = loc_stats->lm_store_bytes;
  this->simStats[ud_id][lane_id].lm_load_count = loc_stats->lm_load_count;
  this->simStats[ud_id][lane_id].lm_store_count = loc_stats->lm_store_count;
  this->simStats[ud_id][lane_id].dram_load_bytes = loc_stats->dram_load_bytes;
  this->simStats[ud_id][lane_id].dram_store_bytes = loc_stats->dram_store_bytes;
  this->simStats[ud_id][lane_id].dram_load_count = loc_stats->dram_load_count;
  this->simStats[ud_id][lane_id].dram_store_count = loc_stats->dram_store_count;
  this->simStats[ud_id][lane_id].eventq_len_max = loc_stats->eventq_len_max;
  this->simStats[ud_id][lane_id].opbuff_len_max = loc_stats->opbuff_len_max;
  //for (int i = 0; i < 16; i++) {
  //  this->simStats[ud_id][lane_num].user_counter[i] = loc_stats->user_counter[i];
  //}
}

struct BASimStats& BASimUDRuntime_t::get_stats(uint32_t ud_id, uint8_t lane_num){
  update_stats(ud_id, lane_num);
  return this->simStats[ud_id][lane_num];
}

struct BASimStats& BASimUDRuntime_t::get_stats(uint32_t lane_num){
  uint8_t lane_id = lane_num % 64;
  uint32_t ud_id = lane_num / 64;
  return this->get_stats(ud_id, lane_id);
}

void BASimUDRuntime_t::print_stats(uint32_t lane_num){
  uint8_t lane_id = lane_num % 64;
  uint32_t ud_id = lane_num / 64;
  print_stats(ud_id, lane_id);
}

void BASimUDRuntime_t::print_stats(uint32_t ud_id, uint8_t lane_num) {
  const int wid = 10;
  const basim::LaneStats* lnstats = uds[ud_id]->getLaneStats(lane_num);

  printf("[UD%d-L%d] Cycles               =%lu\n", ud_id, lane_num, lnstats->cycle_count);
  printf("[UD%d-L%d] InstructionCount     =%lu\n",ud_id, lane_num, lnstats->inst_count); 
  printf("[UD%d-L%d] TransitionCount      =%lu\n",ud_id, lane_num, lnstats->tran_count);
  printf("[UD%d-L%d] ThreadCount          =%lu\n",ud_id, lane_num, lnstats->thread_count);
  printf("[UD%d-L%d] AtomicInstructions   =%lu\n",ud_id, lane_num, lnstats->inst_count_atomic);
  printf("[UD%d-L%d] BitWiseInstructions  =%lu\n",ud_id, lane_num, lnstats->inst_count_bitwise);
  printf("[UD%d-L%d] CtrlFlowInstructions =%lu\n",ud_id, lane_num, lnstats->inst_count_ctrlflow);
  printf("[UD%d-L%d] DataMovInstructions  =%lu\n",ud_id, lane_num, lnstats->inst_count_datmov);
  printf("[UD%d-L%d] EvInstructions       =%lu\n",ud_id, lane_num, lnstats->inst_count_ev);
  printf("[UD%d-L%d] FPArithInstructions  =%lu\n",ud_id, lane_num, lnstats->inst_count_fparith);
  printf("[UD%d-L%d] HashInstructions     =%lu\n",ud_id, lane_num, lnstats->inst_count_hash);
  printf("[UD%d-L%d] IntArithInstructions =%lu\n",ud_id, lane_num, lnstats->inst_count_intarith);
  printf("[UD%d-L%d] IntCompInstructions  =%lu\n",ud_id, lane_num, lnstats->inst_count_intcmp);
  printf("[UD%d-L%d] MsgInstructions      =%lu\n",ud_id, lane_num, lnstats->inst_count_msg);
  printf("[UD%d-L%d] MsgInstructions(Mem) =%lu\n",ud_id, lane_num, lnstats->inst_count_msg_mem);
  printf("[UD%d-L%d] MsgInstructions(Lane)=%lu\n",ud_id, lane_num, lnstats->inst_count_msg_lane);
  printf("[UD%d-L%d] ThrdCtrlInstructions =%lu\n",ud_id, lane_num, lnstats->inst_count_threadctrl);
  printf("[UD%d-L%d] TranCtrlInstructions =%lu\n",ud_id, lane_num, lnstats->inst_count_tranctrl);
  printf("[UD%d-L%d] VectorInstructions   =%lu\n",ud_id, lane_num, lnstats->inst_count_vec);
  printf("[UD%d-L%d] BasicTransitions     =%lu\n",ud_id, lane_num, lnstats->tran_count_basic);
  printf("[UD%d-L%d] MajorityTransitions  =%lu\n",ud_id, lane_num, lnstats->tran_count_majority);
  printf("[UD%d-L%d] DefaultTransitions   =%lu\n",ud_id, lane_num, lnstats->tran_count_default);
  printf("[UD%d-L%d] EpsilonTransitions   =%lu\n",ud_id, lane_num, lnstats->tran_count_epsilon);
  printf("[UD%d-L%d] CommonTransitions    =%lu\n",ud_id, lane_num, lnstats->tran_count_common);
  printf("[UD%d-L%d] FlaggedTransitions   =%lu\n",ud_id, lane_num, lnstats->tran_count_flagged);
  printf("[UD%d-L%d] RefillTransitions    =%lu\n",ud_id, lane_num, lnstats->tran_count_refill);
  printf("[UD%d-L%d] EventTransitions     =%lu\n",ud_id, lane_num, lnstats->tran_count_event);
#ifdef DETAIL_STATS
  printf("[UD%d-L%d] MaxInstCountPerEvent =%lu\n",ud_id, lane_num, lnstats->max_inst_per_event);
  printf("[UD%d-L%d] MaxInstCountPerTx    =%lu\n",ud_id, lane_num, lnstats->max_inst_per_tx);
#endif
  printf("[UD%d-L%d] LMLoadBytes          =%lu\n",ud_id, lane_num, lnstats->lm_load_bytes);
  printf("[UD%d-L%d] LMStoreBytes         =%lu\n",ud_id, lane_num, lnstats->lm_store_bytes);
  printf("[UD%d-L%d] LMLoadCount          =%lu\n",ud_id, lane_num, lnstats->lm_load_count);
  printf("[UD%d-L%d] LMStoreCount         =%lu\n",ud_id, lane_num, lnstats->lm_store_count);
  printf("[UD%d-L%d] DRAMLoadBytes        =%lu\n",ud_id, lane_num, lnstats->dram_load_bytes);
  printf("[UD%d-L%d] DRAMStoreBytes       =%lu\n",ud_id, lane_num, lnstats->dram_store_bytes);
  printf("[UD%d-L%d] DRAMLoadCount        =%lu\n",ud_id, lane_num, lnstats->dram_load_count);
  printf("[UD%d-L%d] DRAMStoreCount       =%lu\n",ud_id, lane_num, lnstats->dram_store_count);
  printf("[UD%d-L%d] MessageBytes         =%lu\n",ud_id, lane_num, lnstats->message_bytes);
  printf("[UD%d-L%d] EventQLenMax         =%lu\n",ud_id, lane_num, lnstats->eventq_len_max);
  printf("[UD%d-L%d] OperandQueueLenMax   =%lu\n",ud_id, lane_num, lnstats->opbuff_len_max);


  //for (int i = 0; i < 16; i++) {
  //  std::printf("[UD%d-L%d] user_counter%2d      = %*ld\n", ud_id, lane_num, i,
  //              wid, this->simStats[ud_id][lane_num].user_counter[i]);
  //}
}
#ifdef DETAIL_STATS
void BASimUDRuntime_t::print_histograms(uint32_t ud_id, uint8_t lane_num) {
  const basim::LaneStats* lnstats = uds[ud_id]->getLaneStats(lane_num);
  printf("[UD%d-L%d] Inst_Per_Event_Histogram   =[",ud_id, lane_num);
  uint64_t loc_count;
  for(int i = 0; i < MAX_BINS/BUCKET_SIZE; i++){
    loc_count = 0;
    for(int j = i * BUCKET_SIZE; j < (i + 1)*BUCKET_SIZE; j++)
      loc_count += lnstats->inst_per_event[j];
    if (loc_count == 0) {
      continue;
    }
    printf("%d:%lu, ", i*BUCKET_SIZE, loc_count);
  }
  printf("]\n");
  printf("[UD%d-L%d] LM_Count_Per_Event_Histogram   =[",ud_id, lane_num);
  for(int i = 0; i < MAX_COUNT_BINS/COUNT_BUCKET_SIZE; i++){
    loc_count = 0;
    for(int j = i * COUNT_BUCKET_SIZE; j < (i + 1)*COUNT_BUCKET_SIZE; j++)
      loc_count += lnstats->lm_load_count_per_event[j] + lnstats->lm_store_count_per_event[j];
    if (loc_count == 0) {
      continue;
    }
    printf("%d:%lu, ", i*COUNT_BUCKET_SIZE, loc_count);
  }
  printf("]\n");
  printf("[UD%d-L%d] LM_Bytes_Per_Event_Histogram   =[",ud_id, lane_num);
  for(int i = 0; i < MAX_BYTES_BINS/BYTES_BUCKET_SIZE; i++){
    loc_count = 0;
    for(int j = i * BYTES_BUCKET_SIZE; j < (i + 1)*BYTES_BUCKET_SIZE; j++)
      loc_count += lnstats->lm_load_bytes_per_event[j] + lnstats->lm_store_bytes_per_event[j];
    if (loc_count == 0) {
      continue;
    }
    printf("%d:%lu, ", i*BYTES_BUCKET_SIZE, loc_count);
  }
  printf("]\n");
  printf("[UD%d-L%d] DRAM_Count_Per_Event_Histogram   =[",ud_id, lane_num);
  for(int i = 0; i < MAX_COUNT_BINS/COUNT_BUCKET_SIZE; i++){
    loc_count = 0;
    for(int j = i * COUNT_BUCKET_SIZE; j < (i + 1)*COUNT_BUCKET_SIZE; j++)
      loc_count += lnstats->dram_load_count_per_event[j] + lnstats->dram_store_count_per_event[j];
    if (loc_count == 0) {
      continue;
    }
    printf("%d:%lu, ", i*COUNT_BUCKET_SIZE, loc_count);
  }
  printf("]\n");
  printf("[UD%d-L%d] DRAM_Bytes_Per_Event_Histogram   =[",ud_id, lane_num);
  for(int i = 0; i < MAX_BYTES_BINS/BYTES_BUCKET_SIZE; i++){
    loc_count = 0;
    for(int j = i * BYTES_BUCKET_SIZE; j < (i + 1)*BYTES_BUCKET_SIZE; j++)
      loc_count += lnstats->dram_load_bytes_per_event[j] + lnstats->dram_store_bytes_per_event[j];
    if (loc_count == 0) {
      continue;
    }
    printf("%d:%lu, ", i*BYTES_BUCKET_SIZE, loc_count);
  }
  printf("]\n");
}

void BASimUDRuntime_t::print_histograms(uint32_t nwid) {
  print_histograms(nwid/64, nwid%64);
}
#endif

BASimUDRuntime_t::~BASimUDRuntime_t() {
  // close perflog
  basim::globalLogs.perflog.close();
  // close tracelog
  basim::globalLogs.tracelog.close();

  // Delete the uds
  for (auto &ud : uds) {
    delete ud;
  }
  uds.clear();
}

} // namespace UpDown
