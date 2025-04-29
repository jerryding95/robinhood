#include "instructionmemory.hh"
#include "debug.hh"
#include "encodings.hh"
#include "fstream"
#include "inst_decode.hh"
#include "types.hh"
#include <cstdint>
#include <cstdio>
#include <cstdlib>

namespace basim {
/* Load Program into Instruction Memory*/
void InstructionMemory::loadProgBinary(std::string progfile) {
  Addr addr;
  uint64_t numinst;
  uint32_t insword;
  uint32_t numEventSymbols;
  uint64_t bytesread = 0;
  std::ifstream instream(progfile.c_str(), std::ifstream::binary);
  if (instream) {
    instream.seekg(0, instream.end);
    int length = instream.tellg();
    instream.seekg(0, instream.beg);

    /* LOAD HEADER */
    instream.read(reinterpret_cast<char *>(&binStartofEventSymbols), sizeof(binStartofEventSymbols));
    instream.read(reinterpret_cast<char *>(&binStartofProgram), sizeof(binStartofProgram));
    instream.read(reinterpret_cast<char *>(&binStartofData), sizeof(binStartofData));

    /* LOAD EVENT SYMBOL TABLE*/
    // skip, only used by Top runtime
    // instream.read(reinterpret_cast<char *>(&numEventSymbols), sizeof(numEventSymbols));

    /* LOAD INSTRUCTIONS */
    // Skip the symbols and head to the program
    instream.seekg(binStartofProgram, instream.beg);
    bytesread = binStartofProgram;
    while (bytesread < binStartofData) {
      // Addr (8), num_inst(8), trans(4), ins0(4), ins1(4)...
      instream.read(reinterpret_cast<char *>(&addr), sizeof(addr));
      bytesread += sizeof(addr);
      instream.read(reinterpret_cast<char *>(&numinst), sizeof(numinst));
      bytesread += sizeof(numinst);
      instream.read(reinterpret_cast<char *>(&insword), sizeof(insword));
      bytesread += sizeof(insword);
      EncInst binst = static_cast<EncInst>(insword);
      insts[addr] = binst;
      addr += 4;
      numinst--;
      for (int i = numinst; i > 0; i--) {
        instream.read(reinterpret_cast<char *>(&insword), sizeof(insword));
        EncInst binst = static_cast<EncInst>(insword);
        insts[addr] = binst;
        addr += 4;
        bytesread += sizeof(insword);
      }
    }

    /* LOAD DEBUG RODATA */
    // loading into separate debug rodata region
    instream.seekg(binStartofData, instream.beg);
    bytesread = binStartofData;
    addr = 0;
    while (bytesread < length) {
      instream.read(reinterpret_cast<char *>(&insword), sizeof(insword));
      uint32_t binst = static_cast<uint32_t>(insword);
      debug_rodata[addr] = binst;
      addr += 4;
      bytesread += sizeof(insword);
    }
  } else {
    BASIM_ERROR("Could not load binary: %s\n", progfile.c_str());
  }
  // dumpInstructionMemory();
}

} // namespace basim
