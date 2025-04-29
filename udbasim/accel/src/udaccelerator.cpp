#include "udaccelerator.hh"
#include "types.hh"
#include "lanetypes.hh"
#include <cstdint>

namespace basim
{   
    UDAccelerator::UDAccelerator(int _numLanes, uint32_t udid, int lmMode): numLanes(_numLanes), lmMode(lmMode){
        spd = new ScratchPad(numLanes);
        this->udid = udid;
        for(auto i = 0; i < _numLanes; i++){
            uint32_t nwid = (udid & 0XFFFFFFC0 ) | (i & 0x3F);
            UDLanePtr lane = new UDLane(nwid, spd);
            udLanes.push_back(lane);
        }
        this->udstats = new UDStats();
    }

    /*  Should reflect Boot sequence - setting up base addresses, translations etc.  */
    void UDAccelerator::initSetup(Addr _pgbase, std::string progfile, Addr _lmbase){
        scratchpadBase = _lmbase;
        scratchpadSize = SCRATCHPAD_SIZE;
        spd->setBase(_lmbase);
        // Initialize default Translation Memory
        transmem = new TranslationMemory(udid, 1, _lmbase);
        instmem = new InstructionMemory();
        instmem->loadProgBinary(progfile);
        BASIM_INFOMSG("Translation Memory %p initialized on updown %d\n", transmem, udid);
        // Initialize all the lanes - need to add perflog, logging file etc
        for(auto i = 0; i < numLanes; i++){
            udLanes[i]->initSetup(_pgbase, instmem, _lmbase, transmem, lmMode);
        }
    }
    
    void UDAccelerator::initSetup(Addr _pgbase, std::string progfile, Addr _lmbase, int _num_uds){
        scratchpadBase = _lmbase;
        scratchpadSize = SCRATCHPAD_SIZE;
        spd->setBase(_lmbase);
        // Initialize Translation Memory
        transmem = new TranslationMemory(udid, _num_uds, _lmbase);
        instmem = new InstructionMemory();
        instmem->loadProgBinary(progfile);
        BASIM_INFOMSG("Translation Memory %p initialized with %d updowns on updown %d\n", transmem, _num_uds, udid);
        // Initialize all the lanes - need to add perflog, logging file etc
        for(auto i = 0; i < numLanes; i++){
            udLanes[i]->initSetup(_pgbase, instmem, _lmbase, transmem, lmMode);
        }
    }

    size_t UDAccelerator::getEventQSize(int laneid){
        return (udLanes[laneid]->getEventQSize());
    }

    bool UDAccelerator::isIdle(){
        // Check idle condition on all lanes
        bool idle = true;
        for(auto i = 0; i < numLanes; i++){
            idle = idle && udLanes[i]->isIdle();
        }
        return idle;
    }

    bool UDAccelerator::isIdle(uint32_t laneID){
        return udLanes[laneID]->isIdle();
    }

