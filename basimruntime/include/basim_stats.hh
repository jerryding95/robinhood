#ifndef BASIM_STATS_HH
#define BASIM_STATS_HH

struct BASimStats {
  uint64_t cycle_count;
  uint64_t inst_count; 
  uint64_t tran_count;
  uint64_t thread_count;
  uint64_t inst_count_atomic;
  uint64_t inst_count_bitwise;
  uint64_t inst_count_ctrlflow;
  uint64_t inst_count_datmov;
  uint64_t inst_count_ev;
  uint64_t inst_count_fparith;
  uint64_t inst_count_hash;
  uint64_t inst_count_intarith;
  uint64_t inst_count_intcmp;
  uint64_t inst_count_msg;
  uint64_t inst_count_msg_mem;
  uint64_t inst_count_msg_lane;
  uint64_t inst_count_threadctrl;
  uint64_t inst_count_tranctrl;
  uint64_t inst_count_vec;
  uint64_t tran_count_basic;
  uint64_t tran_count_majority;
  uint64_t tran_count_default;
  uint64_t tran_count_epsilon;
  uint64_t tran_count_common;
  uint64_t tran_count_flagged;
  uint64_t tran_count_refill;
  uint64_t tran_count_event;
  uint64_t max_inst_count_per_event;
  uint64_t max_inst_count_per_tx;
  uint64_t lm_load_bytes;
  uint64_t lm_store_bytes;
  uint64_t lm_load_count;
  uint64_t lm_store_count;
  uint64_t dram_load_bytes;
  uint64_t dram_store_bytes;
  uint64_t dram_load_count;
  uint64_t dram_store_count;
  uint64_t message_bytes;
  uint64_t eventq_len_max;
  uint64_t opbuff_len_max;
  double event_queue_mean;
  uint64_t operand_queue_max;
  double operand_queue_mean;
  uint64_t user_counter[16];
};

#endif // SIM_STATS_HH
