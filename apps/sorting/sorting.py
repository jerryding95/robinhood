from linker.EFAProgram import efaProgram

## Global constants

@efaProgram
def EFA_sorting(efa):
  efa.code_level = 'machine'
  state0 = efa.State("udweave_init") #Only one state code 
  efa.add_initId(state0.state_id)
  ## Static declarations
  ## Scoped Variable "tot" uses Register X16, scope (0)
  ## Scoped Variable "cur" uses Register X17, scope (0)
  ## Scoped Variable "offset_buffer" uses Register X18, scope (0)
  ## Scoped Variable "offset_vec" uses Register X19, scope (0)
  ## Param "list_addr" uses Register X8, scope (0->50)
  ## Param "list_size" uses Register X9, scope (0->50)
  ## Param "num_lanes" uses Register X10, scope (0->50)
  ## Param "offset_buffer_in" uses Register X11, scope (0->50)
  ## Param "offset_vec_in" uses Register X12, scope (0->50)
  ## Scoped Variable "sp_ptr" uses Register X20, scope (0->50)
  ## Scoped Variable "vec_ptr" uses Register X21, scope (0->50)
  ## Scoped Variable "cur_addr" uses Register X22, scope (0->50)
  ## Scoped Variable "cur_size" uses Register X23, scope (0->50)
  ## Scoped Variable "ev_word" uses Register X24, scope (0->50)
  ## Scoped Variable "evword" uses Register X20, scope (0->53->55)
  ## Scoped Variable "vec_ptr" uses Register X20, scope (0->53->56)
  ## Scoped Variable "nvals" uses Register X21, scope (0->53->56)
  ## Scoped Variable "n_lanes" uses Register X22, scope (0->53->56)
  ## Scoped Variable "evword" uses Register X23, scope (0->53->56)
  ## Scoped Variable "label" uses Register X24, scope (0->53->56)
  ## Scoped Variable "cont_word" uses Register X25, scope (0->53->56)
  ## Scoped Variable "sp_ptr" uses Register X26, scope (0->53->56)
  ## Scoped Variable "evword" uses Register X20, scope (0->61->63)
  ## Scoped Variable "vec_ptr" uses Register X20, scope (0->61->64)
  ## Scoped Variable "n_lanes" uses Register X21, scope (0->61->64)
  ## Scoped Variable "evword" uses Register X22, scope (0->61->64)
  ## Scoped Variable "label" uses Register X23, scope (0->61->64)
  ## Scoped Variable "cont_word" uses Register X24, scope (0->61->64)
  ## Scoped Variable "sp_ptr" uses Register X25, scope (0->61->64)
  ## Scoped Variable "cnt" uses Register X16, scope (0)
  ## Scoped Variable "offset" uses Register X17, scope (0)
  ## Scoped Variable "cur_idx" uses Register X18, scope (0)
  ## Scoped Variable "curaddr" uses Register X19, scope (0)
  ## Scoped Variable "tot" uses Register X20, scope (0)
  ## Scoped Variable "curto" uses Register X21, scope (0)
  ## Param "src" uses Register X8, scope (0->68)
  ## Param "dst" uses Register X9, scope (0->68)
  ## Param "size_in" uses Register X10, scope (0->68)
  ## Scoped Variable "evw" uses Register X22, scope (0->68)
  ## Scoped Variable "sp_ptr" uses Register X22, scope (0->71)
  ## Scoped Variable "out_cnt" uses Register X23, scope (0->71)
  ## Scoped Variable "addr" uses Register X24, scope (0->71->73)
  ## Scoped Variable "evw" uses Register X24, scope (0->71->78)
  ## Param "val" uses Register X8, scope (0->79)
  ## Param "addr" uses Register X9, scope (0->79)
  ## Scoped Variable "sp_ptr" uses Register X22, scope (0->79)
  ## Scoped Variable "lm_ptr" uses Register X23, scope (0->79)
  ## Param "op1" uses Register X8, scope (0->82)
  ## Param "op2" uses Register X9, scope (0->82)
  ## Param "op3" uses Register X10, scope (0->82)
  ## Param "op4" uses Register X11, scope (0->82)
  ## Param "op5" uses Register X12, scope (0->82)
  ## Param "op6" uses Register X13, scope (0->82)
  ## Param "op7" uses Register X14, scope (0->82)
  ## Param "op8" uses Register X15, scope (0->82)
  ## Param "addr" uses Register X3, scope (0->82)
  ## Scoped Variable "sp_ptr" uses Register X22, scope (0->82)
  ## Scoped Variable "lm_ptr" uses Register X23, scope (0->82)
  ## Param "src" uses Register X8, scope (0->85)
  ## Param "dst" uses Register X9, scope (0->85)
  ## Param "size_in" uses Register X10, scope (0->85)
  ## Scoped Variable "evw" uses Register X22, scope (0->85)
  ## Scoped Variable "sp_ptr" uses Register X22, scope (0->88)
  ## Scoped Variable "out_cnt" uses Register X23, scope (0->88)
  ## Scoped Variable "addr" uses Register X24, scope (0->88->90)
  ## Scoped Variable "addrto" uses Register X25, scope (0->88->90)
  ## Scoped Variable "evw" uses Register X24, scope (0->88->95)
  ## Scoped Variable "sp_ptr" uses Register X22, scope (0->96)
  ## Scoped Variable "sp_ptr" uses Register X22, scope (0->99)
  ## Param "src" uses Register X8, scope (0->102)
  ## Param "dst" uses Register X9, scope (0->102)
  ## Param "size_in" uses Register X10, scope (0->102)
  ## Scoped Variable "evw" uses Register X22, scope (0->102)
  ## Scoped Variable "sp_ptr" uses Register X22, scope (0->103)
  ## Scoped Variable "out_cnt" uses Register X23, scope (0->103)
  ## Scoped Variable "addr" uses Register X24, scope (0->103->105)
  ## Scoped Variable "evw" uses Register X24, scope (0->103->110)
  ## Param "val" uses Register X8, scope (0->111)
  ## Param "addr" uses Register X9, scope (0->111)
  ## Scoped Variable "to_ptr" uses Register X22, scope (0->111)
  ## Param "op1" uses Register X8, scope (0->112)
  ## Param "op2" uses Register X9, scope (0->112)
  ## Param "op3" uses Register X10, scope (0->112)
  ## Param "op4" uses Register X11, scope (0->112)
  ## Param "op5" uses Register X12, scope (0->112)
  ## Param "op6" uses Register X13, scope (0->112)
  ## Param "op7" uses Register X14, scope (0->112)
  ## Param "op8" uses Register X15, scope (0->112)
  ## Param "addr" uses Register X3, scope (0->112)
  ## Scoped Variable "to_ptr" uses Register X22, scope (0->112)
  ## Scoped Variable "sp_ptr" uses Register X22, scope (0->113)
  ## Scoped Variable "sp_ptr" uses Register X22, scope (0->116)
  ## Scoped Variable "cnt" uses Register X16, scope (0)
  ## Scoped Variable "offset" uses Register X17, scope (0)
  ## Param "src" uses Register X8, scope (0->120)
  ## Param "dst" uses Register X9, scope (0->120)
  ## Param "size" uses Register X10, scope (0->120)
  ## Scoped Variable "cur_addr" uses Register X18, scope (0->120)
  ## Param "val" uses Register X8, scope (0->124)
  ## Param "addr" uses Register X9, scope (0->124)
  ## Scoped Variable "lm_ptr" uses Register X18, scope (0->124)
  ## Param "op1" uses Register X8, scope (0->127)
  ## Param "op2" uses Register X9, scope (0->127)
  ## Param "op3" uses Register X10, scope (0->127)
  ## Param "op4" uses Register X11, scope (0->127)
  ## Param "op5" uses Register X12, scope (0->127)
  ## Param "op6" uses Register X13, scope (0->127)
  ## Param "op7" uses Register X14, scope (0->127)
  ## Param "op8" uses Register X15, scope (0->127)
  ## Param "addr" uses Register X3, scope (0->127)
  ## Scoped Variable "lm_ptr" uses Register X18, scope (0->127)
  ## Param "src" uses Register X8, scope (0->130)
  ## Param "dst" uses Register X9, scope (0->130)
  ## Param "size" uses Register X10, scope (0->130)
  ## Scoped Variable "cur_src" uses Register X18, scope (0->130)
  ## Scoped Variable "cur_dst" uses Register X19, scope (0->130)
  ## Param "src" uses Register X8, scope (0->140)
  ## Param "dst" uses Register X9, scope (0->140)
  ## Param "size" uses Register X10, scope (0->140)
  ## Scoped Variable "cur_addr" uses Register X18, scope (0->140)
  ## Param "val" uses Register X8, scope (0->144)
  ## Param "addr" uses Register X9, scope (0->144)
  ## Scoped Variable "to_ptr" uses Register X18, scope (0->144)
  ## Param "op1" uses Register X8, scope (0->145)
  ## Param "op2" uses Register X9, scope (0->145)
  ## Param "op3" uses Register X10, scope (0->145)
  ## Param "op4" uses Register X11, scope (0->145)
  ## Param "op5" uses Register X12, scope (0->145)
  ## Param "op6" uses Register X13, scope (0->145)
  ## Param "op7" uses Register X14, scope (0->145)
  ## Param "op8" uses Register X15, scope (0->145)
  ## Param "addr" uses Register X3, scope (0->145)
  ## Scoped Variable "to_ptr" uses Register X18, scope (0->145)
  ## Scoped Variable "list_dram_addr" uses Register X16, scope (0)
  ## Scoped Variable "sp_ptr" uses Register X17, scope (0)
  ## Scoped Variable "list_size" uses Register X18, scope (0)
  ## Scoped Variable "sp_size" uses Register X19, scope (0)
  ## Scoped Variable "cur_idx" uses Register X20, scope (0)
  ## Scoped Variable "save_cont" uses Register X21, scope (0)
  ## Scoped Variable "cur_block_size" uses Register X22, scope (0)
  ## Param "list_dram_addr_in" uses Register X8, scope (0->153)
  ## Param "size_in" uses Register X9, scope (0->153)
  ## Param "sp_ptr_in" uses Register X10, scope (0->153)
  ## Param "sp_size_in" uses Register X11, scope (0->153)
  ## Scoped Variable "evw" uses Register X23, scope (0->153)
  ## Scoped Variable "evw" uses Register X23, scope (0->154)
  ## Scoped Variable "l" uses Register X23, scope (0->155->157)
  ## Scoped Variable "r" uses Register X24, scope (0->155->157)
  ## Scoped Variable "ptr" uses Register X25, scope (0->155->157)
  ## Scoped Variable "evw" uses Register X26, scope (0->155->157)
  ## Scoped Variable "evw" uses Register X23, scope (0->155->160)
  ## Scoped Variable "i" uses Register X23, scope (0->161)
  ## Scoped Variable "local_sp_ptr" uses Register X24, scope (0->161)
  ## Scoped Variable "evw" uses Register X25, scope (0->161)
  ## Scoped Variable "evw" uses Register X23, scope (0->165->167)
  ## Scoped Variable "evw" uses Register X23, scope (0->169->171)
  ## Scoped Variable "send_ptr" uses Register X24, scope (0->169->171)
  ## Scoped Variable "last" uses Register X25, scope (0->169->171)
  ## Scoped Variable "evw" uses Register X23, scope (0->169->174)
  ## Scoped Variable "c0" uses Register X16, scope (0)
  ## Scoped Variable "e0" uses Register X17, scope (0)
  ## Scoped Variable "c1" uses Register X18, scope (0)
  ## Scoped Variable "e1" uses Register X19, scope (0)
  ## Scoped Variable "tot" uses Register X20, scope (0)
  ## Scoped Variable "sp_ptr0" uses Register X21, scope (0)
  ## Scoped Variable "sp_ptr1" uses Register X22, scope (0)
  ## Scoped Variable "k" uses Register X23, scope (0)
  ## Scoped Variable "tmp_addr" uses Register X24, scope (0)
  ## Scoped Variable "cnt" uses Register X25, scope (0)
  ## Scoped Variable "nwait" uses Register X26, scope (0)
  ## Param "p0" uses Register X8, scope (0->176)
  ## Param "p1" uses Register X9, scope (0->176)
  ## Param "p2" uses Register X10, scope (0->176)
  ## Param "sp_ptr_in" uses Register X11, scope (0->176)
  ## Param "sp_size" uses Register X12, scope (0->176)
  ## Param "tmp_addr_in" uses Register X13, scope (0->176)
  ## Scoped Variable "cur_addr" uses Register X27, scope (0->176)
  ## Scoped Variable "lim" uses Register X28, scope (0->176)
  ## Scoped Variable "i" uses Register X28, scope (0->176->177)
  ## Scoped Variable "i" uses Register X29, scope (0->176->182)
  ## Param "val" uses Register X8, scope (0->185)
  ## Param "addr" uses Register X9, scope (0->185)
  ## Scoped Variable "gotcha" uses Register X27, scope (0->185)
  ## Scoped Variable "evw" uses Register X28, scope (0->185->191)
  ## Param "val" uses Register X8, scope (0->194)
  ## Param "addr" uses Register X9, scope (0->194)
  ## Scoped Variable "gotcha" uses Register X27, scope (0->194)
  ## Scoped Variable "evw" uses Register X28, scope (0->194->200)
  ## Scoped Variable "val0" uses Register X27, scope (0->203)
  ## Scoped Variable "val1" uses Register X28, scope (0->203)
  ## Scoped Variable "cur_addr" uses Register X29, scope (0->203->222->224)
  ## Scoped Variable "cur_addr" uses Register X29, scope (0->203->225->227)
  ## Scoped Variable "evw" uses Register X29, scope (0->203->229)
  ## Scoped Variable "evw" uses Register X27, scope (0->230->232)
  ## Scoped Variable "tot_bytes" uses Register X27, scope (0->233)
  ## Scoped Variable "cur_addr" uses Register X28, scope (0->233)
  ## Scoped Variable "evw" uses Register X29, scope (0->233)
  ## Param "val" uses Register X8, scope (0->234)
  ## Param "addr" uses Register X9, scope (0->234)
  ## Scoped Variable "next_addr" uses Register X27, scope (0->234)
  ## Scoped Variable "bid" uses Register X16, scope (0)
  ## Scoped Variable "offset" uses Register X17, scope (0)
  ## Scoped Variable "offset_buffer" uses Register X18, scope (0)
  ## Scoped Variable "has" uses Register X19, scope (0)
  ## Scoped Variable "tot" uses Register X20, scope (0)
  ## Scoped Variable "addr1" uses Register X21, scope (0)
  ## Scoped Variable "addr2" uses Register X22, scope (0)
  ## Scoped Variable "size1" uses Register X23, scope (0)
  ## Scoped Variable "size2" uses Register X24, scope (0)
  ## Param "base_lane_in" uses Register X8, scope (0->239)
  ## Param "addr1_in" uses Register X9, scope (0->239)
  ## Param "size1_in" uses Register X10, scope (0->239)
  ## Param "addr2_in" uses Register X11, scope (0->239)
  ## Param "size2_in" uses Register X12, scope (0->239)
  ## Param "offset_buffer_in" uses Register X13, scope (0->239)
  ## Scoped Variable "st" uses Register X25, scope (0->239)
  ## Scoped Variable "ed" uses Register X26, scope (0->239)
  ## Scoped Variable "ptr" uses Register X27, scope (0->239)
  ## Scoped Variable "evw" uses Register X28, scope (0->239)
  ## Scoped Variable "sp_ptr" uses Register X25, scope (0->242->244)
  ## Scoped Variable "i" uses Register X26, scope (0->242->244)
  ## Scoped Variable "ptr" uses Register X27, scope (0->242->244)
  ## Scoped Variable "sum" uses Register X28, scope (0->242->244)
  ## Param "base_lane_in" uses Register X8, scope (0->253)
  ## Param "addr1_in" uses Register X9, scope (0->253)
  ## Param "size1_in" uses Register X10, scope (0->253)
  ## Param "addr2_in" uses Register X11, scope (0->253)
  ## Param "size2_in" uses Register X12, scope (0->253)
  ## Param "offset_buffer_in" uses Register X13, scope (0->253)
  ## Scoped Variable "st" uses Register X25, scope (0->253)
  ## Scoped Variable "ed" uses Register X26, scope (0->253)
  ## Scoped Variable "ptr" uses Register X27, scope (0->253)
  ## Scoped Variable "evw" uses Register X28, scope (0->253)
  ## Param "key" uses Register X8, scope (0->256)
  ## Param "addr" uses Register X9, scope (0->256)
  ## Scoped Variable "sp_ptr" uses Register X25, scope (0->256->260)
  ## Scoped Variable "i" uses Register X26, scope (0->256->260)
  ## Scoped Variable "ptr" uses Register X27, scope (0->256->260)
  ## Scoped Variable "res" uses Register X28, scope (0->256->260)
  ## Scoped Variable "user_cont" uses Register X16, scope (0)
  ## Param "sort_lm_offset" uses Register X8, scope (0->268)
  ## Param "list_size" uses Register X9, scope (0->268)
  ## Param "list_addr" uses Register X10, scope (0->268)
  ## Param "num_lanes" uses Register X11, scope (0->268)
  ## Param "tmp_addr" uses Register X12, scope (0->268)
  ## Param "num_bins" uses Register X13, scope (0->268)
  ## Param "lb_addr" uses Register X14, scope (0->268)
  ## Param "max_value" uses Register X15, scope (0->268)
  ## Scoped Variable "evword" uses Register X17, scope (0->268)
  ## Scoped Variable "label" uses Register X18, scope (0->268)
  ## Scoped Variable "cont_word" uses Register X19, scope (0->268)
  ## Scoped Variable "sp_ptr" uses Register X20, scope (0->268)
  ## Scoped Variable "sp_ptr" uses Register X17, scope (0->271)
  ## Scoped Variable "evw" uses Register X18, scope (0->271)
  ## Scoped Variable "cont" uses Register X19, scope (0->271)
  ## Scoped Variable "sendbuf_lm_ptr" uses Register X17, scope (0->272)
  ## Scoped Variable "sp_ptr" uses Register X18, scope (0->272)
  ## Scoped Variable "list_size" uses Register X19, scope (0->272)
  ## Scoped Variable "list_addr" uses Register X20, scope (0->272)
  ## Scoped Variable "nlanes" uses Register X21, scope (0->272)
  ## Scoped Variable "input_meta_ptr" uses Register X22, scope (0->272)
  ## Scoped Variable "lb_meta_ptr" uses Register X23, scope (0->272)
  ## Scoped Variable "evw" uses Register X24, scope (0->272)
  ## Scoped Variable "cont" uses Register X25, scope (0->272)
  ## Scoped Variable "sp_ptr" uses Register X17, scope (0->274)
  ## Scoped Variable "evw" uses Register X18, scope (0->274)
  ## Scoped Variable "cont" uses Register X19, scope (0->274)
  ## Scoped Variable "sendbuf_lm_ptr" uses Register X17, scope (0->275)
  ## Scoped Variable "sp_ptr" uses Register X18, scope (0->275)
  ## Scoped Variable "list_size" uses Register X19, scope (0->275)
  ## Scoped Variable "list_addr" uses Register X20, scope (0->275)
  ## Scoped Variable "nlanes" uses Register X21, scope (0->275)
  ## Scoped Variable "input_meta_ptr" uses Register X22, scope (0->275)
  ## Scoped Variable "lb_meta_ptr" uses Register X23, scope (0->275)
  ## Scoped Variable "evw" uses Register X25, scope (0->275)
  ## Scoped Variable "cont" uses Register X26, scope (0->275)
  ## Scoped Variable "evword" uses Register X17, scope (0->280)
  ## Scoped Variable "label" uses Register X18, scope (0->280)
  ## Scoped Variable "cont_word" uses Register X19, scope (0->280)
  ## Scoped Variable "sp_ptr" uses Register X20, scope (0->280)
  ## Scoped Variable "sort_ptr" uses Register X21, scope (0->280)
  ## Scoped Variable "sendbuf_lm_ptr" uses Register X17, scope (0->282)
  ## Scoped Variable "sp_ptr" uses Register X18, scope (0->282)
  ## Scoped Variable "list_size" uses Register X19, scope (0->282)
  ## Scoped Variable "list_addr" uses Register X20, scope (0->282)
  ## Scoped Variable "nlanes" uses Register X21, scope (0->282)
  ## Scoped Variable "input_meta_ptr" uses Register X22, scope (0->282)
  ## Scoped Variable "evw" uses Register X23, scope (0->282)
  ## Scoped Variable "cont" uses Register X24, scope (0->282)
  ## Scoped Variable "tot" uses Register X16, scope (0)
  ## Scoped Variable "tot2" uses Register X17, scope (0)
  ## Scoped Variable "offset" uses Register X18, scope (0)
  ## Param "list_size_base" uses Register X8, scope (0->286)
  ## Param "list_addr" uses Register X9, scope (0->286)
  ## Param "tmp_addr" uses Register X10, scope (0->286)
  ## Param "num_lanes_num_bins" uses Register X11, scope (0->286)
  ## Param "use_unique_max_value" uses Register X12, scope (0->286)
  ## Param "list_ptr" uses Register X13, scope (0->286)
  ## Scoped Variable "num_bins" uses Register X19, scope (0->286)
  ## Scoped Variable "num_lanes" uses Register X20, scope (0->286)
  ## Scoped Variable "bins_per_lane" uses Register X21, scope (0->286)
  ## Scoped Variable "sp_ptr" uses Register X22, scope (0->286->288)
  ## Scoped Variable "idx" uses Register X22, scope (0->286->290)
  ## Scoped Variable "rptr" uses Register X23, scope (0->286->290)
  ## Scoped Variable "ptr" uses Register X22, scope (0->286->295)
  ## Scoped Variable "dram_addr" uses Register X23, scope (0->286->295)
  ## Scoped Variable "lm_addr" uses Register X24, scope (0->286->295)
  ## Scoped Variable "evw" uses Register X25, scope (0->286->295)
  ## Scoped Variable "ptr" uses Register X19, scope (0->296)
  ## Scoped Variable "bins_per_lane" uses Register X20, scope (0->296)
  ## Scoped Variable "dram_addr" uses Register X21, scope (0->296)
  ## Scoped Variable "lm_addr" uses Register X22, scope (0->296)
  ## Scoped Variable "evw" uses Register X23, scope (0->296)
  ## Scoped Variable "cval" uses Register X16, scope (0)
  ## Scoped Variable "bin_idx" uses Register X17, scope (0)
  ## Param "key" uses Register X8, scope (0->301)
  ## Param "val" uses Register X9, scope (0->301)
  ## Scoped Variable "evw" uses Register X18, scope (0->301)
  ## Scoped Variable "ptr" uses Register X19, scope (0->301)
  ## Scoped Variable "ikey" uses Register X20, scope (0->301)
  ## Param "key" uses Register X8, scope (0->302)
  ## Param "value" uses Register X9, scope (0->302)
  ## Scoped Variable "ptr" uses Register X18, scope (0->302)
  ## Scoped Variable "evw" uses Register X19, scope (0->302)
  ## Scoped Variable "addone" uses Register X20, scope (0->302)
  ## Param "key" uses Register X8, scope (0->303)
  ## Param "local_bin_count" uses Register X9, scope (0->303)
  ## Scoped Variable "ptr" uses Register X18, scope (0->303)
  ## Scoped Variable "dram_block_size" uses Register X19, scope (0->303)
  ## Scoped Variable "dram_addr" uses Register X20, scope (0->303)
  ## Scoped Variable "cval" uses Register X16, scope (0)
  ## Scoped Variable "bin_idx" uses Register X17, scope (0)
  ## Scoped Variable "bin_size" uses Register X18, scope (0)
  ## Scoped Variable "bin_dram_addr" uses Register X19, scope (0)
  ## Scoped Variable "bin_sp_addr" uses Register X20, scope (0)
  ## Scoped Variable "save_cont" uses Register X21, scope (0)
  ## Param "key" uses Register X8, scope (0->305)
  ## Param "val" uses Register X9, scope (0->305)
  ## Scoped Variable "evw" uses Register X22, scope (0->305)
  ## Scoped Variable "ptr" uses Register X23, scope (0->305)
  ## Scoped Variable "ikey" uses Register X24, scope (0->305)
  ## Param "key" uses Register X8, scope (0->306)
  ## Param "value" uses Register X9, scope (0->306)
  ## Scoped Variable "ptr" uses Register X22, scope (0->306)
  ## Scoped Variable "evw" uses Register X23, scope (0->306)
  ## Scoped Variable "addone" uses Register X24, scope (0->306)
  ## Param "key" uses Register X8, scope (0->307)
  ## Param "local_bin_count" uses Register X9, scope (0->307)
  ## Scoped Variable "ptr" uses Register X22, scope (0->307)
  ## Scoped Variable "dram_block_size" uses Register X23, scope (0->307)
  ## Scoped Variable "tmp_bin_dram_addr" uses Register X24, scope (0->307)
  ## Scoped Variable "data_sp_ptr" uses Register X25, scope (0->307)
  ## Scoped Variable "evw" uses Register X26, scope (0->307)
  ## Scoped Variable "data_sp_ptr" uses Register X22, scope (0->308)
  ## Scoped Variable "evw" uses Register X23, scope (0->308)
  ## Scoped Variable "i" uses Register X23, scope (0->308->309)
  ## Scoped Variable "x" uses Register X24, scope (0->308->309->311->313)
  ## Scoped Variable "evw" uses Register X22, scope (0->314)
  ## Scoped Variable "cval" uses Register X16, scope (0)
  ## Scoped Variable "bin_idx" uses Register X17, scope (0)
  ## Scoped Variable "bin_size" uses Register X18, scope (0)
  ## Scoped Variable "bin_dram_addr" uses Register X19, scope (0)
  ## Scoped Variable "bin_sp_addr" uses Register X20, scope (0)
  ## Scoped Variable "save_cont" uses Register X21, scope (0)
  ## Param "key" uses Register X8, scope (0->316)
  ## Param "val" uses Register X9, scope (0->316)
  ## Scoped Variable "evw" uses Register X22, scope (0->316)
  ## Scoped Variable "ptr" uses Register X23, scope (0->316)
  ## Scoped Variable "ikey" uses Register X24, scope (0->316)
  ## Param "key" uses Register X8, scope (0->317)
  ## Param "value" uses Register X9, scope (0->317)
  ## Scoped Variable "ptr" uses Register X22, scope (0->317)
  ## Scoped Variable "evw" uses Register X23, scope (0->317)
  ## Scoped Variable "addone" uses Register X24, scope (0->317)
  ## Param "key" uses Register X8, scope (0->318)
  ## Param "local_bin_count" uses Register X9, scope (0->318)
  ## Scoped Variable "ptr" uses Register X22, scope (0->318)
  ## Scoped Variable "dram_block_size" uses Register X23, scope (0->318)
  ## Scoped Variable "tmp_bin_dram_addr" uses Register X24, scope (0->318)
  ## Scoped Variable "data_sp_ptr" uses Register X25, scope (0->318)
  ## Scoped Variable "evw" uses Register X26, scope (0->318)
  ## Scoped Variable "data_sp_ptr" uses Register X22, scope (0->319)
  ## Scoped Variable "evw" uses Register X23, scope (0->319)
  ## Scoped Variable "i" uses Register X23, scope (0->319->320)
  ## Scoped Variable "x" uses Register X24, scope (0->319->320->322->324)
  ## Scoped Variable "evw" uses Register X22, scope (0->325)
  ## Scoped Variable "tot" uses Register X16, scope (0)
  ## Scoped Variable "bin_size" uses Register X17, scope (0)
  ## Scoped Variable "bin_dram_addr" uses Register X18, scope (0)
  ## Scoped Variable "save_cont" uses Register X19, scope (0)
  ## Scoped Variable "offset" uses Register X20, scope (0)
  ## Scoped Variable "local_space_bit" uses Register X21, scope (0)
  ## Param "key" uses Register X8, scope (0->327)
  ## Param "val" uses Register X9, scope (0->327)
  ## Scoped Variable "evw" uses Register X22, scope (0->327)
  ## Scoped Variable "sptr" uses Register X23, scope (0->327)
  ## Scoped Variable "bin_lane_id" uses Register X24, scope (0->327)
  ## Param "ikey" uses Register X8, scope (0->328)
  ## Param "bin_list_size" uses Register X9, scope (0->328)
  ## Param "bin_addr" uses Register X10, scope (0->328)
  ## Scoped Variable "evw" uses Register X22, scope (0->328)
  ## Scoped Variable "sptr" uses Register X23, scope (0->328)
  ## Scoped Variable "bitmap" uses Register X24, scope (0->328)
  ## Scoped Variable "send_buffer" uses Register X25, scope (0->328)
  ## Param "ikey" uses Register X8, scope (0->336)
  ## Param "bin_list_size" uses Register X9, scope (0->336)
  ## Param "bin_addr" uses Register X10, scope (0->336)
  ## Param "ptr" uses Register X11, scope (0->336)
  ## Scoped Variable "sptr" uses Register X22, scope (0->336)
  ## Scoped Variable "bin_id" uses Register X23, scope (0->336)
  ## Scoped Variable "tmp_bin_dram_addr" uses Register X24, scope (0->336)
  ## Scoped Variable "evw" uses Register X25, scope (0->336)
  ## Scoped Variable "send_buffer" uses Register X26, scope (0->336)
  ## Param "ikey" uses Register X8, scope (0->337)
  ## Param "bin_list_size" uses Register X9, scope (0->337)
  ## Param "bin_addr" uses Register X10, scope (0->337)
  ## Param "ptr" uses Register X11, scope (0->337)
  ## Scoped Variable "sptr" uses Register X22, scope (0->337)
  ## Scoped Variable "bin_id" uses Register X23, scope (0->337)
  ## Scoped Variable "tmp_bin_dram_addr" uses Register X24, scope (0->337)
  ## Scoped Variable "evw" uses Register X25, scope (0->337)
  ## Scoped Variable "evw" uses Register X22, scope (0->338->340)
  ## Scoped Variable "cont" uses Register X23, scope (0->338->340)
  ## Scoped Variable "lm_ptr" uses Register X22, scope (0->341)
  ## Scoped Variable "evw" uses Register X23, scope (0->341)
  ## Scoped Variable "evw" uses Register X22, scope (0->342->344)
  ## Scoped Variable "sptr" uses Register X23, scope (0->342->344)
  ## Scoped Variable "bitmap" uses Register X24, scope (0->342->344)
  ## Scoped Variable "evw" uses Register X22, scope (0->345)
  ## Scoped Variable "sptr" uses Register X23, scope (0->345)
  ## Scoped Variable "bitmap" uses Register X24, scope (0->345)
  ## Scoped Variable "tot" uses Register X16, scope (0)
  ## Scoped Variable "bin_size" uses Register X17, scope (0)
  ## Scoped Variable "bin_dram_addr" uses Register X18, scope (0)
  ## Scoped Variable "save_cont" uses Register X19, scope (0)
  ## Scoped Variable "offset" uses Register X20, scope (0)
  ## Scoped Variable "local_space_bit" uses Register X21, scope (0)
  ## Param "key" uses Register X8, scope (0->347)
  ## Param "val" uses Register X9, scope (0->347)
  ## Scoped Variable "evw" uses Register X22, scope (0->347)
  ## Scoped Variable "sptr" uses Register X23, scope (0->347)
  ## Scoped Variable "bin_lane_id" uses Register X24, scope (0->347)
  ## Scoped Variable "ikey" uses Register X25, scope (0->347)
  ## Scoped Variable "bin_list_size" uses Register X26, scope (0->347)
  ## Scoped Variable "bin_addr" uses Register X27, scope (0->347)
  ## Param "ikey" uses Register X8, scope (0->348)
  ## Param "bin_list_size" uses Register X9, scope (0->348)
  ## Param "bin_addr" uses Register X10, scope (0->348)
  ## Scoped Variable "evw" uses Register X22, scope (0->348)
  ## Scoped Variable "sptr" uses Register X23, scope (0->348)
  ## Scoped Variable "bitmap" uses Register X24, scope (0->348)
  ## Scoped Variable "send_buffer" uses Register X25, scope (0->348)
  ## Param "ikey" uses Register X8, scope (0->356)
  ## Param "bin_list_size" uses Register X9, scope (0->356)
  ## Param "bin_addr" uses Register X10, scope (0->356)
  ## Param "ikey" uses Register X8, scope (0->357)
  ## Param "bin_list_size" uses Register X9, scope (0->357)
  ## Param "bin_addr" uses Register X10, scope (0->357)
  ## Param "ptr" uses Register X11, scope (0->357)
  ## Scoped Variable "sptr" uses Register X22, scope (0->357)
  ## Scoped Variable "bin_id" uses Register X23, scope (0->357)
  ## Scoped Variable "tmp_bin_dram_addr" uses Register X24, scope (0->357)
  ## Scoped Variable "evw" uses Register X25, scope (0->357)
  ## Scoped Variable "send_buffer" uses Register X26, scope (0->357)
  ## Param "ikey" uses Register X8, scope (0->358)
  ## Param "bin_list_size" uses Register X9, scope (0->358)
  ## Param "bin_addr" uses Register X10, scope (0->358)
  ## Param "ptr" uses Register X11, scope (0->358)
  ## Scoped Variable "sptr" uses Register X22, scope (0->358)
  ## Scoped Variable "bin_id" uses Register X23, scope (0->358)
  ## Scoped Variable "tmp_bin_dram_addr" uses Register X24, scope (0->358)
  ## Scoped Variable "evw" uses Register X25, scope (0->358)
  ## Scoped Variable "evw" uses Register X22, scope (0->359->361)
  ## Scoped Variable "cont" uses Register X23, scope (0->359->361)
  ## Scoped Variable "lm_ptr" uses Register X22, scope (0->362)
  ## Scoped Variable "evw" uses Register X23, scope (0->362)
  ## Scoped Variable "evw" uses Register X22, scope (0->363->365)
  ## Scoped Variable "sptr" uses Register X23, scope (0->363->365)
  ## Scoped Variable "bitmap" uses Register X24, scope (0->363->365)
  ## Scoped Variable "evw" uses Register X22, scope (0->366)
  ## Scoped Variable "sptr" uses Register X23, scope (0->366)
  ## Scoped Variable "bitmap" uses Register X24, scope (0->366)
  ## Scoped Variable "tot" uses Register X16, scope (0)
  ## Scoped Variable "bin_size" uses Register X17, scope (0)
  ## Scoped Variable "bin_dram_addr" uses Register X18, scope (0)
  ## Scoped Variable "save_cont" uses Register X19, scope (0)
  ## Scoped Variable "offset" uses Register X20, scope (0)
  ## Scoped Variable "local_space_bit" uses Register X21, scope (0)
  ## Param "key" uses Register X8, scope (0->368)
  ## Param "val" uses Register X9, scope (0->368)
  ## Scoped Variable "evw" uses Register X22, scope (0->368)
  ## Scoped Variable "sptr" uses Register X23, scope (0->368)
  ## Scoped Variable "bin_lane_id" uses Register X24, scope (0->368)
  ## Param "ikey" uses Register X8, scope (0->369)
  ## Param "bin_list_size" uses Register X9, scope (0->369)
  ## Param "bin_addr" uses Register X10, scope (0->369)
  ## Scoped Variable "evw" uses Register X22, scope (0->369)
  ## Scoped Variable "sptr" uses Register X23, scope (0->369)
  ## Scoped Variable "bitmap" uses Register X24, scope (0->369)
  ## Scoped Variable "send_buffer" uses Register X25, scope (0->369)
  ## Param "ikey" uses Register X8, scope (0->377)
  ## Param "bin_list_size" uses Register X9, scope (0->377)
  ## Param "bin_addr" uses Register X10, scope (0->377)
  ## Param "ptr" uses Register X11, scope (0->377)
  ## Scoped Variable "sptr" uses Register X22, scope (0->377)
  ## Scoped Variable "bin_id" uses Register X23, scope (0->377)
  ## Scoped Variable "tmp_bin_dram_addr" uses Register X24, scope (0->377)
  ## Scoped Variable "evw" uses Register X25, scope (0->377)
  ## Scoped Variable "send_buffer" uses Register X26, scope (0->377)
  ## Param "ikey" uses Register X8, scope (0->378)
  ## Param "bin_list_size" uses Register X9, scope (0->378)
  ## Param "bin_addr" uses Register X10, scope (0->378)
  ## Param "ptr" uses Register X11, scope (0->378)
  ## Scoped Variable "sptr" uses Register X22, scope (0->378)
  ## Scoped Variable "bin_id" uses Register X23, scope (0->378)
  ## Scoped Variable "tmp_bin_dram_addr" uses Register X24, scope (0->378)
  ## Scoped Variable "evw" uses Register X25, scope (0->378)
  ## Scoped Variable "evw" uses Register X22, scope (0->379->381)
  ## Scoped Variable "cont" uses Register X23, scope (0->379->381)
  ## Scoped Variable "lm_ptr" uses Register X22, scope (0->382)
  ## Scoped Variable "evw" uses Register X23, scope (0->382)
  ## Scoped Variable "evw" uses Register X22, scope (0->383->385)
  ## Scoped Variable "sptr" uses Register X23, scope (0->383->385)
  ## Scoped Variable "bitmap" uses Register X24, scope (0->383->385)
  ## Scoped Variable "evw" uses Register X22, scope (0->386)
  ## Scoped Variable "sptr" uses Register X23, scope (0->386)
  ## Scoped Variable "bitmap" uses Register X24, scope (0->386)
  ## Scoped Variable "tot" uses Register X16, scope (0)
  ## Scoped Variable "bin_size" uses Register X17, scope (0)
  ## Scoped Variable "bin_dram_addr" uses Register X18, scope (0)
  ## Scoped Variable "save_cont" uses Register X19, scope (0)
  ## Scoped Variable "offset" uses Register X20, scope (0)
  ## Scoped Variable "local_space_bit" uses Register X21, scope (0)
  ## Param "key" uses Register X8, scope (0->388)
  ## Param "val" uses Register X9, scope (0->388)
  ## Scoped Variable "evw" uses Register X22, scope (0->388)
  ## Scoped Variable "sptr" uses Register X23, scope (0->388)
  ## Scoped Variable "bin_lane_id" uses Register X24, scope (0->388)
  ## Scoped Variable "ikey" uses Register X25, scope (0->388)
  ## Scoped Variable "bin_list_size" uses Register X26, scope (0->388)
  ## Scoped Variable "bin_addr" uses Register X27, scope (0->388)
  ## Param "ikey" uses Register X8, scope (0->389)
  ## Param "bin_list_size" uses Register X9, scope (0->389)
  ## Param "bin_addr" uses Register X10, scope (0->389)
  ## Scoped Variable "evw" uses Register X22, scope (0->389)
  ## Scoped Variable "sptr" uses Register X23, scope (0->389)
  ## Scoped Variable "bitmap" uses Register X24, scope (0->389)
  ## Scoped Variable "send_buffer" uses Register X25, scope (0->389)
  ## Param "ikey" uses Register X8, scope (0->397)
  ## Param "bin_list_size" uses Register X9, scope (0->397)
  ## Param "bin_addr" uses Register X10, scope (0->397)
  ## Param "ikey" uses Register X8, scope (0->398)
  ## Param "bin_list_size" uses Register X9, scope (0->398)
  ## Param "bin_addr" uses Register X10, scope (0->398)
  ## Param "ptr" uses Register X11, scope (0->398)
  ## Scoped Variable "sptr" uses Register X22, scope (0->398)
  ## Scoped Variable "bin_id" uses Register X23, scope (0->398)
  ## Scoped Variable "tmp_bin_dram_addr" uses Register X24, scope (0->398)
  ## Scoped Variable "evw" uses Register X25, scope (0->398)
  ## Scoped Variable "send_buffer" uses Register X26, scope (0->398)
  ## Param "ikey" uses Register X8, scope (0->399)
  ## Param "bin_list_size" uses Register X9, scope (0->399)
  ## Param "bin_addr" uses Register X10, scope (0->399)
  ## Param "ptr" uses Register X11, scope (0->399)
  ## Scoped Variable "sptr" uses Register X22, scope (0->399)
  ## Scoped Variable "bin_id" uses Register X23, scope (0->399)
  ## Scoped Variable "tmp_bin_dram_addr" uses Register X24, scope (0->399)
  ## Scoped Variable "evw" uses Register X25, scope (0->399)
  ## Scoped Variable "evw" uses Register X22, scope (0->400->402)
  ## Scoped Variable "cont" uses Register X23, scope (0->400->402)
  ## Scoped Variable "lm_ptr" uses Register X22, scope (0->403)
  ## Scoped Variable "evw" uses Register X23, scope (0->403)
  ## Scoped Variable "evw" uses Register X22, scope (0->404->406)
  ## Scoped Variable "sptr" uses Register X23, scope (0->404->406)
  ## Scoped Variable "bitmap" uses Register X24, scope (0->404->406)
  ## Scoped Variable "evw" uses Register X22, scope (0->407)
  ## Scoped Variable "sptr" uses Register X23, scope (0->407)
  ## Scoped Variable "bitmap" uses Register X24, scope (0->407)
  ## Scoped Variable "tot" uses Register X16, scope (0)
  ## Scoped Variable "bin_size" uses Register X17, scope (0)
  ## Scoped Variable "bin_dram_addr" uses Register X18, scope (0)
  ## Scoped Variable "offset" uses Register X19, scope (0)
  ## Param "key" uses Register X8, scope (0->409)
  ## Param "val" uses Register X9, scope (0->409)
  ## Scoped Variable "evw" uses Register X20, scope (0->409)
  ## Param "ikey" uses Register X8, scope (0->410)
  ## Param "bin_list_size" uses Register X9, scope (0->410)
  ## Param "bin_addr" uses Register X10, scope (0->410)
  ## Scoped Variable "ptr" uses Register X20, scope (0->410)
  ## Scoped Variable "sptr" uses Register X21, scope (0->410)
  ## Scoped Variable "bin_ddr" uses Register X22, scope (0->410)
  ## Scoped Variable "bin_id" uses Register X23, scope (0->410)
  ## Scoped Variable "tmp_bin_dram_addr" uses Register X24, scope (0->410)
  ## Param "nxt_bin_size" uses Register X8, scope (0->411)
  ## Scoped Variable "evw" uses Register X20, scope (0->411)
  ## Param "x" uses Register X8, scope (0->415)
  ## Param "sort_lm_offset" uses Register X8, scope (0->419)
  ## Param "list_size" uses Register X9, scope (0->419)
  ## Param "list_addr" uses Register X10, scope (0->419)
  ## Param "num_lanes" uses Register X11, scope (0->419)
  ## Param "tmp_addr" uses Register X12, scope (0->419)
  ## Param "num_bins" uses Register X13, scope (0->419)
  ## Param "lb_addr" uses Register X14, scope (0->419)
  ## Param "max_value" uses Register X15, scope (0->419)
  ## Scoped Variable "evw" uses Register X16, scope (0->419)
  ## Scoped Variable "cont" uses Register X17, scope (0->419)
  ## Scoped Variable "spPtr" uses Register X18, scope (0->419)
  ## Param "list_addr" uses Register X8, scope (0->420)
  ## Param "list_size" uses Register X9, scope (0->420)
  ## Param "num_lanes" uses Register X10, scope (0->420)
  ## Scoped Variable "evw" uses Register X16, scope (0->420)
  ## Scoped Variable "cont" uses Register X17, scope (0->420)
  ## Scoped Variable "spPtr" uses Register X18, scope (0->420)
  ## Scoped Variable "spPtr" uses Register X16, scope (0->421)
  
  from libraries.UDMapShuffleReduce.linkable.LinkableKVMapShuffleReduceTPL import UDKeyValueMapShuffleReduceTemplate
  from libraries.UDMapShuffleReduce.utils.OneDimArrayKeyValueSet import OneDimKeyValueSet
  from libraries.UDMapShuffleReduce.utils.IntermediateKeyValueSet import IntermediateKeyValueSet
  
  from LinkableGlobalSync import Broadcast
  Broadcast(state=state0, identifier='DistributedSortBroadcast', debug_flag=False)
  
  
  from LinkableGlobalSync import Broadcast
  Broadcast(state=state0, identifier='ParallelPrefixBroadcast', debug_flag=False)
  
  
  
  ##   from libraries.UDMapShuffleReduce.linkable.LinkableGlobalSync import Broadcast
  ##   init_broadcast = Broadcast(state0, 'DistributedSortBroadcast', False)
  ##   init_broadcast.gen_broadcast()
  ## Memory layout
  ## 16 words for per-lane variables
  ## #define VAR_SIZE 128
  ## #define COUNTERS_OFFSET 128
  ## #define INSERTION
  ## exclusive scan
  
  ####################################################
  ###### Writing code for thread ParallelPrefix ######
  ####################################################
  # Writing code for event ParallelPrefix::prefix
  tranParallelPrefix__prefix = efa.writeEvent('ParallelPrefix::prefix')
  tranParallelPrefix__prefix.writeAction(f"entry: print 'PP input: %lu %lu %lu %lu %lu' X8 X9 X10 X11 X12") 
  tranParallelPrefix__prefix.writeAction(f"addi X11 X18 0") 
  tranParallelPrefix__prefix.writeAction(f"addi X12 X19 0") 
  tranParallelPrefix__prefix.writeAction(f"add X7 X18 X20") 
  tranParallelPrefix__prefix.writeAction(f"add X7 X19 X21") 
  tranParallelPrefix__prefix.writeAction(f"print 'offset = %d' X19") 
  ## print("num_lanes = %d", num_lanes);
  tranParallelPrefix__prefix.writeAction(f"print 'prallel prefix start'") 
  ## print("list_size = %d", list_size);
  tranParallelPrefix__prefix.writeAction(f"movir X16 0") 
  tranParallelPrefix__prefix.writeAction(f"addi X8 X22 0") 
  tranParallelPrefix__prefix.writeAction(f"addi X9 X23 0") 
  tranParallelPrefix__prefix.writeAction(f"__while_prefix_0_condition: bleiu X23 1 __while_prefix_2_post") 
  ## send_dram_read(cur_addr, PBLOCKSIZE, prefix_load_ret);
  tranParallelPrefix__prefix.writeAction(f"__while_prefix_1_body: sli X16 X24 1") 
  tranParallelPrefix__prefix.writeAction(f"movwrl X22 X21(X24,0,0)") 
  tranParallelPrefix__prefix.writeAction(f"sladdii X16 X25 1 1") 
  tranParallelPrefix__prefix.writeAction(f"movwrl X23 X21(X25,0,0)") 
  ## print("cur_size = %d", cur_size);
  tranParallelPrefix__prefix.writeAction(f"sli X23 X24 3") 
  tranParallelPrefix__prefix.writeAction(f"add X22 X24 X22") 
  tranParallelPrefix__prefix.writeAction(f"addi X23 X24 4096") 
  tranParallelPrefix__prefix.writeAction(f"subi X24 X25 1") 
  tranParallelPrefix__prefix.writeAction(f"sari X25 X23 12") 
  ## print("cur_size = %d", cur_size);
  tranParallelPrefix__prefix.writeAction(f"addi X16 X16 1") 
  tranParallelPrefix__prefix.writeAction(f"jmp __while_prefix_0_condition") 
  tranParallelPrefix__prefix.writeAction(f"__while_prefix_2_post: movir X17 0") 
  tranParallelPrefix__prefix.writeAction(f"evi X2 X24 ParallelPrefix::preifx_forward_for 1") 
  tranParallelPrefix__prefix.writeAction(f"movir X25 0") 
  tranParallelPrefix__prefix.writeAction(f"movir X26 -1") 
  tranParallelPrefix__prefix.writeAction(f"sri X26 X26 1") 
  tranParallelPrefix__prefix.writeAction(f"sendr_wcont X24 X26 X25 X25") 
  ## long* local sp_ptr = LMBASE + SORT_OFFSET;
  ## sp_ptr[LIST_SIZE] = list_size;
  ## sp_ptr[LIST_ADDR] = list_addr;
  ## sp_ptr[TMP_ADDR] = tmp_addr;
  ## send_event(CCONT, 0, IGNRCONT);
  ## yield_terminate;
  tranParallelPrefix__prefix.writeAction(f"yield") 
  
  # Writing code for event ParallelPrefix::preifx_forward_for
  tranParallelPrefix__preifx_forward_for = efa.writeEvent('ParallelPrefix::preifx_forward_for')
  tranParallelPrefix__preifx_forward_for.writeAction(f"entry: print 'forward loop, cur = %d, tot = %d' X17 X16") 
  tranParallelPrefix__preifx_forward_for.writeAction(f"bne X17 X16 __if_preifx_forward_for_1_false") 
  tranParallelPrefix__preifx_forward_for.writeAction(f"__if_preifx_forward_for_0_true: evi X2 X20 ParallelPrefix::preifx_backward_for 1") 
  tranParallelPrefix__preifx_forward_for.writeAction(f"movir X21 0") 
  tranParallelPrefix__preifx_forward_for.writeAction(f"movir X22 -1") 
  tranParallelPrefix__preifx_forward_for.writeAction(f"sri X22 X22 1") 
  tranParallelPrefix__preifx_forward_for.writeAction(f"sendr_wcont X20 X22 X21 X21") 
  tranParallelPrefix__preifx_forward_for.writeAction(f"jmp __if_preifx_forward_for_2_post") 
  ## launch broadcast to calculate prefix of each block in vec_ptr[tot * 2], vector_ptr[tot * 2 + 1]
  tranParallelPrefix__preifx_forward_for.writeAction(f"__if_preifx_forward_for_1_false: add X7 X19 X20") 
  tranParallelPrefix__preifx_forward_for.writeAction(f"__if_preifx_forward_for_3_true: movlr 0(X20) X21 0 8") 
  tranParallelPrefix__preifx_forward_for.writeAction(f"movlr 8(X20) X22 0 8") 
  tranParallelPrefix__preifx_forward_for.writeAction(f"movlr 16(X20) X23 0 8") 
  tranParallelPrefix__preifx_forward_for.writeAction(f"movlr 24(X20) X24 0 8") 
  tranParallelPrefix__preifx_forward_for.writeAction(f"print '%d %d %d %d' X21 X22 X23 X24") 
  tranParallelPrefix__preifx_forward_for.writeAction(f"sladdii X17 X23 1 1") 
  tranParallelPrefix__preifx_forward_for.writeAction(f"movwlr X20(X23,0,0) X21") 
  tranParallelPrefix__preifx_forward_for.writeAction(f"print 'nvals = %d' X21") 
  tranParallelPrefix__preifx_forward_for.writeAction(f"addi X21 X23 4096") 
  tranParallelPrefix__preifx_forward_for.writeAction(f"subi X23 X24 1") 
  tranParallelPrefix__preifx_forward_for.writeAction(f"sari X24 X27 63") 
  tranParallelPrefix__preifx_forward_for.writeAction(f"sri X27 X27 52") 
  tranParallelPrefix__preifx_forward_for.writeAction(f"add X27 X24 X22") 
  tranParallelPrefix__preifx_forward_for.writeAction(f"sari X22 X22 12") 
  tranParallelPrefix__preifx_forward_for.writeAction(f"print 'offset = %d 4096' X19") 
  ## print("xx: %d", vec_ptr[cur * 2 + 1]);
  tranParallelPrefix__preifx_forward_for.writeAction(f"print 'n_lanes = %d' X22") 
  tranParallelPrefix__preifx_forward_for.writeAction(f"movir X23 0") 
  tranParallelPrefix__preifx_forward_for.writeAction(f"evlb X23 DistributedSortBroadcast__broadcast_global") 
  tranParallelPrefix__preifx_forward_for.writeAction(f"evi X23 X23 255 4") 
  tranParallelPrefix__preifx_forward_for.writeAction(f"ev X23 X23 X0 X0 8") 
  tranParallelPrefix__preifx_forward_for.writeAction(f"movir X24 0") 
  tranParallelPrefix__preifx_forward_for.writeAction(f"evlb X24 ParallelPrefixPerLane::prefix_forward_per_lane") 
  ## cont_word = evw_update_event(CEVNT, end_prefix);
  tranParallelPrefix__preifx_forward_for.writeAction(f"addi X7 X26 8") 
  tranParallelPrefix__preifx_forward_for.writeAction(f"movrl X22 0(X26) 0 8") 
  tranParallelPrefix__preifx_forward_for.writeAction(f"movrl X24 8(X26) 0 8") 
  tranParallelPrefix__preifx_forward_for.writeAction(f"movrl X0 16(X26) 0 8") 
  tranParallelPrefix__preifx_forward_for.writeAction(f"sli X17 X28 1") 
  tranParallelPrefix__preifx_forward_for.writeAction(f"movwlr X20(X28,0,0) X29") 
  tranParallelPrefix__preifx_forward_for.writeAction(f"movrl X29 24(X26) 0 8") 
  tranParallelPrefix__preifx_forward_for.writeAction(f"sladdii X17 X29 1 1") 
  tranParallelPrefix__preifx_forward_for.writeAction(f"movwlr X20(X29,0,0) X30") 
  tranParallelPrefix__preifx_forward_for.writeAction(f"movrl X30 32(X26) 0 8") 
  tranParallelPrefix__preifx_forward_for.writeAction(f"movir X28 0") 
  tranParallelPrefix__preifx_forward_for.writeAction(f"movrl X28 40(X26) 0 8") 
  tranParallelPrefix__preifx_forward_for.writeAction(f"movir X28 0") 
  tranParallelPrefix__preifx_forward_for.writeAction(f"movrl X28 48(X26) 0 8") 
  tranParallelPrefix__preifx_forward_for.writeAction(f"movrl X18 56(X26) 0 8") 
  tranParallelPrefix__preifx_forward_for.writeAction(f"addi X17 X27 1") 
  tranParallelPrefix__preifx_forward_for.writeAction(f"ble X16 X27 __if_preifx_forward_for_8_post") 
  tranParallelPrefix__preifx_forward_for.writeAction(f"__if_preifx_forward_for_6_true: addi X17 X28 1") 
  tranParallelPrefix__preifx_forward_for.writeAction(f"sli X28 X29 1") 
  tranParallelPrefix__preifx_forward_for.writeAction(f"movwlr X20(X29,0,0) X30") 
  tranParallelPrefix__preifx_forward_for.writeAction(f"movrl X30 40(X26) 0 8") 
  tranParallelPrefix__preifx_forward_for.writeAction(f"addi X17 X28 1") 
  tranParallelPrefix__preifx_forward_for.writeAction(f"sladdii X28 X30 1 1") 
  tranParallelPrefix__preifx_forward_for.writeAction(f"movwlr X20(X30,0,0) X31") 
  tranParallelPrefix__preifx_forward_for.writeAction(f"movrl X31 48(X26) 0 8") 
  tranParallelPrefix__preifx_forward_for.writeAction(f"__if_preifx_forward_for_8_post: send_wret X23 ParallelPrefix::preifx_forward_for X26 8 X27") 
  tranParallelPrefix__preifx_forward_for.writeAction(f"addi X17 X17 1") 
  tranParallelPrefix__preifx_forward_for.writeAction(f"__if_preifx_forward_for_2_post: yield") 
  
  # Writing code for event ParallelPrefix::preifx_backward_for
  tranParallelPrefix__preifx_backward_for = efa.writeEvent('ParallelPrefix::preifx_backward_for')
  tranParallelPrefix__preifx_backward_for.writeAction(f"entry: print 'backward loop, cur = %d, tot = %d' X17 X16") 
  tranParallelPrefix__preifx_backward_for.writeAction(f"subi X17 X17 1") 
  ## print("in preifx_backward_for, cur = %d", cur);
  tranParallelPrefix__preifx_backward_for.writeAction(f"bnei X17 0 __if_preifx_backward_for_1_false") 
  tranParallelPrefix__preifx_backward_for.writeAction(f"__if_preifx_backward_for_0_true: evi X2 X20 ParallelPrefix::end_prefix 1") 
  tranParallelPrefix__preifx_backward_for.writeAction(f"movir X21 0") 
  tranParallelPrefix__preifx_backward_for.writeAction(f"movir X22 -1") 
  tranParallelPrefix__preifx_backward_for.writeAction(f"sri X22 X22 1") 
  tranParallelPrefix__preifx_backward_for.writeAction(f"sendr_wcont X20 X22 X21 X21") 
  tranParallelPrefix__preifx_backward_for.writeAction(f"jmp __if_preifx_backward_for_2_post") 
  tranParallelPrefix__preifx_backward_for.writeAction(f"__if_preifx_backward_for_1_false: add X7 X19 X20") 
  tranParallelPrefix__preifx_backward_for.writeAction(f"sladdii X17 X23 1 1") 
  tranParallelPrefix__preifx_backward_for.writeAction(f"movwlr X20(X23,0,0) X21") 
  ## print("n_lanes = %d", n_lanes);
  tranParallelPrefix__preifx_backward_for.writeAction(f"movir X22 0") 
  tranParallelPrefix__preifx_backward_for.writeAction(f"evlb X22 DistributedSortBroadcast__broadcast_global") 
  tranParallelPrefix__preifx_backward_for.writeAction(f"evi X22 X22 255 4") 
  tranParallelPrefix__preifx_backward_for.writeAction(f"ev X22 X22 X0 X0 8") 
  tranParallelPrefix__preifx_backward_for.writeAction(f"movir X23 0") 
  tranParallelPrefix__preifx_backward_for.writeAction(f"evlb X23 ParallelPrefixPerLane::prefix_backward_per_lane") 
  tranParallelPrefix__preifx_backward_for.writeAction(f"evi X2 X24 ParallelPrefix::end_prefix 1") 
  tranParallelPrefix__preifx_backward_for.writeAction(f"addi X7 X25 8") 
  tranParallelPrefix__preifx_backward_for.writeAction(f"movrl X21 0(X25) 0 8") 
  tranParallelPrefix__preifx_backward_for.writeAction(f"movrl X23 8(X25) 0 8") 
  tranParallelPrefix__preifx_backward_for.writeAction(f"movrl X0 16(X25) 0 8") 
  tranParallelPrefix__preifx_backward_for.writeAction(f"subi X17 X27 1") 
  tranParallelPrefix__preifx_backward_for.writeAction(f"sli X27 X28 1") 
  tranParallelPrefix__preifx_backward_for.writeAction(f"movwlr X20(X28,0,0) X29") 
  tranParallelPrefix__preifx_backward_for.writeAction(f"movrl X29 24(X25) 0 8") 
  tranParallelPrefix__preifx_backward_for.writeAction(f"subi X17 X27 1") 
  tranParallelPrefix__preifx_backward_for.writeAction(f"sladdii X27 X29 1 1") 
  tranParallelPrefix__preifx_backward_for.writeAction(f"movwlr X20(X29,0,0) X30") 
  tranParallelPrefix__preifx_backward_for.writeAction(f"movrl X30 32(X25) 0 8") 
  tranParallelPrefix__preifx_backward_for.writeAction(f"sli X17 X27 1") 
  tranParallelPrefix__preifx_backward_for.writeAction(f"movwlr X20(X27,0,0) X28") 
  tranParallelPrefix__preifx_backward_for.writeAction(f"movrl X28 40(X25) 0 8") 
  tranParallelPrefix__preifx_backward_for.writeAction(f"sladdii X17 X28 1 1") 
  tranParallelPrefix__preifx_backward_for.writeAction(f"movwlr X20(X28,0,0) X29") 
  tranParallelPrefix__preifx_backward_for.writeAction(f"movrl X29 48(X25) 0 8") 
  tranParallelPrefix__preifx_backward_for.writeAction(f"movrl X18 56(X25) 0 8") 
  tranParallelPrefix__preifx_backward_for.writeAction(f"send_wret X22 ParallelPrefix::preifx_backward_for X25 8 X26") 
  tranParallelPrefix__preifx_backward_for.writeAction(f"__if_preifx_backward_for_2_post: yield") 
  
  # Writing code for event ParallelPrefix::end_prefix
  tranParallelPrefix__end_prefix = efa.writeEvent('ParallelPrefix::end_prefix')
  tranParallelPrefix__end_prefix.writeAction(f"entry: print 'end_prefix'") 
  tranParallelPrefix__end_prefix.writeAction(f"movir X20 0") 
  tranParallelPrefix__end_prefix.writeAction(f"movir X21 -1") 
  tranParallelPrefix__end_prefix.writeAction(f"sri X21 X21 1") 
  tranParallelPrefix__end_prefix.writeAction(f"sendr_wcont X1 X21 X20 X20") 
  tranParallelPrefix__end_prefix.writeAction(f"yield_terminate") 
  
  
  ################################################
  ###### Writing code for thread MemRequest ######
  ################################################
  ## implement dram read/write with a limit on the number of outstanding requests
  
  ###############################################
  ###### Writing code for thread MemcpyLib ######
  ###############################################
  ## let this thread handle all memory copy operations
  ## and we can limit outstanding loads here
  # Writing code for event MemcpyLib::memcpy_dram_to_sp
  tranMemcpyLib__memcpy_dram_to_sp = efa.writeEvent('MemcpyLib::memcpy_dram_to_sp')
  tranMemcpyLib__memcpy_dram_to_sp.writeAction(f"entry: bneiu X10 0 __if_memcpy_dram_to_sp_2_post") 
  tranMemcpyLib__memcpy_dram_to_sp.writeAction(f"__if_memcpy_dram_to_sp_0_true: movir X22 0") 
  tranMemcpyLib__memcpy_dram_to_sp.writeAction(f"movir X23 -1") 
  tranMemcpyLib__memcpy_dram_to_sp.writeAction(f"sri X23 X23 1") 
  tranMemcpyLib__memcpy_dram_to_sp.writeAction(f"sendr_wcont X1 X23 X22 X22") 
  tranMemcpyLib__memcpy_dram_to_sp.writeAction(f"yield_terminate") 
  tranMemcpyLib__memcpy_dram_to_sp.writeAction(f"__if_memcpy_dram_to_sp_2_post: sub X9 X8 X17") 
  tranMemcpyLib__memcpy_dram_to_sp.writeAction(f"addi X10 X20 0") 
  tranMemcpyLib__memcpy_dram_to_sp.writeAction(f"addi X8 X19 0") 
  tranMemcpyLib__memcpy_dram_to_sp.writeAction(f"movir X16 0") 
  tranMemcpyLib__memcpy_dram_to_sp.writeAction(f"movir X18 0") 
  tranMemcpyLib__memcpy_dram_to_sp.writeAction(f"evi X2 X22 MemcpyLib::memcpy_dram_to_sp_loop 1") 
  tranMemcpyLib__memcpy_dram_to_sp.writeAction(f"movir X23 0") 
  tranMemcpyLib__memcpy_dram_to_sp.writeAction(f"movir X24 -1") 
  tranMemcpyLib__memcpy_dram_to_sp.writeAction(f"sri X24 X24 1") 
  tranMemcpyLib__memcpy_dram_to_sp.writeAction(f"sendr_wcont X22 X24 X23 X23") 
  tranMemcpyLib__memcpy_dram_to_sp.writeAction(f"yield") 
  
  # Writing code for event MemcpyLib::memcpy_dram_to_sp_loop
  tranMemcpyLib__memcpy_dram_to_sp_loop = efa.writeEvent('MemcpyLib::memcpy_dram_to_sp_loop')
  tranMemcpyLib__memcpy_dram_to_sp_loop.writeAction(f"entry: addi X7 X22 20000") 
  tranMemcpyLib__memcpy_dram_to_sp_loop.writeAction(f"movlr 120(X22) X23 0 8") 
  tranMemcpyLib__memcpy_dram_to_sp_loop.writeAction(f"__while_memcpy_dram_to_sp_loop_0_condition: movir X24 152") 
  tranMemcpyLib__memcpy_dram_to_sp_loop.writeAction(f"sli X24 X24 16") 
  tranMemcpyLib__memcpy_dram_to_sp_loop.writeAction(f"ori X24 X24 38528") 
  tranMemcpyLib__memcpy_dram_to_sp_loop.writeAction(f"clt X23 X24 X24") 
  tranMemcpyLib__memcpy_dram_to_sp_loop.writeAction(f"clt X18 X20 X25") 
  tranMemcpyLib__memcpy_dram_to_sp_loop.writeAction(f"and X24 X25 X26") 
  tranMemcpyLib__memcpy_dram_to_sp_loop.writeAction(f"beqiu X26 0 __while_memcpy_dram_to_sp_loop_2_post") 
  tranMemcpyLib__memcpy_dram_to_sp_loop.writeAction(f"__while_memcpy_dram_to_sp_loop_1_body: addi X19 X24 0") 
  tranMemcpyLib__memcpy_dram_to_sp_loop.writeAction(f"addi X18 X25 8") 
  tranMemcpyLib__memcpy_dram_to_sp_loop.writeAction(f"bgtu X25 X20 __if_memcpy_dram_to_sp_loop_4_false") 
  ## print("sending 8");
  tranMemcpyLib__memcpy_dram_to_sp_loop.writeAction(f"__if_memcpy_dram_to_sp_loop_3_true: send_dmlm_ld_wret X24 MemcpyLib::memcpy_dram_to_sp_ret8 8 X25") 
  tranMemcpyLib__memcpy_dram_to_sp_loop.writeAction(f"addi X19 X19 64") 
  tranMemcpyLib__memcpy_dram_to_sp_loop.writeAction(f"addi X16 X16 8") 
  tranMemcpyLib__memcpy_dram_to_sp_loop.writeAction(f"addi X18 X18 8") 
  tranMemcpyLib__memcpy_dram_to_sp_loop.writeAction(f"addi X23 X23 1") 
  tranMemcpyLib__memcpy_dram_to_sp_loop.writeAction(f"jmp __if_memcpy_dram_to_sp_loop_5_post") 
  ## print("sending 1");
  tranMemcpyLib__memcpy_dram_to_sp_loop.writeAction(f"__if_memcpy_dram_to_sp_loop_4_false: send_dmlm_ld_wret X24 MemcpyLib::memcpy_dram_to_sp_ret 1 X25") 
  tranMemcpyLib__memcpy_dram_to_sp_loop.writeAction(f"addi X19 X19 8") 
  tranMemcpyLib__memcpy_dram_to_sp_loop.writeAction(f"addi X16 X16 1") 
  tranMemcpyLib__memcpy_dram_to_sp_loop.writeAction(f"addi X18 X18 1") 
  tranMemcpyLib__memcpy_dram_to_sp_loop.writeAction(f"addi X23 X23 1") 
  tranMemcpyLib__memcpy_dram_to_sp_loop.writeAction(f"__if_memcpy_dram_to_sp_loop_5_post: jmp __while_memcpy_dram_to_sp_loop_0_condition") 
  ## print("after sending: out_cnt = %d", out_cnt);
  tranMemcpyLib__memcpy_dram_to_sp_loop.writeAction(f"__while_memcpy_dram_to_sp_loop_2_post: movrl X23 120(X22) 0 8") 
  tranMemcpyLib__memcpy_dram_to_sp_loop.writeAction(f"bleu X20 X18 __if_memcpy_dram_to_sp_loop_8_post") 
  tranMemcpyLib__memcpy_dram_to_sp_loop.writeAction(f"__if_memcpy_dram_to_sp_loop_6_true: evi X2 X24 MemcpyLib::memcpy_dram_to_sp_loop 1") 
  tranMemcpyLib__memcpy_dram_to_sp_loop.writeAction(f"movir X25 0") 
  tranMemcpyLib__memcpy_dram_to_sp_loop.writeAction(f"movir X26 -1") 
  tranMemcpyLib__memcpy_dram_to_sp_loop.writeAction(f"sri X26 X26 1") 
  tranMemcpyLib__memcpy_dram_to_sp_loop.writeAction(f"sendr_wcont X24 X26 X25 X25") 
  tranMemcpyLib__memcpy_dram_to_sp_loop.writeAction(f"yield") 
  tranMemcpyLib__memcpy_dram_to_sp_loop.writeAction(f"__if_memcpy_dram_to_sp_loop_8_post: yield") 
  
  # Writing code for event MemcpyLib::memcpy_dram_to_sp_ret
  tranMemcpyLib__memcpy_dram_to_sp_ret = efa.writeEvent('MemcpyLib::memcpy_dram_to_sp_ret')
  ## copyOperands(op0, lmbase, 8); ???
  ## print("getting %lu", val);
  tranMemcpyLib__memcpy_dram_to_sp_ret.writeAction(f"entry: addi X7 X22 20000") 
  tranMemcpyLib__memcpy_dram_to_sp_ret.writeAction(f"movlr 120(X22) X24 0 8") 
  tranMemcpyLib__memcpy_dram_to_sp_ret.writeAction(f"subi X24 X25 1") 
  tranMemcpyLib__memcpy_dram_to_sp_ret.writeAction(f"movrl X25 120(X22) 0 8") 
  tranMemcpyLib__memcpy_dram_to_sp_ret.writeAction(f"add X9 X17 X23") 
  tranMemcpyLib__memcpy_dram_to_sp_ret.writeAction(f"movrl X8 0(X23) 0 8") 
  tranMemcpyLib__memcpy_dram_to_sp_ret.writeAction(f"subi X16 X16 1") 
  tranMemcpyLib__memcpy_dram_to_sp_ret.writeAction(f"ceq X18 X20 X24") 
  tranMemcpyLib__memcpy_dram_to_sp_ret.writeAction(f"ceqi X16 X25 0") 
  tranMemcpyLib__memcpy_dram_to_sp_ret.writeAction(f"and X24 X25 X26") 
  tranMemcpyLib__memcpy_dram_to_sp_ret.writeAction(f"beqiu X26 0 __if_memcpy_dram_to_sp_ret_2_post") 
  ## print("sending back");
  tranMemcpyLib__memcpy_dram_to_sp_ret.writeAction(f"__if_memcpy_dram_to_sp_ret_0_true: movir X24 0") 
  tranMemcpyLib__memcpy_dram_to_sp_ret.writeAction(f"movir X25 -1") 
  tranMemcpyLib__memcpy_dram_to_sp_ret.writeAction(f"sri X25 X25 1") 
  tranMemcpyLib__memcpy_dram_to_sp_ret.writeAction(f"sendr_wcont X1 X25 X24 X24") 
  tranMemcpyLib__memcpy_dram_to_sp_ret.writeAction(f"yield_terminate") 
  tranMemcpyLib__memcpy_dram_to_sp_ret.writeAction(f"__if_memcpy_dram_to_sp_ret_2_post: yield") 
  
  # Writing code for event MemcpyLib::memcpy_dram_to_sp_ret8
  tranMemcpyLib__memcpy_dram_to_sp_ret8 = efa.writeEvent('MemcpyLib::memcpy_dram_to_sp_ret8')
  ## print("getting 8");
  tranMemcpyLib__memcpy_dram_to_sp_ret8.writeAction(f"entry: addi X7 X22 20000") 
  tranMemcpyLib__memcpy_dram_to_sp_ret8.writeAction(f"movlr 120(X22) X24 0 8") 
  tranMemcpyLib__memcpy_dram_to_sp_ret8.writeAction(f"subi X24 X25 1") 
  tranMemcpyLib__memcpy_dram_to_sp_ret8.writeAction(f"movrl X25 120(X22) 0 8") 
  tranMemcpyLib__memcpy_dram_to_sp_ret8.writeAction(f"add X3 X17 X23") 
  tranMemcpyLib__memcpy_dram_to_sp_ret8.writeAction(f"bcpyoli X8 X23 8") 
  tranMemcpyLib__memcpy_dram_to_sp_ret8.writeAction(f"subi X16 X16 8") 
  tranMemcpyLib__memcpy_dram_to_sp_ret8.writeAction(f"ceq X18 X20 X24") 
  tranMemcpyLib__memcpy_dram_to_sp_ret8.writeAction(f"ceqi X16 X25 0") 
  tranMemcpyLib__memcpy_dram_to_sp_ret8.writeAction(f"and X24 X25 X26") 
  tranMemcpyLib__memcpy_dram_to_sp_ret8.writeAction(f"beqiu X26 0 __if_memcpy_dram_to_sp_ret8_2_post") 
  ## print("sending back");
  tranMemcpyLib__memcpy_dram_to_sp_ret8.writeAction(f"__if_memcpy_dram_to_sp_ret8_0_true: movir X24 0") 
  tranMemcpyLib__memcpy_dram_to_sp_ret8.writeAction(f"movir X25 -1") 
  tranMemcpyLib__memcpy_dram_to_sp_ret8.writeAction(f"sri X25 X25 1") 
  tranMemcpyLib__memcpy_dram_to_sp_ret8.writeAction(f"sendr_wcont X1 X25 X24 X24") 
  tranMemcpyLib__memcpy_dram_to_sp_ret8.writeAction(f"yield_terminate") 
  tranMemcpyLib__memcpy_dram_to_sp_ret8.writeAction(f"__if_memcpy_dram_to_sp_ret8_2_post: yield") 
  
  # Writing code for event MemcpyLib::memcpy_sp_to_dram
  tranMemcpyLib__memcpy_sp_to_dram = efa.writeEvent('MemcpyLib::memcpy_sp_to_dram')
  ## unsigned long *local cur_src = src;
  ## unsigned long *local cur_dst = dst;
  tranMemcpyLib__memcpy_sp_to_dram.writeAction(f"entry: bneiu X10 0 __if_memcpy_sp_to_dram_2_post") 
  tranMemcpyLib__memcpy_sp_to_dram.writeAction(f"__if_memcpy_sp_to_dram_0_true: movir X22 0") 
  tranMemcpyLib__memcpy_sp_to_dram.writeAction(f"movir X23 -1") 
  tranMemcpyLib__memcpy_sp_to_dram.writeAction(f"sri X23 X23 1") 
  tranMemcpyLib__memcpy_sp_to_dram.writeAction(f"sendr_wcont X1 X23 X22 X22") 
  tranMemcpyLib__memcpy_sp_to_dram.writeAction(f"yield_terminate") 
  tranMemcpyLib__memcpy_sp_to_dram.writeAction(f"__if_memcpy_sp_to_dram_2_post: sub X9 X8 X17") 
  tranMemcpyLib__memcpy_sp_to_dram.writeAction(f"addi X10 X20 0") 
  tranMemcpyLib__memcpy_sp_to_dram.writeAction(f"addi X8 X19 0") 
  tranMemcpyLib__memcpy_sp_to_dram.writeAction(f"addi X9 X21 0") 
  tranMemcpyLib__memcpy_sp_to_dram.writeAction(f"movir X16 0") 
  tranMemcpyLib__memcpy_sp_to_dram.writeAction(f"movir X18 0") 
  tranMemcpyLib__memcpy_sp_to_dram.writeAction(f"evi X2 X22 MemcpyLib::memcpy_sp_to_dram_loop 1") 
  tranMemcpyLib__memcpy_sp_to_dram.writeAction(f"movir X23 0") 
  tranMemcpyLib__memcpy_sp_to_dram.writeAction(f"movir X24 -1") 
  tranMemcpyLib__memcpy_sp_to_dram.writeAction(f"sri X24 X24 1") 
  tranMemcpyLib__memcpy_sp_to_dram.writeAction(f"sendr_wcont X22 X24 X23 X23") 
  tranMemcpyLib__memcpy_sp_to_dram.writeAction(f"yield") 
  
  # Writing code for event MemcpyLib::memcpy_sp_to_dram_loop
  tranMemcpyLib__memcpy_sp_to_dram_loop = efa.writeEvent('MemcpyLib::memcpy_sp_to_dram_loop')
  tranMemcpyLib__memcpy_sp_to_dram_loop.writeAction(f"entry: addi X7 X22 20000") 
  tranMemcpyLib__memcpy_sp_to_dram_loop.writeAction(f"movlr 120(X22) X23 0 8") 
  ## print("sp_to_dram: out_cnt = %d", out_cnt);
  tranMemcpyLib__memcpy_sp_to_dram_loop.writeAction(f"__while_memcpy_sp_to_dram_loop_0_condition: movir X24 152") 
  tranMemcpyLib__memcpy_sp_to_dram_loop.writeAction(f"sli X24 X24 16") 
  tranMemcpyLib__memcpy_sp_to_dram_loop.writeAction(f"ori X24 X24 38528") 
  tranMemcpyLib__memcpy_sp_to_dram_loop.writeAction(f"clt X23 X24 X24") 
  tranMemcpyLib__memcpy_sp_to_dram_loop.writeAction(f"clt X18 X20 X25") 
  tranMemcpyLib__memcpy_sp_to_dram_loop.writeAction(f"and X24 X25 X26") 
  tranMemcpyLib__memcpy_sp_to_dram_loop.writeAction(f"beqiu X26 0 __while_memcpy_sp_to_dram_loop_2_post") 
  tranMemcpyLib__memcpy_sp_to_dram_loop.writeAction(f"__while_memcpy_sp_to_dram_loop_1_body: addi X19 X24 0") 
  tranMemcpyLib__memcpy_sp_to_dram_loop.writeAction(f"addi X21 X25 0") 
  tranMemcpyLib__memcpy_sp_to_dram_loop.writeAction(f"addi X18 X26 8") 
  tranMemcpyLib__memcpy_sp_to_dram_loop.writeAction(f"bgtu X26 X20 __if_memcpy_sp_to_dram_loop_4_false") 
  ## print("sending 8");
  tranMemcpyLib__memcpy_sp_to_dram_loop.writeAction(f"__if_memcpy_sp_to_dram_loop_3_true: send_dmlm_wret X25 MemcpyLib::memcpy_sp_to_dram_ret8 X24 8 X26") 
  tranMemcpyLib__memcpy_sp_to_dram_loop.writeAction(f"addi X19 X19 64") 
  tranMemcpyLib__memcpy_sp_to_dram_loop.writeAction(f"addi X21 X21 64") 
  tranMemcpyLib__memcpy_sp_to_dram_loop.writeAction(f"addi X16 X16 8") 
  tranMemcpyLib__memcpy_sp_to_dram_loop.writeAction(f"addi X18 X18 8") 
  tranMemcpyLib__memcpy_sp_to_dram_loop.writeAction(f"addi X23 X23 1") 
  tranMemcpyLib__memcpy_sp_to_dram_loop.writeAction(f"jmp __if_memcpy_sp_to_dram_loop_5_post") 
  ## print("sending 1");
  tranMemcpyLib__memcpy_sp_to_dram_loop.writeAction(f"__if_memcpy_sp_to_dram_loop_4_false: send_dmlm_wret X25 MemcpyLib::memcpy_sp_to_dram_ret X24 1 X26") 
  tranMemcpyLib__memcpy_sp_to_dram_loop.writeAction(f"addi X19 X19 8") 
  tranMemcpyLib__memcpy_sp_to_dram_loop.writeAction(f"addi X21 X21 8") 
  tranMemcpyLib__memcpy_sp_to_dram_loop.writeAction(f"addi X16 X16 1") 
  tranMemcpyLib__memcpy_sp_to_dram_loop.writeAction(f"addi X18 X18 1") 
  tranMemcpyLib__memcpy_sp_to_dram_loop.writeAction(f"addi X23 X23 1") 
  tranMemcpyLib__memcpy_sp_to_dram_loop.writeAction(f"__if_memcpy_sp_to_dram_loop_5_post: jmp __while_memcpy_sp_to_dram_loop_0_condition") 
  ## print("after sending: out_cnt = %d", out_cnt);
  tranMemcpyLib__memcpy_sp_to_dram_loop.writeAction(f"__while_memcpy_sp_to_dram_loop_2_post: movrl X23 120(X22) 0 8") 
  tranMemcpyLib__memcpy_sp_to_dram_loop.writeAction(f"bleu X20 X18 __if_memcpy_sp_to_dram_loop_8_post") 
  tranMemcpyLib__memcpy_sp_to_dram_loop.writeAction(f"__if_memcpy_sp_to_dram_loop_6_true: evi X2 X24 MemcpyLib::memcpy_sp_to_dram_loop 1") 
  tranMemcpyLib__memcpy_sp_to_dram_loop.writeAction(f"movir X25 0") 
  tranMemcpyLib__memcpy_sp_to_dram_loop.writeAction(f"movir X26 -1") 
  tranMemcpyLib__memcpy_sp_to_dram_loop.writeAction(f"sri X26 X26 1") 
  tranMemcpyLib__memcpy_sp_to_dram_loop.writeAction(f"sendr_wcont X24 X26 X25 X25") 
  tranMemcpyLib__memcpy_sp_to_dram_loop.writeAction(f"yield") 
  tranMemcpyLib__memcpy_sp_to_dram_loop.writeAction(f"__if_memcpy_sp_to_dram_loop_8_post: yield") 
  
  # Writing code for event MemcpyLib::memcpy_sp_to_dram_ret
  tranMemcpyLib__memcpy_sp_to_dram_ret = efa.writeEvent('MemcpyLib::memcpy_sp_to_dram_ret')
  tranMemcpyLib__memcpy_sp_to_dram_ret.writeAction(f"entry: addi X7 X22 20000") 
  tranMemcpyLib__memcpy_sp_to_dram_ret.writeAction(f"movlr 120(X22) X24 0 8") 
  tranMemcpyLib__memcpy_sp_to_dram_ret.writeAction(f"subi X24 X25 1") 
  tranMemcpyLib__memcpy_sp_to_dram_ret.writeAction(f"movrl X25 120(X22) 0 8") 
  tranMemcpyLib__memcpy_sp_to_dram_ret.writeAction(f"subi X16 X16 1") 
  ## print("getting write 1");
  tranMemcpyLib__memcpy_sp_to_dram_ret.writeAction(f"ceq X18 X20 X23") 
  tranMemcpyLib__memcpy_sp_to_dram_ret.writeAction(f"ceqi X16 X24 0") 
  tranMemcpyLib__memcpy_sp_to_dram_ret.writeAction(f"and X23 X24 X25") 
  tranMemcpyLib__memcpy_sp_to_dram_ret.writeAction(f"beqiu X25 0 __if_memcpy_sp_to_dram_ret_2_post") 
  tranMemcpyLib__memcpy_sp_to_dram_ret.writeAction(f"__if_memcpy_sp_to_dram_ret_0_true: movir X23 0") 
  tranMemcpyLib__memcpy_sp_to_dram_ret.writeAction(f"movir X24 -1") 
  tranMemcpyLib__memcpy_sp_to_dram_ret.writeAction(f"sri X24 X24 1") 
  tranMemcpyLib__memcpy_sp_to_dram_ret.writeAction(f"sendr_wcont X1 X24 X23 X23") 
  tranMemcpyLib__memcpy_sp_to_dram_ret.writeAction(f"yield_terminate") 
  tranMemcpyLib__memcpy_sp_to_dram_ret.writeAction(f"__if_memcpy_sp_to_dram_ret_2_post: yield") 
  
  # Writing code for event MemcpyLib::memcpy_sp_to_dram_ret8
  tranMemcpyLib__memcpy_sp_to_dram_ret8 = efa.writeEvent('MemcpyLib::memcpy_sp_to_dram_ret8')
  tranMemcpyLib__memcpy_sp_to_dram_ret8.writeAction(f"entry: addi X7 X22 20000") 
  tranMemcpyLib__memcpy_sp_to_dram_ret8.writeAction(f"movlr 120(X22) X24 0 8") 
  tranMemcpyLib__memcpy_sp_to_dram_ret8.writeAction(f"subi X24 X25 1") 
  tranMemcpyLib__memcpy_sp_to_dram_ret8.writeAction(f"movrl X25 120(X22) 0 8") 
  tranMemcpyLib__memcpy_sp_to_dram_ret8.writeAction(f"subi X16 X16 8") 
  ## print("getting write 8");
  tranMemcpyLib__memcpy_sp_to_dram_ret8.writeAction(f"ceq X18 X20 X23") 
  tranMemcpyLib__memcpy_sp_to_dram_ret8.writeAction(f"ceqi X16 X24 0") 
  tranMemcpyLib__memcpy_sp_to_dram_ret8.writeAction(f"and X23 X24 X25") 
  tranMemcpyLib__memcpy_sp_to_dram_ret8.writeAction(f"beqiu X25 0 __if_memcpy_sp_to_dram_ret8_2_post") 
  tranMemcpyLib__memcpy_sp_to_dram_ret8.writeAction(f"__if_memcpy_sp_to_dram_ret8_0_true: movir X23 0") 
  tranMemcpyLib__memcpy_sp_to_dram_ret8.writeAction(f"movir X24 -1") 
  tranMemcpyLib__memcpy_sp_to_dram_ret8.writeAction(f"sri X24 X24 1") 
  tranMemcpyLib__memcpy_sp_to_dram_ret8.writeAction(f"sendr_wcont X1 X24 X23 X23") 
  tranMemcpyLib__memcpy_sp_to_dram_ret8.writeAction(f"yield_terminate") 
  tranMemcpyLib__memcpy_sp_to_dram_ret8.writeAction(f"__if_memcpy_sp_to_dram_ret8_2_post: yield") 
  
  # Writing code for event MemcpyLib::memcpy_dram_to_dram
  tranMemcpyLib__memcpy_dram_to_dram = efa.writeEvent('MemcpyLib::memcpy_dram_to_dram')
  tranMemcpyLib__memcpy_dram_to_dram.writeAction(f"entry: sub X9 X8 X17") 
  tranMemcpyLib__memcpy_dram_to_dram.writeAction(f"addi X10 X20 0") 
  tranMemcpyLib__memcpy_dram_to_dram.writeAction(f"addi X8 X19 0") 
  tranMemcpyLib__memcpy_dram_to_dram.writeAction(f"movir X16 0") 
  tranMemcpyLib__memcpy_dram_to_dram.writeAction(f"movir X18 0") 
  tranMemcpyLib__memcpy_dram_to_dram.writeAction(f"evi X2 X22 MemcpyLib::memcpy_dram_to_dram_loop 1") 
  tranMemcpyLib__memcpy_dram_to_dram.writeAction(f"movir X23 0") 
  tranMemcpyLib__memcpy_dram_to_dram.writeAction(f"movir X24 -1") 
  tranMemcpyLib__memcpy_dram_to_dram.writeAction(f"sri X24 X24 1") 
  tranMemcpyLib__memcpy_dram_to_dram.writeAction(f"sendr_wcont X22 X24 X23 X23") 
  tranMemcpyLib__memcpy_dram_to_dram.writeAction(f"yield") 
  
  # Writing code for event MemcpyLib::memcpy_dram_to_dram_loop
  tranMemcpyLib__memcpy_dram_to_dram_loop = efa.writeEvent('MemcpyLib::memcpy_dram_to_dram_loop')
  tranMemcpyLib__memcpy_dram_to_dram_loop.writeAction(f"entry: addi X7 X22 20000") 
  tranMemcpyLib__memcpy_dram_to_dram_loop.writeAction(f"movlr 120(X22) X23 0 8") 
  ## print("dram_to_dram: out_cnt = %d", out_cnt);
  tranMemcpyLib__memcpy_dram_to_dram_loop.writeAction(f"__while_memcpy_dram_to_dram_loop_0_condition: movir X24 152") 
  tranMemcpyLib__memcpy_dram_to_dram_loop.writeAction(f"sli X24 X24 16") 
  tranMemcpyLib__memcpy_dram_to_dram_loop.writeAction(f"ori X24 X24 38528") 
  tranMemcpyLib__memcpy_dram_to_dram_loop.writeAction(f"clt X23 X24 X24") 
  tranMemcpyLib__memcpy_dram_to_dram_loop.writeAction(f"clt X18 X20 X25") 
  tranMemcpyLib__memcpy_dram_to_dram_loop.writeAction(f"and X24 X25 X26") 
  tranMemcpyLib__memcpy_dram_to_dram_loop.writeAction(f"beqiu X26 0 __while_memcpy_dram_to_dram_loop_2_post") 
  tranMemcpyLib__memcpy_dram_to_dram_loop.writeAction(f"__while_memcpy_dram_to_dram_loop_1_body: addi X19 X24 0") 
  tranMemcpyLib__memcpy_dram_to_dram_loop.writeAction(f"addi X18 X25 8") 
  tranMemcpyLib__memcpy_dram_to_dram_loop.writeAction(f"bgtu X25 X20 __if_memcpy_dram_to_dram_loop_4_false") 
  ## print("sending 8");
  tranMemcpyLib__memcpy_dram_to_dram_loop.writeAction(f"__if_memcpy_dram_to_dram_loop_3_true: send_dmlm_ld_wret X24 MemcpyLib::memcpy_dram_to_dram_ret8 8 X25") 
  tranMemcpyLib__memcpy_dram_to_dram_loop.writeAction(f"addi X19 X19 64") 
  tranMemcpyLib__memcpy_dram_to_dram_loop.writeAction(f"addi X16 X16 8") 
  tranMemcpyLib__memcpy_dram_to_dram_loop.writeAction(f"addi X18 X18 8") 
  tranMemcpyLib__memcpy_dram_to_dram_loop.writeAction(f"addi X23 X23 1") 
  tranMemcpyLib__memcpy_dram_to_dram_loop.writeAction(f"jmp __if_memcpy_dram_to_dram_loop_5_post") 
  ## print("sending 1");
  tranMemcpyLib__memcpy_dram_to_dram_loop.writeAction(f"__if_memcpy_dram_to_dram_loop_4_false: send_dmlm_ld_wret X24 MemcpyLib::memcpy_dram_to_dram_ret 1 X25") 
  tranMemcpyLib__memcpy_dram_to_dram_loop.writeAction(f"addi X19 X19 8") 
  tranMemcpyLib__memcpy_dram_to_dram_loop.writeAction(f"addi X16 X16 1") 
  tranMemcpyLib__memcpy_dram_to_dram_loop.writeAction(f"addi X18 X18 1") 
  tranMemcpyLib__memcpy_dram_to_dram_loop.writeAction(f"addi X23 X23 1") 
  tranMemcpyLib__memcpy_dram_to_dram_loop.writeAction(f"__if_memcpy_dram_to_dram_loop_5_post: jmp __while_memcpy_dram_to_dram_loop_0_condition") 
  ## print("after sending: out_cnt = %d", out_cnt);
  tranMemcpyLib__memcpy_dram_to_dram_loop.writeAction(f"__while_memcpy_dram_to_dram_loop_2_post: movrl X23 120(X22) 0 8") 
  tranMemcpyLib__memcpy_dram_to_dram_loop.writeAction(f"bleu X20 X18 __if_memcpy_dram_to_dram_loop_8_post") 
  tranMemcpyLib__memcpy_dram_to_dram_loop.writeAction(f"__if_memcpy_dram_to_dram_loop_6_true: evi X2 X24 MemcpyLib::memcpy_dram_to_dram_loop 1") 
  tranMemcpyLib__memcpy_dram_to_dram_loop.writeAction(f"movir X25 0") 
  tranMemcpyLib__memcpy_dram_to_dram_loop.writeAction(f"movir X26 -1") 
  tranMemcpyLib__memcpy_dram_to_dram_loop.writeAction(f"sri X26 X26 1") 
  tranMemcpyLib__memcpy_dram_to_dram_loop.writeAction(f"sendr_wcont X24 X26 X25 X25") 
  tranMemcpyLib__memcpy_dram_to_dram_loop.writeAction(f"yield") 
  tranMemcpyLib__memcpy_dram_to_dram_loop.writeAction(f"__if_memcpy_dram_to_dram_loop_8_post: yield") 
  
  # Writing code for event MemcpyLib::memcpy_dram_to_dram_ret
  tranMemcpyLib__memcpy_dram_to_dram_ret = efa.writeEvent('MemcpyLib::memcpy_dram_to_dram_ret')
  tranMemcpyLib__memcpy_dram_to_dram_ret.writeAction(f"entry: add X9 X17 X22") 
  tranMemcpyLib__memcpy_dram_to_dram_ret.writeAction(f"sendr_dmlm_wret X22 MemcpyLib::memcpy_dram_to_dram_write_ret X8 X23") 
  tranMemcpyLib__memcpy_dram_to_dram_ret.writeAction(f"yield") 
  
  # Writing code for event MemcpyLib::memcpy_dram_to_dram_ret8
  tranMemcpyLib__memcpy_dram_to_dram_ret8 = efa.writeEvent('MemcpyLib::memcpy_dram_to_dram_ret8')
  tranMemcpyLib__memcpy_dram_to_dram_ret8.writeAction(f"entry: add X3 X17 X22") 
  tranMemcpyLib__memcpy_dram_to_dram_ret8.writeAction(f"sendops_dmlm_wret X22 MemcpyLib::memcpy_dram_to_dram_write_ret8 X8 8 X23") 
  tranMemcpyLib__memcpy_dram_to_dram_ret8.writeAction(f"yield") 
  
  # Writing code for event MemcpyLib::memcpy_dram_to_dram_write_ret
  tranMemcpyLib__memcpy_dram_to_dram_write_ret = efa.writeEvent('MemcpyLib::memcpy_dram_to_dram_write_ret')
  tranMemcpyLib__memcpy_dram_to_dram_write_ret.writeAction(f"entry: addi X7 X22 20000") 
  tranMemcpyLib__memcpy_dram_to_dram_write_ret.writeAction(f"movlr 120(X22) X24 0 8") 
  tranMemcpyLib__memcpy_dram_to_dram_write_ret.writeAction(f"subi X24 X25 1") 
  tranMemcpyLib__memcpy_dram_to_dram_write_ret.writeAction(f"movrl X25 120(X22) 0 8") 
  tranMemcpyLib__memcpy_dram_to_dram_write_ret.writeAction(f"subi X16 X16 1") 
  tranMemcpyLib__memcpy_dram_to_dram_write_ret.writeAction(f"ceq X18 X20 X23") 
  tranMemcpyLib__memcpy_dram_to_dram_write_ret.writeAction(f"ceqi X16 X24 0") 
  tranMemcpyLib__memcpy_dram_to_dram_write_ret.writeAction(f"and X23 X24 X25") 
  tranMemcpyLib__memcpy_dram_to_dram_write_ret.writeAction(f"beqiu X25 0 __if_memcpy_dram_to_dram_write_ret_2_post") 
  tranMemcpyLib__memcpy_dram_to_dram_write_ret.writeAction(f"__if_memcpy_dram_to_dram_write_ret_0_true: movir X23 0") 
  tranMemcpyLib__memcpy_dram_to_dram_write_ret.writeAction(f"movir X24 -1") 
  tranMemcpyLib__memcpy_dram_to_dram_write_ret.writeAction(f"sri X24 X24 1") 
  tranMemcpyLib__memcpy_dram_to_dram_write_ret.writeAction(f"sendr_wcont X1 X24 X23 X23") 
  tranMemcpyLib__memcpy_dram_to_dram_write_ret.writeAction(f"yield_terminate") 
  tranMemcpyLib__memcpy_dram_to_dram_write_ret.writeAction(f"__if_memcpy_dram_to_dram_write_ret_2_post: yield") 
  
  # Writing code for event MemcpyLib::memcpy_dram_to_dram_write_ret8
  tranMemcpyLib__memcpy_dram_to_dram_write_ret8 = efa.writeEvent('MemcpyLib::memcpy_dram_to_dram_write_ret8')
  tranMemcpyLib__memcpy_dram_to_dram_write_ret8.writeAction(f"entry: addi X7 X22 20000") 
  tranMemcpyLib__memcpy_dram_to_dram_write_ret8.writeAction(f"movlr 120(X22) X24 0 8") 
  tranMemcpyLib__memcpy_dram_to_dram_write_ret8.writeAction(f"subi X24 X25 1") 
  tranMemcpyLib__memcpy_dram_to_dram_write_ret8.writeAction(f"movrl X25 120(X22) 0 8") 
  tranMemcpyLib__memcpy_dram_to_dram_write_ret8.writeAction(f"subi X16 X16 8") 
  tranMemcpyLib__memcpy_dram_to_dram_write_ret8.writeAction(f"ceq X18 X20 X23") 
  tranMemcpyLib__memcpy_dram_to_dram_write_ret8.writeAction(f"ceqi X16 X24 0") 
  tranMemcpyLib__memcpy_dram_to_dram_write_ret8.writeAction(f"and X23 X24 X25") 
  tranMemcpyLib__memcpy_dram_to_dram_write_ret8.writeAction(f"beqiu X25 0 __if_memcpy_dram_to_dram_write_ret8_2_post") 
  tranMemcpyLib__memcpy_dram_to_dram_write_ret8.writeAction(f"__if_memcpy_dram_to_dram_write_ret8_0_true: movir X23 0") 
  tranMemcpyLib__memcpy_dram_to_dram_write_ret8.writeAction(f"movir X24 -1") 
  tranMemcpyLib__memcpy_dram_to_dram_write_ret8.writeAction(f"sri X24 X24 1") 
  tranMemcpyLib__memcpy_dram_to_dram_write_ret8.writeAction(f"sendr_wcont X1 X24 X23 X23") 
  tranMemcpyLib__memcpy_dram_to_dram_write_ret8.writeAction(f"yield_terminate") 
  tranMemcpyLib__memcpy_dram_to_dram_write_ret8.writeAction(f"__if_memcpy_dram_to_dram_write_ret8_2_post: yield") 
  
  
  ##################################################
  ###### Writing code for thread MemcpyLibOld ######
  ##################################################
  ## let this thread handle all memory copy operations
  ## and we can limit outstanding loads here
  # Writing code for event MemcpyLibOld::memcpy_dram_to_sp
  tranMemcpyLibOld__memcpy_dram_to_sp = efa.writeEvent('MemcpyLibOld::memcpy_dram_to_sp')
  tranMemcpyLibOld__memcpy_dram_to_sp.writeAction(f"entry: addi X8 X18 0") 
  tranMemcpyLibOld__memcpy_dram_to_sp.writeAction(f"sub X9 X8 X17") 
  tranMemcpyLibOld__memcpy_dram_to_sp.writeAction(f"movir X16 0") 
  tranMemcpyLibOld__memcpy_dram_to_sp.writeAction(f"__for_memcpy_dram_to_sp_0_condition: bleu X10 X16 __for_memcpy_dram_to_sp_2_post") 
  tranMemcpyLibOld__memcpy_dram_to_sp.writeAction(f"__for_memcpy_dram_to_sp_1_body: send_dmlm_ld_wret X18 MemcpyLibOld::memcpy_dram_to_sp_ret 1 X19") 
  tranMemcpyLibOld__memcpy_dram_to_sp.writeAction(f"addi X18 X18 8") 
  tranMemcpyLibOld__memcpy_dram_to_sp.writeAction(f"addi X16 X16 1") 
  tranMemcpyLibOld__memcpy_dram_to_sp.writeAction(f"jmp __for_memcpy_dram_to_sp_0_condition") 
  tranMemcpyLibOld__memcpy_dram_to_sp.writeAction(f"__for_memcpy_dram_to_sp_2_post: yield") 
  
  # Writing code for event MemcpyLibOld::memcpy_dram_to_sp_ret
  tranMemcpyLibOld__memcpy_dram_to_sp_ret = efa.writeEvent('MemcpyLibOld::memcpy_dram_to_sp_ret')
  ## copyOperands(op0, lmbase, 8); ???
  tranMemcpyLibOld__memcpy_dram_to_sp_ret.writeAction(f"entry: add X9 X17 X18") 
  tranMemcpyLibOld__memcpy_dram_to_sp_ret.writeAction(f"movrl X8 0(X18) 0 8") 
  ## print("getting %lu", val);
  tranMemcpyLibOld__memcpy_dram_to_sp_ret.writeAction(f"subi X16 X16 1") 
  tranMemcpyLibOld__memcpy_dram_to_sp_ret.writeAction(f"bneiu X16 0 __if_memcpy_dram_to_sp_ret_2_post") 
  tranMemcpyLibOld__memcpy_dram_to_sp_ret.writeAction(f"__if_memcpy_dram_to_sp_ret_0_true: movir X19 0") 
  tranMemcpyLibOld__memcpy_dram_to_sp_ret.writeAction(f"movir X20 -1") 
  tranMemcpyLibOld__memcpy_dram_to_sp_ret.writeAction(f"sri X20 X20 1") 
  tranMemcpyLibOld__memcpy_dram_to_sp_ret.writeAction(f"sendr_wcont X1 X20 X19 X19") 
  tranMemcpyLibOld__memcpy_dram_to_sp_ret.writeAction(f"yield_terminate") 
  tranMemcpyLibOld__memcpy_dram_to_sp_ret.writeAction(f"__if_memcpy_dram_to_sp_ret_2_post: yield") 
  
  # Writing code for event MemcpyLibOld::memcpy_dram_to_sp_ret8
  tranMemcpyLibOld__memcpy_dram_to_sp_ret8 = efa.writeEvent('MemcpyLibOld::memcpy_dram_to_sp_ret8')
  tranMemcpyLibOld__memcpy_dram_to_sp_ret8.writeAction(f"entry: add X3 X17 X18") 
  tranMemcpyLibOld__memcpy_dram_to_sp_ret8.writeAction(f"bcpyoli X8 X18 8") 
  tranMemcpyLibOld__memcpy_dram_to_sp_ret8.writeAction(f"subi X16 X16 8") 
  tranMemcpyLibOld__memcpy_dram_to_sp_ret8.writeAction(f"bneiu X16 0 __if_memcpy_dram_to_sp_ret8_2_post") 
  tranMemcpyLibOld__memcpy_dram_to_sp_ret8.writeAction(f"__if_memcpy_dram_to_sp_ret8_0_true: movir X19 0") 
  tranMemcpyLibOld__memcpy_dram_to_sp_ret8.writeAction(f"movir X20 -1") 
  tranMemcpyLibOld__memcpy_dram_to_sp_ret8.writeAction(f"sri X20 X20 1") 
  tranMemcpyLibOld__memcpy_dram_to_sp_ret8.writeAction(f"sendr_wcont X1 X20 X19 X19") 
  tranMemcpyLibOld__memcpy_dram_to_sp_ret8.writeAction(f"yield_terminate") 
  tranMemcpyLibOld__memcpy_dram_to_sp_ret8.writeAction(f"__if_memcpy_dram_to_sp_ret8_2_post: yield") 
  
  # Writing code for event MemcpyLibOld::memcpy_sp_to_dram
  tranMemcpyLibOld__memcpy_sp_to_dram = efa.writeEvent('MemcpyLibOld::memcpy_sp_to_dram')
  tranMemcpyLibOld__memcpy_sp_to_dram.writeAction(f"entry: addi X8 X18 0") 
  tranMemcpyLibOld__memcpy_sp_to_dram.writeAction(f"addi X9 X19 0") 
  tranMemcpyLibOld__memcpy_sp_to_dram.writeAction(f"movir X16 0") 
  tranMemcpyLibOld__memcpy_sp_to_dram.writeAction(f"__for_memcpy_sp_to_dram_0_condition: bleu X10 X16 __for_memcpy_sp_to_dram_2_post") 
  tranMemcpyLibOld__memcpy_sp_to_dram.writeAction(f"__for_memcpy_sp_to_dram_1_body: movlr 0(X18) X20 0 8") 
  tranMemcpyLibOld__memcpy_sp_to_dram.writeAction(f"sendr_dmlm_wret X19 MemcpyLibOld::memcpy_sp_to_dram_ret X20 X21") 
  tranMemcpyLibOld__memcpy_sp_to_dram.writeAction(f"addi X18 X18 8") 
  tranMemcpyLibOld__memcpy_sp_to_dram.writeAction(f"addi X19 X19 8") 
  tranMemcpyLibOld__memcpy_sp_to_dram.writeAction(f"addi X16 X16 1") 
  tranMemcpyLibOld__memcpy_sp_to_dram.writeAction(f"jmp __for_memcpy_sp_to_dram_0_condition") 
  tranMemcpyLibOld__memcpy_sp_to_dram.writeAction(f"__for_memcpy_sp_to_dram_2_post: yield") 
  
  # Writing code for event MemcpyLibOld::memcpy_sp_to_dram_ret
  tranMemcpyLibOld__memcpy_sp_to_dram_ret = efa.writeEvent('MemcpyLibOld::memcpy_sp_to_dram_ret')
  tranMemcpyLibOld__memcpy_sp_to_dram_ret.writeAction(f"entry: subi X16 X16 1") 
  ## print("getting write 1");
  tranMemcpyLibOld__memcpy_sp_to_dram_ret.writeAction(f"bneiu X16 0 __if_memcpy_sp_to_dram_ret_2_post") 
  tranMemcpyLibOld__memcpy_sp_to_dram_ret.writeAction(f"__if_memcpy_sp_to_dram_ret_0_true: movir X18 0") 
  tranMemcpyLibOld__memcpy_sp_to_dram_ret.writeAction(f"movir X19 -1") 
  tranMemcpyLibOld__memcpy_sp_to_dram_ret.writeAction(f"sri X19 X19 1") 
  tranMemcpyLibOld__memcpy_sp_to_dram_ret.writeAction(f"sendr_wcont X1 X19 X18 X18") 
  tranMemcpyLibOld__memcpy_sp_to_dram_ret.writeAction(f"yield_terminate") 
  tranMemcpyLibOld__memcpy_sp_to_dram_ret.writeAction(f"__if_memcpy_sp_to_dram_ret_2_post: yield") 
  
  # Writing code for event MemcpyLibOld::memcpy_sp_to_dram_ret8
  tranMemcpyLibOld__memcpy_sp_to_dram_ret8 = efa.writeEvent('MemcpyLibOld::memcpy_sp_to_dram_ret8')
  tranMemcpyLibOld__memcpy_sp_to_dram_ret8.writeAction(f"entry: subi X16 X16 8") 
  ## print("getting write 8");
  tranMemcpyLibOld__memcpy_sp_to_dram_ret8.writeAction(f"bneiu X16 0 __if_memcpy_sp_to_dram_ret8_2_post") 
  tranMemcpyLibOld__memcpy_sp_to_dram_ret8.writeAction(f"__if_memcpy_sp_to_dram_ret8_0_true: movir X18 0") 
  tranMemcpyLibOld__memcpy_sp_to_dram_ret8.writeAction(f"movir X19 -1") 
  tranMemcpyLibOld__memcpy_sp_to_dram_ret8.writeAction(f"sri X19 X19 1") 
  tranMemcpyLibOld__memcpy_sp_to_dram_ret8.writeAction(f"sendr_wcont X1 X19 X18 X18") 
  tranMemcpyLibOld__memcpy_sp_to_dram_ret8.writeAction(f"yield_terminate") 
  tranMemcpyLibOld__memcpy_sp_to_dram_ret8.writeAction(f"__if_memcpy_sp_to_dram_ret8_2_post: yield") 
  
  # Writing code for event MemcpyLibOld::memcpy_dram_to_dram
  tranMemcpyLibOld__memcpy_dram_to_dram = efa.writeEvent('MemcpyLibOld::memcpy_dram_to_dram')
  tranMemcpyLibOld__memcpy_dram_to_dram.writeAction(f"entry: addi X8 X18 0") 
  tranMemcpyLibOld__memcpy_dram_to_dram.writeAction(f"sub X9 X8 X17") 
  tranMemcpyLibOld__memcpy_dram_to_dram.writeAction(f"movir X16 0") 
  tranMemcpyLibOld__memcpy_dram_to_dram.writeAction(f"__for_memcpy_dram_to_dram_0_condition: bleu X10 X16 __for_memcpy_dram_to_dram_2_post") 
  tranMemcpyLibOld__memcpy_dram_to_dram.writeAction(f"__for_memcpy_dram_to_dram_1_body: send_dmlm_ld_wret X18 MemcpyLibOld::memcpy_dram_to_dram_ret 1 X19") 
  tranMemcpyLibOld__memcpy_dram_to_dram.writeAction(f"addi X18 X18 8") 
  tranMemcpyLibOld__memcpy_dram_to_dram.writeAction(f"addi X16 X16 1") 
  tranMemcpyLibOld__memcpy_dram_to_dram.writeAction(f"jmp __for_memcpy_dram_to_dram_0_condition") 
  tranMemcpyLibOld__memcpy_dram_to_dram.writeAction(f"__for_memcpy_dram_to_dram_2_post: yield") 
  
  # Writing code for event MemcpyLibOld::memcpy_dram_to_dram_ret
  tranMemcpyLibOld__memcpy_dram_to_dram_ret = efa.writeEvent('MemcpyLibOld::memcpy_dram_to_dram_ret')
  tranMemcpyLibOld__memcpy_dram_to_dram_ret.writeAction(f"entry: add X9 X17 X18") 
  tranMemcpyLibOld__memcpy_dram_to_dram_ret.writeAction(f"sendr_dmlm_wret X18 MemcpyLibOld::memcpy_dram_to_dram_write_ret X8 X19") 
  tranMemcpyLibOld__memcpy_dram_to_dram_ret.writeAction(f"yield") 
  
  # Writing code for event MemcpyLibOld::memcpy_dram_to_dram_ret8
  tranMemcpyLibOld__memcpy_dram_to_dram_ret8 = efa.writeEvent('MemcpyLibOld::memcpy_dram_to_dram_ret8')
  tranMemcpyLibOld__memcpy_dram_to_dram_ret8.writeAction(f"entry: add X3 X17 X18") 
  tranMemcpyLibOld__memcpy_dram_to_dram_ret8.writeAction(f"sendops_dmlm_wret X18 MemcpyLibOld::memcpy_dram_to_dram_write_ret8 X8 8 X19") 
  tranMemcpyLibOld__memcpy_dram_to_dram_ret8.writeAction(f"yield") 
  
  # Writing code for event MemcpyLibOld::memcpy_dram_to_dram_write_ret
  tranMemcpyLibOld__memcpy_dram_to_dram_write_ret = efa.writeEvent('MemcpyLibOld::memcpy_dram_to_dram_write_ret')
  tranMemcpyLibOld__memcpy_dram_to_dram_write_ret.writeAction(f"entry: subi X16 X16 1") 
  tranMemcpyLibOld__memcpy_dram_to_dram_write_ret.writeAction(f"bneiu X16 0 __if_memcpy_dram_to_dram_write_ret_2_post") 
  tranMemcpyLibOld__memcpy_dram_to_dram_write_ret.writeAction(f"__if_memcpy_dram_to_dram_write_ret_0_true: movir X18 0") 
  tranMemcpyLibOld__memcpy_dram_to_dram_write_ret.writeAction(f"movir X19 -1") 
  tranMemcpyLibOld__memcpy_dram_to_dram_write_ret.writeAction(f"sri X19 X19 1") 
  tranMemcpyLibOld__memcpy_dram_to_dram_write_ret.writeAction(f"sendr_wcont X1 X19 X18 X18") 
  tranMemcpyLibOld__memcpy_dram_to_dram_write_ret.writeAction(f"yield_terminate") 
  tranMemcpyLibOld__memcpy_dram_to_dram_write_ret.writeAction(f"__if_memcpy_dram_to_dram_write_ret_2_post: yield") 
  
  # Writing code for event MemcpyLibOld::memcpy_dram_to_dram_write_ret8
  tranMemcpyLibOld__memcpy_dram_to_dram_write_ret8 = efa.writeEvent('MemcpyLibOld::memcpy_dram_to_dram_write_ret8')
  tranMemcpyLibOld__memcpy_dram_to_dram_write_ret8.writeAction(f"entry: subi X16 X16 8") 
  tranMemcpyLibOld__memcpy_dram_to_dram_write_ret8.writeAction(f"bneiu X16 0 __if_memcpy_dram_to_dram_write_ret8_2_post") 
  tranMemcpyLibOld__memcpy_dram_to_dram_write_ret8.writeAction(f"__if_memcpy_dram_to_dram_write_ret8_0_true: movir X18 0") 
  tranMemcpyLibOld__memcpy_dram_to_dram_write_ret8.writeAction(f"movir X19 -1") 
  tranMemcpyLibOld__memcpy_dram_to_dram_write_ret8.writeAction(f"sri X19 X19 1") 
  tranMemcpyLibOld__memcpy_dram_to_dram_write_ret8.writeAction(f"sendr_wcont X1 X19 X18 X18") 
  tranMemcpyLibOld__memcpy_dram_to_dram_write_ret8.writeAction(f"yield_terminate") 
  tranMemcpyLibOld__memcpy_dram_to_dram_write_ret8.writeAction(f"__if_memcpy_dram_to_dram_write_ret8_2_post: yield") 
  
  
  #######################################################
  ###### Writing code for thread ExternalMergeSort ######
  #######################################################
  ## sp_size is the number of words available in the scratchpad
  # Writing code for event ExternalMergeSort::sort
  tranExternalMergeSort__sort = efa.writeEvent('ExternalMergeSort::sort')
  tranExternalMergeSort__sort.writeAction(f"entry: addi X8 X16 0") 
  tranExternalMergeSort__sort.writeAction(f"addi X9 X18 0") 
  tranExternalMergeSort__sort.writeAction(f"addi X10 X17 0") 
  tranExternalMergeSort__sort.writeAction(f"addi X11 X19 0") 
  ## print("in external merge sort %lu %lu %lu %lu", list_dram_addr, list_size, sp_ptr, sp_size);
  ## print("in external merge sort");
  tranExternalMergeSort__sort.writeAction(f"evi X2 X23 ExternalMergeSort::phase1 1") 
  tranExternalMergeSort__sort.writeAction(f"addi X1 X21 0") 
  tranExternalMergeSort__sort.writeAction(f"movir X24 0") 
  tranExternalMergeSort__sort.writeAction(f"movir X25 -1") 
  tranExternalMergeSort__sort.writeAction(f"sri X25 X25 1") 
  tranExternalMergeSort__sort.writeAction(f"sendr_wcont X23 X25 X24 X24") 
  tranExternalMergeSort__sort.writeAction(f"yield") 
  
  # Writing code for event ExternalMergeSort::phase1
  tranExternalMergeSort__phase1 = efa.writeEvent('ExternalMergeSort::phase1')
  tranExternalMergeSort__phase1.writeAction(f"entry: movir X20 0") 
  tranExternalMergeSort__phase1.writeAction(f"evi X2 X23 ExternalMergeSort::phase1_main_loop 1") 
  tranExternalMergeSort__phase1.writeAction(f"movir X24 0") 
  tranExternalMergeSort__phase1.writeAction(f"movir X25 -1") 
  tranExternalMergeSort__phase1.writeAction(f"sri X25 X25 1") 
  tranExternalMergeSort__phase1.writeAction(f"sendr_wcont X23 X25 X24 X24") 
  tranExternalMergeSort__phase1.writeAction(f"yield") 
  
  # Writing code for event ExternalMergeSort::phase1_main_loop
  tranExternalMergeSort__phase1_main_loop = efa.writeEvent('ExternalMergeSort::phase1_main_loop')
  ## print("curidx = %d", cur_idx);
  ## print("cur_idx = %d, list_size = %d, sp_size = %d", cur_idx, list_size, sp_size);
  tranExternalMergeSort__phase1_main_loop.writeAction(f"entry: subi X18 X23 1") 
  tranExternalMergeSort__phase1_main_loop.writeAction(f"div X23 X19 X24") 
  tranExternalMergeSort__phase1_main_loop.writeAction(f"bgtu X20 X24 __if_phase1_main_loop_1_false") 
  tranExternalMergeSort__phase1_main_loop.writeAction(f"__if_phase1_main_loop_0_true: mul X20 X19 X23") 
  tranExternalMergeSort__phase1_main_loop.writeAction(f"addi X20 X25 1") 
  tranExternalMergeSort__phase1_main_loop.writeAction(f"mul X25 X19 X24") 
  tranExternalMergeSort__phase1_main_loop.writeAction(f"bleu X24 X18 __if_phase1_main_loop_5_post") 
  tranExternalMergeSort__phase1_main_loop.writeAction(f"__if_phase1_main_loop_3_true: addi X18 X24 0") 
  tranExternalMergeSort__phase1_main_loop.writeAction(f"__if_phase1_main_loop_5_post: addi X20 X20 1") 
  ## unsigned long block_size = r - l;
  tranExternalMergeSort__phase1_main_loop.writeAction(f"sli X23 X26 3") 
  tranExternalMergeSort__phase1_main_loop.writeAction(f"add X16 X26 X25") 
  ## print("block_size = %d", block_size);
  tranExternalMergeSort__phase1_main_loop.writeAction(f"sub X24 X23 X24") 
  tranExternalMergeSort__phase1_main_loop.writeAction(f"evi X2 X26 DistributedSortPhase2LocalSortDRAM::init 1") 
  tranExternalMergeSort__phase1_main_loop.writeAction(f"sendr3_wret X26 ExternalMergeSort::phase1_main_loop X24 X17 X25 X27") 
  tranExternalMergeSort__phase1_main_loop.writeAction(f"jmp __if_phase1_main_loop_2_post") 
  tranExternalMergeSort__phase1_main_loop.writeAction(f"__if_phase1_main_loop_1_false: evi X2 X23 ExternalMergeSort::phase2 1") 
  tranExternalMergeSort__phase1_main_loop.writeAction(f"movir X24 0") 
  tranExternalMergeSort__phase1_main_loop.writeAction(f"movir X25 -1") 
  tranExternalMergeSort__phase1_main_loop.writeAction(f"sri X25 X25 1") 
  tranExternalMergeSort__phase1_main_loop.writeAction(f"sendr_wcont X23 X25 X24 X24") 
  ## send_event(save_cont, 0, IGNRCONT);
  tranExternalMergeSort__phase1_main_loop.writeAction(f"__if_phase1_main_loop_2_post: yield") 
  
  # Writing code for event ExternalMergeSort::phase2
  tranExternalMergeSort__phase2 = efa.writeEvent('ExternalMergeSort::phase2')
  tranExternalMergeSort__phase2.writeAction(f"entry: addi X17 X24 0") 
  tranExternalMergeSort__phase2.writeAction(f"movir X23 0") 
  tranExternalMergeSort__phase2.writeAction(f"__for_phase2_0_condition: bleu X19 X23 __for_phase2_2_post") 
  tranExternalMergeSort__phase2.writeAction(f"__for_phase2_1_body: movir X26 -1") 
  tranExternalMergeSort__phase2.writeAction(f"movwrl X26 X24(X23,0,0)") 
  tranExternalMergeSort__phase2.writeAction(f"addi X23 X23 1") 
  tranExternalMergeSort__phase2.writeAction(f"jmp __for_phase2_0_condition") 
  tranExternalMergeSort__phase2.writeAction(f"__for_phase2_2_post: addi X19 X22 0") 
  tranExternalMergeSort__phase2.writeAction(f"evi X2 X25 ExternalMergeSort::phase2_main_loop 1") 
  tranExternalMergeSort__phase2.writeAction(f"movir X26 0") 
  tranExternalMergeSort__phase2.writeAction(f"movir X27 -1") 
  tranExternalMergeSort__phase2.writeAction(f"sri X27 X27 1") 
  tranExternalMergeSort__phase2.writeAction(f"sendr_wcont X25 X27 X26 X26") 
  tranExternalMergeSort__phase2.writeAction(f"yield") 
  
  # Writing code for event ExternalMergeSort::phase2_main_loop
  tranExternalMergeSort__phase2_main_loop = efa.writeEvent('ExternalMergeSort::phase2_main_loop')
  tranExternalMergeSort__phase2_main_loop.writeAction(f"entry: bleu X18 X22 __if_phase2_main_loop_1_false") 
  tranExternalMergeSort__phase2_main_loop.writeAction(f"__if_phase2_main_loop_0_true: movir X20 0") 
  tranExternalMergeSort__phase2_main_loop.writeAction(f"evi X2 X23 ExternalMergeSort::phase2_inner_loop 1") 
  tranExternalMergeSort__phase2_main_loop.writeAction(f"movir X24 0") 
  tranExternalMergeSort__phase2_main_loop.writeAction(f"movir X25 -1") 
  tranExternalMergeSort__phase2_main_loop.writeAction(f"sri X25 X25 1") 
  tranExternalMergeSort__phase2_main_loop.writeAction(f"sendr_wcont X23 X25 X24 X24") 
  tranExternalMergeSort__phase2_main_loop.writeAction(f"jmp __if_phase2_main_loop_2_post") 
  tranExternalMergeSort__phase2_main_loop.writeAction(f"__if_phase2_main_loop_1_false: movir X23 0") 
  tranExternalMergeSort__phase2_main_loop.writeAction(f"movir X24 -1") 
  tranExternalMergeSort__phase2_main_loop.writeAction(f"sri X24 X24 1") 
  tranExternalMergeSort__phase2_main_loop.writeAction(f"sendr_wcont X21 X24 X23 X23") 
  tranExternalMergeSort__phase2_main_loop.writeAction(f"__if_phase2_main_loop_2_post: yield") 
  
  # Writing code for event ExternalMergeSort::phase2_inner_loop
  tranExternalMergeSort__phase2_inner_loop = efa.writeEvent('ExternalMergeSort::phase2_inner_loop')
  tranExternalMergeSort__phase2_inner_loop.writeAction(f"entry: add X20 X22 X23") 
  tranExternalMergeSort__phase2_inner_loop.writeAction(f"bleu X18 X23 __if_phase2_inner_loop_1_false") 
  ## pta = list_dram_addr + cur_idx * 8;
  ## ptb = list_dram_addr + (cur_idx + cur_block_size) * 8;
  ## print("merging %d %d with blocksize = %d", cur_idx, (cur_idx + cur_block_size), cur_block_size);
  ## unsigned long evw = evw_update_event(CEVNT, phase2_merger);
  tranExternalMergeSort__phase2_inner_loop.writeAction(f"__if_phase2_inner_loop_0_true: movir X23 0") 
  tranExternalMergeSort__phase2_inner_loop.writeAction(f"evlb X23 ExternalMerger::merger") 
  tranExternalMergeSort__phase2_inner_loop.writeAction(f"evi X23 X23 255 4") 
  tranExternalMergeSort__phase2_inner_loop.writeAction(f"ev X23 X23 X0 X0 8") 
  tranExternalMergeSort__phase2_inner_loop.writeAction(f"addi X7 X24 8") 
  tranExternalMergeSort__phase2_inner_loop.writeAction(f"sli X20 X26 3") 
  tranExternalMergeSort__phase2_inner_loop.writeAction(f"add X16 X26 X27") 
  tranExternalMergeSort__phase2_inner_loop.writeAction(f"movrl X27 0(X24) 0 8") 
  tranExternalMergeSort__phase2_inner_loop.writeAction(f"add X20 X22 X26") 
  tranExternalMergeSort__phase2_inner_loop.writeAction(f"sli X26 X27 3") 
  tranExternalMergeSort__phase2_inner_loop.writeAction(f"add X16 X27 X28") 
  tranExternalMergeSort__phase2_inner_loop.writeAction(f"movrl X28 8(X24) 0 8") 
  tranExternalMergeSort__phase2_inner_loop.writeAction(f"sli X22 X26 1") 
  tranExternalMergeSort__phase2_inner_loop.writeAction(f"add X20 X26 X25") 
  ## print("last = %d", last);
  tranExternalMergeSort__phase2_inner_loop.writeAction(f"bgtu X18 X25 __if_phase2_inner_loop_5_post") 
  tranExternalMergeSort__phase2_inner_loop.writeAction(f"__if_phase2_inner_loop_3_true: addi X18 X25 0") 
  tranExternalMergeSort__phase2_inner_loop.writeAction(f"__if_phase2_inner_loop_5_post: sli X25 X27 3") 
  tranExternalMergeSort__phase2_inner_loop.writeAction(f"add X16 X27 X28") 
  tranExternalMergeSort__phase2_inner_loop.writeAction(f"movrl X28 16(X24) 0 8") 
  tranExternalMergeSort__phase2_inner_loop.writeAction(f"movrl X17 24(X24) 0 8") 
  tranExternalMergeSort__phase2_inner_loop.writeAction(f"movrl X19 32(X24) 0 8") 
  tranExternalMergeSort__phase2_inner_loop.writeAction(f"sli X18 X27 3") 
  tranExternalMergeSort__phase2_inner_loop.writeAction(f"add X16 X27 X28") 
  tranExternalMergeSort__phase2_inner_loop.writeAction(f"movrl X28 40(X24) 0 8") 
  tranExternalMergeSort__phase2_inner_loop.writeAction(f"send_wret X23 ExternalMergeSort::phase2_inner_loop X24 6 X26") 
  tranExternalMergeSort__phase2_inner_loop.writeAction(f"sli X22 X26 1") 
  tranExternalMergeSort__phase2_inner_loop.writeAction(f"add X20 X26 X20") 
  tranExternalMergeSort__phase2_inner_loop.writeAction(f"jmp __if_phase2_inner_loop_2_post") 
  tranExternalMergeSort__phase2_inner_loop.writeAction(f"__if_phase2_inner_loop_1_false: evi X2 X23 ExternalMergeSort::phase2_main_loop 1") 
  tranExternalMergeSort__phase2_inner_loop.writeAction(f"movir X24 0") 
  tranExternalMergeSort__phase2_inner_loop.writeAction(f"movir X25 -1") 
  tranExternalMergeSort__phase2_inner_loop.writeAction(f"sri X25 X25 1") 
  tranExternalMergeSort__phase2_inner_loop.writeAction(f"sendr_wcont X23 X25 X24 X24") 
  tranExternalMergeSort__phase2_inner_loop.writeAction(f"muli X22 X22 2") 
  tranExternalMergeSort__phase2_inner_loop.writeAction(f"__if_phase2_inner_loop_2_post: yield") 
  
  
  ####################################################
  ###### Writing code for thread ExternalMerger ######
  ####################################################
  # Writing code for event ExternalMerger::merger
  tranExternalMerger__merger = efa.writeEvent('ExternalMerger::merger')
  ## send_event(CCONT, 0, IGNRCONT);
  ## print("in merger %lu %lu %lu %lu %lu", p0, p1, p2, sp_ptr, sp_size);
  tranExternalMerger__merger.writeAction(f"entry: sub X10 X8 X27") 
  tranExternalMerger__merger.writeAction(f"sari X27 X20 3") 
  tranExternalMerger__merger.writeAction(f"sari X12 X23 1") 
  tranExternalMerger__merger.writeAction(f"addi X8 X16 0") 
  tranExternalMerger__merger.writeAction(f"addi X9 X17 0") 
  tranExternalMerger__merger.writeAction(f"addi X9 X18 0") 
  tranExternalMerger__merger.writeAction(f"addi X10 X19 0") 
  tranExternalMerger__merger.writeAction(f"addi X13 X24 0") 
  tranExternalMerger__merger.writeAction(f"addi X11 X21 0") 
  tranExternalMerger__merger.writeAction(f"sli X23 X27 3") 
  tranExternalMerger__merger.writeAction(f"add X11 X27 X22") 
  tranExternalMerger__merger.writeAction(f"movir X26 0") 
  ## print("starting merging tot = %d", tot);
  ## // merging block A and B
  ## // let k = sp_size / 2;
  ## // sp_ptr[0...k-1] will be circular buffer for block A
  ## // sp_ptr[k, 2k-1] will be circular buffer for block B
  ## // pull the circular buffer
  tranExternalMerger__merger.writeAction(f"movir X25 0") 
  tranExternalMerger__merger.writeAction(f"addi X16 X27 0") 
  tranExternalMerger__merger.writeAction(f"movir X28 0") 
  tranExternalMerger__merger.writeAction(f"__for_merger_0_condition: addi X23 X29 0")  # This is for casting. May be used later on
  tranExternalMerger__merger.writeAction(f"ble X29 X28 __for_merger_2_post") 
  tranExternalMerger__merger.writeAction(f"__for_merger_1_body: send_dmlm_ld_wret X27 ExternalMerger::phase2_merger_load_a_ret 1 X29") 
  tranExternalMerger__merger.writeAction(f"addi X25 X25 1") 
  tranExternalMerger__merger.writeAction(f"addi X27 X27 8") 
  tranExternalMerger__merger.writeAction(f"addi X28 X28 1") 
  tranExternalMerger__merger.writeAction(f"jmp __for_merger_0_condition") 
  tranExternalMerger__merger.writeAction(f"__for_merger_2_post: sub X10 X9 X29") 
  tranExternalMerger__merger.writeAction(f"sari X29 X28 3") 
  tranExternalMerger__merger.writeAction(f"addi X18 X27 0") 
  tranExternalMerger__merger.writeAction(f"bleu X28 X23 __if_merger_5_post") 
  tranExternalMerger__merger.writeAction(f"__if_merger_3_true: addi X23 X28 0") 
  tranExternalMerger__merger.writeAction(f"__if_merger_5_post: movir X29 0") 
  tranExternalMerger__merger.writeAction(f"__for_merger_6_condition: addi X28 X30 0")  # This is for casting. May be used later on
  tranExternalMerger__merger.writeAction(f"ble X30 X29 __for_merger_8_post") 
  tranExternalMerger__merger.writeAction(f"__for_merger_7_body: send_dmlm_ld_wret X27 ExternalMerger::phase2_merger_load_b_ret 1 X30") 
  tranExternalMerger__merger.writeAction(f"addi X25 X25 1") 
  tranExternalMerger__merger.writeAction(f"addi X27 X27 8") 
  tranExternalMerger__merger.writeAction(f"addi X29 X29 1") 
  tranExternalMerger__merger.writeAction(f"jmp __for_merger_6_condition") 
  tranExternalMerger__merger.writeAction(f"__for_merger_8_post: yield") 
  
  # Writing code for event ExternalMerger::phase2_merger_load_a_ret
  tranExternalMerger__phase2_merger_load_a_ret = efa.writeEvent('ExternalMerger::phase2_merger_load_a_ret')
  tranExternalMerger__phase2_merger_load_a_ret.writeAction(f"entry: sari X9 X27 3") 
  tranExternalMerger__phase2_merger_load_a_ret.writeAction(f"mod X27 X23 X28") 
  tranExternalMerger__phase2_merger_load_a_ret.writeAction(f"movwrl X8 X21(X28,0,0)") 
  tranExternalMerger__phase2_merger_load_a_ret.writeAction(f"subi X25 X25 1") 
  tranExternalMerger__phase2_merger_load_a_ret.writeAction(f"movir X27 0") 
  tranExternalMerger__phase2_merger_load_a_ret.writeAction(f"andi X26 X28 1") 
  tranExternalMerger__phase2_merger_load_a_ret.writeAction(f"beqiu X28 0 __if_phase2_merger_load_a_ret_2_post") 
  tranExternalMerger__phase2_merger_load_a_ret.writeAction(f"__if_phase2_merger_load_a_ret_0_true: xori X26 X26 1") 
  tranExternalMerger__phase2_merger_load_a_ret.writeAction(f"movir X28 1024") 
  tranExternalMerger__phase2_merger_load_a_ret.writeAction(f"bneu X26 X28 __if_phase2_merger_load_a_ret_2_post") 
  tranExternalMerger__phase2_merger_load_a_ret.writeAction(f"__if_phase2_merger_load_a_ret_3_true: movir X27 1") 
  tranExternalMerger__phase2_merger_load_a_ret.writeAction(f"__if_phase2_merger_load_a_ret_2_post: ceqi X25 X28 0") 
  tranExternalMerger__phase2_merger_load_a_ret.writeAction(f"ceqi X26 X29 0") 
  tranExternalMerger__phase2_merger_load_a_ret.writeAction(f"and X28 X29 X30") 
  tranExternalMerger__phase2_merger_load_a_ret.writeAction(f"or X30 X27 X31") 
  tranExternalMerger__phase2_merger_load_a_ret.writeAction(f"beqiu X31 0 __if_phase2_merger_load_a_ret_8_post") 
  tranExternalMerger__phase2_merger_load_a_ret.writeAction(f"__if_phase2_merger_load_a_ret_6_true: ceqi X25 X28 0") 
  tranExternalMerger__phase2_merger_load_a_ret.writeAction(f"ceqi X26 X29 0") 
  tranExternalMerger__phase2_merger_load_a_ret.writeAction(f"and X28 X29 X30") 
  tranExternalMerger__phase2_merger_load_a_ret.writeAction(f"beqiu X30 0 __if_phase2_merger_load_a_ret_11_post") 
  tranExternalMerger__phase2_merger_load_a_ret.writeAction(f"__if_phase2_merger_load_a_ret_9_true: movir X26 1024") 
  ## print("got a calling");
  tranExternalMerger__phase2_merger_load_a_ret.writeAction(f"__if_phase2_merger_load_a_ret_11_post: evi X2 X28 ExternalMerger::merge_single 1") 
  tranExternalMerger__phase2_merger_load_a_ret.writeAction(f"movir X29 0") 
  tranExternalMerger__phase2_merger_load_a_ret.writeAction(f"movir X30 -1") 
  tranExternalMerger__phase2_merger_load_a_ret.writeAction(f"sri X30 X30 1") 
  tranExternalMerger__phase2_merger_load_a_ret.writeAction(f"sendr_wcont X28 X30 X29 X29") 
  tranExternalMerger__phase2_merger_load_a_ret.writeAction(f"__if_phase2_merger_load_a_ret_8_post: yield") 
  
  # Writing code for event ExternalMerger::phase2_merger_load_b_ret
  tranExternalMerger__phase2_merger_load_b_ret = efa.writeEvent('ExternalMerger::phase2_merger_load_b_ret')
  ## print("b getting %d %lu at location", val, addr);
  tranExternalMerger__phase2_merger_load_b_ret.writeAction(f"entry: subi X25 X25 1") 
  tranExternalMerger__phase2_merger_load_b_ret.writeAction(f"sari X9 X27 3") 
  tranExternalMerger__phase2_merger_load_b_ret.writeAction(f"mod X27 X23 X28") 
  tranExternalMerger__phase2_merger_load_b_ret.writeAction(f"movwrl X8 X22(X28,0,0)") 
  tranExternalMerger__phase2_merger_load_b_ret.writeAction(f"movir X27 0") 
  tranExternalMerger__phase2_merger_load_b_ret.writeAction(f"andi X26 X28 2") 
  tranExternalMerger__phase2_merger_load_b_ret.writeAction(f"beqiu X28 0 __if_phase2_merger_load_b_ret_2_post") 
  tranExternalMerger__phase2_merger_load_b_ret.writeAction(f"__if_phase2_merger_load_b_ret_0_true: xori X26 X26 2") 
  tranExternalMerger__phase2_merger_load_b_ret.writeAction(f"movir X28 1024") 
  tranExternalMerger__phase2_merger_load_b_ret.writeAction(f"bneu X26 X28 __if_phase2_merger_load_b_ret_2_post") 
  tranExternalMerger__phase2_merger_load_b_ret.writeAction(f"__if_phase2_merger_load_b_ret_3_true: movir X27 1") 
  tranExternalMerger__phase2_merger_load_b_ret.writeAction(f"__if_phase2_merger_load_b_ret_2_post: ceqi X25 X28 0") 
  tranExternalMerger__phase2_merger_load_b_ret.writeAction(f"ceqi X26 X29 0") 
  tranExternalMerger__phase2_merger_load_b_ret.writeAction(f"and X28 X29 X30") 
  tranExternalMerger__phase2_merger_load_b_ret.writeAction(f"or X30 X27 X31") 
  tranExternalMerger__phase2_merger_load_b_ret.writeAction(f"beqiu X31 0 __if_phase2_merger_load_b_ret_8_post") 
  tranExternalMerger__phase2_merger_load_b_ret.writeAction(f"__if_phase2_merger_load_b_ret_6_true: ceqi X25 X28 0") 
  tranExternalMerger__phase2_merger_load_b_ret.writeAction(f"ceqi X26 X29 0") 
  tranExternalMerger__phase2_merger_load_b_ret.writeAction(f"and X28 X29 X30") 
  tranExternalMerger__phase2_merger_load_b_ret.writeAction(f"beqiu X30 0 __if_phase2_merger_load_b_ret_11_post") 
  tranExternalMerger__phase2_merger_load_b_ret.writeAction(f"__if_phase2_merger_load_b_ret_9_true: movir X26 1024") 
  ## print("got b calling");
  tranExternalMerger__phase2_merger_load_b_ret.writeAction(f"__if_phase2_merger_load_b_ret_11_post: evi X2 X28 ExternalMerger::merge_single 1") 
  tranExternalMerger__phase2_merger_load_b_ret.writeAction(f"movir X29 0") 
  tranExternalMerger__phase2_merger_load_b_ret.writeAction(f"movir X30 -1") 
  tranExternalMerger__phase2_merger_load_b_ret.writeAction(f"sri X30 X30 1") 
  tranExternalMerger__phase2_merger_load_b_ret.writeAction(f"sendr_wcont X28 X30 X29 X29") 
  tranExternalMerger__phase2_merger_load_b_ret.writeAction(f"__if_phase2_merger_load_b_ret_8_post: yield") 
  
  # Writing code for event ExternalMerger::merge_single
  tranExternalMerger__merge_single = efa.writeEvent('ExternalMerger::merge_single')
  tranExternalMerger__merge_single.writeAction(f"entry: movir X29 1024") 
  tranExternalMerger__merge_single.writeAction(f"bequ X26 X29 __if_merge_single_2_post") 
  ## print("not making any sense: nwai = %d", nwait);
  tranExternalMerger__merge_single.writeAction(f"__if_merge_single_0_true: yield_terminate") 
  tranExternalMerger__merge_single.writeAction(f"__if_merge_single_2_post: cgt X16 X17 X27") 
  tranExternalMerger__merge_single.writeAction(f"cgt X18 X19 X28") 
  tranExternalMerger__merge_single.writeAction(f"or X27 X28 X29") 
  tranExternalMerger__merge_single.writeAction(f"beqiu X29 0 __if_merge_single_5_post") 
  tranExternalMerger__merge_single.writeAction(f"__if_merge_single_3_true: bneiu X25 0 __if_merge_single_7_false") 
  ## print("???");
  ## send_event(CCONT, 0, IGNRCONT);
  tranExternalMerger__merge_single.writeAction(f"__if_merge_single_6_true: yield_terminate") 
  tranExternalMerger__merge_single.writeAction(f"jmp __if_merge_single_5_post") 
  tranExternalMerger__merge_single.writeAction(f"__if_merge_single_7_false: yield") 
  tranExternalMerger__merge_single.writeAction(f"__if_merge_single_5_post: movir X27 -1") 
  tranExternalMerger__merge_single.writeAction(f"movir X28 -1") 
  ## If the value 
  tranExternalMerger__merge_single.writeAction(f"bleu X17 X16 __if_merge_single_11_post") 
  tranExternalMerger__merge_single.writeAction(f"__if_merge_single_9_true: sari X16 X29 3") 
  tranExternalMerger__merge_single.writeAction(f"mod X29 X23 X30") 
  tranExternalMerger__merge_single.writeAction(f"movwlr X21(X30,0,0) X27") 
  tranExternalMerger__merge_single.writeAction(f"movir X29 -1") 
  tranExternalMerger__merge_single.writeAction(f"bne X27 X29 __if_merge_single_11_post") 
  tranExternalMerger__merge_single.writeAction(f"__if_merge_single_12_true: ori X26 X26 1") 
  tranExternalMerger__merge_single.writeAction(f"__if_merge_single_11_post: bleu X19 X18 __if_merge_single_17_post") 
  tranExternalMerger__merge_single.writeAction(f"__if_merge_single_15_true: sari X18 X29 3") 
  tranExternalMerger__merge_single.writeAction(f"mod X29 X23 X30") 
  tranExternalMerger__merge_single.writeAction(f"movwlr X22(X30,0,0) X28") 
  tranExternalMerger__merge_single.writeAction(f"movir X29 -1") 
  tranExternalMerger__merge_single.writeAction(f"bne X28 X29 __if_merge_single_17_post") 
  tranExternalMerger__merge_single.writeAction(f"__if_merge_single_18_true: ori X26 X26 2") 
  ## print("merging single %d", nwait);
  tranExternalMerger__merge_single.writeAction(f"__if_merge_single_17_post: movir X29 1024") 
  tranExternalMerger__merge_single.writeAction(f"bequ X26 X29 __if_merge_single_23_post") 
  ## wait for values to return
  ## print("waiting for return");
  tranExternalMerger__merge_single.writeAction(f"__if_merge_single_21_true: yield") 
  ## choose 1 value to push, and pull next values
  tranExternalMerger__merge_single.writeAction(f"__if_merge_single_23_post: bleu X28 X27 __if_merge_single_25_false") 
  tranExternalMerger__merge_single.writeAction(f"__if_merge_single_24_true: sendr_dmlm_wret X24 ExternalMerger::merge_single_write_ret X27 X29") 
  tranExternalMerger__merge_single.writeAction(f"addi X25 X25 1") 
  tranExternalMerger__merge_single.writeAction(f"addi X24 X24 8") 
  tranExternalMerger__merge_single.writeAction(f"sari X16 X26 3") 
  tranExternalMerger__merge_single.writeAction(f"mod X26 X23 X26") 
  tranExternalMerger__merge_single.writeAction(f"movir X30 -1") 
  tranExternalMerger__merge_single.writeAction(f"movwrl X30 X21(X26,0,0)") 
  tranExternalMerger__merge_single.writeAction(f"sli X23 X29 3") 
  tranExternalMerger__merge_single.writeAction(f"add X16 X29 X30") 
  tranExternalMerger__merge_single.writeAction(f"bleu X17 X30 __if_merge_single_29_post") 
  tranExternalMerger__merge_single.writeAction(f"__if_merge_single_27_true: sli X23 X30 3") 
  tranExternalMerger__merge_single.writeAction(f"add X16 X30 X29") 
  tranExternalMerger__merge_single.writeAction(f"send_dmlm_ld_wret X29 ExternalMerger::phase2_merger_load_a_ret 1 X30") 
  tranExternalMerger__merge_single.writeAction(f"addi X25 X25 1") 
  tranExternalMerger__merge_single.writeAction(f"__if_merge_single_29_post: addi X16 X16 8") 
  ## print("poping a : %d", val0);
  ## print("outstanding cnt = %d", cnt);
  tranExternalMerger__merge_single.writeAction(f"jmp __if_merge_single_26_post") 
  tranExternalMerger__merge_single.writeAction(f"__if_merge_single_25_false: sendr_dmlm_wret X24 ExternalMerger::merge_single_write_ret X28 X29") 
  tranExternalMerger__merge_single.writeAction(f"addi X25 X25 1") 
  tranExternalMerger__merge_single.writeAction(f"addi X24 X24 8") 
  tranExternalMerger__merge_single.writeAction(f"sari X18 X26 3") 
  tranExternalMerger__merge_single.writeAction(f"mod X26 X23 X26") 
  tranExternalMerger__merge_single.writeAction(f"movir X30 -1") 
  tranExternalMerger__merge_single.writeAction(f"movwrl X30 X22(X26,0,0)") 
  tranExternalMerger__merge_single.writeAction(f"sli X23 X29 3") 
  tranExternalMerger__merge_single.writeAction(f"add X18 X29 X30") 
  tranExternalMerger__merge_single.writeAction(f"bleu X19 X30 __if_merge_single_32_post") 
  tranExternalMerger__merge_single.writeAction(f"__if_merge_single_30_true: sli X23 X30 3") 
  tranExternalMerger__merge_single.writeAction(f"add X18 X30 X29") 
  tranExternalMerger__merge_single.writeAction(f"send_dmlm_ld_wret X29 ExternalMerger::phase2_merger_load_b_ret 1 X30") 
  tranExternalMerger__merge_single.writeAction(f"addi X25 X25 1") 
  tranExternalMerger__merge_single.writeAction(f"__if_merge_single_32_post: addi X18 X18 8") 
  ## print("poping b : %d", val1);
  ## print("outstanding cnt = %d", cnt);
  ## print("c0 = %lu, e0 = %lu, c1 = %lu, e1 = %lu", c0, e0, c1, e1);
  ## borrowed nwait for intermediates
  tranExternalMerger__merge_single.writeAction(f"__if_merge_single_26_post: movir X26 1024") 
  tranExternalMerger__merge_single.writeAction(f"ceq X16 X17 X29") 
  tranExternalMerger__merge_single.writeAction(f"xori X29 X29 1") 
  tranExternalMerger__merge_single.writeAction(f"ceq X18 X19 X30") 
  tranExternalMerger__merge_single.writeAction(f"xori X30 X30 1") 
  tranExternalMerger__merge_single.writeAction(f"or X29 X30 X31") 
  tranExternalMerger__merge_single.writeAction(f"beqiu X31 0 __if_merge_single_35_post") 
  ## print("sending out");
  tranExternalMerger__merge_single.writeAction(f"__if_merge_single_33_true: evi X2 X29 ExternalMerger::merge_single 1") 
  tranExternalMerger__merge_single.writeAction(f"movir X30 0") 
  tranExternalMerger__merge_single.writeAction(f"movir X31 -1") 
  tranExternalMerger__merge_single.writeAction(f"sri X31 X31 1") 
  tranExternalMerger__merge_single.writeAction(f"sendr_wcont X29 X31 X30 X30") 
  tranExternalMerger__merge_single.writeAction(f"__if_merge_single_35_post: yield") 
  
  # Writing code for event ExternalMerger::merge_single_write_ret
  tranExternalMerger__merge_single_write_ret = efa.writeEvent('ExternalMerger::merge_single_write_ret')
  ## print("writing xxx");
  tranExternalMerger__merge_single_write_ret.writeAction(f"entry: subi X25 X25 1") 
  tranExternalMerger__merge_single_write_ret.writeAction(f"ceq X16 X17 X27") 
  tranExternalMerger__merge_single_write_ret.writeAction(f"ceq X18 X19 X28") 
  tranExternalMerger__merge_single_write_ret.writeAction(f"and X27 X28 X29") 
  tranExternalMerger__merge_single_write_ret.writeAction(f"ceqi X25 X30 0") 
  tranExternalMerger__merge_single_write_ret.writeAction(f"and X29 X30 X31") 
  tranExternalMerger__merge_single_write_ret.writeAction(f"beqiu X31 0 __if_merge_single_write_ret_2_post") 
  ## print("returning from merge_sin1gle");
  tranExternalMerger__merge_single_write_ret.writeAction(f"__if_merge_single_write_ret_0_true: evi X2 X27 ExternalMerger::write_back 1") 
  tranExternalMerger__merge_single_write_ret.writeAction(f"movir X28 0") 
  tranExternalMerger__merge_single_write_ret.writeAction(f"movir X29 -1") 
  tranExternalMerger__merge_single_write_ret.writeAction(f"sri X29 X29 1") 
  tranExternalMerger__merge_single_write_ret.writeAction(f"sendr_wcont X27 X29 X28 X28") 
  tranExternalMerger__merge_single_write_ret.writeAction(f"__if_merge_single_write_ret_2_post: yield") 
  
  # Writing code for event ExternalMerger::write_back
  tranExternalMerger__write_back = efa.writeEvent('ExternalMerger::write_back')
  tranExternalMerger__write_back.writeAction(f"entry: movir X25 0") 
  tranExternalMerger__write_back.writeAction(f"sli X20 X27 3") 
  tranExternalMerger__write_back.writeAction(f"sub X24 X27 X24") 
  tranExternalMerger__write_back.writeAction(f"sub X19 X27 X16") 
  tranExternalMerger__write_back.writeAction(f"addi X16 X28 0") 
  tranExternalMerger__write_back.writeAction(f"sub X28 X24 X23") 
  ## for (int i = 0; i < tot; i = i + 1) {
  ## 	send_dram_read(tmp_addr, 1, write_back_load_ret);	
  ## 	tmp_addr = tmp_addr + 8;
  ## 	cnt = cnt + 1;
  ## }
  tranExternalMerger__write_back.writeAction(f"movir X29 0") 
  tranExternalMerger__write_back.writeAction(f"evlb X29 MemcpyLib::memcpy_dram_to_dram") 
  tranExternalMerger__write_back.writeAction(f"evi X29 X29 255 4") 
  tranExternalMerger__write_back.writeAction(f"ev X29 X29 X0 X0 8") 
  tranExternalMerger__write_back.writeAction(f"sendr3_wret X29 ExternalMerger::write_back_write_ret X24 X28 X20 X30") 
  ## write the array back to original place
  tranExternalMerger__write_back.writeAction(f"yield") 
  
  # Writing code for event ExternalMerger::write_back_load_ret
  tranExternalMerger__write_back_load_ret = efa.writeEvent('ExternalMerger::write_back_load_ret')
  tranExternalMerger__write_back_load_ret.writeAction(f"entry: add X9 X23 X27") 
  tranExternalMerger__write_back_load_ret.writeAction(f"sendr_dmlm_wret X27 ExternalMerger::write_back_write_ret X8 X28") 
  tranExternalMerger__write_back_load_ret.writeAction(f"yield") 
  
  # Writing code for event ExternalMerger::write_back_write_ret
  tranExternalMerger__write_back_write_ret = efa.writeEvent('ExternalMerger::write_back_write_ret')
  tranExternalMerger__write_back_write_ret.writeAction(f"__if_write_back_write_ret_0_true: movir X27 0") 
  tranExternalMerger__write_back_write_ret.writeAction(f"movir X28 -1") 
  tranExternalMerger__write_back_write_ret.writeAction(f"sri X28 X28 1") 
  tranExternalMerger__write_back_write_ret.writeAction(f"sendr_wcont X1 X28 X27 X27") 
  tranExternalMerger__write_back_write_ret.writeAction(f"yield_terminate") 
  
  
  ###########################################################
  ###### Writing code for thread ParallelPrefixPerLane ######
  ###########################################################
  ## unsigned long gadd;
  # Writing code for event ParallelPrefixPerLane::prefix_forward_per_lane
  tranParallelPrefixPerLane__prefix_forward_per_lane = efa.writeEvent('ParallelPrefixPerLane::prefix_forward_per_lane')
  tranParallelPrefixPerLane__prefix_forward_per_lane.writeAction(f"entry: addi X9 X21 0") 
  tranParallelPrefixPerLane__prefix_forward_per_lane.writeAction(f"addi X11 X22 0") 
  tranParallelPrefixPerLane__prefix_forward_per_lane.writeAction(f"addi X10 X23 0") 
  tranParallelPrefixPerLane__prefix_forward_per_lane.writeAction(f"addi X12 X24 0") 
  ## pull a block from memory and calculate prefix
  ## (if there is more than one block), store the sum into next block 
  ## print("in prefix_forward_per_lane %d %d", size1_in, size2_in);
  tranParallelPrefixPerLane__prefix_forward_per_lane.writeAction(f"addi X8 X25 0")  # This is for casting. May be used later on
  tranParallelPrefixPerLane__prefix_forward_per_lane.writeAction(f"sub X0 X25 X26") 
  tranParallelPrefixPerLane__prefix_forward_per_lane.writeAction(f"addi X26 X16 0")  # This is for casting. May be used later on
  tranParallelPrefixPerLane__prefix_forward_per_lane.writeAction(f"addi X13 X18 0") 
  tranParallelPrefixPerLane__prefix_forward_per_lane.writeAction(f"sli X16 X25 12") 
  tranParallelPrefixPerLane__prefix_forward_per_lane.writeAction(f"addi X25 X26 4096") 
  tranParallelPrefixPerLane__prefix_forward_per_lane.writeAction(f"ble X26 X23 __if_prefix_forward_per_lane_2_post") 
  tranParallelPrefixPerLane__prefix_forward_per_lane.writeAction(f"__if_prefix_forward_per_lane_0_true: addi X23 X26 0") 
  ## print("st = %d, ed = %d", st, ed);
  tranParallelPrefixPerLane__prefix_forward_per_lane.writeAction(f"__if_prefix_forward_per_lane_2_post: sub X26 X25 X20") 
  tranParallelPrefixPerLane__prefix_forward_per_lane.writeAction(f"sli X16 X28 12") 
  tranParallelPrefixPerLane__prefix_forward_per_lane.writeAction(f"sli X28 X29 3") 
  tranParallelPrefixPerLane__prefix_forward_per_lane.writeAction(f"add X21 X29 X27") 
  tranParallelPrefixPerLane__prefix_forward_per_lane.writeAction(f"movir X28 0") 
  tranParallelPrefixPerLane__prefix_forward_per_lane.writeAction(f"evlb X28 MemcpyLib::memcpy_dram_to_sp") 
  tranParallelPrefixPerLane__prefix_forward_per_lane.writeAction(f"evi X28 X28 255 4") 
  tranParallelPrefixPerLane__prefix_forward_per_lane.writeAction(f"ev X28 X28 X0 X0 8") 
  tranParallelPrefixPerLane__prefix_forward_per_lane.writeAction(f"add X7 X13 X29") 
  tranParallelPrefixPerLane__prefix_forward_per_lane.writeAction(f"sendr3_wret X28 ParallelPrefixPerLane::prefix_forward_per_lane_load_ret X27 X29 X20 X30") 
  ## print("per lane prefix %d %d", size1, size2);
  ## send_event(CCONT, 0, IGNRCONT);
  tranParallelPrefixPerLane__prefix_forward_per_lane.writeAction(f"yield") 
  
  # Writing code for event ParallelPrefixPerLane::prefix_forward_per_lane_load_ret
  tranParallelPrefixPerLane__prefix_forward_per_lane_load_ret = efa.writeEvent('ParallelPrefixPerLane::prefix_forward_per_lane_load_ret')
  tranParallelPrefixPerLane__prefix_forward_per_lane_load_ret.writeAction(f"__if_prefix_forward_per_lane_load_ret_0_true: add X7 X18 X25") 
  tranParallelPrefixPerLane__prefix_forward_per_lane_load_ret.writeAction(f"sli X16 X28 12") 
  tranParallelPrefixPerLane__prefix_forward_per_lane_load_ret.writeAction(f"sli X28 X29 3") 
  tranParallelPrefixPerLane__prefix_forward_per_lane_load_ret.writeAction(f"add X21 X29 X27") 
  tranParallelPrefixPerLane__prefix_forward_per_lane_load_ret.writeAction(f"movir X28 0") 
  tranParallelPrefixPerLane__prefix_forward_per_lane_load_ret.writeAction(f"movir X26 0") 
  tranParallelPrefixPerLane__prefix_forward_per_lane_load_ret.writeAction(f"__for_prefix_forward_per_lane_load_ret_3_condition: ble X20 X26 __for_prefix_forward_per_lane_load_ret_5_post") 
  tranParallelPrefixPerLane__prefix_forward_per_lane_load_ret.writeAction(f"__for_prefix_forward_per_lane_load_ret_4_body: sendr_dmlm_wret X27 ParallelPrefixPerLane::prefix_forward_per_lane_write_ret X28 X29") 
  ## print("%d %d", sp_ptr[i], sum);
  tranParallelPrefixPerLane__prefix_forward_per_lane_load_ret.writeAction(f"movwlr X25(X26,0,0) X29") 
  tranParallelPrefixPerLane__prefix_forward_per_lane_load_ret.writeAction(f"add X28 X29 X28") 
  tranParallelPrefixPerLane__prefix_forward_per_lane_load_ret.writeAction(f"addi X27 X27 8") 
  tranParallelPrefixPerLane__prefix_forward_per_lane_load_ret.writeAction(f"addi X26 X26 1") 
  tranParallelPrefixPerLane__prefix_forward_per_lane_load_ret.writeAction(f"jmp __for_prefix_forward_per_lane_load_ret_3_condition") 
  tranParallelPrefixPerLane__prefix_forward_per_lane_load_ret.writeAction(f"__for_prefix_forward_per_lane_load_ret_5_post: beqiu X24 0 __if_prefix_forward_per_lane_load_ret_8_post") 
  tranParallelPrefixPerLane__prefix_forward_per_lane_load_ret.writeAction(f"__if_prefix_forward_per_lane_load_ret_6_true: sli X16 X29 3") 
  tranParallelPrefixPerLane__prefix_forward_per_lane_load_ret.writeAction(f"add X22 X29 X30") 
  tranParallelPrefixPerLane__prefix_forward_per_lane_load_ret.writeAction(f"sendr_dmlm_wret X30 ParallelPrefixPerLane::prefix_forward_per_lane_write_ret X28 X31") 
  tranParallelPrefixPerLane__prefix_forward_per_lane_load_ret.writeAction(f"addi X20 X20 1") 
  tranParallelPrefixPerLane__prefix_forward_per_lane_load_ret.writeAction(f"__if_prefix_forward_per_lane_load_ret_8_post: yield") 
  
  # Writing code for event ParallelPrefixPerLane::prefix_forward_per_lane_write_ret
  tranParallelPrefixPerLane__prefix_forward_per_lane_write_ret = efa.writeEvent('ParallelPrefixPerLane::prefix_forward_per_lane_write_ret')
  tranParallelPrefixPerLane__prefix_forward_per_lane_write_ret.writeAction(f"entry: subi X20 X20 1") 
  tranParallelPrefixPerLane__prefix_forward_per_lane_write_ret.writeAction(f"bnei X20 0 __if_prefix_forward_per_lane_write_ret_2_post") 
  tranParallelPrefixPerLane__prefix_forward_per_lane_write_ret.writeAction(f"__if_prefix_forward_per_lane_write_ret_0_true: movir X25 0") 
  tranParallelPrefixPerLane__prefix_forward_per_lane_write_ret.writeAction(f"movir X26 -1") 
  tranParallelPrefixPerLane__prefix_forward_per_lane_write_ret.writeAction(f"sri X26 X26 1") 
  tranParallelPrefixPerLane__prefix_forward_per_lane_write_ret.writeAction(f"sendr_wcont X1 X26 X25 X25") 
  tranParallelPrefixPerLane__prefix_forward_per_lane_write_ret.writeAction(f"__if_prefix_forward_per_lane_write_ret_2_post: yield") 
  
  # Writing code for event ParallelPrefixPerLane::prefix_backward_per_lane
  tranParallelPrefixPerLane__prefix_backward_per_lane = efa.writeEvent('ParallelPrefixPerLane::prefix_backward_per_lane')
  tranParallelPrefixPerLane__prefix_backward_per_lane.writeAction(f"entry: addi X9 X21 0") 
  tranParallelPrefixPerLane__prefix_backward_per_lane.writeAction(f"addi X11 X22 0") 
  tranParallelPrefixPerLane__prefix_backward_per_lane.writeAction(f"addi X10 X23 0") 
  tranParallelPrefixPerLane__prefix_backward_per_lane.writeAction(f"addi X12 X24 0") 
  ## pull a block from memory and calculate prefix
  ## (if there is more than one block), store the sum into next block 
  ## print("in prefix_forward_per_lane %d %d", size1_in, size2_in);
  tranParallelPrefixPerLane__prefix_backward_per_lane.writeAction(f"addi X8 X25 0")  # This is for casting. May be used later on
  tranParallelPrefixPerLane__prefix_backward_per_lane.writeAction(f"sub X0 X25 X26") 
  tranParallelPrefixPerLane__prefix_backward_per_lane.writeAction(f"addi X26 X16 0")  # This is for casting. May be used later on
  tranParallelPrefixPerLane__prefix_backward_per_lane.writeAction(f"addi X13 X18 0") 
  tranParallelPrefixPerLane__prefix_backward_per_lane.writeAction(f"sli X16 X25 12") 
  tranParallelPrefixPerLane__prefix_backward_per_lane.writeAction(f"addi X25 X26 4096") 
  tranParallelPrefixPerLane__prefix_backward_per_lane.writeAction(f"ble X26 X23 __if_prefix_backward_per_lane_2_post") 
  tranParallelPrefixPerLane__prefix_backward_per_lane.writeAction(f"__if_prefix_backward_per_lane_0_true: addi X23 X26 0") 
  ## print("st = %d, ed = %d", st, ed);
  tranParallelPrefixPerLane__prefix_backward_per_lane.writeAction(f"__if_prefix_backward_per_lane_2_post: sub X26 X25 X20") 
  tranParallelPrefixPerLane__prefix_backward_per_lane.writeAction(f"sli X16 X28 12") 
  tranParallelPrefixPerLane__prefix_backward_per_lane.writeAction(f"sli X28 X29 3") 
  tranParallelPrefixPerLane__prefix_backward_per_lane.writeAction(f"add X21 X29 X27") 
  tranParallelPrefixPerLane__prefix_backward_per_lane.writeAction(f"add X7 X13 X17") 
  ## for (has = 0; has < tot; has = has + 1) {
  ## 	send_dram_read(ptr, 1, prefix_backward_per_lane_load_ret);
  ## 	ptr = ptr + 8;
  ## }
  tranParallelPrefixPerLane__prefix_backward_per_lane.writeAction(f"movir X28 0") 
  tranParallelPrefixPerLane__prefix_backward_per_lane.writeAction(f"evlb X28 MemcpyLib::memcpy_dram_to_sp") 
  tranParallelPrefixPerLane__prefix_backward_per_lane.writeAction(f"evi X28 X28 255 4") 
  tranParallelPrefixPerLane__prefix_backward_per_lane.writeAction(f"ev X28 X28 X0 X0 8") 
  tranParallelPrefixPerLane__prefix_backward_per_lane.writeAction(f"sendr3_wret X28 ParallelPrefixPerLane::prefix_backward_per_lane_load_ret X27 X17 X20 X31") 
  tranParallelPrefixPerLane__prefix_backward_per_lane.writeAction(f"sli X16 X29 3") 
  tranParallelPrefixPerLane__prefix_backward_per_lane.writeAction(f"add X22 X29 X30") 
  tranParallelPrefixPerLane__prefix_backward_per_lane.writeAction(f"send_dmlm_ld_wret X30 ParallelPrefixPerLane::prefix_backward_per_lane_load_ret 1 X31") 
  ## print("per lane prefix %d %d", size1, size2);
  tranParallelPrefixPerLane__prefix_backward_per_lane.writeAction(f"movir X19 2") 
  tranParallelPrefixPerLane__prefix_backward_per_lane.writeAction(f"yield") 
  
  # Writing code for event ParallelPrefixPerLane::prefix_backward_per_lane_load_ret
  tranParallelPrefixPerLane__prefix_backward_per_lane_load_ret = efa.writeEvent('ParallelPrefixPerLane::prefix_backward_per_lane_load_ret')
  ## if(addr > addr2) {/
  ## } 
  tranParallelPrefixPerLane__prefix_backward_per_lane_load_ret.writeAction(f"entry: sli X16 X25 3") 
  tranParallelPrefixPerLane__prefix_backward_per_lane_load_ret.writeAction(f"add X22 X25 X26") 
  tranParallelPrefixPerLane__prefix_backward_per_lane_load_ret.writeAction(f"bne X26 X9 __if_prefix_backward_per_lane_load_ret_2_post") 
  tranParallelPrefixPerLane__prefix_backward_per_lane_load_ret.writeAction(f"__if_prefix_backward_per_lane_load_ret_0_true: addi X8 X24 0") 
  ## print("geeting size2 = %d %lu", size2, key);
  ## print("getting %d %lu", key, addr);
  tranParallelPrefixPerLane__prefix_backward_per_lane_load_ret.writeAction(f"__if_prefix_backward_per_lane_load_ret_2_post: subi X19 X19 1") 
  tranParallelPrefixPerLane__prefix_backward_per_lane_load_ret.writeAction(f"bnei X19 0 __if_prefix_backward_per_lane_load_ret_5_post") 
  tranParallelPrefixPerLane__prefix_backward_per_lane_load_ret.writeAction(f"__if_prefix_backward_per_lane_load_ret_3_true: add X7 X18 X25") 
  tranParallelPrefixPerLane__prefix_backward_per_lane_load_ret.writeAction(f"sli X16 X28 12") 
  tranParallelPrefixPerLane__prefix_backward_per_lane_load_ret.writeAction(f"sli X28 X29 3") 
  tranParallelPrefixPerLane__prefix_backward_per_lane_load_ret.writeAction(f"add X21 X29 X27") 
  tranParallelPrefixPerLane__prefix_backward_per_lane_load_ret.writeAction(f"movir X26 0") 
  tranParallelPrefixPerLane__prefix_backward_per_lane_load_ret.writeAction(f"__for_prefix_backward_per_lane_load_ret_6_condition: ble X20 X26 __if_prefix_backward_per_lane_load_ret_5_post") 
  tranParallelPrefixPerLane__prefix_backward_per_lane_load_ret.writeAction(f"__for_prefix_backward_per_lane_load_ret_7_body: movwlr X25(X26,0,0) X29") 
  tranParallelPrefixPerLane__prefix_backward_per_lane_load_ret.writeAction(f"add X29 X24 X28") 
  tranParallelPrefixPerLane__prefix_backward_per_lane_load_ret.writeAction(f"sendr_dmlm_wret X27 ParallelPrefixPerLane::prefix_backward_per_lane_write_ret X28 X29") 
  ## print("sending %d %d", size2, res);
  tranParallelPrefixPerLane__prefix_backward_per_lane_load_ret.writeAction(f"addi X27 X27 8") 
  tranParallelPrefixPerLane__prefix_backward_per_lane_load_ret.writeAction(f"addi X26 X26 1") 
  tranParallelPrefixPerLane__prefix_backward_per_lane_load_ret.writeAction(f"jmp __for_prefix_backward_per_lane_load_ret_6_condition") 
  tranParallelPrefixPerLane__prefix_backward_per_lane_load_ret.writeAction(f"__if_prefix_backward_per_lane_load_ret_5_post: yield") 
  
  # Writing code for event ParallelPrefixPerLane::prefix_backward_per_lane_write_ret
  tranParallelPrefixPerLane__prefix_backward_per_lane_write_ret = efa.writeEvent('ParallelPrefixPerLane::prefix_backward_per_lane_write_ret')
  tranParallelPrefixPerLane__prefix_backward_per_lane_write_ret.writeAction(f"entry: subi X20 X20 1") 
  tranParallelPrefixPerLane__prefix_backward_per_lane_write_ret.writeAction(f"bnei X20 0 __if_prefix_backward_per_lane_write_ret_2_post") 
  tranParallelPrefixPerLane__prefix_backward_per_lane_write_ret.writeAction(f"__if_prefix_backward_per_lane_write_ret_0_true: movir X25 0") 
  tranParallelPrefixPerLane__prefix_backward_per_lane_write_ret.writeAction(f"movir X26 -1") 
  tranParallelPrefixPerLane__prefix_backward_per_lane_write_ret.writeAction(f"sri X26 X26 1") 
  tranParallelPrefixPerLane__prefix_backward_per_lane_write_ret.writeAction(f"sendr_wcont X1 X26 X25 X25") 
  tranParallelPrefixPerLane__prefix_backward_per_lane_write_ret.writeAction(f"__if_prefix_backward_per_lane_write_ret_2_post: yield") 
  
  
  ######################################################
  ###### Writing code for thread Distributed_sort ######
  ######################################################
  # Writing code for event Distributed_sort::sort_new
  tranDistributed_sort__sort_new = efa.writeEvent('Distributed_sort::sort_new')
  ## print("in sorssss");
  ## send_event(CCONT, 0, IGNRCONT);
  ## print("sort_lm_offset %d", sort_lm_offset);
  ## print("list_size %d", list_size);
  ## print("num_bins %d", num_bins);
  ## print("num_lanes %d", num_lanes);
  ## print("max_value %d", max_value);
  tranDistributed_sort__sort_new.writeAction(f"entry: addi X1 X16 0") 
  tranDistributed_sort__sort_new.writeAction(f"mod X13 X11 X21") 
  tranDistributed_sort__sort_new.writeAction(f"beqi X21 0 __if_sort_new_2_post") 
  tranDistributed_sort__sort_new.writeAction(f"__if_sort_new_0_true: print 'Number of bins should be a multiple of number of lanes'") 
  tranDistributed_sort__sort_new.writeAction(f"movir X21 0") 
  tranDistributed_sort__sort_new.writeAction(f"movir X22 -1") 
  tranDistributed_sort__sort_new.writeAction(f"sri X22 X22 1") 
  tranDistributed_sort__sort_new.writeAction(f"sendr_wcont X1 X22 X21 X21") 
  tranDistributed_sort__sort_new.writeAction(f"yield_terminate") 
  tranDistributed_sort__sort_new.writeAction(f"__if_sort_new_2_post: movir X17 0") 
  tranDistributed_sort__sort_new.writeAction(f"evlb X17 DistributedSortBroadcast__broadcast_global") 
  tranDistributed_sort__sort_new.writeAction(f"evi X17 X17 255 4") 
  tranDistributed_sort__sort_new.writeAction(f"ev X17 X17 X0 X0 8") 
  tranDistributed_sort__sort_new.writeAction(f"movir X18 0") 
  tranDistributed_sort__sort_new.writeAction(f"evlb X18 Distributed_sort_per_lane_thread::sort_init_per_lane") 
  ## cont_word = evw_update_event(CEVNT, sort_phase1_init_cache);
  tranDistributed_sort__sort_new.writeAction(f"evi X2 X19 Distributed_sort::sort_phase1_init_cache 1") 
  tranDistributed_sort__sort_new.writeAction(f"addi X7 X20 8") 
  tranDistributed_sort__sort_new.writeAction(f"movrl X11 0(X20) 0 8") 
  tranDistributed_sort__sort_new.writeAction(f"movrl X18 8(X20) 0 8") 
  tranDistributed_sort__sort_new.writeAction(f"sli X9 X22 32") 
  tranDistributed_sort__sort_new.writeAction(f"addi X0 X23 0")  # This is for casting. May be used later on
  tranDistributed_sort__sort_new.writeAction(f"or X22 X23 X24") 
  tranDistributed_sort__sort_new.writeAction(f"movrl X24 16(X20) 0 8") 
  tranDistributed_sort__sort_new.writeAction(f"movrl X10 24(X20) 0 8") 
  tranDistributed_sort__sort_new.writeAction(f"movrl X12 32(X20) 0 8") 
  tranDistributed_sort__sort_new.writeAction(f"sli X11 X22 32") 
  tranDistributed_sort__sort_new.writeAction(f"or X22 X13 X23") 
  tranDistributed_sort__sort_new.writeAction(f"movrl X23 40(X20) 0 8") 
  tranDistributed_sort__sort_new.writeAction(f"ori X15 X22 0") 
  tranDistributed_sort__sort_new.writeAction(f"movrl X22 48(X20) 0 8") 
  tranDistributed_sort__sort_new.writeAction(f"movrl X10 56(X20) 0 8") 
  tranDistributed_sort__sort_new.writeAction(f"send_wcont X17 X19 X20 8") 
  tranDistributed_sort__sort_new.writeAction(f"addi X7 X20 20000") 
  tranDistributed_sort__sort_new.writeAction(f"movrl X14 128(X20) 0 8") 
  tranDistributed_sort__sort_new.writeAction(f"print 'lbaddr = %lu' X14") 
  tranDistributed_sort__sort_new.writeAction(f"yield") 
  ## yield_terminate;
  tranDistributed_sort__sort_new.writeAction(f"yield") 
  
  # Writing code for event Distributed_sort::sort_phase1_init_cache
  tranDistributed_sort__sort_phase1_init_cache = efa.writeEvent('Distributed_sort::sort_phase1_init_cache')
  ## long evword, label, cont_word;
  tranDistributed_sort__sort_phase1_init_cache.writeAction(f"entry: addi X7 X17 20000") 
  tranDistributed_sort__sort_phase1_init_cache.writeAction(f"movir X18 0") 
  tranDistributed_sort__sort_phase1_init_cache.writeAction(f"evlb X18 phase1_bin_size_cache::cache_init") 
  tranDistributed_sort__sort_phase1_init_cache.writeAction(f"evi X18 X18 255 4") 
  tranDistributed_sort__sort_phase1_init_cache.writeAction(f"ev X18 X18 X0 X0 8") 
  ## unsigned long evw = evw_update_event(CEVNT, sort_phase1_init);
  tranDistributed_sort__sort_phase1_init_cache.writeAction(f"evi X2 X19 Distributed_sort::sort_phase1_init 1") 
  tranDistributed_sort__sort_phase1_init_cache.writeAction(f"movlr 24(X17) X20 0 8") 
  tranDistributed_sort__sort_phase1_init_cache.writeAction(f"movlr 88(X17) X21 0 8") 
  tranDistributed_sort__sort_phase1_init_cache.writeAction(f"movlr 32(X17) X22 0 8") 
  tranDistributed_sort__sort_phase1_init_cache.writeAction(f"sendr3_wret X18 Distributed_sort::sort_phase1_init X20 X21 X22 X23") 
  tranDistributed_sort__sort_phase1_init_cache.writeAction(f"yield") 
  
  # Writing code for event Distributed_sort::sort_phase1_init
  tranDistributed_sort__sort_phase1_init = efa.writeEvent('Distributed_sort::sort_phase1_init')
  tranDistributed_sort__sort_phase1_init.writeAction(f"entry: perflog 1 0 'sorting phase 1'") 
  tranDistributed_sort__sort_phase1_init.writeAction(f"print 'sort phase1'") 
  ## construct UDKVMSR call
  tranDistributed_sort__sort_phase1_init.writeAction(f"addi X7 X17 8") 
  tranDistributed_sort__sort_phase1_init.writeAction(f"addi X7 X18 20000") 
  tranDistributed_sort__sort_phase1_init.writeAction(f"movlr 0(X18) X19 0 8") 
  tranDistributed_sort__sort_phase1_init.writeAction(f"movlr 8(X18) X20 0 8") 
  tranDistributed_sort__sort_phase1_init.writeAction(f"movlr 24(X18) X21 0 8") 
  tranDistributed_sort__sort_phase1_init.writeAction(f"addi X7 X22 1152") 
  tranDistributed_sort__sort_phase1_init.writeAction(f"movrl X20 0(X22) 0 8") 
  ## Pointer to the input list (64-bit DRAM address)
  tranDistributed_sort__sort_phase1_init.writeAction(f"movrl X19 8(X22) 0 8") 
  ## size of the list (64-bit DRAM address)
  tranDistributed_sort__sort_phase1_init.writeAction(f"addi X7 X24 20000") 
  tranDistributed_sort__sort_phase1_init.writeAction(f"addi X24 X23 128") 
  tranDistributed_sort__sort_phase1_init.writeAction(f"movlr 88(X18) X25 0 8") 
  tranDistributed_sort__sort_phase1_init.writeAction(f"movlr 32(X18) X26 0 8") 
  tranDistributed_sort__sort_phase1_init.writeAction(f"sli X26 X27 3") 
  tranDistributed_sort__sort_phase1_init.writeAction(f"add X25 X27 X28") 
  tranDistributed_sort__sort_phase1_init.writeAction(f"movrl X28 0(X17) 0 8") 
  ## Pointer to the partition array (64-bit DRAM address)
  tranDistributed_sort__sort_phase1_init.writeAction(f"movir X25 1") 
  tranDistributed_sort__sort_phase1_init.writeAction(f"movrl X25 8(X17) 0 8") 
  ## Number of partitions per lane
  tranDistributed_sort__sort_phase1_init.writeAction(f"movrl X21 16(X17) 0 8") 
  ## Number of lanes
  tranDistributed_sort__sort_phase1_init.writeAction(f"movrl X22 24(X17) 0 8") 
  ## input kvset metadata lm address
  tranDistributed_sort__sort_phase1_init.writeAction(f"movrl X23 32(X17) 0 8") 
  ## sendbuf_lm_ptr[4] = msr_output_kvset_metadata_lm_ptr; // output kvset metadata lm address
  tranDistributed_sort__sort_phase1_init.writeAction(f"movir X24 0") 
  tranDistributed_sort__sort_phase1_init.writeAction(f"evlb X24 DistributedSortPhase1::map_shuffle_reduce") 
  tranDistributed_sort__sort_phase1_init.writeAction(f"evi X24 X24 255 4") 
  tranDistributed_sort__sort_phase1_init.writeAction(f"ev X24 X24 X0 X0 8") 
  ## unsigned long cont = evw_update_event(CEVNT, sort_end);
  tranDistributed_sort__sort_phase1_init.writeAction(f"evi X2 X25 Distributed_sort::sort_phase1_post_processing 1") 
  tranDistributed_sort__sort_phase1_init.writeAction(f"send_wcont X24 X25 X17 5") 
  ## print("returning from sort_end");
  ## print("here");
  ## print("launching phase 1");
  ## send_event(CCONT, 0, IGNRCONT);
  ## yield_terminate;
  tranDistributed_sort__sort_phase1_init.writeAction(f"yield") 
  
  # Writing code for event Distributed_sort::sort_phase1_post_processing
  tranDistributed_sort__sort_phase1_post_processing = efa.writeEvent('Distributed_sort::sort_phase1_post_processing')
  tranDistributed_sort__sort_phase1_post_processing.writeAction(f"entry: print 'in sort_phase1_post_processing'") 
  tranDistributed_sort__sort_phase1_post_processing.writeAction(f"addi X7 X17 20000") 
  tranDistributed_sort__sort_phase1_post_processing.writeAction(f"movir X18 0") 
  tranDistributed_sort__sort_phase1_post_processing.writeAction(f"evlb X18 phase1_bin_size_cache::cache_flush") 
  tranDistributed_sort__sort_phase1_post_processing.writeAction(f"evi X18 X18 255 4") 
  tranDistributed_sort__sort_phase1_post_processing.writeAction(f"ev X18 X18 X0 X0 8") 
  ## unsigned long evw = evw_update_event(CEVNT, sort_phase1_init);
  tranDistributed_sort__sort_phase1_post_processing.writeAction(f"evi X2 X19 Distributed_sort::sort_phase1_init 1") 
  tranDistributed_sort__sort_phase1_post_processing.writeAction(f"movlr 24(X17) X20 0 8") 
  tranDistributed_sort__sort_phase1_post_processing.writeAction(f"movlr 88(X17) X21 0 8") 
  tranDistributed_sort__sort_phase1_post_processing.writeAction(f"movlr 32(X17) X22 0 8") 
  tranDistributed_sort__sort_phase1_post_processing.writeAction(f"sendr3_wret X18 Distributed_sort::sort_phase2_init X20 X21 X22 X23") 
  tranDistributed_sort__sort_phase1_post_processing.writeAction(f"yield") 
  ## yield_terminate;
  tranDistributed_sort__sort_phase1_post_processing.writeAction(f"yield") 
  
  ## event sort_phase1_post_processing() {
  ## 	long evword, label, cont_word;
  ## 	long* local sp_ptr;
  ## 	// print("in sort_phase1_post_processing");
  ## 	evword = evw_new(NETID, DistributedSortBroadcast__broadcast_global);
  ##     label = 0;
  ##     label = evw_update_event(label, Distributed_sort_per_lane_thread::sort_post_phase1_per_lane);
  ##     // cont_word = evw_update_event(CEVNT, sort_phase2_init);
  ##     cont_word = evw_update_event(CEVNT, sort_end);
  ## 	unsigned long* local sort_ptr = LMBASE + SORT_OFFSET;
  ##     sp_ptr = LMBASE + SEND_BUFFER_OFFSET;
  ##     sp_ptr[0] = sort_ptr[NUM_LANES];
  ##     sp_ptr[1] = label;
  ##     send_event(evword, sp_ptr, 8, cont_word);
  ## 	yield;
  ## 	// yield_terminate;
  ## }
  # Writing code for event Distributed_sort::sort_phase2_init
  tranDistributed_sort__sort_phase2_init = efa.writeEvent('Distributed_sort::sort_phase2_init')
  tranDistributed_sort__sort_phase2_init.writeAction(f"entry: perflog 1 0 'sorting phase 2'") 
  tranDistributed_sort__sort_phase2_init.writeAction(f"print 'sort phase2'") 
  tranDistributed_sort__sort_phase2_init.writeAction(f"addi X7 X17 8") 
  tranDistributed_sort__sort_phase2_init.writeAction(f"addi X7 X18 20000") 
  tranDistributed_sort__sort_phase2_init.writeAction(f"movlr 0(X18) X19 0 8") 
  tranDistributed_sort__sort_phase2_init.writeAction(f"movlr 8(X18) X20 0 8") 
  tranDistributed_sort__sort_phase2_init.writeAction(f"movlr 24(X18) X21 0 8") 
  tranDistributed_sort__sort_phase2_init.writeAction(f"addi X7 X22 1152") 
  tranDistributed_sort__sort_phase2_init.writeAction(f"movlr 88(X18) X24 0 8") 
  tranDistributed_sort__sort_phase2_init.writeAction(f"movrl X24 0(X22) 0 8") 
  ## Pointer to the input list (64-bit DRAM address)
  tranDistributed_sort__sort_phase2_init.writeAction(f"movlr 32(X18) X24 0 8") 
  tranDistributed_sort__sort_phase2_init.writeAction(f"movrl X24 8(X22) 0 8") 
  ## size of the list (64-bit DRAM address)
  tranDistributed_sort__sort_phase2_init.writeAction(f"movlr 96(X18) X24 0 8") 
  tranDistributed_sort__sort_phase2_init.writeAction(f"movrl X24 0(X17) 0 8") 
  ## Pointer to the partition array (64-bit DRAM address)
  tranDistributed_sort__sort_phase2_init.writeAction(f"movir X24 1") 
  tranDistributed_sort__sort_phase2_init.writeAction(f"movrl X24 8(X17) 0 8") 
  ## Number of partitions per lane
  tranDistributed_sort__sort_phase2_init.writeAction(f"movrl X21 16(X17) 0 8") 
  ## Number of lanes
  ## sendbuf_lm_ptr[1] = sp_ptr[NUM_BINS] / sp_ptr[NUM_LANES]; // Number of partitions per lane
  tranDistributed_sort__sort_phase2_init.writeAction(f"movrl X21 16(X17) 0 8") 
  ## Number of lanes
  tranDistributed_sort__sort_phase2_init.writeAction(f"movrl X22 24(X17) 0 8") 
  ## input kvset metadata lm address
  tranDistributed_sort__sort_phase2_init.writeAction(f"addi X7 X24 20000") 
  tranDistributed_sort__sort_phase2_init.writeAction(f"addi X24 X23 128") 
  tranDistributed_sort__sort_phase2_init.writeAction(f"movrl X23 32(X17) 0 8") 
  ## unsigned long* local lb_meta_ptr = LMBASE + SHT_1_OFFSET;
  ## lb_meta_ptr[0] = sp_ptr[BIN_SIZE_START] + sp_ptr[NUM_BINS] * 3 * 8;
  ## lb_meta_ptr[1] = lb_meta_ptr[0] + sp_ptr[NUM_BINS] * 8;
  ## sendbuf_lm_ptr[4] = lb_meta_ptr;
  tranDistributed_sort__sort_phase2_init.writeAction(f"movlr 0(X23) X24 0 8") 
  tranDistributed_sort__sort_phase2_init.writeAction(f"print 'passed lb start address: %lu' X24") 
  ## sendbuf_lm_ptr[4] = msr_output_kvset_metadata_lm_ptr; // output kvset metadata lm address
  tranDistributed_sort__sort_phase2_init.writeAction(f"movlr 0(X23) X26 0 8") 
  tranDistributed_sort__sort_phase2_init.writeAction(f"bneiu X26 0 __if_sort_phase2_init_1_false") 
  tranDistributed_sort__sort_phase2_init.writeAction(f"__if_sort_phase2_init_0_true: movir X25 0") 
  tranDistributed_sort__sort_phase2_init.writeAction(f"evlb X25 DistributedSortPhase2::map_shuffle_reduce") 
  tranDistributed_sort__sort_phase2_init.writeAction(f"evi X25 X25 255 4") 
  tranDistributed_sort__sort_phase2_init.writeAction(f"ev X25 X25 X0 X0 8") 
  tranDistributed_sort__sort_phase2_init.writeAction(f"jmp __if_sort_phase2_init_2_post") 
  tranDistributed_sort__sort_phase2_init.writeAction(f"__if_sort_phase2_init_1_false: movir X25 0") 
  tranDistributed_sort__sort_phase2_init.writeAction(f"evlb X25 DistributedSortPhase2Lb::map_shuffle_reduce") 
  tranDistributed_sort__sort_phase2_init.writeAction(f"evi X25 X25 255 4") 
  tranDistributed_sort__sort_phase2_init.writeAction(f"ev X25 X25 X0 X0 8") 
  ## unsigned long cont = evw_update_event(CEVNT, sort_phase3_init);
  tranDistributed_sort__sort_phase2_init.writeAction(f"__if_sort_phase2_init_2_post: evi X2 X26 Distributed_sort::sort_end 1") 
  tranDistributed_sort__sort_phase2_init.writeAction(f"send_wcont X25 X26 X17 5") 
  ## print("returning from sort_end");
  ## print("here");
  ## print("launching phase 1");
  ## send_event(CCONT, 0, IGNRCONT);
  tranDistributed_sort__sort_phase2_init.writeAction(f"yield") 
  
  # Writing code for event Distributed_sort::sort_phase3_init
  tranDistributed_sort__sort_phase3_init = efa.writeEvent('Distributed_sort::sort_phase3_init')
  tranDistributed_sort__sort_phase3_init.writeAction(f"entry: print 'sort phase3'") 
  tranDistributed_sort__sort_phase3_init.writeAction(f"perflog 1 0 'sorting phase 3'") 
  ## Phase 3:
  ## 1.  run parallel prefix
  ## 2. use difference between size to put element in place
  tranDistributed_sort__sort_phase3_init.writeAction(f"movir X17 0") 
  tranDistributed_sort__sort_phase3_init.writeAction(f"evlb X17 ParallelPrefix::prefix") 
  tranDistributed_sort__sort_phase3_init.writeAction(f"evi X17 X17 255 4") 
  tranDistributed_sort__sort_phase3_init.writeAction(f"ev X17 X17 X0 X0 8") 
  tranDistributed_sort__sort_phase3_init.writeAction(f"movir X18 0") 
  tranDistributed_sort__sort_phase3_init.writeAction(f"evi X2 X19 Distributed_sort::sort_phase3_move_array 1") 
  tranDistributed_sort__sort_phase3_init.writeAction(f"addi X7 X20 8") 
  tranDistributed_sort__sort_phase3_init.writeAction(f"addi X7 X21 20000") 
  tranDistributed_sort__sort_phase3_init.writeAction(f"movlr 88(X21) X23 0 8") 
  tranDistributed_sort__sort_phase3_init.writeAction(f"movrl X23 0(X20) 0 8") 
  tranDistributed_sort__sort_phase3_init.writeAction(f"movlr 32(X21) X23 0 8") 
  tranDistributed_sort__sort_phase3_init.writeAction(f"addi X23 X24 1") 
  tranDistributed_sort__sort_phase3_init.writeAction(f"movrl X24 8(X20) 0 8") 
  tranDistributed_sort__sort_phase3_init.writeAction(f"movlr 24(X21) X23 0 8") 
  tranDistributed_sort__sort_phase3_init.writeAction(f"movrl X23 16(X20) 0 8") 
  tranDistributed_sort__sort_phase3_init.writeAction(f"movir X23 20256") 
  tranDistributed_sort__sort_phase3_init.writeAction(f"movrl X23 24(X20) 0 8") 
  tranDistributed_sort__sort_phase3_init.writeAction(f"movir X23 53024") 
  tranDistributed_sort__sort_phase3_init.writeAction(f"movrl X23 32(X20) 0 8") 
  tranDistributed_sort__sort_phase3_init.writeAction(f"send_wcont X17 X19 X20 8") 
  tranDistributed_sort__sort_phase3_init.writeAction(f"yield") 
  
  # Writing code for event Distributed_sort::sort_phase3_move_array
  tranDistributed_sort__sort_phase3_move_array = efa.writeEvent('Distributed_sort::sort_phase3_move_array')
  tranDistributed_sort__sort_phase3_move_array.writeAction(f"entry: print 'launching phase 3'") 
  ## move array to the right place
  tranDistributed_sort__sort_phase3_move_array.writeAction(f"addi X7 X17 8") 
  tranDistributed_sort__sort_phase3_move_array.writeAction(f"addi X7 X18 20000") 
  tranDistributed_sort__sort_phase3_move_array.writeAction(f"movlr 0(X18) X19 0 8") 
  tranDistributed_sort__sort_phase3_move_array.writeAction(f"movlr 8(X18) X20 0 8") 
  tranDistributed_sort__sort_phase3_move_array.writeAction(f"movlr 24(X18) X21 0 8") 
  tranDistributed_sort__sort_phase3_move_array.writeAction(f"addi X7 X22 1152") 
  tranDistributed_sort__sort_phase3_move_array.writeAction(f"movlr 88(X18) X24 0 8") 
  tranDistributed_sort__sort_phase3_move_array.writeAction(f"movrl X24 0(X22) 0 8") 
  ## Pointer to the input list (64-bit DRAM address)
  tranDistributed_sort__sort_phase3_move_array.writeAction(f"movlr 32(X18) X24 0 8") 
  tranDistributed_sort__sort_phase3_move_array.writeAction(f"movrl X24 8(X22) 0 8") 
  ## size of the list (64-bit DRAM address)
  tranDistributed_sort__sort_phase3_move_array.writeAction(f"movlr 96(X18) X24 0 8") 
  tranDistributed_sort__sort_phase3_move_array.writeAction(f"addi X24 X25 8") 
  tranDistributed_sort__sort_phase3_move_array.writeAction(f"movrl X25 0(X17) 0 8") 
  ## Pointer to the partition array (64-bit DRAM address)
  tranDistributed_sort__sort_phase3_move_array.writeAction(f"movir X24 1") 
  tranDistributed_sort__sort_phase3_move_array.writeAction(f"movrl X24 8(X17) 0 8") 
  ## Number of partitions per lane
  tranDistributed_sort__sort_phase3_move_array.writeAction(f"movrl X21 16(X17) 0 8") 
  ## Number of lanes
  tranDistributed_sort__sort_phase3_move_array.writeAction(f"movrl X22 24(X17) 0 8") 
  ## input kvset metadata lm address
  ## sendbuf_lm_ptr[4] = msr_output_kvset_metadata_lm_ptr; // output kvset metadata lm address
  tranDistributed_sort__sort_phase3_move_array.writeAction(f"movir X23 0") 
  tranDistributed_sort__sort_phase3_move_array.writeAction(f"evlb X23 DistributedSortPhase3::map_shuffle_reduce") 
  tranDistributed_sort__sort_phase3_move_array.writeAction(f"evi X23 X23 255 4") 
  tranDistributed_sort__sort_phase3_move_array.writeAction(f"ev X23 X23 X0 X0 8") 
  tranDistributed_sort__sort_phase3_move_array.writeAction(f"evi X2 X24 Distributed_sort::sort_end 1") 
  ## unsigned long cont = evw_update_event(CEVNT, sort_end);
  tranDistributed_sort__sort_phase3_move_array.writeAction(f"send_wcont X23 X24 X17 5") 
  ## print("returning from sort_end");
  ## print("here");
  ## print("launching phase 1");
  ## send_event(CCONT, 0, IGNRCONT);
  tranDistributed_sort__sort_phase3_move_array.writeAction(f"yield") 
  
  ## event sort_phase3_init() {
  ## }
  # Writing code for event Distributed_sort::sort_end
  tranDistributed_sort__sort_end = efa.writeEvent('Distributed_sort::sort_end')
  tranDistributed_sort__sort_end.writeAction(f"entry: perflog 1 0 'sorting end'") 
  ## print("Number of workers: %ld", number_workers);
  tranDistributed_sort__sort_end.writeAction(f"print 'returning from sort_end'") 
  ## print("here");
  tranDistributed_sort__sort_end.writeAction(f"movir X17 0") 
  tranDistributed_sort__sort_end.writeAction(f"movir X18 -1") 
  tranDistributed_sort__sort_end.writeAction(f"sri X18 X18 1") 
  tranDistributed_sort__sort_end.writeAction(f"sendr_wcont X16 X18 X17 X17") 
  tranDistributed_sort__sort_end.writeAction(f"yield_terminate") 
  
  
  ######################################################################
  ###### Writing code for thread Distributed_sort_per_lane_thread ######
  ######################################################################
  # Writing code for event Distributed_sort_per_lane_thread::sort_init_per_lane
  tranDistributed_sort_per_lane_thread__sort_init_per_lane = efa.writeEvent('Distributed_sort_per_lane_thread::sort_init_per_lane')
  tranDistributed_sort_per_lane_thread__sort_init_per_lane.writeAction(f"__if_sort_init_per_lane_0_true: addi X7 X22 20000") 
  tranDistributed_sort_per_lane_thread__sort_init_per_lane.writeAction(f"sari X8 X24 32") 
  tranDistributed_sort_per_lane_thread__sort_init_per_lane.writeAction(f"movrl X24 0(X22) 0 8") 
  tranDistributed_sort_per_lane_thread__sort_init_per_lane.writeAction(f"movir X24 -1") 
  tranDistributed_sort_per_lane_thread__sort_init_per_lane.writeAction(f"sri X24 X24 32") 
  tranDistributed_sort_per_lane_thread__sort_init_per_lane.writeAction(f"and X8 X24 X24") 
  tranDistributed_sort_per_lane_thread__sort_init_per_lane.writeAction(f"movrl X24 104(X22) 0 8") 
  tranDistributed_sort_per_lane_thread__sort_init_per_lane.writeAction(f"movrl X9 8(X22) 0 8") 
  tranDistributed_sort_per_lane_thread__sort_init_per_lane.writeAction(f"movrl X10 16(X22) 0 8") 
  tranDistributed_sort_per_lane_thread__sort_init_per_lane.writeAction(f"sari X11 X20 32") 
  tranDistributed_sort_per_lane_thread__sort_init_per_lane.writeAction(f"movrl X20 24(X22) 0 8") 
  tranDistributed_sort_per_lane_thread__sort_init_per_lane.writeAction(f"movir X24 -1") 
  tranDistributed_sort_per_lane_thread__sort_init_per_lane.writeAction(f"sri X24 X24 32") 
  tranDistributed_sort_per_lane_thread__sort_init_per_lane.writeAction(f"and X11 X24 X24") 
  tranDistributed_sort_per_lane_thread__sort_init_per_lane.writeAction(f"movrl X24 32(X22) 0 8") 
  tranDistributed_sort_per_lane_thread__sort_init_per_lane.writeAction(f"sari X12 X24 32") 
  tranDistributed_sort_per_lane_thread__sort_init_per_lane.writeAction(f"movrl X24 40(X22) 0 8") 
  tranDistributed_sort_per_lane_thread__sort_init_per_lane.writeAction(f"movir X24 -1") 
  tranDistributed_sort_per_lane_thread__sort_init_per_lane.writeAction(f"sri X24 X24 32") 
  tranDistributed_sort_per_lane_thread__sort_init_per_lane.writeAction(f"and X12 X24 X24") 
  tranDistributed_sort_per_lane_thread__sort_init_per_lane.writeAction(f"movrl X24 48(X22) 0 8") 
  tranDistributed_sort_per_lane_thread__sort_init_per_lane.writeAction(f"movlr 32(X22) X19 0 8") 
  tranDistributed_sort_per_lane_thread__sort_init_per_lane.writeAction(f"movlr 48(X22) X24 0 8") 
  tranDistributed_sort_per_lane_thread__sort_init_per_lane.writeAction(f"add X24 X19 X25") 
  tranDistributed_sort_per_lane_thread__sort_init_per_lane.writeAction(f"div X25 X19 X26") 
  tranDistributed_sort_per_lane_thread__sort_init_per_lane.writeAction(f"movrl X26 56(X22) 0 8") 
  tranDistributed_sort_per_lane_thread__sort_init_per_lane.writeAction(f"movlr 56(X22) X24 0 8") 
  tranDistributed_sort_per_lane_thread__sort_init_per_lane.writeAction(f"div X19 X20 X25") 
  tranDistributed_sort_per_lane_thread__sort_init_per_lane.writeAction(f"mul X24 X25 X26") 
  tranDistributed_sort_per_lane_thread__sort_init_per_lane.writeAction(f"movrl X26 64(X22) 0 8") 
  tranDistributed_sort_per_lane_thread__sort_init_per_lane.writeAction(f"div X19 X20 X21") 
  tranDistributed_sort_per_lane_thread__sort_init_per_lane.writeAction(f"movrl X21 72(X22) 0 8") 
  tranDistributed_sort_per_lane_thread__sort_init_per_lane.writeAction(f"sari X8 X24 32") 
  tranDistributed_sort_per_lane_thread__sort_init_per_lane.writeAction(f"div X24 X19 X25") 
  tranDistributed_sort_per_lane_thread__sort_init_per_lane.writeAction(f"muli X25 X26 10") 
  tranDistributed_sort_per_lane_thread__sort_init_per_lane.writeAction(f"sli X26 X27 3") 
  tranDistributed_sort_per_lane_thread__sort_init_per_lane.writeAction(f"movrl X27 80(X22) 0 8") 
  tranDistributed_sort_per_lane_thread__sort_init_per_lane.writeAction(f"movlr 16(X22) X24 0 8") 
  tranDistributed_sort_per_lane_thread__sort_init_per_lane.writeAction(f"movlr 80(X22) X25 0 8") 
  tranDistributed_sort_per_lane_thread__sort_init_per_lane.writeAction(f"mul X19 X25 X26") 
  tranDistributed_sort_per_lane_thread__sort_init_per_lane.writeAction(f"add X24 X26 X27") 
  tranDistributed_sort_per_lane_thread__sort_init_per_lane.writeAction(f"movrl X27 88(X22) 0 8") 
  ## print("bin_size_start = %lu", sp_ptr[BIN_SIZE_START]);
  tranDistributed_sort_per_lane_thread__sort_init_per_lane.writeAction(f"movlr 16(X22) X24 0 8") 
  tranDistributed_sort_per_lane_thread__sort_init_per_lane.writeAction(f"movlr 80(X22) X25 0 8") 
  tranDistributed_sort_per_lane_thread__sort_init_per_lane.writeAction(f"mul X19 X25 X26") 
  tranDistributed_sort_per_lane_thread__sort_init_per_lane.writeAction(f"add X24 X26 X27") 
  tranDistributed_sort_per_lane_thread__sort_init_per_lane.writeAction(f"sli X19 X28 3") 
  tranDistributed_sort_per_lane_thread__sort_init_per_lane.writeAction(f"add X27 X28 X29") 
  tranDistributed_sort_per_lane_thread__sort_init_per_lane.writeAction(f"movrl X29 96(X22) 0 8") 
  tranDistributed_sort_per_lane_thread__sort_init_per_lane.writeAction(f"movir X24 0") 
  tranDistributed_sort_per_lane_thread__sort_init_per_lane.writeAction(f"movrl X24 112(X22) 0 8") 
  tranDistributed_sort_per_lane_thread__sort_init_per_lane.writeAction(f"movir X24 0") 
  tranDistributed_sort_per_lane_thread__sort_init_per_lane.writeAction(f"movrl X24 120(X22) 0 8") 
  ## print("list_addr %lu, tmp_addr %lu, num_lanes %d, num_bins %d, use_unique %d, max_value %d, bin_size %d, bksize = %d, dram_block_size = %d", sp_ptr[LIST_ADDR], sp_ptr[TMP_ADDR], sp_ptr[NUM_LANES], sp_ptr[NUM_BINS], sp_ptr[USE_UNIQUE], sp_ptr[MAX_VALUE], sp_ptr[BIN_SIZE], sp_ptr[BKSIZE], sp_ptr[DRAM_BLOCK_SIZE]);
  tranDistributed_sort_per_lane_thread__sort_init_per_lane.writeAction(f"__if_sort_init_per_lane_3_true: movir X22 0") 
  tranDistributed_sort_per_lane_thread__sort_init_per_lane.writeAction(f"addi X7 X23 20256") 
  ## long bins_per_lane = num_bins / num_lanes;
  tranDistributed_sort_per_lane_thread__sort_init_per_lane.writeAction(f"movir X22 0") 
  tranDistributed_sort_per_lane_thread__sort_init_per_lane.writeAction(f"__for_sort_init_per_lane_6_condition: ble X21 X22 __if_sort_init_per_lane_9_true") 
  tranDistributed_sort_per_lane_thread__sort_init_per_lane.writeAction(f"__for_sort_init_per_lane_7_body: movir X25 0") 
  tranDistributed_sort_per_lane_thread__sort_init_per_lane.writeAction(f"movwrl X25 X23(X22,0,0)") 
  ## ptr = ptr + 8;
  ## print("ptr = %lu", ptr);
  tranDistributed_sort_per_lane_thread__sort_init_per_lane.writeAction(f"addi X22 X22 1") 
  tranDistributed_sort_per_lane_thread__sort_init_per_lane.writeAction(f"jmp __for_sort_init_per_lane_6_condition") 
  tranDistributed_sort_per_lane_thread__sort_init_per_lane.writeAction(f"__if_sort_init_per_lane_9_true: addi X7 X22 20000") 
  ## unsigned long bins_per_lane = ptr[BINS_PER_LANE];
  tranDistributed_sort_per_lane_thread__sort_init_per_lane.writeAction(f"movlr 104(X22) X24 0 8") 
  tranDistributed_sort_per_lane_thread__sort_init_per_lane.writeAction(f"addi X24 X25 0")  # This is for casting. May be used later on
  tranDistributed_sort_per_lane_thread__sort_init_per_lane.writeAction(f"sub X0 X25 X26") 
  tranDistributed_sort_per_lane_thread__sort_init_per_lane.writeAction(f"addi X21 X27 0")  # This is for casting. May be used later on
  tranDistributed_sort_per_lane_thread__sort_init_per_lane.writeAction(f"mul X26 X27 X28") 
  tranDistributed_sort_per_lane_thread__sort_init_per_lane.writeAction(f"sli X28 X29 3") 
  tranDistributed_sort_per_lane_thread__sort_init_per_lane.writeAction(f"movlr 88(X22) X30 0 8") 
  tranDistributed_sort_per_lane_thread__sort_init_per_lane.writeAction(f"addi X30 X31 0")  # This is for casting. May be used later on
  tranDistributed_sort_per_lane_thread__sort_init_per_lane.writeAction(f"add X29 X31 X23") 
  tranDistributed_sort_per_lane_thread__sort_init_per_lane.writeAction(f"addi X7 X25 20000") 
  tranDistributed_sort_per_lane_thread__sort_init_per_lane.writeAction(f"addi X25 X24 256") 
  tranDistributed_sort_per_lane_thread__sort_init_per_lane.writeAction(f"evi X2 X25 MemcpyLib::memcpy_sp_to_dram 1") 
  tranDistributed_sort_per_lane_thread__sort_init_per_lane.writeAction(f"sendr3_wcont X25 X1 X24 X23 X21") 
  ## print("sending %lu to %lu, base = %lu", *lm_addr, dram_addr, ptr[BIN_SIZE_START]);
  ## yield_terminate;
  ## send_event(CCONT, 0, IGNRCONT);
  tranDistributed_sort_per_lane_thread__sort_init_per_lane.writeAction(f"yield") 
  
  # Writing code for event Distributed_sort_per_lane_thread::sort_post_phase1_per_lane
  tranDistributed_sort_per_lane_thread__sort_post_phase1_per_lane = efa.writeEvent('Distributed_sort_per_lane_thread::sort_post_phase1_per_lane')
  ## print("in sort_post_phase1_per_lane");
  tranDistributed_sort_per_lane_thread__sort_post_phase1_per_lane.writeAction(f"entry: addi X7 X19 20000") 
  tranDistributed_sort_per_lane_thread__sort_post_phase1_per_lane.writeAction(f"movlr 72(X19) X20 0 8") 
  tranDistributed_sort_per_lane_thread__sort_post_phase1_per_lane.writeAction(f"movlr 104(X19) X22 0 8") 
  tranDistributed_sort_per_lane_thread__sort_post_phase1_per_lane.writeAction(f"addi X22 X23 0")  # This is for casting. May be used later on
  tranDistributed_sort_per_lane_thread__sort_post_phase1_per_lane.writeAction(f"sub X0 X23 X24") 
  tranDistributed_sort_per_lane_thread__sort_post_phase1_per_lane.writeAction(f"addi X20 X25 0")  # This is for casting. May be used later on
  tranDistributed_sort_per_lane_thread__sort_post_phase1_per_lane.writeAction(f"mul X24 X25 X26") 
  tranDistributed_sort_per_lane_thread__sort_post_phase1_per_lane.writeAction(f"sli X26 X27 3") 
  tranDistributed_sort_per_lane_thread__sort_post_phase1_per_lane.writeAction(f"movlr 88(X19) X28 0 8") 
  tranDistributed_sort_per_lane_thread__sort_post_phase1_per_lane.writeAction(f"addi X28 X29 0")  # This is for casting. May be used later on
  tranDistributed_sort_per_lane_thread__sort_post_phase1_per_lane.writeAction(f"add X27 X29 X21") 
  tranDistributed_sort_per_lane_thread__sort_post_phase1_per_lane.writeAction(f"addi X7 X23 20000") 
  tranDistributed_sort_per_lane_thread__sort_post_phase1_per_lane.writeAction(f"addi X23 X22 256") 
  ## for (tot = 0; tot < bins_per_lane; tot = tot + 1) {
  ## 	send_dram_write(dram_addr, lm_addr, 1, sort_post_phase1_per_lane_return);
  ## 	dram_addr = dram_addr + 8;
  ## 	// print("sending %d to %lu", *lm_addr, dram_addr);
  ## 	lm_addr = lm_addr + 8;
  ## }
  tranDistributed_sort_per_lane_thread__sort_post_phase1_per_lane.writeAction(f"evi X2 X23 MemcpyLib::memcpy_sp_to_dram 1") 
  tranDistributed_sort_per_lane_thread__sort_post_phase1_per_lane.writeAction(f"sendr3_wcont X23 X1 X22 X21 X20") 
  ## send_event(CCONT, 0, IGNRCONT);
  ## yield_terminate;
  tranDistributed_sort_per_lane_thread__sort_post_phase1_per_lane.writeAction(f"yield") 
  
  # Writing code for event Distributed_sort_per_lane_thread::sort_post_phase1_per_lane_return
  tranDistributed_sort_per_lane_thread__sort_post_phase1_per_lane_return = efa.writeEvent('Distributed_sort_per_lane_thread::sort_post_phase1_per_lane_return')
  tranDistributed_sort_per_lane_thread__sort_post_phase1_per_lane_return.writeAction(f"__if_sort_post_phase1_per_lane_return_0_true: movir X19 0") 
  tranDistributed_sort_per_lane_thread__sort_post_phase1_per_lane_return.writeAction(f"movir X20 -1") 
  tranDistributed_sort_per_lane_thread__sort_post_phase1_per_lane_return.writeAction(f"sri X20 X20 1") 
  tranDistributed_sort_per_lane_thread__sort_post_phase1_per_lane_return.writeAction(f"sendr_wcont X1 X20 X19 X19") 
  tranDistributed_sort_per_lane_thread__sort_post_phase1_per_lane_return.writeAction(f"yield_terminate") 
  
  
  ###########################################################
  ###### Writing code for thread DistributedSortPhase1 ######
  ###########################################################
  # Writing code for event DistributedSortPhase1::kv_map
  tranDistributedSortPhase1__kv_map = efa.writeEvent('DistributedSortPhase1::kv_map')
  tranDistributedSortPhase1__kv_map.writeAction(f"entry: movir X18 0") 
  tranDistributedSortPhase1__kv_map.writeAction(f"evlb X18 DistributedSortPhase1::kv_map_emit") 
  tranDistributedSortPhase1__kv_map.writeAction(f"evi X18 X18 255 4") 
  tranDistributedSortPhase1__kv_map.writeAction(f"ev X18 X18 X0 X0 8") 
  tranDistributedSortPhase1__kv_map.writeAction(f"addi X7 X19 20000") 
  tranDistributedSortPhase1__kv_map.writeAction(f"movlr 56(X19) X21 0 8") 
  tranDistributedSortPhase1__kv_map.writeAction(f"div X8 X21 X20") 
  ## print("ikey = %d", ikey);
  tranDistributedSortPhase1__kv_map.writeAction(f"sendr_wcont X18 X1 X20 X8") 
  tranDistributedSortPhase1__kv_map.writeAction(f"evi X2 X18 DistributedSortPhase1::kv_map_return 1") 
  tranDistributedSortPhase1__kv_map.writeAction(f"sendr_wcont X18 X1 X0 X0") 
  tranDistributedSortPhase1__kv_map.writeAction(f"yield") 
  
  # Writing code for event DistributedSortPhase1::kv_reduce
  tranDistributedSortPhase1__kv_reduce = efa.writeEvent('DistributedSortPhase1::kv_reduce')
  tranDistributedSortPhase1__kv_reduce.writeAction(f"entry: addi X7 X18 20000") 
  tranDistributedSortPhase1__kv_reduce.writeAction(f"addi X8 X17 0") 
  ## print("getting bin id = %lu, value = %lu, netid = %lu", bin_idx, value, NETID);
  ## print("getting bin id = %lu, value = %lu", bin_idx, value);
  tranDistributedSortPhase1__kv_reduce.writeAction(f"addi X9 X16 0") 
  ## unsigned long local_bin_idx = bin_idx % bins_per_lane;
  ## unsigned long dram_block_size = ptr[DRAM_BLOCK_SIZE];
  ## // print("receiving value = %d, local_bin_idx = %d", value, local_bin_idx);
  ## unsigned long * local counter_addr = LMBASE + (SORT_OFFSET + COUNTERS_OFFSET) + 8 * local_bin_idx;
  ## unsigned long local_bin_count = *counter_addr;
  ## unsigned long * local dram_addr = ptr[TMP_ADDR] + value / bin_size * dram_block_size + local_bin_count * 8;
  ## send_dram_write(dram_addr, value, DistributedSortPhase1::kv_reduce_return);
  ## *counter_addr = local_bin_count + 1;
  ## // print("local_bin_idx = %d, local_bin_count = %d, dram_addr = %lu", local_bin_idx, local_bin_count, dram_addr);
  ## yield;
  ## send_event(evw, 0, IGNRCONT);
  tranDistributedSortPhase1__kv_reduce.writeAction(f"movir X19 0") 
  tranDistributedSortPhase1__kv_reduce.writeAction(f"evlb X19 phase1_bin_size_cache::cache_combine_value") 
  tranDistributedSortPhase1__kv_reduce.writeAction(f"evi X19 X19 255 4") 
  tranDistributedSortPhase1__kv_reduce.writeAction(f"ev X19 X19 X0 X0 8") 
  ## unsigned long cont = evw_update_event(CEVNT, kv_reducer_get_back_from_cache);
  ## unsigned long cont = evw_update_event(CEVNT, sort_phase2_init);
  tranDistributedSortPhase1__kv_reduce.writeAction(f"movir X20 1") 
  tranDistributedSortPhase1__kv_reduce.writeAction(f"sendr_wret X19 DistributedSortPhase1::kv_reducer_get_back_from_cache X17 X20 X21") 
  tranDistributedSortPhase1__kv_reduce.writeAction(f"yield") 
  
  # Writing code for event DistributedSortPhase1::kv_reducer_get_back_from_cache
  tranDistributedSortPhase1__kv_reducer_get_back_from_cache = efa.writeEvent('DistributedSortPhase1::kv_reducer_get_back_from_cache')
  ## print("getting back from cache %lu %lu, putting %lu", key, local_bin_count, cval);
  tranDistributedSortPhase1__kv_reducer_get_back_from_cache.writeAction(f"entry: addi X7 X18 20000") 
  ## unsigned long bin_size = ptr[BIN_SIZE];
  tranDistributedSortPhase1__kv_reducer_get_back_from_cache.writeAction(f"movlr 80(X18) X19 0 8") 
  tranDistributedSortPhase1__kv_reducer_get_back_from_cache.writeAction(f"movlr 16(X18) X21 0 8") 
  tranDistributedSortPhase1__kv_reducer_get_back_from_cache.writeAction(f"mul X17 X19 X22") 
  tranDistributedSortPhase1__kv_reducer_get_back_from_cache.writeAction(f"add X21 X22 X23") 
  tranDistributedSortPhase1__kv_reducer_get_back_from_cache.writeAction(f"subi X9 X24 1") 
  tranDistributedSortPhase1__kv_reducer_get_back_from_cache.writeAction(f"sli X24 X25 3") 
  tranDistributedSortPhase1__kv_reducer_get_back_from_cache.writeAction(f"add X23 X25 X20") 
  tranDistributedSortPhase1__kv_reducer_get_back_from_cache.writeAction(f"sendr_dmlm_wret X20 DistributedSortPhase1::kv_reduce_return X16 X21") 
  ## unsigned long evw = evw_update_event(CEVNT, DistributedSortPhase1::kv_reduce_return);
  ## send_event(evw, 0, IGNRCONT);
  tranDistributedSortPhase1__kv_reducer_get_back_from_cache.writeAction(f"yield") 
  
  
  ####################################################################
  ###### Writing code for thread DistributedSortPhase1Insertion ######
  ####################################################################
  ## long tot, bin_size;
  ## unsigned long offset;
  # Writing code for event DistributedSortPhase1Insertion::kv_map
  tranDistributedSortPhase1Insertion__kv_map = efa.writeEvent('DistributedSortPhase1Insertion::kv_map')
  tranDistributedSortPhase1Insertion__kv_map.writeAction(f"entry: movir X22 0") 
  tranDistributedSortPhase1Insertion__kv_map.writeAction(f"evlb X22 DistributedSortPhase1Insertion::kv_map_emit") 
  tranDistributedSortPhase1Insertion__kv_map.writeAction(f"evi X22 X22 255 4") 
  tranDistributedSortPhase1Insertion__kv_map.writeAction(f"ev X22 X22 X0 X0 8") 
  tranDistributedSortPhase1Insertion__kv_map.writeAction(f"addi X7 X23 20000") 
  tranDistributedSortPhase1Insertion__kv_map.writeAction(f"movlr 56(X23) X25 0 8") 
  tranDistributedSortPhase1Insertion__kv_map.writeAction(f"div X8 X25 X24") 
  ## print("ikey = %d", ikey);
  tranDistributedSortPhase1Insertion__kv_map.writeAction(f"sendr_wcont X22 X1 X24 X8") 
  ## print("kv_map_emit %lu %lu", ikey, key);
  tranDistributedSortPhase1Insertion__kv_map.writeAction(f"evi X2 X22 DistributedSortPhase1Insertion::kv_map_return 1") 
  tranDistributedSortPhase1Insertion__kv_map.writeAction(f"sendr_wcont X22 X1 X0 X0") 
  tranDistributedSortPhase1Insertion__kv_map.writeAction(f"yield") 
  
  # Writing code for event DistributedSortPhase1Insertion::kv_reduce
  tranDistributedSortPhase1Insertion__kv_reduce = efa.writeEvent('DistributedSortPhase1Insertion::kv_reduce')
  tranDistributedSortPhase1Insertion__kv_reduce.writeAction(f"entry: addi X7 X22 20000") 
  tranDistributedSortPhase1Insertion__kv_reduce.writeAction(f"addi X1 X21 0") 
  tranDistributedSortPhase1Insertion__kv_reduce.writeAction(f"addi X8 X17 0") 
  ## print("getting bin id = %lu, value = %lu, netid = %lu", bin_idx, value, NETID);
  ## print("getting bin id = %lu, value = %lu", bin_idx, value);
  tranDistributedSortPhase1Insertion__kv_reduce.writeAction(f"addi X9 X16 0") 
  ## unsigned long local_bin_idx = bin_idx % bins_per_lane;
  ## unsigned long dram_block_size = ptr[DRAM_BLOCK_SIZE];
  ## // print("receiving value = %d, local_bin_idx = %d", value, local_bin_idx);
  ## unsigned long * local counter_addr = LMBASE + (SORT_OFFSET + COUNTERS_OFFSET) + 8 * local_bin_idx;
  ## unsigned long local_bin_count = *counter_addr;
  ## unsigned long * local dram_addr = ptr[TMP_ADDR] + value / bin_size * dram_block_size + local_bin_count * 8;
  ## send_dram_write(dram_addr, value, DistributedSortPhase1::kv_reduce_return);
  ## *counter_addr = local_bin_count + 1;
  ## // print("local_bin_idx = %d, local_bin_count = %d, dram_addr = %lu", local_bin_idx, local_bin_count, dram_addr);
  ## yield;
  ## test return
  ## send_event(evw, 0, IGNRCONT);
  tranDistributedSortPhase1Insertion__kv_reduce.writeAction(f"movir X23 0") 
  tranDistributedSortPhase1Insertion__kv_reduce.writeAction(f"evlb X23 phase1_bin_size_cache::cache_combine_value") 
  tranDistributedSortPhase1Insertion__kv_reduce.writeAction(f"evi X23 X23 255 4") 
  tranDistributedSortPhase1Insertion__kv_reduce.writeAction(f"ev X23 X23 X0 X0 8") 
  ## unsigned long cont = evw_update_event(CEVNT, kv_reducer_get_back_from_cache);
  ## unsigned long cont = evw_update_event(CEVNT, sort_phase2_init);
  ## evw = evw_update_event(CEVNT, DistributedSortPhase1Insertion::kv_reduce_return);
  ## send_event(evw, 0, CCONT);
  ## yield;
  tranDistributedSortPhase1Insertion__kv_reduce.writeAction(f"movir X24 1") 
  tranDistributedSortPhase1Insertion__kv_reduce.writeAction(f"sendr_wret X23 DistributedSortPhase1Insertion::kv_reducer_get_back_from_cache X17 X24 X25") 
  tranDistributedSortPhase1Insertion__kv_reduce.writeAction(f"yield") 
  
  # Writing code for event DistributedSortPhase1Insertion::kv_reducer_get_back_from_cache
  tranDistributedSortPhase1Insertion__kv_reducer_get_back_from_cache = efa.writeEvent('DistributedSortPhase1Insertion::kv_reducer_get_back_from_cache')
  ## print("getting back from cache %lu %lu", key, local_bin_count);
  tranDistributedSortPhase1Insertion__kv_reducer_get_back_from_cache.writeAction(f"entry: subi X9 X18 1") 
  ## print("getting back from cache %lu %lu, putting %lu", key, local_bin_count, cval);
  tranDistributedSortPhase1Insertion__kv_reducer_get_back_from_cache.writeAction(f"addi X7 X22 20000") 
  ## unsigned long bin_size = ptr[BIN_SIZE];
  tranDistributedSortPhase1Insertion__kv_reducer_get_back_from_cache.writeAction(f"movlr 80(X22) X23 0 8") 
  tranDistributedSortPhase1Insertion__kv_reducer_get_back_from_cache.writeAction(f"movlr 16(X22) X25 0 8") 
  tranDistributedSortPhase1Insertion__kv_reducer_get_back_from_cache.writeAction(f"movlr 80(X22) X26 0 8") 
  tranDistributedSortPhase1Insertion__kv_reducer_get_back_from_cache.writeAction(f"mul X17 X26 X27") 
  tranDistributedSortPhase1Insertion__kv_reducer_get_back_from_cache.writeAction(f"add X25 X27 X24") 
  tranDistributedSortPhase1Insertion__kv_reducer_get_back_from_cache.writeAction(f"addi X24 X19 0") 
  ## add space for cache
  tranDistributedSortPhase1Insertion__kv_reducer_get_back_from_cache.writeAction(f"addi X7 X26 20256") 
  tranDistributedSortPhase1Insertion__kv_reducer_get_back_from_cache.writeAction(f"addi X26 X25 1024") 
  tranDistributedSortPhase1Insertion__kv_reducer_get_back_from_cache.writeAction(f"addi X25 X20 0") 
  tranDistributedSortPhase1Insertion__kv_reducer_get_back_from_cache.writeAction(f"movir X26 0") 
  tranDistributedSortPhase1Insertion__kv_reducer_get_back_from_cache.writeAction(f"evlb X26 MemcpyLib::memcpy_dram_to_sp") 
  tranDistributedSortPhase1Insertion__kv_reducer_get_back_from_cache.writeAction(f"evi X26 X26 255 4") 
  tranDistributedSortPhase1Insertion__kv_reducer_get_back_from_cache.writeAction(f"ev X26 X26 X0 X0 8") 
  tranDistributedSortPhase1Insertion__kv_reducer_get_back_from_cache.writeAction(f"sendr3_wret X26 DistributedSortPhase1Insertion::kv_reduce_load_sp_return X19 X25 X18 X27") 
  ## bin_dram_addr = tmp_bin_dram_addr; 
  ## bin_size = local_bin_count;
  tranDistributedSortPhase1Insertion__kv_reducer_get_back_from_cache.writeAction(f"yield") 
  
  # Writing code for event DistributedSortPhase1Insertion::kv_reduce_load_sp_return
  tranDistributedSortPhase1Insertion__kv_reduce_load_sp_return = efa.writeEvent('DistributedSortPhase1Insertion::kv_reduce_load_sp_return')
  tranDistributedSortPhase1Insertion__kv_reduce_load_sp_return.writeAction(f"entry: addi X20 X22 0") 
  tranDistributedSortPhase1Insertion__kv_reduce_load_sp_return.writeAction(f"movir X23 0") 
  tranDistributedSortPhase1Insertion__kv_reduce_load_sp_return.writeAction(f"__for_kv_reduce_load_sp_return_0_condition: addi X18 X24 0")  # This is for casting. May be used later on
  tranDistributedSortPhase1Insertion__kv_reduce_load_sp_return.writeAction(f"ble X24 X23 __for_kv_reduce_load_sp_return_2_post") 
  tranDistributedSortPhase1Insertion__kv_reduce_load_sp_return.writeAction(f"__for_kv_reduce_load_sp_return_1_body: movwlr X22(X23,0,0) X24") 
  tranDistributedSortPhase1Insertion__kv_reduce_load_sp_return.writeAction(f"ble X24 X16 __if_kv_reduce_load_sp_return_5_post") 
  tranDistributedSortPhase1Insertion__kv_reduce_load_sp_return.writeAction(f"__if_kv_reduce_load_sp_return_3_true: movwlr X22(X23,0,0) X24") 
  tranDistributedSortPhase1Insertion__kv_reduce_load_sp_return.writeAction(f"movwrl X16 X22(X23,0,0)") 
  tranDistributedSortPhase1Insertion__kv_reduce_load_sp_return.writeAction(f"addi X24 X16 0") 
  tranDistributedSortPhase1Insertion__kv_reduce_load_sp_return.writeAction(f"__if_kv_reduce_load_sp_return_5_post: addi X23 X23 1") 
  tranDistributedSortPhase1Insertion__kv_reduce_load_sp_return.writeAction(f"jmp __for_kv_reduce_load_sp_return_0_condition") 
  tranDistributedSortPhase1Insertion__kv_reduce_load_sp_return.writeAction(f"__for_kv_reduce_load_sp_return_2_post: movwrl X16 X22(X18,0,0)") 
  tranDistributedSortPhase1Insertion__kv_reduce_load_sp_return.writeAction(f"addi X18 X18 1") 
  tranDistributedSortPhase1Insertion__kv_reduce_load_sp_return.writeAction(f"movir X23 0") 
  tranDistributedSortPhase1Insertion__kv_reduce_load_sp_return.writeAction(f"evlb X23 MemcpyLib::memcpy_sp_to_dram") 
  tranDistributedSortPhase1Insertion__kv_reduce_load_sp_return.writeAction(f"evi X23 X23 255 4") 
  tranDistributedSortPhase1Insertion__kv_reduce_load_sp_return.writeAction(f"ev X23 X23 X0 X0 8") 
  ## print("returning with size : %lu", bin_size);
  tranDistributedSortPhase1Insertion__kv_reduce_load_sp_return.writeAction(f"sendr3_wret X23 DistributedSortPhase1Insertion::kv_reduce_store_sp_return X20 X19 X18 X24") 
  tranDistributedSortPhase1Insertion__kv_reduce_load_sp_return.writeAction(f"yield") 
  
  # Writing code for event DistributedSortPhase1Insertion::kv_reduce_store_sp_return
  tranDistributedSortPhase1Insertion__kv_reduce_store_sp_return = efa.writeEvent('DistributedSortPhase1Insertion::kv_reduce_store_sp_return')
  ## print("returning to sp return");
  ## send_event(save_cont, 0, IGNRCONT);
  tranDistributedSortPhase1Insertion__kv_reduce_store_sp_return.writeAction(f"entry: evi X2 X22 DistributedSortPhase1Insertion::kv_reduce_return 1") 
  tranDistributedSortPhase1Insertion__kv_reduce_store_sp_return.writeAction(f"movir X23 0") 
  tranDistributedSortPhase1Insertion__kv_reduce_store_sp_return.writeAction(f"sendr_wcont X22 X21 X23 X23") 
  tranDistributedSortPhase1Insertion__kv_reduce_store_sp_return.writeAction(f"yield") 
  
  
  ######################################################################
  ###### Writing code for thread DistributedSortPhase1InsertionLb ######
  ######################################################################
  ## long tot, bin_size;
  ## unsigned long offset;
  # Writing code for event DistributedSortPhase1InsertionLb::kv_map
  tranDistributedSortPhase1InsertionLb__kv_map = efa.writeEvent('DistributedSortPhase1InsertionLb::kv_map')
  tranDistributedSortPhase1InsertionLb__kv_map.writeAction(f"entry: movir X22 0") 
  tranDistributedSortPhase1InsertionLb__kv_map.writeAction(f"evlb X22 DistributedSortPhase1InsertionLb::kv_map_emit") 
  tranDistributedSortPhase1InsertionLb__kv_map.writeAction(f"evi X22 X22 255 4") 
  tranDistributedSortPhase1InsertionLb__kv_map.writeAction(f"ev X22 X22 X0 X0 8") 
  tranDistributedSortPhase1InsertionLb__kv_map.writeAction(f"addi X7 X23 20000") 
  tranDistributedSortPhase1InsertionLb__kv_map.writeAction(f"movlr 56(X23) X25 0 8") 
  tranDistributedSortPhase1InsertionLb__kv_map.writeAction(f"div X8 X25 X24") 
  ## print("insertion = %d", ikey);
  tranDistributedSortPhase1InsertionLb__kv_map.writeAction(f"sendr_wcont X22 X1 X24 X8") 
  ## print("kv_map_emit %lu %lu", ikey, key);
  tranDistributedSortPhase1InsertionLb__kv_map.writeAction(f"evi X2 X22 DistributedSortPhase1InsertionLb::kv_map_return 1") 
  tranDistributedSortPhase1InsertionLb__kv_map.writeAction(f"sendr_wcont X22 X1 X0 X0") 
  tranDistributedSortPhase1InsertionLb__kv_map.writeAction(f"yield") 
  
  # Writing code for event DistributedSortPhase1InsertionLb::kv_reduce
  tranDistributedSortPhase1InsertionLb__kv_reduce = efa.writeEvent('DistributedSortPhase1InsertionLb::kv_reduce')
  ## print("kv_reduce_start %lu %lu with cont %lu", key, value, CCONT);
  tranDistributedSortPhase1InsertionLb__kv_reduce.writeAction(f"entry: addi X7 X22 20000") 
  tranDistributedSortPhase1InsertionLb__kv_reduce.writeAction(f"addi X1 X21 0") 
  tranDistributedSortPhase1InsertionLb__kv_reduce.writeAction(f"addi X8 X17 0") 
  ## print("getting bin id = %lu, value = %lu, netid = %lu", bin_idx, value, NETID);
  ## print("getting bin id = %lu, value = %lu", bin_idx, value);
  tranDistributedSortPhase1InsertionLb__kv_reduce.writeAction(f"addi X9 X16 0") 
  ## unsigned long local_bin_idx = bin_idx % bins_per_lane;
  ## unsigned long dram_block_size = ptr[DRAM_BLOCK_SIZE];
  ## // print("receiving value = %d, local_bin_idx = %d", value, local_bin_idx);
  ## unsigned long * local counter_addr = LMBASE + (SORT_OFFSET + COUNTERS_OFFSET) + 8 * local_bin_idx;
  ## unsigned long local_bin_count = *counter_addr;
  ## unsigned long * local dram_addr = ptr[TMP_ADDR] + value / bin_size * dram_block_size + local_bin_count * 8;
  ## send_dram_write(dram_addr, value, DistributedSortPhase1::kv_reduce_return);
  ## *counter_addr = local_bin_count + 1;
  ## // print("local_bin_idx = %d, local_bin_count = %d, dram_addr = %lu", local_bin_idx, local_bin_count, dram_addr);
  ## yield;
  ## test return
  ## send_event(evw, 0, IGNRCONT);
  tranDistributedSortPhase1InsertionLb__kv_reduce.writeAction(f"movir X23 0") 
  tranDistributedSortPhase1InsertionLb__kv_reduce.writeAction(f"evlb X23 phase1_bin_size_cache::cache_combine_value") 
  tranDistributedSortPhase1InsertionLb__kv_reduce.writeAction(f"evi X23 X23 255 4") 
  tranDistributedSortPhase1InsertionLb__kv_reduce.writeAction(f"ev X23 X23 X0 X0 8") 
  ## print("sending out to %lx", evw);
  ## unsigned long cont = evw_update_event(CEVNT, kv_reducer_get_back_from_cache);
  ## unsigned long cont = evw_update_event(CEVNT, sort_phase2_init);
  ## evw = evw_update_event(CEVNT, DistributedSortPhase1Insertion::kv_reduce_return);
  ## send_event(evw, 0, CCONT);
  ## yield;
  tranDistributedSortPhase1InsertionLb__kv_reduce.writeAction(f"movir X24 1") 
  tranDistributedSortPhase1InsertionLb__kv_reduce.writeAction(f"sendr_wret X23 DistributedSortPhase1InsertionLb::kv_reducer_get_back_from_cache X17 X24 X25") 
  ## print("kv_reduce_end %lu %lu", key, value);
  tranDistributedSortPhase1InsertionLb__kv_reduce.writeAction(f"yield") 
  
  # Writing code for event DistributedSortPhase1InsertionLb::kv_reducer_get_back_from_cache
  tranDistributedSortPhase1InsertionLb__kv_reducer_get_back_from_cache = efa.writeEvent('DistributedSortPhase1InsertionLb::kv_reducer_get_back_from_cache')
  ## print("getting back from cache %lu %lu", key, local_bin_count);
  tranDistributedSortPhase1InsertionLb__kv_reducer_get_back_from_cache.writeAction(f"entry: subi X9 X18 1") 
  ## print("getting back from cache %lu %lu, putting %lu", key, local_bin_count, cval);
  tranDistributedSortPhase1InsertionLb__kv_reducer_get_back_from_cache.writeAction(f"addi X7 X22 20000") 
  ## unsigned long bin_size = ptr[BIN_SIZE];
  tranDistributedSortPhase1InsertionLb__kv_reducer_get_back_from_cache.writeAction(f"movlr 80(X22) X23 0 8") 
  tranDistributedSortPhase1InsertionLb__kv_reducer_get_back_from_cache.writeAction(f"movlr 16(X22) X25 0 8") 
  tranDistributedSortPhase1InsertionLb__kv_reducer_get_back_from_cache.writeAction(f"movlr 80(X22) X26 0 8") 
  tranDistributedSortPhase1InsertionLb__kv_reducer_get_back_from_cache.writeAction(f"mul X17 X26 X27") 
  tranDistributedSortPhase1InsertionLb__kv_reducer_get_back_from_cache.writeAction(f"add X25 X27 X24") 
  tranDistributedSortPhase1InsertionLb__kv_reducer_get_back_from_cache.writeAction(f"addi X24 X19 0") 
  ## add space for cache
  tranDistributedSortPhase1InsertionLb__kv_reducer_get_back_from_cache.writeAction(f"addi X7 X26 20256") 
  tranDistributedSortPhase1InsertionLb__kv_reducer_get_back_from_cache.writeAction(f"addi X26 X25 1024") 
  tranDistributedSortPhase1InsertionLb__kv_reducer_get_back_from_cache.writeAction(f"addi X25 X20 0") 
  tranDistributedSortPhase1InsertionLb__kv_reducer_get_back_from_cache.writeAction(f"movir X26 0") 
  tranDistributedSortPhase1InsertionLb__kv_reducer_get_back_from_cache.writeAction(f"evlb X26 MemcpyLib::memcpy_dram_to_sp") 
  tranDistributedSortPhase1InsertionLb__kv_reducer_get_back_from_cache.writeAction(f"evi X26 X26 255 4") 
  tranDistributedSortPhase1InsertionLb__kv_reducer_get_back_from_cache.writeAction(f"ev X26 X26 X0 X0 8") 
  tranDistributedSortPhase1InsertionLb__kv_reducer_get_back_from_cache.writeAction(f"sendr3_wret X26 DistributedSortPhase1InsertionLb::kv_reduce_load_sp_return X19 X25 X18 X27") 
  ## print("kv_reduce_end2");
  ## bin_dram_addr = tmp_bin_dram_addr; 
  ## bin_size = local_bin_count;
  tranDistributedSortPhase1InsertionLb__kv_reducer_get_back_from_cache.writeAction(f"yield") 
  
  # Writing code for event DistributedSortPhase1InsertionLb::kv_reduce_load_sp_return
  tranDistributedSortPhase1InsertionLb__kv_reduce_load_sp_return = efa.writeEvent('DistributedSortPhase1InsertionLb::kv_reduce_load_sp_return')
  tranDistributedSortPhase1InsertionLb__kv_reduce_load_sp_return.writeAction(f"entry: addi X20 X22 0") 
  tranDistributedSortPhase1InsertionLb__kv_reduce_load_sp_return.writeAction(f"movir X23 0") 
  tranDistributedSortPhase1InsertionLb__kv_reduce_load_sp_return.writeAction(f"__for_kv_reduce_load_sp_return_0_condition: addi X18 X24 0")  # This is for casting. May be used later on
  tranDistributedSortPhase1InsertionLb__kv_reduce_load_sp_return.writeAction(f"ble X24 X23 __for_kv_reduce_load_sp_return_2_post") 
  tranDistributedSortPhase1InsertionLb__kv_reduce_load_sp_return.writeAction(f"__for_kv_reduce_load_sp_return_1_body: movwlr X22(X23,0,0) X24") 
  tranDistributedSortPhase1InsertionLb__kv_reduce_load_sp_return.writeAction(f"ble X24 X16 __if_kv_reduce_load_sp_return_5_post") 
  tranDistributedSortPhase1InsertionLb__kv_reduce_load_sp_return.writeAction(f"__if_kv_reduce_load_sp_return_3_true: movwlr X22(X23,0,0) X24") 
  tranDistributedSortPhase1InsertionLb__kv_reduce_load_sp_return.writeAction(f"movwrl X16 X22(X23,0,0)") 
  tranDistributedSortPhase1InsertionLb__kv_reduce_load_sp_return.writeAction(f"addi X24 X16 0") 
  tranDistributedSortPhase1InsertionLb__kv_reduce_load_sp_return.writeAction(f"__if_kv_reduce_load_sp_return_5_post: addi X23 X23 1") 
  tranDistributedSortPhase1InsertionLb__kv_reduce_load_sp_return.writeAction(f"jmp __for_kv_reduce_load_sp_return_0_condition") 
  tranDistributedSortPhase1InsertionLb__kv_reduce_load_sp_return.writeAction(f"__for_kv_reduce_load_sp_return_2_post: movwrl X16 X22(X18,0,0)") 
  tranDistributedSortPhase1InsertionLb__kv_reduce_load_sp_return.writeAction(f"addi X18 X18 1") 
  tranDistributedSortPhase1InsertionLb__kv_reduce_load_sp_return.writeAction(f"movir X23 0") 
  tranDistributedSortPhase1InsertionLb__kv_reduce_load_sp_return.writeAction(f"evlb X23 MemcpyLib::memcpy_sp_to_dram") 
  tranDistributedSortPhase1InsertionLb__kv_reduce_load_sp_return.writeAction(f"evi X23 X23 255 4") 
  tranDistributedSortPhase1InsertionLb__kv_reduce_load_sp_return.writeAction(f"ev X23 X23 X0 X0 8") 
  ## print("returning with size : %lu", bin_size);
  tranDistributedSortPhase1InsertionLb__kv_reduce_load_sp_return.writeAction(f"sendr3_wret X23 DistributedSortPhase1InsertionLb::kv_reduce_store_sp_return X20 X19 X18 X24") 
  ## print("kv_reduce_end3");
  tranDistributedSortPhase1InsertionLb__kv_reduce_load_sp_return.writeAction(f"yield") 
  
  # Writing code for event DistributedSortPhase1InsertionLb::kv_reduce_store_sp_return
  tranDistributedSortPhase1InsertionLb__kv_reduce_store_sp_return = efa.writeEvent('DistributedSortPhase1InsertionLb::kv_reduce_store_sp_return')
  ## print("returning to sp return");
  ## send_event(save_cont, 0, IGNRCONT);
  tranDistributedSortPhase1InsertionLb__kv_reduce_store_sp_return.writeAction(f"entry: evi X2 X22 DistributedSortPhase1InsertionLb::kv_reduce_return 1") 
  tranDistributedSortPhase1InsertionLb__kv_reduce_store_sp_return.writeAction(f"movir X23 0") 
  tranDistributedSortPhase1InsertionLb__kv_reduce_store_sp_return.writeAction(f"sendr_wcont X22 X21 X23 X23") 
  ## print("kv_reduce_store_sp_return %lu", save_cont);
  tranDistributedSortPhase1InsertionLb__kv_reduce_store_sp_return.writeAction(f"yield") 
  
  
  ###########################################################
  ###### Writing code for thread DistributedSortPhase2 ######
  ###########################################################
  # Writing code for event DistributedSortPhase2::kv_map
  tranDistributedSortPhase2__kv_map = efa.writeEvent('DistributedSortPhase2::kv_map')
  ## print("<kv_map2> getting key = %lu, value = %lu", key, val);
  tranDistributedSortPhase2__kv_map.writeAction(f"entry: movir X22 0") 
  tranDistributedSortPhase2__kv_map.writeAction(f"evlb X22 DistributedSortPhase2::kv_map_emit") 
  tranDistributedSortPhase2__kv_map.writeAction(f"evi X22 X22 255 4") 
  tranDistributedSortPhase2__kv_map.writeAction(f"ev X22 X22 X0 X0 8") 
  ## unsigned long* local ptr = LMBASE + SORT_OFFSET;
  ## unsigned long ikey = key / ptr[BKSIZE];
  ## print("ikey = %d", ikey);
  ## send_event(evw, val, key, val, CCONT);
  tranDistributedSortPhase2__kv_map.writeAction(f"addi X7 X23 20000") 
  tranDistributedSortPhase2__kv_map.writeAction(f"movlr 88(X23) X25 0 8") 
  tranDistributedSortPhase2__kv_map.writeAction(f"sub X9 X25 X26") 
  tranDistributedSortPhase2__kv_map.writeAction(f"sari X26 X27 3") 
  tranDistributedSortPhase2__kv_map.writeAction(f"movlr 72(X23) X28 0 8") 
  tranDistributedSortPhase2__kv_map.writeAction(f"div X27 X28 X24") 
  ## print("bin_lane_id = %lu", bin_lane_id);
  ## send_event(evw, val / 8, key, val, CCONT);
  tranDistributedSortPhase2__kv_map.writeAction(f"sendr3_wcont X22 X1 X24 X8 X9") 
  tranDistributedSortPhase2__kv_map.writeAction(f"evi X2 X22 DistributedSortPhase2::kv_map_return 1") 
  tranDistributedSortPhase2__kv_map.writeAction(f"sendr_wcont X22 X1 X0 X0") 
  tranDistributedSortPhase2__kv_map.writeAction(f"yield") 
  
  ## event kv_map(unsigned long key, unsigned long val) {
  ## 	print("<kv_map2> getting key = %lu, value = %lu", key, val);
  ##     unsigned long evw = evw_new(NETID, DistributedSortPhase2::kv_map_emit, 2);
  ## 	// unsigned long* local ptr = LMBASE + SORT_OFFSET;
  ## 	// unsigned long ikey = key / ptr[BKSIZE];
  ## 	// print("ikey = %d", ikey);
  ## 	// send_event(evw, val, key, val, CCONT);
  ## 	send_event(evw, val / 8, key, val, CCONT);
  ##     evw = evw_update_event(CEVNT, DistributedSortPhase2::kv_map_return, 2);
  ##     send_event(evw, NETID, NETID, CCONT);
  ## 	yield;
  ## }
  # Writing code for event DistributedSortPhase2::kv_reduce
  tranDistributedSortPhase2__kv_reduce = efa.writeEvent('DistributedSortPhase2::kv_reduce')
  ## print("receiving %lu %lu %lu", ikey, bin_list_size, bin_addr);
  ## print("bin_list_size = %lu", bin_list_size * 8);
  ## unsigned long cur_size = bin_list_size * 8;
  tranDistributedSortPhase2__kv_reduce.writeAction(f"entry: bneiu X9 0 __if_kv_reduce_2_post") 
  tranDistributedSortPhase2__kv_reduce.writeAction(f"__if_kv_reduce_0_true: evi X2 X22 DistributedSortPhase2::kv_reduce_return 1") 
  tranDistributedSortPhase2__kv_reduce.writeAction(f"movir X23 0") 
  tranDistributedSortPhase2__kv_reduce.writeAction(f"sendr_wcont X22 X1 X23 X23") 
  tranDistributedSortPhase2__kv_reduce.writeAction(f"yield") 
  ## allocate space in scratchpad
  tranDistributedSortPhase2__kv_reduce.writeAction(f"__if_kv_reduce_2_post: addi X7 X23 20000") 
  tranDistributedSortPhase2__kv_reduce.writeAction(f"movlr 112(X23) X25 0 8") 
  tranDistributedSortPhase2__kv_reduce.writeAction(f"addi X25 X24 0")  # This is for casting. May be used later on
  tranDistributedSortPhase2__kv_reduce.writeAction(f"movir X21 0") 
  tranDistributedSortPhase2__kv_reduce.writeAction(f"__while_kv_reduce_3_condition: addi X21 X25 0")  # This is for casting. May be used later on
  tranDistributedSortPhase2__kv_reduce.writeAction(f"sar X24 X25 X26") 
  tranDistributedSortPhase2__kv_reduce.writeAction(f"andi X26 X27 1") 
  tranDistributedSortPhase2__kv_reduce.writeAction(f"beqi X27 0 __while_kv_reduce_5_post") 
  tranDistributedSortPhase2__kv_reduce.writeAction(f"__while_kv_reduce_4_body: addi X21 X21 1") 
  tranDistributedSortPhase2__kv_reduce.writeAction(f"jmp __while_kv_reduce_3_condition") 
  tranDistributedSortPhase2__kv_reduce.writeAction(f"__while_kv_reduce_5_post: movir X25 1") 
  tranDistributedSortPhase2__kv_reduce.writeAction(f"sl X25 X21 X25") 
  tranDistributedSortPhase2__kv_reduce.writeAction(f"addi X25 X26 0")  # This is for casting. May be used later on
  tranDistributedSortPhase2__kv_reduce.writeAction(f"or X24 X26 X24") 
  tranDistributedSortPhase2__kv_reduce.writeAction(f"movrl X24 112(X23) 0 8") 
  tranDistributedSortPhase2__kv_reduce.writeAction(f"movir X26 6000") 
  tranDistributedSortPhase2__kv_reduce.writeAction(f"bgtu X9 X26 __if_kv_reduce_7_false") 
  ## print("getting bit = %d for local sort at NWID %lu", local_space_bit, NETID);
  tranDistributedSortPhase2__kv_reduce.writeAction(f"__if_kv_reduce_6_true: evi X2 X22 DistributedSortPhase2::local_bin_sort 1") 
  tranDistributedSortPhase2__kv_reduce.writeAction(f"jmp __if_kv_reduce_8_post") 
  ## print("getting bit = %d for ext merge sort at NWID %lu", local_space_bit, NETID);
  ## print("bin_list_size = %lu", bin_list_size);
  tranDistributedSortPhase2__kv_reduce.writeAction(f"__if_kv_reduce_7_false: evi X2 X22 DistributedSortPhase2::ext_merge_sort 1") 
  tranDistributedSortPhase2__kv_reduce.writeAction(f"__if_kv_reduce_8_post: addi X7 X25 8") 
  tranDistributedSortPhase2__kv_reduce.writeAction(f"movrl X8 0(X25) 0 8") 
  tranDistributedSortPhase2__kv_reduce.writeAction(f"movrl X9 8(X25) 0 8") 
  tranDistributedSortPhase2__kv_reduce.writeAction(f"movrl X10 16(X25) 0 8") 
  tranDistributedSortPhase2__kv_reduce.writeAction(f"addi X7 X27 20256") 
  tranDistributedSortPhase2__kv_reduce.writeAction(f"muli X21 X28 6000") 
  tranDistributedSortPhase2__kv_reduce.writeAction(f"sli X28 X29 3") 
  tranDistributedSortPhase2__kv_reduce.writeAction(f"add X27 X29 X30") 
  tranDistributedSortPhase2__kv_reduce.writeAction(f"movrl X30 24(X25) 0 8") 
  tranDistributedSortPhase2__kv_reduce.writeAction(f"send_wcont X22 X1 X25 4") 
  tranDistributedSortPhase2__kv_reduce.writeAction(f"addi X1 X19 0") 
  ## send_event(evw, ikey, bin_list_size, bin_addr, CCONT);
  tranDistributedSortPhase2__kv_reduce.writeAction(f"yield") 
  ## unsigned long* local ptr = LMBASE + (SORT_OFFSET);
  ## unsigned long bin_size = ptr[BIN_SIZE];
  ## unsigned long bins_per_lane = ptr[BINS_PER_LANE];
  ## unsigned long local_bin_idx = value / bin_size % bins_per_lane;
  ## unsigned long dram_block_size = ptr[DRAM_BLOCK_SIZE];
  ## print("receiving value = %d, local_bin_idx = %d", value, local_bin_idx);
  ## unsigned long * local counter_addr = LMBASE + (SORT_OFFSET + COUNTERS_OFFSET) + 8 * local_bin_idx;
  ## unsigned long local_bin_count = *counter_addr;
  ## unsigned long * local dram_addr = ptr[TMP_ADDR] + value / bin_size * dram_block_size + local_bin_count * 8;
  ## send_dram_write(dram_addr, value, DistributedSortPhase2::kv_reduce_return);
  ## *counter_addr = local_bin_count + 1;
  ## print("%lu", counter_addr);
  ## print("local_bin_idx = %d, local_bin_count = %d, dram_addr = %lu", local_bin_idx, local_bin_count, dram_addr);
  ## yield;
  ## print("d", local_bin_idx);
  ## print("receiving %d %d, local_bin_idx = %d", key, value, local_bin_idx);
  ## unsigned long evw = evw_update_event(CEVNT, DistributedSortPhase2::kv_reduce_return, 2);
  ## // unsigned long evw = evw_update_event(CEVNT, DistributedSortPhase1::kv_combine, 2);
  ## send_event(evw, 0, IGNRCONT);
  tranDistributedSortPhase2__kv_reduce.writeAction(f"yield") 
  
  ## event ext_merge_sort(unsigned long ikey, unsigned long bin_list_size, unsigned long bin_addr) {
  # Writing code for event DistributedSortPhase2::ext_merge_sort
  tranDistributedSortPhase2__ext_merge_sort = efa.writeEvent('DistributedSortPhase2::ext_merge_sort')
  tranDistributedSortPhase2__ext_merge_sort.writeAction(f"entry: print 'in ext_merge_sort, bin_size = %lu' X9") 
  ## unsigned long* local ptr = LMBASE + SORT_OFFSET + VAR_SIZE;
  tranDistributedSortPhase2__ext_merge_sort.writeAction(f"addi X7 X22 20000") 
  tranDistributedSortPhase2__ext_merge_sort.writeAction(f"movlr 88(X22) X24 0 8") 
  tranDistributedSortPhase2__ext_merge_sort.writeAction(f"sub X10 X24 X25") 
  tranDistributedSortPhase2__ext_merge_sort.writeAction(f"sari X25 X23 3") 
  tranDistributedSortPhase2__ext_merge_sort.writeAction(f"movlr 16(X22) X25 0 8") 
  tranDistributedSortPhase2__ext_merge_sort.writeAction(f"movlr 80(X22) X26 0 8") 
  tranDistributedSortPhase2__ext_merge_sort.writeAction(f"mul X23 X26 X27") 
  tranDistributedSortPhase2__ext_merge_sort.writeAction(f"add X25 X27 X24") 
  tranDistributedSortPhase2__ext_merge_sort.writeAction(f"addi X24 X18 0") 
  tranDistributedSortPhase2__ext_merge_sort.writeAction(f"addi X9 X17 0") 
  tranDistributedSortPhase2__ext_merge_sort.writeAction(f"movir X25 0") 
  tranDistributedSortPhase2__ext_merge_sort.writeAction(f"evlb X25 ExternalMergeSort::sort") 
  tranDistributedSortPhase2__ext_merge_sort.writeAction(f"evi X25 X25 255 4") 
  tranDistributedSortPhase2__ext_merge_sort.writeAction(f"ev X25 X25 X0 X0 8") 
  tranDistributedSortPhase2__ext_merge_sort.writeAction(f"addi X7 X26 8") 
  tranDistributedSortPhase2__ext_merge_sort.writeAction(f"movrl X18 0(X26) 0 8") 
  tranDistributedSortPhase2__ext_merge_sort.writeAction(f"movrl X17 8(X26) 0 8") 
  tranDistributedSortPhase2__ext_merge_sort.writeAction(f"movrl X11 16(X26) 0 8") 
  ## unsigned long bk_size = SP_BLOCKSIZE;
  tranDistributedSortPhase2__ext_merge_sort.writeAction(f"movir X28 6000") 
  tranDistributedSortPhase2__ext_merge_sort.writeAction(f"movrl X28 24(X26) 0 8") 
  tranDistributedSortPhase2__ext_merge_sort.writeAction(f"send_wret X25 DistributedSortPhase2::kv_reduce_ext_sort_ret X26 4 X27") 
  ## yield;
  tranDistributedSortPhase2__ext_merge_sort.writeAction(f"yield") 
  
  # Writing code for event DistributedSortPhase2::local_bin_sort
  tranDistributedSortPhase2__local_bin_sort = efa.writeEvent('DistributedSortPhase2::local_bin_sort')
  ## unsigned long* local ptr = LMBASE + SORT_OFFSET + VAR_SIZE;
  tranDistributedSortPhase2__local_bin_sort.writeAction(f"entry: print 'in local_bin_sort, bin_size = %lu' X9") 
  tranDistributedSortPhase2__local_bin_sort.writeAction(f"addi X7 X22 20000") 
  tranDistributedSortPhase2__local_bin_sort.writeAction(f"movlr 88(X22) X24 0 8") 
  tranDistributedSortPhase2__local_bin_sort.writeAction(f"sub X10 X24 X25") 
  tranDistributedSortPhase2__local_bin_sort.writeAction(f"sari X25 X23 3") 
  tranDistributedSortPhase2__local_bin_sort.writeAction(f"movlr 16(X22) X25 0 8") 
  tranDistributedSortPhase2__local_bin_sort.writeAction(f"movlr 80(X22) X26 0 8") 
  tranDistributedSortPhase2__local_bin_sort.writeAction(f"mul X23 X26 X27") 
  tranDistributedSortPhase2__local_bin_sort.writeAction(f"add X25 X27 X24") 
  ## print("starting sorting bin %d", NETID);
  tranDistributedSortPhase2__local_bin_sort.writeAction(f"addi X24 X18 0") 
  ## print("bin_id = %lu", bin_id);
  tranDistributedSortPhase2__local_bin_sort.writeAction(f"sub X11 X18 X20") 
  ## print("sorting bin from dram: %lu, bin_size = %lu", bin_dram_addr, bin_list_size);
  ## if(NETID == 60) {
  ## 		sptr =  LMBASE + (SORT_OFFSET + VAR_SIZE) + local_space_bit * SP_BLOCKSIZE * 8;
  ## 		for (int i = 0; i < bin_list_size; i = i + 1) {
  ## 			print("begin sort60, having %lu", sptr[i]);
  ## 		}
  ## }
  ## for (tot = 0; tot < bin_list_size; tot = tot + 1) {
  ## 	send_dram_read(bin_dram_addr, 1, DistributedSortPhase2::kv_reduce_load_ret);
  ## 	bin_dram_addr = bin_dram_addr + 8;
  ## }
  ## asm {"perflog 1 0 '[NWID %lu] start sorting bin' X0" };
  tranDistributedSortPhase2__local_bin_sort.writeAction(f"movir X25 0") 
  tranDistributedSortPhase2__local_bin_sort.writeAction(f"evlb X25 MemcpyLib::memcpy_dram_to_sp") 
  tranDistributedSortPhase2__local_bin_sort.writeAction(f"evi X25 X25 255 4") 
  tranDistributedSortPhase2__local_bin_sort.writeAction(f"ev X25 X25 X0 X0 8") 
  tranDistributedSortPhase2__local_bin_sort.writeAction(f"sendr3_wret X25 DistributedSortPhase2::kv_reduce_load_ret X18 X11 X9 X26") 
  tranDistributedSortPhase2__local_bin_sort.writeAction(f"addi X24 X18 0") 
  tranDistributedSortPhase2__local_bin_sort.writeAction(f"addi X9 X17 0") 
  tranDistributedSortPhase2__local_bin_sort.writeAction(f"yield") 
  
  # Writing code for event DistributedSortPhase2::kv_reduce_load_ret
  tranDistributedSortPhase2__kv_reduce_load_ret = efa.writeEvent('DistributedSortPhase2::kv_reduce_load_ret')
  ## asm {"perflog 1 0 '[NWID %lu] loadfinish sorting bin' X0" };
  ## start a new thread for sort?
  tranDistributedSortPhase2__kv_reduce_load_ret.writeAction(f"__if_kv_reduce_load_ret_0_true: evi X2 X22 DistributedSortPhase2LocalSort::init 1") 
  tranDistributedSortPhase2__kv_reduce_load_ret.writeAction(f"evi X2 X23 DistributedSortPhase2::kv_reduce_sort_ret 1") 
  tranDistributedSortPhase2__kv_reduce_load_ret.writeAction(f"addi X7 X24 20256") 
  tranDistributedSortPhase2__kv_reduce_load_ret.writeAction(f"muli X21 X25 6000") 
  tranDistributedSortPhase2__kv_reduce_load_ret.writeAction(f"sli X25 X26 3") 
  tranDistributedSortPhase2__kv_reduce_load_ret.writeAction(f"add X24 X26 X27") 
  tranDistributedSortPhase2__kv_reduce_load_ret.writeAction(f"sendr_wcont X22 X23 X17 X27") 
  tranDistributedSortPhase2__kv_reduce_load_ret.writeAction(f"yield") 
  
  # Writing code for event DistributedSortPhase2::kv_reduce_sort_ret
  tranDistributedSortPhase2__kv_reduce_sort_ret = efa.writeEvent('DistributedSortPhase2::kv_reduce_sort_ret')
  ## print("in kv_reduce_sort_ret");
  tranDistributedSortPhase2__kv_reduce_sort_ret.writeAction(f"entry: addi X7 X23 20256") 
  tranDistributedSortPhase2__kv_reduce_sort_ret.writeAction(f"muli X21 X24 6000") 
  tranDistributedSortPhase2__kv_reduce_sort_ret.writeAction(f"sli X24 X25 3") 
  tranDistributedSortPhase2__kv_reduce_sort_ret.writeAction(f"add X23 X25 X22") 
  tranDistributedSortPhase2__kv_reduce_sort_ret.writeAction(f"sub X22 X20 X18") 
  tranDistributedSortPhase2__kv_reduce_sort_ret.writeAction(f"movir X23 0") 
  tranDistributedSortPhase2__kv_reduce_sort_ret.writeAction(f"evlb X23 MemcpyLib::memcpy_sp_to_dram") 
  tranDistributedSortPhase2__kv_reduce_sort_ret.writeAction(f"evi X23 X23 255 4") 
  tranDistributedSortPhase2__kv_reduce_sort_ret.writeAction(f"ev X23 X23 X0 X0 8") 
  tranDistributedSortPhase2__kv_reduce_sort_ret.writeAction(f"sendr3_wret X23 DistributedSortPhase2::kv_reduce_sort_send_back_ret X22 X18 X17 X24") 
  ## asm {"perflog 1 0 '[NWID %lu] sortfinish sorting bin' X0" };
  ## for (tot = 0; tot < bin_size; tot = tot + 1) {
  ## 	send_dram_write(bin_dram_addr, lm_ptr, 1, kv_reduce_sort_send_back_ret);
  ## 	bin_dram_addr = bin_dram_addr + 8;
  ## 	lm_ptr = lm_ptr + 8;
  ## }
  tranDistributedSortPhase2__kv_reduce_sort_ret.writeAction(f"yield") 
  
  # Writing code for event DistributedSortPhase2::kv_reduce_sort_send_back_ret
  tranDistributedSortPhase2__kv_reduce_sort_send_back_ret = efa.writeEvent('DistributedSortPhase2::kv_reduce_sort_send_back_ret')
  ## print("sended back sorted bin to dram: %lu, bin_size = %lu", bin_dram_addr, bin_size);
  ## asm {"perflog 1 0 '[NWID %lu] storefinish sorting bin' X0" };
  tranDistributedSortPhase2__kv_reduce_sort_send_back_ret.writeAction(f"__if_kv_reduce_sort_send_back_ret_0_true: evi X2 X22 DistributedSortPhase2::kv_reduce_return 1") 
  tranDistributedSortPhase2__kv_reduce_sort_send_back_ret.writeAction(f"movir X25 0") 
  tranDistributedSortPhase2__kv_reduce_sort_send_back_ret.writeAction(f"sendr_wcont X22 X19 X25 X25") 
  ## send_event(evw, 0, IGNRCONT);
  ## clear the current bit
  tranDistributedSortPhase2__kv_reduce_sort_send_back_ret.writeAction(f"addi X7 X23 20000") 
  tranDistributedSortPhase2__kv_reduce_sort_send_back_ret.writeAction(f"movlr 112(X23) X25 0 8") 
  tranDistributedSortPhase2__kv_reduce_sort_send_back_ret.writeAction(f"addi X25 X24 0")  # This is for casting. May be used later on
  tranDistributedSortPhase2__kv_reduce_sort_send_back_ret.writeAction(f"movir X25 1") 
  tranDistributedSortPhase2__kv_reduce_sort_send_back_ret.writeAction(f"sl X25 X21 X25") 
  tranDistributedSortPhase2__kv_reduce_sort_send_back_ret.writeAction(f"addi X25 X26 0")  # This is for casting. May be used later on
  tranDistributedSortPhase2__kv_reduce_sort_send_back_ret.writeAction(f"xor X24 X26 X24") 
  tranDistributedSortPhase2__kv_reduce_sort_send_back_ret.writeAction(f"movrl X24 112(X23) 0 8") 
  tranDistributedSortPhase2__kv_reduce_sort_send_back_ret.writeAction(f"yield") 
  
  # Writing code for event DistributedSortPhase2::kv_reduce_ext_sort_ret
  tranDistributedSortPhase2__kv_reduce_ext_sort_ret = efa.writeEvent('DistributedSortPhase2::kv_reduce_ext_sort_ret')
  ## asm {"perflog 1 0 '[NWID %lu] end sorting bin' X0" };
  tranDistributedSortPhase2__kv_reduce_ext_sort_ret.writeAction(f"entry: evi X2 X22 DistributedSortPhase2::kv_reduce_return 1") 
  tranDistributedSortPhase2__kv_reduce_ext_sort_ret.writeAction(f"movir X25 0") 
  tranDistributedSortPhase2__kv_reduce_ext_sort_ret.writeAction(f"sendr_wcont X22 X19 X25 X25") 
  ## send_event(evw, 0, IGNRCONT);
  tranDistributedSortPhase2__kv_reduce_ext_sort_ret.writeAction(f"addi X7 X23 20000") 
  tranDistributedSortPhase2__kv_reduce_ext_sort_ret.writeAction(f"movlr 112(X23) X25 0 8") 
  tranDistributedSortPhase2__kv_reduce_ext_sort_ret.writeAction(f"addi X25 X24 0")  # This is for casting. May be used later on
  tranDistributedSortPhase2__kv_reduce_ext_sort_ret.writeAction(f"movir X25 1") 
  tranDistributedSortPhase2__kv_reduce_ext_sort_ret.writeAction(f"sl X25 X21 X25") 
  tranDistributedSortPhase2__kv_reduce_ext_sort_ret.writeAction(f"addi X25 X26 0")  # This is for casting. May be used later on
  tranDistributedSortPhase2__kv_reduce_ext_sort_ret.writeAction(f"xor X24 X26 X24") 
  tranDistributedSortPhase2__kv_reduce_ext_sort_ret.writeAction(f"movrl X24 112(X23) 0 8") 
  tranDistributedSortPhase2__kv_reduce_ext_sort_ret.writeAction(f"yield") 
  
  
  #################################################################
  ###### Writing code for thread DistributedSortPhase2Mapper ######
  #################################################################
  # Writing code for event DistributedSortPhase2Mapper::kv_map
  tranDistributedSortPhase2Mapper__kv_map = efa.writeEvent('DistributedSortPhase2Mapper::kv_map')
  tranDistributedSortPhase2Mapper__kv_map.writeAction(f"entry: addi X1 X19 0") 
  ## evw = evw_update_event(CEVNT, DistributedSortPhase2Mapper::kv_map_return);
  ## print("skipping3");
  ## send_event(evw, 0, save_cont);
  ## yield;
  ## print("<adsdsaicoxshui> getting key = %lu, value = %lu", key, val);
  tranDistributedSortPhase2Mapper__kv_map.writeAction(f"evi X2 X22 DistributedSortPhase2Mapper::kv_map_cont 1") 
  ## unsigned long* local ptr = LMBASE + SORT_OFFSET;
  ## unsigned long ikey = key / ptr[BKSIZE];
  ## print("ikey = %d", ikey);
  ## send_event(evw, val, key, val, CCONT);
  tranDistributedSortPhase2Mapper__kv_map.writeAction(f"addi X7 X23 20000") 
  tranDistributedSortPhase2Mapper__kv_map.writeAction(f"movlr 88(X23) X25 0 8") 
  tranDistributedSortPhase2Mapper__kv_map.writeAction(f"sub X9 X25 X26") 
  tranDistributedSortPhase2Mapper__kv_map.writeAction(f"sari X26 X27 3") 
  tranDistributedSortPhase2Mapper__kv_map.writeAction(f"movlr 72(X23) X28 0 8") 
  tranDistributedSortPhase2Mapper__kv_map.writeAction(f"div X27 X28 X24") 
  ## print("bin_lane_id = %lu", bin_lane_id);
  ## send_event(evw, val / 8, key, val, CCONT);
  tranDistributedSortPhase2Mapper__kv_map.writeAction(f"sendr3_wcont X22 X1 X24 X8 X9") 
  tranDistributedSortPhase2Mapper__kv_map.writeAction(f"addi X24 X25 0") 
  tranDistributedSortPhase2Mapper__kv_map.writeAction(f"addi X8 X26 0") 
  tranDistributedSortPhase2Mapper__kv_map.writeAction(f"addi X9 X27 0") 
  ## evw = evw_update_event(CEVNT, DistributedSortPhase2Mapper::kv_map_return, 2);
  ## send_event(evw, NETID, NETID, CCONT);
  tranDistributedSortPhase2Mapper__kv_map.writeAction(f"yield") 
  
  ## // event kv_map(unsigned long key, unsigned long val) {
  ## // 	print("<kv_map2> getting key = %lu, value = %lu", key, val);
  ## //     unsigned long evw = evw_new(NETID, DistributedSortPhase2Mapper::kv_map_emit, 2);
  ## // 	// unsigned long* local ptr = LMBASE + SORT_OFFSET;
  ## // 	// unsigned long ikey = key / ptr[BKSIZE];
  ## // 	// print("ikey = %d", ikey);
  ## // 	// send_event(evw, val, key, val, CCONT);
  ## // 	send_event(evw, val / 8, key, val, CCONT);
  ## //     evw = evw_update_event(CEVNT, DistributedSortPhase2Mapper::kv_map_return, 2);
  ## //     send_event(evw, NETID, NETID, CCONT);
  ## // 	yield;
  ## // }
  # Writing code for event DistributedSortPhase2Mapper::kv_map_cont
  tranDistributedSortPhase2Mapper__kv_map_cont = efa.writeEvent('DistributedSortPhase2Mapper::kv_map_cont')
  tranDistributedSortPhase2Mapper__kv_map_cont.writeAction(f"entry: print 'receiving %lu %lu %lu' X8 X9 X10") 
  ## print("bin_list_size = %lu", bin_list_size * 8);
  ## unsigned long cur_size = bin_list_size * 8;
  ## evw = evw_update_event(CEVNT, DistributedSortPhase2Mapper::kv_map_return);
  ## print("skipping2");
  ## send_event(evw, NETID, NETID, save_cont);
  ## yield;
  tranDistributedSortPhase2Mapper__kv_map_cont.writeAction(f"bneiu X9 0 __if_kv_map_cont_2_post") 
  tranDistributedSortPhase2Mapper__kv_map_cont.writeAction(f"__if_kv_map_cont_0_true: evi X2 X22 DistributedSortPhase2Mapper::kv_map_return 1") 
  tranDistributedSortPhase2Mapper__kv_map_cont.writeAction(f"movir X23 0") 
  tranDistributedSortPhase2Mapper__kv_map_cont.writeAction(f"sendr_wcont X22 X1 X23 X23") 
  tranDistributedSortPhase2Mapper__kv_map_cont.writeAction(f"yield") 
  ## allocate space in scratchpad
  tranDistributedSortPhase2Mapper__kv_map_cont.writeAction(f"__if_kv_map_cont_2_post: addi X7 X23 20000") 
  tranDistributedSortPhase2Mapper__kv_map_cont.writeAction(f"movlr 112(X23) X25 0 8") 
  tranDistributedSortPhase2Mapper__kv_map_cont.writeAction(f"addi X25 X24 0")  # This is for casting. May be used later on
  tranDistributedSortPhase2Mapper__kv_map_cont.writeAction(f"movir X21 0") 
  tranDistributedSortPhase2Mapper__kv_map_cont.writeAction(f"__while_kv_map_cont_3_condition: addi X21 X25 0")  # This is for casting. May be used later on
  tranDistributedSortPhase2Mapper__kv_map_cont.writeAction(f"sar X24 X25 X26") 
  tranDistributedSortPhase2Mapper__kv_map_cont.writeAction(f"andi X26 X27 1") 
  tranDistributedSortPhase2Mapper__kv_map_cont.writeAction(f"beqi X27 0 __while_kv_map_cont_5_post") 
  tranDistributedSortPhase2Mapper__kv_map_cont.writeAction(f"__while_kv_map_cont_4_body: addi X21 X21 1") 
  tranDistributedSortPhase2Mapper__kv_map_cont.writeAction(f"jmp __while_kv_map_cont_3_condition") 
  tranDistributedSortPhase2Mapper__kv_map_cont.writeAction(f"__while_kv_map_cont_5_post: movir X25 1") 
  tranDistributedSortPhase2Mapper__kv_map_cont.writeAction(f"sl X25 X21 X25") 
  tranDistributedSortPhase2Mapper__kv_map_cont.writeAction(f"addi X25 X26 0")  # This is for casting. May be used later on
  tranDistributedSortPhase2Mapper__kv_map_cont.writeAction(f"or X24 X26 X24") 
  tranDistributedSortPhase2Mapper__kv_map_cont.writeAction(f"movrl X24 112(X23) 0 8") 
  tranDistributedSortPhase2Mapper__kv_map_cont.writeAction(f"movir X26 6000") 
  tranDistributedSortPhase2Mapper__kv_map_cont.writeAction(f"bgtu X9 X26 __if_kv_map_cont_7_false") 
  ## print("getting bit = %d for local sort at NWID %lu", local_space_bit, NETID);
  tranDistributedSortPhase2Mapper__kv_map_cont.writeAction(f"__if_kv_map_cont_6_true: evi X2 X22 DistributedSortPhase2Mapper::local_bin_sort 1") 
  tranDistributedSortPhase2Mapper__kv_map_cont.writeAction(f"jmp __if_kv_map_cont_8_post") 
  ## print("getting bit = %d for ext merge sort at NWID %lu", local_space_bit, NETID);
  ## print("bin_list_size = %lu", bin_list_size);
  tranDistributedSortPhase2Mapper__kv_map_cont.writeAction(f"__if_kv_map_cont_7_false: evi X2 X22 DistributedSortPhase2Mapper::ext_merge_sort 1") 
  tranDistributedSortPhase2Mapper__kv_map_cont.writeAction(f"__if_kv_map_cont_8_post: addi X7 X25 8") 
  tranDistributedSortPhase2Mapper__kv_map_cont.writeAction(f"movrl X8 0(X25) 0 8") 
  tranDistributedSortPhase2Mapper__kv_map_cont.writeAction(f"movrl X9 8(X25) 0 8") 
  tranDistributedSortPhase2Mapper__kv_map_cont.writeAction(f"movrl X10 16(X25) 0 8") 
  tranDistributedSortPhase2Mapper__kv_map_cont.writeAction(f"addi X7 X27 20256") 
  tranDistributedSortPhase2Mapper__kv_map_cont.writeAction(f"muli X21 X28 6000") 
  tranDistributedSortPhase2Mapper__kv_map_cont.writeAction(f"sli X28 X29 3") 
  tranDistributedSortPhase2Mapper__kv_map_cont.writeAction(f"add X27 X29 X30") 
  tranDistributedSortPhase2Mapper__kv_map_cont.writeAction(f"movrl X30 24(X25) 0 8") 
  tranDistributedSortPhase2Mapper__kv_map_cont.writeAction(f"send_wcont X22 X1 X25 4") 
  ## send_event(evw, ikey, bin_list_size, bin_addr, CCONT);
  tranDistributedSortPhase2Mapper__kv_map_cont.writeAction(f"yield") 
  ## unsigned long* local ptr = LMBASE + (SORT_OFFSET);
  ## unsigned long bin_size = ptr[BIN_SIZE];
  ## unsigned long bins_per_lane = ptr[BINS_PER_LANE];
  ## unsigned long local_bin_idx = value / bin_size % bins_per_lane;
  ## unsigned long dram_block_size = ptr[DRAM_BLOCK_SIZE];
  ## print("receiving value = %d, local_bin_idx = %d", value, local_bin_idx);
  ## unsigned long * local counter_addr = LMBASE + (SORT_OFFSET + COUNTERS_OFFSET) + 8 * local_bin_idx;
  ## unsigned long local_bin_count = *counter_addr;
  ## unsigned long * local dram_addr = ptr[TMP_ADDR] + value / bin_size * dram_block_size + local_bin_count * 8;
  ## send_dram_write(dram_addr, value, DistributedSortPhase2Mapper::kv_reduce_return);
  ## *counter_addr = local_bin_count + 1;
  ## print("%lu", counter_addr);
  ## print("local_bin_idx = %d, local_bin_count = %d, dram_addr = %lu", local_bin_idx, local_bin_count, dram_addr);
  ## yield;
  ## print("d", local_bin_idx);
  ## print("receiving %d %d, local_bin_idx = %d", key, value, local_bin_idx);
  ## unsigned long evw = evw_update_event(CEVNT, DistributedSortPhase2Mapper::kv_reduce_return, 2);
  ## // unsigned long evw = evw_update_event(CEVNT, DistributedSortPhase1::kv_combine, 2);
  ## send_event(evw, 0, IGNRCONT);
  tranDistributedSortPhase2Mapper__kv_map_cont.writeAction(f"yield") 
  
  # Writing code for event DistributedSortPhase2Mapper::kv_reduce
  tranDistributedSortPhase2Mapper__kv_reduce = efa.writeEvent('DistributedSortPhase2Mapper::kv_reduce')
  tranDistributedSortPhase2Mapper__kv_reduce.writeAction(f"entry: yield") 
  
  ## event ext_merge_sort(unsigned long ikey, unsigned long bin_list_size, unsigned long bin_addr) {
  # Writing code for event DistributedSortPhase2Mapper::ext_merge_sort
  tranDistributedSortPhase2Mapper__ext_merge_sort = efa.writeEvent('DistributedSortPhase2Mapper::ext_merge_sort')
  tranDistributedSortPhase2Mapper__ext_merge_sort.writeAction(f"entry: print 'in ext_merge_sort, bin_size = %lu' X9") 
  ## unsigned long* local ptr = LMBASE + SORT_OFFSET + VAR_SIZE;
  tranDistributedSortPhase2Mapper__ext_merge_sort.writeAction(f"addi X7 X22 20000") 
  tranDistributedSortPhase2Mapper__ext_merge_sort.writeAction(f"movlr 88(X22) X24 0 8") 
  tranDistributedSortPhase2Mapper__ext_merge_sort.writeAction(f"sub X10 X24 X25") 
  tranDistributedSortPhase2Mapper__ext_merge_sort.writeAction(f"sari X25 X23 3") 
  tranDistributedSortPhase2Mapper__ext_merge_sort.writeAction(f"movlr 16(X22) X25 0 8") 
  tranDistributedSortPhase2Mapper__ext_merge_sort.writeAction(f"movlr 80(X22) X26 0 8") 
  tranDistributedSortPhase2Mapper__ext_merge_sort.writeAction(f"mul X23 X26 X27") 
  tranDistributedSortPhase2Mapper__ext_merge_sort.writeAction(f"add X25 X27 X24") 
  tranDistributedSortPhase2Mapper__ext_merge_sort.writeAction(f"addi X24 X18 0") 
  tranDistributedSortPhase2Mapper__ext_merge_sort.writeAction(f"addi X9 X17 0") 
  tranDistributedSortPhase2Mapper__ext_merge_sort.writeAction(f"movir X25 0") 
  tranDistributedSortPhase2Mapper__ext_merge_sort.writeAction(f"evlb X25 ExternalMergeSort::sort") 
  tranDistributedSortPhase2Mapper__ext_merge_sort.writeAction(f"evi X25 X25 255 4") 
  tranDistributedSortPhase2Mapper__ext_merge_sort.writeAction(f"ev X25 X25 X0 X0 8") 
  tranDistributedSortPhase2Mapper__ext_merge_sort.writeAction(f"addi X7 X26 8") 
  tranDistributedSortPhase2Mapper__ext_merge_sort.writeAction(f"movrl X18 0(X26) 0 8") 
  tranDistributedSortPhase2Mapper__ext_merge_sort.writeAction(f"movrl X17 8(X26) 0 8") 
  tranDistributedSortPhase2Mapper__ext_merge_sort.writeAction(f"movrl X11 16(X26) 0 8") 
  ## unsigned long bk_size = SP_BLOCKSIZE;
  tranDistributedSortPhase2Mapper__ext_merge_sort.writeAction(f"movir X28 6000") 
  tranDistributedSortPhase2Mapper__ext_merge_sort.writeAction(f"movrl X28 24(X26) 0 8") 
  tranDistributedSortPhase2Mapper__ext_merge_sort.writeAction(f"send_wret X25 DistributedSortPhase2Mapper::kv_reduce_ext_sort_ret X26 4 X27") 
  ## yield;
  tranDistributedSortPhase2Mapper__ext_merge_sort.writeAction(f"yield") 
  
  # Writing code for event DistributedSortPhase2Mapper::local_bin_sort
  tranDistributedSortPhase2Mapper__local_bin_sort = efa.writeEvent('DistributedSortPhase2Mapper::local_bin_sort')
  ## unsigned long* local ptr = LMBASE + SORT_OFFSET + VAR_SIZE; 
  tranDistributedSortPhase2Mapper__local_bin_sort.writeAction(f"entry: print 'in local_bin_sort, bin_size = %lu' X9") 
  tranDistributedSortPhase2Mapper__local_bin_sort.writeAction(f"addi X7 X22 20000") 
  tranDistributedSortPhase2Mapper__local_bin_sort.writeAction(f"movlr 88(X22) X24 0 8") 
  tranDistributedSortPhase2Mapper__local_bin_sort.writeAction(f"sub X10 X24 X25") 
  tranDistributedSortPhase2Mapper__local_bin_sort.writeAction(f"sari X25 X23 3") 
  tranDistributedSortPhase2Mapper__local_bin_sort.writeAction(f"movlr 16(X22) X25 0 8") 
  tranDistributedSortPhase2Mapper__local_bin_sort.writeAction(f"movlr 80(X22) X26 0 8") 
  tranDistributedSortPhase2Mapper__local_bin_sort.writeAction(f"mul X23 X26 X27") 
  tranDistributedSortPhase2Mapper__local_bin_sort.writeAction(f"add X25 X27 X24") 
  ## print("starting sorting bin %d", NETID);
  tranDistributedSortPhase2Mapper__local_bin_sort.writeAction(f"addi X24 X18 0") 
  ## print("bin_id = %lu", bin_id);
  tranDistributedSortPhase2Mapper__local_bin_sort.writeAction(f"sub X11 X18 X20") 
  ## print("sorting bin from dram: %lu, bin_size = %lu", bin_dram_addr, bin_list_size);
  ## if(NETID == 60) {
  ## 		sptr =  LMBASE + (SORT_OFFSET + VAR_SIZE) + local_space_bit * SP_BLOCKSIZE * 8;
  ## 		for (int i = 0; i < bin_list_size; i = i + 1) {
  ## 			print("begin sort60, having %lu", sptr[i]);
  ## 		}
  ## }
  ## for (tot = 0; tot < bin_list_size; tot = tot + 1) {
  ## 	send_dram_read(bin_dram_addr, 1, DistributedSortPhase2Mapper::kv_reduce_load_ret);
  ## 	bin_dram_addr = bin_dram_addr + 8;
  ## }
  ## asm {"perflog 1 0 '[NWID %lu] start sorting bin' X0" };
  tranDistributedSortPhase2Mapper__local_bin_sort.writeAction(f"movir X25 0") 
  tranDistributedSortPhase2Mapper__local_bin_sort.writeAction(f"evlb X25 MemcpyLib::memcpy_dram_to_sp") 
  tranDistributedSortPhase2Mapper__local_bin_sort.writeAction(f"evi X25 X25 255 4") 
  tranDistributedSortPhase2Mapper__local_bin_sort.writeAction(f"ev X25 X25 X0 X0 8") 
  tranDistributedSortPhase2Mapper__local_bin_sort.writeAction(f"sendr3_wret X25 DistributedSortPhase2Mapper::kv_reduce_load_ret X18 X11 X9 X26") 
  tranDistributedSortPhase2Mapper__local_bin_sort.writeAction(f"addi X24 X18 0") 
  tranDistributedSortPhase2Mapper__local_bin_sort.writeAction(f"addi X9 X17 0") 
  tranDistributedSortPhase2Mapper__local_bin_sort.writeAction(f"yield") 
  
  # Writing code for event DistributedSortPhase2Mapper::kv_reduce_load_ret
  tranDistributedSortPhase2Mapper__kv_reduce_load_ret = efa.writeEvent('DistributedSortPhase2Mapper::kv_reduce_load_ret')
  ## asm {"perflog 1 0 '[NWID %lu] loadfinish sorting bin' X0" };
  ## start a new thread for sort?
  tranDistributedSortPhase2Mapper__kv_reduce_load_ret.writeAction(f"__if_kv_reduce_load_ret_0_true: evi X2 X22 DistributedSortPhase2LocalSort::init 1") 
  tranDistributedSortPhase2Mapper__kv_reduce_load_ret.writeAction(f"evi X2 X23 DistributedSortPhase2Mapper::kv_reduce_sort_ret 1") 
  tranDistributedSortPhase2Mapper__kv_reduce_load_ret.writeAction(f"addi X7 X24 20256") 
  tranDistributedSortPhase2Mapper__kv_reduce_load_ret.writeAction(f"muli X21 X25 6000") 
  tranDistributedSortPhase2Mapper__kv_reduce_load_ret.writeAction(f"sli X25 X26 3") 
  tranDistributedSortPhase2Mapper__kv_reduce_load_ret.writeAction(f"add X24 X26 X27") 
  tranDistributedSortPhase2Mapper__kv_reduce_load_ret.writeAction(f"sendr_wcont X22 X23 X17 X27") 
  tranDistributedSortPhase2Mapper__kv_reduce_load_ret.writeAction(f"yield") 
  
  # Writing code for event DistributedSortPhase2Mapper::kv_reduce_sort_ret
  tranDistributedSortPhase2Mapper__kv_reduce_sort_ret = efa.writeEvent('DistributedSortPhase2Mapper::kv_reduce_sort_ret')
  ## print("in kv_reduce_sort_ret");
  tranDistributedSortPhase2Mapper__kv_reduce_sort_ret.writeAction(f"entry: addi X7 X23 20256") 
  tranDistributedSortPhase2Mapper__kv_reduce_sort_ret.writeAction(f"muli X21 X24 6000") 
  tranDistributedSortPhase2Mapper__kv_reduce_sort_ret.writeAction(f"sli X24 X25 3") 
  tranDistributedSortPhase2Mapper__kv_reduce_sort_ret.writeAction(f"add X23 X25 X22") 
  tranDistributedSortPhase2Mapper__kv_reduce_sort_ret.writeAction(f"sub X22 X20 X18") 
  tranDistributedSortPhase2Mapper__kv_reduce_sort_ret.writeAction(f"movir X23 0") 
  tranDistributedSortPhase2Mapper__kv_reduce_sort_ret.writeAction(f"evlb X23 MemcpyLib::memcpy_sp_to_dram") 
  tranDistributedSortPhase2Mapper__kv_reduce_sort_ret.writeAction(f"evi X23 X23 255 4") 
  tranDistributedSortPhase2Mapper__kv_reduce_sort_ret.writeAction(f"ev X23 X23 X0 X0 8") 
  tranDistributedSortPhase2Mapper__kv_reduce_sort_ret.writeAction(f"sendr3_wret X23 DistributedSortPhase2Mapper::kv_reduce_sort_send_back_ret X22 X18 X17 X24") 
  ## asm {"perflog 1 0 '[NWID %lu] sortfinish sorting bin' X0" };
  ## for (tot = 0; tot < bin_size; tot = tot + 1) {
  ## 	send_dram_write(bin_dram_addr, lm_ptr, 1, kv_reduce_sort_send_back_ret);
  ## 	bin_dram_addr = bin_dram_addr + 8;
  ## 	lm_ptr = lm_ptr + 8;
  ## }
  tranDistributedSortPhase2Mapper__kv_reduce_sort_ret.writeAction(f"yield") 
  
  # Writing code for event DistributedSortPhase2Mapper::kv_reduce_sort_send_back_ret
  tranDistributedSortPhase2Mapper__kv_reduce_sort_send_back_ret = efa.writeEvent('DistributedSortPhase2Mapper::kv_reduce_sort_send_back_ret')
  ## print("sended back sorted bin to dram: %lu, bin_size = %lu", bin_dram_addr, bin_size);
  ## asm {"perflog 1 0 '[NWID %lu] storefinish sorting bin' X0" };
  tranDistributedSortPhase2Mapper__kv_reduce_sort_send_back_ret.writeAction(f"__if_kv_reduce_sort_send_back_ret_0_true: evi X2 X22 DistributedSortPhase2Mapper::kv_map_return 1") 
  tranDistributedSortPhase2Mapper__kv_reduce_sort_send_back_ret.writeAction(f"movir X25 0") 
  tranDistributedSortPhase2Mapper__kv_reduce_sort_send_back_ret.writeAction(f"sendr_wcont X22 X19 X25 X25") 
  ## send_event(evw, 0, IGNRCONT);
  ## clear the current bit
  tranDistributedSortPhase2Mapper__kv_reduce_sort_send_back_ret.writeAction(f"addi X7 X23 20000") 
  tranDistributedSortPhase2Mapper__kv_reduce_sort_send_back_ret.writeAction(f"movlr 112(X23) X25 0 8") 
  tranDistributedSortPhase2Mapper__kv_reduce_sort_send_back_ret.writeAction(f"addi X25 X24 0")  # This is for casting. May be used later on
  tranDistributedSortPhase2Mapper__kv_reduce_sort_send_back_ret.writeAction(f"movir X25 1") 
  tranDistributedSortPhase2Mapper__kv_reduce_sort_send_back_ret.writeAction(f"sl X25 X21 X25") 
  tranDistributedSortPhase2Mapper__kv_reduce_sort_send_back_ret.writeAction(f"addi X25 X26 0")  # This is for casting. May be used later on
  tranDistributedSortPhase2Mapper__kv_reduce_sort_send_back_ret.writeAction(f"xor X24 X26 X24") 
  tranDistributedSortPhase2Mapper__kv_reduce_sort_send_back_ret.writeAction(f"movrl X24 112(X23) 0 8") 
  tranDistributedSortPhase2Mapper__kv_reduce_sort_send_back_ret.writeAction(f"yield") 
  
  # Writing code for event DistributedSortPhase2Mapper::kv_reduce_ext_sort_ret
  tranDistributedSortPhase2Mapper__kv_reduce_ext_sort_ret = efa.writeEvent('DistributedSortPhase2Mapper::kv_reduce_ext_sort_ret')
  ## asm {"perflog 1 0 '[NWID %lu] end sorting bin' X0" };
  ## unsigned long evw = evw_update_event(CEVNT, DistributedSortPhase2Mapper::kv_reduce_return);
  tranDistributedSortPhase2Mapper__kv_reduce_ext_sort_ret.writeAction(f"entry: evi X2 X22 DistributedSortPhase2Mapper::kv_map_return 1") 
  tranDistributedSortPhase2Mapper__kv_reduce_ext_sort_ret.writeAction(f"movir X25 0") 
  tranDistributedSortPhase2Mapper__kv_reduce_ext_sort_ret.writeAction(f"sendr_wcont X22 X19 X25 X25") 
  ## send_event(evw, 0, IGNRCONT);
  tranDistributedSortPhase2Mapper__kv_reduce_ext_sort_ret.writeAction(f"addi X7 X23 20000") 
  tranDistributedSortPhase2Mapper__kv_reduce_ext_sort_ret.writeAction(f"movlr 112(X23) X25 0 8") 
  tranDistributedSortPhase2Mapper__kv_reduce_ext_sort_ret.writeAction(f"addi X25 X24 0")  # This is for casting. May be used later on
  tranDistributedSortPhase2Mapper__kv_reduce_ext_sort_ret.writeAction(f"movir X25 1") 
  tranDistributedSortPhase2Mapper__kv_reduce_ext_sort_ret.writeAction(f"sl X25 X21 X25") 
  tranDistributedSortPhase2Mapper__kv_reduce_ext_sort_ret.writeAction(f"addi X25 X26 0")  # This is for casting. May be used later on
  tranDistributedSortPhase2Mapper__kv_reduce_ext_sort_ret.writeAction(f"xor X24 X26 X24") 
  tranDistributedSortPhase2Mapper__kv_reduce_ext_sort_ret.writeAction(f"movrl X24 112(X23) 0 8") 
  tranDistributedSortPhase2Mapper__kv_reduce_ext_sort_ret.writeAction(f"yield") 
  
  
  #############################################################
  ###### Writing code for thread DistributedSortPhase2Lb ######
  #############################################################
  ## event kv_map(unsigned long key, unsigned long val) {
  ## // print("<kv_map2> getting key = %lu, value = %lu", key, val);
  ##     unsigned long evw = evw_new(NETID, DistributedSortPhase2Lb::kv_map_emit, 2);
  ## // unsigned long* local ptr = LMBASE + SORT_OFFSET;
  ## // unsigned long ikey = key / ptr[BKSIZE];
  ## // print("ikey = %d", ikey);
  ## // send_event(evw, val, key, val, CCONT);
  ## send_event(evw, val / 8, key, val, CCONT);
  ##     evw = evw_update_event(CEVNT, DistributedSortPhase2Lb::kv_map_return, 2);
  ##     send_event(evw, NETID, NETID, CCONT);
  ## yield;
  ## }
  # Writing code for event DistributedSortPhase2Lb::kv_map
  tranDistributedSortPhase2Lb__kv_map = efa.writeEvent('DistributedSortPhase2Lb::kv_map')
  ## print("<kv_map2> getting key = %lu, value = %lu", key, val);
  tranDistributedSortPhase2Lb__kv_map.writeAction(f"entry: movir X22 0") 
  tranDistributedSortPhase2Lb__kv_map.writeAction(f"evlb X22 DistributedSortPhase2Lb::kv_map_emit") 
  tranDistributedSortPhase2Lb__kv_map.writeAction(f"evi X22 X22 255 4") 
  tranDistributedSortPhase2Lb__kv_map.writeAction(f"ev X22 X22 X0 X0 8") 
  ## unsigned long* local ptr = LMBASE + SORT_OFFSET;
  ## unsigned long ikey = key / ptr[BKSIZE];
  ## print("ikey = %d", ikey);
  ## send_event(evw, val, key, val, CCONT);
  tranDistributedSortPhase2Lb__kv_map.writeAction(f"addi X7 X23 20000") 
  tranDistributedSortPhase2Lb__kv_map.writeAction(f"movlr 88(X23) X25 0 8") 
  tranDistributedSortPhase2Lb__kv_map.writeAction(f"sub X9 X25 X26") 
  tranDistributedSortPhase2Lb__kv_map.writeAction(f"sari X26 X27 3") 
  tranDistributedSortPhase2Lb__kv_map.writeAction(f"movlr 72(X23) X28 0 8") 
  tranDistributedSortPhase2Lb__kv_map.writeAction(f"div X27 X28 X24") 
  ## print("bin_lane_id = %lu", bin_lane_id);
  ## send_event(evw, val / 8, key, val, CCONT);
  tranDistributedSortPhase2Lb__kv_map.writeAction(f"sendr3_wcont X22 X1 X24 X8 X9") 
  tranDistributedSortPhase2Lb__kv_map.writeAction(f"evi X2 X22 DistributedSortPhase2Lb::kv_map_return 1") 
  tranDistributedSortPhase2Lb__kv_map.writeAction(f"sendr_wcont X22 X1 X0 X0") 
  tranDistributedSortPhase2Lb__kv_map.writeAction(f"yield") 
  
  # Writing code for event DistributedSortPhase2Lb::kv_reduce
  tranDistributedSortPhase2Lb__kv_reduce = efa.writeEvent('DistributedSortPhase2Lb::kv_reduce')
  ## print("receiving %lu %lu %lu", ikey, bin_list_size, bin_addr);
  ## TODO: need to manage scratchpad
  ## print("bin_list_size = %lu", bin_list_size * 8);
  ## unsigned long cur_size = bin_list_size * 8;
  tranDistributedSortPhase2Lb__kv_reduce.writeAction(f"entry: bneiu X9 0 __if_kv_reduce_2_post") 
  tranDistributedSortPhase2Lb__kv_reduce.writeAction(f"__if_kv_reduce_0_true: evi X2 X22 DistributedSortPhase2Lb::kv_reduce_return 1") 
  tranDistributedSortPhase2Lb__kv_reduce.writeAction(f"movir X23 0") 
  tranDistributedSortPhase2Lb__kv_reduce.writeAction(f"sendr_wcont X22 X1 X23 X23") 
  tranDistributedSortPhase2Lb__kv_reduce.writeAction(f"yield") 
  ## print("%lu trying to sort bin with size %lu", NETID, bin_list_size);
  ## allocate space in scratchpad
  tranDistributedSortPhase2Lb__kv_reduce.writeAction(f"__if_kv_reduce_2_post: addi X7 X23 20000") 
  tranDistributedSortPhase2Lb__kv_reduce.writeAction(f"movlr 112(X23) X25 0 8") 
  tranDistributedSortPhase2Lb__kv_reduce.writeAction(f"addi X25 X24 0")  # This is for casting. May be used later on
  tranDistributedSortPhase2Lb__kv_reduce.writeAction(f"movir X21 0") 
  tranDistributedSortPhase2Lb__kv_reduce.writeAction(f"__while_kv_reduce_3_condition: addi X21 X25 0")  # This is for casting. May be used later on
  tranDistributedSortPhase2Lb__kv_reduce.writeAction(f"sar X24 X25 X26") 
  tranDistributedSortPhase2Lb__kv_reduce.writeAction(f"andi X26 X27 1") 
  tranDistributedSortPhase2Lb__kv_reduce.writeAction(f"beqi X27 0 __while_kv_reduce_5_post") 
  tranDistributedSortPhase2Lb__kv_reduce.writeAction(f"__while_kv_reduce_4_body: addi X21 X21 1") 
  tranDistributedSortPhase2Lb__kv_reduce.writeAction(f"jmp __while_kv_reduce_3_condition") 
  tranDistributedSortPhase2Lb__kv_reduce.writeAction(f"__while_kv_reduce_5_post: movir X25 1") 
  tranDistributedSortPhase2Lb__kv_reduce.writeAction(f"sl X25 X21 X25") 
  tranDistributedSortPhase2Lb__kv_reduce.writeAction(f"addi X25 X26 0")  # This is for casting. May be used later on
  tranDistributedSortPhase2Lb__kv_reduce.writeAction(f"or X24 X26 X24") 
  tranDistributedSortPhase2Lb__kv_reduce.writeAction(f"movrl X24 112(X23) 0 8") 
  tranDistributedSortPhase2Lb__kv_reduce.writeAction(f"movir X26 6000") 
  tranDistributedSortPhase2Lb__kv_reduce.writeAction(f"bgtu X9 X26 __if_kv_reduce_7_false") 
  ## print("getting bit = %d for local sort at NWID %lu", local_space_bit, NETID);
  tranDistributedSortPhase2Lb__kv_reduce.writeAction(f"__if_kv_reduce_6_true: evi X2 X22 DistributedSortPhase2Lb::local_bin_sort 1") 
  tranDistributedSortPhase2Lb__kv_reduce.writeAction(f"jmp __if_kv_reduce_8_post") 
  ## print("getting bit = %d for ext merge sort at NWID %lu", local_space_bit, NETID);
  ## print("bin_list_size = %lu", bin_list_size);
  tranDistributedSortPhase2Lb__kv_reduce.writeAction(f"__if_kv_reduce_7_false: evi X2 X22 DistributedSortPhase2Lb::ext_merge_sort 1") 
  tranDistributedSortPhase2Lb__kv_reduce.writeAction(f"__if_kv_reduce_8_post: addi X7 X25 8") 
  tranDistributedSortPhase2Lb__kv_reduce.writeAction(f"movrl X8 0(X25) 0 8") 
  tranDistributedSortPhase2Lb__kv_reduce.writeAction(f"movrl X9 8(X25) 0 8") 
  tranDistributedSortPhase2Lb__kv_reduce.writeAction(f"movrl X10 16(X25) 0 8") 
  tranDistributedSortPhase2Lb__kv_reduce.writeAction(f"addi X7 X27 20256") 
  tranDistributedSortPhase2Lb__kv_reduce.writeAction(f"muli X21 X28 6000") 
  tranDistributedSortPhase2Lb__kv_reduce.writeAction(f"sli X28 X29 3") 
  tranDistributedSortPhase2Lb__kv_reduce.writeAction(f"add X27 X29 X30") 
  tranDistributedSortPhase2Lb__kv_reduce.writeAction(f"movrl X30 24(X25) 0 8") 
  tranDistributedSortPhase2Lb__kv_reduce.writeAction(f"send_wcont X22 X1 X25 4") 
  tranDistributedSortPhase2Lb__kv_reduce.writeAction(f"addi X1 X19 0") 
  ## send_event(evw, ikey, bin_list_size, bin_addr, CCONT);
  tranDistributedSortPhase2Lb__kv_reduce.writeAction(f"yield") 
  ## unsigned long* local ptr = LMBASE + (SORT_OFFSET);
  ## unsigned long bin_size = ptr[BIN_SIZE];
  ## unsigned long bins_per_lane = ptr[BINS_PER_LANE];
  ## unsigned long local_bin_idx = value / bin_size % bins_per_lane;
  ## unsigned long dram_block_size = ptr[DRAM_BLOCK_SIZE];
  ## print("receiving value = %d, local_bin_idx = %d", value, local_bin_idx);
  ## unsigned long * local counter_addr = LMBASE + (SORT_OFFSET + COUNTERS_OFFSET) + 8 * local_bin_idx;
  ## unsigned long local_bin_count = *counter_addr;
  ## unsigned long * local dram_addr = ptr[TMP_ADDR] + value / bin_size * dram_block_size + local_bin_count * 8;
  ## send_dram_write(dram_addr, value, DistributedSortPhase2Lb::kv_reduce_return);
  ## *counter_addr = local_bin_count + 1;
  ## print("%lu", counter_addr);
  ## print("local_bin_idx = %d, local_bin_count = %d, dram_addr = %lu", local_bin_idx, local_bin_count, dram_addr);
  ## yield;
  ## print("d", local_bin_idx);
  ## print("receiving %d %d, local_bin_idx = %d", key, value, local_bin_idx);
  ## unsigned long evw = evw_update_event(CEVNT, DistributedSortPhase2Lb::kv_reduce_return, 2);
  ## // unsigned long evw = evw_update_event(CEVNT, DistributedSortPhase1::kv_combine, 2);
  ## send_event(evw, 0, IGNRCONT);
  tranDistributedSortPhase2Lb__kv_reduce.writeAction(f"yield") 
  
  ## event ext_merge_sort(unsigned long ikey, unsigned long bin_list_size, unsigned long bin_addr) {
  # Writing code for event DistributedSortPhase2Lb::ext_merge_sort
  tranDistributedSortPhase2Lb__ext_merge_sort = efa.writeEvent('DistributedSortPhase2Lb::ext_merge_sort')
  tranDistributedSortPhase2Lb__ext_merge_sort.writeAction(f"entry: print 'in ext_merge_sort, bin_size = %lu' X9") 
  ## unsigned long* local ptr = LMBASE + SORT_OFFSET + VAR_SIZE;
  tranDistributedSortPhase2Lb__ext_merge_sort.writeAction(f"addi X7 X22 20000") 
  tranDistributedSortPhase2Lb__ext_merge_sort.writeAction(f"movlr 88(X22) X24 0 8") 
  tranDistributedSortPhase2Lb__ext_merge_sort.writeAction(f"sub X10 X24 X25") 
  tranDistributedSortPhase2Lb__ext_merge_sort.writeAction(f"sari X25 X23 3") 
  tranDistributedSortPhase2Lb__ext_merge_sort.writeAction(f"movlr 16(X22) X25 0 8") 
  tranDistributedSortPhase2Lb__ext_merge_sort.writeAction(f"movlr 80(X22) X26 0 8") 
  tranDistributedSortPhase2Lb__ext_merge_sort.writeAction(f"mul X23 X26 X27") 
  tranDistributedSortPhase2Lb__ext_merge_sort.writeAction(f"add X25 X27 X24") 
  tranDistributedSortPhase2Lb__ext_merge_sort.writeAction(f"addi X24 X18 0") 
  tranDistributedSortPhase2Lb__ext_merge_sort.writeAction(f"addi X9 X17 0") 
  tranDistributedSortPhase2Lb__ext_merge_sort.writeAction(f"movir X25 0") 
  tranDistributedSortPhase2Lb__ext_merge_sort.writeAction(f"evlb X25 ExternalMergeSort::sort") 
  tranDistributedSortPhase2Lb__ext_merge_sort.writeAction(f"evi X25 X25 255 4") 
  tranDistributedSortPhase2Lb__ext_merge_sort.writeAction(f"ev X25 X25 X0 X0 8") 
  tranDistributedSortPhase2Lb__ext_merge_sort.writeAction(f"addi X7 X26 8") 
  tranDistributedSortPhase2Lb__ext_merge_sort.writeAction(f"movrl X18 0(X26) 0 8") 
  tranDistributedSortPhase2Lb__ext_merge_sort.writeAction(f"movrl X17 8(X26) 0 8") 
  tranDistributedSortPhase2Lb__ext_merge_sort.writeAction(f"movrl X11 16(X26) 0 8") 
  ## unsigned long bk_size = SP_BLOCKSIZE;
  tranDistributedSortPhase2Lb__ext_merge_sort.writeAction(f"movir X28 6000") 
  tranDistributedSortPhase2Lb__ext_merge_sort.writeAction(f"movrl X28 24(X26) 0 8") 
  tranDistributedSortPhase2Lb__ext_merge_sort.writeAction(f"send_wret X25 DistributedSortPhase2Lb::kv_reduce_ext_sort_ret X26 4 X27") 
  ## yield;
  tranDistributedSortPhase2Lb__ext_merge_sort.writeAction(f"yield") 
  
  # Writing code for event DistributedSortPhase2Lb::local_bin_sort
  tranDistributedSortPhase2Lb__local_bin_sort = efa.writeEvent('DistributedSortPhase2Lb::local_bin_sort')
  ## unsigned long* local ptr = LMBASE + SORT_OFFSET + VAR_SIZE;
  tranDistributedSortPhase2Lb__local_bin_sort.writeAction(f"entry: print 'in local_bin_sort, bin_size = %lu' X9") 
  tranDistributedSortPhase2Lb__local_bin_sort.writeAction(f"addi X7 X22 20000") 
  tranDistributedSortPhase2Lb__local_bin_sort.writeAction(f"movlr 88(X22) X24 0 8") 
  tranDistributedSortPhase2Lb__local_bin_sort.writeAction(f"sub X10 X24 X25") 
  tranDistributedSortPhase2Lb__local_bin_sort.writeAction(f"sari X25 X23 3") 
  tranDistributedSortPhase2Lb__local_bin_sort.writeAction(f"movlr 16(X22) X25 0 8") 
  tranDistributedSortPhase2Lb__local_bin_sort.writeAction(f"movlr 80(X22) X26 0 8") 
  tranDistributedSortPhase2Lb__local_bin_sort.writeAction(f"mul X23 X26 X27") 
  tranDistributedSortPhase2Lb__local_bin_sort.writeAction(f"add X25 X27 X24") 
  ## print("starting sorting bin %d", NETID);
  tranDistributedSortPhase2Lb__local_bin_sort.writeAction(f"addi X24 X18 0") 
  ## print("bin_id = %lu", bin_id);
  tranDistributedSortPhase2Lb__local_bin_sort.writeAction(f"sub X11 X18 X20") 
  ## print("sorting bin from dram: %lu, bin_size = %lu", bin_dram_addr, bin_list_size);
  ## if(NETID == 60) {
  ## 		sptr =  LMBASE + (SORT_OFFSET + VAR_SIZE) + local_space_bit * SP_BLOCKSIZE * 8;
  ## 		for (int i = 0; i < bin_list_size; i = i + 1) {
  ## 			print("begin sort60, having %lu", sptr[i]);
  ## 		}
  ## }
  ## for (tot = 0; tot < bin_list_size; tot = tot + 1) {
  ## 	send_dram_read(bin_dram_addr, 1, DistributedSortPhase2Lb::kv_reduce_load_ret);
  ## 	bin_dram_addr = bin_dram_addr + 8;
  ## }
  ## asm {"perflog 1 0 '[NWID %lu] start sorting bin' X0" };
  tranDistributedSortPhase2Lb__local_bin_sort.writeAction(f"movir X25 0") 
  tranDistributedSortPhase2Lb__local_bin_sort.writeAction(f"evlb X25 MemcpyLib::memcpy_dram_to_sp") 
  tranDistributedSortPhase2Lb__local_bin_sort.writeAction(f"evi X25 X25 255 4") 
  tranDistributedSortPhase2Lb__local_bin_sort.writeAction(f"ev X25 X25 X0 X0 8") 
  tranDistributedSortPhase2Lb__local_bin_sort.writeAction(f"sendr3_wret X25 DistributedSortPhase2Lb::kv_reduce_load_ret X18 X11 X9 X26") 
  tranDistributedSortPhase2Lb__local_bin_sort.writeAction(f"addi X24 X18 0") 
  tranDistributedSortPhase2Lb__local_bin_sort.writeAction(f"addi X9 X17 0") 
  tranDistributedSortPhase2Lb__local_bin_sort.writeAction(f"yield") 
  
  # Writing code for event DistributedSortPhase2Lb::kv_reduce_load_ret
  tranDistributedSortPhase2Lb__kv_reduce_load_ret = efa.writeEvent('DistributedSortPhase2Lb::kv_reduce_load_ret')
  ## asm {"perflog 1 0 '[NWID %lu] loadfinish sorting bin' X0" };
  ## start a new thread for sort?
  tranDistributedSortPhase2Lb__kv_reduce_load_ret.writeAction(f"__if_kv_reduce_load_ret_0_true: evi X2 X22 DistributedSortPhase2LocalSort::init 1") 
  tranDistributedSortPhase2Lb__kv_reduce_load_ret.writeAction(f"evi X2 X23 DistributedSortPhase2Lb::kv_reduce_sort_ret 1") 
  tranDistributedSortPhase2Lb__kv_reduce_load_ret.writeAction(f"addi X7 X24 20256") 
  tranDistributedSortPhase2Lb__kv_reduce_load_ret.writeAction(f"muli X21 X25 6000") 
  tranDistributedSortPhase2Lb__kv_reduce_load_ret.writeAction(f"sli X25 X26 3") 
  tranDistributedSortPhase2Lb__kv_reduce_load_ret.writeAction(f"add X24 X26 X27") 
  tranDistributedSortPhase2Lb__kv_reduce_load_ret.writeAction(f"sendr_wcont X22 X23 X17 X27") 
  tranDistributedSortPhase2Lb__kv_reduce_load_ret.writeAction(f"yield") 
  
  # Writing code for event DistributedSortPhase2Lb::kv_reduce_sort_ret
  tranDistributedSortPhase2Lb__kv_reduce_sort_ret = efa.writeEvent('DistributedSortPhase2Lb::kv_reduce_sort_ret')
  ## print("in kv_reduce_sort_ret");
  tranDistributedSortPhase2Lb__kv_reduce_sort_ret.writeAction(f"entry: addi X7 X23 20256") 
  tranDistributedSortPhase2Lb__kv_reduce_sort_ret.writeAction(f"muli X21 X24 6000") 
  tranDistributedSortPhase2Lb__kv_reduce_sort_ret.writeAction(f"sli X24 X25 3") 
  tranDistributedSortPhase2Lb__kv_reduce_sort_ret.writeAction(f"add X23 X25 X22") 
  tranDistributedSortPhase2Lb__kv_reduce_sort_ret.writeAction(f"sub X22 X20 X18") 
  tranDistributedSortPhase2Lb__kv_reduce_sort_ret.writeAction(f"movir X23 0") 
  tranDistributedSortPhase2Lb__kv_reduce_sort_ret.writeAction(f"evlb X23 MemcpyLib::memcpy_sp_to_dram") 
  tranDistributedSortPhase2Lb__kv_reduce_sort_ret.writeAction(f"evi X23 X23 255 4") 
  tranDistributedSortPhase2Lb__kv_reduce_sort_ret.writeAction(f"ev X23 X23 X0 X0 8") 
  tranDistributedSortPhase2Lb__kv_reduce_sort_ret.writeAction(f"sendr3_wret X23 DistributedSortPhase2Lb::kv_reduce_sort_send_back_ret X22 X18 X17 X24") 
  ## // asm {"perflog 1 0 '[NWID %lu] sortfinish sorting bin' X0" };
  ## for (tot = 0; tot < bin_size; tot = tot + 1) {
  ## 	send_dram_write(bin_dram_addr, lm_ptr, 1, kv_reduce_sort_send_back_ret);
  ## 	bin_dram_addr = bin_dram_addr + 8;
  ## 	lm_ptr = lm_ptr + 8;
  ## }
  tranDistributedSortPhase2Lb__kv_reduce_sort_ret.writeAction(f"yield") 
  
  # Writing code for event DistributedSortPhase2Lb::kv_reduce_sort_send_back_ret
  tranDistributedSortPhase2Lb__kv_reduce_sort_send_back_ret = efa.writeEvent('DistributedSortPhase2Lb::kv_reduce_sort_send_back_ret')
  ## print("sended back sorted bin to dram: %lu, bin_size = %lu", bin_dram_addr, bin_size);
  ## asm {"perflog 1 0 '[NWID %lu] storefinish sorting bin' X0" };
  tranDistributedSortPhase2Lb__kv_reduce_sort_send_back_ret.writeAction(f"__if_kv_reduce_sort_send_back_ret_0_true: evi X2 X22 DistributedSortPhase2Lb::kv_reduce_return 1") 
  tranDistributedSortPhase2Lb__kv_reduce_sort_send_back_ret.writeAction(f"movir X25 0") 
  tranDistributedSortPhase2Lb__kv_reduce_sort_send_back_ret.writeAction(f"sendr_wcont X22 X19 X25 X25") 
  ## send_event(evw, 0, IGNRCONT);
  ## clear the current bit
  tranDistributedSortPhase2Lb__kv_reduce_sort_send_back_ret.writeAction(f"addi X7 X23 20000") 
  tranDistributedSortPhase2Lb__kv_reduce_sort_send_back_ret.writeAction(f"movlr 112(X23) X25 0 8") 
  tranDistributedSortPhase2Lb__kv_reduce_sort_send_back_ret.writeAction(f"addi X25 X24 0")  # This is for casting. May be used later on
  tranDistributedSortPhase2Lb__kv_reduce_sort_send_back_ret.writeAction(f"movir X25 1") 
  tranDistributedSortPhase2Lb__kv_reduce_sort_send_back_ret.writeAction(f"sl X25 X21 X25") 
  tranDistributedSortPhase2Lb__kv_reduce_sort_send_back_ret.writeAction(f"addi X25 X26 0")  # This is for casting. May be used later on
  tranDistributedSortPhase2Lb__kv_reduce_sort_send_back_ret.writeAction(f"xor X24 X26 X24") 
  tranDistributedSortPhase2Lb__kv_reduce_sort_send_back_ret.writeAction(f"movrl X24 112(X23) 0 8") 
  tranDistributedSortPhase2Lb__kv_reduce_sort_send_back_ret.writeAction(f"yield") 
  
  # Writing code for event DistributedSortPhase2Lb::kv_reduce_ext_sort_ret
  tranDistributedSortPhase2Lb__kv_reduce_ext_sort_ret = efa.writeEvent('DistributedSortPhase2Lb::kv_reduce_ext_sort_ret')
  ## asm {"perflog 1 0 '[NWID %lu] end sorting bin' X0" };
  tranDistributedSortPhase2Lb__kv_reduce_ext_sort_ret.writeAction(f"entry: evi X2 X22 DistributedSortPhase2Lb::kv_reduce_return 1") 
  tranDistributedSortPhase2Lb__kv_reduce_ext_sort_ret.writeAction(f"movir X25 0") 
  tranDistributedSortPhase2Lb__kv_reduce_ext_sort_ret.writeAction(f"sendr_wcont X22 X19 X25 X25") 
  ## send_event(evw, 0, IGNRCONT);
  tranDistributedSortPhase2Lb__kv_reduce_ext_sort_ret.writeAction(f"addi X7 X23 20000") 
  tranDistributedSortPhase2Lb__kv_reduce_ext_sort_ret.writeAction(f"movlr 112(X23) X25 0 8") 
  tranDistributedSortPhase2Lb__kv_reduce_ext_sort_ret.writeAction(f"addi X25 X24 0")  # This is for casting. May be used later on
  tranDistributedSortPhase2Lb__kv_reduce_ext_sort_ret.writeAction(f"movir X25 1") 
  tranDistributedSortPhase2Lb__kv_reduce_ext_sort_ret.writeAction(f"sl X25 X21 X25") 
  tranDistributedSortPhase2Lb__kv_reduce_ext_sort_ret.writeAction(f"addi X25 X26 0")  # This is for casting. May be used later on
  tranDistributedSortPhase2Lb__kv_reduce_ext_sort_ret.writeAction(f"xor X24 X26 X24") 
  tranDistributedSortPhase2Lb__kv_reduce_ext_sort_ret.writeAction(f"movrl X24 112(X23) 0 8") 
  tranDistributedSortPhase2Lb__kv_reduce_ext_sort_ret.writeAction(f"yield") 
  
  
  ###################################################################
  ###### Writing code for thread DistributedSortPhase2MapperLb ######
  ###################################################################
  ## event kv_map(unsigned long key, unsigned long val) {
  ## // print("<kv_map2> getting key = %lu, value = %lu", key, val);
  ##     unsigned long evw = evw_new(NETID, DistributedSortPhase2MapperLb::kv_map_cont, 2);
  ## // unsigned long* local ptr = LMBASE + SORT_OFFSET;
  ## // unsigned long ikey = key / ptr[BKSIZE];
  ## // print("ikey = %d", ikey);
  ## // send_event(evw, val, key, val, CCONT);
  ## send_event(evw, val / 8, key, val, CCONT);
  ##     // evw = evw_update_event(CEVNT, DistributedSortPhase2MapperLb::kv_map_return, 2);
  ##     // send_event(evw, NETID, NETID, CCONT);
  ## yield;
  ## }
  # Writing code for event DistributedSortPhase2MapperLb::kv_map
  tranDistributedSortPhase2MapperLb__kv_map = efa.writeEvent('DistributedSortPhase2MapperLb::kv_map')
  tranDistributedSortPhase2MapperLb__kv_map.writeAction(f"entry: print '<adsdsaicoxshui> getting key = %lu, value = %lu' X8 X9") 
  tranDistributedSortPhase2MapperLb__kv_map.writeAction(f"evi X2 X22 DistributedSortPhase2MapperLb::kv_map_cont 1") 
  ## unsigned long* local ptr = LMBASE + SORT_OFFSET;
  ## unsigned long ikey = key / ptr[BKSIZE];
  ## print("ikey = %d", ikey);
  ## send_event(evw, val, key, val, CCONT);
  tranDistributedSortPhase2MapperLb__kv_map.writeAction(f"addi X7 X23 20000") 
  tranDistributedSortPhase2MapperLb__kv_map.writeAction(f"movlr 88(X23) X25 0 8") 
  tranDistributedSortPhase2MapperLb__kv_map.writeAction(f"sub X9 X25 X26") 
  tranDistributedSortPhase2MapperLb__kv_map.writeAction(f"sari X26 X27 3") 
  tranDistributedSortPhase2MapperLb__kv_map.writeAction(f"movlr 72(X23) X28 0 8") 
  tranDistributedSortPhase2MapperLb__kv_map.writeAction(f"div X27 X28 X24") 
  ## print("bin_lane_id = %lu", bin_lane_id);
  ## send_event(evw, val / 8, key, val, CCONT);
  tranDistributedSortPhase2MapperLb__kv_map.writeAction(f"sendr3_wcont X22 X1 X24 X8 X9") 
  tranDistributedSortPhase2MapperLb__kv_map.writeAction(f"addi X24 X25 0") 
  tranDistributedSortPhase2MapperLb__kv_map.writeAction(f"addi X8 X26 0") 
  tranDistributedSortPhase2MapperLb__kv_map.writeAction(f"addi X9 X27 0") 
  ## evw = evw_update_event(CEVNT, DistributedSortPhase2Mapper::kv_map_return, 2);
  ## send_event(evw, NETID, NETID, CCONT);
  tranDistributedSortPhase2MapperLb__kv_map.writeAction(f"yield") 
  
  # Writing code for event DistributedSortPhase2MapperLb::kv_map_cont
  tranDistributedSortPhase2MapperLb__kv_map_cont = efa.writeEvent('DistributedSortPhase2MapperLb::kv_map_cont')
  ## print("receiving %lu %lu %lu", ikey, bin_list_size, bin_addr);
  ## TODO: need to manage scratchpad
  ## print("bin_list_size = %lu", bin_list_size * 8);
  ## unsigned long cur_size = bin_list_size * 8;
  tranDistributedSortPhase2MapperLb__kv_map_cont.writeAction(f"entry: bneiu X9 0 __if_kv_map_cont_2_post") 
  tranDistributedSortPhase2MapperLb__kv_map_cont.writeAction(f"__if_kv_map_cont_0_true: evi X2 X22 DistributedSortPhase2MapperLb::kv_map_return 1") 
  tranDistributedSortPhase2MapperLb__kv_map_cont.writeAction(f"movir X23 0") 
  tranDistributedSortPhase2MapperLb__kv_map_cont.writeAction(f"sendr_wcont X22 X1 X23 X23") 
  tranDistributedSortPhase2MapperLb__kv_map_cont.writeAction(f"yield") 
  ## print("%lu trying to sort bin with size %lu", NETID, bin_list_size);
  ## allocate space in scratchpad
  tranDistributedSortPhase2MapperLb__kv_map_cont.writeAction(f"__if_kv_map_cont_2_post: addi X7 X23 20000") 
  tranDistributedSortPhase2MapperLb__kv_map_cont.writeAction(f"movlr 112(X23) X25 0 8") 
  tranDistributedSortPhase2MapperLb__kv_map_cont.writeAction(f"addi X25 X24 0")  # This is for casting. May be used later on
  tranDistributedSortPhase2MapperLb__kv_map_cont.writeAction(f"movir X21 0") 
  tranDistributedSortPhase2MapperLb__kv_map_cont.writeAction(f"__while_kv_map_cont_3_condition: addi X21 X25 0")  # This is for casting. May be used later on
  tranDistributedSortPhase2MapperLb__kv_map_cont.writeAction(f"sar X24 X25 X26") 
  tranDistributedSortPhase2MapperLb__kv_map_cont.writeAction(f"andi X26 X27 1") 
  tranDistributedSortPhase2MapperLb__kv_map_cont.writeAction(f"beqi X27 0 __while_kv_map_cont_5_post") 
  tranDistributedSortPhase2MapperLb__kv_map_cont.writeAction(f"__while_kv_map_cont_4_body: addi X21 X21 1") 
  tranDistributedSortPhase2MapperLb__kv_map_cont.writeAction(f"jmp __while_kv_map_cont_3_condition") 
  tranDistributedSortPhase2MapperLb__kv_map_cont.writeAction(f"__while_kv_map_cont_5_post: movir X25 1") 
  tranDistributedSortPhase2MapperLb__kv_map_cont.writeAction(f"sl X25 X21 X25") 
  tranDistributedSortPhase2MapperLb__kv_map_cont.writeAction(f"addi X25 X26 0")  # This is for casting. May be used later on
  tranDistributedSortPhase2MapperLb__kv_map_cont.writeAction(f"or X24 X26 X24") 
  tranDistributedSortPhase2MapperLb__kv_map_cont.writeAction(f"movrl X24 112(X23) 0 8") 
  tranDistributedSortPhase2MapperLb__kv_map_cont.writeAction(f"movir X26 6000") 
  tranDistributedSortPhase2MapperLb__kv_map_cont.writeAction(f"bgtu X9 X26 __if_kv_map_cont_7_false") 
  ## print("getting bit = %d for local sort at NWID %lu", local_space_bit, NETID);
  tranDistributedSortPhase2MapperLb__kv_map_cont.writeAction(f"__if_kv_map_cont_6_true: evi X2 X22 DistributedSortPhase2MapperLb::local_bin_sort 1") 
  tranDistributedSortPhase2MapperLb__kv_map_cont.writeAction(f"jmp __if_kv_map_cont_8_post") 
  ## print("getting bit = %d for ext merge sort at NWID %lu", local_space_bit, NETID);
  ## print("bin_list_size = %lu", bin_list_size);
  tranDistributedSortPhase2MapperLb__kv_map_cont.writeAction(f"__if_kv_map_cont_7_false: evi X2 X22 DistributedSortPhase2MapperLb::ext_merge_sort 1") 
  tranDistributedSortPhase2MapperLb__kv_map_cont.writeAction(f"__if_kv_map_cont_8_post: addi X7 X25 8") 
  tranDistributedSortPhase2MapperLb__kv_map_cont.writeAction(f"movrl X8 0(X25) 0 8") 
  tranDistributedSortPhase2MapperLb__kv_map_cont.writeAction(f"movrl X9 8(X25) 0 8") 
  tranDistributedSortPhase2MapperLb__kv_map_cont.writeAction(f"movrl X10 16(X25) 0 8") 
  tranDistributedSortPhase2MapperLb__kv_map_cont.writeAction(f"addi X7 X27 20256") 
  tranDistributedSortPhase2MapperLb__kv_map_cont.writeAction(f"muli X21 X28 6000") 
  tranDistributedSortPhase2MapperLb__kv_map_cont.writeAction(f"sli X28 X29 3") 
  tranDistributedSortPhase2MapperLb__kv_map_cont.writeAction(f"add X27 X29 X30") 
  tranDistributedSortPhase2MapperLb__kv_map_cont.writeAction(f"movrl X30 24(X25) 0 8") 
  tranDistributedSortPhase2MapperLb__kv_map_cont.writeAction(f"send_wcont X22 X1 X25 4") 
  tranDistributedSortPhase2MapperLb__kv_map_cont.writeAction(f"addi X1 X19 0") 
  ## send_event(evw, ikey, bin_list_size, bin_addr, CCONT);
  tranDistributedSortPhase2MapperLb__kv_map_cont.writeAction(f"yield") 
  ## unsigned long* local ptr = LMBASE + (SORT_OFFSET);
  ## unsigned long bin_size = ptr[BIN_SIZE];
  ## unsigned long bins_per_lane = ptr[BINS_PER_LANE];
  ## unsigned long local_bin_idx = value / bin_size % bins_per_lane;
  ## unsigned long dram_block_size = ptr[DRAM_BLOCK_SIZE];
  ## print("receiving value = %d, local_bin_idx = %d", value, local_bin_idx);
  ## unsigned long * local counter_addr = LMBASE + (SORT_OFFSET + COUNTERS_OFFSET) + 8 * local_bin_idx;
  ## unsigned long local_bin_count = *counter_addr;
  ## unsigned long * local dram_addr = ptr[TMP_ADDR] + value / bin_size * dram_block_size + local_bin_count * 8;
  ## send_dram_write(dram_addr, value, DistributedSortPhase2MapperLb::kv_reduce_return);
  ## *counter_addr = local_bin_count + 1;
  ## print("%lu", counter_addr);
  ## print("local_bin_idx = %d, local_bin_count = %d, dram_addr = %lu", local_bin_idx, local_bin_count, dram_addr);
  ## yield;
  ## print("d", local_bin_idx);
  ## print("receiving %d %d, local_bin_idx = %d", key, value, local_bin_idx);
  ## unsigned long evw = evw_update_event(CEVNT, DistributedSortPhase2MapperLb::kv_reduce_return, 2);
  ## // unsigned long evw = evw_update_event(CEVNT, DistributedSortPhase1::kv_combine, 2);
  ## send_event(evw, 0, IGNRCONT);
  tranDistributedSortPhase2MapperLb__kv_map_cont.writeAction(f"yield") 
  
  # Writing code for event DistributedSortPhase2MapperLb::kv_reduce
  tranDistributedSortPhase2MapperLb__kv_reduce = efa.writeEvent('DistributedSortPhase2MapperLb::kv_reduce')
  tranDistributedSortPhase2MapperLb__kv_reduce.writeAction(f"entry: yield") 
  
  ## event ext_merge_sort(unsigned long ikey, unsigned long bin_list_size, unsigned long bin_addr) {
  # Writing code for event DistributedSortPhase2MapperLb::ext_merge_sort
  tranDistributedSortPhase2MapperLb__ext_merge_sort = efa.writeEvent('DistributedSortPhase2MapperLb::ext_merge_sort')
  tranDistributedSortPhase2MapperLb__ext_merge_sort.writeAction(f"entry: print 'in ext_merge_sort, bin_size = %lu' X9") 
  ## unsigned long* local ptr = LMBASE + SORT_OFFSET + VAR_SIZE;
  tranDistributedSortPhase2MapperLb__ext_merge_sort.writeAction(f"addi X7 X22 20000") 
  tranDistributedSortPhase2MapperLb__ext_merge_sort.writeAction(f"movlr 88(X22) X24 0 8") 
  tranDistributedSortPhase2MapperLb__ext_merge_sort.writeAction(f"sub X10 X24 X25") 
  tranDistributedSortPhase2MapperLb__ext_merge_sort.writeAction(f"sari X25 X23 3") 
  tranDistributedSortPhase2MapperLb__ext_merge_sort.writeAction(f"movlr 16(X22) X25 0 8") 
  tranDistributedSortPhase2MapperLb__ext_merge_sort.writeAction(f"movlr 80(X22) X26 0 8") 
  tranDistributedSortPhase2MapperLb__ext_merge_sort.writeAction(f"mul X23 X26 X27") 
  tranDistributedSortPhase2MapperLb__ext_merge_sort.writeAction(f"add X25 X27 X24") 
  tranDistributedSortPhase2MapperLb__ext_merge_sort.writeAction(f"addi X24 X18 0") 
  tranDistributedSortPhase2MapperLb__ext_merge_sort.writeAction(f"addi X9 X17 0") 
  tranDistributedSortPhase2MapperLb__ext_merge_sort.writeAction(f"movir X25 0") 
  tranDistributedSortPhase2MapperLb__ext_merge_sort.writeAction(f"evlb X25 ExternalMergeSort::sort") 
  tranDistributedSortPhase2MapperLb__ext_merge_sort.writeAction(f"evi X25 X25 255 4") 
  tranDistributedSortPhase2MapperLb__ext_merge_sort.writeAction(f"ev X25 X25 X0 X0 8") 
  tranDistributedSortPhase2MapperLb__ext_merge_sort.writeAction(f"addi X7 X26 8") 
  tranDistributedSortPhase2MapperLb__ext_merge_sort.writeAction(f"movrl X18 0(X26) 0 8") 
  tranDistributedSortPhase2MapperLb__ext_merge_sort.writeAction(f"movrl X17 8(X26) 0 8") 
  tranDistributedSortPhase2MapperLb__ext_merge_sort.writeAction(f"movrl X11 16(X26) 0 8") 
  ## unsigned long bk_size = SP_BLOCKSIZE;
  tranDistributedSortPhase2MapperLb__ext_merge_sort.writeAction(f"movir X28 6000") 
  tranDistributedSortPhase2MapperLb__ext_merge_sort.writeAction(f"movrl X28 24(X26) 0 8") 
  tranDistributedSortPhase2MapperLb__ext_merge_sort.writeAction(f"send_wret X25 DistributedSortPhase2MapperLb::kv_reduce_ext_sort_ret X26 4 X27") 
  ## yield;
  tranDistributedSortPhase2MapperLb__ext_merge_sort.writeAction(f"yield") 
  
  # Writing code for event DistributedSortPhase2MapperLb::local_bin_sort
  tranDistributedSortPhase2MapperLb__local_bin_sort = efa.writeEvent('DistributedSortPhase2MapperLb::local_bin_sort')
  ## unsigned long* local ptr = LMBASE + SORT_OFFSET + VAR_SIZE;
  tranDistributedSortPhase2MapperLb__local_bin_sort.writeAction(f"entry: print 'in local_bin_sort, bin_size = %lu' X9") 
  tranDistributedSortPhase2MapperLb__local_bin_sort.writeAction(f"addi X7 X22 20000") 
  tranDistributedSortPhase2MapperLb__local_bin_sort.writeAction(f"movlr 88(X22) X24 0 8") 
  tranDistributedSortPhase2MapperLb__local_bin_sort.writeAction(f"sub X10 X24 X25") 
  tranDistributedSortPhase2MapperLb__local_bin_sort.writeAction(f"sari X25 X23 3") 
  tranDistributedSortPhase2MapperLb__local_bin_sort.writeAction(f"movlr 16(X22) X25 0 8") 
  tranDistributedSortPhase2MapperLb__local_bin_sort.writeAction(f"movlr 80(X22) X26 0 8") 
  tranDistributedSortPhase2MapperLb__local_bin_sort.writeAction(f"mul X23 X26 X27") 
  tranDistributedSortPhase2MapperLb__local_bin_sort.writeAction(f"add X25 X27 X24") 
  ## print("starting sorting bin %d", NETID);
  tranDistributedSortPhase2MapperLb__local_bin_sort.writeAction(f"addi X24 X18 0") 
  ## print("bin_id = %lu", bin_id);
  tranDistributedSortPhase2MapperLb__local_bin_sort.writeAction(f"sub X11 X18 X20") 
  ## print("sorting bin from dram: %lu, bin_size = %lu", bin_dram_addr, bin_list_size);
  ## if(NETID == 60) {
  ## 		sptr =  LMBASE + (SORT_OFFSET + VAR_SIZE) + local_space_bit * SP_BLOCKSIZE * 8;
  ## 		for (int i = 0; i < bin_list_size; i = i + 1) {
  ## 			print("begin sort60, having %lu", sptr[i]);
  ## 		}
  ## }
  ## for (tot = 0; tot < bin_list_size; tot = tot + 1) {
  ## 	send_dram_read(bin_dram_addr, 1, DistributedSortPhase2MapperLb::kv_reduce_load_ret);
  ## 	bin_dram_addr = bin_dram_addr + 8;
  ## }
  ## asm {"perflog 1 0 '[NWID %lu] start sorting bin' X0" };
  tranDistributedSortPhase2MapperLb__local_bin_sort.writeAction(f"movir X25 0") 
  tranDistributedSortPhase2MapperLb__local_bin_sort.writeAction(f"evlb X25 MemcpyLib::memcpy_dram_to_sp") 
  tranDistributedSortPhase2MapperLb__local_bin_sort.writeAction(f"evi X25 X25 255 4") 
  tranDistributedSortPhase2MapperLb__local_bin_sort.writeAction(f"ev X25 X25 X0 X0 8") 
  tranDistributedSortPhase2MapperLb__local_bin_sort.writeAction(f"sendr3_wret X25 DistributedSortPhase2MapperLb::kv_reduce_load_ret X18 X11 X9 X26") 
  tranDistributedSortPhase2MapperLb__local_bin_sort.writeAction(f"addi X24 X18 0") 
  tranDistributedSortPhase2MapperLb__local_bin_sort.writeAction(f"addi X9 X17 0") 
  tranDistributedSortPhase2MapperLb__local_bin_sort.writeAction(f"yield") 
  
  # Writing code for event DistributedSortPhase2MapperLb::kv_reduce_load_ret
  tranDistributedSortPhase2MapperLb__kv_reduce_load_ret = efa.writeEvent('DistributedSortPhase2MapperLb::kv_reduce_load_ret')
  ## asm {"perflog 1 0 '[NWID %lu] loadfinish sorting bin' X0" };
  ## start a new thread for sort?
  tranDistributedSortPhase2MapperLb__kv_reduce_load_ret.writeAction(f"__if_kv_reduce_load_ret_0_true: evi X2 X22 DistributedSortPhase2LocalSort::init 1") 
  tranDistributedSortPhase2MapperLb__kv_reduce_load_ret.writeAction(f"evi X2 X23 DistributedSortPhase2MapperLb::kv_reduce_sort_ret 1") 
  tranDistributedSortPhase2MapperLb__kv_reduce_load_ret.writeAction(f"addi X7 X24 20256") 
  tranDistributedSortPhase2MapperLb__kv_reduce_load_ret.writeAction(f"muli X21 X25 6000") 
  tranDistributedSortPhase2MapperLb__kv_reduce_load_ret.writeAction(f"sli X25 X26 3") 
  tranDistributedSortPhase2MapperLb__kv_reduce_load_ret.writeAction(f"add X24 X26 X27") 
  tranDistributedSortPhase2MapperLb__kv_reduce_load_ret.writeAction(f"sendr_wcont X22 X23 X17 X27") 
  tranDistributedSortPhase2MapperLb__kv_reduce_load_ret.writeAction(f"yield") 
  
  # Writing code for event DistributedSortPhase2MapperLb::kv_reduce_sort_ret
  tranDistributedSortPhase2MapperLb__kv_reduce_sort_ret = efa.writeEvent('DistributedSortPhase2MapperLb::kv_reduce_sort_ret')
  ## print("in kv_reduce_sort_ret");
  tranDistributedSortPhase2MapperLb__kv_reduce_sort_ret.writeAction(f"entry: addi X7 X23 20256") 
  tranDistributedSortPhase2MapperLb__kv_reduce_sort_ret.writeAction(f"muli X21 X24 6000") 
  tranDistributedSortPhase2MapperLb__kv_reduce_sort_ret.writeAction(f"sli X24 X25 3") 
  tranDistributedSortPhase2MapperLb__kv_reduce_sort_ret.writeAction(f"add X23 X25 X22") 
  tranDistributedSortPhase2MapperLb__kv_reduce_sort_ret.writeAction(f"sub X22 X20 X18") 
  tranDistributedSortPhase2MapperLb__kv_reduce_sort_ret.writeAction(f"movir X23 0") 
  tranDistributedSortPhase2MapperLb__kv_reduce_sort_ret.writeAction(f"evlb X23 MemcpyLib::memcpy_sp_to_dram") 
  tranDistributedSortPhase2MapperLb__kv_reduce_sort_ret.writeAction(f"evi X23 X23 255 4") 
  tranDistributedSortPhase2MapperLb__kv_reduce_sort_ret.writeAction(f"ev X23 X23 X0 X0 8") 
  tranDistributedSortPhase2MapperLb__kv_reduce_sort_ret.writeAction(f"sendr3_wret X23 DistributedSortPhase2MapperLb::kv_reduce_sort_send_back_ret X22 X18 X17 X24") 
  ## asm {"perflog 1 0 '[NWID %lu] sortfinish sorting bin' X0" };
  ## for (tot = 0; tot < bin_size; tot = tot + 1) {
  ## 	send_dram_write(bin_dram_addr, lm_ptr, 1, kv_reduce_sort_send_back_ret);
  ## 	bin_dram_addr = bin_dram_addr + 8;
  ## 	lm_ptr = lm_ptr + 8;
  ## }
  tranDistributedSortPhase2MapperLb__kv_reduce_sort_ret.writeAction(f"yield") 
  
  # Writing code for event DistributedSortPhase2MapperLb::kv_reduce_sort_send_back_ret
  tranDistributedSortPhase2MapperLb__kv_reduce_sort_send_back_ret = efa.writeEvent('DistributedSortPhase2MapperLb::kv_reduce_sort_send_back_ret')
  ## print("sended back sorted bin to dram: %lu, bin_size = %lu", bin_dram_addr, bin_size);
  ## asm {"perflog 1 0 '[NWID %lu] storefinish sorting bin' X0" };
  tranDistributedSortPhase2MapperLb__kv_reduce_sort_send_back_ret.writeAction(f"__if_kv_reduce_sort_send_back_ret_0_true: evi X2 X22 DistributedSortPhase2MapperLb::kv_map_return 1") 
  tranDistributedSortPhase2MapperLb__kv_reduce_sort_send_back_ret.writeAction(f"movir X25 0") 
  tranDistributedSortPhase2MapperLb__kv_reduce_sort_send_back_ret.writeAction(f"sendr_wcont X22 X19 X25 X25") 
  ## send_event(evw, 0, IGNRCONT);
  ## clear the current bit
  tranDistributedSortPhase2MapperLb__kv_reduce_sort_send_back_ret.writeAction(f"addi X7 X23 20000") 
  tranDistributedSortPhase2MapperLb__kv_reduce_sort_send_back_ret.writeAction(f"movlr 112(X23) X25 0 8") 
  tranDistributedSortPhase2MapperLb__kv_reduce_sort_send_back_ret.writeAction(f"addi X25 X24 0")  # This is for casting. May be used later on
  tranDistributedSortPhase2MapperLb__kv_reduce_sort_send_back_ret.writeAction(f"movir X25 1") 
  tranDistributedSortPhase2MapperLb__kv_reduce_sort_send_back_ret.writeAction(f"sl X25 X21 X25") 
  tranDistributedSortPhase2MapperLb__kv_reduce_sort_send_back_ret.writeAction(f"addi X25 X26 0")  # This is for casting. May be used later on
  tranDistributedSortPhase2MapperLb__kv_reduce_sort_send_back_ret.writeAction(f"xor X24 X26 X24") 
  tranDistributedSortPhase2MapperLb__kv_reduce_sort_send_back_ret.writeAction(f"movrl X24 112(X23) 0 8") 
  tranDistributedSortPhase2MapperLb__kv_reduce_sort_send_back_ret.writeAction(f"yield") 
  
  # Writing code for event DistributedSortPhase2MapperLb::kv_reduce_ext_sort_ret
  tranDistributedSortPhase2MapperLb__kv_reduce_ext_sort_ret = efa.writeEvent('DistributedSortPhase2MapperLb::kv_reduce_ext_sort_ret')
  ## asm {"perflog 1 0 '[NWID %lu] end sorting bin' X0" };
  tranDistributedSortPhase2MapperLb__kv_reduce_ext_sort_ret.writeAction(f"entry: evi X2 X22 DistributedSortPhase2MapperLb::kv_map_return 1") 
  tranDistributedSortPhase2MapperLb__kv_reduce_ext_sort_ret.writeAction(f"movir X25 0") 
  tranDistributedSortPhase2MapperLb__kv_reduce_ext_sort_ret.writeAction(f"sendr_wcont X22 X19 X25 X25") 
  ## send_event(evw, 0, IGNRCONT);
  tranDistributedSortPhase2MapperLb__kv_reduce_ext_sort_ret.writeAction(f"addi X7 X23 20000") 
  tranDistributedSortPhase2MapperLb__kv_reduce_ext_sort_ret.writeAction(f"movlr 112(X23) X25 0 8") 
  tranDistributedSortPhase2MapperLb__kv_reduce_ext_sort_ret.writeAction(f"addi X25 X24 0")  # This is for casting. May be used later on
  tranDistributedSortPhase2MapperLb__kv_reduce_ext_sort_ret.writeAction(f"movir X25 1") 
  tranDistributedSortPhase2MapperLb__kv_reduce_ext_sort_ret.writeAction(f"sl X25 X21 X25") 
  tranDistributedSortPhase2MapperLb__kv_reduce_ext_sort_ret.writeAction(f"addi X25 X26 0")  # This is for casting. May be used later on
  tranDistributedSortPhase2MapperLb__kv_reduce_ext_sort_ret.writeAction(f"xor X24 X26 X24") 
  tranDistributedSortPhase2MapperLb__kv_reduce_ext_sort_ret.writeAction(f"movrl X24 112(X23) 0 8") 
  tranDistributedSortPhase2MapperLb__kv_reduce_ext_sort_ret.writeAction(f"yield") 
  
  
  ###########################################################
  ###### Writing code for thread DistributedSortPhase3 ######
  ###########################################################
  # Writing code for event DistributedSortPhase3::kv_map
  tranDistributedSortPhase3__kv_map = efa.writeEvent('DistributedSortPhase3::kv_map')
  ## print("<kv_map3> getting key = %lu, value = %lu", key, val);
  tranDistributedSortPhase3__kv_map.writeAction(f"entry: movir X20 0") 
  tranDistributedSortPhase3__kv_map.writeAction(f"evlb X20 DistributedSortPhase3::kv_map_emit") 
  tranDistributedSortPhase3__kv_map.writeAction(f"evi X20 X20 255 4") 
  tranDistributedSortPhase3__kv_map.writeAction(f"ev X20 X20 X0 X0 8") 
  ## unsigned long* local ptr = LMBASE + SORT_OFFSET;
  ## unsigned long ikey = key / ptr[BKSIZE];
  ## print("ikey = %d", ikey);
  tranDistributedSortPhase3__kv_map.writeAction(f"sendr3_wcont X20 X1 X9 X8 X9") 
  tranDistributedSortPhase3__kv_map.writeAction(f"evi X2 X20 DistributedSortPhase3::kv_map_return 1") 
  tranDistributedSortPhase3__kv_map.writeAction(f"sendr_wcont X20 X1 X0 X0") 
  tranDistributedSortPhase3__kv_map.writeAction(f"yield") 
  
  # Writing code for event DistributedSortPhase3::kv_reduce
  tranDistributedSortPhase3__kv_reduce = efa.writeEvent('DistributedSortPhase3::kv_reduce')
  ## print("<kv_reduce3> receiving %lu %lu %lu", ikey, bin_list_size, bin_addr);
  tranDistributedSortPhase3__kv_reduce.writeAction(f"entry: addi X9 X17 0") 
  tranDistributedSortPhase3__kv_reduce.writeAction(f"addi X7 X21 20000") 
  tranDistributedSortPhase3__kv_reduce.writeAction(f"addi X21 X20 256") 
  tranDistributedSortPhase3__kv_reduce.writeAction(f"addi X7 X21 20000") 
  tranDistributedSortPhase3__kv_reduce.writeAction(f"addi X10 X22 0") 
  tranDistributedSortPhase3__kv_reduce.writeAction(f"movlr 88(X21) X24 0 8") 
  tranDistributedSortPhase3__kv_reduce.writeAction(f"sub X10 X24 X25") 
  tranDistributedSortPhase3__kv_reduce.writeAction(f"sari X25 X23 3") 
  tranDistributedSortPhase3__kv_reduce.writeAction(f"movlr 16(X21) X25 0 8") 
  tranDistributedSortPhase3__kv_reduce.writeAction(f"movlr 80(X21) X26 0 8") 
  tranDistributedSortPhase3__kv_reduce.writeAction(f"mul X23 X26 X27") 
  tranDistributedSortPhase3__kv_reduce.writeAction(f"add X25 X27 X24") 
  tranDistributedSortPhase3__kv_reduce.writeAction(f"addi X24 X18 0") 
  ## print("bin_id = %lu", bin_id);
  ## bin_dram_addr = tmp_bin_dram_addr; 
  tranDistributedSortPhase3__kv_reduce.writeAction(f"movlr 8(X21) X25 0 8") 
  tranDistributedSortPhase3__kv_reduce.writeAction(f"sli X17 X26 3") 
  tranDistributedSortPhase3__kv_reduce.writeAction(f"add X25 X26 X27") 
  tranDistributedSortPhase3__kv_reduce.writeAction(f"sub X27 X18 X19") 
  tranDistributedSortPhase3__kv_reduce.writeAction(f"addi X22 X25 8") 
  tranDistributedSortPhase3__kv_reduce.writeAction(f"send_dmlm_ld_wret X25 DistributedSortPhase3::load_next_bin_size 1 X26") 
  tranDistributedSortPhase3__kv_reduce.writeAction(f"yield") 
  
  # Writing code for event DistributedSortPhase3::load_next_bin_size
  tranDistributedSortPhase3__load_next_bin_size = efa.writeEvent('DistributedSortPhase3::load_next_bin_size')
  tranDistributedSortPhase3__load_next_bin_size.writeAction(f"entry: sub X8 X17 X17") 
  ## print("next bin size = %d", bin_size);
  ## print("bin_size = %d", bin_size);
  tranDistributedSortPhase3__load_next_bin_size.writeAction(f"bnei X17 0 __if_load_next_bin_size_2_post") 
  tranDistributedSortPhase3__load_next_bin_size.writeAction(f"__if_load_next_bin_size_0_true: movir X20 0") 
  tranDistributedSortPhase3__load_next_bin_size.writeAction(f"movir X21 -1") 
  tranDistributedSortPhase3__load_next_bin_size.writeAction(f"sri X21 X21 1") 
  tranDistributedSortPhase3__load_next_bin_size.writeAction(f"sendr_wcont X1 X21 X20 X20") 
  tranDistributedSortPhase3__load_next_bin_size.writeAction(f"yield") 
  tranDistributedSortPhase3__load_next_bin_size.writeAction(f"__if_load_next_bin_size_2_post: movir X20 0") 
  tranDistributedSortPhase3__load_next_bin_size.writeAction(f"evlb X20 MemcpyLib::memcpy_dram_to_dram") 
  tranDistributedSortPhase3__load_next_bin_size.writeAction(f"evi X20 X20 255 4") 
  tranDistributedSortPhase3__load_next_bin_size.writeAction(f"ev X20 X20 X0 X0 8") 
  tranDistributedSortPhase3__load_next_bin_size.writeAction(f"add X18 X19 X21") 
  tranDistributedSortPhase3__load_next_bin_size.writeAction(f"sendr3_wcont X20 X1 X18 X21 X17") 
  ## for (tot = 0; tot < bin_size; tot = tot + 1) {
  ## 	send_dram_read(bin_dram_addr, 1, DistributedSortPhase3::kv_reduce_load_ret);
  ## 	bin_dram_addr = bin_dram_addr + 8;
  ## }
  tranDistributedSortPhase3__load_next_bin_size.writeAction(f"yield") 
  
  
  ##########################################
  ###### Writing code for thread Test ######
  ##########################################
  # Writing code for event Test::test
  tranTest__test = efa.writeEvent('Test::test')
  tranTest__test.writeAction(f"entry: sli X8 X16 3") 
  tranTest__test.writeAction(f"movir X16 64") 
  tranTest__test.writeAction(f"bgtu X16 X16 __if_test_2_post") 
  tranTest__test.writeAction(f"__if_test_0_true: print 'test: x = %d' X8") 
  tranTest__test.writeAction(f"__if_test_2_post: yield") 
  
  
  #################################################
  ###### Writing code for thread SortingTest ######
  #################################################
  ## unsigned long cnt;
  # Writing code for event SortingTest::test
  tranSortingTest__test = efa.writeEvent('SortingTest::test')
  tranSortingTest__test.writeAction(f"entry: movir X16 0") 
  tranSortingTest__test.writeAction(f"evlb X16 Distributed_sort::sort_new") 
  tranSortingTest__test.writeAction(f"evi X16 X16 255 4") 
  tranSortingTest__test.writeAction(f"ev X16 X16 X0 X0 8") 
  tranSortingTest__test.writeAction(f"evi X2 X17 SortingTest::theEnd 1") 
  tranSortingTest__test.writeAction(f"addi X7 X18 8") 
  tranSortingTest__test.writeAction(f"movrl X8 0(X18) 0 8") 
  tranSortingTest__test.writeAction(f"movrl X9 8(X18) 0 8") 
  tranSortingTest__test.writeAction(f"movrl X10 16(X18) 0 8") 
  tranSortingTest__test.writeAction(f"movrl X11 24(X18) 0 8") 
  tranSortingTest__test.writeAction(f"movrl X12 32(X18) 0 8") 
  tranSortingTest__test.writeAction(f"movrl X13 40(X18) 0 8") 
  tranSortingTest__test.writeAction(f"movrl X14 48(X18) 0 8") 
  tranSortingTest__test.writeAction(f"movrl X15 56(X18) 0 8") 
  ## print("tmp")
  tranSortingTest__test.writeAction(f"send_wcont X16 X17 X18 8") 
  tranSortingTest__test.writeAction(f"yield") 
  
  # Writing code for event SortingTest::test_parallel_prefix
  tranSortingTest__test_parallel_prefix = efa.writeEvent('SortingTest::test_parallel_prefix')
  tranSortingTest__test_parallel_prefix.writeAction(f"entry: movir X16 0") 
  tranSortingTest__test_parallel_prefix.writeAction(f"evlb X16 ParallelPrefix::prefix") 
  tranSortingTest__test_parallel_prefix.writeAction(f"evi X16 X16 255 4") 
  tranSortingTest__test_parallel_prefix.writeAction(f"ev X16 X16 X0 X0 8") 
  tranSortingTest__test_parallel_prefix.writeAction(f"evi X2 X17 SortingTest::theEnd 1") 
  tranSortingTest__test_parallel_prefix.writeAction(f"addi X7 X18 8") 
  tranSortingTest__test_parallel_prefix.writeAction(f"movrl X8 0(X18) 0 8") 
  tranSortingTest__test_parallel_prefix.writeAction(f"movrl X9 8(X18) 0 8") 
  tranSortingTest__test_parallel_prefix.writeAction(f"movrl X10 16(X18) 0 8") 
  tranSortingTest__test_parallel_prefix.writeAction(f"movir X20 1600") 
  tranSortingTest__test_parallel_prefix.writeAction(f"movrl X20 24(X18) 0 8") 
  tranSortingTest__test_parallel_prefix.writeAction(f"movir X20 34368") 
  tranSortingTest__test_parallel_prefix.writeAction(f"movrl X20 32(X18) 0 8") 
  ## print("in test_parallel_prefix");
  tranSortingTest__test_parallel_prefix.writeAction(f"send_wcont X16 X17 X18 5") 
  tranSortingTest__test_parallel_prefix.writeAction(f"yield") 
  
  # Writing code for event SortingTest::theEnd
  tranSortingTest__theEnd = efa.writeEvent('SortingTest::theEnd')
  ## print("returning to theEnd");
  tranSortingTest__theEnd.writeAction(f"entry: addi X7 X16 0") 
  tranSortingTest__theEnd.writeAction(f"movir X18 1") 
  tranSortingTest__theEnd.writeAction(f"movrl X18 0(X16) 0 8") 
  tranSortingTest__theEnd.writeAction(f"yield_terminate") 
  