    bool UDAccelerator::pushEventOperands(eventoperands_t eop, uint32_t laneid){
        bool result;
        #ifndef GEM5_MODE
            // if(laneid % 65 == 0) {
            //     #pragma omp critical(BARRIER65)
            //     {
            //         result = udLanes[laneid]->pushEventOperands(eop);
            //     }
            // } else if(laneid % 64 == 0) {
            //     #pragma omp critical(BARRIER64)
            //     {
            //         result = udLanes[laneid]->pushEventOperands(eop);
            //     }
            // } else if(laneid % 63 == 0) {
            //     #pragma omp critical(BARRIER63)
            //     {
            //         result = udLanes[laneid]->pushEventOperands(eop);
            //     }
            // } else if(laneid % 62 == 0) {
            //     #pragma omp critical(BARRIER62)
            //     {
            //         result = udLanes[laneid]->pushEventOperands(eop);
            //     }
            // } else if(laneid % 61 == 0) {
            //     #pragma omp critical(BARRIER61)
            //     {
            //         result = udLanes[laneid]->pushEventOperands(eop);
            //     }
            // } else if(laneid % 60 == 0) {
            //     #pragma omp critical(BARRIER60)
            //     {
            //         result = udLanes[laneid]->pushEventOperands(eop);
            //     }
            // } else if(laneid % 59 == 0) {
            //     #pragma omp critical(BARRIER59)
            //     {
            //         result = udLanes[laneid]->pushEventOperands(eop);
            //     }
            // } else if(laneid % 58 == 0) {
            //     #pragma omp critical(BARRIER58)
            //     {
            //         result = udLanes[laneid]->pushEventOperands(eop);
            //     }
            // } else if(laneid % 57 == 0) {
            //     #pragma omp critical(BARRIER57)
            //     {
            //         result = udLanes[laneid]->pushEventOperands(eop);
            //     }
            // } else if(laneid % 56 == 0) {
            //     #pragma omp critical(BARRIER56)
            //     {
            //         result = udLanes[laneid]->pushEventOperands(eop);
            //     }
            // } else if(laneid % 55 == 0) {
            //     #pragma omp critical(BARRIER55)
            //     {
            //         result = udLanes[laneid]->pushEventOperands(eop);
            //     }
            // } else if(laneid % 54 == 0) {
            //     #pragma omp critical(BARRIER54)
            //     {
            //         result = udLanes[laneid]->pushEventOperands(eop);
            //     }
            // } else if(laneid % 53 == 0) {
            //     #pragma omp critical(BARRIER53)
            //     {
            //         result = udLanes[laneid]->pushEventOperands(eop);
            //     }
            // } else if(laneid % 52 == 0) {
            //     #pragma omp critical(BARRIER52)
            //     {
            //         result = udLanes[laneid]->pushEventOperands(eop);
            //     }
            // } else if(laneid % 51 == 0) {
            //     #pragma omp critical(BARRIER51)
            //     {
            //         result = udLanes[laneid]->pushEventOperands(eop);
            //     }
            // } else if(laneid % 50 == 0) {
            //     #pragma omp critical(BARRIER50)
            //     {
            //         result = udLanes[laneid]->pushEventOperands(eop);
            //     }
            // } else if(laneid % 49 == 0) {
            //     #pragma omp critical(BARRIER49)
            //     {
            //         result = udLanes[laneid]->pushEventOperands(eop);
            //     }
            // } else if(laneid % 48 == 0) {
            //     #pragma omp critical(BARRIER48)
            //     {
            //         result = udLanes[laneid]->pushEventOperands(eop);
            //     }
            // } else if(laneid % 47 == 0) {
            //     #pragma omp critical(BARRIER47)
            //     {
            //         result = udLanes[laneid]->pushEventOperands(eop);
            //     }
            // } else if(laneid % 46 == 0) {
            //     #pragma omp critical(BARRIER46)
            //     {
            //         result = udLanes[laneid]->pushEventOperands(eop);
            //     }
            // } else if(laneid % 45 == 0) {
            //     #pragma omp critical(BARRIER45)
            //     {
            //         result = udLanes[laneid]->pushEventOperands(eop);
            //     }
            // } else if(laneid % 44 == 0) {
            //     #pragma omp critical(BARRIER44)
            //     {
            //         result = udLanes[laneid]->pushEventOperands(eop);
            //     }
            // } else if(laneid % 43 == 0) {
            //     #pragma omp critical(BARRIER43)
            //     {
            //         result = udLanes[laneid]->pushEventOperands(eop);
            //     }
            // } else if(laneid % 42 == 0) {
            //     #pragma omp critical(BARRIER42)
            //     {
            //         result = udLanes[laneid]->pushEventOperands(eop);
            //     }
            // } else if(laneid % 41 == 0) {
            //     #pragma omp critical(BARRIER41)
            //     {
            //         result = udLanes[laneid]->pushEventOperands(eop);
            //     }
            // } else if(laneid % 40 == 0) {
            //     #pragma omp critical(BARRIER40)
            //     {
            //         result = udLanes[laneid]->pushEventOperands(eop);
            //     }
            // } else if(laneid % 39 == 0) {
            //     #pragma omp critical(BARRIER39)
            //     {
            //         result = udLanes[laneid]->pushEventOperands(eop);
            //     }
            // } else if(laneid % 38 == 0) {
            //     #pragma omp critical(BARRIER38)
            //     {
            //         result = udLanes[laneid]->pushEventOperands(eop);
            //     }
            // } else if(laneid % 37 == 0) {
            //     #pragma omp critical(BARRIER37)
            //     {
            //         result = udLanes[laneid]->pushEventOperands(eop);
            //     }
            // } else if(laneid % 36 == 0) {
            //     #pragma omp critical(BARRIER36)
            //     {
            //         result = udLanes[laneid]->pushEventOperands(eop);
            //     }
            // } else if(laneid % 35 == 0) {
            //     #pragma omp critical(BARRIER35)
            //     {
            //         result = udLanes[laneid]->pushEventOperands(eop);
            //     }
            // } else if(laneid % 34 == 0) {
            //     #pragma omp critical(BARRIER34)
            //     {
            //         result = udLanes[laneid]->pushEventOperands(eop);
            //     }
            // } else if(laneid % 33 == 0) {
            //     #pragma omp critical(BARRIER33)
            //     {
            //         result = udLanes[laneid]->pushEventOperands(eop);
            //     }
            // } else if(laneid % 32 == 0) {
            //     #pragma omp critical(BARRIER32)
            //     {
            //         result = udLanes[laneid]->pushEventOperands(eop);
            //     }
            // } else if(laneid % 31 == 0) {
            //     #pragma omp critical(BARRIER31)
            //     {
            //         result = udLanes[laneid]->pushEventOperands(eop);
            //     }
            // } else if(laneid % 30 == 0) {
            //     #pragma omp critical(BARRIER30)
            //     {
            //         result = udLanes[laneid]->pushEventOperands(eop);
            //     }
            // } else if(laneid % 29 == 0) {
            //     #pragma omp critical(BARRIER29)
            //     {
            //         result = udLanes[laneid]->pushEventOperands(eop);
            //     }
            // } else if(laneid % 28 == 0) {
            //     #pragma omp critical(BARRIER28)
            //     {
            //         result = udLanes[laneid]->pushEventOperands(eop);
            //     }
            // } else if(laneid % 27 == 0) {
            //     #pragma omp critical(BARRIER27)
            //     {
            //         result = udLanes[laneid]->pushEventOperands(eop);
            //     }
            // } else if(laneid % 26 == 0) {
            //     #pragma omp critical(BARRIER26)
            //     {
            //         result = udLanes[laneid]->pushEventOperands(eop);
            //     }
            // } else if(laneid % 25 == 0) {
            //     #pragma omp critical(BARRIER25)
            //     {
            //         result = udLanes[laneid]->pushEventOperands(eop);
            //     }
            // } else if(laneid % 24 == 0) {
            //     #pragma omp critical(BARRIER24)
            //     {
            //         result = udLanes[laneid]->pushEventOperands(eop);
            //     }
            // } else if(laneid % 23 == 0) {
            //     #pragma omp critical(BARRIER23)
            //     {
            //         result = udLanes[laneid]->pushEventOperands(eop);
            //     }
            // } else if(laneid % 22 == 0) {
            //     #pragma omp critical(BARRIER22)
            //     {
            //         result = udLanes[laneid]->pushEventOperands(eop);
            //     }
            // } else if(laneid % 21 == 0) {
            //     #pragma omp critical(BARRIER21)
            //     {
            //         result = udLanes[laneid]->pushEventOperands(eop);
            //     }
            // } else if(laneid % 20 == 0) {
            //     #pragma omp critical(BARRIER20)
            //     {
            //         result = udLanes[laneid]->pushEventOperands(eop);
            //     }
            // } else if(laneid % 19 == 0) {
            //     #pragma omp critical(BARRIER19)
            //     {
            //         result = udLanes[laneid]->pushEventOperands(eop);
            //     }
            // } else if(laneid % 18 == 0) {
            //     #pragma omp critical(BARRIER18)
            //     {
            //         result = udLanes[laneid]->pushEventOperands(eop);
            //     }
            // } else if(laneid % 17 == 0) {
            //     #pragma omp critical(BARRIER17)
            //     {
            //         result = udLanes[laneid]->pushEventOperands(eop);
            //     }
            // } else if(laneid % 16 == 0) {
            //     #pragma omp critical(BARRIER16)
            //     {
            //         result = udLanes[laneid]->pushEventOperands(eop);
            //     }
            // } else if(laneid % 15 == 0) {
            //     #pragma omp critical(BARRIER15)
            //     {
            //         result = udLanes[laneid]->pushEventOperands(eop);
            //     }
            // } else if(laneid % 14 == 0) {
            //     #pragma omp critical(BARRIER14)
            //     {
            //         result = udLanes[laneid]->pushEventOperands(eop);
            //     }
            // } else if(laneid % 13 == 0) {
            //     #pragma omp critical(BARRIER13)
            //     {
            //         result = udLanes[laneid]->pushEventOperands(eop);
            //     }
            // } else if(laneid % 12 == 0) {
            //     #pragma omp critical(BARRIER12)
            //     {
            //         result = udLanes[laneid]->pushEventOperands(eop);
            //     }
            // } else if(laneid % 11 == 0) {
            //     #pragma omp critical(BARRIER11)
            //     {
            //         result = udLanes[laneid]->pushEventOperands(eop);
            //     }
            // } else if(laneid % 10 == 0) {
            //     #pragma omp critical(BARRIER10)
            //     {
            //         result = udLanes[laneid]->pushEventOperands(eop);
            //     }
            // } else if(laneid % 9 == 0) {
            //     #pragma omp critical(BARRIER9)
            //     {
            //         result = udLanes[laneid]->pushEventOperands(eop);
            //     }
            // } else if(laneid % 8 == 0) {
            //     #pragma omp critical(BARRIER8)
            //     {
            //         result = udLanes[laneid]->pushEventOperands(eop);
            //     }
            // } else if(laneid % 7 == 0) {
            //     #pragma omp critical(BARRIER7)
            //     {
            //         result = udLanes[laneid]->pushEventOperands(eop);
            //     }
            // } else if(laneid % 6 == 0) {
            //     #pragma omp critical(BARRIER6)
            //     {
            //         result = udLanes[laneid]->pushEventOperands(eop);
            //     }
            // } else if(laneid % 5 == 0) {
            //     #pragma omp critical(BARRIER5)
            //     {
            //         result = udLanes[laneid]->pushEventOperands(eop);
            //     }
            // } else if(laneid % 4 == 0) {
            //     #pragma omp critical(BARRIER4)
            //     {
            //         result = udLanes[laneid]->pushEventOperands(eop);
            //     }
            // } else if(laneid % 3 == 0) {
            //     #pragma omp critical(BARRIER3)
            //     {
            //         result = udLanes[laneid]->pushEventOperands(eop);
            //     }
            // } else if(laneid % 2 == 0) {
            //     #pragma omp critical(BARRIER2)
            //     {
            //         result = udLanes[laneid]->pushEventOperands(eop);
            //     }
            // } else {
            //     #pragma omp critical(BARRIER1)
            //     {
            //         result = udLanes[laneid]->pushEventOperands(eop);
            //     }
            // }
            result = udLanes[laneid]->pushEventOperands(eop);
        #else
            result = udLanes[laneid]->pushEventOperands(eop);
        #endif
        if(!(result)) {
           BASIM_ERROR("Push into UD:%d Lane:%d EventQ failed\n", udid, laneid);
        }
        return true;
    }
    
    /* write data into the scratchpad */
    void UDAccelerator::writeScratchPad(int size, Addr addr, uint8_t* data){
        // implement this for all data sizes before release
        spd->writeBytes(size, addr, data);
    }
    
    /* read data from the scratchpad */
    //word_t UDAccelerator::readScratchPad(Addr addr){
    void UDAccelerator::readScratchPad(int size, Addr addr, uint8_t* data){
        //int laneid = (addr - scratchpadBase) / SCRATCHPAD_SIZE;
        // @todo implement all other sizes
        spd->readBytes(size, addr, data);
    }

    void UDAccelerator::readScratchPadBank(uint8_t laneid, uint8_t* data){
        spd->readScratchpadBank(laneid, data);
    }
    
    /* Pointer to all scratchpad data */
    void UDAccelerator::readAllScratchPad(uint8_t* data){
        spd->readAllScratchpad(data);
    }

    void UDAccelerator::writeScratchPadBank(uint8_t laneid, const uint8_t* data){
        spd->writeScratchpadBank(laneid, data);
    }
  
    /* Pointer to all scratchpad data */
    void UDAccelerator::writeAllScratchPad(const uint8_t* data){
        spd->writeAllScratchpad(data);
    }

    void UDAccelerator::tick(uint64_t timestamp){
        // iterate through the vector of lanes
        for(auto ln = udLanes.begin(); ln != udLanes.end(); ++ln){
            (*ln)->tick(timestamp);
        }
    }
    
    bool UDAccelerator::sendReady(uint32_t laneid){
        return udLanes[laneid]->sendReady();
    }

    std::unique_ptr<MMessage> UDAccelerator::getSendMessage(int laneid){
        return udLanes[laneid]->peekSendBuffer();
    }
    
    void UDAccelerator::removeSendMessage(int laneid){
        return udLanes[laneid]->popSendBuffer();
    }

    /* simulate API for accelerator runs through all lanes */
    void UDAccelerator::simulate(uint64_t numTicks, uint64_t timestamp){
        int simTicks = 0;
        while(simTicks < numTicks){
            for(auto ln = udLanes.begin(); ln != udLanes.end(); ++ln){
                if(!(*ln)->isIdle())
                    (*ln)->tick(timestamp);
            }
            simTicks++;
        }

    }

    int UDAccelerator::getLanebyPolicy(int laneid, uint8_t policy){
        if(policy == 0){
          return laneid;
        }
        int start_ln = 0;
        int end_ln = 63;
        int ln_choose = laneid;
        int q_size;
        switch(policy){
            case 1:
                start_ln = 0;
                end_ln = 64;
                q_size = MAX_Q_SIZE;
            break;
            case 2:
                start_ln = 0;
                end_ln = 32;
                q_size = MAX_Q_SIZE;
            break;
            case 3:
                start_ln = 32;
                end_ln = 64;
                q_size = MAX_Q_SIZE;
            break;
            case 4:
                start_ln = 0;
                end_ln = 32;
                q_size = 0;
            break;
            case 5:
                start_ln = 32;
                end_ln = 64;
                q_size = 0;
            break;
            case 6:
                start_ln = 0;
                end_ln = 64;
                q_size = 0;
            break;
            default:
                return laneid;
            break;
        }
        if(policy < 4){
            for(int ln = start_ln; ln < end_ln; ln++){
                if(udLanes[ln]->getEventQSize() == 0){
                    ln_choose = ln;
                    break;
                }
                if(udLanes[ln]->getEventQSize() < q_size){
                    q_size = udLanes[ln]->getEventQSize();
                    ln_choose = ln;
                }
            }
        }else{
            for(int ln = start_ln; ln < end_ln; ln++){
                if(udLanes[ln]->getEventQSize() > q_size){
                    q_size = udLanes[ln]->getEventQSize();
                    ln_choose = ln;
                }
            }
        }
        return ln_choose;
    }
    
    /* Simulate API to call per lane */
    void UDAccelerator::simulate(uint32_t laneID, uint64_t numTicks, uint64_t timestamp){
        int simTicks = 0;
        while(simTicks < numTicks){
            udLanes[laneID]->tick(timestamp);
            simTicks++;
        }
    }

    void UDAccelerator::resetStats(){
        for (auto &ln :udLanes){
            ln->resetStats();
        }
    }

    UDAccelerator::~UDAccelerator(){
      for (auto &ln : udLanes) {
        delete ln;
      }
      delete spd;
      delete udstats;
      delete transmem;
      delete instmem;
    }
    
}//basim
